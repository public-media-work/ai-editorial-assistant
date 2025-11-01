#!/usr/bin/env python3
"""
Convert SRT subtitle files to SCC (Scenarist Closed Caption) format.
SCC is required by many broadcast systems including PBS Media Manager.
"""

import re
from datetime import timedelta


def srt_time_to_frames(time_str):
    """Convert SRT timestamp (HH:MM:SS,mmm) to frame number at 29.97 fps."""
    # Parse the timestamp
    match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', time_str)
    if not match:
        raise ValueError(f"Invalid SRT timestamp: {time_str}")

    hours, minutes, seconds, milliseconds = map(int, match.groups())

    # Convert to total seconds
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0

    # Convert to frames (29.97 non-drop frame)
    frames = int(round(total_seconds * 29.97))

    return frames


def frames_to_smpte(frames, fps=29.97):
    """Convert frame number to SMPTE timecode (HH:MM:SS:FF)."""
    total_seconds = frames / fps

    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    frame = frames % 30  # Approximate frame within second

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frame:02d}"


def text_to_scc_hex(text):
    """
    Convert text to SCC hex codes.
    This is a simplified conversion - full SCC encoding is complex.
    """
    # Clean the text
    text = text.strip()

    # SCC uses special hex codes for characters
    # This is a basic ASCII-to-hex conversion
    # Real SCC encoding requires EIA-608 character codes
    hex_codes = []

    for char in text:
        # Basic ASCII conversion (simplified)
        if char.isalnum() or char in ' .,!?-:;\'"':
            # Convert to hex pair (simplified EIA-608 approximation)
            hex_val = ord(char)
            hex_codes.append(f"{hex_val:02x}")

    return ' '.join(hex_codes)


def parse_srt(srt_content):
    """Parse SRT content into a list of subtitle entries."""
    entries = []
    blocks = srt_content.strip().split('\n\n')

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue

        # Parse sequence number
        try:
            seq_num = int(lines[0])
        except ValueError:
            continue

        # Parse timestamps
        time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
        if not time_match:
            continue

        start_time, end_time = time_match.groups()

        # Get text (may be multiple lines)
        text = '\n'.join(lines[2:])

        entries.append({
            'seq': seq_num,
            'start': start_time,
            'end': end_time,
            'text': text
        })

    return entries


def srt_to_scc(srt_file_path, scc_file_path):
    """Convert SRT file to SCC format."""

    # Read SRT file
    with open(srt_file_path, 'r', encoding='utf-8') as f:
        srt_content = f.read()

    # Parse SRT
    entries = parse_srt(srt_content)

    # Create SCC content
    scc_lines = []

    # SCC header
    scc_lines.append("Scenarist_SCC V1.0")
    scc_lines.append("")

    for entry in entries:
        # Convert start time to SMPTE timecode
        start_frames = srt_time_to_frames(entry['start'])
        timecode = frames_to_smpte(start_frames)

        # Clean and prepare text
        text = entry['text'].replace('\n', ' ')

        # Split text into manageable chunks (32 chars per line max for captions)
        lines = []
        current_line = ""
        words = text.split()

        for word in words:
            if len(current_line) + len(word) + 1 <= 32:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # Generate SCC hex codes (simplified)
        # Real SCC uses EIA-608 control codes - this is a basic approximation
        for line_text in lines:
            # SCC format: TIMECODE\tHEX_CODES
            # Using simplified hex representation
            scc_lines.append(f"{timecode}\t94ae 94ad 9420 {text_to_scc_hex(line_text)} 942c 942f")

    # Write SCC file
    with open(scc_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(scc_lines))

    print(f"Converted {len(entries)} captions from SRT to SCC")
    print(f"Output saved to: {scc_file_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python convert_to_scc.py <input.srt> <output.scc>")
        sys.exit(1)

    srt_file = sys.argv[1]
    scc_file = sys.argv[2]

    try:
        srt_to_scc(srt_file, scc_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
