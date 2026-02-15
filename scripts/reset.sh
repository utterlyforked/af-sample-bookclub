#!/bin/bash
echo "🧹 Resetting to clean state..."
rm -rf docs/0* docs/01-* docs/02-* docs/03-* docs/04-* docs/05-*
echo '{"tasks": []}' > docs/.state/pending-tasks.json
echo '{"tasks": []}' > docs/.state/completed-tasks.json
rm -f docs/.state/feature-registry.json
echo "✅ Ready for init-project.sh"
