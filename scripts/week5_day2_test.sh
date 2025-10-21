#!/bin/bash
#
# Week 5, Day 2: Large-Scale Ingestion Test
# Using curl for API calls to avoid Python dependency issues
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
API_BASE="http://localhost:8000"
REPO_PATH="/repo"

# Helpers
print_header() {
    echo -e "\n${BOLD}${CYAN}================================================================================================${NC}"
    echo -e "${BOLD}${CYAN}$1${NC}"
    echo -e "${BOLD}${CYAN}================================================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_metric() {
    printf "  ${BLUE}%-40s${NC} ${BOLD}%s${NC}\n" "$1" "$2"
}

# Step 1: Health Check
print_header "WEEK 5, DAY 2: LARGE-SCALE INGESTION TEST"

echo -e "${BOLD}Test Configuration:${NC}"
print_metric "API Base URL:" "$API_BASE"
print_metric "Repository Path:" "$REPO_PATH"
print_metric "Expected Files:" "~36,713"
echo ""

print_header "STEP 1: HEALTH CHECK"

print_info "Checking API health..."
HEALTH=$(curl -s "$API_BASE/health")
if echo "$HEALTH" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    print_success "API is healthy"
    echo "$HEALTH" | jq -r '.components | to_entries[] | "  ✅ \(.key): \(.value.status)"'
else
    print_error "API is not healthy"
    exit 1
fi

# Step 2: Start Ingestion
print_header "STEP 2: START INGESTION JOB"

print_info "Preparing ingestion request..."
PAYLOAD='{
  "repo_path": "'$REPO_PATH'",
  "use_git_history": false,
  "force_reingest": false,
  "snapshot_mode": true
}'

echo "$PAYLOAD" | jq '.'

print_info "Sending POST request to /api/v1/admin/ingest..."
RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/admin/ingest" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

echo "$RESPONSE" | jq '.'

if echo "$RESPONSE" | jq -e '.job_id' > /dev/null 2>&1; then
    JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')
    JOB_STATUS=$(echo "$RESPONSE" | jq -r '.status')
    print_success "Ingestion job started!"
    print_metric "Job ID:" "$JOB_ID"
    print_metric "Initial Status:" "$JOB_STATUS"
else
    print_error "Failed to start ingestion"
    echo "$RESPONSE" | jq '.'
    exit 1
fi

# Step 3: Monitor Progress
print_header "STEP 3: MONITOR INGESTION PROGRESS"

print_info "Monitoring job: $JOB_ID"
print_info "Update interval: 10 seconds"
print_info "Press Ctrl+C to stop monitoring (job will continue)"
echo ""

START_TIME=$(date +%s)
ITERATION=0
LAST_PROCESSED=0

while true; do
    ITERATION=$((ITERATION + 1))
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    # Get job status
    STATUS=$(curl -s "$API_BASE/api/v1/admin/ingest/$JOB_ID")
    
    if [ $? -ne 0 ]; then
        print_warning "Could not retrieve job status"
        sleep 10
        continue
    fi
    
    # Parse status
    JOB_STATUS=$(echo "$STATUS" | jq -r '.status // "unknown"')
    TOTAL_FILES=$(echo "$STATUS" | jq -r '.total_files // 0')
    PROCESSED_FILES=$(echo "$STATUS" | jq -r '.processed_files // 0')
    FAILED_FILES=$(echo "$STATUS" | jq -r '.failed_files // 0')
    TOTAL_EMBEDDINGS=$(echo "$STATUS" | jq -r '.total_embeddings // 0')
    
    # Print update
    if [ $ITERATION -gt 1 ]; then
        echo ""
        echo "────────────────────────────────────────────────────────────────────────────────"
        echo ""
    fi
    
    echo -e "${BOLD}📊 Job Status Update #$ITERATION${NC}"
    echo "  Time: $(date '+%H:%M:%S')"
    echo "  Elapsed: ${ELAPSED}s"
    echo ""
    
    # Status
    case $JOB_STATUS in
        "pending") STATUS_EMOJI="⏳" ;;
        "processing") STATUS_EMOJI="🔄" ;;
        "completed") STATUS_EMOJI="✅" ;;
        "failed") STATUS_EMOJI="❌" ;;
        *) STATUS_EMOJI="❓" ;;
    esac
    
    echo -e "${BOLD}Status:${NC} $STATUS_EMOJI $JOB_STATUS"
    
    # Progress
    if [ "$TOTAL_FILES" != "0" ] && [ "$TOTAL_FILES" != "null" ]; then
        PROGRESS_PCT=$(echo "scale=1; ($PROCESSED_FILES / $TOTAL_FILES) * 100" | bc)
        echo -e "${BOLD}Progress:${NC} $PROCESSED_FILES/$TOTAL_FILES files ($PROGRESS_PCT%)"
        
        # Progress bar
        BAR_WIDTH=50
        FILLED=$(echo "scale=0; ($BAR_WIDTH * $PROCESSED_FILES) / $TOTAL_FILES" | bc)
        EMPTY=$((BAR_WIDTH - FILLED))
        BAR=$(printf "█%.0s" $(seq 1 $FILLED))$(printf "░%.0s" $(seq 1 $EMPTY))
        echo "  [$BAR]"
    else
        echo -e "${BOLD}Progress:${NC} $PROCESSED_FILES files processed"
    fi
    
    echo ""
    
    # Performance
    if [ "$PROCESSED_FILES" != "0" ] && [ "$ELAPSED" -gt "0" ]; then
        OVERALL_RATE=$(echo "scale=1; $PROCESSED_FILES / $ELAPSED" | bc)
        echo -e "${BOLD}Performance:${NC}"
        print_metric "Overall Rate:" "${OVERALL_RATE} files/sec"
        
        if [ "$TOTAL_EMBEDDINGS" != "0" ]; then
            EMB_RATE=$(echo "scale=1; $TOTAL_EMBEDDINGS / $ELAPSED" | bc)
            print_metric "Embedding Rate:" "${EMB_RATE} emb/sec"
        fi
        
        # ETA
        if [ "$TOTAL_FILES" != "0" ] && [ "$PROCESSED_FILES" -lt "$TOTAL_FILES" ]; then
            REMAINING=$((TOTAL_FILES - PROCESSED_FILES))
            ETA=$(echo "scale=0; $REMAINING / $OVERALL_RATE" | bc)
            if [ "$ETA" -lt "60" ]; then
                print_metric "ETA:" "${ETA}s"
            elif [ "$ETA" -lt "3600" ]; then
                ETA_MIN=$(echo "scale=1; $ETA / 60" | bc)
                print_metric "ETA:" "${ETA_MIN}m"
            else
                ETA_HR=$(echo "scale=1; $ETA / 3600" | bc)
                print_metric "ETA:" "${ETA_HR}h"
            fi
        fi
    fi
    
    echo ""
    
    # Quality
    if [ "$PROCESSED_FILES" != "0" ]; then
        ERROR_RATE=$(echo "scale=2; ($FAILED_FILES / $PROCESSED_FILES) * 100" | bc)
        echo -e "${BOLD}Quality:${NC}"
        if (( $(echo "$ERROR_RATE < 1" | bc -l) )); then
            echo -e "  ${GREEN}Failed files: $FAILED_FILES ($ERROR_RATE%)${NC}"
        elif (( $(echo "$ERROR_RATE < 5" | bc -l) )); then
            echo -e "  ${YELLOW}Failed files: $FAILED_FILES ($ERROR_RATE%)${NC}"
        else
            echo -e "  ${RED}Failed files: $FAILED_FILES ($ERROR_RATE%)${NC}"
        fi
    fi
    
    # Additional metrics
    if [ "$TOTAL_EMBEDDINGS" != "0" ]; then
        echo ""
        echo -e "${BOLD}Embeddings:${NC}"
        print_metric "Total Generated:" "$TOTAL_EMBEDDINGS"
    fi
    
    # Check if complete
    if [ "$JOB_STATUS" = "completed" ]; then
        echo ""
        print_success "Job completed in ${ELAPSED}s!"
        break
    elif [ "$JOB_STATUS" = "failed" ]; then
        echo ""
        print_error "Job failed after ${ELAPSED}s"
        ERROR_MSG=$(echo "$STATUS" | jq -r '.error_message // "Unknown error"')
        print_error "Error: $ERROR_MSG"
        break
    elif [ "$JOB_STATUS" = "cancelled" ]; then
        echo ""
        print_warning "Job was cancelled after ${ELAPSED}s"
        break
    fi
    
    # Update tracking
    LAST_PROCESSED=$PROCESSED_FILES
    
    # Wait before next check
    sleep 10
done

# Step 4: Final Report
print_header "STEP 4: FINAL REPORT"

FINAL_STATUS=$(curl -s "$API_BASE/api/v1/admin/ingest/$JOB_ID")

echo -e "${BOLD}Test Summary:${NC}"
print_metric "Job ID:" "$JOB_ID"
print_metric "Final Status:" "$(echo "$FINAL_STATUS" | jq -r '.status')"
print_metric "Total Files:" "$(echo "$FINAL_STATUS" | jq -r '.total_files')"
print_metric "Processed Files:" "$(echo "$FINAL_STATUS" | jq -r '.processed_files')"
print_metric "Failed Files:" "$(echo "$FINAL_STATUS" | jq -r '.failed_files')"
print_metric "Total Embeddings:" "$(echo "$FINAL_STATUS" | jq -r '.total_embeddings')"

echo ""
TOTAL_TIME=$(date +%s)
DURATION=$((TOTAL_TIME - START_TIME))
if [ "$DURATION" -lt "60" ]; then
    print_metric "Total Duration:" "${DURATION}s"
elif [ "$DURATION" -lt "3600" ]; then
    DUR_MIN=$(echo "scale=1; $DURATION / 60" | bc)
    print_metric "Total Duration:" "${DUR_MIN}m"
else
    DUR_HR=$(echo "scale=1; $DURATION / 3600" | bc)
    print_metric "Total Duration:" "${DUR_HR}h"
fi

FINAL_PROCESSED=$(echo "$FINAL_STATUS" | jq -r '.processed_files')
if [ "$FINAL_PROCESSED" != "0" ] && [ "$DURATION" -gt "0" ]; then
    AVG_RATE=$(echo "scale=1; $FINAL_PROCESSED / $DURATION" | bc)
    print_metric "Average Rate:" "${AVG_RATE} files/sec"
fi

# Success criteria
echo ""
echo -e "${BOLD}Success Criteria:${NC}"

STATUS_VAL=$(echo "$FINAL_STATUS" | jq -r '.status')
PROC_VAL=$(echo "$FINAL_STATUS" | jq -r '.processed_files')
FAIL_VAL=$(echo "$FINAL_STATUS" | jq -r '.failed_files')
EMB_VAL=$(echo "$FINAL_STATUS" | jq -r '.total_embeddings')

if [ "$STATUS_VAL" = "completed" ]; then
    echo "  ✅ Job Completed"
else
    echo "  ❌ Job Completed"
fi

if [ "$PROC_VAL" != "0" ]; then
    echo "  ✅ Files Processed"
else
    echo "  ❌ Files Processed"
fi

if [ "$PROC_VAL" != "0" ]; then
    ERROR_PCT=$(echo "scale=2; ($FAIL_VAL / $PROC_VAL) * 100" | bc)
    if (( $(echo "$ERROR_PCT < 5" | bc -l) )); then
        echo "  ✅ Error Rate < 5%"
    else
        echo "  ❌ Error Rate < 5% (actual: $ERROR_PCT%)"
    fi
fi

if [ "$EMB_VAL" != "0" ]; then
    echo "  ✅ Embeddings Generated"
else
    echo "  ❌ Embeddings Generated"
fi

print_header "TEST COMPLETE"
print_success "Job ID: $JOB_ID"
print_info "View detailed results in dashboard: http://localhost:8501"

