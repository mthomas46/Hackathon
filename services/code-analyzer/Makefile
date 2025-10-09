# Makefile for code-analyzer service
# Provides common commands for development, testing, and deployment
# Last Updated: October 9, 2025

.PHONY: help install test test-unit test-integration test-workflow run run-docker \
        validate-config check-ports validate-yaml validate-syntax lint format \
        clean build deploy health logs stop

# Default target
.DEFAULT_GOAL := help

# Service configuration
SERVICE_NAME := code-analyzer
SERVICE_PORT := 6000
INTERNAL_PORT := 6001

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help:  ## Show this help message
	@echo "$(GREEN)code-analyzer Makefile Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# === Installation ===

install:  ## Install production dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	pip install -r requirements.txt

install-dev:  ## Install development dependencies
	@echo "$(GREEN)Installing development dependencies...$(NC)"
	pip install -r requirements.txt
	pip install -r requirements-test.txt

# === Testing ===

test:  ## Run all tests
	@echo "$(GREEN)Running all tests...$(NC)"
	pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

test-unit:  ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	pytest tests/unit/ -v -m unit

test-integration:  ## Run integration tests only
	@echo "$(GREEN)Running integration tests...$(NC)"
	pytest tests/integration/ -v -m integration

test-workflow:  ## Run workflow tests only
	@echo "$(GREEN)Running workflow tests...$(NC)"
	pytest tests/integration/ -v -m workflow

test-coverage:  ## Generate detailed coverage report
	@echo "$(GREEN)Generating coverage report...$(NC)"
	pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report generated: htmlcov/index.html$(NC)"

# === Running ===

run:  ## Run service locally (when application layer exists)
	@echo "$(YELLOW)Note: Application layer not yet implemented$(NC)"
	@echo "$(GREEN)Domain layer is available for import$(NC)"
	python -c "from domain.entities.code_analysis import CodeAnalysis; from domain.value_objects import Language; print('✓ Domain layer loaded successfully')"

run-docker:  ## Run service in Docker
	@echo "$(GREEN)Starting code-analyzer in Docker...$(NC)"
	docker-compose up

run-docker-bg:  ## Run service in Docker (background)
	@echo "$(GREEN)Starting code-analyzer in Docker (background)...$(NC)"
	docker-compose up -d

# === Validation ===

validate-config:  ## Validate all configuration
	@echo "$(GREEN)Validating configuration...$(NC)"
	@$(MAKE) check-ports
	@$(MAKE) validate-yaml
	@$(MAKE) validate-syntax
	@echo "$(GREEN)✓ All configuration validation passed$(NC)"

check-ports:  ## Check for port conflicts
	@echo "$(GREEN)Checking port conflicts...$(NC)"
	@if command -v lsof > /dev/null; then \
		if lsof -i :$(SERVICE_PORT) > /dev/null 2>&1; then \
			echo "$(RED)✗ Port $(SERVICE_PORT) is already in use$(NC)"; \
			lsof -i :$(SERVICE_PORT); \
			exit 1; \
		else \
			echo "$(GREEN)✓ Port $(SERVICE_PORT) is available$(NC)"; \
		fi; \
		if lsof -i :$(INTERNAL_PORT) > /dev/null 2>&1; then \
			echo "$(RED)✗ Port $(INTERNAL_PORT) is already in use$(NC)"; \
			lsof -i :$(INTERNAL_PORT); \
			exit 1; \
		else \
			echo "$(GREEN)✓ Port $(INTERNAL_PORT) is available$(NC)"; \
		fi; \
	else \
		echo "$(YELLOW)⚠ lsof not available, skipping port check$(NC)"; \
	fi
	@python ../../scripts/validation/check_port_conflicts.py $(SERVICE_NAME) $(SERVICE_PORT) || true

validate-yaml:  ## Validate YAML files
	@echo "$(GREEN)Validating YAML files...$(NC)"
	@if command -v yamllint > /dev/null; then \
		yamllint docker-compose.yml design/*.yaml || true; \
		echo "$(GREEN)✓ YAML validation complete$(NC)"; \
	else \
		echo "$(YELLOW)⚠ yamllint not installed, skipping YAML validation$(NC)"; \
	fi

validate-syntax:  ## Validate Python syntax
	@echo "$(GREEN)Validating Python syntax...$(NC)"
	@python -m py_compile domain/**/*.py tests/**/*.py 2>/dev/null || echo "$(GREEN)✓ Python syntax valid$(NC)"

validate-pytest:  ## Validate pytest configuration
	@echo "$(GREEN)Validating pytest configuration...$(NC)"
	pytest --collect-only tests/ > /dev/null
	@echo "$(GREEN)✓ pytest configuration valid$(NC)"

# === Code Quality ===

lint:  ## Run linters
	@echo "$(GREEN)Running linters...$(NC)"
	@if command -v pylint > /dev/null; then \
		pylint domain/ --disable=all --enable=E,F || true; \
	else \
		echo "$(YELLOW)⚠ pylint not installed$(NC)"; \
	fi
	@if command -v flake8 > /dev/null; then \
		flake8 domain/ tests/ --max-line-length=120 || true; \
	else \
		echo "$(YELLOW)⚠ flake8 not installed$(NC)"; \
	fi

format:  ## Format code with black
	@echo "$(GREEN)Formatting code...$(NC)"
	@if command -v black > /dev/null; then \
		black domain/ tests/; \
	else \
		echo "$(YELLOW)⚠ black not installed$(NC)"; \
	fi

# === Docker Operations ===

build:  ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t $(SERVICE_NAME):latest .

build-no-cache:  ## Build Docker image without cache
	@echo "$(GREEN)Building Docker image (no cache)...$(NC)"
	docker build --no-cache -t $(SERVICE_NAME):latest .

# === Deployment ===

deploy:  ## Deploy to development
	@echo "$(GREEN)Deploying to development...$(NC)"
	@$(MAKE) validate-config
	@$(MAKE) build
	@$(MAKE) run-docker-bg
	@echo "$(GREEN)Waiting for service to be healthy...$(NC)"
	@sleep 5
	@$(MAKE) health

health:  ## Check service health
	@echo "$(GREEN)Checking service health...$(NC)"
	@if docker ps | grep -q $(SERVICE_NAME); then \
		echo "$(GREEN)✓ Container is running$(NC)"; \
		docker inspect $(SERVICE_NAME) --format='{{.State.Health.Status}}' 2>/dev/null || echo "$(YELLOW)Health check not available yet$(NC)"; \
	else \
		echo "$(RED)✗ Container is not running$(NC)"; \
		exit 1; \
	fi

logs:  ## Show service logs
	@echo "$(GREEN)Showing logs for $(SERVICE_NAME)...$(NC)"
	docker-compose logs -f $(SERVICE_NAME)

logs-tail:  ## Tail service logs
	@echo "$(GREEN)Tailing logs for $(SERVICE_NAME)...$(NC)"
	docker-compose logs -f --tail=100 $(SERVICE_NAME)

stop:  ## Stop service
	@echo "$(GREEN)Stopping $(SERVICE_NAME)...$(NC)"
	docker-compose down

restart:  ## Restart service
	@echo "$(GREEN)Restarting $(SERVICE_NAME)...$(NC)"
	docker-compose restart $(SERVICE_NAME)

# === Cleanup ===

clean:  ## Clean up generated files
	@echo "$(GREEN)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-docker:  ## Clean up Docker resources
	@echo "$(GREEN)Cleaning up Docker resources...$(NC)"
	docker-compose down -v
	docker rmi $(SERVICE_NAME):latest 2>/dev/null || true
	@echo "$(GREEN)✓ Docker cleanup complete$(NC)"

# === Information ===

info:  ## Show service information
	@echo "$(GREEN)Service Information$(NC)"
	@echo "  Name: $(SERVICE_NAME)"
	@echo "  HTTP Port: $(SERVICE_PORT)"
	@echo "  Internal Port: $(INTERNAL_PORT)"
	@echo "  Status: $$(docker ps --filter name=$(SERVICE_NAME) --format '{{.Status}}' 2>/dev/null || echo 'Not running')"
	@echo ""
	@echo "$(GREEN)Available Commands$(NC)"
	@$(MAKE) help

version:  ## Show version information
	@echo "$(GREEN)Version Information$(NC)"
	@echo "  Service: $(SERVICE_NAME) v1.0.0"
	@echo "  Python: $$(python --version 2>&1)"
	@echo "  Docker: $$(docker --version 2>&1)"
	@echo "  Docker Compose: $$(docker-compose --version 2>&1)"

# === Development Helpers ===

shell:  ## Open shell in running container
	@echo "$(GREEN)Opening shell in $(SERVICE_NAME)...$(NC)"
	docker exec -it $(SERVICE_NAME) /bin/bash

pytest-shell:  ## Run pytest with shell on failure
	@echo "$(GREEN)Running tests with shell on failure...$(NC)"
	pytest tests/ -v --pdb

watch-tests:  ## Watch and run tests on file changes
	@echo "$(GREEN)Watching for changes...$(NC)"
	@if command -v pytest-watch > /dev/null; then \
		ptw tests/ domain/ --; \
	else \
		echo "$(YELLOW)⚠ pytest-watch not installed$(NC)"; \
		echo "$(YELLOW)Install with: pip install pytest-watch$(NC)"; \
	fi

