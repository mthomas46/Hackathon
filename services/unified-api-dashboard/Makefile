.PHONY: help install run test clean docker-build docker-run

# Default target
help:
	@echo "Available commands:"
	@echo "  install       Install dependencies"
	@echo "  run           Run the Streamlit dashboard"
	@echo "  run-api       Run the FastAPI server"
	@echo "  test          Run tests"
	@echo "  clean         Clean up generated files"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-run    Run Docker container"
	@echo "  lint          Run code linting"
	@echo "  format        Format code"

# Install dependencies
install:
	pip install -r requirements.txt

# Run the Streamlit dashboard
run:
	streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Run the FastAPI server
run-api:
	uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Run tests
test:
	pytest tests/ -v --cov=. --cov-report=html

# Clean up generated files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/

# Docker commands
docker-build:
	docker build -t unified-api-dashboard .

docker-run:
	docker run -p 8501:8501 -p 8000:8000 unified-api-dashboard

# Code quality
lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:
	black . --line-length 100
	isort .
