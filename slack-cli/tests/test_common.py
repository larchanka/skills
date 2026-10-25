#!/usr/bin/env python3
"""Unit tests for slack-cli shared common utilities."""

import datetime
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import common


class TestSlackCommon(unittest.TestCase):
    def test_format_ts_valid(self):
        # 1712345678 is 2024-04-05
        formatted = common.format_ts("1712345678.123456")
        self.assertRegex(formatted, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

    def test_format_ts_invalid(self):
        # Malformed ts should return raw string without throwing exception
        self.assertEqual(common.format_ts("not-a-timestamp"), "not-a-timestamp")
        self.assertEqual(common.format_ts(""), "")

    @patch("shutil.which")
    def test_get_slackcli_bin_path(self, mock_which):
        mock_which.return_value = "/usr/local/bin/slackcli"
        bin_path = common.get_slackcli_bin()
        self.assertEqual(bin_path, "/usr/local/bin/slackcli")

    @patch("shutil.which")
    @patch("pathlib.Path.exists")
    @patch("os.access")
    def test_get_slackcli_bin_fallback(self, mock_access, mock_exists, mock_which):
        mock_which.return_value = None
        mock_exists.return_value = True
        mock_access.return_value = True

        bin_path = common.get_slackcli_bin()
        self.assertTrue(bin_path.endswith(".local/bin/slackcli"))

    @patch("shutil.which")
    @patch("pathlib.Path.exists")
    def test_get_slackcli_bin_not_found(self, mock_exists, mock_which):
        mock_which.return_value = None
        mock_exists.return_value = False

        with self.assertRaises(FileNotFoundError):
            common.get_slackcli_bin()

    @patch("common.get_slackcli_bin")
    @patch("subprocess.run")
    def test_run_slackcli_success(self, mock_run, mock_get_bin):
        mock_get_bin.return_value = "/bin/slackcli"
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps({"ok": True, "channels": [{"id": "C123"}]})
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        code, data, stdout, stderr = common.run_slackcli(
            ["conversations", "list"],
            workspace="my-workspace",
            json_mode=True,
        )

        self.assertEqual(code, 0)
        self.assertIsNotNone(data)
        self.assertTrue(data.get("ok"))
        self.assertEqual(len(data.get("channels")), 1)

        # Verify command arguments
        cmd_args = mock_run.call_args[0][0]
        self.assertEqual(cmd_args[0], "/bin/slackcli")
        self.assertIn("conversations", cmd_args)
        self.assertIn("--workspace", cmd_args)
        self.assertIn("my-workspace", cmd_args)
        self.assertIn("--json", cmd_args)

    @patch("common.get_slackcli_bin")
    @patch("subprocess.run")
    def test_run_slackcli_error(self, mock_run, mock_get_bin):
        mock_get_bin.return_value = "/bin/slackcli"
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "channel_not_found"
        mock_run.return_value = mock_proc

        code, data, stdout, stderr = common.run_slackcli(["messages", "send"])
        self.assertEqual(code, 1)
        self.assertIsNone(data)
        self.assertEqual(stderr, "channel_not_found")


if __name__ == "__main__":
    unittest.main()
