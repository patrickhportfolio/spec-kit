# Coordinate Extension — Monorepo Cross-Project Features

Route features to the correct project(s) automatically and fan-out cross-project
features into linked per-project specs with dependency ordering.

## How It Works

Engineers always start at the **monorepo root**. The orchestrator:

1. **Discovers** all Spec Kit projects by scanning for `.specify/` directories
2. **Analyzes** the feature description against each project's scope
3. **Routes** to the right destination:
   - Single project → delegates to that project's `/speckit.specify`
   - Multiple projects → creates linked specs via `/speckit.coordinate.specify`

No configuration file needed — projects are discovered dynamically.

## Install

Install at the **monorepo root** (which needs its own `.specify/`):

```bash
# Initialize the root as a minimal Spec Kit project
specify init . --integration <your-agent>

# Install the coordinate extension
specify extension install coordinate
```

The root project doesn't need specs of its own — it's just a coordination hub.

## Usage

```bash
# Always start at the root — describe what you want to build:
/speckit.coordinate.orchestrator Add user preferences display

# The orchestrator will:
# → Discover your projects (api, web, shared, etc.)
# → Analyze which project(s) are affected
# → Route to single-project /speckit.specify or multi-project /speckit.coordinate.specify
```

### Check cross-project progress

```bash
/speckit.coordinate.status
/speckit.coordinate.status user-preferences
```

## Commands

| Command | Purpose |
|---------|---------|
| `/speckit.coordinate.orchestrator` | Entry point — routes features to correct project(s) |
| `/speckit.coordinate.specify` | Creates linked specs across multiple projects |
| `/speckit.coordinate.status` | Tracks progress across all coordinated features |

## Project Discovery

Projects are found by scanning the repository for `.specify/` directories:

```text
my-monorepo/
├── .specify/          ← Root (coordination hub, excluded from discovery)
├── apps/
│   ├── api/.specify/  ← Discovered as project "api"
│   └── web/.specify/  ← Discovered as project "web"
└── packages/
    └── shared/.specify/  ← Discovered as project "shared"
```

**Name derivation**: Uses the immediate directory name. If two projects share a
name (e.g., `apps/api` and `services/api`), they're disambiguated as `apps-api`
and `services-api`.

**Scope understanding**: The orchestrator reads each project's
`.specify/memory/constitution.md` to understand what the project is responsible
for, enabling intelligent routing.

## Cross-Project References

Specs reference other projects' specs using qualified IDs:

```json
{
  "relationships": {
    "depends_on": ["api:20260628-user-preferences-endpoint"]
  }
}
```

Format: `<project-name>:<spec-id>`

## Monorepo Layout

```text
my-monorepo/
├── .specify/                              ← Root (coordination hub)
├── specs/
│   └── coordinations/                     ← Cross-project coordination records
│       └── 20260628-user-preferences.md
├── apps/
│   ├── api/
│   │   ├── .specify/                      ← Project "api"
│   │   └── specs/
│   │       ├── registry.json
│   │       └── 20260628-user-preferences-endpoint/
│   └── web/
│       ├── .specify/                      ← Project "web"
│       └── specs/
│           ├── registry.json
│           └── 20260628-consume-preferences-ui/
└── packages/
    └── shared/
        └── .specify/                      ← Project "shared"
```

## Design Principles

- **Zero configuration**: Projects are discovered, not declared
- **Root is the entry point**: Engineers describe features at root, system routes
- **Per-project specs are self-contained**: Each is independently implementable
- **No root registry**: Project registries are the source of truth
- **Coordination records are lightweight**: Track links and order, not content
