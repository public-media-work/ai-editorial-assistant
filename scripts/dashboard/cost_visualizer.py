"""
Cost visualization and calculation utilities.

Provides functions for calculating cost rates, bucketing timeline data,
and generating ASCII sparklines for cost visualization.
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .session_manager import SessionManager


def calculate_cost_rate(session: "SessionManager") -> dict:
    """
    Calculate cost per minute and hour based on recent activity.

    Analyzes the cost timeline from the last 60 minutes to calculate:
    - Cost per minute
    - Cost per hour (per_minute * 60)
    - Average cost per project

    Args:
        session: SessionManager instance with cost timeline

    Returns:
        Dictionary with keys:
        - per_minute: float - Cost per minute
        - per_hour: float - Cost per hour
        - avg_per_project: float - Average cost per project
    """
    timeline = session.get_cost_timeline(minutes=60)

    if not timeline:
        return {
            "per_minute": 0.0,
            "per_hour": 0.0,
            "avg_per_project": 0.0,
        }

    # Calculate total cost
    total_cost = sum(event["cost"] for event in timeline)

    # Calculate duration between first and last event
    try:
        first_timestamp = datetime.fromisoformat(
            timeline[0]["timestamp"].replace("Z", "+00:00")
        ).replace(tzinfo=None)
        last_timestamp = datetime.fromisoformat(
            timeline[-1]["timestamp"].replace("Z", "+00:00")
        ).replace(tzinfo=None)

        duration_minutes = (last_timestamp - first_timestamp).total_seconds() / 60
    except (ValueError, KeyError):
        duration_minutes = 0

    # Handle edge case: zero duration
    if duration_minutes == 0 and len(timeline) > 1:
        # If all events happened at the same time, use a minimal duration
        duration_minutes = 1

    per_minute = total_cost / duration_minutes if duration_minutes > 0 else 0.0
    per_hour = per_minute * 60
    avg_per_project = total_cost / len(timeline) if timeline else 0.0

    return {
        "per_minute": per_minute,
        "per_hour": per_hour,
        "avg_per_project": avg_per_project,
    }


def bucket_timeline(timeline: list[dict[str, Any]], num_buckets: int) -> list[float]:
    """
    Group timeline events into N time buckets and sum costs.

    Divides the time range from the first to last event into equal intervals
    and calculates the total cost for events falling in each bucket.

    Args:
        timeline: List of timeline events with:
                 - timestamp: ISO8601 timestamp string
                 - cost: float amount
                 - project: string identifier (optional)
        num_buckets: Number of time buckets to create

    Returns:
        List of floats representing the sum of costs in each bucket.
        If timeline is empty or has only one event, returns list of zeros.

    Raises:
        ValueError: If num_buckets <= 0
    """
    if num_buckets <= 0:
        raise ValueError("num_buckets must be positive")

    if not timeline:
        return [0.0] * num_buckets

    if len(timeline) == 1:
        # Single event: put cost in first bucket, zeros in rest
        buckets = [0.0] * num_buckets
        buckets[0] = timeline[0]["cost"]
        return buckets

    # Parse timestamps
    try:
        timestamps = [
            datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00")).replace(
                tzinfo=None
            )
            for event in timeline
        ]
    except (ValueError, KeyError):
        # If parsing fails, distribute evenly
        return [sum(e["cost"] for e in timeline) / num_buckets for _ in range(num_buckets)]

    first_time = min(timestamps)
    last_time = max(timestamps)

    # Handle edge case: all events at same timestamp
    time_span = (last_time - first_time).total_seconds()
    if time_span == 0:
        # All events at same time: put all costs in first bucket
        buckets = [0.0] * num_buckets
        buckets[0] = sum(e["cost"] for e in timeline)
        return buckets

    # Initialize buckets
    buckets = [0.0] * num_buckets

    # Assign each event to a bucket
    for event, event_time in zip(timeline, timestamps):
        # Calculate position (0 to 1)
        position = (event_time - first_time).total_seconds() / time_span

        # Handle edge case: event at exactly the end
        if position >= 1.0:
            bucket_idx = num_buckets - 1
        else:
            bucket_idx = int(position * num_buckets)

        buckets[bucket_idx] += event["cost"]

    return buckets


def format_currency(amount: float) -> str:
    """
    Format a float as USD currency string.

    Converts the amount to a string with exactly 2 decimal places,
    prefixed with the dollar sign.

    Args:
        amount: Dollar amount to format (e.g., 0.1234, 5.0, 100.567)

    Returns:
        Formatted currency string (e.g., "$0.12", "$5.00", "$100.57")
    """
    return f"${amount:.2f}"


def get_bar_char(level: int) -> str:
    """
    Return Unicode block character for given height level.

    Maps height levels (0-8) to Unicode block characters for ASCII
    bar chart visualization.

    Args:
        level: Height level (0-8)
               - 0: space (empty)
               - 1-8: progressively filled blocks

    Returns:
        Unicode block character
    """
    chars = {
        0: " ",
        1: "▁",
        2: "▂",
        3: "▃",
        4: "▄",
        5: "▅",
        6: "▆",
        7: "▇",
        8: "█",
    }
    # Clamp level to valid range
    level = max(0, min(8, level))
    return chars.get(level, " ")


def make_cost_sparkline(
    timeline: list[dict[str, Any]], width: int = 50, height: int = 5
) -> str:
    """
    Generate ASCII sparkline from cost timeline.

    Creates a multi-line ASCII bar chart showing cost distribution over time.
    Uses Unicode block characters and includes axis labels with currency formatting.

    Args:
        timeline: List of cost events with:
                 - timestamp: ISO8601 timestamp string
                 - cost: float amount
                 - project: string identifier (optional)
        width: Width of sparkline in characters (default 50)
        height: Height of sparkline in levels (default 5, max 8)

    Returns:
        Multi-line ASCII sparkline string. If timeline is empty,
        returns a message "No data available".

    Example output (height=5, width=20):
        $0.50 ┤                ╭─╮
        $0.40 ┤                │ │
        $0.30 ┤        ╭─╮     │ │
        $0.20 ┤    ╭─╮ │ │ ╭─╮ │ │
        $0.10 ┤ ╭─╮│ │ │ │ │ │ │ │
              10:00  10:15  10:30
    """
    if not timeline:
        return "No data available"

    # Clamp height to valid range
    height = max(1, min(8, height))

    # Bucket the timeline
    buckets = bucket_timeline(timeline, num_buckets=width)

    # Find max value for scaling
    max_value = max(buckets) if buckets else 0
    if max_value == 0:
        return "No cost data"

    # Get time labels
    time_labels = format_time_labels(timeline, num_labels=5)

    # Build the chart from top to bottom
    lines = []

    # Add each row (from top to bottom, so start with highest level)
    for row in range(height, 0, -1):
        # Add y-axis label
        y_value = (row / height) * max_value
        y_label = format_currency(y_value)
        line = f"{y_label:>6} ┤ "

        # Add bars for this row
        for bucket_value in buckets:
            # Calculate the level of this bucket
            bucket_level = int((bucket_value / max_value) * height) if max_value > 0 else 0

            # Show bar character if bucket_level >= row
            if bucket_level >= row:
                line += get_bar_char(8)  # Full block at this height
            else:
                line += " "

        lines.append(line)

    # Add x-axis
    x_axis = "      └─" + "─" * width

    lines.append(x_axis)

    # Add time labels
    label_line = "       "
    label_spacing = width // (len(time_labels) - 1) if len(time_labels) > 1 else width
    label_positions = [i * label_spacing for i in range(len(time_labels))]

    # Build label line with proper spacing
    current_pos = 0
    label_idx = 0
    for pos in range(width):
        if label_idx < len(label_positions) and pos >= label_positions[label_idx]:
            label = time_labels[label_idx]
            label_line += label[: width - pos]
            current_pos = pos + len(label)
            label_idx += 1
        elif current_pos <= pos:
            label_line += " "
        else:
            current_pos -= 1

    if time_labels:
        lines.append(label_line)

    return "\n".join(lines)


def format_time_labels(timeline: list[dict[str, Any]], num_labels: int = 5) -> list[str]:
    """
    Extract evenly spaced time labels from timeline.

    Selects num_labels time points evenly distributed across the timeline
    and formats them as HH:MM strings in 24-hour format.

    Args:
        timeline: List of timeline events with timestamp field
        num_labels: Number of labels to extract (default 5)

    Returns:
        List of formatted time strings (e.g., ["10:00", "10:15", "10:30"])
        If timeline is empty, returns empty list.

    Note:
        If timeline has fewer events than requested labels, returns what's available.
    """
    if not timeline:
        return []

    if len(timeline) <= num_labels:
        # Return all timestamps
        labels = []
        for event in timeline:
            try:
                dt = datetime.fromisoformat(
                    event["timestamp"].replace("Z", "+00:00")
                ).replace(tzinfo=None)
                labels.append(dt.strftime("%H:%M"))
            except (ValueError, KeyError):
                pass
        return labels

    # Select evenly spaced events
    indices = []
    for i in range(num_labels):
        idx = int((i / (num_labels - 1)) * (len(timeline) - 1))
        indices.append(idx)

    labels = []
    for idx in indices:
        try:
            event = timeline[idx]
            dt = datetime.fromisoformat(
                event["timestamp"].replace("Z", "+00:00")
            ).replace(tzinfo=None)
            labels.append(dt.strftime("%H:%M"))
        except (ValueError, KeyError, IndexError):
            labels.append("")

    return labels
