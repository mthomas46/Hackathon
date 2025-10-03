#!/bin/bash

# Stop Demo Services Helper Script

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                      🛑 Stopping Demo Services                               ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if running in Docker
if docker-compose -f docker-compose.dev.yml ps doc_store 2>/dev/null | grep -q "Up"; then
    echo "🐳 Detected Docker Compose services running..."
    echo ""
    
    docker-compose -f docker-compose.dev.yml down doc_store prompt_store external-service-store memory-agent 2>/dev/null || true
    
    echo ""
    echo "✅ Docker services stopped"
    exit 0
fi

# Stop manual processes
PID_FILE="$SCRIPT_DIR/.demo_services.pids"

if [ -f "$PID_FILE" ]; then
    echo "🐍 Stopping manual Python processes..."
    echo ""
    
    while read pid; do
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "  Stopping PID: $pid"
            kill "$pid" 2>/dev/null || true
        fi
    done < "$PID_FILE"
    
    rm "$PID_FILE"
    
    # Clean up log files
    rm -f .*.log
    
    echo ""
    echo "✅ All services stopped"
else
    echo "⚠️  No PID file found (.demo_services.pids)"
    echo ""
    echo "Checking for running services manually..."
    
    # Try to find and kill processes
    pkill -f "services/doc_store/main.py" 2>/dev/null || true
    pkill -f "services/prompt_store/main.py" 2>/dev/null || true
    pkill -f "services/external-service-store/main.py" 2>/dev/null || true
    pkill -f "services/memory-agent/main.py" 2>/dev/null || true
    
    echo "✅ Cleanup complete"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                        ✅ Services Stopped                                   ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"

