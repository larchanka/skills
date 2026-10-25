# Skills

This repository is a collection of independent skills and tools for software development and automation. Each skill is a self-contained project with its own purpose, implementation, and documentation.

## Available Skills

### 1. [slack-cli](./slack-cli/SKILL.md)
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

### 2. [code-review](./code-review/SKILL.md)
A comprehensive multi-axis code review framework that evaluates changes across five dimensions:

- **Correctness**: Does the code do what it claims? Edge cases, error paths, test coverage.
- **Readability & Simplicity**: Clear names, straightforward control flow, appropriate abstraction levels.
- **Architecture**: Fit with system design, module boundaries, dependency direction.
- **Security**: Input validation, secret management, authentication/authorization, parameterized queries.
- **Performance**: N+1 patterns, unbounded loops, async/sync appropriateness, re-renders.

Includes guidelines on change sizing, change descriptions, review process, handling disagreements, and honesty in review.

### 3. [project-change-intelligence](./project-change-intelligence/SKILL.md)
A progressive investigation framework for understanding how software evolves. Acts as a senior software engineer and technical project historian, helping project owners maintain accurate understanding of codebase evolution without manually inspecting every detail.

Uses a progressive investigation strategy (stages 0-4) from quick scans to full project-level analysis. Emphasizes evidence-first approach, prioritizing significance, and preserving context. Supports parallel investigation with subagents for independent analysis areas.

Core focus areas: architecture evolution, business rule changes, data ownership, API compatibility, security/reliability, test coverage, and deployment implications.

### 4. [agent-loop](./agent-loop/SKILL.md)
Coordinates a multi-agent loop involving planning, development, review, and publishing sub-agents to implement and publish features test-first and with high standards compliance. The workflow includes:

- **Planning Phase**: Analyze user request/specification, generate `tasks/plan.md` and `tasks/todo.md`, present for user approval
- **Development Phase**: Implement tasks test-first using TDD, update task status as completed
- **Review Phase**: Perform standard and spec audits on git diff, resolve findings, loop until 0 findings
- **Publishing Phase**: Automate integration/deployment, commit using Conventional Commits, create GitHub PR

Key constraint: The coordinator MUST NOT write implementation code - all code changes delegated to subagents.

### 5. [manual-automation](./manual-automation/SKILL.md)
Enables manual browser testing and automation using the Chrome DevTools MCP server. Covers the full workflow from port management through application launch, browser automation, login, and end-to-end testing. Includes port conflict handling, application launch sequences, login flows, E2E test execution with MCP tools, and cleanup procedures.

### 6. [planning-and-task-breakdown](./planning-and-task-breakdown/SKILL.md)
Decompose work into small, verifiable tasks with explicit acceptance criteria. Covers the planning process: entering plan mode, identifying dependency graphs, slicing vertically, writing tasks with description/acceptance criteria/verification/dependencies/files/scope, and ordering with checkpoints. Includes task sizing guidelines (XS-L) and red flags to watch for.

### 7. [pull-request](./pull-request/SKILL.md)
Creates a new feature branch from current git changes, commits them, pushes to the remote, and opens a GitHub pull request using the `gh` CLI. Follows conventional commit syntax and handles authentication errors gracefully.

### 8. [tdd](./tdd/SKILL.md)
Test-driven development reference covering the red→green→refactor loop. Defines what makes a good test (verifies behavior through public interfaces, reads like specification, survives refactors), where tests go (at seams, never against internals), anti-patterns (implementation-coupled, tautological, horizontal slicing), and rules of the loop (red before green, one slice at a time, refactoring is not part of the loop).

## Usage

Each skill is standalone - clone or use the specific skill you need. See the individual `SKILL.md` files for detailed documentation, setup instructions, and usage examples.

---

*Repository contains 8 skills total.*