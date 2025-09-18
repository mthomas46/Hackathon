# ============================================================================
# Project Simulation Service - Multi-Stage Docker Build
# ============================================================================
# This Dockerfile implements a multi-stage build for the project-simulation service
# with security hardening, performance optimization, and production readiness.
# ============================================================================

# ============================================================================
# Stage 1: Builder Stage - Dependencies and Compilation
# ============================================================================
FROM python:3.11-slim as builder

# Security: Update packages and install security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        libffi-dev \
        libssl-dev \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r simulation && useradd -r -g simulation simulation

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Security Scanner Stage
# ============================================================================
FROM builder as security-scan

# Install security scanning tools
RUN apt-get update && apt-get install -y --no-install-recommends \
        clamav \
        clamav-daemon \
        && rm -rf /var/lib/apt/lists/*

# Update virus definitions
RUN freshclam

# Copy application code for scanning
COPY . .

# Scan for malware (optional - can be enabled in CI/CD)
# RUN clamscan --infected --recursive /app || true

# ============================================================================
# Stage 3: Runtime Stage - Production Optimized
# ============================================================================
FROM python:3.11-slim as runtime

# Install runtime dependencies only
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        curl \
        procps \
        net-tools \
        && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r simulation && useradd -r -g simulation simulation

# Create necessary directories with proper permissions
RUN mkdir -p /app /app/logs /app/data && \
    chown -R simulation:simulation /app

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=simulation:simulation . .

# Create logs directory and set permissions
RUN mkdir -p logs && chown -R simulation:simulation logs

# Security: Remove unnecessary files and set proper permissions
RUN find . -type f -name "*.pyc" -delete && \
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Set proper permissions on scripts
RUN chmod +x main.py && \
    chmod 755 .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5075/health || exit 1

# Switch to non-root user
USER simulation

# Expose port
EXPOSE 5075

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    SERVICE_NAME=project-simulation

# Labels for container metadata
LABEL maintainer="Hackathon Team" \
      service="project-simulation" \
      version="1.0.0" \
      description="AI-powered project simulation and ecosystem demonstration service" \
      org.opencontainers.image.title="Project Simulation Service" \
      org.opencontainers.image.description="AI-powered project simulation and ecosystem demonstration service" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Hackathon Team"

# Default command
CMD ["python", "main.py"]

# ============================================================================
# Stage 4: Development Stage - For Local Development
# ============================================================================
FROM builder as development

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        vim \
        htop \
        net-tools \
        curl \
        wget \
        && rm -rf /var/lib/apt/lists/*

# Create development user
RUN groupadd -r dev && useradd -r -g dev devuser

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs && chown -R devuser:dev devuser

# Switch to development user
USER devuser

# Expose port
EXPOSE 5075

# Environment variables for development
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENVIRONMENT=development \
    SERVICE_NAME=project-simulation-dev

# Health check for development
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5075/health || exit 1

# Development command with reload
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5075", "--reload", "--log-level", "info"]

# ============================================================================
# Stage 5: Testing Stage - For CI/CD Pipelines
# ============================================================================
FROM builder as testing

# Install testing dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        && rm -rf /var/lib/apt/lists/*

# Install additional testing dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    pytest-mock \
    pytest-xdist \
    coverage \
    black \
    isort \
    flake8 \
    mypy

# Create testing user
RUN groupadd -r test && useradd -r -g test testuser

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Switch to testing user
USER testuser

# Environment variables for testing
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENVIRONMENT=testing \
    SERVICE_NAME=project-simulation-test

# Default testing command
CMD ["pytest", "--cov=.", "--cov-report=html", "--cov-report=term", "tests/"]

# ============================================================================
# Default target: Production Runtime
# ============================================================================
FROM runtime
