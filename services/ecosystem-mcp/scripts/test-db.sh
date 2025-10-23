#!/bin/bash
# Test Database Management Script
# Manage test database container for running integration tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker compose.test.yml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Command handlers
cmd_start() {
    print_header "Starting Test Database"
    docker compose -f "$COMPOSE_FILE" up -d
    
    print_info "Waiting for services to be healthy..."
    sleep 5
    
    if docker compose -f "$COMPOSE_FILE" ps | grep -q "Up (healthy)"; then
        print_success "Test database is running!"
        print_info "PostgreSQL: localhost:5433"
        print_info "Redis: localhost:6380"
        print_info "ChromaDB: localhost:8001"
        echo ""
        print_info "Connection string:"
        echo "  postgresql://test_user:test_password@localhost:5433/ecosystem_mcp_test"
    else
        print_warning "Services starting... check status with: $0 status"
    fi
}

cmd_stop() {
    print_header "Stopping Test Database"
    docker compose -f "$COMPOSE_FILE" down
    print_success "Test database stopped"
}

cmd_restart() {
    print_header "Restarting Test Database"
    cmd_stop
    sleep 2
    cmd_start
}

cmd_reset() {
    print_header "Resetting Test Database"
    print_warning "This will destroy all test data!"
    docker compose -f "$COMPOSE_FILE" down -v
    sleep 2
    cmd_start
    print_success "Test database reset complete"
}

cmd_logs() {
    print_header "Test Database Logs"
    docker compose -f "$COMPOSE_FILE" logs -f
}

cmd_status() {
    print_header "Test Database Status"
    docker compose -f "$COMPOSE_FILE" ps
    echo ""
    
    # Check health
    if docker ps --filter "name=ecosystem-mcp-postgres-test" --filter "health=healthy" | grep -q ecosystem-mcp-postgres-test; then
        print_success "PostgreSQL: Healthy"
    else
        print_error "PostgreSQL: Unhealthy or not running"
    fi
    
    if docker ps --filter "name=ecosystem-mcp-redis-test" --filter "health=healthy" | grep -q ecosystem-mcp-redis-test; then
        print_success "Redis: Healthy"
    else
        print_error "Redis: Unhealthy or not running"
    fi
    
    if docker ps --filter "name=ecosystem-mcp-chroma-test" | grep -q ecosystem-mcp-chroma-test; then
        print_success "ChromaDB: Running"
    else
        print_warning "ChromaDB: Not running"
    fi
}

cmd_psql() {
    print_info "Connecting to test database..."
    docker exec -it ecosystem-mcp-postgres-test psql -U test_user -d ecosystem_mcp_test
}

cmd_redis() {
    print_info "Connecting to test Redis..."
    docker exec -it ecosystem-mcp-redis-test redis-cli
}

cmd_clean() {
    print_header "Cleaning Test Database"
    print_info "Truncating all tables..."
    
    docker exec -i ecosystem-mcp-postgres-test psql -U test_user -d ecosystem_mcp_test <<EOF
DO \$\$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END \$\$;
EOF
    
    docker exec -i ecosystem-mcp-redis-test redis-cli FLUSHALL
    
    print_success "Test database cleaned (tables truncated, Redis flushed)"
}

cmd_init() {
    print_header "Initializing Test Database Schema"
    
    # Check if migrations exist
    if [ -d "$PROJECT_ROOT/src/storage/migrations" ]; then
        print_info "Running migrations..."
        
        export DATABASE_URL="postgresql://test_user:test_password@localhost:5433/ecosystem_mcp_test"
        
        # Run migrations (you'll need to implement your migration runner)
        # python -m src.storage.migrations.run_migrations
        
        print_success "Schema initialized"
    else
        print_warning "No migrations found in src/storage/migrations"
    fi
}

cmd_help() {
    cat <<EOF
${BLUE}Test Database Management${NC}

${GREEN}Usage:${NC}
  $0 <command>

${GREEN}Commands:${NC}
  start     - Start test database containers
  stop      - Stop test database containers
  restart   - Restart test database containers
  reset     - Stop, remove volumes, and start fresh
  status    - Show container status and health
  logs      - Follow container logs
  psql      - Connect to PostgreSQL CLI
  redis     - Connect to Redis CLI
  clean     - Truncate all tables and flush Redis (keep schema)
  init      - Initialize database schema with migrations
  help      - Show this help message

${GREEN}Environment Variables:${NC}
  TEST_DATABASE_URL=postgresql://test_user:test_password@localhost:5433/ecosystem_mcp_test
  TEST_REDIS_URL=redis://localhost:6380/0
  TEST_CHROMA_URL=http://localhost:8001

${GREEN}Examples:${NC}
  # Start test database
  $0 start

  # Run tests with test database
  export DATABASE_URL="postgresql://test_user:test_password@localhost:5433/ecosystem_mcp_test"
  pytest tests/integration/

  # Clean database between test runs
  $0 clean

  # Reset everything
  $0 reset
EOF
}

# Main command router
case "${1:-help}" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    reset)
        cmd_reset
        ;;
    logs)
        cmd_logs
        ;;
    status)
        cmd_status
        ;;
    psql)
        cmd_psql
        ;;
    redis)
        cmd_redis
        ;;
    clean)
        cmd_clean
        ;;
    init)
        cmd_init
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        cmd_help
        exit 1
        ;;
esac

