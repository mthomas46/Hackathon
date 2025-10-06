#!/bin/bash
# Start MCP Provisioner Service Locally
# This script starts the service outside of Docker for local development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}MCP Provisioner Service - Local Startup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
python3 --version

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please review and update .env file${NC}"
fi

# Check Redis connection
echo -e "${YELLOW}Checking Redis connection...${NC}"
if ! redis-cli -h localhost ping > /dev/null 2>&1; then
    echo -e "${RED}❌ Redis is not running on localhost:6379${NC}"
    echo -e "${YELLOW}Please start Redis:${NC}"
    echo -e "  docker run -d -p 6379:6379 redis:latest"
    echo -e "  OR"
    echo -e "  docker-compose up -d redis"
    exit 1
fi
echo -e "${GREEN}✅ Redis is running${NC}"

# Check Docker connection
echo -e "${YELLOW}Checking Docker connection...${NC}"
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not accessible${NC}"
    echo -e "${YELLOW}Please ensure Docker daemon is running${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is accessible${NC}"

# Set PYTHONPATH
export PYTHONPATH=$(pwd)/../..:$PYTHONPATH

# Start service
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting MCP Provisioner Service...${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}API Documentation: http://localhost:5400/docs${NC}"
echo -e "${YELLOW}Health Check: http://localhost:5400/api/v1/health${NC}"
echo ""

python3 -m uvicorn services.mcp_provisioner.main:app \
    --host 0.0.0.0 \
    --port 5400 \
    --reload \
    --log-level info

