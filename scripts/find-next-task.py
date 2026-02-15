#!/usr/bin/env python3
"""
Find the next runnable task from pending-tasks.json
"""
import json
import sys
from pathlib import Path

def find_next_task():
    """Find the next task where all dependencies are met."""
    
    pending_file = Path('docs/.state/pending-tasks.json')
    completed_file = Path('docs/.state/completed-tasks.json')
    
    if not pending_file.exists():
        print("has_task=false")
        return
    
    with open(pending_file) as f:
        pending = json.load(f)
    
    with open(completed_file) as f:
        completed = json.load(f)
        completed_ids = {t['id'] for t in completed.get('tasks', [])}
    
    # Find first runnable task (all dependencies complete)
    for task in sorted(pending.get('tasks', []), key=lambda x: x.get('priority', 99)):
        deps_met = all(dep in completed_ids for dep in task.get('dependencies', []))
        
        if deps_met:
            print("has_task=true")
            print(f"task_id={task['id']}")
            print(f"agent={task['agent']}")
            print(f"task_type={task.get('type', 'planning')}")
            return
    
    print("has_task=false")

if __name__ == '__main__':
    find_next_task()
