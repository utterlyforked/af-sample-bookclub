#!/usr/bin/env python3
"""
Find the next task based on current state (stage-based, idempotent)
"""
import json
import sys
import os
from pathlib import Path

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
    
    # Check if features have been broken down (feature docs exist)
    features_dir = Path('docs/02-features')
    
    if features_dir.exists() and list(features_dir.glob('*.md')):
        # Features already broken down
        return None
    
    # Need to break down features
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

def check_stage_foundation_analysis():
    """Stage 5: All features refined, need foundation analysis?"""
    
    # Check if all features are marked as READY
    refinement_dir = Path('docs/02-refinement')
    
    if not refinement_dir.exists():
        return None
    
    # Look for features that are ready
    ready_features = []
    for feature_dir in refinement_dir.iterdir():
        if not feature_dir.is_dir():
            continue
        
        # Check if any questions file contains "READY FOR IMPLEMENTATION"
        for questions_file in feature_dir.glob('questions-*.md'):
            with open(questions_file) as f:
                if 'READY FOR IMPLEMENTATION' in f.read():
                    ready_features.append(feature_dir.name)
                    break
    
    # If we have ready features but no foundation analysis
    foundation_file = Path('docs/03-foundation/foundation-analysis.md')
    
    if ready_features and not foundation_file.exists():
        return {
            'has_task': True,
            'task_id': 'foundation-analysis',
            'agent': 'foundation-architect',
            'stage': 'foundation-analysis'
        }
    
    return None

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
        check_stage_foundation_analysis,
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
