# Refactoring Skill

This skill enforces the **"Then Make it Right"** phase of software development across **any programming language**. It provides deterministic quality-gate standards, architectural disciplines, and radical structural simplification ("code judo") to restructure code without changing observable behavior.

## The Quality Gates

1. **`risk-gate`**: Reduce each function under **CRAP 10** ($\text{CRAP} = \text{CC}^2 \times (1 - \text{cov})^3 + \text{CC}$).
2. **`clone-check`**: Eliminate structural duplication that ranks **0.8 or above** ($\ge 80\%$) and reuse canonical helpers.
3. **`mutant-gate`**: Mutation testing — *Cover the uncovered, kill the survivors, delete dead code.*
4. **`simplification-gate`**: *Conceptual reduction & "Code Judo"* — Delete complexity rather than rearranging it. Eliminate thin pass-through wrappers, clean up ad-hoc conditional branching, and decompose files exceeding 1,000 lines.

## Native Tooling Matrix

| Ecosystem | `risk-gate` ($\text{CRAP} / \text{CC} < 10$) | `clone-check` (Duplication $< 0.8$) | `mutant-gate` (Mutation Kill) |
| :--- | :--- | :--- | :--- |
| **Universal (150+ langs)** | Check linter complexity rules | `npx jscpd --threshold 80 <path>` | — |
| **TypeScript / JavaScript** | `npx eslint --rule 'complexity: ["error", 10]'` | `npx jscpd --threshold 80 src/` | `npx stryker run` |
| **Go** | `gocyclo -over 10 .` or `golangci-lint run` | `npx jscpd --threshold 80 .` | `go-mutesting ./...` |
| **Rust** | `cargo clippy -- -D clippy::cognitive_complexity` | `npx jscpd --threshold 80 src/` | `cargo mutants` |
| **Python** | `radon cc -s -n B .` or `flake8 --max-complexity 10` | `npx jscpd --threshold 80 .` | `mutmut run` |
| **Java / JVM** | Checkstyle `CyclomaticComplexity` or Sonar | `npx jscpd --threshold 80 src/` | `mvn org.pitest:pitest-maven:mutationCoverage` |
