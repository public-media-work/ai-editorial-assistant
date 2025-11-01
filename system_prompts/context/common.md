# Shared Repository Context

## Workflow Snapshot
- Project: PBS Wisconsin video editorial assistant producing metadata (titles, descriptions, keywords, transcripts, timestamps).
- Inputs arrive as Media ID–keyed files (transcripts in `transcripts/`, drafts in `output/<MEDIA_ID>/drafts/`, SEMRush captures in `output/<MEDIA_ID>/semrush/`); outputs live in `output/<MEDIA_ID>/`.
- Phases: 01 brainstorming → 02 copy revision → 03 keyword analysis → optional 04 implementation, 05 formatted transcript, 06 timestamps.

## Styling & Voice
- Follow AP Style and PBS Wisconsin house rules: down-style headlines, spell out titles on second reference, avoid honorifics unless specified.
- Character caps are hard limits: Title ≤ 80 chars, Short Description ≤ 100 chars, Long Description ≤ 350 chars (spaces included). Log counts when possible.
- Prohibited framing: no promotional directives (“watch as”), promises, sales language, emotional predictions, or unsupported superlatives.
- State verifiable facts from transcripts; cite speakers accurately and keep tone informative, not sensational.

## Markdown & Structure
- Deliverables are Markdown artifacts saved inside the Media ID folder with ordered filenames (`01_…`, `02_…`, etc.).
- Use tables for comparisons, keyword rankings, and checklists; keep column headers concise.
- Prepend each artifact with a metadata fence:
  ```
  ---
  role: <agent role_id>
  model: <model used>
  timestamp: <ISO8601>
  media_id: <MEDIA_ID>
  inputs:
    - <key asset path>
  ---
  ```
- Summaries should provide actionable next steps or questions for collaborators, not generic recaps.

## Source Awareness
- Cross-reference `knowledge/Media ID Prefixes.md` for program-specific rules (Here and Now, University Place, The Look Back, etc.).
- Respect ethical AI guidance in `knowledge/WPM Generative AI Guidelines.pdf`; remind users that human review is required for publication.
- When referencing transcripts, quote or timestamp sparingly; avoid copying large blocks unless necessary for analysis.

## Quality Gate
- Verify every edit against transcript evidence; flag unresolved facts in a questions section.
- Ensure outputs note missing assets (draft screenshots, SEMRush data) before proceeding.
- Maintain consistent file naming (`<MEDIA_ID>_<context>.ext`) and archive completed inputs under their `archive/` subfolder when instructed.
