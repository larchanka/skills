#!/usr/bin/env python3
"""Unit tests for email-triage common utilities."""

import json
import os
import unittest
from unittest.mock import patch
from pathlib import Path

# Add project root to sys.path if needed
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.common import (
    resolve_account,
    get_gog_bin,
    build_gog_command,
    run_gog,
    clean_email_body,
    get_default_account,
    get_account_aliases,
    get_configured_accounts,
    clear_account_cache,
)


class TestAccountResolution(unittest.TestCase):
    """Tests for dynamic account resolution and discovery."""

    def setUp(self):
        clear_account_cache()

    def tearDown(self):
        clear_account_cache()

    @patch("scripts.common.get_gog_bin", return_value="/mock/bin/gog")
    @patch("subprocess.run")
    def test_get_default_account_from_gog_status(self, mock_run, mock_bin):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"account": {"email": "user@example.com"}}'
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_default_account(), "user@example.com")

    def test_get_default_account_from_env(self):
        with patch.dict(os.environ, {"GOG_ACCOUNT": "env_user@example.com"}):
            self.assertEqual(get_default_account(), "env_user@example.com")

    @patch("scripts.common.get_gog_bin", return_value="/mock/bin/gog")
    @patch("subprocess.run")
    def test_get_account_aliases(self, mock_run, mock_bin):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps({
            "aliases": {"work": "work@example.com", "home": "home@gmail.com"}
        })
        aliases = get_account_aliases()
        self.assertEqual(aliases.get("work"), "work@example.com")
        self.assertEqual(aliases.get("home"), "home@gmail.com")

    @patch("scripts.common.get_default_account", return_value="default@example.com")
    @patch("scripts.common.get_gog_bin", return_value="/mock/bin/gog")
    @patch("subprocess.run")
    def test_get_configured_accounts_places_default_first(self, mock_run, mock_bin, mock_def):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps({
            "accounts": [
                {"email": "second@example.com", "services": ["gmail"]},
                {"email": "default@example.com", "services": ["gmail"]},
                {"email": "nogmail@example.com", "services": ["calendar"]},
            ]
        })
        accounts = get_configured_accounts()
        self.assertEqual(accounts, ["default@example.com", "second@example.com"])
        self.assertNotIn("nogmail@example.com", accounts)

    @patch(
        "scripts.common.get_account_aliases",
        return_value={"work_account": "user@company.com", "personal": "horrorgr@gmail.com"},
    )
    @patch("scripts.common.get_default_account", return_value="user@company.com")
    def test_resolve_account_precedence(self, mock_def, mock_alias):
        # 1. Alias resolution
        self.assertEqual(resolve_account("work_account"), "user@company.com")
        self.assertEqual(resolve_account("personal"), "horrorgr@gmail.com")
        # 2. Direct email
        self.assertEqual(resolve_account("other@test.com"), "other@test.com")
        # 3. Env var override when account=None or whitespace
        with patch.dict(os.environ, {"GOG_ACCOUNT": "personal"}):
            self.assertEqual(resolve_account(None), "horrorgr@gmail.com")
            self.assertEqual(resolve_account("   "), "horrorgr@gmail.com")
        # 4. Default account when no input and no env
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve_account(None), "user@company.com")
            self.assertEqual(resolve_account("   "), "user@company.com")


class TestGetGogBin(unittest.TestCase):
    """Tests for get_gog_bin discovery."""

    @patch("shutil.which")
    def test_which_discovery_in_path(self, mock_which):
        mock_which.return_value = "/usr/local/bin/gog"
        self.assertEqual(get_gog_bin(), "/usr/local/bin/gog")
        mock_which.assert_called_once_with("gog")

    @patch("shutil.which", return_value=None)
    @patch("os.path.isfile")
    @patch("os.access")
    def test_fallback_discovery(self, mock_access, mock_isfile, mock_which):
        mock_isfile.side_effect = lambda path: path == "/opt/homebrew/bin/gog"
        mock_access.return_value = True
        self.assertEqual(get_gog_bin(), "/opt/homebrew/bin/gog")

    @patch("shutil.which", return_value=None)
    @patch("os.path.isfile", return_value=False)
    def test_not_found_raises_file_not_found_error(self, mock_isfile, mock_which):
        with self.assertRaises(FileNotFoundError) as ctx:
            get_gog_bin()
        self.assertIn("gog binary not found", str(ctx.exception))


class TestRunGog(unittest.TestCase):
    """Tests for run_gog wrapper execution."""

    @patch("scripts.common.resolve_account", return_value="horrorgr@gmail.com")
    @patch("scripts.common.get_gog_bin", return_value="/opt/homebrew/bin/gog")
    @patch("subprocess.run")
    def test_run_gog_success_with_json(self, mock_run, mock_get_bin, mock_resolve):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"status": "ok", "threads": [1, 2]}'
        mock_run.return_value.stderr = ""

        code, data, out, err = run_gog(
            ["gmail", "search", "test"],
            account="personal",
            json_mode=True,
        )

        self.assertEqual(code, 0)
        self.assertEqual(data, {"status": "ok", "threads": [1, 2]})
        self.assertEqual(out, '{"status": "ok", "threads": [1, 2]}')
        self.assertEqual(err, "")

        # Verify command arguments passed
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[0], "/opt/homebrew/bin/gog")
        self.assertIn("gmail", cmd)
        self.assertIn("search", cmd)
        self.assertIn("-a", cmd)
        self.assertEqual(cmd[cmd.index("-a") + 1], "horrorgr@gmail.com")
        self.assertIn("-j", cmd)

    @patch("scripts.common.get_gog_bin", return_value="/opt/homebrew/bin/gog")
    @patch("subprocess.run")
    def test_run_gog_preserves_existing_account_flag(self, mock_run, mock_get_bin):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "{}"
        mock_run.return_value.stderr = ""

        code, data, out, err = run_gog(
            ["gmail", "search", "-a", "custom@example.com"],
            account="work_account",
        )
        cmd = mock_run.call_args[0][0]
        # Should not append a second -a
        self.assertEqual(cmd.count("-a"), 1)
        self.assertEqual(cmd[cmd.index("-a") + 1], "custom@example.com")

    @patch("scripts.common.get_gog_bin", return_value="/opt/homebrew/bin/gog")
    @patch("subprocess.run")
    def test_run_gog_handles_invalid_json_gracefully(self, mock_run, mock_get_bin):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Non-json output message"
        mock_run.return_value.stderr = ""

        code, data, out, err = run_gog(["status"], json_mode=True)
        self.assertEqual(code, 0)
        self.assertIsNone(data)
        self.assertEqual(out, "Non-json output message")

    @patch("scripts.common.get_gog_bin", return_value="/opt/homebrew/bin/gog")
    @patch("subprocess.run")
    def test_run_gog_non_json_mode(self, mock_run, mock_get_bin):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"key": "value"}'
        mock_run.return_value.stderr = ""

        code, data, out, err = run_gog(["version"], json_mode=False)
        cmd = mock_run.call_args[0][0]
        self.assertNotIn("-j", cmd)
        self.assertIsNone(data)
        self.assertEqual(out, '{"key": "value"}')

    @patch("scripts.common.get_gog_bin", return_value="/opt/homebrew/bin/gog")
    @patch("subprocess.run")
    def test_run_gog_subprocess_failure(self, mock_run, mock_get_bin):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Error: invalid token"

        code, data, out, err = run_gog(["gmail", "search", "error"])
        self.assertEqual(code, 1)
        self.assertIsNone(data)
        self.assertEqual(out, "")
        self.assertEqual(err, "Error: invalid token")

    @patch("scripts.common.resolve_account", return_value="user@company.com")
    @patch("scripts.common.get_gog_bin", return_value="/opt/homebrew/bin/gog")
    def test_build_gog_command(self, mock_get_bin, mock_resolve):
        cmd = build_gog_command(["gmail", "threads"], account="work_account", json_mode=True)
        expected = [
            "/opt/homebrew/bin/gog",
            "gmail",
            "threads",
            "-a",
            "user@company.com",
            "-j",
        ]
        self.assertEqual(cmd, expected)

        # When --account already present
        cmd2 = build_gog_command(
            ["gmail", "threads", "--account", "user@test.com"],
            account="work_account",
            json_mode=False,
        )
        self.assertEqual(
            cmd2,
            ["/opt/homebrew/bin/gog", "gmail", "threads", "--account", "user@test.com"],
        )

        # When --account=email syntax is used
        cmd3 = build_gog_command(
            ["gmail", "threads", "--account=user@test.com"],
            account="work_account",
            json_mode=False,
        )
        self.assertEqual(
            cmd3,
            ["/opt/homebrew/bin/gog", "gmail", "threads", "--account=user@test.com"],
        )

    @patch("scripts.common.get_gog_bin", return_value="/opt/homebrew/bin/gog")
    @patch("subprocess.run")
    def test_run_gog_empty_stdout(self, mock_run, mock_get_bin):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""

        code, data, out, err = run_gog(["gmail", "threads"], json_mode=True)
        self.assertEqual(code, 0)
        self.assertIsNone(data)
        self.assertEqual(out, "")
        self.assertEqual(err, "")


class TestCleanEmailBody(unittest.TestCase):
    """Tests for clean_email_body text sanitation and HTML stripping."""

    def test_empty_and_none_input(self):
        self.assertEqual(clean_email_body(""), "")
        self.assertEqual(clean_email_body(None), "")
        self.assertEqual(clean_email_body("   \n\t  "), "")

    def test_plain_text_normalization(self):
        raw = "Line 1\r\n\r\n\r\n\r\nLine 2 with trailing spaces   \r\n\r\nLine 3"
        cleaned = clean_email_body(raw)
        expected = "Line 1\n\nLine 2 with trailing spaces\n\nLine 3"
        self.assertEqual(cleaned, expected)

    def test_strips_script_style_head(self):
        raw = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Secret Subject</title>
            <style>body { color: red; } p { font-size: 14px; }</style>
            <script>alert('malicious');</script>
        </head>
        <body>
            <script type="text/javascript">console.log('tracker');</script>
            <p>Real content here.</p>
        </body>
        </html>
        """
        cleaned = clean_email_body(raw)
        self.assertNotIn("Secret Subject", cleaned)
        self.assertNotIn("color: red", cleaned)
        self.assertNotIn("alert", cleaned)
        self.assertNotIn("console.log", cleaned)
        self.assertEqual(cleaned, "Real content here.")

    def test_strips_tracking_pixels(self):
        raw = """
        <div>
            <p>Please review our proposal.</p>
            <img src="https://track.mail.com/open?uid=123" width="1" height="1" alt="pixel" />
            <img src="https://track.mail.com/pixel.gif" width="0" height="0" />
            <img src="https://track.mail.com/hidden.png" style="display:none;" />
        </div>
        """
        cleaned = clean_email_body(raw)
        self.assertEqual(cleaned, "Please review our proposal.")
        self.assertNotIn("open?uid", cleaned)
        self.assertNotIn("pixel.gif", cleaned)

    def test_preserves_links(self):
        raw = """
        <p>Check the <a href="https://github.com/pulls">pull request</a> before merging.</p>
        <p>Visit <a href="https://example.com">https://example.com</a> for details.</p>
        <p>Direct link: <a href="https://example.com/empty"></a></p>
        <p>Named anchor: <a>No href text</a></p>
        """
        cleaned = clean_email_body(raw)
        self.assertIn("[pull request](https://github.com/pulls)", cleaned)
        self.assertIn("https://example.com", cleaned)
        # Should not duplicate link if text matches href
        self.assertNotIn("[https://example.com](https://example.com)", cleaned)
        self.assertIn("https://example.com/empty", cleaned)
        self.assertIn("No href text", cleaned)

    def test_non_tracking_image_preserves_alt(self):
        raw = (
            '<p>Diagram: <img src="https://example.com/arch.png" '
            'width="800" height="600" alt="Architecture Chart" /></p>'
        )
        cleaned = clean_email_body(raw)
        self.assertIn("[Architecture Chart]", cleaned)

    def test_malformed_html_handling(self):
        raw = "<p>Unclosed paragraph with <b>bold and <i>nested tags<script>alert(1)</script>"
        cleaned = clean_email_body(raw)
        self.assertIn("Unclosed paragraph with bold and nested tags", cleaned)
        self.assertNotIn("alert(1)", cleaned)

    def test_preserves_list_structure(self):
        raw = """
        <p>Required tasks:</p>
        <ul>
            <li>First task</li>
            <li>Second task</li>
            <li>Third task</li>
        </ul>
        """
        cleaned = clean_email_body(raw)
        expected = "Required tasks:\n\n- First task\n- Second task\n- Third task"
        self.assertEqual(cleaned, expected)

    def test_converts_headings_and_paragraphs(self):
        raw = """
        <h1>Meeting Summary</h1>
        <p>We discussed the upcoming roadmap.<br>Next sync is Friday.</p>
        <h2>Action Items</h2>
        <p>Send documentation.</p>
        """
        cleaned = clean_email_body(raw)
        self.assertIn("# Meeting Summary", cleaned)
        self.assertIn("## Action Items", cleaned)
        self.assertIn("We discussed the upcoming roadmap.\nNext sync is Friday.", cleaned)
        self.assertIn("Send documentation.", cleaned)

    def test_decodes_html_entities(self):
        raw = (
            "<p>Tom &amp; Jerry &quot;fun&quot; &lt;adventure&gt; &mdash; "
            "cost is &euro;5 &amp; &#39;quotes&#39; &nbsp; spaced</p>"
        )
        cleaned = clean_email_body(raw)
        self.assertIn("Tom & Jerry", cleaned)
        self.assertIn('"fun"', cleaned)
        self.assertIn("<adventure>", cleaned)
        self.assertIn("'quotes'", cleaned)

    def test_unclosed_link_flushes_on_close(self):
        raw = (
            '<p>Please click <a href="https://example.com/verify">here to verify'
            '<p>Thank you for registering.</p>'
        )
        cleaned = clean_email_body(raw)
        self.assertIn("[here to verify](https://example.com/verify)", cleaned)
        self.assertIn("Thank you for registering.", cleaned)

    def test_trims_confidentiality_disclaimers(self):
        raw = """
        <p>Hi Alex,</p>
        <p>The revised budget proposal is approved.</p>
        <p>This message and any attachments are confidential and intended solely for the recipient.
        If you are not the intended recipient, please notify the sender and delete this message.</p>
        """
        cleaned = clean_email_body(raw)
        self.assertIn("Hi Alex,", cleaned)
        self.assertIn("The revised budget proposal is approved.", cleaned)
        self.assertNotIn("intended solely for the recipient", cleaned)
        self.assertNotIn("delete this message", cleaned)

    def test_trims_unsubscribe_footers(self):
        raw = """
        <p>Check out our latest release notes.</p>
        <p>You received this email because you are subscribed to updates.<br>
        Click here to unsubscribe: <a href="https://example.com/unsub">Unsubscribe</a></p>
        """
        cleaned = clean_email_body(raw)
        self.assertIn("Check out our latest release notes.", cleaned)
        self.assertNotIn("subscribed to updates", cleaned)
        self.assertNotIn("Unsubscribe", cleaned)

    def test_preserves_legitimate_confidential_mention(self):
        raw = "<p>Please ensure all confidential project keys are stored in Vault.</p>"
        cleaned = clean_email_body(raw)
        expected = "Please ensure all confidential project keys are stored in Vault."
        self.assertEqual(cleaned, expected)


if __name__ == "__main__":
    unittest.main()
