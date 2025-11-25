# Edge Case Handling

Documentation for handling unusual situations in the automated workflow.

---

## 1. Duplicate Transcripts (Same File Processed Twice)

### Scenario
You drop the same transcript file into `/transcripts/` again after it's already been processed and archived.

### What Happens

**First processing**:
```
transcripts/9UNP2007HD_ForClaude.txt → processed → archive/9UNP2007HD_ForClaude.txt
OUTPUT/9UNP2007HD/ created
```

**Second processing (same file)**:
```
transcripts/9UNP2007HD_ForClaude.txt → processed → archive/9UNP2007HD_ForClaude.txt
```

**Archive behavior**:
1. Auto-archive script detects existing file in archive
2. Existing file renamed: `archive/9UNP2007HD_ForClaude_v1.txt`
3. New file archived: `archive/9UNP2007HD_ForClaude.txt`
4. Prevents data loss - both versions preserved

**OUTPUT folder behavior**:
- Batch script checks if OUTPUT folder exists
- If exists, skips creation (preserves existing work)
- New processing creates separate deliverables
- Old revisions remain intact

### Version History in Archive

After multiple processings:
```
archive/
├── 9UNP2007HD_ForClaude.txt        ← Latest version
├── 9UNP2007HD_ForClaude_v1.txt     ← First processing
├── 9UNP2007HD_ForClaude_v2.txt     ← Second processing (if 3rd run)
└── 9UNP2007HD_ForClaude_v3.txt     ← Third processing (if 4th run)
```

### Best Practices

**To avoid duplicates**:
1. Check archive before dropping files: `ls transcripts/archive/`
2. Use unique filenames if reprocessing is needed
3. Review `.watch-state` to see what's been tracked

**If you intentionally reprocess**:
- Previous archive versions are preserved
- OUTPUT folder preserves existing revisions
- Both brainstorming and formatted transcripts will be regenerated
- You can compare versions if needed

**Recovery**:
```bash
# View archive versions
ls -lh transcripts/archive/9UNP2007HD*

# Restore older version if needed
cp transcripts/archive/9UNP2007HD_ForClaude_v1.txt transcripts/9UNP2007HD_restored.txt
```

---

## 2. Missed Transcripts (Watcher Didn't Pick Them Up)

### Scenario
Files are in `/transcripts/` but the watcher didn't detect them (watcher was down, file added while computer was off, etc.)

### Detection Script

Run the check script to find missed files:
```bash
./scripts/check-missed-transcripts.sh
```

**What it checks**:
- All `*_ForClaude.txt` files in `/transcripts/`
- Compares against `.watch-state` (what watcher has tracked)
- Verifies OUTPUT directories exist
- Reports discrepancies

**Example output**:
```
=== Checking for Missed Transcripts ===

Scanning transcripts directory...

✓ 9UNP2007HD_ForClaude.txt - Tracked and processed
✗ 2WLI1206HD_ForClaude.txt - NOT TRACKED
⚠ 6GWQ2504_ForClaude.txt - Tracked but OUTPUT missing!

=== Summary ===
Total transcripts found: 3
Properly tracked: 1
Missed/incomplete: 2

To process missed transcripts, run:
  ./scripts/check-missed-transcripts.sh --process
```

### Auto-Processing Missed Files

Run with `--process` flag to automatically handle missed transcripts:
```bash
./scripts/check-missed-transcripts.sh --process
```

**What this does**:
1. **Identifies** all missed/incomplete transcripts
2. **Runs batch setup** for each missed file
3. **Queues for agent processing** (adds to `.processing-requests.json`)
4. **Updates watch state** to track them
5. **Shows summary** of what was processed

**Example output**:
```
✗ 2WLI1206HD_ForClaude.txt - NOT TRACKED
  → Processing now...
  ✓ Queued for agent processing

⚠ 6GWQ2504_ForClaude.txt - Tracked but OUTPUT missing!
  → Processing now...
  ✓ Queued for agent processing

=== Summary ===
Total transcripts found: 3
Properly tracked: 1
Missed/incomplete: 2
Processed this run: 2

Next steps:
1. Process queue in Claude Code: "Process all items in .processing-requests.json"
2. Finalize: ./scripts/finalize-queue.sh
```

### When to Run This Check

**Regular maintenance**:
```bash
# Weekly check
./scripts/check-missed-transcripts.sh
```

**After watcher downtime**:
```bash
# If watcher was stopped/crashed
./scripts/check-missed-transcripts.sh --process
```

**After bulk file additions**:
```bash
# If you dropped many files at once
./scripts/check-missed-transcripts.sh --process
```

### Why Transcripts Get Missed

**Common reasons**:

1. **Watcher not running**:
   ```bash
   # Check watcher status
   launchctl list | grep editorial-assistant

   # Start if needed
   launchctl start com.editorial-assistant.transcript-watcher
   ```

2. **Files added while computer was off**:
   - Watcher only runs when logged in
   - Files added during shutdown won't be detected until check script runs

3. **Watcher crashed**:
   ```bash
   # Check error log
   tail -f logs/watcher.error.log

   # Restart watcher
   launchctl kickstart -k gui/$(id -u)/com.editorial-assistant.transcript-watcher
   ```

4. **Permission issues**:
   ```bash
   # Verify watcher can read transcripts directory
   ls -la transcripts/
   ```

### Prevention

**Auto-recovery option**: Add check script to daily schedule
```bash
# Create LaunchAgent for daily checks (optional)
# Runs check-missed-transcripts.sh daily at 9 AM
# Auto-processes any missed files
```

**Manual habit**:
```bash
# Quick check before processing queue
./scripts/check-missed-transcripts.sh

# If any missed, process them
./scripts/check-missed-transcripts.sh --process
```

---

## 3. Processing Queue Edge Cases

### Stale Queue Items

**Scenario**: Queue has items from days ago that were never processed.

**Check queue**:
```bash
cat .processing-requests.json | jq '.'
```

**Clear stale items**:
```bash
# Backup first
cp .processing-requests.json .processing-requests.backup.json

# Clear queue
echo "[]" > .processing-requests.json

# Re-scan for missed transcripts
./scripts/check-missed-transcripts.sh --process
```

### Partial Processing

**Scenario**: Brainstorming generated but formatted transcript failed.

**Detected by**:
```bash
./scripts/finalize-queue.sh
```

**Output**:
```
Checking: 9UNP2007HD
  ⊘ Incomplete:
     Brainstorming: ✓
     Formatted transcript: ✗
```

**Solution**: Re-run agents in Claude Code
```
"Process project 9UNP2007HD from the queue"
```

### Corrupted Manifest

**Scenario**: manifest.json is invalid JSON.

**Detected by**: Scripts will show JSON parse errors

**Fix**:
```bash
# Check manifest validity
jq '.' OUTPUT/9UNP2007HD/manifest.json

# If corrupted, regenerate
rm OUTPUT/9UNP2007HD/manifest.json
./scripts/batch-process-transcripts.sh "9UNP2007HD_ForClaude.txt"
```

---

## 4. Archive Edge Cases

### Archive Full of Versions

**Scenario**: Same transcript processed many times, archive cluttered.

**Cleanup**:
```bash
# List versions
ls -lh transcripts/archive/9UNP2007HD*

# Keep only latest, remove old versions
cd transcripts/archive/
rm 9UNP2007HD_ForClaude_v*.txt
```

### Accidentally Archived Active Work

**Scenario**: Transcript archived but you wanted to reprocess.

**Restore**:
```bash
# Move back from archive
mv transcripts/archive/9UNP2007HD_ForClaude.txt transcripts/

# Watcher will detect it on next cycle (10s)
# Or manually process:
./scripts/check-missed-transcripts.sh --process
```

### Archive Directory Missing

**Scenario**: `transcripts/archive/` directory deleted.

**Auto-recovery**: All scripts create it automatically
```bash
# Scripts check and create if needed
mkdir -p transcripts/archive/
```

---

## 5. Watcher State Edge Cases

### Corrupt Watch State

**Scenario**: `.watch-state` file is invalid JSON.

**Fix**:
```bash
# Reset watch state
echo "[]" > .watch-state

# Re-scan transcripts
./scripts/check-missed-transcripts.sh --process
```

### Watch State Out of Sync

**Scenario**: Watch state lists files that don't exist.

**Not a problem**: Scripts check for actual file existence, not just state

**To clean up**:
```bash
# Rebuild clean state from actual files
./scripts/check-missed-transcripts.sh --process
```

---

## 6. Workflow Recovery

### Complete System Reset

If everything gets out of sync:

```bash
# 1. Backup current state
mkdir -p ~/backup-editorial-assistant
cp -r OUTPUT/ ~/backup-editorial-assistant/
cp .watch-state ~/backup-editorial-assistant/
cp .processing-requests.json ~/backup-editorial-assistant/

# 2. Reset state files
echo "[]" > .watch-state
echo "[]" > .processing-requests.json

# 3. Re-scan all transcripts
./scripts/check-missed-transcripts.sh --process

# 4. Check what's queued
cat .processing-requests.json | jq '.'

# 5. Process queue
# In Claude Code: "Process all items in .processing-requests.json"

# 6. Finalize
./scripts/finalize-queue.sh
```

### Verify Everything is Working

```bash
# Check watcher
launchctl list | grep editorial-assistant
tail -f logs/watcher.log

# Check transcripts
ls -lh transcripts/
./scripts/check-missed-transcripts.sh

# Check queue
cat .processing-requests.json | jq '.'

# Check OUTPUT
ls -lh OUTPUT/
```

---

## Summary

**Edge case handling scripts**:
- `check-missed-transcripts.sh` - Find and process missed files
- `auto-archive-transcript.sh` - Handles duplicate archiving with versioning
- `finalize-queue.sh` - Detects incomplete processing

**Best practices**:
1. Run missed check weekly: `./scripts/check-missed-transcripts.sh`
2. Monitor watcher logs: `tail -f logs/watcher.log`
3. Verify queue before processing: `cat .processing-requests.json | jq '.'`
4. Keep watch state in sync: Let scripts handle it automatically

**When things go wrong**:
1. Check watcher is running
2. Run missed transcript check
3. Verify queue contents
4. Review logs for errors
5. Use system reset procedure if needed
