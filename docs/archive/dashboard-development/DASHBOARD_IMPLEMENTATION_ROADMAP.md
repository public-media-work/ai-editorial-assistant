# Dashboard Enhancement - Implementation Roadmap

## Overview
This roadmap breaks down the dashboard enhancements into discrete steps, identifying which tasks can be safely delegated to cheaper models (Haiku) versus complex tasks requiring more capable models (Sonnet).

---

## Task Classification

### 🟢 **Haiku-Safe Tasks**
Simple, well-defined tasks with clear specifications:
- Boilerplate code generation
- Simple utility functions
- File I/O operations
- Data structure definitions
- Basic UI components
- Configuration files
- Documentation updates

### 🟡 **Sonnet-Recommended Tasks**
Complex tasks requiring architectural decisions or integration:
- System architecture and integration
- Complex state management
- Thread-safe operations
- UI layout coordination
- Error handling strategies
- Performance optimization

---

## Phase 1: Foundation & Core Functionality

### Step 1.1: Create Module Structure 🟢 **HAIKU**
**Complexity**: Low
**Why Haiku**: Simple file/directory creation with boilerplate

**Tasks**:
- [ ] Create `scripts/dashboard/` directory
- [ ] Create `scripts/dashboard/__init__.py`
- [ ] Create empty module files:
  - `session_manager.py`
  - `config.py`
  - `exporter.py`
  - `cost_visualizer.py`
  - `ui_components.py`

**Deliverable**: Directory structure with skeleton files

---

### Step 1.2: Implement Configuration System 🟢 **HAIKU**
**Complexity**: Low
**Why Haiku**: Simple JSON schema and basic class with getters

**Tasks**:
- [ ] Create `config/dashboard.json` with default configuration
- [ ] Implement `DashboardConfig` class in `scripts/dashboard/config.py`:
  - `__init__()` - load or create config
  - `load_config()` - read JSON file
  - `get_defaults()` - return default dict
  - `get(path, default)` - dot-path accessor

**Deliverable**: Configuration system with defaults

**Spec for Haiku**:
```python
# config/dashboard.json structure (see DASHBOARD_ENHANCEMENT_PLAN.md section 8.1)
# DashboardConfig class with methods as specified in section 8.2
```

---

### Step 1.3: Implement Session Data Structure 🟢 **HAIKU**
**Complexity**: Low
**Why Haiku**: Well-defined data structure with simple I/O

**Tasks**:
- [ ] Implement `SessionManager` class in `scripts/dashboard/session_manager.py`:
  - `__init__(session_file)` - initialize with file path
  - `load_or_create()` - load existing or create new session
  - `_save()` - private method to write to file with atomic writes
  - Data structure as specified in plan section 1.1

**Deliverable**: SessionManager with load/save capability

**Spec for Haiku**:
```python
# Session file structure from DASHBOARD_ENHANCEMENT_PLAN.md section 1.1
# Basic CRUD operations for session data
# Use atomic writes (write to temp, then rename)
```

---

### Step 1.4: Implement Session Statistics Methods 🟡 **SONNET**
**Complexity**: Medium
**Why Sonnet**: Requires careful state management, thread safety, and integration

**Tasks**:
- [ ] Add to `SessionManager`:
  - `add_project_completion(project, cost, duration, status)` - with thread locking
  - `add_cost_event(project, cost)` - append to timeline
  - `add_error(project, error, backend)` - record error
  - `get_stats()` - calculate aggregate statistics
  - `get_cost_timeline(minutes)` - filter timeline by time window
  - `reset_session()` - archive current, start new

**Deliverable**: Fully functional SessionManager with thread-safe operations

**Integration Points**:
- Must integrate with existing `DashboardState.lock`
- Coordinate with existing queue operations
- Handle edge cases (empty timeline, division by zero)

---

### Step 1.5: Implement Cost Calculation Utilities 🟢 **HAIKU**
**Complexity**: Low
**Why Haiku**: Pure functions with clear mathematical operations

**Tasks**:
- [ ] Create `scripts/dashboard/cost_visualizer.py`
- [ ] Implement functions:
  - `calculate_cost_rate(session: SessionManager) -> dict` - as in plan section 4.3
  - `bucket_timeline(timeline: list, num_buckets: int) -> list[float]` - group by time
  - `format_currency(amount: float) -> str` - consistent formatting

**Deliverable**: Cost calculation utilities

**Spec for Haiku**:
```python
# Functions as specified in DASHBOARD_ENHANCEMENT_PLAN.md section 4.3
# Pure functions, no state management
# Handle edge cases: empty lists, zero duration
```

---

### Step 1.6: Implement ASCII Sparkline Generator 🟢 **HAIKU**
**Complexity**: Low-Medium
**Why Haiku**: Well-defined algorithm, no complex integration

**Tasks**:
- [ ] Add to `cost_visualizer.py`:
  - `make_cost_sparkline(timeline, width, height)` - generate ASCII chart
  - `get_bar_char(height_level)` - return appropriate Unicode block char
  - Helper functions for scaling and formatting

**Deliverable**: ASCII sparkline generator

**Spec for Haiku**:
```python
# Use Unicode block characters: ▁▂▃▄▅▆▇█
# Scale data to fit height (e.g., 5 levels)
# Handle empty data gracefully
# Return formatted multi-line string
```

---

### Step 1.7: Integrate SessionManager into DashboardState 🟡 **SONNET**
**Complexity**: High
**Why Sonnet**: Complex integration with existing state management

**Tasks**:
- [ ] Modify `DashboardState` class in `process_queue_visual.py`:
  - Add `session_manager: SessionManager` field
  - Update `add_cost()` to also call `session_manager.add_cost_event()`
  - Update `log()` to record errors via session manager
  - Initialize session manager in `__init__()`
- [ ] Modify `process_project()` to record completions
- [ ] Update error handling to use `session_manager.add_error()`

**Deliverable**: Integrated session tracking

**Integration Challenges**:
- Thread safety with existing locks
- Coordinate with existing queue state
- Ensure no duplicate cost recording
- Handle session persistence during crashes

---

### Step 1.8: Create Statistics Panel UI Component 🟢 **HAIKU**
**Complexity**: Medium
**Why Haiku**: Following existing UI patterns, well-specified layout

**Tasks**:
- [ ] Add to `ui_components.py`:
  - `make_stats_panel(state: DashboardState, session: SessionManager) -> Panel`
  - Format session duration, project counts, success rate
  - Display cost metrics (total, average, rate)
  - Include backend distribution bars

**Deliverable**: Statistics panel renderer

**Spec for Haiku**:
```python
# Follow existing panel patterns from make_active_panel()
# Use rich.table.Table for layout
# Format as shown in DASHBOARD_ENHANCEMENT_PLAN.md section 4.1
# Call cost_visualizer functions for sparkline
```

---

### Step 1.9: Implement Dashboard Restart Command 🟡 **SONNET**
**Complexity**: High
**Why Sonnet**: Process management, graceful shutdown, state coordination

**Tasks**:
- [ ] Implement `restart_dashboard()` function:
  - Pause processing
  - Save all state (session, queue)
  - Create restart marker file
  - Execute `os.execv()` to restart process
- [ ] Add keyboard handler for `[D]` with confirmation
- [ ] Add startup check for restart marker

**Deliverable**: Restart command with state preservation

**Critical Considerations**:
- Must handle in-flight agent executions
- Ensure atomicity of state saves
- Test recovery from various states
- Handle edge case: restart during project processing

---

### Step 1.10: Update Layout to Include Stats Panel 🟡 **SONNET**
**Complexity**: Medium
**Why Sonnet**: Layout coordination, responsive design decisions

**Tasks**:
- [ ] Modify `generate_layout()` in `process_queue_visual.py`:
  - Add stats panel between main content and footer
  - Adjust proportions as per plan section 10.1
  - Handle responsive resizing for small terminals
- [ ] Test layout at various terminal sizes

**Deliverable**: Updated layout with statistics panel

**Integration Points**:
- Coordinate with existing `make_header()`, `make_active_panel()`, etc.
- Ensure refresh rate handles additional panel
- Test rendering performance

---

## Phase 2: Enhanced Control & Visibility

### Step 2.1: Add Pause/Resume State to DashboardState 🟢 **HAIKU**
**Complexity**: Low
**Why Haiku**: Simple state flag addition

**Tasks**:
- [ ] Add to `DashboardState`:
  - `paused: bool = False`
  - `pause_reason: str | None = None`
  - `toggle_pause()` method as in plan section 3.2

**Deliverable**: Pause state management

---

### Step 2.2: Implement Queue Management Functions 🟢 **HAIKU**
**Complexity**: Low-Medium
**Why Haiku**: Well-defined queue operations

**Tasks**:
- [ ] Add functions to `process_queue_visual.py`:
  - `skip_current_project(project_name)` - move to end of queue
  - `retry_failed_projects()` - reset failed to pending
  - `remove_project(project_name)` - delete from queue

**Deliverable**: Queue manipulation functions

**Spec for Haiku**:
```python
# Each function loads queue, modifies list, saves queue
# Use existing QUEUE_LOCK for thread safety
# Call update_queue_item() for changes
# Log operations via state.log()
```

---

### Step 2.3: Integrate Pause/Resume into Main Loop 🟡 **SONNET**
**Complexity**: Medium
**Why Sonnet**: Control flow integration, timing considerations

**Tasks**:
- [ ] Modify main loop in `main()`:
  - Check `state.paused` before processing projects
  - Display pause indicator in UI
  - Add `[P]` keyboard handler
- [ ] Update `make_active_panel()` to show pause state

**Deliverable**: Working pause/resume functionality

**Integration Challenges**:
- Handle pause during project processing
- Ensure clean pause between projects
- Update UI to show paused state clearly

---

### Step 2.4: Create Error Panel UI Component 🟢 **HAIKU**
**Complexity**: Low
**Why Haiku**: Following existing panel patterns

**Tasks**:
- [ ] Add to `ui_components.py`:
  - `make_error_panel(session: SessionManager) -> Panel`
  - Display last 3-5 errors from `session.get_stats()["errors"]`
  - Format as shown in plan section 2.1

**Deliverable**: Error panel renderer

---

### Step 2.5: Implement Error Detail Viewer 🟡 **SONNET**
**Complexity**: Medium
**Why Sonnet**: Modal UI, keyboard navigation, state management

**Tasks**:
- [ ] Create modal viewer for error details:
  - Full-screen error display
  - Keyboard navigation (ESC to close)
  - Show stack trace, project details, backend info
  - Options to retry or skip
- [ ] Add `[E]` keyboard handler
- [ ] Integrate with layout system

**Deliverable**: Interactive error viewer

**UI Challenges**:
- Modal overlay over existing layout
- Keyboard input routing
- Context switching between normal and modal view

---

### Step 2.6: Add Progress Tracking to DashboardState 🟢 **HAIKU**
**Complexity**: Low
**Why Haiku**: Simple state fields

**Tasks**:
- [ ] Add to `DashboardState`:
  - `current_progress: int = 0` (0-100)
  - `progress_message: str = ""`
  - `set_progress(percent, message)` method

**Deliverable**: Progress state fields

---

### Step 2.7: Add Progress Indicators to Agent Functions 🟢 **HAIKU**
**Complexity**: Low
**Why Haiku**: Inserting calls to existing state method

**Tasks**:
- [ ] Update `run_analyst_agent()`:
  - Add `state.set_progress()` calls at key points (0%, 20%, 80%, 100%)
- [ ] Update `run_formatter_agent()`:
  - Add similar progress updates

**Deliverable**: Agent progress tracking

**Spec for Haiku**:
```python
# Add progress calls at:
# - 0%: Start
# - 20%: After loading prompt
# - 80%: After LLM response
# - 100%: After writing file
```

---

### Step 2.8: Update Active Panel with Progress Bar 🟢 **HAIKU**
**Complexity**: Low-Medium
**Why Haiku**: Following existing rich UI patterns

**Tasks**:
- [ ] Modify `make_active_panel()` to include:
  - Progress bar using `state.current_progress`
  - Progress message display
  - Format as shown in plan section 6.3

**Deliverable**: Visual progress indicator

---

### Step 2.9: Implement All Keyboard Command Handlers 🟡 **SONNET**
**Complexity**: Medium
**Why Sonnet**: Input routing, command coordination, error handling

**Tasks**:
- [ ] Add keyboard handlers in main loop for:
  - `[P]` - Pause/Resume
  - `[S]` - Skip
  - `[R]` - Retry Failed
  - `[E]` - Error Details
  - `[X]` - Remove (with selection)
  - `[L]` - Log Viewer
  - `[T]` - Export
- [ ] Update controls panel to show all commands

**Deliverable**: Complete keyboard command system

**Integration Points**:
- Coordinate with existing `[Q]`, `[N]`, `[C]` handlers
- Handle conflicts and invalid states
- Provide user feedback for each command

---

### Step 2.10: Update Layout with Error Panel 🟡 **SONNET**
**Complexity**: Medium
**Why Sonnet**: Layout coordination, space allocation

**Tasks**:
- [ ] Modify `generate_layout()`:
  - Add error panel in footer section
  - Adjust proportions (split footer between errors and controls)
  - Handle responsive design for small terminals

**Deliverable**: Layout with error visibility

---

## Phase 3: Advanced Features

### Step 3.1: Implement Enhanced Logging 🟢 **HAIKU**
**Complexity**: Low-Medium
**Why Haiku**: File I/O with well-defined format

**Tasks**:
- [ ] Modify `DashboardState.log()`:
  - Add `level` parameter (INFO, WARN, ERROR)
  - Maintain unlimited `full_logs` buffer
  - Write to `LOG_DIR / "dashboard_session.log"`
  - Keep existing 8-line display buffer

**Deliverable**: Persistent logging system

---

### Step 3.2: Implement Log Viewer UI 🟡 **SONNET**
**Complexity**: High
**Why Sonnet**: Complex modal UI with scrolling, filtering, search

**Tasks**:
- [ ] Create full-screen log viewer:
  - Scrollable log display (arrow keys, Page Up/Down)
  - Filter by log level `[A]ll [I]nfo [W]arn [E]rror`
  - Search functionality with `/pattern`
  - ESC to exit
- [ ] Add `[L]` keyboard handler
- [ ] Implement view state management (scroll position, filters)

**Deliverable**: Interactive log viewer

**UI Challenges**:
- Efficient rendering of large log buffers
- Search highlighting
- Real-time log updates while viewing
- Keyboard input routing

---

### Step 3.3: Implement Session Export - JSON 🟢 **HAIKU**
**Complexity**: Low
**Why Haiku**: Simple JSON serialization

**Tasks**:
- [ ] Create `SessionExporter` class in `exporter.py`
- [ ] Implement `export_json(path)` method
- [ ] Create `OUTPUT/reports/` directory if needed

**Deliverable**: JSON export functionality

---

### Step 3.4: Implement Session Export - CSV 🟢 **HAIKU**
**Complexity**: Low
**Why Haiku**: Straightforward CSV writing

**Tasks**:
- [ ] Add `export_csv(path)` to `SessionExporter`
- [ ] Flatten session data to tabular format
- [ ] Handle missing/optional fields

**Deliverable**: CSV export functionality

---

### Step 3.5: Implement Session Export - Markdown Summary 🟢 **HAIKU**
**Complexity**: Medium
**Why Haiku**: Template-based string formatting

**Tasks**:
- [ ] Add `export_summary_md(path)` to `SessionExporter`
- [ ] Implement helper methods:
  - `calculate_duration()`
  - `calculate_success_rate()`
  - `format_backend_costs()`
  - `format_timeline()`
  - `format_errors()`
- [ ] Format as shown in plan section 9.1

**Deliverable**: Markdown summary export

---

### Step 3.6: Create Export UI Modal 🟡 **SONNET**
**Complexity**: Medium
**Why Sonnet**: Interactive UI, file path handling

**Tasks**:
- [ ] Create export modal:
  - Format selection (1-4)
  - File path display/editing
  - Export execution
  - Success/error feedback
- [ ] Add `[T]` keyboard handler
- [ ] Handle file conflicts, directory creation

**Deliverable**: Export UI with all formats

---

### Step 3.7: Add Queue Selection/Navigation 🟡 **SONNET**
**Complexity**: High
**Why Sonnet**: Interactive selection state, UI coordination

**Tasks**:
- [ ] Add selection state to `DashboardState`:
  - `selected_project: str | None`
  - Arrow key handlers for navigation
- [ ] Update `make_queue_table()` to highlight selection
- [ ] Modify commands (`[X]`, priority) to operate on selection

**Deliverable**: Interactive queue selection

**UI Challenges**:
- Selection state persistence
- Visual highlighting in rich tables
- Coordinate with dynamic queue updates

---

### Step 3.8: Implement Responsive Layout Logic 🟡 **SONNET**
**Complexity**: Medium
**Why Sonnet**: Layout decisions based on terminal size

**Tasks**:
- [ ] Add terminal size detection in `generate_layout()`
- [ ] Implement layout modes:
  - Full (terminal height ≥ 30)
  - Compact (terminal height < 30)
- [ ] Hide/rearrange panels based on space
- [ ] Test at various terminal sizes

**Deliverable**: Responsive layout system

---

### Step 3.9: Add Visual Enhancements to Queue Table 🟢 **HAIKU**
**Complexity**: Low
**Why Haiku**: Simple conditional styling

**Tasks**:
- [ ] Update `make_queue_table()`:
  - Add error icons (🔴) for failed projects
  - Use blinking style for processing status
  - Add color coding for cost thresholds
  - Format according to plan section 2.3

**Deliverable**: Enhanced queue table styling

---

### Step 3.10: Final Integration & Testing 🟡 **SONNET**
**Complexity**: High
**Why Sonnet**: End-to-end testing, bug fixing, performance tuning

**Tasks**:
- [ ] Test complete workflow:
  - Start dashboard with queue
  - Process projects with all new features
  - Test all keyboard commands
  - Verify restart preserves state
  - Test export functionality
- [ ] Performance optimization:
  - Monitor refresh rate impact
  - Optimize cost visualization rendering
  - Check thread safety under load
- [ ] Bug fixes and edge cases
- [ ] Code cleanup and documentation

**Deliverable**: Fully functional enhanced dashboard

---

## Phase 4: Documentation

### Step 4.1: Update CLAUDE.md 🟢 **HAIKU**
**Complexity**: Low
**Why Haiku**: Straightforward documentation update

**Tasks**:
- [ ] Add new keyboard commands to CLAUDE.md
- [ ] Document configuration file location and format
- [ ] Add examples of new features

**Deliverable**: Updated project instructions

---

### Step 4.2: Create Dashboard Guide 🟢 **HAIKU**
**Complexity**: Low
**Why Haiku**: Following template, descriptive writing

**Tasks**:
- [ ] Create `docs/DASHBOARD_GUIDE.md`
- [ ] Document:
  - All keyboard commands
  - Configuration options
  - Export formats
  - Cost visualization interpretation
  - Troubleshooting tips

**Deliverable**: Comprehensive user guide

---

### Step 4.3: Add Inline Code Documentation 🟢 **HAIKU**
**Complexity**: Low
**Why Haiku**: Adding docstrings to existing code

**Tasks**:
- [ ] Add docstrings to all new classes and functions
- [ ] Add type hints where missing
- [ ] Add comments for complex logic

**Deliverable**: Well-documented code

---

## Execution Strategy

### Recommended Workflow

#### **Sprint 1: Foundation (Steps 1.1-1.10)**
Execute in order, alternating between Haiku and Sonnet:

1. **Haiku**: 1.1, 1.2, 1.3 (structure, config, basic session) - ~1 hour
2. **Sonnet**: 1.4 (session stats with thread safety) - ~45 min
3. **Haiku**: 1.5, 1.6 (cost utilities, sparkline) - ~1.5 hours
4. **Sonnet**: 1.7 (integration) - ~1 hour
5. **Haiku**: 1.8 (stats panel UI) - ~1 hour
6. **Sonnet**: 1.9, 1.10 (restart + layout) - ~2 hours

**Total Sprint 1**: ~7-8 hours

#### **Sprint 2: Control & Visibility (Steps 2.1-2.10)**
1. **Haiku**: 2.1, 2.2, 2.4, 2.6, 2.7, 2.8 (simple additions) - ~2.5 hours
2. **Sonnet**: 2.3, 2.5, 2.9, 2.10 (complex integration) - ~3 hours

**Total Sprint 2**: ~5.5 hours

#### **Sprint 3: Advanced Features (Steps 3.1-3.10)**
1. **Haiku**: 3.1, 3.3, 3.4, 3.5, 3.9 (logging, export, styling) - ~3 hours
2. **Sonnet**: 3.2, 3.6, 3.7, 3.8, 3.10 (complex UI, testing) - ~4 hours

**Total Sprint 3**: ~7 hours

#### **Sprint 4: Documentation (Steps 4.1-4.3)**
1. **Haiku**: All documentation tasks - ~1.5 hours

**Total Sprint 4**: ~1.5 hours

---

## Cost Optimization

### Estimated Token Usage

**Haiku Tasks**: ~22 tasks × 5K avg tokens = ~110K tokens
**Sonnet Tasks**: ~18 tasks × 20K avg tokens = ~360K tokens

**Rough Cost Estimate**:
- Haiku: 110K input + 50K output = $0.05
- Sonnet: 360K input + 150K output = $4.50

**Total**: ~$4.55 (vs ~$8-10 if all Sonnet)

**Savings**: ~40-45% cost reduction

---

## Quality Gates

Before moving to next phase:

1. ✅ All Haiku-generated code passes basic syntax check
2. ✅ Sonnet reviews Haiku code for integration issues
3. ✅ Each feature tested in isolation before integration
4. ✅ No regressions in existing dashboard functionality

---

## Rollback Strategy

Each step should:
- [ ] Commit working code to git before starting next step
- [ ] Include step number in commit message
- [ ] Tag major milestones (end of each sprint)

This allows easy rollback if issues arise.

---

## Success Metrics

- [ ] All keyboard commands functional
- [ ] Session persists across restarts
- [ ] Cost visualization accurate within 1%
- [ ] UI responsive at 4Hz refresh rate
- [ ] No memory leaks during 8+ hour sessions
- [ ] Error rate < 1% for user commands

---

## Next Steps

**Ready to start?** Begin with Sprint 1, Step 1.1:

```bash
# Create the module structure (Haiku task)
mkdir -p scripts/dashboard
touch scripts/dashboard/__init__.py
touch scripts/dashboard/session_manager.py
touch scripts/dashboard/config.py
touch scripts/dashboard/exporter.py
touch scripts/dashboard/cost_visualizer.py
touch scripts/dashboard/ui_components.py
```

Would you like me to proceed with the first Haiku batch (Steps 1.1-1.3)?
