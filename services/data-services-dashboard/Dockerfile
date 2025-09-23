# =============================================================================
# Data Services Dashboard Dockerfile
# =============================================================================
# Unified interface for Memory Agent, Prompt Store, and Document Store services
# =============================================================================

# Build stage
FROM python:3.12-slim as builder

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY services/data-services-dashboard/requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Production stage
FROM python:3.12-slim as production

# Set environment variables for production
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

# Copy application code
COPY --chown=appuser:appuser services/data-services-dashboard/ /app/

# Set working directory
WORKDIR /app

# Health check - check if Streamlit app is accessible
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8502/ || exit 1

# Labels for better container management
LABEL maintainer="LLM Documentation Ecosystem Team" \
      version="1.0.0" \
      description="Data Services Dashboard - Unified interface for data services" \
      org.opencontainers.image.source="https://github.com/your-org/data-services-dashboard" \
      org.opencontainers.image.title="Data Services Dashboard" \
      org.opencontainers.image.description="Unified web interface for browsing and managing Memory Agent, Prompt Store, and Document Store services"

# Run as non-root user
USER appuser

# Expose port
EXPOSE 8502

# Default command
CMD ["/opt/venv/bin/streamlit", "run", "app.py", "--server.port=8502", "--server.address=0.0.0.0"]
