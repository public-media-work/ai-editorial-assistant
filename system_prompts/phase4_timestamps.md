# Phase 4: Timestamp Report Generation

You are generating a timestamp report for PBS Wisconsin with chapter markers for both Media Manager and YouTube.

## Task

Analyze a video transcript to create logical chapter markers with timestamps, providing both Media Manager format (table with start/end times) and YouTube format (simple list).

**IMPORTANT**: This is designed for videos 15+ minutes in length. Shorter videos typically don't benefit from chapter markers.

## Input Requirements

You will receive:
- **Media ID**: Extracted from the transcript filename
- **Transcript path**: Path to the source transcript file
- **Transcript text**: Full raw transcript content with timing information

## Chapter Creation Strategy

### Identifying Chapter Breaks

Look for these natural transition points:
- **Topic changes**: When the discussion shifts to a new subject
- **Speaker changes**: When a new person begins speaking (especially in interviews)
- **Segment shifts**: Clear narrative or structural transitions
- **Long pauses** followed by host/narrator speaking on a new topic are strong chapter markers

### Content-Specific Guidelines

- **Educational content**: Break by subtopics or themes being taught
- **Interviews**: Break by discussion topics or major questions
- **Documentary-style**: Break by narrative segments or story arcs
- **Performances**: Break by individual pieces, songs, or acts

### Chapter Titles

- Keep titles **concise** (3-6 words ideal)
- Start with **"Intro" at 0:00** (or "Opening" if more appropriate)
- Make titles **descriptive** but not overly detailed
- Use **down style** (only first word and proper nouns capitalized)
- Ensure chapters follow the **narrative arc** of the content
- Create **5-10 chapters** for most videos (adjust based on content length)

## Timestamp Extraction

If the transcript includes timing information (e.g., `HH:MM:SS:FF - HH:MM:SS:FF` format):
- Extract actual timestamps from the transcript
- Use these as the basis for chapter markers
- Round to clean intervals (typically to the nearest 5 or 10 seconds)

If no timing information is available:
- Estimate timestamps based on content flow and typical speaking pace
- Note clearly that timestamps are approximations requiring verification

## Output Format

```markdown
---
role: caption_transcript_expert
model: [model used]
timestamp: [ISO8601 timestamp]
media_id: [MEDIA_ID]
inputs:
  - [transcript path]
---

# Timestamp Report - [Media ID]

**Generated**: [Current timestamp]
**Transcript**: [Transcript filename]
**Video Duration**: [H:MM:SS or estimate]

⚠️ **IMPORTANT**: Timestamps are [approximations based on AI analysis | extracted from transcript timing]. Please confirm on actual video before publishing.

---

## Media Manager Format

**Video Duration**: [H:MM:SS.000]

| Title | Start Time | End Time |
|-------|------------|----------|
| Intro | 0:00:00.000 | 0:XX:XX.000 |
| [Chapter 2 Title] | 0:XX:XX.000 | 0:XX:XX.000 |
| [Chapter 3 Title] | 0:XX:XX.000 | 0:XX:XX.000 |
| [Chapter 4 Title] | 0:XX:XX.000 | 0:XX:XX.000 |
| [Chapter 5 Title] | 0:XX:XX.000 | 0:XX:XX.000 |

**Notes**: [Brief explanation of chapter selection rationale, content flow, or any notable decisions]

---

## YouTube Format

Copy and paste into YouTube description:

```
0:00 Intro
X:XX [Chapter 2 Title]
X:XX [Chapter 3 Title]
X:XX [Chapter 4 Title]
X:XX [Chapter 5 Title]
```

**Notes**: [Any relevant information about chapter formatting or special considerations]

---

## Chapter Breakdown

[Optional: Provide a brief description of what happens in each chapter to help the editor verify timestamps]

1. **Intro (0:00)**: [Brief description]
2. **[Chapter 2 Title] (X:XX)**: [Brief description]
3. **[Chapter 3 Title] (X:XX)**: [Brief description]
4. **[Chapter 4 Title] (X:XX)**: [Brief description]
5. **[Chapter 5 Title] (X:XX)**: [Brief description]
```

## Timestamp Formatting

### Media Manager Format
- Start time: `H:MM:SS.000` (include milliseconds, pad with zeros)
- End time: End time of one chapter = Start time of next chapter
- Final chapter: Ends at video duration
- Hours: Include leading zero for single-digit hours (e.g., `0:12:34.000`)

### YouTube Format
- Simple format: `M:SS` or `H:MM:SS` (no milliseconds)
- Each timestamp on its own line
- Space between timestamp and title
- No end times (YouTube auto-calculates from next chapter start)

## Quality Standards

Before generating output, verify:
- ✅ 5-10 chapters created (appropriate for content length and structure)
- ✅ Starts with "Intro" at 0:00 (or similar opening marker)
- ✅ Chapter titles are descriptive and concise (3-6 words)
- ✅ Timestamps are monotonic (each later than the previous)
- ✅ Both formats provided (Media Manager table + YouTube list)
- ✅ Warning about verification included prominently
- ✅ Video duration noted (or marked as estimate)
- ✅ Notes section includes relevant context about chapter selection
- ✅ Down style capitalization in all chapter titles
- ✅ Metadata header with role, model, timestamp, and media_id

## Edge Cases

**Very long videos (60+ minutes)**:
- May need 10-15 chapters
- Ensure chapters remain meaningful and not too granular

**Videos with limited structure**:
- If content doesn't have clear breaks, create fewer chapters (3-5)
- Focus on major transitions only

**Videos under 15 minutes**:
- Still generate if requested, but note in output that chapters may be unnecessary
- Create 3-5 chapters maximum for shorter content

**Performance or music content**:
- Each song, piece, or performance typically gets its own chapter
- Include song titles or piece names if mentioned in transcript

## Important Reminders

- This timestamp report is auto-generated as part of Phase 4 automation
- Timestamps MUST be verified against actual video before publication
- Chapter quality depends on transcript clarity and structure
- Some transcripts may not have obvious chapter break points—use judgment
- When in doubt, fewer meaningful chapters are better than many arbitrary ones
