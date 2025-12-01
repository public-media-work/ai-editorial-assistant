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
        self.queue_data = []
        self.lock = Lock()
        self.session_manager = session_manager

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

    def log(self, message):
        with self.lock:
            self.logs.insert(0, f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
            if len(self.logs) > 8:
                self.logs.pop()

    def update_queue(self, queue):
        with self.lock:
            self.queue_data = queue

# Global state will be initialized in main() after SessionManager is created
state = None

# --- CORE LOGIC (Adapted) ---

BACKEND_PREFERENCES = {
    "analyst": [],
    "formatter": []
}

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
    state.log(f"💡 Learned new prefix: {prefix} = {program_name}")

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
            state.log(f"Cleared {initial_len - len(new_queue)} completed projects")
        else:
            state.log("No completed projects to clear")

def check_for_new_projects():
    """Run the check-missed-transcripts.sh script"""
    state.log("Checking for new transcripts...")
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
                state.log(f"Found and queued {count} new project(s)!")
                # Reload queue immediately
                state.update_queue(load_queue())
            elif "All transcripts accounted for" in result.stdout:
                state.log("No new projects found.")
            else:
                state.log("Check complete (no changes).")
        else:
            state.log(f"Check script failed: {result.stderr[:50]}...")
            
    except Exception as e:
        state.log(f"Error running check: {e}")

def load_agent_prompt(agent_name: str) -> str:
    agent_file = AGENTS_DIR / f"{agent_name}.md"
    if not agent_file.exists():
        raise FileNotFoundError(f"Agent file not found: {agent_file}")
    with open(agent_file) as f:
        return f.read()

def load_transcript(project_name: str) -> str:
    transcript_path = TRANSCRIPTS_DIR / f"{project_name}_ForClaude.txt"
    if not transcript_path.exists():
        transcript_path = TRANSCRIPTS_DIR / "archive" / f"{project_name}_ForClaude.txt"
    if not transcript_path.exists():
        raise FileNotFoundError(f"Transcript not found for {project_name}")
    
    with open(transcript_path, encoding='utf-8') as f:
        try:
            return f.read()
        except UnicodeDecodeError:
            state.log(f"⚠ Encoding retry (latin-1) for {project_name}")
            with open(transcript_path, encoding='latin-1') as f_latin1:
                return f_latin1.read()

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
            state.log(f"Retry: {backend_name} failed for {agent_key}")

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
    log_event(project_name, "transcript-analyst", "started")
    analyst_prompt_template = load_agent_prompt("transcript-analyst")
    analyst_system = "You are a professional video content analyst. Generate the brainstorming document in Markdown format exactly as specified. Do NOT output JSON. Do NOT wrap output in code blocks."
    analyst_user = f"{analyst_prompt_template}\n\n# TRANSCRIPT TO ANALYZE\n\n{transcript}"
    
    brainstorming, backend_used, cost = run_with_fallback("analyst", analyst_user, analyst_system, llm)
    state.add_cost(cost)
    
    output_dir = OUTPUT_DIR / project_name
    with open(output_dir / "brainstorming.md", "w") as f:
        f.write(brainstorming)
    
    state.log(f"✓ Analyst complete ({len(brainstorming)} chars)")
    log_event(project_name, "transcript-analyst", "completed", {"backend": backend_used})
    return "brainstorming.md"

def run_formatter_agent(project_name: str, transcript: str, llm: LLMBackend) -> tuple[str, str | None]:
    log_event(project_name, "formatter", "started")
    formatter_prompt_template = load_agent_prompt("formatter")
    formatter_system = "You are a professional transcript formatter applying AP Style guidelines. Output raw Markdown only. Do NOT use code blocks (```). Do NOT add conversational text."
    formatter_user = f"{formatter_prompt_template}\n\n# TRANSCRIPT TO FORMAT\n\n{transcript}"
    
    formatter_output, backend_used, cost = run_with_fallback("formatter", formatter_user, formatter_system, llm)
    state.add_cost(cost)
    formatted_transcript, timestamp_report = extract_formatted_transcript_and_timestamps(formatter_output)
    
    output_dir = OUTPUT_DIR / project_name
    with open(output_dir / "formatted_transcript.md", "w") as f:
        f.write(formatted_transcript)
    
    timestamp_filename = None
    if timestamp_report:
        with open(output_dir / "timestamp_report.md", "w") as f:
            f.write(timestamp_report)
        timestamp_filename = "timestamp_report.md"
    
    state.log(f"✓ Formatter complete ({len(formatted_transcript)} chars)")
    log_event(project_name, "formatter", "completed", {"backend": backend_used, "timestamps_created": bool(timestamp_filename)})
    return "formatted_transcript.md", timestamp_filename

def process_project(project_name: str, llm: LLMBackend):
    state.set_active(project_name, "Loading transcript...")
    transcript = load_transcript(project_name)
    
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
            state.log(f"⚠ Failed to learn prefix: {e}")

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
    """New panel showing available keyboard commands"""
    text = Text()
    text.append("Commands: ", style="dim")
    text.append("[N]", style="bold yellow")
    text.append(" Check New  ", style="white")
    text.append("[C]", style="bold yellow")
    text.append(" Clear Completed  ", style="white")
    text.append("[D]", style="bold cyan")
    text.append(" Restart Dashboard  ", style="white")
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
    
    log_text = "\n".join(state.logs)
    
    return Panel(
        table, 
        title="[bold cyan]ACTIVE PROCESSING[/]", 
        border_style="cyan",
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

        status_style = "white"
        if status == "processing": status_style = "bold cyan"
        elif status == "completed": status_style = "green"
        elif status == "failed": status_style = "red"

        # Cost
        cost = item.get('cost')
        if cost is not None:
            cost_str = f"${cost:.2f}"
            cost_style = "bold green"
        else:
            est_cost = item.get('estimated_cost', 0.0)
            cost_str = f"~${est_cost:.2f}"
            cost_style = "dim white"

        est = f"{item.get('estimated_processing_minutes', '?')}m"
        start = item.get('started_at', '')
        if start:
            start = start[11:19] # Extract HH:MM:SS from ISO

        # Add spinner for processing
        status_txt = Text(status.upper(), style=status_style)
        if status == "processing":
            status_txt = Text("⚡ PROCESSING", style="bold cyan blink")

        table.add_row(
            project_cell,
            status_txt,
            Text(cost_str, style=cost_style),
            est,
            start
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
    if term_height >= 30:
        # Full layout with statistics panel
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="statistics", size=12),  # Stats panel gets fixed height
            Layout(name="footer", size=3)
        )
    else:
        # Compact layout without statistics panel (small terminal)
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
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

    layout["footer"].update(make_controls_panel())

    return layout

# --- INPUT HANDLING ---

def is_data():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

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
                    t_len = len(load_transcript(item['project']))
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
                    c = sys.stdin.read(1).lower()
                    if c == 'q':
                        break
                    elif c == 'c':
                        clear_completed_projects()
                    elif c == 'n':
                        check_for_new_projects()
                    elif c == 'd':
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

                # Re-load queue to capture any changes (external or internal)
                queue = load_queue()
                state.update_queue(queue)
                
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
                    process_project(project_name, llm)
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
                    state.log(f"[red]Error: {e}[/]")

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
