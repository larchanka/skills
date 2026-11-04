# Refactoring Skill

This skill enforces the **"Then Make it Right"** phase of software development. It provides deterministic quality-gate tools and architectural principles to restructure code without changing observable behavior.

## Tools Included

### 1. `risk_gate.py`
Calculates function cyclomatic complexity and CRAP score ($\text{CRAP} = \text{CC}^2 \times (1 - \text{cov})^3 + \text{CC}$).
Enforces that every function stays under **CRAP 10**.

```bash
python3 scripts/risk_gate.py path/to/code/ [--coverage-file coverage.json]
```

### 2. `clone_check.py`
Detects AST structural code duplication and Jaccard similarity across functions and methods.
Flags code pairs with similarity **$\ge 0.8$**.

```bash
python3 scripts/clone_check.py path/to/code/ [--threshold 0.8]
```

### 3. `mutant_gate.py`
Performs programmatic mutation testing by inverting comparisons, arithmetic, and boolean logic.
Enforces: *Cover the uncovered, kill the survivors, delete dead code.*

```bash
python3 scripts/mutant_gate.py path/to/file.py --test-cmd "python3 -m unittest"
```

## Running Tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
