#!/bin/bash
# Archive processed transcripts
# Moves transcripts to archive/ after their deliverables are complete
# Usage: ./scripts/archive-processed-transcripts.sh [--dry-run]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TRANSCRIPTS_DIR="$PROJECT_ROOT/transcripts"
OUTPUT_DIR="$PROJECT_ROOT/OUTPUT"
ARCHIVE_DIR="$TRANSCRIPTS_DIR/archive"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
  DRY_RUN=true
  echo -e "${YELLOW}DRY RUN MODE - No files will be moved${NC}"
  echo ""
fi

echo -e "${BLUE}=== Archive Processed Transcripts ===${NC}"
echo ""

# Create archive directory if it doesn't exist
mkdir -p "$ARCHIVE_DIR"

# Track statistics
total_checked=0
total_ready_to_archive=0
total_archived=0
total_incomplete=0

# Find all transcript files
cd "$TRANSCRIPTS_DIR"
for transcript_file in *_ForClaude.txt; do
  # Skip if no files found
  [[ -e "$transcript_file" ]] || continue

  total_checked=$((total_checked + 1))

  # Extract project name
  transcript_name="${transcript_file%_ForClaude.txt}"
  project_dir="$OUTPUT_DIR/$transcript_name"

  # Check if project directory exists
  if [[ ! -d "$project_dir" ]]; then
    echo -e "${YELLOW}⊘${NC} $transcript_file - No OUTPUT directory (not yet processed)"
    total_incomplete=$((total_incomplete + 1))
    continue
  fi

  # Check if manifest exists
  manifest_file="$project_dir/manifest.json"
  if [[ ! -f "$manifest_file" ]]; then
    echo -e "${YELLOW}⊘${NC} $transcript_file - No manifest found"
    total_incomplete=$((total_incomplete + 1))
    continue
  fi

  # Read status from manifest
  status=$(grep '"status"' "$manifest_file" | head -1 | sed 's/.*"status": "\([^"]*\)".*/\1/')

  # Check if has brainstorming deliverable
  has_brainstorming=$(grep '"brainstorming"' "$manifest_file" | grep -v 'null' || echo "")

  # Determine if ready to archive
  ready_to_archive=false
  reason=""

  if [[ "$status" == "ready_for_editing" ]] && [[ -n "$has_brainstorming" ]]; then
    ready_to_archive=true
    reason="brainstorming complete"
  elif [[ "$status" == "complete" ]]; then
    ready_to_archive=true
    reason="marked complete"
  elif [[ "$status" == "revision_in_progress" ]]; then
    # Has revisions, safe to archive
    ready_to_archive=true
    reason="revisions in progress"
  fi

  if [[ "$ready_to_archive" == true ]]; then
    total_ready_to_archive=$((total_ready_to_archive + 1))

    if [[ "$DRY_RUN" == true ]]; then
      echo -e "${GREEN}✓${NC} $transcript_file - Would archive ($reason)"
    else
      # Move to archive
      mv "$TRANSCRIPTS_DIR/$transcript_file" "$ARCHIVE_DIR/"
      echo -e "${GREEN}✓${NC} $transcript_file - Archived ($reason)"
      total_archived=$((total_archived + 1))
    fi
  else
    echo -e "${YELLOW}⊘${NC} $transcript_file - Status: $status (not ready)"
    total_incomplete=$((total_incomplete + 1))
  fi
done

echo ""
echo -e "${BLUE}=== Archive Summary ===${NC}"
echo -e "Transcripts checked: $total_checked"
echo -e "${GREEN}Ready to archive: $total_ready_to_archive${NC}"
if [[ "$DRY_RUN" == true ]]; then
  echo -e "${YELLOW}Actually archived: 0 (dry run mode)${NC}"
else
  echo -e "${GREEN}Archived: $total_archived${NC}"
fi
echo -e "${YELLOW}Incomplete/not ready: $total_incomplete${NC}"
echo ""

if [[ "$DRY_RUN" == true ]]; then
  echo -e "${YELLOW}Run without --dry-run to actually move files${NC}"
else
  if [[ $total_archived -gt 0 ]]; then
    echo -e "${GREEN}✓ Transcripts moved to: $ARCHIVE_DIR${NC}"
  fi
fi
