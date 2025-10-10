# =============================================================================
# Data Services Dashboard Dockerfile
# =============================================================================
# Hybrid Architecture: Streamlit UI (8501) + FastAPI REST API (8080)

FROM python:3.12-slim

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="data-services-dashboard"
LABEL version="1.0.0"
LABEL description="Real-time monitoring dashboard for datastore operations"
LABEL architecture="hybrid"
LABEL ui_port="8501"
LABEL api_port="8080"
LABEL dependencies="log-collector"
LABEL profile="production"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code (modular structure)
COPY api/ ./api/
COPY data/ ./data/
COPY metrics/ ./metrics/
COPY visualization/ ./visualization/
COPY utils/ ./utils/
COPY app.py .
COPY config.py .

# Copy documentation
COPY README.md .
COPY CONFIG.md .
COPY DEPLOYMENT_GUIDE.md .

# Create necessary directories
RUN mkdir -p /app/logs

# Streamlit configuration
RUN mkdir -p /root/.streamlit
RUN echo '\
[server]\n\
port = 8501\n\
address = 0.0.0.0\n\
enableCORS = false\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
' > /root/.streamlit/config.toml

# Set Python path and environment variables
ENV PYTHONPATH=/app
ENV DASHBOARD_SERVICE_NAME=data-services-dashboard
ENV DASHBOARD_SERVICE_VERSION=1.0.0
ENV DASHBOARD_UI_PORT=8501
ENV DASHBOARD_API_PORT=8080
ENV DASHBOARD_LOG_COLLECTOR_URL=http://log-collector:8104
ENV DASHBOARD_ENVIRONMENT=production
ENV DASHBOARD_DEBUG=false

# Create non-root user for security
RUN useradd -m -u 1000 dashboard && chown -R dashboard:dashboard /app
USER dashboard

# Health check (checks FastAPI API)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose ports
EXPOSE 8501  # Streamlit UI
EXPOSE 8080  # FastAPI REST API

# Start command - Run Streamlit (which also starts FastAPI in background thread)
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]

