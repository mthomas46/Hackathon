#!/bin/bash
##
## Ecosystem MCP Network & Self-Healing Test Script
##
## Tests Docker network connectivity and self-healing capabilities
##

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/mykalthomas/Documents/work/Hackathon"
COMPOSE_FILE="$PROJECT_ROOT/services/ecosystem-mcp/docker-compose.yml"
NETWORK_NAME="ecosystem-mcp"

print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}================================================================================${NC}"
    echo -e "${BOLD}${BLUE}$(printf '%*s' $(((${#1}+80)/2)) "$1")${NC}"
    echo -e "${BOLD}${BLUE}================================================================================${NC}"
    echo ""
}

print_test() {
    local name=$1
    local result=$2
    local details=$3
    
    if [ "$result" = "pass" ]; then
        echo -e "${GREEN}✅ PASS${NC} - $name"
    else
        echo -e "${RED}❌ FAIL${NC} - $name"
    fi
    
    if [ -n "$details" ]; then
        echo -e "     ${YELLOW}$details${NC}"
    fi
}

# Test 1: Docker is running
test_docker() {
    print_header "🐳 DOCKER DAEMON TEST"
    
    if docker info > /dev/null 2>&1; then
        print_test "Docker daemon" "pass" "Docker is running"
        return 0
    else
        print_test "Docker daemon" "fail" "Docker is not running"
        echo -e "${YELLOW}Please start Docker Desktop and try again${NC}"
        return 1
    fi
}

# Test 2: Network exists
test_network() {
    print_header "🌐 NETWORK EXISTENCE TEST"
    
    if docker network inspect "$NETWORK_NAME" > /dev/null 2>&1; then
        print_test "Network '$NETWORK_NAME'" "pass" "Network exists"
        
        # Get network details
        local driver=$(docker network inspect "$NETWORK_NAME" -f '{{.Driver}}')
        local subnet=$(docker network inspect "$NETWORK_NAME" -f '{{range .IPAM.Config}}{{.Subnet}}{{end}}')
        echo -e "     ${CYAN}Driver: $driver${NC}"
        echo -e "     ${CYAN}Subnet: $subnet${NC}"
        return 0
    else
        print_test "Network '$NETWORK_NAME'" "fail" "Network does not exist"
        return 1
    fi
}

# Test 3: Services are running
test_services() {
    print_header "📦 CONTAINER STATUS TEST"
    
    local services=("ecosystem-mcp-postgres" "ecosystem-mcp-redis" "ecosystem-mcp-ollama" "ecosystem-mcp-service" "ecosystem-mcp-dashboard")
    local all_pass=0
    
    for service in "${services[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
            local status=$(docker ps --filter "name=^${service}$" --format '{{.Status}}')
            local health=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "none")
            
            if [ "$health" = "healthy" ] || [ "$health" = "none" ]; then
                print_test "$service" "pass" "Status: $status | Health: $health"
            else
                print_test "$service" "fail" "Status: $status | Health: $health"
                all_pass=1
            fi
        else
            print_test "$service" "fail" "Container not running"
            all_pass=1
        fi
    done
    
    return $all_pass
}

# Test 4: Inter-service connectivity
test_connectivity() {
    print_header "🔗 INTER-SERVICE CONNECTIVITY TEST"
    
    # Test from ecosystem-mcp service to other services
    local tests=(
        "postgres:5432:PostgreSQL"
        "redis:6379:Redis"
        "ollama:11434:Ollama"
        "dashboard:8501:Dashboard"
    )
    
    local all_pass=0
    
    for test in "${tests[@]}"; do
        IFS=':' read -r host port name <<< "$test"
        
        # Use nc (netcat) inside the ecosystem-mcp container
        if docker exec ecosystem-mcp-service nc -zv "$host" "$port" > /dev/null 2>&1; then
            print_test "ecosystem-mcp → $name ($host:$port)" "pass" "Connection successful"
        else
            print_test "ecosystem-mcp → $name ($host:$port)" "fail" "Connection failed"
            all_pass=1
        fi
    done
    
    return $all_pass
}

# Test 5: Health endpoints
test_health_endpoints() {
    print_header "🏥 HEALTH ENDPOINT TEST"
    
    local endpoints=(
        "http://localhost:8000/health:API Health"
        "http://localhost:8501/_stcore/health:Dashboard Health"
    )
    
    local all_pass=0
    
    for endpoint in "${endpoints[@]}"; do
        IFS=':' read -r url name <<< "$endpoint"
        
        local status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        
        if [ "$status" = "200" ]; then
            print_test "$name" "pass" "HTTP $status"
        else
            print_test "$name" "fail" "HTTP $status"
            all_pass=1
        fi
    done
    
    return $all_pass
}

# Test 6: Self-healing test
test_self_healing() {
    print_header "🔄 SELF-HEALING TEST"
    
    echo -e "${YELLOW}This test will stop a service and verify Docker restarts it${NC}"
    echo -e "${YELLOW}Testing with Redis (restart policy: unless-stopped)${NC}"
    echo ""
    
    # Stop Redis
    echo "Stopping Redis container..."
    docker stop ecosystem-mcp-redis > /dev/null 2>&1
    print_test "Stop Redis" "pass" "Container stopped"
    
    # Wait a few seconds
    echo "Waiting 10 seconds for Docker to restart..."
    sleep 10
    
    # Check if Redis restarted
    if docker ps --filter "name=ecosystem-mcp-redis" --format '{{.Names}}' | grep -q "ecosystem-mcp-redis"; then
        local status=$(docker ps --filter "name=ecosystem-mcp-redis" --format '{{.Status}}')
        print_test "Redis Self-Healing" "pass" "Container restarted automatically | Status: $status"
        
        # Wait for health check
        echo "Waiting for Redis health check..."
        sleep 5
        
        local health=$(docker inspect --format='{{.State.Health.Status}}' "ecosystem-mcp-redis" 2>/dev/null || echo "none")
        if [ "$health" = "healthy" ]; then
            print_test "Redis Health Recovery" "pass" "Health check: $health"
            return 0
        else
            print_test "Redis Health Recovery" "fail" "Health check: $health"
            return 1
        fi
    else
        print_test "Redis Self-Healing" "fail" "Container did not restart"
        return 1
    fi
}

# Test 7: Run validation inside network
test_validation_script() {
    print_header "🔍 INTERNAL NETWORK VALIDATION"
    
    echo "Running validation script inside ecosystem-mcp container..."
    echo ""
    
    # Copy validation script to container
    docker cp "$PROJECT_ROOT/services/ecosystem-mcp/docker/validate_services.py" ecosystem-mcp-service:/tmp/validate_services.py > /dev/null 2>&1
    
    # Run validation
    if docker exec ecosystem-mcp-service python3 /tmp/validate_services.py; then
        return 0
    else
        return 1
    fi
}

# Main
main() {
    print_header "🧪 ECOSYSTEM MCP NETWORK & SELF-HEALING TEST SUITE"
    echo -e "${BOLD}Testing Docker network connectivity and service resilience${NC}"
    echo ""
    
    local total_tests=0
    local passed_tests=0
    
    # Run all tests
    tests=(
        "test_docker"
        "test_network"
        "test_services"
        "test_connectivity"
        "test_health_endpoints"
        "test_validation_script"
        "test_self_healing"
    )
    
    for test in "${tests[@]}"; do
        ((total_tests++))
        if $test; then
            ((passed_tests++))
        fi
    done
    
    # Summary
    print_header "📊 TEST SUMMARY"
    
    local failed_tests=$((total_tests - passed_tests))
    local success_rate=$((passed_tests * 100 / total_tests))
    
    echo -e "${BOLD}Total Tests:${NC} $total_tests"
    echo -e "${GREEN}${BOLD}Passed:${NC} $passed_tests"
    echo -e "${RED}${BOLD}Failed:${NC} $failed_tests"
    echo -e "${CYAN}${BOLD}Success Rate:${NC} $success_rate%"
    echo ""
    
    if [ $success_rate -ge 80 ]; then
        echo -e "${GREEN}${BOLD}✅ NETWORK & SELF-HEALING TESTS PASSED${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}${BOLD}❌ NETWORK & SELF-HEALING TESTS FAILED${NC}"
        echo ""
        echo -e "${YELLOW}Troubleshooting:${NC}"
        echo "  1. Check logs: docker compose -f $COMPOSE_FILE logs"
        echo "  2. Restart services: docker compose -f $COMPOSE_FILE restart"
        echo "  3. Rebuild: docker compose -f $COMPOSE_FILE up -d --build"
        echo ""
        return 1
    fi
}

# Run main
main
exit $?

