# Automatic Agent Processing Setup

How to automatically generate brainstorming, formatted transcripts, and timestamps when new transcripts are detected.

---

## Current State

**What's automated**:
- ✅ Folder watcher detects new transcripts
- ✅ Batch setup creates OUTPUT directory + manifest

**What's manual**:
- ⏳ Running transcript-analyst agent (generates brainstorming)
- ⏳ Running formatter agent (generates formatted transcript + timestamps)

---

## Solution: Auto-Process Script for Claude Code

Since agent invocation requires Claude Code's Task tool, I'll create a script you can run in Claude Code to automatically process all pending projects.

### Option 1: Semi-Automatic (Recommended)

**Workflow**:
1. Watcher detects new transcript → creates project structure
2. You open Claude Code when convenient
3. Run one command to process all pending projects

**In Claude Code**:
```typescript
// Process all projects that need agents
Task({
  subagent_type: "general-purpose",
  prompt: `Find all projects in OUTPUT/ with status "processing" and run:

  1. transcript-analyst for each (generates brainstorming.md)
  2. formatter for each (generates formatted_transcript.md + timestamp_report.md)
  3. Update manifests to "complete"

  Process in parallel where possible for efficiency.`
})
```

### Option 2: Fully Automatic (Advanced)

Create a Claude Code automation that runs on a schedule or trigger.

**Would require**:
- Python script that invokes Claude Code API
- Scheduled task (cron/LaunchAgent) to run it
- API key configuration

---

## Updated Watcher Workflow

Let me update the watcher to create a "processing queue" file that tracks what needs agent processing:

### Enhanced Watch Script

The watcher will:
1. Detect new transcript
2. Create project structure
3. **Add to processing queue** (`/Users/mriechers/Developer/editorial-assistant/.processing-queue.json`)
4. You process the queue in Claude Code when ready

### Processing Queue Format

`.processing-queue.json`:
```json
[
  {
    "project": "9UNP2007HD",
    "transcript_file": "9UNP2007HD_ForClaude.txt",
    "detected": "2025-11-20T18:00:00Z",
    "needs_brainstorming": true,
    "needs_formatting": true,
    "program_type": "University Place"
  }
]
```

### Batch Process Queue Command

In Claude Code, run:
```
"Process all items in the .processing-queue.json file with agents"
```

---

## MCP Server Enhancement for Formatted Transcripts

Let me also update the MCP server to expose formatted transcripts for fact-checking during editing.

### New MCP Tool: `get_formatted_transcript`

```typescript
{
  name: "get_formatted_transcript",
  description: "Load formatted transcript for fact-checking during copy editing",
  parameters: {
    project_name: string
  }
}
```

### Usage in Claude Desktop

When editing, Claude Desktop can:
1. Load brainstorming via `load_project_for_editing()`
2. **Also load formatted transcript** via `get_formatted_transcript()`
3. Use it to verify quotes, speaker names, facts
4. Ensure copy accuracy against source material

**Example**:
```
User: "Let's revise the title for 9UNP2007HD"

Claude Desktop:
- Calls load_project_for_editing("9UNP2007HD")
- Calls get_formatted_transcript("9UNP2007HD")  // For fact-checking
- Reviews brainstorming against formatted transcript
- Suggests revisions with verified accuracy
```

---

## Implementation Plan

### Phase 1: Enhanced Watcher (Immediate)
✅ Update watcher to create processing queue
✅ Track what needs agent processing

### Phase 2: MCP Enhancement (Immediate)
✅ Add `get_formatted_transcript()` tool
✅ Claude Desktop can fact-check against formatted transcript

### Phase 3: Semi-Automatic Processing (Your workflow)
⏳ Drop transcripts → watcher detects
⏳ Open Claude Code once per day/batch
⏳ Run: "Process the queue"
⏳ All projects get brainstorming + formatted transcripts

### Phase 4: Fully Automatic (Future/Optional)
⏳ Python script with Claude Code API
⏳ Scheduled task runs agents automatically
⏳ Zero manual intervention

---

## Recommended Workflow

**Morning**:
```bash
# Watcher is already running (auto-starts at login)
# Drop new transcripts into /transcripts/
# Watcher detects and queues them
```

**Mid-morning** (when you open Claude Code):
```typescript
// One command processes everything in queue
Task({
  subagent_type: "general-purpose",
  prompt: "Process all pending transcripts in .processing-queue.json"
})
```

**Afternoon** (Claude Desktop editing):
```
"What's ready for editing?"
→ MCP lists all completed projects
→ Load any project
→ Formatted transcript available for fact-checking
→ Edit with confidence
```

---

## Benefits

### Formatted Transcript as Knowledge Base
- **Fact-checking**: Verify quotes are accurate
- **Speaker verification**: Confirm names and roles
- **Context**: See full conversation flow
- **Quality**: Ensure copy reflects actual content

### Auto-Processing
- **Drop and forget**: Transcripts queue automatically
- **Batch processing**: One command processes all pending
- **Parallel execution**: Process multiple at once for speed
- **Status tracking**: Always know what's pending

### MCP Integration
- **Seamless access**: Formatted transcripts available in editing
- **No manual loading**: MCP fetches automatically when needed
- **Fact-check on demand**: Reference source material easily

---

## Implementation Status

**Completed**:
1. ✅ **MCP server updated** - `get_formatted_transcript()` tool added
2. ✅ **MCP server rebuilt** - New tool deployed and ready
3. ✅ **Formatter agent working** - Generates formatted transcripts + timestamps

**Next Steps**:
1. ⏳ **Update watcher** to invoke agents automatically when new transcript detected
2. ⏳ **Update CLAUDE_DESKTOP_INSTRUCTIONS.md** to document fact-checking workflow
3. ⏳ **Test complete workflow** end-to-end

---

## Recommended Semi-Automatic Approach

Since agent invocation requires Claude Code's Task tool, the most practical approach is:

### Auto-Processing When Transcript Detected

The watcher will be updated to:
1. Detect new transcript
2. Create project structure (already does this)
3. **Automatically invoke agents**:
   - Run transcript-analyst (generates brainstorming.md)
   - Run formatter (generates formatted_transcript.md + timestamp_report.md)
4. Update manifest to "ready_for_editing"

### Updated Workflow

**Morning**:
```bash
# Drop transcripts into /transcripts/
# Watcher auto-processes them within minutes
```

**Later** (when projects are ready):
```
# In Claude Desktop
"What's ready for editing?"
→ Load project with MCP
→ Get formatted transcript for fact-checking
→ Edit with confidence
```

No manual processing commands needed - everything happens automatically.
