#!/usr/bin/env python3
"""
risk-gate (CRAP score & complexity gate)

Enforces CRAP < 10 for all functions:
CRAP = CC^2 * (1 - coverage)^3 + CC
"""

import ast
import argparse
import json
import os
import sys
from typing import Dict, List, Any


def calculate_cyclomatic_complexity(node: ast.AST) -> int:
    """Calculate cyclomatic complexity of a function node.
    Base complexity is 1. Increment for decision points:
    if, elif, for, while, except, with, assert, boolean ops (and/or), ternary if.
    """
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, ast.IfExp):  # a if b else c
            complexity += 1
        elif isinstance(child, (ast.ExceptHandler, ast.Assert)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            # and/or with N values adds N-1 branching points
            complexity += max(0, len(child.values) - 1)
    return complexity


def calculate_crap(complexity: int, coverage: float) -> float:
    """Compute CRAP score using Alberto Savoia and Bob Evans formula:
    CRAP = CC^2 * (1 - coverage)^3 + CC
    """
    coverage = max(0.0, min(1.0, coverage))
    return (complexity ** 2) * ((1.0 - coverage) ** 3) + complexity


def analyze_file(
    filepath: str,
    coverage_map: Dict[str, float] = None,
    threshold: float = 10.0,
    no_coverage: bool = False,
) -> List[Dict[str, Any]]:
    """Analyze all functions in a Python file for CC and CRAP score."""
    if coverage_map is None:
        coverage_map = {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except Exception:
        return []

    results = []
    rel_path = os.path.relpath(filepath)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_name = node.name
            line_no = node.lineno
            cc = calculate_cyclomatic_complexity(node)

            # Look up coverage if available; if --no-coverage, assume covered to evaluate raw CC
            cov_key = f"{rel_path}:{func_name}"
            cov = 1.0 if no_coverage else coverage_map.get(cov_key, coverage_map.get(rel_path, 0.0))

            crap = calculate_crap(cc, cov)
            violates = crap >= threshold

            results.append({
                "file": rel_path,
                "name": func_name,
                "line": line_no,
                "complexity": cc,
                "coverage": cov,
                "crap": round(crap, 2),
                "threshold": threshold,
                "violates": violates,
            })

    return results


def analyze_directory(
    dirpath: str,
    coverage_map: Dict[str, float] = None,
    threshold: float = 10.0,
    no_coverage: bool = False,
) -> List[Dict[str, Any]]:
    """Walk directory and analyze all .py files."""
    results = []
    exclude_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}

    for root, dirs, files in os.walk(dirpath):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            if f.endswith(".py"):
                full_path = os.path.join(root, f)
                results.extend(analyze_file(full_path, coverage_map, threshold, no_coverage))

    return results


def load_coverage_json(cov_file: str) -> Dict[str, float]:
    """Parse standard coverage.json if provided."""
    coverage_map = {}
    if not os.path.exists(cov_file):
        return coverage_map
    try:
        with open(cov_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        files = data.get("files", {})
        for filepath, f_data in files.items():
            summary = f_data.get("summary", {})
            percent = summary.get("percent_covered", 0.0) / 100.0
            coverage_map[os.path.relpath(filepath)] = percent
    except Exception:
        pass
    return coverage_map


def main() -> int:
    parser = argparse.ArgumentParser(description="risk-gate: Enforce function CRAP score < 10")
    parser.add_argument("path", nargs="?", default=".", help="File or directory to analyze")
    parser.add_argument("--threshold", type=float, default=10.0, help="CRAP failure threshold (default: 10.0)")
    parser.add_argument("--coverage-file", type=str, default=None, help="Path to coverage.json")
    parser.add_argument("--no-coverage", action="store_true", help="Evaluate cyclomatic complexity only (ignore coverage)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    coverage_map = load_coverage_json(args.coverage_file) if args.coverage_file else {}

    if os.path.isfile(args.path):
        results = analyze_file(args.path, coverage_map, args.threshold, args.no_coverage)
    else:
        results = analyze_directory(args.path, coverage_map, args.threshold, args.no_coverage)

    # Sort descending by CRAP score
    results.sort(key=lambda r: r["crap"], reverse=True)

    violations = [r for r in results if r["violates"]]

    if args.json:
        print(json.dumps({"results": results, "violations": len(violations)}, indent=2))
    else:
        print(f"\n=== risk-gate: CRAP Score Analysis (Threshold: < {args.threshold}) ===")
        print(f"{'File':<35} {'Line':<6} {'Function':<25} {'CC':<5} {'Cov%':<6} {'CRAP':<6} {'Status'}")
        print("-" * 92)
        for r in results:
            status = "FAIL" if r["violates"] else "PASS"
            cov_pct = f"{int(r['coverage'] * 100)}%"
            print(f"{r['file']:<35} {r['line']:<6} {r['name']:<25} {r['complexity']:<5} {cov_pct:<6} {r['crap']:<6.2f} {status}")

        print("\nSummary:")
        print(f"Total functions analyzed: {len(results)}")
        print(f"Functions violating CRAP < {args.threshold}: {len(violations)}")

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
