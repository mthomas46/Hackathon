# Multi-stage Dockerfile for MCP Provisioner Service
# Follows ecosystem standards for Python services

# ==============================================================================
# Stage 1: Base
# ==============================================================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ==============================================================================
# Stage 2: Dependencies
# ==============================================================================
FROM base as dependencies

# Copy requirements
COPY services/mcp-provisioner/requirements.txt /app/services/mcp-provisioner/

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/services/mcp-provisioner/requirements.txt

# ==============================================================================
# Stage 3: Production
# ==============================================================================
FROM base as production

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY services/mcp-provisioner /app/services/mcp-provisioner
COPY services/shared /app/services/shared

# Set Python path
ENV PYTHONPATH=/app

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 5400

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD curl -f http://localhost:5400/api/v1/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "services.mcp_provisioner.main:app", "--host", "0.0.0.0", "--port", "5400"]

