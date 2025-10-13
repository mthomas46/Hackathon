# Ecosystem MCP Service Dockerfile
# Using bookworm (Debian 12) for sqlite3 >= 3.35.0 (required by ChromaDB)
FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data/chroma_db /app/data/backups

# Expose ports
EXPOSE 8000
EXPOSE 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the application
CMD ["uvicorn", "src.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

