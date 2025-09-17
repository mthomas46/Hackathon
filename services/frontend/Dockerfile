# =============================================================================
# Frontend Service Dockerfile
# =============================================================================
# Web UI dashboard and API aggregation service

FROM python:3.12-slim

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="frontend"
LABEL version="1.0.0"
LABEL description="Web UI dashboard and API aggregation service"
LABEL port="5090"
LABEL dependencies="redis,orchestrator,doc_store"
LABEL profile="development"

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

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.base.txt && \
    pip install --no-cache-dir -r shared_requirements.txt

# Copy service code maintaining directory structure
COPY services/frontend/ ./services/frontend/
COPY services/shared/ ./services/shared/
COPY config.yml ./
COPY config/ ./config/

# Set Python path and environment
ENV PYTHONPATH=/app
ENV SERVICE_NAME=frontend
ENV SERVICE_PORT=5090
ENV REDIS_HOST=redis
ENV ENVIRONMENT=development

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5090/health || exit 1

# Expose port
EXPOSE 5090

USER appuser

# Start command - using module path for proper imports
CMD ["python", "services/frontend/start.py"]