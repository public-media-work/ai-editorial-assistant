# Queue Status

Check the status of the watch folder and transcript processing queue.

## Your Task

Display a comprehensive status report of the transcript processing system, including unqueued transcripts in the watch folder and all items in the processing queue.

## Arguments (Optional)

This command accepts an optional filter argument:
- `/queue-status` - Full status report (default)
- `/queue-status summary` - Brief summary only
- `/queue-status pending` - Show only pending items
- `/queue-status failed` - Show only failed items
- `/queue-status completed` - Show only completed items

## How to Execute

### 1. Check Watch Folder

Scan `/transcripts/` for unqueued transcript files:
- Find all `*_ForClaude.txt` files (standard naming)
- Find any other `.txt` files that might be transcripts
- Exclude `transcripts/archive/` and `transcripts/examples/`
- Cross-reference with `.processing-requests.json` to find files not yet in queue

### 2. Read Processing Queue

Read `.processing-requests.json` and extract:
- Count by status (pending, processing, completed, failed)
- List of items with key details
- Estimated processing time for pending items
- Cost tracking for completed items

### 3. Cross-Reference with Output Manifests

For completed/processing items, optionally check `OUTPUT/{project}/manifest.json` for:
- Processing completion timestamps
- Deliverable status
- Any error details

### 4. Calculate Metrics

- **Queue depth**: Total pending + failed items
- **Estimated time**: Sum of `estimated_processing_minutes` for pending items
- **Total cost**: Sum of `cost` for completed items
- **Success rate**: completed / (completed + failed) percentage

## Expected Output

### Full Report (default)

```
Queue Status Report
Generated: 2025-12-17 14:30:00

WATCH FOLDER (transcripts/)
---------------------------
Unqueued transcripts: 2
- NewProject_ForClaude.txt (245 KB)
- AnotherVideo_ForClaude.txt (180 KB)

PROCESSING QUEUE
----------------
Total items: 12

By Status:
  Pending:    3
  Processing: 1
  Completed:  7
  Failed:     1

PENDING ITEMS
-------------
1. 9UNP2005HD (est: 5.2 min, queued: 2 hours ago)
2. 2WLI3000HD (est: 3.8 min, queued: 1 hour ago)
3. 9UNP1994HD (est: 4.1 min, queued: 30 min ago)

CURRENTLY PROCESSING
--------------------
- 2BUC0001HD (started: 5 min ago)

FAILED ITEMS
------------
1. 2WLIGlassTree - Error: API timeout
   (queued: 3 days ago, failed: 2 days ago)

METRICS
-------
Queue depth: 4 items (3 pending + 1 failed)
Estimated time remaining: 13.1 minutes
Total cost (completed): $0.38
Success rate: 87.5% (7/8)
```

### Summary Report (`/queue-status summary`)

```
Queue Status: 3 pending, 1 processing, 7 completed, 1 failed
Watch folder: 2 unqueued transcripts
Est. time: 13.1 min | Cost: $0.38 | Success: 87.5%
```

### Filtered Report (`/queue-status pending`)

```
Pending Items (3)
-----------------
1. 9UNP2005HD
   - Transcript: 9UNP2005HD_ForClaude.txt
   - Characters: 52,000
   - Estimated time: 5.2 min
   - Estimated cost: $0.052
   - Queued: 2025-12-17 12:30:00 (2 hours ago)

2. 2WLI3000HD
   ...
```

## Notes

- Queue file location: `.processing-requests.json` in project root
- Watch folder: `transcripts/` (excluding archive/ and examples/)
- Transcript naming convention: `{ProjectID}_ForClaude.txt`
- Estimates are based on transcript length (roughly 1 min per 10,000 chars)
- Cost estimates use ~$0.01 per 10,000 characters
- "Unqueued" means file exists in watch folder but not in `.processing-requests.json`
