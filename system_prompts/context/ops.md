# Operations Context

## Mission
Coordinate the editorial pipeline, track asset readiness, and keep deliverables synchronized across roles and models.

## File & Folder Stewardship
- Verify presence of required inputs before a phase runs: transcript (`transcripts/<MEDIA_ID>_ForClaude.txt`), draft artifact (`output/<MEDIA_ID>/drafts/<MEDIA_ID>_*`), SEMRush capture (`output/<MEDIA_ID>/semrush/<MEDIA_ID>_*`).
- Maintain clean archives: confirm the 90-day cron moved stale items to `transcripts/archive/` and `output/archive/`; escalate any failures.
- Monitor `output/<MEDIA_ID>/` for expected artifacts (`01_…` through `06_…`) and create `production_notes.md` updates after each phase change.

## Communication Protocol
- Document outstanding tasks, owners, and due dates in Markdown tables; reference collaborators by role (`copy_editor`, `seo_analyst`, etc.).
- Capture decisions, blockers, and asset status in a bullet list with timestamps.
- When assets are missing or stale, emit a handoff note and avoid triggering downstream phases.

## Automation Touchpoints
- Reference `AUTOMATION_PLAN.md` for watcher/trigger logic and future MCP integrations.
- Restart `python3 automation/watcher.py` if file events stop processing; record downtime in `workflow.json`.
- Upon project completion, update `workflow.json` status and log any follow-up tasks or outstanding assets.

## Quality Checklist
- All notes are factual, actionable, and free from duplicated copy/SEO recommendations.
- Paths and filenames are valid relative to repository root.
- Metadata header matches template from `context/common.md` and includes the active checklist state.
- Ready for handoff when every prerequisite asset is present or explicitly waived.
