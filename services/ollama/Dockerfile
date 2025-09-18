# =============================================================================
# Ollama Service Dockerfile
# =============================================================================
# Local LLM inference server for the ecosystem

FROM ollama/ollama:latest

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="ollama"
LABEL version="latest"
LABEL description="Ollama local LLM inference server"
LABEL port="11434"
LABEL dependencies=""
LABEL profile="ai_services"

# Install curl for health checks
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create model cache directory
RUN mkdir -p /root/.ollama

# Health check - Ollama has its own health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:11434/api/tags || exit 1

# Expose Ollama port
EXPOSE 11434

# Override the default entrypoint and start Ollama server
ENTRYPOINT []
CMD ["ollama", "serve"]
