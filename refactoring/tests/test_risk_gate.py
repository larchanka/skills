import unittest
import ast
import tempfile
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from risk_gate import (
    calculate_cyclomatic_complexity,
    calculate_crap,
    analyze_file,
    analyze_directory,
)


class TestRiskGate(unittest.TestCase):
    def test_simple_function_complexity(self):
        code = """
def simple():
    return 42
"""
        tree = ast.parse(code)
        func = tree.body[0]
        # Base complexity is 1
        self.assertEqual(calculate_cyclomatic_complexity(func), 1)

    def test_branching_complexity(self):
        code = """
def branchy(a, b):
    if a > 0:
        if b > 0:
            return 1
        else:
            return 2
    for x in range(10):
        print(x)
    return 0
"""
        tree = ast.parse(code)
        func = tree.body[0]
        # 1 base + 1 (if) + 1 (if) + 1 (for) = 4
        self.assertEqual(calculate_cyclomatic_complexity(func), 4)

    def test_crap_formula(self):
        # CRAP = CC^2 * (1 - cov)^3 + CC
        # CC = 4, coverage = 1.0 -> 16 * 0 + 4 = 4.0
        self.assertAlmostEqual(calculate_crap(4, 1.0), 4.0)
        # CC = 4, coverage = 0.0 -> 16 * 1 + 4 = 20.0
        self.assertAlmostEqual(calculate_crap(4, 0.0), 20.0)
        # CC = 4, coverage = 0.5 -> 16 * 0.125 + 4 = 2.0 + 4 = 6.0
        self.assertAlmostEqual(calculate_crap(4, 0.5), 6.0)

    def test_analyze_file_detects_violations(self):
        code = """
def clean():
    return 1

def high_risk(x):
    if x == 1: pass
    elif x == 2: pass
    elif x == 3: pass
    elif x == 4: pass
    elif x == 5: pass
    elif x == 6: pass
    elif x == 7: pass
    elif x == 8: pass
    elif x == 9: pass
    elif x == 10: pass
    return x
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            results = analyze_file(temp_path, coverage_map={})
            # clean CC=1, CRAP=2 (with 0 coverage: 1^2 * 1 + 1 = 2) -> pass (< 10)
            # high_risk CC=11 -> CRAP >= 11 -> violates threshold 10
            high_risk_func = next(r for r in results if r["name"] == "high_risk")
            self.assertGreaterEqual(high_risk_func["crap"], 10.0)
            self.assertTrue(high_risk_func["violates"])
        finally:
            os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
