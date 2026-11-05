#!/usr/bin/env python3
"""Creates context-aware Gmail draft replies using the gog CLI."""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

# Allow relative imports when run as a standalone script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.common import run_gog


def _resolve_body_content(body: Optional[str], body_file: Optional[str]) -> str:
    """Reads draft body content from string or file path, validating it is non-empty."""
    content = ""
    if body_file:
        file_path = Path(body_file).expanduser().resolve()
        if not file_path.is_file():
            raise FileNotFoundError(f"Body file not found: {body_file}")
        content = file_path.read_text(encoding="utf-8")
    elif body:
        content = body

    content = content.strip()
    if not content:
        raise ValueError("Draft body cannot be empty.")
    return content


def _fetch_message_headers(message_id: str, account: Optional[str]) -> dict[str, str]:
    """Fetches From, Cc, and Subject headers from a message for reply defaults."""
    headers: dict[str, str] = {}
    try:
        args = ["gmail", "get", message_id, "--format=metadata"]
        code, data, _, _ = run_gog(args, account=account, json_mode=True)
        if code == 0 and isinstance(data, dict):
            raw_headers = data.get("payload", {}).get("headers") or []
            for h in raw_headers:
                name = h.get("name", "").lower()
                val = h.get("value", "")
                if name in {"from", "cc", "subject", "reply-to"}:
                    headers[name] = val
    except Exception:
        pass
    return headers


def _format_reply_subject(orig_subject: str) -> str:
    """Ensures a reply subject line is prefixed with Re:."""
    cleaned = orig_subject.strip()
    if not cleaned:
        return "Re: (No subject)"
    if cleaned.lower().startswith("re:"):
        return cleaned
    return f"Re: {cleaned}"


def _populate_from_orig_headers(
    orig: dict[str, str],
    to_addr: str,
    cc_addr: str,
    subject_text: str,
    reply_all: bool,
) -> tuple[str, str, str]:
    """Fills missing reply headers from original message headers."""
    target_to = to_addr if to_addr else (orig.get("reply-to") or orig.get("from", ""))
    target_subj = subject_text if subject_text else _format_reply_subject(orig.get("subject", ""))
    target_cc = cc_addr
    if reply_all and not target_cc:
        target_cc = orig.get("cc", "")
    return target_to, target_cc, target_subj


def _resolve_reply_headers(
    message_id: str,
    to: Optional[str],
    cc: Optional[str],
    subject: Optional[str],
    reply_all: bool,
    account: Optional[str],
) -> tuple[str, str, str]:
    """Resolves To, Cc, and Subject headers, inspecting original message if missing."""
    to_addr = to if to else ""
    cc_addr = cc if cc else ""
    subject_text = subject if subject else ""

    if to_addr and subject_text and (not reply_all or cc_addr):
        return to_addr, cc_addr, subject_text

    orig = _fetch_message_headers(message_id, account)
    return _populate_from_orig_headers(orig, to_addr, cc_addr, subject_text, reply_all)


def _simulate_draft_reply(
    message_id: str,
    to: str,
    cc: str,
    subject: str,
    content: str,
    reply_all: bool,
) -> dict[str, Any]:
    """Builds simulation dictionary for dry-run draft creation."""
    return {
        "status": "simulated",
        "message_id": message_id,
        "draft_id": "draft_simulated",
        "reply_all": reply_all,
        "dry_run": True,
        "to": to,
        "cc": cc,
        "subject": subject,
        "body": content,
    }


def _build_draft_cmd(
    message_id: str,
    temp_path: str,
    to: str,
    cc: str,
    subject: str,
    reply_all: bool,
) -> list[str]:
    """Builds gog CLI arguments for draft reply creation."""
    cmd = [
        "gmail",
        "drafts",
        "create",
        f"--reply-to-message-id={message_id}",
        f"--body-file={temp_path}",
    ]
    if to:
        cmd.append(f"--to={to}")
    if subject:
        cmd.append(f"--subject={subject}")
    if reply_all and cc:
        cmd.append(f"--cc={cc}")
    return cmd


def _execute_draft_creation(
    message_id: str,
    to: str,
    cc: str,
    subject: str,
    content: str,
    reply_all: bool,
    account: Optional[str],
) -> dict[str, Any]:
    """Executes draft creation via temporary file and gog CLI."""
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tf:
        tf.write(content)
        temp_path = tf.name

    try:
        cmd = _build_draft_cmd(message_id, temp_path, to, cc, subject, reply_all)
        code, data, _, stderr = run_gog(cmd, account=account, json_mode=True)
        if code != 0:
            raise RuntimeError(stderr or f"Failed to create draft reply for {message_id}")

        draft_id = "draft_created"
        if isinstance(data, dict):
            draft_id = data.get("id") or (data.get("draft") or {}).get("id") or draft_id

        return {
            "status": "created",
            "message_id": message_id,
            "draft_id": draft_id,
            "reply_all": reply_all,
            "dry_run": False,
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def create_draft_reply(
    message_id: str,
    body: Optional[str] = None,
    body_file: Optional[str] = None,
    to: Optional[str] = None,
    cc: Optional[str] = None,
    subject: Optional[str] = None,
    reply_all: bool = False,
    dry_run: bool = False,
    account: Optional[str] = None,
) -> dict[str, Any]:
    """
    Creates a draft reply to a Gmail message via gog CLI.

    Args:
        message_id: ID of the message being replied to.
        body: Text of the reply draft.
        body_file: File containing text of the reply draft.
        to: Target recipient (defaults to original sender).
        cc: CC recipients.
        subject: Email subject line (defaults to 'Re: <original subject>').
        reply_all: When True, includes original CC recipients.
        dry_run: When True, simulates draft creation without modifying mailbox.
        account: Account alias or email address.

    Returns:
        Structured draft result dictionary.
    """
    content = _resolve_body_content(body=body, body_file=body_file)
    to_addr, cc_addr, subject_text = _resolve_reply_headers(
        message_id=message_id,
        to=to,
        cc=cc,
        subject=subject,
        reply_all=reply_all,
        account=account,
    )

    if dry_run:
        return _simulate_draft_reply(
            message_id=message_id,
            to=to_addr,
            cc=cc_addr,
            subject=subject_text,
            content=content,
            reply_all=reply_all,
        )

    return _execute_draft_creation(
        message_id=message_id,
        to=to_addr,
        cc=cc_addr,
        subject=subject_text,
        content=content,
        reply_all=reply_all,
        account=account,
    )


def format_readable_draft_result(result: dict[str, Any]) -> str:
    """Formats draft reply results into human-readable confirmation text."""
    dry_run = result.get("dry_run", False)
    prefix = "[SIMULATED] " if dry_run else ""
    lines = [
        f"{prefix}Draft Reply Created Successfully",
        "=" * 60,
        f"Message ID:  {result.get('message_id', '')}",
        f"Draft ID:    {result.get('draft_id', '')}",
        f"Reply-All:   {result.get('reply_all', False)}",
    ]
    if result.get("to"):
        lines.append(f"To:          {result.get('to')}")
    if result.get("subject"):
        lines.append(f"Subject:     {result.get('subject')}")
    if result.get("body"):
        lines.append("-" * 60)
        lines.append(result.get("body", "").strip())
    lines.append("=" * 60)
    return "\n".join(lines)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parses command-line arguments for draft_reply."""
    parser = argparse.ArgumentParser(
        description="Create a context-aware Gmail draft reply using gog CLI."
    )
    parser.add_argument(
        "message_id",
        help="Gmail message ID to reply to",
    )
    parser.add_argument(
        "--body",
        "-b",
        default=None,
        help="Draft body content string",
    )
    parser.add_argument(
        "--body-file",
        "-f",
        default=None,
        help="Path to file containing draft body content",
    )
    parser.add_argument(
        "--to",
        default=None,
        help="Optional override recipient email address",
    )
    parser.add_argument(
        "--cc",
        default=None,
        help="Optional override CC email address",
    )
    parser.add_argument(
        "--subject",
        "-s",
        default=None,
        help="Optional override subject line",
    )
    parser.add_argument(
        "--reply-all",
        action="store_true",
        help="Reply to all original recipients",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Simulate draft creation without saving changes",
    )
    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output structured JSON response",
    )
    parser.add_argument(
        "--account",
        "-a",
        default=None,
        help="Google account alias or email (e.g. 'work_account', 'personal_account')",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for draft_reply CLI command."""
    args = parse_args(argv)
    try:
        result = create_draft_reply(
            message_id=args.message_id,
            body=args.body,
            body_file=args.body_file,
            to=args.to,
            cc=args.cc,
            subject=args.subject,
            reply_all=args.reply_all,
            dry_run=args.dry_run,
            account=args.account,
        )
    except Exception as exc:
        print(f"Error creating draft reply: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_readable_draft_result(result))

    return 0


if __name__ == "__main__":
    sys.exit(main())
