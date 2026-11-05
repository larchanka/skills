#!/usr/bin/env python3
"""Modifies Gmail thread labels and status (mark-read, archive, trash, delete, custom labels)."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

# Allow relative imports when run as a standalone script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.common import run_gog


def _split_label_args(label_args: Optional[list[str]]) -> set[str]:
    """Flattens a list of comma-separated or repeated label strings into a set."""
    labels: set[str] = set()
    if not label_args:
        return labels
    for item in label_args:
        for part in item.split(","):
            cleaned = part.strip()
            if cleaned:
                labels.add(cleaned)
    return labels


def _build_modify_args(thread_id: str, add_set: set[str], remove_set: set[str]) -> list[str]:
    """Builds gog CLI arguments for thread modify command."""
    args = ["gmail", "thread", "modify", thread_id]
    if add_set:
        args.append(f"--add={','.join(sorted(add_set))}")
    if remove_set:
        args.append(f"--remove={','.join(sorted(remove_set))}")
    return args


def _build_triage_plan(
    mark_read: bool,
    archive: bool,
    trash: bool,
    delete: bool,
    add_labels: Optional[list[str]],
    remove_labels: Optional[list[str]],
) -> tuple[set[str], set[str], list[str]]:
    """Calculates label additions, removals, and named actions for triage."""
    add_set = _split_label_args(add_labels)
    remove_set = _split_label_args(remove_labels)

    if mark_read:
        remove_set.add("UNREAD")
    if archive:
        remove_set.add("INBOX")
    if trash:
        add_set.add("TRASH")

    action_list = []
    if mark_read:
        action_list.append("mark_read")
    if archive:
        action_list.append("archive")
    if trash:
        action_list.append("trash")
    if delete:
        action_list.append("delete")

    return add_set, remove_set, action_list


def _execute_thread_mutation(
    thread_id: str,
    delete: bool,
    add_set: set[str],
    remove_set: set[str],
    account: Optional[str],
) -> None:
    """Executes state mutation for a single thread via gog CLI."""
    if delete:
        args = ["gmail", "batch", "delete", thread_id, "--force"]
        code, _, _, stderr = run_gog(args, account=account, json_mode=True)
        if code != 0:
            raise RuntimeError(stderr or f"Failed to permanently delete {thread_id}")
    elif add_set or remove_set:
        args = _build_modify_args(thread_id, add_set, remove_set)
        code, _, _, stderr = run_gog(args, account=account, json_mode=True)
        if code != 0:
            raise RuntimeError(stderr or f"Failed to modify labels on {thread_id}")


def apply_triage(
    thread_ids: list[str],
    mark_read: bool = False,
    archive: bool = False,
    trash: bool = False,
    delete: bool = False,
    force: bool = False,
    add_labels: Optional[list[str]] = None,
    remove_labels: Optional[list[str]] = None,
    dry_run: bool = False,
    account: Optional[str] = None,
) -> dict[str, Any]:
    """
    Applies triage actions to one or more Gmail thread IDs.

    Args:
        thread_ids: List of Gmail thread IDs to modify.
        mark_read: Removes UNREAD label.
        archive: Removes INBOX label.
        trash: Adds TRASH label (moves to Gmail Trash).
        delete: Permanently deletes thread(s) (requires force=True).
        force: Required to authorize permanent delete.
        add_labels: Additional labels to add.
        remove_labels: Additional labels to remove.
        dry_run: If True, simulates changes without executing them.
        account: Account alias or email address.

    Returns:
        Structured result dictionary.
    """
    if delete and not force:
        raise RuntimeError("Permanent deletion requires --force for safety.")

    add_set, remove_set, action_list = _build_triage_plan(
        mark_read=mark_read,
        archive=archive,
        trash=trash,
        delete=delete,
        add_labels=add_labels,
        remove_labels=remove_labels,
    )

    details = [
        {
            "thread_id": tid,
            "actions": action_list,
            "add_labels": sorted(list(add_set)),
            "remove_labels": sorted(list(remove_set)),
        }
        for tid in thread_ids
    ]

    if dry_run:
        return {
            "dry_run": True,
            "thread_ids": thread_ids,
            "add_labels": sorted(list(add_set)),
            "remove_labels": sorted(list(remove_set)),
            "delete": delete,
            "success": True,
            "status": "simulated",
            "details": details,
        }

    for tid in thread_ids:
        _execute_thread_mutation(tid, delete, add_set, remove_set, account)

    return {
        "dry_run": False,
        "thread_ids": thread_ids,
        "add_labels": sorted(list(add_set)),
        "remove_labels": sorted(list(remove_set)),
        "delete": delete,
        "success": True,
        "details": details,
    }


def format_readable_triage_result(result: dict[str, Any]) -> str:
    """Formats triage execution results into a human-readable confirmation message."""
    dry_run = result.get("dry_run", False)
    prefix = "[SIMULATED] " if dry_run else ""
    header = f"{prefix}Triage Actions Applied ({len(result.get('thread_ids', []))} threads)"
    lines = [header, "=" * 60]

    for item in result.get("details", []):
        tid = item.get("thread_id", "")
        actions = ", ".join(item.get("actions") or ["no-op"])
        adds = ", ".join(item.get("add_labels") or [])
        removes = ", ".join(item.get("remove_labels") or [])

        lines.append(f"Thread: {tid}")
        lines.append(f"  Actions: {actions}")
        if adds:
            lines.append(f"  Added:   {adds}")
        if removes:
            lines.append(f"  Removed: {removes}")
        lines.append("-" * 60)

    return "\n".join(lines)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parses command-line arguments for apply_triage."""
    parser = argparse.ArgumentParser(
        description="Apply triage label and status modifications to Gmail threads."
    )
    parser.add_argument(
        "thread_ids",
        nargs="+",
        help="One or more Gmail thread IDs to modify",
    )
    parser.add_argument(
        "--mark-read",
        action="store_true",
        help="Remove UNREAD label",
    )
    parser.add_argument(
        "--archive",
        action="store_true",
        help="Remove INBOX label",
    )
    parser.add_argument(
        "--trash",
        action="store_true",
        help="Add TRASH label (moves thread to Gmail Trash)",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Permanently delete thread (requires --force)",
    )
    parser.add_argument(
        "--force",
        "-y",
        action="store_true",
        help="Confirm destructive operations (required for --delete)",
    )
    parser.add_argument(
        "--add-label",
        action="append",
        dest="add_labels",
        help="Label to add (can be repeated or comma-separated)",
    )
    parser.add_argument(
        "--remove-label",
        action="append",
        dest="remove_labels",
        help="Label to remove (can be repeated or comma-separated)",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Simulate actions without modifying Gmail state",
    )
    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output structured JSON summary",
    )
    parser.add_argument(
        "--account",
        "-a",
        default=None,
        help="Google account alias or email (e.g. 'work_account', 'personal_account')",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for the apply_triage CLI command."""
    args = parse_args(argv)
    try:
        result = apply_triage(
            thread_ids=args.thread_ids,
            mark_read=args.mark_read,
            archive=args.archive,
            trash=args.trash,
            delete=args.delete,
            force=args.force,
            add_labels=args.add_labels,
            remove_labels=args.remove_labels,
            dry_run=args.dry_run,
            account=args.account,
        )
    except Exception as exc:
        print(f"Error applying triage: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_readable_triage_result(result))

    return 0


if __name__ == "__main__":
    sys.exit(main())
