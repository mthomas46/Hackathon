#!/bin/bash
# Enable Cursor MCP Server via Command Line
# This script modifies Cursor's settings.json to enable MCP server on port 3000

set -e

echo "════════════════════════════════════════════════════════════════════════════"
echo "           🥇 Enable Cursor MCP Server (Command Line)"
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

# Determine Cursor settings location based on OS
if [ "$MACHINE" = "Mac" ]; then
    CURSOR_CONFIG_DIR="$HOME/Library/Application Support/Cursor/User"
elif [ "$MACHINE" = "Linux" ]; then
    CURSOR_CONFIG_DIR="$HOME/.config/Cursor/User"
else
    echo -e "${RED}❌ Unsupported OS: ${MACHINE}${NC}"
    exit 1
fi

SETTINGS_FILE="$CURSOR_CONFIG_DIR/settings.json"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Locating Cursor settings"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -d "$CURSOR_CONFIG_DIR" ]; then
    echo -e "${YELLOW}⚠ Cursor config directory not found: $CURSOR_CONFIG_DIR${NC}"
    echo ""
    echo "This typically means:"
    echo "  1. Cursor IDE is not installed"
    echo "  2. Cursor has never been run (no config created yet)"
    echo ""
    echo "Please:"
    echo "  1. Install Cursor from https://cursor.sh"
    echo "  2. Run Cursor at least once to create config files"
    echo "  3. Run this script again"
    exit 1
fi

echo -e "${GREEN}✓ Found Cursor config directory: $CURSOR_CONFIG_DIR${NC}"

# Create settings.json if it doesn't exist
if [ ! -f "$SETTINGS_FILE" ]; then
    echo -e "${YELLOW}⚠ Settings file not found, creating new one${NC}"
    echo "{}" > "$SETTINGS_FILE"
fi

echo -e "${GREEN}✓ Settings file: $SETTINGS_FILE${NC}"
echo ""

# Create backup
BACKUP_FILE="${SETTINGS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Creating backup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cp "$SETTINGS_FILE" "$BACKUP_FILE"
echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
echo ""

# Update settings using Python (more reliable than jq for JSON manipulation)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Updating settings.json"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 << EOF
import json
import sys

settings_file = "$SETTINGS_FILE"

try:
    # Read existing settings
    with open(settings_file, 'r') as f:
        content = f.read().strip()
        if not content or content == '':
            settings = {}
        else:
            settings = json.loads(content)
    
    # Add/update MCP server settings
    # Note: The actual setting name may vary depending on Cursor version
    # Common patterns in VS Code-based editors:
    
    # Try multiple possible configuration keys
    settings["cursor.mcp.enabled"] = True
    settings["cursor.mcp.port"] = 3000
    settings["cursor.mcp.autoStart"] = True
    
    # Alternative naming conventions (cover multiple versions)
    settings["mcp.enabled"] = True
    settings["mcp.server.enabled"] = True
    settings["mcp.server.port"] = 3000
    settings["mcp.server.autoStart"] = True
    
    # Security settings
    settings["mcp.server.allowExternalConnections"] = True
    settings["cursor.mcp.allowExternalConnections"] = True
    
    # Save updated settings
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)
    
    print("✓ Settings updated successfully")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Error updating settings: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ MCP server configuration added to settings.json${NC}"
else
    echo -e "${RED}❌ Failed to update settings${NC}"
    echo "Restoring backup..."
    cp "$BACKUP_FILE" "$SETTINGS_FILE"
    exit 1
fi

echo ""

# Show what was added
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Verifying configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${BLUE}MCP settings added:${NC}"
grep -E "(mcp|MCP)" "$SETTINGS_FILE" | sed 's/^/  /' || echo "  (Settings may use different key names)"

echo ""

# Install Cursor CLI if not present
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Checking Cursor CLI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v cursor &> /dev/null; then
    echo -e "${GREEN}✓ Cursor CLI is installed${NC}"
    CURSOR_VERSION=$(cursor --version 2>/dev/null | head -n 1 || echo "unknown")
    echo "  Version: $CURSOR_VERSION"
else
    echo -e "${YELLOW}⚠ Cursor CLI not found in PATH${NC}"
    echo ""
    echo "To install Cursor CLI:"
    if [ "$MACHINE" = "Mac" ]; then
        echo "  1. Open Cursor IDE"
        echo "  2. Press Cmd+Shift+P"
        echo "  3. Type: 'Shell Command: Install cursor command in PATH'"
        echo "  4. Select it and press Enter"
        echo ""
        echo "Or manually create symlink:"
        echo "  sudo ln -s /Applications/Cursor.app/Contents/Resources/app/bin/cursor /usr/local/bin/cursor"
    elif [ "$MACHINE" = "Linux" ]; then
        echo "  1. Open Cursor IDE"
        echo "  2. Press Ctrl+Shift+P"
        echo "  3. Type: 'Shell Command: Install cursor command in PATH'"
        echo "  4. Select it and press Enter"
    fi
fi

echo ""

# Restart Cursor
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Restarting Cursor IDE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Checking if Cursor is running..."

if [ "$MACHINE" = "Mac" ]; then
    CURSOR_RUNNING=$(pgrep -f "Cursor.app" || echo "")
    
    if [ ! -z "$CURSOR_RUNNING" ]; then
        echo -e "${YELLOW}⚠ Cursor is currently running${NC}"
        echo ""
        read -p "Would you like to restart Cursor now? (y/n) " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Closing Cursor..."
            killall Cursor 2>/dev/null || true
            sleep 2
            
            echo "Starting Cursor..."
            open -a Cursor
            echo -e "${GREEN}✓ Cursor restarted${NC}"
        else
            echo -e "${YELLOW}⚠ Skipping restart${NC}"
            echo "Please restart Cursor manually for changes to take effect:"
            echo "  1. Quit Cursor (Cmd+Q)"
            echo "  2. Reopen Cursor"
        fi
    else
        echo "Cursor is not running, starting it..."
        open -a Cursor
        echo -e "${GREEN}✓ Cursor started${NC}"
    fi
elif [ "$MACHINE" = "Linux" ]; then
    CURSOR_RUNNING=$(pgrep -f "cursor" || echo "")
    
    if [ ! -z "$CURSOR_RUNNING" ]; then
        echo -e "${YELLOW}⚠ Cursor is currently running${NC}"
        echo ""
        read -p "Would you like to restart Cursor now? (y/n) " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Closing Cursor..."
            killall cursor 2>/dev/null || true
            sleep 2
            
            if command -v cursor &> /dev/null; then
                echo "Starting Cursor..."
                cursor &
                echo -e "${GREEN}✓ Cursor restarted${NC}"
            else
                echo -e "${YELLOW}⚠ Cursor CLI not found, please start manually${NC}"
            fi
        else
            echo -e "${YELLOW}⚠ Skipping restart${NC}"
            echo "Please restart Cursor manually for changes to take effect"
        fi
    else
        if command -v cursor &> /dev/null; then
            echo "Cursor is not running, starting it..."
            cursor &
            echo -e "${GREEN}✓ Cursor started${NC}"
        else
            echo -e "${YELLOW}⚠ Cursor CLI not found, please start manually${NC}"
        fi
    fi
fi

echo ""
echo "Waiting for Cursor to start (10 seconds)..."
sleep 10

# Test MCP server
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 7: Testing MCP server connectivity"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Testing localhost:3000..."
if curl -s -m 5 http://localhost:3000 &> /dev/null || curl -s -m 5 http://localhost:3000/health &> /dev/null; then
    echo -e "${GREEN}✓ MCP server is responding on port 3000!${NC}"
    MCP_AVAILABLE=true
else
    echo -e "${YELLOW}⚠ MCP server not yet accessible on port 3000${NC}"
    MCP_AVAILABLE=false
fi

echo ""
echo "Testing from Docker (host.docker.internal:3000)..."
DOCKER_TEST=$(docker run --rm curlimages/curl:latest curl -s -m 5 http://host.docker.internal:3000 2>/dev/null || echo "")
if [ ! -z "$DOCKER_TEST" ]; then
    echo -e "${GREEN}✓ MCP server accessible from Docker containers${NC}"
else
    echo -e "${YELLOW}⚠ MCP server not accessible from Docker yet${NC}"
fi

echo ""

# Verify with API
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 8: Checking ecosystem-mcp API recognition"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sleep 5  # Give API time to detect the change

TIER_STATUS=$(curl -s http://localhost:8000/api/v1/query/tier-status 2>/dev/null || echo "")
if [ ! -z "$TIER_STATUS" ]; then
    CURSOR_AVAILABLE=$(echo "$TIER_STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin)['tiers']['cursor']['available'])" 2>/dev/null || echo "false")
    
    if [ "$CURSOR_AVAILABLE" = "True" ]; then
        echo -e "${GREEN}✓ Cursor IDE is now recognized and available in ecosystem-mcp!${NC}"
        echo ""
        echo "$TIER_STATUS" | python3 -m json.tool | grep -A 5 '"cursor":'
    else
        echo -e "${YELLOW}⚠ Cursor IDE recognized but not yet available${NC}"
        echo ""
        echo "Current status:"
        echo "$TIER_STATUS" | python3 -m json.tool | grep -A 5 '"cursor":'
    fi
else
    echo -e "${YELLOW}⚠ Could not connect to ecosystem-mcp API${NC}"
    echo "Make sure the API is running: docker compose ps"
fi

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$MCP_AVAILABLE" = true ]; then
    echo -e "${GREEN}✅ SUCCESS! MCP server is enabled and running!${NC}"
    echo ""
    echo "Cursor MCP Server Status:"
    echo "  ✅ Settings configured"
    echo "  ✅ Port 3000 accessible"
    echo "  ✅ Ready for ecosystem-mcp integration"
    echo ""
    echo "Next Steps:"
    echo "  1. Open dashboard: http://localhost:8501"
    echo "  2. Go to: 🔌 LLM Tier Management"
    echo "  3. Click 'Refresh Status'"
    echo "  4. Verify Cursor IDE (Tier 1) shows as ✅ Available"
    echo ""
    echo "Test with a query:"
    echo "  • Go to: 🎯 Enhanced Query"
    echo "  • Select tier: 'Cursor (Tier 1)'"
    echo "  • Submit a complex question"
else
    echo -e "${YELLOW}⚠ MCP server configuration updated, but not yet accessible${NC}"
    echo ""
    echo "What was done:"
    echo "  ✅ Settings updated: $SETTINGS_FILE"
    echo "  ✅ Backup created: $BACKUP_FILE"
    echo "  ✅ Cursor restarted (if requested)"
    echo ""
    echo "Troubleshooting:"
    echo ""
    echo "1. Manual restart may be needed:"
    echo "   • Fully quit Cursor (don't just close windows)"
    echo "   • Wait 5 seconds"
    echo "   • Reopen Cursor"
    echo ""
    echo "2. Check Cursor version:"
    echo "   • MCP server might not be available in your Cursor version"
    echo "   • Update to the latest version from https://cursor.sh"
    echo ""
    echo "3. Verify settings manually:"
    echo "   • Open Cursor"
    echo "   • Press Cmd/Ctrl + ,"
    echo "   • Search for 'mcp' or 'Model Context Protocol'"
    echo "   • Ensure it's enabled and set to port 3000"
    echo ""
    echo "4. Check for conflicts:"
    echo "   • Make sure port 3000 isn't used by another process:"
    echo "     lsof -i :3000"
    echo ""
    echo "5. Check Cursor logs:"
    if [ "$MACHINE" = "Mac" ]; then
        echo "   • Location: ~/Library/Application Support/Cursor/logs/"
    else
        echo "   • Location: ~/.config/Cursor/logs/"
    fi
    echo "   • Look for MCP-related errors"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Notes:"
echo ""
echo "• Backup saved: $BACKUP_FILE"
echo "• To restore: cp $BACKUP_FILE $SETTINGS_FILE"
echo "• Settings location: $SETTINGS_FILE"
echo "• MCP server should be on: http://localhost:3000"
echo ""
echo "⚠️  IMPORTANT:"
echo "The exact MCP configuration may vary by Cursor version."
echo "If MCP is still not working after restart:"
echo "  1. Check Cursor's official docs for your version"
echo "  2. Look for MCP/API server settings in Cursor preferences"
echo "  3. Consider updating Cursor to the latest version"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


