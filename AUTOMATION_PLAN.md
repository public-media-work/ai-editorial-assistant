# Claude Code Automation Plan

## Overview

The automation stack now couples a filesystem watcher with phase-specific Claude agents so that common deliverables are created the moment source files arrive. The watcher runs locally (via `python3 automation/watcher.py`) and relies on the `automation/config.yaml` file for paths, model settings, and retry parameters. Every project is organized inside `output/<MEDIA_ID>/`, which doubles as the drop-zone for draft screenshots and SEMRush captures.

## Event Triggers

1. **Transcript dropped in `transcripts/`**
   - Creates/updates `output/<MEDIA_ID>/`
   - Generates `01_brainstorming.md`, `05_formatted_transcript.md`, and `06_timestamp_report.md`
   - Seeds `workflow.json` with metadata and status
2. **Draft artifact added to `output/<MEDIA_ID>/drafts/`**
   - Runs the revision agent using `system_prompts/phase2_editing.md`
   - Writes `02_copy_revision.md`
3. **SEMRush screenshot added to `output/<MEDIA_ID>/semrush/`**
   - Runs the keyword agent using `system_prompts/phase3_analysis.md`
   - Writes `03_keyword_report.md` + `04_implementation.md`
4. **Optional reruns**
   - `/revise` lists the 15 most recent projects from `output/` before invoking Phase 2
   - `/brainstorm`, `/format-transcript`, `/create-timestamps`, and `/research-keywords` remain available for manual reruns

Each automation step records its completion (or failure) in `workflow.json`, supplying timestamps and output paths for auditing.

## Key Components

- `automation/config.yaml` – Central configuration for model selection, retry strategy, and folder locations
- `automation/watcher.py` – Watchdog-powered observer that reacts to file events and delegates to the coordinator
- `automation/processors.py` – Contains `AutomationCoordinator`, Claude API helpers, and run-log utilities
- `automation/archive.py` – Cron-friendly cleanup script that moves projects/transcripts older than 90 days into archive folders
- `output/<MEDIA_ID>/workflow.json` – Run log read by both automation and `/revise`

## Output Structure

```
output/
├── archive/
└── <MEDIA_ID>/
    ├── 01_brainstorming.md
    ├── 02_copy_revision.md
    ├── 03_keyword_report.md
    ├── 04_implementation.md
    ├── 05_formatted_transcript.md
    ├── 06_timestamp_report.md
    ├── drafts/
    │   └── <MEDIA_ID>_*.png or .md
    ├── semrush/
    │   └── <MEDIA_ID>_*.png
    └── workflow.json
```

## Archival Procedure

Schedule `python3 automation/archive.py --config automation/config.yaml` to run daily. Any project with no updates for 90 days (configurable) is moved to `output/archive/`, and matching transcripts are moved to `transcripts/archive/`. Use `--dry-run` to preview actions.

## Future Enhancements

- Add Slack/email notifications when phases complete or fail
- Persist Claude responses as JSON alongside Markdown for downstream analytics
- Capture additional metadata (duration, status) in `workflow.json` to support dashboarding
- Package the watcher as a background service (launchd/systemd) for easier startup
