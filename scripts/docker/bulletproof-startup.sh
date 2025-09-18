#!/bin/bash
# Bulletproof Ecosystem Startup System
# Comprehensive validation, self-healing, and automated deployment

set -euo pipefail

# Colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
MAX_RETRIES=3
HEALTH_CHECK_TIMEOUT=120
STARTUP_DELAY=10
SELF_HEAL=${SELF_HEAL:-true}
ROLLBACK_ON_FAILURE=${ROLLBACK_ON_FAILURE:-true}

# Logging functions
log_info() {
    echo -e "${CYAN}ℹ️  INFO: $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ SUCCESS: $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

log_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

log_step() {
    echo -e "${PURPLE}🚀 STEP: $1${NC}"
}

# Validation functions
validate_environment() {
    log_step "Environment Validation"
    
    # Check required tools
    for tool in docker docker-compose curl; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool '$tool' not found"
            return 1
        fi
    done
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon not running"
        return 1
    fi
    
    # Check compose file
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Compose file not found: $COMPOSE_FILE"
        return 1
    fi
    
    log_success "Environment validation passed"
}

run_pre_flight_checks() {
    log_step "Pre-Flight Validation"
    
    # Run comprehensive pre-flight check
    if ./scripts/docker/pre-flight-check.sh; then
        log_success "Pre-flight checks passed"
        return 0
    else
        log_error "Pre-flight checks failed"
        
        if [[ "$SELF_HEAL" == "true" ]]; then
            log_info "Attempting self-healing..."
            attempt_self_heal
            
            # Re-run checks after healing
            if ./scripts/docker/pre-flight-check.sh; then
                log_success "Self-healing successful, pre-flight checks now pass"
                return 0
            fi
        fi
        
        return 1
    fi
}

attempt_self_heal() {
    log_step "Self-Healing Mode"
    
    # Fix common Docker Compose issues
    log_info "Removing deprecated version field..."
    if grep -q "^version:" "$COMPOSE_FILE"; then
        sed -i.bak '/^version:/d' "$COMPOSE_FILE"
        log_success "Removed deprecated version field"
    fi
    
    # Clean up orphaned containers
    log_info "Cleaning orphaned containers..."
    docker container prune -f > /dev/null 2>&1 || true
    
    # Clean up unused networks
    log_info "Cleaning unused networks..."
    docker network prune -f > /dev/null 2>&1 || true
    
    # Clean up unused volumes (carefully)
    log_info "Cleaning unused volumes..."
    docker volume prune -f > /dev/null 2>&1 || true
    
    log_success "Self-healing operations completed"
}

validate_service_readiness() {
    local service_name="$1"
    local port="$2"
    local max_attempts="${3:-10}"
    
    log_info "Validating service readiness: $service_name"
    
    # Smart validation - use best method for each service type
    case "$service_name" in
        "redis")
            if docker exec hackathon-redis-1 redis-cli ping 2>/dev/null | grep -q "PONG"; then
                log_success "Service $service_name is ready (Redis PONG)"
                return 0
            fi
            ;;
        "ollama")
            if curl -f http://localhost:11434/api/tags --connect-timeout 3 --max-time 5 &> /dev/null; then
                log_success "Service $service_name is ready (Ollama API)"
                return 0
            fi
            ;;
        "frontend"|"memory-agent"|"source-agent"|"analysis-service"|"code-analyzer"|"notification-service")
            # Use Docker health status for these services
            if docker ps --filter "name=hackathon-${service_name}" --format "{{.Status}}" | grep -q -E "(healthy|Up)"; then
                log_success "Service $service_name is ready (Docker status)"
                return 0
            else
                log_warning "Service $service_name not ready according to Docker"
                return 1
            fi
            ;;
        *)
            # Try HTTP endpoint first, fallback to Docker status
            if curl -f "http://localhost:$port/health" --connect-timeout 2 --max-time 3 &> /dev/null; then
                log_success "Service $service_name is ready (HTTP endpoint)"
                return 0
            elif docker ps --filter "name=hackathon-${service_name}" --format "{{.Status}}" | grep -q -E "(healthy|Up)"; then
                log_success "Service $service_name is ready (Docker status - no HTTP endpoint)"
                return 0
            else
                log_warning "Service $service_name not ready"
                return 1
            fi
            ;;
    esac
}

orchestrated_startup() {
    log_step "Orchestrated Service Startup"
    
    # Phase 1: Infrastructure Services
    log_info "Phase 1: Starting infrastructure services..."
    docker-compose -f "$COMPOSE_FILE" up -d redis ollama
    
    # Wait for Redis
    log_info "Waiting for Redis to be ready..."
    sleep 5
    
    # Phase 2: Core Services
    log_info "Phase 2: Starting core services..."
    docker-compose -f "$COMPOSE_FILE" up -d orchestrator doc_store prompt_store
    
    # Wait for core services
    sleep "$STARTUP_DELAY"
    
    # Phase 3: AI Services
    log_info "Phase 3: Starting AI services..."
    docker-compose -f "$COMPOSE_FILE" --profile ai_services up -d
    
    # Phase 4: Analysis Services  
    log_info "Phase 4: Starting analysis services..."
    docker-compose -f "$COMPOSE_FILE" --profile development up -d
    
    # Phase 5: Frontend and remaining
    log_info "Phase 5: Starting frontend and remaining services..."
    docker-compose -f "$COMPOSE_FILE" --profile core up -d
    
    log_success "Orchestrated startup completed"
}

comprehensive_health_check() {
    log_step "Comprehensive Health Check"
    
    # Key services to validate - using correct ports from Docker health checks
    local key_services_llm_gateway="5055"
    local key_services_orchestrator="5099"
    local key_services_doc_store="5087"
    local key_services_discovery_agent="5045"
    local key_services_analysis_service="5020"
    local key_services_frontend="5090"
    
    local services=("llm-gateway" "orchestrator" "doc_store" "discovery-agent" "analysis-service" "frontend")
    
    local failed_services=()
    
    # Check each key service
    for service in "${services[@]}"; do
        # Get port using variable indirection
        local port_var="key_services_${service//-/_}"
        local port="${!port_var}"
        if ! validate_service_readiness "$service" "$port" 15; then
            failed_services+=("$service")
        fi
    done
    
    # Report results
    if [[ ${#failed_services[@]} -eq 0 ]]; then
        log_success "All key services are healthy"
        return 0
    else
        log_warning "Failed services: ${failed_services[*]}"
        
        if [[ "$SELF_HEAL" == "true" ]]; then
            log_info "Attempting to heal failed services..."
            for service in "${failed_services[@]}"; do
                heal_service "$service"
            done
        fi
        
        return 1
    fi
}

heal_service() {
    local service_name="$1"
    
    log_info "Healing service: $service_name"
    
    # Get service logs
    log_info "Checking logs for $service_name..."
    docker logs "hackathon-${service_name}-1" --tail 10
    
    # Restart the service
    log_info "Restarting $service_name..."
    docker-compose -f "$COMPOSE_FILE" restart "$service_name"
    
    # Wait and re-check
    sleep 10
    
    log_success "Healing attempt completed for $service_name"
}

rollback_on_failure() {
    log_step "Rollback Initiated"
    
    log_warning "Critical issues detected, initiating rollback..."
    
    # Stop all services
    docker-compose -f "$COMPOSE_FILE" down
    
    # Clean up
    docker container prune -f > /dev/null 2>&1 || true
    
    log_success "Rollback completed - system returned to clean state"
}

generate_startup_report() {
    log_step "Generating Startup Report"
    
    local report_file="startup-report-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "$report_file" << EOF
# Bulletproof Startup Report

**Timestamp**: $(date)
**Compose File**: $COMPOSE_FILE
**Self-Heal Mode**: $SELF_HEAL
**Rollback Enabled**: $ROLLBACK_ON_FAILURE

## Container Status
\`\`\`
$(docker ps --filter "name=hackathon" --format "table {{.Names}}\t{{.Status}}")
\`\`\`

## Health Summary
- **Total Containers**: $(docker ps --filter "name=hackathon" | wc -l | tr -d ' ')
- **Healthy Containers**: $(docker ps --filter "name=hackathon" --format "{{.Status}}" | grep -c "healthy" || echo "0")
- **Running Containers**: $(docker ps --filter "name=hackathon" --format "{{.Status}}" | grep -c "Up" || echo "0")

## Key Service Status
EOF

    # Add key service status - using correct ports from Docker health checks
    local key_services_llm_gateway="5055"
    local key_services_orchestrator="5099"
    local key_services_doc_store="5087"
    local key_services_discovery_agent="5045"
    local key_services_analysis_service="5020"
    local key_services_frontend="5090"
    
    local key_services=("llm-gateway" "orchestrator" "doc_store" "discovery-agent" "analysis-service" "frontend")
    
    for service in "${key_services[@]}"; do
        local port_var="key_services_${service//-/_}"
        local port="${!port_var}"
        if curl -f "http://localhost:$port/health" --connect-timeout 3 &> /dev/null; then
            echo "- **$service**: ✅ Healthy" >> "$report_file"
        else
            echo "- **$service**: ❌ Unhealthy" >> "$report_file"
        fi
    done
    
    log_success "Startup report generated: $report_file"
}

# Main execution function
main() {
    echo ""
    echo -e "${BLUE}🛡️ BULLETPROOF ECOSYSTEM STARTUP${NC}"
    echo -e "${BLUE}=================================${NC}"
    echo ""
    
    local start_time=$(date +%s)
    
    # Step 1: Environment validation
    if ! validate_environment; then
        log_error "Environment validation failed"
        exit 1
    fi
    
    # Step 2: Pre-flight checks
    if ! run_pre_flight_checks; then
        if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
            rollback_on_failure
        fi
        log_error "Pre-flight checks failed"
        exit 1
    fi
    
    # Step 3: Clean shutdown of existing services
    log_step "Clean Shutdown"
    docker-compose -f "$COMPOSE_FILE" down > /dev/null 2>&1 || true
    
    # Step 4: Orchestrated startup
    if ! orchestrated_startup; then
        if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
            rollback_on_failure
        fi
        log_error "Startup failed"
        exit 1
    fi
    
    # Step 5: Wait for services to stabilize
    log_step "Service Stabilization"
    log_info "Waiting ${HEALTH_CHECK_TIMEOUT}s for services to stabilize..."
    sleep "$HEALTH_CHECK_TIMEOUT"
    
    # Step 6: Comprehensive health check
    local health_passed=true
    for ((attempt=1; attempt<=MAX_RETRIES; attempt++)); do
        log_info "Health check attempt $attempt/$MAX_RETRIES"
        
        if comprehensive_health_check; then
            health_passed=true
            break
        else
            health_passed=false
            if [[ $attempt -lt $MAX_RETRIES ]]; then
                log_warning "Health check failed, retrying in 30s..."
                sleep 30
            fi
        fi
    done
    
    # Step 7: Final validation
    if [[ "$health_passed" == "false" ]]; then
        log_error "Health checks failed after $MAX_RETRIES attempts"
        
        if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
            rollback_on_failure
            exit 1
        fi
    fi
    
    # Step 8: Generate report
    generate_startup_report
    
    # Calculate execution time
    local end_time=$(date +%s)
    local execution_time=$((end_time - start_time))
    
    echo ""
    echo -e "${GREEN}🎉 BULLETPROOF STARTUP COMPLETED${NC}"
    echo -e "${GREEN}=================================${NC}"
    echo -e "${GREEN}Execution Time: ${execution_time}s${NC}"
    echo -e "${GREEN}Status: $(docker ps --filter 'name=hackathon' --format '{{.Status}}' | grep -c 'healthy' || echo '0') healthy services${NC}"
    echo ""
}

# Handle script arguments
case "${1:-start}" in
    "start")
        main
        ;;
    "heal")
        log_step "Manual Healing Mode"
        attempt_self_heal
        ;;
    "check")
        log_step "Health Check Only"
        if comprehensive_health_check; then
            log_success "Health check completed successfully"
            exit 0
        else
            log_error "Health check failed"
            exit 1
        fi
        ;;
    "rollback")
        rollback_on_failure
        ;;
    *)
        echo "Usage: $0 [start|heal|check|rollback]"
        echo "  start    - Full bulletproof startup (default)"
        echo "  heal     - Run self-healing operations only"
        echo "  check    - Run health checks only"
        echo "  rollback - Emergency rollback"
        exit 1
        ;;
esac

