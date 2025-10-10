.PHONY: help install setup start stop restart logs clean test lint format

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	python3.11 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	@echo "✅ Dependencies installed"

setup: ## Setup development environment
	@echo "🔧 Setting up Ecosystem MCP..."
	@cp .env.example .env || true
	@mkdir -p data/{postgresql,redis,chroma_db,backups}
	@echo "✅ Environment setup complete"
	@echo "📝 Please edit .env file with your configuration"

start: ## Start services (PostgreSQL + Redis)
	@echo "🚀 Starting services..."
	docker-compose up -d
	@echo "⏳ Waiting for services to be healthy..."
	@sleep 5
	@echo "✅ Services started"
	@echo "   PostgreSQL: localhost:5432"
	@echo "   Redis:      localhost:6379"

stop: ## Stop services
	@echo "🛑 Stopping services..."
	docker-compose down
	@echo "✅ Services stopped"

restart: stop start ## Restart services

logs: ## View service logs
	docker-compose logs -f

db-migrate: ## Run database migrations
	@echo "📦 Running migrations..."
	./venv/bin/alembic upgrade head
	@echo "✅ Migrations complete"

db-reset: ## Reset database (DANGER: destroys all data)
	@read -p "⚠️  This will destroy all data. Continue? [y/N] " confirm && \
	if [ "$$confirm" = "y" ]; then \
		docker-compose down -v; \
		rm -rf data/postgresql/*; \
		docker-compose up -d postgres; \
		sleep 5; \
		make db-migrate; \
		echo "✅ Database reset complete"; \
	else \
		echo "❌ Cancelled"; \
	fi

ollama-setup: ## Setup Ollama models
	@echo "📥 Pulling Ollama models..."
	ollama pull llama3.1:8b-instruct-q8_0
	ollama pull mistral:7b-instruct-q8_0
	ollama pull nomic-embed-text:latest
	@echo "✅ Ollama models ready"

ingest-quick: ## Run quick ingestion (Mode 1: current .md only)
	@echo "📚 Starting quick ingestion..."
	./venv/bin/python scripts/ingest.py --mode quick
	@echo "✅ Ingestion complete"

ingest-standard: ## Run standard ingestion (Mode 2: current code + .md)
	@echo "📚 Starting standard ingestion..."
	./venv/bin/python scripts/ingest.py --mode standard
	@echo "✅ Ingestion complete"

ingest-historical: ## Run historical ingestion (Mode 3: current + .md history)
	@echo "📚 Starting historical ingestion..."
	./venv/bin/python scripts/ingest.py --mode historical
	@echo "✅ Ingestion complete"

ingest-full: ## Run full ingestion (Mode 4: complete history)
	@read -p "⚠️  Full ingestion can take 1-3 hours. Continue? [y/N] " confirm && \
	if [ "$$confirm" = "y" ]; then \
		./venv/bin/python scripts/ingest.py --mode full; \
		echo "✅ Ingestion complete"; \
	else \
		echo "❌ Cancelled"; \
	fi

run: ## Run MCP server
	@echo "🚀 Starting MCP server..."
	./venv/bin/python src/server.py

test: ## Run tests
	@echo "🧪 Running tests..."
	./venv/bin/pytest tests/ -v
	@echo "✅ Tests complete"

test-cov: ## Run tests with coverage
	@echo "🧪 Running tests with coverage..."
	./venv/bin/pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "✅ Coverage report generated: htmlcov/index.html"

lint: ## Run linters
	@echo "🔍 Running linters..."
	./venv/bin/pylint src/
	./venv/bin/mypy src/
	@echo "✅ Linting complete"

format: ## Format code
	@echo "🎨 Formatting code..."
	./venv/bin/black src/ tests/
	./venv/bin/isort src/ tests/
	@echo "✅ Formatting complete"

clean: ## Clean temporary files
	@echo "🧹 Cleaning..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage .pytest_cache/
	@echo "✅ Cleaned"

backup: ## Backup databases
	@echo "💾 Creating backup..."
	@mkdir -p data/backups
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	docker exec ecosystem-mcp-postgres pg_dump -U ecosystem ecosystem_mcp > data/backups/postgres_$$timestamp.sql; \
	tar -czf data/backups/chroma_$$timestamp.tar.gz data/chroma_db/; \
	echo "✅ Backup complete: data/backups/*_$$timestamp.*"

stats: ## Show ingestion statistics
	@echo "📊 Ecosystem MCP Statistics"
	@./venv/bin/python scripts/stats.py

health: ## Check service health
	@echo "🏥 Checking health..."
	@curl -s http://localhost:8000/health | jq . || echo "❌ MCP server not running"
	@docker exec ecosystem-mcp-postgres pg_isready -U ecosystem && echo "✅ PostgreSQL healthy" || echo "❌ PostgreSQL unhealthy"
	@docker exec ecosystem-mcp-redis redis-cli ping && echo "✅ Redis healthy" || echo "❌ Redis unhealthy"
	@curl -s http://localhost:11434/api/tags | jq -r '.models[].name' && echo "✅ Ollama healthy" || echo "❌ Ollama unhealthy"

dev: setup start ollama-setup ## Full development setup
	@echo "✅ Development environment ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env file with your API keys"
	@echo "  2. Run migrations: make db-migrate"
	@echo "  3. Run ingestion: make ingest-quick"
	@echo "  4. Start server: make run"

.DEFAULT_GOAL := help

