# =============================================================================
# frontend Service - Makefile
# =============================================================================
# Comprehensive build, test, and deployment automation for the frontend service
# =============================================================================

# Configuration - Update these values for your service
PYTHON ?= python3
SERVICE_NAME := frontend
SERVICE_PORT := 3000
DOCKER_IMAGE := hackathon/$(SERVICE_NAME)
DOCKER_TAG ?= latest
DOCKER_COMPOSE_FILE := ../../docker-compose.dev.yml
DOCKER_COMPOSE_PROFILE := core

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
	@echo "$(CYAN)🚀 frontend Service Commands$(NC)"
	@echo "====================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(BLUE)%-25s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  make run              - Start service locally"
	@echo "  make test             - Run test suite"
	@echo "  make docker-run       - Start service in Docker"
	@echo "  make docker-compose-up - Start with full ecosystem"

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

.PHONY: run-debug
run-debug: ## Run the service locally (debug mode)
	@echo "$(BLUE)🚀 Starting $(SERVICE_NAME) service in debug mode...$(NC)"
	export ENVIRONMENT=development && export DEBUG=true && $(PYTHON) main.py

# ============================================================================
# DOCKER COMMANDS
# ============================================================================

.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "$(BLUE)🐳 Building $(SERVICE_NAME) Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "$(GREEN)✅ Docker image built: $(DOCKER_IMAGE):$(DOCKER_TAG)$(NC)"

.PHONY: docker-run
docker-run: docker-build ## Run service in Docker container
	@echo "$(BLUE)🚀 Running $(SERVICE_NAME) in Docker container...$(NC)"
	docker run --rm \
		--name $(SERVICE_NAME)-dev \
		-p $(SERVICE_PORT):$(SERVICE_PORT) \
		-e ENVIRONMENT=development \
		-e SERVICE_PORT=$(SERVICE_PORT) \
		-e REDIS_HOST=host.docker.internal \
		-v $(PWD):/app \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

.PHONY: docker-run-detached
docker-run-detached: docker-build ## Run service in Docker container (detached)
	@echo "$(BLUE)🚀 Running $(SERVICE_NAME) in Docker container (detached)...$(NC)"
	docker run -d --rm \
		--name $(SERVICE_NAME)-dev \
		-p $(SERVICE_PORT):$(SERVICE_PORT) \
		-e ENVIRONMENT=development \
		-e SERVICE_PORT=$(SERVICE_PORT) \
		-e REDIS_HOST=host.docker.internal \
		-v $(PWD):/app \
		$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "$(GREEN)✅ Service started in background$(NC)"

.PHONY: docker-stop
docker-stop: ## Stop running Docker containers
	@echo "$(BLUE)🛑 Stopping $(SERVICE_NAME) Docker containers...$(NC)"
	docker stop $(SERVICE_NAME)-dev 2>/dev/null || true
	@echo "$(GREEN)✅ Docker containers stopped$(NC)"

.PHONY: docker-clean
docker-clean: ## Clean Docker images and containers
	@echo "$(BLUE)🧹 Cleaning Docker resources...$(NC)"
	docker stop $(SERVICE_NAME)-dev 2>/dev/null || true
	docker rm $(SERVICE_NAME)-dev 2>/dev/null || true
	docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) 2>/dev/null || true
	@echo "$(GREEN)✅ Docker resources cleaned$(NC)"

# ============================================================================
# DOCKER COMPOSE COMMANDS
# ============================================================================

.PHONY: docker-compose-up
docker-compose-up: ## Start service with docker-compose (full ecosystem)
	@echo "$(BLUE)🚀 Starting $(SERVICE_NAME) with docker-compose (ecosystem)...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) --profile $(DOCKER_COMPOSE_PROFILE) up -d $(SERVICE_NAME)
	@echo "$(GREEN)✅ Service started with docker-compose$(NC)"
	@echo "$(YELLOW)📊 Service available at: http://localhost:$(SERVICE_PORT)$(NC)"

.PHONY: docker-compose-up-logs
docker-compose-up-logs: ## Start service with docker-compose and show logs
	@echo "$(BLUE)🚀 Starting $(SERVICE_NAME) with docker-compose (with logs)...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) --profile $(DOCKER_COMPOSE_PROFILE) up $(SERVICE_NAME)

.PHONY: docker-compose-down
docker-compose-down: ## Stop service with docker-compose
	@echo "$(BLUE)🛑 Stopping $(SERVICE_NAME) with docker-compose...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) --profile $(DOCKER_COMPOSE_PROFILE) down $(SERVICE_NAME)
	@echo "$(GREEN)✅ Service stopped with docker-compose$(NC)"

.PHONY: docker-compose-logs
docker-compose-logs: ## Show docker-compose logs
	@echo "$(BLUE)📋 Showing $(SERVICE_NAME) docker-compose logs...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) --profile $(DOCKER_COMPOSE_PROFILE) logs -f $(SERVICE_NAME)

.PHONY: docker-compose-build
docker-compose-build: ## Build service with docker-compose
	@echo "$(BLUE)🐳 Building $(SERVICE_NAME) with docker-compose...$(NC)"
	docker-compose -f $(DOCKER_COMPOSE_FILE) --profile $(DOCKER_COMPOSE_PROFILE) build $(SERVICE_NAME)
	@echo "$(GREEN)✅ Service built with docker-compose$(NC)"

# ============================================================================
# TESTING COMMANDS
# ============================================================================

.PHONY: test
test: ## Run test suite
	@echo "$(BLUE)🧪 Running $(SERVICE_NAME) test suite...$(NC)"
	if [ -d "tests" ]; then \
		$(PYTHON) -m pytest tests/ -v --tb=short; \
	else \
		echo "$(YELLOW)⚠️  No tests directory found$(NC)"; \
	fi

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "$(BLUE)🧪 Running unit tests...$(NC)"
	if [ -d "tests/unit" ]; then \
		$(PYTHON) -m pytest tests/unit/ -v; \
	else \
		echo "$(YELLOW)⚠️  No unit tests found$(NC)"; \
	fi

.PHONY: test-integration
test-integration: ## Run integration tests only
	@echo "$(BLUE)🧪 Running integration tests...$(NC)"
	if [ -d "tests/integration" ]; then \
		$(PYTHON) -m pytest tests/integration/ -v; \
	else \
		echo "$(YELLOW)⚠️  No integration tests found$(NC)"; \
	fi

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)🧪 Running tests with coverage...$(NC)"
	if [ -d "tests" ]; then \
		$(PYTHON) -m pytest --cov=. --cov-report=html --cov-report=term tests/; \
		echo "$(GREEN)📊 Coverage report generated in htmlcov/$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  No tests directory found$(NC)"; \
	fi

.PHONY: test-watch
test-watch: ## Run tests in watch mode (requires pytest-watch)
	@echo "$(BLUE)👀 Running tests in watch mode...$(NC)"
	if command -v pytest-watch >/dev/null 2>&1; then \
		pytest-watch tests/; \
	else \
		echo "$(YELLOW)⚠️  pytest-watch not installed. Install with: pip install pytest-watch$(NC)"; \
		$(PYTHON) -m pytest tests/ -v; \
	fi

# ============================================================================
# HEALTH AND MONITORING
# ============================================================================

.PHONY: health-check
health-check: ## Check service health
	@echo "$(BLUE)🏥 Checking $(SERVICE_NAME) health...$(NC)"
	curl -f http://localhost:$(SERVICE_PORT)/health 2>/dev/null && echo "$(GREEN)✅ Service is healthy$(NC)" || echo "$(RED)❌ Service not healthy$(NC)"

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
	@curl -s -f http://localhost:$(SERVICE_PORT)/health > /dev/null && echo "✅ Service is healthy" || echo "❌ Service is not responding"
	@echo ""
	@echo "$(YELLOW)Docker Containers:$(NC)"
	@docker ps --filter name=$(SERVICE_NAME) --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "No running containers"
	@echo ""
	@echo "$(YELLOW)Docker Compose:$(NC)"
	@docker-compose -f $(DOCKER_COMPOSE_FILE) --profile $(DOCKER_COMPOSE_PROFILE) ps $(SERVICE_NAME) 2>/dev/null || echo "Not managed by docker-compose"

# ============================================================================
# DEVELOPMENT UTILITIES
# ============================================================================

.PHONY: clean
clean: ## Clean up generated files and caches
	@echo "$(BLUE)🧹 Cleaning up $(SERVICE_NAME)...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage coverage.xml
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

.PHONY: install-deps
install-deps: ## Install Python dependencies
	@echo "$(BLUE)📦 Installing $(SERVICE_NAME) dependencies...$(NC)"
	if [ -f "requirements.txt" ]; then \
		pip install -r requirements.txt; \
	else \
		echo "$(YELLOW)⚠️  No requirements.txt found$(NC)"; \
	fi
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

.PHONY: install-dev-deps
install-dev-deps: install-deps ## Install development dependencies
	@echo "$(BLUE)📦 Installing $(SERVICE_NAME) development dependencies...$(NC)"
	pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-xdist black isort flake8 mypy
	@echo "$(GREEN)✅ Development dependencies installed$(NC)"

.PHONY: lint
lint: ## Run code linting
	@echo "$(BLUE)🔍 Running code linting...$(NC)"
	if command -v black >/dev/null 2>&1; then \
		black --check . || echo "$(YELLOW)⚠️  Code formatting issues found$(NC)"; \
	fi
	if command -v isort >/dev/null 2>&1; then \
		isort --check-only . || echo "$(YELLOW)⚠️  Import sorting issues found$(NC)"; \
	fi
	if command -v flake8 >/dev/null 2>&1; then \
		flake8 . || echo "$(YELLOW)⚠️  Linting issues found$(NC)"; \
	fi
	@echo "$(GREEN)✅ Linting complete$(NC)"

.PHONY: format
format: ## Format code with black and isort
	@echo "$(BLUE)🎨 Formatting code...$(NC)"
	if command -v black >/dev/null 2>&1; then black .; fi
	if command -v isort >/dev/null 2>&1; then isort .; fi
	@echo "$(GREEN)✅ Code formatted$(NC)"

.PHONY: type-check
type-check: ## Run type checking with mypy
	@echo "$(BLUE)🔍 Running type checking...$(NC)"
	if command -v mypy >/dev/null 2>&1; then \
		mypy . || echo "$(YELLOW)⚠️  Type checking issues found$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  mypy not installed$(NC)"; \
	fi

# ============================================================================
# LOGS AND DEBUGGING
# ============================================================================

.PHONY: logs
logs: ## Show service logs
	@echo "$(BLUE)📋 Showing $(SERVICE_NAME) logs...$(NC)"
	docker logs $(SERVICE_NAME)-dev 2>/dev/null || docker-compose -f $(DOCKER_COMPOSE_FILE) --profile $(DOCKER_COMPOSE_PROFILE) logs $(SERVICE_NAME) || echo "$(YELLOW)⚠️  No logs available$(NC)"

.PHONY: logs-follow
logs-follow: ## Follow service logs
	@echo "$(BLUE)👀 Following $(SERVICE_NAME) logs...$(NC)"
	docker logs -f $(SERVICE_NAME)-dev 2>/dev/null || docker-compose -f $(DOCKER_COMPOSE_FILE) --profile $(DOCKER_COMPOSE_PROFILE) logs -f $(SERVICE_NAME) || echo "$(YELLOW)⚠️  No logs available$(NC)"

# ============================================================================
# DEVELOPMENT WORKFLOW
# ============================================================================

.PHONY: dev-setup
dev-setup: install-dev-deps ## Set up development environment
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


.PHONY: security-scan
security-scan: ## Run security scan on dependencies
	@echo "$(BLUE)🔒 Running security scan...$(NC)"
	@if command -v safety >/dev/null 2>&1; then 		safety check --full-report; 	else 		echo "$(YELLOW)⚠️  safety not installed. Install with: pip install safety$(NC)"; 	fi

.PHONY: audit-dependencies
audit-dependencies: ## Audit Python dependencies for vulnerabilities
	@echo "$(BLUE)📦 Auditing dependencies...$(NC)"
	@if command -v pip-audit >/dev/null 2>&1; then 		pip-audit; 	else 		echo "$(YELLOW)⚠️  pip-audit not installed. Install with: pip install pip-audit$(NC)"; 	fi

.PHONY: lint-security
lint-security: ## Run security-focused linting
	@echo "$(BLUE)🛡️  Running security linting...$(NC)"
	@if command -v bandit >/dev/null 2>&1; then 		bandit -r . -f txt; 	else 		echo "$(YELLOW)⚠️  bandit not installed. Install with: pip install bandit$(NC)"; 	fi

.PHONY: security-check
security-check: security-scan audit-dependencies lint-security ## Run all security checks
	@echo "$(GREEN)✅ Security checks completed$(NC)"

.PHONY: ci-security
ci-security: security-check test ## CI pipeline with security checks
	@echo "$(BLUE)🔄 Running CI with security...$(NC)"
	@echo "$(GREEN)✅ CI security pipeline complete$(NC)"
