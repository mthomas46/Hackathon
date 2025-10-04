#!/bin/bash
# Test runner for DataStore operation logging tests
# 
# This script runs both unit and integration tests for the logging middleware
# and generates a comprehensive test report.

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TESTS_DIR="$BASE_DIR/tests"
SHARED_DIR="$BASE_DIR/services/shared"
LOG_COLLECTOR_URL="http://localhost:8104"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        DataStore Operation Logging - Test Suite               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python and pytest
echo -e "${YELLOW}→${NC} Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗${NC} Python 3 not found"
    exit 1
fi

if ! python3 -m pytest --version &> /dev/null; then
    echo -e "${YELLOW}⚠${NC}  pytest not installed, installing..."
    pip3 install pytest pytest-asyncio httpx
fi

echo -e "${GREEN}✓${NC} Prerequisites OK"
echo ""

# Function to check if service is running
check_service() {
    local name=$1
    local port=$2
    if curl -s "http://localhost:${port}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name (port $port) is running"
        return 0
    else
        echo -e "${YELLOW}⚠${NC}  $name (port $port) is NOT running"
        return 1
    fi
}

# Check service availability
echo -e "${YELLOW}→${NC} Checking service availability..."
LOG_COLLECTOR_RUNNING=false
if check_service "log-collector" 8104; then
    LOG_COLLECTOR_RUNNING=true
fi

SERVICES_RUNNING=0
check_service "doc-store" 5020 && ((SERVICES_RUNNING++)) || true
check_service "prompt-store" 5030 && ((SERVICES_RUNNING++)) || true
check_service "external-service-store" 5140 && ((SERVICES_RUNNING++)) || true
check_service "memory-agent" 5090 && ((SERVICES_RUNNING++)) || true
check_service "user-store" 5150 && ((SERVICES_RUNNING++)) || true
check_service "project-planning-service" 5160 && ((SERVICES_RUNNING++)) || true

echo ""

# Run unit tests
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Running Unit Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

cd "$SHARED_DIR"
UNIT_TEST_RESULT=0
python3 -m pytest tests/test_datastore_operation_logger.py -v --tb=short || UNIT_TEST_RESULT=$?

echo ""

# Run integration tests (only if services are available)
if [ "$LOG_COLLECTOR_RUNNING" = true ] && [ $SERVICES_RUNNING -gt 0 ]; then
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Running Integration Tests${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    cd "$TESTS_DIR"
    INTEGRATION_TEST_RESULT=0
    python3 -m pytest integration/test_datastore_logging_integration.py -v --tb=short || INTEGRATION_TEST_RESULT=$?
    
    echo ""
else
    echo -e "${YELLOW}⚠${NC}  Skipping integration tests - services not running"
    echo -e "   To run integration tests:"
    echo -e "   1. Start log-collector: cd services/log-collector && python3 main.py"
    echo -e "   2. Start datastore services (doc-store, prompt-store, etc.)"
    echo -e "   3. Run this script again"
    echo ""
    INTEGRATION_TEST_RESULT=0
fi

# Generate summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ $UNIT_TEST_RESULT -eq 0 ]; then
    echo -e "  Unit Tests:        ${GREEN}✓ PASSED${NC}"
else
    echo -e "  Unit Tests:        ${RED}✗ FAILED${NC}"
fi

if [ "$LOG_COLLECTOR_RUNNING" = true ] && [ $SERVICES_RUNNING -gt 0 ]; then
    if [ $INTEGRATION_TEST_RESULT -eq 0 ]; then
        echo -e "  Integration Tests: ${GREEN}✓ PASSED${NC}"
    else
        echo -e "  Integration Tests: ${RED}✗ FAILED${NC}"
    fi
else
    echo -e "  Integration Tests: ${YELLOW}⊘ SKIPPED${NC}"
fi

echo ""
echo -e "  Services Running:  $SERVICES_RUNNING / 6"
echo -e "  Log Collector:     $([ "$LOG_COLLECTOR_RUNNING" = true ] && echo -e "${GREEN}Running${NC}" || echo -e "${YELLOW}Not running${NC}")"
echo ""

# Exit with failure if any tests failed
if [ $UNIT_TEST_RESULT -ne 0 ] || [ $INTEGRATION_TEST_RESULT -ne 0 ]; then
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
else
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
fi

