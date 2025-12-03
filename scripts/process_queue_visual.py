#!/usr/bin/env python3
"""
Automated queue processor (Visual)
Runs agents on all queued projects using configured LLM backend, with a rich UI.
"""

import json
import sys
import re
import time
import select
import tty
import termios
import subprocess
import os
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Thread

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from llm_backend import LLMBackend
from dashboard.session_manager import SessionManager
from dashboard.ui_components import make_stats_panel

# --- RICH IMPORTS ---
try:
    from rich.console import Console
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.logging import RichHandler
    from rich.align import Align
    from rich import box
except ImportError:
    print("Error: 'rich' library not found. Please run: pip install rich")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent
QUEUE_FILE = PROJECT_ROOT / ".processing-requests.json"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
TRANSCRIPTS_DIR = PROJECT_ROOT / "transcripts"
OUTPUT_DIR = PROJECT_ROOT / "OUTPUT"
LOG_DIR = PROJECT_ROOT / "logs"
SESSION_FILE = OUTPUT_DIR / ".dashboard_session.json"
RESTART_MARKER = OUTPUT_DIR / ".dashboard_restart_marker"

# Locks
QUEUE_LOCK = Lock()
MANIFEST_LOCK = Lock()

# --- DASHBOARD STATE ---
class DashboardState:
    def __init__(self, session_manager: SessionManager):
        self.active_project = "Waiting..."
        self.current_step = "Initializing..."
        self.backend_in_use = "openai-mini"
        self.current_job_cost = 0.0
        self.current_job_start_time = None  # Track when current job started
        self.current_video_length = "-"
        self.start_time = time.time()
        self.logs = []
        self.full_logs = []  # Unlimited log buffer
        self.queue_data = []
        self.lock = Lock()
        self.session_manager = session_manager
        self.paused: bool = False
        self.pause_reason: str | None = None
        self.current_progress: int = 0  # 0-100
        self.progress_message: str = ""
        self.selected_project: str | None = None

    def set_active(self, project, step, backend=None):
        with self.lock:
            self.active_project = project
            self.current_step = step
            if backend:
                self.backend_in_use = backend
            self.logs.insert(0, f"[{datetime.now().strftime('%H:%M:%S')}] {project}: {step}")
            if len(self.logs) > 8:
                self.logs.pop()

    def add_cost(self, cost: float):
        with self.lock:
            self.current_job_cost += cost
            # Also record to session timeline
            if self.active_project != "Waiting..." and self.active_project != "IDLE":
                self.session_manager.add_cost_event(self.active_project, cost)

    def set_video_length(self, length: str):
        with self.lock:
            self.current_video_length = length

    def reset_job_stats(self):
        with self.lock:
            self.current_job_cost = 0.0
            self.current_video_length = "-"
            self.current_job_start_time = time.time()

    def log(self, message, level="INFO"):
        """
        Log a message with level (INFO, WARN, ERROR).

        Maintains both display buffer (8 lines) and full log buffer (unlimited).
        Also writes to persistent log file.
        """
        with self.lock:
            timestamp = datetime.now().strftime('%H:%M:%S')
            log_entry = f"[{timestamp}] [{level}] {message}"

            # Add to display buffer (existing behavior)
            self.logs.insert(0, log_entry)
            if len(self.logs) > 8:
                self.logs.pop()

            # Add to full log buffer
            self.full_logs.append(log_entry)

            # Write to persistent log file
            log_file = LOG_DIR / "dashboard_session.log"
            try:
                log_file.parent.mkdir(parents=True, exist_ok=True)
                with open(log_file, 'a') as f:
                    f.write(log_entry + "\n")
            except Exception:
                pass  # Don't crash if logging fails

    def update_queue(self, queue):
        with self.lock:
            self.queue_data = queue

    def toggle_pause(self, reason: str = "User requested"):
        """Toggle pause state."""
        with self.lock:
            self.paused = not self.paused
            self.pause_reason = reason if self.paused else None
            if self.paused:
                self.log(f"⏸ Paused: {reason}")
            else:
                self.log("▶ Resumed")

    def set_progress(self, percent: int, message: str = ""):
        """Update progress for current operation."""
        with self.lock:
            self.current_progress = max(0, min(100, percent))
            self.progress_message = message

# Global state will be initialized in main() after SessionManager is created
state = None

# --- CORE LOGIC (Adapted) ---

# Optional per-agent backend preferences; falls back to llm-config auto_select order
# analyst: Use cheap model for brainstorming
# formatter: Prefer Gemini Flash (1M context, fast, cheap) for formatting large transcripts
BACKEND_PREFERENCES = {
    "analyst": ["openai-mini", "gemini-flash-8b"],
    "formatter": ["gemini-flash", "openai-mini"]
}

# Transcript length threshold for auto-upgrading formatter to gpt-4o (in characters)
# Based on observed data: 60K+ token transcripts = ~240K+ characters
# Setting threshold at 200K chars to catch large transcripts before they timeout
FORMATTER_LARGE_TRANSCRIPT_THRESHOLD = 200000

# Add helper to load prefixes
PROGRAM_PREFIXES = {}

def load_prefixes():
    prefix_file = PROJECT_ROOT / "knowledge" / "Media ID Prefixes.md"
    if not prefix_file.exists():
        return

    with open(prefix_file) as f:
        lines = f.readlines()
    
    # Parse markdown table
    for line in lines:
        if "|" in line and "File Prefix" not in line and "---" not in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                name = parts[1]
                prefix = parts[2].replace("*", "") # Remove wildcard asterisk
                PROGRAM_PREFIXES[prefix] = name

def update_known_prefixes(prefix: str, program_name: str):
    """Update the knowledge base with a new program prefix"""
    if prefix in PROGRAM_PREFIXES:
        return

    # Update memory
    PROGRAM_PREFIXES[prefix] = program_name
    state.log(f"💡 Learned new prefix: {prefix} = {program_name}", "INFO")

    # Update file
    prefix_file = PROJECT_ROOT / "knowledge" / "Media ID Prefixes.md"
    if prefix_file.exists():
        with open(prefix_file, "a") as f:
            # Ensure we start on a new line
            f.write(f"\n| {program_name} | {prefix} |")

def extract_program_from_brainstorming(content: str) -> str | None:
    """Parse the Program field from brainstorming document"""
    for line in content.splitlines():
        if line.strip().startswith("**Program**:"):
            # Extract value after colon
            val = line.split(":", 1)[1].strip()
            # Clean up common artifacts
            val = val.replace("[", "").replace("]", "")
            if val.lower() not in ["unknown", "n/a", "none", "applicable", "program name", "if applicable"]:
                return val
    return None

def get_program_name(project_name):
    # Try 4 char prefix first
    prefix = project_name[:4]
    if prefix in PROGRAM_PREFIXES:
        return PROGRAM_PREFIXES[prefix]
    
    # Try 3 char (some might be shorter)
    prefix = project_name[:3]
    if prefix in PROGRAM_PREFIXES:
        return PROGRAM_PREFIXES[prefix]
        
    return "Unknown Program"

def estimate_video_duration(transcript_text: str) -> str:
    """Estimate video duration from the last timestamp in the transcript"""
    # Look for timestamp pattern: HH:MM:SS,mmm --> HH:MM:SS,mmm
    # We only need the end time of the last match
    matches = list(re.finditer(r"(\d{2}:\d{2}:\d{2}),\d{3} --> (\d{2}:\d{2}:\d{2}),\d{3}", transcript_text))
    if matches:
        last_match = matches[-1]
        return last_match.group(2) # Return end time
    return "?"

def load_queue():
    if not QUEUE_FILE.exists():
        return []
    with open(QUEUE_FILE) as f:
        return json.load(f)

def save_queue(queue):
    tmp_path = QUEUE_FILE.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        json.dump(queue, f, indent=2)
    tmp_path.replace(QUEUE_FILE)

def update_queue_item(project_name: str, updates: dict):
    with QUEUE_LOCK:
        queue = load_queue()
        updated = False
        for item in queue:
            if item.get("project") == project_name:
                item.update(updates)
                updated = True
                break
        if updated:
            save_queue(queue)
            state.update_queue(queue) # Notify UI

def clear_completed_projects():
    """Remove completed projects from the queue file"""
    with QUEUE_LOCK:
        queue = load_queue()
        initial_len = len(queue)
        # Keep only pending, processing, or failed (maybe user wants to see failed?)
        # The request was "Clear completed projects"
        new_queue = [item for item in queue if item.get("status") != "completed"]

        if len(new_queue) < initial_len:
            save_queue(new_queue)
            state.update_queue(new_queue)
            state.log(f"Cleared {initial_len - len(new_queue)} completed projects", "INFO")
        else:
            state.log("No completed projects to clear", "INFO")

def check_for_new_projects():
    """Run the check-missed-transcripts.sh script"""
    state.log("Checking for new transcripts...", "INFO")
    try:
        # Using subprocess to call the existing shell script
        # We use check-missed-transcripts.sh --process to queue them immediately
        script_path = PROJECT_ROOT / "scripts" / "check-missed-transcripts.sh"
        result = subprocess.run(
            [str(script_path), "--process"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # Check output for confirmation
            if "Queued for agent processing" in result.stdout:
                count = result.stdout.count("Queued for agent processing")
                state.log(f"Found and queued {count} new project(s)!", "INFO")
                # Reload queue immediately
                state.update_queue(load_queue())
            elif "All transcripts accounted for" in result.stdout:
                state.log("No new projects found.", "INFO")
            else:
                state.log("Check complete (no changes).", "INFO")
        else:
            state.log(f"Check script failed: {result.stderr[:50]}...", "ERROR")

    except Exception as e:
        state.log(f"Error running check: {e}", "ERROR")

def load_agent_prompt(agent_name: str) -> str:
    agent_file = AGENTS_DIR / f"{agent_name}.md"
    if not agent_file.exists():
        raise FileNotFoundError(f"Agent file not found: {agent_file}")
    with open(agent_file) as f:
        return f.read()

def _candidate_transcript_paths(project_name: str, transcript_file: str | None = None) -> list[Path]:
    """Return candidate transcript paths for a project."""
    candidates = []
    if transcript_file:
        candidates.append(TRANSCRIPTS_DIR / transcript_file)
        candidates.append(TRANSCRIPTS_DIR / "archive" / transcript_file)

    # Legacy pattern
    candidates.append(TRANSCRIPTS_DIR / f"{project_name}_ForClaude.txt")
    candidates.append(TRANSCRIPTS_DIR / "archive" / f"{project_name}_ForClaude.txt")

    # Raw transcript names (e.g., project.txt or project.<ext>.txt)
    candidates.append(TRANSCRIPTS_DIR / f"{project_name}.txt")
    candidates.append(TRANSCRIPTS_DIR / "archive" / f"{project_name}.txt")
    candidates.extend(TRANSCRIPTS_DIR.glob(f"{project_name}*.txt"))
    candidates.extend((TRANSCRIPTS_DIR / "archive").glob(f"{project_name}*.txt"))

    # Deduplicate while preserving order
    seen = set()
    ordered = []
    for path in candidates:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def load_transcript(project_name: str, transcript_file: str | None = None) -> str:
    """
    Load a transcript for the given project, supporting both legacy _ForClaude
    filenames and raw transcript filenames (e.g., project.mp4.txt).
    """
    for transcript_path in _candidate_transcript_paths(project_name, transcript_file):
        if transcript_path.exists():
            with open(transcript_path, encoding='utf-8') as f:
                try:
                    return f.read()
                except UnicodeDecodeError:
                    state.log(f"⚠ Encoding retry (latin-1) for {project_name}", "WARN")
                    with open(transcript_path, encoding='latin-1') as f_latin1:
                        return f_latin1.read()

    raise FileNotFoundError(f"Transcript not found for {project_name}")

def update_manifest(project_name: str, deliverable_type: str, filename: str, agent: str):
    manifest_path = OUTPUT_DIR / project_name / "manifest.json"
    if not manifest_path.exists():
        return
    with MANIFEST_LOCK:
        with open(manifest_path) as f:
            manifest = json.load(f)
        if "deliverables" not in manifest:
            manifest["deliverables"] = {}
        manifest["deliverables"][deliverable_type] = {
            "file": filename,
            "created": datetime.utcnow().isoformat() + "Z",
            "agent": agent
        }
        has_brainstorming = "brainstorming" in manifest.get("deliverables", {})
        has_formatted = "formatted_transcript" in manifest.get("deliverables", {})
        if has_brainstorming and has_formatted:
            manifest["status"] = "ready_for_editing"
            manifest["processing_completed"] = datetime.utcnow().isoformat() + "Z"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

def extract_formatted_transcript_and_timestamps(output: str) -> tuple[str, str | None]:
    if "# Timestamp Report" in output or "## Timestamp Report" in output:
        parts = output.split("# Timestamp Report", 1)
        if len(parts) == 1:
            parts = output.split("## Timestamp Report", 1)
        return parts[0].strip(), "# Timestamp Report" + parts[1].strip() if len(parts) > 1 else ""
    return output.strip(), ""

def ensure_log_dir(project_name: str) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    project_dir = OUTPUT_DIR / project_name
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir / "processing.log.jsonl"

def log_event(project_name: str, event: str, status: str, details: dict | None = None):
    log_path = ensure_log_dir(project_name)
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event,
        "status": status
    }
    if details:
        payload.update(details)
    with open(log_path, "a") as f:
        f.write(json.dumps(payload) + "\n")

def get_backend_sequence(agent_key: str, llm: LLMBackend) -> list[str | None]:
    prefs = BACKEND_PREFERENCES.get(agent_key) or []
    if prefs: return prefs
    auto_select = llm.config.get("auto_select", {})
    preference_order = auto_select.get("preference_order", [])
    if preference_order: return preference_order
    primary = llm.config.get("primary_backend")
    return [primary] if primary else [None]

def run_with_fallback(agent_key: str, prompt: str, system: str, llm: LLMBackend) -> tuple[str, str, float]:
    errors = []
    for backend_name in get_backend_sequence(agent_key, llm):
        try:
            if backend_name and not llm.is_available(backend_name):
                errors.append(f"{backend_name}: unavailable")
                continue

            state.set_active(state.active_project, f"Running {agent_key}", backend_name)
            response, used_backend, metrics = llm.generate(prompt, system, backend_name)
            cost = metrics.estimated_cost

            # Record backend usage in session
            state.session_manager.add_backend_usage(used_backend, calls=1, cost=cost)

            return response, used_backend, cost
        except Exception as e:
            error_msg = str(e)
            state.log(f"Retry: {backend_name} failed for {agent_key}", "WARN")

            # Record error in session
            if state.active_project != "Waiting..." and state.active_project != "IDLE":
                state.session_manager.add_error(
                    state.active_project,
                    f"{agent_key}: {error_msg[:100]}",  # Truncate long errors
                    backend_name or "auto"
                )

            errors.append(f"{backend_name or 'auto'}: {e}")
            continue
    raise Exception(f"All backends failed: {' | '.join(errors)}")

def run_analyst_agent(project_name: str, transcript: str, llm: LLMBackend) -> str:
    state.set_progress(0, "Starting analyst agent...")
    state.set_active(project_name, "Running analyst agent...", "transcript-analyst")

    state.set_progress(20, "Loading agent prompt...")
    log_event(project_name, "transcript-analyst", "started")
    analyst_prompt_template = load_agent_prompt("transcript-analyst")
    analyst_system = "You are a professional video content analyst. Generate the brainstorming document in Markdown format exactly as specified. Do NOT output JSON. Do NOT wrap output in code blocks."
    analyst_user = f"{analyst_prompt_template}\n\n# TRANSCRIPT TO ANALYZE\n\n{transcript}"

    state.set_progress(80, "Processing LLM response...")
    brainstorming, backend_used, cost = run_with_fallback("analyst", analyst_user, analyst_system, llm)
    state.add_cost(cost)

    state.set_progress(100, "Analyst complete")

    output_dir = OUTPUT_DIR / project_name
    with open(output_dir / "brainstorming.md", "w") as f:
        f.write(brainstorming)

    state.log(f"✓ Analyst complete ({len(brainstorming)} chars)", "INFO")
    log_event(project_name, "transcript-analyst", "completed", {"backend": backend_used})
    return "brainstorming.md"

def run_formatter_agent(project_name: str, transcript: str, llm: LLMBackend) -> tuple[str, str | None]:
    state.set_progress(0, "Starting formatter agent...")
    state.set_active(project_name, "Running formatter agent...", "formatter")

    state.set_progress(20, "Loading formatter prompt...")
    log_event(project_name, "formatter", "started")

    # Check transcript length and dynamically adjust backend preference for large transcripts
    transcript_length = len(transcript)
    if transcript_length > FORMATTER_LARGE_TRANSCRIPT_THRESHOLD:
        # Large transcript detected - prefer Gemini Pro (2M context) for better performance
        state.log(f"⚠ Large transcript ({transcript_length:,} chars) - upgrading to Gemini Pro (2M)", "INFO")
        log_event(project_name, "formatter", "large_transcript_detected", {"length": transcript_length, "upgrade_to": "gemini-pro"})
        # Temporarily override backend preference for this call
        original_prefs = BACKEND_PREFERENCES.get("formatter", [])
        BACKEND_PREFERENCES["formatter"] = ["gemini-pro", "gemini-flash", "openai", "openai-mini"]  # Try Gemini Pro first
    else:
        original_prefs = None

    formatter_prompt_template = load_agent_prompt("formatter")
    formatter_system = "You are a professional transcript formatter applying AP Style guidelines. Output raw Markdown only. Do NOT use code blocks (```). Do NOT add conversational text."
    formatter_user = f"{formatter_prompt_template}\n\n# TRANSCRIPT TO FORMAT\n\n{transcript}"

    state.set_progress(80, "Processing LLM response...")
    try:
        formatter_output, backend_used, cost = run_with_fallback("formatter", formatter_user, formatter_system, llm)
        state.add_cost(cost)
    finally:
        # Restore original preferences if we changed them
        if original_prefs is not None:
            BACKEND_PREFERENCES["formatter"] = original_prefs

    state.set_progress(100, "Formatter complete")
    formatted_transcript, timestamp_report = extract_formatted_transcript_and_timestamps(formatter_output)

    output_dir = OUTPUT_DIR / project_name
    with open(output_dir / "formatted_transcript.md", "w") as f:
        f.write(formatted_transcript)

    timestamp_filename = None
    if timestamp_report:
        with open(output_dir / "timestamp_report.md", "w") as f:
            f.write(timestamp_report)
        timestamp_filename = "timestamp_report.md"

    state.log(f"✓ Formatter complete ({len(formatted_transcript)} chars)", "INFO")
    log_event(project_name, "formatter", "completed", {"backend": backend_used, "timestamps_created": bool(timestamp_filename)})
    return "formatted_transcript.md", timestamp_filename

def skip_current_project(project_name: str):
    """Move project to end of queue."""
    with QUEUE_LOCK:
        queue = load_queue()
        # Find the project
        project_idx = None
        for i, item in enumerate(queue):
            if item['project'] == project_name:
                project_idx = i
                break

        if project_idx is not None:
            # Move to end
            project = queue.pop(project_idx)
            queue.append(project)
            save_queue(queue)
            state.log(f"⏭ Skipped {project_name}", "INFO")

def retry_failed_projects():
    """Reset all failed projects to pending."""
    with QUEUE_LOCK:
        queue = load_queue()
        count = 0
        for item in queue:
            if item.get('status') == 'failed':
                update_queue_item(item['project'], {
                    'status': 'pending',
                    'error': None,
                    'started_at': None,
                    'completed_at': None
                })
                count += 1
        if count > 0:
            state.log(f"🔄 Reset {count} failed project(s)", "INFO")


def requeue_project(project_name: str):
    """Reset a single project to pending and clear error metadata."""
    with QUEUE_LOCK:
        queue = load_queue()
        updated = False
        for item in queue:
            if item.get("project") == project_name:
                item.update({
                    'status': 'pending',
                    'error': None,
                    'started_at': None,
                    'completed_at': None
                })
                updated = True
                break
        if updated:
            save_queue(queue)
            state.update_queue(queue)
            state.log(f"🔄 Requeued {project_name}", "INFO")
        else:
            state.log(f"⚠ Project not found: {project_name}", "WARN")

def remove_project(project_name: str):
    """Remove project from queue entirely."""
    with QUEUE_LOCK:
        queue = load_queue()
        queue = [item for item in queue if item['project'] != project_name]
        save_queue(queue)
        state.update_queue(queue)
        state.log(f"🗑 Removed {project_name}", "INFO")


def _paginate_console(console: Console, items: list, render_item, title: str):
    """Simple pagination helper for console-based viewers."""
    if not items:
        console.print(f"[dim]No {title.lower()}[/]")
        return

    idx = 0
    total = len(items)
    while True:
        console.print(f"\n[bold]{title} ({idx + 1}/{total})[/]")
        console.print(render_item(items[idx]))
        console.print("[dim][N] next  [P] prev  [Q/Enter] exit[/]", end=" ")
        choice = input().strip().lower()
        if choice in ("q", ""):
            break
        if choice == "n" and idx < total - 1:
            idx += 1
        elif choice == "p" and idx > 0:
            idx -= 1


def show_error_viewer(console: Console):
    """Display paginated error viewer."""
    errors = state.session_manager.get_errors()

    def render(err):
        timestamp = err.get("timestamp", "")
        time_str = timestamp[11:19] if len(timestamp) >= 19 else timestamp
        backend = err.get("backend", "unknown")
        project = err.get("project", "Unknown")
        message = err.get("error", "No details")
        return f"{time_str} [{backend}] {project}\n[red]{message}[/]"

    _paginate_console(console, errors, render, "Errors")


def show_log_viewer(console: Console, count: int = 100):
    """Display paginated log viewer."""
    with state.lock:
        logs = list(state.full_logs[-count:])

    logs = list(reversed(logs))  # newest first

    def render(line):
        return line

    _paginate_console(console, logs, render, "Logs")

def process_project(project_name: str, llm: LLMBackend, transcript_file: str | None = None):
    state.set_active(project_name, "Loading transcript...")
    transcript = load_transcript(project_name, transcript_file)
    
    state.reset_job_stats()
    state.set_video_length(estimate_video_duration(transcript))
    
    state.set_active(project_name, f"Processing ({len(transcript)} chars)...")
    
    output_dir = OUTPUT_DIR / project_name
    output_dir.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=2) as executor:
        analyst_future = executor.submit(run_analyst_agent, project_name, transcript, llm)
        formatter_future = executor.submit(run_formatter_agent, project_name, transcript, llm)
        
        brainstorming_filename = analyst_future.result()
        formatted_filename, timestamp_filename = formatter_future.result()

    # Check if we can learn a new prefix
    current_program = get_program_name(project_name)
    if current_program == "Unknown Program":
        # Read the generated brainstorming file
        try:
            with open(output_dir / brainstorming_filename) as f:
                content = f.read()
            new_program = extract_program_from_brainstorming(content)
            if new_program:
                # Determine prefix (assume 4 chars or 3 chars)
                # We use the same logic as get_program_name to decide what the prefix IS
                prefix = project_name[:4]
                update_known_prefixes(prefix, new_program)
        except Exception as e:
            state.log(f"⚠ Failed to learn prefix: {e}", "WARN")

    update_manifest(project_name, "brainstorming", brainstorming_filename, "transcript-analyst")
    update_manifest(project_name, "formatted_transcript", formatted_filename, "formatter")
    if timestamp_filename:
        update_manifest(project_name, "timestamps", timestamp_filename, "formatter")
    
    log_event(project_name, "project", "completed")
    return True

# --- UI RENDERING ---

def make_header():
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="right")
    title = Text(" ✦ PBS WISCONSIN • EDITORIAL AI CORE ✦ ", style="bold magenta on black")
    time_txt = Text(datetime.now().strftime("%H:%M:%S"), style="cyan dim")
    return Panel(title, style="magenta")

def make_controls_panel():
    """Panel showing available keyboard commands"""
    text = Text()
    text.append("Commands: ", style="dim")
    text.append("[N]", style="bold yellow")
    text.append(" New  ", style="white")
    text.append("[C]", style="bold yellow")
    text.append(" Clear  ", style="white")
    text.append("[P]", style="bold yellow")
    text.append(" Pause  ", style="white")
    text.append("[S]", style="bold yellow")
    text.append(" Skip  ", style="white")
    text.append("[R]", style="bold yellow")
    text.append(" Retry  ", style="white")
    text.append("[Z]", style="bold yellow")
    text.append(" Requeue  ", style="white")
    text.append("[E]", style="bold yellow")
    text.append(" Errors  ", style="white")
    text.append("[L]", style="bold yellow")
    text.append(" Logs  ", style="white")
    text.append("[X]", style="bold yellow")
    text.append(" Remove  ", style="white")
    text.append("[T]", style="bold green")
    text.append(" Export  ", style="white")
    text.append("[D]", style="bold cyan")
    text.append(" Restart  ", style="white")
    text.append("[Q]", style="bold red")
    text.append(" Quit", style="white")

    return Panel(text, style="dim", box=box.SIMPLE)

def make_active_panel():
    table = Table(box=None, expand=True, show_header=False)
    table.add_column("Label", style="cyan bold", width=12)
    table.add_column("Value", style="white")

    program = get_program_name(state.active_project) if state.active_project != "IDLE" else "-"

    table.add_row("PROJECT", state.active_project)
    table.add_row("PROGRAM", f"[magenta]{program}[/]")
    table.add_row("STATUS", state.current_step)
    table.add_row("BACKEND", Text(state.backend_in_use, style="green"))
    table.add_row("VIDEO LEN", state.current_video_length)
    table.add_row("JOB COST", f"${state.current_job_cost:.4f}")

    # Add progress bar if progress > 0
    if state.current_progress > 0:
        # Create progress bar
        bar_width = 20
        filled = int((state.current_progress / 100) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        progress_text = Text()
        progress_text.append(bar, style="cyan")
        progress_text.append(f" {state.current_progress}%", style="white")
        table.add_row("PROGRESS", progress_text)

        if state.progress_message:
            table.add_row("", Text(state.progress_message, style="dim"))

    log_text = "\n".join(state.logs)

    # Determine title and border style based on pause state
    if state.paused:
        panel_title = "[bold yellow]⏸ PAUSED[/]"
        panel_border = "yellow"
    else:
        panel_title = "[bold cyan]ACTIVE PROCESSING[/]"
        panel_border = "cyan"

    return Panel(
        table,
        title=panel_title,
        border_style=panel_border,
        subtitle=f"[dim]{log_text.splitlines()[0] if log_text else ''}[/]")

def make_queue_table():
    table = Table(box=box.SIMPLE, expand=True)
    table.add_column("Project / Program", style="white")
    table.add_column("Status", style="dim")
    table.add_column("Cost", justify="right", style="green")
    table.add_column("Est. Time", justify="right", style="yellow")
    table.add_column("Started", justify="right", style="blue")

    with state.lock:
        data = list(state.queue_data) # copy

    for item in data:
        status = item.get('status', 'pending')
        project_name = item['project']
        program_name = get_program_name(project_name)

        # Combined project + program cell
        project_cell = f"[bold]{project_name}[/]\n[dim magenta]{program_name}[/]"

        # Enhanced status styling
        status_style = "white"
        status_icon = ""
        if status == "processing":
            status_style = "bold cyan"
            status_icon = "⚡"
        elif status == "completed":
            status_style = "green"
            status_icon = "✓"
        elif status == "failed":
            status_style = "red"
            status_icon = "🔴"

        # Cost with color coding based on thresholds
        cost = item.get('cost')
        if cost is not None:
            cost_str = f"${cost:.2f}"
            # Color code: green < $0.50, yellow < $2.00, red >= $2.00
            if cost < 0.50:
                cost_style = "green"
            elif cost < 2.00:
                cost_style = "yellow"
            else:
                cost_style = "red bold"
        else:
            est_cost = item.get('estimated_cost', 0.0)
            cost_str = f"~${est_cost:.2f}"
            cost_style = "dim white"

        est = f"{item.get('estimated_processing_minutes', '?')}m"
        start = item.get('started_at', '')
        if start:
            start = start[11:19] # Extract HH:MM:SS from ISO

        # Enhanced status text with icons
        if status == "processing":
            status_txt = Text(f"{status_icon} PROCESSING", style="bold cyan blink")
        else:
            status_txt = Text(f"{status_icon} {status.upper()}", style=status_style)

        row_style = "on blue" if state.selected_project == project_name else None

        table.add_row(
            project_cell,
            status_txt,
            Text(cost_str, style=cost_style),
            est,
            start,
            style=row_style
        )
    return Panel(table, title="[bold white]QUEUE MATRIX[/]", border_style="white")

def generate_layout():
    """
    Generate the complete dashboard layout with all panels.

    Layout structure:
    - Header (3 lines)
    - Main area (flexible):
      - Left: Active project panel (ratio 1)
      - Right: Queue table (ratio 3)
    - Statistics panel (auto-sized based on content)
    - Footer: Controls (3 lines)
    """
    # Get terminal size for responsive layout
    import shutil
    term_width, term_height = shutil.get_terminal_size(fallback=(120, 30))

    layout = Layout()

    # Adjust layout based on terminal height
    if term_height >= 35:
        # Full layout with statistics and error panels
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="statistics", size=12),  # Stats panel gets fixed height
            Layout(name="footer", size=8)  # Increased for errors + controls
        )
        # Split footer into errors and controls
        layout["footer"].split(
            Layout(name="errors", size=5),
            Layout(name="controls", size=3)
        )
    elif term_height >= 30:
        # Medium layout with statistics only
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="statistics", size=12),
            Layout(name="controls", size=3)
        )
    else:
        # Compact layout (minimal)
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="controls", size=3)
        )

    # Split main area into left and right
    layout["main"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=3)
    )

    # Update all panels
    layout["header"].update(make_header())
    layout["left"].update(make_active_panel())
    layout["right"].update(make_queue_table())

    # Add statistics panel if there's enough space
    if term_height >= 30:
        layout["statistics"].update(make_stats_panel(state, state.session_manager))

    # Add error panel if there's enough space
    if term_height >= 35:
        from dashboard.ui_components import make_error_panel
        layout["errors"].update(make_error_panel(state.session_manager))
        layout["controls"].update(make_controls_panel())
    else:
        layout["controls"].update(make_controls_panel())

    return layout

# --- INPUT HANDLING ---

def is_data():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])


def move_selection(delta: int):
    """Move queue selection up/down by delta."""
    with state.lock:
        if not state.queue_data:
            state.selected_project = None
            return

        # Build ordered list of project names
        projects = [item["project"] for item in state.queue_data]
        if state.selected_project in projects:
            idx = projects.index(state.selected_project)
        else:
            idx = 0

        new_idx = max(0, min(len(projects) - 1, idx + delta))
        state.selected_project = projects[new_idx]

# --- RESTART FUNCTIONALITY ---

def restart_dashboard(state: DashboardState, console: Console):
    """
    Restart the dashboard process while preserving all state.

    This function:
    1. Saves the current session state
    2. Creates a restart marker file for recovery
    3. Restarts the process using os.execv()

    Args:
        state: Current DashboardState instance
        console: Rich Console for user feedback
    """
    console.print("[yellow]Restarting dashboard...[/]")

    # Save session state
    try:
        state.session_manager.save()
        console.print("[green]✓ Session state saved[/]")
    except Exception as e:
        console.print(f"[red]⚠ Failed to save session: {e}[/]")

    # Create restart marker
    try:
        with open(RESTART_MARKER, 'w') as f:
            json.dump({
                "restart_time": datetime.utcnow().isoformat() + "Z",
                "reason": "user_requested"
            }, f)
        console.print("[green]✓ Restart marker created[/]")
    except Exception as e:
        console.print(f"[red]⚠ Failed to create restart marker: {e}[/]")

    # Give user feedback before restart
    console.print("[cyan]Dashboard will restart in 1 second...[/]")
    time.sleep(1)

    # Restart the process
    python = sys.executable
    os.execv(python, [python] + sys.argv)

def check_restart_marker(console: Console) -> bool:
    """
    Check if dashboard was restarted and display recovery message.

    Returns:
        True if recovering from restart, False otherwise
    """
    if RESTART_MARKER.exists():
        try:
            with open(RESTART_MARKER, 'r') as f:
                marker_data = json.load(f)

            restart_time = marker_data.get('restart_time', 'unknown')
            console.print(f"[green]✓ Dashboard recovered from restart at {restart_time}[/]")

            # Remove marker file
            RESTART_MARKER.unlink()
            return True
        except Exception as e:
            console.print(f"[yellow]⚠ Error reading restart marker: {e}[/]")
            # Try to remove anyway
            try:
                RESTART_MARKER.unlink()
            except:
                pass

    return False

# --- MAIN ---

def main():
    global state  # Need to set the global state variable

    console = Console()

    # Check for restart marker
    check_restart_marker(console)

    load_prefixes() # Load the knowledge base

    # Initialize session manager
    session_manager = SessionManager(SESSION_FILE)

    # Initialize dashboard state with session manager
    state = DashboardState(session_manager)

    try:
        llm = LLMBackend()
    except Exception as e:
        console.print(f"[red]Error initializing LLM backend: {e}[/]")
        return 1

    state.update_queue(load_queue())
    
    # Update estimates
    if state.queue_data:
        updated = False
        for i, item in enumerate(state.queue_data):
            if item.get("status") == "pending" and "estimated_processing_minutes" not in item:
                # Simple Estimate logic duplicate
                try:
                    t_len = len(load_transcript(item['project'], item.get("transcript_file")))
                    est = max(1.0, round(t_len / 2000, 2))
                    est_cost = round(t_len * 0.000005, 4) # Rough estimate for Sonnet
                except:
                    est = 0
                    est_cost = 0.0
                state.queue_data[i]["estimated_processing_minutes"] = est
                state.queue_data[i]["estimated_cost"] = est_cost
                updated = True
        if updated:
            save_queue(state.queue_data)

    # Setup for input handling
    old_settings = termios.tcgetattr(sys.stdin)
    
    try:
        tty.setcbreak(sys.stdin.fileno())
        
        with Live(generate_layout(), refresh_per_second=4, screen=True) as live:
            successful = 0
            failed = 0
            
            while True:
                # Handle Input
                if is_data():
                    c = sys.stdin.read(1)
                    c_lower = c.lower()
                    if c_lower == 'q':
                        break
                    elif c_lower == 'c':
                        clear_completed_projects()
                    elif c_lower == 'n':
                        check_for_new_projects()
                    elif c_lower == 'p':
                        # Pause/Resume
                        state.toggle_pause()
                        live.update(generate_layout())
                    elif c_lower == 's':
                        # Skip selected project (fallback to active)
                        target = state.selected_project or state.active_project
                        if target and target not in ["IDLE", "PAUSED", "Waiting..."]:
                            skip_current_project(target)
                            state.log(f"⏭ Skipped {target}", "INFO")
                    elif c_lower == 'r':
                        # Retry failed projects
                        retry_failed_projects()
                    elif c_lower == 'z':
                        # Requeue selected/current project
                        target = state.selected_project or state.active_project
                        if target and target not in ["IDLE", "PAUSED", "Waiting..."]:
                            requeue_project(target)
                        else:
                            state.log("⚠ No project selected to requeue", "WARN")
                    elif c_lower == 'e':
                        # Show error viewer
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        try:
                            show_error_viewer(console)
                        finally:
                            tty.setcbreak(sys.stdin.fileno())
                    elif c_lower == 'l':
                        # Show log viewer
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        try:
                            show_log_viewer(console, count=200)
                        finally:
                            tty.setcbreak(sys.stdin.fileno())
                    elif c_lower == 'x':
                        # Remove project from queue
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        try:
                            default_target = state.selected_project or (state.active_project if state.active_project not in ["IDLE", "PAUSED", "Waiting..."] else "")
                            console.print("\n[bold red]Remove project from queue[/]")
                            if default_target:
                                console.print(f"[dim]Press Enter to remove selected/current: {default_target}[/]")
                            console.print("[cyan]Project name:[/] ", end="")
                            target = input().strip() or default_target
                            if target:
                                remove_project(target)
                            else:
                                console.print("[dim]Remove cancelled[/]")
                                time.sleep(1)
                        finally:
                            tty.setcbreak(sys.stdin.fileno())
                    elif c_lower == 't':
                        # Export session data
                        # Temporarily restore terminal settings
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        try:
                            from dashboard.exporter import SessionExporter
                            exporter = SessionExporter(state.session_manager)

                            console.print("\n[bold cyan]═══ Export Session Data ═══[/]")
                            console.print("Select format:")
                            console.print("  [1] JSON (complete data)")
                            console.print("  [2] CSV (tabular)")
                            console.print("  [3] Markdown summary")
                            console.print("  [Q] Cancel")
                            console.print("[cyan]Choice:[/] ", end="")

                            choice = input().lower().strip()

                            if choice == 'q':
                                console.print("[dim]Export cancelled[/]")
                            elif choice in ['1', '2', '3']:
                                # Default filename based on session ID
                                session_id = state.session_manager.session_data.get('session_id', 'unknown')
                                timestamp = session_id.split('T')[0] if 'T' in session_id else 'session'

                                if choice == '1':
                                    default_path = OUTPUT_DIR / "reports" / f"session_{timestamp}.json"
                                    ext = "json"
                                elif choice == '2':
                                    default_path = OUTPUT_DIR / "reports" / f"session_{timestamp}.csv"
                                    ext = "csv"
                                else:
                                    default_path = OUTPUT_DIR / "reports" / f"session_{timestamp}_summary.md"
                                    ext = "md"

                                console.print(f"[dim]Default: {default_path}[/]")
                                console.print("[cyan]File path (press Enter for default):[/] ", end="")
                                custom_path = input().strip()

                                export_path = Path(custom_path) if custom_path else default_path

                                try:
                                    if choice == '1':
                                        exporter.export_json(export_path)
                                    elif choice == '2':
                                        exporter.export_csv(export_path)
                                    else:
                                        exporter.export_summary_md(export_path)

                                    console.print(f"[green]✓ Exported to: {export_path}[/]")
                                    state.log(f"Exported session to {export_path.name}", "INFO")
                                except Exception as e:
                                    console.print(f"[red]✗ Export failed: {e}[/]")
                                    state.log(f"Export failed: {e}", "ERROR")
                            else:
                                console.print("[yellow]Invalid choice[/]")

                            time.sleep(2)
                        finally:
                            # Restore cbreak mode
                            tty.setcbreak(sys.stdin.fileno())
                    elif c_lower == 'd':
                        # Restart dashboard with confirmation
                        # Temporarily restore terminal settings for confirmation
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        try:
                            console.print("\n[yellow]Restart dashboard? This will preserve all state. (y/n):[/] ", end="")
                            confirm = input().lower().strip()
                            if confirm == 'y':
                                restart_dashboard(state, console)
                            else:
                                console.print("[dim]Restart cancelled[/]")
                                time.sleep(1)
                        finally:
                            # Restore cbreak mode
                            tty.setcbreak(sys.stdin.fileno())
                    elif c == '\x1b':
                        # Possible arrow key sequences
                        next_two = sys.stdin.read(2)
                        if next_two == "[A":  # Up
                            move_selection(-1)
                            live.update(generate_layout())
                        elif next_two == "[B":  # Down
                            move_selection(1)
                            live.update(generate_layout())

                # Re-load queue to capture any changes (external or internal)
                queue = load_queue()
                state.update_queue(queue)

                # Check if paused
                if state.paused:
                    state.set_active("PAUSED", f"⏸ {state.pause_reason}", "standby")
                    live.update(generate_layout())
                    time.sleep(0.1)
                    continue

                # Check for pending items
                pending_items = [i for i in queue if i.get("status") == "pending"]

                if not pending_items:
                    state.set_active("IDLE", "Waiting for new projects...", "standby")
                    live.update(generate_layout())
                    time.sleep(0.1) # Reduce sleep for better input responsiveness
                    continue

                # Process pending items
                # IMPORTANT: We only grab ONE item, process it, then loop back
                # This ensures we check for input/interrupts between items

                item = pending_items[0]
                project_name = item["project"]
                
                start_time = datetime.utcnow().isoformat() + "Z"
                update_queue_item(project_name, {"status": "processing", "started_at": start_time, "error": None})
                
                try:
                    process_project(project_name, llm, transcript_file=item.get("transcript_file"))
                    final_cost = state.current_job_cost

                    # Calculate duration in minutes
                    duration_minutes = 0.0
                    if state.current_job_start_time:
                        duration_minutes = (time.time() - state.current_job_start_time) / 60.0

                    # Record completion in session
                    state.session_manager.add_project_completion(
                        project_name,
                        final_cost,
                        duration_minutes,
                        "completed"
                    )

                    update_queue_item(project_name, {
                        "status": "completed",
                        "completed_at": datetime.utcnow().isoformat() + "Z",
                        "cost": final_cost
                    })
                    successful += 1
                except Exception as e:
                    error_msg = str(e)
                    state.log(f"[red]Error: {e}[/]", "ERROR")

                    # Calculate duration in minutes (even for failures)
                    duration_minutes = 0.0
                    if state.current_job_start_time:
                        duration_minutes = (time.time() - state.current_job_start_time) / 60.0

                    # Record failure in session
                    state.session_manager.add_project_completion(
                        project_name,
                        state.current_job_cost,  # Record partial cost
                        duration_minutes,
                        "failed"
                    )

                    # Also record the final error
                    state.session_manager.add_error(
                        project_name,
                        error_msg[:200],  # Truncate long errors
                        "process"
                    )

                    update_queue_item(project_name, {
                        "status": "failed",
                        "error": error_msg,
                        "completed_at": datetime.utcnow().isoformat() + "Z"
                    })
                    failed += 1
                
                live.update(generate_layout())

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    return 0

if __name__ == "__main__":
    sys.exit(main())
