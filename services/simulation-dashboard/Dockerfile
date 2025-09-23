# Project Simulation Dashboard - Docker Configuration
# Multi-stage build for optimized production deployment

# Build stage
FROM python:3.13-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY services/simulation-dashboard/requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Production stage
FROM python:3.13-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH" \
    DASHBOARD_ENVIRONMENT=production \
    DASHBOARD_DEBUG=false

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Create application directory first
RUN mkdir -p /app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code (only the simulation-dashboard service)
COPY --chown=appuser:appuser services/simulation-dashboard/ /app/

# Set working directory
WORKDIR /app

# Health check - check if Streamlit app is accessible
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/ || exit 1

# Expose port
EXPOSE 8501

# Labels for better container management
LABEL maintainer="Project Simulation Team" \
      version="1.0.0" \
      description="Project Simulation Dashboard - Interactive frontend for simulation management" \
      org.opencontainers.image.source="https://github.com/your-org/project-simulation-dashboard" \
      org.opencontainers.image.title="Project Simulation Dashboard" \
      org.opencontainers.image.description="Interactive dashboard for managing project simulations"

# Run as non-root user
USER appuser

# Default command
CMD ["/opt/venv/bin/streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
