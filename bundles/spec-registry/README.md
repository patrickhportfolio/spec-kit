# Spec Registry Bundle

Full spec registry tracking for Spec-Driven Development projects. Installs:

- **spec-registry preset** — appends `specs/registry.json` status tracking to core SDD commands (specify, clarify, plan, implement, analyze)
- **search extension** — search and query the spec registry by keyword, status, tag, or relationship
- **amend extension** — amend existing specs in-place with lightweight validation
- **retroactive extension** — build specification artifacts for existing features by analyzing the codebase

## Install

```bash
# Initialize a new project with the bundle
specify bundle init spec-registry

# Or add to an existing project
specify bundle install spec-registry
```

## What It Does

After installation, every SDD workflow command automatically maintains feature status in `specs/registry.json`:

| Command | Registry Action |
|---------|----------------|
| `/speckit.specify` | Creates/updates entry, sets status to `"draft"` |
| `/speckit.clarify` | Updates status to `"clarified"` |
| `/speckit.plan` | Updates status to `"planned"` |
| `/speckit.implement` | Sets `"in-progress"` at start, `"implemented"` at completion |
| `/speckit.analyze` | Validates registry consistency and detects post-amendment drift |
| `/speckit.search` | Queries registry by keyword, status, tag, or relationship |

## Components

### Preset: spec-registry

Uses the `append` composition strategy to layer registry-update steps onto existing core commands without replacing them. Upstream command improvements flow through automatically.

### Extension: search

A new `/speckit.search` command for querying `specs/registry.json` by keyword, status, tag, or relationship. Also ships `registry.schema.json` for reference.

### Extension: amend

Provides `/speckit.amend` — amend an existing spec in-place and implement the change through a lightweight validation pipeline.

### Extension: retroactive

Provides `/speckit.retroactive` — build specification artifacts for an existing feature by analyzing the current codebase.

## Remove

```bash
specify bundle remove spec-registry
```

