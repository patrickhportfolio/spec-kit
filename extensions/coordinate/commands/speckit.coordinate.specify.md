---
description: "Decompose a cross-project feature into linked per-project specs with dependency ordering"
---

# Coordinate Specify — Cross-Project Feature Fan-Out

Decompose a single feature description into multiple per-project specs, wire up
`relationships.depends_on` between them, and report the implementation order.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Prerequisites — Dynamic Project Discovery

Discover all Spec Kit projects in this repository by scanning for `.specify/`
directories:

1. Find the Git repository root (`git rev-parse --show-toplevel`).
2. Recursively find all directories containing a `.specify/` subdirectory.
3. **Exclude the repository root itself** — that is the coordination host, not a
   member project.
4. Derive each project's **name** from its directory path:
   - Use the immediate directory name (e.g., `apps/api` → `api`)
   - If names collide (e.g., `apps/api` and `services/api`), disambiguate by
     prepending the parent: `apps-api` vs `services-api`
5. Build the project list:

   | Name | Path |
   |------|------|
   | api  | apps/api |
   | web  | apps/web |
   | shared | packages/shared |

If no member projects are found (only the root `.specify/` exists), error:
```
ERROR: No member projects found. Each project needs its own .specify/ directory.
Initialize projects with: specify init <path> --integration <agent>
```

## Execution Flow

### 1. Parse the feature description

Extract the cross-cutting feature intent from the user's input. Identify:
- What the overall feature delivers (user value)
- Which discovered projects are likely affected
- What each project's role is in delivering the feature

### 2. Identify affected projects

Present the user with the discovered projects and ask which are involved.
If the feature description makes it obvious (e.g., "add an API endpoint and
consume it in the web app"), you may pre-select and confirm:

```
## Affected Projects

Based on your description, this feature involves:

| Project | Path | Role |
|---------|------|------|
| api     | apps/api | Provide the new endpoint |
| web     | apps/web | Consume the endpoint and display data |

Is this correct? Should any other projects be included?
```

Wait for user confirmation before proceeding.

### 3. Determine dependency order

For the affected projects, determine which specs depend on which:
- A consumer depends on its provider (web depends on api)
- Shared libraries that both use are implemented first
- If no clear dependency exists, specs are independent (parallel)

Present the proposed order:

```
## Implementation Order

1. **api** — `20260628-user-preferences-endpoint` (no dependencies)
2. **web** — `20260628-consume-preferences` (depends on: api:20260628-user-preferences-endpoint)
```

### 4. Generate per-project short names

For each affected project, generate a concise short name (2-4 words) scoped to
that project's concern:
- Use the same date prefix across all linked specs (ensuring they share the same
  date)
- The short name should describe what THIS project does, not the whole feature
- Examples:
  - API project: `user-preferences-endpoint`
  - Web project: `consume-preferences-ui`
  - Shared project: `preferences-types`

### 5. Create specs in each project

For each project in dependency order:

1. Set `SPECIFY_INIT_DIR` to the project path
2. Invoke the project's `/speckit.specify` command (or equivalent) with a
   **scoped description** that:
   - Describes only this project's piece of the feature
   - References the other project specs it depends on or enables
   - Includes enough context for the spec to be self-contained and independently
     implementable

   **Scoped description format**:
   ```
   [Feature piece for this project].

   Context: This is part of a cross-project feature "<overall feature description>".
   - This project's role: [what this project provides/consumes]
   - Depends on: [list of specs this depends on, if any]
   - Enables: [list of specs that depend on this, if any]
   ```

3. After each spec is created, note the resulting `SPECIFY_FEATURE_DIRECTORY`
   and spec ID.

### 6. Wire up cross-project relationships

After all specs are created, update each project's `specs/registry.json` to add
cross-project references using qualified IDs (`<project-name>:<spec-id>`):

```json
{
  "id": "20260628-consume-preferences-ui",
  "relationships": {
    "depends_on": ["api:20260628-user-preferences-endpoint"],
    "related_to": ["shared:20260628-preferences-types"]
  }
}
```

**Qualified ID format**: `<project-name>:<spec-id>` where:
- `<project-name>` is the derived name from dynamic discovery
- `<spec-id>` is the spec's `id` in that project's registry

For specs with no cross-project dependencies, use `related_to` to link them
to the other specs in the coordination group.

### 7. Create coordination record

Create a coordination record file at the ROOT project's specs directory:
`specs/coordinations/<date>-<short-feature-name>.md`

```markdown
# Coordination: [Feature Name]

**Created**: [DATE]
**Status**: In Progress

## Overview

[One-paragraph description of the cross-project feature]

## Linked Specs

| Project | Spec ID | Path | Status |
|---------|---------|------|--------|
| api | 20260628-user-preferences-endpoint | apps/api/specs/20260628-user-preferences-endpoint/ | draft |
| web | 20260628-consume-preferences-ui | apps/web/specs/20260628-consume-preferences-ui/ | draft |

## Implementation Order

1. **api**: 20260628-user-preferences-endpoint (no dependencies)
2. **web**: 20260628-consume-preferences-ui (depends on: api:20260628-user-preferences-endpoint)

## Notes

- Each spec is independently implementable within its project
- Implementation should follow the dependency order above
- Use `/speckit.coordinate.status` to check progress across all linked specs
```

## Completion Report

Report to the user:

```
## Cross-Project Feature Created ✓

**Feature**: [overall feature name]
**Coordination record**: specs/coordinations/<filename>.md

### Specs Created

| # | Project | Spec | Dependencies |
|---|---------|------|--------------|
| 1 | api | specs/20260628-user-preferences-endpoint/ | — |
| 2 | web | specs/20260628-consume-preferences-ui/ | api:20260628-user-preferences-endpoint |

### Next Steps

- Implement specs in order (api → web)
- Run `/speckit.plan` in each project directory to create implementation plans
- Use `/speckit.coordinate.status` to track progress across projects
```

## Error Handling

- If a project's `/speckit.specify` fails, report the error but continue with
  remaining projects
- If registry update fails for a project, warn but don't fail the entire
  coordination
- If only one project is affected, suggest using the standard `/speckit.specify`
  instead:
  ```
  ℹ Only one project affected. Use /speckit.specify directly in that project instead.
  ```

## Edge Cases

- **Same-project dependencies**: If two specs within the same project have a
  dependency, use the unqualified ID (no project prefix)
- **Circular dependencies**: Error if the dependency graph has cycles. Ask user
  to restructure.
- **Nested .specify/ directories**: Only top-level project `.specify/` dirs are
  discovered. A `.specify/` inside another project's subtree is ignored.
