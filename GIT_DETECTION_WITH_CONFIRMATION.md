# 🔍 Git Detection with User Confirmation

**Automatic git repository detection with smart subdirectory handling**

---

## 🎯 **Overview**

When you select a path for ingestion that's **inside** a git repository (like a subdirectory), the system now:

1. **✅ Automatically detects** the git repository root
2. **📊 Shows you** what it found
3. **🤔 Asks for confirmation** about what to ingest
4. **⚠️ Warns about** nested git repos (submodules)

---

## 🐛 **Problem Solved**

### Original Issue:
```
You tried to ingest: /Users/.../Hackathon/services/ecosystem-mcp-dashboard
Error: "Path is not in a git repository"
```

**Why it failed:**
- The container couldn't see the host filesystem
- Git detection was running **inside the container**
- Host path `/Users/.../Hackathon` not accessible from container
- Git root detection failed ❌

---

## ✅ **Solution**

### Enhanced Git Detection:

```python
# NEW: Smart host path git detection
1. System detects: "This is a HOST path" 
2. Maps to mounted location: /Users/.../Hackathon → /app
3. Checks git in mounted path: git -C /app
4. Finds .git directory: /app/.git exists ✅
5. Maps back to host path: /Users/.../Hackathon
6. Returns: is_git_repo=True, git_root=/Users/.../Hackathon
```

---

## 🎨 **User Experience**

### Scenario 1: Subdirectory Selected

**You select:**
```
/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-dashboard
```

**System detects:**
- 📂 **Your path:** `services/ecosystem-mcp-dashboard`
- 📦 **Git root:** `/Users/.../Hackathon`
- ⚠️ **Status:** Subdirectory within git repo

**System asks:**
```
🔍 Git Repository Detection Results

📂 Your Selected Path:
/Users/.../Hackathon/services/ecosystem-mcp-dashboard
📁 Subdirectory: services/ecosystem-mcp-dashboard

📦 Detected Git Repository:
/Users/.../Hackathon
⚠️ Selected path is inside a git repository

─────────────────────────────────────────────

🤔 What does this mean?

You selected a subdirectory within a larger git repository:
- Selected: services/ecosystem-mcp-dashboard
- Git Root: /Users/.../Hackathon

📋 Your Options:

○ 🎯 Just this subdirectory: services/ecosystem-mcp-dashboard
○ 📦 Entire git repository: /Users/.../Hackathon

✅ I understand and want to proceed with this configuration
```

**You choose:**
- **Option 1:** 🎯 Just this subdirectory
  - Only `services/ecosystem-mcp-dashboard` will be ingested
  - Faster, focused on specific component
  - Good for targeted updates

- **Option 2:** 📦 Entire git repository  
  - All files in `/Users/.../Hackathon` ingested
  - Complete project context
  - Better for comprehensive analysis

**Then:**
- ✅ Check the confirmation box
- 🚀 Ingestion proceeds with your choice

---

### Scenario 2: Root Directory Selected

**You select:**
```
/Users/mykalthomas/Documents/work/Hackathon
```

**System detects:**
- 📦 **Git root:** Same as selected path
- ✅ **Status:** Root directory (not a subdirectory)

**System behavior:**
```
✅ Path validated: /app
⏳ Starting ingestion...
```

- **No confirmation needed** - you selected the root
- Proceeds directly to ingestion

---

## 🔧 **How It Works**

### 1. **Path Resolution:**
```python
# User provides host path
host_path = "/Users/.../Hackathon/services/ecosystem-mcp-dashboard"

# System normalizes
normalized = "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-dashboard"

# System detects: is_host_mount=True
```

### 2. **Git Detection (Container → Host Mapping):**
```python
# Inside container, trying to check HOST path
in_container = True
is_host_path = True

# Map host path to mounted container path
host_path: /Users/.../Hackathon/services/ecosystem-mcp-dashboard
mounted_at: /app/services/ecosystem-mcp-dashboard

# Check git in mounted location
$ git -C /app/services/ecosystem-mcp-dashboard rev-parse --show-toplevel
→ /app

# Map container git root back to host
container_git_root: /app
host_git_root: /Users/.../Hackathon ✅
```

### 3. **Subdirectory Detection:**
```python
# Calculate relative path
git_root: /Users/.../Hackathon
selected: /Users/.../Hackathon/services/ecosystem-mcp-dashboard

relative = selected.relative_to(git_root)
→ "services/ecosystem-mcp-dashboard"

# Detect subdirectory targeting
if relative != ".":
    is_subdirectory = True
    target_subdir = "services/ecosystem-mcp-dashboard"
```

### 4. **User Confirmation:**
```python
if is_subdirectory:
    # Show detection results
    display_git_info(git_root, target_subdir)
    
    # Ask user choice
    choice = user_selects_option()
    # → "Just subdirectory" or "Entire repo"
    
    # Wait for confirmation
    confirmed = user_confirms_checkbox()
    
    if confirmed:
        proceed_with_ingestion(choice)
    else:
        st.stop()  # Don't proceed
```

---

## 📋 **Configuration Options**

### Option A: Subdirectory Only
```json
{
  "repo_path": "/app",
  "mode": "quick",
  "resolve_host_path": false,
  "target_subdirectory": "services/ecosystem-mcp-dashboard"
}
```

**Effect:**
- Ingestion scoped to `services/ecosystem-mcp-dashboard`
- Only files in that directory processed
- Git history still tracked from root

**Use When:**
- ✅ Working on specific service/component
- ✅ Want faster ingestion
- ✅ Need focused analysis

### Option B: Entire Repository
```json
{
  "repo_path": "/app",
  "mode": "quick",
  "resolve_host_path": false,
  "target_subdirectory": null
}
```

**Effect:**
- Entire repository ingested
- All services, docs, configs processed
- Complete project context

**Use When:**
- ✅ Need full project understanding
- ✅ Cross-service analysis required
- ✅ Building comprehensive documentation

---

## ⚠️ **Nested Git Repositories**

### What Are They?
- Git submodules
- Independent git repos within parent repo
- Separate `.git` directories

### How They're Handled:
```
Your Repo:
/Users/.../Hackathon/.git

Contains Submodule:
/Users/.../Hackathon/vendor/library/.git

System Behavior:
1. Detects parent git: /Users/.../Hackathon ✅
2. During ingestion: Detects nested .git in vendor/library
3. Handles appropriately (respects submodule boundaries)
4. Tracks both repos separately
```

### Warning Shown:
```
⚠️ Note on Nested Git Repositories:

If this directory contains git submodules or nested repositories,
they will be detected and handled appropriately during ingestion.
```

---

## 🎯 **Benefits**

### 1. **Prevents Errors**
- ❌ Old: "Path is not in a git repository"
- ✅ New: Automatically finds git root ✅

### 2. **Smart Detection**
- Checks host filesystem via mounted volumes
- Maps paths correctly (host ↔ container)
- Handles subdirectories intelligently

### 3. **User Control**
- **You decide:** Subdirectory vs full repo
- **You confirm:** No accidental ingestion
- **You understand:** Clear explanation of what's happening

### 4. **Flexibility**
- ✅ Ingest specific services
- ✅ Ingest entire projects
- ✅ Handle complex repo structures

---

## 📊 **Examples**

### Example 1: Dashboard Service Only
```
Selected: /Users/.../Hackathon/services/ecosystem-mcp-dashboard

Detected Git Root: /Users/.../Hackathon
Subdirectory: services/ecosystem-mcp-dashboard

Choice: 🎯 Just this subdirectory

Result:
- Ingests: services/ecosystem-mcp-dashboard/**
- Skips: services/other-service/, tests/, docs/, etc.
- Duration: ~30 seconds (faster)
- Documents: ~50-100
```

### Example 2: Entire Hackathon Project
```
Selected: /Users/.../Hackathon/services/ecosystem-mcp-dashboard

Detected Git Root: /Users/.../Hackathon
Subdirectory: services/ecosystem-mcp-dashboard

Choice: 📦 Entire git repository

Result:
- Ingests: /** (everything in Hackathon)
- Includes: All services, tests, docs, configs
- Duration: ~5-10 minutes (comprehensive)
- Documents: ~500-1000+
```

### Example 3: Root Directory (No Confirmation)
```
Selected: /Users/.../Hackathon

Detected Git Root: /Users/.../Hackathon
Subdirectory: None (root)

Result:
- No confirmation needed
- Proceeds directly
- Ingests entire repo
```

---

## 🔍 **Technical Details**

### Mount Point Detection:
```python
possible_mounts = [
    ("/app", "/Users/mykalthomas/Documents/work/Hackathon"),
    ("/workspace", "/Users/mykalthomas/Documents/work"),
    ("/host", ""),  # Catch-all
]

# For path: /Users/.../Hackathon/services
# Matches: ("/app", "/Users/.../Hackathon")
# Maps to: /app/services
# Checks git: /app/.git exists ✅
# Returns: /Users/.../Hackathon
```

### Git Command Flow:
```bash
# Inside container
$ git -C /app/services/ecosystem-mcp-dashboard rev-parse --show-toplevel
/app

# Or manual search
$ ls /app/.git
branches/ config description HEAD hooks/ info/ objects/ refs/
# → Git root found at /app

# Map back to host
container_path: /app
host_prefix: /Users/mykalthomas/Documents/work/Hackathon
result: /Users/mykalthomas/Documents/work/Hackathon
```

### Session State Management:
```python
# After user confirms choice
if user_chose_subdirectory:
    st.session_state.confirmed_target_subdir = "services/ecosystem-mcp-dashboard"
else:
    st.session_state.confirmed_target_subdir = None

# Used in ingestion request
request_data = {
    "repo_path": "/app",
    "target_subdirectory": st.session_state.confirmed_target_subdir
}
```

---

## 🧪 **Testing**

### Test Case 1: Subdirectory Detection
```python
path = "/Users/.../Hackathon/services/ecosystem-mcp-dashboard"

resolver = HostPathResolver()
resolved = resolver.resolve(path)

assert resolved.is_subdirectory == True
assert resolved.git_root == "/Users/.../Hackathon"
assert resolved.target_subdir == "services/ecosystem-mcp-dashboard"
```

### Test Case 2: Root Directory
```python
path = "/Users/.../Hackathon"

resolver = HostPathResolver()
resolved = resolver.resolve(path)

assert resolved.is_subdirectory == False
assert resolved.git_root == "/Users/.../Hackathon"
assert resolved.target_subdir is None
```

### Test Case 3: Host Path Mapping
```python
# In container
path = "/Users/.../Hackathon/services"

git_root = resolver._find_git_root(path, is_host_path=True)

# Should map to /app, find git, map back
assert git_root == "/Users/.../Hackathon"
```

---

## 📝 **Usage Guide**

### Step-by-Step:

1. **Open Dashboard:** http://localhost:8501
2. **Go to:** 📥 Ingestion Manager
3. **Enter path** (e.g., services/ecosystem-mcp-dashboard)
4. **Click:** 🚀 Start Ingestion
5. **Review** git detection results
6. **Choose** subdirectory or full repo
7. **Confirm** checkbox
8. **Watch** ingestion proceed ✨

### Quick Tips:

- **For focused work:** Choose subdirectory
- **For full context:** Choose entire repo
- **Unsure?** Start with subdirectory, can always re-run
- **Nested repos?** System handles them automatically

---

## 🔄 **Workflow Diagram**

```
┌─────────────────────────────────────────┐
│   User Enters Path (e.g., services/)   │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│   System: Is this a host path?          │
│   → Yes: /Users/.../                    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│   Map to Container: /app/services/      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│   Check Git: git -C /app/services       │
│   Find .git: /app/.git                  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│   Map Back: /Users/.../Hackathon        │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│   Calculate: services/ relative to root │
│   Detect: is_subdirectory=True          │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│   Show User: Git Detection Results      │
│   - Your Path: services/                │
│   - Git Root: /Users/.../Hackathon     │
│   - Options: Subdirectory vs Full      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│   User Chooses & Confirms               │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│   ✅ Ingestion Proceeds                 │
│   With: target_subdirectory (if chosen) │
└─────────────────────────────────────────┘
```

---

## ✅ **Status**

**IMPLEMENTED** ✅

- ✅ Enhanced git detection
- ✅ Host path → container mapping
- ✅ Subdirectory detection
- ✅ User confirmation UI
- ✅ Choice preservation (session state)
- ✅ Request integration
- ✅ Documentation complete

**Date:** October 15, 2025  
**Version:** 1.0.0

---

**Try it now!** 🚀

Select any subdirectory in your Hackathon repo and see the smart detection in action!

