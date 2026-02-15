#!/usr/bin/env python3
"""
Find the next task based on current state (stage-based, idempotent)
"""
import json
import sys
import os
from pathlib import Path

def get_latest_feature_docs():
    """Return the most up-to-date doc path for each feature.

    Prefers the latest refined version in docs/03-refinement/ over the
    initial breakdown in docs/02-features/.
    """
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


def check_stage_prd_creation():
    """Stage 1: Do we need to create the PRD?"""
    prd_file = Path('docs/01-prd/prd-v1.0.md')
    
    if not prd_file.exists():
        # Need to create PRD - add task to pending
        task = {
            'id': 'prd-initial',
            'agent': 'product-spec',
            'input': {
                'user_idea_file': 'docs/00-user-idea.md',
                'iteration': 0
            },
            'dependencies': [],
            'priority': 1
        }
        
        # Write to pending
        with open('docs/.state/pending-tasks.json', 'w') as f:
            json.dump({'tasks': [task]}, f, indent=2)
        
        return {
            'has_task': True,
            'task_id': 'prd-initial',
            'agent': 'product-spec',
            'stage': 'prd-creation'
        }
    
    return None

def check_stage_prd_approval():
    """Stage 2: PRD exists but needs approval?"""
    prd_file = Path('docs/01-prd/prd-v1.0.md')
    approval_file = Path('docs/01-prd/.approved')
    
    if prd_file.exists() and not approval_file.exists():
        # Waiting for human approval
        return {
            'has_task': False,
            'reason': 'waiting-for-prd-approval',
            'stage': 'prd-approval-gate'
        }
    
    return None

def check_stage_feature_breakdown():
    """Stage 3: PRD approved but features not broken down into separate docs?"""
    approval_file = Path('docs/01-prd/.approved')
    
    if not approval_file.exists():
        return None  # Not at this stage yet
    
    # Check if there are still pending breakdown tasks (partial progress case)
    pending_path = Path('docs/.state/pending-tasks.json')
    if pending_path.exists():
        with open(pending_path) as f:
            pending = json.load(f)
        breakdown_tasks = [t for t in pending.get('tasks', []) if t['id'].startswith('breakdown-')]
        if breakdown_tasks:
            first_task = breakdown_tasks[0]
            return {
                'has_task': True,
                'task_id': first_task['id'],
                'agent': first_task['agent'],
                'stage': 'feature-breakdown'
            }

    # Check if features have been broken down (feature docs exist)
    features_dir = Path('docs/02-features')

    if features_dir.exists() and list(features_dir.glob('*.md')):
        # All breakdown tasks done and feature docs exist — move on
        return None

    # Need to break down features — create the tasks
    print("📋 Breaking down PRD into individual feature documents...", file=sys.stderr)
    create_feature_breakdown_tasks()

    # Return the first feature breakdown task
    with open('docs/.state/pending-tasks.json') as f:
        pending = json.load(f)
        if pending.get('tasks'):
            first_task = pending['tasks'][0]
            return {
                'has_task': True,
                'task_id': first_task['id'],
                'agent': first_task['agent'],
                'stage': 'feature-breakdown'
            }

    return None

def create_feature_breakdown_tasks():
    """Extract features from PRD and create product-spec breakdown tasks."""
    import re
    
    prd_path = 'docs/01-prd/prd-v1.0.md'
    
    # Extract features
    with open(prd_path, 'r') as f:
        content = f.read()
    
    pattern = r'###\s+Feature\s+\d+:\s+(.+)'
    matches = re.findall(pattern, content)
    
    features = [match.strip() for match in matches]
    
    if not features:
        print("⚠️  No features found in PRD", file=sys.stderr)
        return
    
    print(f"📋 Found {len(features)} features", file=sys.stderr)
    
    # Create feature registry
    feature_registry = {}
    tasks = []
    
    for i, feature in enumerate(features, 1):
        feature_id = f"FEAT-{i:02d}"  # FEAT-01, FEAT-02, etc.
        feature_slug = feature.lower().replace(' ', '-').replace(':', '').replace(',', '')
        
        # Store in registry
        feature_registry[feature_id] = {
            'id': feature_id,
            'name': feature,
            'slug': feature_slug
        }
        
        tasks.append({
            'id': f'breakdown-{feature_id}',
            'agent': 'product-spec',
            'input': {
                'mode': 'feature-breakdown',
                'feature_id': feature_id,
                'feature': feature_slug,
                'feature_name': feature,
                'prd_file': prd_path
            },
            'dependencies': [],
            'priority': i
        })
        print(f"  - {feature_id}: {feature}", file=sys.stderr)
    
    # Save feature registry
    registry_path = Path('docs/.state/feature-registry.json')
    with open(registry_path, 'w') as f:
        json.dump(feature_registry, f, indent=2)
    
    # Save to pending
    with open('docs/.state/pending-tasks.json', 'w') as f:
        json.dump({'tasks': tasks}, f, indent=2)
    
    print(f"✅ Created {len(tasks)} feature breakdown tasks", file=sys.stderr)
    print(f"✅ Feature registry saved to {registry_path}", file=sys.stderr)

def check_stage_feature_refinement():
    """Stage 4: All features broken down, start refinement loops."""
    
    features_dir = Path('docs/02-features')
    
    # Check if we have feature docs
    if not features_dir.exists() or not list(features_dir.glob('*.md')):
        return None  # No features broken down yet
    
    # Count how many features we have
    feature_files = list(features_dir.glob('*.md'))
    
    # Check if ALL breakdown tasks are complete (no pending breakdown tasks)
    if Path('docs/.state/pending-tasks.json').exists():
        with open('docs/.state/pending-tasks.json') as f:
            pending = json.load(f)
            # If there are still breakdown tasks pending, wait
            if any(t['id'].startswith('breakdown-') for t in pending.get('tasks', [])):
                return None  # Still breaking down features
    
    # All features broken down! Check if we've created tech-lead tasks yet
    refinement_started = False
    
    if Path('docs/.state/pending-tasks.json').exists():
        with open('docs/.state/pending-tasks.json') as f:
            pending = json.load(f)
            if any(t['agent'] == 'tech-lead' for t in pending.get('tasks', [])):
                refinement_started = True
    
    if Path('docs/.state/completed-tasks.json').exists():
        with open('docs/.state/completed-tasks.json') as f:
            completed = json.load(f)
            if any(t['agent'] == 'tech-lead' for t in completed.get('tasks', [])):
                refinement_started = True
    
    # If refinement hasn't started, create tech-lead tasks for ALL features
    if not refinement_started:
        print("📋 All features broken down. Creating tech-lead review tasks...", file=sys.stderr)
        create_tech_lead_tasks()
        
        # Return first tech-lead task
        with open('docs/.state/pending-tasks.json') as f:
            pending = json.load(f)
            if pending.get('tasks'):
                first_task = pending['tasks'][0]
                return {
                    'has_task': True,
                    'task_id': first_task['id'],
                    'agent': first_task['agent'],
                    'stage': 'feature-refinement'
                }
    
    # Refinement in progress - check for pending tasks
    if Path('docs/.state/pending-tasks.json').exists():
        with open('docs/.state/pending-tasks.json') as f:
            pending = json.load(f)
    else:
        return None
    
    if not pending.get('tasks'):
        return None  # No pending tasks
    
    # Check if dependencies are met
    if Path('docs/.state/completed-tasks.json').exists():
        with open('docs/.state/completed-tasks.json') as f:
            completed = json.load(f)
            completed_ids = {t['id'] for t in completed.get('tasks', [])}
    else:
        completed_ids = set()
    
    # Find first runnable task (dependencies met)
    for task in sorted(pending.get('tasks', []), key=lambda x: x.get('priority', 99)):
        deps_met = all(dep in completed_ids for dep in task.get('dependencies', []))
        
        if deps_met:
            return {
                'has_task': True,
                'task_id': task['id'],
                'agent': task['agent'],
                'stage': 'feature-refinement'
            }
    
    return None

def create_tech_lead_tasks():
    """Create tech-lead review tasks for all feature docs."""
    features_dir = Path('docs/02-features')
    feature_files = list(features_dir.glob('*.md'))
    
    # Load feature registry
    registry_path = Path('docs/.state/feature-registry.json')
    if registry_path.exists():
        with open(registry_path) as f:
            registry = json.load(f)
    else:
        registry = {}
    
    tasks = []
    for i, feature_file in enumerate(sorted(feature_files), 1):
        # Parse filename: FEAT-01-book-suggestions.md
        filename = feature_file.stem
        
        # Extract feature ID (FEAT-XX)
        import re
        match = re.match(r'(FEAT-\d+)-(.+)', filename)
        if match:
            feature_id = match.group(1)
            feature_slug = match.group(2)
        else:
            # Fallback if no ID in filename
            feature_id = f'FEAT-{i:02d}'
            feature_slug = filename
        
        tasks.append({
            'id': f'questions-{feature_id}-iter-1',
            'agent': 'tech-lead',
            'input': {
                'feature_id': feature_id,
                'feature': feature_slug,
                'iteration': 1,
                'feature_doc': str(feature_file)
            },
            'dependencies': [],
            'priority': i
        })
        print(f"  - Creating tech-lead task for {feature_id}: {feature_slug}", file=sys.stderr)
    
    # Save to pending
    with open('docs/.state/pending-tasks.json', 'w') as f:
        json.dump({'tasks': tasks}, f, indent=2)
    
    print(f"✅ Created {len(tasks)} tech-lead review tasks", file=sys.stderr)

def check_stage_specs_approval():
    """Stage 5: All features refined — wait for human to review and approve before foundation."""
    refinement_dir = Path('docs/03-refinement')
    approval_file = Path('docs/03-refinement/.approved')

    # Already approved — move on
    if approval_file.exists():
        return None

    # Not at this stage yet if refinement hasn't started
    if not refinement_dir.exists():
        return None

    # Check if there are still pending refinement/questions tasks — not done yet
    if Path('docs/.state/pending-tasks.json').exists():
        with open('docs/.state/pending-tasks.json') as f:
            pending = json.load(f)
        if any(
            t['id'].startswith('questions-') or t['id'].startswith('refine-')
            for t in pending.get('tasks', [])
        ):
            return None  # Refinement still in progress

    # Check if ALL features are marked READY FOR IMPLEMENTATION
    features_dir = Path('docs/02-features')
    if not features_dir.exists():
        return None

    expected_features = {f.stem for f in features_dir.glob('*.md')}
    if not expected_features:
        return None

    ready_features = set()
    for feature_dir in refinement_dir.iterdir():
        if not feature_dir.is_dir():
            continue
        for questions_file in sorted(feature_dir.glob('questions-*.md'), reverse=True):
            with open(questions_file) as f:
                if 'READY FOR IMPLEMENTATION' in f.read():
                    ready_features.add(feature_dir.name)
                    break

    if ready_features >= expected_features:
        # All features ready — pause for human review
        return {
            'has_task': False,
            'reason': 'waiting-for-specs-approval',
            'stage': 'specs-approval-gate'
        }

    return None


def check_stage_foundation_analysis():
    """Stage 6: Specs approved by human, run foundation analysis."""
    approval_file = Path('docs/03-refinement/.approved')

    if not approval_file.exists():
        return None

    foundation_file = Path('docs/04-foundation/foundation-analysis.md')

    if foundation_file.exists():
        return None

    task = {
        'id': 'foundation-analysis',
        'agent': 'foundation-architect',
        'input': {
            'feature_docs': get_latest_feature_docs()
        },
        'dependencies': [],
        'priority': 1
    }
    with open('docs/.state/pending-tasks.json', 'w') as f:
        json.dump({'tasks': [task]}, f, indent=2)

    return {
        'has_task': True,
        'task_id': 'foundation-analysis',
        'agent': 'foundation-architect',
        'stage': 'foundation-analysis'
    }

def check_stage_engineering_specs():
    """Stage 7: Foundation done, generate engineering specs for each feature."""
    foundation_file = Path('docs/04-foundation/foundation-analysis.md')

    if not foundation_file.exists():
        return None

    # Return any spec tasks already in the pending queue
    if Path('docs/.state/pending-tasks.json').exists():
        with open('docs/.state/pending-tasks.json') as f:
            pending = json.load(f)
        spec_tasks = [t for t in pending.get('tasks', []) if t['id'].startswith('spec-')]
        if spec_tasks:
            first = spec_tasks[0]
            return {
                'has_task': True,
                'task_id': first['id'],
                'agent': first['agent'],
                'stage': 'engineering-specs'
            }

    # Idempotent fallback: rebuild missing spec tasks from registry
    registry_path = Path('docs/.state/feature-registry.json')
    if not registry_path.exists():
        return None

    with open(registry_path) as f:
        registry = json.load(f)

    specs_dir = Path('docs/05-specs')
    feature_docs = get_latest_feature_docs()
    missing = []

    for i, (feature_id, feature) in enumerate(registry.items(), 1):
        if (specs_dir / f"{feature_id}-{feature['slug']}-spec.md").exists():
            continue
        feature_doc = next(
            (d for d in feature_docs if feature_id in d),
            f"docs/02-features/{feature_id}-{feature['slug']}.md"
        )
        missing.append({
            'id': f'spec-{feature_id}',
            'agent': 'engineering-spec',
            'input': {
                'feature_id': feature_id,
                'feature': feature['slug'],
                'feature_doc': feature_doc,
                'foundation_doc': str(foundation_file)
            },
            'dependencies': [],
            'priority': i
        })

    if not missing:
        return None

    with open('docs/.state/pending-tasks.json', 'w') as f:
        json.dump({'tasks': missing}, f, indent=2)

    return {
        'has_task': True,
        'task_id': missing[0]['id'],
        'agent': missing[0]['agent'],
        'stage': 'engineering-specs'
    }


def find_next_task():
    """
    Stage-based task finder (idempotent).
    
    Checks what EXISTS, not what happened before.
    Can be run repeatedly with same result.
    """
    
    # Check each stage in order
    stages = [
        check_stage_prd_creation,
        check_stage_prd_approval,
        check_stage_feature_breakdown,
        check_stage_feature_refinement,
        check_stage_specs_approval,
        check_stage_foundation_analysis,
        check_stage_engineering_specs,
    ]
    
    for stage_check in stages:
        result = stage_check()
        if result:
            # Found something to do (or a gate to wait at)
            if result.get('has_task'):
                print(f"has_task=true")
                print(f"task_id={result['task_id']}")
                print(f"agent={result['agent']}")
                print(f"task_type=planning")
                
                # Debug info (not consumed by workflow)
                print(f"# Stage: {result['stage']}", file=sys.stderr)
            else:
                # At a gate, waiting for human
                print(f"has_task=false")
                print(f"# {result['reason']}: {result['stage']}", file=sys.stderr)
            
            return
    
    # No tasks found, we're done or waiting
    print("has_task=false")
    print("# All stages complete or waiting for input", file=sys.stderr)

if __name__ == '__main__':
    find_next_task()
