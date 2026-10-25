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

## Usage

Each skill is standalone - clone or use the specific skill you need. See the individual `SKILL.md` files for detailed documentation, setup instructions, and usage examples.

---

*Repository contains 3 skills total.*