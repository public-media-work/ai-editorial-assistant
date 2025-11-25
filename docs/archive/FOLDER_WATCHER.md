# Transcript Folder Watcher

Automatically detect and process new transcripts as they're added to the `/transcripts/` directory.

---

## Quick Start

### Start Watching (Default: checks every 10 seconds)
```bash
./scripts/watch-transcripts.sh
```

### Start with Custom Interval
```bash
# Check every 30 seconds
./scripts/watch-transcripts.sh --interval 30

# Check every 5 seconds (more responsive)
./scripts/watch-transcripts.sh --interval 5
```

### Stop Watching
Press `Ctrl+C`

---

## How It Works

1. **Monitors** `/transcripts/` directory for new `*_ForClaude.txt` files
2. **Detects** files that haven't been processed yet
3. **Runs** batch setup script automatically for each new file
4. **Creates** OUTPUT/{project}/ directory with manifest.json
5. **Tracks** processed files in `.watch-state` to avoid duplicates
6. **Continues** watching for more files

### Visual Example

```
┌─────────────────────────────────────────┐
│   Transcript Folder Watcher Running    │
└─────────────────────────────────────────┘

Watching: /Users/.../transcripts
Check interval: 10s

✓ Watcher started (PID: 12345)

▶ New transcript detected: 9UNP2007HD_ForClaude.txt
  → Running batch setup...
  ✓ Project setup complete: 9UNP2007HD
  → Ready for agent processing

[Checking every 10 seconds...]

▶ New transcript detected: 2WLI1207HD_ForClaude.txt
  → Running batch setup...
  ✓ Project setup complete: 2WLI1207HD
  → Ready for agent processing
```

---

## What Gets Processed

### Automatically Detected
- Any file matching pattern: `*_ForClaude.txt`
- Located in: `/transcripts/` (not subdirectories)
- Not already in `.watch-state` tracking

### Automatically Skipped
- Files already processed (tracked in `.watch-state`)
- Files in `/transcripts/archive/` (not monitored)
- Files without `_ForClaude.txt` suffix
- Hidden files or directories

---

## State Tracking

The watcher maintains a state file: `.watch-state`

### Location
```
/Users/mriechers/Developer/editorial-assistant/.watch-state
```

### Format (JSON array)
```json
[
  "9UNP2007HD_ForClaude.txt",
  "2WLI1207HD_ForClaude.txt",
  "2BUC0000HD_ForClaude.txt"
]
```

### Reset State (Force Reprocessing)
```bash
# Delete state file to reprocess all files
rm .watch-state

# Or manually edit to remove specific files
```

---

## Workflow Integration

### Full Automated Pipeline

**Terminal 1**: Run the watcher
```bash
./scripts/watch-transcripts.sh
```

**Your workflow**:
1. Add transcript to `/transcripts/` folder
2. Watcher detects it automatically (within interval time)
3. Batch setup runs (creates OUTPUT directory + manifest)
4. You process with agents in Claude Code when convenient
5. Archive when complete

**Terminal 2**: Process with agents
```bash
# When watcher notifies new files, process them
# Option 1: Use Task tool for individual projects
# Option 2: Run formatter/transcript-analyst manually
```

### Hybrid: Manual + Automatic

You can combine:
- **Watcher running**: Handles new files automatically as they arrive
- **Manual processing**: Run batch script for immediate processing when needed

```bash
# Terminal 1: Watcher (background)
./scripts/watch-transcripts.sh &

# Terminal 2: Manual immediate processing
./scripts/batch-process-transcripts.sh specific_file.txt
```

---

## Configuration Options

### Check Interval

Default: 10 seconds

Adjust based on your needs:

**Responsive (frequent checks)**:
```bash
./scripts/watch-transcripts.sh --interval 5
```
- Pros: Detects files quickly (5 seconds)
- Cons: More CPU usage, more frequent checks

**Balanced (default)**:
```bash
./scripts/watch-transcripts.sh --interval 10
```
- Pros: Good balance of responsiveness and efficiency
- Cons: Up to 10 second delay before detection

**Relaxed (infrequent checks)**:
```bash
./scripts/watch-transcripts.sh --interval 60
```
- Pros: Minimal resource usage
- Cons: Up to 1 minute delay before detection

### Run in Background

To run persistently in background:

**Using `&`**:
```bash
./scripts/watch-transcripts.sh > /tmp/transcript-watcher.log 2>&1 &
echo $! > /tmp/transcript-watcher.pid
```

**Stop background watcher**:
```bash
kill $(cat /tmp/transcript-watcher.pid)
```

**Using `nohup`**:
```bash
nohup ./scripts/watch-transcripts.sh > ~/transcript-watcher.log 2>&1 &
```
(Continues running even after you close terminal)

**Using `screen` or `tmux`** (recommended):
```bash
# Start screen session
screen -S transcript-watcher

# Run watcher
./scripts/watch-transcripts.sh

# Detach: Ctrl+A, then D
# Reattach: screen -r transcript-watcher
```

---

## Use Cases

### 1. Overnight Batch Processing

Set up watcher before leaving:
```bash
# Terminal 1: Start watcher
./scripts/watch-transcripts.sh

# Leave running overnight
# Drop new transcripts into folder
# Next morning: all projects set up, ready for agent processing
```

### 2. Continuous Production Environment

For ongoing content production:
```bash
# Run watcher persistently
screen -S watcher
./scripts/watch-transcripts.sh --interval 30

# Detach (Ctrl+A, D)
# Watcher runs continuously, processing files as they arrive
```

### 3. Integration with Export/Upload Tools

If you have automated export from video editing software:
```bash
# Your export script saves to:
/Users/.../editorial-assistant/transcripts/

# Watcher picks it up automatically
# No manual intervention needed
```

---

## Troubleshooting

### Watcher Not Detecting Files

**Check 1**: Verify file naming
```bash
ls transcripts/
# Files must end with: _ForClaude.txt
```

**Check 2**: Check state file
```bash
cat .watch-state
# File might already be marked as processed
```

**Check 3**: Verify watcher is running
```bash
ps aux | grep watch-transcripts
```

### Files Detected But Not Processing

**Check batch script**:
```bash
# Test batch script manually
./scripts/batch-process-transcripts.sh test_file.txt
```

**Check permissions**:
```bash
ls -la scripts/
# All .sh files should be executable (x flag)
```

### Want to Reprocess a File

**Option 1**: Remove from state
```bash
# Edit .watch-state and remove the filename from the JSON array
```

**Option 2**: Delete state entirely
```bash
rm .watch-state
# Next cycle will reprocess all files in transcripts/
```

**Option 3**: Process manually
```bash
# Bypass watcher
./scripts/batch-process-transcripts.sh filename.txt
```

### Watcher Consuming Too Many Resources

**Increase interval**:
```bash
./scripts/watch-transcripts.sh --interval 60
# Check once per minute instead of every 10 seconds
```

**Or use filesystem events** (advanced):
- macOS: Use `fswatch` instead of polling
- Linux: Use `inotifywait` instead of polling

---

## Advanced: Event-Based Watching (macOS)

For instant detection without polling, use `fswatch`:

### Install fswatch
```bash
brew install fswatch
```

### Create event-based watcher
```bash
#!/bin/bash
# scripts/watch-transcripts-fswatch.sh

fswatch -0 transcripts/ | while read -d "" path; do
  if [[ "$path" == *_ForClaude.txt ]]; then
    filename=$(basename "$path")
    echo "▶ New file detected: $filename"
    ./scripts/batch-process-transcripts.sh "$filename"
  fi
done
```

**Benefits**:
- Instant detection (no polling delay)
- No CPU usage while idle
- More efficient for long-running processes

---

## Integration with Archive Script

### Combined Workflow

**Watcher** → Detects new files → Batch setup
**[Manual agent processing]**
**Archive script** → Moves processed transcripts

```bash
# Terminal 1: Watcher (continuous)
./scripts/watch-transcripts.sh

# Terminal 2: Process when ready
# (Use Task tool or manual agent invocation)

# Terminal 3: Clean up periodically
./scripts/archive-processed-transcripts.sh
```

### Automated Full Pipeline (Advanced)

Could create a wrapper that:
1. Watches for new files
2. Runs agents automatically
3. Archives when complete

(Would require agent auto-invocation setup - currently manual)

---

## Comparison: Manual vs. Watcher

| Aspect | Manual Batch Script | Folder Watcher |
|--------|---------------------|----------------|
| **Detection** | Run when you remember | Automatic, continuous |
| **Speed** | Immediate (when run) | Interval-based delay |
| **Convenience** | Manual trigger needed | Set and forget |
| **Resource Usage** | None when not running | Minimal, continuous |
| **Best For** | Immediate batch processing | Ongoing production workflow |
| **Control** | Explicit, intentional | Automatic, hands-off |

---

## Best Practices

### 1. Choose Appropriate Interval
- **Active production**: 10-30 seconds
- **Overnight batches**: 60 seconds
- **Immediate needs**: Use manual script instead

### 2. Monitor State File
```bash
# Periodically check what's been processed
cat .watch-state | python -m json.tool
```

### 3. Run in Background for Production
```bash
# Use screen/tmux for persistent watching
screen -S transcript-watcher
./scripts/watch-transcripts.sh
# Detach and let it run
```

### 4. Combine with Archive Script
```bash
# After processing is done, clean up
./scripts/archive-processed-transcripts.sh
```

### 5. Clear State Periodically
```bash
# After archiving processed files, clear state
# (Archived files won't be detected anyway)
./scripts/archive-processed-transcripts.sh
rm .watch-state
```

---

## Example Session

```bash
$ ./scripts/watch-transcripts.sh

╔════════════════════════════════════════════════════════╗
║   Editorial Assistant - Transcript Folder Watcher     ║
╚════════════════════════════════════════════════════════╝

Watching: /Users/mriechers/Developer/editorial-assistant/transcripts
Check interval: 10s
State file: .watch-state

Press Ctrl+C to stop watching

✓ Watcher started (PID: 45678)

[10 seconds pass...]
[20 seconds pass...]

▶ New transcript detected: 9UNP2007HD_ForClaude.txt
  → Running batch setup...
  === Editorial Assistant Batch Processor ===
  Found 1 transcript(s) to process:
    - 9UNP2007HD_ForClaude.txt
  Processing: 9UNP2007HD
  → Creating processing manifest...
  ✓ Created OUTPUT/9UNP2007HD
  ✓ Project setup complete: 9UNP2007HD
  → Ready for agent processing

[10 seconds pass...]
[10 seconds pass...]

▶ New transcript detected: 2WLI1207HD_ForClaude.txt
  → Running batch setup...
  === Editorial Assistant Batch Processor ===
  Found 1 transcript(s) to process:
    - 2WLI1207HD_ForClaude.txt
  Processing: 2WLI1207HD
  → Creating processing manifest...
  ✓ Created OUTPUT/2WLI1207HD
  ✓ Project setup complete: 2WLI1207HD
  → Ready for agent processing

[Continues watching...]

^C
Stopping watcher...
```

---

## Summary

**Purpose**: Automatically detect and set up new transcripts without manual intervention

**Usage**: `./scripts/watch-transcripts.sh [--interval SECONDS]`

**What it does**:
- Monitors `/transcripts/` folder
- Detects new `*_ForClaude.txt` files
- Runs batch setup automatically
- Tracks processed files to avoid duplicates

**What it doesn't do**:
- Run agents (still manual via Task tool or direct invocation)
- Archive files (use separate archive script)
- Process files in subdirectories

**Best for**: Continuous production environments where transcripts arrive regularly

**Alternative**: Manual batch script for immediate, intentional processing
