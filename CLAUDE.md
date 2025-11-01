# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a prompt engineering repository for an AI-powered **video editorial assistant** designed for PBS Wisconsin. The system transforms video transcripts into optimized metadata (titles, descriptions, keywords, timestamps) for video streaming platforms following Associated Press Style Guidelines and SEO best practices.

**Core workflow**: Video transcript → AI analysis → Brainstorming → Editing → SEO optimization → Final metadata + formatted transcript/timestamps

## Repository Structure

```
editorial-assistant/
├── Haiku 4.5 version.md          # Main system prompt (current version)
├── Possible improvements.md       # Feature requests and enhancement ideas
├── knowledge/                     # Reference materials for the AI assistant
│   ├── ap_styleguide.pdf         # AP Style Guide
│   ├── Transcript Style Guide.pdf # PBS Wisconsin transcript formatting rules
│   ├── WPM Generative AI Guidelines.pdf # Ethical AI use guidelines
│   ├── Media ID Prefixes.md      # PBS Wisconsin program identifiers
│   └── *.png                      # Timestamp formatting examples
├── transcripts/                   # Video transcripts to process
│   ├── *.txt                      # Active transcripts
│   └── archive/                   # Completed transcripts
└── old versions/                  # Previous system prompt iterations
```

## System Prompt Architecture

The main system prompt (`Haiku 4.5 version.md`) defines a **four-phase workflow**:

### Phase 1: Research & Brainstorming
- Analyze transcript(s) to determine content type (standard video vs. shortform content)
- Extract keywords using two methods:
  - **Direct keywords**: Terms explicitly mentioned in transcript
  - **Logical/implied keywords**: Conceptual themes and related topics discussed but not explicitly named
- Generate initial brainstorming document with title/description options

### Phase 2: Editing
- Refine user-provided draft descriptions against transcript content
- Create side-by-side original vs. revised comparison with reasoning
- Iterative feedback loop with user

### Phase 3: Analysis (On-Demand)
- Only triggered when user provides SEMRush data or explicitly requests keyword research
- Web search for trending keywords and competitive analysis
- Generate keyword report with search volume rankings
- Generate implementation report with prioritized action items

### Phase 4: Project Conclusion
- Consolidate final deliverables
- Optional: Generate formatted transcript (AP Style compliant)
- Optional: Generate timestamp report for videos 15+ minutes (both Media Manager and YouTube formats)

## Critical Style Rules

### AP Style & House Style
- **Down style for headlines**: Only first word and proper nouns capitalized
- **No dashes/colons in titles**; preserve necessary apostrophes and quotations
- **Abbreviations**: Use freely in titles/short descriptions; spell out on second reference in long descriptions
- **Character limits**: Title (80 chars), Short Description (100 chars), Long Description (350 chars)
- **Title + Short Description pairing**: Must work cohesively as they appear together in search results

### Prohibited Language (Never Use)
- Viewer directives: "watch as", "see how", "discover", "learn", "explore"
- Promises: "will show", "will teach", "will reveal"
- Sales language: "free", monetary value framing
- Emotional predictions: telling viewers how they will feel
- Superlatives without evidence: "amazing", "incredible", "extraordinary"
- Calls to action: "join us", "don't miss", "tune in"

**Instead**: State what the content IS, describe what happens (facts only), use specific details over promotional adjectives

### Program-Specific Rules

#### University Place
- Include series name as keyword if video is part of a lecture series
- Don't use honorific titles like "Dr." or "Professor"
- Avoid inflammatory/bombastic language

#### Here and Now
- **Title Format**: [INTERVIEW SUBJECT] on [brief neutral description of topic]
- **Long Description**: [Organization] [job title] [name] [verb] [subject matter]
  - Use "discuss" for ALL elected officials or candidates
  - Use "explain," "describe," or "consider" for non-elected subjects
  - Include party and location for elected officials (R-Rochester, D-Madison, etc.)
- **Short Description**: [name] on [subject matter] (simplified from long description)

#### The Look Back
- MUST include: Host names (Nick and Taylor), institutions/locations visited, expert historians consulted
- Focus on WHY it matters > WHAT happened
- Use precise historical language showing deliberate decisions, not accidents

## Key Deliverable Templates

All deliverables use **Markdown artifacts** with tables for structured presentation:

1. **Brainstorming Document**: Title options, short/long descriptions, SEO keywords, notable quotes
2. **Digital Shorts Brainstorming Report**: Optimized for social platforms with hashtags
3. **Copy Revision Document**: Side-by-side original vs. proposed revisions with reasoning
4. **Keyword Report**: Platform-ready keyword list ranked by search volume
5. **Implementation Report**: Prioritized action items with platform-specific recommendations
6. **Formatted Transcript**: AP Style compliant with full speaker names (only when explicitly requested)
7. **Timestamp Report**: Both Media Manager and YouTube formats (only for 15+ minute videos when requested)

## Ethical AI Collaboration

The system includes a mandatory disclaimer in all initial deliverables:

> "**Note**: This is AI-generated brainstorming content. Ethical use of generative AI involves collaboration and coaching between the AI and human user. My duty is to provide advice rooted in best practices and the content itself. Your duty is to use this content to advise your own writing and editing, not to publish AI-generated content without review and revision."

## Development Workflow

When modifying the system prompt:

1. **Test changes** by copying a transcript from `transcripts/` and running it through the modified prompt
2. **Compare outputs** with previous versions in `old versions/` to ensure improvements
3. **Save the previous version** to `old versions/` before making significant changes
4. **Update version identifier** in the filename if creating a new major revision
5. **Document changes** in `Possible improvements.md` if tracking feature requests

## Common Tasks

### Testing the System Prompt
```bash
# Copy a test transcript
cp transcripts/archive/[filename].txt test_transcript.txt

# Use Claude.ai or Claude API to process with current system prompt
# Compare output against expected deliverables
```

### Reviewing Knowledge Base
```bash
# Check reference materials
ls -lh knowledge/

# AP Style Guide: knowledge/ap_styleguide.pdf
# Transcript formatting: knowledge/Transcript Style Guide.pdf
# Program identifiers: knowledge/Media ID Prefixes.md
```

### Organizing Transcripts
```bash
# Move completed transcripts to archive
mv transcripts/[filename].txt transcripts/archive/

# Check active transcripts
ls -1 transcripts/*.txt
```

## Transcript File Naming Convention

Transcripts follow PBS Wisconsin's Media ID system: `[PREFIX][NUMBER][FORMAT]_[REVISION]_ForClaude.txt`

- **PREFIX**: Program identifier (see `knowledge/Media ID Prefixes.md`)
- **NUMBER**: Episode/segment number
- **FORMAT**: HD, HDWEB, SM (shortform/social media)
- **REVISION**: REV + date (YYYYMMDD) if applicable

Examples:
- `2WLI1203HD_ForClaude.txt` - Wisconsin Life episode 1203, HD format
- `9UNP1972HD_REV20250804_ForClaude.txt` - University Place episode 1972, revised 2025-08-04
- `6HNS_ForClaude.txt` - Here and Now Digital Short

## Quality Control

Before delivering any artifact, verify:
- ✅ Character counts are EXACT (including spaces)
- ✅ Program-specific rules applied (if applicable)
- ✅ No prohibited language used
- ✅ Proper Markdown formatting with tables
- ✅ AP Style guidelines followed
- ✅ Transcript artifact NOT generated unless explicitly requested
- ✅ Timestamps (if generated): both formats provided, logical chapter breaks

## Automation Workflow (Future Enhancement)

This repository is currently designed for chat-based interaction with Claude. For an automated file-watching workflow suitable for Claude Code, see **[AUTOMATION_PLAN.md](AUTOMATION_PLAN.md)** which details:

- Automated processing triggered by new files in watched folders
- Screenshot-based input for draft copy and SEMRush analysis
- Organized output structure with reports grouped by Media ID
- Migration path from chat-based to file-based workflow

## Important Notes

- This is a **prompt engineering repository**, not a codebase with executables
- The "code" here is natural language instruction for AI models
- Currently designed for chat-based interaction (Claude.ai desktop app)
- The primary artifact is the system prompt in Markdown format
- Knowledge base files (PDFs, PNGs) are reference materials only
