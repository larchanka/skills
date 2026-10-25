# AGENTS.md Template

Use this template as the standard blueprint when generating `AGENTS.md` in the target repository root. Fill in each section with grounded facts discovered from AST analysis and package configurations.

```markdown
# Agent Instructions & Codebase Guidelines

Welcome to [PROJECT_NAME]. This file provides essential guidelines, architecture overview, verified commands, and operating constraints for AI agents and automated tools working in this repository.

---

## 1. Project Overview
- **Repository Purpose**: [1-2 sentences on what this system does and what problem it solves]
- **Core Languages & Frameworks**: [e.g., TypeScript, Rust, Python 3.12, React, FastAPI, etc.]
- **Primary Runtime / Environment**: [e.g., Node.js >= 20, Docker, Cargo, Python venv]

---

## 2. Essential Commands

> [!IMPORTANT]
> Run all commands from the repository root unless explicitly noted.

### Build & Setup
```bash
# Install dependencies
[INSTALL_COMMAND]

# Build / Compile
[BUILD_COMMAND]
```

### Testing & Verification
```bash
# Run all tests
[TEST_COMMAND]

# Run a single test file
[SINGLE_TEST_COMMAND]

# Linting & Formatting
[LINT_COMMAND]

# Type Checking
[TYPECHECK_COMMAND]
```

---

## 3. Architecture & Context Navigation

For in-depth architectural details, refer to the documentation in the [`context/`](./context/) directory:

- [**context/index.md**](./context/index.md): Documentation map and quick index.
- [**context/architecture.md**](./context/architecture.md): High-level system design, subsystem relationships, and data flows.
- [**context/modules.md**](./context/modules.md): Complete module catalog with public interfaces and responsibilities.
- [**context/signatures.md**](./context/signatures.md): Searchable index of all function signatures, parameters, and return types.
- [**context/dependencies.md**](./context/dependencies.md): Internal call graphs and third-party dependencies.
- [**context/conventions.md**](./context/conventions.md): Code style, error handling patterns, and test standards.

### Key Entry Points & Hub Modules
| Component / File | Role | Type |
| :--- | :--- | :--- |
| `[ENTRYPOINT_FILE]` | [Role, e.g. CLI entry point or server bootstrap] | Entrypoint |
| `[HUB_MODULE_FILE]` | [Role, e.g. shared state, utility core, or DB client] | Core Hub |

---

## 4. Agent Rules & Operational Constraints

Follow these rules on every task:

1. **Surgical Changes**: Touch only files necessary for the requested feature or fix. Do not reformat adjacent unrelated code.
2. **Never Break Type Checks or Tests**: Always verify with `[TEST_COMMAND]` and `[TYPECHECK_COMMAND]` before completing a task.
3. **Preserve Existing Patterns**:
   - Follow error handling conventions described in [context/conventions.md](./context/conventions.md).
   - Use existing helpers and abstractions rather than introducing duplicate utilities.
4. **No Speculative Abstractions**: Solve only the immediate problem. Do not add unused configuration or premature abstractions.

---

## 5. Automatic Context & Graph Maintenance (Post-Change Instruction)

> [!IMPORTANT]
> **Always Keep Context & Symbol Graphs In Sync**:
> If any code was created, modified, or deleted during your task, you MUST refresh the symbol graph and context artifacts.

Run the following update sequence (or spawn a lightweight subagent to execute it):

```bash
# 1. Rescan AST and update symbol/call graphs
python3 codebase-context-generator/scripts/ast_scanner.py --root .
python3 codebase-context-generator/scripts/dependency_graph.py --manifest .context_cache/ast_manifest.json
python3 codebase-context-generator/scripts/symbol_graph.py \
  --manifest .context_cache/ast_manifest.json \
  --save-graph .context_cache/symbol_graph.json \
  --export-signatures context/signatures.md

# 2. Update context documentation if public APIs, modules, or architecture changed:
#    - If new modules were added: update context/modules.md
#    - If architecture/data flow changed: update context/architecture.md
#    - If new dependencies were introduced: update context/dependencies.md

# 3. Verify documentation integrity
python3 codebase-context-generator/scripts/verify_context.py --root .
```

If delegating this to a subagent, use the following prompt:
> *"Code changes were completed in the workspace. Run the codebase-context-generator scripts to refresh the AST manifest, symbol graph, and `context/signatures.md`. If new files or architectural components were introduced, update `context/modules.md` and `context/architecture.md`, then run `scripts/verify_context.py` to ensure 0 broken links and full coverage."*
```
