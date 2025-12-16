# Agent Feedback Log

This document captures feedback from AI agents working on this project. Agents should log issues, observations, and improvement suggestions here for consideration in future versions.

---

## 2024-12-12 - Claude Code (Opus 4.5) - Transcript Processing Session

### Context
Manual processing of 9UNP2008HD transcript after discovering queue was stuck. User requested fast turnaround using CLI-based processing.

### Issue 1: MCP CLI-Agent Delegation Timeout/Hang

**What happened:**
Attempted to use `mcp__cli-agent__delegate_task` to process a ~6,800 line transcript (60K+ characters). The task appeared to hang indefinitely with no response.

**Root cause analysis:**
- The CLI agent MCP tool doesn't have clear timeout feedback
- Large context (full transcript + formatting instructions) may exceed practical limits for delegation
- No progress indicators or streaming - just silence until completion or failure

**Recommendations for v3.0:**
1. **Chunk large transcripts** before sending to external agents
2. **Add timeout parameters** to agent delegation with clear feedback
3. **Progress streaming** for long-running tasks
4. **Size estimation** - warn before attempting tasks that exceed practical limits

---

### Issue 2: SRT Format Parsing Complexity

**What happened:**
The raw SRT transcript had inconsistent speaker markers:
- Full names used once: `- Norman Gilliland:`, `- Howard Schweber:`
- Abbreviated names used thereafter: `- Norman:`, `- Howard:`
- Some dialogue had NO speaker markers (continued speech shown with just `- `)

**Root cause analysis:**
This is an upstream transcript generation issue, but the formatter must handle it gracefully. A simple regex split on speaker names results in:
- Misattributed dialogue
- Multiple speakers' words merged into single paragraphs
- Lost speaker transitions

**Recommendations for v3.0:**
1. **Pre-processing normalization** - standardize speaker markers before formatting
2. **Speaker detection heuristics** - detect unmarked speaker changes via:
   - Question/answer patterns
   - Interjections (`Yes.`, `Right.`, `Mm-hmm.`)
   - Contextual clues (e.g., questions typically alternate speakers)
3. **Human review flag** - mark transcripts with ambiguous speaker attribution for manual review
4. **Transcript quality scoring** - rate incoming transcripts and adjust processing strategy

---

### Issue 3: Queue Processor Lacks Stale Job Recovery

**What happened:**
7 jobs were stuck in "processing" status for 6+ days. The queue processor marks jobs as "processing" before starting LLM calls, but if the script crashes mid-call (timeout, network error, killed by OS), the status is never updated.

**Root cause analysis:**
- No heartbeat/watchdog mechanism
- No automatic recovery for stale jobs
- No maximum processing time enforcement

**Recommendations for v3.0:**
1. **Heartbeat mechanism** - jobs should update a `last_heartbeat` timestamp during processing
2. **Stale job detection** - automatically reset jobs stuck in "processing" for >N minutes
3. **Graceful timeout handling** - wrap LLM calls with proper timeout and cleanup
4. **Database-backed queue** - use proper job queue semantics (claimed_at, expires_at, retries)
5. **Dead letter queue** - move repeatedly failed jobs to a separate queue for manual review

---

### Issue 4: No Partial Progress Persistence

**What happened:**
The 9UNP2008HD project had completed brainstorming (analyst step) but failed on formatting. When reprocessing, there was no way to skip the completed step - the system treats it as all-or-nothing.

**Root cause analysis:**
- `needs_brainstorming` and `needs_formatting` flags exist but aren't updated mid-process
- No checkpoint system for multi-step workflows
- Manifest status is either "processing" or "complete" - no partial states

**Recommendations for v3.0:**
1. **Step-level status tracking** - track completion of each agent step independently
2. **Resumable workflows** - allow restarting from last successful step
3. **Deliverable detection** - check if output files exist before re-running steps
4. **Idempotent operations** - steps should be safely re-runnable

---

### General Observations

**What works well:**
- The agent prompt system (`.claude/agents/*.md`) is well-organized
- LLM backend fallback logic is sound
- Cost tracking and model selection is sophisticated

**What needs improvement:**
- Error handling assumes synchronous, reliable execution
- No observability into long-running processes
- Manual intervention required for recovery
- Large transcripts need special handling (chunking, streaming, or model selection)

---

*To add feedback: Append a new dated section following the format above.*
