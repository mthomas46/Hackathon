---
title: "🐳 Container Management Feature - Implementation Complete"
service: "ecosystem-mcp"
category: "api"
tags: ['api', 'config', 'configuration', 'endpoints', 'health', 'llm', 'monitoring', 'ollama', 'rag', 'retrieval']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "intermediate"
semantic_keywords: ['api', 'config', 'configuration', 'endpoints', 'health']
llm_search_hints: ['what is 🐳 container management feature - implementation complete', 'how does 🐳 container management feature - implementation complete work', 'guide to 🐳 container management feature - implementation complete']
---

# 🐳 Container Management Feature - Implementation Complete

## Overview

Added Docker container management functionality to the Ecosystem MCP Dashboard, allowing users to view, monitor, and control Docker containers directly from the web interface.

## What Was Added

### 1. API Endpoints (Backend)

**New File:** `src/api/routes/containers.py`

**Endpoints Created:**
- `GET /api/v1/containers` - List all Docker containers
- `GET /api/v1/containers/{name}` - Get detailed container info
- `POST /api/v1/containers/action` - Perform actions (start, stop, restart, pause, unpause)
- `GET /api/v1/containers/{name}/logs` - Get container logs
- `GET /api/v1/containers/{name}/stats` - Get real-time resource stats

**Features:**
- Full Docker integration using `docker-py`
- Safety checks and error handling
- Resource usage monitoring
- Log retrieval with configurable tail
- Support for all container states

### 2. Dashboard Page (Frontend)

**New File:** `services/ecosystem-mcp-dashboard/pages/containers.py`

**Features:**
- **Container List**: View all containers with status indicators
- **Summary Metrics**: Total, running, stopped, paused counts
- **Container Actions**:
  - 🔄 Restart running containers
  - ▶️ Start stopped containers
  - ⏹️ Stop running containers
  - ⏸️ Pause running containers
  - ▶️ Unpause paused containers
- **Container Details**:
  - Resource usage (memory, CPU)
  - Port mappings
  - Network information
  - Image details
- **Tabs for Each Container**:
  - 📊 Stats - Real-time resource monitoring
  - 📜 Logs - Last 50 log lines
  - ℹ️ Details - Full container configuration
- **Auto-refresh**: Optional auto-refresh every 5 seconds
- **Error Handling**: Graceful error messages and troubleshooting tips

### 3. Dependencies Added

**Updated:** `requirements.txt`
```
docker==7.0.0  # Docker SDK for container management
```

### 4. Docker Configuration

**Updated:** `docker-compose.yml`
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock  # Docker socket for container management
```

**Critical:** The ecosystem-mcp service now has access to the Docker socket, allowing it to control containers.

### 5. Navigation Update

**Updated:** `app.py`
- Added "🐳 Container Management" to navigation menu
- Positioned between "Health & Infrastructure" and "RAG Query"

## Architecture

```
┌──────────────────────────────────────────────┐
│  Dashboard (Streamlit)                       │
│  └─ Container Management Page                │
│     ├─ List all containers                   │
│     ├─ Action buttons                        │
│     └─ Stats/Logs/Details                    │
└───────────────┬──────────────────────────────┘
                │ HTTP Requests
                ▼
┌──────────────────────────────────────────────┐
│  Ecosystem MCP API                           │
│  └─ Container Management Endpoints           │
│     └─ Docker SDK (docker-py)                │
└───────────────┬──────────────────────────────┘
                │ Docker API
                ▼
┌──────────────────────────────────────────────┐
│  Docker Daemon                               │
│  └─ Container Operations                     │
│     ├─ Start/Stop/Restart                    │
│     ├─ Pause/Unpause                         │
│     ├─ Get Stats                             │
│     └─ Get Logs                              │
└──────────────────────────────────────────────┘
```

## Usage

### Access Container Management

1. Start the services:
   ```bash
   cd services/ecosystem-mcp
   docker-compose up -d
   ```

2. Open dashboard:
   ```
   http://localhost:8501
   ```

3. Navigate to **🐳 Container Management**

### Restart a Container

1. Find the container in the list
2. Expand the container details
3. Click **🔄 Restart**
4. Wait for confirmation message
5. Container will restart in ~10-30 seconds

### View Container Logs

1. Expand container
2. Go to **📜 Logs** tab
3. Click **Load Logs**
4. View last 50 lines

### Monitor Resources

1. Expand running container
2. Go to **📊 Stats** tab
3. Click **Load Stats**
4. View memory usage and CPU info

## Security Considerations

### Docker Socket Access

The ecosystem-mcp service has access to the Docker socket, which provides **full control** over the Docker daemon.

**Implications:**
- Can start/stop/restart any container
- Can access container logs and configuration
- Can create/delete containers
- Has same permissions as Docker daemon

**Recommendations:**
1. **Production**: Use Docker API over TCP with TLS authentication
2. **Development**: Current socket mount is acceptable
3. **Access Control**: Implement authentication on the dashboard
4. **Audit**: Log all container operations
5. **Restrictions**: Consider read-only access or whitelisting containers

### API Security

**Current State:**
- ✅ Action validation (only allowed actions)
- ✅ Container name validation
- ✅ Error handling
- ❌ No authentication on endpoints (development only)
- ❌ No authorization checks
- ❌ No action logging/auditing

**For Production:**
```python
# Add authentication
@router.post("/containers/action")
async def container_action(
    action_request: ContainerAction,
    current_user: User = Depends(get_current_user)  # Add auth
):
    # Log action
    logger.info(f"User {current_user.id} performing {action_request.action} on {action_request.container_name}")
    
    # Check permissions
    if not current_user.has_permission("container.manage"):
        raise HTTPException(403, "Insufficient permissions")
    
    # ... perform action ...
```

## API Examples

### List Containers

```bash
curl http://localhost:8000/api/v1/containers
```

Response:
```json
{
  "containers": [
    {
      "id": "abc123def456",
      "name": "ecosystem-mcp-postgres",
      "status": "running",
      "image": "postgres:16-alpine",
      "ports": {"5432/tcp": [{"HostPort": "5432"}]},
      "memory_usage_mb": 45.2,
      "memory_limit_mb": 512.0,
      "memory_percent": 8.83
    }
  ],
  "total": 5
}
```

### Restart Container

```bash
curl -X POST http://localhost:8000/api/v1/containers/action \
  -H "Content-Type: application/json" \
  -d '{"action": "restart", "container_name": "ecosystem-mcp-redis"}'
```

Response:
```json
{
  "success": true,
  "message": "Container 'ecosystem-mcp-redis' restarted successfully",
  "container_name": "ecosystem-mcp-redis",
  "action": "restart",
  "timestamp": "2025-01-12T10:30:45.123Z"
}
```

### Get Container Logs

```bash
curl "http://localhost:8000/api/v1/containers/ecosystem-mcp-ollama/logs?tail=20"
```

### Get Container Stats

```bash
curl http://localhost:8000/api/v1/containers/ecosystem-mcp-service/stats
```

Response:
```json
{
  "container": "ecosystem-mcp-service",
  "timestamp": "2025-01-12T10:30:45.123Z",
  "memory": {
    "usage_mb": 234.5,
    "limit_mb": 2048.0,
    "percent": 11.45
  },
  "cpu": {
    "total_usage": 123456789,
    "online_cpus": 8
  }
}
```

## Error Handling

### Docker Not Available

**Error:**
```
503 Service Unavailable
Docker SDK not available or daemon not running
```

**Solution:**
1. Ensure Docker is running: `docker ps`
2. Check socket mount in docker-compose.yml
3. Restart ecosystem-mcp service

### Container Not Found

**Error:**
```
404 Not Found
Container 'xyz' not found
```

**Solution:**
1. Refresh container list
2. Check container name spelling
3. Container may have been removed

### Permission Denied

**Error:**
```
500 Internal Server Error
Permission denied accessing Docker socket
```

**Solution:**
1. Verify socket mount: `-v /var/run/docker.sock:/var/run/docker.sock`
2. Check file permissions
3. May need to run with elevated privileges

## Testing Checklist

### Basic Functionality
- [ ] Dashboard loads Container Management page
- [ ] Containers list displays correctly
- [ ] Summary metrics show accurate counts
- [ ] Status indicators match actual state

### Container Actions
- [ ] Can restart a running container
- [ ] Can stop a running container
- [ ] Can start a stopped container
- [ ] Can pause a running container
- [ ] Can unpause a paused container
- [ ] Actions complete within expected time
- [ ] Success messages display
- [ ] Error messages display for failures

### Details & Monitoring
- [ ] Can view container stats
- [ ] Memory usage displays correctly
- [ ] Can view container logs
- [ ] Logs display recent entries
- [ ] Can view full container details
- [ ] Details include all expected fields

### Error Handling
- [ ] Graceful error if Docker unavailable
- [ ] Helpful error messages
- [ ] Troubleshooting tips display
- [ ] No crashes on failures

## Troubleshooting

### Cannot Access Docker from Container

**Symptom:** "Docker not available" error

**Solution:**
```yaml
# In docker-compose.yml
ecosystem-mcp:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
```

Restart service:
```bash
docker-compose restart ecosystem-mcp
```

### Restart Button Doesn't Work

**Symptom:** Button click has no effect

**Check:**
1. Browser console for JavaScript errors
2. API logs: `docker logs ecosystem-mcp-service`
3. Network tab for failed requests

### Container State Not Updating

**Symptom:** Shows old status after action

**Solution:**
- Enable auto-refresh in dashboard
- Or click 🔄 Refresh button
- Allow 5-10 seconds for action to complete

## Future Enhancements

- [ ] Bulk actions (restart multiple containers)
- [ ] Container creation/deletion
- [ ] Volume management
- [ ] Network management
- [ ] Image management (pull, remove)
- [ ] Container execution (run commands)
- [ ] Real-time log streaming (WebSocket)
- [ ] Advanced filtering and search
- [ ] Container templates/presets
- [ ] Automated actions (auto-restart on failure)
- [ ] Alert system for container events
- [ ] Container health history
- [ ] Resource usage graphs over time
- [ ] Export container configurations

## Summary

✅ **Container Management Feature Complete**

**Capabilities:**
- View all Docker containers
- Start, stop, restart containers
- Pause and unpause containers
- View logs and resource stats
- Monitor memory and CPU usage
- Comprehensive error handling

**Files Created/Modified:**
- ✅ `src/api/routes/containers.py` (New API endpoints)
- ✅ `pages/containers.py` (New dashboard page)
- ✅ `requirements.txt` (Added docker-py)
- ✅ `docker-compose.yml` (Added Docker socket mount)
- ✅ `app.py` (Added navigation)

**Ready for Use:**
- Start services: `docker-compose up -d`
- Access: http://localhost:8501
- Navigate to: 🐳 Container Management

The container management feature is now fully functional and ready for testing! 🎉

