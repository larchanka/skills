#!/usr/bin/env python3
"""Mark Slack conversations or all unread conversations as read."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import run_slackcli


def get_latest_ts(channel_id: str, workspace: str | None = None) -> str | None:
    """Fetch the latest message timestamp for a channel."""
    rc, data, _, stderr = run_slackcli(
        ["conversations", "read", channel_id, "--limit", "1"],
        workspace=workspace,
        json_mode=True,
    )
    if rc != 0 or not data or not data.get("messages"):
        return None
    return data["messages"][0].get("ts")


def mark_channel_read(
    channel: str,
    ts: str | None = None,
    workspace: str | None = None,
    dry_run: bool = False,
) -> tuple[bool, str, dict]:
    """Marks a single channel as read up to ts or latest message."""
    target_ts = ts
    if not target_ts:
        target_ts = get_latest_ts(channel, workspace=workspace)
        if not target_ts:
            return False, f"Could not find any messages in channel {channel}", {}

    cmd = ["conversations", "mark-read", channel, "--ts", target_ts]
    if dry_run:
        cmd.append("--dry-run")
    else:
        cmd.append("--yes")

    rc, data, stdout, stderr = run_slackcli(cmd, workspace=workspace, json_mode=True)
    if rc != 0:
        return False, stderr or stdout, {}

    return True, f"Marked as read up to {target_ts}", data or {}


def main():
    parser = argparse.ArgumentParser(
        description="Mark a Slack channel or all unread channels as read."
    )
    parser.add_argument(
        "channel",
        nargs="?",
        default=None,
        help="Channel ID, name or URL (e.g. #general, general, C0123...)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Mark all unread channels as read",
    )
    parser.add_argument(
        "--ts",
        type=str,
        default=None,
        help="Message timestamp to mark read up to (defaults to latest message)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the action without actually marking anything as read",
    )
    parser.add_argument(
        "--workspace",
        "-w",
        type=str,
        default=None,
        help="Specific Slack workspace name or ID",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON data",
    )

    args = parser.parse_args()

    if not args.channel and not args.all:
        sys.stderr.write("Error: Must provide either a channel or --all\n")
        sys.exit(1)

    results = []

    if args.all:
        rc, unread_data, _, stderr = run_slackcli(
            ["conversations", "unread"],
            workspace=args.workspace,
            json_mode=True,
        )
        if rc != 0:
            sys.stderr.write(f"Error fetching unread channels: {stderr}\n")
            sys.exit(rc)

        unread_channels = unread_data.get("unread_channels", []) if unread_data else []
        if not unread_channels:
            if args.json:
                print(json.dumps({"marked": []}))
            else:
                print("No unread channels found.")
            return

        for ch in unread_channels:
            ch_id = ch.get("id")
            ch_name = ch.get("name", ch_id)
            success, msg, details = mark_channel_read(
                ch_id, workspace=args.workspace, dry_run=args.dry_run
            )
            results.append(
                {
                    "id": ch_id,
                    "name": ch_name,
                    "success": success,
                    "message": msg,
                    "details": details,
                }
            )
    else:
        success, msg, details = mark_channel_read(
            args.channel, ts=args.ts, workspace=args.workspace, dry_run=args.dry_run
        )
        results.append(
            {
                "id": args.channel,
                "name": args.channel,
                "success": success,
                "message": msg,
                "details": details,
            }
        )

    if args.json:
        print(json.dumps(results, indent=2))
        return

    prefix = "Dry run: " if args.dry_run else "✔ "
    for r in results:
        status_icon = prefix if r["success"] else "✖ "
        channel_label = f"#{r['name']}" if not r['name'].startswith("#") else r['name']
        print(f"{status_icon}{channel_label}: {r['message']}")


if __name__ == "__main__":
    main()
