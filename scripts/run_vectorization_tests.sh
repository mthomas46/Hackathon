#!/bin/bash
#
# Run Vectorization/Semantic Search TDD Tests
#
# Usage:
#   ./scripts/run_vectorization_tests.sh [options]
#
# Options:
#   --unit         Run only unit tests (default)
#   --integration  Run only integration tests
#   --all          Run all tests
#   --coverage     Run with coverage report
#   --verbose      Verbose output
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default options
TEST_TYPE="unit"
COVERAGE=false
VERBOSE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --all)
            TEST_TYPE="all"
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE="-v"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}Running Vectorization/Semantic Search Tests${NC}"
echo "=============================================="
echo ""

# Activate virtual environment if exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Set test environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export TEST_ENV="true"

# Build pytest command
PYTEST_CMD="pytest"

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=services/doc_store/db --cov=services/doc_store/domain/embeddings --cov-report=html --cov-report=term"
fi

# Add verbosity
PYTEST_CMD="$PYTEST_CMD $VERBOSE"

# Run tests based on type
case $TEST_TYPE in
    unit)
        echo -e "${YELLOW}Running Unit Tests...${NC}"
        $PYTEST_CMD tests/unit/doc_store/test_vector_queries.py \
                    tests/unit/doc_store/test_embedding_service.py \
                    tests/unit/doc_store/test_embedding_api.py \
                    -m "not integration"
        ;;
    integration)
        echo -e "${YELLOW}Running Integration Tests...${NC}"
        echo "Note: Integration tests require database and embedding models"
        export RUN_INTEGRATION_TESTS=true
        $PYTEST_CMD tests/integration/test_semantic_search_workflow.py \
                    -m "integration"
        ;;
    all)
        echo -e "${YELLOW}Running All Tests...${NC}"
        
        echo ""
        echo "1. Unit Tests"
        echo "-------------"
        $PYTEST_CMD tests/unit/doc_store/test_vector_queries.py \
                    tests/unit/doc_store/test_embedding_service.py \
                    tests/unit/doc_store/test_embedding_api.py \
                    -m "not integration"
        
        echo ""
        echo "2. Integration Tests"
        echo "--------------------"
        export RUN_INTEGRATION_TESTS=true
        $PYTEST_CMD tests/integration/test_semantic_search_workflow.py \
                    -m "integration"
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
    
    if [ "$COVERAGE" = true ]; then
        echo ""
        echo "Coverage report generated in htmlcov/index.html"
    fi
else
    echo ""
    echo -e "${RED}✗ Tests failed${NC}"
    exit 1
fi

