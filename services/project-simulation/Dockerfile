# =============================================================================
# Standard Service Dockerfile Template
# =============================================================================
# Template for standard services with simple main.py structure

FROM python:3.12-slim

# Metadata - To be customized per service
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="project-simulation"
LABEL version="1.0.0"
LABEL description="Project Simulation service"
LABEL port="5000"
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
COPY services/project-simulation/ ./services/project-simulation/
COPY services/shared/ ./services/shared/
COPY config/config.yml ./config.yml/
COPY config/ ./config/

# Set Python path and environment
ENV PYTHONPATH=/app
ENV project-simulation=project-simulation
ENV 5000=5000
ENV REDIS_HOST=redis
ENV ENVIRONMENT=development

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Expose port
EXPOSE 5000

USER appuser

# Start command - using module path for proper imports
CMD ["python", "-m", "services.project-simulation.main"]
