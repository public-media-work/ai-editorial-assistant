"""SRT subtitle generator from PBS Wisconsin transcript format.

Converts transcripts with timing information (HH:MM:SS:FF - HH:MM:SS:FF format)
into properly formatted SRT subtitle files.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


@dataclass
class TranscriptCue:
    """Represents a single transcript cue with timing and dialogue."""
    start_frames: int
    end_frames: int
    speaker: str
    dialogue: str

    @property
    def duration_frames(self) -> int:
        return self.end_frames - self.start_frames


def parse_timecode(timecode: str, fps: int = 30) -> int:
    """Convert HH:MM:SS:FF timecode to frame count.

    Args:
        timecode: Timecode string in format HH:MM:SS:FF
        fps: Frames per second (default 30)

    Returns:
        Total frame count
    """
    parts = timecode.split(":")
    if len(parts) != 4:
        raise ValueError(f"Invalid timecode format: {timecode}")

    hours, minutes, seconds, frames = map(int, parts)
    total_frames = (hours * 3600 + minutes * 60 + seconds) * fps + frames
    return total_frames


def frames_to_srt_timecode(frames: int, fps: int = 30) -> str:
    """Convert frame count to SRT timecode format HH:MM:SS,mmm.

    Args:
        frames: Total frame count
        fps: Frames per second (default 30)

    Returns:
        SRT timecode string
    """
    milliseconds = int((frames * 1000) / fps)

    hours = milliseconds // 3600000
    milliseconds %= 3600000

    minutes = milliseconds // 60000
    milliseconds %= 60000

    seconds = milliseconds // 1000
    milliseconds %= 1000

    # Clamp milliseconds to prevent 1000+ values
    if milliseconds >= 1000:
        milliseconds = 999

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def parse_transcript(transcript_path: Path) -> List[TranscriptCue]:
    """Parse PBS Wisconsin transcript format into cues.

    Expected format:
    HH:MM:SS:FF - HH:MM:SS:FF
    SPEAKER NAME
    Dialogue line 1
    Dialogue line 2
    [blank line]

    Args:
        transcript_path: Path to transcript file

    Returns:
        List of TranscriptCue objects
    """
    content = transcript_path.read_text(encoding="utf-8")
    cues = []

    # Pattern: timecode range, speaker, then dialogue until blank line
    # Match: HH:MM:SS:FF - HH:MM:SS:FF
    timecode_pattern = re.compile(r"(\d{2}:\d{2}:\d{2}:\d{2})\s*-\s*(\d{2}:\d{2}:\d{2}:\d{2})")

    blocks = content.split("\n\n")

    for block in blocks:
        if not block.strip():
            continue

        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue

        # First line should have timecodes
        timecode_match = timecode_pattern.search(lines[0])
        if not timecode_match:
            continue

        start_tc, end_tc = timecode_match.groups()
        start_frames = parse_timecode(start_tc)
        end_frames = parse_timecode(end_tc)

        # Second line is speaker
        speaker = lines[1].strip().rstrip(":")

        # Remaining lines are dialogue
        dialogue_lines = [line.strip() for line in lines[2:] if line.strip()]
        dialogue = " ".join(dialogue_lines)

        # Collapse duplicate whitespace
        dialogue = re.sub(r"\s+", " ", dialogue).strip()

        if dialogue:
            cues.append(TranscriptCue(
                start_frames=start_frames,
                end_frames=end_frames,
                speaker=speaker,
                dialogue=dialogue
            ))

    return cues


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentence chunks for captions.

    Args:
        text: Full dialogue text

    Returns:
        List of sentence chunks (max ~110 chars each)
    """
    # Simple sentence boundary detection
    sentence_ends = re.compile(r"([.!?])\s+")
    sentences = sentence_ends.split(text)

    # Rejoin punctuation with preceding sentence
    chunks = []
    i = 0
    while i < len(sentences):
        if i + 1 < len(sentences) and sentences[i + 1] in ".!?":
            chunk = sentences[i] + sentences[i + 1]
            i += 2
        else:
            chunk = sentences[i]
            i += 1

        chunk = chunk.strip()
        if chunk:
            # If chunk is too long, split at natural breaks
            if len(chunk) > 110:
                words = chunk.split()
                current = []
                current_len = 0

                for word in words:
                    word_len = len(word) + 1  # +1 for space
                    if current_len + word_len > 110 and current:
                        chunks.append(" ".join(current))
                        current = [word]
                        current_len = word_len
                    else:
                        current.append(word)
                        current_len += word_len

                if current:
                    chunks.append(" ".join(current))
            else:
                chunks.append(chunk)

    return [c for c in chunks if c]


def wrap_caption_text(speaker: str, text: str, max_line_len: int = 42, max_lines: int = 3) -> str:
    """Wrap caption text with speaker name prefix.

    Args:
        speaker: Speaker name
        text: Caption text
        max_line_len: Maximum characters per line
        max_lines: Maximum number of lines

    Returns:
        Wrapped caption text with speaker prefix
    """
    # Prefix first line with speaker
    first_line = f"{speaker}: {text}"

    # Simple word wrapping
    words = text.split()
    lines = []
    current_line = []
    current_len = 0

    # First line includes speaker
    prefix = f"{speaker}: "
    prefix_len = len(prefix)

    for i, word in enumerate(words):
        word_len = len(word) + (1 if current_line else 0)  # +1 for space between words

        # First word of first line needs to account for speaker prefix
        if i == 0:
            effective_len = prefix_len + len(word)
        else:
            effective_len = current_len + word_len

        if effective_len > max_line_len and current_line:
            # Finalize current line
            if lines:
                lines.append(" ".join(current_line))
            else:
                lines.append(prefix + " ".join(current_line))

            current_line = [word]
            current_len = len(word)
        else:
            current_line.append(word)
            current_len += word_len

    # Add remaining words
    if current_line:
        if lines:
            lines.append(" ".join(current_line))
        else:
            lines.append(prefix + " ".join(current_line))

    # Limit to max_lines
    lines = lines[:max_lines]

    return "\n".join(lines)


def generate_srt_captions(cues: List[TranscriptCue], fps: int = 30, min_duration_ms: int = 750) -> str:
    """Generate SRT caption file from transcript cues.

    Args:
        cues: List of TranscriptCue objects
        fps: Frames per second
        min_duration_ms: Minimum caption duration in milliseconds

    Returns:
        Complete SRT file content
    """
    srt_lines = []
    caption_num = 1

    for cue in cues:
        # Split dialogue into chunks
        chunks = split_into_sentences(cue.dialogue)
        if not chunks:
            continue

        # Distribute duration across chunks
        total_duration_frames = cue.duration_frames
        frames_per_chunk = total_duration_frames // len(chunks)

        # Ensure minimum duration (convert ms to frames)
        min_frames = (min_duration_ms * fps) // 1000
        if frames_per_chunk < min_frames:
            frames_per_chunk = min_frames

        current_start = cue.start_frames

        for i, chunk in enumerate(chunks):
            # Calculate end time
            if i == len(chunks) - 1:
                # Last chunk gets remaining time
                current_end = cue.end_frames
            else:
                current_end = current_start + frames_per_chunk

            # Ensure monotonic timing
            if current_end <= current_start:
                current_end = current_start + min_frames

            # Generate SRT entry
            start_tc = frames_to_srt_timecode(current_start, fps)
            end_tc = frames_to_srt_timecode(current_end, fps)

            # Wrap text with speaker prefix
            caption_text = wrap_caption_text(cue.speaker, chunk)

            srt_lines.append(f"{caption_num}")
            srt_lines.append(f"{start_tc} --> {end_tc}")
            srt_lines.append(caption_text)
            srt_lines.append("")  # Blank line between entries

            caption_num += 1
            current_start = current_end

    return "\n".join(srt_lines)


def convert_transcript_to_srt(transcript_path: Path, output_path: Path, fps: int = 30) -> None:
    """Convert PBS Wisconsin transcript to SRT subtitle file.

    Args:
        transcript_path: Path to source transcript
        output_path: Path to output SRT file
        fps: Frames per second (default 30)
    """
    cues = parse_transcript(transcript_path)
    if not cues:
        raise ValueError(f"No valid cues found in transcript: {transcript_path}")

    srt_content = generate_srt_captions(cues, fps=fps)
    output_path.write_text(srt_content, encoding="utf-8")


if __name__ == "__main__":
    # Command-line interface for testing
    import argparse

    parser = argparse.ArgumentParser(description="Convert PBS Wisconsin transcript to SRT")
    parser.add_argument("transcript", type=Path, help="Input transcript file")
    parser.add_argument("output", type=Path, help="Output SRT file")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second (default: 30)")

    args = parser.parse_args()

    try:
        convert_transcript_to_srt(args.transcript, args.output, fps=args.fps)
        print(f"✓ Generated SRT: {args.output}")
    except Exception as e:
        print(f"✗ Error: {e}")
        exit(1)
