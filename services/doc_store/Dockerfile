# =============================================================================
# Doc Store Service Dockerfile
# =============================================================================
# Document storage and retrieval service with advanced features

FROM python:3.12-slim

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="doc_store"
LABEL version="2.0.0"
LABEL description="Document storage and analysis service with advanced features"
LABEL port="5010"
LABEL external_port="5087"
LABEL dependencies="redis"
LABEL profile="core"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY services/requirements.base.txt ./
COPY services/shared/requirements.txt ./shared_requirements.txt
COPY docker-requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.base.txt && \
    pip install --no-cache-dir -r shared_requirements.txt && \
    pip install --no-cache-dir -r docker-requirements.txt

# Copy service code
COPY services/doc_store/ ./services/doc_store/
COPY services/shared/ ./services/shared/
COPY config.yml ./
COPY config/ ./config/

# Set Python path and environment
ENV PYTHONPATH=/app
ENV SERVICE_NAME=doc_store
ENV SERVICE_PORT=5010
ENV REDIS_HOST=redis
ENV ENVIRONMENT=development
ENV DOCSTORE_PORT=5010

# Create data directory and set permissions
RUN mkdir -p /app/data && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5010/health || exit 1

# Expose port
EXPOSE 5010

USER appuser

# Start command
CMD ["python", "-m", "services.doc_store.main"]
