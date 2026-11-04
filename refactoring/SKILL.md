---
name: refactoring
description: "Executes the 'Then Make it Right' discipline: pins behavior, eliminates duplication, enforces CRAP < 10, runs mutation gates, and improves architecture without altering observable behavior."
metadata:
   version: 1.0.0
---

# Refactoring ("Then Make it Right")

Refactoring is the disciplined process of changing internal code structure without changing its external observable behavior. It follows the Red $\to$ Green minimal implementation ("Make it Work") to ensure code health, architectural integrity, and long-term maintainability.

## The Core Rule

1. **Pin what the code does.** Ensure existing tests (or characterization tests) cover the current behavior.
2. **Change the structure.** Refactor code toward cleaner abstractions, lower complexity, and single responsibility.
3. **Prove the behavior did not change.** All tests must stay green. A failing test during refactoring is a regression, not progress.

---

## The Three Automated Quality Gates

To prevent subjective or superficial refactoring, run the automated quality gates provided in `scripts/`:

### 1. `risk-gate` (Complexity & CRAP Score)
* **Rule**: Reduce each function under **CRAP 10** by splitting it, by testing it, or both. Consider whether case statements are worth reducing.
* **The Formula**: $\text{CRAP} = \text{CC}^2 \times (1 - \text{coverage})^3 + \text{CC}$.
  * If Cyclomatic Complexity ($\text{CC}$) is $\ge 10$, the function will fail even with 100% test coverage—it *must* be decomposed.
* **Command**:
  ```bash
  python3 refactoring/scripts/risk_gate.py <file-or-dir> [--coverage-file coverage.json]
  ```

### 2. `clone-check` (Structural Duplication)
* **Rule**: Eliminate structural duplication that ranks **0.8 or above**.
* Normalizes syntax trees to compare structural fingerprints (AST patterns) using Jaccard similarity.
* Extract repeated logic, algorithmic patterns, or mirrored workflows into clean, reusable functions or shared classes.
* **Command**:
  ```bash
  python3 refactoring/scripts/clone_check.py <file-or-dir> [--threshold 0.8]
  ```

### 3. `mutant-gate` (Mutation Testing)
* **Rule**: Cover the uncovered. Kill the survivors. Delete dead code.
* Mutates operators (`==` $\leftrightarrow$ `!=`, `+` $\leftrightarrow$ `-`, booleans) to test whether tests actually catch bugs.
  * **Killed mutant**: Test suite fails (Good—test verified behavior).
  * **Surviving mutant**: Test suite passes (Bad—weak assertion or dead code).
* **Command**:
  ```bash
  python3 refactoring/scripts/mutant_gate.py <file> --test-cmd "<test-command>"
  ```

---

## Architectural Disciplines

Refactoring must drive the code toward the following architectural standards:

### Model the Domain
* Put the domain in a structure that makes illegal states impossible to represent.
* Maintain a glossary of domain terms in documentation or domain models.
* If existing code is already clear and local, leave it alone.

### Boundary Discipline
* Check data where it enters the system boundaries.
* Inside system boundaries, trust it.
* Keep business logic in pure, deterministic functions without side-effects.

### Type System Discipline
* Make the illegal value impossible to write.
* Parse outside data once, where it comes in (parse, don't validate).
* Do not silence compiler, type-checker, or linter warnings with suppressions.

### Make Operations Idempotent
* Ensure running an operation twice, or running it after a crash halfway through, results in the exact same state.

### Separate Before Serializing Shared State
* If two components do not need the same mutable state, give each its own.
* If they do need shared state, allow only one writer, and enforce that single writer strictly in the structure.

---

## Step-by-Step Refactoring Workflow

1. **Verify Baseline Tests**:
   Run the test suite. Ensure all tests pass. If tests do not exist for the code being refactored, write **characterization tests** to lock in current behavior before touching code.
2. **Run Quality Gates**:
   Execute `risk_gate.py` and `clone_check.py` to identify high-risk functions ($\text{CRAP} \ge 10$) and structural duplicates ($\ge 0.8$).
3. **Execute Surgical Refactorings**:
   * Split complex methods into cohesive pure helper functions.
   * Eliminate duplication by extracting shared logic.
   * Apply domain and type system discipline.
4. **Run `mutant-gate`**:
   Verify that the refactored code and tests leave zero surviving mutants.
5. **Prove Invariance**:
   Run the full test suite and confirm 100% pass rate.
