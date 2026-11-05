# Email Triage Action Policies & Execution Playbook

This document defines the execution rules, CLI command patterns, draft generation guidelines, safety invariants, and label conventions for the Email Triage system.

---

## 1. Safety Core Invariants

All automated and sub-agent triage operations must strictly adhere to the following four non-negotiable safety rules:

1. **NO AUTO-SEND**:  
   Under no circumstances may an automated script or agent send an email directly (`gog gmail send` or sending a draft). The system only creates **Drafts** (`draft_reply.py`). The human user remains the sole sender of outbound communication.

2. **SAFE DELETION VIA TRASH**:  
   Unsolicited marketing, spam, and cold outreach are marked as read and moved to Gmail **Trash** (`--trash`, which attaches the system `TRASH` label). They are **never permanently deleted** (`--delete`) unless the user explicitly requests a permanent purge with `--force`. Gmail Trash provides a 30-day safety net to recover any false-positive classifications.

3. **DRY-RUN SUPPORT**:  
   Every state-altering script (`apply_triage.py`, `draft_reply.py`) must support the `--dry-run` flag. In dry-run mode, the script computes and prints planned actions without executing any API calls or altering mailbox state.

4. **EXPLICIT ACCOUNT RESOLUTION**:  
   All CLI operations resolve and pass the targeted account explicitly via `-a <account>` or `--account <account>`. Supported accounts:
   - `work_account` (e.g. corporate email address) — default corporate account
   - `personal_account` (e.g. personal email address) — personal account
   - Environment variable fallback: `GOG_ACCOUNT`

---

## 2. Category Action Playbook

| Category | Primary Action | Gmail State Mutation | Label Updates | CLI Helper Command |
|:---|:---|:---|:---|:---|
| **`SPAM`** | Move to Trash | Mark Read (`-UNREAD`), Remove Inbox (`-INBOX`), Add Trash (`+TRASH`) | System `TRASH` | `python3 email-triage/scripts/apply_triage.py <thread_id> --mark-read --trash -a <account>` |
| **`REGULAR`** | Archive | Mark Read (`-UNREAD`), Remove Inbox (`-INBOX`) | Optional: `Triage/FYI` | `python3 email-triage/scripts/apply_triage.py <thread_id> --mark-read --archive -a <account>` |
| **`NEEDS_ATTENTION`** | Draft Reply & Flag | Mark Read (`-UNREAD`), Keep in or Archive from Inbox per user preference | `Triage/Needs-Reply` | `python3 email-triage/scripts/draft_reply.py <message_id> --body "..." -a <account>`<br>`python3 email-triage/scripts/apply_triage.py <thread_id> --mark-read --add-label "Triage/Needs-Reply" -a <account>` |

---

## 3. Detailed Execution Procedures

### 3.1 SPAM Triage Workflow
When an email is classified as `SPAM`:
1. Mark thread as read and move to Gmail Trash.
2. CLI Command:
   ```bash
   python3 email-triage/scripts/apply_triage.py <thread_id> --mark-read --trash -a <account>
   ```
3. Report output:
   - Summarize the spam pitch in one brief sentence.
   - Note action: "Marked read and moved to Trash (recoverable for 30 days)."
   - Proposed next user action: "None (review Trash if false-positive suspected)."

### 3.2 REGULAR Triage Workflow
When an email is classified as `REGULAR`:
1. Mark thread as read and archive from inbox (removes from active view while retaining in "All Mail" for search).
2. Optional label: `Triage/FYI` (if configured).
3. CLI Command:
   ```bash
   python3 email-triage/scripts/apply_triage.py <thread_id> --mark-read --archive -a <account>
   ```
4. Report output:
   - Summarize the notification/content in one sentence.
   - Note action: "Marked read and archived."
   - Proposed next user action: "None (searchable in All Mail)."

### 3.3 NEEDS_ATTENTION Triage Workflow
When an email is classified as `NEEDS_ATTENTION`:
1. Extract the latest incoming message ID from the thread.
2. Formulate a polite, factual, context-aware draft reply (see Section 4).
3. Generate the draft reply in Gmail:
   ```bash
   python3 email-triage/scripts/draft_reply.py <message_id> --body "<draft_text>" -a <account>
   ```
4. Update thread status and apply label:
   ```bash
   python3 email-triage/scripts/apply_triage.py <thread_id> --mark-read --add-label "Triage/Needs-Reply" -a <account>
   ```
5. Report output:
   - Summarize the incoming request clearly.
   - Note action: "Created draft reply and applied label `Triage/Needs-Reply`."
   - Proposed next user action: "Review and send draft reply in Gmail: Draft `<draft_id>`."

---

## 4. Draft Reply Generation Principles

When drafting replies for `NEEDS_ATTENTION` emails, sub-agents must strictly follow these authoring rules:

### A. Strict Factuality & Zero Hallucination
- **Do not invent commitments**: Never commit the user to specific deadlines, dates, prices, technical solutions, or decisions unless explicitly stated in the context or prompt.
- **Use Clear Placeholders**: If critical information is required from the user, insert high-visibility bracketed placeholders:
  - `[Insert your available time slots, e.g. Thursday 2-4 PM]`
  - `[Confirm whether we should proceed with Option A or Option B]`
  - `[Attach the requested scorecard or report]`
- **Acknowledge and Frame**: Draft an acknowledgment confirming receipt and outlining the next step:
  > *"Hi Sarah, thanks for following up on the Titan API release. I am reviewing the regression test results and will share the confirmed timeline shortly. [Insert preferred release window]. Best regards, Mikhail"*

### B. Tone and Professionalism
- **Brevity & Clarity**: Keep drafts under 3-5 sentences whenever possible. Busy recipients appreciate concise communication.
- **Match Formality**: Match the tone of the sender:
  - *Internal colleague*: Friendly, direct, collaborative ("Hi Sarah, thanks for the update...").
  - *External client / executive*: Professional, courteous, precise ("Dear David, thank you for alerting us to this issue...").
- **Avoid Clichés**: Do NOT use filler phrases like:
  - "I hope this email finds you well"
  - "Per my previous email"
  - "Please let me know if you have any questions or concerns" (unless relevant)

### C. Thread Context Preservation
- Replies must preserve thread threading headers (`In-Reply-To` and `References`) via `gog gmail drafts create --reply-to-message-id=<msg_id>`.
- Use `--reply-all` only when the incoming email included multiple direct stakeholders on `To:` or `Cc:` that require visibility.

---

## 5. Label Taxonomy & Hierarchy

The system utilizes standard Gmail labels and a scoped `Triage/` hierarchy:

| Label Name | Type | Purpose | Applied When |
|:---|:---:|:---|:---|
| `INBOX` | System | Active inbox view | Default for incoming unread emails; removed on Archive/Trash |
| `UNREAD` | System | Read/unread indicator | Removed on all processed emails (`--mark-read`) |
| `TRASH` | System | 30-day auto-purge bin | Added for `SPAM` |
| `Triage/Needs-Reply` | Custom | Active pending user draft review | Added when a draft reply has been generated |
| `Triage/Waiting` | Custom | Awaiting external response | Added when waiting on another party's action |
| `Triage/FYI` | Custom | Archived informational threads | Added when preserving reference context |

---

## 6. Sub-Agent Output Template

Every thread sub-agent invoked by the orchestrator must return its findings in this exact structured format:

```markdown
### Thread: <Subject Line>
- **ID**: `<thread_id>`
- **From**: `<Sender Name> <sender@example.com>`
- **Category**: `SPAM` | `REGULAR` | `NEEDS_ATTENTION`
- **Summary**: <1-2 sentences summarizing the message content>
- **Action Taken**: <e.g. Marked read and moved to Trash | Marked read and archived | Created draft reply #draft_id and labeled 'Triage/Needs-Reply'>
- **Draft Preview**: <Only if category is NEEDS_ATTENTION: 2-3 lines showing the proposed draft>
- **Next Action for User**: <e.g. None | Review and send draft in Gmail | Submit scorecard by 5 PM>
```

This standardized schema allows the Orchestrator to parse and synthesize a single unified Triage Digest Table for the user at the end of the run.
