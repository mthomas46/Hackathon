# 📥 Dashboard Ingestion Quick Start Guide

**Date:** October 16, 2025  
**Purpose:** How to successfully start ingestion jobs from the dashboard

---

## ✅ **Quick Fix Summary**

### **Issue 1: Connection Refused** ✅ FIXED
- **Problem:** Dashboard was connecting to `http://localhost:8000`
- **Solution:** Restarted dashboard with `API_BASE_URL=http://ecosystem-mcp-service:8000`
- **Status:** ✅ Fixed - Dashboard now connects successfully

### **Issue 2: Path Validation** ✅ SOLVED
- **Problem:** Host machine paths don't exist inside Docker container
- **Solution:** Use container mount point `/host` instead
- **Status:** ✅ Resolved - See configuration below

---

## 🚀 **How to Start Ingestion (Step-by-Step)**

### **1. Open the Dashboard**
```
http://localhost:8501
```

### **2. Navigate to Ingestion Manager**
- Click **"📥 Ingestion Manager"** in the left sidebar
- Go to the **"🚀 Start Ingestion"** tab

### **3. Configure the Ingestion**

Use these settings for a successful test ingestion:

```
┌─────────────────────────────────────────────────────────────┐
│ Configuration                                                │
├─────────────────────────────────────────────────────────────┤
│ Path Type:          ● Container Path                         │
│                                                              │
│ Repository Path:    /host                                    │
│                                                              │
│ Target Subdirectory: services/ecosystem-mcp                  │
│ (optional)          (or leave empty for entire repo)        │
│                                                              │
│ File Types:         .py                                      │
│                                                              │
│ Max Files:          50                                       │
│                                                              │
│ ☑ Skip Existing     (recommended for testing)               │
│                                                              │
│ ☑ Generate Embeddings                                        │
│                                                              │
│ Batch Size:         32                                       │
│                                                              │
│          [🚀 Start Ingestion]                                │
└─────────────────────────────────────────────────────────────┘
```

### **4. Click "Start Ingestion"**
- The job should start successfully
- You'll see a Job ID displayed
- Monitor progress in the **"📊 Job Status"** tab

---

## 🎯 **Path Configuration Explained**

### **Container Paths (Recommended) ✅**

| What to Enter | Why |
|---------------|-----|
| **Path Type:** Container Path | Access paths inside the Docker container |
| **Repository Path:** `/host` | Your entire project is mounted here |
| **Target Subdirectory:** `services/ecosystem-mcp` | Only process this subdirectory |

### **Path Mapping**

```
Your Mac (Host):
  /Users/mykalthomas/Documents/work/Hackathon
  
  ↓ Mounted as ↓
  
Docker Container:
  /host
  
Git Repository: ✅ Available at /host
```

### **Why Not Use Host Machine Path?**

The "Host Machine Path" option requires the path resolver service to translate paths, but:
- Path resolver endpoint may not be loaded
- Direct container paths are more reliable
- `/host` is already correctly mounted and accessible

---

## 📊 **Example Configurations**

### **Test Run (Small)**
```yaml
Path Type: Container Path
Repository Path: /host
Target Subdirectory: services/ecosystem-mcp/src/config.py
File Types: .py
Max Files: 1
Skip Existing: Yes
Generate Embeddings: Yes
```
**Result:** Process 1 file (very fast, good for testing)

### **Service Ingestion (Medium)**
```yaml
Path Type: Container Path
Repository Path: /host
Target Subdirectory: services/ecosystem-mcp
File Types: .py
Max Files: 50
Skip Existing: Yes
Generate Embeddings: Yes
```
**Result:** Process up to 50 Python files from the main service

### **Full Project (Large)**
```yaml
Path Type: Container Path
Repository Path: /host
Target Subdirectory: (empty - entire repo)
File Types: .py, .md, .yaml
Max Files: 500
Skip Existing: Yes
Generate Embeddings: Yes
Batch Size: 32
```
**Result:** Process up to 500 files of various types across entire project

---

## ⚡ **Performance Expectations**

With all optimizations active:

| Documents | Expected Time | Processing Rate |
|-----------|---------------|-----------------|
| 1-10 | < 5 seconds | Instant |
| 50 | ~10-30 seconds | ~2-5 docs/sec |
| 500 | ~2-4 minutes | ~2-4 docs/sec |
| 5,000 | ~15-20 minutes | ~4-6 docs/sec |

**Note:** Times assume generating embeddings. Without embeddings, it's 10× faster.

### **Skip Existing Optimization**

If documents are already ingested:
- Bloom filter checks: ~5,000 docs/second ⚡
- Minimal processing time
- Example: 5,561 docs checked in 1.14 seconds

---

## 🔍 **Monitoring Progress**

### **Real-Time Monitoring**
1. Go to **"📊 Job Status"** tab
2. Find your job by Job ID
3. Watch metrics update:
   - Documents processed
   - Embeddings generated
   - Processing rate
   - Current status

### **Via API**
```bash
# Check job status
curl http://localhost:8000/api/v1/admin/ingest/{job_id}

# View all jobs
curl http://localhost:8000/api/v1/admin/ingest/status
```

---

## 🐛 **Troubleshooting**

### **Connection Refused Error**
```
❌ Connection error: [Errno 111] Connection refused
```

**Solution:** Dashboard needs correct API URL
- Check LEFT SIDEBAR → "🔗 Configuration"
- Should show: `http://ecosystem-mcp-service:8000`
- If wrong, restart dashboard (see below)

**Fix command:**
```bash
docker stop ecosystem-mcp-dashboard && docker rm ecosystem-mcp-dashboard
docker run -d --name ecosystem-mcp-dashboard \
  --network ecosystem-mcp \
  -p 8501:8501 \
  -v /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-dashboard:/app \
  -e API_BASE_URL=http://ecosystem-mcp-service:8000 \
  -e PYTHONPATH=/app \
  ecosystem-mcp-dashboard:latest
```

### **Path Not in Git Repository**
```
❌ Path validation failed: Path is not in a git repository
```

**Solution:** Use container path `/host`
- Select **"Container Path"** for Path Type
- Enter `/host` as Repository Path
- `/host` is the mounted git repository

### **No Documents Processed**
```
Job completed: 0 documents processed
```

**Possible reasons:**
1. All documents already ingested (check skipped count)
2. File type filter too restrictive
3. Max files limit too low
4. Target subdirectory has no matching files

**Solutions:**
- Check "skipped_documents" in job details
- Expand file types (e.g., `.py, .md, .yaml`)
- Increase max files
- Verify target subdirectory exists

---

## ✅ **Current System Status**

All services operational and ready:

| Service | Status | Port | Purpose |
|---------|--------|------|---------|
| ecosystem-mcp-service | ✅ Healthy | 8000 | Main API |
| ecosystem-mcp-embedding | ✅ Healthy | 8001 | FastEmbed |
| ecosystem-mcp-dashboard | ✅ Healthy | 8501 | UI |
| PostgreSQL | ✅ Healthy | 5432 | Metadata |
| Redis | ✅ Healthy | 6379 | Cache |
| ChromaDB | ✅ Healthy | Internal | Vectors |

**Optimizations Active:**
- ✅ Phase 1: Background Worker
- ✅ Phase 2: Bloom Filters (90% query reduction)
- ✅ Phase 2: Database Indexes (6× faster)
- ✅ Phase 2: Parallel Processing (20 concurrent)
- ✅ Phase 3: FastEmbed INT8 (50% memory)
- ✅ Phase 4: Multi-level Cache (L1 + L2)

**Performance Gains:**
- 7.5× faster ingestion
- 50% less memory
- 90% fewer database queries

---

## 🎯 **Recommended First Test**

Try this configuration for your first test:

```yaml
Path Type: Container Path
Repository Path: /host
Target Subdirectory: services/ecosystem-mcp-dashboard
File Types: .py
Max Files: 10
Skip Existing: Yes
Generate Embeddings: Yes
Batch Size: 32
```

This will:
- ✅ Process a small, manageable number of files
- ✅ Complete in < 10 seconds
- ✅ Demonstrate all optimizations working
- ✅ Show you the full workflow

---

## 📚 **Additional Resources**

- **API Documentation:** http://localhost:8000/docs
- **Performance Test Results:** `PERFORMANCE_TEST_SUCCESS.md`
- **Configuration Guide:** `CONFIGURATION_AND_DEPLOYMENT_SUCCESS.md`
- **Optimization Details:** `ALL_PHASES_COMPLETE.md`

---

## 🎊 **You're Ready!**

All issues resolved. The ingestion system is fully operational and optimized.

**Start your first ingestion now!** 🚀

