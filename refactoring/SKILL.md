---
name: refactoring
description: "Executes the 'Then Make it Right' discipline: pins behavior, eliminates duplication, enforces CRAP < 10, runs mutation gates, deletes accidental complexity ('code judo'), and improves architecture without altering observable behavior."
metadata:
   version: 1.1.0
---

# Refactoring ("Then Make it Right")

Refactoring is the disciplined process of changing internal code structure without changing its external observable behavior. It follows the Red $\to$ Green minimal implementation ("Make it Work") to ensure code health, architectural integrity, and long-term maintainability across any programming language.

## The Core Rule

1. **Pin what the code does.** Ensure existing tests (or characterization tests) cover the current behavior.
2. **Change the structure.** Refactor code toward cleaner abstractions, lower complexity, single responsibility, and **radical structural simplification**.
3. **Prove the behavior did not change.** All tests must stay green. A failing test during refactoring is a regression, not progress.

---

## The Quality Gates

To prevent subjective or superficial refactoring, enforce both automated metrics and structural simplification gates:

### 1. `risk-gate` (Complexity & CRAP Score)
* **Rule**: Reduce each function under **CRAP 10** by splitting it, by testing it, or both. Consider whether case statements are worth reducing.
* **The Formula**: $\text{CRAP} = \text{CC}^2 \times (1 - \text{coverage})^3 + \text{CC}$.
  * If Cyclomatic Complexity ($\text{CC}$) is $\ge 10$, the function will fail even with 100% test coverage—it *must* be decomposed.

### 2. `clone-check` (Structural Duplication)
* **Rule**: Eliminate structural duplication that ranks **0.8 or above** (or $\ge 80\%$).
* Extract repeated logic, algorithmic patterns, or mirrored workflows into clean, reusable functions or shared classes. Check if a canonical helper already exists in the project before creating a new utility.

### 3. `mutant-gate` (Mutation Testing)
* **Rule**: Cover the uncovered. Kill the survivors. Delete dead code.
* Injects programmatic mutations (inverting comparison operators, arithmetic, or booleans) to verify that tests actually assert behavior.
  * **Killed mutant**: Test suite fails (Good—test verified behavior).
  * **Surviving mutant**: Test suite passes (Bad—weak assertion or dead code).

### 4. `simplification-gate` (Conceptual Reduction & "Code Judo")
* **Rule**: Delete complexity rather than rearranging it. A refactor that leaves the same number of concepts or merely moves messy code into helper functions has failed.
* **No thin wrappers**: Delete identity wrappers and pass-through abstractions that add indirection without buying clarity or protection.
* **Anti-spaghetti**: Clean up ad-hoc flags, booleans, and scattered special cases introduced during quick bug fixes or Green phases.
* **File decomposition**: Decompose files approaching or exceeding 1,000 lines into focused, cohesive modules.

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

### Delete Complexity Rather Than Rearranging It ("Code Judo")
* Look for opportunities to reframe the model so that whole branches, helpers, modes, or layers disappear entirely.
* Prefer solutions that make the code feel inevitable in hindsight.
* Assume there is often a structural move that uses the existing architecture more cleanly rather than layering on new code.

### Direct & Boring Over Generic Magic
* Prefer direct, legible code over "clever" indirection, generic wrappers, or loose typing (`any`/`unknown`).
* Strip out identity abstractions and pass-through helpers that add cognitive overhead without real benefits.

### Eliminate Ad-Hoc Branching
* Never allow temporary flags or one-off conditionals to harden into permanent spaghetti.
* Push branching logic into dedicated abstractions, state machines, or typed dispatchers.

### Canonical Reuse & Layer Cleanliness
* Keep logic in the canonical layer. Feature logic must not leak into shared paths.
* Reuse existing canonical utilities instead of creating near-duplicate helpers.

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

### Make Operations Idempotent & Atomic
* Ensure running an operation twice, or running it after a crash halfway through, results in the exact same state.
* Structure related updates into atomic operations rather than leaving state half-applied.

### Separate Before Serializing Shared State
* If two components do not need the same mutable state, give each its own.
* If they do need shared state, allow only one writer, and enforce that single writer strictly in the structure.
* Avoid unnecessary sequential orchestration when independent tasks can execute in parallel.

---

## Step-by-Step Refactoring Workflow

1. **Verify Baseline Tests**:
   Run the project's test suite. Ensure all tests pass. If tests do not exist for the code being refactored, write **characterization tests** to lock in current behavior before touching code.
2. **Run Quality Gates**:
   Execute the ecosystem's `risk-gate` and `clone-check` commands to identify high-risk functions ($\text{CRAP} \ge 10$) and structural duplicates ($\ge 0.8$). Flag files exceeding 1,000 lines.
3. **Execute Surgical Refactorings & Simplifications**:
   * Search for the "code judo" move: reframe data structures or dispatch logic to delete complexity.
   * Split complex methods into cohesive pure helper functions and decompose files past 1,000 lines.
   * Strip out thin pass-through wrappers and ad-hoc boolean conditionals.
   * Eliminate duplication by reusing canonical helpers.
   * Apply domain and type system discipline.
4. **Run `mutant-gate`**:
   Verify that the refactored code and tests leave zero surviving mutants.
5. **Prove Invariance**:
   Run the full test suite and confirm 100% pass rate.
