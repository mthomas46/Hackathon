# Meta-Orchestration Service

The Meta-Orchestration Service is a powerful management layer that controls the lifecycle and configuration of all services in the Hackathon ecosystem.

## 🚀 Features

### Service Lifecycle Management
- **Start/Stop/Restart** individual services
- **Bulk operations** for entire ecosystem
- **Dependency management** - automatically handles service dependencies
- **Health monitoring** - tracks service status and health

### Configuration Management
- **Dynamic configuration updates** without service restarts
- **Configuration validation** before applying changes
- **Backup and rollback** capabilities
- **Environment-specific** configuration management

### Docker Integration
- **Direct Docker API access** for container operations
- **Docker Compose integration** for multi-container services
- **Container inspection** and monitoring
- **Log retrieval** from any service

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   REST API      │    │  Meta-           │    │   Docker API    │
│   (FastAPI)     │◄──►│  Orchestrator    │◄──►│   & Compose     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Service Status  │    │ Configuration    │    │ Container Mgmt  │
│ & Monitoring    │    │ Management       │    │ & Operations    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📋 API Endpoints

### Service Management
- `GET /api/v1/services` - List all services
- `GET /api/v1/services/{name}` - Get service details
- `POST /api/v1/services/{name}/start` - Start a service
- `POST /api/v1/services/{name}/stop` - Stop a service
- `POST /api/v1/services/{name}/restart` - Restart a service

### Configuration Management
- `PUT /api/v1/services/{name}/config` - Update service configuration
- `GET /api/v1/services/{name}/logs` - Get service logs

### Ecosystem Management
- `POST /api/v1/ecosystem/start` - Start all services
- `POST /api/v1/ecosystem/stop` - Stop all services
- `GET /api/v1/ecosystem/status` - Get ecosystem health status

## 🛠️ Quick Start

### 1. Build the Service
```bash
make meta-orchestrator-build
```

### 2. Run the Service
```bash
make meta-orchestrator-run
```

### 3. Check Health
```bash
make meta-orchestrator-health
```

### 4. View Logs
```bash
make meta-orchestrator-logs
```

## 🔧 Configuration

The service reads configuration from environment variables:

```bash
# Docker settings
DOCKER_HOST=unix:///var/run/docker.sock
DOCKER_TLS_VERIFY=false

# Service settings
DEBUG=false
LOG_LEVEL=INFO

# Security
ENABLE_AUTH=false
API_KEY=your-api-key-here
```

## 🔒 Security Considerations

### ⚠️ CRITICAL WARNING
This service has **complete control** over your Docker ecosystem. In production:

1. **Network Isolation** - Run on secure network only
2. **Authentication** - Enable API key authentication
3. **Access Control** - Restrict to authorized users only
4. **Audit Logging** - All operations are logged
5. **Rate Limiting** - Prevent abuse

### Recommended Production Setup
```yaml
# docker-compose.prod.yml
services:
  meta-orchestrator:
    networks:
      - secure-network
    environment:
      - ENABLE_AUTH=true
      - API_KEY=${META_ORCHESTRATOR_KEY}
      - ALLOWED_NETWORKS=10.0.0.0/8,172.16.0.0/12
```

## 📊 Monitoring & Observability

The service provides comprehensive monitoring:

- **Health Checks** - Automatic container health monitoring
- **Metrics** - Prometheus-compatible metrics endpoint
- **Structured Logging** - JSON-formatted logs with correlation IDs
- **Audit Trail** - Complete history of all operations

## 🔄 Backup & Recovery

### Automatic Backups
- Configuration changes are automatically backed up
- Timestamped backups in `config/backups/`
- Registry of all backup operations

### Rollback Operations
```bash
# Rollback specific corrections
python scripts/safeguards/config_drift_detector.py --rollback-corrections "2025-10-02T15:30:00Z"

# List available backups
python scripts/safeguards/config_drift_detector.py --list-backups
```

## 🚨 Production Readiness Checklist

- [ ] Network security configured
- [ ] Authentication enabled
- [ ] Access controls implemented
- [ ] Audit logging configured
- [ ] Backup strategy tested
- [ ] Rollback procedures documented
- [ ] Monitoring alerts configured
- [ ] Rate limiting enabled

## 🐛 Troubleshooting

### Common Issues

**"Permission denied" errors**
```bash
# Ensure Docker socket permissions
sudo chown $USER /var/run/docker.sock
```

**Connection refused**
```bash
# Check Docker daemon status
docker info
```

**Service not found**
```bash
# Verify service exists in docker-compose.dev.yml
docker compose config
```

## 🤝 Contributing

When adding new features:

1. **Security First** - All operations must be authenticated and authorized
2. **Idempotent Operations** - Actions should be safe to repeat
3. **Comprehensive Logging** - All operations must be logged
4. **Error Handling** - Graceful failure with meaningful error messages
5. **Testing** - Unit and integration tests required

## 📈 Future Enhancements

- **GitOps Integration** - Automatic PR creation for config changes
- **Auto-scaling** - Dynamic service scaling based on metrics
- **Blue-Green Deployments** - Zero-downtime service updates
- **Configuration Templates** - Reusable configuration patterns
- **Multi-cluster Support** - Manage services across multiple Docker swarms
