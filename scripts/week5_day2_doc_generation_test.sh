#!/bin/bash
#
# Week 5, Day 2: Documentation Generation Test
# Testing snapshot-based documentation for the Hackathon directory
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
TEST_NAME="Week 5 Day 2 - Documentation Generation Test"

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
print_header "$TEST_NAME"

echo -e "${BOLD}Test Configuration:${NC}"
print_metric "API Base URL:" "$API_BASE"
print_metric "Repository Path:" "$REPO_PATH"
print_metric "Target Directory:" "/Users/mykalthomas/Documents/work/Hackathon"
print_metric "Test Type:" "Documentation Generation"
echo ""

print_header "STEP 1: HEALTH CHECK"

print_info "Checking API health..."
HEALTH=$(curl -s "$API_BASE/health")
if echo "$HEALTH" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    print_success "API is healthy"
    echo "$HEALTH" | jq -r '.components | to_entries[] | "  ✅ \(.key): \(.value.status)"'
else
    print_error "API is not healthy"
    echo "$HEALTH" | jq '.'
    exit 1
fi

# Step 2: First ingest a small sample for testing
print_header "STEP 2: INGEST SAMPLE DOCUMENTS (Quick Mode)"

print_info "Starting quick ingestion to populate database..."
INGEST_PAYLOAD='{
  "repo_path": "'$REPO_PATH'",
  "use_git_history": false,
  "force_reingest": false,
  "snapshot_mode": true
}'

echo "$INGEST_PAYLOAD" | jq '.'

print_info "Sending POST request to /api/v1/admin/ingest..."
INGEST_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/admin/ingest" \
    -H "Content-Type: application/json" \
    -d "$INGEST_PAYLOAD")

echo "$INGEST_RESPONSE" | jq '.'

if echo "$INGEST_RESPONSE" | jq -e '.job_id' > /dev/null 2>&1; then
    INGEST_JOB_ID=$(echo "$INGEST_RESPONSE" | jq -r '.job_id')
    print_success "Ingestion job started!"
    print_metric "Job ID:" "$INGEST_JOB_ID"
    
    # Wait for ingestion to start
    print_info "Waiting 30 seconds for ingestion to begin..."
    sleep 30
    
    # Check status
    INGEST_STATUS=$(curl -s "$API_BASE/api/v1/admin/ingest/$INGEST_JOB_ID")
    JOB_STATUS=$(echo "$INGEST_STATUS" | jq -r '.status')
    print_metric "Current Status:" "$JOB_STATUS"
    
    if [ "$JOB_STATUS" = "queued" ]; then
        print_warning "Job still queued - this is Bug #9! Continuing with documentation test anyway..."
    fi
else
    print_warning "Ingestion may have issues, but continuing with documentation test..."
fi

# Step 3: Start Documentation Generation
print_header "STEP 3: START DOCUMENTATION GENERATION"

print_info "Preparing documentation generation request..."
DOC_PAYLOAD='{
  "target_path": "'$REPO_PATH'",
  "output_format": "markdown",
  "include_architecture": true,
  "include_api_docs": true,
  "include_dependencies": true,
  "max_depth": 3
}'

echo "$DOC_PAYLOAD" | jq '.'

print_info "Sending POST request to /api/v1/documentation/runs..."
DOC_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/documentation/runs" \
    -H "Content-Type: application/json" \
    -d "$DOC_PAYLOAD")

echo "$DOC_RESPONSE" | jq '.'

if echo "$DOC_RESPONSE" | jq -e '.run_id' > /dev/null 2>&1; then
    RUN_ID=$(echo "$DOC_RESPONSE" | jq -r '.run_id')
    print_success "Documentation run started!"
    print_metric "Run ID:" "$RUN_ID"
else
    print_error "Failed to start documentation generation"
    echo "$DOC_RESPONSE" | jq '.'
    exit 1
fi

# Step 4: Monitor Documentation Progress
print_header "STEP 4: MONITOR DOCUMENTATION GENERATION"

print_info "Monitoring run: $RUN_ID"
print_info "Update interval: 15 seconds"
print_info "Press Ctrl+C to stop monitoring (run will continue)"
echo ""

START_TIME=$(date +%s)
ITERATION=0

while true; do
    ITERATION=$((ITERATION + 1))
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    # Get run status
    STATUS=$(curl -s "$API_BASE/api/v1/documentation/runs/$RUN_ID")
    
    if [ $? -ne 0 ]; then
        print_warning "Could not retrieve run status"
        sleep 15
        continue
    fi
    
    # Parse status
    RUN_STATUS=$(echo "$STATUS" | jq -r '.status // "unknown"')
    TOTAL_ARTIFACTS=$(echo "$STATUS" | jq -r '.total_artifacts // 0')
    GENERATED_ARTIFACTS=$(echo "$STATUS" | jq -r '.generated_artifacts // 0')
    
    # Print update
    if [ $ITERATION -gt 1 ]; then
        echo ""
        echo "────────────────────────────────────────────────────────────────────────────────"
        echo ""
    fi
    
    echo -e "${BOLD}📊 Documentation Status Update #$ITERATION${NC}"
    echo "  Time: $(date '+%H:%M:%S')"
    echo "  Elapsed: ${ELAPSED}s"
    echo ""
    
    # Status
    case $RUN_STATUS in
        "pending") STATUS_EMOJI="⏳" ;;
        "running") STATUS_EMOJI="🔄" ;;
        "completed") STATUS_EMOJI="✅" ;;
        "failed") STATUS_EMOJI="❌" ;;
        *) STATUS_EMOJI="❓" ;;
    esac
    
    echo -e "${BOLD}Status:${NC} $STATUS_EMOJI $RUN_STATUS"
    
    # Progress
    if [ "$TOTAL_ARTIFACTS" != "0" ] && [ "$TOTAL_ARTIFACTS" != "null" ]; then
        PROGRESS_PCT=$(echo "scale=1; ($GENERATED_ARTIFACTS / $TOTAL_ARTIFACTS) * 100" | bc)
        echo -e "${BOLD}Progress:${NC} $GENERATED_ARTIFACTS/$TOTAL_ARTIFACTS artifacts ($PROGRESS_PCT%)"
        
        # Progress bar
        BAR_WIDTH=50
        FILLED=$(echo "scale=0; ($BAR_WIDTH * $GENERATED_ARTIFACTS) / $TOTAL_ARTIFACTS" | bc)
        EMPTY=$((BAR_WIDTH - FILLED))
        BAR=$(printf "█%.0s" $(seq 1 $FILLED))$(printf "░%.0s" $(seq 1 $EMPTY))
        echo "  [$BAR]"
    else
        echo -e "${BOLD}Progress:${NC} $GENERATED_ARTIFACTS artifacts generated"
    fi
    
    echo ""
    
    # Check if complete
    if [ "$RUN_STATUS" = "completed" ]; then
        echo ""
        print_success "Documentation generation completed in ${ELAPSED}s!"
        break
    elif [ "$RUN_STATUS" = "failed" ]; then
        echo ""
        print_error "Documentation generation failed after ${ELAPSED}s"
        ERROR_MSG=$(echo "$STATUS" | jq -r '.error_message // "Unknown error"')
        print_error "Error: $ERROR_MSG"
        break
    fi
    
    # Wait before next check
    sleep 15
done

# Step 5: Retrieve Generated Documentation
print_header "STEP 5: RETRIEVE GENERATED DOCUMENTATION"

ARTIFACTS=$(curl -s "$API_BASE/api/v1/documentation/runs/$RUN_ID/artifacts")
ARTIFACT_COUNT=$(echo "$ARTIFACTS" | jq -r '.artifacts | length')

print_success "Retrieved documentation artifacts"
print_metric "Total Artifacts:" "$ARTIFACT_COUNT"

if [ "$ARTIFACT_COUNT" -gt "0" ]; then
    echo ""
    echo -e "${BOLD}Generated Documents:${NC}"
    echo "$ARTIFACTS" | jq -r '.artifacts[] | "  📄 \(.file_name) (\(.file_type)) - \(.word_count) words"' | head -20
    
    if [ "$ARTIFACT_COUNT" -gt "20" ]; then
        echo "  ... and $((ARTIFACT_COUNT - 20)) more"
    fi
fi

# Step 6: Final Report
print_header "STEP 6: FINAL REPORT"

FINAL_STATUS=$(curl -s "$API_BASE/api/v1/documentation/runs/$RUN_ID")

echo -e "${BOLD}Test Summary:${NC}"
print_metric "Run ID:" "$RUN_ID"
print_metric "Final Status:" "$(echo "$FINAL_STATUS" | jq -r '.status')"
print_metric "Total Artifacts:" "$(echo "$FINAL_STATUS" | jq -r '.total_artifacts')"
print_metric "Generated Artifacts:" "$(echo "$FINAL_STATUS" | jq -r '.generated_artifacts')"
print_metric "Total Word Count:" "$(echo "$FINAL_STATUS" | jq -r '.total_word_count')"

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

# Success criteria
echo ""
echo -e "${BOLD}Success Criteria:${NC}"

STATUS_VAL=$(echo "$FINAL_STATUS" | jq -r '.status')
ARTIFACTS_VAL=$(echo "$FINAL_STATUS" | jq -r '.generated_artifacts')

if [ "$STATUS_VAL" = "completed" ]; then
    echo "  ✅ Run Completed"
else
    echo "  ❌ Run Completed"
fi

if [ "$ARTIFACTS_VAL" != "0" ] && [ "$ARTIFACTS_VAL" != "null" ]; then
    echo "  ✅ Documentation Generated"
else
    echo "  ❌ Documentation Generated"
fi

print_header "TEST COMPLETE"
print_success "Run ID: $RUN_ID"
print_info "View documentation in database or export artifacts"
print_info "Dashboard: http://localhost:8501"

