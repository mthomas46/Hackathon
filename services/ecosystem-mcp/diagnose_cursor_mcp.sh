#!/bin/bash
# Diagnose Cursor MCP Integration Issues

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                  🔍 Cursor MCP Diagnostic Tool                               ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check 1: Is Cursor running?
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Checking if Cursor is running"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CURSOR_RUNNING=$(ps aux | grep -i "Cursor.app" | grep -v grep | wc -l)
if [ "$CURSOR_RUNNING" -gt 0 ]; then
    echo -e "${GREEN}✅ Cursor is running ($CURSOR_RUNNING processes)${NC}"
else
    echo -e "${RED}❌ Cursor is not running${NC}"
    echo "   Please start Cursor first"
    exit 1
fi

echo ""

# Check 2: Is MCP server process running?
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Checking if MCP server process is running"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

MCP_RUNNING=$(ps aux | grep "mcp_server.py" | grep -v grep)
if [ ! -z "$MCP_RUNNING" ]; then
    echo -e "${GREEN}✅ MCP server process is running!${NC}"
    echo ""
    echo "Process details:"
    echo "$MCP_RUNNING" | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠️  MCP server process is NOT running${NC}"
    echo ""
    echo "This means Cursor hasn't started the MCP server yet."
fi

echo ""

# Check 3: Settings configuration
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Checking Cursor settings.json"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SETTINGS_FILE="$HOME/Library/Application Support/Cursor/User/settings.json"

if [ -f "$SETTINGS_FILE" ]; then
    echo -e "${GREEN}✅ Settings file exists${NC}"
    
    if grep -q "ecosystem-mcp" "$SETTINGS_FILE"; then
        echo -e "${GREEN}✅ ecosystem-mcp is configured${NC}"
        echo ""
        echo "Configuration:"
        grep -A 5 '"ecosystem-mcp"' "$SETTINGS_FILE" | sed 's/^/   /'
    else
        echo -e "${RED}❌ ecosystem-mcp NOT found in settings${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Settings file not found${NC}"
    exit 1
fi

echo ""

# Check 4: Test script execution
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Testing MCP server script manually"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TEST_OUTPUT=$(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | timeout 3 python3 /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/mcp_server.py 2>&1)

if echo "$TEST_OUTPUT" | grep -q "Starting ecosystem-mcp"; then
    echo -e "${GREEN}✅ Script executes successfully${NC}"
    echo ""
    echo "Test output:"
    echo "$TEST_OUTPUT" | head -n 2 | sed 's/^/   /'
else
    echo -e "${RED}❌ Script failed to execute${NC}"
    echo "Output:"
    echo "$TEST_OUTPUT" | sed 's/^/   /'
    exit 1
fi

echo ""

# Check 5: Check for Cursor logs
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Looking for Cursor log files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CURSOR_LOGS_DIR="$HOME/Library/Application Support/Cursor/logs"

if [ -d "$CURSOR_LOGS_DIR" ]; then
    echo -e "${GREEN}✅ Cursor logs directory exists${NC}"
    echo "   Location: $CURSOR_LOGS_DIR"
    
    # Find recent log files
    RECENT_LOGS=$(find "$CURSOR_LOGS_DIR" -type f -name "*.log" -mtime -1 2>/dev/null | head -n 5)
    
    if [ ! -z "$RECENT_LOGS" ]; then
        echo ""
        echo "Recent log files:"
        echo "$RECENT_LOGS" | sed 's/^/   /'
        
        echo ""
        echo "Searching for MCP-related errors..."
        grep -i "mcp\|ecosystem" $RECENT_LOGS 2>/dev/null | tail -n 10 | sed 's/^/   /' || echo "   (No MCP-related entries found)"
    fi
else
    echo -e "${YELLOW}⚠️  Cursor logs directory not found${NC}"
fi

echo ""

# Summary and instructions
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Summary & Next Steps"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ ! -z "$MCP_RUNNING" ]; then
    echo -e "${GREEN}✅ Everything looks good! MCP server is running.${NC}"
    echo ""
    echo "To see the output in Cursor:"
    echo "  1. In Cursor, press: Cmd+Shift+U (or View → Output)"
    echo "  2. In the dropdown at the top-right, select: 'MCP: ecosystem-mcp'"
    echo "  3. You should see: 'Starting ecosystem-mcp v1.0.0'"
    echo ""
    echo "If you don't see it in the dropdown:"
    echo "  • The MCP server might not be registered yet"
    echo "  • Try using a tool: type in Cursor chat 'list available tools'"
    echo "  • Cursor may need time to discover the MCP server"
else
    echo -e "${YELLOW}⚠️  MCP server process is not running${NC}"
    echo ""
    echo "Possible reasons:"
    echo ""
    echo "1. Cursor hasn't started the MCP server yet"
    echo "   → This can take 10-30 seconds after reload"
    echo "   → Wait a bit and run this diagnostic again"
    echo ""
    echo "2. Cursor needs to be fully restarted (not just reloaded)"
    echo "   → Quit Cursor completely: Cmd+Q"
    echo "   → Wait 5 seconds"
    echo "   → Reopen Cursor"
    echo "   → Wait 30 seconds, then check again"
    echo ""
    echo "3. MCP feature might not be enabled in your Cursor version"
    echo "   → Update to latest Cursor: Help → Check for Updates"
    echo "   → Ensure you're on Cursor 0.40+ (MCP support)"
    echo ""
    echo "4. Check Output panel in Cursor for errors:"
    echo "   → View → Output (Cmd+Shift+U)"
    echo "   → Look for any error messages"
    echo ""
    echo "5. Try manually triggering MCP:"
    echo "   → In Cursor Settings (Cmd+,)"
    echo "   → Search for 'MCP'"
    echo "   → Toggle any MCP-related settings off and back on"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Tips:"
echo "   • Run this diagnostic again after trying the suggested fixes"
echo "   • Check Cursor's Output panel (View → Output) for error messages"
echo "   • MCP servers can take 10-30 seconds to start after Cursor opens"
echo ""
echo "🔧 Quick fix to try:"
echo "   1. Quit Cursor completely (Cmd+Q)"
echo "   2. Wait 5 seconds"
echo "   3. Open Cursor"
echo "   4. Wait 30 seconds"
echo "   5. Run: ./diagnose_cursor_mcp.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"














