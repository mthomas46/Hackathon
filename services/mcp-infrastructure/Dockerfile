# MCP Infrastructure Service - Multi-stage Dockerfile
# 
# Build optimized Docker image for MCP Infrastructure Service
# Following ecosystem standards for Python services

# Stage 1: Base
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Development
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    isort \
    mypy \
    pylint

# Copy service code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5500

# Development command (with reload)
CMD ["uvicorn", "services.mcp_infrastructure.main:app", "--host", "0.0.0.0", "--port", "5500", "--reload"]

# Stage 3: Production
FROM base as production

# Copy only necessary files
COPY services/mcp-infrastructure /app/services/mcp-infrastructure
COPY services/shared /app/services/shared

# Set Python path
ENV PYTHONPATH=/app

# Create non-root user
RUN useradd -m -u 1000 mcpinfra && \
    chown -R mcpinfra:mcpinfra /app

USER mcpinfra

# Expose port
EXPOSE 5500

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:5500/api/v1/health')"

# Production command
CMD ["uvicorn", "services.mcp_infrastructure.main:app", "--host", "0.0.0.0", "--port", "5500", "--workers", "4"]

