
import json
from pathlib import Path

# This script is a standalone utility to reset the status of failed jobs in the queue.
# It is intended to be run from the root of the project.

QUEUE_FILE = Path(".processing-requests.json")

def reset_failed_jobs():
    """
    Resets all jobs with status 'failed' to 'pending'.
    """
    if not QUEUE_FILE.exists():
        print("No queue file found.")
        return

    try:
        with open(QUEUE_FILE) as f:
            queue = json.load(f)
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from queue file.")
        return

    failed_jobs = [item for item in queue if item.get("status") == "failed"]

    if not failed_jobs:
        print("No failed jobs found.")
        return

    for job in queue:
        if job.get("status") == "failed":
            job["status"] = "pending"
            job["error"] = None
            job["started_at"] = None
            job["completed_at"] = None

    try:
        with open(QUEUE_FILE, "w") as f:
            json.dump(queue, f, indent=2)
        print(f"Reset {len(failed_jobs)} failed jobs to 'pending'.")
    except IOError:
        print("Error: Could not write to queue file.")

if __name__ == "__main__":
    reset_failed_jobs()
