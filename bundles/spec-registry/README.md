# Spec Registry Bundle

Full spec registry tracking for Spec-Driven Development projects. Installs:

- **spec-registry preset** — appends `specs/registry.json` status tracking to all core SDD commands (specify, clarify, plan, implement, analyze) and adds a search command
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

## Remove

```bash
specify bundle remove spec-registry
```
