#!/usr/bin/env python3
"""Unit tests for dependency_graph."""

import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from dependency_graph import build_dependency_graph, normalize_import_path


class TestDependencyGraph(unittest.TestCase):
    def test_normalize_import_path(self):
        known = {
            "src/index.ts",
            "src/utils/math.ts",
            "src/services/user.ts",
        }

        # Relative import
        target, is_int = normalize_import_path("./utils/math", "src/index.ts", known)
        self.assertTrue(is_int)
        self.assertEqual(target, "src/utils/math.ts")

        # Parent relative import
        target2, is_int2 = normalize_import_path("../utils/math", "src/services/user.ts", known)
        self.assertTrue(is_int2)
        self.assertEqual(target2, "src/utils/math.ts")

        # External package
        target3, is_int3 = normalize_import_path("express", "src/index.ts", known)
        self.assertFalse(is_int3)
        self.assertEqual(target3, "express")

    def test_build_dependency_graph(self):
        fake_manifest = {
            "files": [
                {
                    "path": "src/cli.py",
                    "symbols": {
                        "imports": [
                            {"source": "src.service"},
                            {"source": "src.util"},
                        ]
                    }
                },
                {
                    "path": "src/service.py",
                    "symbols": {
                        "imports": [
                            {"source": "src.util"},
                        ]
                    }
                },
                {
                    "path": "src/util.py",
                    "symbols": {
                        "imports": []
                    }
                }
            ]
        }

        graph = build_dependency_graph(fake_manifest)
        self.assertEqual(graph["total_internal_edges"], 3)

        # src/util.py should be a hub (imported by cli and service)
        hub_paths = [h["path"] for h in graph["hub_modules"]]
        self.assertIn("src/util.py", hub_paths)

        # src/cli.py should be an entrypoint
        entry_paths = [e["path"] for e in graph["entrypoints"]]
        self.assertIn("src/cli.py", entry_paths)


if __name__ == "__main__":
    unittest.main()
