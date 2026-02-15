#!/usr/bin/env python3
"""
Find all currently runnable tasks based on filesystem state.
Parallel-safe: uses sentinel files for completion tracking, no shared mutable queue.
Returns a JSON array of all tasks that can run right now.
"""
import json
import sys
import re
from pathlib import Path

MAX_REFINEMENT_ITERATIONS = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_complete(task_id):
    """Check if a task has been completed via sentinel file."""
    return Path(f'docs/.state/completed/{task_id}.done').exists()


def get_latest_feature_docs():
    """Return the most up-to-date doc path for each feature."""
    features_dir = Path('docs/02-features')
    refinement_dir = Path('docs/03-refinement')
    docs = []
    for feature_file in sorted(features_dir.glob('*.md')):
        refined_dir = refinement_dir / feature_file.stem
        if refined_dir.exists():
            updates = sorted(refined_dir.glob('updated-v1.*.md'))
            if updates:
                docs.append(str(updates[-1]))
                continue
        docs.append(str(feature_file))
    return docs


def _parse_feature_registry():
    """Load or derive the feature registry from the PRD."""
    registry_path = Path('docs/.state/feature-registry.json')
    if registry_path.exists():
        with open(registry_path) as f:
            return json.load(f)

    # Derive from PRD
    prd_path = Path('docs/01-prd/prd-v1.0.md')
    if not prd_path.exists():
        return {}

    with open(prd_path) as f:
        content = f.read()

    features = [m.strip() for m in re.findall(r'###\s+Feature\s+\d+:\s+(.+)', content)]
    registry = {}
    for i, feature in enumerate(features, 1):
        feature_id = f'FEAT-{i:02d}'
        slug = feature.lower().replace(' ', '-').replace(':', '').replace(',', '')
        registry[feature_id] = {'id': feature_id, 'name': feature, 'slug': slug}

    if registry:
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
        print(f"📋 Created feature registry with {len(registry)} features", file=sys.stderr)

    return registry


# ---------------------------------------------------------------------------
# Stage checkers — return:
#   []    = nothing to do at this stage (pass through to next stage)
#   [...]  = list of runnable tasks
#   None  = hard gate, stop and wait for human
# ---------------------------------------------------------------------------

def check_stage_prd_creation():
    """Stage 1: Create PRD if it doesn't exist."""
    if Path('docs/01-prd/prd-v1.0.md').exists():
        return []
    if is_complete('prd-initial'):
        return []
    return [{
        'id': 'prd-initial',
        'agent': 'product-spec',
        'input': {'user_idea_file': 'docs/00-user-idea.md', 'iteration': 0}
    }]


def check_stage_prd_approval():
    """Stage 2: Gate — wait for human to approve PRD."""
    prd_file = Path('docs/01-prd/prd-v1.0.md')
    approval_file = Path('docs/01-prd/.approved')
    if prd_file.exists() and not approval_file.exists():
        return None  # hard gate
    return []


def check_stage_feature_breakdown():
    """Stage 3: Break each feature out of the PRD into its own doc."""
    if not Path('docs/01-prd/.approved').exists():
        return []

    registry = _parse_feature_registry()
    if not registry:
        return []

    tasks = []
    for feature_id, feature in registry.items():
        task_id = f'breakdown-{feature_id}'
        output_file = Path(f'docs/02-features/{feature_id}-{feature["slug"]}.md')
        if not is_complete(task_id) and not output_file.exists():
            tasks.append({
                'id': task_id,
                'agent': 'product-spec',
                'input': {
                    'mode': 'feature-breakdown',
                    'feature_id': feature_id,
                    'feature': feature['slug'],
                    'feature_name': feature['name'],
                    'prd_file': 'docs/01-prd/prd-v1.0.md'
                }
            })
    return tasks


def check_stage_feature_refinement():
    """Stage 4: Tech-lead/product-spec iteration loop per feature.

    Features iterate independently — all features that have a runnable next
    step are returned so they can run in parallel.
    """
    features_dir = Path('docs/02-features')
    if not features_dir.exists():
        return []

    feature_files = list(features_dir.glob('*.md'))
    if not feature_files:
        return []

    # All breakdowns must be done before refinement starts
    registry = _parse_feature_registry()
    for feature_id, feature in registry.items():
        task_id = f'breakdown-{feature_id}'
        output_file = Path(f'docs/02-features/{feature_id}-{feature["slug"]}.md')
        if not is_complete(task_id) and not output_file.exists():
            return []  # Still breaking down

    refinement_dir = Path('docs/03-refinement')
    tasks = []

    for feature_file in sorted(feature_files):
        stem = feature_file.stem
        match = re.match(r'(FEAT-\d+)-(.+)', stem)
        if not match:
            continue
        feature_id, feature_slug = match.group(1), match.group(2)
        feature_dir = refinement_dir / stem

        for iteration in range(1, MAX_REFINEMENT_ITERATIONS + 1):
            questions_file = feature_dir / f'questions-iter-{iteration}.md'
            updated_file = feature_dir / f'updated-v1.{iteration}.md'
            questions_task_id = f'questions-{feature_id}-iter-{iteration}'
            refine_task_id = f'refine-{feature_id}-iter-{iteration}'

            # --- Tech-lead step ---
            if not questions_file.exists():
                # Prerequisite: iter 1 is always ok; iter N needs previous product-spec response
                prev_updated = feature_dir / f'updated-v1.{iteration - 1}.md'
                prereq_met = (iteration == 1) or prev_updated.exists()
                if prereq_met and not is_complete(questions_task_id):
                    input_doc = str(prev_updated) if iteration > 1 else str(feature_file)
                    tasks.append({
                        'id': questions_task_id,
                        'agent': 'tech-lead',
                        'input': {
                            'feature_id': feature_id,
                            'feature': feature_slug,
                            'iteration': iteration,
                            'feature_doc': input_doc
                        }
                    })
                break  # Can't advance chain until questions are written

            # Questions file exists — check if feature is ready
            with open(questions_file) as f:
                questions_content = f.read()
            if 'READY FOR IMPLEMENTATION' in questions_content:
                break  # Feature done, nothing more to do

            # --- Product-spec step ---
            if not updated_file.exists():
                if not is_complete(refine_task_id):
                    tasks.append({
                        'id': refine_task_id,
                        'agent': 'product-spec',
                        'input': {
                            'feature_id': feature_id,
                            'feature': feature_slug,
                            'iteration': iteration,
                            'feature_doc': str(feature_file),
                            'questions_file': str(questions_file)
                        }
                    })
                break  # Wait for response before next iteration

            # updated_file exists — advance to next iteration

    return tasks


def check_stage_specs_approval():
    """Stage 5: Gate — all features refined, wait for human approval."""
    refinement_dir = Path('docs/03-refinement')
    approval_file = Path('docs/03-refinement/.approved')

    if approval_file.exists():
        return []  # Already approved

    if not refinement_dir.exists():
        return []

    # If there are still refinement tasks to run, don't gate yet
    if check_stage_feature_refinement():
        return []

    # Check all features are marked READY
    features_dir = Path('docs/02-features')
    if not features_dir.exists():
        return []

    expected = {f.stem for f in features_dir.glob('*.md')}
    if not expected:
        return []

    ready = set()
    for feature_dir in refinement_dir.iterdir():
        if not feature_dir.is_dir():
            continue
        for qf in sorted(feature_dir.glob('questions-*.md'), reverse=True):
            with open(qf) as f:
                if 'READY FOR IMPLEMENTATION' in f.read():
                    ready.add(feature_dir.name)
                    break

    if ready >= expected:
        return None  # Hard gate — all ready, waiting for human

    return []


def check_stage_foundation_analysis():
    """Stage 6: Run foundation analysis after specs are approved."""
    if not Path('docs/03-refinement/.approved').exists():
        return []
    if is_complete('foundation-analysis') or Path('docs/04-foundation/foundation-analysis.md').exists():
        return []
    return [{
        'id': 'foundation-analysis',
        'agent': 'foundation-architect',
        'input': {'feature_docs': get_latest_feature_docs()}
    }]


def check_stage_engineering_specs():
    """Stage 7: Generate engineering spec for each feature in parallel."""
    if not Path('docs/04-foundation/foundation-analysis.md').exists():
        return []

    registry = _parse_feature_registry()
    if not registry:
        return []

    feature_docs = get_latest_feature_docs()
    foundation_doc = 'docs/04-foundation/foundation-analysis.md'
    tasks = []

    for feature_id, feature in registry.items():
        task_id = f'spec-{feature_id}'
        spec_file = Path(f'docs/05-specs/{feature_id}-{feature["slug"]}-spec.md')
        if is_complete(task_id) or spec_file.exists():
            continue
        feature_doc = next(
            (d for d in feature_docs if feature_id in d),
            f'docs/02-features/{feature_id}-{feature["slug"]}.md'
        )
        tasks.append({
            'id': task_id,
            'agent': 'engineering-spec',
            'input': {
                'feature_id': feature_id,
                'feature': feature['slug'],
                'feature_doc': feature_doc,
                'foundation_doc': foundation_doc
            }
        })

    return tasks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def find_next_tasks():
    stages = [
        ('prd-creation',        check_stage_prd_creation),
        ('prd-approval-gate',   check_stage_prd_approval),
        ('feature-breakdown',   check_stage_feature_breakdown),
        ('feature-refinement',  check_stage_feature_refinement),
        ('specs-approval-gate', check_stage_specs_approval),
        ('foundation-analysis', check_stage_foundation_analysis),
        ('engineering-specs',   check_stage_engineering_specs),
    ]

    for stage_name, stage_fn in stages:
        result = stage_fn()

        if result is None:
            # Hard gate — stop everything, waiting for human
            print("has_tasks=false")
            print(f"# Waiting at gate: {stage_name}", file=sys.stderr)
            return

        if result:
            # Found runnable tasks — output for matrix
            print("has_tasks=true")
            print(f"tasks={json.dumps(result)}")
            print(f"# Stage: {stage_name} — {len(result)} task(s): {[t['id'] for t in result]}", file=sys.stderr)
            return

    print("has_tasks=false")
    print("# All stages complete or waiting for input", file=sys.stderr)


if __name__ == '__main__':
    find_next_tasks()
