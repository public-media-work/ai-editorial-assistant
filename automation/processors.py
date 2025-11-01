"""Automation coordinator utilities for the editorial assistant workflow."""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, Optional

import yaml

LOGGER = logging.getLogger(__name__)

try:
    from anthropic import Anthropic
    from anthropic import APIError as AnthropicError
except ImportError:  # pragma: no cover - optional dependency
    Anthropic = None  # type: ignore
    AnthropicError = Exception  # type: ignore

try:
    from .srt_generator import convert_transcript_to_srt
except ImportError:  # pragma: no cover - optional utility
    convert_transcript_to_srt = None  # type: ignore


class CoordinatorError(RuntimeError):
    """Raised when orchestration cannot continue."""


class ArtifactType(Enum):
    DRAFT = "draft"
    SEMRUSH = "semrush"


@dataclass
class PromptPaths:
    brainstorm: Path
    formatted_transcript: Path
    timestamps: Path
    revision: Path
    keyword_report: Path
    implementation: Path


@dataclass
class PathConfig:
    transcripts: Path
    outputs: Path
    archive: Path
    prompts: PromptPaths


def _load_prompt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:  # pragma: no cover - configuration issue
        raise CoordinatorError(f"Prompt file not found: {path}") from exc


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


class ClaudeClient:
    def __init__(self, model: str, max_tokens: int, temperature: float) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise CoordinatorError("ANTHROPIC_API_KEY is not set")
        if Anthropic is None:
            raise CoordinatorError("anthropic package is not installed")
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def text_response(self, system_prompt: str, user_blocks) -> str:
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_blocks}],
            )
        except AnthropicError as exc:  # pragma: no cover - runtime issue
            raise CoordinatorError(f"Claude API error: {exc}") from exc
        return message.content[0].text


class AutomationCoordinator:
    def __init__(
        self,
        paths: PathConfig,
        model: str,
        max_tokens: int,
        temperature: float,
        patterns: Dict[str, str],
        retry_attempts: int = 3,
        retry_backoff_seconds: int = 10,
    ) -> None:
        self.paths = paths
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.patterns = patterns
        self.retry_attempts = retry_attempts
        self.retry_backoff_seconds = retry_backoff_seconds

    @classmethod
    def from_config(cls, config: Dict) -> "AutomationCoordinator":
        paths = PathConfig(
            transcripts=Path(config["paths"]["transcripts"]).resolve(),
            outputs=Path(config["paths"]["outputs"]).resolve(),
            archive=Path(config["paths"]["archive"]).resolve(),
            prompts=PromptPaths(
                brainstorm=Path(config["paths"]["prompts"]["brainstorm"]).resolve(),
                formatted_transcript=Path(config["paths"]["prompts"]["formatted_transcript"]).resolve(),
                timestamps=Path(config["paths"]["prompts"]["timestamps"]).resolve(),
                revision=Path(config["paths"]["prompts"]["revision"]).resolve(),
                keyword_report=Path(config["paths"]["prompts"]["keyword_report"]).resolve(),
                implementation=Path(config["paths"]["prompts"]["implementation"]).resolve(),
            ),
        )
        watcher_config = config.get("watcher", {})
        patterns = config.get("patterns", {})
        return cls(
            paths=paths,
            model=config.get("model", "claude-3-5-sonnet-20241022"),
            max_tokens=int(config.get("max_tokens", 4000)),
            temperature=float(config.get("temperature", 0.7)),
            patterns={
                "transcript": patterns.get("transcript", "*_ForClaude.txt"),
                "draft": patterns.get("draft", "*"),
                "semrush": patterns.get("semrush", "*"),
            },
            retry_attempts=int(watcher_config.get("retry_attempts", 3)),
            retry_backoff_seconds=int(watcher_config.get("retry_backoff_seconds", 10)),
        )

    # -----------------
    # Transcript events
    # -----------------

    def is_transcript(self, path: Path) -> bool:
        return path.match(self.patterns["transcript"])

    def extract_media_id(self, path: Path) -> str:
        """Extract media ID from transcript filename.

        Handles standard format: [PREFIX][NUMBER][FORMAT]_ForClaude.txt
        Also handles non-standard formats gracefully by using the full stem.
        """
        stem = path.stem
        if stem.endswith("_ForClaude"):
            stem = stem[: -len("_ForClaude")]

        # Try to extract first segment as media ID (standard format)
        # If it looks like a proper media ID pattern, use it
        first_segment = stem.split("_", 1)[0]
        if first_segment:
            return first_segment

        # Fallback: use entire stem as media ID for non-standard names
        return stem if stem else path.stem

    def estimate_transcript_duration(self, transcript_text: str) -> float:
        """Estimate transcript duration in seconds based on word count.

        Uses average speaking rate of ~150 words per minute.
        Returns estimated duration in seconds.
        """
        words = len(transcript_text.split())
        words_per_minute = 150
        minutes = words / words_per_minute
        return minutes * 60

    def is_shortform_content(self, transcript_text: str, threshold_seconds: float = 90) -> bool:
        """Determine if transcript represents shortform content (< 90 seconds).

        Args:
            transcript_text: The transcript content to analyze
            threshold_seconds: Duration threshold in seconds (default: 90)

        Returns:
            True if estimated duration is less than threshold
        """
        duration = self.estimate_transcript_duration(transcript_text)
        LOGGER.debug(f"Estimated transcript duration: {duration:.1f} seconds")
        return duration < threshold_seconds

    def handle_transcript(self, transcript_path: Path) -> None:
        media_id = self.extract_media_id(transcript_path)
        if not media_id:
            raise CoordinatorError(f"Unable to derive media ID from {transcript_path.name}")

        project_dir = self._ensure_project_structure(media_id)
        runlog = self._load_runlog(project_dir)
        runlog.setdefault("media_id", media_id)
        runlog["transcript"] = str(transcript_path)

        # Read transcript and determine content type
        transcript_text = transcript_path.read_text(encoding="utf-8")
        is_shortform = self.is_shortform_content(transcript_text)

        runlog.setdefault("events", []).append({
            "event": "transcript_detected",
            "path": str(transcript_path),
            "content_type": "shortform" if is_shortform else "standard",
            "estimated_duration_seconds": self.estimate_transcript_duration(transcript_text),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self._write_runlog(project_dir, runlog)

        client = self._client()

        if is_shortform:
            LOGGER.info(f"Detected shortform content (< 90 seconds): {transcript_path.name}")
            # For shortform: only generate brainstorming (no formatted transcript or timestamps)
            outputs = {
                "brainstorm": project_dir / "01_brainstorming.md",
            }
            prompts = {
                "brainstorm": _load_prompt(self.paths.prompts.brainstorm),
            }
        else:
            LOGGER.info(f"Detected standard content: {transcript_path.name}")
            # For standard content: generate all three outputs
            outputs = {
                "brainstorm": project_dir / "01_brainstorming.md",
                "formatted": project_dir / "05_formatted_transcript.md",
                "timestamps": project_dir / "06_timestamp_report.md",
            }
            prompts = {
                "brainstorm": _load_prompt(self.paths.prompts.brainstorm),
                "formatted": _load_prompt(self.paths.prompts.formatted_transcript),
                "timestamps": _load_prompt(self.paths.prompts.timestamps),
            }

        for key, prompt in prompts.items():
            user_blocks = [
                {
                    "type": "text",
                    "text": f"Media ID: {media_id}\nTranscript path: {transcript_path}\n\nTranscript:\n{transcript_text}",
                }
            ]
            content = self._run_with_retry(lambda: client.text_response(prompt, user_blocks))
            outputs[key].write_text(content, encoding="utf-8")
            self._append_phase_event(project_dir, key, outputs[key])

        # Only try to generate SRT subtitles for standard content with timing info
        if not is_shortform:
            self._try_generate_srt(transcript_path, project_dir)

    # -----------------
    # Artifact events
    # -----------------

    def classify_project_artifact(self, path: Path) -> Optional[ArtifactType]:
        try:
            rel = path.relative_to(self.paths.outputs)
        except ValueError:
            raise CoordinatorError("Path is outside outputs directory")
        if rel.parts[0] == "archive":
            return None
        if len(rel.parts) < 2:
            return None
        section = rel.parts[1]
        name = path.name
        if section == "drafts":
            if fnmatch(name, self.patterns["draft"]):
                return ArtifactType.DRAFT
            return None
        if section.lower() == "semrush":
            # Support case-insensitive matching for common image formats
            name_lower = name.lower()
            if name_lower.endswith(('.png', '.jpg', '.jpeg')):
                return ArtifactType.SEMRUSH
            return None
        return None

    def handle_project_artifact(self, path: Path, artifact: ArtifactType) -> None:
        media_id = path.relative_to(self.paths.outputs).parts[0]
        project_dir = self._ensure_project_structure(media_id)
        runlog = self._load_runlog(project_dir)
        runlog.setdefault("media_id", media_id)
        runlog.setdefault("artifacts", []).append({
            "event": f"{artifact.value}_artifact",
            "path": str(path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self._write_runlog(project_dir, runlog)

        client = self._client()
        transcript_path = Path(runlog.get("transcript", ""))
        if not transcript_path.exists():
            transcript_path = self._locate_transcript(media_id)
        transcript_text = transcript_path.read_text(encoding="utf-8")

        if artifact is ArtifactType.DRAFT:
            output_path = project_dir / "02_copy_revision.md"
            prompt = _load_prompt(self.paths.prompts.revision)
            user_blocks = self._draft_blocks(transcript_text, path)
            content = self._run_with_retry(lambda: client.text_response(prompt, user_blocks))
            output_path.write_text(content, encoding="utf-8")
            self._append_phase_event(project_dir, "revision", output_path)
        elif artifact is ArtifactType.SEMRUSH:
            # Generate keyword report
            keyword_prompt = _load_prompt(self.paths.prompts.keyword_report)
            report_path = project_dir / "03_keyword_report.md"
            user_blocks = self._semrush_blocks(transcript_text, path)
            keyword_content = self._run_with_retry(lambda: client.text_response(keyword_prompt, user_blocks))
            report_path.write_text(keyword_content, encoding="utf-8")
            self._append_phase_event(project_dir, "keyword_report", report_path)

            # Generate implementation report using keyword report as input
            impl_prompt = _load_prompt(self.paths.prompts.implementation)
            impl_path = project_dir / "04_implementation.md"
            impl_user_blocks = self._implementation_blocks(transcript_text, path, keyword_content, project_dir)
            impl_content = self._run_with_retry(lambda: client.text_response(impl_prompt, impl_user_blocks))
            impl_path.write_text(impl_content, encoding="utf-8")
            self._append_phase_event(project_dir, "implementation", impl_path)

    # -----------------
    # Helpers
    # -----------------

    def _client(self) -> ClaudeClient:
        return ClaudeClient(self.model, self.max_tokens, self.temperature)

    def _ensure_project_structure(self, media_id: str) -> Path:
        project_dir = self.paths.outputs / media_id
        _ensure_dir(project_dir)
        _ensure_dir(project_dir / "drafts")
        _ensure_dir(project_dir / "semrush")
        return project_dir

    def _load_runlog(self, project_dir: Path) -> Dict:
        runlog_path = project_dir / "workflow.json"
        if not runlog_path.exists():
            return {}
        return json.loads(runlog_path.read_text(encoding="utf-8"))

    def _write_runlog(self, project_dir: Path, data: Dict) -> None:
        runlog_path = project_dir / "workflow.json"
        runlog_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def _append_phase_event(self, project_dir: Path, phase: str, output_path: Path) -> None:
        data = self._load_runlog(project_dir)
        phases = data.setdefault("phases", {})
        phases[phase] = {
            "status": "complete",
            "output": str(output_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._write_runlog(project_dir, data)

    def _run_with_retry(self, func):
        attempt = 0
        while True:
            attempt += 1
            try:
                return func()
            except CoordinatorError:
                if attempt >= self.retry_attempts:
                    raise
                time.sleep(self.retry_backoff_seconds)

    def _draft_blocks(self, transcript_text: str, artifact_path: Path):
        blocks = [
            {
                "type": "text",
                "text": "Transcript:\n\n" + transcript_text,
            }
        ]
        if artifact_path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            blocks.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png" if artifact_path.suffix.lower() == ".png" else "image/jpeg",
                        "data": base64.b64encode(artifact_path.read_bytes()).decode("utf-8"),
                    },
                }
            )
        else:
            blocks.append(
                {
                    "type": "text",
                    "text": "Draft copy:\n\n" + artifact_path.read_text(encoding="utf-8"),
                }
            )
        return blocks

    def _semrush_blocks(self, transcript_text: str, artifact_path: Path):
        blocks = [
            {
                "type": "text",
                "text": "Transcript:\n\n" + transcript_text,
            }
        ]
        blocks.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png" if artifact_path.suffix.lower() == ".png" else "image/jpeg",
                    "data": base64.b64encode(artifact_path.read_bytes()).decode("utf-8"),
                },
            }
        )
        return blocks

    def _implementation_blocks(self, transcript_text: str, semrush_path: Path, keyword_report_content: str, project_dir: Path):
        blocks = [
            {
                "type": "text",
                "text": "Transcript:\n\n" + transcript_text,
            },
            {
                "type": "text",
                "text": "\n\nKeyword Report:\n\n" + keyword_report_content,
            }
        ]

        # Include brainstorming document if available
        brainstorm_path = project_dir / "01_brainstorming.md"
        if brainstorm_path.exists():
            blocks.append({
                "type": "text",
                "text": "\n\nBrainstorming Document:\n\n" + brainstorm_path.read_text(encoding="utf-8"),
            })

        # Include copy revision if available
        revision_path = project_dir / "02_copy_revision.md"
        if revision_path.exists():
            blocks.append({
                "type": "text",
                "text": "\n\nCopy Revision Document:\n\n" + revision_path.read_text(encoding="utf-8"),
            })

        return blocks

    def _locate_transcript(self, media_id: str) -> Path:
        for path in self.paths.transcripts.glob(f"{media_id}*_ForClaude.txt"):
            return path
        archive_dir = self.paths.transcripts / "archive"
        if archive_dir.exists():
            for path in archive_dir.glob(f"{media_id}*_ForClaude.txt"):
                return path
        raise CoordinatorError(f"Transcript not found for {media_id}")

    def _try_generate_srt(self, transcript_path: Path, project_dir: Path) -> None:
        """Attempt to generate SRT subtitles from transcript if timing info present."""
        if convert_transcript_to_srt is None:
            LOGGER.debug("SRT generator not available, skipping subtitle generation")
            return

        # Check if transcript has timing information (HH:MM:SS:FF format)
        content = transcript_path.read_text(encoding="utf-8")
        if not re.search(r"\d{2}:\d{2}:\d{2}:\d{2}", content):
            LOGGER.debug("No timing information in transcript, skipping SRT generation")
            return

        srt_path = project_dir / "07_subtitles.srt"
        try:
            convert_transcript_to_srt(transcript_path, srt_path, fps=30)
            LOGGER.info("Generated SRT subtitles: %s", srt_path)
            self._append_phase_event(project_dir, "subtitles", srt_path)
        except Exception as exc:
            LOGGER.warning("Failed to generate SRT subtitles: %s", exc)


def load_config(path: Path) -> Dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def archive_project(project_dir: Path, archive_root: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    destination = archive_root / f"{project_dir.name}_{timestamp}"
    _ensure_dir(destination.parent)
    shutil.move(str(project_dir), destination)
    return destination
