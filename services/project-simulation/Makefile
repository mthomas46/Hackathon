# =============================================================================
# Project Simulation Service - Makefile
# =============================================================================
# Comprehensive build, test, and deployment automation for the project-simulation service
# =============================================================================

# Configuration
PYTHON ?= python3
SERVICE_NAME := project-simulation
SERVICE_PORT := 5075
DOCKER_IMAGE := hackathon/$(SERVICE_NAME)
DOCKER_TAG ?= latest
DOCKER_COMPOSE_FILE := docker-compose.dev.yml

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
NC := \033[0m # No Color

# Help target
.PHONY: help
help: ## Show this help message
	@echo "$(CYAN)🚀 Project Simulation Service Commands$(NC)"
	@echo "==========================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(BLUE)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Available Profiles:$(NC)"
	@echo "  make docker-run         - Run service in Docker (development)"
	@echo "  make docker-run-prod    - Run service in Docker (production)"
	@echo "  make docker-run-test    - Run service in Docker (testing)"
	@echo "  make docker-compose-up  - Run with docker-compose (full ecosystem)"

# ============================================================================
# DEVELOPMENT COMMANDS
# ============================================================================

.PHONY: run
run: ## Run the service locally (development mode)
	@echo "$(BLUE)🚀 Starting $(SERVICE_NAME) service in development mode...$(NC)"
	$(PYTHON) main.py

.PHONY: run-production
run-production: ## Run the service locally (production mode)
	@echo "$(BLUE)🚀 Starting $(SERVICE_NAME) service in production mode...$(NC)"
	export ENVIRONMENT=production && $(PYTHON) main.py

# ============================================================================
# DOCKER COMMANDS
# ============================================================================

.PHONY: docker-build
docker-build: ## Build Docker image (development target)
	@echo "$(BLUE)🐳 Building $(SERVICE_NAME) Docker image (development)...$(NC)"
	docker build --target development -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "$(GREEN)✅ Docker image built: $(DOCKER_IMAGE):$(DOCKER_TAG)$(NC)"

.PHONY: docker-build-prod
docker-build-prod: ## Build Docker image (production target)
	@echo "$(BLUE)🐳 Building $(SERVICE_NAME) Docker image (production)...$(NC)"
	docker build --target runtime -t $(DOCKER_IMAGE):prod-$(DOCKER_TAG) .
	@echo "$(GREEN)✅ Docker image built: $(DOCKER_IMAGE):prod-$(DOCKER_TAG)$(NC)"

.PHONY: docker-build-test
docker-build-test: ## Build Docker image (testing target)
	@echo "$(BLUE)🐳 Building $(SERVICE_NAME) Docker image (testing)...$(NC)"
	docker build --target testing -t $(DOCKER_IMAGE):test-$(DOCKER_TAG) .
	@echo "$(GREEN)✅ Docker image built: $(DOCKER_IMAGE):test-$(DOCKER_TAG)$(NC)"

.PHONY: docker-run
docker-run: docker-build ## Run service in Docker container (development)
	@echo "$(BLUE)🚀 Running $(SERVICE_NAME) in Docker container (development)...$(NC)"
	docker run --rm \
		--name $(SERVICE_NAME)-dev \
		-p $(SERVICE_PORT):$(SERVICE_PORT) \
		-e ENVIRONMENT=development \
		-e SERVICE_PORT=$(SERVICE_PORT) \
		-e REDIS_HOST=host.docker.internal \
		-v $(PWD):/app \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

.PHONY: docker-run-prod
docker-run-prod: docker-build-prod ## Run service in Docker container (production)
	@echo "$(BLUE)🚀 Running $(SERVICE_NAME) in Docker container (production)...$(NC)"
	docker run --rm \
		--name $(SERVICE_NAME)-prod \
		-p $(SERVICE_PORT):$(SERVICE_PORT) \
		-e ENVIRONMENT=production \
		-e SERVICE_PORT=$(SERVICE_PORT) \
		-e REDIS_HOST=host.docker.internal \
		$(DOCKER_IMAGE):prod-$(DOCKER_TAG)

.PHONY: docker-run-test
docker-run-test: docker-build-test ## Run tests in Docker container
	@echo "$(BLUE)🧪 Running tests in Docker container...$(NC)"
	docker run --rm \
		--name $(SERVICE_NAME)-test \
		-v $(PWD):/app \
		$(DOCKER_IMAGE):test-$(DOCKER_TAG)

.PHONY: docker-stop
docker-stop: ## Stop running Docker containers
	@echo "$(BLUE)🛑 Stopping $(SERVICE_NAME) Docker containers...$(NC)"
	docker stop $(SERVICE_NAME)-dev $(SERVICE_NAME)-prod $(SERVICE_NAME)-test 2>/dev/null || true
	@echo "$(GREEN)✅ Docker containers stopped$(NC)"

.PHONY: docker-clean
docker-clean: ## Clean Docker images and containers
	@echo "$(BLUE)🧹 Cleaning Docker resources...$(NC)"
	docker stop $(SERVICE_NAME)-dev $(SERVICE_NAME)-prod $(SERVICE_NAME)-test 2>/dev/null || true
	docker rm $(SERVICE_NAME)-dev $(SERVICE_NAME)-prod $(SERVICE_NAME)-test 2>/dev/null || true
	docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_IMAGE):prod-$(DOCKER_TAG) $(DOCKER_IMAGE):test-$(DOCKER_TAG) 2>/dev/null || true
	@echo "$(GREEN)✅ Docker resources cleaned$(NC)"

# ============================================================================
# DOCKER COMPOSE COMMANDS
# ============================================================================

.PHONY: docker-compose-up
docker-compose-up: ## Start service with docker-compose (full ecosystem)
	@echo "$(BLUE)🚀 Starting $(SERVICE_NAME) with docker-compose (ecosystem)...$(NC)"
	docker-compose -f ../../$(DOCKER_COMPOSE_FILE) --profile simulation up -d
	@echo "$(GREEN)✅ Service started with docker-compose$(NC)"
	@echo "$(YELLOW)📊 Service available at: http://localhost:$(SERVICE_PORT)$(NC)"

.PHONY: docker-compose-up-logs
docker-compose-up-logs: ## Start service with docker-compose and show logs
	@echo "$(BLUE)🚀 Starting $(SERVICE_NAME) with docker-compose (with logs)...$(NC)"
	docker-compose -f ../../$(DOCKER_COMPOSE_FILE) --profile simulation up
	@echo "$(GREEN)✅ Service logs displayed$(NC)"

.PHONY: docker-compose-down
docker-compose-down: ## Stop service with docker-compose
	@echo "$(BLUE)🛑 Stopping $(SERVICE_NAME) with docker-compose...$(NC)"
	docker-compose -f ../../$(DOCKER_COMPOSE_FILE) --profile simulation down
	@echo "$(GREEN)✅ Service stopped with docker-compose$(NC)"

.PHONY: docker-compose-logs
docker-compose-logs: ## Show docker-compose logs
	@echo "$(BLUE)📋 Showing $(SERVICE_NAME) docker-compose logs...$(NC)"
	docker-compose -f ../../$(DOCKER_COMPOSE_FILE) --profile simulation logs -f

.PHONY: docker-compose-build
docker-compose-build: ## Build service with docker-compose
	@echo "$(BLUE)🐳 Building $(SERVICE_NAME) with docker-compose...$(NC)"
	docker-compose -f ../../$(DOCKER_COMPOSE_FILE) --profile simulation build
	@echo "$(GREEN)✅ Service built with docker-compose$(NC)"

# ============================================================================
# TESTING COMMANDS
# ============================================================================

.PHONY: test
test: ## Run test suite
	@echo "$(BLUE)🧪 Running $(SERVICE_NAME) test suite...$(NC)"
	$(PYTHON) -m pytest tests/ -v --tb=short

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "$(BLUE)🧪 Running unit tests...$(NC)"
	$(PYTHON) -m pytest tests/unit/ -v

.PHONY: test-integration
test-integration: ## Run integration tests only
	@echo "$(BLUE)🧪 Running integration tests...$(NC)"
	$(PYTHON) -m pytest tests/integration/ -v

.PHONY: test-api
test-api: ## Run API tests only
	@echo "$(BLUE)🧪 Running API tests...$(NC)"
	$(PYTHON) -m pytest tests/api/ -v

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)🧪 Running tests with coverage...$(NC)"
	$(PYTHON) -m pytest --cov=. --cov-report=html --cov-report=term tests/
	@echo "$(GREEN)📊 Coverage report generated in htmlcov/$(NC)"

# ============================================================================
# HEALTH AND MONITORING
# ============================================================================

.PHONY: health-check
health-check: ## Check service health
	@echo "$(BLUE)🏥 Checking $(SERVICE_NAME) health...$(NC)"
	curl -f http://localhost:$(SERVICE_PORT)/health || echo "$(RED)❌ Service not healthy$(NC)"
	@echo "$(GREEN)✅ Service health check complete$(NC)"

.PHONY: status
status: ## Show service status
	@echo "$(BLUE)📊 $(SERVICE_NAME) Service Status$(NC)"
	@echo "=================================="
	@echo "Service: $(SERVICE_NAME)"
	@echo "Port: $(SERVICE_PORT)"
	@echo "Environment: $$(echo $$ENVIRONMENT || echo 'development')"
	@echo "Docker Image: $(DOCKER_IMAGE)"
	@echo ""
	@echo "$(YELLOW)Health Check:$(NC)"
	@curl -s http://localhost:$(SERVICE_PORT)/health > /dev/null && echo "✅ Service is healthy" || echo "❌ Service is not responding"
	@echo ""
	@echo "$(YELLOW)Docker Containers:$(NC)"
	@docker ps --filter name=$(SERVICE_NAME) --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# ============================================================================
# UTILITY COMMANDS
# ============================================================================

.PHONY: clean
clean: ## Clean up generated files and caches
	@echo "$(BLUE)🧹 Cleaning up $(SERVICE_NAME)...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage coverage.xml
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

.PHONY: install-deps
install-deps: ## Install Python dependencies
	@echo "$(BLUE)📦 Installing $(SERVICE_NAME) dependencies...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

.PHONY: install-dev-deps
install-dev-deps: ## Install development dependencies
	@echo "$(BLUE)📦 Installing $(SERVICE_NAME) development dependencies...$(NC)"
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-xdist black isort flake8 mypy
	@echo "$(GREEN)✅ Development dependencies installed$(NC)"

.PHONY: lint
lint: ## Run code linting
	@echo "$(BLUE)🔍 Running code linting...$(NC)"
	black --check . || echo "$(YELLOW)⚠️  Code formatting issues found$(NC)"
	isort --check-only . || echo "$(YELLOW)⚠️  Import sorting issues found$(NC)"
	flake8 . || echo "$(YELLOW)⚠️  Linting issues found$(NC)"
	@echo "$(GREEN)✅ Linting complete$(NC)"

.PHONY: format
format: ## Format code with black and isort
	@echo "$(BLUE)🎨 Formatting code...$(NC)"
	black .
	isort .
	@echo "$(GREEN)✅ Code formatted$(NC)"

.PHONY: db-init
db-init: ## Initialize/reset the simulation database
	@echo "$(BLUE)💾 Initializing $(SERVICE_NAME) database...$(NC)"
	rm -f data/simulation.db
	$(PYTHON) -c "from simulation.infrastructure.repositories.sqlite_repositories import get_sqlite_simulation_repository; repo = get_sqlite_simulation_repository(); print('✅ Database initialized')"
	@echo "$(GREEN)✅ Database initialized$(NC)"

.PHONY: db-migrate
db-migrate: ## Run database migrations
	@echo "$(BLUE)💾 Running database migrations...$(NC)"
	# Add migration logic here if needed
	@echo "$(GREEN)✅ Database migrations complete$(NC)"

.PHONY: logs
logs: ## Show service logs
	@echo "$(BLUE)📋 Showing $(SERVICE_NAME) logs...$(NC)"
	docker logs $(SERVICE_NAME)-dev 2>/dev/null || docker logs $(SERVICE_NAME)-prod 2>/dev/null || echo "$(YELLOW)⚠️  No running containers found$(NC)"

# ============================================================================
# DEVELOPMENT WORKFLOW
# ============================================================================

.PHONY: dev-setup
dev-setup: install-dev-deps db-init ## Set up development environment
	@echo "$(BLUE)🔧 $(SERVICE_NAME) development environment setup complete$(NC)"
	@echo "$(GREEN)✅ Ready for development!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  make run              - Start service locally"
	@echo "  make test             - Run test suite"
	@echo "  make docker-run       - Start service in Docker"

.PHONY: ci
ci: lint test ## Run CI pipeline locally
	@echo "$(BLUE)🔄 Running CI pipeline...$(NC)"
	@echo "$(GREEN)✅ CI pipeline complete$(NC)"

# Default target
.DEFAULT_GOAL := help
