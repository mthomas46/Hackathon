#!/bin/bash
# Start Missing MCP Services
# These services exist as code but aren't in docker-compose-mcp-ecosystem.yml

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================"
echo "Starting Missing MCP Services"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Port $port already in use${NC}"
        return 1
    else
        echo -e "${GREEN}✓ Port $port available${NC}"
        return 0
    fi
}

# Function to start service in background
start_service() {
    local service_name=$1
    local service_dir=$2
    local port=$3
    
    echo ""
    echo "Starting $service_name on port $port..."
    
    if [ ! -d "$service_dir" ]; then
        echo -e "${RED}✗ Directory not found: $service_dir${NC}"
        return 1
    fi
    
    if ! check_port $port; then
        echo -e "${YELLOW}Skipping $service_name (port in use)${NC}"
        return 0
    fi
    
    cd "$service_dir"
    
    # Check for requirements
    if [ -f "requirements.txt" ]; then
        echo "Installing dependencies..."
        pip3 install -q -r requirements.txt
    fi
    
    # Start service in background
    echo "Starting uvicorn..."
    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port $port > "/tmp/${service_name}.log" 2>&1 &
    local pid=$!
    
    # Wait a bit for startup
    sleep 2
    
    # Check if process is still running
    if ps -p $pid > /dev/null; then
        echo -e "${GREEN}✓ $service_name started (PID: $pid)${NC}"
        echo "  Logs: /tmp/${service_name}.log"
        echo "  Health: http://localhost:$port/health"
        echo "  Docs: http://localhost:$port/docs"
    else
        echo -e "${RED}✗ $service_name failed to start${NC}"
        echo "Check logs: tail -f /tmp/${service_name}.log"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
}

# Check if Python and pip are available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ python3 not found. Please install Python 3.${NC}"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}✗ pip3 not found. Please install pip3.${NC}"
    exit 1
fi

echo "Prerequisites check:"
echo -e "${GREEN}✓ python3 found: $(python3 --version)${NC}"
echo -e "${GREEN}✓ pip3 found: $(pip3 --version)${NC}"

# Start each service
echo ""
echo "======================================"
echo "Starting Services..."
echo "======================================"

start_service "mcp-provisioner" "services/mcp-provisioner" 5400
start_service "mcp-training-coordinator" "services/mcp-training-coordinator" 5600
start_service "mcp-registry" "services/mcp-registry" 8102
start_service "mcp-gateway" "services/mcp-gateway" 8001

echo ""
echo "======================================"
echo "Service Startup Complete"
echo "======================================"
echo ""
echo "Testing services..."
sleep 3

# Test each service
echo ""
for port in 5400 5600 8102 8001; do
    echo -n "Port $port: "
    if curl -sf http://localhost:$port/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ UP${NC}"
    else
        echo -e "${RED}✗ DOWN${NC}"
    fi
done

echo ""
echo "======================================"
echo "Next Steps"
echo "======================================"
echo ""
echo "1. Check service health:"
echo "   curl http://localhost:5400/health  # mcp-provisioner"
echo "   curl http://localhost:5600/health  # mcp-training-coordinator"
echo "   curl http://localhost:8102/health  # mcp-registry"
echo "   curl http://localhost:8001/health  # mcp-gateway"
echo ""
echo "2. View API docs:"
echo "   open http://localhost:5400/docs  # mcp-provisioner"
echo "   open http://localhost:5600/docs  # mcp-training-coordinator"
echo ""
echo "3. Run the demo:"
echo "   python3 demo_mcp_lifecycle.py"
echo ""
echo "4. View logs:"
echo "   tail -f /tmp/mcp-provisioner.log"
echo "   tail -f /tmp/mcp-training-coordinator.log"
echo ""
echo "5. Stop services:"
echo "   pkill -f 'uvicorn main:app'"
echo ""
