#!/bin/bash
#
# Editorial Assistant - Setup Script
# Run this after cloning the repo to set up all dependencies
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  PBS Wisconsin Editorial Assistant - Setup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo

# -----------------------------------------------------------------------------
# Check Prerequisites
# -----------------------------------------------------------------------------
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "  ${GREEN}✓${NC} Python 3 found (${PYTHON_VERSION})"

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is required but not installed.${NC}"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "  ${GREEN}✓${NC} Node.js found (${NODE_VERSION})"

# Check for npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is required but not installed.${NC}"
    exit 1
fi
NPM_VERSION=$(npm --version)
echo -e "  ${GREEN}✓${NC} npm found (${NPM_VERSION})"

echo

# -----------------------------------------------------------------------------
# Create Required Directories
# -----------------------------------------------------------------------------
echo -e "${YELLOW}Creating required directories...${NC}"

mkdir -p logs
mkdir -p transcripts
mkdir -p transcripts/archive
mkdir -p OUTPUT
mkdir -p OUTPUT/archive

echo -e "  ${GREEN}✓${NC} logs/"
echo -e "  ${GREEN}✓${NC} transcripts/"
echo -e "  ${GREEN}✓${NC} transcripts/archive/"
echo -e "  ${GREEN}✓${NC} OUTPUT/"
echo -e "  ${GREEN}✓${NC} OUTPUT/archive/"
echo

# -----------------------------------------------------------------------------
# Python Virtual Environment
# -----------------------------------------------------------------------------
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"

if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
    echo -e "  ${GREEN}✓${NC} Virtual environment created"
else
    echo -e "  ${GREEN}✓${NC} Virtual environment already exists"
fi

echo "  Installing Python dependencies..."
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet rich requests
echo -e "  ${GREEN}✓${NC} Python dependencies installed (rich, requests)"
echo

# -----------------------------------------------------------------------------
# MCP Server Setup
# -----------------------------------------------------------------------------
echo -e "${YELLOW}Setting up MCP server...${NC}"

cd mcp-server

if [ ! -d "node_modules" ]; then
    echo "  Installing npm dependencies..."
    npm install --silent
    echo -e "  ${GREEN}✓${NC} npm dependencies installed"
else
    echo -e "  ${GREEN}✓${NC} npm dependencies already installed"
fi

echo "  Building TypeScript..."
npm run build --silent
echo -e "  ${GREEN}✓${NC} MCP server built"

cd ..
echo

# -----------------------------------------------------------------------------
# Verify Installation
# -----------------------------------------------------------------------------
echo -e "${YELLOW}Verifying installation...${NC}"

# Test Python imports
if ./venv/bin/python3 -c "import rich, requests" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Python imports verified"
else
    echo -e "  ${RED}✗${NC} Python import verification failed"
    exit 1
fi

# Test MCP server exists
if [ -f "mcp-server/build/index.js" ]; then
    echo -e "  ${GREEN}✓${NC} MCP server build verified"
else
    echo -e "  ${RED}✗${NC} MCP server build verification failed"
    exit 1
fi

echo
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Setup complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo
echo -e "You can now:"
echo -e "  • Launch the visual dashboard:  ${BLUE}./scripts/launch_dashboard.sh${NC}"
echo -e "  • Run queue processing:         ${BLUE}./venv/bin/python3 scripts/process_queue_auto.py${NC}"
echo
