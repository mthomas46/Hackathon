# Docker Service Management - Quick Start Guide

## What's New? 🎉

Your dashboard now has **intelligent Docker service management** built-in! You can now start, stop, restart, and monitor services directly from the dashboard, even when the main API is unreachable.

## The Problem You Had

```
Error connecting to API: [Errno 61] Connection refused
```

This happened because the `ecosystem-mcp` service wasn't running, and the dashboard had no way to start it.

## The Solution

The dashboard now has **three ways** to manage containers:

### 1. 🐳 Container Management Page (Enhanced!)

Navigate to **🐳 Container Management** and you'll see three tabs:

#### Tab 1: 📊 Via API
- Shows containers through the ecosystem-mcp API
- Works when API is running
- Same functionality as before

#### Tab 2: 🐳 Direct Docker Access ⭐ NEW
- **Works independently of API!**
- Direct Docker CLI integration
- Cached for performance (30-second TTL)
- Filter containers by name or status
- Start/restart any container with one click

#### Tab 3: 🚀 Service Manager ⭐ NEW
- **The game-changer!**
- Manages key ecosystem services
- Auto-start capabilities with docker-compose
- View logs inline
- Bulk operations (start/stop/restart all)

## How to Use It

### Starting a Stopped Service

1. Go to **🐳 Container Management**
2. Click the **🚀 Service Manager** tab
3. Find `ecosystem-mcp-service` in the **🎯 Key Services** list
4. If it shows ⏸️ Stopped or ❌ Not Found, click **▶️ Start**
5. Wait 10-30 seconds for it to start up
6. Done! The API will now be reachable

### Restarting a Misbehaving Service

1. Go to **🐳 Container Management** → **🚀 Service Manager**
2. Find the problematic service
3. Click **🔄 Restart**
4. Wait for confirmation
5. Service restarted with clean state

### Viewing Service Logs

1. Go to **🐳 Container Management** → **🚀 Service Manager**
2. Find your service
3. Click **🔍 Logs**
4. View last 50 lines
5. Click **Close Logs** when done

### Starting All Services at Once

1. Go to **🐳 Container Management** → **🚀 Service Manager**
2. Scroll to **🎛️ Bulk Actions**
3. Click **🚀 Start All Services**
4. Wait for docker-compose to finish (may take 30-60 seconds)
5. All services running!

## Key Features

### ✅ Intelligent Caching
- Service status cached for 30 seconds
- Fast repeated checks (<1ms)
- Automatic cache invalidation on changes

### ✅ Auto-Start
- Services can be started automatically
- Uses docker-compose for proper initialization
- Handles missing containers gracefully

### ✅ Resilient
- Works when API is down
- Falls back to direct Docker CLI
- Clear error messages and instructions

### ✅ Safe
- Confirmation before bulk operations
- Clear status indicators
- Graceful error handling

## Architecture

```
┌─────────────────────────────────────────────┐
│         Streamlit Dashboard UI              │
└─────────────────┬───────────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
    ┌────▼────┐      ┌────▼──────────┐
    │ API     │      │ Docker        │
    │ Client  │      │ Manager       │
    │ (httpx) │      │ (with cache)  │
    └────┬────┘      └────┬──────────┘
         │                │
         │                │
    ┌────▼────┐      ┌────▼──────────┐
    │ ecosystem│      │ Docker CLI    │
    │ -mcp API│      │               │
    └─────────┘      └────┬──────────┘
                          │
                     ┌────▼──────────┐
                     │ Docker Daemon │
                     └───────────────┘
```

## Files Created

```
services/ecosystem-mcp-dashboard/
├── utils/
│   ├── __init__.py                    # Package initialization
│   ├── docker_manager.py              # Core Docker integration
│   └── service_manager_widget.py      # UI widget layer
│
├── dashboard_views/
│   └── containers.py                  # Enhanced with 3 tabs
│
├── DOCKER_SERVICE_MANAGEMENT.md       # Full documentation
└── DOCKER_QUICK_START.md             # This file
```

## Common Scenarios

### Scenario: Dashboard shows "Connection refused"

**Solution:**
1. Go to **🐳 Container Management** → **🚀 Service Manager**
2. Check `ecosystem-mcp-service` status
3. If stopped: Click **▶️ Start**
4. If running but API unreachable: Click **🔄 Restart**
5. Wait 30 seconds, then try your original action

### Scenario: Docker not running

**Solution:**
1. Dashboard will show "❌ Docker daemon is not running"
2. Open the **🐳 How to Start Docker** instructions
3. On macOS: Run `open -a Docker` in terminal
4. Wait for Docker icon in menu bar to be solid
5. Click **🔄 Refresh** in dashboard

### Scenario: Need fresh start

**Solution:**
1. Go to **🐳 Container Management** → **🚀 Service Manager**
2. Scroll to **🎛️ Bulk Actions**
3. Click **🔄 Restart All Services**
4. Everything gets a clean restart

## Performance

### Before (API-only)
- ❌ No access when API down
- ❌ No container management
- ❌ Manual docker commands needed

### After (With Docker Integration)
- ✅ Works independently of API
- ✅ 30-second cache TTL (fast!)
- ✅ One-click operations
- ✅ Self-healing capabilities

### Typical Timings
- **First status check:** 100-500ms (Docker CLI)
- **Cached check:** <1ms (in-memory)
- **Start service:** 2-10 seconds
- **Restart service:** 3-15 seconds
- **Start all services:** 30-60 seconds

## Tips & Best Practices

1. **Use Service Manager first** when API is unreachable
2. **Check logs** if a service won't start
3. **Wait 30 seconds** after starting services for full initialization
4. **Use bulk operations** instead of restarting services individually
5. **Leverage caching** - don't spam the refresh button!

## Troubleshooting

### "Service not found"
- Service may not exist in docker-compose
- Check container names with `docker ps -a`
- Verify docker-compose.dev.yml location

### "Permission denied"
- On Linux: Add user to docker group
- `sudo usermod -aG docker $USER`
- Log out and back in

### "Timeout"
- Service may be slow to start
- Check logs for errors
- Try increasing timeouts in code

## Next Steps

1. **Test it out!** Go to **🐳 Container Management**
2. **Try starting a service** using Service Manager
3. **Explore the tabs** to see different views
4. **Check out the full docs** in `DOCKER_SERVICE_MANAGEMENT.md`

## Summary

You now have a **self-healing dashboard** that can:
- ✅ Detect when services are down
- ✅ Start/restart services automatically
- ✅ Work independently of the main API
- ✅ Provide clear status and actionable errors
- ✅ Cache for performance

**No more manual `docker-compose` commands needed!** 🎉

---

**Questions?** Check the full documentation in `DOCKER_SERVICE_MANAGEMENT.md`

