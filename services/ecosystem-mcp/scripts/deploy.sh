#!/bin/bash
# Deployment script for ecosystem-mcp service
# Ensures proper rebuild and health check

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Service name
SERVICE=${1:-ecosystem-mcp}

echo -e "${GREEN}🚀 Deploying $SERVICE...${NC}"
echo ""

# Get git commit
cd "$(dirname "$0")/.."
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo -e "${YELLOW}📌 Git commit: $GIT_COMMIT${NC}"
echo ""

# Check for uncommitted changes
if git status --porcelain | grep -q "^"; then
    echo -e "${YELLOW}⚠️  Warning: You have uncommitted changes${NC}"
    git status --short
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Deployment cancelled${NC}"
        exit 1
    fi
    echo ""
fi

# Stop service
echo -e "${YELLOW}⏸️  Stopping $SERVICE...${NC}"
docker-compose stop $SERVICE 2>/dev/null || true
echo ""

# Remove container
echo -e "${YELLOW}🗑️  Removing old container...${NC}"
docker-compose rm -f $SERVICE 2>/dev/null || true
echo ""

# Build and start
echo -e "${GREEN}🔨 Building and starting $SERVICE...${NC}"
docker-compose up -d --force-recreate --build $SERVICE

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to start service${NC}"
    exit 1
fi
echo ""

# Wait for startup
echo -e "${YELLOW}⏳ Waiting for service to start (15 seconds)...${NC}"
sleep 15
echo ""

# Check if container is running
if ! docker ps --filter "name=${SERVICE}-service" --filter "status=running" | grep -q "${SERVICE}-service"; then
    echo -e "${RED}❌ Container is not running!${NC}"
    echo ""
    echo -e "${YELLOW}Last 50 log lines:${NC}"
    docker logs ecosystem-mcp-service --tail 50
    exit 1
fi

# Health check
echo -e "${GREEN}🏥 Checking service health...${NC}"
HEALTH_URL="http://localhost:8000/health"

MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s "$HEALTH_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check passed!${NC}"
        echo ""
        
        # Show health status
        echo -e "${GREEN}📊 Service Status:${NC}"
        curl -s "$HEALTH_URL" | python3 -m json.tool
        echo ""
        
        # Show worker status
        echo -e "${GREEN}👷 Worker Status:${NC}"
        curl -s "http://localhost:8000/api/v1/admin/workers/ingestion/status" | python3 -m json.tool || echo "Could not fetch worker status"
        echo ""
        
        # Show git commit in logs
        echo -e "${GREEN}📝 Deployed Version:${NC}"
        docker logs ecosystem-mcp-service 2>&1 | grep "Running code version" | tail -1 || echo "Version: $GIT_COMMIT (not logged)"
        echo ""
        
        echo -e "${GREEN}✅ Deployment complete!${NC}"
        echo ""
        echo -e "${YELLOW}📚 Useful commands:${NC}"
        echo "  View logs:  docker logs ecosystem-mcp-service -f"
        echo "  Check status: curl http://localhost:8000/health"
        echo "  Open shell: docker exec -it ecosystem-mcp-service bash"
        echo ""
        
        exit 0
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -e "${YELLOW}⏳ Waiting for health check ($RETRY_COUNT/$MAX_RETRIES)...${NC}"
    sleep 5
done

# Health check failed
echo -e "${RED}❌ Health check failed after $MAX_RETRIES attempts${NC}"
echo ""
echo -e "${YELLOW}Last 100 log lines:${NC}"
docker logs ecosystem-mcp-service --tail 100
echo ""
echo -e "${RED}Deployment failed! Service may not be healthy.${NC}"
exit 1

