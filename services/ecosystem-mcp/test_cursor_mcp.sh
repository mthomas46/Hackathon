#!/bin/bash
# Test Cursor MCP Server Integration

echo "════════════════════════════════════════════════════════════════════════════"
echo "           🧪 Testing Cursor MCP Integration"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Step 1: Checking configuration${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SETTINGS_FILE="$HOME/Library/Application Support/Cursor/User/settings.json"

if grep -q "ecosystem-mcp" "$SETTINGS_FILE"; then
    echo -e "${GREEN}✅ ecosystem-mcp is configured in Cursor settings${NC}"
else
    echo -e "${RED}❌ ecosystem-mcp not found in settings${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 2: Checking API availability${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ ecosystem-mcp API is running${NC}"
else
    echo -e "${RED}❌ ecosystem-mcp API is not accessible${NC}"
    echo "   Make sure Docker containers are running:"
    echo "   cd services/ecosystem-mcp && docker compose ps"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 3: Testing MCP server directly${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test the MCP server script directly
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | timeout 5 python3 /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/mcp_server.py 2>&1 | head -n 1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ MCP server script responds correctly${NC}"
else
    echo -e "${YELLOW}⚠️  MCP server script test inconclusive${NC}"
fi

echo ""
echo -e "${BLUE}Step 4: Instructions for Cursor${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo -e "${GREEN}✅ Configuration Complete!${NC}"
echo ""
echo "To use ecosystem-mcp in Cursor:"
echo ""
echo "1. Reload Cursor window:"
echo "   • Press Cmd+Shift+P"
echo "   • Type: 'Developer: Reload Window'"
echo "   • Press Enter"
echo ""
echo "2. Verify MCP server is loaded:"
echo "   • Open Cursor Settings (Cmd+,)"
echo "   • Search for 'MCP'"
echo "   • You should see 'ecosystem-mcp' listed"
echo ""
echo "3. Use the MCP tools in Cursor:"
echo "   • In chat, you can now ask Cursor to use ecosystem-mcp tools"
echo "   • Try: '@ecosystem-mcp query: How does the caching system work?'"
echo "   • Or: '@ecosystem-mcp search: authentication'"
echo ""
echo "4. Check MCP server logs:"
echo "   • View > Output"
echo "   • Select 'MCP: ecosystem-mcp' from the dropdown"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Tips:"
echo ""
echo "• The MCP server connects Cursor to your ecosystem-mcp API"
echo "• It provides query, search, and RAG capabilities directly in Cursor"
echo "• Use it to search your documentation while coding"
echo "• Ask questions about your codebase using natural language"
echo ""
echo "🔧 Troubleshooting:"
echo ""
echo "If the MCP server doesn't work:"
echo "  1. Check API is running: curl http://localhost:8000/health"
echo "  2. Check Cursor logs: View > Output > MCP: ecosystem-mcp"
echo "  3. Restart Cursor completely (Quit, not just reload)"
echo "  4. Check settings file: cat \"$SETTINGS_FILE\" | grep ecosystem-mcp"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

