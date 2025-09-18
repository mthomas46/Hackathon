# =============================================================================
# LLM Gateway Service Dockerfile
# =============================================================================
# Production-ready containerization for the LLM Gateway service
# Provides unified access to all LLM providers with caching and security

FROM python:3.12-slim

# Set metadata
LABEL maintainer="LLM Ecosystem Team"
LABEL service="llm-gateway"
LABEL version="1.0.0"
LABEL description="Unified LLM provider access with security and caching"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    SERVICE_NAME=llm-gateway \
    SERVICE_PORT=5055

# Create non-root user for security
RUN groupadd -r llmgateway && useradd -r -g llmgateway llmgateway

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy shared dependencies first for better caching
COPY services/shared/requirements.txt /app/services/shared/requirements.txt

# Copy service-specific requirements
COPY services/llm-gateway/requirements.txt /app/services/llm-gateway/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r services/shared/requirements.txt && \
    pip install --no-cache-dir -r services/llm-gateway/requirements.txt

# Copy shared modules
COPY services/shared/ /app/services/shared/

# Copy service code
COPY services/llm-gateway/ /app/services/llm-gateway/

# Create necessary directories and set permissions
RUN mkdir -p /app/cache /app/logs /app/data /app/config && \
    echo '{}' > /app/config.yml && \
    chown -R llmgateway:llmgateway /app

# Switch to non-root user
USER llmgateway

# Expose service port
EXPOSE 5055

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5055/health || exit 1

# Set Python path to include the app directory
ENV PYTHONPATH=/app

# Default command
WORKDIR /app
CMD ["python", "services/llm-gateway/main.py"]
