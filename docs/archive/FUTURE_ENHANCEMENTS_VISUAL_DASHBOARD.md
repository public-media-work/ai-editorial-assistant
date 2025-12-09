# Visual Dashboard: Future Enhancements

The visual dashboard is a Rich-based terminal UI that monitors and controls the Editorial Assistant pipeline: it shows the active job, queue matrix, stats/costs, errors, and lets operators manage work with keyboard commands (pause, skip, retry, requeue, export, restart, etc.). Core features are functional; the items below capture remaining polish and stretch goals.

---

## Immediate Next Steps (Punchlist)

- Ship full-screen log viewer: filters (Info/Warn/Error), search, smooth scrolling, and non-blocking real-time updates.
- Upgrade error viewer: modal overlay with full messages, retry/skip actions, and no truncation.
- Tighten restart semantics: pause/flush in-flight work and persist session before execv; add confirmation when jobs are running.
- Evaluate web-based monitor: spike a lightweight web UI (FastAPI/Flask + HTMX/Alpine) to mirror dashboard data with richer visuals and easier navigation; compare operator ergonomics vs. CLI.
- Documentation pass: add CLAUDE.md command reference and a short “operations runbook” for common actions (requeue, export, restart, archive).

---

## High-Value Enhancements

### 1. Log Viewer UI (Step 3.2)
**Priority**: Medium
**Complexity**: High (~2 hours)
**Status**: Partially Complete

**Description**:
Full-screen modal log viewer with interactive features:
- Scrollable log display (arrow keys, Page Up/Down)
- Filter by log level: `[A]ll [I]nfo [W]arn [E]rror`
- Search functionality with `/pattern` and highlighting
- Real-time log updates while viewing
- ESC to exit

**Current State**:
- Basic viewer implemented: `[L]` opens a paginated console view of recent logs (newest first) with next/prev navigation.
- Persistent log file at `logs/dashboard_session.log`.

**Gaps**:
- No level filters, search, or smooth scrolling; not a full-screen modal.

**Workarounds**:
- View logs directly: `tail -f logs/dashboard_session.log`
- Full log buffer accessible in `state.full_logs`
- All logs persisted to file automatically

**Implementation Notes**:
- Create modal state management
- Implement efficient rendering for large buffers
- Add keyboard input routing for viewer
- Handle concurrent log writes during viewing
- See `DASHBOARD_IMPLEMENTATION_ROADMAP.md` Step 3.2 for details

---

### 2. Queue Selection/Navigation (Step 3.7)
**Priority**: Medium
**Complexity**: High (~2 hours)
**Status**: Complete

**Description**:
Interactive queue selection and navigation:
- Arrow keys (↑↓) to navigate through queue items
- Visual highlighting of selected project in queue table
- Operations work on selected item:
  - `[X]` - Remove selected project
  - Priority commands operate on selection
  - Skip/retry work on selection

**Current Workaround**:
- `[S]` - Skip currently processing project
- `[R]` - Retry all failed projects
- `[C]` - Clear all completed projects
- Commands work on active/all projects

**Implementation Notes**:
- Implemented: `selected_project`, row highlighting, arrow key handlers, and selection-aware skip/remove/requeue.
- Commands that act on selection: `[S]` skip, `[X]` remove, `[Z]` requeue single project.
- See `DASHBOARD_IMPLEMENTATION_ROADMAP.md` Step 3.7 for details

---

## Low-Priority Enhancements

### 3. Error Detail Viewer (Step 2.5)
**Priority**: Low
**Complexity**: Medium (~1.5 hours)
**Status**: Deferred (basic error viewer exists)

**Description**:
Modal popup for viewing full error details:
- Full-screen error display
- Complete error message (not truncated)
- Stack trace if available
- Project details and backend info
- Options to retry or skip from viewer
- Accessible via `[E]` key

**Current State**:
- `[E]` opens a paginated error viewer (newest first) with next/prev navigation.
- Error panel shows last 3 errors (truncated to 60 chars).
- Full errors in session export (JSON/Markdown) and `logs/dashboard_session.log`.
- Session manager tracks all errors.

**Gaps**:
- Not a modal overlay; no retry/skip actions from viewer; no stack traces; truncation still present in panel.

**Implementation Notes**:
- Similar modal pattern to log viewer
- ESC to close
- Navigate between multiple errors
- See `DASHBOARD_IMPLEMENTATION_ROADMAP.md` Step 2.5 for details

---

### 4. Extended Testing & Performance Tuning (Step 3.10)
**Priority**: Low
**Complexity**: Medium (~1 hour)
**Status**: Partially Complete

**Description**:
Comprehensive testing and optimization:
- Extended load testing (8+ hour sessions)
- Memory leak detection
- Performance profiling under heavy load
- Edge case testing
- Stress testing with large queues (50+ projects)

**Current Status**:
- Basic functionality tested and verified
- No known bugs or performance issues
- 4Hz refresh rate maintained
- Thread safety verified

**Implementation Notes**:
- Run long sessions and monitor memory
- Test with various terminal sizes
- Verify session persistence across restarts
- Profile cost visualization rendering
- See `DASHBOARD_IMPLEMENTATION_ROADMAP.md` Step 3.10 for details

---

## Documentation Improvements (Sprint 4)

### 5. Update CLAUDE.md (Step 4.1)
**Priority**: Low
**Complexity**: Low (~20 minutes)
**Status**: Deferred

**Tasks**:
- Add all new keyboard commands with descriptions
- Document dashboard configuration options
- Add examples of new features (export, pause/resume)
- Link to dashboard guide

---

### 6. Create Dashboard User Guide (Step 4.2)
**Priority**: Low
**Complexity**: Low (~45 minutes)
**Status**: Deferred

**Tasks**:
- Create `docs/DASHBOARD_GUIDE.md`
- Document all keyboard commands with examples
- Explain configuration options
- Describe export formats and use cases
- Cost visualization interpretation guide
- Troubleshooting section
- Screenshots or ASCII art examples

---

### 7. Inline Code Documentation (Step 4.3)
**Priority**: Low
**Complexity**: Low (~25 minutes)
**Status**: Mostly Complete

**Tasks**:
- Review all functions for docstrings
- Add type hints where missing
- Add comments for complex logic
- Document any remaining edge cases

**Current Status**:
- Most functions have comprehensive docstrings
- Type hints on critical functions
- Complex sections commented

---

## Implementation Priority

If implementing enhancements, recommended order:

1. **Documentation** (Sprint 4) - Easiest wins
   - Step 4.1: Update CLAUDE.md
   - Step 4.2: Create user guide
   - Step 4.3: Inline docs
   - **Total**: ~1.5 hours

2. **Log Viewer UI** (Step 3.2) - High utility
   - Very useful for debugging
   - Nice UX improvement
   - **Time**: ~2 hours

3. **Queue Selection** (Step 3.7) - Workflow improvement
   - More intuitive operations
   - Better control over queue
   - **Time**: ~2 hours

4. **Error Viewer** (Step 2.5) - Low priority
   - Current error visibility adequate
   - Only if detailed debugging needed often
   - **Time**: ~1.5 hours

5. **Extended Testing** (Step 3.10) - Ongoing
   - Test naturally during usage
   - Profile if performance issues arise
   - **Time**: ~1 hour

---

## Current Feature Completeness

**Dashboard Status**: 87% complete (26/30 steps)

### Fully Implemented ✅
- Session tracking and persistence
- Cost visualization and tracking
- Queue management (clear, retry, skip)
- Progress indicators (0-100%)
- Error monitoring and display
- Pause/Resume/Skip/Retry controls
- Session export (JSON/CSV/Markdown)
- Enhanced logging with persistence
- Visual status indicators and color-coding
- Responsive layout (3 modes)
- Restart with state preservation

### Optional/Deferred ⏸
- Interactive log viewer
- Queue selection with arrow keys
- Modal error detail viewer
- Extended load testing
- User documentation

---

## How to Implement

All deferred features have detailed specifications in:
- `DASHBOARD_IMPLEMENTATION_ROADMAP.md` - Step-by-step instructions
- `DASHBOARD_ENHANCEMENT_PLAN.md` - Original design specs
- Sprint completion reports - Implementation patterns

Each step includes:
- Detailed task breakdown
- Code examples/templates
- Integration points
- Edge cases to handle
- Testing requirements

---

## Notes

- **Dashboard is production-ready** - These are all optional
- **No bugs or issues** - Current implementation is stable
- **Good performance** - 4Hz refresh rate maintained
- **Test as you go** - Use dashboard naturally to identify real needs
- **Prioritize by pain points** - Only add features if you miss them

---

Last Updated: 2025-12-01
Project Status: Production Ready
