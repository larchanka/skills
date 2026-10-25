#!/usr/bin/env python3
"""Send a message or thread reply to a Slack channel or user."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import run_slackcli


def main():
    parser = argparse.ArgumentParser(
        description="Send a message or thread reply to a Slack channel or DM."
    )
    parser.add_argument(
        "--recipient",
        "-r",
        type=str,
        default=None,
        help="Recipient channel ID (C...), channel name (#general), @username, or email",
    )
    parser.add_argument(
        "--message",
        "-m",
        type=str,
        default=None,
        help="Message text content to send",
    )
    parser.add_argument(
        "--message-file",
        type=str,
        default=None,
        help="Path to a text file containing the message body",
    )
    parser.add_argument(
        "--thread-ts",
        "-t",
        type=str,
        default=None,
        help="Parent message timestamp to post as a thread reply (e.g. 1712345678.123456)",
    )
    parser.add_argument(
        "--permalink",
        "-p",
        type=str,
        default=None,
        help="Slack permalink URL (replaces --recipient and --thread-ts)",
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        action="append",
        default=[],
        help="File path to attach (can be specified multiple times)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate and validate the message without actually posting it",
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

    if not args.permalink and not args.recipient:
        sys.stderr.write("Error: Must provide either --recipient or --permalink\n")
        sys.exit(1)

    if not args.message and not args.message_file:
        sys.stderr.write("Error: Must provide either --message or --message-file\n")
        sys.exit(1)

    cmd = ["messages", "send"]

    if args.permalink:
        cmd.extend(["--permalink", args.permalink])
    elif args.recipient:
        cmd.extend(["--recipient-id", args.recipient])

    if args.thread_ts:
        cmd.extend(["--thread-ts", args.thread_ts])

    if args.message:
        cmd.extend(["--message", args.message])
    elif args.message_file:
        cmd.extend(["--message-file", args.message_file])

    for file_path in args.file:
        cmd.extend(["--file", file_path])

    if args.dry_run:
        cmd.append("--dry-run")

    code, data, stdout, stderr = run_slackcli(cmd, workspace=args.workspace, json_mode=True)

    if code != 0:
        sys.stderr.write(f"Error ({code}): {stderr or stdout}\n")
        sys.exit(code)

    if args.dry_run:
        print("Dry run successful (no message posted):")
        print(stdout or stderr)
        return

    if args.json:
        print(json.dumps(data or {}, indent=2))
        return

    channel_id = (data or {}).get("channel_id")
    ts = (data or {}).get("ts")
    permalink = (data or {}).get("permalink")

    print("✔ Message sent successfully!")
    if channel_id:
        print(f"  Channel:   {channel_id}")
    if ts:
        print(f"  Timestamp: {ts}")
    if permalink:
        print(f"  Permalink: {permalink}")


if __name__ == "__main__":
    main()
