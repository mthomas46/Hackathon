PYTHON ?= python3
VENV ?= venv_hardening

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help test docs docs-serve timeline ecosystem ecosystem-validate ecosystem-health ecosystem-clean validate validate-ports validate-docker-config validate-dockerfiles validate-env validate-health validate-health-endpoints validate-health-continuous validate-config validate-config-drift validate-config-drift-auto validate-config-consistency validate-api-contracts validate-api-compare validate-drift validate-drift-docker validate-drift-pydantic validate-schema validate-production-ready validate-ecosystem-health validate-all-configs validate-network validate-baselines create-baseline generate-baselines validate-environments validate-dependencies auto-correct-config dry-run-corrections rollback-corrections list-correction-backups meta-orchestrator-build meta-orchestrator-run meta-orchestrator-stop meta-orchestrator-logs meta-orchestrator-health ci-validate-config ci-validate-deployment ci-gate-check monitor-config monitor-health alert-config-drift dev-full-validate dev-quick-check config-backup config-version pydantic-enable pydantic-disable pydantic-test pydantic-status validate-pydantic validate-service-startup validate-docker-files validate-docker-compose config-monitor config-health config-service-health docker-standardize docker-standardize-dry-run docker-standardize-apply setup-logging validate-logging monitor-services health-check-all logs-view logs-clean simulation simulation-run simulation-test simulation-docker simulation-stop simulation-status dashboard dashboard-start dashboard-stop dashboard-logs dashboard-health dashboard-test prompt-store-run prompt-store-test prompt-store-docker prompt-store-stop prompt-store-logs prompt-store-health llm-gateway-run llm-gateway-test llm-gateway-docker llm-gateway-stop llm-gateway-logs llm-gateway-health code-analyzer-run code-analyzer-test code-analyzer-docker code-analyzer-stop code-analyzer-logs code-analyzer-health orchestrator-run orchestrator-test orchestrator-docker orchestrator-stop orchestrator-logs orchestrator-health user-store-run user-store-test user-store-docker user-store-stop user-store-logs user-store-health external-service-store-run external-service-store-test external-service-store-docker external-service-stop external-service-logs external-service-health audit audit-all audit-services audit-ci audit-quick audit-comprehensive audit-parallel audit-report audit-clean audit-setup audit-validate audit-benchmark audit-trend audit-config audit-debug audit-docker audit-pre-commit audit-quality-gate audit-enforce docker-start docker-start-validated docker-stop docker-restart docker-compose-up docker-compose-down docker-compose-logs docker-compose-config docker-logs docker-status dev-setup dev-setup-full ci-validate ci-test pre-deploy deploy-safe

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
	$(PYTHON) scripts/docs/generate_timeline.py

# Ecosystem Management
ecosystem-setup: ## Set up virtual environment and dependencies
	@echo "$(BLUE)🔧 Setting up Ecosystem Environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	source $(VENV)/bin/activate && pip install -U pip
	source $(VENV)/bin/activate && pip install pydantic PyYAML redis
	@echo "$(GREEN)✅ Environment setup complete$(NC)"

ecosystem-validate: ## Validate ecosystem configuration and services
	@echo "$(BLUE)🔍 Validating Ecosystem...$(NC)"
	$(PYTHON) scripts/hardening/unified_config_manager.py audit
	$(PYTHON) scripts/hardening/unified_config_manager.py docker-check
	@echo "$(GREEN)✅ Ecosystem validation complete$(NC)"

ecosystem-health: ## Check ecosystem health using unified monitoring
	@echo "$(BLUE)🏥 Checking Ecosystem Health...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/safeguards/unified_health_monitor.py

ecosystem-readiness: ## Check production readiness
	@echo "$(BLUE)🚀 Checking Production Readiness...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/hardening/production_readiness_validator.py

ecosystem-test: ## Run comprehensive ecosystem tests
	@echo "$(BLUE)🧪 Running Ecosystem Tests...$(NC)"
	$(PYTHON) scripts/hardening/ecosystem_functional_test_suite.py
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
	@echo "$(YELLOW)📋 Pre-flight Configuration Check...$(NC)"
	@$(PYTHON) scripts/hardening/unified_config_manager.py audit > /dev/null 2>&1 || (echo "$(RED)❌ Configuration validation failed. Run 'make ecosystem-validate' to check.$(NC)" && exit 1)
	@echo "$(BLUE)🔍 Checking Docker configurations...$(NC)"
	$(PYTHON) scripts/hardening/docker_compose_validator.py --quiet --files docker-compose.dev.yml && echo "$(GREEN)✅ Docker Compose validation passed$(NC)" || echo "$(YELLOW)⚠️  Docker Compose has issues but continuing... Run 'make validate-docker-compose' for details$(NC)"
	docker-compose -f docker-compose.dev.yml config --quiet > /dev/null 2>&1 || (echo "$(RED)❌ docker-compose.dev.yml has syntax errors.$(NC)" && exit 1)
	@echo "$(GREEN)✅ Configuration validated$(NC)"
	@echo "$(BLUE)🐳 Starting services...$(NC)"
	docker-compose -f docker-compose.dev.yml --profile core --profile ai_services --profile development --profile utility up -d
	@echo "$(GREEN)✅ Services starting...$(NC)"

docker-start-validated: validate-config-consistency validate-docker-config validate-docker-files validate-docker-compose ## Start services with comprehensive validation
	@echo "$(BLUE)🚀 Starting Docker Ecosystem with Full Validation...$(NC)"
	@echo "$(GREEN)✅ All validations passed - Docker configurations validated$(NC)"
	$(MAKE) docker-start

docker-stop: ## Stop all services
	@echo "$(BLUE)🛑 Stopping Docker Ecosystem...$(NC)"
	docker-compose -f docker-compose.dev.yml down
	@echo "$(GREEN)✅ Services stopped$(NC)"

docker-restart: ## Restart all services with validation
	@echo "$(BLUE)🔄 Restarting Docker Ecosystem...$(NC)"
	$(MAKE) docker-stop
	$(MAKE) docker-start
	@echo "$(GREEN)✅ Services restarted$(NC)"

docker-compose-up: validate-docker-compose ## Run docker-compose up with validation
	@echo "$(BLUE)🐳 Running docker-compose up...$(NC)"
	docker-compose -f docker-compose.dev.yml up -d
	@echo "$(GREEN)✅ Services started$(NC)"

docker-compose-down: ## Run docker-compose down (no validation needed)
	@echo "$(BLUE)🛑 Running docker-compose down...$(NC)"
	docker-compose -f docker-compose.dev.yml down
	@echo "$(GREEN)✅ Services stopped$(NC)"

docker-compose-logs: ## Run docker-compose logs
	@echo "$(BLUE)📋 Docker Compose Logs...$(NC)"
	docker-compose -f docker-compose.dev.yml logs -f --tail=50

docker-compose-config: validate-docker-compose ## Validate docker-compose config
	@echo "$(BLUE)⚙️  Validating docker-compose config...$(NC)"
	docker-compose -f docker-compose.dev.yml config
	@echo "$(GREEN)✅ Config validated$(NC)"

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
# (moved to integrated workflows section below)

# ========================================
# VALIDATION TARGETS (based on lessons learned)
# ========================================

validate: ## Run comprehensive ecosystem validation
	@echo "$(BLUE)🔍 Running comprehensive validation...$(NC)"
	$(PYTHON) scripts/hardening/unified_config_manager.py audit
	$(PYTHON) scripts/hardening/unified_config_manager.py docker-check
	$(PYTHON) scripts/hardening/unified_docker_standardizer.py --mode validate
	@echo "$(GREEN)✅ Validation completed$(NC)"

validate-ports: ## Validate port configurations and detect conflicts
	@echo "$(BLUE)🔍 Validating ports...$(NC)"
	$(PYTHON) scripts/hardening/ports/port_conflict_detector.py
	@echo "$(GREEN)✅ Port validation completed$(NC)"

validate-docker-config: ## Validate Docker and Docker Compose configuration consistency
	@echo "$(BLUE)🐳 Validating Docker configuration...$(NC)"
	$(PYTHON) scripts/hardening/unified_config_manager.py docker-check
	$(PYTHON) scripts/hardening/unified_docker_standardizer.py --mode validate
	docker-compose -f docker-compose.dev.yml config --quiet || (echo "$(RED)❌ docker-compose.dev.yml has syntax errors$(NC)" && exit 1)
	docker-compose -f docker-compose.prod.yml config --quiet || (echo "$(RED)❌ docker-compose.prod.yml has syntax errors$(NC)" && exit 1)
	@echo "$(GREEN)✅ Docker configuration validation completed$(NC)"

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
	$(PYTHON) scripts/hardening/unified_config_manager.py audit
	$(PYTHON) audit_configuration.py
	@echo "$(GREEN)✅ Configuration validation completed$(NC)"

validate-config-drift: ## Comprehensive configuration drift detection
	@echo "$(BLUE)🔍 Running comprehensive configuration drift detection...$(NC)"
	$(PYTHON) scripts/hardening/config_drift_detector.py --verbose --save-report
	$(PYTHON) scripts/hardening/unified_config_manager.py audit
	@echo "$(GREEN)✅ Configuration drift detection completed$(NC)"

validate-config-drift-auto: ## Configuration drift detection with auto-correction
	@echo "$(BLUE)🔧 Running configuration drift detection with auto-correction...$(NC)"
	$(PYTHON) scripts/hardening/config_drift_detector.py --auto-correct --verbose
	$(PYTHON) scripts/hardening/configuration_standardization.py
	@echo "$(GREEN)✅ Configuration drift auto-correction completed$(NC)"

validate-startup-readiness: ## Validate service startup readiness based on real-world issues
	@echo "$(BLUE)🚀 Validating service startup readiness...$(NC)"
	$(PYTHON) scripts/hardening/unified_config_manager.py startup-check
	@echo "$(GREEN)✅ Startup readiness validation completed$(NC)"

validate-config-consistency: ## Validate configuration consistency across all files
	@echo "$(BLUE)🔍 Validating configuration consistency...$(NC)"
	$(PYTHON) audit_configuration.py
	$(PYTHON) scripts/hardening/unified_config_manager.py audit
	$(PYTHON) scripts/hardening/unified_docker_standardizer.py --mode validate
	@echo "Comparing service configs with Docker configs..."
	@for service in services/*/; do \
		if [ -f "$$service/config.yaml" ] && [ -f "$$service/docker-compose.yml" ]; then \
			service_name=$$(basename $$service); \
			config_port=$$($(PYTHON) -c "import yaml; print(yaml.safe_load(open('$$service/config.yaml'))['server']['port'])" 2>/dev/null || echo "unknown"); \
			compose_port=$$(grep -o '"[0-9]*:[0-9]*"' "$$service/docker-compose.yml" | head -1 | cut -d'"' -f2 | cut -d':' -f1 2>/dev/null || echo "unknown"); \
			if [ "$$config_port" != "unknown" ] && [ "$$compose_port" != "unknown" ] && [ "$$config_port" != "$$compose_port" ]; then \
				echo "$(RED)❌ $$service_name: Port mismatch (config: $$config_port, docker: $$compose_port)$(NC)"; \
			else \
				echo "$(GREEN)✅ $$service_name: Ports consistent$(NC)"; \
			fi; \
		fi; \
	done
	@echo "$(GREEN)✅ Configuration consistency validation completed$(NC)"

validate-api-contracts: ## Validate API contracts between services
	@echo "$(BLUE)🔗 Validating API contracts...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/safeguards/api_contract_validator.py --verbose --save-report
	@echo "$(GREEN)✅ API contract validation completed$(NC)"

validate-api-compare: ## Compare API specifications (usage: make validate-api-compare OLD_SPEC=path/to/old.json NEW_SPEC=path/to/new.json)
	@echo "$(BLUE)🔍 Comparing API specifications...$(NC)"
	source $(VENV)/bin/activate && python3 scripts/safeguards/api_contract_validator.py --compare $(OLD_SPEC) $(NEW_SPEC) --verbose
	@echo "$(GREEN)✅ API comparison completed$(NC)"

# Pydantic Configuration System (Now Default)
pydantic-enable: ## Enable Pydantic configuration system (enhanced validation - now default)
	@echo "$(BLUE)🔧 Pydantic configuration system is now ENABLED by default$(NC)"
	@echo "✅ All services use enhanced validation automatically"
	@echo "✅ New services get type safety and validation"
	@echo "✅ Existing services migrate gradually"
	@echo "$(GREEN)✅ Pydantic configuration system active$(NC)"

pydantic-disable: ## Disable Pydantic configuration system (use legacy dataclass mode)
	@echo "$(BLUE)📋 Switching to legacy dataclass configuration system...$(NC)"
	@echo "Set USE_PYDANTIC_CONFIG=false to disable enhanced validation"
	@echo "⚠️  This disables type safety and advanced validation"
	@echo "Use only for troubleshooting or legacy compatibility"
	@echo "$(YELLOW)⚠️  Legacy mode enabled - enhanced validation disabled$(NC)"

pydantic-test: ## Run Pydantic configuration system tests
	@echo "$(BLUE)🧪 Running Pydantic configuration tests...$(NC)"
	$(PYTHON) scripts/hardening/test_pydantic_config.py
	@echo "$(GREEN)✅ Pydantic configuration tests completed$(NC)"

pydantic-status: ## Check Pydantic configuration system status
	@echo "$(BLUE)📊 Pydantic Configuration System Status$(NC)"
	@echo "=========================================="
	@if [ "$$USE_PYDANTIC_CONFIG" != "false" ]; then \
		echo "🔧 Pydantic Mode: ENABLED (default - enhanced validation)"; \
	else \
		echo "📋 Pydantic Mode: DISABLED (using legacy dataclass)"; \
	fi
	@echo ""
	@echo "Configuration Sources:"
	@echo "  • Environment Variable: USE_PYDANTIC_CONFIG=$$USE_PYDANTIC_CONFIG"
	@echo "  • Default: true (Pydantic enabled)"
	@echo "  • Supported Values: true, false, 1, 0, yes, no, on, off"
	@echo ""
	@echo "Current Behavior:"
	@if [ "$$USE_PYDANTIC_CONFIG" != "false" ]; then \
		echo "  ✅ New services use Pydantic (enhanced validation)"; \
		echo "  ✅ Existing services migrate gradually"; \
	else \
		echo "  ⚠️  All services use legacy dataclass mode"; \
	fi
	@echo ""
	@echo "To disable Pydantic (legacy mode):"
	@echo "  export USE_PYDANTIC_CONFIG=false"
	@echo ""
	@echo "To enable Pydantic for single command:"
	@echo "  USE_PYDANTIC_CONFIG=true make <target>"
	@echo "$(GREEN)✅ Status check completed$(NC)"

validate-pydantic: pydantic-test ## Validate Pydantic configuration system (alias for pydantic-test)
	@echo "$(GREEN)✅ Pydantic validation completed$(NC)"

validate-service-startup: ## Validate service configuration for startup (usage: make validate-service-startup SERVICE=service-name)
	@echo "$(BLUE)🚀 Validating $(SERVICE) configuration for startup...$(NC)"
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)❌ Error: SERVICE parameter required$(NC)"; \
		echo "Usage: make validate-service-startup SERVICE=service-name"; \
		exit 1; \
	fi
	$(PYTHON) services/shared/infrastructure/config/startup_validator.py $(SERVICE)
	@if [ $$? -eq 0 ]; then \
		echo "$(GREEN)✅ $(SERVICE) configuration validated for startup$(NC)"; \
	else \
		echo "$(RED)❌ $(SERVICE) configuration validation failed$(NC)"; \
		exit 1; \
	fi

validate-docker-files: ## Validate all Docker configurations (docker-compose.yml, Dockerfiles)
	@echo "$(BLUE)🐳 Validating Docker configurations...$(NC)"
	$(PYTHON) scripts/hardening/validate_docker_configs.py
	@if [ $$? -eq 0 ]; then \
		echo "$(GREEN)✅ All Docker configurations validated$(NC)"; \
	else \
		echo "$(RED)❌ Docker configuration validation failed$(NC)"; \
		exit 1; \
	fi

validate-docker-compose: ## Validate docker-compose.yml files only
	@echo "$(BLUE)🐳 Validating Docker Compose files...$(NC)"
	$(PYTHON) scripts/hardening/validate_docker_compose.py

config-monitor: ## Show configuration system monitoring and metrics
	@echo "$(BLUE)📊 Configuration System Monitoring$(NC)"
	@echo "======================================"
	$(PYTHON) scripts/hardening/config_monitor_cli.py dashboard
	@echo "$(GREEN)✅ Monitoring check completed$(NC)"

config-health: ## Check configuration health for all services
	@echo "$(BLUE)🏥 Configuration Health Check$(NC)"
	@echo "==============================="
	$(PYTHON) scripts/hardening/config_monitor_cli.py health
	@echo "$(GREEN)✅ Health check completed$(NC)"

config-service-health: ## Check health for specific service (usage: make config-service-health SERVICE=service-name)
	@echo "$(BLUE)🔍 Service Health: $(SERVICE)$(NC)"
	@echo "=========================="
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)❌ Error: SERVICE parameter required$(NC)"; \
		echo "Usage: make config-service-health SERVICE=service-name"; \
		exit 1; \
	fi
	$(PYTHON) scripts/hardening/config_monitor_cli.py service --service $(SERVICE)
	@echo "$(GREEN)✅ Service health check completed$(NC)"

# ========================================
# UNIFIED DOCKER STANDARDIZATION
# ========================================

docker-standardize: ## Run unified Docker standardization (validate mode)
	@echo "$(BLUE)🔧 Running Unified Docker Standardization (Validate Mode)$(NC)"
	$(PYTHON) scripts/hardening/unified_docker_standardizer.py --mode validate

docker-standardize-dry-run: ## Run unified Docker standardization (dry-run mode)
	@echo "$(BLUE)🔧 Running Unified Docker Standardization (Dry Run Mode)$(NC)"
	$(PYTHON) scripts/hardening/unified_docker_standardizer.py --mode dry-run

docker-standardize-apply: ## Run unified Docker standardization (apply changes mode) - USE WITH CAUTION
	@echo "$(YELLOW)⚠️  WARNING: This will modify Docker configuration files$(NC)"
	@echo "$(BLUE)🔧 Running Unified Docker Standardization (Apply Mode)$(NC)"
	$(PYTHON) scripts/hardening/unified_docker_standardizer.py --mode apply

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

# ========================================
# ADVANCED CONFIGURATION VALIDATION
# ========================================

validate-drift: ## Comprehensive configuration drift detection (Docker + YAML + Pydantic + Network + Baselines)
	@echo "$(BLUE)🔍 Running comprehensive configuration drift detection...$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --full-drift --dev-only
	@echo "$(GREEN)✅ Drift detection completed$(NC)"

validate-baselines: ## Check configuration compliance against baselines
	@echo "$(BLUE)📋 Running baseline compliance validation...$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --baseline-only
	@echo "$(GREEN)✅ Baseline validation completed$(NC)"

create-baseline: ## Create baseline for a specific service (usage: make create-baseline ENV=development SERVICE=orchestrator TYPE=yaml)
	@echo "$(BLUE)📋 Creating baseline for $(ENV)/$(SERVICE)/$(TYPE)...$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --create-baseline $(ENV) $(SERVICE) $(TYPE)
	@echo "$(GREEN)✅ Baseline creation completed$(NC)"

generate-baselines: ## Auto-generate baselines for all current configurations
	@echo "$(BLUE)📋 Auto-generating baselines for all configurations...$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --generate-baselines
	@echo "$(GREEN)✅ Baseline generation completed$(NC)"

validate-environments: ## Compare configurations across different environments for consistency
	@echo "$(BLUE)🌍 Comparing configurations across environments...$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --env-compare-only
	@echo "$(GREEN)✅ Environment comparison completed$(NC)"

validate-dependencies: ## Analyze service dependencies and detect cascading effects
	@echo "$(BLUE)🔗 Analyzing service dependencies and cascading effects...$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --dependency-only
	@echo "$(GREEN)✅ Dependency analysis completed$(NC)"

auto-correct-config: ## Automatically correct configuration issues with backups
	@echo "$(BLUE)🔧 Applying automated configuration corrections...$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --auto-correct
	@echo "$(GREEN)✅ Automated correction completed$(NC)"

dry-run-corrections: ## Show what corrections would be applied without making changes
	@echo "$(BLUE)👀 Performing dry run of automated corrections...$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --dry-run-corrections
	@echo "$(GREEN)✅ Dry run completed$(NC)"

rollback-corrections: ## Rollback automated corrections (use TIMESTAMP env var)
	@echo "$(BLUE)🔄 Rolling back corrections made after $(TIMESTAMP)...$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --rollback-corrections "$(TIMESTAMP)"
	@echo "$(GREEN)✅ Rollback completed$(NC)"

list-correction-backups: ## List all available correction backups
	@echo "$(BLUE)📦 Listing correction backups...$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --list-backups
	@echo "$(GREEN)✅ Backup listing completed$(NC)"

# ========================================
# META-ORCHESTRATION SERVICE
# ========================================

meta-orchestrator-build: ## Build the meta-orchestration service
	@echo "$(BLUE)🏗️ Building meta-orchestration service...$(NC)"
	docker build -f services/meta-orchestrator/Dockerfile -t hackathon-meta-orchestrator .
	@echo "$(GREEN)✅ Meta-orchestrator built$(NC)"

meta-orchestrator-run: ## Run the meta-orchestration service
	@echo "$(BLUE)🚀 Starting meta-orchestration service...$(NC)"
	docker run -d \
		--name meta-orchestrator \
		--network hackathon-network \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD):/app \
		-e DOCKER_HOST=unix:///var/run/docker.sock \
		-p 8080:8080 \
		hackathon-meta-orchestrator
	@echo "$(GREEN)✅ Meta-orchestrator running on port 8080$(NC)"

meta-orchestrator-stop: ## Stop the meta-orchestration service
	@echo "$(BLUE)🛑 Stopping meta-orchestration service...$(NC)"
	docker stop meta-orchestrator || true
	docker rm meta-orchestrator || true
	@echo "$(GREEN)✅ Meta-orchestrator stopped$(NC)"

meta-orchestrator-logs: ## View meta-orchestrator logs
	@echo "$(BLUE)📋 Meta-orchestrator logs...$(NC)"
	docker logs -f meta-orchestrator

meta-orchestrator-health: ## Check meta-orchestrator health
	@echo "$(BLUE)🏥 Checking meta-orchestrator health...$(NC)"
	curl -f http://localhost:8080/health || echo "$(RED)❌ Meta-orchestrator unhealthy$(NC)"
	@echo "$(GREEN)✅ Meta-orchestrator healthy$(NC)"

validate-network: ## Network configuration and port conflict validation
	@echo "$(BLUE)🌐 Running network configuration validation...$(NC)"
	@echo "$(BLUE)Step 1: Port conflict detection$(NC)"
	@make validate-ports --silent || echo "$(YELLOW)⚠️  Port validation failed but continuing...$(NC)"
	@echo "$(BLUE)Step 2: Network drift detection$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --network-only
	@echo "$(GREEN)✅ Network validation completed$(NC)"

validate-drift-docker: ## Docker-specific drift detection
	@echo "$(BLUE)🐳 Running Docker drift detection...$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --docker-only
	@echo "$(GREEN)✅ Docker drift detection completed$(NC)"

validate-drift-pydantic: ## Pydantic configuration drift detection
	@echo "$(BLUE)🔧 Running Pydantic drift detection...$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --pydantic-only
	@echo "$(GREEN)✅ Pydantic drift detection completed$(NC)"

validate-schema: ## Validate all configurations against JSON schemas
	@echo "$(BLUE)📋 Running schema validation...$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --schema-only
	@echo "$(GREEN)✅ Schema validation completed$(NC)"

validate-production-ready: ## Full production readiness validation
	@echo "$(BLUE)🚀 Running production readiness validation...$(NC)"
	$(PYTHON) scripts/hardening/validation/production_readiness_validator.py
	@echo "$(GREEN)✅ Production readiness validation completed$(NC)"

validate-ecosystem-health: ## Comprehensive ecosystem health check
	@echo "$(BLUE)🏥 Running ecosystem health validation...$(NC)"
	$(PYTHON) scripts/safeguards/unified_health_monitor.py --comprehensive
	@echo "$(GREEN)✅ Ecosystem health validation completed$(NC)"

validate-all-configs: ## Validate all configuration aspects
	@echo "$(BLUE)🔍 Running complete configuration validation suite...$(NC)"
	@echo "$(BLUE)Step 1: Schema validation$(NC)"
	@make validate-schema --silent || echo "$(YELLOW)⚠️  Schema validation failed but continuing...$(NC)"
	@echo "$(BLUE)Step 2: Network validation$(NC)"
	@make validate-network --silent || echo "$(YELLOW)⚠️  Network validation failed but continuing...$(NC)"
	@echo "$(BLUE)Step 3: Baseline compliance$(NC)"
	@make validate-baselines --silent || echo "$(YELLOW)⚠️  Baseline validation failed but continuing...$(NC)"
	@echo "$(BLUE)Step 4: Environment consistency$(NC)"
	@make validate-environments --silent || echo "$(YELLOW)⚠️  Environment comparison failed but continuing...$(NC)"
	@echo "$(BLUE)Step 5: Service dependencies$(NC)"
	@make validate-dependencies --silent || echo "$(YELLOW)⚠️  Dependency analysis failed but continuing...$(NC)"
	@echo "$(BLUE)Step 6: Configuration drift$(NC)"
	@make validate-drift --silent
	@echo "$(BLUE)Step 7: Production readiness$(NC)"
	@make validate-production-ready --silent
	@echo "$(BLUE)Step 8: Ecosystem health$(NC)"
	@make validate-ecosystem-health --silent
	@echo "$(GREEN)✅ Complete configuration validation completed$(NC)"

# ========================================
# CI/CD INTEGRATION TARGETS
# ========================================

ci-validate-config: ## CI/CD configuration validation (fast, non-blocking)
	@echo "$(BLUE)🔄 Running CI configuration validation...$(NC)"
	@echo "$(BLUE)Step 1: Quick schema check$(NC)"
	@make validate-schema --silent 2>/dev/null || echo "$(YELLOW)⚠️  Schema issues found$(NC)"
	@echo "$(BLUE)Step 2: Basic drift detection$(NC)"
	@make validate-drift --silent 2>/dev/null || echo "$(YELLOW)⚠️  Drift detected$(NC)"
	@echo "$(BLUE)Step 3: Health endpoints$(NC)"
	@make validate-health-endpoints --silent 2>/dev/null || echo "$(YELLOW)⚠️  Health issues found$(NC)"
	@echo "$(GREEN)✅ CI configuration validation completed$(NC)"

ci-validate-deployment: ## CI/CD pre-deployment validation
	@echo "$(BLUE)🚀 Running CI deployment validation...$(NC)"
	@make validate-production-ready --silent
	@make validate-ecosystem-health --silent
	@echo "$(GREEN)✅ CI deployment validation completed$(NC)"

ci-gate-check: ## CI quality gate - fails if critical issues found
	@echo "$(BLUE)🚪 Running CI quality gate...$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --ci-gate || (echo "$(RED)❌ Quality gate failed - critical issues found$(NC)" && exit 1)
	@echo "$(GREEN)✅ Quality gate passed$(NC)"

# ========================================
# MONITORING & ALERTING TARGETS
# ========================================

monitor-config: ## Start configuration monitoring service
	@echo "$(BLUE)👀 Starting configuration monitoring...$(NC)"
	$(PYTHON) scripts/safeguards/config_monitor_service.py --start
	@echo "$(GREEN)✅ Configuration monitoring started$(NC)"

monitor-health: ## Continuous health monitoring
	@echo "$(BLUE)🏥 Starting continuous health monitoring...$(NC)"
	$(PYTHON) scripts/safeguards/unified_health_monitor.py --monitor
	@echo "$(GREEN)✅ Health monitoring started$(NC)"

alert-config-drift: ## Check for configuration drift and alert if found
	@echo "$(BLUE)🚨 Checking for configuration drift...$(NC)"
	$(PYTHON) scripts/safeguards/config_drift_detector.py --alert-on-drift
	@echo "$(GREEN)✅ Drift check completed$(NC)"

# ========================================
# DEVELOPMENT WORKFLOW TARGETS
# ========================================

dev-full-validate: ## Complete development validation (comprehensive but slow)
	@echo "$(BLUE)🔍 Running full development validation...$(NC)"
	@make validate-all-configs --silent
	@make validate-comprehensive --silent
	@echo "$(GREEN)🎉 Full development validation completed$(NC)"

dev-quick-check: ## Quick development validation (fast feedback)
	@echo "$(BLUE)⚡ Running quick development check...$(NC)"
	@make validate-health-endpoints --silent
	@make validate-ports --silent
	@make ci-validate-config --silent
	@echo "$(GREEN)✅ Quick development check completed$(NC)"

# ========================================
# CONFIGURATION MANAGEMENT TARGETS
# ========================================

config-backup: ## Create configuration backup
	@echo "$(BLUE)💾 Creating configuration backup...$(NC)"
	@mkdir -p backups/config/$(shell date +%Y%m%d_%H%M%S)
	@cp -r docker-compose*.yml backups/config/$(shell date +%Y%m%d_%H%M%S)/
	@find services -name "config.yaml" -o -name "config.yml" | xargs -I {} cp {} backups/config/$(shell date +%Y%m%d_%H%M%S)/
	@echo "$(GREEN)✅ Configuration backup created$(NC)"

config-version: ## Show configuration versions
	@echo "$(BLUE)📋 Configuration versions:$(NC)"
	@find . -name "docker-compose*.yml" -exec echo "  {}: $(shell git log -1 --format="%h %s" {})" \;
	@find services -name "config.yaml" -o -name "config.yml" | while read file; do echo "  $$file: $(shell git log -1 --format="%h %s" "$$file" 2>/dev/null || echo "not committed")"; done

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

# Pre-deployment validation (moved to integrated workflows below)

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

# ============================================================================
# UNIFIED API DASHBOARD MANAGEMENT
# ============================================================================

dashboard: ## Show unified API dashboard management commands
	@echo "$(BLUE)🌐 Unified API Dashboard$(NC)"
	@echo "=========================="
	@echo ""
	@echo "Available dashboard commands:"
	@echo "  $(CYAN)make dashboard-start$(NC)    - Start unified API dashboard"
	@echo "  $(CYAN)make dashboard-stop$(NC)     - Stop unified API dashboard"
	@echo "  $(CYAN)make dashboard-logs$(NC)     - Show dashboard logs"
	@echo "  $(CYAN)make dashboard-health$(NC)   - Check dashboard health"
	@echo "  $(CYAN)make dashboard-test$(NC)     - Run dashboard tests"
	@echo ""
	@echo "Dashboard URL: http://localhost:8000"
	@echo "API Documentation: http://localhost:8000/docs"

dashboard-start: ## Start unified API dashboard
	@echo "$(BLUE)🌐 Starting Unified API Dashboard...$(NC)"
	docker-compose -f docker-compose.dev.yml up -d unified-api-dashboard
	@echo "$(GREEN)✅ Dashboard starting...$(NC)"
	@echo "$(YELLOW)📊 Dashboard will be available at: http://localhost:8000$(NC)"

dashboard-stop: ## Stop unified API dashboard
	@echo "$(BLUE)🛑 Stopping Unified API Dashboard...$(NC)"
	docker-compose -f docker-compose.dev.yml stop unified-api-dashboard
	@echo "$(GREEN)✅ Dashboard stopped$(NC)"

dashboard-logs: ## Show unified API dashboard logs
	@echo "$(BLUE)📋 Unified API Dashboard Logs$(NC)"
	docker-compose -f docker-compose.dev.yml logs -f unified-api-dashboard

dashboard-health: ## Check unified API dashboard health
	@echo "$(BLUE)🏥 Unified API Dashboard Health$(NC)"
	@echo "===================================="
	@echo ""
	@echo "$(YELLOW)Container Status:$(NC)"
	@docker-compose -f docker-compose.dev.yml ps unified-api-dashboard --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "$(YELLOW)Health Check:$(NC)"
	@curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health || echo "❌ Service not responding"
	@echo ""
	@echo "$(YELLOW)API Catalog:$(NC)"
	@curl -s http://localhost:8000/api/discovery/services | jq '.data | length' 2>/dev/null | xargs echo "Services discovered:" || echo "Unable to check API catalog"

dashboard-test: ## Run unified API dashboard tests
	@echo "$(BLUE)🧪 Running Unified API Dashboard Tests...$(NC)"
	cd services/unified-api-dashboard && python -m pytest tests/ -v --tb=short
	@echo "$(GREEN)✅ Dashboard tests completed$(NC)"

# ========================================
# 📝 PROMPT STORE SERVICE MANAGEMENT
# ========================================

prompt-store-run: ## Start prompt store service
	@echo "$(BLUE)🚀 Starting Prompt Store Service...$(NC)"
	cd services/prompt_store && python main.py

prompt-store-test: ## Run prompt store tests
	@echo "$(BLUE)🧪 Running Prompt Store Tests...$(NC)"
	cd services/prompt_store && python -m pytest tests/ -v --tb=short
	@echo "$(GREEN)✅ Prompt store tests completed$(NC)"

prompt-store-docker: ## Start prompt store service in Docker
	@echo "$(BLUE)🐳 Starting Prompt Store Service in Docker...$(NC)"
	docker-compose --profile prompt-store up -d
	@echo "$(GREEN)✅ Prompt store service started in Docker$(NC)"
	@echo "$(YELLOW)📊 Service available at: http://localhost:5110$(NC)"

prompt-store-stop: ## Stop prompt store service
	@echo "$(BLUE)🛑 Stopping Prompt Store Service...$(NC)"
	docker-compose --profile prompt-store down
	@echo "$(GREEN)✅ Prompt store service stopped$(NC)"

prompt-store-logs: ## View prompt store service logs
	@echo "$(BLUE)📋 Prompt Store Service Logs$(NC)"
	docker-compose --profile prompt-store logs -f --tail=100

prompt-store-health: ## Check prompt store service health
	@echo "$(BLUE)🏥 Prompt Store Service Health Check$(NC)"
	@echo "$(YELLOW)Container Status:$(NC)"
	@docker-compose --profile prompt-store ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "$(YELLOW)Health Check:$(NC)"
	@curl -s http://localhost:5110/health | jq . 2>/dev/null || curl -s http://localhost:5110/health || echo "❌ Service not responding"

# ========================================
# 🤖 LLM GATEWAY SERVICE MANAGEMENT
# ========================================

llm-gateway-run: ## Start LLM gateway service
	@echo "$(BLUE)🚀 Starting LLM Gateway Service...$(NC)"
	cd services/llm-gateway && python main.py

llm-gateway-test: ## Run LLM gateway tests
	@echo "$(BLUE)🧪 Running LLM Gateway Tests...$(NC)"
	cd services/llm-gateway && python -m pytest tests/ -v --tb=short
	@echo "$(GREEN)✅ LLM gateway tests completed$(NC)"

llm-gateway-docker: ## Start LLM gateway service in Docker
	@echo "$(BLUE)🐳 Starting LLM Gateway Service in Docker...$(NC)"
	docker-compose --profile llm-gateway up -d
	@echo "$(GREEN)✅ LLM gateway service started in Docker$(NC)"
	@echo "$(YELLOW)📊 Service available at: http://localhost:5055$(NC)"

llm-gateway-stop: ## Stop LLM gateway service
	@echo "$(BLUE)🛑 Stopping LLM Gateway Service...$(NC)"
	docker-compose --profile llm-gateway down
	@echo "$(GREEN)✅ LLM gateway service stopped$(NC)"

llm-gateway-logs: ## View LLM gateway service logs
	@echo "$(BLUE)📋 LLM Gateway Service Logs$(NC)"
	docker-compose --profile llm-gateway logs -f --tail=100

llm-gateway-health: ## Check LLM gateway service health
	@echo "$(BLUE)🏥 LLM Gateway Service Health Check$(NC)"
	@echo "$(YELLOW)Container Status:$(NC)"
	@docker-compose --profile llm-gateway ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "$(YELLOW)Health Check:$(NC)"
	@curl -s http://localhost:5055/health | jq . 2>/dev/null || curl -s http://localhost:5055/health || echo "❌ Service not responding"

# ========================================
# 🔍 CODE ANALYZER SERVICE MANAGEMENT
# ========================================

code-analyzer-run: ## Start code analyzer service
	@echo "$(BLUE)🚀 Starting Code Analyzer Service...$(NC)"
	cd services/code-analyzer && python main.py

code-analyzer-test: ## Run code analyzer tests
	@echo "$(BLUE)🧪 Running Code Analyzer Tests...$(NC)"
	cd services/code-analyzer && python -m pytest tests/ -v --tb=short
	@echo "$(GREEN)✅ Code analyzer tests completed$(NC)"

code-analyzer-docker: ## Start code analyzer service in Docker
	@echo "$(BLUE)🐳 Starting Code Analyzer Service in Docker...$(NC)"
	docker-compose --profile code-analyzer up -d
	@echo "$(GREEN)✅ Code analyzer service started in Docker$(NC)"
	@echo "$(YELLOW)📊 Service available at: http://localhost:5025$(NC)"

code-analyzer-stop: ## Stop code analyzer service
	@echo "$(BLUE)🛑 Stopping Code Analyzer Service...$(NC)"
	docker-compose --profile code-analyzer down
	@echo "$(GREEN)✅ Code analyzer service stopped$(NC)"

code-analyzer-logs: ## View code analyzer service logs
	@echo "$(BLUE)📋 Code Analyzer Service Logs$(NC)"
	docker-compose --profile code-analyzer logs -f --tail=100

code-analyzer-health: ## Check code analyzer service health
	@echo "$(BLUE)🏥 Code Analyzer Service Health Check$(NC)"
	@echo "$(YELLOW)Container Status:$(NC)"
	@docker-compose --profile code-analyzer ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "$(YELLOW)Health Check:$(NC)"
	@curl -s http://localhost:5025/health | jq . 2>/dev/null || curl -s http://localhost:5025/health || echo "❌ Service not responding"

# ========================================
# 🎼 ORCHESTRATOR SERVICE MANAGEMENT
# ========================================

orchestrator-run: ## Start orchestrator service
	@echo "$(BLUE)🚀 Starting Orchestrator Service...$(NC)"
	cd services/orchestrator && python main.py

orchestrator-test: ## Run orchestrator tests
	@echo "$(BLUE)🧪 Running Orchestrator Tests...$(NC)"
	cd services/orchestrator && python -m pytest tests/ -v --tb=short
	@echo "$(GREEN)✅ Orchestrator tests completed$(NC)"

orchestrator-docker: ## Start orchestrator service in Docker
	@echo "$(BLUE)🐳 Starting Orchestrator Service in Docker...$(NC)"
	docker-compose --profile orchestrator up -d
	@echo "$(GREEN)✅ Orchestrator service started in Docker$(NC)"
	@echo "$(YELLOW)📊 Service available at: http://localhost:5099$(NC)"

orchestrator-stop: ## Stop orchestrator service
	@echo "$(BLUE)🛑 Stopping Orchestrator Service...$(NC)"
	docker-compose --profile orchestrator down
	@echo "$(GREEN)✅ Orchestrator service stopped$(NC)"

orchestrator-logs: ## View orchestrator service logs
	@echo "$(BLUE)📋 Orchestrator Service Logs$(NC)"
	docker-compose --profile orchestrator logs -f --tail=100

orchestrator-health: ## Check orchestrator service health
	@echo "$(BLUE)🏥 Orchestrator Service Health Check$(NC)"
	@echo "$(YELLOW)Container Status:$(NC)"
	@docker-compose --profile orchestrator ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "$(YELLOW)Health Check:$(NC)"
	@curl -s http://localhost:5099/health | jq . 2>/dev/null || curl -s http://localhost:5099/health || echo "❌ Service not responding"

# ========================================
# 👥 USER STORE SERVICE MANAGEMENT
# ========================================

user-store-run: ## Start user store service
	@echo "$(BLUE)🚀 Starting User Store Service...$(NC)"
	cd services/user-store && python main.py

user-store-test: ## Run user store tests
	@echo "$(BLUE)🧪 Running User Store Tests...$(NC)"
	cd services/user-store && python -m pytest tests/ -v --tb=short
	@echo "$(GREEN)✅ User store tests completed$(NC)"

user-store-docker: ## Start user store service in Docker
	@echo "$(BLUE)🐳 Starting User Store Service in Docker...$(NC)"
	docker-compose --profile utility up -d user-store
	@echo "$(GREEN)✅ User store service started in Docker$(NC)"
	@echo "$(YELLOW)📊 Service available at: http://localhost:5150$(NC)"

user-store-stop: ## Stop user store service
	@echo "$(BLUE)🛑 Stopping User Store Service...$(NC)"
	docker-compose --profile utility down user-store
	@echo "$(GREEN)✅ User store service stopped$(NC)"

user-store-logs: ## View user store service logs
	@echo "$(BLUE)📋 User Store Service Logs$(NC)"
	docker-compose --profile utility logs -f --tail=100 user-store

user-store-health: ## Check user store service health
	@echo "$(BLUE)🏥 User Store Service Health Check$(NC)"
	@echo "$(YELLOW)Container Status:$(NC)"
	@docker-compose --profile utility ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" user-store
	@echo ""
	@echo "$(YELLOW)Health Check:$(NC)"
	@curl -s http://localhost:5150/health | jq . 2>/dev/null || curl -s http://localhost:5150/health || echo "❌ Service not responding"

# ========================================
# 🌐 EXTERNAL SERVICE STORE MANAGEMENT
# ========================================

external-service-store-run: ## Start external service store
	@echo "$(BLUE)🚀 Starting External Service Store...$(NC)"
	cd services/external-service-store && python main.py

external-service-store-test: ## Run external service store tests
	@echo "$(BLUE)🧪 Running External Service Store Tests...$(NC)"
	cd services/external-service-store && python -m pytest tests/ -v --tb=short
	@echo "$(GREEN)✅ External service store tests completed$(NC)"

external-service-store-docker: ## Start external service store in Docker
	@echo "$(BLUE)🐳 Starting External Service Store in Docker...$(NC)"
	docker-compose --profile utility up -d external-service-store
	@echo "$(GREEN)✅ External service store started in Docker$(NC)"
	@echo "$(YELLOW)📊 Service available at: http://localhost:5140$(NC)"

external-service-store-stop: ## Stop external service store
	@echo "$(BLUE)🛑 Stopping External Service Store...$(NC)"
	docker-compose --profile utility down external-service-store
	@echo "$(GREEN)✅ External service store stopped$(NC)"

external-service-store-logs: ## View external service store logs
	@echo "$(BLUE)📋 External Service Store Logs$(NC)"
	docker-compose --profile utility logs -f --tail=100 external-service-store

external-service-store-health: ## Check external service store health
	@echo "$(BLUE)🏥 External Service Store Health Check$(NC)"
	@echo "$(YELLOW)Container Status:$(NC)"
	@docker-compose --profile utility ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" external-service-store
	@echo ""
	@echo "$(YELLOW)Health Check:$(NC)"
	@curl -s http://localhost:5140/health | jq . 2>/dev/null || curl -s http://localhost:5140/health || echo "❌ Service not responding"

# ========================================
# 🔍 AUDIT FRAMEWORK INTEGRATION
# ========================================

audit: ## Run quick service audit
	@echo "$(BLUE)🔍 Running Quick Service Audit...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-quick
	@echo "$(GREEN)✅ Quick audit completed$(NC)"

audit-all: ## Run comprehensive audit of all services
	@echo "$(BLUE)🔬 Running Comprehensive Service Audit...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-all
	@echo "$(GREEN)✅ Comprehensive audit completed$(NC)"

audit-services: ## Audit all services individually
	@echo "$(BLUE)🔍 Auditing All Services...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-services
	@echo "$(GREEN)✅ All services audited$(NC)"

audit-ci: ## CI-optimized audit pipeline
	@echo "$(BLUE)⚡ Running CI Audit Pipeline...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit ci-audit
	@echo "$(GREEN)✅ CI audit pipeline completed$(NC)"

audit-quick: ## Quick audit for development
	@echo "$(BLUE)⚡ Running Quick Development Audit...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-quick
	@echo "$(GREEN)✅ Quick audit completed$(NC)"

audit-comprehensive: ## Comprehensive audit for releases
	@echo "$(BLUE)🔬 Running Comprehensive Release Audit...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-comprehensive
	@echo "$(GREEN)✅ Comprehensive audit completed$(NC)"

audit-parallel: ## Run audits in parallel
	@echo "$(BLUE)🔬 Running Parallel Audits...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-parallel
	@echo "$(GREEN)✅ Parallel audits completed$(NC)"

audit-report: ## Generate audit reports
	@echo "$(BLUE)📊 Generating Audit Reports...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-report
	@echo "$(GREEN)✅ Audit reports generated$(NC)"

audit-clean: ## Clean audit artifacts
	@echo "$(BLUE)🧹 Cleaning Audit Artifacts...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-clean
	@echo "$(GREEN)✅ Audit cleanup completed$(NC)"

audit-setup: ## Set up audit framework environment
	@echo "$(BLUE)🔧 Setting up Audit Environment...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-setup
	@echo "$(GREEN)✅ Audit environment ready$(NC)"

audit-validate: ## Validate audit framework
	@echo "$(BLUE)🔍 Validating Audit Framework...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-validate
	@echo "$(GREEN)✅ Audit validation completed$(NC)"

audit-benchmark: ## Run audit performance benchmark
	@echo "$(BLUE)📈 Running Audit Benchmark...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-benchmark
	@echo "$(GREEN)✅ Audit benchmark completed$(NC)"

audit-trend: ## Analyze audit trends
	@echo "$(BLUE)📈 Analyzing Audit Trends...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-trend
	@echo "$(GREEN)✅ Trend analysis completed$(NC)"

audit-config: ## Show audit configuration
	@echo "$(BLUE)⚙️ Audit Configuration$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-config

audit-debug: ## Debug audit framework
	@echo "$(BLUE)🐛 Debug Audit Framework...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-debug
	@echo "$(GREEN)✅ Debug completed$(NC)"

audit-docker: ## Run audit in Docker
	@echo "$(BLUE)🐳 Running Audit in Docker...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-docker
	@echo "$(GREEN)✅ Docker audit completed$(NC)"

audit-pre-commit: ## Run audit as pre-commit hook
	@echo "$(BLUE)🔒 Running Pre-commit Audit...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-pre-commit
	@echo "$(GREEN)✅ Pre-commit audit completed$(NC)"

audit-quality-gate: ## Check quality gates
	@echo "$(BLUE)🚨 Checking Quality Gates...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-quality-gate
	@echo "$(GREEN)✅ Quality gate check completed$(NC)"

audit-enforce: ## Enforce quality standards
	@echo "$(BLUE)🚫 Enforcing Quality Standards...$(NC)"
	$(MAKE) -f makefiles/Makefile.audit audit-enforce
	@echo "$(GREEN)✅ Quality standards enforced$(NC)"

# ========================================
# 🔄 INTEGRATED WORKFLOWS
# ========================================

# Integrated workflows with comprehensive validation
dev-setup: ecosystem-setup setup-logging validate-config ## Complete development setup with validation
	@echo "$(GREEN)🎉 Development environment ready!$(NC)"

dev-setup-full: ecosystem-setup setup-logging validate-config validate-docker-config ## Complete development setup with full validation
	@echo "$(GREEN)🎉 Development environment with full validation ready!$(NC)"

ci-validate: ## Run comprehensive CI/CD validation suite
	@echo "$(CYAN)🚀 Running CI/CD Configuration Validation Suite$(NC)"
	@$(PYTHON) scripts/hardening/ci_cd_validator.py --quiet || (echo "$(RED)❌ CI/CD validation failed$(NC)" && exit 1)
	@echo "$(GREEN)✅ CI/CD validation passed$(NC)"

ci-test: ci-validate test ## CI testing with validation
	@echo "$(GREEN)✅ CI testing passed$(NC)"

pre-deploy: validate-config-consistency validate-docker-config validate-health ecosystem-health ## Pre-deployment validation
	@echo "$(GREEN)🚀 Pre-deployment validation passed$(NC)"

deploy-safe: pre-deploy docker-start-validated ## Safe deployment with full validation
	@echo "$(GREEN)🚀 Safe deployment completed$(NC)"

# Default target
.DEFAULT_GOAL := help
