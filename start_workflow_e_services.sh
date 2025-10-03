#!/bin/bash
# Start Workflow E Required Services
# This script starts all services needed for full Workflow E integration

set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "  🚀 STARTING WORKFLOW E REQUIRED SERVICES"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Service ports from service-ports.yaml
LLM_GATEWAY_PORT=5055
EXTERNAL_SERVICE_STORE_PORT=5090
ANALYSIS_SERVICE_PORT=5080
USER_STORE_PORT=5150
SOURCE_AGENT_PORT=5085
SUMMARIZER_HUB_PORT=5160
OLLAMA_PORT=11434

# Change to script directory
cd "$(dirname "$0")"

# Function to check if a service is running
check_service() {
    local port=$1
    local name=$2
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "✅ $name is running on port $port"
        return 0
    else
        echo "⚠️  $name is NOT running on port $port"
        return 1
    fi
}

# Function to start a service
start_service() {
    local service_dir=$1
    local service_name=$2
    local port=$3
    
    echo ""
    echo "────────────────────────────────────────────────────────────────────────────"
    echo "Starting $service_name..."
    echo "────────────────────────────────────────────────────────────────────────────"
    
    if [ ! -d "$service_dir" ]; then
        echo "❌ Service directory not found: $service_dir"
        return 1
    fi
    
    cd "$service_dir"
    
    # Check if main.py exists
    if [ ! -f "main.py" ]; then
        echo "❌ main.py not found in $service_dir"
        cd - > /dev/null
        return 1
    fi
    
    # Kill existing process on this port
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
    
    # Start the service in the background
    echo "🔄 Starting $service_name on port $port..."
    nohup python main.py > /dev/null 2>&1 &
    local pid=$!
    echo "   PID: $pid"
    
    # Wait a moment for startup
    sleep 2
    
    # Check if it started successfully
    if check_service $port "$service_name"; then
        echo "✅ $service_name started successfully"
    else
        echo "❌ $service_name failed to start"
    fi
    
    cd - > /dev/null
}

echo "📋 Checking current service status..."
echo ""

# Check Ollama (should already be running)
if check_service $OLLAMA_PORT "Ollama"; then
    echo "   Models available:"
    curl -s http://localhost:$OLLAMA_PORT/api/tags | python3 -c "import json, sys; models = json.load(sys.stdin)['models']; [print(f'     • {m[\"name\"]}') for m in models[:4]]"
else
    echo "❌ Ollama is not running! Please start it first:"
    echo "   ollama serve"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "  Starting Services..."
echo "════════════════════════════════════════════════════════════════════════════════"

# 1. External Service Store (has our populated database)
start_service "services/external-service-store" "External Service Store" $EXTERNAL_SERVICE_STORE_PORT

# 2. LLM Gateway (connects to Ollama)
start_service "services/llm-gateway" "LLM Gateway" $LLM_GATEWAY_PORT

# 3. Analysis Service (uses LLM Gateway)
start_service "services/analysis-service" "Analysis Service" $ANALYSIS_SERVICE_PORT

# 4. User Store
start_service "services/user-store" "User Store" $USER_STORE_PORT

# 5. Source Agent
start_service "services/source-agent" "Source Agent" $SOURCE_AGENT_PORT

# 6. Summarizer Hub (uses LLM Gateway)
start_service "services/summarizer-hub" "Summarizer Hub" $SUMMARIZER_HUB_PORT

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "  📊 FINAL STATUS CHECK"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Final status check
SERVICES_UP=0
SERVICES_TOTAL=6

check_service $OLLAMA_PORT "Ollama" && ((SERVICES_UP++))
check_service $EXTERNAL_SERVICE_STORE_PORT "External Service Store" && ((SERVICES_UP++))
check_service $LLM_GATEWAY_PORT "LLM Gateway" && ((SERVICES_UP++))
check_service $ANALYSIS_SERVICE_PORT "Analysis Service" && ((SERVICES_UP++))
check_service $USER_STORE_PORT "User Store" && ((SERVICES_UP++))
check_service $SOURCE_AGENT_PORT "Source Agent" && ((SERVICES_UP++))

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "  Services Running: $SERVICES_UP / $((SERVICES_TOTAL + 1))"
echo "════════════════════════════════════════════════════════════════════════════════"

if [ $SERVICES_UP -ge 3 ]; then
    echo ""
    echo "✅ Minimum services running! You can now run the demo with full integration:"
    echo ""
    echo "   python demo_with_live_services.py \\"
    echo "     --feature \"Your feature description\" \\"
    echo "     --tickets 35 --team 8 \\"
    echo "     --tech Scala \"Cats Effect\" Elm CRUD API \\"
    echo "     --output demo_with_live_services"
    echo ""
else
    echo ""
    echo "⚠️  Not enough services started. Check the logs and try again."
    echo ""
    echo "To stop all services:"
    echo "   ./stop_workflow_e_services.sh"
    echo ""
fi

echo "════════════════════════════════════════════════════════════════════════════════"

