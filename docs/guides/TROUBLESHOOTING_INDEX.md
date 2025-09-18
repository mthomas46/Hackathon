# 🔧 Troubleshooting Index - LLM Documentation Ecosystem

<!--
LLM Processing Metadata:
- document_type: "troubleshooting_and_diagnostics"
- content_focus: "issue_resolution_and_system_diagnostics"
- key_concepts: ["troubleshooting", "diagnostics", "issue_resolution", "system_health"]
- processing_hints: "Comprehensive troubleshooting guide with quick issue resolution"
- cross_references: ["QUICK_REFERENCE_GUIDES.md", "ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "docs/operations/RUNBOOK.md"]
- target_scenarios: ["service_failures", "deployment_issues", "performance_problems", "integration_errors"]
-->

## 🎯 **Troubleshooting Overview**

**Comprehensive issue resolution guide** for the LLM Documentation Ecosystem. Organized by problem type with quick diagnosis and resolution steps.

**🔗 Related Resources**: [Quick Reference](QUICK_REFERENCE_GUIDES.md) | [Operations Runbook](docs/operations/RUNBOOK.md) | [Health Monitoring](scripts/docker/health-check.sh)

---

## 🚨 **Service Health & Startup Issues**

### **⚠️ Service Won't Start**

#### **Problem**: Container exits immediately
```bash
# Quick diagnosis
docker logs [container-name] --tail 50
docker-compose ps
```

**Common Causes & Solutions**:

| Symptom | Cause | Solution |
|---------|--------|----------|
| **Import Error** | Module path issues | Check `PYTHONPATH` in docker-compose |
| **Port Conflict** | Port already in use | `netstat -tlnp \| grep :port` → change port |
| **Missing Dependencies** | Requirements not installed | Rebuild image: `docker-compose build [service]` |
| **Configuration Error** | Invalid config values | Check `config.yaml` and environment variables |
| **File Permissions** | Volume mount permissions | `chmod 755` on mounted directories |

#### **Problem**: Service starts but health check fails
```bash
# Diagnosis steps
curl -f http://localhost:[port]/health
docker exec [container] curl -f http://localhost:[internal-port]/health
docker logs [container] | grep -i "health\|error"
```

**Resolution Steps**:
1. **Check internal health**: `docker exec [container] curl localhost:[internal-port]/health`
2. **Verify port mapping**: `docker port [container]`
3. **Check service logs**: `docker logs [container] --since 5m`
4. **Restart service**: `docker-compose restart [service]`

### **⚠️ Orchestrator Issues**

#### **Problem**: Workflow execution fails
```bash
# Check orchestrator health
curl http://localhost:5099/health
curl http://localhost:5099/api/v1/system/status

# Check workflow status
curl http://localhost:5099/api/v1/workflows/[workflow-id]/status
```

**Common Issues**:

| Error Type | Diagnosis | Solution |
|------------|-----------|----------|
| **Service Discovery** | Services not registered | Check Discovery Agent: `curl localhost:5045/health` |
| **Redis Connection** | Redis unavailable | Check Redis: `docker logs redis-container` |
| **Service Communication** | Network issues | Test inter-service calls manually |
| **Workflow Definition** | Invalid workflow config | Validate workflow JSON schema |

#### **Problem**: DDD Bounded Context Issues
```bash
# Check DDD implementation
docker logs orchestrator-container | grep -i "domain\|context\|aggregate"
```

**Resolution**:
1. **Repository Issues**: Check database connectivity
2. **Service Dependencies**: Verify dependency injection container
3. **Event Sourcing**: Check Redis event store connectivity
4. **Command/Query Separation**: Validate CQRS implementation

### **⚠️ LLM Gateway Issues**

#### **Problem**: AI provider routing fails
```bash
# Test LLM Gateway
curl -X POST http://localhost:5055/process \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "provider_preference": "ollama"}'

# Check provider availability
curl http://localhost:11434/api/tags  # Ollama
```

**Provider-Specific Issues**:

| Provider | Common Issue | Solution |
|----------|--------------|----------|
| **Ollama** | Model not available | `docker exec ollama ollama pull llama3.2:1b` |
| **OpenAI** | API key invalid | Check `OPENAI_API_KEY` environment variable |
| **Anthropic** | Rate limiting | Check `ANTHROPIC_API_KEY` and usage limits |
| **Bedrock** | AWS credentials | Verify AWS credentials and region |

#### **Problem**: Security analyzer blocking requests
```bash
# Check secure analyzer
curl http://localhost:5100/health
docker logs secure-analyzer-container | grep -i "blocked\|security"
```

**Resolution**: Adjust security policies in secure analyzer configuration

---

## 💾 **Data & Storage Issues**

### **⚠️ Doc Store Problems**

#### **Problem**: Documents not accessible
```bash
# Test Doc Store
curl http://localhost:5087/health
curl http://localhost:5087/api/v1/documents

# Check internal service
docker exec doc-store-container curl localhost:5010/health
```

**Storage Issues**:

| Problem | Diagnosis | Solution |
|---------|-----------|----------|
| **Database Connection** | PostgreSQL unavailable | Check database connectivity |
| **Disk Space** | Storage full | `df -h` → clean up or increase storage |
| **Permission Issues** | File access denied | Check SQLite file permissions |
| **Index Corruption** | Search not working | Rebuild search indices |

#### **Problem**: Document analysis fails
```bash
# Check Analysis Service
curl http://localhost:5080/health
curl -X POST http://localhost:5080/analyze \
  -H "Content-Type: application/json" \
  -d '{"document_id": "test-doc"}'
```

**Analysis Pipeline Issues**:
1. **Worker Processes**: Check Celery workers if using distributed processing
2. **ML Models**: Verify model loading and memory usage
3. **Integration**: Test connection to Doc Store and LLM Gateway

### **⚠️ Memory & Caching Issues**

#### **Problem**: Redis connectivity
```bash
# Test Redis
docker exec redis-container redis-cli ping
docker logs redis-container

# Test Redis from services
docker exec [service-container] curl -f http://redis:6379
```

**Redis Issues**:
- **Memory Full**: `docker exec redis-container redis-cli info memory`
- **Connection Limit**: Check Redis configuration
- **Data Corruption**: Restart Redis (development only)

#### **Problem**: Memory Agent issues
```bash
# Check Memory Agent
curl http://localhost:5090/health
curl -X POST http://localhost:5090/memory \
  -H "Content-Type: application/json" \
  -d '{"key": "test", "value": "data", "ttl": 3600}'
```

---

## 🌐 **Network & Integration Issues**

### **⚠️ Service Communication Problems**

#### **Problem**: Inter-service communication fails
```bash
# Test service-to-service communication
docker exec [service-container] curl -f http://other-service:port/health
docker network ls
docker network inspect [network-name]
```

**Network Diagnostics**:

| Issue Type | Check Command | Solution |
|------------|---------------|----------|
| **DNS Resolution** | `docker exec [container] nslookup service-name` | Check service names in docker-compose |
| **Port Accessibility** | `docker exec [container] telnet service-name port` | Verify port configuration |
| **Network Isolation** | `docker network inspect bridge` | Check network configuration |
| **Load Balancing** | Test multiple requests | Check load balancer configuration |

#### **Problem**: External API integration fails
```bash
# Test external APIs
curl -I https://api.openai.com/v1/models
curl -I https://api.anthropic.com/v1/messages

# Check proxy settings
echo $HTTP_PROXY $HTTPS_PROXY
```

### **⚠️ Discovery Agent Issues**

#### **Problem**: Service registration fails
```bash
# Check Discovery Agent
curl http://localhost:5045/health
curl http://localhost:5045/api/v1/services

# Test service registration
curl -X POST http://localhost:5045/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{"service_name": "test", "port": 5000, "endpoints": ["/health"]}'
```

**Discovery Issues**:
1. **OpenAPI Parsing**: Check service OpenAPI specifications
2. **LangGraph Integration**: Verify tool generation
3. **Service Metadata**: Validate service capability detection

---

## ⚡ **Performance Issues**

### **⚠️ Slow Response Times**

#### **Problem**: Services responding slowly
```bash
# Performance testing
time curl -s http://localhost:[port]/health
docker stats --no-stream | grep [service-name]

# Load testing
for i in {1..10}; do curl -s http://localhost:[port]/health & done; wait
```

**Performance Diagnostics**:

| Metric | Check Command | Threshold | Action |
|--------|---------------|-----------|---------|
| **Response Time** | `time curl [endpoint]` | < 200ms | Optimize code/database |
| **CPU Usage** | `docker stats` | < 80% | Scale or optimize |
| **Memory Usage** | `docker stats` | < 90% | Increase memory or optimize |
| **Disk I/O** | `iostat -x 1` | < 80% utilization | Optimize queries |

#### **Problem**: High resource usage
```bash
# Resource monitoring
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
top -p $(docker inspect --format='{{.State.Pid}}' [container])

# Memory analysis
docker exec [container] ps aux --sort=-%mem | head
```

**Resource Optimization**:
1. **Memory Leaks**: Restart service, monitor memory growth
2. **CPU Bottlenecks**: Profile code, optimize algorithms
3. **I/O Issues**: Optimize database queries, add caching
4. **Network Bottlenecks**: Check network latency and bandwidth

### **⚠️ Analysis Service Performance**

#### **Problem**: Document analysis takes too long
```bash
# Check analysis pipeline
curl -X GET http://localhost:5080/metrics
docker logs analysis-service-container | grep -i "performance\|slow"

# Test analysis performance
time curl -X POST http://localhost:5080/analyze/simple \
  -H "Content-Type: application/json" \
  -d '{"content": "test document"}'
```

**Analysis Optimization**:
1. **Distributed Processing**: Check worker scaling
2. **ML Model Performance**: Monitor model inference times
3. **Database Queries**: Optimize document retrieval
4. **Caching**: Implement result caching for repeated analyses

---

## 🔒 **Security & Authentication Issues**

### **⚠️ Authentication Problems**

#### **Problem**: Service authentication fails
```bash
# Test authentication
curl -H "Authorization: Bearer [token]" http://localhost:[port]/api/protected

# Check service mesh
docker logs [service-container] | grep -i "auth\|security\|unauthorized"
```

**Authentication Issues**:

| Problem | Diagnosis | Solution |
|---------|-----------|----------|
| **Invalid Tokens** | JWT decode error | Check token generation and validation |
| **Expired Certificates** | mTLS handshake fails | Renew service certificates |
| **Service Identity** | Identity validation fails | Check service registration |
| **Role-based Access** | Permission denied | Verify user roles and permissions |

### **⚠️ Content Security Issues**

#### **Problem**: Secure Analyzer blocking content
```bash
# Check security analysis
curl -X POST http://localhost:5100/analyze \
  -H "Content-Type: application/json" \
  -d '{"content": "test content"}'

# Review security policies
docker logs secure-analyzer-container | grep -i "blocked\|policy"
```

**Security Policy Adjustment**:
1. **Sensitivity Levels**: Adjust content sensitivity thresholds
2. **Provider Routing**: Configure secure provider preferences
3. **Policy Exceptions**: Add exceptions for known safe content
4. **Audit Logging**: Review security decision logs

---

## 🔍 **Debugging Tools & Commands**

### **📊 System-Wide Diagnostics**

#### **Complete Health Check**
```bash
# Comprehensive system health
./scripts/docker/health-check.sh

# Bulletproof system status
make -f Makefile.bulletproof status

# Service-specific health
curl http://localhost:[port]/health | jq '.'
```

#### **Container Diagnostics**
```bash
# Container inspection
docker inspect [container-name] | jq '.[]'
docker exec [container] env | sort
docker exec [container] ps aux

# Resource usage
docker stats --no-stream
docker system df
docker system events --since 1h
```

#### **Network Diagnostics**
```bash
# Network connectivity
docker network ls
docker exec [container] netstat -tlnp
docker exec [container] ss -tulpn

# DNS resolution
docker exec [container] cat /etc/resolv.conf
docker exec [container] nslookup [service-name]
```

### **📝 Log Analysis**

#### **Structured Log Search**
```bash
# Error patterns
docker logs [container] 2>&1 | grep -i "error\|exception\|failed"

# Performance issues
docker logs [container] 2>&1 | grep -i "slow\|timeout\|performance"

# Integration issues
docker logs [container] 2>&1 | grep -i "connection\|network\|integration"

# Time-based filtering
docker logs [container] --since 1h | tail -100
```

#### **Log Aggregation**
```bash
# All service logs
docker-compose logs --tail 50 -f

# Specific service logs
docker-compose logs [service-name] --tail 100 -f

# Error-only logs
docker-compose logs 2>&1 | grep -i error
```

---

## 🛠️ **Recovery Procedures**

### **🔄 Service Recovery**

#### **Standard Service Restart**
```bash
# Single service restart
docker-compose restart [service-name]

# Complete ecosystem restart
docker-compose down && docker-compose up -d

# Bulletproof recovery
make -f Makefile.bulletproof heal
```

#### **Database Recovery**
```bash
# Doc Store SQLite recovery
docker exec doc-store-container sqlite3 /app/data/documents.db ".backup backup.db"

# Redis recovery
docker exec redis-container redis-cli SAVE
docker restart redis-container
```

#### **Configuration Recovery**
```bash
# Reset to default configuration
git checkout HEAD -- config/
docker-compose down && docker-compose up -d

# Validate configuration
./scripts/docker/validate-ports.sh
```

### **📊 System Reset**

#### **Development Environment Reset**
```bash
# Clean reset (development only)
docker-compose down -v
docker system prune -f
docker-compose up -d --build

# Rebuild specific service
docker-compose build [service-name]
docker-compose up -d [service-name]
```

#### **Production Recovery**
```bash
# Graceful production restart
docker-compose restart
./scripts/docker/health-check.sh

# Rollback deployment (if needed)
git checkout [previous-commit]
docker-compose up -d --build
```

---

## 📋 **Escalation & Support**

### **🆘 When to Escalate**

**Immediate Escalation**:
- Multiple service failures
- Data corruption or loss
- Security breaches
- Complete system unavailability

**Standard Escalation**:
- Performance degradation > 50%
- Integration failures affecting workflows
- Persistent service health issues
- Configuration problems affecting multiple services

### **📊 Information to Collect**

#### **System Information**
```bash
# System snapshot
./scripts/docker/health-check.sh > system-status.log
docker-compose ps > container-status.log
docker logs [failing-service] > service-logs.log

# Performance snapshot
docker stats --no-stream > resource-usage.log
```

#### **Error Evidence**
- Service logs with timestamps
- Error messages and stack traces
- Configuration files and environment variables
- Network connectivity test results
- Recent changes or deployments

---

*This troubleshooting index provides systematic approaches to common issues. For complex problems, use the diagnostic tools to gather information before attempting solutions. Always test fixes in development before applying to production.*
