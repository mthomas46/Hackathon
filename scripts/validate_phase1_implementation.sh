#!/bin/bash
#
# Phase 1 Implementation Validation Script
#
# Tests all 7 quick wins to ensure proper implementation
#

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           Phase 1 Implementation Validation                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to check test result
check_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $1"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $1"
        ((TESTS_FAILED++))
    fi
}

echo "📋 Running validation tests..."
echo ""

# Test 1.1: Database Pool Sizing
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1.1: Database Connection Pool Sizing"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
grep -q "pool_size = max(settings.database_pool_size, optimal_pool_size)" services/ecosystem-mcp/src/storage/database.py
check_result "Dynamic pool sizing code present"

grep -q "WORKER_COUNT" services/ecosystem-mcp/src/storage/database.py
check_result "WORKER_COUNT environment variable support"

grep -q "self.pool_size" services/ecosystem-mcp/src/storage/database.py
check_result "Pool size tracking"
echo ""

# Test 1.2: Redis Connection Pooling
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1.2: Redis Connection Pooling"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
grep -q "_connection_pool.*ConnectionPool" services/ecosystem-mcp/src/utils/redis_client.py
check_result "Connection pool class variable"

grep -q "_get_or_create_pool" services/ecosystem-mcp/src/utils/redis_client.py
check_result "Pool creation method"

grep -q "get_pool_stats" services/ecosystem-mcp/src/utils/redis_client.py
check_result "Pool stats method"
echo ""

# Test 1.3: Embedding Service Circuit Breaker
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1.3: Embedding Service Circuit Breaker"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
[ -f "services/ecosystem-mcp-embedding/src/utils/circuit_breaker.py" ]
check_result "Circuit breaker utility copied"

grep -q "from.*circuit_breaker import" services/ecosystem-mcp-embedding/src/services/fastembed_service.py
check_result "Circuit breaker imported"

grep -q "self.circuit_breaker = CircuitBreaker" services/ecosystem-mcp-embedding/src/services/fastembed_service.py
check_result "Circuit breaker initialized"
echo ""

# Test 1.4: ChromaDB Lock Monitoring
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1.4: ChromaDB Write Lock Monitoring"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
grep -q "_lock_wait_times" services/ecosystem-mcp/src/storage/chromadb_client.py
check_result "Lock wait times tracking"

grep -q "get_lock_stats" services/ecosystem-mcp/src/storage/chromadb_client.py
check_result "Lock stats method"

grep -q "p95.*percentile" services/ecosystem-mcp/src/storage/chromadb_client.py
check_result "Percentile calculations"
echo ""

# Test 1.5: Request ID Propagation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1.5: Request ID Propagation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
grep -q "X-Request-ID" services/ecosystem-mcp/src/api/middleware/request_id.py
check_result "Request ID middleware exists"

grep -q "structlog" services/ecosystem-mcp/src/api/middleware/request_id.py
check_result "Structlog integration"
echo ""

# Test 1.6: Database Query Indexes
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1.6: Database Query Indexes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
[ -f "services/ecosystem-mcp/src/storage/migrations/013_add_temporal_rag_indexes.py" ]
check_result "Migration file created"

grep -q "idx_documents_git_date" services/ecosystem-mcp/src/storage/migrations/013_add_temporal_rag_indexes.py
check_result "Temporal index defined"

grep -q "CREATE INDEX CONCURRENTLY" services/ecosystem-mcp/src/storage/migrations/013_add_temporal_rag_indexes.py
check_result "Concurrent index creation"
echo ""

# Test 1.7: Dashboard API Cache
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1.7: Dashboard API Deduplication"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
[ -f "services/ecosystem-mcp-dashboard/utils/api_cache.py" ]
check_result "API cache utility created"

grep -q "class APICache" services/ecosystem-mcp-dashboard/utils/api_cache.py
check_result "APICache class defined"

grep -q "@cached_api_call" services/ecosystem-mcp-dashboard/utils/api_cache.py
check_result "Cache decorator defined"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 VALIDATION SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Tests Failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All validation tests passed!${NC}"
    echo -e "${GREEN}Phase 1 implementation is ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some validation tests failed.${NC}"
    echo -e "${YELLOW}Please review the failures above before deploying.${NC}"
    exit 1
fi

