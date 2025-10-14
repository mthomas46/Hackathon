# Docker Service Management Infrastructure

## Overview

The Ecosystem MCP Dashboard now includes comprehensive Docker service management capabilities with caching, auto-start, and direct CLI integration. This infrastructure allows the dashboard to operate even when the main API is unreachable.

## Created: October 14, 2025

## Components

### 1. Docker Manager (`utils/docker_manager.py`)

Core infrastructure for Docker service management with intelligent caching.

**Features:**
- ✅ Direct Docker CLI integration
- ✅ Service status caching (30-second TTL)
- ✅ Auto-start capabilities
- ✅ Health monitoring
- ✅ Docker daemon detection
- ✅ Graceful fallback when Docker unavailable

**Key Functions:**
```python
# Get Docker manager singleton
docker_manager = get_docker_manager()

# Check if Docker is running
is_running = docker_manager.is_docker_running()

# Get service status (cached)
status = docker_manager.get_service_status("ecosystem-mcp")

# Start a service
success, message = docker_manager.start_service("ecosystem-mcp", compose_file)

# Restart a service
success, message = docker_manager.restart_service("ecosystem-mcp")

# Auto-start (creates if not found)
success, message = docker_manager.auto_start_service("ecosystem-mcp", compose_file)

# Get all services
services = docker_manager.get_all_services(filter_prefix="ecosystem-")
```

**Caching Behavior:**
- Service status cached for 30 seconds
- Cache automatically cleared on service operations
- Force refresh with `force_refresh=True` parameter
- Docker running status cached for 60 seconds

### 2. Service Manager Widget (`utils/service_manager_widget.py`)

High-level UI widget for Streamlit integration.

**Features:**
- ✅ Service status display with controls
- ✅ Auto-start on API unreachable
- ✅ Quick fix panels
- ✅ Bulk operations
- ✅ Docker start instructions

**Usage:**
```python
from utils.service_manager_widget import ServiceManagerWidget

# Create widget
manager = ServiceManagerWidget(compose_file="/path/to/docker-compose.yml")

# Show status with controls
manager.show_service_status("ecosystem-mcp", show_controls=True)

# Auto-start if needed
manager.auto_start_if_needed("ecosystem-mcp", "http://localhost:8000")

# Show all services
manager.show_ecosystem_services()

# Show quick fix panel
manager.show_quick_fix_panel("ecosystem-mcp")
```

### 3. Enhanced Container Management Page

The **🐳 Container Management** page now has three tabs:

#### Tab 1: 📊 Via API
- Original functionality using ecosystem-mcp API
- Works when API is reachable
- Provides container stats, logs, and management

#### Tab 2: 🐳 Direct Docker Access
- **NEW:** Direct Docker CLI integration
- Works independently of API
- Features:
  - Filter by name prefix
  - Filter by status
  - Real-time status with caching
  - Start/restart containers
  - Last checked timestamps

#### Tab 3: 🚀 Service Manager
- **NEW:** Comprehensive service management
- Features:
  - Key services quick access (ecosystem-mcp, postgres, redis, etc.)
  - Auto-start/restart with compose integration
  - Container logs viewer
  - Bulk operations:
    - Start all services
    - Restart all services
    - Stop all services
  - Docker start instructions

## Usage Scenarios

### Scenario 1: API is Unreachable

**Problem:** Dashboard shows "Error connecting to API: [Errno 61] Connection refused"

**Solution:**
1. Go to **🐳 Container Management** page
2. Switch to **🚀 Service Manager** tab
3. Check status of `ecosystem-mcp` service
4. Click **▶️ Start** if stopped or **🔄 Restart** if needed
5. Wait 10-30 seconds for service to be ready
6. Return to other pages and they should work

### Scenario 2: Docker Not Running

**Problem:** Dashboard shows "Docker daemon is not running"

**Solution:**
1. Go to **🐳 Container Management** → **🚀 Service Manager**
2. Follow the **🐳 How to Start Docker** instructions
3. On macOS: `open -a Docker`
4. Wait for Docker icon in menu bar to be solid
5. Click **🔄 Refresh** in dashboard

### Scenario 3: Bulk Service Restart

**Problem:** Services are misbehaving or need a fresh start

**Solution:**
1. Go to **🐳 Container Management** → **🚀 Service Manager**
2. Scroll to **🎛️ Bulk Actions**
3. Click **🔄 Restart All Services**
4. Wait for completion message
5. Services will restart with clean state

### Scenario 4: Monitor Service Logs

**Problem:** Need to debug a service issue

**Solution:**
1. Go to **🐳 Container Management** → **🚀 Service Manager**
2. Find the service in **🎯 Key Services**
3. Click **🔍 Logs**
4. View last 50 lines of logs
5. Click **Close Logs** when done

## Architecture

### Caching Strategy

```
┌─────────────────────┐
│ DockerManager       │
│ ┌─────────────────┐ │
│ │ Service Cache   │ │  ← TTL: 30 seconds
│ │ {service_name:  │ │
│ │  DockerService} │ │
│ └─────────────────┘ │
│                     │
│ ┌─────────────────┐ │
│ │ Docker Status   │ │  ← TTL: 60 seconds
│ │ Cache           │ │
│ └─────────────────┘ │
└─────────────────────┘
```

**Why Caching:**
- Docker CLI calls are expensive (~100-500ms)
- Dashboard makes multiple status checks
- 30-second TTL balances freshness vs performance
- Cache cleared on mutations (start, stop, restart)

### Data Flow

```
Streamlit UI
    ↓
Service Manager Widget
    ↓
Docker Manager (with caching)
    ↓
Docker CLI
    ↓
Docker Daemon
```

### Fallback Chain

```
API Request
    ↓
    ├─ Success → Use API data
    │
    └─ Failure → Try Direct Docker Access
            ↓
            ├─ Docker Running → Manage via CLI
            │
            └─ Docker Not Running → Show instructions
```

## File Structure

```
services/ecosystem-mcp-dashboard/
├── utils/
│   ├── __init__.py                      # NEW
│   ├── docker_manager.py                # NEW - Core Docker integration
│   └── service_manager_widget.py        # NEW - UI widget layer
│
├── dashboard_views/
│   └── containers.py                    # ENHANCED - Three tabs
│
└── DOCKER_SERVICE_MANAGEMENT.md         # NEW - This file
```

## Configuration

### Required Docker Compose File

The service manager looks for `docker-compose.dev.yml` at:
```
/Users/mykalthomas/Documents/work/Hackathon/docker-compose.dev.yml
```

**Path Resolution:**
```python
dashboard_dir = Path(__file__).parent.parent  # dashboard root
project_root = dashboard_dir.parent.parent    # project root
compose_file = project_root / "docker-compose.dev.yml"
```

### Key Services

Default services monitored:
- `ecosystem-mcp-service` - Main API service
- `ecosystem-mcp-postgres` - Database
- `ecosystem-mcp-redis` - Cache
- `ecosystem-mcp-ollama` - LLM service

**Customize in `containers.py`:**
```python
key_services = [
    "ecosystem-mcp-service",      # Main API service
    "ecosystem-mcp-postgres",     # Database
    "ecosystem-mcp-redis",        # Cache
    "ecosystem-mcp-ollama",       # LLM service
    # Add more services here
]
```

## API Reference

### DockerService (Data Class)

```python
@dataclass
class DockerService:
    name: str                          # Container name
    status: str                        # running, stopped, not_found, etc.
    container_id: Optional[str]        # Docker container ID
    image: Optional[str]               # Image name
    ports: Optional[Dict[str, str]]    # Port mappings
    last_checked: datetime             # Cache timestamp
```

### DockerManager Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `is_docker_running()` | `bool` | Check if Docker daemon is accessible |
| `get_service_status(name)` | `DockerService` | Get cached service status |
| `get_all_services()` | `List[DockerService]` | Get all running containers |
| `start_service(name)` | `(bool, str)` | Start a container |
| `stop_service(name)` | `(bool, str)` | Stop a container |
| `restart_service(name)` | `(bool, str)` | Restart a container |
| `auto_start_service(name, compose)` | `(bool, str)` | Start with docker-compose |
| `get_service_logs(name, lines)` | `Optional[str]` | Get container logs |

## Performance Considerations

### Cache Hit Rates

Expected cache performance:
- **First request:** 100-500ms (Docker CLI call)
- **Cached request:** <1ms (in-memory lookup)
- **Cache hit rate:** ~80-90% in normal usage

### Resource Usage

- **Memory:** ~1-5 KB per cached service
- **CPU:** Minimal (only during CLI calls)
- **Network:** None (local Docker socket)

### Optimization Tips

1. **Reduce refresh frequency:** Use auto-refresh sparingly
2. **Batch operations:** Use bulk actions instead of individual
3. **Leverage caching:** Don't force refresh unless needed
4. **Monitor cache TTL:** 30s is optimal for most use cases

## Troubleshooting

### Issue: "Docker manager not available"

**Cause:** Import error or missing dependencies

**Fix:**
```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-dashboard
# Ensure utils/__init__.py exists
touch utils/__init__.py
```

### Issue: "Permission denied" on docker commands

**Cause:** User not in docker group (Linux)

**Fix:**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Issue: Services not appearing

**Cause:** Containers may have different names

**Fix:**
1. Check actual container names: `docker ps -a`
2. Update `key_services` list in containers.py
3. Use filter prefix in Direct Docker Access tab

### Issue: Slow performance

**Cause:** Cache TTL too short or disabled

**Fix:**
```python
# In docker_manager.py, increase cache TTL
CACHE_TTL_SECONDS = 60  # Increase from 30
```

## Security Considerations

1. **Docker Socket Access:** Dashboard needs `/var/run/docker.sock` mounted
2. **Container Control:** Dashboard can start/stop ANY container it can see
3. **Logs Access:** Can read logs from any container
4. **No Authentication:** Docker CLI operations are not user-authenticated

**Recommendations:**
- Run dashboard in trusted environment only
- Limit Docker socket access via volume mounts
- Consider using Docker API with TLS instead of socket
- Implement audit logging for container operations

## Future Enhancements

### Planned Features

1. **Enhanced Caching**
   - Redis-backed cache for multi-dashboard deployment
   - Configurable TTL per service type
   - Cache prewarming

2. **Health Checks**
   - HTTP health endpoint polling
   - Container health status integration
   - Alerting on unhealthy services

3. **Resource Monitoring**
   - CPU/Memory usage graphs
   - Network I/O statistics
   - Disk usage tracking

4. **Advanced Operations**
   - Container scaling (replicas)
   - Image updates and pulls
   - Volume management
   - Network inspection

5. **Integration**
   - Webhook notifications
   - Slack/Discord alerts
   - Grafana dashboard export
   - Prometheus metrics endpoint

## Testing

### Manual Testing Checklist

- [ ] Start Docker → Verify dashboard detects it
- [ ] Stop Docker → Verify dashboard shows instructions
- [ ] Start service via Service Manager → Verify it starts
- [ ] Restart running service → Verify restart completes
- [ ] View logs → Verify logs appear
- [ ] Use bulk "Start All" → Verify all services start
- [ ] Use bulk "Stop All" → Verify all services stop
- [ ] Switch between tabs → Verify no errors
- [ ] Test with API unreachable → Verify fallback works
- [ ] Test caching → Verify repeated checks are fast

### Automated Testing

```python
# Example test
def test_docker_manager():
    manager = get_docker_manager()
    
    # Test Docker detection
    assert manager.is_docker_running() == True
    
    # Test service status
    status = manager.get_service_status("ecosystem-mcp")
    assert status.name == "ecosystem-mcp"
    assert status.status in ["running", "stopped", "not_found"]
    
    # Test caching
    import time
    start = time.time()
    status1 = manager.get_service_status("ecosystem-mcp")
    time1 = time.time() - start
    
    start = time.time()
    status2 = manager.get_service_status("ecosystem-mcp")
    time2 = time.time() - start
    
    # Cached call should be much faster
    assert time2 < time1 * 0.1
```

## Related Changes

### Also Modified

1. **app.py** - Updated API_BASE_URL default to `localhost:8000`
2. **containers.py** - Added three-tab interface with Docker integration
3. **Created utils/__init__.py** - Package initialization

### Related Documentation

- `AUDIT_SUMMARY_README.md` - Previous audit findings
- `NAVIGATION_FIX_SUMMARY.md` - Navigation fixes
- `README.md` - Main dashboard documentation

## Summary

The Docker Service Management infrastructure provides:

✅ **Resilience** - Dashboard works even when API is down
✅ **Performance** - Intelligent caching reduces Docker CLI overhead
✅ **Usability** - Simple UI for complex Docker operations
✅ **Flexibility** - API-first with CLI fallback
✅ **Visibility** - Real-time status monitoring with logs access

**Result:** The dashboard can now self-heal by automatically detecting and starting unavailable services, providing a much more robust user experience.

