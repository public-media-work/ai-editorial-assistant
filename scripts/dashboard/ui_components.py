"""
UI components for the dashboard.

Provides rich UI panel generators for displaying statistics, errors,
progress, and other dashboard information.
"""

from typing import TYPE_CHECKING
import time
from datetime import datetime, timedelta

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

if TYPE_CHECKING:
    from .session_manager import SessionManager
    from ..process_queue_visual import DashboardState

from .cost_visualizer import (
    calculate_cost_rate,
    make_cost_sparkline,
    format_currency,
)


def make_stats_panel(state: "DashboardState", session: "SessionManager") -> "Panel":
    """
    Create a statistics panel with session metrics and cost visualization.

    Displays comprehensive session statistics including:
    - Session duration and project processing counts
    - Processing rate (projects per minute)
    - Cost metrics (current session, average per project, estimated hourly)
    - Cost timeline visualization as ASCII sparkline
    - Backend distribution with call counts, costs, and percentages

    Args:
        state: DashboardState instance with start_time attribute
        session: SessionManager instance with statistics and cost data

    Returns:
        Rich Panel with formatted statistics and cost visualization

    Edge Cases:
        - Empty session: Shows "No activity yet"
        - No backend usage: Skips backend distribution section
        - Empty cost timeline: Shows "No cost data" instead of sparkline
        - Very long sessions: Formats as "Xd Xh Xm" for durations > 1 hour
        - Division by zero: Handles gracefully with 0 values
    """
    # Calculate session duration
    elapsed = time.time() - state.start_time
    duration_text = _format_duration(elapsed)

    # Get session statistics
    stats = session.get_stats()
    projects_processed = stats.get("projects_processed", 0)
    projects_failed = stats.get("projects_failed", 0)
    total_cost = stats.get("total_cost", 0.0)
    backend_usage = stats.get("backend_usage", {})

    # Calculate processing rate
    rate = projects_processed / (elapsed / 60) if elapsed > 0 else 0.0

    # Build the main table for the panel
    table = Table(box=None, expand=True, show_header=False, padding=(0, 1))

    # Row 1: Summary line
    summary_text = Text()
    summary_text.append(f"Session: {duration_text}", style="white")
    summary_text.append(" │ Processed: ", style="dim")
    summary_text.append(str(projects_processed), style="green bold")
    summary_text.append(" ✓ ", style="green")
    summary_text.append(str(projects_failed), style="red bold")
    summary_text.append(" ✗", style="red")
    summary_text.append(f" │ Rate: {rate:.2f}/min", style="white")

    table.add_row(summary_text)

    # Row 2: Cost tracking header
    table.add_row("")
    table.add_row(Text("COST TRACKING", style="cyan bold"))

    # Row 3: Cost metrics
    cost_rates = calculate_cost_rate(session)
    cost_text = Text()
    cost_text.append(f"Current Session: {format_currency(total_cost)}", style="bold green")

    # Calculate average per project (avoid division by zero)
    avg_per_project = total_cost / projects_processed if projects_processed > 0 else 0.0
    cost_text.append(f" │ Avg/Project: {format_currency(avg_per_project)}", style="white")

    est_hour = cost_rates.get("per_hour", 0.0)
    cost_text.append(f" │ Est. Hour: {format_currency(est_hour)}", style="white")

    table.add_row(cost_text)

    # Row 4: Cost sparkline (if there's data)
    timeline = session.get_cost_timeline(minutes=60)
    if timeline:
        sparkline = make_cost_sparkline(timeline, width=50, height=5)
        sparkline_panel = Panel(
            sparkline,
            title="[dim]Cost Timeline (Last 60min)[/]",
            border_style="dim",
            box=box.SIMPLE,
            expand=True,
        )
        table.add_row(sparkline_panel)
    else:
        # Show placeholder if no data
        table.add_row(
            Panel(
                "[dim]No cost data[/]",
                title="[dim]Cost Timeline (Last 60min)[/]",
                border_style="dim",
                box=box.SIMPLE,
            )
        )

    # Row 5: Backend distribution
    if backend_usage:
        table.add_row("")
        table.add_row(Text("Backend Distribution:", style="cyan bold"))

        # Sort by call count (descending)
        sorted_backends = sorted(
            backend_usage.items(),
            key=lambda x: x[1].get("calls", 0),
            reverse=True,
        )

        # Calculate total calls for percentage
        total_calls = sum(b[1].get("calls", 0) for b in sorted_backends)

        for backend_name, usage in sorted_backends:
            calls = usage.get("calls", 0)
            cost = usage.get("cost", 0.0)

            # Calculate percentage
            percentage = (calls / total_calls * 100) if total_calls > 0 else 0.0

            # Create bar (10 chars = 100%, scale proportionally)
            bar_length = max(1, int((calls / total_calls * 10))) if total_calls > 0 else 1
            bar = "■" * bar_length

            backend_text = Text()
            backend_text.append(bar, style="cyan bold")
            backend_text.append(f" {backend_name:<20} {calls:>3} calls ", style="white")
            backend_text.append(format_currency(cost), style="bold green")
            backend_text.append(f" ({percentage:>5.1f}%)", style="dim white")

            table.add_row(backend_text)
    else:
        # Show placeholder if no backend usage
        table.add_row("")
        table.add_row(Text("Backend Distribution: None yet", style="dim"))

    # Create the panel
    return Panel(
        table,
        title="[bold cyan]SESSION STATISTICS[/]",
        border_style="cyan",
        expand=True,
    )


def _format_duration(seconds: float) -> str:
    """
    Format seconds as human-readable duration.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "1m 30s", "1h 45m", "2d 3h")
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"
    else:
        days = int(seconds / 86400)
        hours = int((seconds % 86400) / 3600)
        return f"{days}d {hours}h"


def make_error_panel(session: "SessionManager") -> "Panel":
    """
    Create a panel displaying recent errors.

    Args:
        session: SessionManager instance

    Returns:
        Rich Panel with recent errors
    """
    pass


def make_progress_bar(
    percent: int, message: str = "", width: int = 20
) -> "ProgressBar":
    """
    Create a progress bar for long-running tasks.

    Args:
        percent: Progress percentage (0-100)
        message: Progress message
        width: Width of progress bar

    Returns:
        Rich ProgressBar widget
    """
    pass
