#!/bin/bash
# Run all performance tests

set -e  # Exit on error

echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║        COMPREHENSIVE PERFORMANCE TEST SUITE                               ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if service is running
echo "🔍 Checking if ecosystem-mcp service is running..."
if ! curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo -e "${RED}❌ Service not running at http://localhost:8000${NC}"
    echo "Please start the service first:"
    echo "  cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp"
    echo "  docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✅ Service is running${NC}"
echo ""

# Offer to use testing config (high rate limits)
echo "📝 Rate Limiting Configuration:"
echo ""
echo "The service has rate limits that prevent testing true throughput:"
echo "  • RAG: 20 queries/minute"
echo "  • Search: 10 queries/minute"
echo ""
echo "Options:"
echo "  1) Test with current rate limits (tests resilience)"
echo "  2) Test with high rate limits (tests capacity)"
echo ""
read -p "Choice [1/2]: " choice

if [ "$choice" == "2" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  To enable high rate limits for testing:${NC}"
    echo ""
    echo "1. Edit your .env file and add:"
    echo "   RAG_RATE_LIMIT=10000/minute"
    echo "   SEARCH_RATE_LIMIT=10000/minute"
    echo "   QUERY_RATE_LIMIT=10000/minute"
    echo ""
    echo "2. Restart the service:"
    echo "   docker-compose restart"
    echo ""
    read -p "Press Enter when ready to continue..."
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "RUNNING TESTS"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Test results
PASSED=0
FAILED=0

# Test 1: Unit Tests
echo "1️⃣  Running Unit Tests..."
echo "───────────────────────────────────────────────────────────────────────────"
if python3 -m pytest tests/unit/test_cache_decorator.py -v; then
    echo -e "${GREEN}✅ Unit tests passed${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Unit tests failed${NC}"
    ((FAILED++))
fi
echo ""

# Test 2: Integration Tests
echo "2️⃣  Running Integration Tests..."
echo "───────────────────────────────────────────────────────────────────────────"
if python3 -m pytest tests/integration/test_caching_integration.py -v -s; then
    echo -e "${GREEN}✅ Integration tests passed${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Integration tests failed${NC}"
    ((FAILED++))
fi
echo ""

# Test 3: Ingestion Rate
echo "3️⃣  Running Ingestion Rate Test..."
echo "───────────────────────────────────────────────────────────────────────────"
if python3 tests/performance/test_ingestion_rate.py; then
    echo -e "${GREEN}✅ Ingestion test passed${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Ingestion test failed${NC}"
    ((FAILED++))
fi
echo ""

# Test 4: Search Throughput
echo "4️⃣  Running Search Throughput Test..."
echo "───────────────────────────────────────────────────────────────────────────"
if python3 tests/performance/test_search_throughput.py; then
    echo -e "${GREEN}✅ Search throughput test passed${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  Search throughput test failed (likely rate limited)${NC}"
    ((FAILED++))
fi
echo ""

# Test 5: RAG Throughput
echo "5️⃣  Running RAG Throughput Test..."
echo "───────────────────────────────────────────────────────────────────────────"
if python3 tests/performance/test_rag_throughput.py; then
    echo -e "${GREEN}✅ RAG throughput test passed${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  RAG throughput test failed (likely rate limited)${NC}"
    ((FAILED++))
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════════════════"
echo "SUMMARY"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Tests Passed: ${PASSED}/5"
echo "Tests Failed: ${FAILED}/5"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! 🎉${NC}"
    exit 0
elif [ $PASSED -ge 2 ]; then
    echo -e "${YELLOW}⚠️  SOME TESTS FAILED${NC}"
    echo ""
    echo "Note: Throughput tests may fail due to rate limiting."
    echo "This is expected in production configuration."
    echo ""
    echo "The important metrics (latency, caching) are verified by unit/integration tests."
    exit 1
else
    echo -e "${RED}❌ MULTIPLE TESTS FAILED${NC}"
    exit 1
fi

