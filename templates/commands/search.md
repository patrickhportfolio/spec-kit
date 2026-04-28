---
description: Search and discover feature specs using the spec registry. Query by keyword, status, tag, or relationship. Detect duplicates before creating new specs.
handoffs:
  - label: View or Clarify Spec
    agent: speckit.clarify
    prompt: Clarify specification requirements for the selected spec
  - label: Create New Spec
    agent: speckit.specify
    prompt: Create a new feature spec
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --paths-only
  ps: scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
---

# Search Workflow

Query the spec registry to discover, filter, and inspect feature specs
without reading individual spec files.

## Execution Flow

1. **Load registry**: Read `specs/registry.json` from the repo root.
   If the file does not exist, report "No registry found — run
   the specify command to create specs, or manually create
   `specs/registry.json`." and stop.

2. **Parse user query** into one or more filter types:

   | Filter | Syntax Examples | Behavior |
   |--------|----------------|----------|
   | Keyword | `search price alerts` | Fuzzy match against `title`, `summary`, and `tags` |
   | Status | `status:draft`, `status:implemented,planned` | Exact match, comma-separated for OR |
   | Tag | `tag:api`, `tag:charts,data` | Exact match on `tags` array, comma-separated for OR |
   | Depends on | `depends-on:001-feature-name` | Match `relationships.depends_on` |
   | Related to | `related-to:001-feature-name` | Match `relationships.related_to` |
   | All | `all` or no filters | Return all specs |

   Multiple filters are combined with AND logic.

3. **Apply filters** and collect matching specs.

4. **Format output** as a compact table:

   ```
   | ID | Title | Status | Tags | Summary |
   |----|-------|--------|------|---------|
   | 001-... | Feature Name | implemented | api, data | Brief summary... |
   ```

   If no matches: "No specs match the query."

5. **Duplicate detection mode** (triggered by `check-duplicate:<description>`
   or when invoked from the specify command):
   - Tokenize the incoming feature description into keywords
   - Compare against all registry entries' `title`, `summary`, and `tags`
   - Score each entry: +2 for title word match, +1 for summary word match,
     +1 for tag match
   - Return entries scoring above threshold (≥3 points) as potential
     duplicates
   - If no matches above threshold: "No potential duplicates found."
   - If matches found: display matches with scores and present the user
     with a **multiple choice selection** (use a structured choice dialog
     such as the `ask_user` tool with `choices`):
     choices: ["Proceed with new spec anyway", "View an existing spec", "Cancel"]

6. **Report**: Number of results, applied filters, then present the user
   with a **multiple choice selection** of next actions (do NOT use plain
   text suggestions — use a structured choice dialog such as the `ask_user`
   tool with `choices`). Build choices based on results:
   - **If results found**:
     choices: ["View/clarify an existing spec (Recommended)", "Create a new spec", "Search again with different criteria"]
   - **If no results found**:
     choices: ["Create a new spec (Recommended)", "Search again with different criteria"]

## Examples

```
User: search status:draft
Agent: Found 3 draft specs:
| ID | Title | Tags | Summary |
| 005-... | Price Alerts | price, notifications | ... |
| 006-... | ... | ... | ... |

User: search tag:api
Agent: Found 2 specs tagged 'api':
...

User: search check-duplicate: "Show price alerts for sealed products"
Agent: Potential duplicates found:
| ID | Title | Score | Reason |
| 002-sealed-product | Sealed Product View | 4 | Matches: sealed, products, price |
[Agent presents multiple choice: "Proceed with new spec anyway", "View an existing spec", "Cancel"]
```

## Guidelines

- Always read the registry file; never scan individual spec directories
- Keep output concise — the registry is designed for quick scanning
- For keyword search, ignore common stop words (the, a, an, for, etc.)
- Status values are lowercase in the registry: draft, clarified, planned,
  in-progress, implemented, deprecated, superseded
- If the user asks to "list all specs" or "show all features", return
  the full registry as a table
