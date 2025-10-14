#!/bin/bash
# Run all tests for fixes implemented in this session

set -e

echo "════════════════════════════════════════════════════════════════════"
echo "Running Tests for Session Fixes"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "This test suite covers:"
echo "  1. Redis connection lazy loading fix"
echo "  2. Auto-refresh tab context preservation"
echo "  3. Worker monitoring and auto-recovery"
echo "  4. Job management (cancel, clear)"
echo "  5. End-to-end ingestion flow"
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to run test suite
run_tests() {
    local test_file=$1
    local test_name=$2
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Running: $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if pytest "$test_file" -v --tb=short --color=yes 2>&1; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        return 1
    fi
}

# Track results
TOTAL=0
PASSED=0
FAILED=0

# Test 1: Redis Connection Tests (Unit + Integration)
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "TEST SUITE 1: Redis Connection Fix"
echo "═══════════════════════════════════════════════════════════════════"
if run_tests "tests/test_redis_connection.py" "Redis Connection & Lazy Loading"; then
    ((PASSED++))
else
    ((FAILED++))
fi
((TOTAL++))

# Test 2: Dashboard Fixes (Unit)
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "TEST SUITE 2: Dashboard Fixes"
echo "═══════════════════════════════════════════════════════════════════"
if run_tests "tests/test_dashboard_fixes.py" "Dashboard Auto-Refresh & Navigation"; then
    ((PASSED++))
else
    ((FAILED++))
fi
((TOTAL++))

# Test 3: E2E Ingestion Tests (Integration - requires Docker)
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "TEST SUITE 3: End-to-End Ingestion Flow"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo -e "${YELLOW}⚠️  This test suite requires Docker services to be running:${NC}"
echo "  • ecosystem-mcp-service"
echo "  • ecosystem-mcp-redis"
echo "  • ecosystem-mcp-postgres"
echo ""
read -p "Run E2E tests? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if run_tests "tests/test_ingestion_e2e.py" "End-to-End Ingestion"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
    ((TOTAL++))
else
    echo -e "${YELLOW}⏭️  Skipped E2E tests${NC}"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "TEST SUMMARY"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "Total Test Suites: $TOTAL"
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
else
    echo -e "Failed: $FAILED"
fi
echo ""

# Exit code
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
fi

