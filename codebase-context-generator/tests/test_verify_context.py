#!/usr/bin/env python3
"""Unit tests for verify_context."""

import shutil
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from verify_context import (
    check_agents_md,
    check_context_dir,
    check_markdown_links,
    verify_context,
)


class TestVerifyContext(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="ctx_test_")).resolve()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_missing_files(self):
        errors, _ = check_agents_md(self.test_dir / "AGENTS.md")
        self.assertTrue(len(errors) > 0)

        errors, _ = check_context_dir(self.test_dir / "context")
        self.assertTrue(len(errors) > 0)

    def test_valid_setup(self):
        agents_content = """# Agent Guidelines
## Project Overview
This is a sample project for testing.

## Build and Test Commands
```bash
npm run build
npm test
```

## Architecture and Context
See [context/index.md](context/index.md).

## Rules and Conventions
Do not introduce unnecessary abstractions.
"""
        (self.test_dir / "AGENTS.md").write_text(agents_content)

        ctx_dir = self.test_dir / "context"
        ctx_dir.mkdir()
        (ctx_dir / "index.md").write_text("# Index\nSee [architecture.md](architecture.md)")
        (ctx_dir / "architecture.md").write_text("# Architecture")
        (ctx_dir / "modules.md").write_text("# Modules")
        (ctx_dir / "signatures.md").write_text("# Signatures")
        (ctx_dir / "dependencies.md").write_text("# Dependencies")
        (ctx_dir / "conventions.md").write_text("# Conventions")

        self.assertTrue(verify_context(self.test_dir))

    def test_broken_markdown_link(self):
        agents_content = """# Agent Guidelines
## Project Overview
Test

## Commands
```bash
test
```

## Architecture
See [missing file](context/does_not_exist.md).

## Rules
Test
"""
        agents_file = self.test_dir / "AGENTS.md"
        agents_file.write_text(agents_content)

        errors, _ = check_markdown_links(self.test_dir, [agents_file])
        self.assertTrue(any("does_not_exist.md" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
