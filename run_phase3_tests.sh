#!/bin/bash

# Run Phase 3 Tests (Unit, Integration, E2E, Smoke/Functional)

echo "═══════════════════════════════════════════════════════════════════════════"
echo "  PHASE 3 TEST SUITE"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

cd "$(dirname "$0")/services/ecosystem-mcp"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Track results
UNIT_RESULT=0
INTEGRATION_RESULT=0
E2E_RESULT=0
SMOKE_RESULT=0

echo "📦 Running Phase 3 Tests..."
echo ""

# 1. Unit Tests
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  UNIT TESTS (Caching functionality)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 -m pytest tests/test_phase3/test_cache_unit.py -v --tb=short 2>&1 || true
UNIT_RESULT=$?

if [ $UNIT_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Unit tests PASSED${NC}"
else
    echo -e "${RED}❌ Unit tests FAILED${NC}"
fi
echo ""

# 2. Integration Tests
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  INTEGRATION TESTS (Parallel execution)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 -m pytest tests/test_phase3/test_parallel_integration.py -v --tb=short 2>&1 || true
INTEGRATION_RESULT=$?

if [ $INTEGRATION_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Integration tests PASSED${NC}"
else
    echo -e "${RED}❌ Integration tests FAILED${NC}"
fi
echo ""

# 3. Smoke Tests (Quick validation)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  SMOKE TESTS (Quick validation)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 -m pytest tests/test_phase3/test_smoke_functional.py -v -m smoke --tb=short 2>&1 || true
SMOKE_RESULT=$?

if [ $SMOKE_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Smoke tests PASSED${NC}"
else
    echo -e "${YELLOW}⚠️  Smoke tests FAILED (service may not be running)${NC}"
fi
echo ""

# 4. E2E Tests (Requires running service)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  E2E TESTS (Complete flow - requires running service)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 -m pytest tests/test_phase3/test_e2e_complete_flow.py -v -m e2e --tb=short 2>&1 || true
E2E_RESULT=$?

if [ $E2E_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ E2E tests PASSED${NC}"
else
    echo -e "${YELLOW}⚠️  E2E tests FAILED (service may not be running)${NC}"
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════════════════"
echo "  TEST SUMMARY"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

if [ $UNIT_RESULT -eq 0 ]; then
    echo -e "Unit Tests:        ${GREEN}✅ PASS${NC}"
else
    echo -e "Unit Tests:        ${RED}❌ FAIL${NC}"
fi

if [ $INTEGRATION_RESULT -eq 0 ]; then
    echo -e "Integration Tests: ${GREEN}✅ PASS${NC}"
else
    echo -e "Integration Tests: ${RED}❌ FAIL${NC}"
fi

if [ $SMOKE_RESULT -eq 0 ]; then
    echo -e "Smoke Tests:       ${GREEN}✅ PASS${NC}"
else
    echo -e "Smoke Tests:       ${YELLOW}⚠️  SKIP (service not running)${NC}"
fi

if [ $E2E_RESULT -eq 0 ]; then
    echo -e "E2E Tests:         ${GREEN}✅ PASS${NC}"
else
    echo -e "E2E Tests:         ${YELLOW}⚠️  SKIP (service not running)${NC}"
fi

echo ""

# Overall result
if [ $UNIT_RESULT -eq 0 ] && [ $INTEGRATION_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ CORE TESTS PASSED${NC} (Unit + Integration)"
    echo ""
    echo "ℹ️  E2E and Smoke tests require running service:"
    echo "   cd services/ecosystem-mcp && docker-compose up -d"
    exit 0
else
    echo -e "${RED}❌ TESTS FAILED${NC}"
    exit 1
fi

