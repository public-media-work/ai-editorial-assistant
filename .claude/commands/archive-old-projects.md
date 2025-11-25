# Archive Old Output Projects

Move output project folders older than 30 days to the archive.

## Your Task

Archive completed project folders from `/OUTPUT/` to `/OUTPUT/archive/` based on their age. Age is determined by the `processing_completed` date in each project's `manifest.json`.

## Arguments (Optional)

This command accepts an optional age threshold argument:
- Default: 30 days
- Usage: `/archive-old-projects` (uses 30 days)
- Usage: `/archive-old-projects 60` (uses 60 days)

## How to Execute

1. Create `/OUTPUT/archive/` directory if it doesn't exist
2. For each project folder in `/OUTPUT/` (excluding `archive/` and hidden folders):
   a. Read `manifest.json`
   b. Get the `processing_completed` date (or `processing_started` as fallback)
   c. Calculate age in days from today
   d. If older than threshold, move entire folder to `/OUTPUT/archive/`
3. Skip folders that:
   - Already exist in archive
   - Have no manifest.json
   - Have no processing date
   - Are younger than the threshold
4. Report results

## Expected Output

```
Archive Old Projects Complete

Threshold: 30 days
Today: 2025-11-25

Archived: X folders
- 9UNP1850HD (45 days old, completed 2025-10-11)
- 2WLI1100HD (62 days old, completed 2025-09-24)

Skipped: Y folders
- 9UNP2005HD: only 5 days old (threshold: 30)
- 2BUC0000HD: no manifest.json found
- OldProject: already exists in archive

Errors: Z folders
- CorruptProject: permission denied
```

## Notes

- Uses manifest dates, not filesystem dates, for accuracy
- Falls back to `processing_started` if `processing_completed` is not set
- Projects without manifests are skipped (not archived)
- Archive directory preserves original folder names
- This operation moves folders, not copies
