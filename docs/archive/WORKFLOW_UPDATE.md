# Workflow Update: Unified Processing for All Videos

**Date**: 2025-11-20
**Change**: Simplified content type detection to auto-detect based on duration

---

## What Changed

### Before
- Manual distinction between "standard" and "shortform" content
- Shortform videos grouped into digital_shorts_report.md
- Line count used for detection (unreliable with SRT timestamps)

### After
- **Every video gets its own individual brainstorming.md**
- **Duration auto-detected** from video timestamps
- **Videos under 3 minutes automatically get social media optimization** added to their brainstorming

---

## New Processing Logic

### All Videos (Regardless of Length)
Every transcript receives:
- Individual OUTPUT/{project}/brainstorming.md file
- 3 title options (80 chars max)
- 2 short descriptions (100 chars max)
- 2 long descriptions (350 chars max)
- Keywords (15-20 for standard, 5-10 for shortform)
- Notable quotes and key moments
- Program-specific compliance checks

### Videos Under 3 Minutes (Additional)
Shortform videos also receive in the same brainstorming.md:
- **Social Media Description** (150 chars max, platform-optimized)
- **Recommended Hashtags** (5 suggestions)
- **Social Media Keywords** (5-10 focused terms)
- **Platform-Specific Notes** (YouTube, Instagram/Facebook, TikTok)

---

## Why This Is Better

### 1. No More Guessing Content Type
- Duration is objective (from timestamps)
- No manual classification needed
- Works for all content: full episodes, DVD extras, web clips, social media

### 2. Individual Projects = Better Editing
- Each video editable separately in Claude Desktop
- Can load, refine, and save revisions independently
- Cleaner project structure in OUTPUT/

### 3. Flexible Social Media Support
- DVD extras (like Bucky clips) get full treatment
- But if under 3 min, also get social optimization
- Best of both worlds

### 4. Consistent Workflow
- Same batch script works for everything
- Same agent (transcript-analyst) handles all
- Same template with conditional sections

---

## Example: Bucky DVD Extras

### Old Way
- Grouped into 2BUC_DigitalShorts/digital_shorts_report.md
- All 4 clips in one file
- Had to edit together

### New Way
Each gets individual project:
```
OUTPUT/
├── 2BUC0000HDDVD01/  (Mascot Factory - 6:42)
│   └── brainstorming.md
│       - Standard metadata (titles, descriptions, keywords)
│       - NO social media section (over 3 min)
│
├── 2BUC0000HDDVD02/  (Chemistry Demo - 5:15)
│   └── brainstorming.md
│       - Standard metadata
│       - NO social media section (over 3 min)
│
├── 2BUC0000HDDVD03/  (Guitar Performance - 4:29)
│   └── brainstorming.md
│       - Standard metadata
│       - NO social media section (over 3 min)
│
└── 2BUC0000HDWEB01/  (Secret Revealed - 2:45)
    └── brainstorming.md
        - Standard metadata
        - ✅ INCLUDES social media section (under 3 min!)
```

---

## Duration Detection

The agent checks timestamps in transcript:
```
Example SRT format:
1
00:00:09,042 --> 00:00:10,911
Content here

Last timestamp:
145
00:06:42,123 --> 00:06:45,000
Final content
```

**Detected duration**: 6:45 (6 minutes 45 seconds)
**Is shortform?**: No (over 3 minutes)
**Social media section?**: Not included

---

## Updated Agent Contract

### Input
```typescript
{
  "transcript_file": string  // Just the file path
  // No need to specify content_type anymore
}
```

### Output
```typescript
{
  "duration": "6:45",           // Auto-detected
  "is_shortform": false,        // Auto-determined (< 3 min)
  "artifacts": {
    "files_created": [
      "OUTPUT/2BUC0000HDDVD01/brainstorming.md"
    ]
  },
  "social_media_optimization": null  // Only included if is_shortform: true
}
```

---

## Batch Processing Examples

### Processing Multiple Videos of Different Lengths

```bash
./scripts/batch-process-transcripts.sh
```

Finds:
- 9UNP2501HD_ForClaude.txt (56 min lecture)
- 2BUC0000HDDVD01_ForClaude.txt (6 min DVD extra)
- 2WLIMilitaryFamilySM_ForClaude.txt (2 min social clip)

Creates:
```
OUTPUT/
├── 9UNP2501HD/
│   └── brainstorming.md
│       Duration: 56:43
│       Social media section: NO
│
├── 2BUC0000HDDVD01/
│   └── brainstorming.md
│       Duration: 6:42
│       Social media section: NO
│
└── 2WLIMilitaryFamilySM/
    └── brainstorming.md
        Duration: 2:15
        Social media section: YES ✅
```

---

## Claude Desktop Discovery

When you ask "What's ready for editing?" you now see:

```
We have 3 projects ready for editing:

1. 9UNP2501HD (University Place)
   56-minute lecture on climate change
   Standard content

2. 2BUC0000HDDVD01 (Bucky Documentary - DVD Extra)
   6-minute behind-the-scenes at mascot factory
   Standard content (supplementary)

3. 2WLIMilitaryFamilySM (Wisconsin Life - Social Media)
   2-minute story about military family
   Shortform content with social media optimization
```

Load any individually to edit!

---

## Migration for Existing Projects

If you already processed videos the old way:

### Digital Shorts Reports
The existing `2BUC_DigitalShorts/digital_shorts_report.md` is fine to keep, but:
- Future processing will create individual projects
- You can manually split if desired, or leave as-is

### Re-processing Individual Clips
To re-process Bucky DVD extras individually:

```bash
# Move transcripts back from archive
mv transcripts/archive/2BUC0000HDDVD*.txt transcripts/

# Delete the grouped project
rm -rf OUTPUT/2BUC_DigitalShorts/

# Re-run batch processing
./scripts/batch-process-transcripts.sh

# Invoke transcript-analyst for each
# (Or use Task tool to process in parallel)
```

---

## Template Updates

### brainstorming-document.md
Added:
- **Duration** field in header
- **Content Type** shows "Shortform (under 3 min)" when applicable
- **Social Media Optimization** section (conditional)
  - Only appears when duration < 3 minutes
  - Includes: social description, hashtags, keywords, platform notes

### Agent Instructions
Updated:
- Removed manual content_type input requirement
- Added duration detection logic
- Added 3-minute threshold for social optimization
- Updated keyword counts (15-20 standard, 5-10 shortform)

---

## Quality Assurance

The agent still validates:
- ✅ Exact character counts (with spaces)
- ✅ Program-specific rules applied
- ✅ No prohibited language
- ✅ AP Style compliance
- ✅ Title/description pairing cohesion
- ✅ Keywords grounded in transcript
- ✅ **Duration detection accuracy** (new)

---

## Benefits Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Detection** | Manual or line count | Auto from timestamps |
| **Organization** | Grouped shortform | Individual projects |
| **Editing** | Edit groups together | Edit each separately |
| **Flexibility** | Fixed categories | Duration-based logic |
| **Social Media** | Separate template | Conditional section |
| **DVD Extras** | Unclear handling | Clear: individual + full metadata |
| **Workflow** | Multiple paths | Single unified flow |

---

## Next Steps

### For Future Processing
Just run batch script as normal:
```bash
./scripts/batch-process-transcripts.sh
```

The transcript-analyst agent will:
1. Detect duration from timestamps
2. Create individual brainstorming.md
3. Add social media section if < 3 min
4. Apply all quality standards

### For Editing in Claude Desktop
Ask "What's ready?" and load any project:
```
"Load 2BUC0000HDDVD01"
→ Gets full brainstorming for 6-minute DVD extra

"Load 2WLIMilitaryFamilySM"
→ Gets brainstorming + social media optimization
```

---

## Questions & Answers

**Q: What about videos with no timestamps?**
A: Agent will estimate from content length or ask for user input if unclear.

**Q: Can I override the 3-minute threshold?**
A: Yes, you can request social optimization for longer videos or exclude it for shorter ones during editing.

**Q: What if I want to group clips (like a series)?**
A: Process individually, then in Claude Desktop you can request a combined metadata document that references all clips.

**Q: Do I need to re-process old projects?**
A: No, existing deliverables are fine. This only affects new processing going forward.

---

**Status**: Implemented ✅
**Effective**: Immediately for all new processing
**Documentation Updated**: Agent contract, template, this file
