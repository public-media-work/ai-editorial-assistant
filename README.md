# PBS Wisconsin Video Editorial Assistant

An AI-powered workflow for transforming video transcripts into optimized metadata (titles, descriptions, keywords, timestamps) following AP Style Guidelines and SEO best practices.

## Quick Start

> Prerequisite: start the watcher in a terminal (`python3 -m automation.watcher --config automation/config.yaml`) so file drops trigger the agents below.

### 1. Drop a Transcript

```bash
cp ~/path/to/your/transcript.txt transcripts/2WLI1203HD_ForClaude.txt
```

As soon as the file lands in `transcripts/`, the watcher spins up Brainstorming, Formatted Transcript, and Timestamp agents for that Media ID.

### 2. Review Auto-Generated Outputs

Open `output/2WLI1203HD/01_brainstorming.md`, `05_formatted_transcript.md`, and `06_timestamp_report.md` to plan your copy and chapter markers.

### 3. Trigger Copy Revision

Save your draft metadata (screenshot or text) into the project’s drafts folder:
```bash
cp ~/Screenshots/draft.png output/2WLI1203HD/drafts/20240212_draft.png
```
Dropping a file here fires the revision agent and refreshes `02_copy_revision.md`.

### 4. Trigger Keyword Research (Optional)

Place the SEMRush capture in the project’s semrush folder:
```bash
cp ~/Screenshots/semrush.png output/2WLI1203HD/semrush/20240212_semrush.png
```
The keyword agent generates `03_keyword_report.md` and `04_implementation.md` automatically.

### 5. Iterate with `/revise`

Use `/revise` in Claude Code to pick from the 15 most recent projects in `output/`, review the latest draft, and continue the interactive workflow.

---

## Available Commands

| Command | Description | Phase |
|---------|-------------|-------|
| `/revise` | Lists the 15 most recent projects, then regenerates Phase 2 with the selected draft | Phase 2 |
| `/research-keywords` | Manually reruns the keyword agent for the selected project | Phase 3 |
| `/brainstorm` | Optional manual rerun of Phase 1 if you tweak the transcript | Phase 1 |
| `/format-transcript` | Optional manual rerun of formatted transcript generation | Phase 4 |
| `/create-timestamps` | Optional manual rerun of timestamp generation | Phase 4 |

---

## Folder Structure

```
editorial-assistant/
├── transcripts/                  # Drop raw transcripts here
│   ├── 2WLI1203HD_ForClaude.txt
│   └── archive/                  # Auto-archived after 90 days
│
├── output/
│   ├── archive/                  # Archived projects live here
│   └── 2WLI1203HD/
│       ├── 01_brainstorming.md
│       ├── 02_copy_revision.md
│       ├── 03_keyword_report.md
│       ├── 04_implementation.md
│       ├── 05_formatted_transcript.md
│       ├── 06_timestamp_report.md
│       ├── drafts/               # Drop draft screenshots/text to trigger Phase 2
│       ├── semrush/              # Drop SEMRush screenshots to trigger Phase 3
│       └── workflow.json         # Run log used by automation + /revise picker
│
├── automation/                   # Watcher + archival scripts
│   ├── config.yaml
│   ├── watcher.py
│   └── archive.py
│
├── knowledge/                    # Reference materials
│   ├── ap_styleguide.pdf
│   ├── Transcript Style Guide.pdf
│   ├── WPM Generative AI Guidelines.pdf
│   └── Media ID Prefixes.md
│
├── system_prompts/
│   ├── phase1_brainstorming.md
│   ├── phase2_editing.md
│   ├── phase3_analysis.md
│   ├── phase4_transcript.md
│   ├── phase4_timestamps.md
│   └── archive/
│
└── .claude/commands/
    ├── revise.md
    ├── research-keywords.md
    ├── format-transcript.md
    └── create-timestamps.md
```

---

## Workflow Phases

### Phase 1: Research & Brainstorming

**Trigger**: Transcript copied to `transcripts/`  
**Output**: `01_brainstorming.md`

The watcher automatically analyzes the transcript and produces:
- 3 title options (80 char max)
- 2 short description options (100 char max)
- 2 long description options (350 char max)
- 20 SEO keywords (direct + logical/implied)
- Notable quotes and key information

**Manual Rerun (optional)**: `/brainstorm [transcript_path]`

---

### Phase 2: Copy Revision

**Trigger**: Draft file added to `output/<MEDIA_ID>/drafts/`  
**Output**: `02_copy_revision.md`

The revision agent:
- Extracts draft metadata from the screenshot or text
- Provides side-by-side original vs. revised copy
- Explains each change with AP Style/program notes
- Updates keyword recommendations when appropriate

**Manual Flow**: `/revise` → pick a project → supply additional draft if needed

---

### Phase 3: SEO Analysis (Optional)

**Trigger**: SEMRush screenshot added to `output/<MEDIA_ID>/semrush/`  
**Output**: `03_keyword_report.md` + `04_implementation.md`

Delivers:
- Platform-ready keyword list (ranked by search volume)
- Trending keywords and competitive gaps
- Platform-specific recommendations (YouTube, website, social)
- Prioritized action items with timeline
- Success metrics to track

**Manual Rerun**: `/research-keywords [media_id or screenshot_path]`

---

### Phase 4: Optional Outputs

Both artifacts are created automatically alongside Phase 1 whenever a new transcript arrives.

#### Formatted Transcript
- **Output**: `05_formatted_transcript.md`
- Includes full speaker names, paragraphing, and non-verbal cues per AP Style.
- **Manual rerun**: `/format-transcript [media_id]`

#### Timestamp Report
- **Output**: `06_timestamp_report.md`
- Provides Media Manager and YouTube chapter lists with descriptive labels.
- **Manual rerun**: `/create-timestamps [media_id]`

---

## File Naming Convention

Transcripts follow PBS Wisconsin's Media ID system:

**Format**: `[PREFIX][NUMBER][FORMAT]_[REVISION]_ForClaude.txt`

- **PREFIX**: Program identifier (see `knowledge/Media ID Prefixes.md`)
- **NUMBER**: Episode/segment number
- **FORMAT**: HD, HDWEB, SM (shortform/social media)
- **REVISION**: REV + date (YYYYMMDD) if applicable

**Examples**:
- `2WLI1203HD_ForClaude.txt` - Wisconsin Life episode 1203, HD
- `9UNP1972HD_REV20250804_ForClaude.txt` - University Place episode 1972, revised 2025-08-04
- `6HNS_ForClaude.txt` - Here and Now Digital Short

### Draft & Research Artifacts
- Place draft screenshots or markdown in `output/<MEDIA_ID>/drafts/` using a timestamped suffix (e.g., `output/2WLI1203HD/drafts/2WLI1203HD_20240212_draft.png`).
- Place SEMRush screenshots in `output/<MEDIA_ID>/semrush/` (e.g., `output/2WLI1203HD/semrush/2WLI1203HD_20240212_semrush.png`).
- Automation keys off the Media ID prefix, so keep it at the start of every filename.

---

## Editorial Standards

### AP Style & House Style
- **Down style for headlines**: Only first word and proper nouns capitalized
- **No dashes/colons in titles**; preserve necessary apostrophes and quotations
- **Character limits**: Title (80), Short Description (100), Long Description (350)
- **Title + Short Description pairing**: Must work cohesively (appear together in search results)

### Prohibited Language
❌ Never use:
- Viewer directives: "watch as", "see how", "discover", "learn"
- Promises: "will show", "will teach", "will reveal"
- Sales language: "free", monetary value framing
- Superlatives without evidence: "amazing", "incredible"
- Calls to action: "join us", "don't miss"

✅ Instead:
- State what the content IS
- Describe what happens (facts only)
- Use specific details over promotional adjectives

### Program-Specific Rules

#### University Place
- Include series name as keyword (if part of series)
- Don't use honorific titles ("Dr.", "Professor")
- Avoid inflammatory/bombastic language

#### Here and Now
- **Title**: [SUBJECT] on [topic]
- **Long**: [Org] [title] [name] [verb] [subject]
  - "discuss" for elected officials
  - "explain"/"describe" for others
  - Include party/location for elected (R-Rochester)
- **Short**: [name] on [subject] (simplified from long)

#### The Look Back
- MUST include: Hosts (Nick and Taylor), locations, expert historians
- Focus on WHY it matters > WHAT happened
- Use precise language showing deliberate decisions

---

## Typical Workflow Example

### Standard Video (e.g., Wisconsin Life Episode)

1. **Drop transcript** in `transcripts/` → watcher builds brainstorming, formatted transcript, and timestamps.
2. **Draft in CMS** using `01_brainstorming.md` → save screenshot to `output/<MEDIA_ID>/drafts/` → automation refreshes `02_copy_revision.md` → implement edits.
3. **(Optional)** capture SEMRush → save to `output/<MEDIA_ID>/semrush/` → automation writes keyword and implementation reports.
4. **Run `/revise`** if you want an interactive review or to re-run Phase 2 manually.
5. **Archival cron** retires the project automatically after 90 days.

**Time**: ~10-15 minutes (vs. 30-45 minutes manual)

### Shortform Content (e.g., Digital Short)

1. **Drop transcript(s)** → watcher generates brainstorming + formatted transcript immediately.
2. **Draft & screenshot** → store in `output/<MEDIA_ID>/drafts/` → automation crafts quick revisions.
3. **Optional**: `/revise` for ad-hoc edits or `/brainstorm` to fine-tune after manual tweaks.
4. **Archival cron** cleans up in the background.

**Time**: ~5-10 minutes per short

### Long-Form Educational (e.g., University Place Lecture)

1. **Drop transcript** → auto outputs deliver brainstorming, formatted transcript, and timestamps.
2. **Draft in CMS** → place screenshot in `drafts/` → automation issues revision guidance.
3. **SEMRush research** → store capture in `semrush/` → automation publishes keyword + implementation reports.
4. **Use `/revise`** for any interactive follow-up or manual re-runs.
5. **Archival cron** files everything away after 90 days of inactivity.

**Time**: ~15-20 minutes

---

## Archiving Workflow

Automation handles cleanup for you. Add a cron/launchd job that runs:

```bash
python3 automation/archive.py --config automation/config.yaml
```

Projects (and their transcripts) older than 90 days are moved into `output/archive/` and `transcripts/archive/`. Use `--dry-run` to preview upcoming moves. The `workflow.json` log travels with the project so you can resurrect it later if needed.

---

## Ethical AI Guidelines

All outputs include a note about ethical AI collaboration:

> This is AI-generated brainstorming content. Ethical use of generative AI involves collaboration and coaching between the AI and human user. Use this content to advise your own writing and editing, not to publish AI-generated content without review and revision.

**Key Principles**:
- AI provides recommendations based on best practices
- Human editor makes final decisions
- Always review and revise before publishing
- Maintain editorial integrity and factual accuracy

---

## Troubleshooting

### Command not found
- Make sure you're in the repository directory
- Check that `.claude/commands/` folder exists
- Try `/help` to see available commands

### Screenshot not reading correctly
- Ensure screenshot shows all metadata fields clearly
- Try providing text manually instead
- Check that filename follows convention: `[MEDIA_ID]_draft.png`

### Character counts seem off
- All counts include spaces
- Use exact character count from output files
- CMS may count differently—trust the AI counts

### Program-specific rules not applied
- Check that Media ID matches a program in `knowledge/Media ID Prefixes.md`
- Filename must start with correct prefix (e.g., `2WLI`, `9UNP`, `2HNW`)

---

## Advanced: Future Automation

See **[AUTOMATION_PLAN.md](AUTOMATION_PLAN.md)** for plans to automate this workflow with:
- File watching (auto-process when transcripts added)
- Python scripts + Claude API integration
- MCP server for Claude Code
- Batch processing capabilities

---

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Guidance for Claude Code when working in this repo
- **[AUTOMATION_PLAN.md](AUTOMATION_PLAN.md)** - Future automation roadmap
- **[Possible improvements.md](Possible%20improvements.md)** - Feature requests and enhancements
- **`output/EXAMPLE_2WLI1203HD/README.md`** - Example output structure

---

## Support

For issues or questions:
1. Check this README
2. Review the specific slash command file in `.claude/commands/`
3. Check system prompt in `system_prompts/`
4. Consult knowledge base in `knowledge/`

---

## Co-Authors

This project is developed collaboratively with AI assistance. Commit attribution follows the workspace conventions in `/Users/mriechers/Developer/workspace_ops/conventions/COMMIT_CONVENTIONS.md`.

| Agent | Role | Recent Commits |
|-------|------|----------------|
| Main Assistant | Prompt iteration and automation | `git log --grep="Agent: Main Assistant"` |
| code-reviewer | Code review and QA | `git log --grep="Agent: code-reviewer"` |

Run `git log --grep="Agent:" --oneline` to view the full agent history for this repository. See the workspace conventions document for more query examples.

---

**Version**: File-based workflow for Claude Code
**Last Updated**: 2025-10-22
