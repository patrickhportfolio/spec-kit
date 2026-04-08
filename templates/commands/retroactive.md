---
description: Build specification artifacts for an existing feature by analyzing the current codebase.
handoffs: 
  - label: Clarify Spec Gaps
    agent: speckit.clarify
    prompt: Clarify specification gaps identified during retroactive analysis
    send: true
scripts:
  sh: scripts/bash/create-new-feature.sh "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 "{ARGS}"
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before retroactive specification)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_retroactive` key
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

## Outline

The text the user typed after `/speckit.retroactive` in the triggering message **is** the feature description. This describes an **existing** feature already implemented in the codebase. Assume you always have it available in this conversation even if `{ARGS}` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that feature description, do this:

### Phase 0: Setup

1. **Generate a concise short name** (2-4 words) for the branch:
   - Analyze the feature description and extract the most meaningful keywords
   - Create a 2-4 word short name that captures the essence of the feature
   - Use noun format when possible (e.g., "user-auth", "payment-processing", "search-api")
   - Preserve technical terms and acronyms (OAuth2, API, JWT, etc.)
   - Keep it concise but descriptive enough to understand the feature at a glance

2. **Create the feature branch** by running the script with `--short-name` (and `--json`). In sequential mode, do NOT pass `--number` — the script auto-detects the next available number. In timestamp mode, the script generates a `YYYYMMDD-HHMMSS` prefix automatically:

   **Branch numbering mode**: Before running the script, check if `.specify/init-options.json` exists and read the `branch_numbering` value.
   - If `"timestamp"`, add `--timestamp` (Bash) or `-Timestamp` (PowerShell) to the script invocation
   - If `"sequential"` or absent, do not add any extra flag (default behavior)

   - Bash example: `{SCRIPT} --json --short-name "user-auth" "Retroactive: User authentication system"`
   - Bash (timestamp): `{SCRIPT} --json --timestamp --short-name "user-auth" "Retroactive: User authentication system"`
   - PowerShell example: `{SCRIPT} -Json -ShortName "user-auth" "Retroactive: User authentication system"`
   - PowerShell (timestamp): `{SCRIPT} -Json -Timestamp -ShortName "user-auth" "Retroactive: User authentication system"`

   **IMPORTANT**:
   - Do NOT pass `--number` — the script determines the correct next number automatically
   - Always include the JSON flag (`--json` for Bash, `-Json` for PowerShell) so the output can be parsed reliably
   - You must only ever run this script once per feature
   - The JSON is provided in the terminal as output - always refer to it to get the actual content you're looking for
   - The JSON output will contain BRANCH_NAME and SPEC_FILE paths
   - For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot")

### Phase 1: Codebase Analysis

3. **Analyze the existing codebase** to find all code related to the described feature:

   a. **Search for relevant files**: Use the feature description to identify keywords, module names, class names, function names, and API endpoints. Search across:
      - Source files (models, services, controllers, handlers, utilities)
      - Test files (unit tests, integration tests, contract tests)
      - Configuration files (environment configs, database schemas, migration files)
      - Documentation (README, inline docs, API docs)
      - Infrastructure (Dockerfiles, CI/CD configs, deployment scripts)

   b. **Read and analyze discovered files**: For each relevant file:
      - Identify its role in the feature (model, service, controller, utility, test, etc.)
      - Extract key entities, data structures, and relationships
      - Note API contracts, endpoints, and interfaces
      - Identify dependencies on other modules or external services
      - Capture error handling patterns, validation rules, and edge cases

   c. **Build a feature map**: Create a mental model of:
      - **Entities & Data Model**: What data structures exist, their fields, relationships, and constraints
      - **Business Logic**: What operations/services process the data, business rules, validation
      - **Interfaces**: API endpoints, CLI commands, UI components, message handlers
      - **Dependencies**: External services, libraries, databases the feature relies on
      - **Test Coverage**: What tests exist, what they cover, what gaps remain
      - **Configuration**: Environment variables, feature flags, settings

   d. **Identify gaps**: Note areas where:
      - Code behavior is unclear or undocumented
      - Multiple code paths exist with ambiguous intent
      - Tests are missing for important scenarios
      - Configuration is complex or environment-dependent
      - Mark these as `[NEEDS CLARIFICATION: specific question]` (max 3)

### Phase 2: Generate spec.md

4. Load `templates/spec-template.md` to understand required sections.

5. **Write the specification to SPEC_FILE** by reverse-engineering from the analyzed code:

   a. **User Scenarios & Testing**: Derive user stories from:
      - Existing test cases (test names → user journeys)
      - API endpoint patterns (REST routes → user workflows)
      - UI flows or CLI commands (entry points → user interactions)
      - Each user story must be prioritized (P1, P2, P3) based on:
        - Centrality to the feature (how many other components depend on it)
        - Usage frequency (if metrics/logs available, otherwise infer from code)
        - Complexity of the implementation
      - Write acceptance scenarios in Given/When/Then format, derived from existing test assertions

   b. **Functional Requirements**: Extract from code:
      - Validation rules → MUST constraints
      - Authorization checks → access control requirements
      - Data processing logic → behavioral requirements
      - Error handling → failure mode requirements
      - Each requirement (FR-###) must be traceable to specific source files

   c. **Key Entities**: Extract from data models:
      - Database models/schemas → entity definitions
      - ORM classes → field lists and relationships
      - Data transfer objects → API contract entities
      - Describe relationships without implementation details

   d. **Success Criteria**: Derive measurable outcomes from:
      - Existing performance tests or benchmarks → performance criteria
      - Test assertions → functional success criteria
      - Monitoring/alerting thresholds → operational criteria
      - Keep technology-agnostic (describe user outcomes, not system metrics)

   e. **Assumptions**: Document:
      - Inferred design decisions not explicitly documented in code
      - Dependencies on external services discovered during analysis
      - Scope boundaries (what the feature does NOT do)

6. **Specification Quality Validation**: After writing the spec, validate it:

   a. **Create Spec Quality Checklist** at `FEATURE_DIR/checklists/requirements.md`:

      ```markdown
      # Specification Quality Checklist: [FEATURE NAME] (Retroactive)

      **Purpose**: Validate retroactive specification completeness and accuracy
      **Created**: [DATE]
      **Feature**: [Link to spec.md]
      **Source**: Retroactive analysis of existing codebase

      ## Accuracy (Retroactive-Specific)

      - [ ] Spec accurately reflects current code behavior
      - [ ] No requirements describe behavior that doesn't exist in code
      - [ ] All major code paths are captured in user stories
      - [ ] Entity descriptions match actual data models

      ## Content Quality

      - [ ] No implementation details (languages, frameworks, APIs)
      - [ ] Focused on user value and business needs
      - [ ] Written for non-technical stakeholders
      - [ ] All mandatory sections completed

      ## Requirement Completeness

      - [ ] Requirements are testable and unambiguous
      - [ ] Success criteria are measurable
      - [ ] Success criteria are technology-agnostic
      - [ ] Edge cases are identified
      - [ ] Scope is clearly bounded
      - [ ] Dependencies and assumptions identified

      ## Coverage Gaps

      - [ ] Undocumented code paths are flagged
      - [ ] Missing test coverage areas are noted
      - [ ] Ambiguous behavior is marked with [NEEDS CLARIFICATION]

      ## Notes

      - This spec was generated retroactively from existing code
      - Items marked incomplete may indicate spec-code gaps requiring `/speckit.clarify`
      ```

   b. **Run Validation**: Review spec against each checklist item. Handle results same as `/speckit.specify`:
      - If all pass: proceed to Phase 3
      - If items fail: fix and re-validate (max 3 iterations)
      - If `[NEEDS CLARIFICATION]` markers remain (max 3): present to user with options table

### Phase 3: Generate plan.md

7. Load `templates/plan-template.md` to understand required sections.

8. **Generate the implementation plan** at `FEATURE_DIR/plan.md` by documenting the **actual** architecture:

   a. **Summary**: One paragraph describing what the feature does and how it was built.

   b. **Technical Context**: Fill from actual codebase analysis (not hypothetical):
      - **Language/Version**: Detected from project files (package.json, pyproject.toml, go.mod, Cargo.toml, etc.)
      - **Primary Dependencies**: Extracted from dependency manifests
      - **Storage**: Identified from database drivers, ORM configs, file I/O patterns
      - **Testing**: Detected from test framework imports and test runner configs
      - **Target Platform**: Inferred from deployment configs, CI/CD, Dockerfiles
      - **Project Type**: Classified from project structure (library, CLI, web-service, etc.)
      - **Performance Goals**: Extracted from benchmarks, load tests, or SLA configs (if available)
      - **Constraints**: Identified from resource limits, timeouts, rate limiting configs

   c. **Constitution Check**: If `.specify/memory/constitution.md` exists, evaluate the existing implementation against the project's principles. Note any violations.

   d. **Project Structure**: Document the **actual** source code layout (not a template). Show the real directory tree for files related to this feature.

   e. **Research & Design Artifacts**: Generate supporting files:
      - `research.md`: Document key technical decisions visible in the code (library choices, architecture patterns, trade-offs)
      - `data-model.md`: Extract entity definitions, field types, relationships, and constraints from actual models
      - `contracts/`: Extract API contracts from route definitions, request/response schemas, CLI argument parsers, or interface definitions
      - `quickstart.md`: Document how to run/test the feature based on existing scripts, configs, and README content

9. **Update agent context** by running `{AGENT_SCRIPT}` to add technologies from the plan.

### Phase 4: Generate tasks.md

10. Load `templates/tasks-template.md` to understand required format.

11. **Generate the task list** at `FEATURE_DIR/tasks.md` describing what was **already built**:

    **CRITICAL**: ALL tasks must be marked as completed with `[X]` since this is retroactive documentation of existing work.

    a. **Phase 1: Setup** — Document project initialization that was done:
       - Project structure creation
       - Dependency installation
       - Configuration setup

    b. **Phase 2: Foundational** — Document infrastructure that was built:
       - Database setup, migrations
       - Authentication/authorization framework
       - Core middleware, routing
       - Logging, error handling infrastructure

    c. **Phase 3+: User Stories** — One phase per user story (matching spec.md priorities):
       - Map each implemented component to its user story
       - Include tests if they exist (mark `[X]`)
       - Include models, services, endpoints, integrations
       - Each story phase should show what was built for that story

    d. **Final Phase: Polish** — Cross-cutting work that was done:
       - Documentation, code cleanup
       - Performance optimization
       - Security hardening

    e. **Task format** (all completed):
       ```text
       - [X] T001 [P] [US1] Description with actual file path
       ```

    f. **Dependencies section**: Document the actual dependency order of what was built.

    g. **Implementation Strategy**: Note "Retroactive — all tasks completed" and document the actual implementation approach used.

### Phase 5: Registry & Completion

12. **Update spec registry**: Update the feature's entry in `specs/registry.json`:
    - Set `title` and `summary` from the generated spec
    - Set `status` to `"retroactive"`
    - If the registry file or entry is missing, create/add it

13. **Report completion** with:

    ```markdown
    ## Retroactive Specification Complete

    **Branch**: `[branch-name]`
    **Feature Directory**: `[FEATURE_DIR]`

    ### Generated Artifacts
    | Artifact | Path | Status |
    |----------|------|--------|
    | Specification | spec.md | ✓ Generated |
    | Quality Checklist | checklists/requirements.md | ✓ Generated |
    | Implementation Plan | plan.md | ✓ Generated |
    | Research Notes | research.md | ✓ Generated |
    | Data Model | data-model.md | ✓ Generated (if entities found) |
    | API Contracts | contracts/ | ✓ Generated (if interfaces found) |
    | Quickstart Guide | quickstart.md | ✓ Generated |
    | Task List | tasks.md | ✓ Generated (all tasks marked complete) |

    ### Coverage Summary
    - **Files analyzed**: [count]
    - **User stories identified**: [count]
    - **Requirements extracted**: [count]
    - **Tasks documented**: [count] (all complete)
    - **Gaps identified**: [count] (see [NEEDS CLARIFICATION] markers)

    ### Registry Status
    - Status set to `"retroactive"` — this spec was reverse-engineered from existing code
    - Use `/speckit.clarify` to fill specification gaps

    ### Recommended Next Step
    Run `/speckit.clarify` to address any [NEEDS CLARIFICATION] markers and refine the specification.
    ```

14. **Check for extension hooks**: After reporting completion, check if `.specify/extensions.yml` exists in the project root.
    - If it exists, read it and look for entries under the `hooks.after_retroactive` key
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

**NOTE:** The script creates and checks out the new branch and initializes the spec file before writing.

## Quick Guidelines

- This command analyzes **existing code** to build specification artifacts retroactively
- Focus on accurately capturing **WHAT** the feature does and **WHY**, derived from the code
- Avoid copying implementation details verbatim — translate code into business requirements
- Written for business stakeholders, not developers (same principle as forward specs)
- The plan.md documents **actual** architecture, not aspirational design
- ALL tasks in tasks.md are marked `[X]` — they describe completed work
- Use `[NEEDS CLARIFICATION]` markers (max 3) for code behavior that is ambiguous or undocumented
- DO NOT create any checklists that are embedded in the spec. That will be a separate command.

### Section Requirements

- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Analysis

When creating this spec from existing code:

1. **Read the code thoroughly**: Don't guess when you can read the source
2. **Trace data flows**: Follow data from entry points through processing to storage/output
3. **Map tests to behavior**: Test names and assertions reveal intended behavior
4. **Check git history**: Recent commits may reveal intent and design decisions
5. **Document unknowns honestly**: Use `[NEEDS CLARIFICATION]` for genuinely ambiguous code (max 3)
6. **Prioritize by centrality**: P1 stories are the core purpose; P2/P3 are supporting features
7. **Think like a product owner**: Translate implementation into user value

### Success Criteria Guidelines

Success criteria must be:

1. **Measurable**: Include specific metrics (time, percentage, count, rate)
2. **Technology-agnostic**: No mention of frameworks, languages, databases, or tools
3. **User-focused**: Describe outcomes from user/business perspective, not system internals
4. **Verifiable**: Can be tested/validated without knowing implementation details
5. **Grounded in reality**: Derived from actual behavior, tests, or metrics — not aspirational
