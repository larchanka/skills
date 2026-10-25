#!/usr/bin/env python3
"""Read a thread conversation in Slack."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import format_ts, run_slackcli


def main():
    parser = argparse.ArgumentParser(
        description="Read all messages in a specific Slack thread."
    )
    parser.add_argument(
        "channel",
        nargs="?",
        default=None,
        help="Channel ID, name or Slack URL (omit if using --permalink)",
    )
    parser.add_argument(
        "thread_ts",
        nargs="?",
        default=None,
        help="Thread parent timestamp (e.g. 1712345678.123456)",
    )
    parser.add_argument(
        "--permalink",
        "-p",
        type=str,
        default=None,
        help="Slack permalink URL to the thread message",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=50,
        help="Maximum number of replies to return (default: 50)",
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

    cmd = ["conversations", "read"]

    if args.permalink:
        cmd.extend(["--permalink", args.permalink])
    elif args.channel and args.thread_ts:
        cmd.extend([args.channel, "--thread-ts", args.thread_ts])
    else:
        sys.stderr.write(
            "Error: Provide either both <channel> and <thread_ts>, or --permalink <url>\n"
        )
        sys.exit(1)

    cmd.extend(["--limit", str(args.limit)])

    code, data, stdout, stderr = run_slackcli(cmd, workspace=args.workspace, json_mode=True)

    if code != 0:
        sys.stderr.write(f"Error ({code}): {stderr or stdout}\n")
        sys.exit(code)

    if args.json:
        print(json.dumps(data or {}, indent=2))
        return

    messages = (data or {}).get("messages", [])
    if not messages:
        print("No thread messages found.")
        return

    users_map = {}
    for u in (data or {}).get("users", []):
        uid = u.get("id")
        if uid:
            display = u.get("real_name") or u.get("name") or uid
            username = u.get("name")
            users_map[uid] = f"{display} (@{username})" if username else display

    parent = messages[0]
    replies = messages[1:]

    p_time = format_ts(parent.get("ts", ""))
    p_author = users_map.get(parent.get("user"), parent.get("user", "Unknown"))
    print(f"=== Thread Parent: [{p_time}] {p_author} ===")
    print(parent.get("text", ""))
    print(f"Parent ts: {parent.get('ts')}\n")

    if replies:
        print(f"--- Replies ({len(replies)}) ---")
        for idx, r in enumerate(replies, start=1):
            r_time = format_ts(r.get("ts", ""))
            r_author = users_map.get(r.get("user"), r.get("user", "Unknown"))
            print(f"[{idx}] [{r_time}] {r_author} (ts: {r.get('ts')}):")
            print(f"    {r.get('text', '')}")
            reactions = r.get("reactions", [])
            if reactions:
                reaction_strs = [f":{rx.get('name')}: ({rx.get('count')})" for rx in reactions]
                print(f"    Reactions: {' '.join(reaction_strs)}")
            print()
    else:
        print("No replies in this thread yet.")


if __name__ == "__main__":
    main()
