"""
Session data export functionality.

Provides SessionExporter class for exporting session data in multiple formats
(JSON, CSV, Markdown).
"""

from pathlib import Path
from typing import Optional


class SessionExporter:
    """
    Exports session data in multiple formats.

    Provides methods to export session data as JSON, CSV, or Markdown summary.
    """

    def __init__(self, session_manager: "SessionManager") -> None:
        """
        Initialize exporter with a session manager instance.

        Args:
            session_manager: SessionManager instance to export from
        """
        self.session = session_manager

    def export_json(self, path: Path) -> None:
        """
        Export full session data as JSON.

        Args:
            path: Output file path
        """
        pass

    def export_csv(self, path: Path) -> None:
        """
        Export project list as CSV.

        Args:
            path: Output file path
        """
        pass

    def export_summary_md(self, path: Path) -> None:
        """
        Export human-readable summary as Markdown.

        Args:
            path: Output file path
        """
        pass
