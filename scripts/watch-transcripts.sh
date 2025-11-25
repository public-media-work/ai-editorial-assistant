#!/bin/bash
# Watch transcripts directory for new files and auto-process
# Usage: ./scripts/watch-transcripts.sh [--interval SECONDS]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TRANSCRIPTS_DIR="$PROJECT_ROOT/transcripts"
WATCH_STATE="$PROJECT_ROOT/.watch-state"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default check interval (in seconds)
INTERVAL=10

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--interval SECONDS]"
      exit 1
      ;;
  esac
done

# Initialize watch state file if doesn't exist
if [ ! -f "$WATCH_STATE" ]; then
  echo "[]" > "$WATCH_STATE"
fi

echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   Editorial Assistant - Transcript Folder Watcher     ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Watching:${NC} $TRANSCRIPTS_DIR"
echo -e "${BLUE}Check interval:${NC} ${INTERVAL}s"
echo -e "${BLUE}State file:${NC} $WATCH_STATE"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop watching${NC}"
echo ""

# Function to get list of processed files from state
get_processed_files() {
  if [ -f "$WATCH_STATE" ]; then
    cat "$WATCH_STATE"
  else
    echo "[]"
  fi
}

# Function to add file to processed list
mark_as_processed() {
  local file="$1"
  local state=$(get_processed_files)

  # Add to state (simple array append)
  if [ "$state" = "[]" ]; then
    echo "[\"$file\"]" > "$WATCH_STATE"
  else
    # Remove trailing ] and append
    echo "$state" | sed "s/]$/,\"$file\"]/" > "$WATCH_STATE"
  fi
}

# Function to check if file is already processed
is_processed() {
  local file="$1"
  local state=$(get_processed_files)

  if echo "$state" | grep -q "\"$file\""; then
    return 0  # true - already processed
  else
    return 1  # false - not processed
  fi
}

# Main watch loop
echo -e "${GREEN}✓${NC} Watcher started (PID: $$)"
echo ""

while true; do
  # Find new transcript files
  cd "$TRANSCRIPTS_DIR"

  for transcript_file in *_ForClaude.txt; do
    # Skip if no files found
    [[ -e "$transcript_file" ]] || continue

    # Skip if already processed
    if is_processed "$transcript_file"; then
      continue
    fi

    # New file detected!
    echo -e "${YELLOW}▶${NC} New transcript detected: ${CYAN}$transcript_file${NC}"

    # Run batch processing for this file
    cd "$PROJECT_ROOT"
    echo -e "  ${BLUE}→${NC} Running batch setup..."

    if ./scripts/batch-process-transcripts.sh "$transcript_file" 2>&1 | grep -v "^$"; then
      # Extract project name
      project_name="${transcript_file%_ForClaude.txt}"

      echo -e "  ${GREEN}✓${NC} Project setup complete: ${CYAN}$project_name${NC}"

      # Queue for agent processing
      echo -e "  ${BLUE}→${NC} Queueing for agent processing..."
      if ./scripts/auto-process-project.sh "$project_name" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Added to processing queue"
        echo -e "  ${YELLOW}→${NC} Run in Claude Code: \"Process all items in .processing-requests.json\""
      else
        echo -e "  ${YELLOW}⚠${NC} Could not queue for processing"
      fi
      echo ""

      # Mark as processed
      mark_as_processed "$transcript_file"
    else
      echo -e "  ${YELLOW}⚠${NC} Batch setup had issues, will retry next cycle"
      echo ""
    fi

    cd "$TRANSCRIPTS_DIR"
  done

  # Sleep before next check
  sleep "$INTERVAL"
done
