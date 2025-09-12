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

# Install CLI-specific packages
RUN pip install --no-cache-dir rich click

# Copy shared modules
COPY services/shared /app/services/shared

# Copy service code
COPY services/cli /app/services/cli

# Set environment variables
ENV PYTHONPATH=/app

# Default command (can be overridden)
CMD ["python", "services/cli/main.py", "interactive"]
