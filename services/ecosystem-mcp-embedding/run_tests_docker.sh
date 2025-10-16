#!/bin/bash

# Run containerized tests for embedding service

set -e

echo "======================================================================================================"
echo "🧪 RUNNING CONTAINERIZED TEST SUITE"
echo "======================================================================================================"
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'  # No Color

# Create test results directory
mkdir -p test_results

echo "📦 Building test container..."
docker-compose -f docker-compose.test.yml build

echo
echo "🚀 Starting Redis test instance..."
docker-compose -f docker-compose.test.yml up -d redis-test

echo
echo "⏳ Waiting for Redis to be ready..."
sleep 3

echo
echo "🧪 Running tests..."
docker-compose -f docker-compose.test.yml run --rm test-runner

TEST_EXIT_CODE=$?

echo
echo "🧹 Cleaning up test containers..."
docker-compose -f docker-compose.test.yml down

echo
echo "======================================================================================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
else
    echo -e "${RED}❌ SOME TESTS FAILED (exit code: $TEST_EXIT_CODE)${NC}"
fi
echo "======================================================================================================"
echo
echo "📊 Test Results:"
echo "   • Coverage Report: ./test_results/index.html"
echo "   • Test Report:     ./test_results/test_results.html"
echo "   • JUnit XML:       ./test_results/test_results.xml"
echo

exit $TEST_EXIT_CODE

