# MCP Server Specification for Editorial Assistant

**Purpose**: Bridge Claude Code batch processing with Claude Chat interactive editing

---

## Server Capabilities

### 1. Processed Projects Discovery

**Tool**: `list_processed_projects`

**What it does**: Lists all projects in OUTPUT/ with their current status

**Returns**:
```json
{
  "projects": [
    {
      "name": "9UNP2005HD",
      "program": "University Place",
      "processed_date": "2025-11-18",
      "has_brainstorming": true,
      "has_formatted_transcript": true,
      "has_timestamps": true,
      "has_revisions": false,
      "status": "ready_for_editing",
      "transcript_summary": "56-minute lecture on Wisconsin labor history by Dr. Sarah Johnson"
    }
  ]
}
```

**Chat usage**:
```
User: "What recent transcripts have we processed?"
Chat: *calls list_processed_projects()*
Chat: "We've processed 3 transcripts recently:
      1. 9UNP2005HD - University Place lecture (ready for editing)
      2. 2WLI1206HD - Wisconsin Life episode (needs review)
      3. 2BUC0000HDDVD01 - Bucky documentary extra (complete)"
```

---

### 2. Load Project Context

**Tool**: `load_project_for_editing`

**Parameters**:
- `project_name`: e.g., "9UNP2005HD"

**What it does**: Loads all artifacts for conversational editing session

**Returns**:
```json
{
  "project_name": "9UNP2005HD",
  "transcript": {
    "file": "9UNP2005HD_ForClaude.txt",
    "content": "[full transcript text]",
    "duration": "56:32"
  },
  "brainstorming": {
    "title_options": [...],
    "description_options": [...],
    "keywords": [...]
  },
  "formatted_transcript": "[formatted version]",
  "user_draft": null,  // Will be populated if exists
  "program_rules": "University Place"
}
```

**Chat usage**:
```
User: "Let's work on the UW Place lecture"
Chat: *loads project context*
Chat: "I've loaded the Wisconsin labor history lecture.
      I see we generated 3 title options. Would you like to:
      1. Review and refine the brainstorming?
      2. Upload your draft for revision?
      3. Discuss specific aspects of the content?"
```

---

### 3. Save Revision

**Tool**: `save_revision`

**Parameters**:
- `project_name`
- `revision_content`: The markdown content
- `version`: Auto-incrementing (Rev 1, Rev 2, etc.)

**What it does**: Saves copy revision back to OUTPUT/{project}/

**Returns**: Confirmation + file path

**Chat usage**:
```
User: "The revised short description looks good"
Chat: *saves revision*
Chat: "✓ Saved as copy_revision_v2.md in OUTPUT/9UNP2005HD/
      Ready for you to implement or request further changes."
```

---

### 4. Get SEO Data (Future Enhancement)

**Tool**: `get_semrush_keywords`

**Parameters**:
- `topic`: e.g., "Wisconsin labor history"
- `cached_results`: Check if we have recent data

**What it does**:
- Option A: Read from uploaded CSV/screenshot OCR
- Option B: Direct SEMRush API integration (if API key provided)
- Option C: Prompt user to upload data if not cached

**Returns**: Structured keyword data

---

### 5. Compare Versions

**Tool**: `compare_revisions`

**Parameters**:
- `project_name`
- `version_a`: e.g., "brainstorming"
- `version_b`: e.g., "copy_revision_v2"

**What it does**: Side-by-side diff of metadata versions

**Returns**: Comparison table

---

## MCP Server Implementation

### Option 1: Filesystem MCP (Simplest)

Use the standard filesystem MCP server, pointed at editorial-assistant:

```json
{
  "mcpServers": {
    "editorial-outputs": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/mriechers/Developer/editorial-assistant/OUTPUT"
      ]
    },
    "editorial-transcripts": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/mriechers/Developer/editorial-assistant/transcripts"
      ]
    }
  }
}
```

**Pros**: Zero custom code, works immediately
**Cons**: Chat has to navigate file structure manually

---

### Option 2: Custom Editorial MCP Server (Recommended)

Create custom server with editorial-specific tools:

**Location**: `/Users/mriechers/Developer/editorial-assistant/mcp-server/`

**Structure**:
```
mcp-server/
├── package.json
├── src/
│   ├── index.ts          # Main server
│   ├── tools/
│   │   ├── list-projects.ts
│   │   ├── load-project.ts
│   │   ├── save-revision.ts
│   │   └── compare-versions.ts
│   └── utils/
│       ├── manifest-parser.ts
│       └── project-scanner.ts
└── README.md
```

**Tools exposed to Chat**:
1. `list_processed_projects()` → Discovery
2. `load_project_for_editing(name)` → Context loading
3. `save_revision(name, content, version)` → Save work
4. `compare_revisions(name, v1, v2)` → Diff tool
5. `get_project_status(name)` → Check completeness

---

## Workflow Integration

### Morning Batch Processing (Claude Code)

```bash
# Add new transcripts to /transcripts/
# Run batch setup
./scripts/batch-process-transcripts.sh

# Claude Code session - process each:
# 1. transcript-analyst generates brainstorming
# 2. formatter generates formatted transcript + timestamps
# 3. Results saved to OUTPUT/{project}/
# 4. manifest.json updated with status
```

### Interactive Editing (Claude Chat)

```
User: "What's ready for editing?"

Chat (via MCP): *calls list_processed_projects()*
"3 projects ready:
 1. 9UNP2005HD - University Place lecture
 2. 2WLI1206HD - Wisconsin Life episode
 3. 6GWQ2504 - Garden Wanderings"

User: "Let's work on the University Place one"

Chat (via MCP): *loads project context*
"I've loaded:
 - Transcript (56min lecture on labor history)
 - 3 title options from brainstorming
 - 20 keywords extracted
 - Formatted transcript with timestamps

 What would you like to edit?"

User: "I have draft copy to review. Here's my title: [paste]"

Chat: *analyzes against loaded context*
"Comparing your draft to the transcript:
 - Title uses 'Dr.' honorific (University Place rule: avoid)
 - Description has 'watch as' (prohibited language)
 - Let me suggest revisions..."

[Conversational back-and-forth editing]

User: "Perfect, save that revision"

Chat (via MCP): *calls save_revision()*
"✓ Saved to OUTPUT/9UNP2005HD/copy_revision_v1.md
 Ready for implementation or further refinement."
```

---

## SEO Data Integration Options

### Current State (Pain Point)
1. You run SEMRush bulk search
2. Screenshot results
3. Upload to Chat
4. Chat extracts via vision

### Improvement Option 1: CSV Upload

```
User: *uploads SEMRush CSV export*

Chat (via MCP): *parses CSV, structures data*
"I've ingested keyword data for 'Wisconsin labor history':
 - High volume: 'Wisconsin history' (12K/mo)
 - Medium volume: 'labor unions Wisconsin' (850/mo)
 - Distinctive: 'Progressive Era labor' (90/mo, low competition)

 Should I integrate these into the copy revisions?"
```

**Implementation**:
- Add CSV parsing to MCP server
- Tool: `import_semrush_data(csv_content, project_name)`
- Caches to `OUTPUT/{project}/seo_data.json`

### Improvement Option 2: SEMRush API Integration

**If you have API access**:
```typescript
// In MCP server
async function fetchKeywordData(topic: string) {
  const response = await fetch('https://api.semrush.com/analytics/v1/', {
    params: {
      key: process.env.SEMRUSH_API_KEY,
      type: 'phrase_all',
      phrase: topic,
      database: 'us'
    }
  });
  return parseKeywordData(response);
}
```

**Chat usage**:
```
User: "Research keywords for Wisconsin labor history"

Chat (via MCP): *calls SEMRush API*
"Researching... found 47 related keywords.
 Top opportunities:
 - 'Wisconsin labor movement' (1.2K/mo, moderate difficulty)
 - 'Progressive Era Wisconsin' (890/mo, easy)

 Should I generate a keyword report?"
```

### Improvement Option 3: Hybrid OCR + Structured

```
User: *uploads SEMRush screenshot*

Chat: *OCR extracts data, structures it*
      *calls MCP to save structured version*

"I've extracted and cached this keyword data.
 Next time you can just reference 'Wisconsin labor history keywords'
 without re-uploading."
```

---

## Recommended Implementation Path

### Phase 1: Basic MCP (This Week)

1. **Use standard filesystem MCP** for OUTPUT/ and transcripts/
2. **Create manifest.json** in each project (batch script does this)
3. **Test Chat access** to processed files

### Phase 2: Custom Tools (Next Week)

1. **Build custom MCP server** with:
   - `list_processed_projects()`
   - `load_project_for_editing(name)`
   - `save_revision(name, content)`

2. **Test editing workflow**:
   - Process transcript in Code
   - Edit in Chat with MCP context
   - Verify Chat can save revisions back

### Phase 3: SEO Enhancement (Future)

1. **Add CSV import** to MCP server
2. **Or** integrate SEMRush API if available
3. **Or** improve OCR workflow with caching

---

## Example manifest.json Format

```json
{
  "transcript_file": "9UNP2005HD_ForClaude.txt",
  "project_name": "9UNP2005HD",
  "program_type": "University Place",
  "processing_started": "2025-11-18T14:30:00Z",
  "processing_completed": "2025-11-18T14:45:00Z",
  "status": "ready_for_editing",

  "content_summary": "56-minute lecture on Wisconsin labor history during Progressive Era by Dr. Sarah Johnson",

  "deliverables": {
    "brainstorming": {
      "file": "brainstorming.md",
      "created": "2025-11-18T14:32:00Z",
      "agent": "transcript-analyst"
    },
    "formatted_transcript": {
      "file": "formatted_transcript.md",
      "created": "2025-11-18T14:40:00Z",
      "agent": "formatter"
    },
    "timestamps": {
      "file": "timestamp_report.md",
      "created": "2025-11-18T14:40:00Z",
      "agent": "formatter"
    },
    "copy_revisions": [],
    "seo_data": null
  },

  "editing_sessions": [],

  "metadata": {
    "duration": "56:32",
    "speakers": ["Host: Michael Stevens", "Guest: Dr. Sarah Johnson"],
    "topics": ["Wisconsin labor history", "Progressive Era", "unions"]
  }
}
```

---

## Chat Project Instructions Enhancement

Add to your Claude Chat project instructions:

```markdown
## Editorial Assistant Workflow

You have access to processed transcripts via MCP server.

### Discovery
When user asks "what can we work on?" or "what's ready for editing?":
1. Use MCP to list processed projects
2. Show projects with `status: "ready_for_editing"`
3. Summarize each: program, topic, what's been generated

### Editing Session
When user selects a project to edit:
1. Load full project context via MCP (transcript + brainstorming + any existing revisions)
2. Ask what type of editing: review brainstorming, revise draft, or start fresh
3. Apply all editorial rules from AGENT INSTRUCTIONS
4. Save revisions back via MCP with version tracking

### SEO Integration
If user uploads SEMRush data:
1. Parse and structure the keyword data
2. Save to project via MCP
3. Integrate into copy recommendations
4. Reference in revision reasoning

### Handoff to Code
If user requests:
- Formatted transcripts → "Run formatter agent in Claude Code"
- Batch processing → "Add transcripts and run batch script"
- New projects → "Use Claude Code for initial processing"
```

---

## Next Steps

Would you like me to:

1. **Build the basic custom MCP server** with the 5 core tools?
2. **Create the batch processing workflow** that agents can use?
3. **Design the CSV import tool** for SEMRush data?
4. **Set up the Chat project** with MCP configuration?

I'd recommend starting with #1 (custom MCP server) - it's the bridge that makes everything else work.
