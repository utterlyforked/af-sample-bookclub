#!/bin/bash
set -e

# Initialize a new project from the template

if [ -z "$1" ]; then
    echo "Usage: ./scripts/init-project.sh \"Your app idea description\""
    exit 1
fi

USER_IDEA="$1"

echo "🚀 Initializing new project..."

# Create user idea document
mkdir -p docs
cat > docs/00-user-idea.md << EOF
# User Idea

**Created**: $(date -u +"%Y-%m-%d")

## Description

$USER_IDEA

## Goals

[What are you trying to achieve with this application?]

## Target Users

[Who will use this application?]

## Key Features (Initial Thoughts)

[What are the main capabilities you envision?]
EOF

echo "📝 Created docs/00-user-idea.md"

# Initialize state files
mkdir -p docs/.state

# Create initial pending task (run product-spec)
cat > docs/.state/pending-tasks.json << EOF
{
  "tasks": [
    {
      "id": "prd-initial",
      "agent": "product-spec",
      "type": "planning",
      "input": {
        "user_idea_file": "docs/00-user-idea.md",
        "iteration": 0
      },
      "dependencies": [],
      "priority": 1,
      "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    }
  ]
}
EOF

# Create empty completed tasks
cat > docs/.state/completed-tasks.json << 'EOF'
{
  "tasks": []
}
EOF

# Create current phase
cat > docs/.state/current-phase.json << EOF
{
  "phase": "initialization",
  "waiting_for": "product-manager",
  "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

echo "✅ State files initialized"

# Create placeholder directories
mkdir -p docs/{01-prd,02-refinement,03-foundation,04-specs}

echo ""
echo "✨ Project initialized!"
echo ""
echo "Next steps:"
echo "  1. Review docs/00-user-idea.md and add more detail if desired"
echo "  2. git add ."
echo "  3. git commit -m 'feat: initialize project'"
echo "  4. git push"
echo ""
echo "The orchestrator will then:"
echo "  - Run the Product Specification agent to create your PRD"
echo "  - Begin feature refinement iterations"
echo "  - Generate engineering specifications"
echo ""
echo "Check the Actions tab in GitHub to watch progress!"
