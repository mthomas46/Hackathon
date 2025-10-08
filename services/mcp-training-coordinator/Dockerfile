# Multi-stage Dockerfile for Training Coordinator Service
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ./services/mcp-training-coordinator/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./services/mcp-training-coordinator /app/services/training_coordinator
COPY ./services/shared /app/services/shared

# Set Python path
ENV PYTHONPATH=/app

# Set working directory to app root
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 coordinator && chown -R coordinator:coordinator /app
USER coordinator

# Expose port
EXPOSE 5600

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5600/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "services.training_coordinator.main:app", "--host", "0.0.0.0", "--port", "5600"]

