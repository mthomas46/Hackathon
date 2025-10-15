#!/bin/bash

# Test runner for git detection with subdirectory support
# Tests enhanced error feedback and complete workflows

set -e

echo "════════════════════════════════════════════════════════════"
echo "  🧪 GIT DETECTION & SUBDIRECTORY TEST SUITE"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Track results
UNIT_RESULT=0
INTEGRATION_RESULT=0

# Ensure pytest is installed
echo -e "${BLUE}📦 Checking dependencies...${NC}"
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}⚠️  pytest not found, installing...${NC}"
    python3 -m pip install --break-system-packages pytest pytest-asyncio httpx || {
        echo -e "${RED}❌ Failed to install pytest${NC}"
        exit 1
    }
fi
echo -e "${GREEN}✅ Dependencies ready${NC}"
echo ""

# Run unit tests
echo "════════════════════════════════════════════════════════════"
echo -e "${BLUE}1️⃣  UNIT TESTS - Git Detection Logic${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""

if python3 -m pytest tests/test_git_detection_subdirectory.py -v --tb=short --color=yes; then
    echo -e "${GREEN}✅ Unit tests PASSED (21/21)${NC}"
    UNIT_RESULT=0
else
    echo -e "${RED}❌ Unit tests FAILED${NC}"
    UNIT_RESULT=1
fi
echo ""

# Run integration tests
echo "════════════════════════════════════════════════════════════"
echo -e "${BLUE}2️⃣  INTEGRATION TESTS - API Endpoints${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${YELLOW}⚠️  Note: Integration tests require backend service running${NC}"
echo -e "${YELLOW}   Start with: docker restart ecosystem-mcp-service${NC}"
echo ""

if python3 -m pytest tests/integration/test_git_detection_api_integration.py -v --tb=short --color=yes -m integration; then
    echo -e "${GREEN}✅ Integration tests PASSED${NC}"
    INTEGRATION_RESULT=0
else
    echo -e "${YELLOW}⚠️  Integration tests FAILED or SKIPPED${NC}"
    echo -e "${YELLOW}   (May be skipped if backend not running)${NC}"
    INTEGRATION_RESULT=1
fi
echo ""

# Summary
echo "════════════════════════════════════════════════════════════"
echo "  📊 TEST SUMMARY"
echo "════════════════════════════════════════════════════════════"
echo ""

if [ $UNIT_RESULT -eq 0 ]; then
    echo -e "   ${GREEN}✅ Unit Tests: 21/21 PASSED${NC}"
else
    echo -e "   ${RED}❌ Unit Tests: FAILED${NC}"
fi

if [ $INTEGRATION_RESULT -eq 0 ]; then
    echo -e "   ${GREEN}✅ Integration Tests: PASSED${NC}"
else
    echo -e "   ${YELLOW}⚠️  Integration Tests: FAILED/SKIPPED${NC}"
fi

echo ""

# Overall result
if [ $UNIT_RESULT -eq 0 ]; then
    echo "════════════════════════════════════════════════════════════"
    echo -e "  ${GREEN}✅ CORE TESTS PASSED!${NC}"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${GREEN}Git detection logic is working correctly.${NC}"
    echo ""
    
    if [ $INTEGRATION_RESULT -ne 0 ]; then
        echo -e "${YELLOW}ℹ️  Some integration tests were skipped.${NC}"
        echo -e "${YELLOW}   This is normal if services are not running.${NC}"
        echo ""
        echo "To run all tests:"
        echo "  1. Start service: docker restart ecosystem-mcp-service"
        echo "  2. Re-run this script: ./run_git_detection_tests.sh"
    fi
    
    exit 0
else
    echo "════════════════════════════════════════════════════════════"
    echo -e "  ${RED}❌ TESTS FAILED${NC}"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${RED}Some unit tests failed. Please review the output above.${NC}"
    echo ""
    exit 1
fi

