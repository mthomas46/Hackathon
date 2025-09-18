# =============================================================================
# Mock Data Generator Service Dockerfile
# =============================================================================
# Production-ready containerization for the Mock Data Generator service
# Provides LLM-integrated realistic mock data generation for testing

FROM python:3.12-slim

# Set metadata
LABEL maintainer="LLM Ecosystem Team"
LABEL service="mock-data-generator"
LABEL version="1.0.0"
LABEL description="LLM-integrated mock data generation for testing"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    SERVICE_NAME=mock-data-generator \
    SERVICE_PORT=5065

# Create non-root user for security
RUN groupadd -r mockgen && useradd -r -g mockgen mockgen

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy shared dependencies first for better caching
COPY services/shared/requirements.txt /app/services/shared/requirements.txt

# Copy service-specific requirements
COPY services/mock-data-generator/requirements.txt /app/services/mock-data-generator/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r services/shared/requirements.txt && \
    pip install --no-cache-dir -r services/mock-data-generator/requirements.txt

# Copy shared modules
COPY services/shared/ /app/services/shared/

# Copy service code
COPY services/mock-data-generator/ /app/services/mock-data-generator/

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/logs /app/config && \
    echo '{}' > /app/config.yml && \
    chown -R mockgen:mockgen /app

# Switch to non-root user
USER mockgen

# Expose service port
EXPOSE 5065

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5065/health || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "services.mock_data_generator.main:app", "--host", "0.0.0.0", "--port", "5065"]
