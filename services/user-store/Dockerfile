# =============================================================================
# Standard Service Dockerfile Template
# =============================================================================
# Template for standard services with simple main.py structure

FROM python:3.12-slim

# Metadata - To be customized per service
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="user-store"
LABEL version="1.0.0"
LABEL description="User store service"
LABEL port="5150"
LABEL dependencies="redis"
LABEL profile="core"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY services/requirements.base.txt ./
COPY services/shared/requirements.txt ./shared_requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.base.txt && \
    pip install --no-cache-dir -r shared_requirements.txt

# Copy service code maintaining directory structure
COPY services/user-store/ ./services/user_store/
COPY services/shared/ ./services/shared/
COPY config/config.yml ./config.yml/
COPY config/ ./config/

# Set Python path and environment
ENV PYTHONPATH=/app
ENV SERVICE_NAME=user-store
ENV SERVICE_PORT=5150
ENV REDIS_HOST=redis
ENV ENVIRONMENT=development

# Create data directory and non-root user
RUN mkdir -p /app/data && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod 755 /app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5150/health || exit 1

# Expose port
EXPOSE 5150

USER appuser

# Start command - run main.py directly with absolute path
CMD ["python", "-m", "services.user_store.main"]
