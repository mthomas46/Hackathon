#!/bin/bash

###############################################################################
# Production Deployment Script for Ecosystem MCP (Week 5, Day 1)
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}$1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Header
clear
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Ecosystem MCP - Production Deployment (Week 5)      ║"
echo "║  Real-World Validation & Hardening                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Step 1: Pre-deployment checks
log_section "Step 1: Pre-Deployment Checks"

log_info "Checking Docker..."
if ! docker --version > /dev/null 2>&1; then
    log_error "Docker is not installed or not running"
    exit 1
fi
log_info "✓ Docker found: $(docker --version)"

log_info "Checking Docker Compose..."
if ! docker-compose --version > /dev/null 2>&1; then
    log_error "Docker Compose is not installed"
    exit 1
fi
log_info "✓ Docker Compose found: $(docker-compose --version)"

log_info "Checking disk space..."
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
log_info "✓ Available disk space: $AVAILABLE_SPACE"

log_info "Checking current directory..."
if [ ! -f "docker-compose.yml" ]; then
    log_error "docker-compose.yml not found in current directory"
    log_error "Please run this script from services/ecosystem-mcp directory"
    exit 1
fi
log_info "✓ docker-compose.yml found"

# Step 2: Stop existing services
log_section "Step 2: Stopping Existing Services"

log_info "Stopping any running containers..."
docker-compose down --remove-orphans || true
log_info "✓ Existing containers stopped"

# Step 3: Pull/Build images
log_section "Step 3: Building Images"

log_info "Building all service images..."
docker-compose build --no-cache || {
    log_error "Failed to build images"
    exit 1
}
log_info "✓ All images built successfully"

# Step 4: Start services
log_section "Step 4: Starting Services"

log_info "Starting all services..."
docker-compose up -d || {
    log_error "Failed to start services"
    exit 1
}
log_info "✓ All services started"

# Step 5: Wait for services to be healthy
log_section "Step 5: Waiting for Services to be Healthy"

log_info "Waiting for PostgreSQL..."
timeout 60 bash -c 'until docker exec ecosystem-mcp-postgres pg_isready -U ecosystem > /dev/null 2>&1; do sleep 2; done' || {
    log_error "PostgreSQL failed to start"
    docker logs ecosystem-mcp-postgres --tail 50
    exit 1
}
log_info "✓ PostgreSQL is healthy"

log_info "Waiting for Redis..."
timeout 60 bash -c 'until docker exec ecosystem-mcp-redis redis-cli ping > /dev/null 2>&1; do sleep 2; done' || {
    log_error "Redis failed to start"
    docker logs ecosystem-mcp-redis --tail 50
    exit 1
}
log_info "✓ Redis is healthy"

log_info "Waiting for Embedding Service..."
timeout 120 bash -c 'until curl -sf http://localhost:8001/health > /dev/null 2>&1; do sleep 5; done' || {
    log_warn "Embedding service may not be healthy yet (continuing...)"
}
log_info "✓ Embedding Service is starting..."

log_info "Waiting for Ollama..."
log_info "(This may take 2-3 minutes for model loading...)"
timeout 180 bash -c 'until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do sleep 10; done' || {
    log_warn "Ollama may not be fully ready yet (continuing...)"
}
log_info "✓ Ollama is starting..."

log_info "Waiting for Main API..."
timeout 120 bash -c 'until curl -sf http://localhost:8000/health > /dev/null 2>&1; do sleep 5; done' || {
    log_error "Main API failed to start"
    docker logs ecosystem-mcp-service --tail 100
    exit 1
}
log_info "✓ Main API is healthy"

log_info "Waiting for Dashboard..."
timeout 60 bash -c 'until curl -sf http://localhost:8501/_stcore/health > /dev/null 2>&1; do sleep 5; done' || {
    log_warn "Dashboard may not be fully ready yet (continuing...)"
}
log_info "✓ Dashboard is starting..."

# Step 6: Display service status
log_section "Step 6: Service Status"

log_info "Running containers:"
docker-compose ps

# Step 7: Health check endpoints
log_section "Step 7: Health Check Verification"

log_info "Testing API health endpoint..."
API_HEALTH=$(curl -s http://localhost:8000/health || echo "FAILED")
if echo "$API_HEALTH" | grep -q "healthy"; then
    log_info "✓ API health check passed"
else
    log_warn "⚠ API health check incomplete: $API_HEALTH"
fi

log_info "Testing Embedding service health endpoint..."
EMB_HEALTH=$(curl -s http://localhost:8001/health || echo "FAILED")
if echo "$EMB_HEALTH" | grep -q "status"; then
    log_info "✓ Embedding service health check passed"
else
    log_warn "⚠ Embedding service health check incomplete"
fi

# Step 8: Display access information
log_section "Step 8: Deployment Complete! 🎉"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║           DEPLOYMENT SUCCESSFUL! ✅                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "📍 Service URLs:"
echo "   • Dashboard:         http://localhost:8501"
echo "   • API:               http://localhost:8000"
echo "   • API Docs:          http://localhost:8000/docs"
echo "   • Embedding Service: http://localhost:8001"
echo "   • Ollama:            http://localhost:11434"
echo "   • Metrics:           http://localhost:9090"
echo ""
echo "🔍 Database Connections:"
echo "   • PostgreSQL: localhost:5432 (user: ecosystem, db: ecosystem_mcp)"
echo "   • Redis:      localhost:6379"
echo ""
echo "📊 Monitor Services:"
echo "   docker-compose logs -f                  # All logs"
echo "   docker-compose logs -f ecosystem-mcp    # API logs"
echo "   docker-compose logs -f dashboard        # Dashboard logs"
echo "   docker-compose ps                       # Service status"
echo ""
echo "🛑 Stop Services:"
echo "   docker-compose down                     # Stop all"
echo "   docker-compose down -v                  # Stop + remove data"
echo ""
echo "🎯 Next Steps:"
echo "   1. Open dashboard at http://localhost:8501"
echo "   2. Run smoke tests to verify all features"
echo "   3. Proceed with Week 5, Day 2: Large-Scale Testing"
echo ""

log_info "Deployment script completed successfully!"
exit 0

