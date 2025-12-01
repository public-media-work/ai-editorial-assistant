# Dashboard Enhancement Plan

## Overview
Comprehensive improvements to `scripts/process_queue_visual.py` to add enhanced monitoring, control, and cost visualization capabilities.

---

## 1. Session State Persistence

### Goal
Preserve session statistics across dashboard restarts and enable historical tracking.

### Implementation

#### 1.1 Session State File
**Location**: `OUTPUT/.dashboard_session.json`

**Structure**:
```json
{
  "session_id": "2025-12-01T10:30:00Z",
  "start_time": "2025-12-01T10:30:00Z",
  "last_updated": "2025-12-01T10:45:23Z",
  "stats": {
    "projects_processed": 15,
    "projects_failed": 2,
    "total_cost": 3.4567,
    "total_processing_minutes": 45.2,
    "backend_usage": {
      "openai-mini": {"calls": 20, "cost": 2.1},
      "anthropic-sonnet": {"calls": 10, "cost": 1.3567}
    }
  },
  "cost_timeline": [
    {"timestamp": "2025-12-01T10:30:15Z", "cost": 0.12, "project": "HNOW_123"},
    {"timestamp": "2025-12-01T10:32:45Z", "cost": 0.24, "project": "HNOW_124"}
  ],
  "errors": [
    {
      "timestamp": "2025-12-01T10:35:00Z",
      "project": "HNOW_125",
      "error": "Backend timeout",
      "backend": "openai-mini"
    }
  ]
}
```

#### 1.2 SessionManager Class
```python
class SessionManager:
    def __init__(self, session_file: Path):
        self.session_file = session_file
        self.session_data = self.load_or_create()

    def load_or_create(self) -> dict:
        """Load existing session or create new one"""

    def add_project_completion(self, project: str, cost: float, duration: float, status: str):
        """Record a completed project"""

    def add_cost_event(self, project: str, cost: float):
        """Add to cost timeline for visualization"""

    def add_error(self, project: str, error: str, backend: str):
        """Record an error"""

    def get_stats(self) -> dict:
        """Return current session statistics"""

    def get_cost_timeline(self, minutes: int = 60) -> list:
        """Get cost events for last N minutes"""

    def export_session(self, export_path: Path):
        """Export session data as JSON/CSV"""

    def reset_session(self):
        """Start a new session (keep historical data)"""
```

---

## 2. Enhanced Error Visibility

### Goal
Make errors immediately visible and provide detailed error inspection.

### Implementation

#### 2.1 Error Panel
**New panel in layout showing recent errors**:
```
┌─ RECENT ERRORS (3) ────────────────────────┐
│ [10:35] HNOW_125 • Backend timeout         │
│         Backend: openai-mini               │
│ [10:32] HNOW_122 • Invalid transcript      │
│         Backend: anthropic-sonnet          │
│ [10:28] HNOW_118 • Rate limit exceeded     │
│         Backend: openai-mini               │
│                                            │
│ Press [E] to view full error details       │
└────────────────────────────────────────────┘
```

#### 2.2 Error Detail Modal
When user presses `[E]`, show full-screen modal with:
- Complete stack trace
- Project details
- Backend configuration used
- Retry options
- Option to skip or requeue

#### 2.3 Queue Table Enhancement
Add visual indicators for failed projects:
```python
if status == "failed":
    status_txt = Text("⚠ FAILED", style="bold red blink")
    # Add error icon to project name
    project_cell = f"🔴 [bold]{project_name}[/]\n[dim magenta]{program_name}[/]"
```

---

## 3. Expanded Queue Management Commands

### Goal
Provide comprehensive operator control over queue processing.

### Implementation

#### 3.1 New Keyboard Commands
| Key | Command | Description |
|-----|---------|-------------|
| `P` | Pause/Resume | Toggle processing of queue |
| `S` | Skip Current | Move current project to end of queue |
| `R` | Retry Failed | Move all failed projects back to pending |
| `E` | Error Details | Show detailed error viewer |
| `X` | Remove Project | Remove selected project from queue |
| `D` | Dashboard Restart | Restart the dashboard (reload config) |
| `L` | Log Viewer | Toggle full log viewer mode |
| `T` | Export Session | Export current session stats |

#### 3.2 Pause/Resume State
```python
class DashboardState:
    def __init__(self):
        # ... existing fields ...
        self.paused = False
        self.pause_reason = None

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.log("⏸ Processing paused by operator")
        else:
            self.log("▶ Processing resumed")
```

#### 3.3 Project Selection
Add interactive project selection:
- Use arrow keys or number to select project
- Selected project highlights in queue table
- Commands like `[X]` Remove or `[↑][↓]` Priority operate on selection

---

## 4. Aggregate Statistics Panel with Cost Visualization

### Goal
Real-time session statistics with visual cost tracking over time.

### Implementation

#### 4.1 Stats Panel Layout
```
┌─ SESSION STATISTICS ────────────────────────────────────────┐
│ Session: 45m 23s │ Processed: 15 ✓ 2 ✗ │ Rate: 0.38/min   │
│                                                              │
│ COST TRACKING                                                │
│ Current Session: $3.46 │ Avg/Project: $0.23 │ Est. Hour: $4.14│
│                                                              │
│ ┌─ Cost Timeline (Last 60min) ──────────────────────────┐   │
│ │ $0.50 ┤                                            ╭─╮│   │
│ │ $0.40 ┤                                    ╭─╮     │ ││   │
│ │ $0.30 ┤                        ╭─╮ ╭─╮     │ │ ╭─╮ │ ││   │
│ │ $0.20 ┤            ╭─╮ ╭─╮     │ │ │ │ ╭─╮ │ │ │ │ │ ││   │
│ │ $0.10 ┤ ╭─╮ ╭─╮ ╭─╮│ │ │ │ ╭─╮ │ │ │ │ │ │ │ │ │ │ │ ││   │
│ │ $0.00 ┴─┴─┴─┴─┴─┴─┴┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘│   │
│ │       10:00      10:15      10:30      10:45      11:00  │   │
│ └────────────────────────────────────────────────────────┘   │
│                                                              │
│ Backend Distribution:                                        │
│ ■■■■■■■■■■ openai-mini      20 calls $2.10 (61%)           │
│ ■■■■■ anthropic-sonnet      10 calls $1.36 (39%)           │
└──────────────────────────────────────────────────────────────┘
```

#### 4.2 Cost Timeline Implementation
Use `rich.bar` or ASCII plotting for cost visualization:

```python
def make_cost_sparkline(timeline: list[dict], width: int = 50) -> str:
    """Generate ASCII sparkline from cost timeline"""
    if not timeline:
        return "No data"

    # Bucket costs by time intervals
    buckets = bucket_timeline(timeline, num_buckets=width)
    max_cost = max(buckets)

    # Generate bar chart
    bars = []
    for cost in buckets:
        height = int((cost / max_cost) * 5) if max_cost > 0 else 0
        bars.append(get_bar_char(height))

    return "".join(bars)

def bucket_timeline(timeline: list[dict], num_buckets: int) -> list[float]:
    """Group timeline into N time buckets and sum costs"""
    # Implementation here
```

#### 4.3 Running Cost Display
Add prominent running total with rate calculation:
```python
def calculate_cost_rate(session: SessionManager) -> dict:
    """Calculate cost per minute/hour based on recent activity"""
    timeline = session.get_cost_timeline(minutes=60)
    if not timeline:
        return {"per_minute": 0.0, "per_hour": 0.0}

    total_cost = sum(e["cost"] for e in timeline)
    duration_minutes = (
        datetime.fromisoformat(timeline[-1]["timestamp"]) -
        datetime.fromisoformat(timeline[0]["timestamp"])
    ).total_seconds() / 60

    per_minute = total_cost / duration_minutes if duration_minutes > 0 else 0
    return {
        "per_minute": per_minute,
        "per_hour": per_minute * 60,
        "avg_per_project": total_cost / len(timeline) if timeline else 0
    }
```

---

## 5. Persistent Log System with Viewer

### Goal
Keep comprehensive logs and provide interactive viewer.

### Implementation

#### 5.1 Enhanced Logging
```python
class DashboardState:
    def __init__(self):
        # ... existing ...
        self.full_logs = []  # Unlimited log buffer
        self.log_file = LOG_DIR / "dashboard_session.log"

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime('%H:%M:%S')
        full_message = f"[{timestamp}] [{level}] {message}"

        # Add to in-memory buffer
        self.full_logs.insert(0, full_message)
        self.logs.insert(0, f"[{timestamp}] {message}")  # Display buffer

        if len(self.logs) > 8:
            self.logs.pop()

        # Write to file
        with open(self.log_file, "a") as f:
            f.write(full_message + "\n")
```

#### 5.2 Log Viewer Mode
When user presses `[L]`, switch to full-screen log viewer:
```
┌─ DASHBOARD LOG VIEWER ─────────────────── [ESC] to exit ──┐
│ [10:45:23] [INFO] ✓ Formatter complete (15234 chars)     │
│ [10:45:18] [INFO] ✓ Analyst complete (8901 chars)        │
│ [10:45:10] [INFO] Running formatter                       │
│ [10:45:10] [INFO] Running analyst                         │
│ [10:45:05] [INFO] Processing HNOW_126 (45234 chars)...    │
│ [10:44:50] [WARN] Retry: openai-mini failed for analyst   │
│ [10:44:45] [INFO] ✓ Formatter complete (12456 chars)     │
│ ... (scrollable with arrow keys)                          │
│                                                            │
│ Filters: [A]ll [I]nfo [W]arn [E]rror    Search: /pattern  │
└────────────────────────────────────────────────────────────┘
```

Features:
- Scrollable with arrow keys or Page Up/Down
- Filter by log level
- Search with `/` pattern
- Export visible logs to file

---

## 6. Progress Indicators for Long-Running Tasks

### Goal
Show sub-task progress during agent execution.

### Implementation

#### 6.1 Progress Bar in Active Panel
Use the imported `rich.progress.Progress`:

```python
# In run_with_fallback or agent functions
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

def run_analyst_agent(project_name: str, transcript: str, llm: LLMBackend) -> str:
    state.set_active(project_name, "Analyzing transcript...", "analyst")

    # Update progress through state
    state.set_progress(0, "Loading agent prompt...")
    analyst_prompt = load_agent_prompt("transcript-analyst")

    state.set_progress(20, "Sending to LLM backend...")
    brainstorming, backend_used, cost = run_with_fallback(...)

    state.set_progress(80, "Writing output...")
    # ... write file ...

    state.set_progress(100, "Complete")
    return filename
```

#### 6.2 DashboardState Enhancement
```python
class DashboardState:
    def __init__(self):
        # ... existing ...
        self.current_progress = 0  # 0-100
        self.progress_message = ""

    def set_progress(self, percent: int, message: str = ""):
        with self.lock:
            self.current_progress = percent
            self.progress_message = message
```

#### 6.3 Visual Progress Bar
```
┌─ ACTIVE PROCESSING ────────────────────────────────────┐
│ PROJECT    HNOW_126                                    │
│ PROGRAM    Here & Now                                  │
│ STATUS     Analyzing transcript...                     │
│ BACKEND    anthropic-sonnet                            │
│                                                        │
│ Progress: ████████████░░░░░░░░ 60%                    │
│           Generating brainstorming document...         │
│                                                        │
│ VIDEO LEN  00:28:45                                    │
│ JOB COST   $0.1234                                     │
└────────────────────────────────────────────────────────┘
```

---

## 7. Dashboard Restart Command

### Goal
Allow operator to restart dashboard without losing session state.

### Implementation

#### 7.1 Restart Mechanism
```python
def restart_dashboard():
    """Restart the dashboard process"""
    state.log("🔄 Restarting dashboard...")

    # Save current session state
    session_manager.save()

    # Get the current script path
    script = Path(__file__).absolute()

    # Use os.execv to replace current process
    os.execv(sys.executable, [sys.executable, str(script)] + sys.argv[1:])
```

#### 7.2 Keyboard Binding
```python
# In main loop
if c == 'd':
    # Confirm restart
    state.log("Press [D] again to confirm restart...")
    time.sleep(0.5)
    if is_data() and sys.stdin.read(1).lower() == 'd':
        restart_dashboard()
```

#### 7.3 Graceful Restart
Before restart:
1. Pause current processing
2. Save session state
3. Save queue state
4. Write restart marker file
5. Execute restart

On startup:
1. Check for restart marker
2. Restore session state
3. Resume from where it left off

---

## 8. Configuration System

### Goal
Make dashboard behavior customizable without code changes.

### Implementation

#### 8.1 Configuration File
**Location**: `config/dashboard.json`

```json
{
  "display": {
    "refresh_rate": 4,
    "log_buffer_size": 8,
    "theme": "default",
    "show_sparkline": true,
    "cost_timeline_minutes": 60
  },
  "behavior": {
    "auto_clear_completed": false,
    "auto_check_new_interval_seconds": 0,
    "pause_on_error": false,
    "max_retries": 3
  },
  "cost": {
    "warning_threshold_per_hour": 10.0,
    "alert_threshold_per_project": 1.0,
    "show_estimates": true
  },
  "keyboard": {
    "pause": "p",
    "skip": "s",
    "retry": "r",
    "errors": "e",
    "remove": "x",
    "restart": "d",
    "logs": "l",
    "export": "t",
    "quit": "q",
    "clear": "c",
    "new": "n"
  }
}
```

#### 8.2 Config Class
```python
class DashboardConfig:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> dict:
        if not self.config_path.exists():
            return self.get_defaults()
        with open(self.config_path) as f:
            return {**self.get_defaults(), **json.load(f)}

    def get_defaults(self) -> dict:
        return {
            "display": {"refresh_rate": 4, "log_buffer_size": 8},
            # ... etc
        }

    def get(self, path: str, default=None):
        """Get config value by dot path: 'display.refresh_rate'"""
        keys = path.split('.')
        value = self.config
        for key in keys:
            value = value.get(key, {})
        return value if value != {} else default
```

---

## 9. Session Export Functionality

### Goal
Export session data for reporting and analysis.

### Implementation

#### 9.1 Export Formats
```python
class SessionExporter:
    def __init__(self, session: SessionManager):
        self.session = session

    def export_json(self, path: Path):
        """Export full session data as JSON"""
        with open(path, 'w') as f:
            json.dump(self.session.session_data, f, indent=2)

    def export_csv(self, path: Path):
        """Export project list as CSV"""
        import csv
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'project', 'status', 'cost', 'duration',
                'backend', 'timestamp', 'error'
            ])
            writer.writeheader()
            # Write rows from cost_timeline + errors

    def export_summary_md(self, path: Path):
        """Export human-readable summary as Markdown"""
        stats = self.session.get_stats()

        md = f"""# Session Summary

**Session ID**: {self.session.session_data['session_id']}
**Duration**: {self.calculate_duration()}
**Total Projects**: {stats['projects_processed']}
**Success Rate**: {self.calculate_success_rate()}%
**Total Cost**: ${stats['total_cost']:.4f}

## Cost Breakdown by Backend
{self.format_backend_costs(stats['backend_usage'])}

## Timeline
{self.format_timeline()}

## Errors
{self.format_errors()}
"""
        with open(path, 'w') as f:
            f.write(md)
```

#### 9.2 Export UI
When user presses `[T]`:
```
┌─ EXPORT SESSION ───────────────────────────────────┐
│                                                    │
│ Export format:                                     │
│   [1] JSON (full data)                            │
│   [2] CSV (project list)                          │
│   [3] Markdown (summary report)                   │
│   [4] All formats                                 │
│                                                    │
│ Export to: OUTPUT/reports/session_2025-12-01.ext  │
│                                                    │
│ Press 1-4 to export, ESC to cancel                │
└────────────────────────────────────────────────────┘
```

---

## 10. Updated Layout Design

### Goal
Reorganize layout to accommodate new panels.

### Implementation

#### 10.1 New Layout Structure
```
┌─────────────────────────────────────────────────────────────┐
│                      HEADER (3 lines)                       │
├──────────────────────┬──────────────────────────────────────┤
│                      │                                      │
│   ACTIVE PROCESSING  │        QUEUE MATRIX                  │
│      (Left 30%)      │         (Right 70%)                  │
│                      │                                      │
├──────────────────────┴──────────────────────────────────────┤
│                  SESSION STATISTICS                         │
│          (includes cost visualization)                      │
│                      (25%)                                  │
├─────────────────────────────────────┬───────────────────────┤
│        RECENT ERRORS (3-5 lines)    │  CONTROLS (3-5 lines) │
└─────────────────────────────────────┴───────────────────────┘
```

#### 10.2 Dynamic Layout Modes
- **Normal Mode**: Full layout as shown above
- **Log Viewer Mode**: Full screen logs
- **Error Detail Mode**: Full screen error inspector
- **Compact Mode**: Hide stats panel for smaller terminals

#### 10.3 Responsive Design
Adjust layout based on terminal size:
```python
def generate_layout(console: Console) -> Layout:
    terminal_height = console.height
    terminal_width = console.width

    layout = Layout()

    if terminal_height < 30:
        # Compact mode: stack vertically
        layout.split_column(...)
    else:
        # Full mode: complex layout
        layout.split(...)

    return layout
```

---

## Implementation Priority

### Phase 1: Core Functionality (Highest Priority)
1. ✅ Session state persistence (SessionManager)
2. ✅ Aggregate statistics panel with cost tracking
3. ✅ Dashboard restart command
4. ✅ Cost visualization (sparkline/timeline)

### Phase 2: Enhanced Control
5. ✅ Expanded queue management (pause, skip, retry)
6. ✅ Error visibility panel
7. ✅ Progress indicators

### Phase 3: Advanced Features
8. ✅ Persistent log system with viewer
9. ✅ Configuration system
10. ✅ Session export functionality

---

## Testing Plan

### Unit Tests
- SessionManager save/load
- Cost calculation functions
- Timeline bucketing algorithm
- Export functions

### Integration Tests
- Full processing cycle with state persistence
- Restart recovery
- Multi-project queue processing with cost tracking

### Manual Testing
- All keyboard commands
- Layout rendering at different terminal sizes
- Error handling and display
- Cost visualization accuracy

---

## File Structure

```
editorial-assistant/
├── scripts/
│   ├── process_queue_visual.py (enhanced)
│   ├── dashboard/
│   │   ├── __init__.py
│   │   ├── session_manager.py
│   │   ├── config.py
│   │   ├── exporter.py
│   │   ├── cost_visualizer.py
│   │   └── ui_components.py
│   └── llm_backend.py
├── config/
│   └── dashboard.json
├── OUTPUT/
│   ├── .dashboard_session.json
│   └── reports/
│       └── session_*.{json,csv,md}
└── logs/
    └── dashboard_session.log
```

---

## Configuration Migration

For backward compatibility, the enhanced dashboard should:
1. Work without configuration file (use defaults)
2. Auto-create config with defaults on first run
3. Preserve existing queue file format
4. Add new fields to queue items gracefully

---

## Documentation Updates

After implementation:
1. Update `CLAUDE.md` with new keyboard commands
2. Create `docs/DASHBOARD_GUIDE.md` with screenshots
3. Add configuration reference
4. Document export formats
5. Add troubleshooting section

---

## Estimated Effort

- **Phase 1**: 4-6 hours (core functionality)
- **Phase 2**: 3-4 hours (enhanced control)
- **Phase 3**: 4-5 hours (advanced features)
- **Testing & Documentation**: 2-3 hours

**Total**: 13-18 hours of development time

---

## Success Criteria

1. ✅ Session statistics persist across restarts
2. ✅ Cost visualization updates in real-time
3. ✅ All keyboard commands work reliably
4. ✅ Dashboard can restart without losing state
5. ✅ Errors are prominently displayed and actionable
6. ✅ Logs are searchable and exportable
7. ✅ Session data can be exported in multiple formats
8. ✅ Dashboard remains responsive under load
9. ✅ Configuration changes apply without code modification
10. ✅ Layout adapts to terminal size gracefully
