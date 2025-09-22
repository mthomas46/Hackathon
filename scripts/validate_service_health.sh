#!/bin/bash

# Service Health Validation Script
# Validates that all services in the ecosystem are healthy

set -e

echo "🏥 Validating Service Health..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SERVICES=(
    "redis:6379"
    "orchestrator:5099"
    "discovery-agent:5045"
    "doc_store:5087"
    "prompt_store:5110"
    "interpreter:5120"
    "llm-gateway:5055"
    "summarizer-hub:5160"
    "analysis-service:5080"
    "code-analyzer:5025"
    "secure-analyzer:5100"
    "architecture-digitizer:5105"
    "notification-service:5130"
    "source-agent:5085"
    "cli:5050"
    "mock-data-generator:5065"
    "frontend:3000"
    "log-collector:5040"
    "project-simulation:5075"
)

FAILED_SERVICES=()
UNHEALTHY_SERVICES=()

# Function to check if a port is open
check_port() {
    local host=$1
    local port=$2
    timeout 5 bash -c "</dev/tcp/$host/$port" 2>/dev/null && return 0 || return 1
}

# Function to check service health endpoint
check_health() {
    local service=$1
    local port=$2
    local url="http://localhost:$port/health"

    if curl -s -f --max-time 10 "$url" > /dev/null 2>&1; then
        # Check if response contains "healthy" or "status.*healthy"
        if curl -s --max-time 10 "$url" | grep -q '"healthy"\|"status":\s*"healthy"'; then
            echo -e "${GREEN}✅ $service ($port) - Healthy${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  $service ($port) - Responding but not healthy${NC}"
            UNHEALTHY_SERVICES+=("$service:$port")
            return 1
        fi
    else
        echo -e "${RED}❌ $service ($port) - Not responding${NC}"
        FAILED_SERVICES+=("$service:$port")
        return 1
    fi
}

echo "🔍 Checking service connectivity and health..."
echo "=============================================="

TOTAL_SERVICES=${#SERVICES[@]}
HEALTHY_COUNT=0

for service_port in "${SERVICES[@]}"; do
    IFS=':' read -r service port <<< "$service_port"

    # First check if port is open
    if check_port "localhost" "$port"; then
        # Then check health endpoint
        if check_health "$service" "$port"; then
            ((HEALTHY_COUNT++))
        fi
    else
        echo -e "${RED}❌ $service ($port) - Port not accessible${NC}"
        FAILED_SERVICES+=("$service:$port")
    fi
done

echo ""
echo "📊 Health Check Summary:"
echo "========================"
echo "Total Services: $TOTAL_SERVICES"
echo "Healthy Services: $HEALTHY_COUNT"
echo "Failed Services: ${#FAILED_SERVICES[@]}"
echo "Unhealthy Services: ${#UNHEALTHY_SERVICES[@]}"

# Show details of failed services
if [ ${#FAILED_SERVICES[@]} -gt 0 ]; then
    echo ""
    echo "❌ Failed Services:"
    for service in "${FAILED_SERVICES[@]}"; do
        echo "  - $service"
    done
fi

# Show details of unhealthy services
if [ ${#UNHEALTHY_SERVICES[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  Unhealthy Services:"
    for service in "${UNHEALTHY_SERVICES[@]}"; do
        echo "  - $service"
    done
fi

# Overall result
echo ""
if [ ${#FAILED_SERVICES[@]} -eq 0 ] && [ ${#UNHEALTHY_SERVICES[@]} -eq 0 ]; then
    echo -e "${GREEN}🎉 All services are healthy!${NC}"
    exit 0
elif [ ${#FAILED_SERVICES[@]} -eq 0 ]; then
    echo -e "${YELLOW}⚠️  All services are responding but some are not healthy${NC}"
    exit 1
else
    echo -e "${RED}❌ Some services are not responding${NC}"
    exit 1
fi
