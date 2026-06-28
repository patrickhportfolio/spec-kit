# Retroactive Spec Workflow Extension

Build specification artifacts for an existing feature by analyzing the current codebase. Reverse-engineers a spec, plan, and tasks from code that was implemented without the Spec-Driven Development workflow.

## Overview

This extension provides the `speckit.retroactive` command — a structured workflow for creating spec artifacts from existing code. Use it when you have a feature already implemented but want to bring it under the SDD umbrella for future maintenance, amendments, and consistency tracking.

## Commands

| Command | Description |
|---------|-------------|
| `speckit.retroactive.retroactive` | Analyze existing code and generate spec, plan, and tasks |

**Alias**: `speckit.retroactive` (for backward compatibility with orchestrator and workflow references)

## When to Use

- Feature already exists in code but has no spec
- Onboarding a legacy codebase into Spec-Driven Development
- Documenting existing behavior before making changes
- Creating a baseline spec for future amendments

## Workflow

The retroactive command:

1. Analyzes the codebase to understand the existing feature
2. Generates a spec (`spec.md`) describing what was built
3. Generates a plan (`plan.md`) documenting the architecture
4. Generates tasks (`tasks.md`) reflecting what was done
5. Hands off to `speckit.clarify` if gaps are identified

## Installation

Bundled with Spec Kit — automatically available after `specify init`.

```bash
# Or install explicitly
specify extension add retroactive
```

## Usage

```text
# In your coding agent
/speckit.retroactive User authentication and session management

# Or via workflow
specify workflow run speckit-retroactive
```
