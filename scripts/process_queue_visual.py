#!/usr/bin/env python3
"""
Automated queue processor (Visual)
Runs agents on all queued projects using configured LLM backend, with a rich UI.
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Thread

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from llm_backend import LLMBackend

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

# Locks
QUEUE_LOCK = Lock()
MANIFEST_LOCK = Lock()

# --- DASHBOARD STATE ---
class DashboardState:
    def __init__(self):
        self.active_project = "Waiting..."
        self.current_step = "Initializing..."
        self.backend_in_use = "openai-mini"
        self.start_time = time.time()
        self.logs = []
        self.queue_data = []
        self.lock = Lock()

    def set_active(self, project, step, backend=None):
        with self.lock:
            self.active_project = project
            self.current_step = step
            if backend:
                self.backend_in_use = backend
            self.logs.insert(0, f"[{datetime.now().strftime('%H:%M:%S')}] {project}: {step}")
            if len(self.logs) > 8:
                self.logs.pop()

    def log(self, message):
        with self.lock:
            self.logs.insert(0, f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
            if len(self.logs) > 8:
                self.logs.pop()

    def update_queue(self, queue):
        with self.lock:
            self.queue_data = queue

state = DashboardState()

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

def run_with_fallback(agent_key: str, prompt: str, system: str, llm: LLMBackend) -> tuple[str, str]:
    errors = []
    for backend_name in get_backend_sequence(agent_key, llm):
        try:
            if backend_name and not llm.is_available(backend_name):
                errors.append(f"{backend_name}: unavailable")
                continue
            
            state.set_active(state.active_project, f"Running {agent_key}", backend_name)
            response, used_backend = llm.generate(prompt, system, backend_name)
            return response, used_backend
        except Exception as e:
            state.log(f"Retry: {backend_name} failed for {agent_key}")
            errors.append(f"{backend_name or 'auto'}: {e}")
            continue
    raise Exception(f"All backends failed: {' | '.join(errors)}")

def run_analyst_agent(project_name: str, transcript: str, llm: LLMBackend) -> str:
    log_event(project_name, "transcript-analyst", "started")
    analyst_prompt_template = load_agent_prompt("transcript-analyst")
    analyst_system = "You are a professional video content analyst generating SEO metadata for PBS Wisconsin video content."
    analyst_user = f"{analyst_prompt_template}\n\n# TRANSCRIPT TO ANALYZE\n\n{transcript}"
    
    brainstorming, backend_used = run_with_fallback("analyst", analyst_user, analyst_system, llm)
    
    output_dir = OUTPUT_DIR / project_name
    with open(output_dir / "brainstorming.md", "w") as f:
        f.write(brainstorming)
    
    state.log(f"✓ Analyst complete ({len(brainstorming)} chars)")
    log_event(project_name, "transcript-analyst", "completed", {"backend": backend_used})
    return "brainstorming.md"

def run_formatter_agent(project_name: str, transcript: str, llm: LLMBackend) -> tuple[str, str | None]:
    log_event(project_name, "formatter", "started")
    formatter_prompt_template = load_agent_prompt("formatter")
    formatter_system = "You are a professional transcript formatter applying AP Style guidelines."
    formatter_user = f"{formatter_prompt_template}\n\n# TRANSCRIPT TO FORMAT\n\n{transcript}"
    
    formatter_output, backend_used = run_with_fallback("formatter", formatter_user, formatter_system, llm)
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
    state.set_active(project_name, f"Processing ({len(transcript)} chars)...")
    
    output_dir = OUTPUT_DIR / project_name
    output_dir.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=2) as executor:
        analyst_future = executor.submit(run_analyst_agent, project_name, transcript, llm)
        formatter_future = executor.submit(run_formatter_agent, project_name, transcript, llm)
        
        brainstorming_filename = analyst_future.result()
        formatted_filename, timestamp_filename = formatter_future.result()

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

def make_active_panel():
    table = Table(box=None, expand=True, show_header=False)
    table.add_column("Label", style="cyan bold", width=12)
    table.add_column("Value", style="white")
    
    program = get_program_name(state.active_project) if state.active_project != "IDLE" else "-"

    table.add_row("PROJECT", state.active_project)
    table.add_row("PROGRAM", f"[magenta]{program}[/]")
    table.add_row("STATUS", state.current_step)
    table.add_row("BACKEND", Text(state.backend_in_use, style="green"))
    
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
    table.add_column("Est.", justify="right", style="yellow")
    table.add_column("Started", justify="right", style="blue")

    with state.lock:
        data = list(state.queue_data) # copy

    for item in data:
        status = item.get('status', 'pending')
        project_name = item['project']
        program_name = get_program_name(project_name)
        
        # Combined project + program cell
        project_cell = f"[bold]{project_name}[/]\n[dim magenta]{program_name}[/]