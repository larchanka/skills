#!/usr/bin/env python3
"""Inspects and manages Gmail labels, ensuring standard triage labels exist."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

# Allow relative imports when run as a standalone script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.common import run_gog

DEFAULT_TRIAGE_LABELS = [
    "Triage/Action-Needed",
    "Triage/Waiting",
    "Triage/FYI",
]


def list_labels(account: Optional[str] = None) -> list[dict[str, Any]]:
    """Lists all Gmail labels for the specified account."""
    code, data, _, stderr = run_gog(["gmail", "labels", "list"], account=account, json_mode=True)
    if code != 0:
        raise RuntimeError(stderr or f"Failed to list labels with exit code {code}")

    if not isinstance(data, dict):
        return []

    raw_labels = data.get("labels") or []
    return [
        {
            "id": lbl.get("id", ""),
            "name": lbl.get("name", ""),
            "type": lbl.get("type", "user"),
        }
        for lbl in raw_labels
    ]


def setup_triage_labels(
    account: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Idempotently creates standard triage labels if they do not already exist.

    Args:
        account: Account alias or email address.
        dry_run: When True, simulates creation without altering Gmail state.

    Returns:
        Summary dict of created and existing triage labels.
    """
    existing_labels = list_labels(account=account)
    existing_names = {lbl.get("name") for lbl in existing_labels}

    created: list[str] = []
    already_existing: list[str] = []

    for label_name in DEFAULT_TRIAGE_LABELS:
        if label_name in existing_names:
            already_existing.append(label_name)
        else:
            if not dry_run:
                code, _, _, stderr = run_gog(
                    ["gmail", "labels", "create", label_name],
                    account=account,
                    json_mode=True,
                )
                if code != 0:
                    raise RuntimeError(stderr or f"Failed to create label '{label_name}'")
            created.append(label_name)

    return {
        "status": "ok",
        "created": created,
        "existing": already_existing,
        "dry_run": dry_run,
    }


def format_readable_labels(labels: list[dict[str, Any]]) -> str:
    """Formats a list of labels into a readable table."""
    lines = [
        f"Gmail Labels ({len(labels)} total):",
        "-" * 60,
        f"{'ID':<25} {'TYPE':<10} {'NAME'}",
        "-" * 60,
    ]
    for lbl in sorted(labels, key=lambda x: (x.get("type", ""), x.get("name", ""))):
        lines.append(f"{lbl.get('id', ''):<25} {lbl.get('type', ''):<10} {lbl.get('name', '')}")
    lines.append("-" * 60)
    return "\n".join(lines)


def format_readable_setup(result: dict[str, Any]) -> str:
    """Formats label setup results into readable text."""
    dry_run = result.get("dry_run", False)
    prefix = "[SIMULATED] " if dry_run else ""
    created = result.get("created") or []
    existing = result.get("existing") or []

    lines = [
        f"{prefix}Triage Label Setup Completed",
        "=" * 60,
    ]
    if created:
        lines.append(f"Labels Created:  {', '.join(created)}")
    else:
        lines.append("Labels Created:  None (all labels already exist)")

    if existing:
        lines.append(f"Labels Existing: {', '.join(existing)}")
    lines.append("=" * 60)
    return "\n".join(lines)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parses command-line arguments for manage_labels."""
    parser = argparse.ArgumentParser(
        description="Inspect and set up standard Gmail triage labels."
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all labels in the mailbox",
    )
    parser.add_argument(
        "--setup",
        "-s",
        action="store_true",
        help="Ensure standard triage labels exist (creates missing ones)",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Simulate operations without making changes",
    )
    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output structured JSON instead of human-readable text",
    )
    parser.add_argument(
        "--account",
        "-a",
        default=None,
        help="Google account alias or email (e.g. 'work_account', 'personal_account')",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for manage_labels CLI command."""
    args = parse_args(argv)
    try:
        if args.setup:
            res = setup_triage_labels(account=args.account, dry_run=args.dry_run)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(format_readable_setup(res))
            return 0

        # Default action is listing labels
        labels = list_labels(account=args.account)
        if args.json:
            print(json.dumps(labels, indent=2))
        else:
            print(format_readable_labels(labels))
        return 0

    except Exception as exc:
        print(f"Error managing labels: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
