# =============================================================================
# Bedrock Proxy Service Dockerfile
# =============================================================================
# AWS Bedrock AI model proxy with template-based response generation

FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# =============================================================================
# Final stage
# =============================================================================
FROM python:3.12-slim

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="bedrock-proxy"
LABEL version="1.0.0"
LABEL description="AWS Bedrock integration gateway with template-driven responses"
LABEL port="7090"

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 bedrock && \
    chown -R bedrock:bedrock /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/bedrock/.local

# Copy service code
COPY --chown=bedrock:bedrock . .

# Set environment variables
ENV PATH=/home/bedrock/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    SERVICE_API_PORT=7090 \
    BEDROCK_MOCK_MODE=true

# Create logs directory
RUN mkdir -p logs && chown -R bedrock:bedrock logs

# Switch to non-root user
USER bedrock

# Expose service port
EXPOSE 7090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7090/health || exit 1

# Run the service
CMD ["python", "main.py"]
