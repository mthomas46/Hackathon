# Dockerfile for code-analyzer service
# Multi-stage build for optimized production image
# Last Updated: October 9, 2025

# === Build Stage ===
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (cache layer)
COPY requirements.txt .
COPY requirements-test.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# === Runtime Stage ===
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY domain/ ./domain/
COPY tests/ ./tests/
COPY main.py .
COPY pytest.ini .
COPY README.md .
COPY CONFIG.md .

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Standard labels
LABEL service="code-analyzer" \
      version="1.0.0" \
      description="Static code analysis service" \
      maintainer="Hackathon Team" \
      architecture="DDD" \
      tier="analysis"

# Environment variables
ENV SERVICE_NAME=code-analyzer \
    SERVICE_PORT=6000 \
    LOG_LEVEL=info \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Expose ports
EXPOSE 6000 6001

# Health check (checks if FastAPI is responding)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:6000/health || exit 1

# Run as non-root user for security
RUN useradd -m -u 1000 analyzer && \
    chown -R analyzer:analyzer /app
USER analyzer

# Default command - Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6000", "--log-level", "info"]
