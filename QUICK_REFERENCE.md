# Quick Reference Guide

Fast lookup for common tasks in the editorial assistant workflow.

---

## Daily Workflow

### 1. Add New Transcripts
```bash
# Drop files into transcripts folder
cp /path/to/transcripts/*.txt ~/Developer/editorial-assistant/transcripts/

# Watcher auto-detects within 10 seconds
# Check log to confirm
tail -f logs/watcher.log
```

### 2. Process Queue (in Claude Code)
```
"Process all items in .processing-requests.json"
```

### 3. Finalize & Archive
```bash
./scripts/finalize-queue.sh
```

### 4. Edit in Claude Desktop
```
"What's ready for editing?"
```

---

## Common Commands

### Check System Status
```bash
# Watcher running?
launchctl list | grep editorial-assistant

# What's queued?
cat .processing-requests.json | jq '.'

# Any missed files?
./scripts/check-missed-transcripts.sh
```

### Process Missed Transcripts
```bash
# Check for missed files
./scripts/check-missed-transcripts.sh

# Auto-process them
./scripts/check-missed-transcripts.sh --process
```

### Manual Archive
```bash
# Dry run (preview)
./scripts/archive-processed-transcripts.sh --dry-run

# Actually archive
./scripts/archive-processed-transcripts.sh
```

### Watcher Management
```bash
# Status
launchctl list | grep editorial-assistant

# Logs
tail -f logs/watcher.log

# Restart
launchctl kickstart -k gui/$(id -u)/com.editorial-assistant.transcript-watcher

# Stop
launchctl stop com.editorial-assistant.transcript-watcher

# Start
launchctl start com.editorial-assistant.transcript-watcher
```

---

## File Locations

### Input
```
transcripts/               ← Drop new files here
transcripts/archive/       ← Auto-archived after processing
```

### Processing
```
.watch-state              ← What watcher has tracked
.processing-requests.json ← Projects waiting for agents
```

### Output
```
OUTPUT/<project_name>/
├── manifest.json                 ← Project metadata
├── brainstorming.md             ← AI-generated ideas
├── formatted_transcript.md      ← AP Style transcript
├── timestamp_report.md          ← Chapter markers (15+ min)
├── copy_revision_v1.md          ← Refined metadata
├── copy_revision_v2.md          ← Further refinements
└── copy_revision_v3.md          ← Final version
```

### Logs
```
logs/watcher.log          ← Watcher activity
logs/watcher.error.log    ← Watcher errors
```

---

## Scripts Reference

### Automation
| Script | Purpose | Usage |
|--------|---------|-------|
| `watch-transcripts.sh` | Monitor folder for new files | Auto-runs at login |
| `batch-process-transcripts.sh` | Create project structure | Auto-called by watcher |
| `auto-process-project.sh` | Add to processing queue | Auto-called by watcher |
| `finalize-queue.sh` | Archive & clear completed | Run after agent processing |

### Maintenance
| Script | Purpose | Usage |
|--------|---------|-------|
| `check-missed-transcripts.sh` | Find missed files | `./scripts/check-missed-transcripts.sh` |
| `check-missed-transcripts.sh --process` | Process missed files | `./scripts/check-missed-transcripts.sh --process` |
| `archive-processed-transcripts.sh` | Manual archive | `./scripts/archive-processed-transcripts.sh` |
| `auto-archive-transcript.sh` | Archive single file | Auto-called by finalize-queue.sh |

---

## Claude Code Commands

### Process Queue
```
"Process all items in .processing-requests.json"
```

### Process Specific Project
```
"Process project <PROJECT_NAME> from the queue"
```

### Agent Invocation
```
# For brainstorming
"Run transcript-analyst on <PROJECT_NAME>"

# For formatted transcript + timestamps
"Run formatter on <PROJECT_NAME>"
```

---

## Claude Desktop (MCP Tools)

### Discovery
```
"What's ready for editing?"
```

### Load Project
```
"Load project <PROJECT_NAME> for editing"
```

### Fact-Checking
```
"Get formatted transcript for <PROJECT_NAME>"
```

### Save Work
```
"Save this revision for <PROJECT_NAME>"
```

---

## Troubleshooting

### Watcher Not Running
```bash
launchctl start com.editorial-assistant.transcript-watcher
```

### Files Not Detected
```bash
./scripts/check-missed-transcripts.sh --process
```

### Queue Stuck
```bash
# View queue
cat .processing-requests.json | jq '.'

# Clear and rebuild
echo "[]" > .processing-requests.json
./scripts/check-missed-transcripts.sh --process
```

### Duplicate in Archive
```bash
# Automatically handled with versioning
# Original: archive/<file>.txt
# Duplicate: archive/<file>_v1.txt
# Newest always without version suffix
```

### Reset Everything
```bash
# Backup first
mkdir -p ~/backup-editorial-assistant
cp -r OUTPUT/ ~/backup-editorial-assistant/

# Reset state
echo "[]" > .watch-state
echo "[]" > .processing-requests.json

# Re-scan
./scripts/check-missed-transcripts.sh --process
```

---

## Key File Formats

### Processing Queue (.processing-requests.json)
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

### Watch State (.watch-state)
```json
[
  "9UNP2007HD_ForClaude.txt",
  "2WLI1206HD_ForClaude.txt",
  "6GWQ2504_ForClaude.txt"
]
```

### Manifest (manifest.json)
```json
{
  "transcript_file": "9UNP2007HD_ForClaude.txt",
  "project_name": "9UNP2007HD",
  "program_type": "University Place",
  "processing_started": "2025-11-21T18:00:00Z",
  "status": "ready_for_editing",
  "deliverables": {
    "brainstorming": {
      "file": "brainstorming.md",
      "created": "2025-11-21T18:05:00Z",
      "agent": "transcript-analyst"
    },
    "formatted_transcript": {
      "file": "formatted_transcript.md",
      "created": "2025-11-21T18:08:00Z",
      "agent": "formatter"
    },
    "timestamps": {
      "file": "timestamp_report.md",
      "created": "2025-11-21T18:08:00Z",
      "agent": "formatter"
    },
    "copy_revisions": [
      {
        "file": "copy_revision_v1.md",
        "version": 1,
        "created": "2025-11-21T20:15:00Z"
      }
    ]
  },
  "transcript_archived": true,
  "archived_at": "2025-11-21T18:10:00Z"
}
```

---

## Weekly Maintenance

### Monday Morning
```bash
# Check for missed files from weekend
./scripts/check-missed-transcripts.sh --process

# View queue
cat .processing-requests.json | jq '.'
```

### Friday Afternoon
```bash
# Check watcher health
tail -20 logs/watcher.log

# Verify all transcripts accounted for
./scripts/check-missed-transcripts.sh

# Check archive
ls -lh transcripts/archive/ | tail -20
```

---

## Documentation Links

- **[AUTO_WORKFLOW_COMPLETE.md](AUTO_WORKFLOW_COMPLETE.md)** - Complete workflow guide
- **[EDGE_CASES.md](EDGE_CASES.md)** - Edge case handling
- **[AUTO_PROCESSING.md](AUTO_PROCESSING.md)** - Auto-processing details
- **[CLAUDE_DESKTOP_INSTRUCTIONS.md](CLAUDE_DESKTOP_INSTRUCTIONS.md)** - Editing workflow
- **[AUTO_START_SETUP.md](AUTO_START_SETUP.md)** - Watcher configuration
- **[CLEANUP_WORKFLOW.md](CLEANUP_WORKFLOW.md)** - Archive procedures

---

## Summary

**Normal day**:
1. Drop files → auto-detected
2. Process queue → agents run
3. Finalize → auto-archived
4. Edit → Claude Desktop

**Weekly check**:
```bash
./scripts/check-missed-transcripts.sh
```

**Emergency reset**:
```bash
echo "[]" > .watch-state
echo "[]" > .processing-requests.json
./scripts/check-missed-transcripts.sh --process
```
