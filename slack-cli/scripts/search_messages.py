#!/usr/bin/env python3
"""Search messages across Slack workspace conversations."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import format_ts, run_slackcli


def main():
    parser = argparse.ArgumentParser(
        description="Search messages across Slack conversations with operators."
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="Search query text (supports Slack operators like after:YYYY-MM-DD, has:link)",
    )
    parser.add_argument(
        "--in",
        dest="in_channel",
        type=str,
        default=None,
        help="Filter by channel name (e.g. general)",
    )
    parser.add_argument(
        "--from",
        dest="from_user",
        type=str,
        default=None,
        help="Filter by username (e.g. alice)",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=20,
        help="Maximum results per page (default: 20)",
    )
    parser.add_argument(
        "--page",
        "-p",
        type=int,
        default=1,
        help="Page number (default: 1)",
    )
    parser.add_argument(
        "--sort",
        choices=["timestamp", "score"],
        default="timestamp",
        help="Sort results by timestamp or score (default: timestamp)",
    )
    parser.add_argument(
        "--sort-dir",
        choices=["desc", "asc"],
        default="desc",
        help="Sort direction (default: desc)",
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

    if not args.query and not args.in_channel and not args.from_user:
        sys.stderr.write("Error: Must provide search query, --in <channel>, or --from <user>\n")
        sys.exit(1)

    cmd = ["search", "messages"]
    if args.query:
        cmd.append(args.query)
    if args.in_channel:
        cmd.extend(["--in", args.in_channel])
    if args.from_user:
        cmd.extend(["--from", args.from_user])

    cmd.extend([
        "--limit", str(args.limit),
        "--page", str(args.page),
        "--sort", args.sort,
        "--sort-dir", args.sort_dir,
    ])

    code, data, stdout, stderr = run_slackcli(cmd, workspace=args.workspace, json_mode=True)

    if code != 0:
        sys.stderr.write(f"Error ({code}): {stderr or stdout}\n")
        sys.exit(code)

    if args.json:
        print(json.dumps(data or {}, indent=2))
        return

    matches = (data or {}).get("matches", [])
    total = (data or {}).get("total", 0)

    if not matches:
        print("No matching messages found.")
        return

    print(f"Found {total} result(s) (showing {len(matches)} on page {args.page}):\n")

    for idx, m in enumerate(matches, start=1):
        ch = m.get("channel", {})
        ch_name = ch.get("name") or ch.get("id") or "unknown"
        user = m.get("username") or m.get("user") or "unknown"
        ts = m.get("ts", "")
        time_str = format_ts(ts)
        text = m.get("text", "").replace("\n", " ")
        if len(text) > 120:
            text = text[:117] + "..."
        permalink = m.get("permalink", "")

        print(f"[{idx}] #{ch_name} | {user} ({time_str})")
        print(f"    Message:   {text}")
        if permalink:
            print(f"    Permalink: {permalink}")
        print()


if __name__ == "__main__":
    main()
