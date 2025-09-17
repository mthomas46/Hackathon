# =============================================================================
# Architecture Digitizer Service Dockerfile
# =============================================================================
# System architecture analysis and digitization service

FROM python:3.12-slim

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="architecture-digitizer"
LABEL version="1.0.0"
LABEL description="System architecture analysis and digitization service"
LABEL port="5022"
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
    pip install --no-cache-dir -r shared_requirements.txt && \
    pip install --no-cache-dir python-multipart

# Copy service code maintaining directory structure
COPY services/architecture-digitizer/ ./services/architecture_digitizer/
COPY services/shared/ ./services/shared/
COPY config.yml ./
COPY config/ ./config/

# Set Python path and environment
ENV PYTHONPATH=/app
ENV SERVICE_NAME=architecture-digitizer
ENV SERVICE_PORT=5022
ENV REDIS_HOST=redis
ENV ENVIRONMENT=development

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5022/health || exit 1

# Expose port
EXPOSE 5022

USER appuser

# Start command - using module path for proper imports
CMD ["python", "-m", "services.architecture_digitizer.main"]