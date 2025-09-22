# =============================================================================
# Bedrock Proxy Service Dockerfile
# =============================================================================
# AWS Bedrock AI model proxy with caching and template management

FROM python:3.12-slim

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="bedrock-proxy"
LABEL version="1.0.0"
LABEL description="AWS Bedrock AI model proxy with caching and template management"
LABEL port="7090"
LABEL dependencies="redis"
LABEL profile="ai_services"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
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
COPY services/bedrock-proxy/ ./services/bedrock-proxy/
COPY services/shared/ ./services/shared/
COPY config.yml ./
COPY config/ ./config/

# Set Python path and environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV SERVICE_NAME=bedrock-proxy
ENV SERVICE_PORT=7090
ENV REDIS_HOST=redis
ENV ENVIRONMENT=development

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7090/health || exit 1

# Expose port
EXPOSE 7090

USER appuser

# Start command - using module path for proper imports
CMD ["python", "-m", "services.bedrock-proxy.main"]