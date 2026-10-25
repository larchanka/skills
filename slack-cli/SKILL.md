---
name: slack-cli
description: >-
  Interact with Slack workspaces safely via dedicated Python helper scripts.
  Allows reading unread messages, channels, threads, searching messages, sending
  messages, and reacting with emojis without direct CLI execution.
---

# Slack CLI Helper Skill

This skill enables the agent to safely interact with Slack workspaces using a curated suite of Python scripts.

> [!IMPORTANT]
> **Strict Tool Policy: No Direct Raw CLI Fallback**
> Do **NOT** invoke the raw `slackcli` executable directly.
> You must **ONLY** use the approved Python scripts located in:
> `./scripts/`
>
> This ensures safe operations, eliminates accidental destructive actions (e.g. channel deletion or token exposure), and provides normalized output.

---

## Script Suite & Usage Reference

All scripts reside in `./scripts/`. Run them using `python3 <script-path> [options]`.

### 1. `get_unread.py` - Check Unread Messages
Quickly scan for channels, DMs, or threads with unread messages or mentions.

```bash
# Human-readable summary table
python3 ./scripts/get_unread.py

# Machine-readable JSON output
python3 ./scripts/get_unread.py --json
```

---

### 2. `list_channels.py` - Discover Channels and DMs
List public/private channels and conversations you have access to.

```bash
# List all channels
python3 ./scripts/list_channels.py

# Filter channels by name
python3 ./scripts/list_channels.py --filter "general"

# Filter by type and limit results
python3 ./scripts/list_channels.py --types public,private --limit 20
```

---

### 3. `read_channel.py` - Read Recent Channel or DM Messages
Fetch recent messages from any channel, private group, or direct message conversation. Automatically formats timestamps and resolves user IDs to human-readable names and handles.

```bash
# Read recent messages from a channel by name
python3 ./scripts/read_channel.py questions --limit 10

# Read by channel ID or #channel
python3 ./scripts/read_channel.py "#questions" --limit 20

# Read only top-level channel messages (exclude threaded replies)
python3 ./scripts/read_channel.py questions --exclude-replies

# Programmatic JSON extraction
python3 ./scripts/read_channel.py questions --limit 10 --json
```

---

### 4. `read_thread.py` - Read Message Thread Replies
Inspect an entire conversation thread, displaying the parent message and all subsequent replies chronologically.

```bash
# By channel and thread parent timestamp
python3 ./scripts/read_thread.py questions 1791446699.326619

# By Slack permalink URL
python3 ./scripts/read_thread.py --permalink "https://workspace.slack.com/archives/C0123/p1791446699326619"
```

---

### 5. `search_messages.py` - Search Workspace History
Search across messages you have access to using keywords or Slack query operators (`after:YYYY-MM-DD`, `has:link`, etc.).

```bash
# Search query across conversations
python3 ./scripts/search_messages.py "Thinkpad"

# Search in a specific channel
python3 ./scripts/search_messages.py "deploy" --in general

# Search from a specific user
python3 ./scripts/search_messages.py --from alice --limit 10
```

---

### 6. `send_message.py` - Post Messages & Thread Replies
Send a message to a channel, DM, or thread.

> [!TIP]
> Always use `--dry-run` to preview and validate the message target before posting to a shared or public channel.

```bash
# Preview / Dry run (does not send anything)
python3 ./scripts/send_message.py \
  --recipient "#questions" \
  --message "Hello team" \
  --dry-run

# Post to a channel or user
python3 ./scripts/send_message.py \
  --recipient "#general" \
  --message "Deployment completed."

# Post reply in an existing thread
python3 ./scripts/send_message.py \
  --recipient "#questions" \
  --thread-ts 1791446699.326619 \
  --message "I found the charger!"
```

---

### 7. `react_message.py` - Add or Remove Emoji Reactions
React to any Slack message using emoji names (without colons).

```bash
# Add a reaction
python3 ./scripts/react_message.py \
  --channel questions \
  --timestamp 1791446699.326619 \
  --emoji thumbsup

# Remove a reaction
python3 ./scripts/react_message.py \
  --channel questions \
  --timestamp 1791446699.326619 \
  --emoji thumbsup \
  --remove
```

---

### 8. `get_user_info.py` - Look Up User Profiles
Retrieve user profile details, email, timezone, and account status.

```bash
python3 ./scripts/get_user_info.py @username
python3 ./scripts/get_user_info.py user@example.com
```

---

### 9. `edit_message.py` - Edit Existing Messages
Replace the text of an existing message you posted.

```bash
python3 ./scripts/edit_message.py \
  --channel questions \
  --timestamp 1791446699.326619 \
  --message "Updated message text"
```

---

### 10. `mark_read.py` - Mark Channels as Read
Mark a specific channel or all unread channels as read.

```bash
# Mark all unread channels as read
python3 ./scripts/mark_read.py --all

# Mark a specific channel as read up to latest message
python3 ./scripts/mark_read.py questions

# Mark up to a specific timestamp
python3 ./scripts/mark_read.py questions --ts 1791446699.326619
```

---

## Agent Operational Guidelines

1. **Verify Before Sending**: If instructed to post a message or announcement, run `--dry-run` first or ask the user to confirm the text and target channel.
2. **Name Resolution**: The scripts automatically accept human-friendly names (e.g. `questions`, `#questions`, `@username`, or email addresses) as well as Slack IDs (`C049...`, `U09A...`).
3. **Structured Data**: When you need to parse results to make follow-up decisions, append `--json` to any script.


