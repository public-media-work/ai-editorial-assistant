# Transcript Cleanup & Archive Workflow

Keep your transcripts directory organized by automatically archiving processed files.

---

## Quick Start

### Check what would be archived (safe preview)
```bash
./scripts/archive-processed-transcripts.sh --dry-run
```

### Archive all processed transcripts
```bash
./scripts/archive-processed-transcripts.sh
```

---

## How It Works

The archive script checks each transcript file and determines if it's safe to archive based on:

### ✅ Ready to Archive When:
- **Status is "ready_for_editing"** AND has brainstorming deliverable
- **Status is "complete"** (all deliverables finished)
- **Status is "revision_in_progress"** (editing work underway)

### ⊘ Not Ready to Archive When:
- No OUTPUT directory exists (not yet processed)
- No manifest.json found (processing not started)
- Status is "processing" (work in progress)

---

## Archive Criteria

A transcript is archived when its deliverables are safely stored in OUTPUT/:

```
transcripts/9UNP2501HD_ForClaude.txt
    ↓ (after brainstorming generated)
OUTPUT/9UNP2501HD/
  ├─ manifest.json (status: ready_for_editing)
  ├─ brainstorming.md
  └─ [future: copy_revision_v1.md, formatted_transcript.md, etc.]
    ↓ (archive script runs)
transcripts/archive/9UNP2501HD_ForClaude.txt
```

**Why it's safe**: All deliverables reference the transcript by filename in manifest.json, and the MCP server will still load the project correctly even with the transcript archived.

---

## Workflow Integration

### Option 1: Manual Cleanup (Recommended)

After batch processing and reviewing deliverables:

```bash
# 1. Process transcripts
./scripts/batch-process-transcripts.sh

# 2. Generate deliverables with agents
# (transcript-analyst, formatter, etc.)

# 3. Preview what would be archived
./scripts/archive-processed-transcripts.sh --dry-run

# 4. Archive when satisfied
./scripts/archive-processed-transcripts.sh
```

### Option 2: Automatic Cleanup

Add to your workflow script or create an alias:

```bash
# After processing, automatically archive
process-and-archive() {
  ./scripts/batch-process-transcripts.sh
  # ... run agents ...
  ./scripts/archive-processed-transcripts.sh
}
```

### Option 3: Periodic Cleanup

Run periodically to clean up accumulated processed files:

```bash
# Weekly cleanup (can add to cron)
./scripts/archive-processed-transcripts.sh
```

---

## Safety Features

### Dry Run Mode
Always test first:
```bash
./scripts/archive-processed-transcripts.sh --dry-run
```

Shows what would happen without moving any files.

### Status-Based Logic
Only archives when manifest confirms processing is complete:
- Checks for manifest.json existence
- Reads status field
- Verifies deliverables exist

### Preserves Incomplete Work
Never archives transcripts that are:
- Not yet processed
- Currently being processed (status: "processing")
- Missing deliverables

---

## Archive Directory Structure

```
transcripts/
├─ archive/                          # Processed transcripts
│  ├─ 9UNP2501HD_ForClaude.txt      # Archived (has deliverables)
│  └─ 2BUC0000HD_ForClaude.txt      # Archived (has deliverables)
│
├─ 2WLI1206HD_ForClaude.txt         # Not yet processed
├─ 6GWQ2504_ForClaude.txt           # Not yet processed
└─ 9UNP2005HD_ForClaude.txt         # Not yet processed
```

---

## Output Examples

### Dry Run Output
```
DRY RUN MODE - No files will be moved

=== Archive Processed Transcripts ===

✓ 9UNP2501HD_ForClaude.txt - Would archive (brainstorming complete)
✓ 2BUC0000HD_ForClaude.txt - Would archive (brainstorming complete)
⊘ 2WLI1206HD_ForClaude.txt - No OUTPUT directory (not yet processed)
⊘ 6GWQ2504_ForClaude.txt - No manifest found

=== Archive Summary ===
Transcripts checked: 4
Ready to archive: 2
Actually archived: 0 (dry run mode)
Incomplete/not ready: 2

Run without --dry-run to actually move files
```

### Actual Archive Output
```
=== Archive Processed Transcripts ===

✓ 9UNP2501HD_ForClaude.txt - Archived (brainstorming complete)
✓ 2BUC0000HD_ForClaude.txt - Archived (brainstorming complete)
⊘ 2WLI1206HD_ForClaude.txt - No OUTPUT directory (not yet processed)

=== Archive Summary ===
Transcripts checked: 3
Ready to archive: 2
Archived: 2
Incomplete/not ready: 1

✓ Transcripts moved to: /path/to/transcripts/archive
```

---

## Recovery from Archive

If you need to reprocess an archived transcript:

```bash
# Move it back to transcripts/
mv transcripts/archive/9UNP2501HD_ForClaude.txt transcripts/

# Delete or rename the OUTPUT directory if starting fresh
rm -rf OUTPUT/9UNP2501HD/

# Reprocess
./scripts/batch-process-transcripts.sh 9UNP2501HD_ForClaude.txt
```

---

## Why Archive?

### Benefits

**1. Clean Working Directory**
- Easy to see which transcripts need processing
- Reduces clutter in file listings
- Clearer git status (if transcripts are tracked)

**2. Safe Organization**
- Deliverables are in OUTPUT/ (the source of truth)
- Transcript referenced by filename in manifest
- MCP server loads from OUTPUT/, not raw transcripts

**3. Workflow Clarity**
- `/transcripts/` = to be processed
- `/transcripts/archive/` = already processed
- `/OUTPUT/` = deliverables and working files

**4. Performance**
- Fewer files for batch script to scan
- Faster directory listings
- Reduced search/index overhead

### What Stays in transcripts/?

Only unprocessed files:
- New transcripts awaiting batch processing
- Files that failed processing (you'll see errors)
- Files intentionally held for later processing

---

## Integration with MCP Server

The MCP server **does not** load raw transcripts - it loads from OUTPUT/ directories:

```typescript
// MCP server loads project data from OUTPUT/
const projectPath = path.join(OUTPUT_DIR, projectName);
const manifest = readManifest(projectPath);  // Has transcript filename
const brainstorming = readFile(projectPath, "brainstorming.md");
const formattedTranscript = readFile(projectPath, "formatted_transcript.md");

// Raw transcript only needed if user requests full original
// which would be loaded from transcripts/ OR transcripts/archive/
```

**Result**: Archiving transcripts **does not break** Claude Desktop's ability to load projects.

---

## Best Practices

### 1. Always Dry Run First
```bash
./scripts/archive-processed-transcripts.sh --dry-run
```
Review before archiving.

### 2. Archive After Verification
Only archive after confirming deliverables look good:
- Check brainstorming quality
- Verify character counts
- Review keywords
- Test MCP loading in Claude Desktop

### 3. Keep Archive Organized
The archive is chronological by processing date. For long-term organization:

```bash
# Optional: organize by program type
transcripts/archive/
  ├─ UniversityPlace/
  ├─ WisconsinLife/
  ├─ GardenWanderings/
  └─ BuckyDocumentary/
```

### 4. Don't Archive While Editing
If you're actively working on revisions in Claude Desktop, wait to archive until editing is complete.

### 5. Regular Cleanup
Run weekly or after batch processing sessions:
```bash
# Add to your workflow
./scripts/batch-process-transcripts.sh
# ... agents run ...
./scripts/archive-processed-transcripts.sh --dry-run
./scripts/archive-processed-transcripts.sh  # if dry run looks good
```

---

## Troubleshooting

### "Would archive" but I want to keep it in transcripts/

If you want to keep a transcript accessible even after processing:

**Option 1**: Leave it (script won't hurt anything)
**Option 2**: Mark status differently in manifest:
```json
"status": "keep_accessible"  // Custom status, won't archive
```

### "No OUTPUT directory" but I processed this

Check if the project name matches:
```bash
ls OUTPUT/  # See what was created
# Verify transcript filename matches OUTPUT directory name
```

### "No manifest found" for old projects

Old projects from before manifest.json was added:
```bash
# Manually create manifest
cat > OUTPUT/ProjectName/manifest.json << EOF
{
  "status": "complete",
  "transcript_file": "ProjectName_ForClaude.txt"
}
EOF
```

---

## Summary

**Archive script**: `./scripts/archive-processed-transcripts.sh`
**Preview mode**: `--dry-run` flag
**Archives when**: Status is ready_for_editing, complete, or revision_in_progress
**Safe because**: Deliverables in OUTPUT/ are the source of truth
**Result**: Clean transcripts/ directory showing only unprocessed files

**Workflow**: Process → Verify → Preview → Archive → Clean workspace! 🎉
