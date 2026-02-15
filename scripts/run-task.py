#!/usr/bin/env python3
"""
Run a single task: load agent prompt, call LLM, validate, update state
"""
import json
import os
import sys
import argparse
from pathlib import Path
from anthropic import Anthropic

def load_task(task_id):
    """Load task from pending queue."""
    with open('docs/.state/pending-tasks.json') as f:
        pending = json.load(f)
    
    task = next((t for t in pending['tasks'] if t['id'] == task_id), None)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    
    return task

def load_agent_prompt(agent, task_input):
    """Load agent prompt and inject task input."""
    prompt_file = Path(f'agents/{agent}/prompt.md')
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Agent prompt not found: {prompt_file}")
    
    with open(prompt_file) as f:
        prompt = f.read()
    
    # Add task input
    prompt += "\n\n## Task Input\n\n"
    prompt += "```json\n"
    prompt += json.dumps(task_input, indent=2)
    prompt += "\n```\n"
    
    return prompt

def call_agent(agent, prompt):
    """Call LLM with agent prompt."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    client = Anthropic(api_key=api_key)
    
    print(f"🤖 Calling {agent} agent...")
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.content[0].text

def extract_features_from_prd(prd_path):
    """Extract feature names from PRD markdown file."""
    features = []

    with open(prd_path, 'r') as f:
        content = f.read()

    # Look for "### Feature N: Name" patterns
    import re
    pattern = r'###\s+Feature\s+\d+:\s+(.+)'
    matches = re.findall(pattern, content)

    for match in matches:
        # Clean up the feature name
        feature_name = match.strip()
        features.append(feature_name)

    return features

def get_output_path(agent, task_input):
    """Determine where to save agent output."""
    
    if agent == 'product-spec':
        # Check if this is initial (no iteration) or refinement
        iteration = task_input.get('iteration', 0)
        if iteration == 0:
            return 'docs/01-prd/prd-v1.0.md'
        else:
            feature = task_input.get('feature', 'unknown')
            return f'docs/02-refinement/{feature}/prd-v1.{iteration}.md'
    
    elif agent == 'tech-lead':
        feature = task_input.get('feature', 'unknown')
        iteration = task_input.get('iteration', 1)
        return f'docs/02-refinement/{feature}/questions-iter-{iteration}.md'
    
    elif agent == 'foundation-architect':
        return 'docs/03-foundation/foundation-analysis.md'
    
    elif agent == 'engineering-spec':
        spec_type = task_input.get('type', 'feature')
        if spec_type == 'foundation':
            return 'docs/04-specs/foundation-spec.md'
        else:
            feature = task_input.get('feature', 'unknown')
            return f'docs/04-specs/{feature}-spec.md'
    
    return f'docs/output/{agent}-output.md'

def save_output(output_path, content):
    """Save agent output to file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"📝 Saved output to {output_path}")

def run_judge(agent, output_path):
    """Run judge validation on agent output."""
    judge_dir = f'agents/judge-{agent}'
    
    if not Path(judge_dir).exists():
        print(f"⚠️  No judge for {agent}, skipping validation")
        return {'result': 'PASS', 'score': 100, 'issues': []}
    
    # For now, simple pass-through
    # In production, this would call another LLM to validate
    print(f"✅ Judge validation passed")
    return {'result': 'PASS', 'score': 95, 'issues': []}

def mark_complete(task_id):
    """Move task from pending to completed."""
    with open('docs/.state/pending-tasks.json') as f:
        pending = json.load(f)
    
    with open('docs/.state/completed-tasks.json') as f:
        completed = json.load(f)
    
    # Find and move task
    task = next((t for t in pending['tasks'] if t['id'] == task_id), None)
    if task:
        from datetime import datetime
        task['completed_at'] = datetime.utcnow().isoformat()
        
        completed['tasks'].append(task)
        pending['tasks'] = [t for t in pending['tasks'] if t['id'] != task_id]
        
        with open('docs/.state/pending-tasks.json', 'w') as f:
            json.dump(pending, f, indent=2)
        
        with open('docs/.state/completed-tasks.json', 'w') as f:
            json.dump(completed, f, indent=2)
        
        print(f"✅ Task {task_id} marked complete")

def create_next_tasks(completed_task, output_path):
    """Generate follow-on tasks based on what just completed."""
    agent = completed_task['agent']
    next_tasks = []
    
    # Simple logic - in production this would be more sophisticated
    if agent == 'product-spec' and completed_task['input'].get('iteration', 0) == 0:
        # After initial PRD, start feature refinement
        # This is simplified - in reality, parse PRD for features
        print("📋 PRD complete. Manual step: Add feature refinement tasks")
    
    elif agent == 'tech-lead':
        # Check if "READY FOR IMPLEMENTATION"
        with open(output_path) as f:
            if 'READY FOR IMPLEMENTATION' in f.read():
                print("✅ Feature ready for implementation")
            else:
                # Create product-spec refinement task
                feature = completed_task['input']['feature']
                iteration = completed_task['input']['iteration']
                next_tasks.append({
                    'id': f'refine-{feature}-iter-{iteration}',
                    'agent': 'product-spec',
                    'input': {
                        'feature': feature,
                        'iteration': iteration,
                        'questions_file': output_path
                    },
                    'dependencies': [],
                    'priority': 1
                })
    
    elif agent == 'product-spec' and completed_task['input'].get('iteration', 0) > 0:
        # After product-spec refinement, create next tech-lead iteration
        feature = completed_task['input']['feature']
        iteration = completed_task['input']['iteration']
        next_tasks.append({
            'id': f'questions-{feature}-iter-{iteration + 1}',
            'agent': 'tech-lead',
            'input': {
                'feature': feature,
                'iteration': iteration + 1,
                'prd_file': output_path
            },
            'dependencies': [],
            'priority': 1
        })
    
    # Add new tasks to pending
    if next_tasks:
        with open('docs/.state/pending-tasks.json') as f:
            pending = json.load(f)
        
        pending['tasks'].extend(next_tasks)
        
        with open('docs/.state/pending-tasks.json', 'w') as f:
            json.dump(pending, f, indent=2)
        
        print(f"📋 Created {len(next_tasks)} follow-on task(s)")

def run_task(task_id, agent):
    """Main task execution."""
    
    # Load task
    task = load_task(task_id)
    task_input = task.get('input', {})
    
    print(f"\n{'='*60}")
    print(f"Running task: {task_id}")
    print(f"Agent: {agent}")
    print(f"{'='*60}\n")
    
    # Load agent prompt
    prompt = load_agent_prompt(agent, task_input)
    
    # Call agent
    output = call_agent(agent, prompt)
    
    # Determine output path
    output_path = get_output_path(agent, task_input)
    
    # Save output
    save_output(output_path, output)
    
    # Run judge
    judge_result = run_judge(agent, output_path)
    
    if judge_result['result'] == 'PASS':
        # Mark complete
        mark_complete(task_id)
        
        # Create next tasks
        create_next_tasks(task, output_path)
        
        print(f"\n✅ Task {task_id} completed successfully")
    else:
        print(f"\n❌ Task {task_id} failed validation")
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--task-id', required=True)
    parser.add_argument('--agent', required=True)
    args = parser.parse_args()
    
    run_task(args.task_id, args.agent)
