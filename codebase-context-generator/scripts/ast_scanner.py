#!/usr/bin/env python3
"""
Tree-sitter and AST-based codebase scanner.
Extracts symbols (classes, functions, interfaces, structs, imports, exports)
into a structured JSON manifest to generate AI context without exceeding context windows.
"""

import argparse
import ast
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    from common import (
        DEFAULT_IGNORE_DIRS,
        EXTENSION_TO_LANG,
        discover_source_files,
        get_parser_for_language,
        save_json,
    )
except ImportError:
    from .common import (
        DEFAULT_IGNORE_DIRS,
        EXTENSION_TO_LANG,
        discover_source_files,
        get_parser_for_language,
        save_json,
    )


def extract_python_ast(code_bytes: bytes, file_path: Path) -> Dict[str, Any]:
    """Extracts symbols from Python code using the standard library ast module."""
    symbols: Dict[str, Any] = {
        "classes": [],
        "functions": [],
        "interfaces_and_types": [],
        "imports": [],
        "exports": [],
        "callees": [],
    }
    try:
        source_text = code_bytes.decode("utf-8")
        parsed = ast.parse(source_text, filename=str(file_path))
    except Exception as e:
        symbols["parse_error"] = str(e)
        return symbols

    # Check for __all__
    for node in parsed.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                symbols["exports"].append(elt.value)

    for node in parsed.body:
        # Imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                symbols["imports"].append({
                    "source": alias.name,
                    "symbols": [alias.asname or alias.name],
                    "raw": f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else "")
                })
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            names = [a.asname or a.name for a in node.names]
            symbols["imports"].append({
                "source": mod,
                "symbols": names,
                "raw": f"from {mod} import " + ", ".join(names)
            })

        # Classes
        elif isinstance(node, ast.ClassDef):
            bases = []
            for b in node.bases:
                if isinstance(b, ast.Name):
                    bases.append(b.id)
                elif isinstance(b, ast.Attribute):
                    bases.append(f"{getattr(b.value, 'id', '')}.{b.attr}")
                else:
                    bases.append("...")

            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_args = []
                    for a in item.args.args:
                        anno = ast.unparse(a.annotation) if getattr(a, "annotation", None) else None
                        m_args.append({"name": a.arg, "type": anno})

                    ret_anno = ast.unparse(item.returns) if getattr(item, "returns", None) else None
                    arg_str = ", ".join([f"{a['name']}: {a['type']}" if a["type"] else a["name"] for a in m_args])
                    sig = f"{item.name}({arg_str})" + (f" -> {ret_anno}" if ret_anno else "")

                    calls = []
                    for c_node in ast.walk(item):
                        if isinstance(c_node, ast.Call):
                            try:
                                calls.append(ast.unparse(c_node.func))
                            except Exception:
                                pass

                    methods.append({
                        "name": item.name,
                        "signature": sig,
                        "args": m_args,
                        "return_type": ret_anno,
                        "callees": sorted(list(set(calls))),
                        "is_async": isinstance(item, ast.AsyncFunctionDef),
                        "docstring": ast.get_docstring(item) or "",
                        "line": item.lineno,
                    })

            symbols["classes"].append({
                "name": node.name,
                "bases": bases,
                "docstring": ast.get_docstring(node) or "",
                "line_start": node.lineno,
                "line_end": getattr(node, "end_lineno", node.lineno),
                "methods": methods,
            })

        # Functions
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            f_args = []
            for a in node.args.args:
                anno = ast.unparse(a.annotation) if getattr(a, "annotation", None) else None
                f_args.append({"name": a.arg, "type": anno})

            ret_anno = ast.unparse(node.returns) if getattr(node, "returns", None) else None
            arg_str = ", ".join([f"{a['name']}: {a['type']}" if a["type"] else a["name"] for a in f_args])
            sig = f"{node.name}({arg_str})" + (f" -> {ret_anno}" if ret_anno else "")

            calls = []
            for c_node in ast.walk(node):
                if isinstance(c_node, ast.Call):
                    try:
                        calls.append(ast.unparse(c_node.func))
                    except Exception:
                        pass

            symbols["functions"].append({
                "name": node.name,
                "signature": sig,
                "args": f_args,
                "return_type": ret_anno,
                "callees": sorted(list(set(calls))),
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "docstring": ast.get_docstring(node) or "",
                "line_start": node.lineno,
                "line_end": getattr(node, "end_lineno", node.lineno),
            })

        # Type aliases (TypeVar, NewType, etc.)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    symbols["interfaces_and_types"].append({
                        "name": target.id,
                        "kind": "type_alias",
                        "line": node.lineno,
                    })

    # Module-level calls (calls outside functions/classes)
    mod_calls = []
    for node in parsed.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for c_node in ast.walk(node):
                if isinstance(c_node, ast.Call):
                    try:
                        mod_calls.append(ast.unparse(c_node.func))
                    except Exception:
                        pass
    symbols["callees"] = sorted(list(set(mod_calls)))

    return symbols


def extract_node_text(node: Any, code_bytes: bytes) -> str:
    """Safely extracts UTF-8 string for a Tree-sitter node."""
    return code_bytes[node.start_byte:node.end_byte].decode("utf-8", "replace").strip()


def extract_tree_sitter_symbols(
    parser: Any,
    code_bytes: bytes,
    lang: str,
    file_path: Path
) -> Dict[str, Any]:
    """Extracts symbols using a Tree-sitter AST parser."""
    symbols: Dict[str, Any] = {
        "classes": [],
        "functions": [],
        "interfaces_and_types": [],
        "imports": [],
        "exports": [],
        "callees": [],
    }

    try:
        tree = parser.parse(code_bytes)
    except Exception as e:
        symbols["parse_error"] = str(e)
        return symbols

    root = tree.root_node

    def find_callees(node: Any) -> List[str]:
        calls = []
        def _rec(n):
            if n.type in ("call_expression", "method_invocation", "object_creation_expression"):
                fn_node = (
                    n.child_by_field_name("function")
                    or n.child_by_field_name("name")
                    or n.child_by_field_name("type")
                )
                if fn_node:
                    calls.append(extract_node_text(fn_node, code_bytes))
            for c in n.children:
                _rec(c)
        _rec(node)
        return sorted(list(set(calls)))

    def walk(node: Any):
        ntype = node.type

        # TypeScript / JavaScript / TSX
        if lang in ("typescript", "tsx", "javascript"):
            if ntype in ("class_declaration", "abstract_class_declaration"):
                name_node = node.child_by_field_name("name")
                name = extract_node_text(name_node, code_bytes) if name_node else "Anonymous"
                symbols["classes"].append({
                    "name": name,
                    "line_start": node.start_point.row + 1,
                    "line_end": node.end_point.row + 1,
                })
            elif ntype in ("interface_declaration", "type_alias_declaration", "enum_declaration"):
                name_node = node.child_by_field_name("name")
                name = extract_node_text(name_node, code_bytes) if name_node else "Anonymous"
                symbols["interfaces_and_types"].append({
                    "name": name,
                    "kind": ntype.replace("_declaration", ""),
                    "line": node.start_point.row + 1,
                })
            elif ntype in ("function_declaration", "generator_function_declaration"):
                name_node = node.child_by_field_name("name")
                name = extract_node_text(name_node, code_bytes) if name_node else "Anonymous"
                params_node = node.child_by_field_name("parameters")
                params = extract_node_text(params_node, code_bytes) if params_node else "()"
                ret_node = node.child_by_field_name("return_type")
                ret = extract_node_text(ret_node, code_bytes) if ret_node else ""
                sig = f"{name}{params}" + (f" {ret}" if ret else "")
                callees = find_callees(node)

                symbols["functions"].append({
                    "name": name,
                    "signature": sig,
                    "callees": callees,
                    "line_start": node.start_point.row + 1,
                    "line_end": node.end_point.row + 1,
                })
            elif ntype == "method_definition":
                name_node = node.child_by_field_name("name")
                name = extract_node_text(name_node, code_bytes) if name_node else "Anonymous"
                params_node = node.child_by_field_name("parameters")
                params = extract_node_text(params_node, code_bytes) if params_node else "()"
                ret_node = node.child_by_field_name("return_type")
                ret = extract_node_text(ret_node, code_bytes) if ret_node else ""
                sig = f"{name}{params}" + (f" {ret}" if ret else "")
                callees = find_callees(node)

                symbols["functions"].append({
                    "name": name,
                    "signature": sig,
                    "callees": callees,
                    "line_start": node.start_point.row + 1,
                    "line_end": node.end_point.row + 1,
                })
            elif ntype == "variable_declarator":
                val_node = node.child_by_field_name("value")
                if val_node and val_node.type in ("arrow_function", "function_expression"):
                    name_node = node.child_by_field_name("name")
                    name = extract_node_text(name_node, code_bytes) if name_node else "Anonymous"
                    params_node = val_node.child_by_field_name("parameters")
                    params = extract_node_text(params_node, code_bytes) if params_node else "()"
                    ret_node = val_node.child_by_field_name("return_type")
                    ret = extract_node_text(ret_node, code_bytes) if ret_node else ""
                    sig = f"{name}{params}" + (f" {ret}" if ret else "")
                    callees = find_callees(val_node)

                    symbols["functions"].append({
                        "name": name,
                        "signature": sig,
                        "callees": callees,
                        "line_start": node.start_point.row + 1,
                        "line_end": node.end_point.row + 1,
                    })
            elif ntype == "import_statement":
                raw = extract_node_text(node, code_bytes)
                source_node = node.child_by_field_name("source")
                source = extract_node_text(source_node, code_bytes).strip("\"'") if source_node else ""
                symbols["imports"].append({
                    "source": source,
                    "raw": raw,
                })
            elif ntype == "export_statement":
                decl = node.child_by_field_name("declaration")
                if decl:
                    walk(decl)
                else:
                    symbols["exports"].append(extract_node_text(node, code_bytes))
                return

        # Go
        elif lang == "go":
            if ntype == "type_declaration":
                raw = extract_node_text(node, code_bytes)
                symbols["interfaces_and_types"].append({
                    "name": raw.split("\n")[0],
                    "kind": "go_type",
                    "line": node.start_point.row + 1,
                })
            elif ntype in ("function_declaration", "method_declaration"):
                name_node = node.child_by_field_name("name")
                name = extract_node_text(name_node, code_bytes) if name_node else "Anonymous"
                params_node = node.child_by_field_name("parameters")
                params = extract_node_text(params_node, code_bytes) if params_node else "()"
                result_node = node.child_by_field_name("result")
                ret = extract_node_text(result_node, code_bytes) if result_node else ""
                sig = f"func {name}{params}" + (f" {ret}" if ret else "")
                callees = find_callees(node)

                symbols["functions"].append({
                    "name": name,
                    "signature": sig,
                    "callees": callees,
                    "line_start": node.start_point.row + 1,
                    "line_end": node.end_point.row + 1,
                })
            elif ntype == "import_declaration":
                symbols["imports"].append({
                    "raw": extract_node_text(node, code_bytes),
                    "source": extract_node_text(node, code_bytes),
                })

        # Rust
        elif lang == "rust":
            if ntype in ("struct_item", "enum_item", "union_item"):
                name_node = node.child_by_field_name("name")
                name = extract_node_text(name_node, code_bytes) if name_node else "Anonymous"
                symbols["classes"].append({
                    "name": name,
                    "kind": ntype.replace("_item", ""),
                    "line_start": node.start_point.row + 1,
                    "line_end": node.end_point.row + 1,
                })
            elif ntype == "trait_item":
                name_node = node.child_by_field_name("name")
                name = extract_node_text(name_node, code_bytes) if name_node else "Anonymous"
                symbols["interfaces_and_types"].append({
                    "name": name,
                    "kind": "trait",
                    "line": node.start_point.row + 1,
                })
            elif ntype == "function_item":
                name_node = node.child_by_field_name("name")
                name = extract_node_text(name_node, code_bytes) if name_node else "Anonymous"
                params_node = node.child_by_field_name("parameters")
                params = extract_node_text(params_node, code_bytes) if params_node else "()"
                ret_node = node.child_by_field_name("return_type")
                ret = extract_node_text(ret_node, code_bytes) if ret_node else ""
                sig = f"fn {name}{params}" + (f" {ret}" if ret else "")
                callees = find_callees(node)

                symbols["functions"].append({
                    "name": name,
                    "signature": sig,
                    "callees": callees,
                    "line_start": node.start_point.row + 1,
                    "line_end": node.end_point.row + 1,
                })
            elif ntype == "use_declaration":
                symbols["imports"].append({
                    "raw": extract_node_text(node, code_bytes),
                    "source": extract_node_text(node, code_bytes),
                })

        # Java
        elif lang == "java":
            if ntype in ("class_declaration", "record_declaration"):
                name_node = node.child_by_field_name("name")
                name = extract_node_text(name_node, code_bytes) if name_node else "Anonymous"
                symbols["classes"].append({
                    "name": name,
                    "line_start": node.start_point.row + 1,
                    "line_end": node.end_point.row + 1,
                })
            elif ntype in ("interface_declaration", "enum_declaration", "annotation_type_declaration"):
                name_node = node.child_by_field_name("name")
                name = extract_node_text(name_node, code_bytes) if name_node else "Anonymous"
                symbols["interfaces_and_types"].append({
                    "name": name,
                    "kind": ntype.replace("_declaration", ""),
                    "line": node.start_point.row + 1,
                })
            elif ntype == "method_declaration":
                name_node = node.child_by_field_name("name")
                name = extract_node_text(name_node, code_bytes) if name_node else "Anonymous"
                params_node = node.child_by_field_name("parameters")
                params = extract_node_text(params_node, code_bytes) if params_node else "()"
                type_node = node.child_by_field_name("type")
                ret = extract_node_text(type_node, code_bytes) if type_node else ""
                sig = f"{name}{params}" + (f" -> {ret}" if ret else "")
                callees = find_callees(node)
                symbols["functions"].append({
                    "name": name,
                    "signature": sig,
                    "callees": callees,
                    "line_start": node.start_point.row + 1,
                    "line_end": node.end_point.row + 1,
                })
            elif ntype == "import_declaration":
                symbols["imports"].append({
                    "raw": extract_node_text(node, code_bytes),
                    "source": extract_node_text(node, code_bytes),
                })

        # Recurse child nodes
        for child in node.children:
            walk(child)

    walk(root)
    return symbols


def extract_regex_symbols(code_bytes: bytes, lang: str) -> Dict[str, Any]:
    """Lightweight fallback symbol extraction using regex heuristics."""
    symbols: Dict[str, Any] = {
        "classes": [],
        "functions": [],
        "interfaces_and_types": [],
        "imports": [],
        "exports": [],
        "callees": [],
    }
    text = code_bytes.decode("utf-8", "replace")
    lines = text.split("\n")

    call_keywords = {
        "if", "for", "while", "switch", "catch", "function", "class", "constructor",
        "import", "export", "return", "throw", "typeof", "super", "new", "require",
        "else", "try", "finally", "with", "yield", "await", "delete", "void", "in",
        "instanceof", "type", "interface", "get", "set", "from", "as", "default", "case",
        "let", "const", "var"
    }
    call_re = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")

    def extract_calls(code_text: str, current_name: Optional[str] = None) -> List[str]:
        cleaned = re.sub(r"\"[^\"]*\"|\'[^\']*\'|\`[^\`]*\`|//.*|/\*[\s\S]*?\*/|#.*", "", code_text)
        raw = call_re.findall(cleaned)
        return sorted(list(set(c for c in raw if c not in call_keywords and c != current_name)))

    class_re = re.compile(r"^\s*(?:export\s+)?(?:(?:public|private|protected|abstract|sealed|final|declare|static)\s+)*(class|struct|trait)\s+([A-Za-z0-9_]+)")
    type_re = re.compile(r"^\s*(?:export\s+)?(?:(?:public|declare)\s+)*(interface|type|enum)\s+([A-Za-z0-9_]+)")
    func_re = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:function|def|fn|func|sub)\s+([A-Za-z0-9_]+)\s*(\([^)]*\))?(?:\s*(?:->|:)\s*([^{:\n]+))?")
    arrow_re = re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s*)?(?:(\([^)]*\)|[A-Za-z0-9_]+))\s*(?::\s*([^{=\n]+))?\s*=>")
    method_re = re.compile(r"^\s*(?:(?:public|private|protected|static|async|override|readonly|abstract)\s+)+([A-Za-z0-9_]+)\s*(\([^)]*\))(?:\s*(?:->|:)\s*([^{:\n]+))?")
    bare_method_re = re.compile(r"^\s*(?:async\s+)?([A-Za-z0-9_]+)\s*(\([^)]*\))(?:\s*(?:->|:)\s*([^{:\n]+))?\s*\{")
    import_re = re.compile(r"^\s*(?:import\s+|from\s+|use\s+|require\()([^;\n]+)")

    # 1. Track class scopes via brace tracking
    active_class: Optional[Dict[str, Any]] = None
    brace_depth = 0

    for idx, line in enumerate(lines, 1):
        cleaned = re.sub(r"\"[^\"]*\"|\'[^\']*\'|\`[^\`]*\`|//.*|/\*[\s\S]*?\*/|#.*", "", line)
        if not active_class:
            cm = class_re.search(line)
            if cm:
                c_name = cm.group(2)
                c_kind = cm.group(1)
                active_class = {
                    "name": c_name,
                    "kind": c_kind,
                    "line_start": idx,
                    "methods": [],
                }
                brace_depth = cleaned.count("{") - cleaned.count("}")
                symbols["classes"].append(active_class)
        else:
            brace_depth += cleaned.count("{") - cleaned.count("}")
            if brace_depth <= 0:
                active_class["line_end"] = idx
                active_class = None

    if active_class:
        active_class["line_end"] = len(lines)

    # 2. Extract types, imports, and collect all callable declarations
    callable_decls = []

    for idx, line in enumerate(lines, 1):
        i_match = import_re.search(line)
        if i_match:
            symbols["imports"].append({"raw": line.strip(), "source": i_match.group(1).strip()})

        t_match = type_re.search(line)
        if t_match:
            symbols["interfaces_and_types"].append({
                "name": t_match.group(2),
                "kind": t_match.group(1),
                "line": idx,
            })
            continue

        if any(c["line_start"] == idx for c in symbols["classes"]):
            continue

        in_class = any(c["line_start"] <= idx <= c.get("line_end", len(lines)) for c in symbols["classes"])

        m_match = method_re.search(line)
        if m_match and m_match.group(1) not in call_keywords:
            m_name = m_match.group(1)
            args = m_match.group(2) or "()"
            ret = f" -> {m_match.group(3).strip()}" if m_match.group(3) else ""
            sig = f"{m_name}{args}{ret}"
            callable_decls.append((idx, "method" if in_class else "func", m_name, sig))
            continue

        if in_class:
            bm_match = bare_method_re.search(line)
            if bm_match and bm_match.group(1) not in call_keywords:
                m_name = bm_match.group(1)
                args = bm_match.group(2) or "()"
                ret = f" -> {bm_match.group(3).strip()}" if bm_match.group(3) else ""
                sig = f"{m_name}{args}{ret}"
                callable_decls.append((idx, "method", m_name, sig))
                continue

        f_match = func_re.search(line)
        if f_match and f_match.group(1) not in call_keywords:
            f_name = f_match.group(1)
            args = f_match.group(2) or "()"
            ret = f" -> {f_match.group(3).strip()}" if f_match.group(3) else ""
            sig = f"{f_name}{args}{ret}"
            callable_decls.append((idx, "method" if in_class else "func", f_name, sig))
            continue

        a_match = arrow_re.search(line)
        if a_match and a_match.group(1) not in call_keywords:
            a_name = a_match.group(1)
            args = a_match.group(2) if a_match.group(2).startswith("(") else f"({a_match.group(2)})"
            ret = f" -> {a_match.group(3).strip()}" if a_match.group(3) else ""
            sig = f"{a_name}{args}{ret}"
            callable_decls.append((idx, "func", a_name, sig))
            continue

    # 3. Compute function/method bodies and callees
    callable_decls.sort(key=lambda d: d[0])
    covered_lines = set()

    for i, (line_num, kind, name, sig) in enumerate(callable_decls):
        next_line = callable_decls[i + 1][0] if i + 1 < len(callable_decls) else len(lines) + 1
        body_lines = lines[line_num - 1:next_line - 1]
        for l_idx in range(line_num, next_line):
            covered_lines.add(l_idx)
        body_text = "\n".join(body_lines)
        callees = extract_calls(body_text, current_name=name)

        parent_class = None
        for c in symbols["classes"]:
            if c["line_start"] <= line_num <= c.get("line_end", len(lines)):
                parent_class = c
                break

        if kind == "method" and parent_class:
            parent_class["methods"].append({
                "name": name,
                "signature": sig,
                "line": line_num,
                "callees": callees,
            })
        else:
            symbols["functions"].append({
                "name": name,
                "signature": sig,
                "line_start": line_num,
                "callees": callees,
            })

    uncovered_lines = [line for idx, line in enumerate(lines, 1) if idx not in covered_lines]
    if uncovered_lines:
        symbols["callees"] = extract_calls("\n".join(uncovered_lines))

    return symbols


def scan_file(file_path: Path, root_path: Path) -> Dict[str, Any]:
    """Analyzes a single source file, extracting AST symbols and metadata."""
    rel_path = file_path.relative_to(root_path).as_posix()
    ext = file_path.suffix.lower()
    lang = EXTENSION_TO_LANG.get(ext, "unknown")

    try:
        raw_bytes = file_path.read_bytes()
    except Exception as e:
        return {
            "path": rel_path,
            "language": lang,
            "error": f"Failed to read file: {e}",
            "lines": 0,
            "size_bytes": 0,
        }

    line_count = raw_bytes.count(b"\n") + (1 if raw_bytes else 0)

    # 1. Native Python AST parsing
    if lang == "python":
        symbols = extract_python_ast(raw_bytes, file_path)
        symbols["parser"] = "python_ast"

    # 2. Tree-sitter parsing
    else:
        parser = get_parser_for_language(lang)
        if parser:
            symbols = extract_tree_sitter_symbols(parser, raw_bytes, lang, file_path)
            symbols["parser"] = f"tree_sitter_{lang}"
        else:
            symbols = extract_regex_symbols(raw_bytes, lang)
            symbols["parser"] = "regex_fallback"

    return {
        "path": rel_path,
        "language": lang,
        "extension": ext,
        "lines": line_count,
        "size_bytes": len(raw_bytes),
        "parser": symbols.get("parser"),
        "symbols": symbols,
    }


def scan_codebase(
    root_path: Path,
    extra_ignores: Optional[Set[str]] = None,
    allowed_extensions: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """Scans the entire repository and returns a structured AST manifest."""
    root = root_path.resolve()
    files = discover_source_files(root, extra_ignores=extra_ignores, allowed_extensions=allowed_extensions)

    file_results: List[Dict[str, Any]] = []
    lang_stats: Dict[str, int] = {}
    total_lines = 0
    total_symbols = 0

    for f in files:
        res = scan_file(f, root)
        file_results.append(res)

        lang = res.get("language", "unknown")
        lang_stats[lang] = lang_stats.get(lang, 0) + 1
        total_lines += res.get("lines", 0)

        syms = res.get("symbols", {})
        s_count = (
            len(syms.get("classes", []))
            + len(syms.get("functions", []))
            + len(syms.get("interfaces_and_types", []))
        )
        total_symbols += s_count

    return {
        "root": str(root),
        "total_files": len(files),
        "total_lines": total_lines,
        "total_symbols": total_symbols,
        "languages": lang_stats,
        "files": file_results,
    }


def main():
    parser = argparse.ArgumentParser(description="Tree-sitter and AST symbol extractor for codebase context.")
    parser.add_argument("--root", "-r", type=str, default=".", help="Root path of target codebase.")
    parser.add_argument("--out", "-o", type=str, default=None, help="Output JSON path (default: .context_cache/ast_manifest.json).")
    parser.add_argument("--summary", action="store_true", help="Print summary to stdout instead of full JSON.")

    args = parser.parse_args()
    root_path = Path(args.root).resolve()

    manifest = scan_codebase(root_path)

    out_file = Path(args.out) if args.out else (root_path / ".context_cache" / "ast_manifest.json")
    save_json(manifest, out_file)

    if args.summary:
        print(f"Codebase Scan Summary for: {root_path}")
        print(f"Total Files Scanned: {manifest['total_files']}")
        print(f"Total Lines of Code: {manifest['total_lines']}")
        print(f"Total Symbols Extracted: {manifest['total_symbols']}")
        print(f"Languages: {manifest['languages']}")
        print(f"Manifest saved to: {out_file}")
    else:
        print(f"Wrote AST manifest with {manifest['total_files']} files to {out_file}")


if __name__ == "__main__":
    main()
