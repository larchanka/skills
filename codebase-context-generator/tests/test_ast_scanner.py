#!/usr/bin/env python3
"""Unit tests for ast_scanner and common utilities."""

import shutil
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import (
    discover_source_files,
    get_parser_for_language,
    load_tree_sitter_language,
)
from ast_scanner import (
    extract_python_ast,
    extract_tree_sitter_symbols,
    scan_codebase,
)


class TestASTScanner(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="ast_test_")).resolve()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_python_ast_extraction(self):
        py_code = b'''
"""Module docstring."""
import os
from pathlib import Path

class UserService:
    """Handles user operations."""
    def __init__(self, db_client):
        self.db = db_client

    async def get_user(self, user_id: str) -> dict:
        return {"id": user_id}

def calculate_hash(data: bytes) -> str:
    return "hash"
'''
        symbols = extract_python_ast(py_code, Path("test.py"))
        self.assertEqual(len(symbols["classes"]), 1)
        cls = symbols["classes"][0]
        self.assertEqual(cls["name"], "UserService")
        self.assertIn("Handles user operations", cls["docstring"])
        self.assertEqual(len(cls["methods"]), 2)

        self.assertEqual(len(symbols["functions"]), 1)
        fn = symbols["functions"][0]
        self.assertEqual(fn["name"], "calculate_hash")

        self.assertEqual(len(symbols["imports"]), 2)

    def test_tree_sitter_rust_extraction(self):
        parser = get_parser_for_language("rust")
        if not parser:
            self.skipTest("tree-sitter-rust not available")

        rs_code = b'''
pub struct ServerConfig {
    pub port: u16,
}

pub trait Service {
    fn run(&self);
}

pub fn start(cfg: ServerConfig) {
    println!("Starting");
}
'''
        symbols = extract_tree_sitter_symbols(parser, rs_code, "rust", Path("lib.rs"))
        class_names = [c["name"] for c in symbols["classes"]]
        self.assertIn("ServerConfig", class_names)

        trait_names = [t["name"] for t in symbols["interfaces_and_types"]]
        self.assertIn("Service", trait_names)

        fn_names = [f["name"] for f in symbols["functions"]]
        self.assertIn("start", fn_names)

    def test_tree_sitter_typescript_extraction(self):
        parser = get_parser_for_language("typescript")
        if not parser:
            self.skipTest("tree-sitter-typescript not available")

        ts_code = b'''
import { Config } from "./config";

export interface UserSession {
    token: string;
    expiresAt: number;
}

export class AuthController {
    login() {}
}

export function validateToken(token: string): boolean {
    return true;
}
'''
        symbols = extract_tree_sitter_symbols(parser, ts_code, "typescript", Path("auth.ts"))
        self.assertTrue(any(c["name"] == "AuthController" for c in symbols["classes"]))
        self.assertTrue(any(i["name"] == "UserSession" for i in symbols["interfaces_and_types"]))
        self.assertTrue(any(f["name"] == "validateToken" for f in symbols["functions"]))
        self.assertTrue(len(symbols["imports"]) > 0)

    def test_file_discovery_ignores(self):
        (self.test_dir / "src").mkdir()
        (self.test_dir / "node_modules").mkdir()
        (self.test_dir / ".git").mkdir()

        (self.test_dir / "src" / "index.ts").write_text("console.log('hi');")
        (self.test_dir / "node_modules" / "foo.js").write_text("console.log('bad');")
        (self.test_dir / ".git" / "config").write_text("ignore")

        files = discover_source_files(self.test_dir)
        rel_files = [f.relative_to(self.test_dir).as_posix() for f in files]

        self.assertIn("src/index.ts", rel_files)
        self.assertNotIn("node_modules/foo.js", rel_files)


if __name__ == "__main__":
    unittest.main()
