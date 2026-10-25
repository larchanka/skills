#!/usr/bin/env python3
"""
Dependency Graph Analyzer.
Processes import relationships from source files to identify:
- Entrypoints vs Core Hubs/Utilities
- Internal dependency graph (who imports whom)
- Third-party / external ecosystem dependencies
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

try:
    from common import load_json, save_json
except ImportError:
    from .common import load_json, save_json


def normalize_import_path(source_str: str, current_file: str, known_files: Set[str]) -> Tuple[str, bool]:
    """
    Attempts to match an import string to an internal project file.
    Returns (resolved_target_or_module, is_internal).
    """
    if not source_str:
        return "", False

    # Clean quotes or punctuation
    clean_src = source_str.strip("\"'; ()")

    # Relative path resolution (JS/TS/Python relative)
    if clean_src.startswith("."):
        curr_dir = Path(current_file).parent
        # Resolve relative to current directory and normalize path
        candidate = os.path.normpath((curr_dir / clean_src).as_posix()).replace("\\", "/")
        # Try matching with known file extensions
        for ext in ["", ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs"]:
            cand_with_ext = candidate + ext if ext else candidate
            if cand_with_ext in known_files:
                return cand_with_ext, True
            # Also check index files (e.g. foo/index.ts)
            index_cand = f"{candidate}/index{ext}"
            if index_cand in known_files:
                return index_cand, True

    # Absolute or package-style matching
    for kf in known_files:
        stem = Path(kf).stem
        kf_no_ext = Path(kf).with_suffix("").as_posix()
        # Direct match with file path or stem
        if clean_src == kf or clean_src == kf_no_ext:
            return kf, True
        # Match python dot-separated module path: foo.bar -> foo/bar.py
        dot_path = clean_src.replace(".", "/")
        if dot_path == kf_no_ext or dot_path in kf:
            return kf, True

    # If unmatched internally, classify as external dependency
    # Extract root package name (e.g. 'react-dom/client' -> 'react-dom')
    parts = clean_src.split("/")
    if parts[0].startswith("@") and len(parts) > 1:
        root_pkg = f"{parts[0]}/{parts[1]}"
    else:
        root_pkg = parts[0].split(".")[0]

    return root_pkg, False


def build_dependency_graph(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Builds internal and external dependency maps from AST manifest."""
    files_data = manifest.get("files", [])
    known_files: Set[str] = {f["path"] for f in files_data}

    internal_graph: Dict[str, List[str]] = {f: [] for f in known_files}
    reverse_graph: Dict[str, List[str]] = {f: [] for f in known_files}
    external_deps: Set[str] = set()
    file_external_deps: Dict[str, List[str]] = {f: [] for f in known_files}

    for f_entry in files_data:
        fpath = f_entry["path"]
        syms = f_entry.get("symbols", {})
        imports = syms.get("imports", [])

        for imp in imports:
            src = imp.get("source", "")
            if not src and "raw" in imp:
                raw_str = imp["raw"]
                # Heuristic extract from raw import line
                m = re.search(r"['\"]([^'\"]+)['\"]", raw_str)
                if m:
                    src = m.group(1)

            target, is_internal = normalize_import_path(src, fpath, known_files)
            if is_internal and target in known_files:
                if target not in internal_graph[fpath] and target != fpath:
                    internal_graph[fpath].append(target)
                if fpath not in reverse_graph[target] and target != fpath:
                    reverse_graph[target].append(fpath)
            elif not is_internal and target:
                # Filter out standard keywords or empty
                if target not in {"typing", "os", "sys", "re", "json", "pathlib", "math", "time"}:
                    external_deps.add(target)
                    if target not in file_external_deps[fpath]:
                        file_external_deps[fpath].append(target)

    # Calculate metrics
    # Entry points: files that nobody internally imports, but that import other things or have functions
    entrypoints = []
    # Hub modules: files that are heavily imported by others
    hubs = []

    for fpath in known_files:
        in_degree = len(reverse_graph[fpath])
        out_degree = len(internal_graph[fpath])

        if in_degree == 0 and out_degree > 0:
            entrypoints.append({
                "path": fpath,
                "out_degree": out_degree,
                "note": "Root orchestrator or CLI/service entry point"
            })
        elif in_degree >= 2:
            hubs.append({
                "path": fpath,
                "in_degree": in_degree,
                "imported_by": reverse_graph[fpath],
                "note": "Core shared component or utility hub"
            })

    entrypoints.sort(key=lambda x: x["out_degree"], reverse=True)
    hubs.sort(key=lambda x: x["in_degree"], reverse=True)

    return {
        "total_internal_edges": sum(len(v) for v in internal_graph.values()),
        "entrypoints": entrypoints,
        "hub_modules": hubs,
        "external_dependencies": sorted(list(external_deps)),
        "internal_graph": internal_graph,
        "reverse_graph": reverse_graph,
        "file_external_deps": file_external_deps,
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze dependency graph from AST manifest.")
    parser.add_argument("--manifest", "-m", type=str, default=".context_cache/ast_manifest.json", help="Path to AST manifest JSON.")
    parser.add_argument("--out", "-o", type=str, default=None, help="Output JSON path (default: .context_cache/dependency_graph.json).")

    args = parser.parse_args()
    manifest_path = Path(args.manifest).resolve()

    if not manifest_path.exists():
        print(f"Error: manifest file {manifest_path} not found. Run ast_scanner.py first.")
        sys.exit(1)

    manifest_data = load_json(manifest_path)
    graph = build_dependency_graph(manifest_data)

    out_file = Path(args.out) if args.out else (manifest_path.parent / "dependency_graph.json")
    save_json(graph, out_file)

    print(f"Dependency analysis complete:")
    print(f"- Total internal edges: {graph['total_internal_edges']}")
    print(f"- Identified {len(graph['entrypoints'])} potential entrypoints")
    print(f"- Identified {len(graph['hub_modules'])} core hub modules")
    print(f"- External dependencies detected: {len(graph['external_dependencies'])}")
    print(f"Saved graph to {out_file}")


if __name__ == "__main__":
    main()
