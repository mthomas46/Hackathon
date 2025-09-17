# =============================================================================
# CLI Service Dockerfile
# =============================================================================
# Command line interface for the LLM Documentation Ecosystem

FROM python:3.12-slim

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="cli"
LABEL version="1.0.0"
LABEL description="Command line interface for the LLM Documentation Ecosystem"
LABEL dependencies="prompt-store,orchestrator,analysis-service"
LABEL profile="tooling"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY services/requirements.base.txt ./
COPY services/shared/requirements.txt ./shared_requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.base.txt && \
    pip install --no-cache-dir -r shared_requirements.txt

# Copy service code
COPY services/cli/ ./cli/
COPY services/shared/ ./shared/
COPY config.yml ./
COPY config/ ./config/

# Set Python path and environment
ENV PYTHONPATH=/app
ENV SERVICE_NAME=cli
ENV ENVIRONMENT=development

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

USER appuser

# Keep container running for interactive use
CMD ["sleep", "infinity"]