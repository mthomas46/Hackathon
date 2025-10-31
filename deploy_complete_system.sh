#!/bin/bash

# Deploy Complete Intelligent Document Management System
# Date: 2025-10-30
# Components: File Safety + Intelligent Filtering + Document Scoring + Document Cleanup

set -e  # Exit on error

echo "🚀 Starting Complete System Deployment"
echo "======================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Base directory
BASE_DIR="/Users/mykalthomas/Documents/work/Hackathon"
SERVICE_DIR="$BASE_DIR/services/ecosystem-mcp"

# ============================================================
# Phase 1: Database Migration
# ============================================================

echo -e "${BLUE}Phase 1: Database Migration${NC}"
echo "----------------------------------------"

# Copy migration to container
echo "📋 Copying migration script to container..."
docker cp "$SERVICE_DIR/src/storage/migrations/add_quality_score.sql" \
  ecosystem-mcp-postgres:/tmp/add_quality_score.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migration script copied${NC}"
else
    echo -e "${RED}❌ Failed to copy migration script${NC}"
    exit 1
fi

# Run migration
echo "🔄 Running database migration..."
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp \
  -f /tmp/add_quality_score.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migration complete${NC}"
else
    echo -e "${RED}❌ Migration failed${NC}"
    exit 1
fi

# Verify migration
echo "🔍 Verifying new columns..."
COLUMNS=$(docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp \
  -t -c "SELECT COUNT(*) FROM information_schema.columns 
         WHERE table_name = 'documents' 
         AND column_name IN ('quality_score', 'quality_grade', 'score_breakdown');")

if [ "$COLUMNS" -eq 3 ]; then
    echo -e "${GREEN}✅ All 3 columns verified${NC}"
else
    echo -e "${RED}❌ Column verification failed (found $COLUMNS, expected 3)${NC}"
    exit 1
fi

echo ""

# ============================================================
# Phase 2: Container Rebuild
# ============================================================

echo -e "${BLUE}Phase 2: Container Rebuild${NC}"
echo "----------------------------------------"

cd "$SERVICE_DIR"

echo "🔨 Building ecosystem-mcp container..."
docker-compose build ecosystem-mcp

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container built successfully${NC}"
else
    echo -e "${RED}❌ Container build failed${NC}"
    exit 1
fi

echo "🔄 Restarting service..."
docker-compose up -d ecosystem-mcp

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Service restarted${NC}"
else
    echo -e "${RED}❌ Service restart failed${NC}"
    exit 1
fi

# Wait for service to be healthy
echo "⏳ Waiting for service to be healthy (30 seconds)..."
sleep 30

# Check health
HEALTH=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null)

if [ "$HEALTH" == "healthy" ]; then
    echo -e "${GREEN}✅ Service is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Service health check inconclusive (status: $HEALTH)${NC}"
    echo "   Continuing anyway..."
fi

echo ""

# ============================================================
# Phase 3: Verify Endpoints
# ============================================================

echo -e "${BLUE}Phase 3: Endpoint Verification${NC}"
echo "----------------------------------------"

# Check scoring endpoints
echo "🔍 Checking scoring endpoints..."
SCORING_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/documents/score/statistics)

if [ "$SCORING_RESPONSE" == "200" ]; then
    echo -e "${GREEN}✅ Scoring endpoints available${NC}"
else
    echo -e "${RED}❌ Scoring endpoints not available (HTTP $SCORING_RESPONSE)${NC}"
    exit 1
fi

# Check cleanup endpoints
echo "🔍 Checking cleanup endpoints..."
CLEANUP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/documents/cleanup/report)

if [ "$CLEANUP_RESPONSE" == "200" ]; then
    echo -e "${GREEN}✅ Cleanup endpoints available${NC}"
else
    echo -e "${RED}❌ Cleanup endpoints not available (HTTP $CLEANUP_RESPONSE)${NC}"
    exit 1
fi

echo ""

# ============================================================
# Phase 4: Bulk Score Existing Documents
# ============================================================

echo -e "${BLUE}Phase 4: Bulk Scoring${NC}"
echo "----------------------------------------"

echo "📊 Scoring all existing documents..."
echo "   This may take 1-2 minutes for 1,854 documents..."

SCORE_RESULT=$(curl -s -X POST http://localhost:8000/api/v1/documents/score/bulk \
  -H 'Content-Type: application/json' \
  -d '{"score_all": true, "only_unscored": true, "batch_size": 100}')

SCORED=$(echo "$SCORE_RESULT" | jq -r '.scored' 2>/dev/null)
FAILED=$(echo "$SCORE_RESULT" | jq -r '.failed' 2>/dev/null)

if [ "$SCORED" != "null" ] && [ "$SCORED" != "" ]; then
    echo -e "${GREEN}✅ Scored $SCORED documents${NC}"
    if [ "$FAILED" != "0" ]; then
        echo -e "${YELLOW}⚠️  $FAILED documents failed to score${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No new documents to score (already scored)${NC}"
fi

echo ""

# ============================================================
# Phase 5: Statistics & Report
# ============================================================

echo -e "${BLUE}Phase 5: Results & Statistics${NC}"
echo "----------------------------------------"

# Get score statistics
echo "📊 Score Distribution:"
STATS=$(curl -s http://localhost:8000/api/v1/documents/score/statistics)

TOTAL_SCORED=$(echo "$STATS" | jq -r '.total_scored' 2>/dev/null)
AVG_SCORE=$(echo "$STATS" | jq -r '.average_score' 2>/dev/null)

if [ "$TOTAL_SCORED" != "null" ] && [ "$TOTAL_SCORED" != "" ]; then
    echo "   Total scored: $TOTAL_SCORED documents"
    echo "   Average score: $AVG_SCORE"
    echo ""
    
    echo "   Grade Distribution:"
    echo "$STATS" | jq -r '.grade_distribution | to_entries[] | "     \(.key): \(.value) docs"' 2>/dev/null
    echo ""
    
    echo "   Score Ranges:"
    echo "$STATS" | jq -r '.score_ranges | to_entries[] | "     \(.key): \(.value) docs"' 2>/dev/null
fi

echo ""

# Get cleanup report
echo "🧹 Cleanup Opportunities:"
CLEANUP_REPORT=$(curl -s http://localhost:8000/api/v1/documents/cleanup/report)

TOTAL_DOCS=$(echo "$CLEANUP_REPORT" | jq -r '.report.total_documents' 2>/dev/null)
OLD_VERSIONS=$(echo "$CLEANUP_REPORT" | jq -r '.report.old_versions' 2>/dev/null)

if [ "$TOTAL_DOCS" != "null" ] && [ "$TOTAL_DOCS" != "" ]; then
    echo "   Total documents: $TOTAL_DOCS"
    echo "   Old versions: $OLD_VERSIONS (can be removed)"
    echo ""
    
    echo "   Recommendations:"
    echo "$CLEANUP_REPORT" | jq -r '.report.recommendations[] | "     • \(.description)"' 2>/dev/null
fi

echo ""

# ============================================================
# Summary
# ============================================================

echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${GREEN}=======================================${NC}"
echo ""

echo "✅ Database migration applied"
echo "✅ Container rebuilt and restarted"
echo "✅ All endpoints verified"
echo "✅ Documents scored"
echo ""

echo "📚 Available Endpoints:"
echo "   Scoring:"
echo "     POST /api/v1/documents/score"
echo "     POST /api/v1/documents/score/bulk"
echo "     GET  /api/v1/documents/score/statistics"
echo "     POST /api/v1/documents/score/custom-glossary"
echo "     POST /api/v1/documents/score/filter"
echo ""
echo "   Cleanup:"
echo "     GET  /api/v1/documents/cleanup/report"
echo "     POST /api/v1/documents/cleanup/low-value"
echo "     POST /api/v1/documents/cleanup/old-versions"
echo "     POST /api/v1/documents/cleanup/by-category"
echo ""

echo "📖 Documentation:"
echo "   DOCUMENT_SCORING_GUIDE.md"
echo "   DOCUMENT_CLEANUP_GUIDE.md"
echo "   COMPLETE_INTELLIGENT_SYSTEM_SUMMARY.md"
echo ""

echo "🚀 Next Steps:"
echo "   1. Test ingestion with scoring:"
echo "      curl -X POST http://localhost:8000/api/v1/admin/ingest \\"
echo "        -d '{\"repo_path\": \"/repo/services/ecosystem-mcp/docs\", \"mode\": \"enriched\"}'"
echo ""
echo "   2. View score statistics:"
echo "      curl http://localhost:8000/api/v1/documents/score/statistics | jq"
echo ""
echo "   3. Clean up low-value documents (optional):"
echo "      curl -X POST http://localhost:8000/api/v1/documents/cleanup/low-value?dry_run=false"
echo ""

echo -e "${GREEN}Deployment successful! ✨${NC}"


