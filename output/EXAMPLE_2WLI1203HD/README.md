# Example Output Structure

This folder demonstrates how each Media ID workspace is organized once the automation watcher runs.

## Core Deliverables

The watcher produces the following Markdown files automatically when a transcript is dropped into `transcripts/`:

- `01_brainstorming.md` – Phase 1 titles, descriptions, keyword seed list, notable quotes
- `05_formatted_transcript.md` – AP Style formatted transcript
- `06_timestamp_report.md` – Chapter markers for Media Manager and YouTube

Additional phases appear as you supply more assets:

- `02_copy_revision.md` – Created when a file is added to `drafts/`
- `03_keyword_report.md` + `04_implementation.md` – Created when a SEMRush screenshot appears in `semrush/`

## Triggering Phases

1. **Transcript**
   ```bash
   cp ~/Downloads/2WLI1203HD_ForClaude.txt transcripts/
   ```
   Automation creates `output/2WLI1203HD/` with the Phase 1 + Phase 4 files and initializes `workflow.json`.

2. **Draft Revision**
   ```bash
   cp ~/Screenshots/draft.png output/2WLI1203HD/drafts/20240212_draft.png
   ```
   The watcher refreshes `02_copy_revision.md` using the newest draft artifact. `/revise` can also be used to rerun this phase manually.

3. **Keyword Research (Optional)**
   ```bash
   cp ~/Screenshots/semrush.png output/2WLI1203HD/semrush/20240212_semrush.png
   ```
   Automation generates both keyword report files. `/research-keywords` is available for additional passes.

## Project Layout

```
output/
└── 2WLI1203HD/
    ├── 01_brainstorming.md
    ├── 02_copy_revision.md
    ├── 03_keyword_report.md
    ├── 04_implementation.md
    ├── 05_formatted_transcript.md
    ├── 06_timestamp_report.md
    ├── drafts/
    │   └── 2WLI1203HD_*.png or .md
    ├── semrush/
    │   └── 2WLI1203HD_*.png
    └── workflow.json
```

## Archiving

A cron job running `python3 automation/archive.py --config automation/config.yaml` moves projects and transcripts older than 90 days to the respective `archive/` folders. You can still run it manually with `--dry-run` to preview the actions.
