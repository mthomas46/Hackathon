# Dockerfile for Confluence Hub Service
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY services/confluence-hub/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY services/shared/ services/shared/

# Copy service code
COPY services/confluence-hub/ services/confluence-hub/

# Copy configuration
COPY config/ config/

# Expose port
EXPOSE 5070

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5070/health || exit 1

# Run the service
CMD ["python", "-m", "uvicorn", "services.confluence-hub.main:app", "--host", "0.0.0.0", "--port", "5070"]