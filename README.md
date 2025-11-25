# PBS Wisconsin Video Editorial Assistant

An AI-powered system prompt for transforming video transcripts into SEO-optimized metadata for streaming platforms.

## What This Is

This is a **prompt engineering project**, not a software application. The core artifact is a carefully crafted system prompt that instructs AI assistants (like Claude) on how to:

- Analyze video transcripts
- Generate SEO-optimized titles, descriptions, and keywords
- Edit draft copy to match AP Style and PBS Wisconsin standards
- Create formatted transcripts and timestamp chapters
- Follow program-specific editorial guidelines

## How to Use

### Quick Start (2 minutes)

1. Open [Claude.ai](https://claude.ai) in your browser
2. Start a new chat
3. Upload the system prompt: `Haiku 4.5 version.md`
4. Upload reference materials from `knowledge/` folder (optional but recommended)
5. Paste your video transcript
6. Ask Claude to process it: "Please analyze this transcript and create brainstorming options"

### What You Get

**Phase 1 - Brainstorming**: Multiple title/description options with SEO keywords
**Phase 2 - Editing**: Refinement of your draft copy with side-by-side comparison
**Phase 3 - Analysis**: Keyword research and competitive analysis (when needed)
**Phase 4 - Finalization**: Formatted transcripts and timestamp chapters (on request)

## Repository Structure

```
editorial-assistant/
├── Haiku 4.5 version.md          # System prompt (upload this to Claude)
├── knowledge/                     # Reference materials (upload to Claude)
│   ├── ap_styleguide.pdf         # AP Style Guide
│   ├── Transcript Style Guide.pdf
│   ├── WPM Generative AI Guidelines.pdf
│   └── Media ID Prefixes.md
├── transcripts/                   # Your video transcripts
│   ├── *.txt                      # Active transcripts
│   └── archive/                   # Completed transcripts
└── Possible improvements.md       # Feature requests and ideas
```

## Key Features

### Content Type Detection
Automatically identifies standard videos vs. shortform content and adjusts recommendations accordingly.

### Program-Specific Rules
Built-in knowledge of PBS Wisconsin programs:
- **Here and Now**: Interview format with strict political coverage rules
- **University Place**: Academic lecture series guidelines
- **The Look Back**: Historical narrative requirements
- **Wisconsin Life**: Documentary storytelling standards

### AP Style Compliance
- Down style for headlines (only proper nouns capitalized)
- No dashes/colons in titles
- Character limits enforced (title: 80, short: 100, long: 350)
- Prohibited language detection (viewer directives, promotional language)

### Ethical AI Practices
Every deliverable includes a reminder that AI-generated content requires human review and revision before publication.

## Workflow Example

```
You: [paste transcript]
Claude: [generates brainstorming document with 3-4 title options, descriptions, keywords]

You: "I like option 2 for the title. Here's my draft description: [paste]"
Claude: [creates revision document with original vs. proposed copy, explains changes]

You: "Great, make that change. Also create a formatted transcript."
Claude: [delivers final AP Style transcript with proper speaker identification]
```

## Tips for Best Results

1. **Attach knowledge base files** at the start of your chat for better accuracy
2. **Specify the program** if it has special rules (Here and Now, University Place, etc.)
3. **Provide SEMRush data** if you want keyword research (Phase 3)
4. **Request timestamps only for videos 15+ minutes** (both Media Manager and YouTube formats)
5. **Iterate on copy** - the editing phase is conversational, not one-shot

## Customization

The system prompt is written in plain language Markdown. To modify:

1. Open `Haiku 4.5 version.md` in any text editor
2. Edit the instructions
3. Save and upload the modified version to Claude
4. Test with a sample transcript from `transcripts/archive/`

Common customizations:
- Add new program-specific rules
- Adjust character limits
- Modify prohibited language list
- Update keyword extraction methods

## File Naming Convention

Transcripts use PBS Wisconsin Media ID system:

```
[PREFIX][NUMBER][FORMAT]_[REVISION]_ForClaude.txt
```

Examples:
- `2WLI1203HD_ForClaude.txt` - Wisconsin Life episode 1203
- `9UNP1972HD_REV20250804_ForClaude.txt` - University Place (revised)
- `6HNS_ForClaude.txt` - Here and Now Digital Short

See `knowledge/Media ID Prefixes.md` for program prefix list.

## Why This Approach Works

**Simplicity**: No installation, no dependencies, no automation to maintain
**Flexibility**: Works with any AI chat interface that supports Claude
**Portability**: System prompt can be used anywhere (Claude.ai, Claude Code, API)
**Maintainability**: Changes to style rules are just text edits
**Transparency**: You see exactly what instructions the AI is following

## Version History

Current version optimized for Claude 3.5 Haiku (fast, cost-effective for this task).

Previous iterations stored in `old versions/` (not included in this reset branch).

## Questions?

This system was designed through iterative refinement with PBS Wisconsin's SEO team. The system prompt contains detailed rules and examples built from real-world usage.

For feature requests or improvements, see `Possible improvements.md`.

---

**Remember**: This tool generates starting points and suggestions. All AI-generated content must be reviewed and edited by humans before publication.

## Co-Authors

This repository is developed collaboratively with AI assistance. Contributors are tracked via git commits:

| Agent | Role | Recent Commits |
|-------|------|----------------|
| **Main Assistant** | Primary development, bug fixes, documentation | `git log --grep="Agent: Main Assistant"` |

To see agent-specific contributions:
```bash
# View all commits by agent
git log --grep="Agent: Main Assistant"

# View agent distribution
git log --oneline | grep -o '\[Agent: [^]]*\]' | sort | uniq -c
```

See [workspace conventions](../workspace_ops/conventions/COMMIT_CONVENTIONS.md) for details.
