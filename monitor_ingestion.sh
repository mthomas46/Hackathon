#!/bin/bash
#
# Monitor Ingestion Job in Real-Time
#

API_BASE="http://localhost:8000"
JOB_ID="$1"

if [ -z "$JOB_ID" ]; then
    echo "Usage: $0 <job_id>"
    exit 1
fi

echo "================================================================================================="
echo "📊 MONITORING INGESTION JOB"
echo "================================================================================================="
echo "Job ID: $JOB_ID"
echo "Started: $(date)"
echo ""

# Monitor loop
LAST_PROCESSED=0
LAST_STATUS=""
ITERATION=0

while true; do
    ((ITERATION++))
    
    # Get job status
    RESPONSE=$(curl -s "$API_BASE/api/v1/admin/ingest/status")
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to connect to API"
        sleep 5
        continue
    fi
    
    # Extract job info
    JOB=$(echo "$RESPONSE" | jq -r ".jobs[] | select(.job_id==\"$JOB_ID\")")
    
    if [ -z "$JOB" ] || [ "$JOB" = "null" ]; then
        echo "❌ Job not found: $JOB_ID"
        exit 1
    fi
    
    STATUS=$(echo "$JOB" | jq -r '.status')
    PROCESSED=$(echo "$JOB" | jq -r '.processed_documents // 0')
    TOTAL=$(echo "$JOB" | jq -r '.total_documents // 0')
    SKIPPED=$(echo "$JOB" | jq -r '.skipped_documents // 0')
    FAILED=$(echo "$JOB" | jq -r '.failed_documents // 0')
    EMBEDDINGS=$(echo "$JOB" | jq -r '.embeddings_generated // 0')
    
    # Clear line and show progress
    if [ "$STATUS" = "processing" ]; then
        if [ $TOTAL -gt 0 ]; then
            PROGRESS=$((PROCESSED * 100 / TOTAL))
            EXAMINED=$((PROCESSED + SKIPPED + FAILED))
            
            # Show progress bar
            FILLED=$((PROGRESS / 2))
            BAR=$(printf "%-50s" "$(printf '#%.0s' $(seq 1 $FILLED))")
            
            printf "\r[%-50s] %3d%% | 📄 New: %d | 📊 Total: %d | ⏭️ Dup: %d | ❌ Err: %d | 🧬 Emb: %d" \
                "$BAR" "$PROGRESS" "$PROCESSED" "$TOTAL" "$SKIPPED" "$FAILED" "$EMBEDDINGS"
        else
            printf "\r🔍 Scanning... | 📄 Processed: %d | ⏭️ Skipped: %d | ❌ Failed: %d | 🧬 Embeddings: %d" \
                "$PROCESSED" "$SKIPPED" "$FAILED" "$EMBEDDINGS"
        fi
        
        # Show status change
        if [ "$STATUS" != "$LAST_STATUS" ]; then
            echo ""
            echo "📌 Status: $STATUS"
        fi
        
        LAST_STATUS="$STATUS"
        LAST_PROCESSED=$PROCESSED
        
        sleep 3
    else
        # Job finished
        echo ""
        echo ""
        echo "================================================================================================="
        echo "✅ JOB COMPLETE"
        echo "================================================================================================="
        echo "Status: $STATUS"
        echo ""
        echo "📊 Final Statistics:"
        echo "  Processed:  $PROCESSED documents"
        echo "  Total:      $TOTAL documents"
        echo "  Skipped:    $SKIPPED duplicates"
        echo "  Failed:     $FAILED errors"
        echo "  Embeddings: $EMBEDDINGS generated"
        echo ""
        
        if [ $TOTAL -gt 0 ]; then
            UNIQUENESS=$((PROCESSED * 100 / (PROCESSED + SKIPPED)))
            echo "💎 Uniqueness: ${UNIQUENESS}%"
        fi
        
        ERROR_MSG=$(echo "$JOB" | jq -r '.error_message // ""')
        if [ -n "$ERROR_MSG" ] && [ "$ERROR_MSG" != "null" ]; then
            echo ""
            echo "❌ Error: $ERROR_MSG"
        fi
        
        echo ""
        echo "Completed: $(date)"
        break
    fi
done
