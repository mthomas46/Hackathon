# =============================================================================
# Summarizer Hub Service Dockerfile
# =============================================================================
# Multi-provider AI summarization service with ensemble capabilities

FROM python:3.12-slim

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="summarizer-hub"
LABEL version="1.0.0"
LABEL description="Multi-provider AI summarization service with ensemble capabilities"
LABEL port="5080"
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

# Install Python dependencies including AWS SDK
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.base.txt && \
    pip install --no-cache-dir -r shared_requirements.txt && \
    pip install --no-cache-dir boto3 botocore

# Copy service code maintaining directory structure
COPY services/summarizer-hub/ ./services/summarizer_hub/
COPY services/shared/ ./services/shared/
COPY config.yml ./
COPY config/ ./config/

# Set Python path and environment
ENV PYTHONPATH=/app
ENV SERVICE_NAME=summarizer-hub
ENV SERVICE_PORT=5080
ENV REDIS_HOST=redis
ENV ENVIRONMENT=development

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5080/health || exit 1

# Expose port
EXPOSE 5080

USER appuser

# Start command - using module path for proper imports
CMD ["python", "-m", "services.summarizer_hub.main"]