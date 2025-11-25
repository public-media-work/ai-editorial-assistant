#!/bin/bash
# Finalize processed projects: archive transcripts and clear queue
# Usage: ./scripts/finalize-queue.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
QUEUE_FILE="$PROJECT_ROOT/.processing-requests.json"
OUTPUT_DIR="$PROJECT_ROOT/OUTPUT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Finalizing Processed Projects ===${NC}"
echo ""

# Check if queue file exists
if [ ! -f "$QUEUE_FILE" ]; then
  echo -e "${YELLOW}No processing queue found${NC}"
  exit 0
fi

# Read queue
queue=$(cat "$QUEUE_FILE")
queue_count=$(echo "$queue" | jq 'length')

if [ "$queue_count" -eq 0 ]; then
  echo -e "${YELLOW}Queue is empty${NC}"
  exit 0
fi

echo -e "${BLUE}Checking $queue_count project(s) for completion...${NC}"
echo ""

# Track statistics
total_completed=0
total_archived=0
total_incomplete=0

# Process each project in queue
for row in $(echo "$queue" | jq -r '.[] | @base64'); do
  _jq() {
    echo "${row}" | base64 --decode | jq -r "${1}"
  }

  project=$(_jq '.project')

  echo -e "${BLUE}Checking: $project${NC}"

  # Check if project has required deliverables
  manifest_path="$OUTPUT_DIR/$project/manifest.json"

  if [ ! -f "$manifest_path" ]; then
    echo -e "  ${RED}✗${NC} No manifest found"
    total_incomplete=$((total_incomplete + 1))
    continue
  fi

  # Check for brainstorming and formatted transcript
  has_brainstorming=$(grep '"brainstorming"' "$manifest_path" | grep -v 'null' || echo "")
  has_formatted=$(grep '"formatted_transcript"' "$manifest_path" | grep -v 'null' || echo "")

  if [[ -n "$has_brainstorming" ]] && [[ -n "$has_formatted" ]]; then
    echo -e "  ${GREEN}✓${NC} Processing complete"
    total_completed=$((total_completed + 1))

    # Auto-archive the transcript
    if ./scripts/auto-archive-transcript.sh "$project" 2>&1 | grep -q "Archived"; then
      echo -e "  ${GREEN}✓${NC} Transcript archived"
      total_archived=$((total_archived + 1))
    else
      echo -e "  ${YELLOW}⊘${NC} Transcript already archived or not found"
    fi
  else
    echo -e "  ${YELLOW}⊘${NC} Incomplete:"
    echo -e "     Brainstorming: $([ -n "$has_brainstorming" ] && echo "✓" || echo "✗")"
    echo -e "     Formatted transcript: $([ -n "$has_formatted" ] && echo "✓" || echo "✗")"
    total_incomplete=$((total_incomplete + 1))
  fi

  echo ""
done

echo -e "${BLUE}=== Finalization Summary ===${NC}"
echo -e "Projects checked: $queue_count"
echo -e "${GREEN}Completed: $total_completed${NC}"
echo -e "${GREEN}Archived: $total_archived${NC}"
echo -e "${YELLOW}Incomplete: $total_incomplete${NC}"
echo ""

# Clear completed projects from queue if all are done
if [ "$total_incomplete" -eq 0 ]; then
  echo "[]" > "$QUEUE_FILE"
  echo -e "${GREEN}✓ Queue cleared - all projects complete${NC}"
else
  echo -e "${YELLOW}Queue not cleared - some projects still incomplete${NC}"
  echo -e "${BLUE}Run agent processing on incomplete projects, then run this script again${NC}"
fi
