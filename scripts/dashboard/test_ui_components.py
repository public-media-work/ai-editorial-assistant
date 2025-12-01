#!/usr/bin/env python3
"""
Test script for UI components.

Tests the make_stats_panel function with various data scenarios.
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from session_manager import SessionManager
from ui_components import make_stats_panel


class MockDashboardState:
    """Mock DashboardState for testing"""

    def __init__(self, start_offset_seconds=0):
        """
        Create mock state with start time.

        Args:
            start_offset_seconds: How many seconds in the past to set start_time
        """
        self.start_time = time.time() - start_offset_seconds
        self.active_project = "TEST_001"
        self.current_step = "Testing..."
        self.backend_in_use = "test-backend"
        self.current_job_cost = 0.0
        self.current_video_length = "00:30:00"
        self.logs = []
        self.queue_data = []


def test_empty_session():
    """Test with empty session (no projects processed)"""
    print("\n" + "=" * 70)
    print("TEST 1: Empty Session (No Activity)")
    print("=" * 70)

    # Create temporary session file
    temp_session = Path("/tmp/test_session_empty.json")
    session = SessionManager(temp_session)

    # Create mock state with 5 minutes of elapsed time
    state = MockDashboardState(start_offset_seconds=300)

    # Render the panel
    console = Console()
    panel = make_stats_panel(state, session)
    console.print(panel)

    # Cleanup
    temp_session.unlink(missing_ok=True)


def test_session_with_projects():
    """Test with session that has processed projects"""
    print("\n" + "=" * 70)
    print("TEST 2: Session with Processed Projects")
    print("=" * 70)

    # Create temporary session file
    temp_session = Path("/tmp/test_session_projects.json")
    session = SessionManager(temp_session)

    # Add some project completions
    session.add_project_completion("PROJ_001", 0.12, 5.0, "completed")
    session.add_project_completion("PROJ_002", 0.18, 7.0, "completed")
    session.add_project_completion("PROJ_003", 0.15, 6.0, "completed")
    session.add_project_completion("PROJ_004", 0.5, 1.0, "failed")

    # Add some backend usage
    session.add_backend_usage("openai-mini", calls=20, cost=2.10)
    session.add_backend_usage("anthropic-sonnet", calls=10, cost=1.35)

    # Add cost events to timeline
    now = datetime.utcnow()
    for i in range(15):
        event_time = now - timedelta(minutes=15 - i)
        session.session_data["cost_timeline"].append({
            "timestamp": event_time.isoformat() + "Z",
            "cost": 0.08 + (i * 0.02),
            "project": f"PROJ_{i:03d}",
        })

    # Create mock state with 45 minutes of elapsed time
    state = MockDashboardState(start_offset_seconds=45 * 60)

    # Render the panel
    console = Console()
    panel = make_stats_panel(state, session)
    console.print(panel)

    # Cleanup
    temp_session.unlink(missing_ok=True)


def test_session_with_long_duration():
    """Test with session that has been running for a very long time"""
    print("\n" + "=" * 70)
    print("TEST 3: Long Duration Session (2+ hours)")
    print("=" * 70)

    # Create temporary session file
    temp_session = Path("/tmp/test_session_long.json")
    session = SessionManager(temp_session)

    # Add many projects over time
    for i in range(25):
        session.add_project_completion(f"PROJ_{i:04d}", 0.15 + (i * 0.01), 4.0, "completed")

    # Add backend usage
    session.add_backend_usage("openai-mini", calls=40, cost=4.20)
    session.add_backend_usage("anthropic-sonnet", calls=25, cost=3.45)
    session.add_backend_usage("openai-large", calls=10, cost=2.50)

    # Add cost events spread over 2 hours
    now = datetime.utcnow()
    for i in range(75):
        minutes_ago = 120 - int((i / 75) * 120)
        event_time = now - timedelta(minutes=minutes_ago)
        session.session_data["cost_timeline"].append({
            "timestamp": event_time.isoformat() + "Z",
            "cost": 0.10 + (i * 0.005),
            "project": f"PROJ_{i:04d}",
        })

    # Create mock state with 2 hours and 15 minutes elapsed
    state = MockDashboardState(start_offset_seconds=2 * 3600 + 15 * 60)

    # Render the panel
    console = Console()
    panel = make_stats_panel(state, session)
    console.print(panel)

    # Cleanup
    temp_session.unlink(missing_ok=True)


def test_session_with_high_failure_rate():
    """Test with session that has many failures"""
    print("\n" + "=" * 70)
    print("TEST 4: Session with High Failure Rate")
    print("=" * 70)

    # Create temporary session file
    temp_session = Path("/tmp/test_session_failures.json")
    session = SessionManager(temp_session)

    # Add mostly failed projects
    for i in range(10):
        session.add_project_completion(f"PROJ_{i:03d}", 0.25, 2.0, "failed")

    for i in range(3):
        session.add_project_completion(f"PROJ_{i+100:03d}", 0.15, 5.0, "completed")

    # Add errors
    session.add_error("PROJ_000", "Backend timeout", "openai-mini")
    session.add_error("PROJ_001", "Invalid transcript", "anthropic-sonnet")
    session.add_error("PROJ_002", "Rate limit exceeded", "openai-mini")

    # Add backend usage
    session.add_backend_usage("openai-mini", calls=8, cost=2.00)
    session.add_backend_usage("anthropic-sonnet", calls=5, cost=0.75)

    # Create mock state with 30 minutes elapsed
    state = MockDashboardState(start_offset_seconds=30 * 60)

    # Render the panel
    console = Console()
    panel = make_stats_panel(state, session)
    console.print(panel)

    # Cleanup
    temp_session.unlink(missing_ok=True)


def test_session_very_short():
    """Test with very short session (just seconds)"""
    print("\n" + "=" * 70)
    print("TEST 5: Very Short Session (15 seconds)")
    print("=" * 70)

    # Create temporary session file
    temp_session = Path("/tmp/test_session_short.json")
    session = SessionManager(temp_session)

    # Add just one quick project
    session.add_project_completion("PROJ_001", 0.05, 0.25, "completed")
    session.add_backend_usage("openai-mini", calls=1, cost=0.05)

    # Create mock state with 15 seconds elapsed
    state = MockDashboardState(start_offset_seconds=15)

    # Render the panel
    console = Console()
    panel = make_stats_panel(state, session)
    console.print(panel)

    # Cleanup
    temp_session.unlink(missing_ok=True)


if __name__ == "__main__":
    console = Console()

    try:
        test_empty_session()
        test_session_with_projects()
        test_session_with_long_duration()
        test_session_with_high_failure_rate()
        test_session_very_short()

        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 70)

    except Exception as e:
        console.print(f"[red]ERROR: {e}[/]")
        import traceback

        traceback.print_exc()
        sys.exit(1)
