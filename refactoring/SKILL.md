---
name: refactoring
description: "Executes the 'Then Make it Right' discipline: pins behavior, eliminates duplication, enforces CRAP < 10, runs mutation gates, and improves architecture without altering observable behavior."
metadata:
   version: 1.0.0
---

# Refactoring ("Then Make it Right")

Refactoring is the disciplined process of changing internal code structure without changing its external observable behavior. It follows the Red $\to$ Green minimal implementation ("Make it Work") to ensure code health, architectural integrity, and long-term maintainability across any programming language.

## The Core Rule

1. **Pin what the code does.** Ensure existing tests (or characterization tests) cover the current behavior.
2. **Change the structure.** Refactor code toward cleaner abstractions, lower complexity, and single responsibility.
3. **Prove the behavior did not change.** All tests must stay green. A failing test during refactoring is a regression, not progress.

---

## The Three Automated Quality Gates

To prevent subjective or superficial refactoring, enforce the three automated quality gates using the native tools of the target project's ecosystem:

### 1. `risk-gate` (Complexity & CRAP Score)
* **Rule**: Reduce each function under **CRAP 10** by splitting it, by testing it, or both. Consider whether case statements are worth reducing.
* **The Formula**: $\text{CRAP} = \text{CC}^2 \times (1 - \text{coverage})^3 + \text{CC}$.
  * If Cyclomatic Complexity ($\text{CC}$) is $\ge 10$, the function will fail even with 100% test coverage—it *must* be decomposed.

### 2. `clone-check` (Structural Duplication)
* **Rule**: Eliminate structural duplication that ranks **0.8 or above** (or $\ge 80\%$).
* Extract repeated logic, algorithmic patterns, or mirrored workflows into clean, reusable functions or shared classes.

### 3. `mutant-gate` (Mutation Testing)
* **Rule**: Cover the uncovered. Kill the survivors. Delete dead code.
* Injects programmatic mutations (inverting comparison operators, arithmetic, or booleans) to verify that tests actually assert behavior.
  * **Killed mutant**: Test suite fails (Good—test verified behavior).
  * **Surviving mutant**: Test suite passes (Bad—weak assertion or dead code).

---

## Native Tooling Matrix by Language

Execute the corresponding native CLI tool for the project being refactored:

| Ecosystem | `risk-gate` ($\text{CRAP} / \text{CC} < 10$) | `clone-check` (Duplication $< 0.8$) | `mutant-gate` (Mutation Kill) |
| :--- | :--- | :--- | :--- |
| **Universal (150+ langs)** | Check linter complexity rules | `npx jscpd --threshold 80 <path>` | — |
| **TypeScript / JavaScript** | `npx eslint --rule 'complexity: ["error", 10]'` | `npx jscpd --threshold 80 src/` | `npx stryker run` |
| **Go** | `gocyclo -over 10 .` or `golangci-lint run` | `npx jscpd --threshold 80 .` | `go-mutesting ./...` |
| **Rust** | `cargo clippy -- -D clippy::cognitive_complexity` | `npx jscpd --threshold 80 src/` | `cargo mutants` |
| **Python** | `radon cc -s -n B .` or `flake8 --max-complexity 10` | `npx jscpd --threshold 80 .` | `mutmut run` |
| **Java / JVM** | Checkstyle `CyclomaticComplexity` or Sonar | `npx jscpd --threshold 80 src/` | `mvn org.pitest:pitest-maven:mutationCoverage` |

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
   Run the project's test suite. Ensure all tests pass. If tests do not exist for the code being refactored, write **characterization tests** to lock in current behavior before touching code.
2. **Run Quality Gates**:
   Execute the ecosystem's `risk-gate` and `clone-check` commands to identify high-risk functions ($\text{CRAP} \ge 10$) and structural duplicates ($\ge 0.8$).
3. **Execute Surgical Refactorings**:
   * Split complex methods into cohesive pure helper functions.
   * Eliminate duplication by extracting shared logic.
   * Apply domain and type system discipline.
4. **Run `mutant-gate`**:
   Verify that the refactored code and tests leave zero surviving mutants.
5. **Prove Invariance**:
   Run the full test suite and confirm 100% pass rate.
