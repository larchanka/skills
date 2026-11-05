# Implementation Plan: Email Triage Skill (`email-triage`)

## Overview
Build an **Email Triage** skill inside `email-triage/` using a **Multi-Agent Orchestration Architecture** powered by dedicated Python helper scripts wrapping the `gog gmail` CLI. An Orchestrator Agent scans inbox threads and invokes a dedicated sub-agent for each thread. Each thread sub-agent cleanses and reads the thread, classifies it against documented rules (`references/classification_rules.md`), executes appropriate triage actions (`apply_triage.py`, `draft_reply.py`), and returns a structured summary to the Orchestrator, who delivers a consolidated digest to the user.

## Architecture Decisions & Rationale
1. **Multi-Agent Sub-agent per Thread Isolation**:
   - *Decision*: The Orchestrator delegates each thread to a dedicated sub-agent using `invoke_subagent(Role: 'Thread Triage Agent', ...)`.
   - *Rationale*: Keeps context windows minimal, prevents cross-thread contamination, enables isolated reasoning for classification and drafting, and allows clean parallel or batch triage without context bloat.
2. **Python Wrapper Scripts over Direct CLI Invocation**:
   - *Decision*: All email operations run through standalone, tested CLI helper scripts (`common.py`, `scan_inbox.py`, `read_email.py`, `apply_triage.py`, `draft_reply.py`, `manage_labels.py`).
   - *Rationale*: Enforces consistent account switching (`sytac` vs `personal`), isolates JSON parsing/formatting, strips HTML noise before LLM inspection, and protects against destructive command misuse.
3. **Safe Deletion Policy (Trash vs Hard Delete)**:
   - *Decision*: Spam / Unsolicited email triage moves emails to Gmail Trash (`--trash` via adding label `TRASH`) by default rather than hard deleting. Permanent deletion (`--delete`) requires `--force`.
   - *Rationale*: Gmail auto-cleans Trash after 30 days while providing a critical safety net against false-positive spam classifications.
4. **Draft Reply Instead of Auto-Sending**:
   - *Decision*: High-priority emails requiring response have drafts generated via `gog gmail drafts create --reply-to-message-id=<msgId>`. Messages are never automatically sent.
   - *Rationale*: Human-in-the-loop safety for all outbound communication; user reviews and sends when ready.
5. **Dry-Run Support Across All Mutating Scripts**:
   - *Decision*: `apply_triage.py` and `draft_reply.py` provide a `--dry-run` flag matching `gog` CLI's `-n, --dry-run`.
   - *Rationale*: Allows sub-agents and developers to simulate triage runs safely before committing mailbox state changes.

## Dependency Graph
```
email-triage/references/ (classification_rules.md, actions_policy.md)
    │
email-triage/scripts/common.py & tests/test_common.py
    │
    ├── email-triage/scripts/scan_inbox.py & tests/test_scripts.py
    ├── email-triage/scripts/read_email.py & tests/test_scripts.py
    │
    ├── email-triage/scripts/apply_triage.py & tests/test_scripts.py
    └── email-triage/scripts/draft_reply.py & manage_labels.py & tests/test_scripts.py
            │
    email-triage/SKILL.md & README.md (Multi-agent orchestration protocol)
            │
    End-to-End Verification with gog accounts (sytac / personal)
```

---

## Detailed Task Breakdown

### Phase 1: Foundation (Policies & Common Utilities)

#### Task 1: Create Classification Rules and Action Policy References
**Description:** Define explicit, human- and agent-readable rules for email categorization (Spam, Regular, Needs Attention) and the standard action playbook for automated and proposed next actions.
**Acceptance criteria:**
- [ ] `email-triage/references/classification_rules.md` details criteria, signals, and edge cases for SPAM, REGULAR, and NEEDS_ATTENTION.
- [ ] `email-triage/references/actions_policy.md` details exact CLI actions, draft reply principles (tone, safety, facts), and user next steps.
**Verification:**
- [ ] Verify files exist and contain complete criteria for all three categories.
**Dependencies:** None
**Files likely touched:**
- `email-triage/references/classification_rules.md`
- `email-triage/references/actions_policy.md`
**Estimated scope:** Small (2 files)

#### Task 2: Implement Common CLI Runner & Text Utilities
**Description:** Build `email-triage/scripts/common.py` providing account resolution (`sytac` vs `personal`), binary discovery (`gog`), robust subprocess execution with JSON parsing, and HTML/text sanitation for email bodies.
**Acceptance criteria:**
- [ ] `run_gog()` correctly passes `-a <account>` and `-j`, catches errors, and parses JSON output.
- [ ] `clean_email_body()` converts HTML/plain text into clean markdown/text by stripping tracking pixels, excessive disclaimers, and styles.
- [ ] Account resolution defaults to `sytac` (mikhail.larchanka@sytac.io) and supports `personal` (horrorgr@gmail.com) and environment variable `GOG_ACCOUNT`.
- [ ] Unit tests in `email-triage/tests/test_common.py` achieve 100% test pass rate using `python3 -m unittest`.
**Verification:**
- [ ] `python3 -m unittest email-triage/tests/test_common.py`
**Dependencies:** Task 1
**Files likely touched:**
- `email-triage/scripts/common.py`
- `email-triage/tests/test_common.py`
**Estimated scope:** Small (2 files)

### Checkpoint: Foundation
- [ ] All unit tests in `email-triage/tests/test_common.py` pass.
- [ ] Account resolution and `gog` CLI execution wrappers operate reliably.

---

### Phase 2: Email Inspection & Reading Utilities

#### Task 3: Implement Inbox Scanning Script (`scan_inbox.py`)
**Description:** Build `email-triage/scripts/scan_inbox.py` to query unread threads in Gmail inbox using `gog gmail search`, returning sanitized thread metadata (ID, date, sender, subject, snippet).
**Acceptance criteria:**
- [ ] Accepts `--query` (default `'is:unread in:inbox'`), `--max` (default 10), `--account`, and `--json`.
- [ ] Returns a structured JSON array or tabular output of thread headers and snippets.
- [ ] Handles empty search results gracefully (exit code 0 with empty list).
- [ ] Unit tests added in `email-triage/tests/test_scripts.py`.
**Verification:**
- [ ] `python3 -m unittest discover -s email-triage/tests`
- [ ] `python3 email-triage/scripts/scan_inbox.py --max 2 -a sytac --json`
**Dependencies:** Task 2
**Files likely touched:**
- `email-triage/scripts/scan_inbox.py`
- `email-triage/tests/test_scripts.py`
**Estimated scope:** Small (2 files)

#### Task 4: Implement Email & Thread Reader Script (`read_email.py`)
**Description:** Build `email-triage/scripts/read_email.py` to fetch full thread details via `gog gmail thread get <id> --full --json`, clean each message's body text, extract headers, and format for sub-agent consumption.
**Acceptance criteria:**
- [ ] Accepts `<thread_id>`, `--account`, and `--json`.
- [ ] Extracts message sequence, sender, recipient, date, subject, attachment names, and clean body text.
- [ ] Handles multi-part messages and plain text vs HTML bodies.
- [ ] Unit tests added in `email-triage/tests/test_scripts.py`.
**Verification:**
- [ ] `python3 -m unittest discover -s email-triage/tests`
- [ ] Dry-run or mock execution tests pass.
**Dependencies:** Task 3
**Files likely touched:**
- `email-triage/scripts/read_email.py`
- `email-triage/tests/test_scripts.py`
**Estimated scope:** Small (2 files)

### Checkpoint: Read Pipeline
- [ ] All unit tests for `scan_inbox.py` and `read_email.py` pass.
- [ ] Read pipeline produces sanitized markdown/JSON thread content without leaking raw HTML artifacts.

---

### Phase 3: Triage Actions & Reply Drafting

#### Task 5: Implement Triage State Modification Script (`apply_triage.py`)
**Description:** Build `email-triage/scripts/apply_triage.py` to modify thread labels and status: marking read, archiving (removing `INBOX`), trashing (adding `TRASH`), permanently deleting (with `--force`), and adding/removing custom triage labels.
**Acceptance criteria:**
- [ ] Supports `--mark-read`, `--archive`, `--trash`, `--delete` (requires `--force`), `--add-label`, `--remove-label`.
- [ ] Supports `--dry-run` to output intended label mutations without modifying Gmail state.
- [ ] Supports `--account`.
- [ ] Unit tests added in `email-triage/tests/test_scripts.py` covering all flags and `--dry-run`.
**Verification:**
- [ ] `python3 -m unittest discover -s email-triage/tests`
- [ ] `python3 email-triage/scripts/apply_triage.py dummy_thread --mark-read --archive --dry-run -a sytac`
**Dependencies:** Task 2
**Files likely touched:**
- `email-triage/scripts/apply_triage.py`
- `email-triage/tests/test_scripts.py`
**Estimated scope:** Small (2 files)

#### Task 6: Implement Reply Drafting & Label Management Scripts (`draft_reply.py`, `manage_labels.py`)
**Description:** Build `email-triage/scripts/draft_reply.py` to draft context-aware replies via `gog gmail drafts create --reply-to-message-id=<msgId>`, and `manage_labels.py` to inspect or create standard triage labels (`Triage/Needs-Reply`, `Triage/Waiting`, `Triage/FYI`).
**Acceptance criteria:**
- [ ] `draft_reply.py` creates a draft reply linked to a message with `--body` or `--body-file`, `--reply-all`, and `--dry-run`.
- [ ] `draft_reply.py` automatically extracts In-Reply-To recipient and subject from message metadata if not provided.
- [ ] `manage_labels.py` lists labels and ensures triage labels exist.
- [ ] Unit tests added in `email-triage/tests/test_scripts.py`.
**Verification:**
- [ ] `python3 -m unittest discover -s email-triage/tests`
- [ ] `python3 email-triage/scripts/draft_reply.py dummy_msg --to "test@example.com" --subject "Re: Test" --body "Draft content" --dry-run -a sytac`
**Dependencies:** Task 4, Task 5
**Files likely touched:**
- `email-triage/scripts/draft_reply.py`
- `email-triage/scripts/manage_labels.py`
- `email-triage/tests/test_scripts.py`
**Estimated scope:** Medium (3 files)

### Checkpoint: Mutation & Actions
- [ ] All action scripts (`apply_triage.py`, `draft_reply.py`, `manage_labels.py`) pass unit tests.
- [ ] Dry-run mode functions properly for all mutating operations.

---

### Phase 4: Skill Definition, Orchestrator Protocol & E2E Validation

#### Task 7: Author Skill Definition & Documentation (`SKILL.md` & `README.md`)
**Description:** Create `email-triage/SKILL.md` and `email-triage/README.md` defining the Multi-Agent Orchestrator protocol, sub-agent invocation prompt, required parameters, and usage examples.
**Acceptance criteria:**
- [ ] `SKILL.md` contains valid YAML frontmatter (`name: email-triage`, `description: ...`).
- [ ] `SKILL.md` documents step-by-step Orchestrator workflow: scanning inbox, invoking sub-agents with `Role: 'Thread Triage Agent'`, collecting structured results, and rendering the final report.
- [ ] `SKILL.md` specifies the Sub-Agent workflow: reading thread, consulting classification rules, applying action, creating draft if needed, and returning the structured template.
- [ ] `README.md` provides installation, CLI usage, account selection (`sytac` vs `personal`), and script references.
**Verification:**
- [ ] Validate skill syntax and frontmatter.
**Dependencies:** Tasks 1-6
**Files likely touched:**
- `email-triage/SKILL.md`
- `email-triage/README.md`
**Estimated scope:** Small (2 files)

#### Task 8: End-to-End Verification & Sanity Checks
**Description:** Execute full test suite and run live read-only / dry-run commands with `gog` CLI across accounts (`sytac` and `personal`).
**Acceptance criteria:**
- [ ] `python3 -m unittest discover -s email-triage/tests` passes 100%.
- [ ] Live inbox scan succeeds for default account (`sytac`).
- [ ] Dry-run triage actions and draft creations execute without runtime errors.
- [ ] Meets all items on the standing Definition of Done.
**Verification:**
- [ ] Run test suite command and verify exit code 0.
- [ ] Verify clean git status and formatting.
**Dependencies:** Tasks 1-7
**Files likely touched:**
- `email-triage/tests/*`
**Estimated scope:** Small (1-2 files)

### Checkpoint: Complete
- [x] All acceptance criteria met across all 8 tasks.
- [x] Full test suite passes without errors.
- [x] Ready for review and publication.

---

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| False positive spam deletion | High | Move to Gmail Trash (`--trash`) by default rather than permanent delete; preserves 30-day recovery. |
| Inadvertent email dispatch | High | Only create Gmail Drafts (`drafts create`); never execute `drafts send` or `send`. |
| Excessive context window consumption in Orchestrator | Medium | Delegate each thread to an isolated sub-agent; sub-agents return concise 5-line structured reports. |
| Malformed or heavily nested HTML emails | Medium | Robust HTML cleaning in `common.py` using `html.parser` / regex to strip scripts, styles, and tags, extracting only plain content. |
| Multi-account mismatch | Medium | Pass explicit `-a <account>` to all script calls with clear fallback to `sytac` default. |

## Open Questions
- None. Account specifications (`sytac` default, `personal` alternative) and triage actions (trash for spam, archive for regular, draft for needs attention) have been confirmed.
