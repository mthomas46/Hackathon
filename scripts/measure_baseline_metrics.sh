#!/bin/bash
#
# Baseline Metrics Measurement Script
#
# Captures pre-implementation metrics for comparison
#

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              Baseline Metrics Measurement                     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
OUTPUT_FILE="baseline_metrics_$(date +%Y%m%d_%H%M%S).json"

echo "📊 Measuring baseline metrics..."
echo "API Base URL: $API_BASE_URL"
echo "Output file: $OUTPUT_FILE"
echo ""

# Helper function to make API calls with timing
measure_endpoint() {
    local endpoint="$1"
    local name="$2"
    
    echo "Testing: $name"
    START=$(date +%s%3N)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL$endpoint" || echo "000")
    END=$(date +%s%3N)
    DURATION=$((END - START))
    
    echo "  Status: $HTTP_CODE"
    echo "  Duration: ${DURATION}ms"
    
    # Store result
    echo "  \"$name\": {\"status\": $HTTP_CODE, \"duration_ms\": $DURATION}," >> "$OUTPUT_FILE"
}

# Start JSON output
echo "{" > "$OUTPUT_FILE"
echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"," >> "$OUTPUT_FILE"
echo "  \"api_base_url\": \"$API_BASE_URL\"," >> "$OUTPUT_FILE"
echo "  \"measurements\": {" >> "$OUTPUT_FILE"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Health Endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
measure_endpoint "/health" "health_check"
measure_endpoint "/api/v1/infrastructure/health" "infrastructure_health"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Database Operations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
measure_endpoint "/api/v1/documents?limit=10" "document_list_10"
measure_endpoint "/api/v1/documents?limit=100" "document_list_100"
measure_endpoint "/api/v1/ingestion/jobs?limit=10" "jobs_list_10"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Temporal RAG Endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
# Note: These require POST with data, so we measure availability
measure_endpoint "/api/v1/temporal/timelines" "temporal_timelines"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Cache Statistics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
measure_endpoint "/api/v1/cache/stats" "cache_stats"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Diagnostics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
measure_endpoint "/api/v1/infrastructure/diagnostics" "diagnostics"
echo ""

# Close JSON
# Remove trailing comma from last measurement
sed -i '' '$ s/,$//' "$OUTPUT_FILE"
echo "  }" >> "$OUTPUT_FILE"
echo "}" >> "$OUTPUT_FILE"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Baseline metrics captured!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📄 Results saved to: $OUTPUT_FILE"
echo ""
echo "📊 To compare with post-implementation metrics:"
echo "   1. Deploy Phase 1 changes"
echo "   2. Run this script again"
echo "   3. Compare the two JSON files"
echo ""

# Pretty print the JSON
if command -v jq &> /dev/null; then
    echo "📈 Summary:"
    jq '.measurements | to_entries | map({name: .key, duration: .value.duration_ms}) | sort_by(.duration) | reverse[]' "$OUTPUT_FILE"
fi

