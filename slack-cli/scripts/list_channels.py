#!/usr/bin/env python3
"""List accessible channels and conversations in the Slack workspace."""

import argparse
import json
import sys
from pathlib import Path

# Add script directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))
from common import run_slackcli


def main():
    parser = argparse.ArgumentParser(
        description="List Slack channels, private groups, and DMs."
    )
    parser.add_argument(
        "--filter",
        "-f",
        type=str,
        default="",
        help="Filter channels by name substring",
    )
    parser.add_argument(
        "--types",
        "-t",
        type=str,
        default="",
        help="Comma-separated channel types to include (e.g. public,private,im,mpim)",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=0,
        help="Limit the number of results shown (0 for all)",
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

    cmd = ["conversations", "list"]
    if args.types:
        cmd.extend(["--types", args.types])

    code, data, stdout, stderr = run_slackcli(cmd, workspace=args.workspace, json_mode=True)

    if code != 0:
        sys.stderr.write(f"Error ({code}): {stderr or stdout}\n")
        sys.exit(code)

    if not data or "conversations" not in data:
        if args.json:
            print(json.dumps(data or {}))
        else:
            print("No conversations found.")
        return

    conversations = data.get("conversations", [])

    if args.filter:
        pattern = args.filter.lower()
        conversations = [
            c for c in conversations if pattern in c.get("name", "").lower()
        ]

    if args.limit > 0:
        conversations = conversations[: args.limit]

    if args.json:
        print(json.dumps({"conversations": conversations, "count": len(conversations)}, indent=2))
        return

    print(f"Found {len(conversations)} conversation(s):\n")
    header = f"{'ID':<14} {'NAME':<32} {'TYPE':<10} {'MEMBERS':<8} {'TOPIC'}"
    print(header)
    print("-" * len(header))

    for c in conversations:
        cid = c.get("id", "")
        name = c.get("name", "<unnamed>")
        if c.get("is_im"):
            ctype = "DM"
        elif c.get("is_mpim"):
            ctype = "Group DM"
        elif c.get("is_private"):
            ctype = "Private"
        else:
            ctype = "Public"

        members = str(c.get("num_members", "-"))
        topic = (c.get("topic") or c.get("purpose") or "").replace("\n", " ")
        if len(topic) > 40:
            topic = topic[:37] + "..."

        print(f"{cid:<14} #{name:<31} {ctype:<10} {members:<8} {topic}")


if __name__ == "__main__":
    main()
