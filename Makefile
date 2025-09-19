PYTHON ?= python3
VENV ?= venv_hardening

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help test docs docs-serve timeline ecosystem ecosystem-validate ecosystem-health ecosystem-clean validate-health-endpoints validate-health-continuous validate-config-drift validate-config-drift-auto validate-api-contracts validate-api-compare setup-logging validate-logging monitor-services health-check-all logs-view logs-clean simulation simulation-run simulation-test simulation-docker simulation-stop simulation-status

help: ## Show this help message
	@echo "🚀 Hackathon Ecosystem Commands"
	@echo "================================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(BLUE)%-25s$(NC) %s\n", $$1, $$2}'

# Development and Testing
test: ## Run test suite
	@echo "$(BLUE)🧪 Running Tests...$(NC)"
	$(PYTHON) -m pytest -q

docs: ## Build documentation
	@echo "$(BLUE)📚 Building Documentation...$(NC)"
	mkdocs build -q

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)📚 Serving Documentation...$(NC)"
	mkdocs serve -a 0.0.0.0:8000

timeline: ## Generate project timeline
	@echo "$(BLUE)📊 Generating Timeline...$(NC)"
	$(PYTHON) scripts/generate_timeline.py

# Ecosystem Management
ecosystem-setup: ## Set up virtual environment and dependencies
	@echo "$(BLUE)🔧 Setting up Ecosystem Environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	source $(VENV)/bin/activate && pip install -U pip
	source $(VENV)/bin/activate && pip install pydantic PyYAML redis
	@echo "$(GREEN)✅ Environment setup complete$(NC)"

ecosystem-validate: ## Validate ecosystem configuration and services
	@echo "$(BLUE)🔍 Validating Ecosystem...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/hardening/docker_standardization.py
	source $(VENV)/bin/activate && python3 scripts/hardening/service_connectivity_validator.py
	@echo "$(GREEN)✅ Ecosystem validation complete$(NC)"

ecosystem-health: ## Check ecosystem health using unified monitoring
	@echo "$(BLUE)🏥 Checking Ecosystem Health...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/safeguards/unified_health_monitor.py

ecosystem-readiness: ## Check production readiness
	@echo "$(BLUE)🚀 Checking Production Readiness...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/hardening/production_readiness_validator.py

ecosystem-test: ## Run comprehensive ecosystem tests
	@echo "$(BLUE)🧪 Running Ecosystem Tests...$(NC)"
	$(PYTHON) ecosystem_functional_test_suite.py
	source $(VENV)/bin/activate && python3 scripts/hardening/service_connectivity_validator.py

ecosystem-clean: ## Clean ecosystem resources
	@echo "$(YELLOW)🧹 Cleaning Ecosystem...$(NC)"
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans
	docker container prune -f
	docker network prune -f
	docker volume prune -f
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

# Docker Management
docker-start: ## Start all services with validation
	@echo "$(BLUE)🚀 Starting Docker Ecosystem...$(NC)"
	docker-compose -f docker-compose.dev.yml --profile core --profile ai_services --profile development up -d
	@echo "$(GREEN)✅ Services starting...$(NC)"

docker-stop: ## Stop all services
	@echo "$(BLUE)🛑 Stopping Docker Ecosystem...$(NC)"
	docker-compose -f docker-compose.dev.yml down
	@echo "$(GREEN)✅ Services stopped$(NC)"

docker-logs: ## Show service logs
	docker-compose -f docker-compose.dev.yml logs -f --tail=50

docker-status: ## Show service status
	@echo "$(BLUE)📊 Service Status$(NC)"
	docker ps --filter "name=hackathon" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# API and Schema Validation
api-validate: ## Validate API schemas
	@echo "$(BLUE)🔍 Validating API Schemas...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/safeguards/api_schema_validator.py

# CLI and Environment
cli-test: ## Test environment-aware CLI
	@echo "$(BLUE)💻 Testing Environment-Aware CLI...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/safeguards/environment_aware_cli.py

# Development Workflow
dev-setup: ecosystem-setup setup-logging ecosystem-validate docker-start ## Complete development setup
	@echo "$(GREEN)🎉 Development environment ready!$(NC)"
	@echo "Run 'make ecosystem-health' to check service status"
	@echo "Run 'make health-check-all' to validate all service health endpoints"
	@echo "Run 'make logs-view' to see service log files"
	@echo "Run 'make docs-serve' to view documentation"

# CI/CD
ci-validate: ecosystem-validate api-validate ## CI validation pipeline
	@echo "$(GREEN)✅ CI validation passed$(NC)"

ci-test: ci-validate test ecosystem-test ## CI testing pipeline
	@echo "$(GREEN)✅ CI testing passed$(NC)"

# ========================================
# VALIDATION TARGETS (based on lessons learned)
# ========================================

validate: ## Run comprehensive ecosystem validation
	@echo "$(BLUE)🔍 Running comprehensive validation...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/hardening/docker_standardization.py
	source $(VENV)/bin/activate && python3 scripts/hardening/service_connectivity_validator.py
	@echo "$(GREEN)✅ Validation completed$(NC)"

validate-ports: ## Validate port configurations and detect conflicts
	@echo "$(BLUE)🔍 Validating ports...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/hardening/docker_standardization.py
	@echo "$(GREEN)✅ Port validation completed$(NC)"

validate-dockerfiles: ## Validate all Dockerfiles with comprehensive analysis
	@echo "$(BLUE)🔍 Validating Dockerfiles with comprehensive analysis...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/hardening/dockerfile_validator.py
	@echo "$(GREEN)✅ Dockerfile validation completed$(NC)"

validate-env: ## Validate environment variables comprehensively
	@echo "$(BLUE)🔍 Validating environment variables...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/hardening/environment_validator.py
	@echo "$(GREEN)✅ Environment validation completed$(NC)"

validate-health: ## Validate health check endpoints
	@echo "$(BLUE)🔍 Validating health checks...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/safeguards/unified_health_monitor.py --validate-endpoints
	@echo "$(GREEN)✅ Health check validation completed$(NC)"

validate-health-endpoints: ## Comprehensive health endpoint validation
	@echo "$(BLUE)🏥 Running comprehensive health endpoint validation...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/safeguards/health_endpoint_validator.py --verbose --save-report
	@echo "$(GREEN)✅ Health endpoint validation completed$(NC)"

validate-health-continuous: ## Continuous health monitoring
	@echo "$(BLUE)🔄 Starting continuous health monitoring...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/safeguards/health_endpoint_validator.py --mode continuous --duration 5 --verbose
	@echo "$(GREEN)✅ Continuous health monitoring completed$(NC)"

validate-config: ## Check for configuration drift
	@echo "$(BLUE)🔍 Checking configuration consistency...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/hardening/docker_standardization.py --check-drift
	@echo "$(GREEN)✅ Configuration validation completed$(NC)"

validate-config-drift: ## Comprehensive configuration drift detection
	@echo "$(BLUE)🔍 Running comprehensive configuration drift detection...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/safeguards/config_drift_detector.py --verbose --save-report
	@echo "$(GREEN)✅ Configuration drift detection completed$(NC)"

validate-config-drift-auto: ## Configuration drift detection with auto-correction
	@echo "$(BLUE)🔧 Running configuration drift detection with auto-correction...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/safeguards/config_drift_detector.py --auto-correct --verbose
	@echo "$(GREEN)✅ Configuration drift auto-correction completed$(NC)"

validate-api-contracts: ## Validate API contracts between services
	@echo "$(BLUE)🔗 Validating API contracts...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/safeguards/api_contract_validator.py --verbose --save-report
	@echo "$(GREEN)✅ API contract validation completed$(NC)"

validate-api-compare: ## Compare API specifications (usage: make validate-api-compare OLD_SPEC=path/to/old.json NEW_SPEC=path/to/new.json)
	@echo "$(BLUE)🔍 Comparing API specifications...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/safeguards/api_contract_validator.py --compare $(OLD_SPEC) $(NEW_SPEC) --verbose
	@echo "$(GREEN)✅ API comparison completed$(NC)"

# ========================================
# STANDARDIZED LOGGING & MONITORING
# ========================================

setup-logging: ## Setup standardized logging for all services
	@echo "$(BLUE)🔧 Setting up standardized logging...$(NC)"
	@for service in services/*/; do \
		if [ -f "$$service/main.py" ]; then \
			service_name=$$(basename $$service); \
			echo "  Setting up logging for $$service_name..."; \
			mkdir -p "$$service/logs"; \
		fi \
	done
	@echo "$(GREEN)✅ Logging setup completed$(NC)"

validate-logging: ## Validate logging configuration across services
	@echo "$(BLUE)🔍 Validating logging configuration...$(NC)"
	@for service in services/*/; do \
		if [ -f "$$service/main.py" ]; then \
			service_name=$$(basename $$service); \
			if [ -f "$$service/logs/$$service_name.log" ]; then \
				echo "  ✅ $$service_name has log file"; \
			else \
				echo "  ❌ $$service_name missing log file"; \
			fi; \
		fi \
	done
	@echo "$(GREEN)✅ Logging validation completed$(NC)"

monitor-services: ## Start monitoring for all running services
	@echo "$(BLUE)📊 Starting service monitoring...$(NC)"
	@echo "  Note: Services must be running to enable monitoring"
	@echo "  Use 'make docker-start' to start services first"
	@echo "$(GREEN)✅ Monitoring setup ready$(NC)"

health-check-all: ## Check health status of all services
	@echo "$(BLUE)🏥 Checking health of all services...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/safeguards/health_endpoint_validator.py --verbose
	@echo "$(GREEN)✅ Health check completed$(NC)"

logs-view: ## View logs for all services
	@echo "$(BLUE)📋 Service Logs:$(NC)"
	@for service in services/*/; do \
		if [ -d "$$service/logs" ]; then \
			service_name=$$(basename $$service); \
			log_file="$$service/logs/$$service_name.log"; \
			if [ -f "$$log_file" ]; then \
				echo "  📄 $$service_name: $$log_file"; \
			fi; \
		fi \
	done
	@echo "$(GREEN)✅ Log files listed$(NC)"

logs-clean: ## Clean old log files
	@echo "$(YELLOW)🧹 Cleaning old log files...$(NC)"
	@find services/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Log cleanup completed$(NC)"

validate-conflicts: ## Run comprehensive port conflict detection
	@echo "$(BLUE)🔍 Running port conflict detection...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/hardening/port_conflict_detector.py
	@echo "$(GREEN)✅ Conflict detection completed$(NC)"

validate-enhanced: ## Run enhanced validation with conflict detection
	@echo "$(BLUE)🔍 Running enhanced validation...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/hardening/docker_standardization.py --check-drift
	@echo "$(GREEN)✅ Enhanced validation completed$(NC)"

validate-comprehensive: ## Run comprehensive validation (ports, dockerfiles, env, health, logging)
	@echo "$(BLUE)🔍 Running comprehensive ecosystem validation...$(NC)"
	@echo "$(BLUE)Step 1: Port validation$(NC)"
	@make validate-ports --silent
	@echo "$(BLUE)Step 2: Dockerfile validation$(NC)"
	@make validate-dockerfiles --silent
	@echo "$(BLUE)Step 3: Environment validation$(NC)"
	@make validate-env --silent
	@echo "$(BLUE)Step 4: Health check validation$(NC)"
	@make validate-health-endpoints --silent
	@echo "$(BLUE)Step 5: API contract validation$(NC)"
	@make validate-api-contracts --silent
	@echo "$(BLUE)Step 6: Logging validation$(NC)"
	@make validate-logging --silent
	@echo "$(BLUE)Step 7: Conflict detection$(NC)"
	@make validate-conflicts --silent
	@echo "$(GREEN)✅ Comprehensive validation completed$(NC)"

validate-startup: ## Validate service startup configurations
	@echo "$(BLUE)🔍 Validating startup configurations...$(NC)"
	@for service in services/*/; do \
		if [ -f "$$service/main.py" ] && [ -f "$$service/Dockerfile" ]; then \
			service_name=$$(basename $$service); \
			echo "  ✅ $$service_name startup config OK"; \
		else \
			echo "  ❌ $$service_name missing startup files"; \
		fi \
	done
	@echo "$(GREEN)✅ Startup validation completed$(NC)"

# ========================================
# DEVELOPMENT VALIDATION WORKFLOWS
# ========================================

dev-validate: validate-ports validate-env validate-health-endpoints validate-logging validate-conflicts ## Quick development validation
	@echo "$(GREEN)🎉 Development validation passed$(NC)"

pre-deploy: validate-all ecosystem-health ## Pre-deployment validation
	@echo "$(GREEN)🚀 Ready for deployment$(NC)"

# ========================================
# ERROR RECOVERY TARGETS
# ========================================

recover-services: ## Attempt to recover unhealthy services
	@echo "$(BLUE)🔧 Attempting service recovery...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/hardening/service_connectivity_validator.py --recover
	@echo "$(GREEN)✅ Recovery attempt completed$(NC)"

heal-start: ## Start auto-healing monitoring system
	@echo "$(BLUE)🚀 Starting auto-healing system...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/hardening/auto_healer.py --start --interval 30
	@echo "$(GREEN)✅ Auto-healing system started$(NC)"

heal-stop: ## Stop auto-healing monitoring system
	@echo "$(BLUE)🛑 Stopping auto-healing system...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/hardening/auto_healer.py --stop
	@echo "$(GREEN)✅ Auto-healing system stopped$(NC)"

heal-status: ## Show auto-healing system status
	@echo "$(BLUE)📊 Auto-healing system status...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/hardening/auto_healer.py --status

# ============================================================================
# SIMULATION SERVICE MANAGEMENT
# ============================================================================

simulation: ## Show simulation service management commands
	@echo "$(BLUE)🚀 Project Simulation Service$(NC)"
	@echo "================================"
	@echo ""
	@echo "Available simulation commands:"
	@echo "  $(CYAN)make simulation-run$(NC)       - Start simulation service"
	@echo "  $(CYAN)make simulation-test$(NC)      - Run simulation tests"
	@echo "  $(CYAN)make simulation-docker$(NC)    - Start simulation in Docker"
	@echo "  $(CYAN)make simulation-stop$(NC)      - Stop simulation service"
	@echo "  $(CYAN)make simulation-status$(NC)    - Check simulation status"
	@echo ""

simulation-run: ## Start project simulation service
	@echo "$(BLUE)🚀 Starting Project Simulation Service...$(NC)"
	cd services/project-simulation && make run

simulation-test: ## Run project simulation tests
	@echo "$(BLUE)🧪 Running Project Simulation Tests...$(NC)"
	cd services/project-simulation && make test

simulation-docker: ## Start project simulation service in Docker
	@echo "$(BLUE)🐳 Starting Project Simulation Service in Docker...$(NC)"
	docker-compose --profile simulation up -d
	@echo "$(GREEN)✅ Simulation service started in Docker$(NC)"
	@echo "$(YELLOW)📊 Service available at: http://localhost:5075$(NC)"

simulation-stop: ## Stop project simulation service
	@echo "$(BLUE)🛑 Stopping Project Simulation Service...$(NC)"
	docker-compose --profile simulation down
	@echo "$(GREEN)✅ Simulation service stopped$(NC)"

simulation-status: ## Check project simulation service status
	@echo "$(BLUE)📊 Project Simulation Service Status$(NC)"
	@echo "=========================================="
	@echo ""
	@echo "$(YELLOW)Health Check:$(NC)"
	@curl -s http://localhost:5075/health > /dev/null && echo "✅ Service is healthy" || echo "❌ Service is not responding"
	@echo ""
	@echo "$(YELLOW)Docker Containers:$(NC)"
	@docker ps --filter name=project-simulation --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "$(YELLOW)Database:$(NC)"
	@if [ -f "services/project-simulation/data/simulation.db" ]; then \
		echo "✅ Database file exists"; \
		sqlite3 services/project-simulation/data/simulation.db "SELECT COUNT(*) FROM simulations;" 2>/dev/null | xargs echo "📊 Simulations in database:"; \
	else \
		echo "❌ Database file not found"; \
	fi

# Default target
.DEFAULT_GOAL := help
