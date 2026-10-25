---
name: agent-loop
description: Orchestrates a multi-agent loop involving planning, development, review, and publishing sub-agents to implement and publish features test-first and with high standards compliance.
metadata:
   version: 1.0.0
---

# Multi-Agent Iteration Loop

This skill coordinates four independent agents (`planning`, `development`, `review`, and `publisher`) in a continuous loop to deliver and publish spec-compliant, standard-abiding features.

```mermaid
graph TD
    Start["User Request / Spec"] --> Plan["1. Planning Subagent"]
    Plan --> SavePlan["Generate tasks/plan.md & todo.md"]
    SavePlan --> ApprPlan{"User Approval?"}
    ApprPlan -- No --> Plan
    ApprPlan -- Yes --> Dev["2. Development Subagent"]
    Dev --> ImpTask["Implement Next Task via TDD"]
    ImpTask --> Rev["3. Review Subagent"]
    Rev --> Check{"Any Findings?"}
    Check -- Yes (Bug / Smell) --> Dev
    Check -- No --> CheckMore{"More Tasks?"}
    CheckMore -- Yes --> Dev
    CheckMore -- No --> Pub["4. Publisher Subagent"]
    Pub --> OpenPR["Create Branch, Commit & gh pr create"]
    OpenPR --> Done["Done - Pull Request Published"]
```

## Workflow Execution Steps

> [!IMPORTANT]
> **Coordinator Constraint**: The coordinator agent executing this skill MUST NOT write implementation code, create source files, or modify files in the codebase directly during the development phase. The coordinator is solely responsible for planning, orchestrating the loop, conducting code reviews, and managing publishing. All code changes and task implementations MUST be delegated to the spawned subagents.

### 1. Planning Phase
- **Spawn the `planning` subagent** to read the user request/specification and codebase structure.
- The `planning` agent will output `tasks/plan.md` (architecture, design, tasks) and `tasks/todo.md` (checkbox todo list).
- Once the plan is saved, present it to the user for feedback and approval.

### 2. Development Phase (Task Implementation)
- **Select the first incomplete task** from `tasks/todo.md`.
- **Spawn the `development` subagent** to implement that task.
- The `development` agent must:
  - Operate incrementally, writing a failing unit test first.
  - Implement only enough code to pass the test.
  - Verify compile checks and execution results.
  - Update the status of the task in `tasks/todo.md` to completed `[x]`.

### 3. Review Phase (Quality Gates)
- **Spawn the `review` subagent** to perform standard and spec audits on the branch's git diff.
- The `review` agent outputs findings under `## Standards` and `## Spec` headers.
- **Evaluate results**:
  - **If there are findings** (e.g., hard violations or baseline smells):
    - Send a message to the `development` subagent containing the reviewer's report.
    - Instruct the developer to resolve the bugs or smells.
    - Rerun the `review` agent once the developer has updated the branch.
  - **If there are 0 findings**:
    - Check `tasks/todo.md` for the next incomplete task.
    - If tasks remain, loop back to **Step 2**.
    - If all tasks are completed, proceed to **Step 4**.

### 4. Publishing Phase (Deployment Gate)
- **Spawn the `publisher` subagent** to automate the integration and deployment lifecycle.
- The `publisher` agent must:
  - Verify `git status` and stage all changed files.
  - Commit files using the Conventional Commits syntax and push to origin.
  - Execute `gh pr create` with standard metadata titles/descriptions to open the GitHub Pull Request.
  - Return the direct URL link to the Pull Request.

## Exit Criteria
- All tasks in `tasks/todo.md` are marked `[x]`.
- The `review` agent reports 0 standard violations or spec omissions.
- All unit and integration tests in the test suite pass successfully.
- The `publisher` agent has successfully pushed and opened a GitHub Pull Request, sharing its URL.

## Sub-Agent Skill References

To ensure execution consistency, each sub-agent in this loop is dedicated to executing a specific workspace skill. They must load and re-use the following guides:

*   **Planning Sub-Agent**:
    *   Primary Skill: [planning-and-task-breakdown](../planning-and-task-breakdown/SKILL.md) (used to analyze dependencies, partition slices, and output plans).
*   **Development Sub-Agent**:
    *   Primary Skill: [test-driven-development](./test-driven-development/SKILL.md) (drives test-first RED-GREEN loops at public boundaries).
*   **Review Sub-Agent**:
    *   Primary Skill: [code-review](../code-review/SKILL.md) (performs two-axis checks for standard compliance and specification compliance).
*   **Publisher Sub-Agent**:
    *   Primary Skill: [pull-request](../pull-request/SKILL.md) (automates git checkout, commits, pushes, and GitHub CLI PR creation).

