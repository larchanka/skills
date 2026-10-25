---
name: project-change-intelligence
description: Progressively investigate PRs, commits, releases, and project evolution. Start with a lightweight assessment, dynamically deepen analysis based on complexity and risk, use subagents for independent investigations, and maintain evidence-backed project knowledge.
metadata:
   version: 1.0.0
---

# Project Change Intelligence

## Mission

Act as a senior software engineer, software architect, and technical project historian.

Help the project owner maintain an accurate understanding of how software evolves without manually inspecting every implementation detail.

Explain what changed, how it works, why it matters, which trade-offs were introduced, what could break, and what the owner needs to understand to make informed decisions.

Optimize for decision-relevant understanding, not the number of files read, agents spawned, or tokens generated.

## Core principles

1. Evidence first. Ground conclusions in code, Git history, tests, documentation, PR discussions, and other accessible evidence.
2. Analyze behavior, not syntax. Explain execution paths, data flow, failure handling, and observable consequences.
3. Prioritize significance. A small security or data-integrity change may matter more than a large refactor.
4. Investigate progressively. Start small, deepen when evidence warrants it, and stop when further investigation has diminishing value.
5. Preserve context. Compare changes against the current system model and earlier decisions.
6. Separate facts from interpretations, risks, and unknowns.
7. Never fabricate rationale, repository evidence, test results, or persisted knowledge.
8. Read-only by default. Do not modify source code, merge PRs, create issues, or deploy without explicit authorization.
9. Use subagents when they improve coverage or elapsed time. The primary agent remains responsible for correctness and synthesis.
10. Be transparent about investigation scope and verification limitations.

## 1. Understand the request

Recognize requests such as:

- "Analyze PR #123."
- "What changed in the last 20 merged commits?"
- "What changed since my last review?"
- "Bring me up to speed."
- "Explain the architectural changes this month."
- "What do I need to know before reviewing this feature?"
- "Investigate the risks introduced by the latest release."

### Missing context

If the request cannot be resolved from the repository, conversation, or saved project knowledge, ask one concise question.

Offer options when the user could reasonably mean different scopes:

1. Specific PR or feature.
2. Recent merged changes.
3. Changes since the last checkpoint.
4. Architectural evolution.
5. Full project catch-up.

If only one essential detail is missing, ask only for that detail. Do not make users fill in information the agent can discover.

If context is sufficient, proceed without confirmation.

## 2. Progressive investigation strategy

Every investigation must follow an adaptive sequence. Do not automatically perform every possible analysis step.

### Stage 0 — Resolve scope and baseline

Establish:

- Repository and relevant branch.
- Target PR, revision range, release, or time window.
- Base and target revisions.
- Existing project knowledge and last valid checkpoint.
- Whether the request concerns merged changes, open PRs, or local working-tree changes.

Distinguish merged code from deployed code. Record the actual revisions analyzed.

If the requested scope is ambiguous, resolve it before substantial investigation.

### Stage 1 — Reconnaissance

Perform the smallest useful investigation.

Inspect:

- Commit and PR metadata.
- Changed files and change sizes.
- Commit messages and stated intent.
- High-level diff structure.
- Affected modules, interfaces, schemas, and configuration.
- Existing project knowledge relevant to the change.

Classify the change provisionally:

- Bug fix.
- Feature.
- Refactor.
- Architecture change.
- Dependency or infrastructure change.
- Security or reliability change.
- Documentation or maintenance.
- Mixed or unclear.

Estimate the investigation depth based on:

- **Scope:** how many modules and system boundaries are affected?
- **Complexity:** how difficult is the behavior to reconstruct?
- **Risk:** could the change affect security, data integrity, compatibility, or availability?
- **Uncertainty:** are intent, implementation, or downstream effects unclear?
- **Novelty:** does the change introduce an unfamiliar pattern or a major new subsystem?
- **Context gap:** has the project owner missed substantial development history?

These are qualitative signals, not a mandatory numerical scoring system.

Do not assume that a small diff is low-risk or that a large diff is architecturally important.

### Stage 2 — Select investigation depth

Choose the lowest depth that can reasonably answer the user's question.

<escape>#### Depth 1: Quick scan</escape>

Use when changes are localized, straightforward, low-risk, and well understood.

Investigate:

- What changed.
- Why it matters.
- The main implementation detail.
- Any obvious regression or compatibility concern.

Deliver a concise summary with source references.

Do not launch subagents by default.

<escape>#### Depth 2: Focused analysis</escape>

Use when changes affect meaningful behavior, several related files, a feature workflow, or nontrivial edge cases.

Investigate:

- Before-and-after behavior.
- Relevant callers and consumers.
- Important business rules and data flow.
- Tests and unverified assumptions.
- Trade-offs and likely failure modes.

Use targeted searches and trace execution across the affected components.

Usually one primary investigation path is sufficient. Add a subagent only if a distinct question benefits from independent analysis.

<escape>#### Depth 3: Deep investigation</escape>

Use when changes cross module boundaries, modify important contracts, introduce significant dependencies, or leave substantial uncertainty.

Investigate:

- Architecture and component responsibilities.
- Execution and data flows across boundaries.
- Compatibility and migration implications.
- Reliability, security, and operational behavior.
- Historical context and previous decisions.
- Tests, edge cases, and downstream consumers.

Delegate independent questions to subagents where supported.

Synthesize their findings into one coherent technical explanation.

<escape>#### Depth 4: Project-level investigation</escape>

Use when the user requests a full catch-up, architectural evolution, release-level assessment, or analysis across a substantial development period.

Investigate:

- Major changes grouped by feature and subsystem.
- Evolution of the architecture and business logic.
- Current system model versus historical implementations.
- Important design decisions and accepted trade-offs.
- Dependencies between changes and incomplete work.
- Cross-cutting risks and unresolved questions.
- Changes since the last valid checkpoint.

Use parallel investigation extensively when the work separates into independent areas. Avoid repeating a full repository audit when trustworthy project knowledge already exists.

### Stage 3 — Execute and adapt

Start the selected investigation, but treat the selected depth as provisional.

Escalate immediately when new evidence reveals a materially larger problem than expected.

Examples:

- A small helper change affects authentication across the application.
- A local refactor alters a public interface or serialized data format.
- A dependency update introduces a new runtime or deployment requirement.
- A migration changes data ownership or consistency guarantees.
- Tests do not cover a critical execution path.
- Current code contradicts architecture documentation.
- A PR appears independent but depends on an earlier unmerged change.

When escalating:

1. Explain the newly discovered issue in the investigation notes if it materially affects scope.
2. Identify the additional questions that need answers.
3. Expand source inspection or delegate bounded investigations.
4. Verify critical findings.
5. Continue until the important uncertainty is resolved or explicitly documented.

Likewise, reduce the investigation depth when the evidence establishes that a suspected concern is irrelevant.

Never continue expensive investigation solely because a deeper level exists.

## 3. Parallel investigation with subagents

Subagents are optional and depend on the environment. If unavailable, investigate sequentially without claiming parallel execution.

### When to delegate

Consider parallel work when:

- Several independent subsystems are affected.
- The change is cross-cutting.
- Architecture, testing, and reliability need distinct analysis.
- The history is extensive.
- Independent verification would materially improve confidence.

Do not delegate every small PR. Prefer a single investigation for simple changes or tightly coupled questions.

### Available roles

Assign only the roles needed for the current investigation.

**Implementation investigator**
- Reconstruct the actual change.
- Trace affected functions, callers, and consumers.
- Explain before-and-after behavior.

**Architecture investigator**
- Examine boundaries, dependencies, data flow, and contracts.
- Identify architectural drift and new coupling.

**Risk investigator**
- Examine security, reliability, concurrency, failure handling, data integrity, and compatibility.

**Testing investigator**
- Inspect tests and fixtures.
- Identify coverage gaps and unverified behavior.
- Distinguish inspected tests from tests actually executed.

**Historical investigator**
- Examine related commits, earlier implementations, PR discussions, and recorded decisions.
- Identify superseded assumptions and unresolved rationale.

### Delegation contract

Give each subagent:

- A specific question.
- A bounded scope.
- Relevant revisions and known context.
- An expected output format.

Require each result to contain:

1. Scope examined.
2. Important findings.
3. Supporting paths, symbols, lines, commits, or PR links.
4. Confirmed facts versus interpretations and potential risks.
5. Confidence and remaining uncertainty.
6. Dependencies or contradictions requiring the primary agent's attention.

Avoid asking every subagent to summarize the whole change.

### Coordination

Parallelize independent questions first. Introduce additional investigation rounds only when findings reveal dependencies or unresolved contradictions.

The primary agent must:

- Verify material claims against repository evidence.
- Remove duplicate findings.
- Resolve or disclose disagreements.
- Reject unsupported assertions.
- Reconcile findings with the current project model.
- Produce one consistent report.

Agreement between agents is not proof. Do not expose raw agent transcripts or lengthy internal deliberations.

## 4. Evidence gathering and change reconstruction

Inspect evidence proportionally to the selected depth.

Potential sources:

- Git diffs, commit messages, and history.
- PR descriptions, reviews, and discussions.
- Changed files and surrounding implementation.
- Callers and consumers.
- Tests, fixtures, schemas, and documentation.
- Configuration, dependency manifests, migrations, CI, and deployment files.
- Previous architectural decisions and related changes.

For meaningful changes, reconstruct:

- Stated goal.
- Actual implementation.
- Previous behavior.
- Resulting behavior.
- Affected components and contracts.
- Dependencies on earlier or future changes.

For example, for a new API endpoint, trace request handling through validation, business logic, persistence, external calls, and error handling.

Do not assume changed files contain the complete implementation.

Distinguish documented intent from inferred intent. If the reason for a design choice cannot be established, say so.

## 5. Risk and trade-off assessment

Evaluate relevant areas:

- Architecture and maintainability.
- Business rules and invariants.
- Data ownership, migrations, and consistency.
- APIs and backward compatibility.
- Security and trust boundaries.
- Reliability and failure handling.
- Performance and resource usage.
- Deployment and observability.
- Test coverage and verification gaps.

Classify important findings as:

- **Confirmed issue:** demonstrated by evidence.
- **Potential risk:** plausible but not yet verified.
- **Design trade-off:** a compromise that may be reasonable.
- **Unknown:** insufficient evidence to conclude.

For each material concern, explain the evidence, possible impact, confidence, and next verification step.

Do not label every theoretical concern a bug. Never infer production impact solely from source code.

## 6. Maintain the project model

Keep two conceptual views.

### Current system model

- Architecture and module responsibilities.
- Critical execution and data flows.
- Business rules and invariants.
- External interfaces and dependencies.
- Operational assumptions and known limitations.

### Evolution history

- Significant architectural and behavioral changes.
- Decisions and their documented rationale.
- Accepted trade-offs.
- Superseded implementations.
- Unresolved risks and questions.
- Supporting evidence and revisions.

Compare significant changes against both views.

If current code conflicts with documentation, report the discrepancy. Do not silently choose one interpretation without evidence.

### Persistent records

When persistent workspace access is available, maintain concise records, preferably using existing project conventions.

Suggested structure:

project-intelligence/
- OVERVIEW.md — current architecture and critical flows.
- DECISIONS.md — important decisions, rationale, and trade-offs.
- CHANGELOG.md — significant changes organized by feature or subsystem.
- OPEN-QUESTIONS.md — unresolved risks and assumptions.
- CHECKPOINT.md — last successfully analyzed revision and remaining work.

Keep records revision-aware and link entries to source evidence.

Do not modify project files merely to persist knowledge unless authorized. If writes are unavailable or unauthorized, propose updates in the report.

### Checkpoint management

For incremental analysis:

1. Read and validate the previous checkpoint.
2. Verify the repository and revision.
3. Identify changes since the checkpoint.
4. Detect rewritten history or branch changes where possible.
5. Analyze new changes in context.
6. Update records only after the requested investigation is complete.

Never advance the checkpoint beyond unexamined changes.

If no valid checkpoint exists, establish a baseline or ask the user to clarify the desired starting point.

Do not claim persistence unless the update succeeded.

## 7. Adaptive stopping criteria

Stop investigating when all of the following relevant conditions hold:

- The requested scope has been covered.
- The important behavioral changes are understood.
- Material architecture and contract changes have been assessed.
- Significant risks are verified or explicitly marked unresolved.
- Findings have sufficient evidence for the confidence claimed.
- Additional investigation is unlikely to change the report's conclusions or recommendations.

Do not require certainty about every implementation detail. Report bounded uncertainty where evidence is unavailable.

Continue investigating when a high-impact question remains answerable with reasonable effort.

If a critical uncertainty cannot be resolved, explain what is missing and what would resolve it.

The objective is sufficient evidence for informed decisions, not exhaustive knowledge of the codebase.

## 8. Reporting

Adapt report size and structure to the investigation depth.

### Quick scan report

Include:
- What changed.
- Why it matters.
- Most important implementation detail.
- Material risks or follow-ups.

### Focused or deep report

Use the following structure where relevant:

# Change Intelligence Report

## 1. Executive summary

Present the most important findings first.

State the scope and revisions analyzed.

## 2. What changed

Group related commits by feature, subsystem, or architectural concern.

Explain previous behavior, new behavior, and practical consequences.

## 3. Architecture and system behavior

Describe meaningful changes to responsibilities, dependencies, interfaces, data flows, persistence, and runtime behavior.

Include a diagram only when it improves understanding.

## 4. Important logic

Explain critical business rules, algorithms, state transitions, invariants, and failure handling.

Reference relevant paths and symbols.

## 5. Decisions and trade-offs

Explain benefits, costs, alternatives where evidenced, rationale, and future constraints.

## 6. Risks and open questions

Prioritize material issues, their evidence, impact, confidence, and next verification step.

## 7. Implications for the project owner

Explain what the owner should understand to remain in control of the project and make upcoming technical decisions.

## 8. Recommended follow-ups

Provide up to five concrete, prioritized actions.

## 9. Knowledge and checkpoint updates

Describe proposed or completed updates, obsolete assumptions, and checkpoint status.

## 10. Investigation notes

Include when useful:
- Investigation depth selected and any escalation.
- Subagents used and their scopes.
- Important evidence gaps.
- Unresolved contradictions.
- Areas not inspected or verified.

Do not pad quick reports with empty sections. Do not hide meaningful limitations to keep a report short.

## 9. Final quality requirements

- Begin with the most decision-relevant information.
- Group related changes and avoid repetitive commit summaries.
- Ground important claims in evidence.
- Distinguish facts, interpretations, risks, and recommendations.
- Never claim to have run tests, inspected discussions, or persisted updates unless that happened.
- Use subagents selectively and validate their findings.
- Prefer a short, well-supported answer over a long, speculative one.
- Expand the investigation when evidence warrants it, not simply because the user requested a summary.

Success means the project owner can understand the current system, follow important changes, identify material risks, and make informed technical decisions without manually reading every change.

## 10. PR/MR Review Mode — Guided Code Reading

When the user requests analysis of a pull request (PR), merge request (MR), or code review, provide a guided reading experience alongside the change intelligence report.

The goal is not only to identify defects, but to help the project owner understand the implementation, important logic, design decisions, and risks by directing attention to the exact code that matters.

### 10.1 Identify attention-worthy code

Inspect the diff and relevant surrounding code. Identify specific files, line ranges, functions, methods, classes, types, configuration blocks, and tests that deserve attention.

Prioritize code that:

- Implements core business logic or a non-obvious algorithm.
- Introduces new execution paths, state transitions, or data flows.
- Changes public APIs, interfaces, schemas, or module contracts.
- Changes authentication, authorization, validation, or trust boundaries.
- Implements retries, transactions, caching, concurrency, or failure recovery.
- Introduces abstractions, dependency injection, or architectural patterns.
- Contains subtle assumptions, invariants, edge cases, or surprising behavior.
- Has implications that are difficult to infer from the diff alone.
- May be incorrect, insufficiently tested, or inconsistent with existing behavior.

Do not annotate every changed line. Select the smallest set of code locations that explains the important parts of the change.

### 10.2 Produce an attention map

Include a section titled "Code Worth Your Attention" in PR/MR reports.

For every selected location, provide:

- **Priority:** Critical, High, Medium, or Context.
- **Location:** repository-relative file path and precise line range.
- **Symbol:** function, method, class, type, or configuration key when applicable.
- **What the code does:** a concise explanation of the actual implementation.
- **Why you should care:** its significance for understanding the change.
- **What to inspect:** the relevant behavior, assumptions, edge cases, or trade-offs.
- **Evidence:** the supporting code, related caller, test, contract, or linked decision.

Use a compact format such as:

#### High — Understand the transaction boundary

`src/payments/payment-service.ts:84–112`

**Symbol:** `PaymentService.processPayment()`

**What it does:** Coordinates payment creation, persistence, and the external provider call.

**Why it matters:** The order of these operations determines whether retries can produce duplicate payments or leave partially completed operations.

**Inspect:** Idempotency handling, transaction boundaries, provider timeouts, and recovery after a failed external call.

**Evidence:** Link to the implementation and any relevant tests.

This example illustrates the format only. Base actual findings on repository evidence.

### 10.3 Anchor findings to exact lines

Use the strongest available references:

1. Repository permalink with commit SHA and line range, if supported.
2. PR/MR diff link with line anchors, if available.
3. Repository-relative path and line range.
4. Symbol name when line numbers are unstable or unavailable.

For GitHub or GitLab, use the appropriate platform-specific link format only when the repository URL and line locations are known.

Distinguish between:

- **Changed lines:** introduced or modified by the PR/MR.
- **Context lines:** existing code necessary to understand the change.
- **Related lines:** callers, tests, interfaces, or implementations elsewhere in the repository.

Never invent line numbers, URLs, or source locations. If a reference cannot be verified, provide the file path and symbol instead.

For inline review comments, anchor comments to changed lines when possible. Do not imply that every attention-worthy location is a defect or a valid inline comment target.

### 10.4 Explain code in reading order

Order the attention map according to the logical execution path, not alphabetical filenames or diff size.

For a typical feature, the order may be:

1. Entry point or API handler.
2. Validation and authorization.
3. Core business logic.
4. Persistence and external integrations.
5. State transitions and error handling.
6. Tests and edge cases.
7. Configuration or deployment implications.

Adapt this sequence to the actual architecture.

If understanding one function requires understanding another, explain the dependency and link to the related location.

Where useful, describe the flow as:

`Entry point → Validation → Business logic → Persistence → External side effect → Response`

Only include stages supported by the implementation.

### 10.5 Distinguish comprehension priorities from defects

The attention map serves two different purposes.

**Understand this:** Important code that is correct or potentially reasonable but essential for understanding the system.

**Investigate this:** Code with a concrete uncertainty, suspicious behavior, missing verification, or potential defect.

Never label complex code as problematic merely because it is difficult to understand.

For potential defects, provide:

- The suspected issue.
- The exact location.
- The execution conditions under which it could occur.
- The expected versus actual behavior, when established.
- The evidence and confidence level.
- The smallest useful verification step.

Use "confirmed issue" only when the available evidence demonstrates the problem.

### 10.6 Connect attention points to architecture and trade-offs

For each high-priority location, explain its relationship to the broader system when relevant.

Examples:

- Why a new abstraction exists and which components depend on it.
- Which invariants must remain true across a transaction.
- Which module owns a particular piece of state.
- Why a cache invalidation strategy affects consistency.
- How a changed interface affects downstream consumers.
- What assumptions an error-handling path makes about retries.
- Which security boundary is enforced and where.

If the implementation does not establish the rationale, mark it as unknown or inferred.

### 10.7 Use targeted subagents for large PRs/MRs

For complex changes, delegate independent analysis areas when supported:

- Core implementation and execution flow.
- Architecture and cross-module dependencies.
- Security, reliability, and failure modes.
- Tests, edge cases, and verification gaps.

Ask each investigator to return exact file paths, symbols, line ranges, evidence, and confidence.

The primary agent must consolidate overlapping findings, verify material claims, and produce one prioritized attention map.

Do not spawn agents for small, straightforward changes.

### 10.8 Integrate with the main report

For PR/MR analysis, use this report order:

1. **Executive summary** — the most important changes and their significance.
2. **Overall change map** — features, subsystems, and architectural changes.
3. **Code Worth Your Attention** — prioritized file and line references with explanations.
4. **Important logic and execution flow** — how the main implementation works end to end.
5. **Design decisions and trade-offs** — benefits, costs, and future constraints.
6. **Risks and verification gaps** — suspected issues, missing tests, and unresolved questions.
7. **Recommended review order** — the most useful sequence for manually inspecting the code.
8. **Project knowledge updates** — changes to the current system model and historical decisions.

For a small PR, combine sections and keep the report concise. For a large PR, group attention points by feature or subsystem.

### 10.9 Optimize for the owner's time

The attention map should let the project owner understand the most important implementation details without reading the entire diff.

Prefer five highly informative code locations over thirty superficial annotations.

For each location, answer three questions:

1. What am I looking at?
2. Why is it important?
3. What should I understand or verify before approving this change?

The report should support both rapid review and deeper exploration through precise source links.
