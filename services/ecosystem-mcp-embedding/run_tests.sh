#!/bin/bash

# Comprehensive test runner for embedding service
# Runs unit, integration, E2E, and smoke tests

set -e

echo "======================================================================================================"
echo "🧪 EMBEDDING SERVICE TEST SUITE"
echo "======================================================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if service is running
echo "Checking if embedding service is running..."
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Service is running${NC}"
else
    echo -e "${RED}❌ Service is not running${NC}"
    echo "Please start the service with: docker-compose up -d embedding-service"
    exit 1
fi
echo ""

# Run smoke tests first
echo "======================================================================================================"
echo "🔥 Running Smoke Tests"
echo "======================================================================================================"
python tests/smoke_tests.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Smoke tests passed${NC}"
else
    echo -e "${RED}❌ Smoke tests failed${NC}"
    exit 1
fi
echo ""

# Run unit tests
echo "======================================================================================================"
echo "🔬 Running Unit Tests"
echo "======================================================================================================"
pytest tests/unit/ -v --tb=short
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Unit tests passed${NC}"
else
    echo -e "${RED}❌ Unit tests failed${NC}"
    exit 1
fi
echo ""

# Run integration tests
echo "======================================================================================================"
echo "🔗 Running Integration Tests"
echo "======================================================================================================"
pytest tests/integration/ -v --tb=short
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Integration tests passed${NC}"
else
    echo -e "${RED}❌ Integration tests failed${NC}"
    exit 1
fi
echo ""

# Run E2E tests
echo "======================================================================================================"
echo "🌐 Running End-to-End Tests"
echo "======================================================================================================"
pytest tests/e2e/ -v --tb=short
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ E2E tests passed${NC}"
else
    echo -e "${RED}❌ E2E tests failed${NC}"
    exit 1
fi
echo ""

# Generate coverage report
echo "======================================================================================================"
echo "📊 Generating Coverage Report"
echo "======================================================================================================"
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
echo ""

# Summary
echo "======================================================================================================"
echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
echo "======================================================================================================"
echo ""
echo "Coverage report available at: htmlcov/index.html"
echo ""

