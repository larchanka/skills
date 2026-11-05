#!/usr/bin/env python3
"""Scans Gmail inbox for unread threads using the gog CLI across one or all configured accounts."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

# Allow relative imports when run as a standalone script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.common import get_configured_accounts, resolve_account, run_gog


def _scan_single_account(
    account: str,
    query: str,
    max_results: int,
) -> list[dict[str, Any]]:
    """Scans unread threads for a single Google account."""
    args = ["gmail", "search", query, f"--max={max_results}"]
    code, data, _, stderr = run_gog(args, account=account, json_mode=True)

    if code != 0:
        error_msg = stderr or f"gog gmail search failed for {account} with code {code}"
        raise RuntimeError(error_msg)

    if not isinstance(data, dict) or "threads" not in data:
        return []

    raw_threads = data.get("threads") or []
    normalized: list[dict[str, Any]] = []

    for t in raw_threads:
        raw_count = t.get("messageCount") or t.get("message_count") or 1
        normalized.append({
            "id": str(t.get("id", "")),
            "account": account,
            "date": str(t.get("date", "")),
            "from": str(t.get("from", "")),
            "subject": str(t.get("subject", "")),
            "snippet": str(t.get("snippet", "")),
            "labels": list(t.get("labels", [])),
            "message_count": int(raw_count),
        })

    return normalized


def scan_inbox(
    query: str = "is:unread in:inbox",
    max_results: int = 10,
    account: Optional[str] = None,
    all_accounts: bool = False,
) -> list[dict[str, Any]]:
    """
    Queries Gmail threads matching `query` across one or all configured accounts.
    Default account is always queried first.
    """
    if account:
        resolved_acc = resolve_account(account)
        return _scan_single_account(resolved_acc, query, max_results)

    # When account is None or all_accounts is set, query all configured accounts
    configured = get_configured_accounts()
    if not configured:
        fallback = resolve_account(None)
        configured = [fallback]

    all_threads: list[dict[str, Any]] = []
    for acc in configured:
        try:
            threads = _scan_single_account(acc, query, max_results)
            all_threads.extend(threads)
        except Exception:
            # Continue scanning other accounts if one encounters an error
            pass

    return all_threads


def format_readable_summary(threads: list[dict[str, Any]], query: str) -> str:
    """Formats a list of threads into a human-readable summary table."""
    if not threads:
        return f"No threads found matching query: '{query}'"

    lines = [
        f"Found {len(threads)} unread thread(s) matching '{query}':",
        "-" * 80,
    ]

    for th in threads:
        th_id = th.get("id", "")
        account = th.get("account", "")
        date = th.get("date", "")
        count = th.get("message_count", 1)
        sender = th.get("from", "Unknown")
        subject = th.get("subject", "(No subject)")
        labels = ", ".join(th.get("labels", []))
        snippet = th.get("snippet", "")

        header = f"[{th_id}] {date} | {count} msg(s)"
        if account:
            header += f" | {account}"
        lines.append(header)
        lines.append(f"  From:    {sender}")
        lines.append(f"  Subject: {subject}")
        if labels:
            lines.append(f"  Labels:  {labels}")
        if snippet:
            lines.append(f"  Snippet: {snippet}")
        lines.append("-" * 80)

    return "\n".join(lines)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parses command-line arguments for scan_inbox."""
    parser = argparse.ArgumentParser(
        description="Scan Gmail inbox for unread threads using gog CLI."
    )
    parser.add_argument(
        "--query",
        "-q",
        default="is:unread in:inbox",
        help="Gmail search query syntax (default: 'is:unread in:inbox')",
    )
    parser.add_argument(
        "--max",
        "-m",
        type=int,
        default=10,
        help="Maximum number of threads to return per account (default: 10)",
    )
    parser.add_argument(
        "--account",
        "-a",
        default=None,
        help="Specific Google account alias or email (scans all if omitted)",
    )
    parser.add_argument(
        "--all-accounts",
        action="store_true",
        help="Scan through all configured accounts (default behavior when --account is omitted)",
    )
    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output structured JSON instead of human-readable text",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for the scan_inbox CLI command."""
    args = parse_args(argv)
    try:
        threads = scan_inbox(
            query=args.query,
            max_results=args.max,
            account=args.account,
            all_accounts=args.all_accounts,
        )
    except Exception as exc:
        print(f"Error scanning inbox: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(threads, indent=2))
    else:
        print(format_readable_summary(threads, args.query))

    return 0


if __name__ == "__main__":
    sys.exit(main())
