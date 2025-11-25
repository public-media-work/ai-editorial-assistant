# Archive Unprocessed Transcripts

Move all transcript files from `/transcripts/` to `/transcripts/archive/`.

## Your Task

Archive all unprocessed transcript files from the main transcripts directory to the archive subdirectory. This is typically used after a batch processing run to clean up the working directory.

## What This Does

1. Scans `/transcripts/` for all `.txt` files (excluding hidden files)
2. Moves each file to `/transcripts/archive/`
3. Skips files that already exist in the archive
4. Reports results showing what was archived, skipped, or errored

## How to Execute

Use the file system to:
1. List all `.txt` files in the `transcripts/` directory
2. For each file, move it to `transcripts/archive/`
3. Skip any files that already exist in the archive (don't overwrite)
4. Report the results

## Expected Output

After completion, display a summary:

```
Archive Complete

Archived: X files
- filename1.txt
- filename2.txt

Skipped: Y files (already in archive)
- existing1.txt

Errors: Z files
- failed1.txt: reason
```

## Notes

- This operation moves files, it does not copy them
- Files already in the archive are preserved (not overwritten)
- The archive directory is created if it doesn't exist
- This does not affect the processing queue - only moves the source files
