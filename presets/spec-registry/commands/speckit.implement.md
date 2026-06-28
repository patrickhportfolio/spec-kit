## Spec Registry Updates

This command requires two registry status transitions:

1. **At start of implementation** (before beginning any task execution): Update the `status` field in `specs/registry.json` for this feature's entry to `"in-progress"`. If the registry file or entry does not exist, skip silently.

2. **At completion** (after final verification passes): Update the `status` field in `specs/registry.json` for this feature's entry to `"implemented"`. If the registry file or entry does not exist, skip silently.
