.PHONY: help preflight start stop restart status logs clean build test dashboard

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)         Ecosystem MCP - Service Management$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)Examples:$(NC)"
	@echo "  make preflight          # Run all preflight checks"
	@echo "  make start             # Start all services"
	@echo "  make status            # Check service status"
	@echo "  make logs              # View service logs"
	@echo ""

preflight: ## Run preflight checks before starting
	@echo "$(BLUE)Running preflight checks...$(NC)"
	@chmod +x preflight_check.sh
	@./preflight_check.sh

start: preflight ## Start all services (with preflight checks)
	@echo "$(GREEN)Starting services...$(NC)"
	@docker-compose up -d postgres redis ollama
	@echo "$(YELLOW)Waiting for dependencies to be healthy...$(NC)"
	@sleep 5
	@docker-compose ps
	@echo ""
	@echo "$(GREEN)✅ Core services started!$(NC)"
	@echo ""
	@echo "$(BLUE)Starting API service on host...$(NC)"
	@echo "  Run: make start-api"
	@echo ""
	@echo "$(BLUE)Or start dashboard:$(NC)"
	@echo "  Run: make dashboard"

start-all: start ## Start all services including API and dashboard
	@echo "$(BLUE)Starting API service...$(NC)"
	@python3 -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 &
	@sleep 3
	@echo "$(GREEN)✅ API service started on http://localhost:8000$(NC)"

start-api: ## Start API service on host (non-containerized)
	@echo "$(BLUE)Starting API service on host...$(NC)"
	@python3 -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload

start-api-bg: ## Start API service in background
	@echo "$(BLUE)Starting API service in background...$(NC)"
	@nohup python3 -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
	@echo $$! > .api.pid
	@echo "$(GREEN)✅ API service started (PID: $$(cat .api.pid))$(NC)"
	@echo "  Logs: tail -f logs/api.log"

stop-api: ## Stop API service running in background
	@if [ -f .api.pid ]; then \
		echo "$(YELLOW)Stopping API service...$(NC)"; \
		kill $$(cat .api.pid) 2>/dev/null || true; \
		rm .api.pid; \
		echo "$(GREEN)✅ API service stopped$(NC)"; \
	else \
		echo "$(YELLOW)API service is not running$(NC)"; \
	fi

dashboard: ## Start the dashboard container
	@echo "$(BLUE)Building and starting dashboard...$(NC)"
	@cd ../ecosystem-mcp-dashboard && docker build -t ecosystem-mcp-dashboard .
	@docker run -d --name ecosystem-mcp-dashboard \
		-p 8501:8501 \
		-e API_BASE_URL=http://host.docker.internal:8000 \
		--network ecosystem-mcp_ecosystem-mcp \
		ecosystem-mcp-dashboard
	@echo "$(GREEN)✅ Dashboard started at http://localhost:8501$(NC)"

stop: ## Stop all services
	@echo "$(YELLOW)Stopping services...$(NC)"
	@docker-compose down
	@make stop-api
	@echo "$(GREEN)✅ All services stopped$(NC)"

restart: stop start ## Restart all services

status: ## Check status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	@echo ""
	@docker-compose ps
	@echo ""
	@if [ -f .api.pid ]; then \
		if ps -p $$(cat .api.pid) > /dev/null 2>&1; then \
			echo "$(GREEN)✅ API Service: Running (PID: $$(cat .api.pid))$(NC)"; \
		else \
			echo "$(RED)❌ API Service: Not running (stale PID)$(NC)"; \
		fi; \
	else \
		echo "$(YELLOW)○ API Service: Not running$(NC)"; \
	fi
	@echo ""
	@if docker ps --filter "name=ecosystem-mcp-dashboard" --format "{{.Names}}" | grep -q dashboard; then \
		echo "$(GREEN)✅ Dashboard: Running at http://localhost:8501$(NC)"; \
	else \
		echo "$(YELLOW)○ Dashboard: Not running$(NC)"; \
	fi

logs: ## View logs from all services
	@docker-compose logs -f --tail=100

logs-api: ## View API logs
	@if [ -f logs/api.log ]; then \
		tail -f logs/api.log; \
	else \
		echo "$(YELLOW)No API logs found$(NC)"; \
	fi

logs-postgres: ## View PostgreSQL logs
	@docker-compose logs -f postgres

logs-redis: ## View Redis logs
	@docker-compose logs -f redis

logs-ollama: ## View Ollama logs
	@docker-compose logs -f ollama

health: ## Check health of all services
	@echo "$(BLUE)Health Checks:$(NC)"
	@echo ""
	@echo "PostgreSQL:"
	@docker exec ecosystem-mcp-postgres pg_isready -U ecosystem || echo "$(RED)Not healthy$(NC)"
	@echo ""
	@echo "Redis:"
	@docker exec ecosystem-mcp-redis redis-cli ping || echo "$(RED)Not healthy$(NC)"
	@echo ""
	@echo "API:"
	@curl -s http://localhost:8000/health | jq . || echo "$(RED)Not healthy$(NC)"

clean: stop ## Clean up containers and volumes
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@docker-compose down -v
	@docker system prune -f
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

build: ## Build all Docker images
	@echo "$(BLUE)Building images...$(NC)"
	@docker-compose build
	@echo "$(GREEN)✅ Images built$(NC)"

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@python3 -m pytest tests/ -v

test-dashboard: ## Run dashboard tests
	@echo "$(BLUE)Running dashboard tests...$(NC)"
	@cd ../ecosystem-mcp-dashboard && python3 -m pytest test_dashboard.py -v

install: ## Install Python dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@pip3 install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

dev: ## Start development environment
	@echo "$(BLUE)Starting development environment...$(NC)"
	@make start
	@sleep 5
	@make start-api

dev-stop: ## Stop development environment
	@make stop

shell: ## Open a shell in the API container
	@docker exec -it ecosystem-mcp-service /bin/bash

psql: ## Connect to PostgreSQL database
	@docker exec -it ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp

redis-cli: ## Connect to Redis CLI
	@docker exec -it ecosystem-mcp-redis redis-cli

urls: ## Show all service URLs
	@echo "$(BLUE)Service URLs:$(NC)"
	@echo ""
	@echo "  API:          http://localhost:8000"
	@echo "  API Docs:     http://localhost:8000/docs"
	@echo "  Dashboard:    http://localhost:8501"
	@echo "  PostgreSQL:   localhost:5432"
	@echo "  Redis:        localhost:6379"
	@echo "  Ollama:       http://localhost:11434"
	@echo ""

version: ## Show version information
	@echo "$(BLUE)Version Information:$(NC)"
	@echo ""
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$(docker-compose --version)"
	@echo "Python: $$(python3 --version)"
	@echo ""
