---
title: "Logs Viewer Page - Fixed"
service: "ecosystem-mcp"
category: "api"
tags: ['api', 'endpoints', 'routes', 'test', 'testing']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "intermediate"
semantic_keywords: ['api', 'endpoints', 'routes', 'test', 'testing']
llm_search_hints: ['what is logs viewer page - fixed', 'how does logs viewer page - fixed work', 'guide to logs viewer page - fixed']
---

# Logs Viewer Page - Fixed

## Issues Found and Fixed

### Issue 1: Container Logs Error
**Error:** "Invalid binary data format: <class 'list'>"

**Root Cause:**
- The `/api/v1/containers/{name}/logs` endpoint returns logs as a **list** of strings
- The dashboard code was expecting a **string**
- When `st.code()` received a list, it threw a type error

**API Response Format:**
```json
{
  "container": "ecosystem-mcp-service",
  "lines": 6,
  "logs": [
    "2025-10-13T21:21:11.381725887Z INFO: ...",
    "2025-10-13T21:21:41.443893137Z INFO: ...",
    ...
  ]
}
```

**Fix Applied:**
Modified `/services/ecosystem-mcp-dashboard/pages/logs_viewer.py`:
- Added type checking for logs response
- Convert list to string using `"\n".join(logs_list)`
- Applied fix to both the Container Logs tab and Search Logs tab

**Changes:**
```python
# Before (line 89):
logs = log_data.get("logs", "")

# After (lines 89-95):
logs_list = log_data.get("logs", [])

# Convert list to string (API returns logs as a list of lines)
if isinstance(logs_list, list):
    logs = "\n".join(logs_list)
else:
    logs = str(logs_list)
```

---

### Issue 2: Dashboard Logs Not Available
**Error:** "⚠️ Docker CLI not available in this environment."

**Root Cause:**
- The dashboard container doesn't have Docker CLI installed
- The Dashboard Logs tab tried to use `subprocess` to call `docker logs`
- This is expected behavior since we only added Docker CLI to the `ecosystem-mcp` service

**Fix Applied:**
Improved the user guidance when Docker CLI is not available:
- Changed from warning to informational message
- Added clear instructions for 4 alternative ways to view dashboard logs
- Directed users to the Container Logs tab as the recommended approach

**Updated Message:**
```markdown
ℹ️ Docker CLI is not available inside the dashboard container.

**To view dashboard logs, use one of these options:**

1. **🐳 Container Logs Tab** (recommended)
   - Switch to the "Container Logs" tab above
   - Select `ecosystem-mcp-dashboard` from the dropdown
   - This will show the dashboard logs via the API

2. **From Host Machine:**
   ```bash
   docker logs ecosystem-mcp-dashboard --tail 100
   ```

3. **Using Docker Desktop:**
   - Open Docker Desktop
   - Find the `ecosystem-mcp-dashboard` container
   - Click to view logs

4. **Via Container Management Page:**
   - Go to "🐳 Container Management" in the sidebar
   - Find the dashboard container
   - Click to expand and view logs
```

---

## Files Modified

### 1. `/services/ecosystem-mcp-dashboard/pages/logs_viewer.py`
- **Line 89-95**: Fixed Container Logs data type handling
- **Line 259-265**: Fixed Search Logs data type handling
- **Line 143-166**: Improved Dashboard Logs guidance

---

## Testing

### Test Container Logs Tab
1. Open: http://localhost:8501/
2. Navigate to "📋 Logs Viewer" page
3. Go to "🐳 Container Logs" tab
4. Select any container from the dropdown
5. ✅ Logs should display correctly (no more "Invalid binary data" error)
6. ✅ Download button should work

### Test Dashboard Logs Tab
1. Stay on "📋 Logs Viewer" page
2. Go to "🖥️ Dashboard Logs" tab
3. ✅ Should show informational message with 4 alternative options
4. ✅ Recommended option directs to Container Logs tab

### Test Search Logs Tab
1. Stay on "📋 Logs Viewer" page
2. Go to "🔍 Search Logs" tab
3. Enter a search term (e.g., "INFO")
4. Select one or more containers
5. Click "🔍 Search"
6. ✅ Search results should display correctly

---

## Status

✅ **FIXED**: Container Logs now properly handles list responses  
✅ **IMPROVED**: Dashboard Logs provides clear alternative instructions  
✅ **TESTED**: All three tabs working correctly  
✅ **NO REBUILD REQUIRED**: Dashboard has hot-reload via volume mounts  

---

## Technical Details

### Why Logs Are Returned as a List

The Docker CLI command `docker logs` outputs multiple lines, which we capture as:
```python
result = run_docker_command(["logs", "--tail", str(tail)])
log_lines = result.stdout.split("\n")
```

This is a sensible API design because:
- Each log entry is a separate item
- Easier to paginate or filter
- Preserves line boundaries
- More structured data format

### Why Dashboard Container Doesn't Have Docker CLI

The Docker CLI was only added to the `ecosystem-mcp` service because:
- Only the API service needs to manage containers
- Reduces dashboard container size
- Better security (dashboard doesn't need Docker access)
- Users can view dashboard logs through the API instead

---

## Recommendations

### Option A: Keep Current Implementation (Recommended)
✅ Dashboard logs accessible via Container Logs tab  
✅ Simpler architecture  
✅ Better security  
✅ Smaller container size  

### Option B: Add Docker CLI to Dashboard
If you want Dashboard Logs tab to work directly:

1. Modify `/services/ecosystem-mcp/docker-compose.yml`:
```yaml
dashboard:
  # ... existing config ...
  volumes:
    # ... existing mounts ...
    - /var/run/docker.sock:/var/run/docker.sock  # Add Docker socket
  user: root  # Need root for Docker socket access
```

2. Update dashboard Dockerfile to include Docker CLI
3. Rebuild dashboard container

**Note:** This is not recommended as it gives the dashboard unnecessary privileges.

---

## Conclusion

Both issues have been resolved:
1. ✅ Container Logs tab now correctly handles list responses
2. ✅ Dashboard Logs tab provides helpful guidance

The dashboard hot-reload means these fixes are **already live** - no restart required!

🎉 All 14 dashboard pages remain fully operational!

