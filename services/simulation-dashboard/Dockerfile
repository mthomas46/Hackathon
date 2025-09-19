# Project Simulation Dashboard - Docker Configuration
# Multi-stage build for optimized production deployment

# Build stage
FROM python:3.13-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Production stage
FROM python:3.13-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DASHBOARD_ENVIRONMENT=production \
    DASHBOARD_DEBUG=false

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Create non-root user
RUN useradd --create-home --shell /bin/bash dashboard && \
    mkdir -p /app && \
    chown dashboard:dashboard /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=dashboard:dashboard . /app/

# Set working directory
WORKDIR /app

# Switch to non-root user
USER dashboard

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/health || exit 1

# Expose port
EXPOSE 8501

# Default command
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# Labels for better container management
LABEL maintainer="Project Simulation Team" \
      version="1.0.0" \
      description="Project Simulation Dashboard - Interactive frontend for simulation management" \
      org.opencontainers.image.source="https://github.com/your-org/project-simulation-dashboard" \
      org.opencontainers.image.title="Project Simulation Dashboard" \
      org.opencontainers.image.description="Interactive dashboard for managing project simulations"
