#!/bin/bash
#
# Start Automatic Cleanup Service
#
# Quick script to start the automatic cleanup service and verify it's running
#

set -e

API_BASE="http://localhost:8000"

echo "================================================================================================="
echo "🤖 STARTING AUTOMATIC CLEANUP SERVICE"
echo "================================================================================================="
echo ""

# Check API connectivity
echo "🔌 Checking API connectivity..."
if ! curl -s --max-time 5 "$API_BASE/health" > /dev/null 2>&1; then
    echo "❌ Cannot connect to API at $API_BASE"
    echo "   Make sure the ecosystem-mcp service is running"
    exit 1
fi
echo "✅ API is accessible"
echo ""

# Start the service
echo "🚀 Starting automatic cleanup service..."
RESULT=$(curl -s -X POST "$API_BASE/api/v1/maintenance/cleanup/start")

if echo "$RESULT" | jq -e '.success == true' > /dev/null 2>&1; then
    echo "✅ Cleanup service started successfully!"
    echo ""
    
    # Show configuration
    echo "📋 Configuration:"
    echo "$RESULT" | jq -r '
        "  Interval: \(.cleanup_interval_minutes) minutes",
        "  Job Retention: \(.job_retention_days) days"
    '
    echo ""
    
elif echo "$RESULT" | jq -e '.success == false' > /dev/null 2>&1; then
    MESSAGE=$(echo "$RESULT" | jq -r '.message')
    if [[ "$MESSAGE" == *"already running"* ]]; then
        echo "✅ Service is already running!"
        echo ""
    else
        echo "⚠️  $MESSAGE"
        echo ""
    fi
else
    echo "❌ Failed to start service"
    echo "$RESULT" | jq '.' || echo "$RESULT"
    exit 1
fi

# Check status
echo "📊 Current Status:"
curl -s "$API_BASE/api/v1/maintenance/cleanup/status" | jq -r '
    "  Status: \(.status)",
    "  Total Cleanups: \(.stats.total_cleanups)",
    "  Jobs Deleted: \(.stats.jobs_deleted)",
    "  Redis Messages Removed: \(.stats.redis_messages_removed)",
    "  Orphaned Jobs Detected: \(.stats.orphaned_jobs_detected)"
'
echo ""

# Offer to run cleanup now
echo "================================================================================================="
echo "💡 Options"
echo "================================================================================================="
echo ""
echo "The service is now running and will clean up automatically every hour."
echo ""
echo "Would you like to run an immediate cleanup now?"
read -p "Run cleanup now? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🧹 Running cleanup now..."
    CLEANUP_RESULT=$(curl -s -X POST "$API_BASE/api/v1/maintenance/cleanup/run-now")
    
    if echo "$CLEANUP_RESULT" | jq -e '.success == true' > /dev/null 2>&1; then
        echo "✅ Cleanup completed!"
        echo ""
        echo "📊 Results:"
        echo "$CLEANUP_RESULT" | jq '.results.tasks' | jq -r '
            to_entries[] |
            "  \(.key): \(.value | if type == "object" then 
                (if has("deleted") then "deleted \(.deleted)" 
                elif has("messages_removed") then "removed \(.messages_removed)" 
                elif has("orphaned_found") then "found \(.orphaned_found)" 
                else . end)
            else . end)"
        '
    else
        echo "❌ Cleanup failed"
        echo "$CLEANUP_RESULT" | jq '.' || echo "$CLEANUP_RESULT"
    fi
fi

echo ""
echo "================================================================================================="
echo "✅ Setup Complete!"
echo "================================================================================================="
echo ""
echo "Your automatic cleanup service is running!"
echo ""
echo "Useful commands:"
echo "  Check status:  curl http://localhost:8000/api/v1/maintenance/cleanup/status | jq"
echo "  View stats:    curl http://localhost:8000/api/v1/maintenance/cleanup/stats | jq"
echo "  Health check:  curl http://localhost:8000/api/v1/maintenance/cleanup/health | jq"
echo "  Run now:       curl -X POST http://localhost:8000/api/v1/maintenance/cleanup/run-now | jq"
echo "  Stop service:  curl -X POST http://localhost:8000/api/v1/maintenance/cleanup/stop | jq"
echo ""
echo "Dashboard: http://localhost:8001"
echo ""
echo "Documentation: See AUTOMATIC_CLEANUP_SYSTEM.md for full details"
echo ""

