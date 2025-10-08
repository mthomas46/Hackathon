# Docker Compose Updated - Services Added

**Date**: Wednesday, October 8, 2025  
**File**: `docker-compose-mcp-ecosystem.yml`  
**Status**: ✅ **UPDATED**

---

## Changes Made

### Services Added/Fixed (6 total)

| Service | Previous Status | New Status | Changes |
|---------|----------------|------------|---------|
| **mcp-provisioner** | ❌ Missing | ✅ **Added** | New service, port 5400 |
| **mcp-training-coordinator** | ⚠️ Wrong config | ✅ **Fixed** | Port 8100→5600, build from source |
| **mcp-store** | ⚠️ Image only | ✅ **Fixed** | Now builds from source |
| **mcp-registry** | ⚠️ Image only | ✅ **Fixed** | Now builds from source |
| **mcp-gateway** | ❌ Missing | ✅ **Added** | New service, port 8001 |
| **doc_store** | ⚠️ Image only | ✅ **Fixed** | Now builds from source |

---

## Key Updates

### 1. mcp-provisioner (NEW)
```yaml
mcp-provisioner:
  build:
    context: ./services/mcp-provisioner
  ports:
    - "5400:5400"
  environment:
    - SERVICE_API_PORT=5400
    - REDIS_HOST=redis
    - DOCKER_NETWORK=ams
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
```

**Purpose**: MCP instance provisioning and lifecycle management

---

### 2. mcp-training-coordinator (FIXED)
**Before**:
```yaml
image: mcp-training-coordinator:latest  # No source!
ports: "8100:8100"  # Wrong port!
profiles: - full  # Won't start by default!
```

**After**:
```yaml
build:
  context: ./services/mcp-training-coordinator  # Build from source!
ports: "5600:5600"  # Correct port!
environment:
  - SERVICE_API_PORT=5600
  - CELERY_BROKER_URL=redis://redis:6379/8
# No profiles - starts by default!
```

**Purpose**: Training job orchestration with Celery workers

---

### 3. mcp-gateway (NEW)
```yaml
mcp-gateway:
  build:
    context: ./services/mcp-gateway
  ports:
    - "8001:8001"
  environment:
    - SERVICE_API_PORT=8001
  depends_on:
    - mcp-registry
```

**Purpose**: API gateway for MCP queries and routing

---

### 4. mcp-registry (FIXED)
**Before**:
```yaml
image: mcp-registry:latest
profiles: - full
```

**After**:
```yaml
build:
  context: ./services/mcp-registry
ports: "8102:8102"
# Starts by default
```

**Purpose**: MCP instance registry and discovery

---

### 5. mcp-store (FIXED)
**Before**:
```yaml
image: mcp-store:latest
profiles: - full
```

**After**:
```yaml
build:
  context: ./services/mcp-store
ports: "8101:8101"
environment:
  - REDIS_HOST=redis
# Starts by default
```

**Purpose**: MCP storage and persistence

---

### 6. doc_store (FIXED)
**Before**:
```yaml
image: doc_store:latest
profiles: - full
```

**After**:
```yaml
build:
  context: ./services/doc_store
ports: "5087:5087"
# Starts by default
```

**Purpose**: Document storage service

---

## Common Issues Fixed

### 1. Using Images Instead of Build
**Problem**: Services used `image:` which required pre-built images
**Solution**: Changed to `build:` to build from source code

### 2. Profile Restrictions
**Problem**: Services under `profiles: - full` only start with `--profile full`
**Solution**: Removed profiles so services start by default

### 3. Wrong Ports
**Problem**: mcp-training-coordinator used port 8100
**Solution**: Changed to correct port 5600

### 4. Missing Environment Variables
**Problem**: Services had minimal environment configuration
**Solution**: Added proper SERVICE_NAME, REDIS_HOST, LOG_LEVEL, etc.

---

## Network Configuration

All services connected to `ams` network:
```yaml
networks:
  ams:
    driver: bridge
    name: ams
```

**Benefits**:
- Services can communicate using service names
- Network isolation
- Proper Docker DNS resolution

---

## Complete Service List (After Update)

### Infrastructure (6 services)
- ✅ kafka
- ✅ zookeeper
- ✅ redis
- ✅ elasticsearch
- ✅ ollama

### MCP Ecosystem (11 services)
- ✅ mcp-logs
- ✅ kafka-ingestion-service
- ✅ llm-tagging-pipeline
- ✅ mcp-local-llm
- ✅ mcp-package-manager
- ✅ mcp-evergreen-docs
- ✅ **mcp-provisioner** (NEW)
- ✅ **mcp-training-coordinator** (FIXED)
- ✅ **mcp-store** (FIXED)
- ✅ **mcp-registry** (FIXED)
- ✅ **mcp-gateway** (NEW)
- ✅ **doc_store** (FIXED)

**Total**: 17 services

---

## How to Deploy

### Build and Start All Services

```bash
# Navigate to project root
cd /Users/mykalthomas/Documents/work/Hackathon

# Build all services (may take 10-15 minutes first time)
docker-compose -f docker-compose-mcp-ecosystem.yml build

# Start all services
docker-compose -f docker-compose-mcp-ecosystem.yml up -d

# Check status
docker-compose -f docker-compose-mcp-ecosystem.yml ps

# View logs
docker-compose -f docker-compose-mcp-ecosystem.yml logs -f
```

### Start Specific Services Only

```bash
# Start just the new MCP services
docker-compose -f docker-compose-mcp-ecosystem.yml up -d \
  mcp-provisioner \
  mcp-training-coordinator \
  mcp-registry \
  mcp-gateway
```

### Rebuild After Code Changes

```bash
# Rebuild specific service
docker-compose -f docker-compose-mcp-ecosystem.yml build mcp-provisioner

# Rebuild and restart
docker-compose -f docker-compose-mcp-ecosystem.yml up -d --build mcp-provisioner
```

---

## Verification

### Check Service Health

```bash
# Check all containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Test health endpoints
for port in 5400 5600 8001 8101 8102 5087; do
  echo -n "Port $port: "
  curl -s http://localhost:$port/health > /dev/null && echo "✓ UP" || echo "✗ DOWN"
done
```

### Expected Output
```
Port 5400: ✓ UP  # mcp-provisioner
Port 5600: ✓ UP  # mcp-training-coordinator
Port 8001: ✓ UP  # mcp-gateway
Port 8101: ✓ UP  # mcp-store
Port 8102: ✓ UP  # mcp-registry
Port 5087: ✓ UP  # doc_store
```

---

## Run the Demo

Once services are up:

```bash
python3 demo_mcp_lifecycle.py
```

### Expected Improvements

**Before**:
```
Phase 5: ⚠️  MCP creation (fallback)
Phase 6: ⚠️  Training (simulated)
Phase 7: ⚠️  Registration (simulated)
Phase 8: ❌ Queries (0/3)
Success Rate: 60%
```

**After** (with services running):
```
Phase 5: ✅ MCP provisioned (real!)
Phase 6: ✅ Training job created (real!)
Phase 7: ✅ MCP registered (real!)
Phase 8: ✅ Queries answered (3/3)
Success Rate: 90-100%! 🎉
```

---

## Troubleshooting

### Build Failures

If a service fails to build:

```bash
# Check Dockerfile exists
ls services/mcp-provisioner/Dockerfile

# View build logs
docker-compose -f docker-compose-mcp-ecosystem.yml build mcp-provisioner 2>&1 | tee build.log

# Check for missing dependencies
cat services/mcp-provisioner/requirements.txt
```

### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose-mcp-ecosystem.yml logs mcp-provisioner

# Check if ports are available
lsof -i :5400

# Restart specific service
docker-compose -f docker-compose-mcp-ecosystem.yml restart mcp-provisioner
```

### Redis Connection Issues

```bash
# Verify Redis is running
docker-compose -f docker-compose-mcp-ecosystem.yml ps redis

# Test Redis connection
docker exec -it redis redis-cli ping
```

---

## Cleanup

### Stop All Services

```bash
docker-compose -f docker-compose-mcp-ecosystem.yml down
```

### Stop and Remove Volumes

```bash
docker-compose -f docker-compose-mcp-ecosystem.yml down -v
```

### Remove Images

```bash
docker-compose -f docker-compose-mcp-ecosystem.yml down --rmi all
```

---

## Summary

### Changes Made ✅
- ✅ Added mcp-provisioner service
- ✅ Added mcp-gateway service
- ✅ Fixed mcp-training-coordinator (port + build)
- ✅ Fixed mcp-store (build from source)
- ✅ Fixed mcp-registry (build from source)
- ✅ Fixed doc_store (build from source)
- ✅ Removed profile restrictions
- ✅ Added proper environment variables

### Next Steps
1. Build services: `docker-compose build`
2. Start services: `docker-compose up -d`
3. Verify health: `curl localhost:5400/health`
4. Run demo: `python3 demo_mcp_lifecycle.py`
5. Expect 90-100% real execution!

---

**Status**: ✅ **READY TO BUILD AND DEPLOY**

*Docker compose file updated successfully. All services now configured to build from source.*
