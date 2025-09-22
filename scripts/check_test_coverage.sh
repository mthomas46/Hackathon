#!/bin/bash

# Test Coverage Check Script
# Checks test coverage across all services in the ecosystem

set -e

echo "📊 Checking Test Coverage..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Services to check
SERVICES=(
    "analysis-service"
    "architecture-digitizer"
    "bedrock-proxy"
    "cli"
    "code-analyzer"
    "discovery-agent"
    "doc_store"
    "frontend"
    "github-mcp"
    "interpreter"
    "llm-gateway"
    "log-collector"
    "memory-agent"
    "mock-data-generator"
    "notification-service"
    "orchestrator"
    "project-simulation"
    "prompt_store"
    "secure-analyzer"
    "simulation-dashboard"
    "data-services-dashboard"
    "source-agent"
    "summarizer-hub"
)

MISSING_TESTS=()
HAS_TESTS=()

echo "🔍 Checking test directories..."
echo "=============================="

TOTAL_SERVICES=${#SERVICES[@]}
SERVICES_WITH_TESTS=0

for service in "${SERVICES[@]}"; do
    test_dir="services/$service/tests"

    if [ -d "$test_dir" ]; then
        # Count test files
        test_count=$(find "$test_dir" -name "test*.py" -type f | wc -l)

        if [ "$test_count" -gt 0 ]; then
            echo -e "${GREEN}✅ $service - $test_count test files${NC}"
            HAS_TESTS+=("$service:$test_count")
            ((SERVICES_WITH_TESTS++))
        else
            echo -e "${YELLOW}⚠️  $service - Has test directory but no test files${NC}"
            MISSING_TESTS+=("$service (empty test dir)")
        fi
    else
        echo -e "${RED}❌ $service - No test directory${NC}"
        MISSING_TESTS+=("$service (no test dir)")
    fi
done

echo ""
echo "📈 Coverage Summary:"
echo "==================="
echo "Total Services: $TOTAL_SERVICES"
echo "Services with Tests: $SERVICES_WITH_TESTS"
echo "Coverage: $((SERVICES_WITH_TESTS * 100 / TOTAL_SERVICES))%"

# Show services with most tests
if [ ${#HAS_TESTS[@]} -gt 0 ]; then
    echo ""
    echo "🏆 Services with Most Tests:"
    printf '%s\n' "${HAS_TESTS[@]}" | sort -t: -k2 -nr | head -5 | while IFS=: read -r service count; do
        echo "  - $service: $count test files"
    done
fi

# Show missing tests
if [ ${#MISSING_TESTS[@]} -gt 0 ]; then
    echo ""
    echo "❌ Services Missing Tests:"
    for service in "${MISSING_TESTS[@]}"; do
        echo "  - $service"
    done
fi

# Recommendations
echo ""
echo "💡 Recommendations:"
if [ ${#MISSING_TESTS[@]} -gt 0 ]; then
    echo "  - Create test directories and basic test files for missing services"
    echo "  - Focus on core services first: orchestrator, doc_store, analysis-service"
    echo "  - Add at least unit tests for each service's main functionality"
fi

# Overall assessment
COVERAGE_PERCENT=$((SERVICES_WITH_TESTS * 100 / TOTAL_SERVICES))
if [ $COVERAGE_PERCENT -ge 80 ]; then
    echo -e "${GREEN}🎉 Excellent test coverage!${NC}"
    exit 0
elif [ $COVERAGE_PERCENT -ge 60 ]; then
    echo -e "${YELLOW}⚠️  Good test coverage, but room for improvement${NC}"
    exit 0
else
    echo -e "${RED}❌ Insufficient test coverage${NC}"
    exit 1
fi
