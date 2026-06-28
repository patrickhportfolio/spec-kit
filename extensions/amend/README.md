# Amend Spec Workflow Extension

Amend an existing feature spec in-place and implement the change through a lightweight validation pipeline. Supports natural language input from users or other agents.

## Overview

This extension provides the `speckit.amend` command — a structured workflow for making surgical edits to an existing spec and optionally implementing those changes. It follows the Spec-Driven Development principle of "spec-first, always": the spec is edited and validated before any code changes happen.

## Design Principles

1. **Agent-native**: Takes a natural language description of what changed
2. **Spec-first, always**: The spec is edited before any code changes
3. **Correct before fast**: Every amendment goes through a mini validation pipeline
4. **Human-in-the-loop**: User must approve spec changes (Gate 1) and amendment plan (Gate 2)
5. **Surgical edits**: Precise modifications to existing sections, not rewrites
6. **Atomic commits**: Spec + code are committed together

## Commands

| Command | Description |
|---------|-------------|
| `speckit.amend.amend` | Amend an existing feature spec in-place and implement the change |

**Alias**: `speckit.amend` (for backward compatibility with existing orchestrator references)

## Workflow Phases

1. **Locate and Load Context** — Find the target spec and load current artifacts
2. **Edit the Spec** — Make surgical edits to `spec.md`
3. **Gate 1** — User approves proposed spec changes
4. **Validate the Spec Edit** — Internal consistency, testability, contradiction detection
5. **Assess Complexity and Plan** — Analyze codebase impact, classify as SMALL/MEDIUM/LARGE
6. **Gate 2** — User approves amendment plan
7. **Implementation** — Apply code changes following the plan
8. **Completion** — Update registry, report results

## Installation

Bundled with Spec Kit — automatically available after `specify init`.

```bash
# Or install explicitly
specify extension add amend
```

## Usage

```text
# In your coding agent
/speckit.amend Add email verification to the user signup flow

# Or via workflow
specify workflow run speckit-amend
```

## When to Use

- **Amend** for incremental changes to existing features
- **Specify** (with supersede) for major rewrites

The command will suggest creating a new spec if the current one has been amended 5+ times.
