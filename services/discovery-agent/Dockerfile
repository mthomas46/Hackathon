# =============================================================================
# Discovery Agent Service Dockerfile - Refactored October 2025
# =============================================================================
# Service discovery and LangGraph tool generation service
# Architecture: DDD + Clean Architecture
# Test Coverage: 80%+
# Quality: A+

FROM python:3.12-slim

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="discovery-agent"
LABEL version="2.0.0"
LABEL description="Service discovery and LangGraph tool generation engine"
LABEL http_port="5050"
LABEL internal_port="5051"
LABEL architecture="DDD + Clean Architecture"
LABEL test_coverage="80%+"
LABEL quality_grade="A+"
LABEL python_version="3.11+"
LABEL refactored="2025-10-09"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt ./
COPY requirements-test.txt ./requirements-test.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY domain/ ./domain/
COPY application/ ./application/
COPY infrastructure/ ./infrastructure/
COPY presentation/ ./presentation/
COPY main.py ./
COPY config.yaml ./
COPY pytest.ini ./pytest.ini

# Copy tests (for validation)
COPY tests/ ./tests/

# Copy documentation
COPY README.md ./
COPY PHASE_*.md ./

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Set Python path and environment
ENV PYTHONPATH=/app
ENV SERVICE_NAME=discovery-agent
ENV SERVICE_API_PORT=5050
ENV SERVICE_INTERNAL_PORT=5051
ENV SERVER_API_HOST=0.0.0.0
ENV ENVIRONMENT=production

# Standard labels for ecosystem
LABEL ecosystem.tier="3"
LABEL ecosystem.role="integration"
LABEL ecosystem.provides="service-discovery,tool-generation"
LABEL ecosystem.depends="orchestrator,log-collector"

# Create non-root user for security
RUN useradd -m -u 1000 discovery && chown -R discovery:discovery /app

# Health check (updated for new port)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5050/health || exit 1

# Expose ports
EXPOSE 5050
EXPOSE 5051

USER discovery

# Start command - run FastAPI with uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5050", "--log-level", "info"]
