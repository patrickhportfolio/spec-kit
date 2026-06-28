# Using Spec Kit in a Monorepo

A Spec Kit project is **directory-scoped**: the project is whichever directory
contains `.specify/`. A monorepo can hold several independent Spec Kit projects
under one repository root, each with its own `.specify/`, `specs/`, constitution,
and feature numbering.

Root resolution already prefers the **nearest** `.specify/` over the Git
toplevel, so commands run from inside a member project resolve to that project,
not the repo root.

## Layout

```text
my-monorepo/
├── .git/                     # one Git repository at the root
├── apps/
│   ├── web/
│   │   └── .specify/         # Spec Kit project "web"
│   │       └── memory/constitution.md
│   └── api/
│       └── .specify/         # Spec Kit project "api"
│           └── memory/constitution.md
└── packages/
    └── ui/
        └── .specify/         # Spec Kit project "ui"
```

Initialize each member project independently:

```bash
specify init apps/web --integration claude
specify init apps/api --integration claude
```

Each project keeps its own `specs/` directory and numbers features
independently (`apps/web/specs/001-…`, `apps/api/specs/001-…`).

## Working inside a member project

The default workflow is unchanged: change into the project directory and run the
slash commands. Root resolution finds the nearest `.specify/`.

```bash
cd apps/web
# then run /speckit.specify, /speckit.plan, … in your agent
```

## Targeting a member project from the repo root

For non-interactive or CI runs where you do not want to `cd`, set
**`SPECIFY_INIT_DIR`** to the member project root (the directory *containing*
`.specify/`). Relative paths resolve against the current directory.

```bash
# operate on apps/web from the monorepo root (no cd required)
export SPECIFY_INIT_DIR=apps/web
```

The path must exist and contain `.specify/`. If it does not, the command
**errors and does not fall back** to the current directory or the Git toplevel.
This is deliberate: a typo never writes specs into the wrong project. A
nonexistent path is reported as you typed it; a path that exists but is not a
Spec Kit project is reported as its resolved absolute path:

```text
# SPECIFY_INIT_DIR=apps/wbe  (typo: no such directory)
ERROR: SPECIFY_INIT_DIR does not point to an existing directory: apps/wbe

# SPECIFY_INIT_DIR=apps  (exists, but has no .specify/ of its own)
ERROR: SPECIFY_INIT_DIR is not a Spec Kit project (no .specify/ directory): /home/you/my-monorepo/apps
```

`SPECIFY_INIT_DIR` selects the **project**; `SPECIFY_FEATURE_DIRECTORY` selects
the **feature** within it. They compose: set both to pick a project and a
feature non-interactively. See the
[`SPECIFY_INIT_DIR` reference](../reference/core.md#environment-variables) for
the full contract and the two-axes model.

## How `SPECIFY_INIT_DIR` reaches your agent

`SPECIFY_INIT_DIR` is read by the shell scripts that the slash commands invoke
(`get_repo_root` in Bash, `Get-RepoRoot` in PowerShell). It takes effect only
when it is present in the environment of the shell that runs those scripts.

- **Scripted / CI runs:** export it in the same shell that drives the commands;
  it is reliable there.
- **Interactive agents:** whether an exported variable reaches the shell tool an
  agent uses is agent-specific. Export `SPECIFY_INIT_DIR` *before* launching the
  agent, and verify once (e.g. run `/speckit.specify` and confirm the new feature
  landed under the intended project's `specs/`).

## Git in a monorepo

> [!NOTE]
> Spec Kit project files are scoped to the **resolved project root**, but Git
> operations still run in the containing Git work tree. In a monorepo with a
> single Git repository at the root and projects in subdirectories, feature
> branch creation creates or switches branches in the shared root repository.
> Spec directories still live under the selected member project, while the Git
> branch namespace is shared by the whole monorepo. Manage branches and commits
> at the repository root, or initialize Git per member project if you want
> isolated per-project branch namespaces.

## Constitutions

Each member project has its own `.specify/memory/constitution.md` and
`/speckit.constitution` edits the local project's file. Spec Kit does not provide
a built-in base/inheritance mechanism; if you want one constitution to reference
shared rules elsewhere in the monorepo, you need to maintain that wiring yourself.
Otherwise, duplicate or sync shared engineering rules per project.

## Cross-Project Features

When a feature spans multiple projects (e.g., adding an API endpoint in one
project and consuming it in another), use the **coordinate** extension. It
provides a root-level orchestrator that routes features to the correct project(s)
automatically.

### Setup

Install the coordinate extension at the monorepo root:

```bash
specify extension install coordinate
```

No configuration file needed — projects are discovered dynamically by scanning
for `.specify/` directories.

### Workflow

Engineers always start at the root:

```bash
# Describe the feature at the monorepo root:
/speckit.coordinate.orchestrator Add user preferences — new API endpoint + web UI display
```

The orchestrator will:

1. **Discover** all projects by scanning for `.specify/` dirs
2. **Read** each project's constitution to understand scope
3. **Route** based on analysis:
   - Single project → delegates to that project's `/speckit.specify`
   - Multiple projects → delegates to `/speckit.coordinate.specify`
4. **Link** cross-project specs via `relationships.depends_on`
5. **Report** implementation order

### Cross-Project References

Specs reference other projects' specs using qualified IDs:

```json
{
  "relationships": {
    "depends_on": ["api:20260628-user-preferences-endpoint"]
  }
}
```

Format: `<project-name>:<spec-id>` — the project name is derived from the
directory name during discovery.

### Tracking Progress

```bash
/speckit.coordinate.status
```

Shows the status of all coordinated features across projects.

### Single-Project Features

The orchestrator handles these too — it simply routes to the correct project.
No need to `cd` into the project first.

