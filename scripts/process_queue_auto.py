#!/usr/bin/env python3
"""
Automated queue processor
Runs agents on all queued projects using configured LLM backend
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from llm_backend import LLMBackend

PROJECT_ROOT = Path(__file__).parent.parent
QUEUE_FILE = PROJECT_ROOT / ".processing-requests.json"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
TRANSCRIPTS_DIR = PROJECT_ROOT / "transcripts"
OUTPUT_DIR = PROJECT_ROOT / "OUTPUT"
LOG_DIR = PROJECT_ROOT / "logs"

# Locks to prevent concurrent writes clobbering data
QUEUE_LOCK = Lock()
MANIFEST_LOCK = Lock()

# Optional per-agent backend preferences; falls back to llm-config auto_select order
BACKEND_PREFERENCES = {
    "analyst": [],
    "formatter": []
}


def load_queue():
    """Load processing queue"""
    if not QUEUE_FILE.exists():
        return []
    with open(QUEUE_FILE) as f:
        return json.load(f)


def save_queue(queue):
    """Persist queue atomically"""
    tmp_path = QUEUE_FILE.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        json.dump(queue, f, indent=2)
    tmp_path.replace(QUEUE_FILE)


def update_queue_item(project_name: str, updates: dict):
    """Apply updates to a queue entry"""
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
        else:
            print(f"    ⚠ Project not found in queue: {project_name}")


def load_agent_prompt(agent_name: str) -> str:
    """Load agent markdown file"""
    agent_file = AGENTS_DIR / f"{agent_name}.md"
    if not agent_file.exists():
        raise FileNotFoundError(f"Agent file not found: {agent_file}")

    with open(agent_file) as f:
        return f.read()


def load_transcript(project_name: str) -> str:
    """Load transcript content"""
    # Try transcripts directory first
    transcript_path = TRANSCRIPTS_DIR / f"{project_name}_ForClaude.txt"

    if not transcript_path.exists():
        # Try archive
        transcript_path = TRANSCRIPTS_DIR / "archive" / f"{project_name}_ForClaude.txt"

    if not transcript_path.exists():
        raise FileNotFoundError(f"Transcript not found for {project_name}")

    with open(transcript_path, encoding='utf-8') as f:
        try:
            return f.read()
        except UnicodeDecodeError:
            # If UTF-8 fails, try a more lenient encoding like latin-1
            print(f"    ⚠ UnicodeDecodeError with UTF-8 for {transcript_path}, trying latin-1.")
            with open(transcript_path, encoding='latin-1') as f_latin1:
                return f_latin1.read()


def update_manifest(project_name: str, deliverable_type: str, filename: str, agent: str):
    """Update project manifest with new deliverable"""
    manifest_path = OUTPUT_DIR / project_name / "manifest.json"

    if not manifest_path.exists():
        print(f"    ⚠ Manifest not found: {manifest_path}")
        return

    with MANIFEST_LOCK:
        with open(manifest_path) as f:
            manifest = json.load(f)

        # Update deliverables
        if "deliverables" not in manifest:
            manifest["deliverables"] = {}

        manifest["deliverables"][deliverable_type] = {
            "file": filename,
            "created": datetime.utcnow().isoformat() + "Z",
            "agent": agent
        }

        # Update status
        has_brainstorming = "brainstorming" in manifest.get("deliverables", {})
        has_formatted = "formatted_transcript" in manifest.get("deliverables", {})

        if has_brainstorming and has_formatted:
            manifest["status"] = "ready_for_editing"
            manifest["processing_completed"] = datetime.utcnow().isoformat() + "Z"

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


def ensure_log_dir(project_name: str) -> Path:
    """Ensure log directory exists and return project log path"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    project_dir = OUTPUT_DIR / project_name
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir / "processing.log.jsonl"


def log_event(project_name: str, event: str, status: str, details: dict | None = None):
    """Append structured event for monitoring/streaming"""
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


def run_with_fallback(agent_key: str, prompt: str, system: str, llm: LLMBackend) -> tuple[str, str]:
    """Try multiple backends in order; auto-upgrade on failure"""
    errors = []
    for backend_name in get_backend_sequence(agent_key, llm):
        try:
            if backend_name and not llm.is_available(backend_name):
                errors.append(f"{backend_name}: unavailable")
                continue
            response, used_backend = llm.generate(prompt, system, backend_name)
            return response, used_backend
        except Exception as e:
            errors.append(f"{backend_name or 'auto'}: {e}")
            continue
    raise Exception(f"All backends failed for {agent_key}: {' | '.join(errors)}")


def run_analyst_agent(project_name: str, transcript: str, llm: LLMBackend, verbose: bool = True) -> str:
    """Run transcript-analyst and save brainstorming"""
    if verbose:
        print("\n→ Running transcript-analyst agent...")
    log_event(project_name, "transcript-analyst", "started")

    analyst_prompt_template = load_agent_prompt("transcript-analyst")
    analyst_system = "You are a professional video content analyst generating SEO metadata for PBS Wisconsin video content. Follow the template and guidelines exactly."
    analyst_user = f"{analyst_prompt_template}\n\n# TRANSCRIPT TO ANALYZE\n\n{transcript}"

    brainstorming, backend_used = run_with_fallback("analyst", analyst_user, analyst_system, llm)

    output_dir = OUTPUT_DIR / project_name
    brainstorming_path = output_dir / "brainstorming.md"
    with open(brainstorming_path, "w") as f:
        f.write(brainstorming)

    if verbose:
        print(f"  ✓ Saved: brainstorming.md ({len(brainstorming)} chars) via {backend_used}")

    log_event(project_name, "transcript-analyst", "completed", {"backend": backend_used})
    return "brainstorming.md"


def run_formatter_agent(project_name: str, transcript: str, llm: LLMBackend, verbose: bool = True) -> tuple[str, str | None]:
    """Run formatter and save formatted transcript (+ timestamps if present)"""
    if verbose:
        print("\n→ Running formatter agent...")
    log_event(project_name, "formatter", "started")

    formatter_prompt_template = load_agent_prompt("formatter")
    formatter_system = "You are a professional transcript formatter applying AP Style guidelines for PBS Wisconsin content."
    formatter_user = f"{formatter_prompt_template}\n\n# TRANSCRIPT TO FORMAT\n\n{transcript}"

    formatter_output, backend_used = run_with_fallback("formatter", formatter_user, formatter_system, llm)
    formatted_transcript, timestamp_report = extract_formatted_transcript_and_timestamps(formatter_output)

    output_dir = OUTPUT_DIR / project_name
    formatted_path = output_dir / "formatted_transcript.md"
    with open(formatted_path, "w") as f:
        f.write(formatted_transcript)

    if verbose:
        print(f"  ✓ Saved: formatted_transcript.md ({len(formatted_transcript)} chars) via {backend_used}")

    timestamp_filename = None
    if timestamp_report:
        timestamp_path = output_dir / "timestamp_report.md"
        with open(timestamp_path, "w") as f:
            f.write(timestamp_report)
        timestamp_filename = "timestamp_report.md"
        if verbose:
            print(f"  ✓ Saved: timestamp_report.md ({len(timestamp_report)} chars)")

    log_event(
        project_name,
        "formatter",
        "completed",
        {"backend": backend_used, "timestamps_created": bool(timestamp_filename)}
    )
    return "formatted_transcript.md", timestamp_filename


def process_project(project_name: str, llm: LLMBackend, verbose: bool = True):
    """Process a single project with both agents"""
    if verbose:
        print(f"\n{'='*60}")
        print(f"Processing: {project_name}")
        print(f"{'='*60}")

    # Load transcript
    if verbose:
        print("\n→ Loading transcript...")
    transcript = load_transcript(project_name)
    if verbose:
        print(f"  ✓ Loaded ({len(transcript)} chars)")

    output_dir = OUTPUT_DIR / project_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run agents concurrently
    with ThreadPoolExecutor(max_workers=2) as executor:
        analyst_future = executor.submit(run_analyst_agent, project_name, transcript, llm, verbose)
        formatter_future = executor.submit(run_formatter_agent, project_name, transcript, llm, verbose)

        brainstorming_filename = analyst_future.result()
        formatted_filename, timestamp_filename = formatter_future.result()

    # Update manifest after both complete to avoid write races
    update_manifest(project_name, "brainstorming", brainstorming_filename, "transcript-analyst")
    update_manifest(project_name, "formatted_transcript", formatted_filename, "formatter")
    if timestamp_filename:
        update_manifest(project_name, "timestamps", timestamp_filename, "formatter")

    if verbose:
        print(f"\n✓ {project_name} processing complete!")
    log_event(project_name, "project", "completed")

    return True


# Constants for estimation (adjust based on LLM performance)
CHARS_PER_MINUTE_PROCESSING = 2000 # Heuristic: X characters processed per minute for both agents


def get_transcript_length(project_name: str) -> int:
    """Safely get the length of the transcript content."""
    try:
        transcript = load_transcript(project_name)
        return len(transcript)
    except FileNotFoundError:
        return 0 # Indicate transcript not found or empty


def calculate_estimated_time(transcript_length: int) -> float:
    """Calculate estimated processing time in minutes based on transcript length."""
    if transcript_length == 0:
        return 0.0
    # Minimum 1 minute for any processing
    return max(1.0, round(transcript_length / CHARS_PER_MINUTE_PROCESSING, 2))


def main():
    """Main automation loop"""
    print("="*60)
    print("AUTOMATED QUEUE PROCESSOR")
    print("="*60)

    # Initialize LLM backend
    try:
        llm = LLMBackend()
    except Exception as e:
        print(f"\n✗ Error initializing LLM backend: {e}")
        print("\nCheck that config/llm-config.json exists and is valid.")
        return 1

    # Load queue
    queue = load_queue()

    if not queue:
        print("\n✓ Queue is empty - nothing to process")
        return 0

    # Calculate and store estimates for pending jobs if not already present
    queue_updated_with_estimates = False
    for i, item in enumerate(queue):
        if item.get("status") == "pending" and "estimated_processing_minutes" not in item:
            transcript_len = get_transcript_length(item['project'])
            queue[i]["transcript_length_chars"] = transcript_len
            queue[i]["estimated_processing_minutes"] = calculate_estimated_time(transcript_len)
            queue_updated_with_estimates = True
    if queue_updated_with_estimates:
        save_queue(queue)
        print("\n✓ Updated queue with processing time estimates.")


    print(f"\nFound {len(queue)} project(s) in queue:")
    for item in queue:
        status_info = f"status: {item.get('status', 'pending')}"
        estimate_info = ""
        if item.get('estimated_processing_minutes'):
            estimate_info = f", est: {item['estimated_processing_minutes']} min"
        print(f"  • {item['project']} ({status_info}{estimate_info})")

    print("\n" + "="*60)
    print("Starting processing...")
    print("="*60)

    # Process each project
    successful = 0
    failed = 0

    for item in queue:
        project_name = item["project"]

        if item.get("status") == "completed":
            print(f"\n→ Skipping {project_name} (already completed)")
            continue

        start_time = datetime.utcnow().isoformat() + "Z"
        update_queue_item(project_name, {"status": "processing", "started_at": start_time, "error": None})

        try:
            process_project(project_name, llm)
            update_queue_item(project_name, {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat() + "Z"
            })
            successful += 1
        except Exception as e:
            print(f"\n✗ Error processing {project_name}: {e}")
            update_queue_item(project_name, {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat() + "Z"
            })
            log_event(project_name, "project", "failed", {"error": str(e)})
            failed += 1

    # Summary
    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)
    print(f"\n✓ Successful: {successful}")
    if failed > 0:
        print(f"✗ Failed: {failed}")

    print("\nNext step: Run ./scripts/finalize-queue.sh to archive transcripts")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
