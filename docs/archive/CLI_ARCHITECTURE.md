# Editorial Assistant CLI Architecture

## Overview

This document describes the architecture for the ADHD-friendly CLI version of the PBS Wisconsin Editorial Assistant.

## Key Design Goals

1. **Format Consistency**: Use file-based templates to ensure consistent output structure
2. **ADHD-Friendly UX**: Always-visible progress, smart resume, gentle guidance
3. **Conversational Flow**: Preserve the staged input pattern (transcript → draft → data)
4. **Integration with Claude Code**: Leverage the video-metadata-seo-editor agent

## Architecture Decision

**Hybrid Approach**: The CLI provides the user-facing interface, state management, and UX, while delegating the actual content generation to the video-metadata-seo-editor agent running in Claude Code.

### Why This Works

1. **CLI handles**: Project management, progress tracking, file organization, user interaction
2. **Agent handles**: Content analysis, metadata generation, editorial judgment
3. **Templates provide**: Format consistency and validation structure
4. **User benefits**: ADHD-friendly interface + expert editorial assistance + format guarantees

## Workflow

### User Journey

```
1. User: editorial-assistant start "Project Name"
   → CLI creates project directory and state file
   → Displays welcome with clear next steps

2. User: editorial-assistant transcript path/to/file.txt
   → CLI copies transcript to project folder
   → Launches Claude Code with video-metadata-seo-editor agent
   → Agent processes transcript using brainstorming template
   → CLI saves output as 01_brainstorming.md
   → Updates state, shows celebration, suggests next step

3. User: editorial-assistant revise <screenshot or text>
   → CLI captures draft copy
   → Launches agent for Phase 2 (revision)
   → Agent creates revision document using template
   → CLI saves as 02_revision_v1.md
   → Shows summary, asks if another round needed

4. User: editorial-assistant analyze [optional]
   → CLI prompts for SEMRush data or does web search
   → Agent creates keyword analysis
   → CLI saves reports

5. User: editorial-assistant finalize
   → Agent generates final deliverables
   → CLI packages everything
   → Celebration and project summary
```

## Technical Implementation

### Directory Structure

```
editorial-assistant/
├── editorial_assistant.py           # Main CLI application
├── templates/                        # Output format templates
│   ├── brainstorming_standard.md
│   ├── copy_revision_document.md
│   ├── digital_shorts_brainstorming.md
│   ├── keyword_analysis.md
│   ├── implementation_report.md
│   ├── formatted_transcript.md
│   └── timestamp_report.md
├── knowledge/                        # Reference materials for agent
│   ├── ap_styleguide.pdf
│   ├── Transcript Style Guide.pdf
│   └── ...
├── Haiku 4.5 version.md             # Agent system prompt
└── .claude/
    └── commands/
        └── editorial-assistant.md    # Slash command for agent integration
```

### Project Directory Structure

```
~/editorial-assistant-projects/project-name/
├── .state.json                      # Project state and progress
├── transcript.txt                   # Source transcript
├── draft_screenshot.png             # Optional: user's draft
├── 01_brainstorming.md             # Phase 1 output
├── 02_revision_v1.md               # Phase 2 output (versioned)
├── 02_revision_v2.md               # Phase 2 revision
├── 03_analysis.md                  # Phase 3 keyword analysis (optional)
├── 04_implementation.md            # Phase 3 action plan (optional)
├── 05_formatted_transcript.md      # Phase 4 deliverable
└── 06_timestamps.md                # Phase 4 deliverable
```

### State Management

`.state.json` structure:
```json
{
  "project_name": "here-and-now-interview",
  "created_at": "2025-11-06T10:30:00",
  "last_modified": "2025-11-06T11:45:00",
  "current_phase": 2,
  "completed_phases": [1],
  "files": {
    "brainstorming": [{
      "path": "01_brainstorming.md",
      "version": 1,
      "created_at": "2025-11-06T10:45:00"
    }],
    "revision": [{
      "path": "02_revision_v1.md",
      "version": 1,
      "created_at": "2025-11-06T11:30:00"
    }]
  },
  "notes": [{
    "text": "Check with boss about Stroebel title",
    "timestamp": "2025-11-06T11:40:00"
  }],
  "transcript_path": "transcript.txt",
  "program_type": "Here and Now"
}
```

## Integration with Claude Code

### Approach 1: Subprocess (Current Plan)

The CLI spawns Claude Code as a subprocess:

```python
def invoke_agent(self, phase: Phase, inputs: Dict[str, Any]) -> str:
    """Invoke video-metadata-seo-editor agent via Claude Code"""
    # Build prompt for agent
    prompt = self._build_agent_prompt(phase, inputs)

    # Call Claude Code CLI
    result = subprocess.run([
        "claude",
        "chat",
        "--agent", "video-metadata-seo-editor",
        "--prompt", prompt
    ], capture_output=True, text=True)

    return result.stdout
```

### Approach 2: Direct API (Alternative)

Use Anthropic API directly:

```python
import anthropic

def invoke_agent(self, phase: Phase, inputs: Dict[str, Any]) -> str:
    """Invoke agent via Anthropic API"""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Load system prompt and templates
    system_prompt = self._load_system_prompt()
    template = self._load_template(phase)

    message = client.messages.create(
        model="claude-sonnet-4",
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": self._build_user_message(phase, inputs, template)
        }]
    )

    return message.content
```

### Approach 3: Interactive Session (Future)

Keep Claude Code session running, send commands interactively:

```python
def start_agent_session(self):
    """Start persistent Claude Code session"""
    self.agent_process = subprocess.Popen([
        "claude",
        "chat",
        "--agent", "video-metadata-seo-editor",
        "--interactive"
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

def send_to_agent(self, message: str) -> str:
    """Send message to running agent session"""
    self.agent_process.stdin.write(message + "\n")
    self.agent_process.stdin.flush()
    return self._read_agent_response()
```

## ADHD-Friendly Features

### 1. Always-Visible Progress

Every command output includes:
```
╭─ Progress ──────────────────────────────────────────────╮
│ ✓ ✓ → ⃝ ⃝                                              │
│ Brainstorm → Edit → Keywords → Finalize               │
│ ████████████░░░░░░░░ 50% | ~6 min left                 │
╰─────────────────────────────────────────────────────────╯
```

### 2. Smart Resume

When resuming a project:
```
Welcome back! You've been away for 3 hours.

Last session recap:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You were working on: Here and Now Interview

What you completed:
  ✓ Brainstorming (01_brainstorming.md)
  ✓ Draft revision (02_revision_v1.md)

Your note to yourself: "Check if apprenticeship should be
                        emphasized more in keywords"

Pick up where you left off? [Y/n/s]
```

### 3. Celebration Milestones

```
🎉 Brainstorming complete!

Progress: ████████░░░░░░░░ 25% complete!

Nice work! You've finished Phase 1.
Next up: Phase 2 - Editing & Revision

Ready to continue? [Y/n]
```

### 4. Context-Sensitive Help

```
──────────────────────────────────────────────────────────
💡 Common next steps: 'revise' | 'preview' | 'analyze'
   Type '?' for all commands
```

### 5. Time Estimates

```
Next step: Generate formatted transcript
⏱ Estimated time: 2-3 minutes

This will create an AP-style transcript ready for your CMS.
```

## Validation System

### Template-Based Validation

Each template includes validation rules:

```python
def validate_brainstorming(content: str) -> List[str]:
    """Validate brainstorming document format"""
    errors = []

    # Check required sections
    required = ["Content Summary", "Title Options", "SEO Keywords"]
    for section in required:
        if f"## {section}" not in content:
            errors.append(f"Missing required section: {section}")

    # Check character counts
    title_pattern = r"([A-Za-z ]+) \((\d+) chars\)"
    for match in re.finditer(title_pattern, content):
        title, stated_count = match.groups()
        actual_count = len(title)
        if actual_count != int(stated_count):
            errors.append(f"Title count mismatch: {title}")

    # Check prohibited language
    prohibited = ["watch as", "discover", "will show"]
    for phrase in prohibited:
        if phrase.lower() in content.lower():
            errors.append(f"Prohibited language: {phrase}")

    return errors
```

## Commands Reference

### Core Commands

- `editorial-assistant` - Show welcome / smart resume
- `editorial-assistant start <name>` - Create new project
- `editorial-assistant status` - Show current project status
- `editorial-assistant continue` - Resume last project
- `editorial-assistant transcript <path>` - Process transcript (Phase 1)
- `editorial-assistant revise [input]` - Create/update revision (Phase 2)
- `editorial-assistant analyze` - Keyword analysis (Phase 3)
- `editorial-assistant finalize` - Generate final deliverables (Phase 4)
- `editorial-assistant preview [file]` - Preview outputs
- `editorial-assistant note <text>` - Add session note
- `editorial-assistant undo` - Undo last action
- `editorial-assistant help` - Show all commands

### Utility Commands

- `editorial-assistant list` - List all projects
- `editorial-assistant archive <project>` - Archive completed project
- `editorial-assistant export` - Export to clipboard/CMS format
- `editorial-assistant validate` - Run format validation checks

## Next Steps

1. ✅ Complete basic CLI shell with state management
2. ⏳ Integrate with video-metadata-seo-editor agent
3. ⏳ Implement all phase workflows
4. ⏳ Add validation system
5. ⏳ Create all remaining templates
6. ⏳ Build preview and undo functionality
7. ⏳ Add export/clipboard features
8. ⏳ Comprehensive testing with real transcripts
9. ⏳ Write user documentation
10. ⏳ Create installation script

## Questions to Resolve

1. Should we use Claude Code CLI, direct API, or both?
2. How should we handle API keys / authentication?
3. Should the CLI work offline (cached responses)?
4. Do we need a config file for user preferences?
5. Should we integrate with PBS CMS directly or just export?

---

This architecture balances:
- **User Experience**: ADHD-friendly, guided, forgiving
- **Format Consistency**: Template-based with validation
- **Editorial Quality**: Powered by specialized agent
- **Flexibility**: Works with staged inputs, supports iteration
- **Maintainability**: Clear separation of concerns
