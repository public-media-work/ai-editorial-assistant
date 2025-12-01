"""
Test suite for cost_visualizer module.

Tests cost calculation, timeline bucketing, currency formatting,
and sparkline generation with various edge cases.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.dashboard.cost_visualizer import (
    calculate_cost_rate,
    bucket_timeline,
    format_currency,
    get_bar_char,
    make_cost_sparkline,
    format_time_labels,
)
from scripts.dashboard.session_manager import SessionManager


def test_format_currency():
    """Test currency formatting with various amounts."""
    print("Testing format_currency()...")
    test_cases = [
        (0.1234, "$0.12"),
        (5.0, "$5.00"),
        (100.567, "$100.57"),
        (0.0, "$0.00"),
        (1.999, "$2.00"),
        (0.005, "$0.01"),  # Rounds up
    ]

    for amount, expected in test_cases:
        result = format_currency(amount)
        assert result == expected, f"format_currency({amount}) = {result}, expected {expected}"
        print(f"  ✓ {amount:>8} -> {result}")

    print("  All format_currency tests passed!\n")


def test_get_bar_char():
    """Test Unicode bar character selection."""
    print("Testing get_bar_char()...")
    test_cases = [
        (0, " "),
        (1, "▁"),
        (2, "▂"),
        (3, "▃"),
        (4, "▄"),
        (5, "▅"),
        (6, "▆"),
        (7, "▇"),
        (8, "█"),
        (-1, " "),  # Out of range (clamped to 0)
        (10, "█"),  # Out of range (clamped to 8)
    ]

    for level, expected in test_cases:
        result = get_bar_char(level)
        assert result == expected, f"get_bar_char({level}) = {result}, expected {expected}"
        print(f"  ✓ Level {level:>2} -> '{result}'")

    print("  All get_bar_char tests passed!\n")


def test_bucket_timeline_empty():
    """Test bucket_timeline with edge cases."""
    print("Testing bucket_timeline() edge cases...")

    # Empty timeline
    result = bucket_timeline([], 5)
    assert result == [0.0, 0.0, 0.0, 0.0, 0.0], f"Empty timeline failed: {result}"
    print("  ✓ Empty timeline")

    # Single event
    single = [{"timestamp": "2025-12-01T10:00:00Z", "cost": 0.5, "project": "TEST"}]
    result = bucket_timeline(single, 5)
    assert result == [0.5, 0.0, 0.0, 0.0, 0.0], f"Single event failed: {result}"
    print("  ✓ Single event")

    # All events at same timestamp
    same_time = [
        {"timestamp": "2025-12-01T10:00:00Z", "cost": 0.1, "project": "P1"},
        {"timestamp": "2025-12-01T10:00:00Z", "cost": 0.2, "project": "P2"},
        {"timestamp": "2025-12-01T10:00:00Z", "cost": 0.15, "project": "P3"},
    ]
    result = bucket_timeline(same_time, 5)
    assert result == [0.45, 0.0, 0.0, 0.0, 0.0], f"Same time events failed: {result}"
    print("  ✓ All events at same timestamp")

    print("  All bucket_timeline edge case tests passed!\n")


def test_bucket_timeline_distribution():
    """Test bucket_timeline with distributed events."""
    print("Testing bucket_timeline() distribution...")

    # Create timeline with events at different times
    base_time = datetime(2025, 12, 1, 10, 0, 0)
    timeline = []

    # Add events at 0, 15, 30, 45 minutes
    for i in range(4):
        timestamp = (base_time + timedelta(minutes=i * 15)).isoformat() + "Z"
        timeline.append({"timestamp": timestamp, "cost": 0.1 + i * 0.05, "project": f"P{i}"})

    result = bucket_timeline(timeline, num_buckets=4)
    total_cost = sum(e["cost"] for e in timeline)
    result_sum = sum(result)

    assert len(result) == 4, f"Wrong number of buckets: {len(result)}"
    assert abs(result_sum - total_cost) < 0.0001, f"Cost not preserved: {result_sum} vs {total_cost}"
    print(f"  ✓ 4 events over 45 minutes distributed into 4 buckets")
    print(f"    Buckets: {[f'${b:.2f}' for b in result]}")
    print(f"    Total: ${result_sum:.2f} (input: ${total_cost:.2f})")

    print("  All bucket_timeline distribution tests passed!\n")


def test_format_time_labels_empty():
    """Test format_time_labels with edge cases."""
    print("Testing format_time_labels() edge cases...")

    # Empty timeline
    result = format_time_labels([], num_labels=5)
    assert result == [], f"Empty timeline failed: {result}"
    print("  ✓ Empty timeline")

    # Single event
    single = [{"timestamp": "2025-12-01T10:30:45Z", "cost": 0.5, "project": "TEST"}]
    result = format_time_labels(single, num_labels=5)
    assert len(result) == 1, f"Single event should return 1 label: {result}"
    assert result[0] == "10:30", f"Wrong time format: {result[0]}"
    print(f"  ✓ Single event: {result}")

    print("  All format_time_labels edge case tests passed!\n")


def test_format_time_labels_distribution():
    """Test format_time_labels with distributed events."""
    print("Testing format_time_labels() distribution...")

    # Create timeline with 10 events at hourly intervals
    base_time = datetime(2025, 12, 1, 10, 0, 0)
    timeline = []

    for i in range(10):
        timestamp = (base_time + timedelta(hours=i)).isoformat() + "Z"
        timeline.append({"timestamp": timestamp, "cost": 0.1, "project": f"P{i}"})

    result = format_time_labels(timeline, num_labels=5)
    assert len(result) == 5, f"Wrong number of labels: {len(result)}"
    print(f"  ✓ 10 events over 9 hours, 5 labels: {result}")

    print("  All format_time_labels distribution tests passed!\n")


def test_make_cost_sparkline_empty():
    """Test sparkline generation with empty timeline."""
    print("Testing make_cost_sparkline() with empty data...")

    result = make_cost_sparkline([])
    assert result == "No data available", f"Wrong empty message: {result}"
    print("  ✓ Empty timeline returns 'No data available'")

    print("  All sparkline empty tests passed!\n")


def test_make_cost_sparkline_simple():
    """Test sparkline generation with simple data."""
    print("Testing make_cost_sparkline() with simple data...")

    # Create simple timeline
    base_time = datetime(2025, 12, 1, 10, 0, 0)
    timeline = []

    costs = [0.1, 0.2, 0.15, 0.25, 0.3]
    for i, cost in enumerate(costs):
        timestamp = (base_time + timedelta(minutes=i * 15)).isoformat() + "Z"
        timeline.append({"timestamp": timestamp, "cost": cost, "project": f"P{i}"})

    result = make_cost_sparkline(timeline, width=20, height=5)
    lines = result.split("\n")

    assert len(lines) >= 5, f"Sparkline should have at least 5 lines (height), got {len(lines)}"
    print(f"  ✓ Generated {len(lines)} line sparkline")
    print("\nSparkline output:")
    for line in lines:
        print(f"    {line}")

    print("  All sparkline simple tests passed!\n")


def test_make_cost_sparkline_realistic():
    """Test sparkline with realistic timeline data."""
    print("Testing make_cost_sparkline() with realistic data...")

    # Create realistic timeline with varying costs
    base_time = datetime(2025, 12, 1, 10, 0, 0)
    timeline = []

    # Simulate costs with peaks and valleys
    cost_pattern = [0.05, 0.08, 0.12, 0.15, 0.10, 0.20, 0.25, 0.18, 0.22, 0.16]

    for i, cost in enumerate(cost_pattern):
        timestamp = (base_time + timedelta(minutes=i * 6)).isoformat() + "Z"
        timeline.append({"timestamp": timestamp, "cost": cost, "project": f"PROJ_{i:03d}"})

    result = make_cost_sparkline(timeline, width=50, height=5)
    lines = result.split("\n")

    assert len(lines) >= 5, f"Should have at least 5 lines, got {len(lines)}"
    assert "$" in result, "Should contain currency formatting"
    print(f"  ✓ Generated realistic sparkline with {len(lines)} lines")
    print("\nRealistic sparkline output (50 chars wide, 5 height):")
    for line in lines:
        print(f"    {line}")

    print("  All sparkline realistic tests passed!\n")


def test_calculate_cost_rate_mock():
    """Test cost rate calculation with mock session."""
    print("Testing calculate_cost_rate() with mock session...")

    # Create a temporary session for testing
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        session_file = Path(tmpdir) / "test_session.json"
        session = SessionManager(session_file)

        # Add some cost events
        base_time = datetime(2025, 12, 1, 10, 0, 0)

        for i in range(10):
            session.session_data["cost_timeline"].append(
                {
                    "timestamp": (base_time + timedelta(minutes=i * 6)).isoformat() + "Z",
                    "cost": 0.1 + i * 0.02,
                    "project": f"TEST_{i}",
                }
            )

        session._save()

        # Calculate rates
        rates = calculate_cost_rate(session)

        assert "per_minute" in rates, "Missing per_minute"
        assert "per_hour" in rates, "Missing per_hour"
        assert "avg_per_project" in rates, "Missing avg_per_project"
        assert rates["per_hour"] > rates["per_minute"], "per_hour should be > per_minute"

        print(f"  ✓ per_minute: ${rates['per_minute']:.6f}")
        print(f"  ✓ per_hour:   ${rates['per_hour']:.4f}")
        print(f"  ✓ avg_per_project: ${rates['avg_per_project']:.4f}")

    print("  All cost rate calculation tests passed!\n")


def test_calculate_cost_rate_empty():
    """Test cost rate calculation with empty session."""
    print("Testing calculate_cost_rate() with empty session...")

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        session_file = Path(tmpdir) / "empty_session.json"
        session = SessionManager(session_file)

        # Get rates from empty session
        rates = calculate_cost_rate(session)

        assert rates["per_minute"] == 0.0, "Empty should have 0 per_minute"
        assert rates["per_hour"] == 0.0, "Empty should have 0 per_hour"
        assert rates["avg_per_project"] == 0.0, "Empty should have 0 avg_per_project"

        print("  ✓ Empty session returns zero rates")

    print("  All empty cost rate tests passed!\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Cost Visualizer Test Suite")
    print("=" * 60)
    print()

    try:
        test_format_currency()
        test_get_bar_char()
        test_bucket_timeline_empty()
        test_bucket_timeline_distribution()
        test_format_time_labels_empty()
        test_format_time_labels_distribution()
        test_make_cost_sparkline_empty()
        test_make_cost_sparkline_simple()
        test_make_cost_sparkline_realistic()
        test_calculate_cost_rate_mock()
        test_calculate_cost_rate_empty()

        print("=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
