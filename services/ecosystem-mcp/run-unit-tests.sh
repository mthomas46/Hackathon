#!/bin/bash
# Run unit and integration tests WITHOUT Docker

echo "🧪 Running Unit & Integration Tests (No Docker Required)..."
echo ""

cd "$(dirname "$0")"
source venv/bin/activate

echo "📊 1/2: Running critical data isolation tests..."
pytest tests/unit/test_data_isolation.py -v --tb=short

echo ""
echo "📊 2/2: Running all unit tests..."
pytest tests/unit/ --ignore=tests/unit/test_cache_decorator.py -q

echo ""
echo "✅ Unit tests complete!"
echo ""
echo "Next: Run functional tests with Docker using:"
echo "  ./run-functional-tests.sh"

