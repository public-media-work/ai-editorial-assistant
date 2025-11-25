# Prioritize Transcript

Move a specific transcript to the front of the processing queue.

## Your Task

Take a transcript identifier from the user and move it to the front of the pending items in the processing queue (`.processing-requests.json`).

## Arguments

This command accepts a transcript identifier as an argument:
- Project name (e.g., `9UNP2005HD`)
- Full filename (e.g., `9UNP2005HD_ForClaude.txt`)
- Partial match (e.g., `2005` will match `9UNP2005HD`)

Usage: `/prioritize-transcript <transcript>`

## How to Execute

1. Read the `.processing-requests.json` file
2. Find the transcript matching the provided identifier
3. If found and status is "pending" or "failed":
   - Remove it from its current position
   - Insert it at the front of pending/failed items (after any "completed" or "processing" items)
   - Update `queued_at` timestamp to current time
   - Save the updated queue
4. Report the result

## Validation

- Transcript must exist in the queue
- Transcript status must be "pending" or "failed" (not "completed" or "processing")
- If already at front, report success but note no change was needed

## Expected Output

On success:
```
Transcript Prioritized

"9UNP2005HD" moved to position 1 in queue (was position 5)

Queue order (pending/failed items):
1. 9UNP2005HD (pending) <- prioritized
2. 2WLIGlassTreeSM (failed)
3. 9UNP1994HD (failed)
...
```

On failure:
```
Could Not Prioritize

Transcript "INVALID" not found in queue.

Available pending/failed items:
- 9UNP2005HD
- 2WLIGlassTreeSM
- 9UNP1994HD
```

## Notes

- This only changes queue order, it does not start processing
- The queue processor picks up items in order when it runs
- Failed items can be prioritized to retry them first
- Completed items cannot be prioritized (they're already done)
