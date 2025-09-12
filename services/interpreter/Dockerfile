FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/requirements.base.txt .
COPY services/shared/requirements.txt ./

RUN pip install --no-cache-dir -r requirements.base.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY services/shared /app/services/shared

# Copy service code
COPY services/interpreter /app/services/interpreter

# Set environment variables
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5120

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5120/health')"

# Run service
CMD ["python", "services/interpreter/main.py"]
