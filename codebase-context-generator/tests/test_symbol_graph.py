#!/usr/bin/env python3
"""Unit tests for symbol_graph."""

import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from symbol_graph import (
    build_symbol_graph,
    export_signatures_markdown,
    query_symbol,
)


class TestSymbolGraph(unittest.TestCase):
    def setUp(self):
        self.manifest = {
            "files": [
                {
                    "path": "service/user.py",
                    "symbols": {
                        "classes": [
                            {
                                "name": "UserManager",
                                "bases": ["BaseManager"],
                                "docstring": "Manages users.",
                                "line_start": 10,
                                "methods": [
                                    {
                                        "name": "create_user",
                                        "signature": "create_user(name: str) -> dict",
                                        "args": [{"name": "name", "type": "str"}],
                                        "return_type": "dict",
                                        "callees": ["db_insert", "send_welcome_email"],
                                        "line": 15,
                                    }
                                ]
                            }
                        ],
                        "functions": [
                            {
                                "name": "send_welcome_email",
                                "signature": "send_welcome_email(email: str) -> bool",
                                "args": [{"name": "email", "type": "str"}],
                                "return_type": "bool",
                                "callees": [],
                                "line_start": 30,
                            }
                        ],
                        "interfaces_and_types": []
                    }
                },
                {
                    "path": "db/client.py",
                    "symbols": {
                        "functions": [
                            {
                                "name": "db_insert",
                                "signature": "db_insert(table: str, data: dict) -> None",
                                "args": [{"name": "table", "type": "str"}, {"name": "data", "type": "dict"}],
                                "return_type": "None",
                                "callees": [],
                                "line_start": 5,
                            }
                        ],
                        "classes": [],
                        "interfaces_and_types": []
                    }
                }
            ]
        }

    def test_build_symbol_graph_and_callers(self):
        graph = build_symbol_graph(self.manifest)
        self.assertGreaterEqual(graph["total_symbols"], 3)

        # Check create_user callers and callees
        create_user_sym = graph["symbols"]["service/user.py::UserManager.create_user"]
        self.assertIn("db_insert", create_user_sym["callees"])

        # Check db_insert has create_user as a caller
        db_insert_sym = graph["symbols"]["db/client.py::db_insert"]
        self.assertIn("service/user.py::UserManager.create_user", db_insert_sym["callers"])

        # Check send_welcome_email has create_user as caller
        email_sym = graph["symbols"]["service/user.py::send_welcome_email"]
        self.assertIn("service/user.py::UserManager.create_user", email_sym["callers"])

    def test_query_symbol(self):
        graph = build_symbol_graph(self.manifest)
        results = query_symbol(graph, "create_user")
        self.assertTrue(len(results) >= 1)
        self.assertEqual(results[0]["name"], "UserManager.create_user")

    def test_export_signatures_markdown(self):
        graph = build_symbol_graph(self.manifest)
        md = export_signatures_markdown(graph)
        self.assertIn("# Codebase Signatures & Symbol Index", md)
        self.assertIn("UserManager.create_user", md)
        self.assertIn("db_insert", md)


if __name__ == "__main__":
    unittest.main()
