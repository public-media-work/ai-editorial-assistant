# Agent Roster

## Purpose
Keep the editorial assistant aligned on who does what, which tools they own, and where to look for shared context.
We now operate with four lightweight roles that cover orchestration, implementation, review, and comms.

## Core Agents
- **Editor (Claude Code)** – Runs `/start`, launches the watcher, keeps the user oriented in the workflow, and surfaces the right artifacts or commands at each phase. Primary references: `agents/editor.md`, `.claude/commands/start.md`.
- **Implementer (Claude Code)** – Designs automation flows, prompt structures, and report templates. Owns `automation/`, `system_prompts/`, and any sandbox projects used for testing. See `agents/implementer.md`.
- **Project Coordinator (Codex)** – Tracks decisions, run history, and outstanding tasks. Maintains the shared notes in each project folder and routes follow-ups to the correct teammate. See `agents/project_coordinator.md`.
- **Code Reviewer (Codex)** – Performs independent reviews before handoff or commit. Checks for regressions, missed requirements, and testing gaps. Guidance lives in `agents/code_reviewer.md`.

## Collaboration Flow
1. Project Coordinator confirms current state (transcript, outputs, drafts) and tags the next action.
2. Editor runs the interactive session with the user and requests work from the Implementer when automation or prompt changes are needed.
3. Implementer builds or updates the automation pieces, then signals back to the Coordinator and Editor.
4. Code Reviewer audits the changes using the checklist in `knowledge/code_review_notes.md`, reports findings, and the Implementer addresses them.

## Code Review Notes
- Working notes and open follow-up items sit in `knowledge/code_review_notes.md`. Implementers should read and clear this log before merging their own changes.
- Each project folder stores execution history in `workflow.json` and any Coordinator notes in `production_notes.md`. The Editor references both when guiding a session.
- Legacy role briefs (SEO analyst, production assistant, caption expert) are kept for historical reference but are no longer part of the default workflow.
