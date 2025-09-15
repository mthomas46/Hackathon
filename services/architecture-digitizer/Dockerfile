# Architecture Digitizer Service Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.base.txt ./
RUN pip install --no-cache-dir -r requirements.base.txt

# Copy service code
COPY services/architecture-digitizer/ ./services/architecture-digitizer/
COPY services/shared/ ./services/shared/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 5105

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5105/health || exit 1

# Run the service
CMD ["python", "services/architecture-digitizer/main.py"]
