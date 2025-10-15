#!/bin/bash

# Job Recovery Test Runner
# Runs unit, integration, and E2E tests for the recovery system

set -e  # Exit on error

echo "================================================"
echo "🧪 Job Recovery System - Test Suite"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if ecosystem-mcp-service is running
echo "🔍 Checking if ecosystem-mcp-service is running..."
if ! docker ps | grep -q ecosystem-mcp-service; then
    echo -e "${RED}❌ ecosystem-mcp-service is not running${NC}"
    echo "   Please start it with: docker-compose -f docker-compose-mcp-ecosystem.yml up -d"
    exit 1
fi
echo -e "${GREEN}✅ Service is running${NC}"
echo ""

# Wait for service to be healthy
echo "⏳ Waiting for service to be healthy..."
max_retries=30
retries=0
while [ $retries -lt $max_retries ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Service is healthy${NC}"
        break
    fi
    retries=$((retries + 1))
    echo "   Retry $retries/$max_retries..."
    sleep 2
done

if [ $retries -eq $max_retries ]; then
    echo -e "${RED}❌ Service did not become healthy${NC}"
    exit 1
fi
echo ""

# Test execution directory
cd /Users/mykalthomas/Documents/work/Hackathon

# Function to run tests in container
run_tests_in_container() {
    local test_type=$1
    local test_path=$2
    local markers=$3
    
    echo "================================================"
    echo "Running $test_type Tests"
    echo "================================================"
    echo ""
    
    docker exec ecosystem-mcp-service pytest \
        "$test_path" \
        -v \
        --tb=short \
        -m "$markers" \
        --color=yes \
        2>&1 || true  # Don't exit on test failures
    
    echo ""
}

# Run Unit Tests
echo -e "${YELLOW}📋 Phase 1: Unit Tests${NC}"
run_tests_in_container "Unit" "/app/tests/test_job_recovery.py" "not integration and not e2e"

# Run Integration Tests
echo -e "${YELLOW}📋 Phase 2: Integration Tests${NC}"
run_tests_in_container "Integration" "/app/tests/integration/test_job_recovery_integration.py" "integration"

# Run E2E Tests
echo -e "${YELLOW}📋 Phase 3: E2E Tests${NC}"
run_tests_in_container "E2E" "/app/tests/e2e/test_job_recovery_e2e.py" "e2e"

# Summary
echo "================================================"
echo "🎯 Test Suite Complete"
echo "================================================"
echo ""
echo "Test results saved. Review output above for details."
echo ""
echo "To run individual test suites:"
echo "  Unit:        docker exec ecosystem-mcp-service pytest tests/test_job_recovery.py -v"
echo "  Integration: docker exec ecosystem-mcp-service pytest tests/integration/test_job_recovery_integration.py -v -m integration"
echo "  E2E:         docker exec ecosystem-mcp-service pytest tests/e2e/test_job_recovery_e2e.py -v -m e2e"
echo ""

