#!/usr/bin/env python3
"""List unread conversations and mentions in the Slack workspace."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import run_slackcli


def main():
    parser = argparse.ArgumentParser(
        description="Check for unread messages, channels, and threads in Slack."
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

    code, data, stdout, stderr = run_slackcli(
        ["conversations", "unread"],
        workspace=args.workspace,
        json_mode=True,
    )

    if code != 0:
        sys.stderr.write(f"Error ({code}): {stderr or stdout}\n")
        sys.exit(code)

    if args.json:
        print(json.dumps(data or {}, indent=2))
        return

    channels = (data or {}).get("unread_channels", [])
    threads = (data or {}).get("threads", {})

    if not channels and not threads.get("has_unreads"):
        print("No unread messages or conversations found.")
        return

    print(f"Unread Conversations ({len(channels)}):\n")
    header = f"{'ID':<14} {'NAME':<32} {'TYPE':<10} {'MENTIONS'}"
    print(header)
    print("-" * len(header))

    for c in channels:
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
        mentions = c.get("mention_count", 0)
        mention_str = f"{mentions} mention(s)" if mentions > 0 else "-"

        print(f"{cid:<14} #{name:<31} {ctype:<10} {mention_str}")

    if threads.get("has_unreads"):
        print(f"\nThreads: Has unreads (mentions: {threads.get('mention_count', 0)})")


if __name__ == "__main__":
    main()
