#!/bin/bash
# Datastore Operations Dashboard Launcher
# 
# This script starts the Streamlit dashboard for monitoring datastore operations.
# It performs pre-flight checks and provides helpful diagnostics.

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║        📊 Datastore Operations Dashboard Launcher               ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to project root
cd "$(dirname "$0")/../.."

# Check Python
echo "🔍 Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found:${NC} $(python3 --version)"

# Check if streamlit is installed
echo "🔍 Checking Streamlit..."
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Streamlit not installed${NC}"
    echo "Installing dependencies..."
    pip install -r services/data-services-dashboard/requirements.txt
else
    echo -e "${GREEN}✅ Streamlit installed${NC}"
fi

# Check if log-collector is running
echo "🔍 Checking log-collector service..."
if curl -s http://localhost:8104/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Log-collector is running${NC}"
else
    echo -e "${RED}❌ Log-collector not running${NC}"
    echo ""
    echo "The dashboard needs log-collector to be running."
    echo "Start it with one of these commands:"
    echo "  • docker-compose up log-collector"
    echo "  • cd services/log-collector && python3 main.py"
    echo ""
    read -p "Start dashboard anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check datastore services
echo "🔍 Checking datastore services..."
services_checked=0
services_running=0

for service in "doc_store:5087" "prompt_store:5110" "external-service-store:5140" "memory-agent:5090"; do
    IFS=':' read -r name port <<< "$service"
    services_checked=$((services_checked + 1))
    
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo -e "${GREEN}  ✅ $name${NC}"
        services_running=$((services_running + 1))
    else
        echo -e "${YELLOW}  ⚠️  $name (not running)${NC}"
    fi
done

echo ""
echo "Services Status: $services_running/$services_checked running"
echo ""

if [ $services_running -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No datastore services are running${NC}"
    echo "You won't see any data in the dashboard yet."
    echo ""
    echo "Start services with:"
    echo "  ./start_demo_services.sh"
    echo ""
fi

# Display info
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    Starting Dashboard...                         ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Dashboard will open in your browser at: http://localhost:8501"
echo ""
echo "Features:"
echo "  📊 Overview: Service health and operation distribution"
echo "  ⏱️  Performance: Response time trends and statistics"
echo "  🔍 Operations: Detailed operation logs with filtering"
echo "  🌊 Workflows: End-to-end request tracing"
echo "  ⚠️  Errors: Error analysis and diagnostics"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""
echo "─────────────────────────────────────────────────────────────────"
echo ""

# Start streamlit
streamlit run services/data-services-dashboard/app.py \
    --server.port 8501 \
    --server.address localhost \
    --server.headless true \
    --browser.gatherUsageStats false

