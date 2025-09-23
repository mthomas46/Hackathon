PYTHON ?= python3
VENV ?= venv_hardening

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help test docs docs-serve timeline ecosystem ecosystem-validate ecosystem-health ecosystem-clean validate-health-endpoints validate-health-continuous validate-config-drift validate-config-drift-auto validate-api-contracts validate-api-compare setup-logging validate-logging monitor-services health-check-all logs-view logs-clean simulation simulation-run simulation-test simulation-docker simulation-stop simulation-status test-redis test-orchestrator test-discovery-agent test-doc-store test-prompt-store test-interpreter test-llm-gateway test-summarizer-hub test-bedrock-proxy test-github-mcp test-analysis-service test-code-analyzer test-secure-analyzer test-architecture-digitizer test-memory-agent test-notification-service test-source-agent test-cli test-mock-data-generator test-frontend test-simulation-dashboard test-data-services-dashboard test-log-collector test-project-simulation test-core-services test-document-services test-ai-services test-analysis-services test-agent-services test-utility-services test-frontend-services test-simulation-services test-all-services test-infrastructure test-business-logic test-integration-ready perf-test-project-simulation perf-test-analysis-service perf-test-all validate-service-health validate-docker-config validate-test-coverage validate-all test-ci-unit test-ci-integration test-ci-e2e test-ci-performance test-ci-full lint lint-imports lint-format lint-check lint-fix lint-security

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

# Service-Specific Test Targets
# ============================================================================

# Core Infrastructure Tests
test-redis: ## Test Redis infrastructure
	@echo "$(BLUE)🗄️  Testing Redis...$(NC)"
	docker exec hackathon-redis-1 redis-cli ping | grep -q PONG && echo "$(GREEN)✅ Redis OK$(NC)" || echo "$(RED)❌ Redis Failed$(NC)"

test-orchestrator: ## Test orchestrator service
	@echo "$(BLUE)🎯 Testing Orchestrator...$(NC)"
	$(PYTHON) -m pytest services/orchestrator/tests/ -v --tb=short
	@echo "$(GREEN)✅ Orchestrator tests complete$(NC)"

test-discovery-agent: ## Test discovery agent
	@echo "$(BLUE)🔍 Testing Discovery Agent...$(NC)"
	$(PYTHON) -m pytest services/discovery-agent/tests/ -v --tb=short
	@echo "$(GREEN)✅ Discovery Agent tests complete$(NC)"

# Document Services Tests
test-doc-store: ## Test document store service
	@echo "$(BLUE)📄 Testing Document Store...$(NC)"
	$(PYTHON) -m pytest services/doc_store/tests/ -v --tb=short
	@echo "$(GREEN)✅ Document Store tests complete$(NC)"

test-prompt-store: ## Test prompt store service
	@echo "$(BLUE)💭 Testing Prompt Store...$(NC)"
	$(PYTHON) -m pytest services/prompt_store/tests/ -v --tb=short
	@echo "$(GREEN)✅ Prompt Store tests complete$(NC)"

test-interpreter: ## Test interpreter service
	@echo "$(BLUE)🔮 Testing Interpreter...$(NC)"
	$(PYTHON) -m pytest services/interpreter/tests/ -v --tb=short
	@echo "$(GREEN)✅ Interpreter tests complete$(NC)"

# AI/ML Services Tests
test-llm-gateway: ## Test LLM gateway service
	@echo "$(BLUE)🤖 Testing LLM Gateway...$(NC)"
	$(PYTHON) -m pytest services/llm-gateway/tests/ -v --tb=short
	@echo "$(GREEN)✅ LLM Gateway tests complete$(NC)"

test-summarizer-hub: ## Test summarizer hub service
	@echo "$(BLUE)📝 Testing Summarizer Hub...$(NC)"
	$(PYTHON) -m pytest services/summarizer-hub/tests/ -v --tb=short
	@echo "$(GREEN)✅ Summarizer Hub tests complete$(NC)"

test-bedrock-proxy: ## Test bedrock proxy service
	@echo "$(BLUE)🛡️  Testing Bedrock Proxy...$(NC)"
	$(PYTHON) -m pytest services/bedrock-proxy/tests/ -v --tb=short
	@echo "$(GREEN)✅ Bedrock Proxy tests complete$(NC)"

test-github-mcp: ## Test GitHub MCP service
	@echo "$(BLUE)🐙 Testing GitHub MCP...$(NC)"
	$(PYTHON) -m pytest services/github-mcp/tests/ -v --tb=short
	@echo "$(GREEN)✅ GitHub MCP tests complete$(NC)"

# Analysis Services Tests
test-analysis-service: ## Test analysis service
	@echo "$(BLUE)🔬 Testing Analysis Service...$(NC)"
	$(PYTHON) -m pytest services/analysis-service/tests/ -v --tb=short
	@echo "$(GREEN)✅ Analysis Service tests complete$(NC)"

test-code-analyzer: ## Test code analyzer service
	@echo "$(BLUE)💻 Testing Code Analyzer...$(NC)"
	$(PYTHON) -m pytest services/code-analyzer/tests/ -v --tb=short
	@echo "$(GREEN)✅ Code Analyzer tests complete$(NC)"

test-secure-analyzer: ## Test secure analyzer service
	@echo "$(BLUE)🔒 Testing Secure Analyzer...$(NC)"
	$(PYTHON) -m pytest services/secure-analyzer/tests/ -v --tb=short
	@echo "$(GREEN)✅ Secure Analyzer tests complete$(NC)"

test-architecture-digitizer: ## Test architecture digitizer service
	@echo "$(BLUE)🏗️  Testing Architecture Digitizer...$(NC)"
	$(PYTHON) -m pytest services/architecture-digitizer/tests/ -v --tb=short
	@echo "$(GREEN)✅ Architecture Digitizer tests complete$(NC)"

# Agent Services Tests
test-memory-agent: ## Test memory agent (Note: may not exist yet)
	@echo "$(BLUE)🧠 Testing Memory Agent...$(NC)"
	@if [ -d services/memory-agent/tests ]; then \
		$(PYTHON) -m pytest services/memory-agent/tests/ -v --tb=short; \
	else \
		echo "$(YELLOW)⚠️  Memory Agent tests not found$(NC)"; \
	fi
	@echo "$(GREEN)✅ Memory Agent tests complete$(NC)"

test-notification-service: ## Test notification service
	@echo "$(BLUE)📢 Testing Notification Service...$(NC)"
	$(PYTHON) -m pytest services/notification-service/tests/ -v --tb=short
	@echo "$(GREEN)✅ Notification Service tests complete$(NC)"

test-source-agent: ## Test source agent service
	@echo "$(BLUE)📚 Testing Source Agent...$(NC)"
	$(PYTHON) -m pytest services/source-agent/tests/ -v --tb=short
	@echo "$(GREEN)✅ Source Agent tests complete$(NC)"

# Utility Services Tests
test-cli: ## Test CLI service
	@echo "$(BLUE)💻 Testing CLI...$(NC)"
	$(PYTHON) -m pytest services/cli/tests/ -v --tb=short
	@echo "$(GREEN)✅ CLI tests complete$(NC)"

test-mock-data-generator: ## Test mock data generator service
	@echo "$(BLUE)🎲 Testing Mock Data Generator...$(NC)"
	$(PYTHON) -m pytest services/mock-data-generator/tests/ -v --tb=short
	@echo "$(GREEN)✅ Mock Data Generator tests complete$(NC)"

# Frontend & Dashboard Tests
test-frontend: ## Test frontend service
	@echo "$(BLUE)🌐 Testing Frontend...$(NC)"
	$(PYTHON) -m pytest services/frontend/tests/ -v --tb=short
	@echo "$(GREEN)✅ Frontend tests complete$(NC)"

test-simulation-dashboard: ## Test simulation dashboard
	@echo "$(BLUE)📊 Testing Simulation Dashboard...$(NC)"
	$(PYTHON) -m pytest services/simulation-dashboard/tests/ -v --tb=short
	@echo "$(GREEN)✅ Simulation Dashboard tests complete$(NC)"

test-data-services-dashboard: ## Test data services dashboard
	@echo "$(BLUE)📈 Testing Data Services Dashboard...$(NC)"
	$(PYTHON) -m pytest services/data-services-dashboard/tests/ -v --tb=short
	@echo "$(GREEN)✅ Data Services Dashboard tests complete$(NC)"

# Logging & Monitoring Tests
test-log-collector: ## Test log collector service
	@echo "$(BLUE)📋 Testing Log Collector...$(NC)"
	$(PYTHON) -m pytest services/log-collector/tests/ -v --tb=short
	@echo "$(GREEN)✅ Log Collector tests complete$(NC)"

# Project Simulation Tests
test-project-simulation: ## Test project simulation service
	@echo "$(BLUE)🚀 Testing Project Simulation...$(NC)"
	$(PYTHON) -m pytest services/project-simulation/tests/ -v --tb=short
	@echo "$(GREEN)✅ Project Simulation tests complete$(NC)"

# Combined Service Test Targets
# ============================================================================

test-core-services: test-redis test-orchestrator test-discovery-agent ## Test all core services
	@echo "$(GREEN)✅ Core services tests complete$(NC)"

test-document-services: test-doc-store test-prompt-store test-interpreter ## Test all document-related services
	@echo "$(GREEN)✅ Document services tests complete$(NC)"

test-ai-services: test-llm-gateway test-summarizer-hub test-bedrock-proxy test-github-mcp ## Test all AI/ML services
	@echo "$(GREEN)✅ AI services tests complete$(NC)"

test-analysis-services: test-analysis-service test-code-analyzer test-secure-analyzer test-architecture-digitizer ## Test all analysis services
	@echo "$(GREEN)✅ Analysis services tests complete$(NC)"

test-agent-services: test-memory-agent test-notification-service test-source-agent ## Test all agent services
	@echo "$(GREEN)✅ Agent services tests complete$(NC)"

test-utility-services: test-cli test-mock-data-generator test-log-collector ## Test all utility services
	@echo "$(GREEN)✅ Utility services tests complete$(NC)"

test-frontend-services: test-frontend test-simulation-dashboard test-data-services-dashboard ## Test all frontend/dashboard services
	@echo "$(GREEN)✅ Frontend services tests complete$(NC)"

test-simulation-services: test-project-simulation ## Test all simulation services
	@echo "$(GREEN)✅ Simulation services tests complete$(NC)"

# Comprehensive Test Suites
# ============================================================================

test-all-services: test-core-services test-document-services test-ai-services test-analysis-services test-agent-services test-utility-services test-frontend-services test-simulation-services ## Run all service tests
	@echo "$(GREEN)🎉 All service tests completed!$(NC)"

test-infrastructure: test-redis ## Test infrastructure components only
	@echo "$(GREEN)✅ Infrastructure tests complete$(NC)"

test-business-logic: test-document-services test-ai-services test-analysis-services ## Test business logic services
	@echo "$(GREEN)✅ Business logic tests complete$(NC)"

test-integration-ready: test-core-services test-document-services test-ai-services ## Test services ready for integration
	@echo "$(GREEN)✅ Integration-ready tests complete$(NC)"

# Performance Testing Targets
# ============================================================================

perf-test-project-simulation: ## Run performance tests for project simulation
	@echo "$(BLUE)⚡ Running Project Simulation Performance Tests...$(NC)"
	$(PYTHON) -m pytest services/project-simulation/tests/performance/ -v --tb=short -k "perf"
	@echo "$(GREEN)✅ Performance tests complete$(NC)"

perf-test-analysis-service: ## Run performance tests for analysis service
	@echo "$(BLUE)⚡ Running Analysis Service Performance Tests...$(NC)"
	$(PYTHON) -m pytest services/analysis-service/tests/performance/ -v --tb=short -k "perf"
	@echo "$(GREEN)✅ Performance tests complete$(NC)"

perf-test-all: perf-test-project-simulation perf-test-analysis-service ## Run all performance tests
	@echo "$(GREEN)⚡ All performance tests completed!$(NC)"

# Validation and Health Check Targets
# ============================================================================

validate-service-health: ## Validate all services are healthy
	@echo "$(BLUE)🏥 Validating Service Health...$(NC)"
	@./scripts/validate_service_health.sh
	@echo "$(GREEN)✅ Service health validation complete$(NC)"

validate-docker-config: ## Validate Docker configuration
	@echo "$(BLUE)🐳 Validating Docker Configuration...$(NC)"
	docker-compose -f docker-compose.dev.yml config --quiet
	@echo "$(GREEN)✅ Docker configuration is valid$(NC)"

validate-test-coverage: ## Check test coverage across services
	@echo "$(BLUE)📊 Checking Test Coverage...$(NC)"
	@./scripts/check_test_coverage.sh
	@echo "$(GREEN)✅ Test coverage check complete$(NC)"

validate-all: validate-service-health validate-docker-config validate-test-coverage ## Run all validation checks
	@echo "$(GREEN)✅ All validations passed!$(NC)"

# CI/CD Test Pipeline
# ============================================================================

test-ci-unit: ## CI unit tests (fast)
	@echo "$(BLUE)🚀 Running CI Unit Tests...$(NC)"
	$(PYTHON) -m pytest -x --tb=short -q --disable-warnings \
		--ignore=services/*/tests/integration/ \
		--ignore=services/*/tests/e2e/ \
		--ignore=services/*/tests/performance/
	@echo "$(GREEN)✅ CI unit tests complete$(NC)"

test-ci-integration: ## CI integration tests
	@echo "$(BLUE)🔗 Running CI Integration Tests...$(NC)"
	$(PYTHON) -m pytest -x --tb=short -q --disable-warnings \
		services/*/tests/integration/
	@echo "$(GREEN)✅ CI integration tests complete$(NC)"

test-ci-e2e: ## CI end-to-end tests
	@echo "$(BLUE)🌐 Running CI E2E Tests...$(NC)"
	$(PYTHON) -m pytest -x --tb=short -q --disable-warnings \
		services/*/tests/e2e/
	@echo "$(GREEN)✅ CI E2E tests complete$(NC)"

test-ci-performance: ## CI performance tests
	@echo "$(BLUE)⚡ Running CI Performance Tests...$(NC)"
	$(PYTHON) -m pytest -x --tb=short -q --disable-warnings \
		services/*/tests/performance/
	@echo "$(GREEN)✅ CI performance tests complete$(NC)"

test-ci-full: test-ci-unit test-ci-integration test-ci-e2e test-ci-performance ## Full CI pipeline
	@echo "$(GREEN)🎉 Full CI pipeline completed!$(NC)"

# Code Quality & Linting
# ============================================================================

lint: lint-check ## Run all linting checks (alias for lint-check)

lint-check: ## Run comprehensive linting checks
	@echo "$(BLUE)🔧 Running comprehensive linting checks...$(NC)"
	$(PYTHON) -m pip install -q -r requirements-dev.txt
	@echo "$(YELLOW)🔄 Checking import sorting...$(NC)"
	isort --profile=black --line-length=120 --check-only --diff services/ scripts/ *.py || (echo "$(RED)❌ Import sorting failed$(NC)" && exit 1)
	@echo "$(YELLOW)🎨 Checking code formatting...$(NC)"
	black --line-length=120 --check --diff services/ scripts/ *.py || (echo "$(RED)❌ Code formatting failed$(NC)" && exit 1)
	@echo "$(YELLOW)🐛 Running linting...$(NC)"
	flake8 services/ scripts/ *.py --max-line-length=120 --extend-ignore=E203,W503 --max-complexity=10 --count --statistics || (echo "$(RED)❌ Linting failed$(NC)" && exit 1)
	@echo "$(YELLOW)📝 Checking docstring formatting...$(NC)"
	docformatter --check --pre-summary-newline --recursive services/ scripts/ *.py || (echo "$(RED)❌ Docstring formatting failed$(NC)" && exit 1)
	@echo "$(GREEN)✅ All linting checks passed!$(NC)"

lint-fix: ## Automatically fix linting issues
	@echo "$(BLUE)🔧 Running automatic linting fixes...$(NC)"
	$(PYTHON) -m pip install -q -r requirements-dev.txt
	@echo "$(YELLOW)🔄 Fixing import sorting...$(NC)"
	isort --profile=black --line-length=120 services/ scripts/ *.py
	@echo "$(YELLOW)🎨 Fixing code formatting...$(NC)"
	black --line-length=120 services/ scripts/ *.py
	@echo "$(YELLOW)🐛 Running linting (may show remaining issues)...$(NC)"
	-flake8 services/ scripts/ *.py --max-line-length=120 --extend-ignore=E203,W503 --max-complexity=10 --count --statistics
	@echo "$(YELLOW)📝 Fixing docstring formatting...$(NC)"
	docformatter --in-place --pre-summary-newline --recursive services/ scripts/ *.py
	@echo "$(GREEN)✅ Automatic fixes completed!$(NC)"

lint-imports: ## Check and fix import sorting only
	@echo "$(BLUE)🔄 Checking import sorting...$(NC)"
	$(PYTHON) -m pip install -q isort
	isort --profile=black --line-length=120 --check-only --diff services/ scripts/ *.py || (echo "$(RED)❌ Import sorting issues found$(NC)" && exit 1)
	@echo "$(GREEN)✅ Import sorting is correct!$(NC)"

lint-format: ## Check and fix code formatting only
	@echo "$(BLUE)🎨 Checking code formatting...$(NC)"
	$(PYTHON) -m pip install -q black
	black --line-length=120 --check --diff services/ scripts/ *.py || (echo "$(RED)❌ Code formatting issues found$(NC)" && exit 1)
	@echo "$(GREEN)✅ Code formatting is correct!$(NC)"

lint-security: ## Run security analysis
	@echo "$(BLUE)🔒 Running security analysis...$(NC)"
	$(PYTHON) -m pip install -q bandit[toml]
	bandit -r services/ scripts/ --exclude-dir="*/tests/*,*/test_venv/*" -f json -o security-report.json --exit-zero
	@echo "$(YELLOW)📊 Security report saved to security-report.json$(NC)"
	@echo "$(GREEN)✅ Security analysis completed!$(NC)"

# Legacy/Compatibility Targets
# ============================================================================

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
