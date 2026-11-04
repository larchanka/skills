import unittest
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from mutant_gate import (
    generate_mutations,
    apply_mutation,
)


class TestMutantGate(unittest.TestCase):
    def test_generate_comparison_mutations(self):
        code = """
def is_positive(x):
    return x > 0
"""
        tree = ast.parse(code)
        mutations = generate_mutations(tree)
        # Should find comparison mutation for `>` (Gt -> GtE or Lt)
        self.assertGreater(len(mutations), 0)
        gt_mutations = [m for m in mutations if "Gt" in m["type"]]
        self.assertTrue(len(gt_mutations) > 0)

    def test_generate_arithmetic_mutations(self):
        code = """
def add(a, b):
    return a + b
"""
        tree = ast.parse(code)
        mutations = generate_mutations(tree)
        # Should find arithmetic mutation for `+` (Add -> Sub)
        add_mutations = [m for m in mutations if "Add" in m["type"]]
        self.assertTrue(len(add_mutations) > 0)

    def test_apply_mutation_modifies_code(self):
        code = """
def is_even(n):
    return n % 2 == 0
"""
        tree = ast.parse(code)
        mutations = generate_mutations(tree)
        self.assertGreater(len(mutations), 0)

        # Mutate the Eq operator
        mutated_tree = apply_mutation(tree, mutations[0]["id"])
        mutated_code = ast.unparse(mutated_tree)
        self.assertNotEqual(code.strip(), mutated_code.strip())
        self.assertIn("!=", mutated_code)


if __name__ == "__main__":
    unittest.main()
