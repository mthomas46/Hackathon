# =============================================================================
# Redis Service Dockerfile
# =============================================================================
# In-memory data store and cache service for the ecosystem

FROM redis:7-alpine

# Metadata
LABEL maintainer="LLM Documentation Ecosystem Team"
LABEL service="redis"
LABEL version="7.0"
LABEL description="Redis in-memory data store and cache"
LABEL port="6379"
LABEL dependencies=""
LABEL profile="core"

# Redis configuration for persistence and performance
COPY --chown=redis:redis redis.conf /etc/redis/redis.conf

# Create data directory
RUN mkdir -p /data && chown redis:redis /data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD redis-cli ping || exit 1

# Expose Redis port
EXPOSE 6379

# Start Redis with configuration
CMD ["redis-server", "/etc/redis/redis.conf"]
