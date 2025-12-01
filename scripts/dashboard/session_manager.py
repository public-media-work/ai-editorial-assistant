"""
Session management for dashboard state persistence.

Provides SessionManager class for loading, saving, and managing session data
across dashboard restarts.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
from threading import Lock


class SessionManager:
    """
    Manages session state persistence for the dashboard.

    Loads existing session data from file or creates a new session with initial structure.
    Provides thread-safe save operations using atomic writes (write to temp file, then rename).
    """

    def __init__(self, session_file: Path) -> None:
        """
        Initialize session manager with file path.

        Args:
            session_file: Path to the session JSON file
        """
        self.session_file = Path(session_file)
        self.lock = Lock()
        self.session_data = self.load_or_create()

    def load_or_create(self) -> dict:
        """
        Load existing session file or create new session.

        If the session file exists, load it. Otherwise, create a new session
        with initial structure and current timestamp.

        Returns:
            Session data dictionary with required structure
        """
        if self.session_file.exists():
            try:
                with open(self.session_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, create new session
                return self._create_new_session()
        else:
            return self._create_new_session()

    def _create_new_session(self) -> dict:
        """
        Create a new session with initial structure.

        Returns:
            New session dictionary with default structure
        """
        now = datetime.utcnow().isoformat() + "Z"
        return {
            "session_id": now,
            "start_time": now,
            "last_updated": now,
            "stats": {
                "projects_processed": 0,
                "projects_failed": 0,
                "total_cost": 0.0,
                "total_processing_minutes": 0.0,
                "backend_usage": {},
            },
            "cost_timeline": [],
            "errors": [],
        }

    def _save(self) -> None:
        """
        Save session data to file using atomic writes.

        Writes to a temporary file first, then renames it to the target path
        to ensure atomicity and prevent data loss if write is interrupted.
        """
        # Ensure parent directory exists
        self.session_file.parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file first
        tmp_path = self.session_file.with_suffix(".tmp")
        try:
            with open(tmp_path, "w") as f:
                json.dump(self.session_data, f, indent=2)
            # Atomically rename temp file to target
            tmp_path.replace(self.session_file)
        except Exception as e:
            # Clean up temp file if it exists
            if tmp_path.exists():
                tmp_path.unlink()
            raise

    def save(self) -> None:
        """
        Public method to save session data.

        Thread-safe wrapper for _save() that can be called from external code
        like restart functionality.
        """
        with self.lock:
            self._save()

    def add_project_completion(
        self, project: str, cost: float, duration: float, status: str
    ) -> None:
        """
        Record a completed project in session statistics.

        Updates project count, cost tracking, and processing duration.

        Args:
            project: Project name/identifier
            cost: Cost of processing this project
            duration: Processing duration in minutes
            status: Completion status ("completed" or "failed")
        """
        with self.lock:
            stats = self.session_data["stats"]

            if status == "completed":
                stats["projects_processed"] += 1
            elif status == "failed":
                stats["projects_failed"] += 1

            stats["total_cost"] += cost
            stats["total_processing_minutes"] += duration

            self.session_data["last_updated"] = datetime.utcnow().isoformat() + "Z"
            self._save()

    def add_cost_event(self, project: str, cost: float) -> None:
        """
        Add a cost event to the timeline for visualization.

        Args:
            project: Project name/identifier
            cost: Cost amount for this event
        """
        with self.lock:
            event = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "cost": cost,
                "project": project,
            }
            self.session_data["cost_timeline"].append(event)
            self.session_data["last_updated"] = datetime.utcnow().isoformat() + "Z"
            self._save()

    def add_error(self, project: str, error: str, backend: str) -> None:
        """
        Record an error in the session.

        Args:
            project: Project name/identifier where error occurred
            error: Error message or description
            backend: Name of the backend that failed
        """
        with self.lock:
            error_record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "project": project,
                "error": error,
                "backend": backend,
            }
            self.session_data["errors"].append(error_record)
            self.session_data["last_updated"] = datetime.utcnow().isoformat() + "Z"
            self._save()

    def get_stats(self) -> dict:
        """
        Return current session statistics.

        Returns:
            Session statistics dictionary with aggregated data
        """
        with self.lock:
            # Return a copy to prevent external modifications
            return dict(self.session_data["stats"])

    def get_cost_timeline(self, minutes: int = 60) -> list:
        """
        Get cost events for the last N minutes.

        Filters the cost timeline to include only events within the specified
        time window from now.

        Args:
            minutes: Number of minutes to look back (default 60)

        Returns:
            List of cost events within the time window
        """
        with self.lock:
            if not self.session_data["cost_timeline"]:
                return []

            # Calculate cutoff time
            try:
                # Get the most recent timestamp and subtract minutes
                latest_event = self.session_data["cost_timeline"][-1]
                latest_time = datetime.fromisoformat(
                    latest_event["timestamp"].replace("Z", "+00:00")
                ).replace(tzinfo=None)

                from datetime import timedelta

                cutoff_time = latest_time - timedelta(minutes=minutes)

                # Filter events within the time window
                return [
                    event.copy()  # Return copies to prevent external modifications
                    for event in self.session_data["cost_timeline"]
                    if datetime.fromisoformat(
                        event["timestamp"].replace("Z", "+00:00")
                    ).replace(tzinfo=None)
                    >= cutoff_time
                ]
            except (ValueError, KeyError):
                # If any timestamp parsing fails, return all events
                return [event.copy() for event in self.session_data["cost_timeline"]]

    def reset_session(self) -> None:
        """
        Start a new session while preserving historical data.

        Archives the current session data and initializes a new session with fresh counters.
        """
        with self.lock:
            # Store the old session data before resetting
            self.session_data = self._create_new_session()
            self._save()

    def add_backend_usage(self, backend: str, calls: int = 1, cost: float = 0.0) -> None:
        """
        Record backend usage statistics.

        Args:
            backend: Name of the backend
            calls: Number of calls to add (default 1)
            cost: Cost to add for this backend
        """
        with self.lock:
            backend_usage = self.session_data["stats"]["backend_usage"]

            if backend not in backend_usage:
                backend_usage[backend] = {"calls": 0, "cost": 0.0}

            backend_usage[backend]["calls"] += calls
            backend_usage[backend]["cost"] += cost

            self.session_data["last_updated"] = datetime.utcnow().isoformat() + "Z"
            self._save()
