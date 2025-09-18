# =============================================================================
# Orchestrator Service Dockerfile
# =============================================================================
# Central coordination service for the LLM Documentation Ecosystem
# Manages service discovery, workflow orchestration, and inter-service communication

FROM python:3.12-slim

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="orchestrator"
LABEL version="1.0.0"
LABEL description="Central coordination service for workflow orchestration"
LABEL port="5099"
LABEL dependencies="redis"
LABEL profile="core"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY services/requirements.base.txt ./
COPY services/shared/requirements.txt ./shared_requirements.txt
COPY docker-requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.base.txt && \
    pip install --no-cache-dir -r shared_requirements.txt && \
    pip install --no-cache-dir -r docker-requirements.txt

# Copy service code
COPY services/orchestrator/ ./services/orchestrator/
COPY services/shared/ ./services/shared/
COPY config.yml ./
COPY config/ ./config/

# Set Python path
ENV PYTHONPATH=/app
ENV SERVICE_NAME=orchestrator
ENV SERVICE_PORT=5099
ENV REDIS_HOST=redis
ENV ENVIRONMENT=development

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5099/health || exit 1

# Expose port
EXPOSE 5099

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Start command
CMD ["python", "-m", "services.orchestrator.main"]
