**Date:** November 19, 2025  
**Status:** Multi-Repository Access Solutions  
**Problem:** Need to ingest from arbitrary host directories without mounting each one individually  

---

## 🎯 Problem Statement

**Current Limitation:**
- Each repository requires a separate volume mount in `docker-compose.yml`
- Adding a new project requires:
  1. Edit docker-compose.yml
  2. Add volume mount
  3. Restart service
  4. Try ingestion

**Goal:**
- Access any directory in `/Users/mykalthomas/Documents/work/` without pre-mounting
- Dynamic, flexible repository access from the UI

---

## ✅ Solution 1: Parent Directory Mount (Recommended)

**Mount the entire parent directory once, access all projects forever.**

### Implementation

**Edit `docker-compose.yml`:**

```yaml
volumes:
  # OLD: Individual mounts for each project
  # - /Users/mykalthomas/Documents/work/Hackathon:/repo:ro
  # - /Users/mykalthomas/Documents/work/authservice:/authservice:ro
  # - /Users/mykalthomas/Documents/work/project3:/project3:ro  # Tedious!
  
  # NEW: Single mount for all projects
  - /Users/mykalthomas/Documents/work:/work:ro  # ✅ Mount ENTIRE work directory
```

### Usage

**In Dashboard Ingestion UI:**
- **Hackathon:** `/work/Hackathon`
- **AuthService:** `/work/authservice`
- **Any Project:** `/work/your-project-name`

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/work/authservice",
    "mode": "snapshot"
  }'
```

### Pros & Cons

✅ **Pros:**
- One-time setup, works forever
- No configuration changes needed for new projects
- Simple path structure: `/work/<project-name>`
- Read-only mount is secure

❌ **Cons:**
- Container can read ALL projects in `/work` directory
- If you have many large repos, Docker may scan them all during mount (usually not an issue)

---

## ✅ Solution 2: Host File Server + API Client

**Run a lightweight file server on your host that the container connects to via HTTP.**

### Architecture

```
┌─────────────────────────────────────┐
│         Host Machine                │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  File Server (Python/Node)   │  │
│  │  Listens on: localhost:8765  │  │
│  │  Serves: /Users/.../work/*   │  │
│  └──────────────────────────────┘  │
│              ↑                      │
│              │ HTTP                 │
│              ↓                      │
│  ┌──────────────────────────────┐  │
│  │  Docker Container            │  │
│  │  Connects to:                │  │
│  │  host.docker.internal:8765   │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

### Implementation

**1. Create Host File Server:**

```python
# ~/file_server.py
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import json

class FileServerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/Users/mykalthomas/Documents/work", **kwargs)
    
    def do_GET(self):
        if self.path == "/list":
            # List available repositories
            projects = os.listdir("/Users/mykalthomas/Documents/work")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"projects": projects}).encode())
        else:
            super().do_GET()

if __name__ == "__main__":
    port = 8765
    server = HTTPServer(("0.0.0.0", port), FileServerHandler)
    print(f"🚀 File server running on http://localhost:{port}")
    server.serve_forever()
```

**2. Start Server:**

```bash
python3 ~/file_server.py
# Or run in background:
nohup python3 ~/file_server.py > /tmp/file_server.log 2>&1 &
```

**3. Access from Container:**

The container can now fetch files via HTTP:
```python
import httpx

# List projects
response = httpx.get("http://host.docker.internal:8765/list")
projects = response.json()["projects"]

# Download file
response = httpx.get("http://host.docker.internal:8765/authservice/README.md")
content = response.text
```

### Pros & Cons

✅ **Pros:**
- No volume mounts needed at all
- Works with any directory structure
- Can add authentication/security easily
- Container remains isolated

❌ **Cons:**
- Requires running a separate server
- Slower than direct file access
- Need to fetch files over HTTP (not direct read)
- More complex architecture

---

## ✅ Solution 3: Hybrid Worker Approach

**Run ingestion worker on host for local paths, in container for remote/shared paths.**

### Architecture

```
┌─────────────────────────────────────────┐
│            Host Machine                 │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Ingestion Worker (Host)        │   │
│  │  - Reads local filesystem       │   │
│  │  - Direct file access           │   │
│  │  - Writes to PostgreSQL/Chroma  │   │
│  └─────────────────────────────────┘   │
│              ↑ ↓                        │
│              API                        │
│              ↑ ↓                        │
│  ┌─────────────────────────────────┐   │
│  │  Docker Container               │   │
│  │  - API Server                   │   │
│  │  - Dashboard                    │   │
│  │  - Routes jobs to host worker   │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### Implementation

**1. Create Host Worker Script:**

```python
#!/usr/bin/env python3
# ~/ecosystem-mcp-host-worker.py
"""
Host-side ingestion worker that can access any local directory.
Connects to the containerized API and databases.
"""
import asyncio
import os
from pathlib import Path
import httpx

# Environment configuration
API_URL = os.getenv("MCP_API_URL", "http://localhost:8000")
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://ecosystem:ecosystem_password@localhost:5432/ecosystem_mcp")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

async def process_local_ingestion(repo_path: str, mode: str):
    """
    Process ingestion from local filesystem.
    Has full access to host filesystem - no mount limitations!
    """
    print(f"🚀 Processing local ingestion: {repo_path}")
    
    # Can access ANY directory on host
    path = Path(repo_path)
    if not path.exists():
        print(f"❌ Path does not exist: {repo_path}")
        return
    
    # Your ingestion logic here
    # Read files directly from host filesystem
    # Write to containerized databases
    
    print(f"✅ Ingestion complete: {repo_path}")

async def listen_for_jobs():
    """
    Listen for ingestion jobs that need host access.
    """
    print("👂 Listening for host ingestion jobs...")
    
    while True:
        # Poll API for jobs marked as "host-path"
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/api/v1/admin/host-jobs")
            
            if response.status_code == 200:
                jobs = response.json().get("jobs", [])
                
                for job in jobs:
                    await process_local_ingestion(
                        repo_path=job["repo_path"],
                        mode=job["mode"]
                    )
        
        await asyncio.sleep(5)  # Poll every 5 seconds

if __name__ == "__main__":
    asyncio.run(listen_for_jobs())
```

**2. Run Worker:**

```bash
# Install dependencies in host Python
pip3 install httpx asyncio sqlalchemy psycopg2-binary

# Run worker
python3 ~/ecosystem-mcp-host-worker.py
```

**3. Configure API to Detect Host Paths:**

The API detects host paths and routes them to the host worker instead of container worker.

### Pros & Cons

✅ **Pros:**
- Unlimited access to host filesystem
- No volume mount configuration needed
- Best performance (direct file access)
- Security: worker only accesses what you run it with

❌ **Cons:**
- Most complex solution
- Need to keep host worker running
- Requires API modifications
- Need to manage two workers

---

## 📊 Solution Comparison

| Solution | Setup Complexity | Performance | Flexibility | Maintenance |
|----------|-----------------|-------------|-------------|-------------|
| **Parent Mount** | ⭐ Simple | ⭐⭐⭐ Excellent | ⭐⭐ Good | ⭐⭐⭐ Easy |
| **File Server** | ⭐⭐ Medium | ⭐⭐ Good | ⭐⭐⭐ Excellent | ⭐⭐ Medium |
| **Hybrid Worker** | ⭐⭐⭐ Complex | ⭐⭐⭐ Excellent | ⭐⭐⭐ Excellent | ⭐ Complex |

---

## 🎯 Recommended: Solution 1 (Parent Directory Mount)

**For 95% of use cases, mounting the parent directory is the best solution:**

### Quick Setup

```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp

# Edit docker-compose.yml (already done)
# Change:
#   - /Users/mykalthomas/Documents/work/Hackathon:/repo:ro
#   - /Users/mykalthomas/Documents/work/authservice:/authservice:ro
# To:
#   - /Users/mykalthomas/Documents/work:/work:ro

# Restart service
docker-compose up -d --force-recreate ecosystem-mcp
```

### Usage After Setup

**Dashboard:**
- Custom Repository Path: `/work/authservice`
- Custom Repository Path: `/work/any-project`
- Custom Repository Path: `/work/hackathon-2024`

**API:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/work/authservice",
    "mode": "snapshot"
  }'
```

---

## 🔒 Security Considerations

### Parent Mount (Solution 1)

**Security Profile:**
- ✅ Read-only mount (`:ro` flag)
- ✅ Container cannot modify host files
- ✅ Container cannot write outside mounted directory
- ⚠️ Container CAN read all projects in `/work`
- ⚠️ Don't put secrets in project directories

**Mitigation:**
- Keep secrets in separate directories (outside `/work`)
- Use `.gitignore` and `.dockerignore` for sensitive files
- Review which projects are in `/work` before mounting

### File Server (Solution 2)

**Additional Security:**
- Can add authentication (API keys, tokens)
- Can whitelist specific paths
- Can log all file access
- Can run with restricted user permissions

### Hybrid Worker (Solution 3)

**Additional Security:**
- Worker runs with your user permissions
- Can use file system ACLs
- Can be sandboxed in a separate environment
- Most secure as it respects OS-level permissions

---

## 📝 Implementation Status

### ✅ Already Implemented in Your Codebase

Your system already has sophisticated path resolution:

1. **HostPathResolver** (`src/utils/host_path_resolver.py`)
   - Resolves host paths to container paths
   - Detects git repository roots
   - Suggests mount configurations

2. **Path Validation** (in API endpoints)
   - Validates paths before ingestion
   - Provides helpful error messages
   - Suggests docker-compose configuration

3. **Flexible Path Support**
   - Can handle container paths (`/repo`, `/work`)
   - Can handle host paths (with resolution)
   - Auto-detects subdirectory targeting

### 🔄 What Changes With Parent Mount

**Before:**
```yaml
# docker-compose.yml
volumes:
  - /Users/mykalthomas/Documents/work/Hackathon:/repo:ro
  - /Users/mykalthomas/Documents/work/authservice:/authservice:ro
  - /Users/mykalthomas/Documents/work/project3:/project3:ro
  # ... need to add each project manually
```

**After:**
```yaml
# docker-compose.yml
volumes:
  - /Users/mykalthomas/Documents/work:/work:ro  # ALL projects accessible!
```

**Path Mapping:**
| Host Path | Container Path (Before) | Container Path (After) |
|-----------|------------------------|------------------------|
| `/Users/.../work/Hackathon` | `/repo` | `/work/Hackathon` |
| `/Users/.../work/authservice` | `/authservice` | `/work/authservice` |
| `/Users/.../work/new-project` | ❌ Not accessible | ✅ `/work/new-project` |

---

## 🚀 Migration Guide

### Step 1: Update docker-compose.yml

```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp
# File already updated above
```

### Step 2: Restart Service

```bash
docker-compose up -d --force-recreate ecosystem-mcp
```

### Step 3: Verify Mount

```bash
# Check if /work directory exists in container
docker exec ecosystem-mcp-service ls -la /work

# Should show all your projects:
# Hackathon/
# authservice/
# project-3/
# ...
```

### Step 4: Update Dashboard UI (Optional)

Add helpful placeholder text:

```
Repository Path:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/work/your-project-name
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Examples:
  • /work/Hackathon
  • /work/authservice
  • /work/my-new-project
```

### Step 5: Update Documentation

Add to README:
```markdown
## Available Projects

All projects in `/Users/mykalthomas/Documents/work/` are accessible at:
- Container path: `/work/<project-name>`

To ingest a project:
1. Go to Ingestion Manager
2. Enter: `/work/<your-project-name>`
3. Select mode and start ingestion
```

---

## 💡 Pro Tips

### 1. List Available Projects

Add endpoint to API:
```python
@router.get("/available-repos")
async def list_available_repos():
    """List all accessible repositories."""
    work_dir = Path("/work")
    if not work_dir.exists():
        return {"repos": []}
    
    repos = []
    for item in work_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            # Check if it's a git repo
            if (item / ".git").exists():
                repos.append({
                    "name": item.name,
                    "path": f"/work/{item.name}",
                    "is_git_repo": True
                })
    
    return {"repos": repos}
```

Then dashboard can show a dropdown of available projects!

### 2. Path Autocomplete

Add autocomplete in dashboard:
```python
# When user types in path field, suggest from /work/*
available_repos = api.get_available_repos()
suggestions = [r["path"] for r in available_repos]
```

### 3. Breadcrumb Navigation

Show which part of `/work` hierarchy you're browsing:
```
Work > authservice > services > auth-api
```

---

## ✅ Summary

**Recommended Solution:** Mount parent directory (`/work`)

**Advantages:**
- ✅ One-time setup
- ✅ Access ALL current and future projects
- ✅ No configuration changes needed for new projects
- ✅ Simple, clean path structure
- ✅ Works with existing path resolution code
- ✅ Read-only for security

**Implementation:**
1. Change one line in docker-compose.yml
2. Restart service
3. Access any project at `/work/<name>`

**You're done!** No more mounting individual directories. 🎉

