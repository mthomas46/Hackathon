.PHONY: help deploy start stop restart rebuild teardown status validate clean test logs

# Default target
help:
	@echo ""
	@echo "════════════════════════════════════════════════════════════════"
	@echo "  ECOSYSTEM MCP - Deployment Commands"
	@echo "════════════════════════════════════════════════════════════════"
	@echo ""
	@echo "  Deployment:"
	@echo "    make deploy          - Full deployment (validation + start)"
	@echo "    make start           - Start services only"
	@echo "    make stop            - Stop services gracefully"
	@echo "    make restart         - Restart services"
	@echo "    make rebuild         - Rebuild and redeploy"
	@echo "    make rebuild-clean   - Clean rebuild (removes cache)"
	@echo ""
	@echo "  Management:"
	@echo "    make status          - Show deployment status"
	@echo "    make validate        - Run system validation only"
	@echo "    make teardown        - Stop everything"
	@echo "    make teardown-clean  - Stop and remove all data"
	@echo ""
	@echo "  Development:"
	@echo "    make logs            - Show server logs"
	@echo "    make test            - Run tests"
	@echo "    make clean           - Clean build artifacts"
	@echo "    make health          - Check service health"
	@echo ""
	@echo "════════════════════════════════════════════════════════════════"
	@echo ""

# Deployment targets
deploy:
	@python3 deployment_manager.py deploy

deploy-quick:
	@python3 deployment_manager.py deploy --skip-validation

start:
	@python3 deployment_manager.py start

stop:
	@python3 deployment_manager.py stop

stop-force:
	@python3 deployment_manager.py stop --force

restart:
	@python3 deployment_manager.py restart

rebuild:
	@python3 deployment_manager.py rebuild

rebuild-clean:
	@python3 deployment_manager.py rebuild --clean

# Management targets
status:
	@python3 deployment_manager.py status

validate:
	@source venv/bin/activate && python -m src.utils.system_validator

teardown:
	@python3 deployment_manager.py teardown

teardown-clean:
	@python3 deployment_manager.py teardown --remove-data

# Development targets
logs:
	@if [ -f server.log ]; then \
		tail -f server.log; \
	else \
		echo "❌ No server.log found. Service may not be running."; \
	fi

logs-all:
	@if [ -f server.log ]; then \
		cat server.log; \
	else \
		echo "❌ No server.log found"; \
	fi

test:
	@echo "🧪 Running tests..."
	@source venv/bin/activate && pytest tests/ -v --cov=src --cov-report=term-missing

test-quick:
	@source venv/bin/activate && pytest tests/ -x

clean:
	@echo "🧹 Cleaning build artifacts..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Clean complete"

health:
	@echo "🏥 Checking service health..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "❌ Service not responding"

# API interaction targets
api-docs:
	@echo "📖 Opening API documentation..."
	@open http://localhost:8000/docs || echo "Visit: http://localhost:8000/docs"

api-health:
	@curl -s http://localhost:8000/health | python -m json.tool

api-about:
	@curl -s http://localhost:8000/about-me | python -m json.tool

api-endpoints:
	@curl -s http://localhost:8000/endpoints | python -m json.tool

# Docker targets
docker-up:
	@echo "🐳 Starting Docker services..."
	@docker-compose up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo "✅ Docker services started"

docker-down:
	@echo "🐳 Stopping Docker services..."
	@docker-compose down
	@echo "✅ Docker services stopped"

docker-ps:
	@docker-compose ps

docker-logs:
	@docker-compose logs -f

# Development setup
setup:
	@echo "🔧 Setting up development environment..."
	@python3 -m venv venv
	@source venv/bin/activate && pip install -U pip setuptools wheel
	@source venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Setup complete"
	@echo ""
	@echo "Run 'make deploy' to start the service"

# Quick commands
up: deploy
down: stop
ps: status
