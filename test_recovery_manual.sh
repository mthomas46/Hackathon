#!/bin/bash

# Manual Recovery Testing Script
# Demonstrates job recovery functionality

set -e

echo "================================================"
echo "🔄 Job Recovery - Manual Test"
echo "================================================"
echo ""

API_URL="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}1️⃣  Creating a new ingestion job...${NC}"
JOB_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/admin/ingestion/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "recent",
    "repo_path": "/app",
    "service_id": "manual-recovery-test"
  }')

JOB_ID=$(echo $JOB_RESPONSE | python3 -c "import json, sys; print(json.load(sys.stdin)['job_id'])" 2>/dev/null)

if [ -z "$JOB_ID" ]; then
    echo "❌ Failed to create job"
    exit 1
fi

echo -e "${GREEN}✅ Job created: $JOB_ID${NC}"
echo ""

echo -e "${BLUE}2️⃣  Waiting for job to create checkpoints (10 seconds)...${NC}"
sleep 10

echo -e "${BLUE}3️⃣  Checking for checkpoints...${NC}"
CHECKPOINT_RESPONSE=$(curl -s "$API_URL/api/v1/recovery/checkpoints/$JOB_ID")
echo "$CHECKPOINT_RESPONSE" | python3 -m json.tool

CHECKPOINT_COUNT=$(echo $CHECKPOINT_RESPONSE | python3 -c "import json, sys; print(json.load(sys.stdin)['total_checkpoints'])" 2>/dev/null)
echo ""
echo -e "${GREEN}📊 Total checkpoints: $CHECKPOINT_COUNT${NC}"
echo ""

echo -e "${BLUE}4️⃣  Getting recovery status...${NC}"
STATUS_RESPONSE=$(curl -s "$API_URL/api/v1/recovery/status/$JOB_ID")
echo "$STATUS_RESPONSE" | python3 -m json.tool

CAN_RESUME=$(echo $STATUS_RESPONSE | python3 -c "import json, sys; print(json.load(sys.stdin)['can_resume'])" 2>/dev/null)
echo ""
echo -e "${GREEN}🔄 Can resume: $CAN_RESUME${NC}"
echo ""

if [ "$CAN_RESUME" = "True" ]; then
    echo -e "${BLUE}5️⃣  Testing resume API...${NC}"
    RESUME_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/recovery/resume" \
      -H "Content-Type: application/json" \
      -d "{
        \"job_id\": \"$JOB_ID\",
        \"job_type\": \"ingestion\"
      }")
    
    echo "$RESUME_RESPONSE" | python3 -m json.tool
    echo ""
fi

echo -e "${BLUE}6️⃣  Getting job details...${NC}"
JOB_DETAILS=$(curl -s "$API_URL/api/v1/admin/ingestion/jobs/$JOB_ID")
echo "$JOB_DETAILS" | python3 -m json.tool | head -40
echo ""

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ Recovery test complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Job ID: $JOB_ID"
echo "Checkpoints Created: $CHECKPOINT_COUNT"
echo "Can Resume: $CAN_RESUME"
echo ""
echo "To monitor this job:"
echo "  curl $API_URL/api/v1/recovery/status/$JOB_ID"
echo ""
echo "To view in dashboard:"
echo "  http://localhost:8501 → 🔄 Job Recovery"
echo ""

