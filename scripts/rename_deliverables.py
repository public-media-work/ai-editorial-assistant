#!/usr/bin/env python3
"""
Rename deliverable files so they are prefixed with the project id
(e.g., `formatted_transcript.md` -> `9UNP1995HD_formatted_transcript.md`)
and update manifest.json references accordingly.

Usage:
  python scripts/rename_deliverables.py          # dry run
  python scripts/rename_deliverables.py --apply  # perform renames
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"

EXCLUDED_DIRS = {"archive", "examples"}
EXCLUDED_FILES = {
    "manifest.json",
    "processing.log.jsonl",
    ".state.json",
    "workflow.json",
    ".DS_Store",
}


@dataclass
class RenameAction:
    project: str
    old_name: str
    new_name: str
    skipped: bool = False
    reason: str | None = None


def replace_manifest_filenames(data: Any, rename_pairs: Dict[str, str]) -> Any:
    """Recursively replace manifest filenames that match rename pairs."""
    if isinstance(data, dict):
        return {k: replace_manifest_filenames(v, rename_pairs) for k, v in data.items()}
    if isinstance(data, list):
        return [replace_manifest_filenames(item, rename_pairs) for item in data]
    if isinstance(data, str) and data in rename_pairs:
        return rename_pairs[data]
    return data


def collect_project_dirs() -> List[Path]:
    if not OUTPUT_DIR.exists():
        return []
    return [
        p
        for p in OUTPUT_DIR.iterdir()
        if p.is_dir() and p.name not in EXCLUDED_DIRS
    ]


def plan_renames(project_dir: Path) -> Tuple[List[RenameAction], Dict[str, str]]:
    project_id = project_dir.name
    actions: List[RenameAction] = []
    mapping: Dict[str, str] = {}

    for file_path in project_dir.iterdir():
        if not file_path.is_file():
            continue
        if file_path.name in EXCLUDED_FILES:
            continue
        if file_path.name.startswith(f"{project_id}_"):
            continue

        new_name = f"{project_id}_{file_path.name}"
        target_path = project_dir / new_name
        if target_path.exists():
            actions.append(
                RenameAction(
                    project=project_id,
                    old_name=file_path.name,
                    new_name=new_name,
                    skipped=True,
                    reason="target exists",
                )
            )
            continue

        actions.append(RenameAction(project=project_id, old_name=file_path.name, new_name=new_name))
        mapping[file_path.name] = new_name

    return actions, mapping


def apply_renames(actions: List[RenameAction], project_dir: Path) -> None:
    for action in actions:
        if action.skipped:
            continue
        src = project_dir / action.old_name
        dst = project_dir / action.new_name
        src.rename(dst)


def update_manifest(project_dir: Path, mapping: Dict[str, str]) -> bool:
    manifest_path = project_dir / "manifest.json"
    if not manifest_path.exists() or not mapping:
        return False

    with manifest_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    updated = replace_manifest_filenames(data, mapping)
    if updated != data:
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(updated, f, indent=2, ensure_ascii=False)
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Prefix deliverables with project id and update manifests.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Perform renames. Without this flag, a dry run is shown.",
    )
    args = parser.parse_args()

    projects = collect_project_dirs()
    if not projects:
        print("No output projects found.")
        return

    all_actions: List[RenameAction] = []
    for project_dir in projects:
        actions, mapping = plan_renames(project_dir)
        if args.apply and actions:
            apply_renames(actions, project_dir)
            manifest_changed = update_manifest(project_dir, mapping)
        else:
            manifest_changed = False
        all_actions.extend(actions)
        if manifest_changed:
            print(f"[{project_dir.name}] manifest updated")

    if not all_actions:
        print("No files need renaming.")
        return

    print("Planned renames:")
    for action in all_actions:
        status = "SKIP" if action.skipped else ("RENAMED" if args.apply else "DRY-RUN")
        reason = f" ({action.reason})" if action.reason else ""
        print(f"[{status}] {action.project}: {action.old_name} -> {action.new_name}{reason}")


if __name__ == "__main__":
    main()
