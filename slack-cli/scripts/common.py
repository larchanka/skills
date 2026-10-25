#!/usr/bin/env python3
"""Shared helper utilities for Slack CLI automation scripts."""

import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional, Tuple


def get_slackcli_bin() -> str:
    """Finds the path to the slackcli executable."""
    bin_path = shutil.which("slackcli")
    if bin_path:
        return bin_path
    
    fallback = Path.home() / ".local" / "bin" / "slackcli"
    if fallback.exists() and os.access(fallback, os.X_OK):
        return str(fallback)
        
    raise FileNotFoundError(
        "slackcli binary not found in PATH or ~/.local/bin/slackcli. "
        "Please install it or check your environment."
    )


def run_slackcli(
    args: list[str],
    workspace: Optional[str] = None,
    json_mode: bool = True,
) -> Tuple[int, Optional[Any], str, str]:
    """
    Executes a slackcli command safely.
    
    Returns:
        (returncode, parsed_json_data, stdout_text, stderr_text)
    """
    slackcli = get_slackcli_bin()
    cmd = [slackcli] + args
    
    if workspace:
        cmd.extend(["--workspace", workspace])
        
    if json_mode and "--json" not in cmd:
        cmd.append("--json")
        
    proc = subprocess.run(cmd, capture_output=True, text=True)
    
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    
    parsed_json = None
    if json_mode and stdout:
        try:
            parsed_json = json.loads(stdout)
        except json.JSONDecodeError:
            pass
            
    return proc.returncode, parsed_json, stdout, stderr


def format_ts(ts: str) -> str:
    """Converts a Slack timestamp (e.g. 1712345678.123456) to human-readable string."""
    try:
        epoch = float(ts.split(".")[0])
        dt = datetime.datetime.fromtimestamp(epoch)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ts
