# Agentic Development Framework

## Software Development in the LLM Era

### The Shift Happening Now

Large language models are transforming how we build software. Not in the distant future—right now. Teams are already using Claude, GPT-4, and other LLMs to generate code, write tests, and draft documentation. But we're still planning software the same way we did in 2010: Jira tickets, scattered Google Docs, and tribal knowledge in Slack.

**The mismatch is obvious.** If agents can write implementation code, why are we still manually writing requirements in isolated tools?

### What This Framework Does

This is a **practical experiment** in using LLMs for the full software development lifecycle. The core idea:

**Define a workflow where LLM agents create and refine specifications through structured iteration, then implement those specifications—all version-controlled in Git.**

That's it. No magic. Just:
- Planning agents that generate and refine specifications
- Validation agents that check quality before human review
- Implementation agents (like Claude Code) that build from specs
- Git as the storage and collaboration layer
- A simple state machine to orchestrate it all

### Why Git, Not Jira

Jira made sense in 2010. It doesn't make sense in 2025.

**What Jira gives you:**
- Tickets (disconnected from code)
- Comments (lost in threads)
- Attachments (PDFs nobody opens)
- Custom fields (that vary by team)
- History (but not diffs)

**What Git gives you:**
- Documents (next to code)
- Commits (with full context)
- Diffs (exactly what changed)
- Branches (parallel work)
- Blame (who decided and when)

More importantly: **Git is where LLM agents naturally operate.** They read files, write files, commit changes. They don't navigate Jira's UI or parse its API responses well.

If you're building software with AI assistance, your planning artifacts should live where the AI (and your code) already lives: in Git.

### How It Works

#### Step 1: Define the Process Once

Create a template repository with:
- Agent prompts (Product Manager, Tech Lead, Engineering Spec, etc.)
- Validation criteria (what makes a "good" PRD, spec, etc.)
- Orchestration scripts (~200 lines of Python)
- GitHub Actions to run it all

This is your organization's **planning process as code**.

#### Step 2: Fork for Each New Product

```bash
gh repo create my-company/new-app --template agentic-framework
./scripts/init-project.py --idea "Task management with AI prioritization"
git push
```

The orchestrator reads the state files, sees "pending task: run product-manager agent," calls the LLM with the appropriate prompt, validates the output, commits it, and moves to the next task.

#### Step 3: Agents Plan Through Iteration

```
Product Manager agent writes initial PRD
  ↓
Tech Lead agent reviews feature, asks clarifying questions
  ↓
Product Owner agent answers questions, updates PRD
  ↓
Loop until refined
  ↓
Foundation Architect agent identifies common elements
  ↓
Engineering Spec agent writes detailed implementation specs
  ↓
Specs committed to main branch
```

Humans review at key decision points. Otherwise, agents and validators handle the iteration.

#### Step 4: Agents Build From Specs

Once specs are validated and merged:

```
State machine creates feature branches
  ↓
Claude Code (or similar) reads engineering spec
  ↓
Implements:
  - Database migrations
  - API endpoints
  - Service layer
  - Frontend components
  - Tests
  ↓
Commits to feature branch
  ↓
CI runs (tests, linting, security scans)
  ↓
PR created for human review
  ↓
Merge when approved
```

The same orchestrator that drove planning now drives implementation. Specs aren't handed off to humans—they're executed by implementation agents.

### What Makes This Different

**It's not about replacing product managers.** The agents execute a process—a product manager still makes decisions about what to build and why.

**It's not about eliminating developers.** Implementation agents generate initial code, but humans review, refine, and make architectural decisions.

**It's not about eliminating human review.** Validators catch mechanical issues in specs. CI catches issues in code. Humans make strategic judgments and approve PRs.

**It is about structure.** LLMs work best with clear prompts, defined outputs, and iteration loops. This framework provides that structure—from idea to running code.

### What You Actually Get

A Git repository with:
```
docs/
  .state/              # Which agents run when (JSON)
  01-prd/              # Product requirements (agent-generated)
  02-refinement/       # Q&A iterations per feature (agent-generated)
  03-foundation/       # Architectural analysis (agent-generated)
  04-specs/            # Engineering specifications (agent-generated)
src/
  API/                 # Implementation (agent-generated, human-reviewed)
  Web/                 # Implementation (agent-generated, human-reviewed)
  Tests/               # Tests (agent-generated, human-reviewed)
```

Every decision is traceable through `git log` and `git blame`. Every change is a diff you can review. Every document evolved through visible iterations. Every line of code traces back to the spec that defined it.

Is this better than Jira + manual coding? Depends on your team. But it's **designed for LLM-native workflows** in a way traditional tools aren't.

### The Full Workflow

```
User idea
  ↓
Planning agents iterate → Specs validated → Specs merged to main
  ↓
State machine creates feature/foundation branches
  ↓
Implementation agents (Claude Code, etc.):
  - Read engineering spec
  - Generate database schema
  - Generate API controllers
  - Generate service layer
  - Generate frontend components
  - Generate tests
  - Commit to branch
  ↓
CI validates implementation (tests, coverage, security)
  ↓
Judge agent reviews code quality
  ↓
Human reviews PR (architecture, business logic)
  ↓
Merge to main → Deploy
```

**Agents handle iteration and boilerplate. Humans handle strategy and approval.**

### The Evolution Question

Software doesn't end at v1. Three months later, you need to fix a bug or add a feature.

**Bug fix:** Developer fixes code directly, commits, creates PR. No agents needed.

**New feature:** 
1. Initialize agent workflow for the feature
2. Planning agents refine spec (with context of existing system)
3. Implementation agents generate code in feature branch
4. Human reviews and merges

**Breaking change:** 
1. Impact analysis agent identifies affected components
2. Planning agents update multiple specs
3. Migration agent generates upgrade specification
4. Implementation agents update code across features
5. Human reviews coordinated changes

The framework handles evolution because specs and code live together in Git, versioned in lockstep. Six months from now, `git log` shows why you made every architectural decision **and** the code that implemented it.

### Why This Matters Now

LLMs are getting better at following complex instructions. They're not perfect, but they're **good enough** to:
- Draft PRDs and ask clarifying questions
- Write technical specifications
- Generate database schemas and API code
- Write tests with good coverage
- Implement UI components from specs

**If you give them:**
1. Clear prompts
2. Structured inputs/outputs
3. Validation criteria
4. Iteration loops

This framework provides that scaffolding for **both planning and implementation**.

Five years from now, LLMs might write entire applications from natural language descriptions. But today, in 2025, the practical application is **structured workflows with human oversight**. Planning agents iterate on specs. Implementation agents generate code. Humans review, approve, and guide.

### What This Isn't

- **Not a low-code platform.** Code is generated by agents, but it's real code you can modify.
- **Not a replacement for thinking.** Strategic decisions are still human.
- **Not fully automated.** Humans review specs and code before merge.
- **Not production-ready.** This is an experimental framework.

### What This Is

An attempt to answer: **If LLMs can plan AND implement, what should the development process look like?**

The answer we're exploring: Version-controlled documents that define the system, agents that iterate on those documents until they're right, then agents that implement those specifications—with humans reviewing and approving at key gates.

It's not revolutionary. It's **evolutionary**—taking what works about modern development (Git, CI/CD, code review) and applying it to the entire lifecycle, from idea to deployed code.

### Tools That Make This Possible

- **Claude** (or GPT-4): Powers planning agents
- **Claude Code**: Implements engineering specifications
- **GitHub Actions**: Orchestrates the workflow
- **Git**: Version control for specs and code
- **CI/CD**: Validates agent-generated code

The framework is **tool-agnostic**. Swap Claude for another LLM. Use GitLab instead of GitHub. The pattern remains: agents iterate on specs, agents implement specs, humans review and approve.

---

**The bet:** In the LLM era, both planning documents and implementation code should be agent-generated and version-controlled together. Not in Jira. Not in Confluence. Not manually coded. In Git, created by agents, reviewed by humans.

This framework is one way to do that. Fork it, try it, adapt it. Or build your own version. Either way, the shift from manual planning and coding to agent-driven development with human oversight is happening. This is just one early experiment in what that might look like.
