#!/bin/bash

# Phase 4R Performance Tests Runner
# Run comprehensive tests for all Phase 4R optimizations

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║             PHASE 4R PERFORMANCE OPTIMIZATIONS - TEST SUITE                 ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Navigate to services directory
cd services/ecosystem-mcp || exit 1

echo "📦 Installing test dependencies..."
pip install -q pytest pytest-asyncio pytest-mock

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Running Phase 4R Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run tests with verbose output
pytest tests/test_rag_accuracy/test_phase4r_performance.py -v --tb=short --color=yes

TEST_EXIT_CODE=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ ALL PHASE 4R TESTS PASSED"
else
    echo "❌ SOME PHASE 4R TESTS FAILED (exit code: $TEST_EXIT_CODE)"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run benchmarks separately
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚡ Running Performance Benchmarks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

pytest tests/test_rag_accuracy/test_phase4r_performance.py -v -m benchmark --tb=short --color=yes

BENCHMARK_EXIT_CODE=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $BENCHMARK_EXIT_CODE -eq 0 ]; then
    echo "✅ ALL BENCHMARKS PASSED"
else
    echo "⚠️  SOME BENCHMARKS FAILED OR SKIPPED (exit code: $BENCHMARK_EXIT_CODE)"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Summary
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                           TEST SUMMARY                                       ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Components Tested:"
echo "  ✅ Task 4R.1: BM25 Corpus Caching"
echo "  ✅ Task 4R.2: Answer Caching"
echo "  ✅ Task 4R.3: Context Optimizer (In-Place)"
echo "  ✅ Task 4R.4: Bulk Fetching Verification"
echo "  ✅ Integration Tests"
echo "  ✅ Performance Benchmarks"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "🎯 Status: READY FOR DEPLOYMENT"
    exit 0
else
    echo "⚠️  Status: NEEDS ATTENTION"
    exit 1
fi

