# How to Use the PBS Wisconsin Editorial Assistant

This guide shows you exactly how to use the system prompt with Claude chat to process video transcripts.

## Setup (One-Time, 5 Minutes)

### Option 1: Claude.ai Web Interface (Recommended for Most Users)

1. Go to [claude.ai](https://claude.ai)
2. Sign in with your Anthropic account
3. Keep this repository folder handy for drag-and-drop file uploads

### Option 2: Claude Desktop App

1. Download from [claude.ai/download](https://claude.ai/download)
2. Install and sign in
3. Same workflow as web interface, but works offline after initial setup

## Basic Workflow

### Step 1: Start a New Chat

Open Claude and start a fresh conversation. Each transcript should get its own chat to maintain clean context.

### Step 2: Upload the System Prompt

**Drag and drop** or click the attachment icon and select:
```
Haiku 4.5 version.md
```

This file contains all the instructions Claude needs to act as your editorial assistant.

### Step 3: Upload Reference Materials (Recommended)

Upload these files from the `knowledge/` folder:

**Essential** (always include):
- `ap_styleguide.pdf` - AP Style rules
- `Media ID Prefixes.md` - Program identifiers

**Recommended** (if generating transcripts or timestamps):
- `Transcript Style Guide.pdf` - Formatting rules
- `WPM Generative AI Guidelines.pdf` - Ethical AI use

**Optional** (visual references for timestamps):
- Screenshot PNGs showing timestamp formatting examples

You can drag all of these at once. Claude will reference them as needed.

### Step 4: Provide Your Transcript

Either:
- **Drag and drop** a `.txt` file from `transcripts/` folder
- **Copy/paste** the transcript text directly into chat

If your transcript has a Media ID filename (like `2WLI1203HD_ForClaude.txt`), Claude will automatically detect the program and apply specific rules.

### Step 5: Request Analysis

**Say something like:**
```
Please analyze this transcript and create brainstorming options for title, descriptions, and keywords.
```

Claude will automatically:
- Detect if it's standard video or shortform content
- Extract direct and implied keywords
- Generate 3-4 title options
- Create short and long description options
- Provide notable quotes and SEO recommendations

## Phase-by-Phase Usage

### Phase 1: Brainstorming (Automatic)

Claude delivers a Markdown artifact with:

| Section | Content |
|---------|---------|
| Title Options | 3-4 variations (under 80 chars each) |
| Short Descriptions | Paired with each title (under 100 chars) |
| Long Description | Detailed option (under 350 chars) |
| SEO Keywords | Direct + implied keywords |
| Notable Quotes | Pull quotes for social media |

**What to do:**
- Review options
- Pick your favorite title
- Decide if you want to use AI-generated descriptions or edit your own draft

### Phase 2: Editing (On Request)

**If you have draft copy to refine:**

```
I like title option 2. Here's my draft description that I'd like you to edit:

[paste your draft]
```

Claude will create a side-by-side comparison document showing:
- Original copy
- Proposed revision
- Character counts
- Reasoning for each change

**You can iterate:**
```
Good changes, but keep the original phrasing about [topic]. Try again.
```

### Phase 3: Keyword Research (Optional, On Request)

**Only needed when:**
- You have SEMRush data to analyze
- You explicitly request competitive keyword research

**How to trigger:**
```
I have SEMRush data. [paste data or upload screenshot]
```

Claude will generate:
1. **Keyword Report**: Platform-ready list ranked by search volume
2. **Implementation Report**: Prioritized action items

Most transcripts don't need this phase.

### Phase 4: Finalization (On Request)

**Formatted Transcript**:
```
Please create a formatted transcript following AP Style.
```

Claude will deliver:
- Proper speaker name formatting (first mention: full name; subsequent: last name only)
- Cleaned up filler words and false starts (if appropriate)
- AP Style conventions applied

**Timestamp Chapters** (only for 15+ minute videos):
```
Please create timestamp chapters for this video.
```

Claude will deliver BOTH formats:
- **Media Manager format**: `HH:MM:SS;FF` with chapter names
- **YouTube format**: `MM:SS` with chapter names

## Program-Specific Workflows

### Here and Now (Interview Format)

Claude automatically applies these rules when it detects `6HN` prefix:

**Title format**: `[SUBJECT] on [topic]`

**Long description**: Include party affiliation and location for elected officials
- Use "discuss" for all elected officials/candidates
- Use "explain/describe/consider" for non-elected subjects

**Example**:
```
Title: State Sen. Duey Stroebel on Wisconsin workforce development
Long Description: State Sen. Duey Stroebel, R-Cedarburg, discusses workforce challenges facing Wisconsin manufacturers and proposed legislative solutions.
```

### University Place (Academic Lectures)

- No honorific titles (Dr., Professor)
- Include lecture series name as keyword if applicable
- Avoid inflammatory language

### The Look Back (Historical Documentary)

Must include:
- Host names (Nick and Taylor)
- Institutions/locations visited
- Expert historians consulted
- Focus on WHY it matters, not just WHAT happened

### Digital Shorts (Social Media)

Claude auto-detects shortform content and optimizes for:
- Platform-specific hashtags
- Shorter, punchier language
- Mobile-first framing
- Hook-focused titles

## Tips for Better Results

### 1. Be Specific About What You Want

**Vague**: "Fix this"
**Better**: "Edit this description to reduce it to under 350 characters while keeping the mention of Milwaukee"

### 2. Use Conversational Refinement

This is a conversation, not a one-shot tool:
```
You: [initial request]
Claude: [delivers draft]
You: "Good, but the title feels too academic. Make it more accessible."
Claude: [revises title only]
You: "Perfect. Now create the formatted transcript."
```

### 3. Provide Context for Edge Cases

```
This is a University Place lecture, but the speaker explicitly asked to be called Dr. Rodriguez. Please keep the title.
```

Claude will override default rules when you provide context.

### 4. Verify Character Counts

Claude counts characters, but always double-check critical copy:
- Title: 80 characters max
- Short description: 100 characters max
- Long description: 350 characters max

### 5. Request Explanations

```
Why did you choose "considers" instead of "discusses" in this description?
```

Claude will explain its editorial reasoning based on the style guide.

## Common Requests Cheat Sheet

| You Want | Say This |
|----------|----------|
| Initial brainstorming | "Analyze this transcript and create brainstorming options" |
| Edit your draft | "Please edit this copy: [paste]" |
| Just title options | "Give me 5 title options for this transcript" |
| Keywords only | "Extract SEO keywords from this transcript" |
| Formatted transcript | "Create a formatted transcript following AP Style" |
| Timestamps | "Generate timestamp chapters" (15+ min videos only) |
| Different angle | "Reframe the description to emphasize [aspect]" |
| Shorter copy | "This is too long, cut it to [X] characters" |
| More formal tone | "Make this description more formal/academic" |
| More accessible | "Simplify this for general audience" |

## Troubleshooting

### "The descriptions feel too promotional"

Claude is trained to avoid this, but if it happens:
```
This sounds too promotional. Remove phrases like "discover" and "explore" and just state the facts.
```

### "Character count is wrong"

Claude counts spaces. If you're pasting into a CMS that counts differently:
```
My CMS shows this as [X] characters. Please recount and adjust.
```

### "Wrong program rules applied"

If filename doesn't have Media ID prefix:
```
This is a Here and Now interview. Please apply Here and Now formatting rules.
```

### "I need a different keyword approach"

```
These keywords are too broad. Focus on Wisconsin-specific long-tail keywords.
```

### "Output isn't showing as formatted table"

Claude delivers artifacts in Markdown. If your interface doesn't render it:
```
Please provide this as plain text instead of a Markdown table.
```

## Workflow for Multiple Transcripts

### Sequential Processing (Recommended)

1. Start new chat for each transcript
2. Upload system prompt + knowledge base (same every time)
3. Upload transcript
4. Process through phases
5. Copy final deliverables to your CMS
6. Archive transcript to `transcripts/archive/`

### Batch Processing (Advanced)

You can process multiple transcripts in one chat:
```
I have three transcripts to process. I'll upload them one at a time. For each one, just provide brainstorming options, then wait for my next transcript.

Transcript 1: [upload]
```

This works well if you only need Phase 1 for multiple videos.

## Saving Your Work

**Claude.ai automatically saves chat history.** You can:
- Return to any previous chat
- Search chat history by transcript name
- Copy deliverables out at any time

**For your records:**
- Copy final deliverables to your content management system
- Save original transcripts to `transcripts/archive/` when done
- Keep chat links for reference if you need to regenerate

## Next Steps

**New user?** Try processing one of the sample transcripts in `transcripts/archive/` to see how it works.

**Regular user?** Consider creating a "template chat" with the system prompt and knowledge base already uploaded, then duplicate it for each new transcript.

**Advanced user?** You can modify `Haiku 4.5 version.md` to customize the system prompt for your specific needs.

---

**Questions not covered here?** Start a chat with Claude and ask. The system prompt includes detailed instructions that Claude can explain to you.
