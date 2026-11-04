#!/usr/bin/env python3
"""
mutant-gate (Mutation Testing Gate)

Injects small programmatic mutations into AST to verify test assertions:
- Inverts comparison operators (== <-> !=, > <-> <=, etc.)
- Inverts boolean operations (and <-> or)
- Swaps arithmetic operators (+ <-> -, * <-> /)
- Mutates boolean constants (True <-> False)

Rule: Cover the uncovered, kill the survivors, delete dead code.
"""

import ast
import argparse
import copy
import json
import os
import shlex
import subprocess
import sys
from typing import List, Dict, Any, Optional


COMP_MUTATIONS = {
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.Lt: ast.LtE,
    ast.LtE: ast.Gt,
    ast.Gt: ast.GtE,
    ast.GtE: ast.Lt,
    ast.Is: ast.IsNot,
    ast.IsNot: ast.Is,
    ast.In: ast.NotIn,
    ast.NotIn: ast.In,
}

OP_MUTATIONS = {
    ast.Add: ast.Sub,
    ast.Sub: ast.Add,
    ast.Mult: ast.FloorDiv,
    ast.FloorDiv: ast.Mult,
}

BOOL_MUTATIONS = {
    ast.And: ast.Or,
    ast.Or: ast.And,
}


def generate_mutations(tree: ast.AST) -> List[Dict[str, Any]]:
    """Scan AST and discover all candidate mutation locations."""
    mutations: List[Dict[str, Any]] = []
    mut_id = 0

    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)

        # 1. Comparison operations (e.g., a == b -> a != b)
        if isinstance(node, ast.Compare):
            for idx, op in enumerate(node.ops):
                op_type = type(op)
                if op_type in COMP_MUTATIONS:
                    mutations.append({
                        "id": mut_id,
                        "type": f"Compare:{op_type.__name__}->{COMP_MUTATIONS[op_type].__name__}",
                        "line": line,
                        "node_ref": (node, "Compare", idx),
                    })
                    mut_id += 1

        # 2. Binary operations (e.g., a + b -> a - b)
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type in OP_MUTATIONS:
                mutations.append({
                    "id": mut_id,
                    "type": f"BinOp:{op_type.__name__}->{OP_MUTATIONS[op_type].__name__}",
                    "line": line,
                    "node_ref": (node, "BinOp", None),
                })
                mut_id += 1

        # 3. Boolean operations (e.g., a and b -> a or b)
        elif isinstance(node, ast.BoolOp):
            op_type = type(node.op)
            if op_type in BOOL_MUTATIONS:
                mutations.append({
                    "id": mut_id,
                    "type": f"BoolOp:{op_type.__name__}->{BOOL_MUTATIONS[op_type].__name__}",
                    "line": line,
                    "node_ref": (node, "BoolOp", None),
                })
                mut_id += 1

        # 4. Constant booleans (True <-> False)
        elif isinstance(node, ast.Constant) and isinstance(node.value, bool):
            mutations.append({
                "id": mut_id,
                "type": f"Constant:{node.value}->{not node.value}",
                "line": line,
                "node_ref": (node, "Constant", None),
            })
            mut_id += 1

    return mutations


class MutationApplier(ast.NodeTransformer):
    """Applies a single mutation identified by index."""
    def __init__(self, target_id: int):
        super().__init__()
        self.target_id = target_id
        self.current_id = 0

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        self.generic_visit(node)
        new_ops = []
        for op in node.ops:
            op_type = type(op)
            if op_type in COMP_MUTATIONS:
                if self.current_id == self.target_id:
                    new_ops.append(COMP_MUTATIONS[op_type]())
                else:
                    new_ops.append(op)
                self.current_id += 1
            else:
                new_ops.append(op)
        node.ops = new_ops
        return node

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        self.generic_visit(node)
        op_type = type(node.op)
        if op_type in OP_MUTATIONS:
            if self.current_id == self.target_id:
                node.op = OP_MUTATIONS[op_type]()
            self.current_id += 1
        return node

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        self.generic_visit(node)
        op_type = type(node.op)
        if op_type in BOOL_MUTATIONS:
            if self.current_id == self.target_id:
                node.op = BOOL_MUTATIONS[op_type]()
            self.current_id += 1
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if isinstance(node.value, bool):
            if self.current_id == self.target_id:
                node.value = not node.value
            self.current_id += 1
        return node


def apply_mutation(tree: ast.AST, target_id: int) -> ast.AST:
    """Return a deep copy of tree with target mutation applied."""
    cloned = copy.deepcopy(tree)
    transformer = MutationApplier(target_id)
    return transformer.visit(cloned)


def run_mutation_analysis(
    target_file: str,
    test_cmd: str,
    max_mutants: Optional[int] = None,
) -> Dict[str, Any]:
    """Mutate target_file and execute test_cmd for each mutant."""
    with open(target_file, "r", encoding="utf-8") as f:
        original_code = f.read()

    tree = ast.parse(original_code, filename=target_file)
    mutations = generate_mutations(tree)

    if max_mutants and len(mutations) > max_mutants:
        mutations = mutations[:max_mutants]

    killed = 0
    survived = 0
    survivors: List[Dict[str, Any]] = []

    try:
        for mut in mutations:
            mut_id = mut["id"]
            mutated_tree = apply_mutation(tree, mut_id)
            mutated_code = ast.unparse(mutated_tree)

            # Write mutant to file temporarily
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(mutated_code)

            # Run test command safely via shlex.split
            cmd = shlex.split(test_cmd)
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if res.returncode != 0:
                killed += 1
            else:
                survived += 1
                survivors.append({
                    "id": mut_id,
                    "line": mut["line"],
                    "mutation": mut["type"],
                })

    finally:
        # Always restore original file
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(original_code)

    total = killed + survived
    score = (killed / total * 100.0) if total > 0 else 100.0

    return {
        "target_file": target_file,
        "total": total,
        "killed": killed,
        "survived": survived,
        "mutation_score": round(score, 2),
        "survivors": survivors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="mutant-gate: Mutation Testing Quality Gate")
    parser.add_argument("target", help="Target source file to mutate")
    parser.add_argument("--test-cmd", required=True, help="Test suite command to execute (e.g. 'pytest' or 'python3 -m unittest')")
    parser.add_argument("--max-mutants", type=int, default=None, help="Limit number of mutants to evaluate")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    if not os.path.isfile(args.target):
        print(f"Error: Target file {args.target} does not exist", file=sys.stderr)
        return 2

    print(f"Running mutant-gate on {args.target} with test command: '{args.test_cmd}'...")
    results = run_mutation_analysis(args.target, args.test_cmd, args.max_mutants)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\n=== mutant-gate: Mutation Testing Results ===")
        print(f"Target file:     {results['target_file']}")
        print(f"Total Mutants:   {results['total']}")
        print(f"Killed (Passed): {results['killed']}")
        print(f"Survived (Fail): {results['survived']}")
        print(f"Mutation Score:  {results['mutation_score']}%")

        if results["survivors"]:
            print("\nSurviving Mutants (Tests did not catch these programmatic errors):")
            for s in results["survivors"]:
                print(f"  - Line {s['line']}: {s['mutation']}")
            print("\nAction required: Cover the uncovered, kill the survivors, or delete dead code.")

    return 1 if results["survived"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
