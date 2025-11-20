#!/bin/bash
# Test runner script for Adaptive Documentation System
# Usage: ./run_tests.sh [test_type] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Adaptive Documentation System - Test Suite${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Default values
TEST_TYPE="${1:-all}"
VERBOSE="${2:-}"

# Function to run tests
run_tests() {
    local marker=$1
    local description=$2
    
    echo -e "${YELLOW}Running ${description}...${NC}"
    
    if [ "$VERBOSE" == "-v" ] || [ "$VERBOSE" == "--verbose" ]; then
        pytest -m "$marker" -v --tb=short
    else
        pytest -m "$marker" -q
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ${description} passed${NC}"
    else
        echo -e "${RED}❌ ${description} failed${NC}"
        return 1
    fi
    echo ""
}

# Parse command
case $TEST_TYPE in
    all)
        echo -e "${BLUE}Running all tests...${NC}"
        echo ""
        run_tests "unit" "Unit Tests"
        run_tests "integration" "Integration Tests"
        run_tests "functional" "Functional Tests"
        run_tests "e2e" "End-to-End Tests"
        ;;
    
    unit)
        run_tests "unit" "Unit Tests"
        ;;
    
    integration)
        run_tests "integration" "Integration Tests"
        ;;
    
    functional)
        run_tests "functional" "Functional Tests"
        ;;
    
    e2e)
        run_tests "e2e" "End-to-End Tests"
        ;;
    
    smoke)
        echo -e "${YELLOW}Running smoke tests (quick validation)...${NC}"
        pytest -m "smoke" -v --tb=short
        ;;
    
    slow)
        echo -e "${YELLOW}Running slow tests (performance & benchmarks)...${NC}"
        pytest -m "slow" -v --tb=short
        ;;
    
    coverage)
        echo -e "${YELLOW}Running tests with coverage report...${NC}"
        pytest --cov=src --cov-report=html --cov-report=term-missing
        echo -e "${GREEN}Coverage report generated at: coverage_report/index.html${NC}"
        ;;
    
    fast)
        echo -e "${YELLOW}Running fast tests only (excluding slow tests)...${NC}"
        pytest -m "not slow" -q
        ;;
    
    failed)
        echo -e "${YELLOW}Re-running failed tests...${NC}"
        pytest --lf -v
        ;;
    
    specific)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please specify a test file or pattern${NC}"
            echo -e "${YELLOW}Usage: ./run_tests.sh specific <pattern>${NC}"
            echo -e "${YELLOW}Example: ./run_tests.sh specific tests/unit/test_template_manager.py${NC}"
            exit 1
        fi
        echo -e "${YELLOW}Running specific tests: $2${NC}"
        pytest "$2" -v
        ;;
    
    help|--help|-h)
        echo -e "${GREEN}Available test commands:${NC}"
        echo ""
        echo -e "  ${YELLOW}all${NC}          - Run all tests (default)"
        echo -e "  ${YELLOW}unit${NC}         - Run unit tests only"
        echo -e "  ${YELLOW}integration${NC}  - Run integration tests only"
        echo -e "  ${YELLOW}functional${NC}   - Run functional/API tests only"
        echo -e "  ${YELLOW}e2e${NC}          - Run end-to-end tests only"
        echo -e "  ${YELLOW}smoke${NC}        - Run quick smoke tests"
        echo -e "  ${YELLOW}slow${NC}         - Run slow tests (performance, benchmarks)"
        echo -e "  ${YELLOW}coverage${NC}     - Run tests with coverage report"
        echo -e "  ${YELLOW}fast${NC}         - Run fast tests only (exclude slow)"
        echo -e "  ${YELLOW}failed${NC}       - Re-run only failed tests"
        echo -e "  ${YELLOW}specific${NC}     - Run specific test file or pattern"
        echo ""
        echo -e "${GREEN}Options:${NC}"
        echo -e "  ${YELLOW}-v, --verbose${NC}  - Verbose output"
        echo ""
        echo -e "${GREEN}Examples:${NC}"
        echo -e "  ./run_tests.sh                    # Run all tests"
        echo -e "  ./run_tests.sh unit -v            # Run unit tests with verbose output"
        echo -e "  ./run_tests.sh coverage           # Generate coverage report"
        echo -e "  ./run_tests.sh specific tests/unit/test_template_manager.py"
        echo ""
        exit 0
        ;;
    
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo -e "Run './run_tests.sh help' for usage information"
        exit 1
        ;;
esac

# Final summary
if [ $? -eq 0 ]; then
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✅ All tests passed!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ❌ Some tests failed${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
    exit 1
fi

