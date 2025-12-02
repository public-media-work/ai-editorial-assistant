#!/bin/bash
# Batch process new transcripts
# Usage: ./scripts/batch-process-transcripts.sh [optional: specific transcript file]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TRANSCRIPTS_DIR="$PROJECT_ROOT/transcripts"
OUTPUT_DIR="$PROJECT_ROOT/OUTPUT"
ARCHIVE_DIR="$TRANSCRIPTS_DIR/archive"
PROCESSING_LOG="$PROJECT_ROOT/.processing-log.json"

# Helper: derive project name from a transcript filename
project_name_from_file() {
  local fname="$1"
  fname="${fname##*/}"
  fname="${fname%.txt}"
  fname="${fname%_ForClaude}"
  fname="${fname%.mp4}"
  fname="${fname%.mov}"
  fname="${fname%.mkv}"
  fname="${fname%.srt}"
  echo "$fname"
}

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Editorial Assistant Batch Processor ===${NC}"
echo ""

# Initialize processing log if doesn't exist
if [ ! -f "$PROCESSING_LOG" ]; then
  echo "[]" > "$PROCESSING_LOG"
fi

# Find unprocessed transcripts
if [ -n "$1" ]; then
  # Process specific file
  TRANSCRIPTS=("$1")
else
  # Find all .txt files NOT in archive (includes legacy _ForClaude)
  cd "$TRANSCRIPTS_DIR"
  TRANSCRIPTS=($(find . -maxdepth 1 -name "*.txt" -type f))
fi

if [ ${#TRANSCRIPTS[@]} -eq 0 ]; then
  echo -e "${YELLOW}No unprocessed transcripts found.${NC}"
  exit 0
fi

echo -e "${GREEN}Found ${#TRANSCRIPTS[@]} transcript(s) to process:${NC}"
for transcript in "${TRANSCRIPTS[@]}"; do
  echo "  - $transcript"
done
echo ""

# Process each transcript
for transcript in "${TRANSCRIPTS[@]}"; do
  transcript_file=$(basename "$transcript")
  transcript_name="$(project_name_from_file "$transcript_file")"

  echo -e "${BLUE}Processing: $transcript_name${NC}"

  # Create project output directory
  project_dir="$OUTPUT_DIR/$transcript_name"
  mkdir -p "$project_dir"

  # Determine program type from filename prefix
  program_type="unknown"
  if [[ $transcript_name == 9UNP* ]]; then
    program_type="University Place"
  elif [[ $transcript_name == 2WLI* ]]; then
    program_type="Wisconsin Life"
  elif [[ $transcript_name == 6GWQ* ]]; then
    program_type="Garden Wanderings"
  elif [[ $transcript_name == 2BUC* ]]; then
    program_type="Bucky Documentary"
  fi

  # Log processing start
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  echo "  → Creating processing manifest..."
  cat > "$project_dir/manifest.json" << EOF
{
  "transcript_file": "$transcript_file",
  "project_name": "$transcript_name",
  "program_type": "$program_type",
  "processing_started": "$timestamp",
  "status": "processing",
  "deliverables": {
    "brainstorming": null,
    "formatted_transcript": null,
    "timestamps": null,
    "keywords": null
  }
}
EOF

  echo -e "  ${GREEN}✓${NC} Created $project_dir"
  echo ""
  echo -e "${YELLOW}  Note: Agent invocation requires manual Claude Code session${NC}"
  echo -e "  ${BLUE}Next steps:${NC}"
  echo -e "    1. Open Claude Code in this directory"
  echo -e "    2. Run: Task({subagent_type: 'transcript-analyst', ...})"
  echo -e "    3. Run: Task({subagent_type: 'formatter', ...})"
  echo -e "    4. Update manifest.json when complete"
  echo ""

done

echo -e "${GREEN}=== Batch setup complete ===${NC}"
echo -e "Ready for agent processing in Claude Code"
