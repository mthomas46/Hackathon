#!/bin/bash
# Setup script for Desktop Ollama (Tier 2)
# This enables GPU-accelerated LLM inference on your host machine

set -e

echo "════════════════════════════════════════════════════════════════════════════"
echo "           🚀 Desktop Ollama Setup (Tier 2 - GPU Enhanced)"
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

# Step 1: Check if Ollama is installed
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Checking if Ollama is installed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v ollama &> /dev/null; then
    OLLAMA_VERSION=$(ollama --version 2>&1 | head -1)
    echo -e "${GREEN}✓ Ollama is installed: ${OLLAMA_VERSION}${NC}"
else
    echo -e "${YELLOW}⚠ Ollama is not installed${NC}"
    echo ""
    echo "To install Ollama:"
    echo ""
    if [ "$MACHINE" = "Mac" ]; then
        echo "  Option 1 (Recommended): Homebrew"
        echo "    brew install ollama"
        echo ""
        echo "  Option 2: Official Installer"
        echo "    Download from: https://ollama.ai/download"
    elif [ "$MACHINE" = "Linux" ]; then
        echo "  Run the official install script:"
        echo "    curl -fsSL https://ollama.ai/install.sh | sh"
    fi
    echo ""
    echo -e "${RED}Please install Ollama first, then run this script again.${NC}"
    exit 1
fi

echo ""

# Step 2: Check if Ollama is running on port 11435
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Checking if Ollama is running on port 11435"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if curl -s http://localhost:11435/api/version &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is running on port 11435${NC}"
    VERSION_INFO=$(curl -s http://localhost:11435/api/version)
    echo "  $VERSION_INFO"
else
    echo -e "${YELLOW}⚠ Ollama is not running on port 11435${NC}"
    echo ""
    echo "Starting Ollama on port 11435..."
    echo ""
    echo "This will start Ollama in the background."
    echo "To stop it later, run: killall ollama"
    echo ""
    
    # Start Ollama in background
    if [ "$MACHINE" = "Mac" ]; then
        echo "Starting Ollama service..."
        OLLAMA_HOST=0.0.0.0:11435 nohup ollama serve > /tmp/ollama_desktop.log 2>&1 &
        OLLAMA_PID=$!
        echo -e "${GREEN}✓ Ollama started (PID: $OLLAMA_PID)${NC}"
        echo "  Logs: /tmp/ollama_desktop.log"
    elif [ "$MACHINE" = "Linux" ]; then
        echo "Starting Ollama service..."
        OLLAMA_HOST=0.0.0.0:11435 nohup ollama serve > /tmp/ollama_desktop.log 2>&1 &
        OLLAMA_PID=$!
        echo -e "${GREEN}✓ Ollama started (PID: $OLLAMA_PID)${NC}"
        echo "  Logs: /tmp/ollama_desktop.log"
    fi
    
    # Wait for service to start
    echo ""
    echo "Waiting for Ollama to start..."
    sleep 3
    
    # Verify it started
    if curl -s http://localhost:11435/api/version &> /dev/null; then
        echo -e "${GREEN}✓ Ollama is now running on port 11435${NC}"
    else
        echo -e "${RED}✗ Failed to start Ollama. Check logs at /tmp/ollama_desktop.log${NC}"
        exit 1
    fi
fi

echo ""

# Step 3: Check available models
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Checking installed models"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

MODELS=$(ollama list 2>/dev/null || echo "")
if [ -z "$MODELS" ] || [ "$MODELS" = "NAME	ID	SIZE	MODIFIED" ]; then
    echo -e "${YELLOW}⚠ No models installed${NC}"
    echo ""
    echo "Recommended models:"
    echo "  • llama3:latest (7B) - Good balance of speed and quality"
    echo "  • llama3:70b - Best quality (requires 40GB+ VRAM)"
    echo "  • mistral:latest (7B) - Fast and efficient"
    echo ""
    
    # Offer to install llama3
    echo -e "${BLUE}Would you like to install llama3:latest (7B, ~4GB download)? [y/N]${NC}"
    read -r INSTALL_MODEL
    
    if [[ "$INSTALL_MODEL" =~ ^[Yy]$ ]]; then
        echo ""
        echo "Pulling llama3:latest..."
        echo "This may take a few minutes depending on your internet speed..."
        OLLAMA_HOST=localhost:11435 ollama pull llama3:latest
        echo -e "${GREEN}✓ llama3:latest installed${NC}"
    else
        echo ""
        echo "Skipping model installation."
        echo "You can install models later with:"
        echo "  OLLAMA_HOST=localhost:11435 ollama pull llama3:latest"
    fi
else
    echo -e "${GREEN}✓ Installed models:${NC}"
    echo "$MODELS" | tail -n +2 | while IFS= read -r line; do
        if [ ! -z "$line" ]; then
            MODEL_NAME=$(echo "$line" | awk '{print $1}')
            MODEL_SIZE=$(echo "$line" | awk '{print $3}')
            echo "  • $MODEL_NAME ($MODEL_SIZE)"
        fi
    done
fi

echo ""

# Step 4: Test the connection
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Testing Desktop Ollama connection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test from host perspective
echo "Testing from host (localhost:11435)..."
if curl -s http://localhost:11435/api/version &> /dev/null; then
    echo -e "${GREEN}✓ Accessible from host${NC}"
else
    echo -e "${RED}✗ Not accessible from host${NC}"
fi

# Test from Docker perspective (host.docker.internal)
echo ""
echo "Testing from Docker perspective (host.docker.internal:11435)..."
DOCKER_TEST=$(docker run --rm curlimages/curl:latest curl -s -m 5 http://host.docker.internal:11435/api/version 2>/dev/null || echo "")
if [ ! -z "$DOCKER_TEST" ]; then
    echo -e "${GREEN}✓ Accessible from Docker containers${NC}"
else
    echo -e "${YELLOW}⚠ Not accessible from Docker (may need Docker Desktop or network config)${NC}"
fi

echo ""

# Step 5: Verify with ecosystem-mcp API
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Verifying with ecosystem-mcp API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Checking tier status via API..."
TIER_STATUS=$(curl -s http://localhost:8000/api/v1/query/tier-status 2>/dev/null || echo "")

if [ ! -z "$TIER_STATUS" ]; then
    DESKTOP_AVAILABLE=$(echo "$TIER_STATUS" | jq -r '.tiers.desktop.available' 2>/dev/null || echo "false")
    
    if [ "$DESKTOP_AVAILABLE" = "true" ]; then
        echo -e "${GREEN}✓ Desktop Ollama is now available in the system!${NC}"
        echo ""
        echo "  Tier Status:"
        echo "$TIER_STATUS" | jq '.tiers' 2>/dev/null | sed 's/^/    /'
    else
        echo -e "${YELLOW}⚠ Desktop Ollama not yet detected by API${NC}"
        echo ""
        echo "This may be due to:"
        echo "  1. API cache (will refresh in ~30 seconds)"
        echo "  2. Network configuration"
        echo "  3. Docker host.docker.internal not working"
        echo ""
        echo "Try refreshing the LLM Tier Management page in the dashboard."
    fi
else
    echo -e "${YELLOW}⚠ Could not connect to ecosystem-mcp API${NC}"
    echo "Make sure the API is running on http://localhost:8000"
fi

echo ""

# Step 6: Summary and next steps
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Desktop Ollama is now running on port 11435"
echo ""
echo "📋 What's Next:"
echo ""
echo "  1. Open the dashboard: http://localhost:8501"
echo "  2. Go to: Tools & Configuration → 🔌 LLM Tier Management"
echo "  3. Click 'Refresh Status' to see Desktop Ollama available"
echo "  4. Test with a query in the RAG Query Interface"
echo ""
echo "💡 Tips:"
echo ""
echo "  • Desktop Ollama will automatically be used for heavy queries"
echo "  • You can manually select it in Enhanced Query mode"
echo "  • To stop: killall ollama"
echo "  • To restart: OLLAMA_HOST=0.0.0.0:11435 ollama serve"
echo "  • Logs: /tmp/ollama_desktop.log"
echo ""
echo "🎯 To install more models:"
echo "  OLLAMA_HOST=localhost:11435 ollama pull llama3:70b"
echo "  OLLAMA_HOST=localhost:11435 ollama pull mistral:latest"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
