#!/bin/bash
# Check for transcripts that weren't picked up by the watcher
# Usage: ./scripts/check-missed-transcripts.sh [--process]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TRANSCRIPTS_DIR="$PROJECT_ROOT/transcripts"
WATCH_STATE="$PROJECT_ROOT/.watch-state"
OUTPUT_DIR="$PROJECT_ROOT/OUTPUT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROCESS_MODE=false
if [[ "$1" == "--process" ]]; then
  PROCESS_MODE=true
fi

echo -e "${BLUE}=== Checking for Missed Transcripts ===${NC}"
echo ""

# Get list of processed files from watch state
if [ -f "$WATCH_STATE" ]; then
  processed_files=$(cat "$WATCH_STATE")
else
  processed_files="[]"
fi

# Track statistics
total_transcripts=0
total_missed=0
total_processed_now=0

# Find all transcripts in directory
cd "$TRANSCRIPTS_DIR"

echo -e "${BLUE}Scanning transcripts directory...${NC}"
echo ""

for transcript_file in *_ForClaude.txt; do
  # Skip if no files found
  [[ -e "$transcript_file" ]] || continue

  total_transcripts=$((total_transcripts + 1))

  # Check if in watch state
  if echo "$processed_files" | jq -e ". | index(\"$transcript_file\")" > /dev/null 2>&1; then
    # In watch state - check if actually processed
    transcript_name="${transcript_file%_ForClaude.txt}"
    project_dir="$OUTPUT_DIR/$transcript_name"

    if [ -d "$project_dir" ]; then
      echo -e "${GREEN}✓${NC} $transcript_file - Tracked and processed"
    else
      echo -e "${YELLOW}⚠${NC} $transcript_file - Tracked but OUTPUT missing!"
      total_missed=$((total_missed + 1))

      if [[ "$PROCESS_MODE" == true ]]; then
        echo -e "  ${BLUE}→${NC} Processing now..."
        cd "$PROJECT_ROOT"
        if ./scripts/batch-process-transcripts.sh "$transcript_file" > /dev/null 2>&1; then
          if ./scripts/auto-process-project.sh "$transcript_name" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} Queued for agent processing"
            total_processed_now=$((total_processed_now + 1))
          fi
        fi
        cd "$TRANSCRIPTS_DIR"
      fi
    fi
  else
    # Not in watch state - definitely missed
    echo -e "${RED}✗${NC} $transcript_file - NOT TRACKED"
    total_missed=$((total_missed + 1))

    if [[ "$PROCESS_MODE" == true ]]; then
      transcript_name="${transcript_file%_ForClaude.txt}"
      echo -e "  ${BLUE}→${NC} Processing now..."
      cd "$PROJECT_ROOT"
      if ./scripts/batch-process-transcripts.sh "$transcript_file" > /dev/null 2>&1; then
        if ./scripts/auto-process-project.sh "$transcript_name" > /dev/null 2>&1; then
          echo -e "  ${GREEN}✓${NC} Queued for agent processing"
          total_processed_now=$((total_processed_now + 1))

          # Add to watch state
          if [ "$processed_files" = "[]" ]; then
            echo "[\"$transcript_file\"]" > "$WATCH_STATE"
          else
            echo "$processed_files" | jq ". += [\"$transcript_file\"]" > "$WATCH_STATE"
          fi
          processed_files=$(cat "$WATCH_STATE")
        fi
      fi
      cd "$TRANSCRIPTS_DIR"
    fi
  fi
done

echo ""
echo -e "${BLUE}=== Summary ===${NC}"
echo -e "Total transcripts found: $total_transcripts"
echo -e "${GREEN}Properly tracked: $((total_transcripts - total_missed))${NC}"

if [ $total_missed -gt 0 ]; then
  echo -e "${YELLOW}Missed/incomplete: $total_missed${NC}"

  if [[ "$PROCESS_MODE" == true ]]; then
    echo -e "${GREEN}Processed this run: $total_processed_now${NC}"

    if [ $total_processed_now -gt 0 ]; then
      echo ""
      echo -e "${BLUE}Next steps:${NC}"
      echo -e "1. Process queue in Claude Code: \"Process all items in .processing-requests.json\""
      echo -e "2. Finalize: ./scripts/finalize-queue.sh"
    fi
  else
    echo ""
    echo -e "${YELLOW}To process missed transcripts, run:${NC}"
    echo -e "  ./scripts/check-missed-transcripts.sh --process"
  fi
else
  echo -e "${GREEN}✓ All transcripts accounted for!${NC}"
fi

echo ""
