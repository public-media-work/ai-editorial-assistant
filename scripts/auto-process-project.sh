#!/bin/bash
# Automatically process a project with agents after batch setup completes
# Usage: ./scripts/auto-process-project.sh <project_name>

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <project_name>"
  exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$PROJECT_ROOT/OUTPUT"

project_name="$1"
project_dir="$OUTPUT_DIR/$project_name"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Auto-Processing: $project_name ===${NC}"
echo ""

# Check if project exists
if [ ! -d "$project_dir" ]; then
  echo -e "${RED}Error: Project directory not found: $project_dir${NC}"
  exit 1
fi

# Check if manifest exists
manifest_path="$project_dir/manifest.json"
if [ ! -f "$manifest_path" ]; then
  echo -e "${RED}Error: Manifest not found: $manifest_path${NC}"
  exit 1
fi

# Get transcript file from manifest
transcript_file=$(jq -r '.transcript_file' "$manifest_path")
transcript_path="$PROJECT_ROOT/transcripts/$transcript_file"

if [ ! -f "$transcript_path" ]; then
  echo -e "${YELLOW}Warning: Transcript not found at $transcript_path${NC}"
  echo -e "${YELLOW}Will attempt processing anyway...${NC}"
fi

echo -e "${BLUE}Processing workflow:${NC}"
echo "  1. Run transcript-analyst (generates brainstorming)"
echo "  2. Run formatter (generates formatted_transcript + timestamps)"
echo ""

# Create a processing request file that Claude Code can pick up
processing_request="$PROJECT_ROOT/.processing-requests.json"

# Initialize or load existing requests
if [ -f "$processing_request" ]; then
  requests=$(cat "$processing_request")
else
  requests="[]"
fi

# Add this project to processing queue if not already there
if ! echo "$requests" | jq -e ".[] | select(.project == \"$project_name\")" > /dev/null 2>&1; then
  new_request=$(cat <<EOF
{
  "project": "$project_name",
  "transcript_file": "$transcript_file",
  "queued_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "status": "pending",
  "needs_brainstorming": true,
  "needs_formatting": true
}
EOF
)

  updated_requests=$(echo "$requests" | jq ". += [$new_request]")
  echo "$updated_requests" | jq '.' > "$processing_request"

  echo -e "${GREEN}✓ Added to processing queue${NC}"
  echo -e "${BLUE}Queue file: $processing_request${NC}"
else
  echo -e "${YELLOW}Project already in processing queue${NC}"
fi

echo ""
echo -e "${BLUE}=== Next Steps ===${NC}"
echo ""
echo "This project is now queued for agent processing."
echo ""
echo "To process all queued projects in Claude Code, run:"
echo -e "${YELLOW}  \"Process all items in .processing-requests.json\"${NC}"
echo ""
echo "Or to process this project specifically:"
echo -e "${YELLOW}  \"Process project $project_name from the queue\"${NC}"
echo ""
