#!/usr/bin/env python3
"""Unit tests for email-triage operational scripts."""

import io
import json
import unittest
from unittest.mock import patch
from pathlib import Path

# Add project root to sys.path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.scan_inbox import scan_inbox, parse_args, main
from scripts.read_email import (
    read_thread,
    decode_base64_payload,
    extract_message_data,
    main as read_email_main,
)
from scripts.apply_triage import (
    apply_triage,
    main as triage_main,
)
from scripts.draft_reply import (
    create_draft_reply,
    main as draft_main,
)
from scripts.manage_labels import (
    list_labels,
    setup_triage_labels,
    main as labels_main,
)


class TestScanInbox(unittest.TestCase):
    """Unit tests for scan_inbox.py inbox scanner."""

    @patch("scripts.scan_inbox.resolve_account", return_value="user@company.com")
    @patch("scripts.scan_inbox.run_gog")
    def test_scan_inbox_success_normalization(self, mock_run_gog, mock_resolve):
        mock_raw_payload = {
            "threads": [
                {
                    "id": "thread123",
                    "date": "2026-11-05 09:30",
                    "from": "Sender Name <sender@example.com>",
                    "subject": "Important Meeting Update",
                    "labels": ["UNREAD", "INBOX"],
                    "messageCount": 3,
                    "snippet": "Here is the agenda...",
                }
            ]
        }
        mock_run_gog.return_value = (0, mock_raw_payload, json.dumps(mock_raw_payload), "")

        threads = scan_inbox(query="is:unread in:inbox", max_results=10, account="work_account")

        self.assertEqual(len(threads), 1)
        th = threads[0]
        self.assertEqual(th["id"], "thread123")
        self.assertEqual(th["account"], "user@company.com")
        self.assertEqual(th["date"], "2026-11-05 09:30")
        self.assertEqual(th["from"], "Sender Name <sender@example.com>")
        self.assertEqual(th["subject"], "Important Meeting Update")
        self.assertEqual(th["labels"], ["UNREAD", "INBOX"])
        self.assertEqual(th["message_count"], 3)
        self.assertEqual(th["snippet"], "Here is the agenda...")

        mock_run_gog.assert_called_once_with(
            ["gmail", "search", "is:unread in:inbox", "--max=10"],
            account="user@company.com",
            json_mode=True,
        )

    @patch(
        "scripts.scan_inbox.get_configured_accounts",
        return_value=["acc1@test.com", "acc2@test.com"],
    )
    @patch("scripts.scan_inbox.run_gog")
    def test_scan_inbox_multi_account(self, mock_run_gog, mock_configured):
        mock_run_gog.side_effect = [
            (0, {"threads": [{"id": "t1", "subject": "S1"}]}, "{}", ""),
            (0, {"threads": [{"id": "t2", "subject": "S2"}]}, "{}", ""),
        ]
        threads = scan_inbox(account=None)
        self.assertEqual(len(threads), 2)
        self.assertEqual(threads[0]["account"], "acc1@test.com")
        self.assertEqual(threads[1]["account"], "acc2@test.com")

    @patch("scripts.scan_inbox.run_gog")
    def test_scan_inbox_empty_results(self, mock_run_gog):
        # Empty threads list
        mock_run_gog.return_value = (0, {"threads": []}, '{"threads": []}', "")
        threads = scan_inbox(query="is:unread", max_results=5)
        self.assertEqual(threads, [])

        # Missing threads key
        mock_run_gog.return_value = (0, {}, "{}", "")
        threads2 = scan_inbox(query="is:unread", max_results=5)
        self.assertEqual(threads2, [])

        # None parsed json payload
        mock_run_gog.return_value = (0, None, "", "")
        threads3 = scan_inbox(query="is:unread", max_results=5)
        self.assertEqual(threads3, [])

    @patch("scripts.scan_inbox.run_gog")
    def test_scan_inbox_error_handling(self, mock_run_gog):
        mock_run_gog.return_value = (1, None, "", "Google API Error: Unauthorized")
        with self.assertRaises(RuntimeError) as ctx:
            scan_inbox(query="is:unread", max_results=5, account="work_account")
        self.assertIn("Google API Error: Unauthorized", str(ctx.exception))

    def test_parse_args_defaults(self):
        args = parse_args([])
        self.assertEqual(args.query, "is:unread in:inbox")
        self.assertEqual(args.max, 10)
        self.assertIsNone(args.account)
        self.assertFalse(args.json)

    def test_parse_args_custom(self):
        args = parse_args([
            "--query", "label:spam",
            "--max", "25",
            "--account", "personal",
            "--json",
        ])
        self.assertEqual(args.query, "label:spam")
        self.assertEqual(args.max, 25)
        self.assertEqual(args.account, "personal")
        self.assertTrue(args.json)

    @patch("scripts.scan_inbox.scan_inbox")
    def test_main_json_output(self, mock_scan):
        mock_scan.return_value = [
            {
                "id": "th1",
                "date": "2026-11-05 10:00",
                "from": "Alice <alice@test.com>",
                "subject": "Test Subject",
                "snippet": "Test snippet",
                "labels": ["UNREAD"],
                "message_count": 1,
            }
        ]

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = main(["--json"])
            self.assertEqual(code, 0)
            output = fake_out.getvalue()
            parsed = json.loads(output)
            self.assertEqual(len(parsed), 1)
            self.assertEqual(parsed[0]["id"], "th1")

    @patch("scripts.scan_inbox.scan_inbox")
    def test_main_human_readable_output(self, mock_scan):
        mock_scan.return_value = [
            {
                "id": "th1",
                "date": "2026-11-05 10:00",
                "from": "Alice <alice@test.com>",
                "subject": "Test Subject",
                "snippet": "Test snippet",
                "labels": ["UNREAD"],
                "message_count": 1,
            }
        ]

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = main([])
            self.assertEqual(code, 0)
            output = fake_out.getvalue()
            self.assertIn("Found 1 unread thread(s)", output)
            self.assertIn("Test Subject", output)
            self.assertIn("Alice <alice@test.com>", output)

    @patch("scripts.scan_inbox.scan_inbox")
    def test_main_empty_readable_output(self, mock_scan):
        mock_scan.return_value = []
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = main([])
            self.assertEqual(code, 0)
            output = fake_out.getvalue()
            self.assertIn("No threads found", output)

    @patch("scripts.scan_inbox.scan_inbox", side_effect=RuntimeError("Subprocess failed"))
    def test_main_error_handling(self, mock_scan):
        with patch("sys.stderr", new=io.StringIO()) as fake_err:
            code = main([])
            self.assertEqual(code, 1)
            err_output = fake_err.getvalue()
            self.assertIn("Error scanning inbox: Subprocess failed", err_output)


class TestReadEmail(unittest.TestCase):
    """Unit tests for read_email.py thread reader."""

    def test_decode_base64_payload(self):
        # Standard base64
        self.assertEqual(decode_base64_payload("SGVsbG8gV29ybGQ="), "Hello World")
        # URL safe base64 with missing padding
        import base64
        raw = "Special ? & = / test"
        urlsafe = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
        self.assertEqual(decode_base64_payload(urlsafe), raw)
        # Empty and None
        self.assertEqual(decode_base64_payload(""), "")
        self.assertEqual(decode_base64_payload(None), "")

    def test_extract_message_data_single_part(self):
        raw_msg = {
            "id": "msg001",
            "snippet": "Hello there",
            "payload": {
                "headers": [
                    {"name": "From", "value": "Boss <boss@company.com>"},
                    {"name": "To", "value": "Me <me@company.com>"},
                    {"name": "Cc", "value": "Team <team@company.com>"},
                    {"name": "Subject", "value": "Quarterly Planning"},
                    {"name": "Date", "value": "Thu, 5 Nov 2026 10:00:00 +0000"},
                ],
                "mimeType": "text/plain",
                "body": {
                    "data": "UGxlYXNlIHJldmlldyB0aGUgcm9hZG1hcC4=",  # "Please review the roadmap."
                    "size": 30,
                },
            },
        }

        extracted = extract_message_data(raw_msg)
        self.assertEqual(extracted["id"], "msg001")
        self.assertEqual(extracted["from"], "Boss <boss@company.com>")
        self.assertEqual(extracted["to"], "Me <me@company.com>")
        self.assertEqual(extracted["cc"], "Team <team@company.com>")
        self.assertEqual(extracted["subject"], "Quarterly Planning")
        self.assertEqual(extracted["clean_body"], "Please review the roadmap.")
        self.assertEqual(extracted["attachments"], [])

    def test_extract_message_data_multipart_with_attachment(self):
        raw_msg = {
            "id": "msg002",
            "snippet": "Attachment included",
            "payload": {
                "headers": [
                    {"name": "From", "value": "Client <client@corp.com>"},
                    {"name": "To", "value": "Me <me@company.com>"},
                    {"name": "Subject", "value": "Invoice #101"},
                    {"name": "Date", "value": "Thu, 5 Nov 2026 11:00:00 +0000"},
                ],
                "mimeType": "multipart/mixed",
                "parts": [
                    {
                        "mimeType": "multipart/alternative",
                        "parts": [
                            {
                                "mimeType": "text/plain",
                                "body": {"data": "UGxhaW4gdGV4dCBib2R5"},  # "Plain text body"
                            },
                            {
                                "mimeType": "text/html",
                                "body": {
                                    # "<p>HTML with <a href='https://link.com'>link</a></p>"
                                    "data": (
                                        "PHA-SFRNTCB3aXRoIDxhIGhyZWY9Imh0dHBzOi8vbGluay5jb20iP"
                                        "mxpbms8L2E-PC9wPg=="
                                    ),
                                },
                            },
                        ],
                    },
                    {
                        "filename": "invoice.pdf",
                        "mimeType": "application/pdf",
                        "body": {"size": 20480, "attachmentId": "att_pdf_123"},
                    },
                ],
            },
        }

        extracted = extract_message_data(raw_msg)
        self.assertEqual(extracted["id"], "msg002")
        self.assertIn("[link](https://link.com)", extracted["clean_body"])
        self.assertEqual(len(extracted["attachments"]), 1)
        att = extracted["attachments"][0]
        self.assertEqual(att["filename"], "invoice.pdf")
        self.assertEqual(att["mimeType"], "application/pdf")
        self.assertEqual(att["size"], 20480)
        self.assertEqual(att["attachmentId"], "att_pdf_123")

    @patch("scripts.read_email.run_gog")
    def test_read_thread_success(self, mock_run_gog):
        mock_payload = {
            "thread": {
                "id": "th100",
                "messages": [
                    {
                        "id": "msg1",
                        "payload": {
                            "headers": [
                                {"name": "From", "value": "Colleague <colleague@test.com>"},
                                {"name": "Subject", "value": "Project Sync"},
                                {"name": "Date", "value": "Thu, 5 Nov 2026 09:00:00"},
                            ],
                            "body": {"data": "SGVsbG8="},  # "Hello"
                        },
                    },
                    {
                        "id": "msg2",
                        "payload": {
                            "headers": [
                                {"name": "From", "value": "Me <me@test.com>"},
                                {"name": "Subject", "value": "Re: Project Sync"},
                                {"name": "Date", "value": "Thu, 5 Nov 2026 09:30:00"},
                            ],
                            "body": {"data": "SGVsbG8gYmFjaw=="},  # "Hello back"
                        },
                    },
                ],
            }
        }
        mock_run_gog.return_value = (0, mock_payload, json.dumps(mock_payload), "")

        res = read_thread("th100", account="work_account")

        self.assertEqual(res["id"], "th100")
        self.assertEqual(res["subject"], "Project Sync")
        self.assertEqual(res["message_count"], 2)
        self.assertEqual(len(res["messages"]), 2)
        self.assertEqual(res["latest_message"]["id"], "msg2")
        self.assertIn("mail.google.com", res["url"])
        self.assertIn("th100", res["url"])

        mock_run_gog.assert_called_once_with(
            ["gmail", "thread", "get", "th100", "--full"],
            account="work_account",
            json_mode=True,
        )

    @patch("scripts.read_email.run_gog")
    def test_read_thread_error(self, mock_run_gog):
        mock_run_gog.return_value = (1, None, "", "Thread not found")
        with self.assertRaises(RuntimeError) as ctx:
            read_thread("nonexistent", account="work_account")
        self.assertIn("Thread not found", str(ctx.exception))

    @patch("scripts.read_email.read_thread")
    def test_main_json_output(self, mock_read):
        mock_read.return_value = {
            "id": "th123",
            "subject": "Status Report",
            "message_count": 1,
            "messages": [
                {
                    "id": "m1",
                    "from": "alice@test.com",
                    "to": "bob@test.com",
                    "cc": "",
                    "date": "2026-11-05",
                    "clean_body": "All systems operational.",
                    "snippet": "All systems operational.",
                    "attachments": [],
                }
            ],
            "latest_message": {"id": "m1", "clean_body": "All systems operational."},
            "url": "https://mail.google.com/mail/u/work_account/#all/th123",
        }

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = read_email_main(["th123", "--json"])
            self.assertEqual(code, 0)
            parsed = json.loads(fake_out.getvalue())
            self.assertEqual(parsed["id"], "th123")
            self.assertEqual(parsed["subject"], "Status Report")

    @patch("scripts.read_email.read_thread")
    def test_main_readable_output(self, mock_read):
        mock_read.return_value = {
            "id": "th123",
            "subject": "Status Report",
            "message_count": 1,
            "messages": [
                {
                    "id": "m1",
                    "from": "alice@test.com",
                    "to": "bob@test.com",
                    "cc": "",
                    "date": "2026-11-05",
                    "clean_body": "All systems operational.",
                    "snippet": "All systems operational.",
                    "attachments": [{"filename": "log.txt", "size": 100}],
                }
            ],
            "latest_message": {"id": "m1", "clean_body": "All systems operational."},
            "url": "https://mail.google.com/mail/u/work_account/#all/th123",
        }

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = read_email_main(["th123"])
            self.assertEqual(code, 0)
            out = fake_out.getvalue()
            self.assertIn("Thread: Status Report", out)
            self.assertIn("alice@test.com", out)
            self.assertIn("All systems operational.", out)
            self.assertIn("log.txt", out)

    @patch("scripts.read_email.read_thread", side_effect=RuntimeError("Thread lookup failed"))
    def test_main_error_handling(self, mock_read):
        with patch("sys.stderr", new=io.StringIO()) as fake_err:
            code = read_email_main(["th_err"])
            self.assertEqual(code, 1)
            self.assertIn("Error reading thread: Thread lookup failed", fake_err.getvalue())


class TestApplyTriage(unittest.TestCase):
    """Unit tests for apply_triage.py triage state modification."""

    def test_dry_run_preview(self):
        with patch("scripts.apply_triage.run_gog") as mock_run_gog:
            res = apply_triage(
                ["th1", "th2"],
                mark_read=True,
                archive=True,
                trash=False,
                dry_run=True,
            )
            # run_gog should NOT be invoked in dry-run mode
            mock_run_gog.assert_not_called()
            self.assertTrue(res["dry_run"])
            self.assertEqual(res["thread_ids"], ["th1", "th2"])
            self.assertIn("UNREAD", res["remove_labels"])
            self.assertIn("INBOX", res["remove_labels"])
            self.assertEqual(len(res["details"]), 2)

    @patch("scripts.apply_triage.run_gog")
    def test_apply_triage_mark_read_and_archive(self, mock_run_gog):
        mock_run_gog.return_value = (0, {"status": "ok"}, "{}", "")
        res = apply_triage(
            ["th1"],
            mark_read=True,
            archive=True,
            account="work_account",
        )
        self.assertFalse(res["dry_run"])
        self.assertTrue(res["success"])
        mock_run_gog.assert_called_once_with(
            ["gmail", "thread", "modify", "th1", "--remove=INBOX,UNREAD"],
            account="work_account",
            json_mode=True,
        )

    @patch("scripts.apply_triage.run_gog")
    def test_apply_triage_trash(self, mock_run_gog):
        mock_run_gog.return_value = (0, {"status": "ok"}, "{}", "")
        res = apply_triage(
            ["th1"],
            mark_read=True,
            trash=True,
            account="personal",
        )
        self.assertTrue(res["success"])
        mock_run_gog.assert_called_once_with(
            ["gmail", "thread", "modify", "th1", "--add=TRASH", "--remove=UNREAD"],
            account="personal",
            json_mode=True,
        )

    @patch("scripts.apply_triage.run_gog")
    def test_apply_triage_custom_labels(self, mock_run_gog):
        mock_run_gog.return_value = (0, {"status": "ok"}, "{}", "")
        res = apply_triage(
            ["th1"],
            add_labels=["Triage/Needs-Reply", "Important"],
            remove_labels=["Spam"],
        )
        self.assertTrue(res["success"])
        mock_run_gog.assert_called_once_with(
            [
                "gmail",
                "thread",
                "modify",
                "th1",
                "--add=Important,Triage/Needs-Reply",
                "--remove=Spam",
            ],
            account=None,
            json_mode=True,
        )

    def test_permanent_delete_safety_check(self):
        # Without force -> raises RuntimeError
        with self.assertRaises(RuntimeError) as ctx:
            apply_triage(["th1"], delete=True, force=False)
        self.assertIn("--force", str(ctx.exception))

    @patch("scripts.apply_triage.run_gog")
    def test_permanent_delete_with_force(self, mock_run_gog):
        mock_run_gog.return_value = (0, {"status": "deleted"}, "{}", "")
        res = apply_triage(["th1", "th2"], delete=True, force=True)
        self.assertTrue(res["success"])
        self.assertEqual(mock_run_gog.call_count, 2)
        mock_run_gog.assert_any_call(
            ["gmail", "batch", "delete", "th1", "--force"],
            account=None,
            json_mode=True,
        )
        mock_run_gog.assert_any_call(
            ["gmail", "batch", "delete", "th2", "--force"],
            account=None,
            json_mode=True,
        )

    @patch("scripts.apply_triage.apply_triage")
    def test_cli_main_dry_run_json(self, mock_apply):
        mock_apply.return_value = {
            "dry_run": True,
            "thread_ids": ["th1"],
            "add_labels": ["TRASH"],
            "remove_labels": ["UNREAD"],
            "success": True,
            "details": [{"thread_id": "th1", "actions": ["trash", "mark_read"]}],
        }

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = triage_main(["th1", "--mark-read", "--trash", "--dry-run", "--json"])
            self.assertEqual(code, 0)
            parsed = json.loads(fake_out.getvalue())
            self.assertTrue(parsed["dry_run"])
            self.assertEqual(parsed["thread_ids"], ["th1"])

    @patch("scripts.apply_triage.apply_triage")
    def test_cli_main_readable(self, mock_apply):
        mock_apply.return_value = {
            "dry_run": False,
            "thread_ids": ["th1"],
            "add_labels": [],
            "remove_labels": ["INBOX", "UNREAD"],
            "delete": False,
            "success": True,
            "details": [{"thread_id": "th1", "actions": ["mark_read", "archive"]}],
        }

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = triage_main(["th1", "--mark-read", "--archive"])
            self.assertEqual(code, 0)
            out = fake_out.getvalue()
            self.assertIn("Triage Actions Applied", out)
            self.assertIn("th1", out)

    def test_cli_main_delete_without_force_fails(self):
        with patch("sys.stderr", new=io.StringIO()) as fake_err:
            code = triage_main(["th1", "--delete"])
            self.assertEqual(code, 1)
            self.assertIn("Permanent deletion requires --force", fake_err.getvalue())


class TestDraftReply(unittest.TestCase):
    """Unit tests for draft_reply.py."""

    def test_create_draft_reply_empty_body_raises(self):
        with self.assertRaises(ValueError) as ctx:
            create_draft_reply("msg1", body="", body_file=None)
        self.assertIn("cannot be empty", str(ctx.exception))

    def test_create_draft_reply_dry_run(self):
        with patch("scripts.draft_reply.run_gog") as mock_run_gog:
            res = create_draft_reply(
                "msg1",
                body="Thank you for your email.",
                dry_run=True,
                to="boss@corp.com",
                subject="Re: Update",
            )
            mock_run_gog.assert_not_called()
            self.assertTrue(res["dry_run"])
            self.assertEqual(res["status"], "simulated")
            self.assertEqual(res["message_id"], "msg1")

    @patch("scripts.draft_reply.run_gog")
    def test_create_draft_reply_with_string_body(self, mock_run_gog):
        mock_run_gog.return_value = (0, {"id": "draft_abc123"}, "{}", "")
        res = create_draft_reply(
            "msg10",
            body="I will attend.",
            to="alice@test.com",
            subject="Re: Sync",
            account="work_account",
        )
        self.assertFalse(res["dry_run"])
        self.assertEqual(res["draft_id"], "draft_abc123")
        self.assertEqual(res["status"], "created")

        mock_run_gog.assert_called_once()
        cmd = mock_run_gog.call_args[0][0]
        self.assertEqual(cmd[0], "gmail")
        self.assertEqual(cmd[1], "drafts")
        self.assertEqual(cmd[2], "create")
        self.assertIn("--reply-to-message-id=msg10", cmd)
        self.assertIn("--to=alice@test.com", cmd)
        self.assertIn("--subject=Re: Sync", cmd)
        self.assertTrue(any(arg.startswith("--body-file=") for arg in cmd))

    @patch("scripts.draft_reply.run_gog")
    def test_create_draft_reply_reply_all(self, mock_run_gog):
        mock_run_gog.return_value = (0, {"id": "draft_xyz"}, "{}", "")
        res = create_draft_reply(
            "msg10",
            body="Noted.",
            to="alice@test.com",
            cc="team@test.com",
            subject="Re: Sync",
            reply_all=True,
        )
        self.assertTrue(res["reply_all"])
        cmd = mock_run_gog.call_args[0][0]
        self.assertIn("--cc=team@test.com", cmd)

    @patch("scripts.draft_reply.create_draft_reply")
    def test_main_cli_json_and_readable(self, mock_create):
        mock_create.return_value = {
            "status": "created",
            "message_id": "msg99",
            "draft_id": "draft99",
            "reply_all": False,
            "dry_run": False,
        }

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = draft_main(["msg99", "--body", "Will do.", "--json"])
            self.assertEqual(code, 0)
            parsed = json.loads(fake_out.getvalue())
            self.assertEqual(parsed["draft_id"], "draft99")

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = draft_main(["msg99", "--body", "Will do."])
            self.assertEqual(code, 0)
            self.assertIn("Draft Reply Created", fake_out.getvalue())

    def test_main_cli_missing_body_error(self):
        with patch("sys.stderr", new=io.StringIO()) as fake_err:
            code = draft_main(["msg99"])
            self.assertEqual(code, 1)
            self.assertIn("Draft body cannot be empty", fake_err.getvalue())


class TestManageLabels(unittest.TestCase):
    """Unit tests for manage_labels.py."""

    @patch("scripts.manage_labels.run_gog")
    def test_list_labels(self, mock_run_gog):
        mock_run_gog.return_value = (
            0,
            {
                "labels": [
                    {"id": "INBOX", "name": "INBOX", "type": "system"},
                    {"id": "Label_1", "name": "Work", "type": "user"},
                ]
            },
            "{}",
            "",
        )
        labels = list_labels(account="work_account")
        self.assertEqual(len(labels), 2)
        self.assertEqual(labels[0]["name"], "INBOX")
        mock_run_gog.assert_called_once_with(
            ["gmail", "labels", "list"],
            account="work_account",
            json_mode=True,
        )

    @patch("scripts.manage_labels.run_gog")
    def test_setup_triage_labels_idempotent(self, mock_run_gog):
        # 1 existing triage label, 2 missing
        mock_run_gog.side_effect = [
            (
                0,
                {
                    "labels": [
                        {"id": "INBOX", "name": "INBOX", "type": "system"},
                        {"id": "L1", "name": "Triage/FYI", "type": "user"},
                    ]
                },
                "{}",
                "",
            ),
            (0, {"id": "L2", "name": "Triage/Action-Needed"}, "{}", ""),
            (0, {"id": "L3", "name": "Triage/Waiting"}, "{}", ""),
        ]

        res = setup_triage_labels(account="work_account", dry_run=False)
        self.assertFalse(res["dry_run"])
        self.assertIn("Triage/FYI", res["existing"])
        self.assertIn("Triage/Action-Needed", res["created"])
        self.assertIn("Triage/Waiting", res["created"])

    @patch("scripts.manage_labels.run_gog")
    def test_setup_triage_labels_dry_run(self, mock_run_gog):
        mock_run_gog.return_value = (0, {"labels": []}, "{}", "")
        res = setup_triage_labels(account="work_account", dry_run=True)
        self.assertTrue(res["dry_run"])
        # Only list_labels should be called, no create calls
        mock_run_gog.assert_called_once()
        self.assertEqual(len(res["created"]), 3)

    @patch("scripts.manage_labels.list_labels")
    def test_labels_main_list(self, mock_list):
        mock_list.return_value = [{"id": "INBOX", "name": "INBOX", "type": "system"}]
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            code = labels_main(["--list", "--json"])
            self.assertEqual(code, 0)
            parsed = json.loads(fake_out.getvalue())
            self.assertEqual(parsed[0]["name"], "INBOX")


if __name__ == "__main__":
    unittest.main()
