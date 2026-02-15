# Agentic Development Framework

**Software development in the LLM era: From idea to production with agent-driven planning and implementation.**

## What This Is

A template repository that orchestrates LLM agents to:
1. **Plan** your application (PRD → refinement → specs)
2. **Implement** your application (specs → code)
3. **Evolve** your application (new features, breaking changes)

All artifacts live in Git. All workflows are automated. Humans review and approve at key gates.

## Quick Start

### 1. Use This Template

```bash
# Create your app from this template
gh repo create my-org/my-app --template my-org/agentic-framework --private

cd my-app
```

### 2. Configure Secrets

In GitHub Settings → Secrets and variables → Actions, add:

```
ANTHROPIC_API_KEY=your-api-key-here
```

### 3. Initialize Your Project

```bash
# Initialize with your app idea
./scripts/init-project.sh "Task management app with AI prioritization"

git add .
git commit -m "feat: initialize project"
git push
```

### 4. Watch It Run

The orchestrator will automatically:
- Run Product Manager agent → creates PRD
- Run Tech Lead agent → asks questions per feature
- Run Product Owner agent → answers questions
- Loop until features are refined
- Run Foundation Architect → analyzes common elements
- Run Engineering Spec agent → creates implementation specs
- Create feature branches → Claude Code implements
- Create PRs for your review

Check the Actions tab in GitHub to watch progress.

## What You'll Get

After the workflow completes:

```
my-app/
├── docs/
│   ├── .state/                  # Orchestration state
│   ├── 01-prd/                  # Product requirements
│   ├── 02-refinement/           # Q&A iterations
│   ├── 03-foundation/           # Architecture analysis
│   └── 04-specs/                # Engineering specs
│
└── src/                         # Implemented code
    ├── API/
    ├── Web/
    └── Tests/
```

Everything traced back to decisions in Git history.

## Customization

Before using, customize for your organization:

### Tech Stack

Edit `context/tech-stack-standards.md` to match your preferred:
- Backend framework
- Frontend framework
- Database
- Testing tools
- Deployment platform

### Agent Prompts

Optionally customize agent behaviors in `agents/*/prompt.md`:
- Product Manager tone
- Tech Lead question style
- Engineering Spec detail level

## How It Works

See [INTRODUCTION.md](./INTRODUCTION.md) for the full story.

**Short version:**

1. **State machine** (`docs/.state/*.json`) tracks what needs to happen
2. **Orchestrator** (`scripts/orchestrate.py`) finds next task and runs it
3. **Agents** (`agents/*/`) generate artifacts (PRD, questions, specs, code)
4. **Judges** (`agents/judge-*/`) validate quality before human review
5. **GitHub Actions** (`.github/workflows/`) automates it all

Humans review at strategic decision points. Agents handle iteration and implementation.

## Evolution

Three months later, add a new feature:

```bash
./scripts/init-feature.sh "reading-calendar" \
  --description "Calendar view of meetings and deadlines"

git add docs/.state/
git commit -m "feat: request reading calendar feature"
git push
```

Agents analyze existing specs, refine the new feature, generate specs, and implement—with full context of your existing application.

## Requirements

- GitHub repository
- Anthropic API key (for Claude)
- Python 3.9+
- Git

## Directory Structure

```
agentic-framework/
├── .github/
│   └── workflows/
│       └── orchestrator.yml          # Main automation
│
├── agents/
│   ├── product-manager/
│   ├── tech-lead/
│   ├── product-owner/
│   ├── foundation-architect/
│   ├── engineering-spec/
│   └── judge-*/                      # Validation agents
│
├── context/
│   └── tech-stack-standards.md       # Customize per org
│
├── docs/
│   ├── .state/                       # Template state files
│   │   ├── pending-tasks.json.template
│   │   ├── completed-tasks.json.template
│   │   └── current-phase.json.template
│   └── README.md
│
├── scripts/
│   ├── init-project.sh               # Initialize new app
│   ├── init-feature.sh               # Add new feature
│   ├── orchestrate.py                # Main orchestrator
│   ├── run-agent.py                  # Generic agent runner
│   ├── run-judge.py                  # Generic judge runner
│   └── state-manager.py              # State machine logic
│
├── claude.md                         # Instructions for Claude Code
├── INTRODUCTION.md                   # Full framework explanation
├── README.md                         # This file
└── LICENSE
```

## Contributing

This is an experimental framework. Contributions welcome:

- Improved agent prompts
- Additional validation criteria
- Better state management
- Tool integrations
- Example projects

## License

MIT License - See LICENSE file

---

**The bet:** Planning and implementation should both be agent-driven, version-controlled, and traceable. This framework is one way to explore that future.
