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
        # Need to create PRD
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

def check_stage_feature_extraction():
    """Stage 3: PRD approved but features not extracted?"""
    approval_file = Path('docs/01-prd/.approved')
    
    if not approval_file.exists():
        return None  # Not at this stage yet
    
    # Check if features have been extracted (tech-lead tasks exist or completed)
    features_extracted = False
    
    # Check pending tasks for tech-lead questions
    if Path('docs/.state/pending-tasks.json').exists():
        with open('docs/.state/pending-tasks.json') as f:
            pending = json.load(f)
            if any('questions-' in t['id'] for t in pending.get('tasks', [])):
                features_extracted = True
    
    # Check completed tasks for tech-lead questions
    if Path('docs/.state/completed-tasks.json').exists():
        with open('docs/.state/completed-tasks.json') as f:
            completed = json.load(f)
            if any('questions-' in t['id'] for t in completed.get('tasks', [])):
                features_extracted = True
    
    # Check if refinement directory exists with content
    refinement_dir = Path('docs/02-refinement')
    if refinement_dir.exists() and list(refinement_dir.iterdir()):
        features_extracted = True
    
    if not features_extracted:
        # Extract features NOW (not as a task)
        print("📋 Extracting features from approved PRD...", file=sys.stderr)
        extract_and_create_tasks()
        
        # Now return the first tech-lead task
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
    
    return None

def extract_and_create_tasks():
    """Extract features from PRD and create tech-lead tasks."""
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
    
    # Create tech-lead tasks
    tasks = []
    for i, feature in enumerate(features, 1):
        feature_slug = feature.lower().replace(' ', '-').replace(':', '')
        tasks.append({
            'id': f'questions-{feature_slug}-iter-1',
            'agent': 'tech-lead',
            'input': {
                'feature': feature_slug,
                'iteration': 1,
                'prd_file': prd_path
            },
            'dependencies': [],
            'priority': i
        })
        print(f"  - {feature}", file=sys.stderr)
    
    # Save to pending
    with open('docs/.state/pending-tasks.json', 'w') as f:
        json.dump({'tasks': tasks}, f, indent=2)
    
    print(f"✅ Created {len(tasks)} tech-lead tasks", file=sys.stderr)

def check_stage_feature_refinement():
    """Stage 4: Features being refined - any pending tasks?"""
    
    if not Path('docs/.state/pending-tasks.json').exists():
        return None
    
    with open('docs/.state/pending-tasks.json') as f:
        pending = json.load(f)
    
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
        check_stage_feature_extraction,
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
