## Additional Analysis Checks

### Registry Consistency

If `specs/registry.json` exists, verify:

- Current feature has an entry in the registry
- Registry `status` matches spec.md `**Status**:` field (case-insensitive)
- Registry `tags` array is non-empty
- Registry `summary` is non-empty
- Registry `relationships.depends_on` IDs reference existing registry entries
- No orphaned registry entries (entries with no matching `specs/` directory)
- No unregistered spec directories (directories in `specs/` with no registry entry, excluding `registry.json` and `registry.schema.json`)
- If a registry entry has `last_amended` set, verify the spec's `## Amendment Log` section exists and contains at least one entry

### Post-Amendment Drift

If the spec has been amended (indicated by `last_amended` in the registry or an `## Amendment Log` section in spec.md):

- Check if `plan.md` or `tasks.md` were generated **before** the last amendment date
- If plan/tasks pre-date the amendment, this is **expected drift** — report as **INFO**, not CRITICAL or HIGH:
  - "Spec was amended on [date] but plan.md was last generated on [date]. This is expected after an amendment — plan.md reflects the original plan, not the amended spec."
- Check that the Amendment Log entries reference sections that actually exist in the spec (e.g., if an entry says "FR-008 added" then FR-008 should exist)
- Flag any Amendment Log entries that reference removed sections without corresponding spec changes

### Additional Severity Level

- **INFO**: Expected post-amendment drift (plan/tasks pre-date a spec amendment). These are informational — they indicate the spec was intentionally amended and plan/tasks have not been regenerated, which is normal for small/medium amendments.

### Enhanced Next Actions

At end of report, present the user with a **multiple choice selection** of next actions (do NOT use plain text suggestions — use a structured choice dialog such as the `ask_user` tool with `choices`).

Build the choices dynamically based on findings:

- **If CRITICAL issues exist**, present choices like:
  choices: ["Fix critical issues before implementing (Recommended)", "Refine the spec", "Adjust the plan", "Proceed to implementation anyway"]
- **If only LOW/MEDIUM issues**, present choices like:
  choices: ["Start implementing (Recommended)", "Suggest remediation edits for top issues", "Refine the spec", "Adjust the plan"]
- **If no issues found**, present choices like:
  choices: ["Start implementing (Recommended)", "Review the analysis report again"]

If the user selects remediation from the choices above, suggest concrete remediation edits for the top N issues. (Do NOT apply them automatically.)
