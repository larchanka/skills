#!/usr/bin/env python3
"""Edit the text of an existing Slack message posted by the user."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import run_slackcli


def main():
    parser = argparse.ArgumentParser(
        description="Edit an existing Slack message posted by the authenticated user."
    )
    parser.add_argument(
        "--channel",
        "-c",
        type=str,
        default=None,
        help="Channel ID, name or URL (e.g. #general, general, C0123...)",
    )
    parser.add_argument(
        "--timestamp",
        "-t",
        type=str,
        default=None,
        help="Message timestamp (e.g. 1712345678.123456)",
    )
    parser.add_argument(
        "--permalink",
        "-p",
        type=str,
        default=None,
        help="Slack permalink URL to the message",
    )
    parser.add_argument(
        "--message",
        "-m",
        type=str,
        default=None,
        help="New message text content",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the action without actually modifying the message",
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

    if not args.permalink and not (args.channel and args.timestamp):
        sys.stderr.write("Error: Must provide either --permalink, or both --channel and --timestamp\n")
        sys.exit(1)

    if not args.message:
        sys.stderr.write("Error: Must provide --message with the new text content\n")
        sys.exit(1)

    cmd = ["messages", "edit", "--message", args.message]

    if args.permalink:
        cmd.extend(["--permalink", args.permalink])
    else:
        cmd.extend(["--channel-id", args.channel, "--timestamp", args.timestamp])

    if args.dry_run:
        cmd.append("--dry-run")

    code, data, stdout, stderr = run_slackcli(cmd, workspace=args.workspace, json_mode=True)

    if code != 0:
        sys.stderr.write(f"Error ({code}): {stderr or stdout}\n")
        sys.exit(code)

    if args.dry_run:
        print("Dry run: message would be updated.")
        print(stdout or stderr)
        return

    if args.json:
        print(json.dumps(data or {}, indent=2))
        return

    print("✔ Message edited successfully.")


if __name__ == "__main__":
    main()
