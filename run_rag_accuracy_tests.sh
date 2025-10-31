#!/bin/bash
#
# Run RAG Accuracy Phase 1 Test Suite
#
# Runs unit, integration, and E2E tests

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║           RAG ACCURACY PHASE 1 TEST SUITE                                   ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")/services/ecosystem-mcp"

echo "📦 Installing test dependencies..."
pip install pytest pytest-asyncio pytest-mock httpx -q

echo ""
echo "=" * 80
echo "UNIT TESTS"
echo "=" * 80
echo ""

echo "🧪 Running BM25 Search tests..."
python -m pytest tests/test_rag_accuracy/test_bm25_search.py -v --tb=short || true

echo ""
echo "🧪 Running Query Rewriter tests..."
python -m pytest tests/test_rag_accuracy/test_query_rewriter.py -v --tb=short || true

echo ""
echo "🧪 Running Confidence Scorer tests..."
python -m pytest tests/test_rag_accuracy/test_confidence_scorer.py -v --tb=short || true

echo ""
echo "=" * 80
echo "INTEGRATION TESTS"
echo "=" * 80
echo ""

echo "🧪 Running Hybrid Search integration tests..."
python -m pytest tests/test_rag_accuracy/test_hybrid_search_integration.py -v --tb=short -m integration || true

echo ""
echo "=" * 80
echo "E2E TESTS (requires running API)"
echo "=" * 80
echo ""

echo "🧪 Running API endpoint tests..."
python -m pytest tests/test_rag_accuracy/test_api_endpoints_e2e.py -v --tb=short -m e2e || true

echo ""
echo "=" * 80
echo "TEST SUMMARY"
echo "=" * 80
echo ""

# Run all tests with summary
python -m pytest tests/test_rag_accuracy/ -v --tb=short --co -q 2>/dev/null | grep "test_" | wc -l | xargs echo "Total tests found:"

echo ""
echo "✅ Test run complete!"
echo ""
echo "📝 To run specific test categories:"
echo "   Unit tests only:        pytest tests/test_rag_accuracy/ -v -m 'not integration and not e2e'"
echo "   Integration tests:      pytest tests/test_rag_accuracy/ -v -m integration"
echo "   E2E tests:              pytest tests/test_rag_accuracy/ -v -m e2e"
echo "   All tests:              pytest tests/test_rag_accuracy/ -v"
echo ""

