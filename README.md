```text
┌────────────────────────────────────────────────────────────────────┐
│  ███████╗██╗  ██╗██╗██╗     ██╗     ███████╗                       │
│  ██╔════╝██║ ██╔╝██║██║     ██║     ██╔════╝   AUTONOMOUS AGENT    │
│  ███████╗█████╔╝ ██║██║     ██║     ███████╗      TOOLSUITE &      │
│  ╚════██║██╔═██╗ ██║██║     ██║     ╚════██║  WORKFLOW EXTENSIONS  │
│  ███████║██║  ██╗██║███████╗███████╗███████║                       │
│  ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝                       │
└────────────────────────────────────────────────────────────────────┘
```

# Skills

This repository is a collection of independent skills and tools for software development and automation. Each skill is a self-contained project with its own purpose, implementation, and documentation.

## Available Skills

### 1. [agent-loop](./agent-loop/SKILL.md)
Coordinates a multi-agent loop involving planning, development, review, and publishing sub-agents to implement and publish features test-first and with high standards compliance. The workflow includes:

- **Planning Phase**: Analyze user request/specification, generate `tasks/plan.md` and `tasks/todo.md`, present for user approval
- **Development Phase**: Implement tasks test-first using TDD, update task status as completed
- **Review Phase**: Perform standard and spec audits on git diff, resolve findings, loop until 0 findings
- **Publishing Phase**: Automate integration/deployment, commit using Conventional Commits, create GitHub PR

Key constraint: Pure orchestration only — the coordinator MUST NOT read codebase files or write code. It passes tasks directly to subagents and forces them to load and execute their corresponding workspace skills.

### 2. [code-review](./code-review/SKILL.md)
A comprehensive multi-axis code review framework that evaluates changes across five dimensions:

- **Correctness**: Does the code do what it claims? Edge cases, error paths, test coverage.
- **Readability & Simplicity**: Clear names, straightforward control flow, appropriate abstraction levels.
- **Architecture**: Fit with system design, module boundaries, dependency direction.
- **Security**: Input validation, secret management, authentication/authorization, parameterized queries.
- **Performance**: N+1 patterns, unbounded loops, async/sync appropriateness, re-renders.

Includes guidelines on change sizing, change descriptions, review process, handling disagreements, and honesty in review.

### 3. [codebase-context-generator](./codebase-context-generator/SKILL.md)
Generates comprehensive AI context, `AGENTS.md`, and structured documentation in a `context/` directory for any brownfield codebase using Tree-sitter AST extraction, dependency analysis, predefined Python scripts, and orchestrated subagents.

### 4. [email-triage](./email-triage/SKILL.md)
An autonomous multi-agent email triage system powered by dedicated Python wrapper scripts around the Google Workspace CLI (`gog`). Discovers accounts dynamically via `gog auth` (prioritizing default account first), delegates each thread to an isolated sub-agent for classification, and safely executes non-destructive actions:
- Moving cold outreach and spam to Gmail Trash (`--trash`) with a 30-day recovery safety net.
- Marking read and archiving regular notifications and automated alerts (`--archive`).
- Creating contextual draft replies in Gmail for action items and questions without auto-sending.
- Comprehensive `--dry-run` simulation support across all mutating operations.

### 5. [manual-automation](./manual-automation/SKILL.md)
Enables manual browser testing and automation using the Chrome DevTools MCP server. Covers the full workflow from port management through application launch, browser automation, login, and end-to-end testing. Includes port conflict handling, application launch sequences, login flows, E2E test execution with MCP tools, and cleanup procedures.

### 6. [planning-and-task-breakdown](./planning-and-task-breakdown/SKILL.md)
Decompose work into small, verifiable tasks with explicit acceptance criteria. Covers the planning process: entering plan mode, identifying dependency graphs, slicing vertically, writing tasks with description/acceptance criteria/verification/dependencies/files/scope, and ordering with checkpoints. Includes task sizing guidelines (XS-L) and red flags to watch for.

### 7. [project-change-intelligence](./project-change-intelligence/SKILL.md)
A progressive investigation framework for understanding how software evolves. Acts as a senior software engineer and technical project historian, helping project owners maintain accurate understanding of codebase evolution without manually inspecting every detail.

Uses a progressive investigation strategy (stages 0-4) from quick scans to full project-level analysis. Emphasizes evidence-first approach, prioritizing significance, and preserving context. Supports parallel investigation with subagents for independent analysis areas.

Core focus areas: architecture evolution, business rule changes, data ownership, API compatibility, security/reliability, test coverage, and deployment implications.

### 8. [pull-request](./pull-request/SKILL.md)
Creates a new feature branch from current git changes, commits them, pushes to the remote, and opens a GitHub pull request using the `gh` CLI. Follows conventional commit syntax and handles authentication errors gracefully.

### 9. [refactoring](./refactoring/SKILL.md)
Executes the disciplined "Then Make it Right" refactoring workflow without altering observable behavior across any programming language. Defines three automated quality-gate standards:
- **`risk-gate`**: Enforces function CRAP score < 10 (complexity & coverage).
- **`clone-check`**: Detects and eliminates structural code duplication >= 0.8 (e.g. using `jscpd` across 150+ languages).
- **`mutant-gate`**: Verifies test assertion efficacy via mutation testing (kill surviving mutants, delete dead code).

Includes native tooling matrix (TypeScript, Go, Rust, Python, Java) and architectural rules: modeling the domain, boundary discipline, type-system discipline, idempotent operations, and shared-state serialization.

### 10. [slack-cli](./slack-cli/SKILL.md)
A Python-based Slack workspace helper that enables safe interaction with Slack using curated scripts. Provides functionality for:

- Checking unread messages and mentions
- Listing channels and DMs
- Reading channel messages and threads
- Searching workspace history
- Posting messages and thread replies
- Adding/removing emoji reactions
- Looking up user profiles
- Editing existing messages
- Marking channels as read

**Key philosophy**: All Slack operations go through approved Python scripts (in `./scripts/`) rather than direct CLI execution, ensuring safe operations and normalized output.

### 11. [test-driven-development](./test-driven-development/SKILL.md)
Test-driven development reference covering the red→green loop. Defines what makes a good test (verifies behavior through public interfaces, reads like specification, survives refactors), where tests go (at seams, never against internals), anti-patterns (implementation-coupled, tautological, horizontal slicing), and rules of the loop (red before green, one slice at a time, laziness protocol, fixing root causes).

### 12. [yt-random-comment-picker](./yt-random-comment-picker/SKILL.md)
Downloads YouTube video comments, filters to unique authors, and randomly selects one comment to return. Uses `yt-dlp` to fetch comments and Python's `random` module for selection.

## Dependencies & Required Tools

Depending on which skills you plan to use, ensure the following host applications, CLIs, and runtimes are pre-installed and available in your environment.

### 1. Core Runtimes & System Tools

| Tool | Minimum Version | Used By Skills | Description & Download Link |
| :--- | :--- | :--- | :--- |
| **Git** | `2.30+` | `agent-loop`, `pull-request`, `code-review`, `project-change-intelligence`, `codebase-context-generator` | Distributed version control system.<br/>👉 [git-scm.com](https://git-scm.com/) |
| **GitHub CLI (`gh`)** | `2.40+` | `pull-request`, `agent-loop`, `project-change-intelligence` | Official GitHub CLI for branch push, authentication, and PR automation.<br/>👉 [cli.github.com](https://cli.github.com/) |
| **Python 3** | `3.10+` | `email-triage`, `slack-cli`, `yt-random-comment-picker`, `codebase-context-generator` | Python runtime environment for executing automation script suites and tests.<br/>👉 [python.org/downloads](https://www.python.org/downloads/) |
| **Node.js & npm** | `v18+` | `manual-automation`, `refactoring` | JavaScript runtime required for Chrome DevTools MCP and universal quality gates.<br/>👉 [nodejs.org](https://nodejs.org/) |

### 2. Service & Platform CLIs

| Tool | Used By Skill | Purpose & Installation Link |
| :--- | :--- | :--- |
| **Google Workspace CLI (`gog`)** | `email-triage` | Official Google Workspace CLI for Gmail, Calendar, Drive, and auth.<br/>👉 [gogcli.sh](https://gogcli.sh/) · [GitHub Repo](https://github.com/google/gogcli) |
| **Slack CLI (`slackcli`)** | `slack-cli` | Fast, lightweight standalone CLI for Slack workspaces by `shaharia-lab`.<br/>👉 [slackcli.dev](https://slackcli.dev/) · [GitHub Repo](https://github.com/shaharia-lab/slackcli) |
| **yt-dlp** | `yt-random-comment-picker` | Command-line media and comment thread extractor for YouTube.<br/>👉 [github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) |

### 3. Browser & Automation Tools

| Tool | Used By Skill | Purpose & Installation Link |
| :--- | :--- | :--- |
| **Google Chrome / Chromium** | `manual-automation` | Browser runtime for interactive and headless DevTools automation.<br/>👉 [google.com/chrome](https://www.google.com/chrome/) |
| **Chrome DevTools MCP Server** | `manual-automation` | Model Context Protocol server exposing browser control and inspection.<br/>👉 [Chrome DevTools MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/chrome-devtools) |

### 4. Code Quality & Analysis Packages

| Tool / Package | Used By Skill | Purpose & Installation Link |
| :--- | :--- | :--- |
| **Tree-sitter & Grammars** | `codebase-context-generator` | Parser generator and Python bindings for AST and call graph generation (`pip install -r requirements.txt`).<br/>👉 [tree-sitter.github.io](https://tree-sitter.github.io/tree-sitter/) |
| **jscpd** | `refactoring` | Universal copy/paste detector across 150+ programming languages (`npx jscpd`).<br/>👉 [github.com/kucherenko/jscpd](https://github.com/kucherenko/jscpd) |
| **Linters & Mutation Runners** | `refactoring`, `test-driven-development` | Native quality gate tools: `radon`/`flake8` (Python), `eslint`/`stryker` (JS/TS), `gocyclo`/`go-mutesting` (Go), `clippy`/`cargo-mutants` (Rust). |

---

### Quick Install Guide

#### macOS (via Homebrew)
```bash
# Core tools & CLIs
brew install git gh python node yt-dlp

# Google Workspace CLI
brew install google/gogcli/gog

# Slack CLI
brew install shaharia-lab/tap/slackcli

# Google Chrome
brew install --cask google-chrome

# Python AST requirements
pip install -r requirements.txt
```

#### Ubuntu / Debian
```bash
# Core tools & CLIs
sudo apt-get update && sudo apt-get install -y git gh python3 python3-pip nodejs npm

# yt-dlp
sudo wget https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -O /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp

# Python AST requirements
pip install -r requirements.txt
```

---

## Usage

Each skill is standalone - clone or use the specific skill you need. See the individual `SKILL.md` files for detailed documentation, setup instructions, and usage examples.

---

*Repository contains 12 skills total.*
