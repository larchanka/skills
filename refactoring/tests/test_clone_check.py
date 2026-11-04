import unittest
import ast
import tempfile
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from clone_check import (
    extract_fingerprints,
    jaccard_similarity,
    find_clones_in_code,
)


class TestCloneCheck(unittest.TestCase):
    def test_jaccard_identical(self):
        s1 = {"A", "B", "C"}
        s2 = {"A", "B", "C"}
        self.assertAlmostEqual(jaccard_similarity(s1, s2), 1.0)

    def test_jaccard_disjoint(self):
        s1 = {"A", "B"}
        s2 = {"C", "D"}
        self.assertAlmostEqual(jaccard_similarity(s1, s2), 0.0)

    def test_detects_structural_duplicate(self):
        # Two functions with different variable names and constants but identical control flow and operations
        code = """
def calculate_tax(salary, rate):
    if salary <= 0:
        return 0
    total = salary * rate
    if total > 1000:
        total = total * 0.95
    return total

def calculate_discount(price, pct):
    if price <= 0:
        return 0
    subtotal = price * pct
    if subtotal > 1000:
        subtotal = subtotal * 0.95
    return subtotal

def completely_different(items):
    for item in items:
        try:
            item.process()
        except Exception:
            pass
    return None
"""
        clones = find_clones_in_code(code, threshold=0.8, min_lines=4)
        self.assertEqual(len(clones), 1)
        clone = clones[0]
        self.assertIn("calculate_tax", (clone["func1"], clone["func2"]))
        self.assertIn("calculate_discount", (clone["func1"], clone["func2"]))
        self.assertGreaterEqual(clone["similarity"], 0.8)


if __name__ == "__main__":
    unittest.main()
