# Multi-stage Dockerfile for MCP Gateway Service
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ./services/mcp-gateway/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./services/mcp-gateway /app/services/mcp_gateway
COPY ./services/shared /app/services/shared

# Set Python path
ENV PYTHONPATH=/app

# Set working directory to app root
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 gateway && chown -R gateway:gateway /app
USER gateway

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "services.mcp_gateway.main:app", "--host", "0.0.0.0", "--port", "8001"]

