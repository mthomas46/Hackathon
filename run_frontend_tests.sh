#!/bin/bash

# Run Frontend Feedback Tests
# Tests embeddings, LLM tiers, documentation generation, and error handling

echo "🧪 Running Frontend Feedback Tests"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found${NC}"
    echo "Installing pytest..."
    pip install pytest pytest-asyncio
fi

# Navigate to project root
cd "$(dirname "$0")"

echo "📋 Test Plan:"
echo "  - Unit Tests: Embeddings regeneration logic"
echo "  - Integration Tests: API endpoints and LLM tier fallback"
echo "  - E2E Tests: Documentation generation workflow"
echo "  - Error Handling: Timeouts, retries, fallbacks"
echo ""

# Run tests with verbose output
echo "🚀 Running tests..."
echo ""

pytest tests/test_frontend_feedback.py \
    -v \
    --tb=short \
    --color=yes \
    -W ignore::DeprecationWarning \
    2>&1 | tee /tmp/frontend_tests.log

TEST_EXIT_CODE=$?

echo ""
echo "=================================="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "📊 Summary:"
    grep -E "passed|failed|error" /tmp/frontend_tests.log | tail -1
    echo ""
    echo "📋 Next steps:"
    echo "  1. Deploy fixes to dashboard container"
    echo "  2. Verify in browser at http://localhost:8501"
    echo "  3. Test documentation generation with desktop tier"
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "📋 Failed tests:"
    grep -E "FAILED|ERROR" /tmp/frontend_tests.log || echo "  Check /tmp/frontend_tests.log for details"
    echo ""
    echo "💡 Troubleshooting:"
    echo "  - Check if services are running (docker ps)"
    echo "  - Verify API is accessible (curl http://localhost:8000/api/v1/health)"
    echo "  - Review test output in /tmp/frontend_tests.log"
fi

echo ""
echo "📄 Full log: /tmp/frontend_tests.log"

exit $TEST_EXIT_CODE

