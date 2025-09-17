# =============================================================================
# Interpreter Service Dockerfile
# =============================================================================
# Natural language query interpretation and workflow generation service

FROM python:3.12-slim

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="interpreter"
LABEL version="1.0.0"
LABEL description="Natural language query interpretation and workflow generation service"
LABEL port="5120"
LABEL dependencies="redis"
LABEL profile="ai_services"

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
COPY services/interpreter/ ./services/interpreter/
COPY services/shared/ ./services/shared/
COPY config.yml ./
COPY config/ ./config/

# Set Python path and environment
ENV PYTHONPATH=/app
ENV SERVICE_NAME=interpreter
ENV SERVICE_PORT=5120
ENV REDIS_HOST=redis
ENV ENVIRONMENT=development

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5120/health || exit 1

# Expose port
EXPOSE 5120

USER appuser

# Start command - using module path for proper imports
CMD ["python", "-m", "services.interpreter.main"]