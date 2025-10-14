#!/bin/bash

echo "════════════════════════════════════════════════════════════════════"
echo "🧪 INGESTION PIPELINE DIAGNOSTIC TESTS"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "This test suite will:"
echo "  1. Test Git service file retrieval"
echo "  2. Test document normalizers"
echo "  3. Test database operations"
echo "  4. Test embedding generation"
echo "  5. Test ChromaDB storage"
echo "  6. Run end-to-end single file ingestion"
echo ""
echo "All tests include detailed logging to identify failure points."
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo ""

# Copy test file to container
echo "📦 Copying test file to container..."
docker cp /Users/mykalthomas/Documents/work/Hackathon/tests/test_ingestion_pipeline.py ecosystem-mcp-service:/app/tests/

# Install pytest if not already installed
echo "📦 Ensuring pytest is installed..."
docker exec ecosystem-mcp-service pip install pytest pytest-asyncio --quiet

# Run tests
echo ""
echo "🚀 Running tests..."
echo "════════════════════════════════════════════════════════════════════"
echo ""

docker exec ecosystem-mcp-service python3 -m pytest \
  /app/tests/test_ingestion_pipeline.py \
  -v \
  -s \
  --tb=short \
  --log-cli-level=INFO

EXIT_CODE=$?

echo ""
echo "════════════════════════════════════════════════════════════════════"
if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ ALL TESTS PASSED!"
else
  echo "❌ SOME TESTS FAILED (exit code: $EXIT_CODE)"
fi
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Test Results Summary:"
echo ""
echo "Check the output above for detailed logs showing:"
echo "  • Which component failed"
echo "  • Exact error messages"
echo "  • Stack traces for debugging"
echo ""
echo "════════════════════════════════════════════════════════════════════"

exit $EXIT_CODE

