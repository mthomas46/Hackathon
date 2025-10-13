#!/bin/bash

# Ecosystem MCP Preflight Check Script
# Validates all dependencies and environment before starting the service

# Don't exit on errors, we want to check everything
set +e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# Print functions
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
}

print_check() {
    echo -e "${BLUE}▶ Checking: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((CHECKS_PASSED++))
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    ((CHECKS_FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((CHECKS_WARNING++))
}

# Preflight checks
print_header "ECOSYSTEM MCP - PREFLIGHT CHECKS"

# 1. Check Docker
print_check "Docker daemon"
if docker info >/dev/null 2>&1; then
    print_success "Docker is running"
else
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi

# 2. Check Docker Compose
print_check "Docker Compose"
if command -v docker-compose >/dev/null 2>&1; then
    VERSION=$(docker-compose version --short)
    print_success "Docker Compose installed (v$VERSION)"
else
    print_error "Docker Compose is not installed"
    exit 1
fi

# 3. Check required ports
print_check "Required ports availability"
REQUIRED_PORTS=(5432 6379 8000 8501 11434)
PORT_CONFLICTS=()

for PORT in "${REQUIRED_PORTS[@]}"; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        PROCESS=$(lsof -Pi :$PORT -sTCP:LISTEN | tail -n 1 | awk '{print $1}')
        PORT_CONFLICTS+=("$PORT ($PROCESS)")
    fi
done

if [ ${#PORT_CONFLICTS[@]} -eq 0 ]; then
    print_success "All required ports are available (5432, 6379, 8000, 8501, 11434)"
else
    print_warning "Some ports are already in use: ${PORT_CONFLICTS[*]}"
    echo "  This may be OK if the services are already running."
fi

# 4. Check Python
print_check "Python 3.11+"
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
        print_success "Python $PYTHON_VERSION installed"
    else
        print_warning "Python $PYTHON_VERSION found, but 3.11+ recommended"
    fi
else
    print_error "Python 3 is not installed"
    exit 1
fi

# 5. Check required files
print_check "Required configuration files"
REQUIRED_FILES=(
    "requirements.txt"
    "docker-compose.yml"
    "src/config.py"
    "src/api/app.py"
)

for FILE in "${REQUIRED_FILES[@]}"; do
    if [ -f "$FILE" ]; then
        echo -e "  ${GREEN}✓${NC} $FILE"
    else
        print_error "Missing file: $FILE"
        exit 1
    fi
done
print_success "All required files present"

# 6. Check Docker containers status
print_check "Docker containers"
POSTGRES_RUNNING=$(docker ps --filter "name=ecosystem-mcp-postgres" --format "{{.Names}}" 2>/dev/null)
REDIS_RUNNING=$(docker ps --filter "name=ecosystem-mcp-redis" --format "{{.Names}}" 2>/dev/null)
OLLAMA_RUNNING=$(docker ps --filter "name=ecosystem-mcp-ollama" --format "{{.Names}}" 2>/dev/null)

if [ -n "$POSTGRES_RUNNING" ]; then
    POSTGRES_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' $POSTGRES_RUNNING 2>/dev/null || echo "unknown")
    echo -e "  ${GREEN}✓${NC} PostgreSQL: running ($POSTGRES_HEALTH)"
else
    echo -e "  ${YELLOW}○${NC} PostgreSQL: not running (will be started)"
fi

if [ -n "$REDIS_RUNNING" ]; then
    REDIS_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' $REDIS_RUNNING 2>/dev/null || echo "unknown")
    echo -e "  ${GREEN}✓${NC} Redis: running ($REDIS_HEALTH)"
else
    echo -e "  ${YELLOW}○${NC} Redis: not running (will be started)"
fi

if [ -n "$OLLAMA_RUNNING" ]; then
    echo -e "  ${GREEN}✓${NC} Ollama: running"
else
    echo -e "  ${YELLOW}○${NC} Ollama: not running (will be started)"
fi

# 7. Check disk space
print_check "Disk space"
AVAILABLE_SPACE=$(df -h . | tail -1 | awk '{print $4}')
AVAILABLE_SPACE_GB=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')

if [ "$AVAILABLE_SPACE_GB" -gt 10 ]; then
    print_success "Sufficient disk space available ($AVAILABLE_SPACE)"
else
    print_warning "Low disk space: $AVAILABLE_SPACE (10GB+ recommended)"
fi

# 8. Check memory
print_check "System memory"
if command -v free >/dev/null 2>&1; then
    TOTAL_MEM=$(free -h | grep Mem | awk '{print $2}')
    AVAILABLE_MEM=$(free -h | grep Mem | awk '{print $7}')
    print_success "Memory: $AVAILABLE_MEM available of $TOTAL_MEM total"
elif command -v vm_stat >/dev/null 2>&1; then
    # macOS
    PAGES_FREE=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    PAGES_INACTIVE=$(vm_stat | grep "Pages inactive" | awk '{print $3}' | sed 's/\.//')
    PAGE_SIZE=4096
    FREE_MEM=$((($PAGES_FREE + $PAGES_INACTIVE) * $PAGE_SIZE / 1024 / 1024))
    print_success "Memory: ~${FREE_MEM}MB available"
else
    print_warning "Could not check memory status"
fi

# 9. Check network connectivity
print_check "Network connectivity"
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    print_success "Network connectivity OK"
else
    print_warning "Network connectivity check failed (may be OK if using local DNS)"
fi

# 10. Check environment variables
print_check "Environment configuration"
if [ -f ".env" ]; then
    echo -e "  ${GREEN}✓${NC} .env file found"
    
    # Check for critical env vars
    if grep -q "POSTGRES_PASSWORD" .env; then
        echo -e "  ${GREEN}✓${NC} POSTGRES_PASSWORD configured"
    else
        print_warning "POSTGRES_PASSWORD not found in .env"
    fi
else
    print_warning ".env file not found (using defaults)"
fi

# Summary
print_header "PREFLIGHT CHECK SUMMARY"

echo -e "${GREEN}✅ Passed:  $CHECKS_PASSED${NC}"
if [ $CHECKS_WARNING -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Warnings: $CHECKS_WARNING${NC}"
fi
if [ $CHECKS_FAILED -gt 0 ]; then
    echo -e "${RED}❌ Failed:  $CHECKS_FAILED${NC}"
fi

echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🚀 System is ready to start!${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}⛔ System is not ready. Please fix the errors above.${NC}"
    echo ""
    exit 1
fi

