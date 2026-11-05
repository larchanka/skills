#!/usr/bin/env python3
"""Shared helper utilities for email-triage automation scripts wrapping the gog CLI."""

import html
import html.parser
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional, Tuple

# Common fallback paths for gog binary
GOG_FALLBACK_PATHS = [
    "/opt/homebrew/bin/gog",
    "/usr/local/bin/gog",
    str(Path.home() / ".local" / "bin" / "gog"),
    str(Path.home() / "bin" / "gog"),
]

IGNORED_TAGS = {"script", "style", "head", "title", "svg", "noscript"}

_ACCOUNT_CACHE: dict[str, Any] = {}


def clear_account_cache() -> None:
    """Clears the internal cache for dynamically discovered accounts and aliases."""
    _ACCOUNT_CACHE.clear()


DISCLAIMER_PATTERNS = [
    re.compile(
        r"(?is)^.*?(this (message|email|communication)|the information in this (email|message)).*?"
        r"(confidential|privileged).*?"
        r"(intended recipient|delete|destroy|notify).*?$"
    ),
    re.compile(
        r"(?is)^.*?if you (are not the intended recipient|"
        r"have received this (email|message) in error).*?"
        r"(notify|delete|destroy).*?$"
    ),
    re.compile(
        r"(?is)^.*?you (are receiving|received) this (email|update|message|newsletter) because.*$"
    ),
    re.compile(
        r"(?is)^.*?(click here to unsubscribe|to unsubscribe|opt[ -]?out|manage preferences).*$"
    ),
    re.compile(
        r"(?is)^.*?\[?unsubscribe\]?.*?(preferences|privacy policy|view in browser).*?$"
    ),
]


def get_gog_bin() -> str:
    """Discovers the path to the gog executable from PATH or common locations."""
    bin_path = shutil.which("gog")
    if bin_path:
        return bin_path

    for fallback in GOG_FALLBACK_PATHS:
        if os.path.isfile(fallback) and os.access(fallback, os.X_OK):
            return fallback

    raise FileNotFoundError(
        "gog binary not found in PATH or standard installation locations "
        f"({', '.join(GOG_FALLBACK_PATHS)}). Please install gog or check PATH."
    )


def get_default_account() -> Optional[str]:
    """
    Discovers the default Google account email from GOG_ACCOUNT env var
    or via `gog auth status --json`.
    """
    env_acc = os.environ.get("GOG_ACCOUNT")
    if env_acc and env_acc.strip():
        return env_acc.strip()

    if "default_account" in _ACCOUNT_CACHE:
        return _ACCOUNT_CACHE["default_account"]

    try:
        gog_bin = get_gog_bin()
        proc = subprocess.run([gog_bin, "auth", "status", "-j"], capture_output=True, text=True)
        if proc.returncode == 0 and proc.stdout.strip():
            data = json.loads(proc.stdout.strip())
            email = data.get("account", {}).get("email")
            if email and email.strip():
                _ACCOUNT_CACHE["default_account"] = email.strip()
                return email.strip()
    except Exception:
        pass

    return None


def get_account_aliases() -> dict[str, str]:
    """Discovers account aliases dynamically via `gog auth alias list --json`."""
    if "aliases" in _ACCOUNT_CACHE:
        return _ACCOUNT_CACHE["aliases"]

    try:
        gog_bin = get_gog_bin()
        proc = subprocess.run(
            [gog_bin, "auth", "alias", "list", "-j"],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            data = json.loads(proc.stdout.strip())
            aliases = data.get("aliases") or {}
            normalized = {k.lower(): v.strip() for k, v in aliases.items() if v}
            _ACCOUNT_CACHE["aliases"] = normalized
            return normalized
    except Exception:
        pass

    return {}


def _extract_gmail_emails(accounts: list[dict[str, Any]]) -> list[str]:
    """Filters email addresses with active gmail service."""
    discovered: list[str] = []
    for acc in accounts:
        email = (acc.get("email") or "").strip()
        services = acc.get("services") or []
        if email and "gmail" in services and email not in discovered:
            discovered.append(email)
    return discovered


def _fetch_accounts_from_gog() -> list[str]:
    """Queries `gog auth list --json` and filters accounts with Gmail service enabled."""
    try:
        gog_bin = get_gog_bin()
        proc = subprocess.run([gog_bin, "auth", "list", "-j"], capture_output=True, text=True)
        if proc.returncode == 0 and proc.stdout.strip():
            data = json.loads(proc.stdout.strip())
            return _extract_gmail_emails(data.get("accounts") or [])
    except Exception:
        pass
    return []


def get_configured_accounts() -> list[str]:
    """
    Discovers all configured Google accounts with Gmail service enabled via `gog auth list --json`.
    Returns the default account first, followed by remaining configured accounts.
    """
    if "accounts" in _ACCOUNT_CACHE:
        return _ACCOUNT_CACHE["accounts"]

    discovered = _fetch_accounts_from_gog()
    default_acc = get_default_account()

    ordered: list[str] = []
    if default_acc:
        ordered.append(default_acc)
    for email in discovered:
        if email not in ordered:
            ordered.append(email)

    _ACCOUNT_CACHE["accounts"] = ordered
    return ordered


def resolve_account(account: Optional[str] = None) -> str:
    """
    Resolves the Google account email address dynamically.

    Precedence:
    1. Explicit `account` argument (resolving aliases like 'work_account' or 'personal_account')
    2. Environment variable `GOG_ACCOUNT` (resolving aliases)
    3. Discovered default account from `get_default_account()`
    """
    candidate = account.strip() if account and account.strip() else None
    if not candidate:
        env_acc = os.environ.get("GOG_ACCOUNT")
        candidate = env_acc.strip() if env_acc and env_acc.strip() else None

    aliases = get_account_aliases()
    if candidate:
        return aliases.get(candidate.lower(), candidate)

    default_acc = get_default_account()
    if default_acc:
        return aliases.get(default_acc.lower(), default_acc)

    configured = get_configured_accounts()
    if configured:
        return configured[0]

    return "default"


def build_gog_command(
    cmd_args: list[str],
    account: Optional[str] = None,
    json_mode: bool = True,
) -> list[str]:
    """Constructs the gog CLI argument list with account and JSON output flags."""
    gog_bin = get_gog_bin()
    cmd = [gog_bin] + list(cmd_args)

    has_account = any(arg == "-a" or arg.startswith("--account") for arg in cmd)
    if not has_account:
        resolved_acc = resolve_account(account)
        cmd.extend(["-a", resolved_acc])

    has_json = any(arg == "-j" or arg.startswith("--json") for arg in cmd)
    if json_mode and not has_json:
        cmd.append("-j")

    return cmd


def run_gog(
    cmd_args: list[str],
    account: Optional[str] = None,
    json_mode: bool = True,
) -> Tuple[int, Optional[Any], str, str]:
    """
    Executes a gog CLI command safely via subprocess.

    Args:
        cmd_args: List of command arguments (e.g. ['gmail', 'search', 'is:unread'])
        account: Account name or alias ('work_account', 'personal_account', or full email).
        json_mode: When True, appends -j if not present and parses stdout into JSON.

    Returns:
        (returncode, parsed_json_or_none, stdout_str, stderr_str)
    """
    cmd = build_gog_command(cmd_args, account=account, json_mode=json_mode)
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


class _HTMLCleaner(html.parser.HTMLParser):
    """Parses HTML email body and converts it to clean structured markdown text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.pieces: list[str] = []
        self.skip_depth = 0
        self.link_stack: list[dict[str, Any]] = []

    def close(self) -> None:
        while self.link_stack:
            self._handle_link_end()
        super().close()

    def handle_starttag(self, tag: str, attrs: list[Tuple[str, Optional[str]]]) -> None:
        tag_lower = tag.lower()
        if tag_lower in IGNORED_TAGS:
            self.skip_depth += 1
            return

        if self.skip_depth > 0:
            return

        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        if tag_lower == "img":
            self._handle_img(attr_dict)
        elif tag_lower == "a":
            self.link_stack.append({
                "href": attr_dict.get("href", "").strip(),
                "text_parts": [],
            })
        else:
            self._handle_block_start(tag_lower)

    def _handle_img(self, attrs: dict[str, str]) -> None:
        if self._is_tracking_pixel(attrs):
            return
        alt = attrs.get("alt", "").strip()
        if alt:
            self.pieces.append(f"[{alt}]")

    def _handle_block_start(self, tag: str) -> None:
        # Flush any open unclosed link if a block level element starts
        while self.link_stack:
            self._handle_link_end()

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(tag[1])
            self._ensure_newlines(2)
            self.pieces.append(f"{'#' * level} ")
        elif tag in {"p", "div", "blockquote", "ul", "ol"}:
            self._ensure_newlines(2)
        elif tag == "br":
            self.pieces.append("\n")
        elif tag == "li":
            self._ensure_newlines(1)
            self.pieces.append("- ")

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower in IGNORED_TAGS:
            if self.skip_depth > 0:
                self.skip_depth -= 1
            return

        if self.skip_depth > 0:
            return

        if tag_lower == "a" and self.link_stack:
            self._handle_link_end()
        else:
            self._handle_block_end(tag_lower)

    def _handle_link_end(self) -> None:
        if not self.link_stack:
            return
        link_info = self.link_stack.pop()
        href = link_info["href"]
        text = "".join(link_info["text_parts"]).strip()

        if href and text:
            if text == href:
                self.pieces.append(href)
            else:
                self.pieces.append(f"[{text}]({href})")
        elif href:
            self.pieces.append(href)
        elif text:
            self.pieces.append(text)

    def _handle_block_end(self, tag: str) -> None:
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote", "ul", "ol"}:
            self._ensure_newlines(2)
        elif tag == "li":
            self._ensure_newlines(1)

    def handle_data(self, data: str) -> None:
        if self.skip_depth > 0:
            return

        if self.link_stack:
            self.link_stack[-1]["text_parts"].append(data)
            return

        if not data.strip():
            if not self.pieces:
                return
            last = self.pieces[-1]
            if last.endswith("\n") or last.endswith(" ") or last.endswith("- "):
                return
            self.pieces.append(" ")
        else:
            self.pieces.append(data)

    def _ensure_newlines(self, count: int) -> None:
        """Ensures that the output buffer ends with at least `count` newlines."""
        if not self.pieces:
            return
        combined = "".join(self.pieces[-3:])
        existing = len(combined) - len(combined.rstrip("\n"))
        needed = count - existing
        if needed > 0:
            self.pieces.append("\n" * needed)

    def _is_tracking_pixel(self, attrs: dict[str, str]) -> bool:
        """Detects 0x0 or 1x1 tracking pixels or hidden images."""
        width = attrs.get("width", "").strip()
        height = attrs.get("height", "").strip()
        style = attrs.get("style", "").lower()

        if width in {"0", "1"} and height in {"0", "1"}:
            return True
        if "display:none" in style or "visibility:hidden" in style:
            return True
        return False

    def get_text(self) -> str:
        return "".join(self.pieces)


def _is_disclaimer_or_boilerplate(paragraph: str) -> bool:
    """Checks whether a paragraph matches standard corporate disclaimer/footer patterns."""
    text = paragraph.strip()
    for pattern in DISCLAIMER_PATTERNS:
        if pattern.match(text):
            return True
    return False


def clean_email_body(raw_content: Optional[str]) -> str:
    """
    Sanitizes raw email content by stripping HTML tags, scripts, CSS,
    tracking pixels, and corporate confidentiality/unsubscribe boilerplates,
    preserving links, lists, and formatting.
    """
    if not raw_content or not raw_content.strip():
        return ""

    text = raw_content

    # If it contains HTML markup, parse via _HTMLCleaner
    if "<" in text and ">" in text:
        try:
            parser = _HTMLCleaner()
            parser.feed(text)
            parser.close()
            text = parser.get_text()
        except Exception:
            # Fallback regex strip if HTML parsing encounters any unrecoverable errors
            text = re.sub(
                r"<(script|style|head)[^>]*>.*?</\1>",
                "",
                text,
                flags=re.DOTALL | re.IGNORECASE,
            )
            text = re.sub(r"<[^>]+>", " ", text)
            text = html.unescape(text)

    # Normalize line endings and whitespace
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    normalized = "\n".join(lines)

    # Collapse 3 or more consecutive newlines into 2
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)

    # Filter out confidentiality boilerplates and unsubscribe footers
    paragraphs = normalized.split("\n\n")
    filtered = [p for p in paragraphs if not _is_disclaimer_or_boilerplate(p)]

    return "\n\n".join(filtered).strip()
