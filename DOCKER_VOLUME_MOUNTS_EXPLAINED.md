# 🐳 Docker Volume Mounts Explained

**Question:** Why does `/app` have a git repo in the container when `/Users/mykalthomas/Documents/work/Hackathon` is the actual repo?

**Answer:** There are **TWO DIFFERENT** git repositories mounted in your container!

---

## 🗺️ The Volume Mount Map

### Your Container Has TWO Mounts:

```
HOST                                              CONTAINER
====================================================|============
/Users/mykalthomas/Documents/work/Hackathon       →  /repo
/Users/mykalthomas/Documents/work/Hackathon/.git  →  /repo/.git ✓

services/ecosystem-mcp/                           →  /app
services/ecosystem-mcp/.git                       →  /app/.git ✓
```

**Both directories are git repositories, but they're DIFFERENT repos!**

---

## 🔍 The Two Git Repositories

### 1. `/repo` - The Main Hackathon Repository

**Host Path:** `/Users/mykalthomas/Documents/work/Hackathon`

**Container Path:** `/repo`

**What it is:**
- Your entire Hackathon project
- The parent/root repository
- Contains all services, documentation, configs
- Currently on branch: `automated-refactor`

**Contents:**
```
/repo/
├── .git/                    ← Main repo git history
├── services/
│   ├── ecosystem-mcp/       ← This is a separate repo!
│   ├── llm-gateway/
│   ├── mcp-interpreter/
│   └── ...
├── docker-compose.yml
├── docs/
└── ...
```

**Git Status:**
```bash
$ docker exec ecosystem-mcp-service git -C /repo status
On branch automated-refactor
Changes not staged for commit:
  modified:   services/ecosystem-mcp-dashboard/...
  modified:   services/ecosystem-mcp/...
```

---

### 2. `/app` - The ecosystem-mcp Service Repository

**Host Path:** `/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp`

**Container Path:** `/app`

**What it is:**
- Just the ecosystem-mcp service
- A **separate git repository** (likely a submodule or independent repo)
- Currently on branch: `master`
- This is what the container's code runs from

**Contents:**
```
/app/
├── .git/                    ← Service-specific git history
├── src/
│   ├── api/
│   ├── ingestion/
│   ├── services/
│   └── ...
├── requirements.txt
├── Dockerfile
└── ...
```

**Git Status:**
```bash
$ docker exec ecosystem-mcp-service git -C /app status
On branch master
Changes not staged for commit:
  modified:   various files
```

---

## 🤔 Why Two Repositories?

### Architecture Pattern: Monorepo with Service Repos

This is a **nested repository structure**:

**Main Repository (Hackathon):**
- Contains the entire project
- Manages infrastructure, configs, docker-compose
- Coordinates multiple services

**Service Repository (ecosystem-mcp):**
- Independent git history for this service
- Can be developed/versioned separately
- Could be a git submodule or subtree
- Has its own commits, branches, tags

**Benefits:**
1. ✅ Service can be versioned independently
2. ✅ Service can have its own release cycle
3. ✅ Service could be moved to separate repo later
4. ✅ Clear boundaries between services
5. ✅ Each service tracks its own history

---

## 📊 The Container Volume Setup

### Actual Docker Mounts (from `docker inspect`):

```
Source                                                          Destination
====================================================================|===========
/Users/.../Hackathon/services/ecosystem-mcp/data/backups       →   /app/data/backups
/Users/.../Hackathon                                           →   /repo
/var/run/docker.sock                                           →   /var/run/docker.sock
/Users/.../Hackathon/services/ecosystem-mcp/data/chroma_db     →   /app/data/chroma_db
```

**Plus the main service code:**
```
/Users/.../Hackathon/services/ecosystem-mcp                    →   /app (implicit)
```

---

## 🎯 Why `/app` is Used for Ingestion

### The GitService Configuration

**File:** `services/ecosystem-mcp/src/config.py`

```python
class Settings(BaseSettings):
    # Git repository path
    git_repo_path: Path = Field(
        default="/app",  # ← Points to /app!
        description="Path to git repository"
    )
```

**Why `/app` makes sense:**
1. ✅ It's the **service's own repository**
2. ✅ Contains the service's code and documentation
3. ✅ Has complete git history for the service
4. ✅ Ingestion documents the service itself
5. ✅ Most relevant for RAG queries about the service

---

## 🔄 The Complete Picture

### When You Ingest from `/app`:

```
1. GitService opens: /app/.git
2. Scans files in: /app/
3. Finds: Python files, Markdown docs, YAML configs
4. Gets git history: From /app/.git
5. Extracts commits: Service-specific commits
6. Links documents: To service's git commits
7. Result: Documentation of the ecosystem-mcp service
```

**Files ingested:**
- `/app/src/**/*.py` - Service source code
- `/app/*.md` - Service documentation
- `/app/*.yaml` - Service configs
- `/app/tests/**/*.py` - Service tests

### If You Were to Ingest from `/repo`:

```
1. GitService opens: /repo/.git
2. Scans files in: /repo/
3. Finds: ALL files across ALL services
4. Gets git history: From main repo
5. Extracts commits: Project-wide commits
6. Links documents: To main repo commits
7. Result: Documentation of entire Hackathon project
```

**Files ingested:**
- `/repo/services/*/` - All services
- `/repo/docs/` - All documentation
- `/repo/*.md` - Project documentation
- `/repo/config/` - Infrastructure configs

---

## 💡 Which Path Should You Use?

### Option 1: `/app` (Current Default) ✅ Recommended

**What you get:**
- Documents about the ecosystem-mcp service
- Service-specific code and docs
- Service's git history
- Focused, relevant content

**Use when:**
- You want to query about ecosystem-mcp
- Building a service-specific RAG
- Service documentation and code
- Smaller dataset, faster ingestion

**Example queries:**
- "How does the ingestion pipeline work?"
- "What are the API endpoints?"
- "Show me the caching implementation"

---

### Option 2: `/repo` (The Full Project)

**What you get:**
- Documents about the ENTIRE project
- All services, all documentation
- Main repo's git history
- Comprehensive but large

**Use when:**
- You want to query about the whole project
- Need cross-service information
- Want to include infrastructure docs
- Larger dataset, longer ingestion

**Example queries:**
- "How do services communicate?"
- "What's the overall architecture?"
- "Show me all the dashboards"
- "What services exist?"

**To use this:**
```python
# Change config or pass parameter
repo_path = "/repo"
```

---

## 🧪 Test Both Paths

### Check `/app` (Service Repo):

```bash
# Git info
docker exec ecosystem-mcp-service git -C /app log --oneline -5

# File count
docker exec ecosystem-mcp-service find /app -name "*.py" -o -name "*.md" | wc -l

# Branch
docker exec ecosystem-mcp-service git -C /app branch --show-current
```

### Check `/repo` (Main Repo):

```bash
# Git info
docker exec ecosystem-mcp-service git -C /repo log --oneline -5

# File count
docker exec ecosystem-mcp-service find /repo -name "*.py" -o -name "*.md" | wc -l

# Branch
docker exec ecosystem-mcp-service git -C /repo branch --show-current
```

---

## 📊 Current Status

### What You Have Now:

```
Container: ecosystem-mcp-service

Mounted Volumes:
├── /app
│   ├── Source: services/ecosystem-mcp/
│   ├── Git: ✅ YES (.git exists)
│   ├── Branch: master
│   └── Files: ~2,000-3,000
│
└── /repo
    ├── Source: Hackathon/
    ├── Git: ✅ YES (.git exists)
    ├── Branch: automated-refactor
    └── Files: ~10,000-50,000
```

**Default ingestion path:** `/app`

**Why your jobs failed:**
- Used host path: `/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp`
- Should use container path: `/app`
- The host path is not accessible **inside** the container

---

## 🎯 The Fix

### Your 18 Failed Jobs Used:

```
Path: /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp
                  ☝️ This is a HOST path!
```

**Inside the container, this path doesn't exist!**

The container sees:
- ✅ `/app` - Mounted from host's `services/ecosystem-mcp/`
- ✅ `/repo` - Mounted from host's `Hackathon/`
- ❌ `/Users/...` - Not mounted, doesn't exist

### Use This Instead:

```
Path: /app
      ☝️ This is the CONTAINER path that maps to your host directory
```

---

## 🚀 Summary

### The Key Insight:

**Docker volumes create a mapping:**

```
HOST (what you see)                     CONTAINER (what app sees)
========================================|=========================
/Users/.../Hackathon/services/         
  ecosystem-mcp/                    →   /app/
  ecosystem-mcp/.git                →   /app/.git
```

**When you specify a path in the dashboard, you're specifying a CONTAINER path, not a HOST path!**

### What to Remember:

1. ✅ **Use `/app`** - Service repository (default, recommended)
2. ✅ **Or use `/repo`** - Full project repository
3. ❌ **Don't use host paths** - Container can't see them
4. ✅ **Both are git repos** - Both work for ingestion
5. ✅ **Different content** - Choose based on what you want to ingest

---

## 🎓 Docker Volumes 101

### How Volume Mounts Work:

**docker-compose.yml:**
```yaml
services:
  ecosystem-mcp-service:
    volumes:
      # Format: HOST_PATH:CONTAINER_PATH
      - ./services/ecosystem-mcp:/app
      - .:/repo
```

**What this means:**
- Files in host's `./services/ecosystem-mcp/` appear at `/app` in container
- Files in host's `.` (project root) appear at `/repo` in container
- Changes in host are visible in container (and vice versa)
- Git repos in host are accessible in container

**The Magic:**
- Host and container share the same files
- But use different paths to access them
- Container path: `/app`
- Host path: `/Users/.../Hackathon/services/ecosystem-mcp`

---

## 📚 Next Steps

### Test Ingestion with Correct Path:

**Option A: Service Only (Recommended)**
```
Dashboard → Ingestion Manager
Path: /app
Mode: full
→ Start Ingestion
→ Result: ~2,000-3,000 documents about ecosystem-mcp
```

**Option B: Full Project**
```
Dashboard → Ingestion Manager
Path: /repo
Mode: full
→ Start Ingestion
→ Result: ~10,000+ documents about entire Hackathon project
```

### Verify Paths First:

```bash
# Check what's in /app
docker exec ecosystem-mcp-service ls -la /app | head -20

# Check what's in /repo  
docker exec ecosystem-mcp-service ls -la /repo | head -20

# Verify both are git repos
docker exec ecosystem-mcp-service git -C /app status
docker exec ecosystem-mcp-service git -C /repo status
```

---

**Status:** ✅ **Now you understand the volume mounts!**

**Key Takeaway:** Your host directory is mounted at `/app` in the container, and it includes the `.git` directory, so the container sees a complete git repository at `/app`.

