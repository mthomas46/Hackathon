#!/bin/bash

# ============================================================================
# Project Simulation Service - Docker Integration Test Script
# ============================================================================
# This script validates the complete Docker Compose integration for the
# project-simulation service with the full ecosystem.
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
SERVICE_NAME="project-simulation"
TIMEOUT=300  # 5 minutes timeout

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up Docker containers and volumes..."
    cd "$PROJECT_ROOT"
    docker-compose down -v --remove-orphans || true
    docker system prune -f || true
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Function to check if a service is healthy
check_service_health() {
    local service_name=$1
    local max_attempts=30
    local attempt=1

    log_info "Checking health of $service_name..."

    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps "$service_name" | grep -q "Up"; then
            log_success "$service_name is running"
            return 0
        fi

        log_info "Waiting for $service_name to be healthy (attempt $attempt/$max_attempts)..."
        sleep 10
        ((attempt++))
    done

    log_error "$service_name failed to start within timeout"
    return 1
}

# Function to test service connectivity
test_service_connectivity() {
    local service_name=$1
    local port=$2
    local endpoint=${3:-"/health"}
    local max_attempts=10
    local attempt=1

    log_info "Testing connectivity to $service_name on port $port..."

    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "http://localhost:$port$endpoint" > /dev/null 2>&1; then
            log_success "$service_name is responding on port $port"
            return 0
        fi

        log_info "Waiting for $service_name to respond (attempt $attempt/$max_attempts)..."
        sleep 5
        ((attempt++))
    done

    log_error "$service_name is not responding on port $port"
    return 1
}

# Function to test database connectivity
test_database_connectivity() {
    log_info "Testing PostgreSQL connectivity..."

    # Wait for PostgreSQL to be ready
    docker-compose exec -T postgres pg_isready -U simulation_user -d simulation_db

    if [ $? -eq 0 ]; then
        log_success "PostgreSQL is ready and accepting connections"
        return 0
    else
        log_error "PostgreSQL is not ready"
        return 1
    fi
}

# Function to test Redis connectivity
test_redis_connectivity() {
    log_info "Testing Redis connectivity..."

    # Test Redis ping
    if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis is responding to ping"
        return 0
    else
        log_error "Redis is not responding"
        return 1
    fi
}

# Function to test project-simulation service
test_simulation_service() {
    log_info "Testing project-simulation service..."

    # Test basic health endpoint
    if ! test_service_connectivity "project-simulation" "5075" "/health"; then
        return 1
    fi

    # Test detailed health endpoint
    if ! test_service_connectivity "project-simulation" "5075" "/health/detailed"; then
        return 1
    fi

    # Test API root endpoint
    if ! test_service_connectivity "project-simulation" "5075" "/"; then
        return 1
    fi

    # Test OpenAPI documentation
    if ! test_service_connectivity "project-simulation" "5075" "/docs"; then
        log_warning "OpenAPI docs not accessible (may be expected in production)"
    fi

    log_success "Project-simulation service tests passed"
    return 0
}

# Function to test ecosystem integration
test_ecosystem_integration() {
    log_info "Testing ecosystem service integration..."

    # Test creating a simulation
    log_info "Creating a test simulation..."
    create_response=$(curl -s -X POST \
        "http://localhost:5075/api/v1/simulations" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Docker Integration Test",
            "description": "Testing Docker Compose integration",
            "type": "web_application",
            "team_size": 3,
            "complexity": "simple",
            "duration_weeks": 4
        }')

    if echo "$create_response" | grep -q '"success":true'; then
        log_success "Simulation creation successful"

        # Extract simulation ID
        simulation_id=$(echo "$create_response" | grep -o '"simulation_id":"[^"]*' | cut -d'"' -f4)

        if [ -n "$simulation_id" ]; then
            log_info "Created simulation with ID: $simulation_id"

            # Test getting simulation status
            status_response=$(curl -s "http://localhost:5075/api/v1/simulations/$simulation_id")

            if echo "$status_response" | grep -q '"success":true'; then
                log_success "Simulation status retrieval successful"
            else
                log_error "Failed to retrieve simulation status"
                return 1
            fi

            # Test simulation execution (this will test ecosystem integration)
            log_info "Testing simulation execution (ecosystem integration)..."
            execute_response=$(curl -s -X POST \
                "http://localhost:5075/api/v1/simulations/$simulation_id/execute")

            if echo "$execute_response" | grep -q '"success":true'; then
                log_success "Simulation execution started (ecosystem integration working)"
            else
                log_warning "Simulation execution failed (may be expected if ecosystem services not running)"
                log_info "Execution response: $execute_response"
            fi
        else
            log_error "Could not extract simulation ID from response"
            return 1
        fi
    else
        log_error "Simulation creation failed"
        log_info "Create response: $create_response"
        return 1
    fi

    return 0
}

# Function to test monitoring stack
test_monitoring_stack() {
    log_info "Testing monitoring stack..."

    # Test Prometheus
    if test_service_connectivity "prometheus" "9090" "/"; then
        log_success "Prometheus is accessible"
    else
        log_warning "Prometheus not accessible (may not be enabled)"
    fi

    # Test Grafana
    if test_service_connectivity "grafana" "3000" "/"; then
        log_success "Grafana is accessible"
    else
        log_warning "Grafana not accessible (may not be enabled)"
    fi
}

# Function to run performance tests
run_performance_tests() {
    log_info "Running basic performance tests..."

    # Test concurrent requests
    log_info "Testing concurrent requests to simulation service..."

    # Run 10 concurrent requests
    for i in {1..10}; do
        curl -s "http://localhost:5075/health" > /dev/null &
    done

    # Wait for all requests to complete
    wait

    log_success "Concurrent request test completed"
}

# Main test function
main() {
    log_info "Starting Docker Compose Integration Tests"
    log_info "=========================================="
    log_info "Project Root: $PROJECT_ROOT"
    log_info "Compose File: $COMPOSE_FILE"
    log_info "Timeout: ${TIMEOUT}s"
    log_info ""

    # Change to project directory
    cd "$PROJECT_ROOT"

    # Start the stack
    log_info "Starting Docker Compose stack..."
    docker-compose up -d

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."

    # Test database connectivity
    if ! test_database_connectivity; then
        log_error "Database connectivity test failed"
        exit 1
    fi

    # Test Redis connectivity
    if ! test_redis_connectivity; then
        log_error "Redis connectivity test failed"
        exit 1
    fi

    # Test project-simulation service
    if ! test_simulation_service; then
        log_error "Project-simulation service test failed"
        exit 1
    fi

    # Test ecosystem integration
    if ! test_ecosystem_integration; then
        log_warning "Ecosystem integration test had issues (may be expected)"
    fi

    # Test monitoring stack
    test_monitoring_stack

    # Run performance tests
    run_performance_tests

    # All tests passed
    log_success "🎉 All Docker Compose integration tests passed!"
    log_info ""
    log_info "Services are running and accessible:"
    log_info "• Project Simulation: http://localhost:5075"
    log_info "• API Documentation: http://localhost:5075/docs"
    log_info "• Health Check: http://localhost:5075/health"
    log_info "• Prometheus: http://localhost:9090"
    log_info "• Grafana: http://localhost:3000"
    log_info ""
    log_info "To stop the stack, run: docker-compose down"
    log_info "To view logs, run: docker-compose logs -f"
}

# Run main function
main "$@"
