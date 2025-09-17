# =============================================================================
# Analysis Service Dockerfile
# =============================================================================
# Document analysis and consistency checking service using DDD architecture

FROM python:3.12-slim

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="analysis-service"
LABEL version="1.0.0"
LABEL description="Document analysis and consistency checking service with DDD architecture"
LABEL port="5020"
LABEL dependencies="redis,doc_store"
LABEL profile="core"
LABEL architecture="Domain-Driven Design with CQRS"

# Set working directory
WORKDIR /app

# Install system dependencies for ML libraries
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY services/requirements.base.txt ./
COPY services/shared/requirements.txt ./shared_requirements.txt
COPY docker-requirements.txt ./

# Install Python dependencies (including ML dependencies)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.base.txt && \
    pip install --no-cache-dir -r shared_requirements.txt && \
    pip install --no-cache-dir -r docker-requirements.txt

# Copy service code maintaining directory structure
COPY services/analysis-service/ ./services/analysis_service/
COPY services/shared/ ./services/shared/
COPY config.yml ./
COPY config/ ./config/

# Set Python path and environment
ENV PYTHONPATH=/app
ENV SERVICE_NAME=analysis-service
ENV SERVICE_PORT=5020
ENV REDIS_HOST=redis
ENV ENVIRONMENT=development
ENV DDD_ARCHITECTURE=true
ENV DDD_CONFIG_FILE=config/ddd_config.yaml

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5020/health || exit 1

# Expose port
EXPOSE 5020

USER appuser

# Start command using the wrapper script
CMD ["python", "-m", "services.analysis_service.main_simple"]