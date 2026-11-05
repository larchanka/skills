# Todo List: Email Triage Skill Implementation

## Phase 1: Foundation (Policies & Common Utilities)
- [x] Task 1: Create Classification Rules and Action Policy References
  - [x] Create `email-triage/references/classification_rules.md`
  - [x] Create `email-triage/references/actions_policy.md`
  - [x] Verify reference documents contain explicit criteria for SPAM, REGULAR, and NEEDS_ATTENTION
- [x] Task 2: Implement Common CLI Runner & Text Utilities
  - [x] Create `email-triage/scripts/common.py` (run_gog, clean_email_body, account resolution)
  - [x] Create `email-triage/tests/test_common.py`
  - [x] Verify all tests pass with `python3 -m unittest email-triage/tests/test_common.py`

### Checkpoint: Foundation
- [x] Unit tests in `test_common.py` pass cleanly
- [x] Account resolution and `gog` CLI execution verified

---

## Phase 2: Email Inspection & Reading Utilities
- [x] Task 3: Implement Inbox Scanning Script (`scan_inbox.py`)
  - [x] Create `email-triage/scripts/scan_inbox.py`
  - [x] Add unit tests in `email-triage/tests/test_scripts.py` for scan_inbox
  - [x] Verify test discovery passes and live scan test runs
- [x] Task 4: Implement Email & Thread Reader Script (`read_email.py`)
  - [x] Create `email-triage/scripts/read_email.py`
  - [x] Add unit tests in `email-triage/tests/test_scripts.py` for read_email
  - [x] Verify clean body extraction and message header parsing

### Checkpoint: Read Pipeline
- [x] Read pipeline unit tests pass
- [x] Clean text extraction verified without HTML noise

---

## Phase 3: Triage Actions & Reply Drafting
- [x] Task 5: Implement Triage State Modification Script (`apply_triage.py`)
  - [x] Create `email-triage/scripts/apply_triage.py` (mark-read, archive, trash, delete, labels, dry-run)
  - [x] Add unit tests in `email-triage/tests/test_scripts.py` for apply_triage
  - [x] Verify `--dry-run` and action behavior
- [x] Task 6: Implement Reply Drafting & Label Management Scripts (`draft_reply.py`, `manage_labels.py`)
  - [x] Create `email-triage/scripts/draft_reply.py` (draft create reply)
  - [x] Create `email-triage/scripts/manage_labels.py` (ensure triage labels exist)
  - [x] Add unit tests in `email-triage/tests/test_scripts.py`
  - [x] Verify draft reply dry-run and creation logic

### Checkpoint: Mutation & Actions
- [x] All mutation scripts (`apply_triage.py`, `draft_reply.py`, `manage_labels.py`) pass unit tests
- [x] Dry-run mode functions properly for all operations

---

## Phase 4: Skill Definition, Orchestrator Protocol & E2E Validation
- [x] Task 7: Author Skill Definition & Documentation (`SKILL.md` & `README.md`)
  - [x] Create `email-triage/SKILL.md` with multi-agent orchestration instructions
  - [x] Create `email-triage/README.md` with usage documentation
  - [x] Verify YAML frontmatter and tool invocation instructions
- [x] Task 8: End-to-End Verification & Sanity Checks
  - [x] Run full test suite: `python3 -m unittest discover -s email-triage/tests`
  - [x] Test dry-run triage workflows end-to-end
  - [x] Confirm adherence to Definition of Done

### Checkpoint: Complete
- [x] All 8 tasks completed and verified
- [x] Ready for review and merge
