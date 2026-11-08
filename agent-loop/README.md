# Multi-Agent Iteration Loop (`agent-loop`)

An autonomous, multi-agent coordination skill that orchestrates four dedicated AI subagents—**Planning**, **Development**, **Review**, and **Publisher**—in a continuous, test-driven iteration loop to deliver and publish spec-compliant, high-standard software features.

---

## Overview & Core Philosophy

### Philosophy: Strict Separation of Concerns & Pure Orchestration
The fundamental principles of `agent-loop` are **role isolation** and **pure orchestration**:
- **The Coordinator Agent**: Acts strictly as the project manager and workflow orchestrator.
  - **Zero Task-Related Actions**: The coordinator **MUST NOT** read codebase files, search or grep code, explore project architecture, or inspect git diffs. All reading, implementation, testing, and reviewing are delegated strictly to subagents.
  - **Zero Code Changes**: The coordinator **MUST NOT** write code, create source files, or edit application logic.
  - **Force Skill Loading (No Instruction Inlining)**: The coordinator **MUST NOT** summarize, fragment, or paraphrase skill instructions in subagent prompts. Instead, it explicitly instructs each subagent to read and execute its designated skill (`SKILL.md`).
  - **Subagent Context Lifecycle**: Enforces strict context isolation between tasks and continuity within task fixes: spawns a fresh subagent for each new task via `invoke_subagent`, and reuses the same subagent via `send_message` for post-review fixes.
- **The Subagents**: Specialized agents spawned for distinct phases of the software development lifecycle (SDLC), required to load and operate under dedicated workspace skill playbooks (`planning-and-task-breakdown`, `test-driven-development`, `refactoring`, `code-review`, and `pull-request`).

By enforcing strict boundaries, the loop eliminates common single-agent failure modes—such as skipping unit tests, rationalizing sloppy implementations, or opening half-finished pull requests without quality audits.

### When to Use
- **Feature Development**: Converting a specification, PRD, or user story into production-ready code.
- **Complex Refactoring**: Multi-step codebase refactorings requiring incremental test verification at each step.
- **Autonomous End-to-End Execution**: Hands-off development workflows that must culminate in a validated GitHub Pull Request without human micro-management.

---

## Workflow & Architecture

The skill manages a closed-loop state machine with quality gates at every transition:

```mermaid
graph TD
    Start["User Request / Specification"] --> Plan["1. Planning Subagent<br/>(planning-and-task-breakdown)"]
    Plan --> SavePlan["Generate tasks/plan.md & tasks/todo.md"]
    SavePlan --> ApprPlan{"User Approval?"}
    ApprPlan -- "No / Revisions" --> Plan
    ApprPlan -- "Yes (Proceed)" --> Dev["2. Development Subagent<br/>(test-driven-development + refactoring)<br/><i>Spawn fresh context per new task</i>"]
    Dev --> ImpTask["Implement Task via TDD & Quality Gates"]
    ImpTask --> Rev["3. Review Subagent<br/>(code-review)"]
    Rev --> Check{"Any Findings?<br/>(Standards / Spec / Bugs)"}
    Check -- "Yes (Fix with same dev context via send_message)" --> Dev
    Check -- "No (0 Findings)" --> CheckMore{"Remaining Tasks in todo.md?"}
    CheckMore -- "Yes (Spawn new dev agent with fresh context)" --> Dev
    CheckMore -- "No" --> Pub["4. Publisher Subagent<br/>(pull-request)"]
    Pub --> OpenPR["Create Branch, Conventional Commit, Push & gh pr create"]
    OpenPR --> Done["Complete: Pull Request Published"]
```

### The 4 Phases

1. **Planning Phase (`planning` subagent)**
   - Coordinator passes user request/spec directly without inspecting or reading codebase files.
   - Subagent is mandated to load and follow `planning-and-task-breakdown/SKILL.md`.
   - Explores codebase architecture, decomposes the initiative into small, vertically sliced tasks.
   - Produces `tasks/plan.md` (architectural design) and `tasks/todo.md` (actionable checklist) for user confirmation.
2. **Development Phase (`development` subagent)**
   - Coordinator delegates the next incomplete task from `tasks/todo.md` by spawning a **fresh** subagent instance (`invoke_subagent`) to guarantee clean, isolated context.
   - Subagent is mandated to load and follow `test-driven-development/SKILL.md` (test-first Red-Green cycle) and `refactoring/SKILL.md` (automated quality gates: CRAP < 10, duplication elimination, mutation killing).
   - Writes tests first, implements minimal code to pass, refactors under quality gates, and marks task `[x]`.
3. **Review Phase (`review` subagent)**
   - Coordinator triggers the subagent without inspecting diffs itself.
   - Subagent is mandated to load and follow `code-review/SKILL.md`.
   - Inspects `git diff` against five review axes: Correctness, Readability, Architecture, Security, and Performance.
   - Findings are routed directly back to the **same** development subagent instance via `send_message` for remediation within the same working context.
4. **Publishing Phase (`publisher` subagent)**
   - Coordinator delegates publication once all tasks in `tasks/todo.md` pass review.
   - Subagent is mandated to load and follow `pull-request/SKILL.md`.
   - Cleans worktree, verifies test suite, commits following Conventional Commits, pushes branch, and opens a GitHub Pull Request via `gh pr create`.

---

## Required Dependencies & Installation Links

To execute `agent-loop` and its underlying subagent tools, ensure the following command-line tools and runtimes are installed:

| Tool | Purpose | Download & Documentation |
| :--- | :--- | :--- |
| **Git** | Distributed version control and diff tracking | [git-scm.com](https://git-scm.com/) |
| **GitHub CLI (`gh`)** | Automated authentication, branch push, and PR creation | [cli.github.com](https://cli.github.com/) |
| **Python 3** | Runtime for auxiliary automation scripts (v3.10+) | [python.org/downloads](https://www.python.org/downloads/) |

### Installation Instructions

#### macOS (Homebrew)
```bash
# Install Git, GitHub CLI, and Python
brew install git gh python

# Authenticate GitHub CLI with your GitHub account
gh auth login
```

#### Ubuntu / Debian Linux
```bash
# Install Git and Python
sudo apt-get update
sudo apt-get install -y git python3 python3-pip

# Install GitHub CLI (official repository)
type -p curl >/dev/null || (sudo apt update && sudo apt install curl -y)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh -y

# Authenticate GitHub CLI
gh auth login
```

#### Windows (Winget / Scoop)
```powershell
# Using Winget
winget install --id Git.Git -e --source winget
winget install --id GitHub.cli -e --source winget
winget install --id Python.Python.3.12 -e --source winget

# Authenticate GitHub CLI
gh auth login
```

---

## Usage & Examples

### Invoking via AI Assistant

When prompting an AI assistant or orchestrator in an agentic coding environment:

```text
Use the agent-loop skill to implement the following user feature:
"Add rate-limiting middleware to our Express API router based on client IP using a sliding window algorithm."
Ensure tasks are tracked in tasks/plan.md and tasks/todo.md, and open a PR when completed.
```

### Coordinator Execution Contract

The coordinator executes pure workflow orchestration without inspecting codebase files:

1. **Step 1: Plan Generation**
   - Coordinator invokes `planning` subagent, passing raw user request/spec directly.
   - Mandates the subagent load and execute `planning-and-task-breakdown/SKILL.md`.
   - Files created by subagent:
     ```
     tasks/
     ├── plan.md   # Architectural breakdown and design rationale
     └── todo.md   # [ ] Task 1, [ ] Task 2, [ ] Task 3
     ```
   - Coordinator presents plan summary to the user for approval.

2. **Step 2: Task-by-Task TDD Implementation**
   - Coordinator selects the next incomplete task from `tasks/todo.md`.
   - Spawns a **fresh** `development` subagent instance via `invoke_subagent` to ensure clean, isolated context per task and records its `conversationId`.
   - Mandates the subagent load and execute `test-driven-development/SKILL.md` and `refactoring/SKILL.md`.
   - Subagent implements test-first, refactors under quality gates (CRAP < 10, clone checks, mutation tests), and marks task `[x]`.

3. **Step 3: Quality Gate Review**
   - Coordinator triggers `review` subagent, mandating it to load and execute `code-review/SKILL.md`.
   - Subagent audits git diff against the 5 quality axes.
   - If findings are reported, coordinator routes the reviewer's report directly to the **same** `development` subagent via `send_message` (using its `conversationId`) to remediate within the original context.
   - When 0 findings remain, the loop advances to the next task in `tasks/todo.md` (spawning a new development subagent with fresh context).

4. **Step 4: Publishing Pull Request**
   - Once all tasks in `tasks/todo.md` are marked `[x]`, coordinator invokes `publisher` subagent.
   - Mandates the subagent load and execute `pull-request/SKILL.md`.
   - Subagent cleans worktree, validates tests, commits via Conventional Commits, pushes branch, and executes `gh pr create`.
   - The coordinator shares the published pull request URL with the user.

---

## File Structure & Subagent Skill References

```
agent-loop/
├── README.md               # Overview, dependencies, workflow, and instructions (this file)
└── SKILL.md                # Core execution rules, phase definitions, and constraints
```

### Linked Workspace Skills
`agent-loop` relies on subagents loading specialized workspace skills:

- **Planning Subagent**: [planning-and-task-breakdown](../planning-and-task-breakdown/SKILL.md) (Task sizing, vertical slicing, dependency ordering)
- **Development Subagent**: [test-driven-development](../test-driven-development/SKILL.md) (Red-Green-Refactor loop, interface seams, anti-patterns)
- **Review Subagent**: [code-review](../code-review/SKILL.md) (5-axis code quality gate, severity tagging)
- **Publisher Subagent**: [pull-request](../pull-request/SKILL.md) (Git branch isolation, Conventional Commits, GitHub CLI PR automation)
