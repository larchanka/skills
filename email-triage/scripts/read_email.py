#!/usr/bin/env python3
"""Reads and formats a full Gmail thread using the gog CLI."""

import argparse
import base64
import json
import sys
from pathlib import Path
from typing import Any, Optional, Tuple

# Allow relative imports when run as a standalone script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.common import clean_email_body, resolve_account, run_gog


def decode_base64_payload(data_str: Optional[str]) -> str:
    """Decodes standard or URL-safe base64 encoded Gmail body data."""
    if not data_str:
        return ""

    # Replace URL-safe base64 characters and ensure proper 4-byte padding
    padded = data_str.replace("-", "+").replace("_", "/")
    mod = len(padded) % 4
    if mod != 0:
        padded += "=" * (4 - mod)

    try:
        decoded_bytes = base64.b64decode(padded)
        return decoded_bytes.decode("utf-8", errors="replace")
    except Exception:
        return ""


def get_header_value(headers: list[dict[str, str]], header_name: str) -> str:
    """Retrieves a header value from a list of header dicts case-insensitively."""
    target = header_name.lower()
    for h in headers:
        if h.get("name", "").lower() == target:
            return h.get("value", "")
    return ""


def _collect_parts(
    part: dict[str, Any],
    body_candidates: dict[str, str],
    attachments: list[dict[str, Any]],
) -> None:
    """Recursively traverses payload parts to gather body candidates and attachment metadata."""
    filename = part.get("filename", "")
    mime_type = part.get("mimeType", "")
    body_dict = part.get("body") or {}

    # Check if this part is a downloadable attachment
    if filename:
        attachments.append({
            "filename": filename,
            "mimeType": mime_type,
            "size": body_dict.get("size", 0),
            "attachmentId": body_dict.get("attachmentId", ""),
        })
        return

    # Check for body data
    data = body_dict.get("data")
    if data:
        decoded = decode_base64_payload(data)
        if mime_type.startswith("text/html"):
            body_candidates["html"] = decoded
        elif mime_type.startswith("text/plain"):
            body_candidates["plain"] = decoded

    # Recurse into nested parts
    for subpart in part.get("parts") or []:
        _collect_parts(subpart, body_candidates, attachments)


def _extract_headers(headers: list[dict[str, str]]) -> dict[str, str]:
    """Extracts standard email headers into a dictionary."""
    return {
        "from": get_header_value(headers, "From"),
        "to": get_header_value(headers, "To"),
        "cc": get_header_value(headers, "Cc"),
        "subject": get_header_value(headers, "Subject"),
        "date": get_header_value(headers, "Date"),
    }


def _extract_body_candidates(
    payload: dict[str, Any],
) -> Tuple[dict[str, str], list[dict[str, Any]]]:
    """Collects body text candidates and attachments from message payload."""
    body_candidates: dict[str, str] = {}
    attachments: list[dict[str, Any]] = []

    top_body = payload.get("body")
    top_data = top_body.get("data") if isinstance(top_body, dict) else None
    top_mime = payload.get("mimeType", "")
    if top_data:
        decoded = decode_base64_payload(top_data)
        if top_mime.startswith("text/html"):
            body_candidates["html"] = decoded
        else:
            body_candidates["plain"] = decoded

    for subpart in payload.get("parts") or []:
        _collect_parts(subpart, body_candidates, attachments)

    return body_candidates, attachments


def extract_message_data(raw_msg: dict[str, Any]) -> dict[str, Any]:
    """Extracts metadata, cleaned body text, and attachments from a Gmail message dict."""
    msg_id = str(raw_msg.get("id", ""))
    snippet = raw_msg.get("snippet", "")
    payload = raw_msg.get("payload") if isinstance(raw_msg.get("payload"), dict) else {}
    hdr = _extract_headers(payload.get("headers") or [])

    body_candidates, attachments = _extract_body_candidates(payload)

    raw_body = body_candidates.get("html") or body_candidates.get("plain") or snippet
    clean_body = clean_email_body(raw_body)

    return {
        "id": msg_id,
        "from": hdr["from"],
        "to": hdr["to"],
        "cc": hdr["cc"],
        "subject": hdr["subject"],
        "date": hdr["date"],
        "clean_body": clean_body,
        "snippet": snippet,
        "attachments": attachments,
    }


def read_thread(thread_id: str, account: Optional[str] = None) -> dict[str, Any]:
    """
    Fetches full thread details via gog CLI, cleans message bodies, and formats metadata.

    Args:
        thread_id: Gmail thread ID.
        account: Account alias or email address.

    Returns:
        Structured thread dictionary.
    """
    resolved_acc = resolve_account(account)
    args = ["gmail", "thread", "get", thread_id, "--full"]
    code, data, _, stderr = run_gog(args, account=account, json_mode=True)

    if code != 0:
        error_msg = stderr or f"gog gmail thread get failed with exit code {code}"
        raise RuntimeError(error_msg)

    thread_obj = data.get("thread") if isinstance(data, dict) and "thread" in data else data
    if not isinstance(thread_obj, dict):
        raise RuntimeError(f"Thread payload for {thread_id} is invalid or missing.")

    raw_messages = thread_obj.get("messages") or []
    messages = [extract_message_data(m) for m in raw_messages]

    # Find thread subject from the first message with a non-empty subject
    thread_subject = "(No subject)"
    for m in messages:
        if m.get("subject"):
            thread_subject = m["subject"]
            break

    url = f"https://mail.google.com/mail/u/{resolved_acc}/#all/{thread_id}"

    return {
        "id": thread_id,
        "subject": thread_subject,
        "message_count": len(messages),
        "messages": messages,
        "latest_message": messages[-1] if messages else {},
        "url": url,
    }


def format_readable_thread(thread_data: dict[str, Any]) -> str:
    """Formats thread details into a clean human-readable conversation view."""
    subject = thread_data.get("subject", "(No subject)")
    count = thread_data.get("message_count", 0)
    url = thread_data.get("url", "")
    messages = thread_data.get("messages") or []

    lines = [
        f"Thread: {subject} ({count} messages)",
        f"URL: {url}",
        "=" * 80,
    ]

    for idx, msg in enumerate(messages, 1):
        lines.append(f"[Message {idx}/{count}] ID: {msg.get('id', '')}")
        lines.append(f"Date: {msg.get('date', '')}")
        lines.append(f"From: {msg.get('from', '')}")
        lines.append(f"To:   {msg.get('to', '')}")
        if msg.get("cc"):
            lines.append(f"Cc:   {msg.get('cc', '')}")

        attachments = msg.get("attachments") or []
        if attachments:
            att_desc = ", ".join(
                f"{a.get('filename', '')} ({a.get('size', 0)} bytes)" for a in attachments
            )
            lines.append(f"Attachments: {att_desc}")

        lines.append("-" * 80)
        lines.append(msg.get("clean_body", "").strip())
        lines.append("=" * 80)

    return "\n".join(lines)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parses command-line arguments for read_email."""
    parser = argparse.ArgumentParser(
        description="Read and sanitize a full Gmail thread using gog CLI."
    )
    parser.add_argument(
        "thread_id",
        help="Gmail thread ID to fetch",
    )
    parser.add_argument(
        "--account",
        "-a",
        default=None,
        help="Google account alias or email (e.g. 'work_account', 'personal_account')",
    )
    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output structured JSON instead of human-readable text",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for the read_email CLI command."""
    args = parse_args(argv)
    try:
        thread_data = read_thread(args.thread_id, account=args.account)
    except Exception as exc:
        print(f"Error reading thread: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(thread_data, indent=2))
    else:
        print(format_readable_thread(thread_data))

    return 0


if __name__ == "__main__":
    sys.exit(main())
