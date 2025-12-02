"""
Session data exporter for the Editorial Assistant Dashboard.

Provides multiple export formats: JSON, CSV, and Markdown summary.
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session_manager import SessionManager


class SessionExporter:
    """
    Export session data to various formats.

    Supports JSON (full data), CSV (tabular), and Markdown (summary report).
    """

    def __init__(self, session_manager: "SessionManager"):
        """
        Initialize exporter with session manager.

        Args:
            session_manager: SessionManager instance with data to export
        """
        self.session = session_manager
        self.session_data = session_manager.session_data

    def export_json(self, path: Path) -> None:
        """
        Export complete session data as JSON.

        Args:
            path: Output file path
        """
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON with pretty formatting
        with open(path, 'w') as f:
            json.dump(self.session_data, f, indent=2)

    def export_csv(self, path: Path) -> None:
        """
        Export session data as CSV (tabular format).

        Flattens the session data into rows, one per project processed.

        Args:
            path: Output file path
        """
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Get stats
        stats = self.session_data.get("stats", {})

        # Prepare CSV rows - one row per backend
        rows = []
        backend_usage = stats.get("backend_usage", {})

        for backend_name, usage in backend_usage.items():
            rows.append({
                "session_id": self.session_data.get("session_id", ""),
                "start_time": self.session_data.get("start_time", ""),
                "backend": backend_name,
                "calls": usage.get("calls", 0),
                "cost": usage.get("cost", 0.0),
                "total_projects": stats.get("projects_processed", 0),
                "failed_projects": stats.get("projects_failed", 0),
                "total_cost": stats.get("total_cost", 0.0),
                "total_minutes": stats.get("total_processing_minutes", 0.0)
            })

        # If no backends, create one summary row
        if not rows:
            rows.append({
                "session_id": self.session_data.get("session_id", ""),
                "start_time": self.session_data.get("start_time", ""),
                "backend": "none",
                "calls": 0,
                "cost": 0.0,
                "total_projects": stats.get("projects_processed", 0),
                "failed_projects": stats.get("projects_failed", 0),
                "total_cost": stats.get("total_cost", 0.0),
                "total_minutes": stats.get("total_processing_minutes", 0.0)
            })

        # Write CSV
        with open(path, 'w', newline='') as f:
            fieldnames = ["session_id", "start_time", "backend", "calls", "cost",
                         "total_projects", "failed_projects", "total_cost", "total_minutes"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def export_summary_md(self, path: Path) -> None:
        """
        Export session summary as Markdown report.

        Creates a human-readable summary with statistics, costs, and errors.

        Args:
            path: Output file path
        """
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        stats = self.session_data.get("stats", {})

        # Calculate metrics
        duration = self._calculate_duration()
        success_rate = self._calculate_success_rate()
        backend_costs = self._format_backend_costs()
        errors_section = self._format_errors()

        # Build markdown content
        content = f"""# Dashboard Session Report

**Session ID**: {self.session_data.get('session_id', 'Unknown')}
**Start Time**: {self.session_data.get('start_time', 'Unknown')}
**Duration**: {duration}

---

## Summary

- **Projects Processed**: {stats.get('projects_processed', 0)}
- **Projects Failed**: {stats.get('projects_failed', 0)}
- **Success Rate**: {success_rate}%
- **Total Cost**: ${stats.get('total_cost', 0.0):.4f}
- **Total Processing Time**: {stats.get('total_processing_minutes', 0.0):.1f} minutes

---

## Backend Usage

{backend_costs}

---

## Errors

{errors_section}

---

*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        with open(path, 'w') as f:
            f.write(content)

    def _calculate_duration(self) -> str:
        """Calculate session duration as human-readable string."""
        start = self.session_data.get("start_time", "")
        last = self.session_data.get("last_updated", "")

        if not start or not last:
            return "Unknown"

        try:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            last_dt = datetime.fromisoformat(last.replace('Z', '+00:00'))
            delta = last_dt - start_dt

            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60

            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except:
            return "Unknown"

    def _calculate_success_rate(self) -> float:
        """Calculate success rate percentage."""
        stats = self.session_data.get("stats", {})
        processed = stats.get("projects_processed", 0)
        failed = stats.get("projects_failed", 0)
        total = processed + failed

        if total == 0:
            return 0.0

        return round((processed / total) * 100, 1)

    def _format_backend_costs(self) -> str:
        """Format backend usage as markdown table."""
        stats = self.session_data.get("stats", {})
        backend_usage = stats.get("backend_usage", {})

        if not backend_usage:
            return "*No backend usage recorded*"

        lines = ["| Backend | Calls | Cost |", "|---------|-------|------|"]

        for backend, usage in sorted(backend_usage.items()):
            calls = usage.get("calls", 0)
            cost = usage.get("cost", 0.0)
            lines.append(f"| {backend} | {calls} | ${cost:.4f} |")

        return "\n".join(lines)

    def _format_errors(self) -> str:
        """Format errors as markdown list."""
        errors = self.session_data.get("errors", [])

        if not errors:
            return "*No errors recorded*"

        lines = []
        for i, error in enumerate(errors[-10:], 1):  # Last 10 errors
            timestamp = error.get("timestamp", "")
            project = error.get("project", "Unknown")
            message = error.get("error", "No details")
            backend = error.get("backend", "unknown")

            # Truncate long messages
            if len(message) > 100:
                message = message[:97] + "..."

            lines.append(f"{i}. **{project}** [{backend}] - {message}")
            lines.append(f"   *{timestamp}*")

        return "\n".join(lines)
