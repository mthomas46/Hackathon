#!/bin/bash
#
# Verify Automatic Cleanup Integration
#
# Tests that the cleanup service is properly integrated and running
#

set -e

API_BASE="http://localhost:8000"

echo "================================================================================================="
echo "🧪 VERIFYING AUTOMATIC CLEANUP INTEGRATION"
echo "================================================================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

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

PASSED=0
FAILED=0

# Test 1: API Connectivity
echo "Test 1: API Connectivity"
echo "-------------------------"
if curl -s --max-time 5 "$API_BASE/health" > /dev/null 2>&1; then
    print_success "API is accessible"
    ((PASSED++))
else
    print_error "Cannot connect to API at $API_BASE"
    print_info "Make sure the ecosystem-mcp service is running"
    ((FAILED++))
fi
echo ""

# Test 2: Cleanup API Endpoint Exists
echo "Test 2: Cleanup API Endpoint"
echo "-----------------------------"
RESPONSE=$(curl -s -w "%{http_code}" "$API_BASE/api/v1/maintenance/cleanup/status" -o /tmp/cleanup_status.json)
if [ "$RESPONSE" = "200" ]; then
    print_success "Cleanup API endpoint is accessible"
    ((PASSED++))
else
    print_error "Cleanup API endpoint returned HTTP $RESPONSE"
    print_info "Expected: 200"
    print_info "The API endpoint may not be registered"
    ((FAILED++))
fi
echo ""

# Test 3: Service Status
echo "Test 3: Service Status"
echo "----------------------"
if [ "$RESPONSE" = "200" ]; then
    STATUS=$(cat /tmp/cleanup_status.json | jq -r '.status')
    if [ "$STATUS" = "running" ]; then
        print_success "Cleanup service is running"
        ((PASSED++))
    elif [ "$STATUS" = "stopped" ]; then
        print_warning "Cleanup service is stopped (not auto-started)"
        print_info "This may be expected if auto_start=False in the code"
        print_info "Try starting it: curl -X POST $API_BASE/api/v1/maintenance/cleanup/start"
        ((FAILED++))
    else
        print_error "Unexpected status: $STATUS"
        ((FAILED++))
    fi
else
    print_warning "Skipping (API endpoint not accessible)"
fi
echo ""

# Test 4: Startup Logs
echo "Test 4: Startup Logs"
echo "--------------------"
if docker ps | grep -q ecosystem-mcp-service; then
    print_info "Checking Docker logs for startup message..."
    
    if docker logs ecosystem-mcp-service 2>&1 | grep -q "Automatic cleanup service started"; then
        print_success "Found startup log entry"
        ((PASSED++))
        
        # Show the relevant log lines
        echo ""
        print_info "Relevant log entries:"
        docker logs ecosystem-mcp-service 2>&1 | grep -A 2 -B 2 "cleanup service" | tail -10
    else
        print_warning "Startup log entry not found"
        print_info "The service may have been restarted before integration"
        print_info "Try: docker restart ecosystem-mcp-service"
        ((FAILED++))
    fi
else
    print_warning "Docker container not found"
    print_info "Looking for container 'ecosystem-mcp-service'"
    ((FAILED++))
fi
echo ""

# Test 5: Health Check
echo "Test 5: Health Check"
echo "--------------------"
HEALTH_RESPONSE=$(curl -s "$API_BASE/api/v1/maintenance/cleanup/health" 2>/dev/null)
if [ $? -eq 0 ]; then
    HEALTHY=$(echo "$HEALTH_RESPONSE" | jq -r '.healthy')
    HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.status')
    
    if [ "$HEALTHY" = "true" ]; then
        print_success "Service is healthy (status: $HEALTH_STATUS)"
        ((PASSED++))
    else
        print_warning "Service is unhealthy (status: $HEALTH_STATUS)"
        echo "$HEALTH_RESPONSE" | jq '.'
        ((FAILED++))
    fi
else
    print_warning "Could not check health"
    ((FAILED++))
fi
echo ""

# Test 6: OpenAPI Documentation
echo "Test 6: OpenAPI Documentation"
echo "------------------------------"
if curl -s "$API_BASE/openapi.json" | jq -e '.paths | has("/api/v1/maintenance/cleanup/status")' > /dev/null 2>&1; then
    print_success "Cleanup endpoints in OpenAPI spec"
    ((PASSED++))
    
    # Count endpoints
    ENDPOINT_COUNT=$(curl -s "$API_BASE/openapi.json" | jq '[.paths | keys[] | select(contains("cleanup"))] | length')
    print_info "Found $ENDPOINT_COUNT cleanup endpoints"
else
    print_error "Cleanup endpoints not in OpenAPI spec"
    print_info "The router may not be registered correctly"
    ((FAILED++))
fi
echo ""

# Summary
echo "================================================================================================="
echo "📊 TEST SUMMARY"
echo "================================================================================================="
echo ""
echo "Total Tests: $((PASSED + FAILED))"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    print_success "ALL TESTS PASSED! 🎉"
    echo ""
    echo "✅ The automatic cleanup service is properly integrated and running."
    echo ""
    echo "Next steps:"
    echo "  1. Check status:   curl $API_BASE/api/v1/maintenance/cleanup/status | jq"
    echo "  2. View stats:     curl $API_BASE/api/v1/maintenance/cleanup/stats | jq"
    echo "  3. View docs:      open $API_BASE/docs#/Automatic%20Cleanup"
    echo ""
    exit 0
else
    print_warning "SOME TESTS FAILED"
    echo ""
    echo "🔧 Troubleshooting:"
    echo ""
    
    if docker ps | grep -q ecosystem-mcp-service; then
        echo "The service is running. Try:"
        echo "  1. Restart service: docker restart ecosystem-mcp-service"
        echo "  2. Check logs:      docker logs ecosystem-mcp-service --tail 100"
        echo "  3. Verify files:    docker exec ecosystem-mcp-service ls -la src/services/maintenance/"
    else
        echo "The service is not running. Try:"
        echo "  1. Start service:   docker-compose up -d ecosystem-mcp-service"
        echo "  2. Check status:    docker ps -a | grep ecosystem"
    fi
    echo ""
    exit 1
fi

