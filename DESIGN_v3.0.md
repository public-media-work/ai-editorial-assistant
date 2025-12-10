# Editorial Assistant v3.0 - Design & Vision Document

**Goal:** Transition from a sophisticated CLI tool (v2.0) to a robust, database-backed application (v3.0) that decouples processing logic from the user interface, enabling greater stability, scalability, and future web/mobile integrations.

**Last Updated:** December 2024

---

## Executive Summary

Editorial Assistant v3.0 represents an evolution from a working prototype to a production-ready system. The core value proposition remains unchanged: **transform video transcripts into SEO-optimized metadata with minimal human intervention and maximum cost efficiency**.

What changes is *how* we deliver that value:
- **Decoupled architecture** separates viewing from doing
- **Database-backed state** replaces brittle JSON files
- **API-first design** enables multiple interfaces (CLI, TUI, Web, Mobile)
- **Orchestrator/Agent model** enables parallel development and processing
- **Smart cost routing** leverages CLI agents and external services

---

## Part 1: Where We Are (v2.0 Assessment)

### Current Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           v2.0 SYSTEM OVERVIEW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐     ┌──────────────────────┐     ┌───────────────────┐   │
│  │   Claude    │────▶│   MCP Server (TS)    │────▶│  .processing-     │   │
│  │   Desktop   │     │   14 tools exposed   │     │  requests.json    │   │
│  └─────────────┘     └──────────────────────┘     └─────────┬─────────┘   │
│                                                              │             │
│  ┌─────────────┐     ┌──────────────────────┐               ▼             │
│  │  Terminal   │────▶│  process_queue_      │     ┌───────────────────┐   │
│  │    User     │     │  visual.py (TUI)     │────▶│  LLM Backend      │   │
│  └─────────────┘     └──────────────────────┘     │  Router           │   │
│                                                    │  ┌─────────────┐  │   │
│                      ┌──────────────────────┐     │  │ Gemini Flash│  │   │
│                      │  process_queue_      │     │  │ OpenAI Mini │  │   │
│                      │  auto.py (headless)  │────▶│  │ GPT-4o      │  │   │
│                      └──────────────────────┘     │  │ Claude 3.5  │  │   │
│                                                    │  └─────────────┘  │   │
│                                                    └─────────┬─────────┘   │
│                                                              │             │
│                                                              ▼             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         Agent System                                 │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │  │
│  │  │ transcript │  │  formatter │  │copy-editor │  │    seo-    │    │  │
│  │  │  analyst   │  │            │  │            │  │ researcher │    │  │
│  │  │  (Phase 1) │  │  (Phase 4) │  │ (Phase 2-3)│  │  (Phase 3) │    │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                              │             │
│                                                              ▼             │
│                      ┌──────────────────────────────────────────────────┐ │
│                      │  OUTPUT/{project}/                               │ │
│                      │  ├── manifest.json                               │ │
│                      │  ├── {project}_brainstorming.md                  │ │
│                      │  ├── {project}_formatted_transcript.md           │ │
│                      │  ├── {project}_copy_revision_v{N}.md             │ │
│                      │  └── processing.log.jsonl                        │ │
│                      └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### What's Working Well

| Strength | Implementation | Impact |
|----------|----------------|--------|
| **Cost Optimization** | Multi-backend routing with Gemini Flash preference | 70%+ cost reduction vs. GPT-4o only |
| **Robust Processing** | Atomic file ops, thread-safe locks, timeout protection | Zero data loss in production |
| **Agent Modularity** | 4 specialized agents with clear phase ownership | Easy to extend, test, and maintain |
| **Auditability** | Per-deliverable manifest tracking, JSONL logs | Full provenance for every output |
| **MCP Integration** | 14 tools for Claude Desktop | Seamless drag-and-drop workflow |
| **Visual Dashboard** | Rich TUI with sparkline charts | Real-time cost and progress visibility |

### Current Limitations

| Gap | Root Cause | v3.0 Solution |
|-----|------------|---------------|
| JSON queue is primary state | SQLite exists but not integrated | Full database migration |
| No external API | Processing tightly coupled to UI | FastAPI control plane |
| Copy-editor workflow incomplete | No automated revision loop | Chat agent integration |
| Single-threaded processing | Stability prioritized over speed | Parallel orchestrator |
| Terminal-only interface | No web layer | React dashboard |
| No remote monitoring | Requires local terminal access | WebSocket-based updates |

---

## Part 2: Architectural Shift

### Core Design Principles

1. **Separation of Concerns**: Processing logic knows nothing about UI
2. **Database as Truth**: All state lives in SQLite, not JSON files
3. **API-First**: Every action is an API call (even from TUI)
4. **Event-Driven**: State changes emit events for real-time updates
5. **Cost-Aware**: Every decision considers token/dollar tradeoffs
6. **Parallel by Default**: Work that can be parallelized, should be

### Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           v3.0 TARGET ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INTERFACE LAYER (Multiple Frontends)                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Claude  │  │   Web    │  │   TUI    │  │   CLI    │  │  Mobile  │     │
│  │ Desktop  │  │Dashboard │  │  (Rich)  │  │ Commands │  │  (Future)│     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │             │             │             │             │            │
│       └─────────────┴──────┬──────┴─────────────┴─────────────┘            │
│                            ▼                                                │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    API LAYER (FastAPI + WebSocket)                    │  │
│  │  POST /api/queue/add     GET /api/queue          WS /api/events      │  │
│  │  POST /api/jobs/{id}/... GET /api/jobs/{id}      GET /api/analytics  │  │
│  │  POST /api/control/...   GET /api/config         POST /api/config    │  │
│  └───────────────────────────────────┬──────────────────────────────────┘  │
│                                      │                                      │
│  ┌───────────────────────────────────┴──────────────────────────────────┐  │
│  │                    ORCHESTRATOR (Event-Driven Worker)                 │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │ Job Poller  │  │  Executor   │  │  Event Bus  │  │  Scheduler  │  │  │
│  │  │ (DB Watch)  │  │  (Parallel) │  │  (Pub/Sub)  │  │ (Priority)  │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └───────────────────────────────────┬──────────────────────────────────┘  │
│                                      │                                      │
│  ┌───────────────────────────────────┴──────────────────────────────────┐  │
│  │                    MODEL ROUTER (Cost-Optimized)                      │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │  │
│  │  │  CLI-Agent MCP   │  │   Direct APIs    │  │   Local Ollama   │   │  │
│  │  │  (Gemini/Claude  │  │   (OpenAI,       │  │   (Zero-cost,    │   │  │
│  │  │   CLI wrappers)  │  │    Anthropic)    │  │    fallback)     │   │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘   │  │
│  └───────────────────────────────────┬──────────────────────────────────┘  │
│                                      │                                      │
│  ┌───────────────────────────────────┴──────────────────────────────────┐  │
│  │                         AGENT LAYER                                   │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐        │  │
│  │  │ transcript │ │  formatter │ │copy-editor │ │    seo-    │        │  │
│  │  │  analyst   │ │            │ │ (chat mode)│ │ researcher │        │  │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘        │  │
│  └───────────────────────────────────┬──────────────────────────────────┘  │
│                                      │                                      │
│  ┌───────────────────────────────────┴──────────────────────────────────┐  │
│  │                    DATA LAYER (SQLite + Files)                        │  │
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────────┐ │  │
│  │  │  dashboard.db   │  │   OUTPUT/{proj}  │  │   transcripts/       │ │  │
│  │  │  - jobs         │  │   - manifest     │  │   - incoming         │ │  │
│  │  │  - session_stats│  │   - deliverables │  │   - archive          │ │  │
│  │  │  - config       │  │   - logs         │  │                      │ │  │
│  │  │  - analytics    │  │                  │  │                      │ │  │
│  │  └─────────────────┘  └──────────────────┘  └──────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Comparison

| Component | v2.0 (Current) | v3.0 (Target) | Migration Path |
|-----------|----------------|---------------|----------------|
| **State Management** | `.processing-requests.json` | SQLite `dashboard.db` | Migration script exists |
| **Processing Logic** | Monolithic `process_queue_visual.py` | Headless `orchestrator.py` | Refactor in progress |
| **Interface** | Terminal UI (Rich) | Hybrid (TUI + Web + CLI) | Additive, TUI remains |
| **Control Plane** | Direct script execution | FastAPI server | New component |
| **Configuration** | Raw JSON files | Pydantic models + DB | Validation layer |
| **Real-time Updates** | Polling + Rich.Live | WebSocket events | New component |
| **Cost Routing** | Hardcoded preferences | Dynamic router + CLI-Agent | Enhanced |

---

## Part 3: Database Schema (Expanded)

### Core Tables

```sql
-- Jobs: The heart of the processing queue
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path TEXT NOT NULL,
    transcript_file TEXT NOT NULL,
    project_name TEXT GENERATED ALWAYS AS (
        substr(project_path, instr(project_path, '/') + 1)
    ) STORED,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled', 'paused')),
    priority INTEGER NOT NULL DEFAULT 0,

    -- Timing
    queued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    completed_at DATETIME,

    -- Cost tracking
    estimated_cost REAL DEFAULT 0.0,
    actual_cost REAL DEFAULT 0.0,

    -- Processing metadata
    agent_phases TEXT DEFAULT '["analyst", "formatter"]',  -- JSON array of phases to run
    current_phase TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Error handling
    error_message TEXT,
    error_timestamp DATETIME,

    -- Links
    manifest_path TEXT,
    logs_path TEXT
);

-- Session events: Granular tracking for analytics and debugging
CREATE TABLE session_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER REFERENCES jobs(id),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'job_queued', 'job_started', 'job_completed', 'job_failed',
        'phase_started', 'phase_completed', 'phase_failed',
        'cost_update', 'model_selected', 'model_fallback',
        'system_pause', 'system_resume', 'system_error',
        'user_action', 'api_call'
    )),
    data TEXT  -- JSON: {cost, tokens, backend, model, error, duration_ms, ...}
);

-- Model performance: Track which models work best for which tasks
CREATE TABLE model_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    transcript_size_bucket TEXT CHECK (transcript_size_bucket IN ('small', 'medium', 'large', 'xlarge')),

    -- Performance metrics
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_duration_ms INTEGER,
    avg_cost REAL,
    avg_quality_score REAL,  -- Optional: user ratings

    -- Last updated
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(model_name, agent_type, transcript_size_bucket)
);

-- System configuration: Runtime settings in DB
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    value_type TEXT DEFAULT 'string' CHECK (value_type IN ('string', 'int', 'float', 'bool', 'json')),
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Daily aggregates: Pre-computed analytics
CREATE TABLE daily_analytics (
    date TEXT PRIMARY KEY,  -- YYYY-MM-DD
    jobs_completed INTEGER DEFAULT 0,
    jobs_failed INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0,
    avg_cost_per_job REAL,
    total_tokens INTEGER DEFAULT 0,
    most_used_model TEXT,
    avg_duration_ms INTEGER
);
```

### Indexes for Performance

```sql
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_priority ON jobs(priority DESC, id ASC);
CREATE INDEX idx_jobs_queued_at ON jobs(queued_at);
CREATE INDEX idx_session_stats_job ON session_stats(job_id);
CREATE INDEX idx_session_stats_timestamp ON session_stats(timestamp);
CREATE INDEX idx_session_stats_type ON session_stats(event_type);
CREATE INDEX idx_model_perf_agent ON model_performance(agent_type);
```

---

## Part 4: API Specification

### RESTful Endpoints

```yaml
# Queue Management
GET    /api/queue                    # List all jobs with status
POST   /api/queue                    # Add new job(s) to queue
DELETE /api/queue/{job_id}           # Cancel/remove job

# Job Control
GET    /api/jobs/{job_id}            # Get job details
PATCH  /api/jobs/{job_id}            # Update job (priority, status)
POST   /api/jobs/{job_id}/pause      # Pause processing
POST   /api/jobs/{job_id}/resume     # Resume processing
POST   /api/jobs/{job_id}/retry      # Retry failed job
POST   /api/jobs/{job_id}/eject      # Stop mid-stream, mark for manual

# Batch Operations
POST   /api/queue/reorder            # Bulk priority update
POST   /api/queue/pause-all          # Pause entire queue
POST   /api/queue/resume-all         # Resume queue processing

# System Control
GET    /api/system/status            # Orchestrator status
POST   /api/system/pause             # Pause orchestrator
POST   /api/system/resume            # Resume orchestrator
GET    /api/system/health            # Health check

# Configuration
GET    /api/config                   # Get all config
PATCH  /api/config                   # Update config values
GET    /api/config/backends          # List available backends
POST   /api/config/backends/test     # Test backend availability

# Analytics
GET    /api/analytics/summary        # 30/90 day overview
GET    /api/analytics/costs          # Cost breakdown by model/agent
GET    /api/analytics/performance    # Model performance comparison
GET    /api/analytics/timeline       # Hourly/daily cost timeline

# Files (read-only, for web dashboard)
GET    /api/projects                 # List completed projects
GET    /api/projects/{name}          # Project details + files
GET    /api/projects/{name}/files/{path}  # Read specific file
```

### WebSocket Events

```yaml
# Connection
WS /api/events

# Events emitted (server → client)
job:queued         {job_id, project_name, estimated_cost}
job:started        {job_id, phase, model}
job:progress       {job_id, phase, percent, tokens_used}
job:completed      {job_id, actual_cost, duration_ms}
job:failed         {job_id, error, retry_count}
system:paused      {reason}
system:resumed     {}
cost:update        {total_today, total_session}
model:selected     {job_id, model, reason}
model:fallback     {job_id, from_model, to_model, reason}
```

---

## Part 5: Web Dashboard Design

### Page Structure

```
/                      → Dashboard (queue overview + live status)
/queue                 → Queue Management (drag-drop reorder)
/jobs/{id}             → Job Detail (logs, phases, cost breakdown)
/projects              → Completed Projects (browse outputs)
/projects/{name}       → Project Viewer (files, revisions)
/analytics             → Analytics Dashboard (costs, performance)
/settings              → Configuration (backends, preferences)
```

### Dashboard Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PBS Wisconsin Editorial Assistant                    [Pause] [Settings] ⚙  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐  │
│  │   TODAY'S STATS             │  │   PROCESSING NOW                    │  │
│  │   ─────────────────────     │  │   ─────────────────────────────     │  │
│  │   Jobs Completed: 12        │  │   2WLI1206HD_REV20251103            │  │
│  │   Jobs Failed: 1            │  │   ████████████░░░░░░  65%           │  │
│  │   Total Cost: $0.42         │  │   Phase: formatter                  │  │
│  │   Avg Cost: $0.03/job       │  │   Model: gemini-flash               │  │
│  │                             │  │   Est. remaining: 2m 30s            │  │
│  └─────────────────────────────┘  └─────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │   QUEUE (4 pending)                                    [+ Add Jobs]  │  │
│  │   ──────────────────────────────────────────────────────────────     │  │
│  │   ≡  Snowmobile_Short         pending    $0.02 est    [▲] [▼] [✕]   │  │
│  │   ≡  TLB0303_Interview        pending    $0.08 est    [▲] [▼] [✕]   │  │
│  │   ≡  Demo_LongForm            pending    $0.15 est    [▲] [▼] [✕]   │  │
│  │   ≡  Archive_Restoration      pending    $0.05 est    [▲] [▼] [✕]   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │   RECENT ACTIVITY                                                     │  │
│  │   ──────────────────────────────────────────────────────────────     │  │
│  │   14:32  ✓ Euchre_Short completed ($0.02, 45s, gemini-flash)        │  │
│  │   14:28  ✓ LadyLuck_Documentary completed ($0.12, 3m 20s, gpt-4o)   │  │
│  │   14:15  ✗ MemoryProject failed: timeout (retry 1/3 scheduled)      │  │
│  │   14:10  → 2WLI1206HD started (analyst phase)                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │   COST TIMELINE (Last 60 minutes)                                    │  │
│  │        $0.15 ┤                                    ╭─╮                │  │
│  │        $0.10 ┤              ╭─╮         ╭─╮      │ │                 │  │
│  │        $0.05 ┤    ╭─╮      │ │  ╭─╮   │ │      │ │    ╭─╮          │  │
│  │        $0.00 ┼────┴─┴──────┴─┴──┴─┴───┴─┴──────┴─┴────┴─┴──────▶   │  │
│  │              14:00      14:15      14:30      14:45      15:00      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Analytics Page Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Analytics                                              [30 Days] [90 Days] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐  │
│  │   COST SUMMARY (30 DAYS)    │  │   MODEL PERFORMANCE                 │  │
│  │   ─────────────────────     │  │   ──────────────────────────────    │  │
│  │   Total Cost: $12.45        │  │   Model          Success  Avg Cost  │  │
│  │   Avg/Job: $0.04            │  │   ─────────────  ───────  ────────  │  │
│  │   Jobs: 312                 │  │   gemini-flash    98.2%    $0.015   │  │
│  │   Failed: 8 (2.5%)          │  │   openai-mini     95.1%    $0.025   │  │
│  │                             │  │   gpt-4o          99.8%    $0.18    │  │
│  │   COST BY MODEL             │  │   claude-3.5      97.5%    $0.22    │  │
│  │   ██████████████ gemini 62% │  │                                     │  │
│  │   ██████ openai-mini 25%    │  │   Best for large: gpt-4o           │  │
│  │   ███ gpt-4o 10%            │  │   Best for speed: gemini-flash     │  │
│  │   █ claude 3%               │  │   Best value: gemini-flash         │  │
│  └─────────────────────────────┘  └─────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │   DAILY COST TREND                                                    │  │
│  │   $2.00 ┤                                                             │  │
│  │   $1.50 ┤      ╭─╮                                      ╭─╮          │  │
│  │   $1.00 ┤  ╭─╮│ │  ╭─╮          ╭─╮  ╭─╮  ╭─╮        │ │  ╭─╮      │  │
│  │   $0.50 ┤──┴─┴┴─┴──┴─┴──────────┴─┴──┴─┴──┴─┴────────┴─┴──┴─┴──▶   │  │
│  │         Nov 8    Nov 15    Nov 22    Nov 29    Dec 6               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 6: Model Router & CLI-Agent Integration

### Cost-Optimized Model Selection

```python
# Routing logic (pseudocode)
def select_model(agent_type: str, transcript_size: int, quality_required: str) -> str:
    """
    Decision tree for model selection:

    1. Check CLI-Agent availability (free tier)
       - gemini CLI → use for analyst, seo-researcher
       - claude CLI → use for copy-editor (quality)

    2. Fall back to direct APIs based on:
       - transcript_size: small (<50K), medium (<120K), large (<200K), xlarge (>200K)
       - quality_required: draft, standard, premium
       - agent_type: analyst (cheap OK), formatter (context needed), copy-editor (quality)

    3. Cost hierarchy:
       CLI agents (free) → gemini-flash-8b → openai-mini → gemini-flash → gpt-4o → claude
    """
```

### CLI-Agent MCP Integration

The `workspace_ops/mcp-servers/cli-agent-server` provides these tools for cost savings:

| Tool | Use Case | Cost Savings |
|------|----------|--------------|
| `query_agent(prompt, agent="gemini")` | Brainstorming, keyword research | 100% (uses Gemini CLI subscription) |
| `query_agent(prompt, agent="claude")` | Copy editing, quality review | 100% (uses Claude CLI subscription) |
| `codex_review_code(...)` | Code review if extending agents | 100% (uses CLI) |
| `query_multiple_agents(...)` | Consensus on ambiguous decisions | Parallel queries at no API cost |

**Integration Strategy:**
1. Attempt CLI-Agent first for all non-time-critical tasks
2. Fall back to direct API if CLI unavailable or timeout
3. Track CLI vs API usage in `model_performance` table
4. Alert user if CLI availability drops (suggests subscription issue)

### Model Selection Matrix

| Agent | Transcript Size | Quality | Primary Model | Fallback |
|-------|-----------------|---------|---------------|----------|
| analyst | any | draft | CLI gemini | gemini-flash-8b |
| analyst | any | standard | gemini-flash | openai-mini |
| formatter | small | any | gemini-flash | openai-mini |
| formatter | medium | any | gemini-flash | gpt-4o-mini |
| formatter | large/xlarge | any | gpt-4o | claude-3.5 |
| copy-editor | any | draft | CLI claude | openai-mini |
| copy-editor | any | premium | claude-3.5 | gpt-4o |
| seo-researcher | any | any | CLI gemini | gemini-flash-8b |

---

## Part 7: Editor Agent UX & Session Awareness

### The Problem: Disconnected Experience

In v1.0/v2.0, users face these friction points:

| Pain Point | Current State | User Impact |
|------------|---------------|-------------|
| **Invisible outputs** | Revisions created but only referenced in chat | User must navigate to `OUTPUT/{project}/` to find files |
| **No workflow guidance** | Agent doesn't know where user is in the process | User must remember what phase they're in |
| **Manual input gathering** | Keywords → SEMRush → screenshot → upload → report | 5+ steps for a single analysis |
| **Scattered context** | Brainstorming in one file, transcript in another, revisions in a third | Constant context-switching |
| **No progress visibility** | User doesn't know what deliverables exist or are pending | Confusion about what's been done |

### Design Principle: The Agent as Guide

The editor agent should feel like a **collaborative partner with a clipboard** - always aware of:
1. **What project you're working on** (and confirming it)
2. **What phase you're in** (brainstorming, editing, analysis, conclusion)
3. **What deliverables exist** (and surfacing them proactively)
4. **What inputs are needed next** (and prompting for them)
5. **Where to find things** (artifacts in chat, or explicit paths for CLI users)

### Session State Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EDITOR SESSION STATE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PROJECT CONTEXT (always visible to agent)                          │   │
│  │                                                                      │   │
│  │  project_id: "2WLI1206HD_REV20251103"                               │   │
│  │  project_path: "OUTPUT/2WLI1206HD_REV20251103/"                     │   │
│  │  current_phase: "editing"                                            │   │
│  │                                                                      │   │
│  │  deliverables_status:                                                │   │
│  │    brainstorming:        ✅ created (Dec 8, 14:32)                  │   │
│  │    formatted_transcript: ✅ created (Dec 8, 14:45)                  │   │
│  │    copy_revision_v1:     ✅ created (Dec 8, 15:02)                  │   │
│  │    copy_revision_v2:     🔄 in_progress                             │   │
│  │    keyword_report:       ⏳ pending (needs SEMRush data)            │   │
│  │    timestamp_report:     ⏳ available (video is 23 min)             │   │
│  │                                                                      │   │
│  │  user_inputs_received:                                               │   │
│  │    transcript: ✅                                                    │   │
│  │    draft_copy: ✅ (title + short desc)                              │   │
│  │    semrush_screenshot: ❌                                            │   │
│  │    user_feedback: ✅ ("make title shorter")                         │   │
│  │                                                                      │   │
│  │  next_suggested_action: "Review copy_revision_v2 artifact below"    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Artifact Delivery Strategy

**Goal**: Deliverables should appear where the user is working, not hidden in folders.

| Interface | Artifact Delivery | Fallback |
|-----------|-------------------|----------|
| **Claude Desktop (chat)** | Claude Artifacts (inline, copyable) | "Saved to `OUTPUT/{project}/{file}` - [click to open]" |
| **Claude Code (CLI)** | Reference saved file with full path | Open in editor via `code` or `open` command |
| **Web Dashboard** | Inline preview panel | Download button + copy-to-clipboard |

**Implementation Approach:**

```python
# Pseudocode for artifact delivery
def deliver_artifact(artifact_type: str, content: str, session: EditorSession):
    """
    Deliver artifact to user based on their interface.
    Always save to disk, but present appropriately.
    """
    # 1. Always persist to project folder
    file_path = save_to_project(session.project_path, artifact_type, content)

    # 2. Deliver based on interface
    if session.interface == "claude_desktop":
        # Create Claude Artifact for inline viewing
        return create_artifact(
            title=f"{artifact_type} - {session.project_id}",
            content=content,
            type="markdown"
        )
    elif session.interface == "claude_code":
        # Reference file with actionable path
        return f"""
✅ **{artifact_type}** saved to:
   `{file_path}`

To open: `open "{file_path}"` or `code "{file_path}"`
"""
    elif session.interface == "web":
        # Return both inline preview and file reference
        return {
            "inline_content": content,
            "file_path": file_path,
            "actions": ["copy", "download", "open_in_editor"]
        }
```

### Phase-Based Workflow with Clear Triggers

Adapting v1.0's rigid phase logic for v3.0:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE FLOW WITH TRIGGERS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐                                                           │
│  │   START     │  User provides transcript                                 │
│  └──────┬──────┘                                                           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐  Agent creates Brainstorming Document                     │
│  │  PHASE 1    │  → Delivered as ARTIFACT (chat) or saved file (CLI)      │
│  │ BRAINSTORM  │  → Agent prompts: "Ready to start editing, or would      │
│  │             │     you like keyword research first?"                     │
│  └──────┬──────┘                                                           │
│         │                                                                   │
│    ┌────┴────┐                                                             │
│    │         │                                                              │
│    ▼         ▼                                                              │
│  ┌─────┐  ┌─────┐                                                          │
│  │ 2   │  │ 3   │  TRIGGERS:                                               │
│  │EDIT │  │ANLZ │  • User provides draft copy → Phase 2                   │
│  └──┬──┘  └──┬──┘  • User provides SEMRush data → Phase 3                 │
│     │        │     • User asks for keyword research → Phase 3              │
│     │        │                                                              │
│     └────┬───┘                                                             │
│          │                                                                  │
│          ▼                                                                  │
│  ┌─────────────┐  Agent creates Copy Revision Document                     │
│  │  PHASE 2    │  → ALWAYS as artifact (visible next to conversation)     │
│  │  EDITING    │  → Shows: Original | Revised | Reasoning                 │
│  │             │  → Agent prompts: "What would you like to adjust?"       │
│  └──────┬──────┘                                                           │
│         │                                                                   │
│    ┌────┴────┐   LOOP until user satisfied                                 │
│    │ REVISE  │   Each revision → new artifact version                      │
│    └────┬────┘   Always visible, never hidden                              │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐  Agent offers final deliverables:                         │
│  │  PHASE 4    │  → Formatted Transcript (if not already created)         │
│  │ CONCLUSION  │  → Timestamp Report (if video 15+ min)                   │
│  │             │  → Final keyword list (platform-ready)                    │
│  └─────────────┘                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Proactive Agent Prompts

The agent should **always end messages with a clear next step**:

| Phase | After Action | Agent Prompt |
|-------|-------------|--------------|
| **Brainstorming complete** | Delivered brainstorming doc | "When you have draft copy to review, share it here and I'll create a revision document. Or if you'd like keyword research first, upload a SEMRush screenshot or ask me to research." |
| **Revision created** | Delivered copy revision | "Here's your revision (see artifact above). What would you like to adjust? You can: (1) Give feedback on specific elements, (2) Share updated draft copy, (3) Request keyword research, or (4) Move to conclusion if satisfied." |
| **Analysis complete** | Delivered keyword report | "Based on this keyword data, I'd suggest these copy tweaks: [summary]. Would you like me to create an updated revision?" |
| **User seems done** | Multiple revisions completed | "It looks like we're in good shape! Would you like me to: (1) Generate the formatted transcript, (2) Create a timestamp report (your video is 23 min), or (3) Finalize the keyword list for platform upload?" |

### Project Status Panel

For both web dashboard and chat, maintain a visible status panel:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📁 PROJECT: 2WLI1206HD_REV20251103                    Phase: EDITING      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DELIVERABLES                          INPUTS RECEIVED                      │
│  ─────────────                         ───────────────                      │
│  ✅ Brainstorming Document             ✅ Transcript                        │
│  ✅ Formatted Transcript               ✅ Draft copy (title, short desc)   │
│  ✅ Copy Revision v1                   ❌ SEMRush data                      │
│  🔄 Copy Revision v2 (in progress)     ✅ Feedback ("shorter title")       │
│  ⏳ Keyword Report (needs SEMRush)                                         │
│  ⏳ Timestamp Report (available)                                           │
│                                                                             │
│  💡 NEXT: Review revision v2 artifact, or provide SEMRush screenshot       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Simplified SEMRush Workflow

Current flow (5+ steps) vs. target flow:

**Current:**
1. User finds keyword list in JSON/brainstorming doc
2. User copies keywords to SEMRush
3. User takes screenshot of results
4. User uploads screenshot to chat
5. Agent analyzes and creates report

**Target (v3.0):**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Option A: Streamlined Manual                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Agent provides COPY-READY keyword list in artifact:                    │
│     "Here are your keywords formatted for SEMRush. Click to copy:"         │
│     ┌────────────────────────────────────────────────────────────┐         │
│     │ wisconsin history, state parks, hiking trails, outdoor... │ [COPY]  │
│     └────────────────────────────────────────────────────────────┘         │
│                                                                             │
│  2. Agent prompts: "Paste these into SEMRush, then share the               │
│     screenshot here. I'll analyze the results and update your              │
│     keyword strategy."                                                      │
│                                                                             │
│  3. User uploads screenshot → Agent delivers Keyword Report artifact       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Option B: API Integration (Future)                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Agent calls SEMRush API directly with keywords                          │
│  2. Results analyzed automatically                                          │
│  3. Keyword Report delivered as artifact                                    │
│                                                                             │
│  (Requires: SEMRush API key, rate limit management, cost tracking)         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### CLI vs Chat Interface Awareness

The agent should detect and adapt to the interface:

| Signal | Interface | Artifact Strategy |
|--------|-----------|-------------------|
| MCP tool calls present | Claude Desktop | Use Claude Artifacts |
| Running in Claude Code | CLI | Reference file paths, suggest `open` commands |
| API call from web dashboard | Web | Return structured JSON with inline + file |

**Agent greeting should set context:**

```markdown
# Claude Desktop Version
"I see you're working on **2WLI1206HD_REV20251103**. You have a brainstorming
document ready and one copy revision so far. I'll show all new revisions as
artifacts right here in our conversation.

What would you like to work on? You can share draft copy for revision, or
I can help with keyword research."

# CLI Version
"I see you're working on **2WLI1206HD_REV20251103**.

📁 Project folder: `OUTPUT/2WLI1206HD_REV20251103/`

Existing deliverables:
  ✅ `2WLI1206HD_brainstorming.md`
  ✅ `2WLI1206HD_copy_revision_v1.md`

What would you like to work on? Share draft copy, or I can open an existing
file for you: `open OUTPUT/2WLI1206HD_REV20251103/`"
```

### Web Dashboard: Unified Queue + Editor View

The web dashboard serves double duty: **monitoring automation** AND **editing workspace**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PBS Wisconsin Editorial Assistant                              [Settings] │
├───────────────┬─────────────────────────────────────────────────────────────┤
│               │                                                             │
│  QUEUE        │   PROJECT WORKSPACE                                         │
│  ─────────    │   ─────────────────                                         │
│               │                                                             │
│  🔄 Processing│   📁 2WLI1206HD_REV20251103              Phase: EDITING    │
│  └ 2WLI1206HD │   ─────────────────────────────────────────────────────    │
│    65% fmt    │                                                             │
│               │   ┌─────────────────────────────────────────────────────┐  │
│  ⏳ Pending   │   │  DELIVERABLES              │  DOCUMENT VIEWER       │  │
│  ├ Snowmobile │   │  ─────────────             │  ────────────────      │  │
│  ├ TLB0303    │   │                            │                        │  │
│  └ Demo_Long  │   │  ✅ Brainstorming    [👁]  │  # Copy Revision v2    │  │
│               │   │  ✅ Formatted Trans  [👁]  │                        │  │
│  ✅ Completed │   │  ✅ Copy Rev v1      [👁]  │  ## Title Revisions    │  │
│  ├ Euchre     │   │  🔄 Copy Rev v2      [👁]  │  | Original | Revised |│  │
│  ├ LadyLuck   │   │  ⏳ Keyword Report        │  |----------|---------|│  │
│  └ Memory...  │   │  ⏳ Timestamps            │  | Wisconsin | Wisc... |│  │
│               │   │                            │                        │  │
│  ─────────    │   │  📋 COPY KEYWORDS:        │  ## Reasoning          │  │
│  [+ Add Job]  │   │  ┌────────────────────┐   │  The revision uses...  │  │
│               │   │  │wisconsin, hiking...│   │                        │  │
│               │   │  └────────────────────┘   │  [Copy] [Download]     │  │
│               │   │        [Copy to Clipboard]│                        │  │
│               │   └─────────────────────────────────────────────────────┘  │
│               │                                                             │
│               │   ┌─────────────────────────────────────────────────────┐  │
│               │   │  💬 CHAT WITH EDITOR AGENT                          │  │
│               │   │  ───────────────────────                            │  │
│               │   │                                                      │  │
│               │   │  Agent: Here's revision v2. The title is now 68     │  │
│               │   │  chars. What would you like to adjust?              │  │
│               │   │                                                      │  │
│               │   │  ┌────────────────────────────────────────────────┐ │  │
│               │   │  │ Make the description more active voice...     │ │  │
│               │   │  └────────────────────────────────────────────────┘ │  │
│               │   │                                        [Send] [📎]  │  │
│               │   └─────────────────────────────────────────────────────┘  │
│               │                                                             │
└───────────────┴─────────────────────────────────────────────────────────────┘
```

**Key Features:**

| Feature | Description |
|---------|-------------|
| **Split view** | Queue on left (compact), workspace on right (detailed) |
| **Click to focus** | Click any project in queue to load its workspace |
| **Document viewer** | Inline markdown rendering with copy/download buttons |
| **Eye icons** | Quick preview of any deliverable without leaving page |
| **Chat integration** | Embedded chat with editor agent (WebSocket-based) |
| **Copy-ready keywords** | One-click copy for SEMRush workflow |
| **Real-time updates** | WebSocket pushes new deliverables as they're created |

**Project Workspace Modes:**

| Mode | Trigger | View |
|------|---------|------|
| **Processing** | Job is `in_progress` | Progress bar, live logs, "Eject" button |
| **Ready to Edit** | Job is `completed` | Deliverable list, document viewer, chat |
| **Editing Active** | User is chatting | Full chat + document side-by-side |
| **Review** | Multiple revisions exist | Version comparison, "Accept" button |

**Mobile-Responsive Behavior:**

```
┌─────────────────────────────────────┐
│  PBS Editorial Assistant     [≡]   │
├─────────────────────────────────────┤
│                                     │
│  📁 2WLI1206HD            EDITING  │
│  ───────────────────────────────   │
│                                     │
│  [Queue] [Docs] [Chat] [Settings]  │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  # Copy Revision v2         │   │
│  │                             │   │
│  │  ## Title Revisions         │   │
│  │  | Original | Revised |     │   │
│  │  |----------|---------|     │   │
│  │  | Wisconsin | Wisc...|     │   │
│  │                             │   │
│  │  [Copy] [Download] [Share]  │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Type a message...      [➤] │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

**API Endpoints for Web Workspace:**

```yaml
# Workspace-specific endpoints (in addition to queue endpoints)
GET  /api/projects/{name}/workspace    # Full workspace state
GET  /api/projects/{name}/deliverables # List with content previews
GET  /api/projects/{name}/chat/history # Chat session history
POST /api/projects/{name}/chat/message # Send message to editor agent
WS   /api/projects/{name}/events       # Real-time updates for this project
```

---

## Part 7b: Chat Agent Workflow (Copy-Editor)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COPY-EDITOR CHAT WORKFLOW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐         ┌─────────────┐         ┌─────────────┐          │
│  │   Phase 1   │────────▶│   Phase 2   │────────▶│   Phase 3   │          │
│  │ Brainstorm  │         │  User Draft │         │   Revision  │          │
│  │  (auto)     │         │  (manual)   │         │   Loop      │          │
│  └─────────────┘         └─────────────┘         └──────┬──────┘          │
│                                                         │                   │
│                                                         ▼                   │
│                          ┌──────────────────────────────────────────────┐  │
│                          │  User provides:                              │  │
│                          │  - Draft title/description                   │  │
│                          │  - Screenshot of current CMS state           │  │
│                          │  - Specific feedback ("too long", "wrong     │  │
│                          │    tone", "missing keyword X")               │  │
│                          └──────────────────────────────────────────────┘  │
│                                                         │                   │
│                                                         ▼                   │
│                          ┌──────────────────────────────────────────────┐  │
│                          │  Copy-Editor Agent:                          │  │
│                          │  1. Ingests brainstorming + transcript       │  │
│                          │  2. Analyzes user draft vs. brainstorming    │  │
│                          │  3. Generates revision as ARTIFACT           │  │
│                          │  4. Provides side-by-side comparison         │  │
│                          │  5. Flags AP Style / character count issues  │  │
│                          └──────────────────────────────────────────────┘  │
│                                                         │                   │
│                                                         ▼                   │
│                          ┌──────────────────────────────────────────────┐  │
│                          │  Revision saved as:                          │  │
│                          │  OUTPUT/{project}/{project}_copy_revision_   │  │
│                          │  v{N}.md                                     │  │
│                          │                                              │  │
│                          │  Loop continues until user approves or       │  │
│                          │  marks "eject" to complete manually          │  │
│                          └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Eject Button Behavior

The "Eject" feature allows graceful mid-stream interruption:

1. **Trigger**: User clicks Eject (web) or sends `/eject` (CLI/chat)
2. **Immediate Actions**:
   - Current LLM call is allowed to complete (no wasted tokens)
   - Job status → `paused_user_takeover`
   - Partial outputs saved with `_PARTIAL` suffix
3. **Resume Options**:
   - `resume`: Continue from last checkpoint
   - `restart_phase`: Redo current phase only
   - `manual_complete`: Mark job done, user handles rest

### Smart Retry Logic

```python
RETRY_STRATEGY = {
    "rate_limit": {
        "wait_time": lambda attempt: min(60 * (2 ** attempt), 300),  # 1m, 2m, 4m, 5m max
        "fallback_model": True,  # Try different model
        "max_attempts": 3
    },
    "timeout": {
        "wait_time": lambda attempt: 30,  # Fixed 30s wait
        "fallback_model": False,  # Same model, might be temp
        "max_attempts": 2
    },
    "context_length": {
        "wait_time": lambda attempt: 0,  # Immediate
        "fallback_model": True,  # Must use larger context model
        "upgrade_path": ["gemini-flash", "gpt-4o", "claude-3.5"]
    },
    "api_error": {
        "wait_time": lambda attempt: 60,
        "fallback_model": True,
        "max_attempts": 3
    }
}
```

---

## Part 8: User Stories

### Core Workflow

**US-001: Batch Processing**
> As an editor, I want to drop multiple transcript files into a folder and have them automatically queued and processed, so I can focus on other work while metadata is generated.

**Acceptance Criteria:**
- [ ] Transcripts in `transcripts/` folder auto-detected within 30s
- [ ] Each transcript creates a job in pending status
- [ ] Jobs process in FIFO order unless prioritized
- [ ] Completed jobs have brainstorming + formatted transcript

**US-002: Priority Override**
> As an editor with a deadline, I want to move a specific transcript to the front of the queue, so it processes before other pending jobs.

**Acceptance Criteria:**
- [ ] Can prioritize via web dashboard (drag-drop or button)
- [ ] Can prioritize via CLI (`/prioritize-transcript NAME`)
- [ ] Can prioritize via API (`PATCH /api/jobs/{id}` with priority)
- [ ] Prioritized job starts within 60s if orchestrator is running

**US-003: Real-time Monitoring**
> As an editor, I want to see live progress of the current job, including which phase it's in and estimated time remaining.

**Acceptance Criteria:**
- [ ] Dashboard shows current job with progress bar
- [ ] Phase name displayed (analyst, formatter, etc.)
- [ ] Estimated time updates as processing continues
- [ ] Cost-so-far visible during processing

### Error Handling

**US-004: Failed Job Recovery**
> As an editor, when a job fails, I want to see why it failed and easily retry it without re-uploading the transcript.

**Acceptance Criteria:**
- [ ] Failed jobs show error message in UI
- [ ] "View Logs" button shows detailed error
- [ ] "Retry" button re-queues with same settings
- [ ] Retry count visible (e.g., "Attempt 2 of 3")

**US-005: Mid-Stream Eject**
> As an editor, if I realize I uploaded the wrong file or need to take over manually, I want to stop processing without losing partial work.

**Acceptance Criteria:**
- [ ] "Eject" button visible during processing
- [ ] Current LLM call completes (no token waste)
- [ ] Partial outputs saved with `_PARTIAL` suffix
- [ ] Job status clearly shows "User Takeover"

### Cost Management

**US-006: Cost Visibility**
> As a budget-conscious editor, I want to see estimated and actual costs for each job before and after processing.

**Acceptance Criteria:**
- [ ] Queue shows estimated cost per job
- [ ] Completed jobs show actual cost
- [ ] Daily/monthly totals visible on dashboard
- [ ] Alert if daily cost exceeds threshold

**US-007: Model Performance Insights**
> As a power user, I want to see which models perform best for different tasks so I can optimize my settings.

**Acceptance Criteria:**
- [ ] Analytics page shows success rate by model
- [ ] Average cost per model visible
- [ ] Recommendation for "best value" model
- [ ] Historical comparison (last 30/90 days)

### Integration

**US-008: Claude Desktop Workflow**
> As an editor using Claude Desktop, I want to interact with the queue and request revisions through natural conversation.

**Acceptance Criteria:**
- [ ] MCP tools work for queue status, prioritization
- [ ] Copy-editor agent accessible via chat
- [ ] Revisions saved automatically to project folder
- [ ] Project context (brainstorming, transcript) loaded on demand

**US-009: Web-Based Editing Workspace**
> As an editor, I want to view my deliverables and chat with the editor agent directly in the web dashboard, so I don't have to switch between browser and file explorer.

**Acceptance Criteria:**
- [ ] Click project in queue → workspace loads with all deliverables
- [ ] Document viewer renders markdown inline with copy/download buttons
- [ ] Keywords displayed with one-click copy for SEMRush workflow
- [ ] Chat panel embedded in workspace for revision requests
- [ ] New deliverables appear in real-time as they're created
- [ ] Phase indicator shows where I am in the workflow
- [ ] Clear "next step" prompt visible at all times

**US-010: Unified Experience Across Interfaces**
> As an editor who switches between CLI and web, I want my project state to be consistent regardless of which interface I use.

**Acceptance Criteria:**
- [ ] Revisions created in CLI appear immediately in web dashboard
- [ ] Chat history persists across sessions
- [ ] Project phase and deliverable status synced in real-time
- [ ] Agent greets me with current context regardless of interface
- [ ] Keywords and copy-ready text available in all interfaces

---

## Part 8b: Development Isolation Strategy

### The Challenge

v2.0 is in active production use. We need to develop v3.0 without breaking the current workflow.

### Solution: Parallel Directory Structure + Protected Branches

**Directory Strategy:**

```
editorial-assistant/
├── scripts/                    # v2.0 PRODUCTION - minimize changes
│   ├── process_queue_visual.py # ← Keep working, don't refactor
│   ├── process_queue_auto.py   # ← Keep working, don't refactor
│   ├── llm_backend.py          # ← Shared, enhance carefully
│   ├── orchestrator.py         # ← v3.0 foundation, extend with flags
│   └── dashboard/              # ← TUI components, keep working
│
├── api/                        # v3.0 NEW - develop freely
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── routers/                # Endpoint modules
│   ├── models/                 # Pydantic schemas
│   ├── services/               # Business logic
│   └── websocket.py            # Real-time events
│
├── web/                        # v3.0 NEW - develop freely
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
│
├── config/
│   ├── llm-config.json         # Shared, backward compatible
│   └── dashboard_schema.sql    # Extend with migrations, don't break
│
├── .processing-requests.json   # v2.0 uses this
└── dashboard.db                # v3.0 uses this (v2.0 orchestrator too)
```

**Key Principle:** v3.0 is mostly *additive*. The new `api/` and `web/` directories don't conflict with existing `scripts/`. We extend rather than replace.

### Branch Strategy

```
main (agent-version)
│
├── Protected: Production-ready code only
├── v2.0 scripts work here
│
├─── v3-api ────────────────────────────────
│    │ Phase 2 development
│    │ FastAPI + Pydantic + WebSocket
│    │ Merge to main when stable
│    │
├─── v3-web ────────────────────────────────
│    │ Phase 3 development
│    │ React + Tailwind dashboard
│    │ Merge to main when stable
│    │
└─── v3-integration ────────────────────────
     │ Phase 4 development
     │ CLI-Agent integration, copy-editor workflow
     │ Merge to main when stable
```

### Backward Compatibility Rules

| Component | Rule |
|-----------|------|
| `.processing-requests.json` | Keep working until v3.0 fully replaces it |
| `process_queue_visual.py` | Don't modify; TUI will become API client later |
| `process_queue_auto.py` | Don't modify; headless processing stays |
| `orchestrator.py` | Can extend, but must work standalone |
| `llm-config.json` | Add fields, never remove or rename |
| `dashboard.db` | Use migrations, never drop tables |
| MCP server | Keep all existing tools working |

### Feature Flags for Gradual Migration

```python
# config/feature_flags.py
FEATURES = {
    "use_database_queue": False,      # True = SQLite, False = JSON
    "enable_api_server": False,       # True = start FastAPI alongside
    "websocket_events": False,        # True = emit real-time events
    "new_model_router": False,        # True = use CLI-Agent integration
}
```

This allows testing v3.0 components without breaking v2.0 production use.

---

## Part 8c: Cloud Agent Sprint (Claude Code Web)

> **FOR CLAUDE CODE WEB**: This section defines your sprint scope. Focus ONLY on the tasks below. Do not modify production-critical files in `scripts/` unless explicitly listed.

### Sprint Overview

**Purpose:** Infrastructure and documentation improvements that benefit both v2.0 and v3.0, without touching production-critical code paths.

**Constraints:**
- Budget: ~$75-100 in credits
- Timeline: 3-5 focused sessions
- Scope: Documentation, type hints, validation, error handling
- **NOT in scope:** Feature development, refactoring working code, v3.0 implementation

### Why This Work Matters

| Improvement | v2.0 Benefit | v3.0 Benefit |
|-------------|--------------|--------------|
| Type hints | Easier debugging | Pydantic model foundation |
| Docstrings | Self-documenting code | Architecture understanding |
| Error messages | Less troubleshooting | Better API error responses |
| Agent documentation | Clearer workflows | Copy-editor agent design |
| Config validation | Catch errors early | Pydantic settings prep |

### Session 1: Agent & Template Audit

**Goal:** Ensure all agent prompts and templates are documented and consistent.

**Tasks:**
1. Audit `.claude/agents/*.md` files:
   - [ ] Each agent has clear role description at top
   - [ ] Input/output expectations documented
   - [ ] Phase ownership clearly stated
   - [ ] No conflicting instructions between agents

2. Audit `.claude/templates/*.md` files:
   - [ ] Templates match current deliverable formats
   - [ ] Character count requirements are accurate
   - [ ] AP Style requirements are explicit

3. Create `docs/AGENT_REFERENCE.md`:
   ```markdown
   # Agent Reference

   ## transcript-analyst
   - Phase: 1 (Brainstorming)
   - Input: Raw transcript
   - Output: brainstorming.md
   - Model preference: gemini-flash (cheap, fast)

   ## formatter
   ...
   ```

4. Create `docs/TEMPLATE_GUIDE.md`:
   - Document each template's purpose
   - Show example output for each
   - Note character limits and validation rules

**Deliverables:**
- Updated agent files with consistent structure
- `docs/AGENT_REFERENCE.md`
- `docs/TEMPLATE_GUIDE.md`

### Session 2: Type Hints & Validation

**Goal:** Add type safety to core modules (prep for Pydantic migration).

**Files to modify (SAFE - these are utility modules):**
- [ ] `scripts/llm_backend.py` - Add type hints to all functions
- [ ] `config/` - Create `settings.py` with Pydantic models

**DO NOT modify:**
- `scripts/process_queue_visual.py` (production TUI)
- `scripts/process_queue_auto.py` (production processor)

**Tasks:**
1. Add type hints to `llm_backend.py`:
   ```python
   # Before
   def select_backend(agent, transcript_size):
       ...

   # After
   def select_backend(
       agent: Literal["analyst", "formatter", "copy-editor", "seo-researcher"],
       transcript_size: int
   ) -> tuple[str, str]:  # (backend_name, model_name)
       ...
   ```

2. Create `config/settings.py` with Pydantic models:
   ```python
   from pydantic import BaseModel, Field

   class BackendConfig(BaseModel):
       type: Literal["openai", "anthropic", "gemini", "ollama"]
       endpoint: str
       model: str
       timeout: int = 180
       cost_per_project: float = 0.0
       enabled: bool = True

   class LLMConfig(BaseModel):
       primary_backend: str
       fallback_backend: str
       backends: dict[str, BackendConfig]
       ...
   ```

3. Add validation function that loads and validates `llm-config.json`:
   ```python
   def load_config() -> LLMConfig:
       """Load and validate LLM configuration."""
       with open("config/llm-config.json") as f:
           data = json.load(f)
       return LLMConfig(**data)  # Raises ValidationError if invalid
   ```

**Deliverables:**
- Type-hinted `llm_backend.py`
- New `config/settings.py` with Pydantic models
- Validation function for config loading

### Session 3: Error Handling & Logging

**Goal:** Make errors self-explanatory and logging actionable.

**Tasks:**
1. Audit error messages in `scripts/llm_backend.py`:
   - [ ] Every exception includes context (what failed, why, what to try)
   - [ ] API errors include model/backend that failed
   - [ ] Timeout errors suggest increasing timeout or trying fallback

2. Create structured logging utilities:
   ```python
   # utils/logging.py
   import logging
   from datetime import datetime

   def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
       """Configure logger with consistent format."""
       logger = logging.getLogger(name)
       handler = logging.StreamHandler()
       handler.setFormatter(logging.Formatter(
           '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
       ))
       logger.addHandler(handler)
       logger.setLevel(level)
       return logger
   ```

3. Create `docs/TROUBLESHOOTING.md`:
   ```markdown
   # Troubleshooting Guide

   ## Common Errors

   ### "Backend unavailable: gemini-flash"
   **Cause:** Gemini API not responding or rate limited
   **Solution:**
   1. Check GEMINI_API_KEY is set
   2. Wait 60 seconds and retry
   3. System will auto-fallback to openai-mini

   ### "Context length exceeded"
   **Cause:** Transcript too long for selected model
   **Solution:** System should auto-upgrade to gpt-4o
   ...
   ```

**Deliverables:**
- Improved error messages in `llm_backend.py`
- New `scripts/utils/logging.py`
- `docs/TROUBLESHOOTING.md`

### Session 4: User Documentation

**Goal:** Documentation that reduces "how does this work" questions.

**Tasks:**
1. Update `README.md`:
   - [ ] Current architecture overview (with ASCII diagram)
   - [ ] Quick start for new users
   - [ ] Link to detailed docs

2. Create `docs/QUICK_START.md`:
   - [ ] Prerequisites (Python, API keys, etc.)
   - [ ] Installation steps
   - [ ] First transcript processing walkthrough
   - [ ] Expected output structure

3. Create `docs/ARCHITECTURE.md`:
   - [ ] System overview diagram
   - [ ] Component descriptions
   - [ ] Data flow explanation
   - [ ] File/folder purposes

4. Create `docs/WORKFLOW.md`:
   - [ ] Phase 1-4 workflow with triggers
   - [ ] Deliverable creation flow
   - [ ] User decision points
   - [ ] Example session walkthrough

**Deliverables:**
- Updated `README.md`
- `docs/QUICK_START.md`
- `docs/ARCHITECTURE.md`
- `docs/WORKFLOW.md`

### Session 5: Validation & Handoff

**Goal:** Verify all work and create summary.

**Tasks:**
1. Run any existing tests
2. Validate type hints with `mypy` (if installed)
3. Verify documentation accuracy
4. Create `SPRINT_SUMMARY.md`:
   - What was accomplished
   - Files modified/created
   - Recommendations for v3.0 development
   - Estimated future token savings

**Deliverables:**
- `SPRINT_SUMMARY.md`
- Clean commit history

### Files You MAY Modify

| File | Modifications Allowed |
|------|----------------------|
| `.claude/agents/*.md` | Add docstrings, clarify instructions |
| `.claude/templates/*.md` | Fix formatting, add examples |
| `scripts/llm_backend.py` | Add type hints, improve errors |
| `config/settings.py` | Create new (Pydantic models) |
| `scripts/utils/logging.py` | Create new |
| `docs/*.md` | Create/update documentation |
| `README.md` | Update with current info |

### Files You MUST NOT Modify

| File | Reason |
|------|--------|
| `scripts/process_queue_visual.py` | Production TUI |
| `scripts/process_queue_auto.py` | Production processor |
| `scripts/orchestrator.py` | v3.0 development (local) |
| `mcp-server/*` | Production MCP tools |
| `.processing-requests.json` | Production queue state |
| `dashboard.db` | Production database |

---

## Part 9: Development Roadmap

### Phase 1: The Iron Core (State & Logic) - ✅ COMPLETE

**Goal:** Replace brittle JSON files with robust database and decoupled worker.

| Task | Status | Notes |
|------|--------|-------|
| Schema design (jobs, session_stats) | ✅ Done | `config/dashboard_schema.sql` |
| Migration script (JSON → SQLite) | ✅ Done | 17 jobs migrated |
| Orchestrator refactor | ✅ Done | `scripts/orchestrator.py` (553 lines) |
| Database connection management | ✅ Done | Thread-safe connections |

### Phase 2: The Nervous System (API Layer)

**Goal:** Enable external control without touching files.

| Task | Priority | Complexity | Agent Assignment |
|------|----------|------------|------------------|
| FastAPI project setup | High | Low | CLI-Agent (Gemini) |
| Core endpoints (queue CRUD) | High | Medium | Claude Code |
| Job control endpoints (pause/resume/retry) | High | Medium | Claude Code |
| WebSocket event system | Medium | High | Claude Code |
| Pydantic models for validation | Medium | Low | CLI-Agent (Gemini) |
| OpenAPI documentation | Low | Low | CLI-Agent (Gemini) |
| Authentication (optional) | Low | Medium | Defer to Phase 4 |

**Estimated Duration:** 2-3 focused development sessions

### Phase 3: The Face (Web & Visuals)

**Goal:** Visually appealing, substantially complete interface with unified queue + editing workspace.

| Task | Priority | Complexity | Agent Assignment |
|------|----------|------------|------------------|
| React + Vite + Tailwind setup | High | Low | CLI-Agent (Gemini) |
| Dashboard page (queue + stats) | High | Medium | Claude Code |
| Queue management (drag-drop) | High | High | Claude Code |
| **Project workspace panel** | High | High | Claude Code |
| **Document viewer (markdown)** | High | Medium | Claude Code |
| **Embedded chat component** | High | High | Claude Code |
| Job detail page | Medium | Medium | CLI-Agent (Claude) |
| Analytics page | Medium | Medium | Parallel: Explore agent |
| Settings page | Low | Low | CLI-Agent (Gemini) |
| WebSocket integration | High | Medium | Claude Code |
| **Copy-to-clipboard helpers** | Medium | Low | CLI-Agent (Gemini) |
| Dark mode support | Low | Low | CLI-Agent (Gemini) |
| Mobile-responsive layout | Medium | Medium | CLI-Agent (Gemini) |

**Estimated Duration:** 4-5 focused development sessions (increased due to workspace features)

### Phase 4: Polish & Integration

**Goal:** Production-ready with all integrations.

| Task | Priority | Complexity | Agent Assignment |
|------|----------|------------|------------------|
| CLI-Agent MCP integration | High | Medium | Claude Code |
| Chat agent workflow (copy-editor) | High | High | Claude Code |
| Eject button implementation | Medium | Medium | Claude Code |
| Smart retry logic | Medium | Low | CLI-Agent (Claude) |
| Screenshot ingestion | Low | Medium | Defer |
| CMS direct push (hooks) | Low | High | Defer |
| Mobile-responsive web | Low | Low | CLI-Agent (Gemini) |
| User onboarding flow | Medium | Medium | Claude Code |

**Estimated Duration:** 2-3 focused development sessions

### Phase 5: Documentation & Release

| Task | Priority | Agent Assignment |
|------|----------|------------------|
| User documentation (HOW_TO_USE.md) | High | CLI-Agent (Claude) |
| API documentation | Medium | Auto-generated from OpenAPI |
| Developer setup guide | High | Claude Code |
| Video walkthrough | Low | Human |
| Changelog consolidation | Medium | CLI-Agent (Gemini) |

---

## Part 10: Parallel Development Strategy

### Agent Collaboration Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR / AGENT COLLABORATION                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CLAUDE CODE (ORCHESTRATOR)                        │   │
│  │                                                                      │   │
│  │  Responsibilities:                                                   │   │
│  │  • Complex architectural decisions                                   │   │
│  │  • Multi-file refactoring                                           │   │
│  │  • Integration between components                                    │   │
│  │  • Code review and quality assurance                                │   │
│  │  • Debugging complex issues                                          │   │
│  │  • User-facing workflow design                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CLI-AGENT (WORKER POOL)                           │   │
│  │                                                                      │   │
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────┐  │   │
│  │  │  Gemini Agent     │  │  Claude Agent     │  │  Codex Agent    │  │   │
│  │  │                   │  │                   │  │  (if available) │  │   │
│  │  │  Good for:        │  │  Good for:        │  │                 │  │   │
│  │  │  • Boilerplate    │  │  • Documentation  │  │  Good for:      │  │   │
│  │  │  • Simple CRUD    │  │  • Explanations   │  │  • Code review  │  │   │
│  │  │  • Config files   │  │  • Copy editing   │  │  • Bug finding  │  │   │
│  │  │  • Test stubs     │  │  • User stories   │  │                 │  │   │
│  │  │  • CSS/styling    │  │  • Quality review │  │                 │  │   │
│  │  └───────────────────┘  └───────────────────┘  └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SPECIALIZED CLAUDE AGENTS                         │   │
│  │                                                                      │   │
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────┐  │   │
│  │  │  Explore Agent    │  │  Plan Agent       │  │ Code Trouble-   │  │   │
│  │  │                   │  │                   │  │ shooter Agent   │  │   │
│  │  │  Good for:        │  │  Good for:        │  │                 │  │   │
│  │  │  • Codebase       │  │  • Architecture   │  │  Good for:      │  │   │
│  │  │    exploration    │  │    planning       │  │  • Debugging    │  │   │
│  │  │  • Finding files  │  │  • Breaking down  │  │    failed code  │  │   │
│  │  │  • Understanding  │  │    complex tasks  │  │  • Root cause   │  │   │
│  │  │    patterns       │  │  • Trade-off      │  │    analysis     │  │   │
│  │  │                   │  │    analysis       │  │                 │  │   │
│  │  └───────────────────┘  └───────────────────┘  └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Task Assignment Guidelines

| Task Type | Primary Agent | Rationale |
|-----------|---------------|-----------|
| **Architectural decisions** | Claude Code | Needs full context, multi-file awareness |
| **New feature implementation** | Claude Code | Complex integration |
| **Boilerplate/scaffolding** | CLI-Agent (Gemini) | Repetitive, well-defined |
| **Pydantic models** | CLI-Agent (Gemini) | Schema → code translation |
| **CSS/Tailwind styling** | CLI-Agent (Gemini) | Visual, low-risk |
| **API endpoint stubs** | CLI-Agent (Gemini) | Template-based |
| **Documentation writing** | CLI-Agent (Claude) | Quality prose |
| **User story refinement** | CLI-Agent (Claude) | Clear communication |
| **Code review** | CLI-Agent (Codex) | Independent perspective |
| **Codebase exploration** | Explore Agent | Efficient search |
| **Implementation planning** | Plan Agent | Structured breakdown |
| **Debugging failures** | Code Troubleshooter | Root cause focus |

### Parallelization Opportunities

**Phase 2 (API Layer):**
```
Parallel Stream A: FastAPI setup + Pydantic models (CLI-Agent Gemini)
Parallel Stream B: Core endpoint logic (Claude Code)
Merge Point: Integration testing
```

**Phase 3 (Web Dashboard):**
```
Parallel Stream A: React component scaffolding (CLI-Agent Gemini)
Parallel Stream B: State management + WebSocket (Claude Code)
Parallel Stream C: Analytics calculations (Explore Agent for research)
Merge Point: Full page integration
```

---

## Part 11: Open Questions & Decisions

### Resolved

| Question | Decision | Rationale |
|----------|----------|-----------|
| SQLite vs Postgres? | SQLite | Single-user, local-first, simpler deployment |
| FastAPI vs Flask? | FastAPI | Async support, auto OpenAPI docs, Pydantic native |
| React vs Vue vs Svelte? | React | Larger ecosystem, more familiar, Tailwind works well |

### Still Open

| Question | Options | Decision Needed By |
|----------|---------|-------------------|
| **Authentication?** | None (local only) vs. Simple token vs. OAuth | Phase 4 |
| **Redis for job queue?** | SQLite polling vs. Redis pub/sub | Phase 4 (if remote processing needed) |
| **Artifact delivery in chat?** | Claude Artifacts vs. File saves vs. Both | Phase 4 (copy-editor workflow) |
| **Remote processing?** | Local only vs. Optional remote worker | Post-v3.0 |
| **Notification system?** | None vs. Desktop notifications vs. Email | Post-v3.0 |

---

## Part 12: Success Metrics

### v3.0 Release Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Queue reliability** | 99% jobs complete without manual intervention | Success rate over 100 jobs |
| **API coverage** | All queue operations available via API | Endpoint checklist |
| **Web dashboard** | Usable for daily workflow | User testing (self) |
| **Cost tracking** | Accurate to within 5% | Compare to API billing |
| **Response time** | Dashboard loads in <2s | Lighthouse score |
| **Documentation** | New user can onboard in <30min | Timed test |

### Long-term Goals (Post-v3.0)

- **Multi-user support**: Separate queues/projects per user
- **Team features**: Shared project review, approval workflows
- **Mobile app**: Push notifications, quick status checks
- **Plugin system**: Custom agents, external integrations
- **Self-hosted option**: Docker compose for easy deployment

---

## Appendix A: File Structure (Target)

```
editorial-assistant/
├── .claude/
│   ├── agents/                 # Agent system prompts
│   ├── commands/               # Slash commands
│   └── templates/              # Output templates
├── api/                        # NEW: FastAPI application
│   ├── __init__.py
│   ├── main.py                 # App entry point
│   ├── routers/
│   │   ├── queue.py
│   │   ├── jobs.py
│   │   ├── system.py
│   │   ├── config.py
│   │   └── analytics.py
│   ├── models/                 # Pydantic models
│   │   ├── job.py
│   │   ├── config.py
│   │   └── events.py
│   ├── services/
│   │   ├── database.py
│   │   ├── orchestrator.py
│   │   └── model_router.py
│   └── websocket.py
├── web/                        # NEW: React dashboard
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── lib/
│   ├── package.json
│   └── vite.config.ts
├── scripts/                    # Processing scripts
│   ├── orchestrator.py         # Database-backed worker
│   ├── llm_backend.py          # Model router
│   └── dashboard/              # TUI components
├── config/
│   ├── dashboard_schema.sql
│   ├── llm-config.json
│   └── settings.py             # NEW: Pydantic settings
├── mcp-server/                 # Claude Desktop integration
├── transcripts/                # Input files
├── OUTPUT/                     # Processed projects
├── docs/
│   ├── USER_GUIDE.md
│   ├── API.md
│   └── archive/
├── dashboard.db                # SQLite database
├── CLAUDE.md
├── DESIGN_v3.0.md              # This document
└── README.md
```

---

## Appendix B: Migration Checklist

### Before v3.0 Release

- [ ] All queue operations work via API
- [ ] Web dashboard deployed and functional
- [ ] TUI updated to use API (not direct file access)
- [ ] MCP server updated to use API
- [ ] Database migration script tested
- [ ] Backup/restore procedure documented
- [ ] Cost tracking validated against actual bills
- [ ] All 4 agents working with new orchestrator
- [ ] Documentation complete and reviewed

### Cleanup

- [ ] Remove `.processing-requests.json` dependency
- [ ] Archive `process_queue_visual.py` (replaced by API + TUI client)
- [ ] Consolidate working docs to `docs/archive/`
- [ ] Update CLAUDE.md with v3.0 commands
- [ ] Tag release in git

---

*This document is a living specification. Update as decisions are made and implementation progresses.*
