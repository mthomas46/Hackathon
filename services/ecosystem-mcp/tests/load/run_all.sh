#!/bin/bash
#
# Automated Load Testing Runner
# Runs all load test scenarios and generates reports
#

set -e

echo "════════════════════════════════════════════════════════════════"
echo "🔥 ECOSYSTEM-MCP LOAD TESTING SUITE"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Configuration
HOST="${LOAD_TEST_HOST:-http://localhost:8000}"
REPORT_DIR="tests/load/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create reports directory
mkdir -p "$REPORT_DIR"

echo "Configuration:"
echo "  Host: $HOST"
echo "  Report Directory: $REPORT_DIR"
echo "  Timestamp: $TIMESTAMP"
echo ""

# Function to check if service is ready
check_service() {
    echo "Checking if service is ready..."
    for i in {1..30}; do
        if curl -s "$HOST/health" > /dev/null 2>&1; then
            echo "✅ Service is ready!"
            return 0
        fi
        echo "  Waiting for service... ($i/30)"
        sleep 2
    done
    echo "❌ Service not ready after 60 seconds"
    exit 1
}

# Check service
check_service

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Test 1/4: Baseline Test (1 user, 1 minute)"
echo "════════════════════════════════════════════════════════════════"
echo "Purpose: Establish baseline performance metrics"
echo ""

locust -f tests/load/locustfile.py \
    --host="$HOST" \
    --users 1 \
    --spawn-rate 1 \
    --run-time 1m \
    --headless \
    --html "$REPORT_DIR/baseline_$TIMESTAMP.html" \
    --csv "$REPORT_DIR/baseline_$TIMESTAMP"

echo ""
echo "✅ Baseline test complete!"
echo ""

# Wait between tests
sleep 5

echo "════════════════════════════════════════════════════════════════"
echo "Test 2/4: Sustained Load Test (100 users, 10 minutes)"
echo "════════════════════════════════════════════════════════════════"
echo "Purpose: Validate performance under normal production load"
echo ""

locust -f tests/load/locustfile.py \
    --host="$HOST" \
    --users 100 \
    --spawn-rate 10 \
    --run-time 10m \
    --headless \
    --html "$REPORT_DIR/sustained_$TIMESTAMP.html" \
    --csv "$REPORT_DIR/sustained_$TIMESTAMP"

echo ""
echo "✅ Sustained load test complete!"
echo ""

# Wait between tests
sleep 10

echo "════════════════════════════════════════════════════════════════"
echo "Test 3/4: Spike Test (500 users, 5 minutes)"
echo "════════════════════════════════════════════════════════════════"
echo "Purpose: Test resilience to sudden traffic spikes"
echo ""

locust -f tests/load/locustfile.py \
    --host="$HOST" \
    --users 500 \
    --spawn-rate 50 \
    --run-time 5m \
    --headless \
    --html "$REPORT_DIR/spike_$TIMESTAMP.html" \
    --csv "$REPORT_DIR/spike_$TIMESTAMP"

echo ""
echo "✅ Spike test complete!"
echo ""

# Wait between tests
sleep 10

echo "════════════════════════════════════════════════════════════════"
echo "Test 4/4: Soak Test (50 users, 1 hour)"
echo "════════════════════════════════════════════════════════════════"
echo "Purpose: Detect memory leaks and long-term stability issues"
echo "Note: This test will take 1 hour to complete"
echo ""

locust -f tests/load/locustfile.py \
    --host="$HOST" \
    --users 50 \
    --spawn-rate 5 \
    --run-time 1h \
    --headless \
    --html "$REPORT_DIR/soak_$TIMESTAMP.html" \
    --csv "$REPORT_DIR/soak_$TIMESTAMP"

echo ""
echo "✅ Soak test complete!"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "🎉 ALL LOAD TESTS COMPLETE!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Reports generated:"
echo "  • $REPORT_DIR/baseline_$TIMESTAMP.html"
echo "  • $REPORT_DIR/sustained_$TIMESTAMP.html"
echo "  • $REPORT_DIR/spike_$TIMESTAMP.html"
echo "  • $REPORT_DIR/soak_$TIMESTAMP.html"
echo ""
echo "CSV data:"
echo "  • $REPORT_DIR/baseline_$TIMESTAMP_stats.csv"
echo "  • $REPORT_DIR/sustained_$TIMESTAMP_stats.csv"
echo "  • $REPORT_DIR/spike_$TIMESTAMP_stats.csv"
echo "  • $REPORT_DIR/soak_$TIMESTAMP_stats.csv"
echo ""
echo "Next steps:"
echo "  1. Review HTML reports"
echo "  2. Check for performance issues"
echo "  3. Verify success rates > 95%"
echo "  4. Ensure no memory leaks"
echo ""

