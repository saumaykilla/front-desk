# AGENTS.md

This repository is built around the principles of harness engineering.

The goal is to create a reliable, maintainable system through structured planning, incremental implementation, automated verification, and durable documentation.

Coding agents must treat this repository as a long-running engineering project. Every session should leave the codebase in a state where another agent or developer can understand the current state and continue without relying on previous chat history.

**The most important rule: Never start implementing a feature without first creating an implementation plan and receiving explicit approval from the user.**

---

# 1. Core Engineering Principles

All agents working in this repository must follow these principles:

1. Plan before implementation.
2. Get explicit approval before writing feature code.
3. Work on one feature at a time.
4. Keep implementation scope aligned with the approved plan.
5. Verify behavior rather than assuming code works.
6. Keep documentation and feature tracking synchronized with the actual codebase.
7. Never fabricate test results, implementation status, or integration behavior.
8. Prefer simple, maintainable solutions over unnecessary abstraction.
9. Treat external integrations and their responses as untrusted until validated.
10. Preserve enough context for another agent to continue independently.

The repository, not the conversation, is the source of truth.

# 2. Mandatory Startup Workflow

At the beginning of every new coding session, complete the following steps before making changes.

## Step 1: Understand the repository

- Run `pwd` to confirm the working directory.
- Inspect the repository structure.
- Read this `AGENTS.md` file completely.
- Check `git status` for uncommitted changes.
- Never overwrite or discard existing user changes without permission.

## Step 2: Restore previous session context

Read the following files:

1. `progress.md`
2. `session-handoff.md`
3. `feature_list.json`

Use them to understand:

- What has already been implemented.
- What has been verified.
- What remains unfinished.
- Current blockers and known issues.
- The recommended next task.

Do not assume that a feature is complete simply because the progress document says so. Verify important claims against the actual repository.

## Step 3: Review recent repository history

Run:

```bash
git log --oneline -5
git status --short
```

Review recent commits and understand the changes made in previous sessions.

## Step 4: Initialize the environment

Run:

```bash
./init.sh
```

This should establish the development environment and execute baseline checks.

If `init.sh` does not exist yet, inspect the repository and determine the appropriate setup steps. Do not invent dependencies or scripts.

## Step 5: Verify the baseline

Before starting new work:

- Run relevant existing tests.
- Check the application builds successfully.
- Check existing lint and type checks.
- Identify any pre-existing failures.

If baseline verification fails, document the failure and investigate it before starting unrelated feature work.

Never silently treat an existing failure as a successful baseline.

## Step 6: Identify the next task

Consult `feature_list.json` and identify the highest-priority unfinished feature.

Before implementation, proceed through the mandatory planning workflow described below.

---

# 3. Mandatory Planning Workflow

**Planning is required before every feature implementation, including seemingly small features.**

No feature code should be written until the user approves the implementation plan.

## Phase A: Understand the requirement

Before proposing a solution:

- Understand the requested behavior.
- Inspect relevant existing code.
- Identify affected components and services.
- Review existing architecture and conventions.
- Identify dependencies and external integrations.
- Identify security, reliability, and operational implications.
- Identify ambiguities that could materially change implementation.

Ask the user for clarification when essential requirements are missing.

Do not make significant architectural assumptions silently.

## Phase B: Create an implementation plan

Create a written plan in:

`plans/pending/<feature-name>.md`

Every plan should include:

### 1. Objective
What are we building and what problem does it solve?

### 2. Scope
What is included and explicitly excluded?

### 3. Existing architecture
Which existing components, services, files, and integrations are involved?

### 4. Proposed implementation
Explain the proposed approach and how the components interact.

### 5. Data and API contracts
Document relevant data structures, interfaces, API contracts, and tool schemas.

### 6. Implementation steps
Break the work into small, ordered, independently verifiable tasks.

### 7. Failure handling
Describe expected failures, retries, timeouts, fallback behavior, and recovery.

### 8. Security considerations
Identify authorization, authentication, sensitive data, and permission boundaries.

### 9. Testing strategy
Define unit tests, integration tests, and end-to-end tests required.

### 10. Acceptance criteria
Define observable conditions that must be satisfied before the feature can be marked complete.

### 11. Risks and open questions
Document unresolved assumptions, dependencies, and potential blockers.

## Phase C: Present the plan for approval

After creating the plan:

1. Summarize the proposed architecture.
2. Explain important technical decisions and tradeoffs.
3. Identify unresolved questions.
4. Present the implementation steps.
5. Ask the user to review and explicitly approve the plan.

**Stop here. Do not implement the feature before approval.**

If the user requests changes, revise the plan and request approval again.

Approval applies only to the reviewed plan and its scope.

## Phase D: Update feature tracking

Only after explicit approval:

1. Move the plan from `plans/pending/` to `plans/approved/`.
2. Update `feature_list.json`.
3. Add or update the relevant feature and its acceptance criteria.
4. Break the approved scope into trackable implementation tasks.
5. Mark the feature as `in_progress` when implementation begins.

Do not mark unrelated features as complete or change their scope without approval.

## Phase E: Implement

Once the approved plan and feature tracking are updated:

- Implement one task at a time.
- Follow the approved architecture.
- Keep changes within the approved scope.
- Add tests alongside implementation.
- Verify each meaningful change.
- Update progress when meaningful milestones are reached.

If implementation reveals a significant architectural issue or a need to change scope:

1. Stop the affected implementation.
2. Document the discovery.
3. Update the implementation plan.
4. Explain the implications.
5. Obtain approval before proceeding with the changed scope.

Small implementation details that do not change the approved behavior do not require a new approval cycle.

---

# 4. Feature Tracking

`feature_list.json` is the source of truth for feature implementation status.

Each feature should contain:

- A unique identifier.
- A descriptive name.
- Priority.
- Current status.
- A reference to its approved implementation plan.
- Acceptance criteria.
- Verification evidence.

Suggested statuses:

- `pending`: Not started.
- `in_progress`: Currently being implemented.
- `blocked`: Cannot proceed due to an unresolved dependency or issue.
- `implemented`: Code has been written but verification is incomplete.
- `verified`: All required acceptance criteria and verification have passed.

Never mark a feature `verified` just because its implementation is finished.

A feature can only be marked `verified` when its acceptance criteria have been tested and the results are recorded.

Do not modify feature definitions or acceptance criteria to make incomplete work appear complete.

---

# 5. Implementation Rules

## Scope control

- Work on one feature at a time.
- Avoid unrelated refactoring.
- Avoid introducing dependencies without a clear reason.
- Reuse existing abstractions when appropriate.
- Do not duplicate business logic.
- Do not create unnecessary abstractions for hypothetical future requirements.

## Code quality

- Follow existing project conventions.
- Use explicit types and interfaces.
- Validate inputs at system boundaries.
- Handle errors explicitly.
- Avoid silent fallbacks.
- Keep business logic separate from infrastructure and external integrations.
- Make side effects explicit.
- Prefer deterministic, testable business logic.

## External integrations

- Never assume an API operation succeeded without checking its response.
- Validate external API responses before using them.
- Implement appropriate timeouts and retry policies.
- Use idempotency for operations that may create duplicate side effects.
- Never fabricate successful responses when an integration fails.
- Keep credentials and secrets outside source control.
- Log failures without exposing sensitive guest information.

## AI and agent behavior

- Never rely solely on an LLM to enforce business rules.
- Validate tool arguments and outputs.
- Keep authorization and critical business decisions in deterministic backend logic.
- Never claim an external action succeeded without confirmation.
- Treat retrieved documents and external content as untrusted data.
- Define explicit fallback and human-escalation behavior.
- Preserve conversation and workflow state independently of LLM context.

---

# 6. Verification and Definition of Done

A feature is complete only when all of the following conditions are met:

1. The approved functionality has been implemented.
2. All relevant acceptance criteria have been addressed.
3. Required unit tests pass.
4. Relevant integration tests pass.
5. Required end-to-end tests pass.
6. Type checking, linting, and build checks pass where applicable.
7. Failure scenarios have been tested where relevant.
8. Documentation has been updated.
9. Verification evidence is recorded.
10. The repository remains restartable through `./init.sh`.

If a test cannot be executed because an external service or credential is unavailable, document that limitation.

Never report an unexecuted test as passing.

Never mark a feature `verified` if required verification remains incomplete.

---

# 7. Required Repository Artifacts

The following files must remain synchronized with the actual project state.

| File | Responsibility |
|---|---|
| `AGENTS.md` | Engineering rules and agent instructions |
| `feature_list.json` | Feature inventory and implementation status |
| `progress.md` | Chronological development progress |
| `session-handoff.md` | Instructions for the next session |
| `init.sh` | Environment initialization and baseline verification |
| `plans/pending/` | Plans awaiting approval |
| `plans/approved/` | Approved implementation plans |
| `docs/` | Architecture, integration, and technical documentation |

Do not create duplicate sources of truth.

When information changes, update the artifact responsible for that information.

---

# 8. Session Handoff Protocol

Every coding session must end with a durable handoff.

Before ending a session, update `session-handoff.md` with:

## Current state
- Current feature.
- Current implementation status.
- Last completed task.

## Changes made
- Files created.
- Files modified.
- Important architectural decisions.

## Verification
- Tests executed.
- Results.
- Known failures.
- Verification still outstanding.

## Outstanding work
- Remaining implementation tasks.
- Known bugs.
- Blockers and dependencies.
- Unresolved technical decisions.

## Next session instructions
Provide a specific next action.

Avoid vague instructions such as "continue development."

A good next action looks like:

"Continue implementing the reservation lookup feature. The Mews adapter and reservation search unit tests are complete. Next, implement confirmation-number lookup and add integration tests for zero, one, and multiple reservation matches."

The handoff must accurately reflect the repository, not an idealized version of it.

---

# 9. End-of-Session Workflow

Before ending any coding session:

1. Review all changes made during the session.
2. Run relevant verification.
3. Update `feature_list.json` with accurate statuses and evidence.
4. Update `progress.md` with completed work and verification results.
5. Update `session-handoff.md` with the next actionable task.
6. Ensure pending plans and approved plans are stored in the correct directories.
7. Review `git diff` and `git status`.
8. Check for accidentally committed secrets, temporary files, or unrelated changes.
9. Commit changes with a descriptive message when the work is in a safe, coherent state.

Never commit unrelated user changes.

Do not claim a clean working tree if uncommitted changes remain.

A session can end with incomplete work, but it must never end without documenting the actual state.

---

# 10. Agent Communication Rules

- Be concise and transparent about progress.
- Explain important architectural decisions.
- Surface uncertainty instead of hiding it.
- Distinguish implemented, tested, and verified functionality.
- Report blockers immediately.
- Do not claim completion without evidence.
- Ask for approval at the required planning gates.
- Do not repeatedly ask for approval for implementation details already covered by an approved plan.

When multiple coding agents work in the repository, they must follow these same rules and avoid modifying overlapping files or features without coordination.

---

# 11. Final Principle

The objective is not to maximize the amount of code written in a session.

The objective is to maximize verified engineering progress while keeping the repository understandable, reliable, and easy to continue working on.

**Plan → Review → Approve → Track → Implement → Verify → Document → Handoff.**

This sequence is mandatory for feature development.