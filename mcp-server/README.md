# Editorial Assistant MCP Server

MCP server that bridges Claude Code batch processing with Claude Chat interactive editing.

## What It Does

This server exposes 4 tools to Claude Chat for discovering and working with transcripts processed by Claude Code agents:

1. **list_processed_projects** - Discover what's ready for editing
2. **load_project_for_editing** - Load full context (transcript, brainstorming, revisions)
3. **save_revision** - Save copy revisions back with auto-versioning
4. **get_project_summary** - Quick status check

## Installation

```bash
cd /Users/mriechers/Developer/editorial-assistant/mcp-server
npm install
npm run build
```

## Configuration for Claude Chat

Add this to your Claude Chat MCP settings:

### Option 1: Using npx (Recommended)

```json
{
  "mcpServers": {
    "editorial-assistant": {
      "command": "npx",
      "args": [
        "-y",
        "editorial-assistant-mcp-server"
      ],
      "cwd": "/Users/mriechers/Developer/editorial-assistant"
    }
  }
}
```

### Option 2: Direct path to built server

```json
{
  "mcpServers": {
    "editorial-assistant": {
      "command": "node",
      "args": [
        "/Users/mriechers/Developer/editorial-assistant/mcp-server/build/index.js"
      ]
    }
  }
}
```

## Workflow

### 1. Batch Processing in Claude Code

```bash
# Add transcripts to /transcripts/
cp ~/Desktop/9UNP2005HD_ForClaude.txt transcripts/

# Run batch setup
./scripts/batch-process-transcripts.sh

# In Claude Code, process each project:
# - transcript-analyst generates brainstorming
# - formatter generates formatted transcript + timestamps
```

### 2. Interactive Editing in Claude Chat

```
User: "What recent transcripts have we processed?"

Chat (via MCP): *calls list_processed_projects()*
"We've processed 3 projects recently:
 1. 9UNP2005HD - University Place lecture (ready for editing)
 2. 2WLI1206HD - Wisconsin Life episode (processing)
 3. 6GWQ2504 - Garden Wanderings (complete)"

User: "Let's work on the University Place one"

Chat (via MCP): *calls load_project_for_editing("9UNP2005HD")*
"I've loaded:
 - Transcript (56min lecture on Wisconsin labor history)
 - 3 title options from brainstorming
 - 20 keywords extracted
 - Formatted transcript with timestamps

 What would you like to edit?"

[Conversational back-and-forth editing]

User: "Save that revision"

Chat (via MCP): *calls save_revision("9UNP2005HD", content)*
"✓ Saved as copy_revision_v1.md in OUTPUT/9UNP2005HD/"
```

## Tool Reference

### list_processed_projects()

**Parameters**: None

**Returns**: Array of projects with status

```json
[
  {
    "name": "9UNP2005HD",
    "program": "University Place",
    "processed_date": "2025-11-18",
    "has_brainstorming": true,
    "has_formatted_transcript": true,
    "has_timestamps": true,
    "has_revisions": false,
    "status": "ready_for_editing",
    "transcript_summary": "56-minute lecture on Wisconsin labor history",
    "manifest_path": "/path/to/manifest.json"
  }
]
```

### load_project_for_editing(project_name)

**Parameters**:
- `project_name`: string (e.g., "9UNP2005HD")

**Returns**: Complete project context

```json
{
  "project_name": "9UNP2005HD",
  "manifest": { ... },
  "transcript": {
    "file": "9UNP2005HD_ForClaude.txt",
    "content": "[full transcript text]",
    "duration": "56:32"
  },
  "brainstorming": "[brainstorming.md content]",
  "formatted_transcript": "[formatted_transcript.md content]",
  "latest_revision": "[copy_revision_v2.md content or null]",
  "program_rules": "University Place"
}
```

### save_revision(project_name, content, version?)

**Parameters**:
- `project_name`: string
- `content`: string (markdown content)
- `version`: number (optional, auto-increments if not provided)

**Returns**: File path confirmation

```
Revision saved to: /Users/mriechers/Developer/editorial-assistant/OUTPUT/9UNP2005HD/copy_revision_v3.md
```

**Side effects**:
- Creates `copy_revision_vN.md` in project directory
- Updates manifest.json with revision metadata
- Logs editing session

### get_project_summary(project_name)

**Parameters**:
- `project_name`: string

**Returns**: Quick status summary (same format as list_processed_projects but for single project)

## Project Status Values

- `"processing"` - Brainstorming exists, but not complete
- `"ready_for_editing"` - Brainstorming + formatted transcript available
- `"revision_in_progress"` - Revisions exist
- `"complete"` - All deliverables finalized
- `"unknown"` - No manifest or indeterminate state

## Troubleshooting

### Server doesn't appear in Claude Chat

1. Check Claude Chat MCP settings are correct
2. Verify build succeeded: `npm run build`
3. Test server manually: `npm start` (should show "Editorial Assistant MCP Server running on stdio")
4. Check logs in Claude Chat developer tools

### "No projects found"

1. Verify `/OUTPUT/` directory has project subdirectories
2. Check that projects have either:
   - `manifest.json` file
   - At least `brainstorming.md` or `digital_shorts_report.md`

### "Transcript not found" when loading project

1. Verify transcript file exists in `/transcripts/`
2. Check manifest.json has correct `transcript_file` value
3. Ensure filename matches exactly (case-sensitive)

## Development

### Build

```bash
npm run build
```

### Watch mode (auto-rebuild on changes)

```bash
npm run watch
```

### Test directly

```bash
npm start
# Server runs on stdio - send MCP protocol messages
```

## Architecture

```
Claude Chat (conversational editing)
     ↕
MCP Server (this)
     ↕
File System
  ├─ /OUTPUT/{project}/        # Processed deliverables
  │   ├─ manifest.json
  │   ├─ brainstorming.md
  │   ├─ formatted_transcript.md
  │   ├─ timestamp_report.md
  │   └─ copy_revision_v*.md
  └─ /transcripts/              # Source transcripts
      └─ {project}_ForClaude.txt
```

## Next Steps

1. Install and build the server
2. Add configuration to Claude Chat
3. Process a test transcript in Claude Code
4. Open Claude Chat and ask "What's ready for editing?"
5. Load a project and start an editing session

## Future Enhancements

- CSV import for SEMRush keyword data
- SEMRush API integration (if API key available)
- Comparison tool for revision diffs
- Bulk status updates
- Search/filter projects by program type or status
