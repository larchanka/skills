#!/usr/bin/env python3
"""Unit tests for slack-cli individual automation scripts."""

import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import list_channels
import send_message
import react_message
import get_user_info


class TestSlackScripts(unittest.TestCase):
    @patch("send_message.run_slackcli")
    def test_send_message_dry_run(self, mock_run):
        mock_run.return_value = (0, None, "Dry run payload simulated", "")

        test_args = [
            "send_message.py",
            "--recipient", "C0AJTS0J648",
            "--message", "Test message",
            "--dry-run",
        ]

        with patch.object(sys, "argv", test_args):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                send_message.main()
                output = mock_stdout.getvalue()

        self.assertIn("Dry run successful (no message posted):", output)
        # Verify run_slackcli was invoked with --dry-run
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        self.assertIn("--dry-run", cmd)
        self.assertIn("--recipient-id", cmd)
        self.assertIn("C0AJTS0J648", cmd)

    @patch("send_message.run_slackcli")
    def test_send_message_success(self, mock_run):
        mock_run.return_value = (
            0,
            {
                "channel_id": "C12345",
                "ts": "1712345678.999999",
                "permalink": "https://slack.com/archives/C12345/p1712345678999999",
            },
            "",
            "",
        )

        test_args = [
            "send_message.py",
            "--recipient", "C12345",
            "--message", "Live message",
        ]

        with patch.object(sys, "argv", test_args):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                send_message.main()
                output = mock_stdout.getvalue()

        self.assertIn("✔ Message sent successfully!", output)
        self.assertIn("C12345", output)
        self.assertIn("https://slack.com/archives/C12345/p1712345678999999", output)

    @patch("list_channels.run_slackcli")
    def test_list_channels_filter(self, mock_run):
        fake_channels = [
            {"id": "C1", "name": "general", "is_channel": True, "num_members": 20, "topic": "All"},
            {"id": "C2", "name": "random", "is_channel": True, "num_members": 15, "topic": "Fun"},
            {"id": "C3", "name": "dev-general", "is_channel": True, "num_members": 5, "topic": "Dev"},
        ]
        mock_run.return_value = (0, {"conversations": fake_channels}, "", "")

        test_args = [
            "list_channels.py",
            "--filter", "general",
        ]

        with patch.object(sys, "argv", test_args):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                list_channels.main()
                output = mock_stdout.getvalue()

        # Should match 'general' and 'dev-general', but not 'random'
        self.assertIn("Found 2 conversation(s)", output)
        self.assertIn("general", output)
        self.assertIn("dev-general", output)
        self.assertNotIn("random", output)

    @patch("react_message.run_slackcli")
    def test_react_message_add(self, mock_run):
        mock_run.return_value = (0, {"ok": True}, "", "")

        test_args = [
            "react_message.py",
            "--channel", "C12345",
            "--timestamp", "1712345678.123456",
            "--emoji", "rocket",
        ]

        with patch.object(sys, "argv", test_args):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                react_message.main()
                output = mock_stdout.getvalue()

        self.assertIn("✔ Added reaction :rocket:", output)
        cmd = mock_run.call_args[0][0]
        self.assertIn("messages", cmd)
        self.assertIn("react", cmd)
        self.assertIn("--emoji", cmd)
        self.assertIn("rocket", cmd)
        self.assertIn("--channel-id", cmd)
        self.assertIn("C12345", cmd)

    @patch("get_user_info.run_slackcli")
    def test_get_user_info(self, mock_run):
        fake_user = {
            "id": "U12345",
            "name": "john.doe",
            "real_name": "John Doe",
            "profile": {
                "display_name": "jdoe",
                "email": "jdoe@example.com",
                "title": "Staff Engineer",
                "status_text": "Working",
                "status_emoji": ":laptop:",
            },
            "is_admin": False,
            "is_bot": False,
            "deleted": False,
            "tz": "Europe/Amsterdam",
        }
        mock_run.return_value = (0, fake_user, "", "")

        test_args = [
            "get_user_info.py",
            "U12345",
        ]

        with patch.object(sys, "argv", test_args):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                get_user_info.main()
                output = mock_stdout.getvalue()

        self.assertIn("User: John Doe", output)
        self.assertIn("@john.doe", output)
        self.assertIn("Staff Engineer", output)
        self.assertIn("Europe/Amsterdam", output)


if __name__ == "__main__":
    unittest.main()
