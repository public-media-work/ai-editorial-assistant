"""File watcher that orchestrates project automation.

Requires watchdog and anthropic packages.
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import yaml
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from .processors import (
    AutomationCoordinator,
    ArtifactType,
    CoordinatorError,
)

LOGGER = logging.getLogger(__name__)


def _should_ignore(event: FileSystemEvent) -> bool:
    path = Path(event.src_path)
    if path.name.startswith('.'):
        return True
    if path.name.endswith('~'):
        return True
    if path.suffix in {'.tmp', '.swp'}:
        return True
    return False


class TranscriptHandler(FileSystemEventHandler):
    def __init__(self, coordinator: AutomationCoordinator, debounce: float) -> None:
        super().__init__()
        self.coordinator = coordinator
        self.debounce = debounce

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory or _should_ignore(event):
            return
        time.sleep(self.debounce)
        path = Path(event.src_path)
        if self.coordinator.is_transcript(path):
            LOGGER.info("Detected transcript %s", path)
            try:
                self.coordinator.handle_transcript(path)
            except CoordinatorError as exc:
                LOGGER.exception("Failed to process transcript %s: %s", path, exc)


class ProjectHandler(FileSystemEventHandler):
    def __init__(self, coordinator: AutomationCoordinator, debounce: float) -> None:
        super().__init__()
        self.coordinator = coordinator
        self.debounce = debounce

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory or _should_ignore(event):
            return
        time.sleep(self.debounce)
        path = Path(event.src_path)
        try:
            artifact = self.coordinator.classify_project_artifact(path)
        except CoordinatorError:
            return
        if artifact is None:
            return
        LOGGER.info("Detected %s artifact: %s", artifact.value, path)
        try:
            self.coordinator.handle_project_artifact(path, artifact)
        except CoordinatorError as exc:
            LOGGER.exception("Failed to process artifact %s: %s", path, exc)


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run editorial-assistant automation watcher")
    parser.add_argument("--config", default="automation/config.yaml", help="Path to YAML config file")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    configure_logging(args.verbose)
    config_path = Path(args.config)
    with config_path.open() as fh:
        config = yaml.safe_load(fh)

    coordinator = AutomationCoordinator.from_config(config)
    debounce = config.get("watcher", {}).get("debounce_seconds", 2)

    observer = Observer()
    observer.schedule(
        TranscriptHandler(coordinator, debounce),
        str(coordinator.paths.transcripts),
        recursive=False,
    )
    observer.schedule(
        ProjectHandler(coordinator, debounce),
        str(coordinator.paths.outputs),
        recursive=True,
    )

    LOGGER.info("Automation watcher running. Monitoring transcripts and project folders.")
    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        LOGGER.info("Stopping watcher…")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
