# =============================================================================
# Prompt Store Service Dockerfile
# =============================================================================
# AI analytics and prompt optimization service with A/B testing

FROM python:3.12-slim

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="prompt_store"
LABEL version="1.0.0"
LABEL description="AI analytics and prompt optimization service with A/B testing"
LABEL port="5110"
LABEL dependencies="redis"
LABEL profile="ai_services"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY services/requirements.base.txt ./
COPY services/shared/requirements.txt ./shared_requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.base.txt && \
    pip install --no-cache-dir -r shared_requirements.txt && \
    pip install --no-cache-dir aiohttp

# Copy service code maintaining directory structure
COPY services/prompt_store/ ./services/prompt_store/
COPY services/shared/ ./services/shared/
COPY config.yml ./
COPY config/ ./config/

# Set Python path and environment
ENV PYTHONPATH=/app
ENV SERVICE_NAME=prompt_store
ENV SERVICE_PORT=5110
ENV REDIS_HOST=redis
ENV ENVIRONMENT=development

# Create data directory and non-root user
RUN mkdir -p /app/data && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5110/health || exit 1

# Expose port
EXPOSE 5110

USER appuser

# Start command - using module path for proper imports
CMD ["python", "-m", "services.prompt_store.main"]
