---
description: Amend an existing feature spec in-place and implement the change through a lightweight validation pipeline. Supports natural language input from users or other agents.
handoffs:
  - label: Run Full Analysis
    agent: speckit.analyze
    prompt: Run a full consistency analysis across spec, plan, and tasks
  - label: Create New Spec Instead
    agent: speckit.specify
    prompt: Create a new feature spec to supersede the current one
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --paths-only
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before amendment)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_amend` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Outline.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Design Principles

1. **Agent-native**: Takes a natural language description of what changed — does not rely on the user having manually edited files. A user tells an agent, or another agent invokes it programmatically.
2. **Spec-first, always**: The spec is edited before any code changes.
3. **Correct before fast**: Every amendment goes through a mini validation pipeline — spec edit → consistency check → change plan → implement. Lighter than the full specify→plan→tasks→implement pipeline, but never skips validation.
4. **Human-in-the-loop**: The user must explicitly approve the proposed spec changes (Gate 1) and the amendment plan (Gate 2) before any file writes or code changes happen. Never auto-pilot through the full flow.
5. **Surgical edits**: Spec changes are precise modifications to existing sections, not rewrites. The spec remains a single, self-contained document.
6. **Atomic commits**: Spec + code are committed together. If implementation fails, the spec edit is reverted too.

## Outline

The text the user typed after `/speckit.amend` in the triggering message **is** the amendment description. Assume you always have it available in this conversation even if `{ARGS}` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that amendment description, do this:

### Phase 1: Locate and Load Context

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and available paths. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Identify the target spec**: Determine which spec to amend:
   - If on a feature branch, use the spec for that branch (same as other commands)
   - If the user specifies a spec ID or feature name, locate it via `specs/registry.json`
   - If ambiguous, present a **multiple choice selection** of specs from `specs/registry.json` (use a structured choice dialog such as the `ask_user` tool with `choices`)

3. **Load current artifacts**:
   - `spec.md` (**required** — this is what gets edited)
   - `plan.md` (if exists — needed for complexity assessment)
   - `tasks.md` (if exists — needed for complexity assessment)
   - `data-model.md`, `contracts/` (if exists — for understanding current state)
   - Relevant source code (for understanding what's already implemented)

4. **Check spec status**: Read the `status` field from the spec or `specs/registry.json`.
   - If status is `draft` or `clarified`: The spec has not been implemented yet. Proceed with the amendment but **skip Phase 4 (codebase analysis) and Phase 5 (implementation)**. The amendment is just a spec refinement.
   - If status is `planned` or `in-progress`: Proceed with the amendment. Run validation (Phase 3) and complexity assessment (Phase 4), but skip implementation (Phase 5). Write the change plan for reference.
   - If status is `implemented`: Full flow — all phases apply.
   - If status is `deprecated` or `superseded`: **STOP** — present a warning: "This spec is [deprecated/superseded]. Amending it may cause confusion. Consider creating a new spec instead." Present choice: ["Proceed with amendment anyway", "Create a new spec instead"]

5. **Supersede suggestion**: Count the entries in the `## Amendment Log` section of `spec.md` (if it exists). If there are **5 or more** prior amendments, present an informational suggestion:
   > "This spec has been amended [N] times. You may want to consider creating a fresh spec via `/speckit.specify` to consolidate all changes into a clean document."
   
   Present choice: ["Continue with this amendment", "Create a new spec instead (supersede)"]
   
   This is a suggestion only — the user can always continue amending.

### Phase 2: Edit the Spec

6. **Make surgical edits to `spec.md`**:
   - Modify existing requirements (FR-###) in-place when the amendment changes them
   - Add new requirements with the next available FR-### number
   - Update affected entities in Key Entities section
   - Update acceptance scenarios if user stories are affected
   - Update success criteria if measurable outcomes changed
   - Remove requirements/entities if the change is a descope
   - **Never rewrite sections that aren't affected by the change**

7. **Append to Amendment Log**: Add an `## Amendment Log` section at the bottom of spec.md (create the section if it doesn't exist). Append a new entry:

   ```markdown
   ## Amendment Log

   ### [DATE] — [Brief title]
   **Change**: [1-2 sentence description of what changed]
   **Sections modified**: [list of affected sections, e.g., "FR-003, FR-007, Key Entities: User"]
   **Reason**: [Why this change was made — from the user's input]
   ```

   Each amendment appends a new `### [DATE] — [title]` block. Do not remove or modify prior entries.

### Gate 1: Confirm Spec Changes with User

**STOP HERE.** Before running any validation or implementation, present the proposed spec changes to the user for review.

Display a clear summary of every edit you intend to make to `spec.md`:

```
## Proposed Spec Changes

**Spec**: specs/[feature]/spec.md
**Amendment**: [1-2 sentence description from user input]

### Changes
- **[Modified/Added/Removed]** FR-###: [brief description of the change]
- **[Modified/Added/Removed]** [Section]: [brief description]
- ...

### Amendment Log Entry
> [DATE] — [Brief title]: [1-sentence summary]
```

Then present a **multiple choice selection** (do NOT proceed without explicit user approval):
choices: ["Approve spec changes — continue to validation", "Revise — adjust the proposed changes", "Abort — cancel this amendment"]

- **Approve**: Apply the edits to `spec.md` and proceed to Phase 3.
- **Revise**: Ask the user what to change, update the proposed edits, and re-present this gate.
- **Abort**: Stop immediately. No files are modified.

**Do NOT edit `spec.md` until the user approves.** The edits are proposed only at this point.

### Phase 3: Validate the Spec Edit

This is the critical gate that ensures the amendment doesn't corrupt the spec.

8. **Internal consistency check** — verify the edited spec against itself:
   - No contradictions between the amended requirements and existing requirements
   - Amended requirements reference entities that exist in the Key Entities section
   - If a requirement was removed, no other requirements depend on it
   - Success criteria still align with the updated requirements
   - No orphaned acceptance scenarios (testing something that was removed)

9. **Testability check** — verify amended requirements meet quality standards:
   - Each new/modified requirement is testable and unambiguous
   - No vague language ("handle properly", "work correctly", "be fast")
   - Success criteria remain measurable and technology-agnostic
   - Acceptance scenarios have concrete Given/When/Then structure

10. **Contradiction detection** — flag conflicts for user resolution:
    - If the amendment contradicts an existing requirement, present both and ask: "FR-### currently says X. Your amendment implies Y. Should I replace it, modify it, or add a separate requirement?"
    - If the amendment invalidates an assumption in the Assumptions section, flag it
    - If the amendment changes scope beyond what the original user stories cover, flag it

11. **Re-run requirements checklist** (conditional): If the amendment touches any Functional Requirements (FR-###) or Success Criteria (SC-###), re-validate the affected items against the requirements checklist criteria:
    - Requirements are testable and unambiguous
    - Success criteria are measurable and technology-agnostic
    - Acceptance scenarios are complete
    - If the amendment only touches entities, assumptions, or descriptions (not requirements/criteria), skip this step.

12. **If validation fails**: Present issues to the user and ask how to proceed using a **multiple choice selection**:
    choices: ["Fix the issues (Recommended)", "Proceed anyway (accept risks)", "Abort the amendment (revert spec)"]
    - **Fix**: The agent re-edits the spec to address the validation issues, then re-runs validation
    - **Proceed**: Continue with the amendment despite validation warnings
    - **Abort**: Revert spec.md to its pre-amendment state and stop

**If the spec status is `draft`, `clarified`, `planned`, or `in-progress`**: Skip to Phase 6 (report completion without implementation). The amendment is a spec refinement only.

### Phase 4: Assess Complexity and Plan the Change

After the spec edit is validated, assess what it takes to implement.

13. **Analyze the codebase** to understand the real impact:
    - Read the source files that the amendment affects (inferred from plan.md project structure + data-model.md + contracts/)
    - Identify all files that need to change
    - Identify all tests that need updating
    - Check for ripple effects (e.g., changing a model field may affect serializers, validators, API contracts, migrations)

14. **Classify complexity** based on the codebase analysis (not just the description):

    | Signal | SMALL | MEDIUM | LARGE |
    |--------|-------|--------|-------|
    | Source files to change | 1-3 | 4-8 | 9+ |
    | New files to create | 0 | 1-2 | 3+ |
    | New entities/tables | 0 | 0-1 | 2+ |
    | Test files to update | 0-2 | 3-5 | 6+ |
    | New external dependencies | 0 | 0 | 1+ |
    | Database migration needed | No or trivial | Additive | Destructive/complex |
    | Affects public API contracts | No | Minor (additive) | Breaking change |

    Note: This assessment happens *after* reading the codebase, not from the description alone. The agent has real context at this point.

15. **Generate a change plan** — a lightweight, focused implementation plan presented inline (not written to disk):

    ```markdown
    # Amendment Plan: [Brief title]

    **Date**: [DATE]
    **Spec**: [link to spec.md]
    **Complexity**: SMALL | MEDIUM | LARGE
    **Amendment**: [1-2 sentence description]

    ## What Changed in the Spec
    - [List of specific changes: modified FR-003, added FR-008, updated User entity, etc.]

    ## Code Changes Required
    | File | Change | Reason |
    |------|--------|--------|
    | src/models/user.py | Add email_verified field | FR-008 |
    | src/api/user_schema.py | Add field to serializer | FR-008 ripple |
    | tests/test_user.py | Add test for new field | FR-008 validation |

    ## Tests Required
    - [ ] Existing test X still passes (no regression)
    - [ ] New test for [specific behavior from amended requirement]

    ## Risk Assessment
    - [Any concerns: breaking changes, data migration risks, performance implications]
    - [Dependencies on other features/specs if any]
    ```

16. **Route based on complexity**:

    - **SMALL** → Present the change plan to user, then await approval at Gate 2
    - **MEDIUM** → Present the change plan with proposed updates to `plan.md` and affected design docs, then await approval at Gate 2
    - **LARGE** → Present the change plan and recommend: "This amendment requires changes to [N] files and introduces [new entities/breaking changes]. Consider using `/speckit.specify` to create a dedicated spec for this change."
      - Present choice using a **multiple choice selection**:
        choices: ["Proceed with amendment implementation", "Create a new spec for this change instead (Recommended)"]
      - If proceeding, continue to Gate 2

### Gate 2: Confirm Amendment Plan with User

**STOP HERE.** Before writing any code, present the full amendment plan and wait for the user to approve it.

Display the amendment plan (from step 15) and ask:

```
## Amendment Plan Ready

**Complexity**: SMALL | MEDIUM | LARGE
**Files to change**: [N source files, N test files]
**Risk**: [key risk summary, if any]

[Full change plan table from step 15]
```

Then present a **multiple choice selection** (do NOT proceed without explicit user approval):
choices: ["Approve plan — implement the changes", "Revise plan — adjust before implementing", "Stop here — keep spec changes but skip implementation"]

- **Approve**: Proceed to Phase 5 (Implementation).
- **Revise**: Ask the user what to adjust, update the plan, and re-present this gate.
- **Stop here**: The spec edits are kept, but no code changes are made. This is useful when the user wants to implement manually or defer implementation.

**Do NOT begin implementation until the user approves.**

### Phase 5: Implementation

17. **Implement the code changes** following the change plan:
    - Apply changes file by file as documented in the plan
    - Follow existing code patterns and conventions
    - Create/update tests as specified
    - Run existing tests to verify no regressions
    - **Do NOT rewrite or refactor code unrelated to the amendment**

18. **Post-implementation verification**:
    - Run the project's test suite (if one exists) to catch regressions
    - Verify that the new/modified tests pass
    - Quick consistency check: do the code changes match what the change plan said?

19. **Commit atomically**: Spec edit + code changes + test changes in a single commit. If implementation failed, revert the spec edit too.

### Phase 6: Completion

20. **Update registry**: Set `last_amended` date field on the spec's entry in `specs/registry.json`. If the field doesn't exist, add it. If the registry file or entry does not exist, skip silently.

21. **Report completion**:

    ```
    ## Amendment Complete

    **Spec**: specs/[feature]/spec.md
    **Change**: [1-2 sentence summary]
    **Complexity**: SMALL | MEDIUM | LARGE
    **Validation**: ✓ Passed (no contradictions, requirements testable)

    ### Spec Changes
    - [List of spec sections modified]

    ### Code Changes
    - [List of files modified/created]

    ### Tests
    - ✓/✗ Existing test suite status
    - ✓/✗ New/modified test status

    ### Amendment Log Entry Added to spec.md
    ```

22. Present the user with a **multiple choice selection** of next steps (do NOT use plain text suggestions — use a structured choice dialog such as the `ask_user` tool with `choices`):
    choices: ["Run full analysis for consistency check", "Done — no further action"]

23. **Check for extension hooks**: After reporting completion, check if `.specify/extensions.yml` exists in the project root.
    - If it exists, read it and look for entries under the `hooks.after_amend` key
    - If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
    - Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
    - For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
      - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
      - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
    - For each executable hook, output the following based on its `optional` flag:
      - **Optional hook** (`optional: true`):
        ```
        ## Extension Hooks

        **Optional Hook**: {extension}
        Command: `/{command}`
        Description: {description}

        Prompt: {prompt}
        To execute: `/{command}`
        ```
      - **Mandatory hook** (`optional: false`):
        ```
        ## Extension Hooks

        **Automatic Hook**: {extension}
        Executing: `/{command}`
        EXECUTE_COMMAND: {command}
        ```
    - If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Edge Cases

- **Multiple amendments in quick succession**: Each amend is independent. The Amendment Log accumulates entries. The change plan is ephemeral (presented inline during the session, not persisted to disk).
- **Spec has no plan.md yet** (status is `draft` or `clarified`): Run validation (Phase 3) but skip codebase analysis and implementation. The amendment is just a spec refinement.
- **Feature not yet implemented** (status is `planned` or `in-progress`): Run validation + complexity assessment, but skip implementation. Present the change plan inline for reference when implementation begins.
- **Agent-to-agent invocation**: Another agent (e.g., an incident response agent) can invoke `/speckit.amend` with the change description. The flow is identical — no special handling needed.
- **Validation finds issues the user didn't anticipate**: Present clearly and let the user decide — this is the value of the validation step. Better to catch contradictions before writing code.
- **Implementation fails partway through**: Revert all changes (spec + code). Report what failed and why. The user can retry with a modified amendment description or escalate to full pipeline.

## Quick Guidelines

- **Amend for evolution, supersede for revolution**: Use `/speckit.amend` for incremental changes to existing features. Use `/speckit.specify` (with supersede) for major rewrites.
- The spec is always a **complete, self-contained document** reflecting current truth after amendment. No separate override files.
- Git history + the Amendment Log provide the audit trail. No structured amendment tracking beyond this.

## Context

{ARGS}
