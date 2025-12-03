# Dashboard Overhaul & Modernization Roadmap

## 1. Executive Summary
The current visual dashboard (`process_queue_visual.py`) and its web prototype (`dashboard_web_monitor.py`) rely on a file-based synchronization mechanism (`.processing-requests.json`) that is becoming a bottleneck. As the system scales, this approach causes race conditions, makes "pause/resume" functionality difficult to implement reliably, and limits the ability to have a responsive, rich user interface.

This roadmap proposes moving to a **Database-Backed Orchestrator Pattern**. By centralizing state in a lightweight SQLite database and exposing it via an API, we decouple the *processing logic* from the *user interface*. This allows for a robust, "long-running agent" harness that can survive restarts, handle interruptions, and support a modern, interactive Web Dashboard.

## 2. Architecture Evolution

### Current State (Fragile)
*   **State:** JSON files (`.processing-requests.json`, `.dashboard_session.json`).
*   **Concurrency:** File locking / Polling (Race condition prone).
*   **UI:** TUI (Terminal) mixed with processing logic; Read-only Web Monitor.
*   **Control:** "Pause" is checking a flag in a loop; "Restart" is hard.

### Target State (Robust)
*   **State:** **SQLite Database** (`dashboard.db`).
    *   Tables: `Queue` (Jobs), `SessionStats` (Costs, Time), `Logs`.
    *   Benefits: Transactional integrity, easy sorting/filtering, concurrent access.
*   **Logic:** **Headless Orchestrator** (`orchestrator.py`).
    *   A dedicated background worker that polls the DB for `pending` jobs.
    *   Handles the "Harness" logic: initializing agents, tracking costs, updating DB state.
*   **Control Plane:** **FastAPI Server** (`server.py`).
    *   Exposes endpoints: `GET /queue`, `POST /queue/move`, `POST /control/pause`.
    *   Serves the frontend.
*   **UI:** **Modern Web Dashboard** (React + Vite).
    *   Real-time updates (polling or WebSockets).
    *   Rich controls: Drag-and-drop reordering, cost visualization charts.

## 3. Development Roadmap

### Phase 1: The Iron Core (State & Logic)
**Goal:** Replace brittle JSON files with a robust database and a decoupled worker.

1.  **Schema Design:** Create a generic `Job` model and `Session` model in SQLite.
    *   Fields: `id`, `project_path`, `status` (pending, in_progress, completed, failed), `priority`, `estimated_cost`, `logs`.
2.  **Migration Script:** Write `scripts/migrate_queue.py` to convert existing `.processing-requests.json` to SQLite.
3.  **The Orchestrator:** Refactor `process_queue_auto.py` into `services/orchestrator.py`.
    *   **Input:** Polls SQLite for highest priority `pending` job.
    *   **Process:** Calls `editorial_assistant.py` logic (imported or subprocess).
    *   **Output:** Updates DB status to `completed` or `failed`; logs costs to `Session` table.
    *   **Control:** Checks a DB-flag `system_status` (RUNNING/PAUSED) before every job.

### Phase 2: The Nervous System (API Layer)
**Goal:** Allow external control without touching files.

1.  **FastAPI Setup:** Initialize `scripts/dashboard/server/app.py`.
2.  **Endpoints:**
    *   `GET /api/queue`: Returns list of jobs.
    *   `POST /api/queue/{id}/move`: Reorder priority.
    *   `POST /api/queue/{id}/cancel`: Mark as cancelled.
    *   `GET /api/stats`: Returns session costs and aggregate metrics.
    *   `POST /api/system/pause`: Sets global pause flag.
3.  **Integration:** Ensure the Orchestrator respects the API-triggered flags immediately.

### Phase 3: The Face (Visual Dashboard)
**Goal:** A "visually appealing, substantially complete" interface.

*   **Technology:** React (TypeScript) + Vite + Tailwind CSS.
*   **Components:**
    *   **Kanban/Queue List:** Drag-and-drop list of projects. Status indicators (Spinner for active, Check for done).
    *   **Control Deck:** Big "Pause", "Resume", "Add Project" buttons.
    *   **Telemetry Panel:** Live charts (Recharts) showing "Cost per Project", "Total Session Cost", "Tokens/Sec".
    *   **Log Viewer:** Scrollable window showing the live logs of the current active job (streamed from DB/API).
*   **Deployment:** The FastAPI server serves the compiled React static files. One command `start-dashboard.sh` launches both.

## 4. Alignment with Long-Running Agent Guidance
*   **Harnessing:** The `Orchestrator` acts as the "Initializer Agent" described in Anthropic's docs—setting up the environment and strictly managing the lifecycle of the "Coding Agent" (in this case, the editorial processor).
*   **Persistence:** By using SQLite, the "Feature List" (Queue) and "Progress Log" (Session Stats) are permanent artifacts. If the machine crashes, the Orchestrator restarts, sees a job `in_progress` that stalled, marks it `failed` (or retries), and continues.
*   **Observability:** The API layer allows us to attach *any* monitor (even a future AI Supervisor) to watch the system state without interfering with the worker process.

## 5. Immediate Next Steps
1.  **Approve this Roadmap.**
2.  **Scaffold the React App:** Create `dashboard-ui/` inside the project.
3.  **Scaffold the FastAPI Server:** Create `scripts/server/`.
4.  **Begin Phase 1 Implementation:** Define the SQLite schema.
