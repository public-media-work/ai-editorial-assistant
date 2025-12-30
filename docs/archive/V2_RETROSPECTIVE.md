# V2.0 Retrospective: CLI + Desktop Combined Workflow

**Branch:** `2.0-CLI-Desktop-Combined-Workflow`
**Active Period:** November 2025 - December 2025
**Status:** Archived (superseded by V3.0)

---

## What V2 Was

Version 2.0 attempted to create a hybrid automation system combining:

1. **File-based queue management** - JSON files for job tracking (`.processing-requests.json`)
2. **Shell script automation** - Bash scripts for watching, batching, and processing
3. **LaunchAgent persistence** - macOS launchd service for always-on monitoring
4. **Rich terminal dashboard** - Real-time visual monitoring with cost tracking
5. **MCP server integration** - TypeScript MCP server for Claude Desktop interaction
6. **Multi-model LLM backend** - OpenRouter, Claude, Gemini fallback chain

### Core Components

| Component | Purpose | Status |
|-----------|---------|--------|
| `watch-transcripts.sh` | Poll `/transcripts/` for new files | Worked reliably |
| `com.editorial-assistant.watcher.plist` | LaunchAgent for persistence | Worked |
| `process_queue_visual.py` | Rich TUI dashboard | Feature complete |
| `llm_backend.py` | Multi-provider API abstraction | Solid foundation |
| `mcp-server/` | Claude Desktop integration | Functional |
| `.processing-requests.json` | File-based job queue | Fragile |

---

## What Worked Well

### 1. Visual Dashboard (Rich TUI)
The `rich` library dashboard was genuinely useful:
- Real-time progress tracking
- Cost-per-project visibility
- Sparkline cost visualization
- Session statistics
- Backend distribution metrics

**Lesson for V3:** Users value visibility into processing status and costs. Keep these features.

### 2. Multi-Model LLM Backend
The `llm_backend.py` fallback system proved valuable:
- Primary: OpenRouter (model rotation for cost optimization)
- Fallback: Claude API direct
- Emergency: Gemini CLI

**Lesson for V3:** Model abstraction layer is worth maintaining. Dynamic model registry is a good V3 enhancement.

### 3. Agent Prompt System
The `.claude/agents/*.md` prompt files were well-organized:
- `analyst.md` - Brainstorming phase
- `formatter.md` - Transcript formatting
- `copy-editor.md` - Revision workflow

**Lesson for V3:** Keep prompt versioning and separate agent instructions. Add prompt versioning to database.

### 4. MCP Server Architecture
The TypeScript MCP server successfully bridged Claude Desktop and local files:
- Project listing and loading
- Revision saving with auto-versioning
- Queue status visibility

**Lesson for V3:** MCP is the right integration pattern for Claude Desktop. Extend it for V3 API.

---

## What Didn't Work

### 1. File-Based Queue Management
**Problem:** JSON file as job queue led to:
- Race conditions when multiple processes read/wrote simultaneously
- No atomic operations
- Stale job recovery impossible
- No partial progress persistence

**Evidence:** 7 jobs stuck in "processing" for 6+ days with no recovery mechanism.

**V3 Solution:** SQLite database with proper job queue semantics (claimed_at, expires_at, heartbeats).

### 2. Shell Script Orchestration
**Problem:** Bash scripts for workflow coordination were:
- Hard to debug
- No error recovery
- No partial state persistence
- Platform-specific (macOS launchd)

**V3 Solution:** Python-based orchestration with FastAPI backend, proper error handling, and database-backed state.

### 3. Large Transcript Handling
**Problem:** Transcripts >100K characters caused:
- Timeouts with CLI agents
- No chunking strategy
- Memory issues in dashboard

**Evidence:** MCP CLI-Agent delegation hung indefinitely on 60K+ character transcripts.

**V3 Solution:** Chunking pipeline with parallel processing for large transcripts.

### 4. SRT Speaker Normalization
**Problem:** Inconsistent speaker markers in transcripts:
- Full names used once, abbreviations thereafter
- Some dialogue with no speaker markers
- Regex parsing failed on edge cases

**V3 Solution:** Pre-processing step to normalize speaker markers before main processing.

### 5. No Step-Level Recovery
**Problem:** Jobs were all-or-nothing:
- If formatting failed after brainstorming succeeded, both had to re-run
- No checkpoint system
- `needs_brainstorming` / `needs_formatting` flags not updated mid-process

**V3 Solution:** Step-level status tracking with resumable workflows.

---

## Key Metrics

### Processing Statistics (Nov-Dec 2025)
- **Transcripts processed:** 22+
- **Average processing time:** Variable (1-15 min depending on length)
- **Failure rate:** ~15% (mostly timeout/stale jobs)
- **Cost:** Tracked per-session via dashboard

### Architecture Complexity
- **Shell scripts:** 10
- **Python scripts:** 8
- **Config files:** 3
- **LaunchAgents:** 1
- **MCP server files:** 12

---

## Lessons That Informed V3.0

### Architecture
1. **Database over files** - SQLite provides ACID guarantees that JSON files can't
2. **API over scripts** - FastAPI enables web dashboard and better orchestration
3. **Step-level tracking** - Each processing step needs independent status
4. **Heartbeat mechanism** - Detect and recover stale jobs automatically

### User Experience
1. **Visibility is critical** - Dashboard cost/progress tracking was valued
2. **Resume is essential** - ADHD-friendly resume features save time
3. **Error messages matter** - Raw JSON error dumps were unusable

### Operations
1. **Chunking required** - Large transcripts need special handling
2. **Pre-processing helps** - SRT normalization prevents downstream errors
3. **Dead letter queue** - Failed jobs need somewhere to go for manual review

---

## Files to Archive

With V2 shutdown, these components are now dormant:

### LaunchAgent (Removed)
```
~/Library/LaunchAgents/com.editorial-assistant.watcher.plist
```
Status: Unloaded via `launchctl unload`

### Watch State
```
.watch-state  # Processed transcript tracking
```

### Shell Scripts (Superseded by V3 API)
```
scripts/watch-transcripts.sh
scripts/batch-process-transcripts.sh
scripts/auto-process-project.sh
scripts/auto-archive-transcript.sh
scripts/check-missed-transcripts.sh
```

### Dashboard (Superseded by V3 Web Dashboard)
```
scripts/process_queue_visual.py
scripts/dashboard/
```

---

## Migration Notes

### For V3.0 Development
1. **Keep:** `llm_backend.py` model abstraction layer
2. **Keep:** `.claude/agents/` prompt files
3. **Keep:** `mcp-server/` as foundation for V3 MCP
4. **Migrate:** Queue logic to SQLite
5. **Migrate:** Dashboard to React web app
6. **Add:** FastAPI backend for orchestration

### Data Migration
- No database migration needed (V2 was file-based)
- Processed transcripts in `transcripts/archive/` are permanent
- Output projects in `OUTPUT/` are permanent
- `.processing-requests.json` can be cleared

---

## Conclusion

V2 successfully demonstrated that:
1. AI-assisted editorial workflows are viable for PBS Wisconsin
2. Cost tracking and visibility are essential
3. Multi-model backends provide resilience
4. MCP integration enables Claude Desktop workflows

V2 also revealed that:
1. File-based queues don't scale
2. Shell script orchestration is fragile
3. Large content needs chunking
4. Step-level recovery is necessary

These lessons directly shaped the V3.0 design, which addresses each limitation while preserving what worked.

---

*Document created: 2025-12-30*
*Branch archived: 2.0-CLI-Desktop-Combined-Workflow*
