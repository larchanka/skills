#!/usr/bin/env python3
"""
clone-check (Structural Code Duplication Detector)

Detects structural code duplication using AST normalization and Jaccard similarity.
Flags duplicate function pairs with similarity >= 0.8.
"""

import ast
import argparse
import json
import os
import sys
from typing import Set, List, Dict, Tuple, Any


def extract_fingerprints(node: ast.AST) -> Set[str]:
    """Extract structural fingerprint tokens from an AST node.
    Normalizes variable names, literals, and docstrings while preserving
    structural AST types, operations, and control flow paths.
    """
    tokens: List[str] = []

    for child in ast.walk(node):
        # Ignore docstrings and comments (ast.Constant strings at function top level)
        if isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant) and isinstance(child.value.value, str):
            continue

        # Structural AST node type name
        node_type = type(child).__name__

        # Append operators and control flow indicators specifically
        if isinstance(child, ast.operator):
            tokens.append(f"OP:{node_type}")
        elif isinstance(child, ast.cmpop):
            tokens.append(f"CMP:{node_type}")
        elif isinstance(child, ast.boolop):
            tokens.append(f"BOOL:{node_type}")
        elif isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.Return, ast.Call, ast.Assign)):
            tokens.append(f"STMT:{node_type}")
        else:
            tokens.append(node_type)

    # Generate 2-gram fingerprints to capture local structural sequences
    fingerprints: Set[str] = set()
    for i in range(len(tokens) - 1):
        fingerprints.add(f"{tokens[i]}->{tokens[i+1]}")
    if tokens:
        fingerprints.add(tokens[0])

    return fingerprints


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Compute Jaccard similarity coefficient: |A n B| / |A u B|."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0


def find_clones_in_code(
    code: str,
    threshold: float = 0.8,
    min_lines: int = 4,
    filename: str = "<string>",
) -> List[Dict[str, Any]]:
    """Scan code string for functions with structural similarity >= threshold."""
    try:
        tree = ast.parse(code, filename=filename)
    except Exception:
        return []

    functions: List[Dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Check function length in lines
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            line_count = end_line - start_line + 1

            if line_count >= min_lines:
                fp = extract_fingerprints(node)
                functions.append({
                    "name": node.name,
                    "file": filename,
                    "line": start_line,
                    "lines_count": line_count,
                    "fingerprints": fp,
                })

    clones: List[Dict[str, Any]] = []
    n = len(functions)

    for i in range(n):
        for j in range(i + 1, n):
            f1 = functions[i]
            f2 = functions[j]
            sim = jaccard_similarity(f1["fingerprints"], f2["fingerprints"])
            if sim >= threshold:
                clones.append({
                    "func1": f1["name"],
                    "file1": f1["file"],
                    "line1": f1["line"],
                    "func2": f2["name"],
                    "file2": f2["file"],
                    "line2": f2["line"],
                    "similarity": round(sim, 2),
                    "threshold": threshold,
                })

    return clones


def scan_directory(
    dirpath: str,
    threshold: float = 0.8,
    min_lines: int = 4,
) -> List[Dict[str, Any]]:
    """Scan all Python files across directory for cross-function and cross-file clones."""
    exclude_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}
    all_functions: List[Dict[str, Any]] = []

    for root, dirs, files in os.walk(dirpath):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            if f.endswith(".py"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path)
                try:
                    with open(full_path, "r", encoding="utf-8") as file_obj:
                        content = file_obj.read()
                    tree = ast.parse(content, filename=rel_path)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            start_line = node.lineno
                            end_line = getattr(node, "end_lineno", start_line)
                            line_count = end_line - start_line + 1
                            if line_count >= min_lines:
                                fp = extract_fingerprints(node)
                                all_functions.append({
                                    "name": node.name,
                                    "file": rel_path,
                                    "line": start_line,
                                    "lines_count": line_count,
                                    "fingerprints": fp,
                                })
                except Exception:
                    continue

    clones: List[Dict[str, Any]] = []
    n = len(all_functions)
    for i in range(n):
        for j in range(i + 1, n):
            f1 = all_functions[i]
            f2 = all_functions[j]
            sim = jaccard_similarity(f1["fingerprints"], f2["fingerprints"])
            if sim >= threshold:
                clones.append({
                    "func1": f1["name"],
                    "file1": f1["file"],
                    "line1": f1["line"],
                    "func2": f2["name"],
                    "file2": f2["file"],
                    "line2": f2["line"],
                    "similarity": round(sim, 2),
                    "threshold": threshold,
                })

    return clones


def main() -> int:
    parser = argparse.ArgumentParser(description="clone-check: Detect structural duplication >= threshold (default: 0.8)")
    parser.add_argument("path", nargs="?", default=".", help="File or directory to scan")
    parser.add_argument("--threshold", type=float, default=0.8, help="Duplication similarity threshold (default: 0.8)")
    parser.add_argument("--min-lines", type=int, default=4, help="Minimum function line count to evaluate (default: 4)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    if os.path.isfile(args.path):
        with open(args.path, "r", encoding="utf-8") as f:
            code = f.read()
        clones = find_clones_in_code(code, args.threshold, args.min_lines, args.path)
    else:
        clones = scan_directory(args.path, args.threshold, args.min_lines)

    clones.sort(key=lambda c: c["similarity"], reverse=True)

    if args.json:
        print(json.dumps({"clones": clones, "count": len(clones)}, indent=2))
    else:
        print(f"\n=== clone-check: Structural Duplication (Threshold: >= {args.threshold}) ===")
        print(f"{'Target A (Location)':<40} {'Target B (Location)':<40} {'Similarity'}")
        print("-" * 92)
        for c in clones:
            target_a = f"{c['file1']}:{c['line1']} ({c['func1']})"
            target_b = f"{c['file2']}:{c['line2']} ({c['func2']})"
            print(f"{target_a:<40} {target_b:<40} {c['similarity']:<6.2f}")

        print(f"\nTotal duplicate pairs found: {len(clones)}")
        if clones:
            print("Action required: Eliminate structural duplication ranked 0.8 or above by extracting shared abstractions.")

    return 1 if clones else 0


if __name__ == "__main__":
    sys.exit(main())
