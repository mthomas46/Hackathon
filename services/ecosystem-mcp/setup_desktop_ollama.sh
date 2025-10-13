#!/bin/bash
#
# Desktop Ollama Setup Script
# Configures native Ollama on desktop for GPU-accelerated RAG
#

set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 DESKTOP OLLAMA SETUP FOR ECOSYSTEM-MCP"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found!"
    echo ""
    echo "Please install Ollama first:"
    echo "  1. Download from: https://ollama.com/download"
    echo "  2. Or install via Homebrew: brew install ollama"
    echo ""
    exit 1
fi

echo "✅ Ollama is installed"
echo ""

# Check if desktop Ollama is running
echo "Checking desktop Ollama on port 11435..."
if curl -s http://localhost:11435/api/tags > /dev/null 2>&1; then
    echo "✅ Desktop Ollama is already running on port 11435"
else
    echo "⚠️  Desktop Ollama not running on port 11435"
    echo ""
    echo "To start desktop Ollama:"
    echo "  export OLLAMA_HOST=0.0.0.0:11435"
    echo "  ollama serve &"
    echo ""
    read -p "Start desktop Ollama now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        export OLLAMA_HOST=0.0.0.0:11435
        nohup ollama serve > logs/desktop_ollama.log 2>&1 &
        OLLAMA_PID=$!
        echo "✅ Started desktop Ollama (PID: $OLLAMA_PID)"
        echo "   Logs: logs/desktop_ollama.log"
        sleep 5
    else
        echo "Please start desktop Ollama manually and run this script again"
        exit 1
    fi
fi

echo ""

# Pull recommended model
echo "Pulling recommended model: llama3.1:8b-instruct-q8_0"
echo "(This may take 5-10 minutes for first-time download)"
echo ""

OLLAMA_HOST=http://localhost:11435 ollama pull llama3.1:8b-instruct-q8_0

echo ""
echo "✅ Model pulled successfully"
echo ""

# List models
echo "Available models on desktop Ollama:"
OLLAMA_HOST=http://localhost:11435 ollama list
echo ""

# Configure .env
echo "Configuring .env file..."

if [ ! -f .env ]; then
    touch .env
fi

# Remove existing desktop config if present
sed -i.bak '/OLLAMA_DESKTOP/d' .env
sed -i.bak '/USE_DESKTOP_FOR_RAG/d' .env

# Add desktop config
cat >> .env << 'EOF'

# Desktop Ollama Configuration (GPU-accelerated)
OLLAMA_DESKTOP_ENABLED=true
OLLAMA_DESKTOP_URL=http://localhost:11435
OLLAMA_DESKTOP_MODEL=llama3.1:8b-instruct-q8_0
USE_DESKTOP_FOR_RAG=true
EOF

echo "✅ .env configured"
echo ""

# Verify configuration
echo "════════════════════════════════════════════════════════════════════════════════"
echo "📊 CONFIGURATION SUMMARY"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Docker Ollama:  http://localhost:11434 (CPU)"
echo "Desktop Ollama: http://localhost:11435 (GPU)"
echo ""
echo "RAG Routing:    Desktop (GPU) → 4-8x faster!"
echo ""

# Check if service needs restart
if pgrep -f "uvicorn.*ecosystem-mcp" > /dev/null; then
    echo "⚠️  ecosystem-mcp service is running"
    echo ""
    read -p "Restart service to apply changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Restarting service..."
        pkill -9 -f uvicorn
        sleep 3
        python3 -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 > logs/service_with_desktop.log 2>&1 &
        echo "✅ Service restarted (PID: $!)"
        echo "   Logs: logs/service_with_desktop.log"
        sleep 30
        
        # Test status
        echo ""
        echo "Testing Ollama status..."
        curl -s http://localhost:8000/api/v1/ollama/status | python3 -m json.tool
    fi
else
    echo "ℹ️  Start ecosystem-mcp service to use desktop Ollama:"
    echo "   python3 -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 &"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETE!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Desktop Ollama is configured and ready to use!"
echo ""
echo "Next steps:"
echo "  1. Test RAG: python3 generate_dev_history.py"
echo "  2. Check status: curl http://localhost:8000/api/v1/ollama/status"
echo "  3. View guide: cat DESKTOP_OLLAMA_SETUP.md"
echo ""
echo "Expected performance: 15-30 seconds (vs >120s timeout before)"
echo ""

