# DEV_LONG_RUNNING_AGENT_PLAN

Purpose: apply the two-agent harness pattern (Initializer + Coding Agent) from `knowledge/agents/long_running_agents_summary.md` to this repo so long-running work stays consistent across sessions.

## Roles
- **Initializer Agent**: run `./init.sh`, read `claude-progress.txt` and `feature_list.json`, refresh context from `CLAUDE.md`, queue any new feedback into the feature list, and set the next `in_progress` feature.
- **Coding Agent**: pick the single `in_progress` feature, execute it end-to-end (tests/verification included), update `feature_list.json`, append to `claude-progress.txt`, and leave the tree clean with a commit (with agent attribution) before exit.

## Required Artifacts
- `init.sh` — one-command bootstrap for Python + MCP server.
- `feature_list.json` — authoritative work queue with `pending | in_progress | completed` status and `passes` flags.
- `claude-progress.txt` — rolling session log with dates, work done, tests run, blockers, and handoff notes.
- `USER_FEEDBACK.md` — intake log; new items get translated into `feature_list.json` entries.

## Session Protocol
1) Run `./init.sh`.
2) Read `claude-progress.txt` and `feature_list.json`; do not start coding without an assigned `in_progress` feature.
3) Work **one feature at a time**; never flip `passes` to true without verification.
4) Update `feature_list.json` + `claude-progress.txt` before finishing; commit with `[Agent: <name>]`.

## Backlog Sources (mapped to feature IDs)
- F001: Brainstorming exports must stay human-readable Markdown (no odd markup).
- F002: Formatted transcript output has stray code fences; clean the template.
- F003: Deliverable filenames should append the raw transcript id; write a renamer script across projects.
- F004: Archive protocol enforcement — archive raw transcripts after processing; archive output folders after 15 days; add daily archive check when the watch script starts.
- F005: Chat agent workflow clarity — enforce the revision-loop behavior and SEMRush-triggered reports.
- F006: Visualizer buttons non-functional; align with `FUTURE_ENHANCEMENTS_VISUAL_DASHBOARD.md` and `DASHBOARD_OVERHAUL_ROADMAP.md` to prioritize fixes.
- F007: Attribute deliverables by model/agent and show per-model cost breakdowns in the visualizer.

## Guardrails (from best practices)
- Always start by reading progress + feature list; never remove features from the queue.
- Keep the working tree clean; no marking features as complete without tests/verification.
- Prefer plan-first execution with small steps; capture reasoning in progress log for handoffs.
- Use structured outputs and spend tracking to simplify auditing.

## Current Focus
- Initialize the harness artifacts (this file, `init.sh`, `feature_list.json`, `claude-progress.txt`).
- Next eligible feature to pick up: **F003 — Deliverable renamer + filename convention**, because it unblocks consistent artifact naming across projects.
