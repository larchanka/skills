#!/usr/bin/env python3
"""
Symbol & Call Graph Generator and Navigator.
Builds a function-level, method-level, and class-level call/reference graph with full signatures.
Allows AI agents to quickly query signatures, argument types, callers, and callees across the codebase.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from common import load_json, save_json
except ImportError:
    from .common import load_json, save_json


def build_symbol_graph(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constructs a symbol dictionary and cross-references caller-callee relationships.
    """
    symbols: Dict[str, Dict[str, Any]] = {}
    name_to_ids: Dict[str, List[str]] = defaultdict(list)

    files_data = manifest.get("files", [])

    for f_entry in files_data:
        fpath = f_entry.get("path", "")
        file_syms = f_entry.get("symbols", {})

        # 1. Functions
        for fn in file_syms.get("functions", []):
            fn_name = fn.get("name", "")
            sym_id = f"{fpath}::{fn_name}"
            sig = fn.get("signature") or f"{fn_name}()"
            symbols[sym_id] = {
                "id": sym_id,
                "name": fn_name,
                "kind": "function",
                "path": fpath,
                "line": fn.get("line_start", fn.get("line", 1)),
                "signature": sig,
                "args": fn.get("args", []),
                "return_type": fn.get("return_type"),
                "docstring": fn.get("docstring", ""),
                "callees": fn.get("callees", []),
                "callers": [],
            }
            name_to_ids[fn_name].append(sym_id)

        # 2. Classes and their methods
        for cls in file_syms.get("classes", []):
            cls_name = cls.get("name", "")
            cls_id = f"{fpath}::{cls_name}"
            symbols[cls_id] = {
                "id": cls_id,
                "name": cls_name,
                "kind": "class",
                "path": fpath,
                "line": cls.get("line_start", cls.get("line", 1)),
                "signature": f"class {cls_name}",
                "bases": cls.get("bases", []),
                "docstring": cls.get("docstring", ""),
                "callees": [],
                "callers": [],
            }
            name_to_ids[cls_name].append(cls_id)

            for m in cls.get("methods", []):
                m_name = m.get("name", "")
                m_id = f"{fpath}::{cls_name}.{m_name}"
                sig = m.get("signature") or f"{m_name}()"
                symbols[m_id] = {
                    "id": m_id,
                    "name": f"{cls_name}.{m_name}",
                    "kind": "method",
                    "path": fpath,
                    "line": m.get("line", 1),
                    "signature": sig,
                    "args": m.get("args", []),
                    "return_type": m.get("return_type"),
                    "docstring": m.get("docstring", ""),
                    "callees": m.get("callees", []),
                    "callers": [],
                }
                name_to_ids[m_name].append(m_id)
                name_to_ids[f"{cls_name}.{m_name}"].append(m_id)

        # 3. Interfaces and Types
        for item in file_syms.get("interfaces_and_types", []):
            item_name = item.get("name", "")
            item_id = f"{fpath}::{item_name}"
            symbols[item_id] = {
                "id": item_id,
                "name": item_name,
                "kind": item.get("kind", "type"),
                "path": fpath,
                "line": item.get("line", 1),
                "signature": f"{item.get('kind', 'type')} {item_name}",
                "args": [],
                "docstring": "",
                "callees": [],
                "callers": [],
            }
            name_to_ids[item_name].append(item_id)

    # Resolve cross-reference calls
    for sym_id, sym_data in symbols.items():
        for callee_raw in sym_data.get("callees", []):
            callee_name = callee_raw.split(".")[-1]
            matches = name_to_ids.get(callee_raw) or name_to_ids.get(callee_name)
            if matches:
                for target_id in matches:
                    if target_id != sym_id and sym_id not in symbols[target_id]["callers"]:
                        symbols[target_id]["callers"].append(sym_id)

    return {
        "total_symbols": len(symbols),
        "symbols": symbols,
        "name_index": dict(name_to_ids),
    }


def export_signatures_markdown(graph: Dict[str, Any]) -> str:
    """Renders a comprehensive signature dictionary in Markdown for AI agent navigation."""
    symbols = graph.get("symbols", {})
    by_file: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for sym in symbols.values():
        by_file[sym["path"]].append(sym)

    lines = [
        "# Codebase Signatures & Symbol Index",
        "",
        "Quick-reference catalog of function and method signatures, arguments, and return types.",
        "",
    ]

    for fpath in sorted(by_file.keys()):
        file_syms = by_file[fpath]
        lines.append(f"## [`{fpath}`](../{fpath})")
        lines.append("")

        classes = [s for s in file_syms if s["kind"] == "class"]
        methods = [s for s in file_syms if s["kind"] == "method"]
        functions = [s for s in file_syms if s["kind"] == "function"]
        types = [s for s in file_syms if s["kind"] not in ("class", "method", "function")]

        if classes:
            lines.append("### Classes")
            for c in classes:
                lines.append(f"- **`{c['signature']}`** (L{c['line']})")
                if c.get("docstring"):
                    lines.append(f"  *{c['docstring'].strip().splitlines()[0]}*")
            lines.append("")

        if functions or methods:
            lines.append("### Functions & Methods")
            lines.append("| Symbol | Signature | Line | Callers |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for fn in functions + methods:
                sig = fn["signature"].replace("|", "\\|")
                callers_count = len(fn.get("callers", []))
                lines.append(f"| `{fn['name']}` | `{sig}` | L{fn['line']} | {callers_count} |")
            lines.append("")

        if types:
            lines.append("### Types & Interfaces")
            for t in types:
                lines.append(f"- `{t['signature']}` (L{t['line']})")
            lines.append("")

    return "\n".join(lines)


def query_symbol(graph: Dict[str, Any], query_str: str) -> List[Dict[str, Any]]:
    """Finds symbols matching query_str exactly or by substring."""
    symbols = graph.get("symbols", {})
    results = []

    q_lower = query_str.lower()
    for sym_id, sym in symbols.items():
        if query_str == sym["name"] or query_str == sym_id:
            # Exact match prioritized
            results.insert(0, sym)
        elif q_lower in sym["name"].lower() or q_lower in sym_id.lower():
            results.append(sym)

    return results


def main():
    parser = argparse.ArgumentParser(description="Query or export Symbol & Call Graph.")
    parser.add_argument("--manifest", "-m", type=str, default=".context_cache/ast_manifest.json", help="Path to AST manifest.")
    parser.add_argument("--save-graph", "-s", type=str, default=None, help="Save symbol graph JSON to path.")
    parser.add_argument("--export-signatures", "-e", type=str, default=None, help="Export signatures to Markdown file.")
    parser.add_argument("--find", "-f", type=str, default=None, help="Search for a symbol by name.")
    parser.add_argument("--callers", "-c", type=str, default=None, help="Find callers of a symbol.")
    parser.add_argument("--callees", type=str, default=None, help="Find callees invoked by a symbol.")

    args = parser.parse_args()
    manifest_path = Path(args.manifest).resolve()

    if not manifest_path.exists():
        print(f"Error: manifest {manifest_path} not found. Run ast_scanner.py first.")
        sys.exit(1)

    manifest_data = load_json(manifest_path)
    graph = build_symbol_graph(manifest_data)

    if args.save_graph:
        out_p = Path(args.save_graph)
        save_json(graph, out_p)
        print(f"Saved symbol graph with {graph['total_symbols']} symbols to {out_p}")

    if args.export_signatures:
        sig_p = Path(args.export_signatures)
        sig_p.parent.mkdir(parents=True, exist_ok=True)
        md_text = export_signatures_markdown(graph)
        sig_p.write_text(md_text, encoding="utf-8")
        print(f"Exported signature documentation to {sig_p}")

    if args.find:
        matches = query_symbol(graph, args.find)
        if not matches:
            print(f"No symbols matching '{args.find}' found.")
        else:
            print(f"Found {len(matches)} matching symbol(s):")
            for m in matches:
                print(f"\n[{m['kind'].upper()}] {m['id']}")
                print(f"  Signature: {m['signature']}")
                print(f"  Location:  {m['path']}:{m['line']}")
                if m.get("docstring"):
                    print(f"  Doc:       {m['docstring'].strip().splitlines()[0]}")
                print(f"  Callers:   {len(m.get('callers', []))} caller(s)")
                if m.get("callees"):
                    print(f"  Callees:   {m['callees']}")

    if args.callers:
        matches = query_symbol(graph, args.callers)
        if not matches:
            print(f"Symbol '{args.callers}' not found.")
        else:
            for m in matches:
                print(f"\nCallers for {m['id']}:")
                if not m.get("callers"):
                    print("  (No internal callers detected)")
                for c in m["callers"]:
                    print(f"  <- {c}")

    if args.callees:
        matches = query_symbol(graph, args.callees)
        if not matches:
            print(f"Symbol '{args.callees}' not found.")
        else:
            for m in matches:
                print(f"\nCallees called by {m['id']}:")
                if not m.get("callees"):
                    print("  (No internal calls detected)")
                for c in m["callees"]:
                    print(f"  -> {c}")


if __name__ == "__main__":
    main()
