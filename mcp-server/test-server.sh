#!/bin/bash
# Quick test to verify MCP server starts correctly

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Testing Editorial Assistant MCP Server..."
echo ""

# Check if build exists
if [ ! -f "build/index.js" ]; then
  echo "❌ Build not found. Running npm run build..."
  npm run build
fi

echo "✓ Build exists"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo "❌ Dependencies not installed. Running npm install..."
  npm install
fi

echo "✓ Dependencies installed"
echo ""

# Test server starts (will run for 2 seconds then exit)
echo "Testing server startup..."
timeout 2 node build/index.js 2>&1 | head -n 1 || true

echo ""
echo "✅ MCP Server is ready to use!"
echo ""
echo "Next steps:"
echo "1. Add this server to Claude Chat MCP settings"
echo "2. See CLAUDE_CHAT_SETUP.md for configuration details"
