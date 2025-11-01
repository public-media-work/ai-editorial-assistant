#!/usr/bin/env python3
"""Simple integration test for automation system.

Tests that configuration loads properly and key components are available.
Does NOT test actual Claude API calls (which require API key and credits).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add automation directory to path
sys.path.insert(0, str(Path(__file__).parent))

from processors import (
    AutomationCoordinator,
    load_config,
    CoordinatorError,
    ArtifactType,
)


def test_config_loading():
    """Test that configuration file loads correctly."""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        print(f"✗ Config file not found: {config_path}")
        return False

    try:
        config = load_config(config_path)
        print(f"✓ Config loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return False


def test_coordinator_creation():
    """Test that AutomationCoordinator can be created from config."""
    config_path = Path(__file__).parent / "config.yaml"
    try:
        config = load_config(config_path)
        coordinator = AutomationCoordinator.from_config(config)
        print(f"✓ AutomationCoordinator created successfully")
        print(f"  - Model: {coordinator.model}")
        print(f"  - Max tokens: {coordinator.max_tokens}")
        print(f"  - Temperature: {coordinator.temperature}")
        return True
    except Exception as e:
        print(f"✗ Failed to create coordinator: {e}")
        return False


def test_prompt_files():
    """Test that all configured prompt files exist."""
    config_path = Path(__file__).parent / "config.yaml"
    config = load_config(config_path)

    prompt_paths = config.get("paths", {}).get("prompts", {})
    all_exist = True

    for key, rel_path in prompt_paths.items():
        abs_path = (Path(__file__).parent.parent / rel_path).resolve()
        if abs_path.exists():
            print(f"✓ Prompt file exists: {key} ({rel_path})")
        else:
            print(f"✗ Prompt file missing: {key} ({rel_path})")
            all_exist = False

    return all_exist


def test_transcript_pattern():
    """Test transcript filename pattern matching."""
    config_path = Path(__file__).parent / "config.yaml"
    config = load_config(config_path)
    coordinator = AutomationCoordinator.from_config(config)

    test_cases = [
        ("2WLI1203HD_ForClaude.txt", True, "2WLI1203HD"),
        ("9UNP1972HD_REV20250804_ForClaude.txt", True, "9UNP1972HD"),
        ("6HNS_ForClaude.txt", True, "6HNS"),
        ("random_file.txt", False, None),
        ("test.md", False, None),
    ]

    all_passed = True
    for filename, should_match, expected_media_id in test_cases:
        path = Path(filename)
        is_transcript = coordinator.is_transcript(path)

        if is_transcript != should_match:
            print(f"✗ Pattern match failed for {filename}: expected {should_match}, got {is_transcript}")
            all_passed = False
            continue

        if is_transcript:
            media_id = coordinator.extract_media_id(path)
            if media_id != expected_media_id:
                print(f"✗ Media ID extraction failed for {filename}: expected {expected_media_id}, got {media_id}")
                all_passed = False
            else:
                print(f"✓ Transcript pattern matched: {filename} → {media_id}")

    return all_passed


def test_artifact_classification():
    """Test artifact classification logic."""
    config_path = Path(__file__).parent / "config.yaml"
    config = load_config(config_path)
    coordinator = AutomationCoordinator.from_config(config)

    test_cases = [
        ("output/2WLI1203HD/drafts/2WLI1203HD_20240212_draft.png", ArtifactType.DRAFT),
        ("output/2WLI1203HD/semrush/2WLI1203HD_20240212_semrush.png", ArtifactType.SEMRUSH),
        ("output/2WLI1203HD/01_brainstorming.md", None),
        ("output/archive/2WLI1203HD/drafts/old_draft.png", None),
    ]

    all_passed = True
    for path_str, expected_type in test_cases:
        path = Path(__file__).parent.parent / path_str
        try:
            artifact_type = coordinator.classify_project_artifact(path)
            if artifact_type != expected_type:
                print(f"✗ Classification failed for {path_str}: expected {expected_type}, got {artifact_type}")
                all_passed = False
            else:
                print(f"✓ Artifact classified correctly: {path_str} → {expected_type}")
        except CoordinatorError:
            if expected_type is not None:
                print(f"✗ Classification raised error for {path_str}")
                all_passed = False
            else:
                print(f"✓ Artifact correctly rejected: {path_str}")

    return all_passed


def test_srt_generator():
    """Test that SRT generator is available and works."""
    try:
        from srt_generator import convert_transcript_to_srt, parse_transcript
        print(f"✓ SRT generator module imported successfully")

        # Test with actual transcript if available
        transcript_path = Path(__file__).parent.parent / "transcripts" / "New Tech Times 101.txt"
        if transcript_path.exists():
            try:
                cues = parse_transcript(transcript_path)
                if cues:
                    print(f"✓ SRT generator parsed transcript: {len(cues)} cues found")
                    return True
                else:
                    print(f"✗ No cues parsed from transcript")
                    return False
            except Exception as e:
                print(f"✗ SRT generation failed: {e}")
                return False
        else:
            print(f"  (No test transcript available for full test)")
            return True

    except ImportError as e:
        print(f"✗ SRT generator not available: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Automation System Integration Tests")
    print("=" * 60)
    print()

    tests = [
        ("Config Loading", test_config_loading),
        ("Coordinator Creation", test_coordinator_creation),
        ("Prompt Files", test_prompt_files),
        ("Transcript Pattern Matching", test_transcript_pattern),
        ("Artifact Classification", test_artifact_classification),
        ("SRT Generator", test_srt_generator),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"✗ Test crashed: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Total: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
