# Quick Start: Getting Your Framework Running in GitHub

This guide gets you from zero to a working agentic framework in ~15 minutes.

## What You'll Do

1. Create the template repository on GitHub
2. Configure it as a template
3. Set up secrets
4. Create your first app
5. Watch agents generate your specifications

## Prerequisites

✅ GitHub account  
✅ GitHub CLI installed (`gh` command)  
✅ Anthropic API key ([get one](https://console.anthropic.com/))  
✅ This framework downloaded/cloned  

## Step-by-Step

### 1. Upload Framework to GitHub (2 minutes)

```bash
# Navigate to the framework directory
cd agentic-framework

# Initialize git if not already done
git init
git add .
git commit -m "feat: initial agentic framework"

# Create repository on GitHub
gh repo create YOUR-ORG/agentic-framework \
  --public \
  --source=. \
  --remote=origin \
  --push

# Wait for push to complete...
```

**Result**: Framework is now on GitHub at `github.com/YOUR-ORG/agentic-framework`

### 2. Mark as Template (1 minute)

```bash
# Enable template mode via GitHub CLI
gh repo edit YOUR-ORG/agentic-framework --enable-template

# Or do it manually:
# 1. Go to github.com/YOUR-ORG/agentic-framework
# 2. Click Settings
# 3. Check "Template repository"
```

**Result**: Anyone can now create repos from your template ✅

### 3. Add API Key Secret (1 minute)

```bash
# Add your Anthropic API key as a secret
gh secret set ANTHROPIC_API_KEY \
  --repo YOUR-ORG/agentic-framework

# When prompted, paste your API key
```

**Result**: Workflows can now call Claude ✅

### 4. Test the Template (Optional, 3 minutes)

Before using it for real, test it works:

```bash
# Create a test app from your template
gh repo create YOUR-ORG/test-app \
  --template YOUR-ORG/agentic-framework \
  --private \
  --clone

cd test-app

# Set API key for this repo too
gh secret set ANTHROPIC_API_KEY
# (paste your key)

# Initialize a simple project
./scripts/init-project.sh "A simple note-taking app"

# Check what was created
cat docs/00-user-idea.md
cat docs/.state/pending-tasks.json

# Commit and push to trigger workflow
git add .
git commit -m "feat: initialize test project"
git push

# Watch the workflow
gh run watch
```

**What should happen**:
1. Workflow starts automatically
2. Calls Product Manager agent
3. Creates `docs/01-prd/prd-v1.0.md`
4. Commits it back to the repo
5. Triggers again (loop continues)

**Check progress**:
```bash
# Pull latest changes
git pull

# See the PRD
cat docs/01-prd/prd-v1.0.md

# Check state
cat docs/.state/completed-tasks.json
```

### 5. Create Your Real App (2 minutes)

Now that it works, create your actual application:

```bash
cd ..  # Back out of test-app

# Create your real app
gh repo create YOUR-ORG/my-awesome-app \
  --template YOUR-ORG/agentic-framework \
  --private \
  --clone

cd my-awesome-app

# Set API key
gh secret set ANTHROPIC_API_KEY

# Initialize with your real idea
./scripts/init-project.sh "AI-powered task management with smart prioritization and team collaboration"

# Optionally, edit docs/00-user-idea.md to add more detail
vim docs/00-user-idea.md

# Commit and push
git add .
git commit -m "feat: initialize my-awesome-app"
git push

# Watch it run
gh run watch
```

### 6. Monitor Progress (Ongoing)

Watch the agents work:

```bash
# View workflow runs
gh run list

# Watch current run
gh run watch

# View logs of latest run
gh run view --log

# Pull latest generated docs
git pull

# See what's been created
ls -R docs/
```

### 7. Review Generated Specs

After workflows complete:

```bash
# Pull everything
git pull

# Review the PRD
cat docs/01-prd/prd-v1.0.md

# Review feature refinements
ls docs/02-refinement/

# Review engineering specs
ls docs/04-specs/
```

## Troubleshooting

### Workflow Doesn't Start

**Check**:
```bash
# Is the secret set?
gh secret list

# Are there pending tasks?
cat docs/.state/pending-tasks.json

# Try manual trigger
gh workflow run orchestrator.yml
```

### Workflow Fails

**View logs**:
```bash
gh run view --log
```

**Common issues**:
- Invalid API key → Check `gh secret list`
- No tasks → Check `pending-tasks.json` has tasks
- Python error → Check scripts have execute permissions

**Fix permissions**:
```bash
chmod +x scripts/*.sh scripts/*.py
git add scripts/
git commit -m "fix: make scripts executable"
git push
```

### Agents Produce Poor Output

**Improve prompts**:
```bash
# Edit agent prompt
vim agents/product-manager/prompt.md

# Add more examples or constraints
git add agents/
git commit -m "improve: better product manager prompts"
git push
```

## What Happens Next?

After initialization, the workflow will:

1. ✅ **Create PRD** (Product Manager agent)
2. 🔄 **Refine features** (Tech Lead ↔ Product Owner loop)
   - Asks questions
   - Gets answers  
   - Iterates until "READY"
3. 🏗️ **Analyze foundation** (Foundation Architect)
4. 📋 **Generate specs** (Engineering Spec agent)
5. ⏸️ **Wait for implementation setup**

The workflow continues automatically until all planning is complete.

## Next: Implementation Phase

Once specs are done, set up implementation:

1. Review specs in `docs/04-specs/`
2. Integrate Claude Code or similar
3. Let agents implement from specs
4. Review and merge PRs

See `claude.md` for implementation agent instructions.

## Customization

Before creating many apps, customize:

### Tech Stack
```bash
vim context/tech-stack-standards.md
# Update to your preferred stack
```

### Agent Behavior
```bash
vim agents/product-manager/prompt.md
# Adjust tone, detail level, etc.
```

### Workflow Triggers
```bash
vim .github/workflows/orchestrator.yml
# Adjust when workflow runs
```

## Commands Cheat Sheet

```bash
# Create template repo
gh repo create ORG/agentic-framework --public --source=. --push
gh repo edit ORG/agentic-framework --enable-template

# Create app from template
gh repo create ORG/my-app --template ORG/agentic-framework --private --clone
cd my-app
gh secret set ANTHROPIC_API_KEY

# Initialize project
./scripts/init-project.sh "Your app idea"
git add . && git commit -m "init" && git push

# Monitor
gh run watch
git pull
cat docs/.state/current-phase.json

# Trigger manually
gh workflow run orchestrator.yml
```

## Success Criteria

✅ Template repo exists and is marked as template  
✅ Secrets are configured  
✅ Test app runs workflow successfully  
✅ PRD gets generated in `docs/01-prd/`  
✅ State files update automatically  
✅ Commits appear from "Agentic Bot"  

If all ✅, you're good to go! 🎉

## Getting Help

- Check workflow logs: `gh run view --log`
- Check state files: `cat docs/.state/*.json`
- Test scripts locally: `python scripts/find-next-task.py`
- Review SETUP.md for detailed troubleshooting

---

**Time to first PRD**: ~5-10 minutes after push (depending on API response time)

**Time to complete all planning**: Varies by complexity (simple app: 30 min, complex app: 2-3 hours)
