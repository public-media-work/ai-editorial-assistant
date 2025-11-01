#!/usr/bin/env python3
"""Convert New Tech Times transcript to SRT format"""

import re

def timecode_to_srt(timecode):
    """Convert HH:MM:SS:FF to SRT format HH:MM:SS,mmm"""
    # Input format: 00:00:53:27 (hours:minutes:seconds:frames at 30fps)
    parts = timecode.split(':')
    hours = parts[0]
    minutes = parts[1]
    seconds = parts[2]
    frames = int(parts[3])

    # Convert frames to milliseconds (assuming 30fps)
    milliseconds = int((frames / 30.0) * 1000)

    return f"{hours}:{minutes}:{seconds},{milliseconds:03d}"

def parse_transcript(input_file):
    """Parse the transcript file and extract subtitle entries"""
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    subtitles = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Look for timecode lines
        if re.match(r'\d{2}:\d{2}:\d{2}:\d{2} - \d{2}:\d{2}:\d{2}:\d{2}', line):
            timecodes = line.split(' - ')
            start_time = timecode_to_srt(timecodes[0])
            end_time = timecode_to_srt(timecodes[1])

            # Get speaker (next line)
            i += 1
            if i < len(lines):
                speaker = lines[i].strip()
            else:
                break

            # Get text (next line)
            i += 1
            if i < len(lines):
                text = lines[i].strip()

                # Skip very short non-substantive entries
                if text and text != "To." and len(text) > 1:
                    # Add speaker name in italics if not Narrator
                    if speaker and speaker not in ['Narrator', 'Announcer', 'Exercise Instructor', "Dragon's Lair Character"]:
                        full_text = f"<i>{speaker}:</i> {text}"
                    else:
                        full_text = text

                    subtitles.append({
                        'start': start_time,
                        'end': end_time,
                        'text': full_text
                    })

        i += 1

    return subtitles

def write_srt(subtitles, output_file):
    """Write subtitles to SRT file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for idx, sub in enumerate(subtitles, 1):
            f.write(f"{idx}\n")
            f.write(f"{sub['start']} --> {sub['end']}\n")
            f.write(f"{sub['text']}\n")
            f.write("\n")

def main():
    input_file = 'transcripts/New Tech Times 101.txt'
    output_file = 'output/New Tech Times 101/New_Tech_Times_101.srt'

    print("Parsing transcript...")
    subtitles = parse_transcript(input_file)

    print(f"Found {len(subtitles)} subtitle entries")
    print("Writing SRT file...")
    write_srt(subtitles, output_file)

    print(f"SRT file created: {output_file}")

if __name__ == '__main__':
    main()
