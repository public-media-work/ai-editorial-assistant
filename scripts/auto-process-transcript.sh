#!/bin/bash
# Automatically process transcript through both agents
# Usage: ./scripts/auto-process-transcript.sh <transcript_file>

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <transcript_file>"
  exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TRANSCRIPTS_DIR="$PROJECT_ROOT/transcripts"
OUTPUT_DIR="$PROJECT_ROOT/OUTPUT"

transcript_file=$(basename "$1")
transcript_name="${transcript_file%_ForClaude.txt}"
project_dir="$OUTPUT_DIR/$transcript_name"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=== Auto-Processing: $transcript_name ===${NC}"
echo ""

# Check if transcript exists
transcript_path="$TRANSCRIPTS_DIR/$transcript_file"
if [ ! -f "$transcript_path" ]; then
  # Try archive
  transcript_path="$TRANSCRIPTS_DIR/archive/$transcript_file"
  if [ ! -f "$transcript_path" ]; then
    echo -e "${YELLOW}Error: Transcript not found${NC}"
    exit 1
  fi
fi

# Step 1: Batch setup (if not already done)
if [ ! -d "$project_dir" ]; then
  echo -e "${BLUE}→ Step 1: Creating project structure${NC}"
  "$SCRIPT_DIR/batch-process-transcripts.sh" "$transcript_file"
else
  echo -e "${GREEN}✓ Step 1: Project structure exists${NC}"
fi

# Step 2: Process with transcript-analyst
echo -e "${BLUE}→ Step 2: Generating brainstorming (transcript-analyst)${NC}"
echo "  This will take 1-2 minutes..."

# Create temporary processing marker
touch "$project_dir/.processing_brainstorming"

# Note: Actual agent invocation would happen here
# For now, this is a placeholder that shows the workflow
echo -e "${YELLOW}  Note: Agent processing requires Claude Code Task tool${NC}"
echo -e "${YELLOW}  Run: Task({subagent_type: 'general-purpose', prompt: '...'})${NC}"

# Step 3: Process with formatter
echo -e "${BLUE}→ Step 3: Generating formatted transcript (formatter)${NC}"
echo "  This will take 2-3 minutes..."

# Create temporary processing marker
touch "$project_dir/.processing_formatter"

echo -e "${YELLOW}  Note: Agent processing requires Claude Code Task tool${NC}"
echo -e "${YELLOW}  Run formatter agent for formatted transcript + timestamps${NC}"

echo ""
echo -e "${GREEN}=== Processing workflow outlined ===${NC}"
echo -e "Manual agent invocation still required in Claude Code"
