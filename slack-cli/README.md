# Slack CLI Helper Skill (`slack-cli`)

A safe, curated Python automation suite providing programmatic Slack workspace integration for AI agents and developers.

---

## Overview

The `slack-cli` skill provides a secure, structured layer over the Slack CLI tool. Rather than allowing unrestricted or error-prone command-line execution, this skill wraps common Slack operations into dedicated, thoroughly tested Python helper scripts.

### Core Philosophy

> [!IMPORTANT]
> **Strict Tool Policy: No Direct Raw CLI Execution**
> AI agents and automated routines must **NEVER** run the raw `slackcli` binary directly. All interactions MUST proceed through the approved scripts in `./scripts/`.

- **Operational Safety**: Eliminates the risk of destructive actions (e.g., accidental channel deletion, member removal, or secret exposure).
- **Safe Message Previews**: Provides built-in `--dry-run` validation for outbound messages before posting to public or shared channels.
- **Automatic Entity Resolution**: Automatically translates human-readable identifiers (`#general`, `questions`, `@username`, or email addresses) into Slack internal IDs (`C049...`, `U09A...`).
- **Normalized & Machine-Readable Output**: Every script provides formatted terminal output for humans and a standardized `--json` flag for machine parsing.
- **Zero Third-Party Python Dependencies**: The Python scripts utilize only standard library modules (`subprocess`, `json`, `datetime`, `pathlib`, `argparse`).

### When to Use

- When an AI agent needs to inspect unread messages, mentions, or conversations.
- When querying channel history, reviewing message threads, or searching workspace context.
- When posting notifications, replying to threads, or adding emoji reactions safely.
- When performing maintenance tasks such as marking channels as read or retrieving user profile information.

---

## Workflow & Architecture

The following diagram illustrates how the `slack-cli` skill mediates interactions between AI agents or developers and Slack workspaces:

```mermaid
flowchart TD
    subgraph Caller["Caller Layer"]
        Agent[AI Agent / Assistant]
        Dev[Developer / CLI User]
    end

    subgraph ScriptSuite["Approved Script Suite (./scripts/)"]
        S1[get_unread.py]
        S2[list_channels.py]
        S3[read_channel.py]
        S4[read_thread.py]
        S5[search_messages.py]
        S6[send_message.py --dry-run]
        S7[react_message.py]
        S8[get_user_info.py]
        S9[edit_message.py]
        S10[mark_read.py]
    end

    subgraph CoreBridge["Execution & Safety Bridge"]
        Common[common.py]
        Common -->|Find binary in PATH or ~/.local/bin| BinCheck[Binary Verification]
        Common -->|Normalize args, capture stdout/stderr| SafeExec[Safe Subprocess Runner]
    end

    subgraph UnderlyingCLI["Underlying CLI Binary"]
        SlackCli["slackcli binary (by shaharia-lab)"]
    end

    subgraph SlackAPI["Slack Cloud Platform"]
        SlackWebAPI[Slack Web API / Workspaces]
    end

    Agent -->|Execute with python3| ScriptSuite
    Dev -->|Execute with python3| ScriptSuite
    ScriptSuite --> Common
    SafeExec --> SlackCli
    SlackCli -->|Authenticated HTTPS| SlackWebAPI
```

### Safety & Processing Flow

1. **Invocation**: The caller executes `python3 ./scripts/<script_name>.py [args] [--json]`.
2. **Resolution & Sanitization**: The script validates arguments (e.g. `--dry-run` checks on outbound messages, sanitizing user/channel identifiers).
3. **Subprocess Bridge (`common.py`)**: Resolves the `slackcli` executable location, constructs safe invocation arguments, captures output streams, and intercepts error codes.
4. **Data Normalization**: Timestamps (e.g., `1712345678.123456`) are converted to human-readable datetime formats (`YYYY-MM-DD HH:MM:SS`), and JSON payloads are cleanly serialized.

---

## Required Dependencies & Installation Links

This skill requires **Python 3** (standard library only) and the standalone **`slackcli` binary**.

| Tool | Minimum Version | Description | Installation Link |
| :--- | :--- | :--- | :--- |
| **Python 3** | `3.9+` | Runtime for approved helper scripts (uses standard library only) | [python.org/downloads](https://www.python.org/downloads/) |
| **SlackCLI (`slackcli`)** | `0.17+` | Fast CLI for Slack workspaces by `shaharia-lab` | [github.com/shaharia-lab/slackcli](https://github.com/shaharia-lab/slackcli) · [slackcli.dev](https://slackcli.dev/) |

### Command-Line Installation

#### 1. Install Python 3
- **macOS (via Homebrew)**:
  ```bash
  brew install python
  ```
- **Debian / Ubuntu Linux**:
  ```bash
  sudo apt-get update && sudo apt-get install -y python3
  ```

#### 2. Install SlackCLI (`slackcli`)
- **macOS & Linux (via Homebrew - Recommended)**:
  ```bash
  brew tap shaharia-lab/tap
  brew install slackcli
  ```
- **Linux (Direct Binary Download)**:
  ```bash
  # x86_64
  curl -L https://github.com/shaharia-lab/slackcli/releases/latest/download/slackcli-linux -o slackcli
  # or ARM64:
  # curl -L https://github.com/shaharia-lab/slackcli/releases/latest/download/slackcli-linux-arm64 -o slackcli

  chmod +x slackcli && mkdir -p ~/.local/bin && mv slackcli ~/.local/bin/
  ```
- **macOS (Direct Binary Download)**:
  ```bash
  # Apple Silicon (M1/M2/M3/M4)
  curl -L https://github.com/shaharia-lab/slackcli/releases/latest/download/slackcli-macos-arm64 -o slackcli
  # or Intel:
  # curl -L https://github.com/shaharia-lab/slackcli/releases/latest/download/slackcli-macos -o slackcli

  chmod +x slackcli && mkdir -p ~/.local/bin && mv slackcli ~/.local/bin/
  ```

Ensure `~/.local/bin` is in your `PATH`:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Initial Workspace Authentication

Before running the helper scripts, configure your workspace credentials in `slackcli`:

```bash
# Option A: Browser-based login (no Slack App creation required)
slackcli auth login-auto

# Option B: Manual browser token login
slackcli auth login-browser

# Option C: Slack Bot/User App Token (xoxb/xoxp)
slackcli auth login --token "xoxb-your-token"

# Verify active login
slackcli auth whoami
```

---

## Usage & Examples

All helper scripts reside in `./scripts/` and accept `--help` to inspect full options.

### Script Command Reference

#### 1. `get_unread.py` — Check Unread Messages & Mentions
```bash
# Human-readable summary table
python3 ./scripts/get_unread.py

# Machine-readable JSON
python3 ./scripts/get_unread.py --json
```

#### 2. `list_channels.py` — List Conversations
```bash
# List all channels
python3 ./scripts/list_channels.py

# Filter by channel name
python3 ./scripts/list_channels.py --filter "engineering"

# Limit to public channels only
python3 ./scripts/list_channels.py --types public --limit 25
```

#### 3. `read_channel.py` — Read Channel or DM Messages
```bash
# Read 10 most recent messages by channel name
python3 ./scripts/read_channel.py questions --limit 10

# Read by channel ID or with # prefix
python3 ./scripts/read_channel.py "#general" --limit 20

# Read top-level messages only (exclude thread replies)
python3 ./scripts/read_channel.py announcements --exclude-replies

# Programmatic JSON extraction
python3 ./scripts/read_channel.py dev --limit 5 --json
```

#### 4. `read_thread.py` — Read Message Thread History
```bash
# By channel name and parent message timestamp
python3 ./scripts/read_thread.py questions 1791446699.326619

# By Slack web permalink
python3 ./scripts/read_thread.py --permalink "https://workspace.slack.com/archives/C0123/p1791446699326619"
```

#### 5. `search_messages.py` — Search Workspace History
```bash
# Search text across all accessible channels
python3 ./scripts/search_messages.py "incident postmortem"

# Scope search to a specific channel
python3 ./scripts/search_messages.py "release" --in general

# Search messages from a specific person
python3 ./scripts/search_messages.py --from alice --limit 10
```

#### 6. `send_message.py` — Post Messages & Thread Replies
> [!TIP]
> Always run with `--dry-run` first to preview the target recipient and content safely.

```bash
# 1. Preview message (dry run)
python3 ./scripts/send_message.py \
  --recipient "#dev-chat" \
  --message "Automated build passed." \
  --dry-run

# 2. Send top-level message
python3 ./scripts/send_message.py \
  --recipient "#dev-chat" \
  --message "Automated build passed."

# 3. Post reply within an existing thread
python3 ./scripts/send_message.py \
  --recipient "#questions" \
  --thread-ts 1791446699.326619 \
  --message "Issue resolved in PR #104."
```

#### 7. `react_message.py` — Add or Remove Emoji Reactions
```bash
# Add a reaction (specify emoji name without colons)
python3 ./scripts/react_message.py \
  --channel questions \
  --timestamp 1791446699.326619 \
  --emoji rocket

# Remove an emoji reaction
python3 ./scripts/react_message.py \
  --channel questions \
  --timestamp 1791446699.326619 \
  --emoji rocket \
  --remove
```

#### 8. `get_user_info.py` — Inspect User Profiles
```bash
# Look up by Slack handle
python3 ./scripts/get_user_info.py @john.doe

# Look up by email address
python3 ./scripts/get_user_info.py john.doe@company.com
```

#### 9. `edit_message.py` — Update Sent Messages
```bash
python3 ./scripts/edit_message.py \
  --channel alerts \
  --timestamp 1791446699.326619 \
  --message "Updated: Deployment completed successfully."
```

#### 10. `mark_read.py` — Mark Channels as Read
```bash
# Mark all channels as read
python3 ./scripts/mark_read.py --all

# Mark a specific channel as read up to latest message
python3 ./scripts/mark_read.py general

# Mark a channel as read up to a specific timestamp
python3 ./scripts/mark_read.py general --ts 1791446699.326619
```

---

## File Structure

```text
slack-cli/
├── README.md                  # Comprehensive skill documentation (this file)
├── SKILL.md                   # Agent guidelines, operational policy, and usage rules
└── scripts/                   # Curated suite of approved Python helper scripts
    ├── common.py              # Shared subprocess execution, binary location, and timestamp utils
    ├── edit_message.py        # Edit an existing sent message
    ├── get_unread.py          # Check unread channels, DMs, and mentions
    ├── get_user_info.py       # Query user profile and status by handle/email/ID
    ├── list_channels.py       # Discover accessible public and private conversations
    ├── mark_read.py           # Mark channels or messages as read
    ├── react_message.py       # Add or remove emoji reactions
    ├── read_channel.py        # Fetch recent messages from a channel or DM
    ├── read_thread.py         # Inspect full chronological thread discussions
    ├── search_messages.py     # Search workspace messages using query parameters
    └── send_message.py        # Post messages or thread replies (with --dry-run support)
```

- **[SKILL.md](./SKILL.md)**: Details the strict "no raw CLI" policy, agent operational instructions, and command reference.
- **`scripts/common.py`**: Locates `slackcli` in `$PATH` or `~/.local/bin/slackcli`, executes commands safely via `subprocess.run`, and provides error-handling and JSON output serialization.
- **`scripts/*.py`**: Specialized command wrappers ensuring safe parameter validation and clean JSON output formatting.
