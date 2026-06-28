---
description: "Show cross-project feature status across all linked specs"
---

# Coordinate Status — Cross-Project Feature Progress

Display the current status of all coordinated (cross-project) features by reading
coordination records and checking each linked spec's registry status.

## User Input

```text
$ARGUMENTS
```

If the user provides a feature name or date prefix, filter to that coordination.
If empty, show all active coordinations.

## Prerequisites

1. **Discover projects**: Scan the repository for all `.specify/` directories
   (same discovery logic as `/speckit.coordinate.specify`). Build the project
   name → path mapping.
2. **Check coordination records**: Look for files under `specs/coordinations/`.
   If the directory doesn't exist or is empty:
   ```
   ℹ No cross-project coordinations found. Use /speckit.coordinate.specify to create one.
   ```

## Execution Flow

### 1. Load coordination records

Read all `*.md` files from `specs/coordinations/`. Parse each to extract:
- Feature name (from `# Coordination:` heading)
- Linked specs table (project, spec ID, path)
- Overall status

### 2. Check current status of each linked spec

For each linked spec in a coordination:
1. Resolve the project path from the discovered project list
2. Read that project's `specs/registry.json`
3. Find the spec entry by ID
4. Extract its current `status`

If a project's registry is missing or the spec ID isn't found, mark as `unknown`.

### 3. Determine coordination status

A coordination's overall status is determined by its linked specs:
- **All draft**: `Not Started`
- **Any in-progress**: `In Progress`
- **All implemented**: `Complete`
- **Mixed (some implemented, some not)**: `Partially Complete`
- **Any blocked**: `Blocked`

### 4. Display results

**Single coordination** (filtered):

```
## Coordination: [Feature Name]

**Overall Status**: In Progress
**Created**: 2026-06-28

| # | Project | Spec ID | Status | Dependencies Met? |
|---|---------|---------|--------|-------------------|
| 1 | api | 20260628-user-preferences-endpoint | implemented | ✓ (none) |
| 2 | web | 20260628-consume-preferences-ui | in-progress | ✓ (api complete) |

### Ready to Implement

- **web**: 20260628-consume-preferences-ui — all dependencies satisfied

### Blocked

(none)
```

**All coordinations** (summary):

```
## Active Coordinations

| Feature | Status | Progress | Created |
|---------|--------|----------|---------|
| User Preferences Display | In Progress | 1/2 complete | 2026-06-28 |
| Auth Token Refresh | Not Started | 0/3 complete | 2026-06-25 |
| Shared Logger Migration | Complete | 3/3 complete | 2026-06-20 |

Use `/speckit.coordinate.status <feature-name>` for details.
```

## Staleness Detection

If a coordination has specs stuck in `draft` or `planned` for more than 14 days,
flag it:

```
⚠ Stale: "Auth Token Refresh" — 3 specs in draft since 2026-06-25 (3 days ago)
```

## Next Step Suggestions

Based on the current state, suggest the logical next action:
- If all specs are `draft`: "Run `/speckit.plan` in **<first-project>** to begin planning"
- If some are `planned`: "Run `/speckit.implement` in **<next-project>** (dependencies satisfied)"
- If all are `implemented`: "✓ All specs implemented. Consider archiving this coordination."
