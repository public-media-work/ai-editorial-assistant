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

    if not manifest_path.exists():
        print(f"    ⚠ Manifest not found: {manifest_path}")
        return

    with MANIFEST_LOCK:
        with open(manifest_path) as f:
            manifest = json.load(f)

        # Update deliverables
        if "deliverables" not in manifest:
            manifest["deliverables"] = {}

        deliverable_entry = {
            "file": filename,
            "created": datetime.utcnow().isoformat() + "Z",
            "agent": agent
        }

        # Add metrics if provided
        if metrics:
            deliverable_entry["metrics"] = metrics

        manifest["deliverables"][deliverable_type] = deliverable_entry

        # Update status
        has_brainstorming = "brainstorming" in manifest.get("deliverables", {})
        has_formatted = "formatted_transcript" in manifest.get("deliverables", {})

        if has_brainstorming and has_formatted:
            manifest["status"] = "ready_for_editing"
            manifest["processing_completed"] = datetime.utcnow().isoformat() + "Z"

            # Calculate total project cost
            total_cost = 0.0
            total_tokens = 0
            for deliverable in manifest["deliverables"].values():
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


def run_analyst_agent(project_name: str, transcript: str, llm: LLMBackend, verbose: bool = True) -> tuple[str, dict]:
    """Run transcript-analyst and save brainstorming

    Returns:
        tuple: (filename, metrics_dict)
    """
    if verbose:
        print("\n→ Running transcript-analyst agent...")
    log_event(project_name, "transcript-analyst", "started")

    analyst_prompt_template = load_agent_prompt("transcript-analyst")
    analyst_system = "You are a professional video content analyst. Generate the brainstorming document in Markdown format exactly as specified. Do NOT output JSON. Do NOT wrap output in code blocks."
    analyst_user = f"{analyst_prompt_template}\n\n# TRANSCRIPT TO ANALYZE\n\n{transcript}"

    brainstorming, backend_used, metrics = run_with_fallback("analyst", analyst_user, analyst_system, llm)

    output_dir = OUTPUT_DIR / project_name
    brainstorming_path = output_dir / "brainstorming.md"
    with open(brainstorming_path, "w") as f:
        f.write(brainstorming)

    if verbose:
        print(f"  ✓ Saved: brainstorming.md ({len(brainstorming)} chars) via {backend_used}")
        print(f"  ✓ Cost: ${metrics.estimated_cost:.4f} ({metrics.total_tokens} tokens)")

    metrics_dict = {
        "input_tokens": metrics.input_tokens,
        "output_tokens": metrics.output_tokens,
        "total_tokens": metrics.total_tokens,
        "estimated_cost": metrics.estimated_cost,
        "model": metrics.model,
        "backend": backend_used
    }

    log_event(project_name, "transcript-analyst", "completed", {"backend": backend_used, "metrics": metrics_dict})
    return "brainstorming.md", metrics_dict


def run_formatter_agent(project_name: str, transcript: str, llm: LLMBackend, verbose: bool = True) -> tuple[str, str | None, dict]:
    """Run formatter and save formatted transcript (+ timestamps if present)

    Returns:
        tuple: (formatted_filename, timestamp_filename, metrics_dict)
    """
    if verbose:
        print("\n→ Running formatter agent...")
    log_event(project_name, "formatter", "started")

    # Check transcript length and dynamically adjust backend preference for large transcripts
    transcript_length = len(transcript)
    if transcript_length > FORMATTER_LARGE_TRANSCRIPT_THRESHOLD:
        # Large transcript detected - prefer Gemini Pro (2M context) or gpt-4o for better performance
        if verbose:
            print(f"  ⚠ Large transcript detected ({transcript_length:,} chars) - upgrading to Gemini Pro (2M context)")
        log_event(project_name, "formatter", "large_transcript_detected", {"length": transcript_length, "upgrade_to": "gemini-pro"})
        # Temporarily override backend preference for this call
        original_prefs = BACKEND_PREFERENCES.get("formatter", [])
        BACKEND_PREFERENCES["formatter"] = ["gemini-pro", "gemini-flash", "openai", "openai-mini"]  # Try Gemini Pro first
    else:
        original_prefs = None

    formatter_prompt_template = load_agent_prompt("formatter")
    formatter_system = "You are a professional transcript formatter applying AP Style guidelines. Output raw Markdown only. Do NOT use code blocks (```). Do NOT add conversational text."
    formatter_user = f"{formatter_prompt_template}\n\n# TRANSCRIPT TO FORMAT\n\n{transcript}"

    try:
        formatter_output, backend_used, metrics = run_with_fallback("formatter", formatter_user, formatter_system, llm)
    finally:
        # Restore original preferences if we changed them
        if original_prefs is not None:
            BACKEND_PREFERENCES["formatter"] = original_prefs
    formatted_transcript, timestamp_report = extract_formatted_transcript_and_timestamps(formatter_output)

    output_dir = OUTPUT_DIR / project_name
    formatted_path = output_dir / "formatted_transcript.md"
    with open(formatted_path, "w") as f:
        f.write(formatted_transcript)

    if verbose:
        print(f"  ✓ Saved: formatted_transcript.md ({len(formatted_transcript)} chars) via {backend_used}")
        print(f"  ✓ Cost: ${metrics.estimated_cost:.4f} ({metrics.total_tokens} tokens)")

    timestamp_filename = None
    if timestamp_report:
        timestamp_path = output_dir / "timestamp_report.md"
        with open(timestamp_path, "w") as f:
            f.write(timestamp_report)
        timestamp_filename = "timestamp_report.md"
        if verbose:
            print(f"  ✓ Saved: timestamp_report.md ({len(timestamp_report)} chars)")

    metrics_dict = {
        "input_tokens": metrics.input_tokens,
        "output_tokens": metrics.output_tokens,
        "total_tokens": metrics.total_tokens,
        "estimated_cost": metrics.estimated_cost,
        "model": metrics.model,
        "backend": backend_used
    }

    log_event(
        project_name,
        "formatter",
        "completed",
        {"backend": backend_used, "timestamps_created": bool(timestamp_filename), "metrics": metrics_dict}
    )
    return "formatted_transcript.md", timestamp_filename, metrics_dict


def process_project(project_name: str, llm: LLMBackend, verbose: bool = True, transcript_file: str | None = None):
    """Process a single project with both agents"""
    if verbose:
        print(f"\n{'='*60}")
        print(f"Processing: {project_name}")
        print(f"{'='*60}")

    # Load transcript
    if verbose:
        print("\n→ Loading transcript...")
    transcript = load_transcript(project_name, transcript_file)
    if verbose:
        print(f"  ✓ Loaded ({len(transcript)} chars)")

    output_dir = OUTPUT_DIR / project_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run agents concurrently
    with ThreadPoolExecutor(max_workers=2) as executor:
        analyst_future = executor.submit(run_analyst_agent, project_name, transcript, llm, verbose)
        formatter_future = executor.submit(run_formatter_agent, project_name, transcript, llm, verbose)

        brainstorming_filename, analyst_metrics = analyst_future.result()
        formatted_filename, timestamp_filename, formatter_metrics = formatter_future.result()

    # Update manifest after both complete to avoid write races
    update_manifest(project_name, "brainstorming", brainstorming_filename, "transcript-analyst", analyst_metrics)
    update_manifest(project_name, "formatted_transcript", formatted_filename, "formatter", formatter_metrics)
    if timestamp_filename:
        update_manifest(project_name, "timestamps", timestamp_filename, "formatter")

    # Calculate and display total cost
    total_cost = analyst_metrics["estimated_cost"] + formatter_metrics["estimated_cost"]
    total_tokens = analyst_metrics["total_tokens"] + formatter_metrics["total_tokens"]

    if verbose:
        print(f"\n{'='*60}")
        print(f"✓ {project_name} processing complete!")
        print(f"  Total cost: ${total_cost:.4f}")
        print(f"  Total tokens: {total_tokens}")
        print(f"{'='*60}")
    log_event(project_name, "project", "completed", {"total_cost": total_cost, "total_tokens": total_tokens})

    return True


# Constants for estimation (adjust based on LLM performance)
CHARS_PER_MINUTE_PROCESSING = 2000 # Heuristic: X characters processed per minute for both agents


def get_transcript_length(project_name: str, transcript_file: str | None = None) -> int:
    """Safely get the length of the transcript content."""
    try:
        transcript = load_transcript(project_name, transcript_file)
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
            transcript_len = get_transcript_length(item['project'], item.get("transcript_file"))
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

        transcript_file = item.get("transcript_file")

        start_time = datetime.utcnow().isoformat() + "Z"
        update_queue_item(project_name, {"status": "processing", "started_at": start_time, "error": None})

        try:
            process_project(project_name, llm, transcript_file=transcript_file)
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
