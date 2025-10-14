#!/bin/bash
# Setup script for Cursor IDE (Tier 1)
# This enables premium Claude 4.5 Sonnet access via Cursor's MCP server

set -e

echo "════════════════════════════════════════════════════════════════════════════"
echo "           🥇 Cursor IDE Setup (Tier 1 - Premium Models)"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo -e "${BLUE}Detected OS: ${MACHINE}${NC}"
echo ""

# Step 1: Check if Cursor IDE is installed
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Checking if Cursor IDE is installed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CURSOR_INSTALLED=false

if [ "$MACHINE" = "Mac" ]; then
    if [ -d "/Applications/Cursor.app" ]; then
        echo -e "${GREEN}✓ Cursor IDE is installed: /Applications/Cursor.app${NC}"
        CURSOR_INSTALLED=true
    fi
elif [ "$MACHINE" = "Linux" ]; then
    if command -v cursor &> /dev/null; then
        CURSOR_PATH=$(which cursor)
        echo -e "${GREEN}✓ Cursor IDE is installed: ${CURSOR_PATH}${NC}"
        CURSOR_INSTALLED=true
    fi
fi

if [ "$CURSOR_INSTALLED" = false ]; then
    echo -e "${YELLOW}⚠ Cursor IDE is not installed${NC}"
    echo ""
    echo "To install Cursor IDE:"
    echo "  Visit: https://cursor.sh"
    echo "  Download and install the application"
    echo ""
    echo -e "${BLUE}Note: Cursor IDE is required for Tier 1 (Premium Models)${NC}"
    echo "It provides access to Claude 4.5 Sonnet and other premium models."
    echo ""
    echo -e "${YELLOW}After installing Cursor IDE, run this script again.${NC}"
    exit 1
fi

echo ""

# Step 2: Check if Cursor MCP server is running
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Checking Cursor MCP server status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if MCP server is accessible on port 3000
if curl -s http://localhost:3000/health &> /dev/null || curl -s http://localhost:3000 &> /dev/null; then
    echo -e "${GREEN}✓ Cursor MCP server is running on port 3000${NC}"
    MCP_RUNNING=true
else
    echo -e "${YELLOW}⚠ Cursor MCP server is not accessible on port 3000${NC}"
    MCP_RUNNING=false
fi

echo ""

# Step 3: Provide setup instructions
if [ "$MCP_RUNNING" = false ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 3: Cursor MCP Server Setup Instructions"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${YELLOW}Cursor MCP server needs to be configured and running.${NC}"
    echo ""
    echo "📋 Manual Setup Required:"
    echo ""
    echo "1. Open Cursor IDE"
    echo ""
    echo "2. Enable MCP Server (if not already enabled):"
    echo "   • Go to Cursor Settings (Cmd/Ctrl + ,)"
    echo "   • Search for 'MCP' or 'Model Context Protocol'"
    echo "   • Enable MCP server functionality"
    echo "   • Set port to 3000"
    echo ""
    echo "3. Configure API Access:"
    echo "   • Ensure you have Claude API access in Cursor"
    echo "   • Verify your Cursor subscription includes Claude models"
    echo ""
    echo "4. Start/Restart Cursor IDE"
    echo "   • Close and reopen Cursor"
    echo "   • Or reload window (Cmd/Ctrl + Shift + P → 'Reload Window')"
    echo ""
    echo "5. Verify MCP server is running:"
    echo "   curl http://localhost:3000/health"
    echo ""
    echo -e "${BLUE}Note: MCP server configuration varies by Cursor version.${NC}"
    echo "Check Cursor documentation for your specific version."
    echo ""
    echo -e "${YELLOW}After configuring the MCP server, run this script again.${NC}"
    echo ""
fi

# Step 4: Test connectivity from Docker perspective
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Testing Docker connectivity"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test from host perspective
echo "Testing from host (localhost:3000)..."
if curl -s -m 2 http://localhost:3000/health &> /dev/null || curl -s -m 2 http://localhost:3000 &> /dev/null; then
    echo -e "${GREEN}✓ Accessible from host${NC}"
    HOST_ACCESSIBLE=true
else
    echo -e "${YELLOW}⚠ Not accessible from host${NC}"
    HOST_ACCESSIBLE=false
fi

# Test from Docker perspective (host.docker.internal)
echo ""
echo "Testing from Docker perspective (host.docker.internal:3000)..."
DOCKER_TEST=$(docker run --rm curlimages/curl:latest curl -s -m 5 http://host.docker.internal:3000/health 2>/dev/null || echo "")
if [ ! -z "$DOCKER_TEST" ]; then
    echo -e "${GREEN}✓ Accessible from Docker containers${NC}"
    DOCKER_ACCESSIBLE=true
else
    echo -e "${YELLOW}⚠ Not accessible from Docker${NC}"
    DOCKER_ACCESSIBLE=false
fi

echo ""

# Step 5: Update configuration
if [ "$HOST_ACCESSIBLE" = true ] || [ "$DOCKER_ACCESSIBLE" = true ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 5: Updating configuration"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Add to .env if not already present
    if ! grep -q "CURSOR_ENABLED" .env 2>/dev/null; then
        echo "" >> .env
        echo "# Cursor IDE (Tier 1) - Premium Models" >> .env
        echo "CURSOR_ENABLED=true" >> .env
        echo "CURSOR_MCP_URL=http://host.docker.internal:3000" >> .env
        echo "CURSOR_MODEL=claude-4.5-sonnet" >> .env
        echo -e "${GREEN}✓ Added Cursor IDE configuration to .env${NC}"
    else
        echo -e "${BLUE}ℹ Cursor IDE already configured in .env${NC}"
    fi
fi

echo ""

# Step 6: Verify with ecosystem-mcp API
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Verifying with ecosystem-mcp API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Checking tier status via API..."
TIER_STATUS=$(curl -s http://localhost:8000/api/v1/query/tier-status 2>/dev/null || echo "")

if [ ! -z "$TIER_STATUS" ]; then
    CURSOR_AVAILABLE=$(echo "$TIER_STATUS" | jq -r '.tiers.cursor.available' 2>/dev/null || echo "false")
    
    if [ "$CURSOR_AVAILABLE" = "true" ]; then
        echo -e "${GREEN}✓ Cursor IDE is now available in the system!${NC}"
        echo ""
        echo "  Tier Status:"
        echo "$TIER_STATUS" | jq '.tiers' 2>/dev/null | sed 's/^/    /'
    else
        echo -e "${YELLOW}⚠ Cursor IDE not yet detected by API${NC}"
        echo ""
        echo "This may be due to:"
        echo "  1. API cache (will refresh in ~30 seconds)"
        echo "  2. MCP server not fully started"
        echo "  3. Docker host.docker.internal not working"
        echo "  4. Need to restart ecosystem-mcp service"
        echo ""
        echo "Try refreshing the LLM Tier Management page in the dashboard."
    fi
else
    echo -e "${YELLOW}⚠ Could not connect to ecosystem-mcp API${NC}"
    echo "Make sure the API is running on http://localhost:8000"
fi

echo ""

# Step 7: Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Setup Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
if [ "$CURSOR_INSTALLED" = true ] && [ "$HOST_ACCESSIBLE" = true ]; then
    echo -e "${GREEN}✅ Cursor IDE Setup Complete!${NC}"
    echo ""
    echo "Cursor IDE is installed and the MCP server is accessible."
    echo ""
    echo "📋 Next Steps:"
    echo ""
    echo "  1. Restart ecosystem-mcp service:"
    echo "     cd /path/to/ecosystem-mcp"
    echo "     docker compose down ecosystem-mcp"
    echo "     docker compose up -d ecosystem-mcp"
    echo ""
    echo "  2. Wait ~10 seconds for service to start"
    echo ""
    echo "  3. Open dashboard: http://localhost:8501"
    echo "     Go to: Tools & Configuration → 🔌 LLM Tier Management"
    echo "     Click 'Refresh Status'"
    echo "     You should see Cursor IDE (Tier 1) as available"
    echo ""
    echo "  4. Test with a query:"
    echo "     Go to: 🎯 Enhanced Query"
    echo "     Select tier: 'Cursor' (Tier 1)"
    echo "     Submit a complex query to use Claude 4.5 Sonnet"
    echo ""
else
    echo -e "${YELLOW}⚠ Cursor IDE Setup Incomplete${NC}"
    echo ""
    if [ "$CURSOR_INSTALLED" = false ]; then
        echo "❌ Cursor IDE not installed"
        echo "   → Install from https://cursor.sh"
    fi
    if [ "$HOST_ACCESSIBLE" = false ]; then
        echo "❌ MCP server not accessible"
        echo "   → Follow Step 3 instructions above to configure MCP server"
    fi
    echo ""
    echo "Run this script again after completing the prerequisites."
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 About Cursor IDE (Tier 1):"
echo ""
echo "  • Premium tier with Claude 4.5 Sonnet access"
echo "  • Best for: Complex reasoning, code generation, analysis"
echo "  • Requires: Cursor IDE + MCP server + API access"
echo "  • Automatic routing: System uses Tier 1 for complex queries"
echo "  • Manual selection: Choose 'Cursor' in Enhanced Query mode"
echo ""
echo "🎯 When to use Cursor IDE:"
echo ""
echo "  ✅ Complex multi-step reasoning"
echo "  ✅ Advanced code generation"
echo "  ✅ Detailed technical analysis"
echo "  ✅ When quality is more important than speed"
echo ""
echo "⚙️  When to use lower tiers:"
echo ""
echo "  • Desktop Ollama (Tier 2): Fast queries with GPU"
echo "  • Docker Ollama (Tier 3): Simple queries, always available"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

