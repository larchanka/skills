#!/usr/bin/env python3
"""Read recent messages from a Slack channel or DM."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import format_ts, run_slackcli


def main():
    parser = argparse.ArgumentParser(
        description="Read messages from a Slack channel, group, or DM."
    )
    parser.add_argument(
        "channel",
        type=str,
        help="Channel ID, Slack URL, or channel name (e.g. #general, general, C0123...)",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=20,
        help="Maximum number of messages to return (default: 20)",
    )
    parser.add_argument(
        "--exclude-replies",
        action="store_true",
        help="Exclude threaded replies (show only top-level channel messages)",
    )
    parser.add_argument(
        "--oldest",
        type=str,
        default=None,
        help="Start of time range (timestamp or epoch seconds)",
    )
    parser.add_argument(
        "--latest",
        type=str,
        default=None,
        help="End of time range (timestamp or epoch seconds)",
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

    cmd = ["conversations", "read", args.channel, "--limit", str(args.limit)]
    if args.exclude_replies:
        cmd.append("--exclude-replies")
    if args.oldest:
        cmd.extend(["--oldest", args.oldest])
    if args.latest:
        cmd.extend(["--latest", args.latest])

    code, data, stdout, stderr = run_slackcli(cmd, workspace=args.workspace, json_mode=True)

    if code != 0:
        sys.stderr.write(f"Error ({code}): {stderr or stdout}\n")
        sys.exit(code)

    if args.json:
        print(json.dumps(data or {}, indent=2))
        return

    messages = (data or {}).get("messages", [])
    if not messages:
        print(f"No messages found for channel {args.channel}.")
        return

    users_map = {}
    for u in (data or {}).get("users", []):
        uid = u.get("id")
        if uid:
            display = u.get("real_name") or u.get("name") or uid
            username = u.get("name")
            users_map[uid] = f"{display} (@{username})" if username else display

    print(f"Messages in {args.channel} ({len(messages)}):\n")

    for msg in messages:
        ts = msg.get("ts", "")
        readable_time = format_ts(ts)
        uid = msg.get("user") or msg.get("bot_id") or "Unknown"
        author = users_map.get(uid, uid)
        text = msg.get("text", "")

        header = f"[{readable_time}] {author} (ts: {ts})"
        print(header)
        print("-" * min(len(header), 80))
        print(text)

        # Reactions
        reactions = msg.get("reactions", [])
        if reactions:
            reaction_strs = [f":{r.get('name')}: ({r.get('count')})" for r in reactions]
            print(f"Reactions: {' '.join(reaction_strs)}")

        # Thread information
        reply_count = msg.get("reply_count", 0)
        thread_ts = msg.get("thread_ts")
        if reply_count > 0 and thread_ts:
            print(f"Thread: {reply_count} replies (thread_ts: {thread_ts})")

        # Files attached
        files = msg.get("files", [])
        if files:
            file_names = [f.get("name") or f.get("title") or f.get("id") for f in files]
            print(f"Attachments: {', '.join(file_names)}")

        print()


if __name__ == "__main__":
    main()
