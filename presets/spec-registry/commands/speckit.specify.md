## Spec Registry Update

**Update spec registry**: After generating the spec, update `specs/registry.json`:

1. If `specs/registry.json` does not exist, create it with this structure:
   ```json
   {
     "version": 1,
     "specs": []
   }
   ```

2. Find or create an entry in the `specs` array matching this feature's ID (the branch/directory name). Each entry has this shape:
   ```json
   {
     "id": "<feature-id>",
     "title": "<feature title from spec>",
     "summary": "<one-sentence summary from spec>",
     "status": "draft",
     "tags": ["<relevant>", "<tags>"],
     "created": "<YYYY-MM-DD>",
     "relationships": {}
   }
   ```

3. Update the entry's `title` and `summary` fields from the generated spec content. Confirm `status` is `"draft"`. Add relevant tags (1-5, lowercase hyphenated).
