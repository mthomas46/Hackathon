# =============================================================================
# External Service Store Dockerfile
# =============================================================================
# Lightweight service for storing and managing external service configurations

FROM python:3.11-slim

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="external-service-store"
LABEL version="1.0.0"
LABEL description="External service configuration store"
LABEL port="8010"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Create data directory with proper permissions
RUN mkdir -p data && chown -R appuser:appuser data

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8010/health || exit 1

# Run the application
CMD ["python", "main.py"]
