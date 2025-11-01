"""Archive stale projects and transcripts.

Run via cron/launchd to move work older than the configured threshold
into archive folders. Requires the configuration used by the watcher.
"""
from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

from .processors import load_config, AutomationCoordinator, archive_project


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Archive stale editorial assistant projects")
    parser.add_argument("--config", default="automation/config.yaml", help="Path to watcher YAML config")
    parser.add_argument("--dry-run", action="store_true", help="Log actions without modifying the filesystem")
    return parser.parse_args()


def project_last_modified(path: Path) -> datetime:
    latest = path.stat().st_mtime
    for child in path.rglob("*"):
        try:
            latest = max(latest, child.stat().st_mtime)
        except FileNotFoundError:
            continue
    return datetime.fromtimestamp(latest, tz=timezone.utc)


def move_transcripts(media_id: str, coordinator: AutomationCoordinator, dry_run: bool, transcript_archive: Path) -> None:
    transcript_srcs = list((coordinator.paths.transcripts).glob(f"{media_id}*_ForClaude.txt"))
    transcript_srcs += list((coordinator.paths.transcripts / "archive").glob(f"{media_id}*_ForClaude.txt")) if (coordinator.paths.transcripts / "archive").exists() else []
    for src in transcript_srcs:
        dest = transcript_archive / src.name
        if dry_run:
            print(f"[dry-run] mv {src} -> {dest}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), dest)


def archive_stale_projects(config: Dict, dry_run: bool) -> None:
    coordinator = AutomationCoordinator.from_config(config)
    archive_cfg = config.get("archive", {})
    days_to_keep = int(archive_cfg.get("days_to_keep", 90))
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

    coordinator.paths.archive.mkdir(parents=True, exist_ok=True)
    transcript_archive = coordinator.paths.transcripts / "archive"
    transcript_archive.mkdir(parents=True, exist_ok=True)

    for project_dir in coordinator.paths.outputs.iterdir():
        if project_dir.name == "archive" or not project_dir.is_dir():
            continue
        last_modified = project_last_modified(project_dir)
        if last_modified >= cutoff:
            continue
        media_id = project_dir.name
        if dry_run:
            print(f"[dry-run] archive project {media_id} from {project_dir}")
        else:
            destination = archive_project(project_dir, coordinator.paths.archive)
            print(f"Archived {media_id} -> {destination}")
        if archive_cfg.get("include_transcripts", True):
            move_transcripts(media_id, coordinator, dry_run, transcript_archive)


def main() -> None:
    args = parse_args()
    config = load_config(Path(args.config))
    archive_stale_projects(config, args.dry_run)


if __name__ == "__main__":
    main()
