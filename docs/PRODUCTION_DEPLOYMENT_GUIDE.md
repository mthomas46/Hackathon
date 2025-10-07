# 🚀 **Production Deployment Guide**

## **Complete Guide to Deploying MCP System**

---

## **Overview**

This guide covers deploying the MCP (Model Context Protocol) system to production with proper configuration, monitoring, and best practices.

---

## **Pre-Deployment Checklist**

### **Infrastructure**
- [ ] Docker installed and configured
- [ ] Docker Compose available
- [ ] PostgreSQL database provisioned
- [ ] Redis instance provisioned
- [ ] Sufficient disk space (minimum 20GB)
- [ ] Network connectivity verified

### **Configuration**
- [ ] Environment variables configured
- [ ] Database credentials secured
- [ ] API keys/secrets stored securely
- [ ] Service ports documented
- [ ] Log directories created

### **Security**
- [ ] Firewall rules configured
- [ ] SSL/TLS certificates ready
- [ ] Database access restricted
- [ ] API authentication enabled
- [ ] Secrets management configured

---

## **System Requirements**

### **Minimum Requirements:**
- **CPU:** 4 cores
- **RAM:** 8GB
- **Disk:** 20GB SSD
- **Network:** 100 Mbps

### **Recommended for Production:**
- **CPU:** 8+ cores
- **RAM:** 16GB+
- **Disk:** 50GB+ SSD
- **Network:** 1 Gbps

---

## **Configuration**

### **Environment Variables**

Create `.env` file:

```bash
# Environment
MCP_ENV=production

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000
SERVICE_WORKERS=4
LOG_LEVEL=INFO

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mcp_production
DB_USER=mcp_user
DB_PASSWORD=<secure_password>

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Secrets
SECRET_JWT_KEY=<generate_secure_key>
SECRET_API_KEY=<generate_secure_key>
```

### **Config Files**

Create `config/production.json`:

```json
{
  "database": {
    "host": "db.example.com",
    "port": 5432,
    "database": "mcp_production",
    "pool_size": 20
  },
  "redis": {
    "host": "redis.example.com",
    "port": 6379,
    "max_connections": 100
  }
}
```

---

## **Deployment Steps**

### **1. Prepare Environment**

```bash
# Clone repository
git clone <repository_url>
cd Hackathon

# Create environment file
cp .env.example .env
vi .env  # Configure variables

# Create data directories
mkdir -p data/postgres data/redis logs
```

### **2. Build Docker Images**

```bash
# Build all services
docker-compose -f docker-compose.prod.yml build

# Verify images
docker images | grep mcp
```

### **3. Initialize Database**

```bash
# Start database only
docker-compose -f docker-compose.prod.yml up -d postgres

# Wait for database
sleep 10

# Run migrations
docker-compose -f docker-compose.prod.yml run --rm mcp_provisioner python migrate.py
```

### **4. Start Services**

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Verify all services started
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### **5. Verify Deployment**

```bash
# Check health endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# Check service connectivity
docker-compose -f docker-compose.prod.yml exec mcp_provisioner python -c "import redis; r = redis.Redis(host='redis'); print(r.ping())"
```

---

## **Service Ports**

| Service | Port | Protocol |
|---------|------|----------|
| MCP Provisioner | 8000 | HTTP |
| MCP Orchestrator | 8001 | HTTP |
| MCP Composer | 8002 | HTTP |
| MCP Registry | 8003 | HTTP |
| MCP Performance Store | 8004 | HTTP |
| MCP Store | 8005 | HTTP |
| Dashboard | 8501 | HTTP |
| PostgreSQL | 5432 | TCP |
| Redis | 6379 | TCP |

---

## **Monitoring**

### **Health Checks**

All services expose health endpoints:

```bash
# Health check
curl http://service:port/health

# Response:
{
  "service": "mcp-provisioner",
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "checks": [...]
}
```

### **Readiness Checks**

```bash
# Readiness check
curl http://service:port/ready

# Response:
{"ready": true}
```

### **Log Monitoring**

```bash
# View logs
docker-compose logs -f service_name

# Filter errors
docker-compose logs service_name | grep ERROR

# Tail recent logs
docker-compose logs --tail=100 service_name
```

---

## **Backup & Recovery**

### **Database Backup**

```bash
# Backup database
docker-compose exec postgres pg_dump -U mcp_user mcp_production > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T postgres psql -U mcp_user mcp_production < backup.sql
```

### **Redis Backup**

```bash
# Trigger save
docker-compose exec redis redis-cli BGSAVE

# Copy RDB file
docker cp mcp_redis:/data/dump.rdb ./redis_backup.rdb
```

---

## **Scaling**

### **Horizontal Scaling**

```bash
# Scale service
docker-compose -f docker-compose.prod.yml up -d --scale mcp_provisioner=3

# Verify
docker-compose ps
```

### **Load Balancing**

Use nginx or HAProxy:

```nginx
upstream mcp_provisioner {
    server mcp_provisioner_1:8000;
    server mcp_provisioner_2:8000;
    server mcp_provisioner_3:8000;
}
```

---

## **Security Best Practices**

### **1. Network Security**
- Use firewalls to restrict access
- Enable SSL/TLS for all services
- Use VPC/private networks
- Restrict database access

### **2. Authentication**
- Enable API authentication
- Use strong passwords
- Rotate credentials regularly
- Implement rate limiting

### **3. Data Security**
- Encrypt sensitive data
- Use secure secret storage
- Enable database encryption
- Regular security audits

---

## **Troubleshooting**

### **Service Won't Start**

```bash
# Check logs
docker-compose logs service_name

# Check configuration
docker-compose config

# Verify connectivity
docker-compose exec service_name ping other_service
```

### **Database Connection Issues**

```bash
# Test connection
docker-compose exec postgres psql -U mcp_user -d mcp_production

# Check connection string
echo $DB_HOST $DB_PORT $DB_NAME
```

### **Performance Issues**

```bash
# Check resource usage
docker stats

# Check service health
curl http://localhost:8000/health

# Review logs for errors
docker-compose logs --tail=1000 | grep ERROR
```

---

## **Maintenance**

### **Regular Tasks**

**Daily:**
- Check service health
- Monitor logs for errors
- Verify backup completion

**Weekly:**
- Review performance metrics
- Check disk space
- Update dependencies

**Monthly:**
- Security updates
- Database optimization
- Cleanup old logs

---

## **Rollback Procedure**

```bash
# Stop current version
docker-compose down

# Restore previous version
git checkout <previous_tag>

# Restore database if needed
docker-compose exec -T postgres psql -U mcp_user mcp_production < backup.sql

# Start services
docker-compose up -d
```

---

## **Support**

For issues or questions:
- Check logs first
- Review troubleshooting section
- Contact support team
- File GitHub issue

---

**Production deployment complete! 🚀**
