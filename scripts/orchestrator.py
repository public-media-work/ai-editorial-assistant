#!/usr/bin/env python3
"""
Database-backed orchestrator for editorial processing queue
Polls SQLite for pending jobs, processes them, and updates status
"""

import json
import sys
import time
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from llm_backend import LLMBackend

PROJECT_ROOT = Path(__file__).parent.parent
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
TRANSCRIPTS_DIR = PROJECT_ROOT / "transcripts"
OUTPUT_DIR = PROJECT_ROOT / "OUTPUT"

DATABASE_FILE = PROJECT_ROOT / "dashboard.db"
SCHEMA_FILE = PROJECT_ROOT / "config" / "dashboard_schema.sql"

# Locks to prevent concurrent writes clobbering data (might not be needed with proper DB transactions)
MANIFEST_LOCK = Lock()

def get_db_connection():
    """Establishes a connection to the SQLite database.

    IMPORTANT: SQLite connections are not thread-safe. Each thread must have its own connection.
    """
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def initialize_database(conn):
    """Initializes the database schema from the SQL file if not already done."""
    with open(SCHEMA_FILE, 'r') as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    print(f"  ✓ Database schema initialized from {SCHEMA_FILE}")

def get_system_status(conn):
    """Retrieves the global system status (e.g., RUNNING, PAUSED).
    For now, this is a placeholder. Will be implemented later in Phase 2.
    """
    # Placeholder: assume running for now
    # TODO Phase 2: Implement actual system_status table or setting
    return "RUNNING"

def log_session_event(conn, job_id: int | None, event_type: str, details: dict | None = None):
    """Log an event to the session_stats table."""
    cursor = conn.cursor()
    details_json = json.dumps(details) if details else None
    cursor.execute(
        """
        INSERT INTO session_stats (job_id, event_type, data)
        VALUES (?, ?, ?)
        """,
        (job_id, event_type, details_json)
    )
    conn.commit()

def get_next_job(conn):
    """Fetches the highest priority pending job from the database."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM jobs
        WHERE status = 'pending'
        ORDER BY priority DESC, id ASC
        LIMIT 1
        """
    )
    return cursor.fetchone()

def update_job_status(conn, job_id: int, status: str, updates: dict | None = None):
    """Updates the status and other fields of a job in the database."""
    cursor = conn.cursor()
    set_clauses = ["status = ?"]
    params = [status]

    if updates:
        for key, value in updates.items():
            if value is not None:
                set_clauses.append(f"{key} = ?")
                params.append(value)

    query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id = ?"
    params.append(job_id)

    cursor.execute(query, tuple(params))
    conn.commit()

# --- Functions copied from process_queue_auto.py (with minimal adaptations) ---
def prefixed(project_name: str, basename: str) -> str:
    """Return deliverable filename prefixed with project id."""
    return f"{project_name}_{basename}"

CODE_FENCE_PATTERN = re.compile(r"```[a-zA-Z0-9_+-]*\s*\n(.*?)\n```", re.DOTALL)

def strip_code_fences(content: str) -> str:
    """Remove triple-backtick code fences while preserving inner content."""
    cleaned = CODE_FENCE_PATTERN.sub(r"\1\n", content)
    # Strip any stray standalone fences
    cleaned = cleaned.replace("```", "")
    return cleaned.strip() + "\n"


def utc_now_iso(timespec: str | None = None) -> str:
    """Timezone-aware UTC timestamp with trailing Z."""
    now = datetime.now(timezone.utc)
    iso = now.isoformat(timespec=timespec) if timespec else now.isoformat()
    return iso.replace("+00:00", "Z")


def estimate_transcript_minutes(transcript: str) -> float:
    """Roughly estimate transcript duration to guide model selection."""
    words = len(transcript.split())
    if words == 0:
        return 0.0
    return words / WORDS_PER_MINUTE

# Optional per-agent backend preferences; falls back to llm-config auto_select order
# Defaults favor OpenRouter with Gemini (use dev credits first), upgrading to Pro for longer jobs
BACKEND_PREFERENCES = {
    "analyst": ["openrouter"],
    "formatter": ["openrouter"]
}

# Transcript length threshold for auto-upgrading formatter to gpt-4o (in characters)
FORMATTER_LARGE_TRANSCRIPT_THRESHOLD = 200000

# Transcript length threshold to favor a more capable model for timestamp accuracy
TIMESTAMP_ACCURACY_THRESHOLD = 120000

WORDS_PER_MINUTE = 170  # Speech heuristic for duration estimates
LONG_TRANSCRIPT_MINUTES = 15  # Upgrade to larger-context Gemini after this point


def load_agent_prompt(agent_name: str) -> str:
    """Load agent markdown file"""
    agent_file = AGENTS_DIR / f"{agent_name}.md"
    if not agent_file.exists():
        raise FileNotFoundError(f"Agent file not found: {agent_file}")

    with open(agent_file) as f:
        return f.read()


def _candidate_transcript_paths(project_name: str, transcript_file: str | None = None) -> list[Path]:
    candidates: list[Path] = []
    if transcript_file:
        candidates.append(TRANSCRIPTS_DIR / transcript_file)
        candidates.append(TRANSCRIPTS_DIR / "archive" / transcript_file)

    candidates.append(TRANSCRIPTS_DIR / f"{project_name}_ForClaude.txt")
    candidates.append(TRANSCRIPTS_DIR / "archive" / f"{project_name}_ForClaude.txt")
    candidates.append(TRANSCRIPTS_DIR / f"{project_name}.txt")
    candidates.append(TRANSCRIPTS_DIR / "archive" / f"{project_name}.txt")
    candidates.extend(TRANSCRIPTS_DIR.glob(f"{project_name}*.txt"))
    candidates.extend((TRANSCRIPTS_DIR / "archive").glob(f"{project_name}*.txt"))

    seen = set()
    ordered: list[Path] = []
    for path in candidates:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def load_transcript(project_name: str, transcript_file: str | None = None) -> str:
    """Load transcript content (supports legacy _ForClaude and raw filenames)."""
    for transcript_path in _candidate_transcript_paths(project_name, transcript_file):
        if transcript_path.exists():
            with open(transcript_path, encoding='utf-8') as f:
                try:
                    return f.read()
                except UnicodeDecodeError:
                    print(f"    ⚠ UnicodeDecodeError with UTF-8 for {transcript_path}, trying latin-1.")
                    with open(transcript_path, encoding='latin-1') as f_latin1:
                        return f_latin1.read()

    raise FileNotFoundError(f"Transcript not found for {project_name}")


def update_manifest(project_name: str, deliverable_type: str, filename: str, agent: str, metrics: dict | None = None):
    """Update project manifest with new deliverable and optional metrics"""
    manifest_path = OUTPUT_DIR / project_name / "manifest.json"

    # If manifest doesn't exist, create a basic one
    if not manifest_path.exists():
        manifest = {
            "project_name": project_name,
            "status": "in_progress",
            "created_at": utc_now_iso(),
            "deliverables": {}
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        with open(manifest_path) as f:
            manifest = json.load(f)

    with MANIFEST_LOCK: # Still use lock for file write, even with DB orchestration
        # Update deliverables
        if "deliverables" not in manifest:
            manifest["deliverables"] = {}

        deliverable_entry = {
            "file": filename,
            "created": utc_now_iso(),
            "agent": agent
        }

        # Add metrics if provided
        if metrics:
            deliverable_entry["metrics"] = metrics

        manifest["deliverables"][deliverable_type] = deliverable_entry

        # Update status (simplified for orchestrator context)
        has_brainstorming = "brainstorming" in manifest.get("deliverables", {})
        has_formatted = "formatted_transcript" in manifest.get("deliverables", {})

        if has_brainstorming and has_formatted:
            manifest["status"] = "ready_for_editing"
            manifest["processing_completed"] = utc_now_iso()

            # Calculate total project cost
            total_cost = 0.0
            total_tokens = 0
            for deliverable in manifest["deliverables"].values():
                # Skip null/placeholder entries
                if not isinstance(deliverable, dict):
                    continue
                if "metrics" in deliverable:
                    total_cost += deliverable["metrics"].get("estimated_cost", 0.0)
                    total_tokens += deliverable["metrics"].get("total_tokens", 0)

            manifest["processing_metrics"] = {
                "total_estimated_cost": round(total_cost, 4),
                "total_tokens": total_tokens
            }

        # Save manifest
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)


def extract_formatted_transcript_and_timestamps(output: str) -> tuple[str, str]:
    """
    Extract formatted transcript and timestamps from formatter output
    Formatter outputs both in a single response
    """
    # Look for timestamp report section
    if "# Timestamp Report" in output or "## Timestamp Report" in output:
        # Split on timestamp report header
        parts = output.split("# Timestamp Report", 1)
        if len(parts) == 1:
            parts = output.split("## Timestamp Report", 1)

        formatted_transcript = parts[0].strip()
        timestamp_report = "# Timestamp Report" + parts[1].strip() if len(parts) > 1 else ""

        return formatted_transcript, timestamp_report
    else:
        # No timestamps section, return all as formatted transcript
        return output.strip(), ""


def get_backend_sequence(agent_key: str, llm: LLMBackend) -> list[str | None]:
    """Determine backend order for a given agent"""
    prefs = BACKEND_PREFERENCES.get(agent_key) or []
    if prefs:
        return prefs
    # Fallback to auto_select preference order
    auto_select = llm.config.get("auto_select", {})
    preference_order = auto_select.get("preference_order", [])
    if preference_order:
        return preference_order
    # Last resort: let LLMBackend auto-select
    primary = llm.config.get("primary_backend")
    return [primary] if primary else [None]

def run_with_fallback(agent_key: str, prompt: str, system: str, llm: LLMBackend):
    """Try multiple backends in order; auto-upgrade on failure

    Returns:
        tuple: (response, backend_used, usage_metrics)
    """
    errors = []
    for backend_name in get_backend_sequence(agent_key, llm):
        try:
            if backend_name and not llm.is_available(backend_name):
                errors.append(f"{backend_name}: unavailable")
                continue
            response, used_backend, metrics = llm.generate(prompt, system, backend_name)
            return response, used_backend, metrics
        except Exception as e:
            errors.append(f"{backend_name or 'auto'}: {e}")
            continue
    raise Exception(f"All backends failed for {agent_key}: {' | '.join(errors)}")

def run_analyst_agent(project_name: str, transcript: str, llm: LLMBackend, job_id: int, verbose: bool = True) -> tuple[str, dict]:
    """Run transcript-analyst and save brainstorming

    Returns:
        tuple: (filename, metrics_dict)
    """
    duration_minutes = estimate_transcript_minutes(transcript)
    analyst_order = ["openrouter"]
    original_prefs = BACKEND_PREFERENCES.get("analyst", [])
    BACKEND_PREFERENCES["analyst"] = analyst_order

    # Create thread-local DB connection
    conn = get_db_connection()
    try:
        if verbose:
            print("\n→ Running transcript-analyst agent...")
            print(f"  ℹ Estimated duration: {duration_minutes:0.1f} minutes → {analyst_order[0]}")
        log_session_event(conn, job_id, "transcript-analyst_started", {"project": project_name})

        analyst_prompt_template = load_agent_prompt("transcript-analyst")
        analyst_system = "You are a professional video content analyst. Generate the brainstorming document in Markdown format exactly as specified. Do NOT output JSON. Do NOT wrap output in code blocks."
        analyst_user = f"{analyst_prompt_template}\n\n# TRANSCRIPT TO ANALYZE\n\n{transcript}"

        try:
            brainstorming_raw, backend_used, metrics = run_with_fallback("analyst", analyst_user, analyst_system, llm)
        finally:
            BACKEND_PREFERENCES["analyst"] = original_prefs or BACKEND_PREFERENCES["analyst"]
        brainstorming = strip_code_fences(brainstorming_raw)

        output_dir = OUTPUT_DIR / project_name
        output_dir.mkdir(parents=True, exist_ok=True)
        brainstorming_filename = prefixed(project_name, "brainstorming.md")
        brainstorming_path = output_dir / brainstorming_filename
        with open(brainstorming_path, "w") as f:
            f.write(brainstorming)

        if verbose:
            print(f"  ✓ Saved: {brainstorming_filename} ({len(brainstorming)} chars) via {backend_used}")
            print(f"  ✓ Cost: ${metrics.estimated_cost:.4f} ({metrics.total_tokens} tokens)")

        metrics_dict = {
            "input_tokens": metrics.input_tokens,
            "output_tokens": metrics.output_tokens,
            "total_tokens": metrics.total_tokens,
            "estimated_cost": metrics.estimated_cost,
            "model": metrics.model,
            "backend": backend_used
        }

        log_session_event(conn, job_id, "transcript-analyst_completed", {"project": project_name, "backend": backend_used, "metrics": metrics_dict})
        return brainstorming_filename, metrics_dict
    finally:
        conn.close()

def run_formatter_agent(project_name: str, transcript: str, llm: LLMBackend, job_id: int, verbose: bool = True) -> tuple[str, str | None, dict]:
    """Run formatter and save formatted transcript (+ timestamps if present)

    Returns:
        tuple: (formatted_filename, timestamp_filename, metrics_dict)
    """
    duration_minutes = estimate_transcript_minutes(transcript)
    # Create thread-local DB connection
    conn = get_db_connection()
    try:
        if verbose:
            print("\n→ Running formatter agent...")
            print(f"  ℹ Estimated duration: {duration_minutes:0.1f} minutes")
        log_session_event(conn, job_id, "formatter_started", {"project": project_name})

        # Check transcript length and dynamically adjust backend preference for large transcripts
        transcript_length = len(transcript)
        original_prefs = None
        formatter_override: list[str] | None = None

        long_context_needed = duration_minutes >= LONG_TRANSCRIPT_MINUTES or transcript_length > FORMATTER_LARGE_TRANSCRIPT_THRESHOLD

        if long_context_needed:
            # Large/long transcript - stick to OpenRouter auto (it will pick a suitable model)
            formatter_override = ["openrouter"]
            if verbose:
                print(f"  ⚠ Long transcript detected ({transcript_length:,} chars, ~{duration_minutes:0.1f} min) - using OpenRouter auto for larger context")
            log_session_event(conn, job_id, "formatter_large_transcript_detected", {"project": project_name, "length": transcript_length, "duration_minutes": duration_minutes, "upgrade_to": "openrouter"})
        else:
            # Short/medium transcript - still use OpenRouter auto
            formatter_override = ["openrouter"]
            if verbose:
                print(f"  ℹ Estimated duration: {duration_minutes:0.1f} minutes → openrouter (auto)")

        if formatter_override:
            original_prefs = BACKEND_PREFERENCES.get("formatter", [])
            BACKEND_PREFERENCES["formatter"] = formatter_override

        formatter_prompt_template = load_agent_prompt("formatter")
        formatter_system = "You are a professional transcript formatter applying AP Style guidelines. Output raw Markdown only. Do NOT use code blocks (```). Do NOT add conversational text."
        formatter_user = f"{formatter_prompt_template}\n\n# TRANSCRIPT TO FORMAT\n\n{transcript}"

        try:
            formatter_output, backend_used, metrics = run_with_fallback("formatter", formatter_user, formatter_system, llm)
        finally:
            # Restore original preferences if we changed them
            if original_prefs is not None:
                BACKEND_PREFERENCES["formatter"] = original_prefs
        formatted_transcript_raw, timestamp_report_raw = extract_formatted_transcript_and_timestamps(formatter_output)
        formatted_transcript = strip_code_fences(formatted_transcript_raw)
        timestamp_report = strip_code_fences(timestamp_report_raw) if timestamp_report_raw else None

        output_dir = OUTPUT_DIR / project_name
        output_dir.mkdir(parents=True, exist_ok=True)
        formatted_filename = prefixed(project_name, "formatted_transcript.md")
        formatted_path = output_dir / formatted_filename
        with open(formatted_path, "w") as f:
            f.write(formatted_transcript)

        if verbose:
            print(f"  ✓ Saved: {formatted_filename} ({len(formatted_transcript)} chars) via {backend_used}")
            print(f"  ✓ Cost: ${metrics.estimated_cost:.4f} ({metrics.total_tokens} tokens)")

        timestamp_filename = None
        if timestamp_report:
            timestamp_filename = prefixed(project_name, "timestamp_report.md")
            timestamp_path = output_dir / timestamp_filename
            with open(timestamp_path, "w") as f:
                f.write(timestamp_report)
            if verbose:
                print(f"  ✓ Saved: {timestamp_filename} ({len(timestamp_report)} chars)")

        metrics_dict = {
            "input_tokens": metrics.input_tokens,
            "output_tokens": metrics.output_tokens,
            "total_tokens": metrics.total_tokens,
            "estimated_cost": metrics.estimated_cost,
            "model": metrics.model,
            "backend": backend_used
        }

        log_session_event(
            conn,
            job_id,
            "formatter_completed",
            {"project": project_name, "backend": backend_used, "timestamps_created": bool(timestamp_filename), "metrics": metrics_dict}
        )
        return formatted_filename, timestamp_filename, metrics_dict
    finally:
        conn.close()

# Constants for estimation (adjust based on LLM performance)
CHARS_PER_MINUTE_PROCESSING = 2000 # Heuristic: X characters processed per minute for both agents

def get_transcript_length_for_job(job_row, transcript_file: str | None = None) -> int:
    """Safely get the length of the transcript content for a given job row."""
    project_name = job_row['project_path']
    try:
        transcript = load_transcript(project_name, transcript_file)
        return len(transcript)
    except FileNotFoundError:
        return 0 # Indicate transcript not found or empty


def process_job_from_db(job_row, llm: LLMBackend, conn, verbose: bool = True):
    """Process a single job fetched from the database."""
    job_id = job_row['id']
    project_name = job_row['project_path']
    transcript_file = job_row['transcript_file'] # Access directly as column now exists

    if verbose:
        print(f"\n{'='*60}")
        print(f"Processing Job ID: {job_id}, Project: {project_name}")
        print(f"{'='*60}")

    log_session_event(conn, job_id, "project_processing_started", {"project": project_name})
    update_job_status(conn, job_id, "in_progress", {"start_time": utc_now_iso(timespec='milliseconds')})

    try:
        # Load transcript
        if verbose:
            print("\n→ Loading transcript...")
        transcript = load_transcript(project_name, transcript_file)
        if verbose:
            print(f"  ✓ Loaded ({len(transcript)} chars)")
        log_session_event(conn, job_id, "transcript_load_completed", {"project": project_name, "length_chars": len(transcript)})

        output_dir = OUTPUT_DIR / project_name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run agents concurrently
        with ThreadPoolExecutor(max_workers=2) as executor:
            analyst_future = executor.submit(run_analyst_agent, project_name, transcript, llm, job_id, verbose)
            formatter_future = executor.submit(run_formatter_agent, project_name, transcript, llm, job_id, verbose)

            brainstorming_filename, analyst_metrics = analyst_future.result()
            formatted_filename, timestamp_filename, formatter_metrics = formatter_future.result()

        # Update manifest after both complete
        update_manifest(project_name, "brainstorming", brainstorming_filename, "transcript-analyst", analyst_metrics)
        update_manifest(project_name, "formatted_transcript", formatted_filename, "formatter", formatter_metrics)
        if timestamp_filename:
            update_manifest(project_name, "timestamps", timestamp_filename, "formatter")

        # Calculate and display total cost
        total_cost = analyst_metrics["estimated_cost"] + formatter_metrics["estimated_cost"]
        total_tokens = analyst_metrics["total_tokens"] + formatter_metrics["total_tokens"]

        if verbose:
            print(f"\n{'='*60}")
            print(f"✓ Job {job_id} ({project_name}) processing complete!")
            print(f"  Total cost: ${total_cost:.4f}")
            print(f"  Total tokens: {total_tokens}")
            print(f"{'='*60}")
        
        log_session_event(conn, job_id, "project_processing_completed", {"project": project_name, "total_cost": total_cost, "total_tokens": total_tokens})
        update_job_status(conn, job_id, "completed", {
            "end_time": utc_now_iso(timespec='milliseconds'),
            "estimated_cost": total_cost, # Update actual cost here
            "logs": "Processing successful."
        })
        return True

    except Exception as e:
        error_message = str(e)
        print(f"\n✗ Error processing Job ID: {job_id}, Project: {project_name}: {error_message}")
        log_session_event(conn, job_id, "project_processing_failed", {"project": project_name, "error": error_message})
        update_job_status(conn, job_id, "failed", {
            "end_time": utc_now_iso(timespec='milliseconds'),
            "logs": f"Error: {error_message}"
        })
        return False

def main():
    """Main orchestrator loop"""
    print("="*60)
    print("ORCHESTRATOR - DATABASE-BACKED JOB PROCESSOR")
    print("="*60)

    conn = get_db_connection()
    initialize_database(conn) # Ensure schema is up-to-date

    # Initialize LLM backend
    try:
        llm = LLMBackend()
    except Exception as e:
        print(f"\n✗ Error initializing LLM backend: {e}")
        print("\nCheck that config/llm-config.json exists and is valid.")
        conn.close()
        return 1

    try:
        while True:
            # Check system status (placeholder for actual implementation)
            if get_system_status(conn) == "PAUSED":
                print("System is paused. Waiting...")
                time.sleep(30) # Wait before checking again
                continue

            job = get_next_job(conn)

            if job:
                print(f"Found pending job: {job['project_path']} (ID: {job['id']})")
                process_job_from_db(job, llm, conn)
            else:
                print("No pending jobs found. Waiting...")
            
            time.sleep(10) # Poll every 10 seconds for new jobs

    except KeyboardInterrupt:
        print("\nOrchestrator stopped by user.")
    finally:
        conn.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
