# Email Classification Rules & Heuristics

This document defines the classification criteria, indicators, heuristics, edge cases, and fallback rules used by Email Triage sub-agents to categorize incoming emails.

---

## 1. Classification Overview & Decision Hierarchy

Incoming emails are evaluated against three distinct categories:
1. **`SPAM`**: Unsolicited commercial outreach, bulk marketing, recruitment blasts, scams, or phishing attempts.
2. **`REGULAR`**: Informational updates, automated system alerts, subscribed newsletters, transactional receipts, and FYI notifications where no reply or user intervention is required.
3. **`NEEDS_ATTENTION`**: Direct human communications, action items, approvals, interview scorecards, questions directed to the user, and deadline-sensitive requests.

### Evaluation Precedence
To prevent data loss and ensure user safety, evaluate each email in the following strict order:

```
[Incoming Email]
       │
       ▼
1. Security & Phishing Check ─────────────► [Is malicious/phishing?] ──► SPAM (Trash)
       │ No
       ▼
2. Actionability Check ───────────────────► [Requires user reply/action?] ──► NEEDS_ATTENTION (Draft Reply)
       │ No
       ▼
3. Regular & Informational Check ─────────► [Known sender / subscribed / automated?] ──► REGULAR (Archive)
       │ No
       ▼
4. Cold Outreach & Marketing Check ───────► [Unsolicited pitch / mass blast?] ──► SPAM (Trash)
       │ Unclear
       ▼
5. Ambiguity Fallback: Prefer safer category (NEEDS_ATTENTION > REGULAR > SPAM)
```

---

## 2. Category 1: `SPAM`

### Scope & Definition
Unsolicited, mass, or deceptive communications that clutter the user's inbox, including:
- Cold B2B sales pitches (e.g. software development services, SEO audits, SaaS platforms).
- Cold recruiter blasts sent without specific regard to the user's current role or profile.
- Unsolicited commercial marketing and promotional newsletters without opt-in.
- Fraud, credential phishing, fake invoices, scam lures, and domain-spoofed attacks.

### Positive Detection Indicators
- **Generic Salutations & Form Letters**:
  - "Dear Founder", "Hi there", "Quick question for you", "Saw your profile on LinkedIn and was impressed", "Following up on my last 3 emails".
- **Cold Sales Patterns**:
  - Offers of offshore development, outsourced SDRs, lead generation, link building, AI automation consulting.
  - "Do you have 15 minutes this Thursday for a quick chat?", "Are you the right person to speak to regarding...".
- **Sender & Domain Signals**:
  - Mass-mail platforms or cold outreach automation tools (Lemlist, Apollo.io, Instantly, Woodpecker, Salesloft).
  - Suspicious domain variations (e.g., lookalike domains, free webmail addresses claiming to represent corporate brands).
  - High mismatch between `From` display name and actual sender address domain.
- **Phishing & Fraud Signals**:
  - Urgent threats of account suspension ("Your account will be terminated in 24 hours").
  - Unsolicited attachments with generic names (`invoice_9021.pdf`, `receipt.html`, `.zip` or macro files).
  - Cryptocurrency extortion, CEO gift card requests, unexpected wire transfer confirmations.
  - Mismatched hyperlinks pointing to third-party redirection or credential-harvesting endpoints.

### Negative Indicators (Exceptions - DO NOT classify as SPAM)
- Messages from verified internal company domains (e.g. `@company.com`).
- Direct responses to email threads initiated by the user.
- Scheduled calendar invitations from confirmed business partners or clients.
- Automated service notifications from platforms actively used by the user (GitHub, AWS, Google Cloud, Slack, Stripe) — unless verified as phishing spoof.

### Concrete Examples
- **Example A (Cold Sales)**:
  > *Subject: Quick question regarding your team's mobile development*  
  > *From: alex@offshore-dev-leads.biz*  
  > *Body: Hi Mikhail, Hope you are doing great. We provide top 1% React and Python developers starting at $25/hr. Would you be open to a 10-minute discovery call next Tuesday?*
- **Example B (Phishing / Scam)**:
  > *Subject: Action Required: Corporate Account Re-verification*  
  > *From: security@support-verify-google-account.com*  
  > *Body: Dear User, Your mailbox storage is full. Click here to confirm your password within 12 hours to avoid service disruption.*

---

## 3. Category 2: `REGULAR`

### Scope & Definition
Legitimate, expected communications that provide useful context, status updates, or reference material, but require **no action, reply, or immediate decision** from the user:
- Automated DevOps and system alerts (CI/CD passes, Dependabot bumps without conflict, release notices).
- Subscribed technical newsletters, engineering blogs, and digest feeds.
- Transactional receipts, payment confirmations, shipment tracking updates.
- Automated calendar notifications (Accept/Decline responses without custom comments).
- Broad company announcements, HR policy updates, all-hands reminders.

### Positive Detection Indicators
- **Sender Address**:
  - `no-reply@*`, `notifications@github.com`, `mailer-daemon@*`, `updates@*`, `billing@*`, `news@*`.
- **Headers & Footers**:
  - Presence of `List-Unsubscribe` headers.
  - Standard newsletter footers: "You are receiving this email because you subscribed to...", "Manage email preferences".
- **Content Characteristics**:
  - Summary / digest formats (bulleted lists of articles, release notes, weekly roundups).
  - Clear informational receipts with zero request for reply or feedback ("This is an automated message. Please do not reply.").
  - Meeting acceptance notices: "Mikhail, John Doe has accepted this invitation".

### Negative Indicators (Exceptions - Escalate to NEEDS_ATTENTION)
- Automated alerts indicating critical production failures where user is on call or owner.
- Newsletters or updates that embed an explicit direct question or action deadline for the user.
- Notifications containing an approval request requiring user click-through or sign-off.

### Concrete Examples
- **Example A (CI/CD Notification)**:
  > *Subject: [GitHub] Build #4812 passed on repo/skills-repo (main)*  
  > *From: notifications@github.com*  
  > *Body: Workflow 'CI Quality Gate' succeeded on commit 8f9b1c2. View workflow run details at https://github.com/...*
- **Example B (Subscribed Newsletter)**:
  > *Subject: ByteByteGo Newsletter: Top 5 Architectural Patterns for Distributed Systems*  
  > *From: alex@bytebytego.com*  
  > *Body: In this edition, we explore CQRS, Event Sourcing, and Saga patterns... [Unsubscribe link at bottom]*
- **Example C (Receipt / Transactional)**:
  > *Subject: Your receipt from Apple for iCloud+ storage*  
  > *From: no_reply@email.apple.com*  
  > *Body: Apple Invoice ID #INV-92812. Total billed: €2.99. Payment method: Master Card ending in 1234.*

---

## 4. Category 3: `NEEDS_ATTENTION`

### Scope & Definition
High-priority messages where human intervention, intellectual judgment, or a direct response is required:
- Direct emails from team members, managers, clients, or prospects asking questions.
- Action items, task assignments, and review requests (code reviews, document feedback).
- Interview scorecard reminders, hiring feedback requests, candidate interview schedules.
- Escalated bugs, urgent production incidents, security disclosures, or client blockers.
- Deadline-driven administrative requests (visa paperwork, contract approvals, compliance renewals).

### Positive Detection Indicators
- **Recipient Addressing**:
  - User's primary email address is in the `To:` field (not mass BCC, not broad alias like `all@`).
- **Direct Requests & Inquiries**:
  - "Could you please confirm...", "Can you review this pull request before 3 PM?", "What is your availability for...".
  - Explicit action request directed to the user.
- **Urgency & Deadlines**:
  - Clear deadline mentioned: "by EOD Friday", "before our client demo on Monday".
  - Subject tags: `[URGENT]`, `Action Required:`, `Approval Needed:`, `Scorecard Reminder:`.
- **Interview & Talent Operations**:
  - Prompts from Greenhouse, Lever, or recruiter asking to submit candidate evaluation scores.

### Negative Indicators (Exceptions)
- Routine automated emails that use the word "urgent" in generic marketing subject lines (e.g. "Urgent: 50% discount ends today!"). Check the sender and body authenticity.

### Concrete Examples
- **Example A (Colleague Inquiry)**:
  > *Subject: Question regarding client delivery timeline for Project Titan*  
  > *From: sarah.miller@company.com*  
  > *Body: Hi Mikhail, we need to finalize the deployment window for the Titan API. Do you think we can schedule the release for next Tuesday morning, or do we still need another day for regression testing? Let me know what you think.*
- **Example B (Interview Scorecard Reminder)**:
  > *Subject: Scorecard reminder for candidate: Alex Chen (Senior Backend Engineer)*  
  > *From: recruiting@company.com*  
  > *Body: Hi Mikhail, you recently completed the technical interview with Alex Chen. Please submit your scorecard feedback before 5:00 PM today so the hiring committee can make a decision.*
- **Example C (Client Escalation)**:
  > *Subject: Production API timeout errors observed in US-East cluster*  
  > *From: david.reed@client-enterprise.com*  
  > *Body: Hi Mikhail, our monitoring began reporting elevated HTTP 504 errors from the reporting endpoint starting at 09:30 CET. Could your team investigate whether the latest release caused this?*

---

## 5. Edge Cases & Ambiguity Resolution Matrix

| Scenario | Classification | Rationale & Handling |
|:---|:---:|:---|
| **Cold recruiter message** with generic template | `SPAM` | Mass outreach with no prior context or customized fit. |
| **Recruiter message** following up on a conversation user replied to previously | `NEEDS_ATTENTION` | Active conversation thread with ongoing interest. |
| **Vendor promotional email** with webinar invite | `REGULAR` | Informational marketing from existing vendor. Archive, do not trash. |
| **All-hands company announcement** from CEO | `REGULAR` | Broad company broadcast, no reply expected. |
| **Automated GitHub mention**: `@username please review` | `NEEDS_ATTENTION` | Direct human request routed through automated notification service. |
| **Automated CI/CD build failure** for user's active branch | `NEEDS_ATTENTION` | Requires user action to unblock pipeline. |
| **Automated CI/CD build failure** on unrelated shared branch | `REGULAR` | Informational status update not blocking user. |
| **Calendar invite update** with body: *"Mikhail, please prepare slide 4"* | `NEEDS_ATTENTION` | Contains specific human request embedded in invite. |
| **Calendar invite acceptance** with no text | `REGULAR` | Pure transactional status confirmation. |

### The Golden Fallback Rule
When in doubt:
1. **Never classify an email as `SPAM` unless there is high confidence** of unsolicited marketing or malicious intent. False-positive spam trashing risks missing critical business communications.
2. If uncertain between `REGULAR` and `NEEDS_ATTENTION`, classify as `NEEDS_ATTENTION` so the user is informed and has an opportunity to review or respond.
