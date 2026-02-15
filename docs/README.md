# Documentation Directory

This directory contains all agent-generated planning documents.

## Structure

```
docs/
├── .state/              # Orchestration state (DO NOT EDIT MANUALLY)
│   ├── pending-tasks.json
│   ├── completed-tasks.json
│   └── current-phase.json
│
├── 00-user-idea.md      # Your initial application concept
│
├── 01-prd/              # Product Requirements Documents
│   └── prd-v1.0.md
│
├── 02-refinement/       # Feature refinement Q&A
│   ├── feature-1/
│   │   ├── questions-iter-1.md
│   │   ├── prd-v1.1.md
│   │   └── questions-iter-2.md
│   └── feature-2/
│       └── ...
│
├── 03-foundation/       # Architecture analysis
│   └── foundation-analysis.md
│
└── 04-specs/            # Engineering specifications
    ├── foundation-spec.md
    ├── feature-1-spec.md
    └── feature-2-spec.md
```

## What Gets Created When

1. **Initialization**: `00-user-idea.md`, `.state/*.json`
2. **Product Manager**: `01-prd/prd-v1.0.md`
3. **Feature Refinement**: `02-refinement/[feature]/`
4. **Foundation Analysis**: `03-foundation/foundation-analysis.md`
5. **Engineering Specs**: `04-specs/*.md`

## State Files

### `.state/pending-tasks.json`

Contains tasks waiting to run:
```json
{
  "tasks": [
    {
      "id": "task-123",
      "agent": "tech-lead",
      "input": {...},
      "dependencies": [],
      "priority": 1
    }
  ]
}
```

### `.state/completed-tasks.json`

Contains tasks that have finished:
```json
{
  "tasks": [
    {
      "id": "task-122",
      "agent": "product-manager",
      "completed_at": "2025-02-15T10:30:00Z"
    }
  ]
}
```

### `.state/current-phase.json`

Shows current workflow phase:
```json
{
  "phase": "feature-refinement",
  "waiting_for": "product-owner",
  "last_updated": "2025-02-15T10:30:00Z"
}
```

## DO NOT Edit Manually

The `.state/` directory is managed by the orchestrator. Manual edits will be overwritten.

To add tasks or modify workflow, use the provided scripts:
- `scripts/init-feature.sh` - Add new features
- `scripts/init-project.sh` - Initialize projects

## Viewing Progress

```bash
# What phase are we in?
cat docs/.state/current-phase.json

# What's pending?
jq '.tasks[] | .id' docs/.state/pending-tasks.json

# What's complete?
jq '.tasks[] | .id' docs/.state/completed-tasks.json

# Full history
git log docs/
```

## Specs Are Versioned

As features evolve, specs are versioned:
- `prd-v1.0.md` - Initial
- `prd-v1.1.md` - After first refinement
- `prd-v1.2.md` - After second refinement

Always use the latest version.
