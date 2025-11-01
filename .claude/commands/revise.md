---
description: Regenerate copy revision with project picker (Phase 2)
---

You are executing Phase 2 of the PBS Wisconsin video editorial workflow.

## Task Overview

Help the user choose a project from the 15 most recent Media IDs in `output/`, collect the latest draft artifact, then generate an updated copy revision document.

## Steps

1. **List recent projects**
   - Scan `output/` (exclude `archive/`) sorted by last-modified time.
   - Present the 15 most recent Media IDs with their phase statuses from `workflow.json` (if present).
   - Offer `more` to show additional batches of 15 when the user asks.

2. **Resolve the target Media ID**
   - Accept a numeric choice from the list, a typed Media ID, or a direct path supplied by the user.
   - Confirm the resolved Media ID before continuing.

3. **Collect inputs**
   - Transcript: `transcripts/<MEDIA_ID>*_ForClaude.txt` (fall back to `transcripts/archive/` if necessary).
   - Draft artifact: newest file inside `output/<MEDIA_ID>/drafts/` unless the user supplies a path or pastes text.
   - If no draft exists, ask the user to provide one (image or text) and save it into the project folder before proceeding.

4. **Apply program knowledge**
   - Consult `knowledge/Media ID Prefixes.md` for program-specific rules.
   - Use `system_prompts/phase2_editing.md` to guide the revision.

5. **Generate the output**
   - Produce `output/<MEDIA_ID>/02_copy_revision.md` (overwrite if it exists).
   - Capture side-by-side comparisons, reasoning for each change, AP Style checks, and keyword adjustments.

6. **Report back**
   - Confirm the processed Media ID and summarize the top recommendations (2–3 bullets).
   - Provide the output path for reference.
   - Offer to run Phase 3 (`/research-keywords`) if a SEMRush artifact is available.

## Quality Checks

Before finishing, verify that:
- ✅ Draft content is accurately extracted from the provided file or user input
- ✅ Character counts are listed for original and revised metadata
- ✅ Program-specific rules are explicitly acknowledged
- ✅ Output file path matches `output/<MEDIA_ID>/02_copy_revision.md`
- ✅ Workflow log (`workflow.json`) is updated when automation is involved
