#!/usr/bin/env python3
"""
Automated queue processor
Runs agents on all queued projects using configured LLM backend
"""

import json
import sys
import time
import re
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


def prefixed(project_name: str, basename: str) -> str:
    """Return deliverable filename prefixed with project id."""
    return f"{project_name}_{basename}"


def strip_code_fences(content: str) -> str:
    """Remove triple-backtick code fences while preserving inner content."""
    cleaned = CODE_FENCE_PATTERN.sub(r"\1\n", content)
    # Strip any stray standalone fences
    cleaned = cleaned.replace("```", "")
    return cleaned.strip() + "\n"


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

# Transcript length threshold to favor a more capable model for timestamp accuracy
# Captures medium/long transcripts that benefit from better alignment without waiting for the large-doc upgrade
TIMESTAMP_ACCURACY_THRESHOLD = 120000

CODE_FENCE_PATTERN = re.compile(r"```[a-zA-Z0-9_+-]*\s*\n(.*?)\n```", re.DOTALL)


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

        # Add metrics if provided (includes model, backend, costs, tokens)
        if metrics:
            deliverable_entry["metrics"] = metrics
            # Also add top-level model/backend for quick reference
            if "model" in metrics:
                deliverable_entry["model"] = metrics["model"]
            if "backend" in metrics:
                deliverable_entry["backend"] = metrics["backend"]

        manifest["deliverables"][deliverable_type] = deliverable_entry

        # Update status
        has_brainstorming = "brainstorming" in manifest.get("deliverables", {})
        has_formatted = "formatted_transcript" in manifest.get("deliverables", {})

        if has_brainstorming and has_formatted:
            manifest["status"] = "ready_for_editing"
            manifest["processing_completed"] = datetime.utcnow().isoformat() + "Z"

            # Calculate total project cost and per-model breakdown
            total_cost = 0.0
            total_tokens = 0
            model_costs = {}  # Track cost per model
            for deliverable in manifest["deliverables"].values():
                # Skip null/placeholder entries
                if not isinstance(deliverable, dict):
                    continue
                if "metrics" in deliverable:
                    cost = deliverable["metrics"].get("estimated_cost", 0.0)
                    tokens = deliverable["metrics"].get("total_tokens", 0)
                    model = deliverable["metrics"].get("model", "unknown")

                    total_cost += cost
                    total_tokens += tokens

                    # Accumulate per-model costs
                    if model not in model_costs:
                        model_costs[model] = {"cost": 0.0, "tokens": 0, "calls": 0}
                    model_costs[model]["cost"] += cost
                    model_costs[model]["tokens"] += tokens
                    model_costs[model]["calls"] += 1

            manifest["processing_metrics"] = {
                "total_estimated_cost": round(total_cost, 4),
                "total_tokens": total_tokens,
                "model_breakdown": {
                    model: {
                        "cost": round(stats["cost"], 4),
                        "tokens": stats["tokens"],
                        "calls": stats["calls"]
                    }
                    for model, stats in model_costs.items()
                }
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

    brainstorming_raw, backend_used, metrics = run_with_fallback("analyst", analyst_user, analyst_system, llm)
    brainstorming = strip_code_fences(brainstorming_raw)

    output_dir = OUTPUT_DIR / project_name
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

    log_event(project_name, "transcript-analyst", "completed", {"backend": backend_used, "metrics": metrics_dict})
    return brainstorming_filename, metrics_dict


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
    original_prefs = None
    formatter_override: list[str] | None = None

    if transcript_length > FORMATTER_LARGE_TRANSCRIPT_THRESHOLD:
        # Large transcript detected - prefer Gemini Pro (2M context) or gpt-4o for better performance
        formatter_override = ["gemini-pro", "gemini-flash", "gemini-flash-8b", "openai", "openai-mini"]
        if verbose:
            print(f"  ⚠ Large transcript detected ({transcript_length:,} chars) - upgrading to Gemini Pro (2M context)")
        log_event(project_name, "formatter", "large_transcript_detected", {"length": transcript_length, "upgrade_to": "gemini-pro"})
    elif transcript_length > TIMESTAMP_ACCURACY_THRESHOLD:
        # Medium/long transcript - prefer more capable model to improve timestamp alignment (Gemini-first)
        formatter_override = ["gemini-flash", "gemini-flash-8b", "openai", "openai-mini"]
        if verbose:
            print(f"  ⚠ Transcript {transcript_length:,} chars - upgrading formatter for better timestamp accuracy (Gemini-first)")
        log_event(project_name, "formatter", "timestamp_upgrade", {"length": transcript_length, "upgrade_to": "gemini-flash"})

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

    log_event(
        project_name,
        "formatter",
        "completed",
        {"backend": backend_used, "timestamps_created": bool(timestamp_filename), "metrics": metrics_dict}
    )
    return formatted_filename, timestamp_filename, metrics_dict


def archive_transcript(project_name: str, transcript_file: str | None = None, verbose: bool = True):
    """Archive the transcript file for a processed project"""
    archive_dir = TRANSCRIPTS_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Find the transcript file to archive
    candidates = _candidate_transcript_paths(project_name, transcript_file)

    for transcript_path in candidates:
        if transcript_path.exists() and transcript_path.parent == TRANSCRIPTS_DIR:
            # Only archive if it's in the main transcripts directory (not already archived)
            dest_path = archive_dir / transcript_path.name

            if dest_path.exists():
                if verbose:
                    print(f"  ⚠ Transcript already archived: {transcript_path.name}")
                return

            try:
                transcript_path.rename(dest_path)
                if verbose:
                    print(f"  ✓ Archived transcript: {transcript_path.name}")
                return
            except Exception as e:
                if verbose:
                    print(f"  ⚠ Failed to archive transcript: {e}")
                return

    if verbose:
        print(f"  ⚠ No unarchived transcript found for {project_name}")


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

    # Archive transcript immediately after successful processing
    if verbose:
        print(f"\n→ Archiving transcript...")
    archive_transcript(project_name, transcript_file, verbose)

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


def archive_old_output_folders(max_age_days: int = 15, verbose: bool = True):
    """Archive output project folders older than max_age_days

    Args:
        max_age_days: Maximum age in days before archiving (default: 15)
        verbose: Print status messages

    Returns:
        Number of folders archived
    """
    archive_dir = OUTPUT_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    archived_count = 0
    now = datetime.utcnow()

    if verbose:
        print(f"\n→ Checking for output folders older than {max_age_days} days...")

    # Scan all project directories in OUTPUT
    for project_dir in OUTPUT_DIR.iterdir():
        # Skip if not a directory, or if it's the archive directory itself
        if not project_dir.is_dir() or project_dir.name == "archive" or project_dir.name.startswith("."):
            continue

        manifest_path = project_dir / "manifest.json"

        # Skip if no manifest
        if not manifest_path.exists():
            continue

        try:
            with open(manifest_path) as f:
                manifest = json.load(f)

            # Get completion date from manifest
            completed_date_str = manifest.get("processing_completed")
            if not completed_date_str:
                # Fall back to processing_started if no completion date
                completed_date_str = manifest.get("processing_started")

            if not completed_date_str:
                continue

            # Parse date (ISO format)
            completed_date = datetime.fromisoformat(completed_date_str.replace("Z", "+00:00"))

            # Calculate age in days
            age = (now - completed_date).days

            if age >= max_age_days:
                dest_path = archive_dir / project_dir.name

                # Skip if already exists in archive
                if dest_path.exists():
                    continue

                # Move to archive
                project_dir.rename(dest_path)
                archived_count += 1

                if verbose:
                    print(f"  ✓ Archived {project_dir.name} ({age} days old)")

        except Exception as e:
            if verbose:
                print(f"  ⚠ Error archiving {project_dir.name}: {e}")

    if verbose:
        if archived_count > 0:
            print(f"\n✓ Archived {archived_count} output folder(s)")
        else:
            print(f"\n✓ No output folders older than {max_age_days} days")

    return archived_count


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
