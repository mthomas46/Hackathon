# 🚀 Deployment Guide - Ecosystem MCP Service

**IMPORTANT:** This guide explains the CORRECT way to deploy code changes.

---

## ❌ **NEVER DO THIS**

```bash
# ❌ WRONG: Copying files and restarting
docker cp src/file.py ecosystem-mcp-service:/app/src/file.py
docker restart ecosystem-mcp-service
```

**Why this is wrong:**
1. Python caches imported modules in memory
2. `docker restart` doesn't reload Python modules
3. Your code changes won't actually run
4. Bytecode (`.pyc`) files persist in `__pycache__`
5. You'll waste hours debugging "why isn't my fix working?"

---

## ✅ **ALWAYS DO THIS**

### **Method 1: Full Rebuild (Recommended)**

```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp

# Stop and remove the container
docker-compose down ecosystem-mcp

# Rebuild and start
docker-compose up -d --force-recreate --build ecosystem-mcp

# Wait for startup
sleep 15

# Verify health
curl -f http://localhost:8000/health || echo "❌ Health check failed!"
```

**Why this works:**
- `--build` rebuilds the Docker image
- `COPY . .` in Dockerfile includes your latest code
- Fresh Python process with no cached modules
- Clean `__pycache__` directories
- Guaranteed to run your new code

---

### **Method 2: Quick Deploy Script**

Use the provided deployment script:

```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp

# Deploy with automatic health check
./scripts/deploy.sh
```

The script does:
1. Rebuilds the container
2. Waits for service to be healthy
3. Verifies the API is responding
4. Shows git commit of deployed code

---

## 📝 **Deployment Checklist**

Before deploying:

- [ ] All changes committed to git
- [ ] Tests passing (if any)
- [ ] No linting errors
- [ ] Requirements.txt updated (if dependencies changed)

Deploy:

- [ ] Use `docker-compose up --build` (not `docker cp`)
- [ ] Wait for health check to pass
- [ ] Check logs for startup errors
- [ ] Verify service is responding

After deploy:

- [ ] Test the feature you changed
- [ ] Check for any errors in logs
- [ ] Monitor metrics/errors

---

## 🔍 **Verifying Deployment**

### **1. Check Container is Running**

```bash
docker ps --filter name=ecosystem-mcp-service
```

Expected: Status should be "Up" and "healthy"

### **2. Check Health Endpoint**

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

Expected: `{"status": "healthy", ...}`

### **3. Check Git Commit**

```bash
docker logs ecosystem-mcp-service 2>&1 | grep "Running code version"
```

Expected: Should show the latest commit hash

### **4. Check Worker is Running**

```bash
docker logs ecosystem-mcp-service 2>&1 | grep "IngestionWorker started"
```

Expected: `✅ IngestionWorker started`

### **5. Check for Errors**

```bash
docker logs ecosystem-mcp-service 2>&1 | grep -E "ERROR|Exception" | tail -20
```

Expected: No recent errors (old errors from previous runs are okay)

---

## 🐛 **Troubleshooting**

### **"My changes aren't working!"**

**Diagnosis:**
```bash
# Check what code is actually running
docker exec ecosystem-mcp-service cat /app/src/your_file.py | grep "your_change"
```

If your change isn't there:
- You used `docker cp` (wrong method)
- You forgot to rebuild with `--build`
- Container is running old image

**Solution:**
```bash
# Force complete rebuild
docker-compose down ecosystem-mcp
docker-compose build --no-cache ecosystem-mcp
docker-compose up -d ecosystem-mcp
```

### **"Container won't start"**

**Check logs:**
```bash
docker logs ecosystem-mcp-service --tail 100
```

Common issues:
- Syntax error in Python code
- Missing dependency in requirements.txt
- Port already in use
- Database connection failed

**Solution:**
1. Fix the error
2. Rebuild: `docker-compose up -d --build ecosystem-mcp`
3. Check logs again

### **"Worker not processing jobs"**

**Check worker status:**
```bash
curl -s http://localhost:8000/api/v1/admin/workers/ingestion/status
```

Expected: `{"running": true, "processing": true, "healthy": true}`

**Check for stuck jobs:**
```bash
curl -s http://localhost:8000/api/v1/admin/ingest/status | python3 -m json.tool
```

**Solution:**
- Restart may have created orphaned jobs
- Use fail endpoint: `POST /api/v1/admin/ingest/{job_id}/fail`
- Create new job

---

## 🏗️ **Docker Compose Commands**

### **Start Service**
```bash
docker-compose up -d ecosystem-mcp
```

### **Stop Service**
```bash
docker-compose stop ecosystem-mcp
```

### **Restart Service (after rebuild)**
```bash
docker-compose restart ecosystem-mcp
```

### **View Logs**
```bash
# Real-time logs
docker-compose logs -f ecosystem-mcp

# Last 100 lines
docker logs ecosystem-mcp-service --tail 100

# Follow logs with timestamps
docker logs ecosystem-mcp-service -f --timestamps
```

### **Execute Command in Container**
```bash
# Open shell
docker exec -it ecosystem-mcp-service bash

# Run Python command
docker exec ecosystem-mcp-service python3 -c "import sys; print(sys.version)"

# Check file
docker exec ecosystem-mcp-service cat /app/src/api/app.py
```

---

## 📦 **What Gets Deployed**

The Docker image includes:

1. **Python 3.11** (from base image)
2. **All requirements.txt packages**
3. **Your source code** (via `COPY . .`)
4. **Configuration files**
5. **Git repository** (if present)

What does NOT get included:
- `__pycache__/` directories (`.dockerignore`)
- `.git/` directory (`.dockerignore`)
- `venv/` directories (`.dockerignore`)
- `data/` directory (volume mount instead)

---

## 🎯 **Best Practices**

### **1. Always Use docker-compose**

✅ **DO:**
```bash
docker-compose up -d --build ecosystem-mcp
```

❌ **DON'T:**
```bash
docker cp file.py ecosystem-mcp-service:/app/file.py
```

### **2. Check Logs After Deploy**

```bash
# Watch for 30 seconds
docker logs ecosystem-mcp-service -f &
sleep 30
kill %1
```

### **3. Test Before Deploying to Production**

```bash
# Run tests
pytest tests/

# Check linting
flake8 src/

# Verify locally first
docker-compose up -d --build ecosystem-mcp
# Test your changes
# Then deploy to prod
```

### **4. Keep Requirements.txt Updated**

```bash
# Add new package
pip install package-name

# Update requirements
pip freeze > requirements.txt

# Rebuild to install
docker-compose up -d --build ecosystem-mcp
```

### **5. Use Git Tags for Releases**

```bash
# Tag a release
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# Deploy specific version
git checkout v1.0.0
docker-compose up -d --build ecosystem-mcp
```

---

## 🚨 **Common Mistakes**

1. **Using `docker cp` for code changes**
   - ❌ Wrong: Fast but doesn't work
   - ✅ Right: Use `docker-compose up --build`

2. **Forgetting `--build` flag**
   - ❌ Wrong: `docker-compose up -d ecosystem-mcp`
   - ✅ Right: `docker-compose up -d --build ecosystem-mcp`

3. **Not waiting for health check**
   - ❌ Wrong: Deploy and immediately test
   - ✅ Right: Wait 10-15s for startup

4. **Editing files in running container**
   - ❌ Wrong: `docker exec ... vim /app/file.py`
   - ✅ Right: Edit locally, then rebuild

5. **Not checking logs**
   - ❌ Wrong: Assume it worked
   - ✅ Right: Always check logs for errors

---

## 📚 **Related Documentation**

- [Docker Compose docs](https://docs.docker.com/compose/)
- [Dockerfile reference](https://docs.docker.com/engine/reference/builder/)
- [Python module caching](https://docs.python.org/3/library/sys.html#sys.modules)

---

## ✅ **Summary**

**Golden Rule:** Always use `docker-compose up --build` for code changes.

**Quick Reference:**
```bash
# Deploy changes
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp
docker-compose up -d --build ecosystem-mcp

# Verify
curl -f http://localhost:8000/health
docker logs ecosystem-mcp-service --tail 20

# Done! ✅
```

---

**Remember: `docker cp` is for temporary debugging only, NEVER for deploying code changes!** 🚀

