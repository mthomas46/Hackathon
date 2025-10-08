# Multi-stage Dockerfile for MCP Registry Service
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    libsnappy-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ./services/mcp-registry/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./services/mcp-registry /app/services/mcp_registry
COPY ./services/shared /app/services/shared

# Set Python path
ENV PYTHONPATH=/app

# Set working directory to app root
WORKDIR /app

# Create data directory for local storage
RUN mkdir -p /app/data/mcp-packages

# Create non-root user
RUN useradd -m -u 1000 registry && chown -R registry:registry /app
USER registry

# Expose port
EXPOSE 8102

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8102/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "services.mcp_registry.main:app", "--host", "0.0.0.0", "--port", "8102"]

