#!/bin/bash

# Test Runner for Documentation Run Management System
# Runs unit, integration, and E2E tests

set -e

echo "════════════════════════════════════════════════════════════"
echo "  Documentation Run Management System - Test Suite"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! python3 -m pytest --version &> /dev/null; then
    echo -e "${YELLOW}⚠️  pytest not found. Installing...${NC}"
    python3 -m pip install --break-system-packages pytest pytest-asyncio httpx selenium 2>&1 | grep -v "WARNING"
fi

# Test results tracking
UNIT_PASSED=0
INTEGRATION_PASSED=0
E2E_PASSED=0

# ==========================================
# Unit Tests
# ==========================================
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  1️⃣  UNIT TESTS${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

if python3 -m pytest tests/test_documentation_runs.py -v --tb=short; then
    UNIT_PASSED=1
    echo ""
    echo -e "${GREEN}✅ Unit tests PASSED${NC}"
else
    echo ""
    echo -e "${RED}❌ Unit tests FAILED${NC}"
fi

echo ""
echo ""

# ==========================================
# Integration Tests
# ==========================================
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  2️⃣  INTEGRATION TESTS${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}🔍 Checking if services are running...${NC}"

# Check if API is accessible
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API is running${NC}"
    echo ""
    
    if python3 -m pytest tests/integration/test_documentation_runs_integration.py -v --tb=short; then
        INTEGRATION_PASSED=1
        echo ""
        echo -e "${GREEN}✅ Integration tests PASSED${NC}"
    else
        echo ""
        echo -e "${RED}❌ Integration tests FAILED${NC}"
    fi
else
    echo -e "${RED}❌ API is not running at http://localhost:8000${NC}"
    echo -e "${YELLOW}⚠️  Skipping integration tests${NC}"
    echo -e "${YELLOW}   Start services with: docker-compose up -d${NC}"
fi

echo ""
echo ""

# ==========================================
# E2E Tests
# ==========================================
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  3️⃣  END-TO-END TESTS${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}🔍 Checking if dashboard is running...${NC}"

# Check if dashboard is accessible
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Dashboard is running${NC}"
    echo ""
    
    if python3 -m pytest tests/e2e/test_documentation_runs_e2e.py -v --tb=short -s; then
        E2E_PASSED=1
        echo ""
        echo -e "${GREEN}✅ E2E tests PASSED${NC}"
    else
        echo ""
        echo -e "${RED}❌ E2E tests FAILED${NC}"
    fi
else
    echo -e "${RED}❌ Dashboard is not running at http://localhost:8501${NC}"
    echo -e "${YELLOW}⚠️  Skipping E2E tests${NC}"
    echo -e "${YELLOW}   Start services with: docker-compose up -d${NC}"
fi

echo ""
echo ""

# ==========================================
# Test Summary
# ==========================================
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  TEST SUMMARY${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

if [ $UNIT_PASSED -eq 1 ]; then
    echo -e "Unit Tests:        ${GREEN}✅ PASSED${NC}"
else
    echo -e "Unit Tests:        ${RED}❌ FAILED${NC}"
fi

if [ $INTEGRATION_PASSED -eq 1 ]; then
    echo -e "Integration Tests: ${GREEN}✅ PASSED${NC}"
elif curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "Integration Tests: ${RED}❌ FAILED${NC}"
else
    echo -e "Integration Tests: ${YELLOW}⚠️  SKIPPED (services not running)${NC}"
fi

if [ $E2E_PASSED -eq 1 ]; then
    echo -e "E2E Tests:         ${GREEN}✅ PASSED${NC}"
elif curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo -e "E2E Tests:         ${RED}❌ FAILED${NC}"
else
    echo -e "E2E Tests:         ${YELLOW}⚠️  SKIPPED (dashboard not running)${NC}"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

# Exit with appropriate code
TOTAL_TESTS=$(($UNIT_PASSED + $INTEGRATION_PASSED + $E2E_PASSED))

if [ $TOTAL_TESTS -eq 3 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! 🎉${NC}"
    exit 0
elif [ $TOTAL_TESTS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Some tests passed, some failed or skipped${NC}"
    exit 1
else
    echo -e "${RED}❌ ALL TESTS FAILED${NC}"
    exit 1
fi

