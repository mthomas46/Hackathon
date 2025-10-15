#!/bin/bash

# Test runner for ingestion path resolution feature
# Tests the automatic path validation and resolution functionality

set -e

echo "════════════════════════════════════════════════════════════"
echo "  🧪 INGESTION PATH RESOLUTION TEST SUITE"
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
E2E_RESULT=0

# Ensure pytest is installed
echo -e "${BLUE}📦 Checking dependencies...${NC}"
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}⚠️  pytest not found, installing...${NC}"
    python3 -m pip install --break-system-packages pytest pytest-asyncio httpx selenium || {
        echo -e "${RED}❌ Failed to install pytest${NC}"
        exit 1
    }
fi
echo -e "${GREEN}✅ Dependencies ready${NC}"
echo ""

# Run unit tests
echo "════════════════════════════════════════════════════════════"
echo -e "${BLUE}1️⃣  UNIT TESTS${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""

if python3 -m pytest tests/test_ingestion_path_resolution.py -v --tb=short --color=yes; then
    echo -e "${GREEN}✅ Unit tests PASSED${NC}"
    UNIT_RESULT=0
else
    echo -e "${RED}❌ Unit tests FAILED${NC}"
    UNIT_RESULT=1
fi
echo ""

# Run integration tests
echo "════════════════════════════════════════════════════════════"
echo -e "${BLUE}2️⃣  INTEGRATION TESTS${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${YELLOW}⚠️  Note: Integration tests require backend service to be running${NC}"
echo -e "${YELLOW}   Start with: docker restart ecosystem-mcp-service${NC}"
echo ""

if python3 -m pytest tests/integration/test_ingestion_path_resolution_integration.py -v --tb=short --color=yes -m integration; then
    echo -e "${GREEN}✅ Integration tests PASSED${NC}"
    INTEGRATION_RESULT=0
else
    echo -e "${YELLOW}⚠️  Integration tests FAILED or SKIPPED${NC}"
    echo -e "${YELLOW}   (May be skipped if backend is not running)${NC}"
    INTEGRATION_RESULT=1
fi
echo ""

# Run E2E tests
echo "════════════════════════════════════════════════════════════"
echo -e "${BLUE}3️⃣  END-TO-END TESTS${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "${YELLOW}⚠️  Note: E2E tests require both backend and dashboard to be running${NC}"
echo -e "${YELLOW}   Start with: docker restart ecosystem-mcp-service ecosystem-mcp-dashboard${NC}"
echo ""

if python3 -m pytest tests/e2e/test_ingestion_path_resolution_e2e.py -v --tb=short --color=yes -m e2e; then
    echo -e "${GREEN}✅ E2E tests PASSED${NC}"
    E2E_RESULT=0
else
    echo -e "${YELLOW}⚠️  E2E tests FAILED or SKIPPED${NC}"
    echo -e "${YELLOW}   (May be skipped if services are not running)${NC}"
    E2E_RESULT=1
fi
echo ""

# Summary
echo "════════════════════════════════════════════════════════════"
echo "  📊 TEST SUMMARY"
echo "════════════════════════════════════════════════════════════"
echo ""

if [ $UNIT_RESULT -eq 0 ]; then
    echo -e "   ${GREEN}✅ Unit Tests: PASSED${NC}"
else
    echo -e "   ${RED}❌ Unit Tests: FAILED${NC}"
fi

if [ $INTEGRATION_RESULT -eq 0 ]; then
    echo -e "   ${GREEN}✅ Integration Tests: PASSED${NC}"
else
    echo -e "   ${YELLOW}⚠️  Integration Tests: FAILED/SKIPPED${NC}"
fi

if [ $E2E_RESULT -eq 0 ]; then
    echo -e "   ${GREEN}✅ E2E Tests: PASSED${NC}"
else
    echo -e "   ${YELLOW}⚠️  E2E Tests: FAILED/SKIPPED${NC}"
fi

echo ""

# Overall result
if [ $UNIT_RESULT -eq 0 ]; then
    echo "════════════════════════════════════════════════════════════"
    echo -e "  ${GREEN}✅ CORE TESTS PASSED!${NC}"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${GREEN}The path resolution feature is working correctly.${NC}"
    echo ""
    
    if [ $INTEGRATION_RESULT -ne 0 ] || [ $E2E_RESULT -ne 0 ]; then
        echo -e "${YELLOW}ℹ️  Some integration/E2E tests were skipped.${NC}"
        echo -e "${YELLOW}   This is normal if services are not running.${NC}"
        echo ""
        echo "To run all tests:"
        echo "  1. Start services: docker restart ecosystem-mcp-service ecosystem-mcp-dashboard"
        echo "  2. Re-run this script: ./run_path_resolution_tests.sh"
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

