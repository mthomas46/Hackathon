#!/bin/bash
# Stop Workflow E Services

echo "🛑 Stopping Workflow E Services..."

# Kill processes by port
for port in 5055 5090 5080 5150 5085 5160; do
    if lsof -ti:$port > /dev/null 2>&1; then
        echo "   Stopping service on port $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    fi
done

echo "✅ All services stopped"

