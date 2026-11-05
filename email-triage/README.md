# Email Triage Skill (`email-triage`)

An autonomous, multi-account email triage framework designed for Google Workspace users and AI agents. It wraps the `gog` CLI with clean Python automation scripts to discover unread threads across multiple Google accounts, safely categorize them, draft replies, and apply triage labels without accidental emails or data loss.

---

## Key Features

- **Multi-Account Discovery**: Dynamically queries Google accounts and aliases via `gog auth`. The primary/default account is always processed first, followed by secondary accounts.
- **Strict Safety Policies**:
  - **No Accidental Sending**: Scripts create Gmail **drafts** only; no emails are automatically sent.
  - **Safe Deletion**: Low-value/spam emails are moved to **Gmail Trash** (`--trash`). Permanent deletion (`--delete`) requires explicit confirmation (`--force`).
  - **Dry-Run Mode**: Every mutating script provides `--dry-run` to inspect planned changes without touching mailbox state.
- **Clean Text Normalization**: Decodes multipart and URL-safe base64 payloads, converts HTML to readable Markdown, removes tracking pixels (1x1 web bugs), and trims corporate legal disclaimers.
- **Multi-Agent Architecture**: Designed for an Orchestrator Agent to delegate individual threads to isolated Sub-Agents, preventing context pollution and hallucination.

---

## Directory Structure

```
email-triage/
├── SKILL.md                          # Agent instruction file & orchestrator protocol
├── README.md                         # Human-readable documentation & guide
├── references/
│   ├── classification_rules.md      # Rules for SPAM, REGULAR, and NEEDS_ATTENTION
│   └── actions_policy.md            # Action decision matrix & safety rules
├── scripts/
│   ├── common.py                    # Shared gog execution, account resolver, HTML cleaner
│   ├── scan_inbox.py                # Multi-account inbox scanner
│   ├── read_email.py                # Thread parser, body decoder, attachment extractor
│   ├── apply_triage.py              # Labeling, read status, archiving, trashing
│   ├── draft_reply.py               # Safe draft reply creator
│   └── manage_labels.py             # Label inspection & setup
└── tests/
    ├── test_common.py               # Unit tests for common utilities & account resolver
    └── test_scripts.py              # Unit tests for all operational scripts
```

---

## Prerequisites

1. **Python 3.9+**
2. **`gog` CLI**: Ensure `gog` is installed and authorized with Google accounts:
   ```bash
   brew install gogcli
   gog auth login
   ```
   To verify authorized accounts:
   ```bash
   gog auth list
   ```

---

## Quick Start & CLI Usage

### 1. Set Up Standard Triage Labels
Ensure your mailbox has the necessary triage labels (`Triage/Action-Needed`, `Triage/Waiting`, `Triage/FYI`):
```bash
# Preview label setup
python3 email-triage/scripts/manage_labels.py --setup --dry-run

# Create labels
python3 email-triage/scripts/manage_labels.py --setup

# List existing labels
python3 email-triage/scripts/manage_labels.py --list
```

### 2. Scan Inboxes
Scan for unread threads across all configured accounts (default account listed first):
```bash
python3 email-triage/scripts/scan_inbox.py
```

Scan a specific account or use a custom query:
```bash
# Specific account alias
python3 email-triage/scripts/scan_inbox.py -a work_account -m 15

# Custom query with JSON output
python3 email-triage/scripts/scan_inbox.py -q "is:unread label:important" -j
```

### 3. Read & Inspect a Thread
Fetch and clean an email thread:
```bash
# Human-readable summary
python3 email-triage/scripts/read_email.py <thread_id>

# Structured JSON format
python3 email-triage/scripts/read_email.py <thread_id> --json
```

### 4. Apply Triage Actions
Safely modify email state:

```bash
# Preview action (dry-run)
python3 email-triage/scripts/apply_triage.py <thread_id> --mark-read --archive --dry-run

# Mark as read and archive
python3 email-triage/scripts/apply_triage.py <thread_id> --mark-read --archive

# Move spam/unwanted emails to Trash (safe deletion)
python3 email-triage/scripts/apply_triage.py <thread_id> --trash

# Add custom triage label
python3 email-triage/scripts/apply_triage.py <thread_id> --add-label "Triage/Action-Needed"
```

### 5. Create a Draft Reply
Draft a response to a thread without sending:
```bash
# Preview draft creation
python3 email-triage/scripts/draft_reply.py <message_id> --body "Hi, I will review this by noon." --dry-run

# Create draft reply in Gmail
python3 email-triage/scripts/draft_reply.py <message_id> --body "Hi, I will review this by noon."

# Reply all using a body file
python3 email-triage/scripts/draft_reply.py <message_id> --body-file ./reply.txt --reply-all
```

---

## Running Tests

Run the complete test suite:
```bash
python3 -m unittest discover -v -s email-triage/tests
```

All 66 tests verify:
- Account discovery and alias resolution
- HTML and text cleaning with tracking pixel elimination
- CLI argument parsing and error handling
- Subprocess safety and payload transformations
- Triage mutation logic, dry-run guarantees, and label idempotency
