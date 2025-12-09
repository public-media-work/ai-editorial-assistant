# Editorial Assistant v3.0 - Design & Vision Document

**Goal:** Transition from a sophisticated CLI tool (v2.0) to a robust, database-backed application (v3.0) that decouples processing logic from the user interface, enabling greater stability, scalability, and future web/mobile integrations.

---

## 🏗 Architectural Shift

| Feature | v2.0 (Current) | v3.0 (Target) | Why Change? |
| :--- | :--- | :--- | :--- |
| **State Management** | JSON Files (`.processing-requests.json`) | SQLite Database (`dashboard.db`) | Eliminates file locking issues; enables robust history & concurrent access. |
| **Processing Logic** | Monolithic UI Script (`process_queue_visual.py`) | Headless Orchestrator (`orchestrator.py`) | Decouples "viewing" from "doing". The UI can crash without stopping the worker. |
| **Interface** | Terminal UI (Rich) | Hybrid (TUI + Web Dashboard + CLI) | Allows remote monitoring and control; enables future React/Mobile apps. |
| **Control Plane** | Direct Script Execution | FastAPI Server | API-based control allows for web apps, mobile notifications, and easier integration. |
| **Configuration** | Raw JSON | Pydantic Models | Prevents runtime crashes due to typos or invalid config values. |

---

## 🗺 Development Roadmap (Phases)

### Phase 1: The Iron Core (State & Logic)
**Goal:** Replace brittle JSON files with a robust database and a decoupled worker.
- [ ] **Schema Design:** generic `Job` model and `Session` model in SQLite.
- [ ] **Migration Script:** Convert existing `.processing-requests.json` to SQLite.
- [ ] **The Orchestrator:** Refactor logic into a background worker that polls the DB.
- [ ] **Harnessing:** Ensure the orchestrator acts as a proper "Initializer Agent", setting up the environment for the coding agent.

### Phase 2: The Nervous System (API Layer)
**Goal:** Allow external control without touching files.
- [ ] **FastAPI Setup:** Initialize server with endpoints (`GET /queue`, `POST /queue/move`, `POST /control/pause`).
- [ ] **External Control:** Allow other apps (or agents) to query status and pause/resume execution via API.

### Phase 3: The Face (Web & Visuals)
**Goal:** A "visually appealing, substantially complete" interface.
- [ ] **Web Dashboard:** React + Vite + Tailwind CSS.
- [ ] **Features:** Drag-and-drop queue reordering, real-time cost charts, log streaming.
- [ ] **Legacy TUI:** Maintain the terminal UI as a lightweight client connecting to the same DB/API.

---

## 📝 Wishlist & Ideas

### Core Processing & Workflow
- [ ] **"Eject" Button:** Ability to stop an agent mid-stream and take over manually without breaking the queue.
- [ ] **Smart Retries:** Intelligent backoff for API rate limits (e.g., "Wait 5m then try Gemini instead of OpenAI").
- [ ] **Priority Queue:** Ability to reorder jobs dynamically in the database.
- [ ] **Direct Output:** Hooks to push finished transcripts directly to CMS or shared folders.

### Integrations & Cost Control
- [ ] **CLI MCP Server:** Explore using the `workspace_ops` CLI MCP logic to leverage existing paid CLI subscriptions (GitHub Copilot CLI, etc.) instead of direct API calls.
- [ ] **Model Router:** External service or logic to switch LLMs based on task complexity (cost vs. quality).
- [ ] **Remote Job Routing:** Infrastructure (Redis?) to potentially route jobs to a remote server for processing.

---

## ❓ Open Questions & User Notes

### Infrastructure & Architecture
- **Infrastructure:** Do we need Redis for job routing if we move to a remote server model? Would that improve local performance or just add bloat?
- **Artifacts:** How can we get the chat agent to more consistently deliver revisions as artifacts, rather than in-line as part of the conversation?
- **Workflow:** To better accommodate workflows of different users, is it feasible to essentially have a CLI workflow and the chat-based editor agent, both interfacing with the automated processing component of the project?
    - *Ideal Scenario:* You clone this project repo, provide API keys through a clearly-defined and straightforward onboarding flow, and then you'd have the option to either interact with the editor agent via the CLI of your AI agent of choice (we're planning for Claude since that's the primary user usecase) as well as desktop chat front-ends for the editing agent.

### Usability & Design
- **Holistic Design:** For usability, we should plan some more holistic design to the experience of using the app, including a basic web app that provides both the visualizations of the queue in progress and some of the user configuration features so that an AI agent isn't needed to manage the app.
- **Documentation:** As we dial in this 3.0 version, let's also be sure to clean up working documents, consolidate agent communication into a subfolder within the repo, and make sure we have a plan for robust workflow documentation as part of the roadmap.
- **User Stories:** We should write some user stories that capture a lot of the edge cases as well as the core workflow, to give the editor agent a clear idea of what to expect as they shephard the user through the process.

### Visualization upgrades
- Let's clarify the problems we're trying to address with the visualizations, and use that as our guide: 
1) A user should be able to tell, at a glance, which transcript files are in the processing queue, what their progress is if they are mid-processing, and what their estimated and then final cost ends up being. A time estimate is also helpful but ideally that would be combined with some kind of visual progress indicator for each job. 
2) It should be fairly easy for a user to see if a job is near the bottom of the queue, and there should be a simple GUI way for them to elevate it to the top priority. 
3) If a job fails for some reason, there should be some sort of link to logs or more information as to what happened, as well as a way to restart the job. 
4) We can probably seperate the long-term tracking analytics to another page or view, which should really just visualize the average cost per job and what the total cost in the last 30 and 90 days has been. Bonus if we can include some kind of insight in terms of which models perform best at which job as part of this view. 

### Cost & External Dependencies
- **Cost Control:** Let's both explore the use of the CLI-agent local MCP service (which utilizes account-based coding agents via their command line interfaces) and external vendors and services that provide LLM switching based on the complexity of the task at hand.
    - *Note:* This CLI MCP server is in the `workspace_ops` meta-repo so it would likely be an optional tool that could be added to editorial-assistant, since that introduces outside dependencies on other work that would need to be publicly released. If we needed to replicate or iterate on the CLI MCP server within this project, that would be acceptable.

### Project Philosophy
- **User Personas:** The priority is building a tool that works for my editing needs, so being a bit custom is okay, but I would like the option to share the project with others, so let's try to balance those two user profiles in mind.

---

## 🚧 Status: Planned
*Work on v3.0 is scheduled to begin in the New Year. Current focus is on v2.0 stability.*
