#!/bin/bash

# Development Setup Script
# Project Simulation Service - Local Development Environment Setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="project-simulation"
CONFIG_DIR="config"
DATA_DIR="data"
LOGS_DIR="logs"
CACHE_DIR="cache"

# Functions
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}🚀 $PROJECT_NAME - Development Setup${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

check_dependencies() {
    print_step "Checking dependencies..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        exit 1
    fi

    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is required but not installed."
        exit 1
    fi

    # Check Docker (optional)
    if ! command -v docker &> /dev/null; then
        print_warning "Docker is not installed. Docker Compose features will not be available."
    else
        print_success "Docker is available"
    fi

    # Check Docker Compose (optional)
    if ! command -v docker-compose &> /dev/null; then
        print_warning "Docker Compose is not installed. Docker Compose features will not be available."
    fi

    print_success "Dependencies check completed"
}

setup_directories() {
    print_step "Setting up directories..."

    # Create required directories
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOGS_DIR"
    mkdir -p "$CACHE_DIR"
    mkdir -p "profiling"

    # Set proper permissions
    chmod 755 "$CONFIG_DIR"
    chmod 755 "$DATA_DIR"
    chmod 755 "$LOGS_DIR"
    chmod 755 "$CACHE_DIR"

    print_success "Directories created"
}

setup_python_environment() {
    print_step "Setting up Python environment..."

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_step "Creating virtual environment..."
        python3 -m venv venv
    else
        print_success "Virtual environment already exists"
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install development dependencies
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi

    # Install the project in development mode
    pip install -e .

    print_success "Python environment setup completed"
}

setup_configuration() {
    print_step "Setting up configuration..."

    # Copy local development configuration if it doesn't exist
    if [ ! -f ".env" ] && [ -f "$CONFIG_DIR/local-development.env" ]; then
        cp "$CONFIG_DIR/local-development.env" .env
        print_success "Local development configuration copied to .env"
    elif [ ! -f ".env" ]; then
        print_warning "No .env file found. Creating basic development configuration..."

        cat > .env << EOF
# Basic Development Configuration
ENVIRONMENT=development
SERVICE_NAME=project-simulation
SERVICE_VERSION=1.0.0-dev
HOST=0.0.0.0
PORT=5075
DEBUG=true
RELOAD=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///./data/project_simulation_dev.db
REDIS_URL=redis://localhost:6379/0
ENABLE_SWAGGER=true
ENABLE_REDOC=true
ENABLE_CORS=true
RATE_LIMIT_ENABLED=false
ENABLE_METRICS=true
ENABLE_HEALTH_CHECKS=true
EOF
        print_success "Basic .env file created"
    else
        print_success "Configuration already exists"
    fi
}

setup_database() {
    print_step "Setting up database..."

    # For SQLite, just ensure the data directory exists
    if [[ $DATABASE_URL == sqlite* ]]; then
        mkdir -p "$DATA_DIR"
        print_success "SQLite database directory ready"
    else
        print_warning "Non-SQLite database detected. Please ensure database is running and accessible."
    fi
}

setup_docker_services() {
    print_step "Setting up Docker services..."

    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        # Check if docker-compose.dev.yml exists
        if [ -f "docker-compose.dev.yml" ]; then
            print_step "Starting development Docker services..."

            # Start services in detached mode
            docker-compose -f docker-compose.dev.yml up -d redis

            # Wait for services to be ready
            echo "Waiting for Redis to be ready..."
            sleep 5

            print_success "Docker services started"
        else
            print_warning "docker-compose.dev.yml not found"
        fi
    else
        print_warning "Docker or Docker Compose not available. Skipping Docker setup."
    fi
}

validate_setup() {
    print_step "Validating setup..."

    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi

    # Run configuration validation
    if python3 -c "from simulation.infrastructure.config import validate_configuration; validate_configuration()" 2>/dev/null; then
        print_success "Configuration validation passed"
    else
        print_warning "Configuration validation failed. Check logs for details."
    fi

    # Test basic imports
    if python3 -c "from simulation.infrastructure.config import get_config; config = get_config(); print('Config loaded successfully')" 2>/dev/null; then
        print_success "Basic imports working"
    else
        print_error "Basic imports failed. Check Python path and dependencies."
        exit 1
    fi
}

print_instructions() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${GREEN}🎉 Development environment setup completed!${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Activate the virtual environment:"
    echo -e "   ${GREEN}source venv/bin/activate${NC}"
    echo ""
    echo "2. Start the development server:"
    echo -e "   ${GREEN}python main.py${NC}"
    echo "   or"
    echo -e "   ${GREEN}uvicorn main:app --host 0.0.0.0 --port 5075 --reload${NC}"
    echo ""
    echo "3. Open API documentation:"
    echo -e "   ${GREEN}http://localhost:5075/docs${NC}"
    echo ""
    echo "4. Check health endpoint:"
    echo -e "   ${GREEN}http://localhost:5075/health${NC}"
    echo ""
    echo "5. View logs:"
    echo -e "   ${GREEN}tail -f logs/project_simulation_dev.log${NC}"
    echo ""
    echo -e "${YELLOW}Useful commands:${NC}"
    echo "- Run tests: python -m pytest"
    echo "- Check config: python -c \"from simulation.infrastructure.config import print_env_info; print_env_info()\""
    echo "- Validate config: python -c \"from simulation.infrastructure.config import print_validation_report; print_validation_report()\""
    echo ""
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        echo -e "${YELLOW}Docker commands:${NC}"
        echo "- Start all services: docker-compose -f docker-compose.dev.yml up -d"
        echo "- Stop all services: docker-compose -f docker-compose.dev.yml down"
        echo "- View logs: docker-compose -f docker-compose.dev.yml logs -f"
        echo ""
    fi
}

main() {
    print_header

    check_dependencies
    setup_directories
    setup_python_environment
    setup_configuration
    setup_database
    setup_docker_services
    validate_setup

    print_instructions
}

# Handle command line arguments
case "${1:-}" in
    "--help"|"-h")
        echo "Development Setup Script for $PROJECT_NAME"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --clean              Clean existing setup before installing"
        echo "  --no-docker          Skip Docker setup"
        echo ""
        exit 0
        ;;
    "--clean")
        print_warning "Cleaning existing setup..."
        rm -rf venv .env "$DATA_DIR" "$LOGS_DIR" "$CACHE_DIR"
        ;;
    "--no-docker")
        print_warning "Skipping Docker setup..."
        setup_docker_services() { print_warning "Docker setup skipped"; }
        ;;
esac

main
