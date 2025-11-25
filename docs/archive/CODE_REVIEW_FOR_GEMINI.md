# Code Review Notes for Gemini Agent

## Objectives
- Minimize token usage when agents load project context.
- Keep queue state authoritative and visible to MCP.
- Allow MCP to trigger/observe backend processing.

## Key Changes Made
- **Queue processor (`scripts/process_queue_auto.py`):**
  - Writes status transitions to `.processing-requests.json`: `pending → processing → completed/failed`; keeps completed entries.
  - Records errors with timestamps; skips already completed on rerun.
  - Analyst + formatter now run concurrently.
  - Backend fallback per step (uses per-agent prefs or auto-select order; auto-upgrades on failure/unavailable).
  - Structured per-project log at `OUTPUT/<project>/processing.log.jsonl`.
- **MCP server (`mcp-server/src/index.ts`):**
  - `load_project_for_editing` returns manifest + file pointers, sizes, previews (head/tail), and file list—no full file bodies.
  - New tools:
    - `list_project_files` (names, sizes, mtimes).
    - `read_project_file(file_path, max_bytes?)` (whitelisted to `OUTPUT/` and `transcripts/`).
    - `get_queue_status` (reads `.processing-requests.json`).
    - `run_queue_processing` (runs the Python queue processor and returns recent stdout/stderr).

## Rationale (Token Hygiene & Control Plane)
- Default loads now avoid large transcripts/brainstorming/revisions; agents must explicitly fetch full text via `read_project_file`.
- Queue status is ground truth for MCP: agents can detect done/failed without polling the filesystem heuristically.
- MCP can trigger processing from chat (`run_queue_processing`) and inspect queue state/logs instead of guessing.

## Usage Notes
- To inspect queue: call `get_queue_status`.
- To process queue: call `run_queue_processing`; inspect returned output, then re-check queue.
- To work a project: call `load_project_for_editing` (lightweight), optionally `list_project_files`, then fetch full files via `read_project_file`.
- Logs: `OUTPUT/<project>/processing.log.jsonl` per project for step-level trace.

## Open Config Points
- Per-step backend preferences (formatter/analyst/timestamps) can be set in Python via `BACKEND_PREFERENCES` or `llm-config` auto-select order.
- Queue entries remain after completion for traceability; failures stay marked with `error`.
