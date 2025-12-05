
# User Feedback Log

Status: `[ ]` new/untriaged, `[~]` in progress, `[x]` integrated into the roadmap (`feature_list.json`).

## Checklist
- [x] Brainstorming deliverables should stay human-readable Markdown without odd markup. (Tracked as F001)
- [x] Remove weird codeblock markup from formatted transcripts. (Tracked as F002)
- [x] Append deliverables with the raw transcript filename and ship a renamer script (e.g., `2BUC0000HDWEB02_formatted_transcript`). (Tracked as F003)
- [x] Archive raw transcripts after processing; archive output folders after 15 days; run archive check at watch-script startup. (Tracked as F004)
- [x] Chat agent must follow the revision loop: accept draft copy (including screenshots), suggest recent/matching transcripts, emit Markdown-only revision reports with reasoning, loop until approval, and trigger keyword/implementation reports when SEMRush data is provided. (Tracked as F005)
- [x] Visualizer buttons are non-functional; prioritize roadmap work from `FUTURE_ENHANCEMENTS_VISUAL_DASHBOARD.md` since current version is a proof of concept. (Tracked as F006)
- [x] Attribute outputs by model/agent and show per-model cost breakdowns in the visualizer. (Tracked as F007)

## How to add new feedback
- Append new items under this section with `[ ]` so they can be pulled into `feature_list.json` during the next planning pass.
- [x] uh-oh, we broke the visualizer when it comes to the names of programs, everything is coming up as "unknown program" now. (Tracked as F008)
