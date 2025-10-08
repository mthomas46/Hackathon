#!/bin/bash

# Start Demo Services Helper Script
# Starts all services required for the hyper-realistic demo

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║              🚀 Starting Demo Services for Full Persistence                  ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose detected"
    echo ""
    echo "Choose startup method:"
    echo "  1) Docker Compose (recommended)"
    echo "  2) Manual Python processes"
    echo ""
    read -p "Enter choice (1 or 2): " choice
    
    if [ "$choice" = "1" ]; then
        echo ""
        echo "🐳 Starting services with Docker Compose..."
        echo ""
        
        # Start only the required services
        docker-compose -f docker-compose.dev.yml up -d \
            doc_store \
            prompt_store \
            external-service-store \
            memory-agent
        
        echo ""
        echo "⏳ Waiting for services to be ready (10 seconds)..."
        sleep 10
        
        echo ""
        echo "🔍 Verifying service health..."
        echo ""
        
        # Check each service
        services=(
            "doc_store:5087"
            "prompt_store:5110"
            "external-service-store:5140"
            "memory-agent:5090"
        )
        
        for service in "${services[@]}"; do
            name="${service%%:*}"
            port="${service##*:}"
            
            if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
                echo "  ✅ $name (port $port) is healthy"
            else
                echo "  ⚠️  $name (port $port) - not responding yet (may need more time)"
            fi
        done
        
        echo ""
        echo "╔══════════════════════════════════════════════════════════════════════════════╗"
        echo "║                                                                              ║"
        echo "║                     ✅ Services Started with Docker!                         ║"
        echo "║                                                                              ║"
        echo "║  To view logs:    docker-compose -f docker-compose.dev.yml logs -f          ║"
        echo "║  To stop:         docker-compose -f docker-compose.dev.yml down             ║"
        echo "║                                                                              ║"
        echo "╚══════════════════════════════════════════════════════════════════════════════╝"
        
        exit 0
    fi
fi

# Manual startup
echo ""
echo "🐍 Starting services with Python (manual mode)..."
echo ""

# Create PID tracking file
PID_FILE="$SCRIPT_DIR/.demo_services.pids"
> "$PID_FILE"

# Function to start a service
start_service() {
    local service_name=$1
    local service_path=$2
    local port=$3
    
    echo "  Starting $service_name on port $port..."
    
    cd "$SCRIPT_DIR/services/$service_path"
    python main.py > "$SCRIPT_DIR/.${service_name}.log" 2>&1 &
    local pid=$!
    echo "$pid" >> "$PID_FILE"
    
    echo "    PID: $pid"
    cd "$SCRIPT_DIR"
}

# Start each service
start_service "doc_store" "doc_store" "5087"
start_service "prompt_store" "prompt_store" "5110"
start_service "external-service-store" "external-service-store" "5140"
start_service "memory-agent" "memory-agent" "5090"

echo ""
echo "⏳ Waiting for services to initialize (15 seconds)..."
sleep 15

echo ""
echo "🔍 Verifying service health..."
echo ""

# Check each service
services=(
    "doc_store:5087"
    "prompt_store:5110"
    "external-service-store:5140"
    "memory-agent:5090"
)

all_healthy=true
for service in "${services[@]}"; do
    name="${service%%:*}"
    port="${service##*:}"
    
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "  ✅ $name (port $port) is healthy"
    else
        echo "  ❌ $name (port $port) - FAILED to start"
        all_healthy=false
    fi
done

echo ""

if [ "$all_healthy" = true ]; then
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                     ✅ All Services Started Successfully!                    ║"
    echo "║                                                                              ║"
    echo "║  To view logs:    tail -f .*.log                                            ║"
    echo "║  To stop:         ./stop_demo_services.sh                                   ║"
    echo "║  PIDs saved in:   .demo_services.pids                                       ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
else
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║              ⚠️  Some Services Failed to Start                               ║"
    echo "║                                                                              ║"
    echo "║  Check logs in:   .*.log files                                              ║"
    echo "║  Try stopping:    ./stop_demo_services.sh                                   ║"
    echo "║  Then restart                                                                ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    exit 1
fi

echo ""
echo "🎉 Ready to run the demo with full persistence!"
echo ""
echo "Run demo with:"
echo "  python demo_hyper_realistic_parameterized.py --feature \"your feature\" --tickets 35 --team 8 --tech Scala Elm --output demo_v9"

