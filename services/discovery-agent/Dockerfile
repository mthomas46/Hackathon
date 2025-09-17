# =============================================================================
# Discovery Agent Service Dockerfile
# =============================================================================
# Service endpoint discovery and OpenAPI spec analysis service

FROM python:3.12-slim

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="discovery-agent"
LABEL version="1.0.0"
LABEL description="Service endpoint discovery and OpenAPI spec analysis service"
LABEL port="5040"
LABEL dependencies="redis"
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

# Skip copying service code - rely on volume mounts for development
# COPY services/discovery-agent/ ./services/discovery_agent/
# COPY services/shared/ ./services/shared/
# COPY config.yml ./
# COPY config/ ./config/

# Set Python path and environment
ENV PYTHONPATH=/app
ENV SERVICE_NAME=discovery-agent
ENV SERVICE_PORT=5040
ENV REDIS_HOST=redis
ENV ENVIRONMENT=development

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5040/health || exit 1

# Expose port
EXPOSE 5040

USER appuser

# Start command - using module path for proper imports
CMD ["python", "-m", "services.discovery_agent.main"]