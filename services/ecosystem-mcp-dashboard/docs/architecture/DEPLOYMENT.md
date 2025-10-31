# Ecosystem MCP Dashboard - Deployment Guide

## Quick Start

### 1. Deploy the Full Stack

```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp

# Start all services (Postgres, Redis, Ollama, Ecosystem MCP, Dashboard)
docker-compose up -d

# Or build from scratch
docker-compose up --build -d
```

### 2. Access the Dashboard

Open your browser and navigate to:
```
http://localhost:8501
```

### 3. Verify Services

Check that all services are running:
```bash
docker-compose ps
```

Expected output:
```
NAME                        STATUS    PORTS
ecosystem-mcp-dashboard     Up        0.0.0.0:8501->8501/tcp
ecosystem-mcp-ollama        Up        0.0.0.0:11434->11434/tcp
ecosystem-mcp-postgres      Up        0.0.0.0:5432->5432/tcp
ecosystem-mcp-redis         Up        0.0.0.0:6379->6379/tcp
ecosystem-mcp-service       Up        0.0.0.0:8000->8000/tcp
```

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│   Ecosystem MCP Dashboard (Port 8501)       │
│         Streamlit Frontend                  │
└─────────────────┬───────────────────────────┘
                  │ HTTP/REST
                  ▼
┌─────────────────────────────────────────────┐
│   Ecosystem MCP API (Port 8000)             │
│         FastAPI + RAG System                │
└─┬──────────┬──────────┬─────────────────────┘
  │          │          │
  ▼          ▼          ▼
┌────────┐ ┌───────┐ ┌──────────┐
│Postgres│ │ Redis │ │  Ollama  │
│  5432  │ │  6379 │ │  11434   │
└────────┘ └───────┘ └──────────┘
```

## Testing

### 1. Health Check

Test the API:
```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-12T...",
  "components": { ... }
}
```

### 2. Dashboard Connection Test

1. Go to http://localhost:8501
2. Navigate to **🔧 Settings**
3. Click **🧪 Test Connection**
4. Should see: ✅ Connection successful!

### 3. Test RAG Query

1. Navigate to **🤖 RAG Query**
2. Enter a question: "How does the caching system work?"
3. Click **🚀 Ask Question**
4. Should receive an answer with sources

### 4. Test Document Browsing

1. Navigate to **📚 Documents**
2. Tab: **📋 Browse Documents**
3. Click **🔍 Search**
4. Should see list of ingested documents

### 5. Test Cache Monitoring

1. Navigate to **⚡ Cache Performance**
2. Should see cache statistics
3. Pie chart showing hits vs misses

### 6. Test Health Monitoring

1. Navigate to **🏥 Health & Infrastructure**
2. Should see all components as "healthy"
3. Circuit breakers should show "CLOSED" state

## Troubleshooting

### Dashboard Cannot Connect to API

**Symptom**: "Cannot connect to service" error

**Solutions**:
1. Verify ecosystem-mcp service is running:
   ```bash
   docker logs ecosystem-mcp-service
   ```

2. Check network connectivity:
   ```bash
   docker network inspect ecosystem-mcp
   ```

3. Verify API is accessible:
   ```bash
   docker exec ecosystem-mcp-dashboard curl http://ecosystem-mcp:8000/health
   ```

### Dashboard Not Loading

**Symptom**: Browser shows loading spinner indefinitely

**Solutions**:
1. Check dashboard logs:
   ```bash
   docker logs ecosystem-mcp-dashboard
   ```

2. Verify port 8501 is not in use:
   ```bash
   lsof -i :8501
   ```

3. Restart dashboard:
   ```bash
   docker-compose restart ecosystem-mcp-dashboard
   ```

### API Timeouts

**Symptom**: Requests timeout after 10-30 seconds

**Solutions**:
1. Check Ollama is responding:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. Increase memory for Ollama:
   Edit `docker-compose.yml`:
   ```yaml
   ollama:
     mem_limit: 30g  # Increase if needed
   ```

3. Check ChromaDB initialization:
   ```bash
   docker exec ecosystem-mcp-service ls -la /app/data/chroma_db
   ```

### Database Connection Errors

**Symptom**: "database does not exist" or "connection refused"

**Solutions**:
1. Check PostgreSQL is healthy:
   ```bash
   docker exec ecosystem-mcp-postgres pg_isready -U ecosystem
   ```

2. Verify database exists:
   ```bash
   docker exec ecosystem-mcp-postgres psql -U ecosystem -l
   ```

3. Create database if missing:
   ```bash
   docker exec ecosystem-mcp-postgres psql -U ecosystem -c "CREATE DATABASE ecosystem_mcp;"
   ```

## Configuration

### Environment Variables

Dashboard (`docker-compose.yml`):
```yaml
environment:
  - API_BASE_URL=http://ecosystem-mcp:8000  # API endpoint
```

Ecosystem MCP Service:
```yaml
environment:
  DATABASE_URL: postgresql://ecosystem:ecosystem_password@postgres:5432/ecosystem_mcp
  REDIS_URL: redis://redis:6379/0
  OLLAMA_BASE_URL: http://ollama:11434
  MODEL_STRATEGY: ollama-only
  ENABLE_CACHE: "true"
  RATE_LIMIT_ENABLED: "false"  # For development
```

### Ports

- **8501** - Dashboard (Streamlit)
- **8000** - Ecosystem MCP API
- **9090** - Prometheus metrics
- **5432** - PostgreSQL
- **6379** - Redis
- **11434** - Ollama

## Performance Tuning

### For Local Development

```yaml
# In docker-compose.yml
ecosystem-mcp:
  environment:
    RATE_LIMIT_ENABLED: "false"  # Disable rate limiting
    CACHE_TTL: 3600             # 1 hour cache
    ENABLE_CACHE: "true"         # Enable all caching
```

### For Production

```yaml
ecosystem-mcp:
  environment:
    RATE_LIMIT_ENABLED: "true"   # Enable rate limiting
    CACHE_TTL: 7200              # 2 hour cache
    ENABLE_CACHE: "true"
    # Add authentication
```

## Backup & Maintenance

### Backup Data Volumes

```bash
# Backup PostgreSQL
docker exec ecosystem-mcp-postgres pg_dump -U ecosystem ecosystem_mcp > backup.sql

# Backup ChromaDB
tar -czf chroma_backup.tar.gz ./data/chroma_db/

# Backup Redis
docker exec ecosystem-mcp-redis redis-cli BGSAVE
```

### Update Services

```bash
# Pull latest changes
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp
git pull

# Rebuild and restart
docker-compose up --build -d
```

### Clear All Data

```bash
# Stop services
docker-compose down

# Remove volumes
rm -rf data/postgresql data/redis data/chroma_db

# Restart fresh
docker-compose up -d
```

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f ecosystem-mcp-dashboard
docker-compose logs -f ecosystem-mcp

# Last 100 lines
docker-compose logs --tail=100 ecosystem-mcp
```

### Resource Usage

```bash
# Container stats
docker stats

# Specific containers
docker stats ecosystem-mcp-service ecosystem-mcp-dashboard
```

### Metrics

Access Prometheus metrics:
```bash
curl http://localhost:9090/metrics
```

Or view in dashboard:
1. Navigate to **📊 Metrics & Analytics**
2. View system-wide performance data

## Security

### Production Recommendations

1. **Add Authentication**:
   - Implement API key authentication
   - Use JWT tokens
   - Add Streamlit authentication

2. **Use HTTPS**:
   - Add reverse proxy (nginx)
   - Configure SSL certificates
   - Enforce HTTPS redirect

3. **Network Isolation**:
   - Use internal networks
   - Expose only necessary ports
   - Implement firewall rules

4. **Secrets Management**:
   - Use Docker secrets
   - Environment variable encryption
   - Rotate credentials regularly

## Integration with Main Docker Compose

To integrate with the main `docker-compose.dev.yml`:

1. Add to the main compose file:
   ```yaml
   ecosystem-mcp-dashboard:
     build: ./services/ecosystem-mcp-dashboard
     container_name: hackathon-ecosystem-mcp-dashboard
     ports:
       - "8501:8501"
     environment:
       - API_BASE_URL=http://ecosystem-mcp:8000
     networks:
       - hackathon_default
     profiles:
       - all
       - ecosystem-mcp
   ```

2. Ensure ecosystem-mcp service is also in main compose

3. Use same network for inter-service communication

## Next Steps

1. ✅ Deploy and test the dashboard
2. ✅ Ingest your first documents via dashboard
3. ✅ Try RAG queries
4. ✅ Monitor cache performance
5. ✅ Explore health monitoring
6. 🔄 Customize dashboard (themes, pages)
7. 🔄 Add authentication (if needed)
8. 🔄 Set up monitoring alerts

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Verify health: `/health` endpoint
3. Test connectivity: Settings page
4. Review documentation in README.md

For questions or bugs, file an issue on GitHub.

