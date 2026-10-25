#!/usr/bin/env python3
"""Look up Slack user profile and account details."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import run_slackcli


def main():
    parser = argparse.ArgumentParser(
        description="Show profile and status details for a Slack user."
    )
    parser.add_argument(
        "user",
        type=str,
        help="User ID (U...), @handle, or email address",
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

    cmd = ["users", "info", args.user]
    code, data, stdout, stderr = run_slackcli(cmd, workspace=args.workspace, json_mode=True)

    if code != 0:
        sys.stderr.write(f"Error ({code}): {stderr or stdout}\n")
        sys.exit(code)

    if args.json:
        print(json.dumps(data or {}, indent=2))
        return

    user = data or {}
    profile = user.get("profile", {})

    print(f"User: {user.get('real_name') or user.get('name')}")
    print("-" * 40)
    print(f"ID:         {user.get('id')}")
    print(f"Handle:     @{user.get('name')}")
    print(f"Email:      {profile.get('email', '-')}")
    print(f"Title:      {profile.get('title', '-')}")
    print(f"Timezone:   {user.get('tz', '-')} ({user.get('tz_label', '-')})")
    print(f"Is Admin:   {user.get('is_admin', False)}")
    print(f"Is Bot:     {user.get('is_bot', False)}")
    print(f"Deactivated:{user.get('deleted', False)}")


if __name__ == "__main__":
    main()
