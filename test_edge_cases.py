#!/usr/bin/env python3
"""Quick test script for edge case handling in automation coordinator."""
from pathlib import Path
from automation.processors import AutomationCoordinator


def test_shortform_detection():
    """Test shortform content detection based on word count."""
    print("Testing shortform detection...")

    # Create minimal config
    config = {
        "paths": {
            "transcripts": "transcripts",
            "outputs": "output",
            "archive": "transcripts/archive",
            "prompts": {
                "brainstorm": "system_prompts/phase1_brainstorming.md",
                "formatted_transcript": "system_prompts/phase4_transcript.md",
                "timestamps": "system_prompts/phase4_timestamps.md",
                "revision": "system_prompts/phase2_revision.md",
                "keyword_report": "system_prompts/phase3_keywords.md",
                "implementation": "system_prompts/phase3_implementation.md",
            }
        }
    }

    coordinator = AutomationCoordinator.from_config(config)

    # Test shortform (< 90 seconds at 150 wpm = < 225 words)
    short_text = " ".join(["word"] * 200)  # 200 words ≈ 80 seconds
    assert coordinator.is_shortform_content(short_text), "Should detect as shortform"
    duration = coordinator.estimate_transcript_duration(short_text)
    print(f"  ✓ Short content (200 words): {duration:.1f}s - Detected as shortform")

    # Test standard content (> 90 seconds)
    long_text = " ".join(["word"] * 300)  # 300 words ≈ 120 seconds
    assert not coordinator.is_shortform_content(long_text), "Should detect as standard"
    duration = coordinator.estimate_transcript_duration(long_text)
    print(f"  ✓ Long content (300 words): {duration:.1f}s - Detected as standard")

    print()


def test_media_id_extraction():
    """Test Media ID extraction from various filename formats."""
    print("Testing Media ID extraction...")

    config = {
        "paths": {
            "transcripts": "transcripts",
            "outputs": "output",
            "archive": "transcripts/archive",
            "prompts": {
                "brainstorm": "system_prompts/phase1_brainstorming.md",
                "formatted_transcript": "system_prompts/phase4_transcript.md",
                "timestamps": "system_prompts/phase4_timestamps.md",
                "revision": "system_prompts/phase2_revision.md",
                "keyword_report": "system_prompts/phase3_keywords.md",
                "implementation": "system_prompts/phase3_implementation.md",
            }
        }
    }

    coordinator = AutomationCoordinator.from_config(config)

    test_cases = [
        # (filename, expected_media_id)
        ("2WLI1203HD_ForClaude.txt", "2WLI1203HD"),
        ("6HNS_ForClaude.txt", "6HNS"),
        ("9UNP1972HD_REV20250804_ForClaude.txt", "9UNP1972HD"),
        ("test_video_ForClaude.txt", "test"),
        ("shortform_ForClaude.txt", "shortform"),
        ("single_ForClaude.txt", "single"),
    ]

    for filename, expected in test_cases:
        path = Path(filename)
        media_id = coordinator.extract_media_id(path)
        status = "✓" if media_id == expected else "✗"
        print(f"  {status} {filename} → Media ID: {media_id} (expected: {expected})")
        if media_id != expected:
            print(f"     ERROR: Got '{media_id}', expected '{expected}'")

    print()


def main():
    """Run all edge case tests."""
    print("=" * 60)
    print("Edge Case Testing for Editorial Assistant Automation")
    print("=" * 60)
    print()

    try:
        test_shortform_detection()
        test_media_id_extraction()

        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
