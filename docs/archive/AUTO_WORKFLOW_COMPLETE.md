# Automated Editorial Assistant Workflow - Complete

**Status**: ✅ Fully Operational

Your editorial assistant now has end-to-end automation with fact-checking capabilities.

---

## What's Automated

### 1. Transcript Detection
- **Watcher**: Auto-starts at login, monitors `/transcripts/` every 10 seconds
- **Detection**: Finds new `*_ForClaude.txt` files automatically
- **Status**: ✅ Running (PID: 72351)

### 2. Project Setup
- **Batch Processing**: Creates OUTPUT directory structure + manifest
- **Program Detection**: Identifies program type from filename
- **Metadata**: Initializes project tracking

### 3. Processing Queue
- **Auto-Queuing**: New projects added to `.processing-requests.json`
- **Status Tracking**: Monitors what needs agent processing
- **Ready for agents**: Queue file ready for Claude Code to process

### 4. MCP Server Integration
- **Formatted Transcripts**: Available via `get_formatted_transcript()` tool
- **Fact-Checking**: Claude Desktop can verify quotes, names, facts
- **Status**: ✅ Rebuilt and deployed

### 5. Auto-Archiving
- **After Processing**: Transcripts automatically archived to `transcripts/archive/`
- **Triggered by**: `finalize-queue.sh` after agent processing completes
- **Preserves**: OUTPUT folders remain for editing in Claude Desktop
- **Status**: ✅ Integrated into workflow

---

## Your Complete Workflow

### Morning: Drop Files
```bash
# Add transcripts to folder
cp /path/to/new/transcripts/* ~/Developer/editorial-assistant/transcripts/

# Watcher detects automatically within 10 seconds
# - Creates project structure
# - Adds to processing queue
# - Logs activity
```

### When Convenient: Process Queue
Open Claude Code and run:
```
"Process all items in .processing-requests.json"
```

This will:
1. Run **transcript-analyst** on each queued project
   - Generates brainstorming.md with titles, descriptions, keywords
   - Auto-detects duration from SRT timestamps
   - Includes social media optimization for videos under 3 minutes

2. Run **formatter** on each queued project
   - Generates formatted_transcript.md (AP Style, speaker identification)
   - Generates timestamp_report.md (for 15+ min videos)
   - Creates chapter markers in Media Manager and YouTube formats

3. Update manifests to "ready_for_editing"

### After Processing: Auto-Archive
After agents complete, run:
```bash
./scripts/finalize-queue.sh
```

This will:
1. Check each project for completion (brainstorming + formatted transcript)
2. **Automatically archive transcripts** to `transcripts/archive/`
3. Keep OUTPUT folders for editing in Claude Desktop
4. Clear the processing queue
5. Show summary of what was archived

### Anytime: Edit in Claude Desktop

```
"What's ready for editing?"
```

Claude Desktop will:
- List all projects with brainstorming + formatted transcripts
- Load project context via MCP
- **Fact-check using formatted transcript**
- Help refine metadata through conversation
- Save revisions with version tracking

---

## Fact-Checking Workflow

### New Feature: Formatted Transcript Access

Claude Desktop can now verify accuracy against formatted transcripts:

**When to use**:
- Verifying speaker names and titles
- Checking direct quotes word-for-word
- Confirming facts mentioned in video
- Validating proper nouns (places, organizations)

**How it works**:
```
# In Claude Desktop during editing
You: "Let's refine the title for 9UNP2005HD"

Claude Desktop:
1. Loads project context (brainstorming, revisions)
2. Calls get_formatted_transcript("9UNP2005HD") to verify details
3. Cross-checks AI suggestions against formatted transcript
4. Suggests revisions with verified accuracy
5. Saves refined copy
```

**Example scenarios**:

1. **Speaker verification**:
   - Draft: "Dr. Sarah Johnson discusses..."
   - Formatted transcript: "Sarah Johnson, historian, discusses..."
   - Correction: Remove "Dr." per University Place guidelines

2. **Quote accuracy**:
   - AI brainstorming: "The speaker mentions that progress was rapid"
   - Formatted transcript: "The actual quote was 'progress was steady but slow'"
   - Correction: Use verbatim quote

3. **Fact checking**:
   - Title: "1912 Labor Strike at Milwaukee Factory"
   - Formatted transcript: Video discusses 1913 strike
   - Correction: Update year to match source

---

## File Structure

### Input
```
editorial-assistant/
└── transcripts/
    ├── 9UNP2007HD_ForClaude.txt  ← Drop here
    ├── 2WLI1206HD_ForClaude.txt
    └── archive/                   ← Auto-archived after processing
```

### Processing Queue
```
editorial-assistant/
├── .processing-requests.json  ← Projects waiting for agents
└── .watch-state              ← Tracks what's been detected
```

### Output
```
editorial-assistant/OUTPUT/
└── 9UNP2007HD/
    ├── manifest.json                    ← Project metadata
    ├── brainstorming.md                 ← AI-generated initial ideas
    ├── formatted_transcript.md          ← AP Style formatted transcript
    ├── timestamp_report.md              ← Chapter markers (15+ min)
    ├── copy_revision_v1.md             ← Refined metadata (from Desktop)
    ├── copy_revision_v2.md             ← Further refinements
    └── copy_revision_v3.md             ← Final version
```

---

## Tools Reference

### Watcher Management
```bash
# Check status
launchctl list | grep editorial-assistant

# View logs
tail -f logs/watcher.log

# Restart watcher (after script updates)
launchctl kickstart -k gui/$(id -u)/com.editorial-assistant.transcript-watcher
```

### Manual Processing
```bash
# Process single transcript (if needed)
./scripts/batch-process-transcripts.sh "9UNP2007HD_ForClaude.txt"

# Archive processed transcripts
./scripts/archive-processed-transcripts.sh
```

### MCP Server (Claude Desktop)
```bash
# Rebuild after changes
cd mcp-server && npm run build

# Restart Claude Desktop to load new tools
```

---

## Processing Queue Format

`.processing-requests.json`:
```json
[
  {
    "project": "9UNP2007HD",
    "transcript_file": "9UNP2007HD_ForClaude.txt",
    "queued_at": "2025-11-21T18:00:00Z",
    "status": "pending",
    "needs_brainstorming": true,
    "needs_formatting": true
  }
]
```

**To process in Claude Code**:
```
"Process all items in .processing-requests.json"
```

This invokes:
1. `transcript-analyst` agent for each project (brainstorming)
2. `formatter` agent for each project (formatted transcript + timestamps)
3. Updates each project's manifest to "ready_for_editing"
4. Removes from queue when complete

---

## Quality Assurance

### Every Project Gets:
- ✅ **Brainstorming document** with title options, descriptions, keywords
- ✅ **Duration detection** from SRT timestamps
- ✅ **Formatted transcript** in AP Style with speaker identification
- ✅ **Timestamp report** (for videos 15+ minutes)
- ✅ **Manifest tracking** of all deliverables and status

### Videos Under 3 Minutes Also Get:
- ✅ **Social media optimization** section in brainstorming
  - Platform-optimized description (150 char)
  - Recommended hashtags (5 tags)
  - Platform-specific notes (YouTube, Instagram, TikTok)

### During Editing:
- ✅ **Fact-checking** against formatted transcript
- ✅ **AP Style compliance** verification
- ✅ **Program-specific rules** applied (University Place, Here and Now, etc.)
- ✅ **Version tracking** of all revisions
- ✅ **Character count validation**

---

## What Changed Today

### 1. MCP Server Enhancement
**Added**: `get_formatted_transcript()` tool
- Loads AP Style formatted transcript for fact-checking
- Available in Claude Desktop during editing
- Verifies quotes, speaker names, facts, proper nouns

### 2. Watcher Auto-Queuing
**Updated**: `watch-transcripts.sh`
- Now calls `auto-process-project.sh` after batch setup
- Adds projects to `.processing-requests.json` automatically
- Provides command to process queue in Claude Code

### 3. Processing Queue System
**Created**: `auto-process-project.sh`
- Creates/updates `.processing-requests.json` queue file
- Tracks which projects need agent processing
- Enables batch processing of multiple transcripts

### 4. Claude Desktop Instructions
**Updated**: Fact-checking workflow documented
- How to use `get_formatted_transcript()`
- When to verify against formatted transcript
- Common fact-checking scenarios
- Best practices for accuracy

---

## Benefits

### Time Savings
- **Before**: Manual setup, manual agent runs, manual status tracking
- **Now**: Drop files → auto-detected → auto-queued → one command processes all

### Quality Improvements
- **Formatted transcripts** as authoritative source for fact-checking
- **Automatic verification** of quotes and speaker attributions
- **AP Style compliance** from the start
- **Version tracking** of all refinements

### Scale
- **Process multiple transcripts** in parallel
- **Queue builds automatically** as files are added
- **Batch operations** for efficiency
- **No manual intervention** for detection and setup

---

## Next Steps

### Ready to Use
Everything is configured and running. To test:

1. **Drop a test transcript** into `/transcripts/`
2. **Check watcher log**: `tail -f logs/watcher.log`
3. **See queue**: `cat .processing-requests.json`
4. **Process in Claude Code**: "Process all items in .processing-requests.json"
5. **Edit in Claude Desktop**: Use MCP tools to load and refine

### Optional Enhancements

If you want fully automatic processing (no manual Claude Code step):

1. **Python script** that invokes Claude Code API
2. **Scheduled task** (cron/LaunchAgent) runs periodically
3. **Zero intervention** - just drop files and they're ready to edit

This would require:
- Claude API key
- Python script development
- Scheduled task configuration

Current semi-automatic approach is recommended for:
- ✅ **Control**: You decide when to process
- ✅ **Resources**: Process when you have compute time available
- ✅ **Visibility**: See what's happening in Claude Code
- ✅ **Flexibility**: Process selectively if needed

---

## Support

### Logs
```bash
# Watcher activity
tail -f logs/watcher.log

# Watcher errors
tail -f logs/watcher.error.log
```

### Status Checks
```bash
# Is watcher running?
ps aux | grep watch-transcripts.sh

# What's in the queue?
cat .processing-requests.json | jq '.'

# What's been detected?
cat .watch-state | jq '.'

# Check for missed transcripts
./scripts/check-missed-transcripts.sh
```

### Troubleshooting
```bash
# Restart watcher
launchctl kickstart -k gui/$(id -u)/com.editorial-assistant.transcript-watcher

# Process any missed transcripts
./scripts/check-missed-transcripts.sh --process

# Clear queue (if needed)
echo "[]" > .processing-requests.json

# Clear state (to re-process existing files)
echo "[]" > .watch-state
```

### Edge Cases

See **[EDGE_CASES.md](EDGE_CASES.md)** for detailed handling of:
- **Duplicate transcripts**: Automatic versioning in archive prevents data loss
- **Missed transcripts**: Check script finds and processes files the watcher didn't pick up
- **Stale queue items**: How to clear and rebuild processing queue
- **Corrupt state files**: Recovery procedures
- **Archive management**: Version cleanup and restoration

---

## Summary

**You now have**:
- ✅ Automatic transcript detection at login
- ✅ Automatic project setup and queuing
- ✅ One-command batch processing in Claude Code
- ✅ Fact-checking with formatted transcripts in Claude Desktop
- ✅ Version-tracked editing workflow
- ✅ Automatic archiving of completed transcripts

**Your workflow is**:
1. Drop files → auto-detected
2. Run one command → fully processed
3. Edit conversationally → fact-checked and refined
4. Archive when done → clean workspace

**No manual setup. No manual tracking. Just results.** 🎉
