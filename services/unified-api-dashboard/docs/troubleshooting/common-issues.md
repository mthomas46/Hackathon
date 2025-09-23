# 🔧 Troubleshooting Guide

## Common Issues and Solutions

This guide covers frequently encountered issues with the Unified API Dashboard and their resolutions.

## Installation & Setup Issues

### Docker Build Failures

**Issue:** `docker build` fails with dependency errors

**Symptoms:**
```
ERROR: Could not install packages due to an environment error
```

**Solutions:**

1. **Clear Docker cache:**
```bash
docker system prune -a
docker build --no-cache .
```

2. **Check Python version compatibility:**
```dockerfile
FROM python:3.11-slim  # Use specific version instead of 'latest'
```

3. **Fix pip cache issues:**
```bash
pip install --no-cache-dir -r requirements.txt
```

4. **Check network connectivity:**
```bash
docker build --network host .
```

### Port Conflicts

**Issue:** Port 8000 already in use

**Symptoms:**
```
ERROR: Port already in use: 8000
```

**Solutions:**

1. **Find process using port:**
```bash
# Linux/Mac
lsof -i :8000
netstat -tulpn | grep :8000

# Windows
netstat -ano | findstr :8000
```

2. **Change dashboard port:**
```yaml
# docker-compose.yml
services:
  dashboard:
    environment:
      - SERVICE_PORT=8001
    ports:
      - "8001:8001"
```

3. **Use different host port:**
```yaml
ports:
  - "127.0.0.1:8001:8000"  # Host:8001 -> Container:8000
```

### Redis Connection Issues

**Issue:** Dashboard can't connect to Redis

**Symptoms:**
```
ConnectionError: Error 111 connecting to redis:6379. Connection refused.
```

**Solutions:**

1. **Check Redis container status:**
```bash
docker-compose ps redis
docker logs <redis-container-id>
```

2. **Verify network connectivity:**
```bash
docker exec -it <dashboard-container> redis-cli -h redis ping
```

3. **Check Redis configuration:**
```yaml
services:
  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
```

4. **Fix environment variables:**
```yaml
environment:
  - REDIS_HOST=redis
  - REDIS_PORT=6379
  - REDIS_PASSWORD=${REDIS_PASSWORD}
```

## Authentication Issues

### JWT Token Errors

**Issue:** Authentication fails with invalid token

**Symptoms:**
```
HTTP 401: {"error": "Invalid token"}
```

**Solutions:**

1. **Check token expiration:**
```python
import jwt
# Decode token to check 'exp' claim
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded['exp'])  # Should be future timestamp
```

2. **Verify JWT secret:**
```python
# In config.yml
security:
  jwt_secret_key: "your-secret-key-here"
```

3. **Check token format:**
```bash
# Should start with 'Bearer '
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/catalog/endpoints
```

### Permission Denied

**Issue:** User gets 403 Forbidden despite valid login

**Symptoms:**
```
HTTP 403: {"error": "Access denied: Missing permission: api_catalog:read"}
```

**Solutions:**

1. **Check user role permissions:**
```python
# In user manager, verify permissions for role
user_permissions = {
    "admin": ["*"],
    "developer": ["api_catalog:read", "analytics:read"],
    "analyst": ["analytics:read"]
}
```

2. **Update user role:**
```bash
curl -X POST "http://localhost:8000/api/admin/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"username": "user", "role": "developer"}'
```

3. **Check endpoint requirements:**
```python
# Some endpoints require specific permissions
@app.get("/api/admin/system", dependencies=[Depends(require_admin)])
```

## API Discovery Problems

### Services Not Appearing

**Issue:** Discovered services don't show in catalog

**Symptoms:**
- `/api/discovery/services` returns empty list
- API catalog shows no services

**Solutions:**

1. **Check Discovery Agent connectivity:**
```bash
curl http://discovery-agent:8080/health
```

2. **Trigger manual discovery:**
```bash
curl -X POST "http://localhost:8000/api/discovery/scan" \
  -H "Authorization: Bearer $TOKEN"
```

3. **Verify service registration:**
```bash
# Check if services have proper health endpoints
curl http://your-service:8000/health
```

4. **Check OpenAPI specs:**
```bash
curl http://your-service:8000/openapi.json
```

### Stale API Specifications

**Issue:** API specs don't update after service changes

**Solutions:**

1. **Clear cache:**
```bash
# Restart dashboard container
docker-compose restart dashboard

# Or clear Redis cache
docker exec -it redis redis-cli FLUSHALL
```

2. **Force refresh:**
```bash
curl -X POST "http://localhost:8000/api/discovery/scan" \
  -H "Authorization: Bearer $TOKEN"
```

3. **Check cache TTL settings:**
```yaml
# In config.yml
cache:
  ttl: 3600  # 1 hour
  enabled: true
```

## API Testing Issues

### Test Execution Failures

**Issue:** API tests fail with connection errors

**Symptoms:**
```
ConnectionError: HTTPConnectionPool(host='service', port=8000): Max retries exceeded
```

**Solutions:**

1. **Check service availability:**
```bash
docker-compose ps
curl http://service:8000/health
```

2. **Verify network configuration:**
```yaml
# In docker-compose.yml
networks:
  default:
    driver: bridge
```

3. **Check service dependencies:**
```yaml
depends_on:
  - redis
  - service
    condition: service_healthy
```

### Test Timeout Issues

**Issue:** Tests timeout waiting for responses

**Solutions:**

1. **Increase timeout settings:**
```python
# In test configuration
timeout = 30  # seconds
retries = 3
backoff_factor = 0.3
```

2. **Check service performance:**
```bash
# Monitor response times
curl -w "@curl-format.txt" -o /dev/null -s http://service:8000/api
```

3. **Scale services if needed:**
```bash
docker-compose up -d --scale service=3
```

## Analytics & Monitoring Issues

### Missing Metrics

**Issue:** Analytics data not appearing in dashboard

**Solutions:**

1. **Check data collection:**
```bash
# Verify API requests are being recorded
curl "http://localhost:8000/api/analytics/usage/overview" \
  -H "Authorization: Bearer $TOKEN"
```

2. **Verify Redis connectivity:**
```bash
docker exec -it dashboard redis-cli ping
```

3. **Check analytics module initialization:**
```python
# In logs, look for:
# "Analytics modules initialized successfully"
docker-compose logs dashboard | grep analytics
```

### Performance Degradation

**Issue:** Dashboard becomes slow under load

**Solutions:**

1. **Check resource usage:**
```bash
docker stats
docker exec dashboard ps aux
```

2. **Enable caching:**
```yaml
environment:
  - CACHE_ENABLED=true
  - CACHE_TTL=3600
```

3. **Scale horizontally:**
```bash
docker-compose up -d --scale dashboard=3
```

4. **Database optimization:**
```bash
# Check Redis memory usage
docker exec redis redis-cli info memory
```

## Security & Compliance Issues

### Audit Log Errors

**Issue:** Audit logging fails

**Symptoms:**
```
ERROR: Audit log write failed
```

**Solutions:**

1. **Check file permissions:**
```bash
docker exec dashboard ls -la /app/logs/
```

2. **Verify disk space:**
```bash
df -h
docker system df
```

3. **Check log rotation:**
```yaml
logging:
  max_file_size: 100MB
  backup_count: 5
```

### Compliance Violations

**Issue:** Compliance checks failing

**Solutions:**

1. **Review compliance rules:**
```python
# Check compliance configuration
compliance_rules = {
    "gdpr": True,
    "hipaa": False,
    "sox": True
}
```

2. **Fix data handling:**
```python
# Ensure proper data anonymization
def anonymize_data(data):
    # Remove PII before logging
    pass
```

3. **Update compliance settings:**
```yaml
compliance:
  gdpr_enabled: true
  hipaa_enabled: false
  audit_retention_days: 2555
```

## Web Interface Issues

### Streamlit App Not Loading

**Issue:** Web UI fails to load

**Symptoms:**
- Browser shows connection refused
- Streamlit errors in logs

**Solutions:**

1. **Check Streamlit port:**
```python
# In app.py
st.set_page_config(page_title="API Dashboard", page_icon="🌐")
```

2. **Verify static file serving:**
```bash
curl http://localhost:8501/health
```

3. **Check browser console errors**

4. **Restart Streamlit:**
```bash
docker-compose restart dashboard
```

### WebSocket Connection Issues

**Issue:** Real-time features not working

**Solutions:**

1. **Check WebSocket endpoint:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/analytics');
```

2. **Verify CORS settings:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

3. **Check firewall/proxy settings**

## Database & Persistence Issues

### Data Loss After Restart

**Issue:** Analytics data disappears after container restart

**Solutions:**

1. **Enable Redis persistence:**
```yaml
command: redis-server --appendonly yes --appendfsync everysec
```

2. **Use persistent volumes:**
```yaml
volumes:
  - redis_data:/data
```

3. **Check volume permissions:**
```bash
docker exec dashboard ls -la /data
```

### High Memory Usage

**Issue:** Redis consuming too much memory

**Solutions:**

1. **Set memory limits:**
```yaml
redis:
  maxmemory: 512mb
  maxmemory-policy: allkeys-lru
```

2. **Enable compression:**
```yaml
cache:
  compression: true
  compression_level: 6
```

3. **Implement data cleanup:**
```python
# Regular cleanup job
scheduler.add_job(cleanup_old_data, 'interval', hours=24)
```

## Performance Optimization

### Slow API Responses

**Issue:** API endpoints responding slowly

**Solutions:**

1. **Enable response caching:**
```python
from fastapi_cache import FastAPICache
FastAPICache.init(backend, prefix="fastapi-cache")
```

2. **Database query optimization:**
```python
# Add database indexes
# Use connection pooling
# Implement query result caching
```

3. **Async processing:**
```python
@app.get("/api/analytics/overview")
async def get_overview():
    # Use async database calls
    # Parallel API calls for multiple services
    pass
```

### High CPU Usage

**Issue:** Container using excessive CPU

**Solutions:**

1. **Profile application:**
```bash
docker exec dashboard python -m cProfile -s cumtime app.py
```

2. **Optimize algorithms:**
```python
# Use more efficient data structures
# Implement lazy loading
# Cache expensive computations
```

3. **Horizontal scaling:**
```yaml
deploy:
  replicas: 3
  resources:
    limits:
      cpus: '1.0'
      memory: 1Gi
```

## Logging & Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In config.yml
logging:
  level: DEBUG
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Log Analysis

```bash
# View recent logs
docker-compose logs --tail=100 dashboard

# Follow logs in real-time
docker-compose logs -f dashboard

# Search for specific errors
docker-compose logs dashboard | grep ERROR

# Export logs for analysis
docker-compose logs dashboard > dashboard.log
```

### Debug Mode

```bash
# Run with debug flags
docker-compose exec dashboard python -c "
import sys
sys.path.append('.')
from app import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000, reload=True, debug=True)
"
```

## Emergency Recovery

### Complete System Reset

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: This deletes all data)
docker volume rm $(docker volume ls -q)

# Clean rebuild
docker system prune -a
docker-compose build --no-cache
docker-compose up -d
```

### Backup and Restore

```bash
# Backup Redis data
docker exec redis redis-cli save
docker cp redis:/data/dump.rdb ./backup/

# Restore Redis data
docker cp ./backup/dump.rdb redis:/data/
docker-compose restart redis
```

## Getting Help

### Support Resources

1. **Documentation:** Check the full documentation at `/docs`
2. **Logs:** Enable debug logging and check container logs
3. **Health Checks:** Use `/health` endpoint for system status
4. **Metrics:** Check `/metrics` endpoint for performance data

### Common Log Messages

```
✅ Service started successfully
❌ Connection failed to Redis
⚠️  High memory usage detected
🔒 Security alert: Suspicious activity
📊 Analytics data updated
```

### Contact Support

- **GitHub Issues:** Report bugs and request features
- **Documentation Issues:** Submit PRs for documentation improvements
- **Community:** Join the API Dashboard community discussions

This troubleshooting guide should resolve most common issues. For complex problems, enable debug logging and gather comprehensive logs before contacting support.
