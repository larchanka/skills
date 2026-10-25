#!/usr/bin/env python3
"""Shared helper utilities and Tree-sitter loader for codebase-context-generator."""

import importlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Standard directories and files to exclude from codebase scanning
DEFAULT_IGNORE_DIRS: Set[str] = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "node_modules",
    "vendor",
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "target",
    "build",
    "dist",
    "out",
    "bin",
    "obj",
    ".next",
    ".nuxt",
    ".cache",
    "coverage",
    ".turbo",
    "Pods",
}

# Mapping file extensions to language identifiers
EXTENSION_TO_LANG: Dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
    ".tsx": "tsx",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".php": "php",
    ".dart": "dart",
    ".rb": "ruby",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    ".cs": "c_sharp",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
}

# Mapping language name to tree-sitter python module and function candidates
GRAMMAR_MODULE_MAP: Dict[str, Tuple[str, List[str]]] = {
    "python": ("tree_sitter_python", ["language", "language_python"]),
    "typescript": ("tree_sitter_typescript", ["language_typescript", "language"]),
    "tsx": ("tree_sitter_typescript", ["language_tsx", "language"]),
    "javascript": ("tree_sitter_javascript", ["language", "language_javascript"]),
    "go": ("tree_sitter_go", ["language", "language_go"]),
    "rust": ("tree_sitter_rust", ["language", "language_rust"]),
    "java": ("tree_sitter_java", ["language", "language_java"]),
    "php": ("tree_sitter_php", ["language_php", "language"]),
    "dart": ("tree_sitter_dart_orchard", ["language", "language_dart"]),
    "c": ("tree_sitter_c", ["language", "language_c"]),
    "cpp": ("tree_sitter_cpp", ["language", "language_cpp"]),
    "c_sharp": ("tree_sitter_c_sharp", ["language", "language_c_sharp"]),
    "ruby": ("tree_sitter_ruby", ["language", "language_ruby"]),
}

_LOADED_LANGUAGES: Dict[str, Any] = {}
_PARSER_CACHE: Dict[str, Any] = {}


def load_tree_sitter_language(lang_name: str) -> Optional[Any]:
    """Dynamically loads and returns a tree-sitter Language object for lang_name."""
    if lang_name in _LOADED_LANGUAGES:
        return _LOADED_LANGUAGES[lang_name]

    if lang_name not in GRAMMAR_MODULE_MAP:
        return None

    try:
        from tree_sitter import Language
    except ImportError:
        return None

    mod_name, func_names = GRAMMAR_MODULE_MAP[lang_name]
    try:
        mod = importlib.import_module(mod_name)
        for fn_name in func_names:
            if hasattr(mod, fn_name):
                fn = getattr(mod, fn_name)
                ptr = fn()
                # Depending on tree-sitter version, Language() takes pointer or is created directly
                try:
                    lang = Language(ptr)
                except Exception:
                    lang = ptr
                _LOADED_LANGUAGES[lang_name] = lang
                return lang
    except Exception:
        pass

    return None


def get_parser_for_language(lang_name: str) -> Optional[Any]:
    """Returns a cached tree_sitter.Parser instance for lang_name."""
    if lang_name in _PARSER_CACHE:
        return _PARSER_CACHE[lang_name]

    lang = load_tree_sitter_language(lang_name)
    if not lang:
        return None

    try:
        from tree_sitter import Parser
        try:
            # Modern tree_sitter 0.22+
            parser = Parser(lang)
        except TypeError:
            # Older tree_sitter
            parser = Parser()
            parser.set_language(lang)
        _PARSER_CACHE[lang_name] = parser
        return parser
    except Exception:
        return None


def should_ignore_dir(dir_name: str, extra_ignores: Optional[Set[str]] = None) -> bool:
    """Returns True if the directory should be skipped."""
    if dir_name.startswith(".") and dir_name not in {".github"}:
        return True
    if dir_name in DEFAULT_IGNORE_DIRS:
        return True
    if extra_ignores and dir_name in extra_ignores:
        return True
    return False


def discover_source_files(
    root_path: Path,
    extra_ignores: Optional[Set[str]] = None,
    allowed_extensions: Optional[Set[str]] = None,
) -> List[Path]:
    """Recursively collects source files within root_path, respecting exclusions."""
    source_files: List[Path] = []
    root = root_path.resolve()

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored directories in-place
        dirnames[:] = [
            d for d in dirnames
            if not should_ignore_dir(d, extra_ignores)
        ]

        for fname in filenames:
            if fname.startswith("."):
                continue
            fpath = Path(dirpath) / fname
            ext = fpath.suffix.lower()
            if allowed_extensions:
                if ext in allowed_extensions:
                    source_files.append(fpath)
            elif ext in EXTENSION_TO_LANG:
                source_files.append(fpath)

    return sorted(source_files)


def save_json(data: Any, out_path: Path) -> None:
    """Writes formatted JSON data safely."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(in_path: Path) -> Any:
    """Reads JSON data from file."""
    with open(in_path, "r", encoding="utf-8") as f:
        return json.load(f)
