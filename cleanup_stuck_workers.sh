#!/bin/bash
#
# Cleanup Script for Stuck Workers
#
# Cleans up stale Redis messages and verifies system health
#

set -e

API_BASE="http://localhost:8000"
DASHBOARD_URL="http://localhost:8001"

echo "================================================================================================="
echo "🧹 STUCK WORKERS CLEANUP SCRIPT"
echo "================================================================================================="
echo "Date: $(date)"
echo "API Base: $API_BASE"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo "ℹ️  $1"
}

# Check if API is accessible
echo "🔌 Step 1: Testing API connectivity..."
echo "---------------------------------"
if curl -s --max-time 5 "$API_BASE/health" > /dev/null 2>&1; then
    print_success "API is accessible"
else
    print_error "Cannot connect to API at $API_BASE"
    print_info "Make sure the ecosystem-mcp service is running: docker ps | grep ecosystem-mcp-service"
    exit 1
fi
echo ""

# Show current status
echo "📊 Step 2: Current system status"
echo "---------------------------------"
echo "Redis Stream Status:"
curl -s "$API_BASE/api/v1/admin/redis/stream-status" | jq -r '
  .status.ingestion_stream | 
  "  Length: \(.length // "N/A")\n  Groups: \(.groups // "N/A")"
' 2>/dev/null || print_warning "Could not get stream status"

curl -s "$API_BASE/api/v1/admin/redis/stream-status" | jq -r '
  .status.pending_messages | 
  "  Pending: \(.count // "N/A")"
' 2>/dev/null || true
echo ""

echo "Job Status:"
curl -s "$API_BASE/api/v1/admin/ingest/status" | jq -r '
  "  Total jobs: \(.total // 0)",
  "  By status:",
  (.jobs | group_by(.status) | .[] | "    \(.[0].status): \(length)")
' 2>/dev/null || print_warning "Could not get job status"
echo ""

echo "Worker Health:"
curl -s "$API_BASE/api/v1/admin/workers/health" | jq -r '
  .workers.ingestion | 
  "  Running: \(.running // false)\n  Healthy: \(.healthy // false)\n  Processing: \(.processing // false)"
' 2>/dev/null || print_warning "Could not get worker health"
echo ""

# Check for stuck workers
echo "🔍 Step 3: Checking for stuck workers..."
echo "---------------------------------"
STUCK_COUNT=$(curl -s "$API_BASE/api/v1/admin/workers/stuck-check" | jq -r '.stuck_workers // 0' 2>/dev/null)
if [ "$STUCK_COUNT" -gt 0 ]; then
    print_warning "Found $STUCK_COUNT stuck workers"
    curl -s "$API_BASE/api/v1/admin/workers/stuck-check" | jq '.stuck_jobs' || true
else
    print_success "No stuck workers detected"
fi
echo ""

# Check queue health
echo "🏥 Step 4: Checking queue health..."
echo "---------------------------------"
QUEUE_HEALTH=$(curl -s "$API_BASE/api/v1/admin/redis/queue-health" 2>/dev/null)
if echo "$QUEUE_HEALTH" | jq -e '.healthy == true' > /dev/null 2>&1; then
    print_success "Queue is healthy"
else
    print_warning "Queue health issues detected"
    echo "$QUEUE_HEALTH" | jq '{
        healthy,
        orphaned_messages: .orphaned_messages | length,
        missing_messages: .missing_messages | length,
        warnings
    }' || true
fi
echo ""

# Cleanup orphaned messages
echo "🧹 Step 5: Cleaning up orphaned Redis messages..."
echo "---------------------------------"
print_info "This will remove Redis messages for jobs that no longer exist in the database"
read -p "Proceed with cleanup? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Cleaning up orphaned messages..."
    CLEANUP_RESULT=$(curl -s -X POST "$API_BASE/api/v1/admin/redis/cleanup-orphaned" 2>/dev/null)
    
    MESSAGES_REMOVED=$(echo "$CLEANUP_RESULT" | jq -r '.messages_removed // 0')
    MESSAGES_CHECKED=$(echo "$CLEANUP_RESULT" | jq -r '.messages_checked // 0')
    
    if [ "$MESSAGES_REMOVED" -gt 0 ]; then
        print_success "Removed $MESSAGES_REMOVED of $MESSAGES_CHECKED messages"
    elif [ "$MESSAGES_CHECKED" -gt 0 ]; then
        print_success "Checked $MESSAGES_CHECKED messages, none needed removal"
    else
        print_warning "No messages found to clean"
    fi
    
    # Show any errors
    ERRORS=$(echo "$CLEANUP_RESULT" | jq -r '.errors | length')
    if [ "$ERRORS" -gt 0 ]; then
        print_warning "$ERRORS errors occurred:"
        echo "$CLEANUP_RESULT" | jq '.errors' || true
    fi
else
    print_info "Skipping cleanup"
fi
echo ""

# Clear pending messages
echo "🔄 Step 6: Checking pending messages..."
echo "---------------------------------"
PENDING_COUNT=$(curl -s "$API_BASE/api/v1/admin/redis/stream-status" | jq -r '.status.pending_messages.count // 0' 2>/dev/null)
if [ "$PENDING_COUNT" -gt 0 ]; then
    print_warning "Found $PENDING_COUNT pending messages"
    print_info "Pending messages are claimed by workers but not acknowledged"
    echo ""
    read -p "Attempt to recover pending messages? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Recovering pending messages..."
        # Note: This endpoint may need to be implemented
        curl -s -X POST "$API_BASE/api/v1/admin/redis/recover-pending" 2>/dev/null || \
            print_warning "Pending message recovery not available via API"
    fi
else
    print_success "No pending messages"
fi
echo ""

# Check if we should restart worker
echo "🔧 Step 7: Worker recovery check..."
echo "---------------------------------"
WORKER_HEALTHY=$(curl -s "$API_BASE/api/v1/admin/workers/health" | jq -r '.workers.ingestion.healthy // false' 2>/dev/null)
if [ "$WORKER_HEALTHY" = "false" ]; then
    print_warning "Worker is unhealthy"
    echo ""
    read -p "Attempt auto-recovery? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Running auto-recovery..."
        curl -s -X POST "$API_BASE/api/v1/admin/workers/ingestion/auto-recover" | jq || true
    fi
else
    print_success "Worker is healthy"
fi
echo ""

# Final status check
echo "📊 Step 8: Final status check"
echo "---------------------------------"
echo "Redis Stream:"
curl -s "$API_BASE/api/v1/admin/redis/stream-status" | jq -r '
  .status.ingestion_stream | 
  "  Length: \(.length // "N/A")\n  Pending: \(.groups // 0)"
' 2>/dev/null || true
echo ""

echo "Jobs by Status:"
curl -s "$API_BASE/api/v1/admin/ingest/status" | jq -r '
  (.jobs | group_by(.status) | .[] | "  \(.[0].status): \(length)")
' 2>/dev/null || true
echo ""

# Suggestions
echo "================================================================================================="
echo "💡 Next Steps & Recommendations"
echo "================================================================================================="
echo ""
echo "1. Monitor the dashboard: $DASHBOARD_URL"
echo "   - Go to 'Worker Monitor' to check worker health"
echo "   - Go to 'Ingestion Manager' to view job status"
echo ""
echo "2. Test with a new ingestion job:"
echo "   curl -X POST $API_BASE/api/v1/admin/ingest \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"repo_path\": \"/host\", \"mode\": \"quick\", \"processing_mode\": \"snapshot\"}'"
echo ""
echo "3. View recent logs:"
echo "   docker logs ecosystem-mcp-service --tail 100"
echo ""
echo "4. If problems persist:"
echo "   - Check worker logs: docker logs ecosystem-mcp-service -f"
echo "   - Restart worker: curl -X POST $API_BASE/api/v1/admin/workers/ingestion/restart"
echo "   - Restart container: docker restart ecosystem-mcp-service"
echo ""
print_success "Cleanup complete!"

