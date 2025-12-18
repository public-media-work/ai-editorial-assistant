# Format Transcript

You are working within the PBS Wisconsin Editorial Assistant CLI workflow.

## Agent Instructions

**CRITICAL**: Before proceeding, read and internalize the agent instructions at:
`.claude/agents/formatter.md`

You MUST follow all rules, guidelines, and output formats specified in that agent file. This includes:
- AP Style compliance
- Speaker identification (full names, bolded, every instance)
- Non-verbal cue notation
- Verbatim transcription preservation
- Template format from `.claude/templates/formatted-transcript.md`

## Your Task

1. **Find the project** - Look in `OUTPUT/` for the active project, or use the project the user specified
2. **Read the source transcript** - Get the original SRT/text file from `transcripts/`
3. **Read the agent instructions** - Load `.claude/agents/formatter.md` and follow them exactly
4. **Convert to readable format** - Transform SRT subtitles to prose format
5. **Save output** to `OUTPUT/{project_name}/00_transcript.md`
6. **Update `.state.json`** to record the formatted transcript
7. **Display success** with file location

## Formatting Rules (from agent file)

### Speaker Identification
- **ALWAYS use full name** (first AND last) in bold
- Format: `**Jane Smith:**`
- Every speaker turn gets full name, every time
- If only first name is known, note this limitation

### Structural Formatting
- New paragraph for each speaker change
- Verbatim transcription — maintain all speaker content exactly as spoken
- Non-verbal cues in square brackets: `[laughter]`, `[adjusts microphone]`
- Preserve all content, no omissions

### For Blooper/Outtakes Content
- Each distinct moment gets its own paragraph
- Preserve filler words and incomplete thoughts
- Note that timestamps have been removed for readability

## Output Requirements

The formatted transcript MUST:
- Follow `.claude/templates/formatted-transcript.md` structure
- Include proper speaker identification
- Apply AP Style throughout
- Include quality verification checklist
- Note any limitations (unknown speaker names, etc.)

## After Completion

Display:
- File saved location
- Number of speaker turns formatted
- Any notes about speaker identification

Now proceed: Read the formatter agent file, find the transcript, and generate the formatted document.
