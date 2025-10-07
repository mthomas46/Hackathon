# Service Startup Guide for Demo Persistence

**Date:** October 3, 2025  
**Purpose:** Guide for starting the 4 required services for full demo persistence

---

## 🎯 Services Required

| Service | Port | Purpose |
|---------|------|---------|
| doc_store | 5087 | Stores historical documents (Jira, Confluence, GitHub) |
| prompt_store | 5110 | Stores workflow prompts |
| external-service-store | 5140 | Stores discovered external services |
| memory-agent | 5090 | Stores workflow execution contexts |

---

## ✅ What We've Done

1. **Investigated** why stores weren't saving (they weren't running!)
2. **Verified** Docker Compose configuration (properly configured)
3. **Created helper scripts:**
   - `start_demo_services.sh` - Automated startup
   - `stop_demo_services.sh` - Automated cleanup
4. **Fixed schema issues:**
   - Changed `memory_type` from `"workflow_workflow_a"` to `"context"`
   - Updated status logic to show ⚠️ when count=0
   - Added explanatory notes in reports

---

## 🚀 How to Start Services

### Option 1: Helper Script (Recommended)

```bash
cd /Users/mykalthomas/Documents/work/Hackathon
./start_demo_services.sh
```

Choose **option 2** (Manual Python processes) when prompted.

### Option 2: Manual Start (4 Terminals)

**IMPORTANT:** Set PYTHONPATH in each terminal!

```bash
# Terminal 1: doc_store
cd /Users/mykalthomas/Documents/work/Hackathon
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon
cd services/doc_store && python3 main.py

# Terminal 2: prompt_store
cd /Users/mykalthomas/Documents/work/Hackathon
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon
cd services/prompt_store && python3 main.py

# Terminal 3: external-service-store
cd /Users/mykalthomas/Documents/work/Hackathon
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon
cd services/external-service-store && python3 main.py

# Terminal 4: memory-agent
cd /Users/mykalthomas/Documents/work/Hackathon
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon
cd services/memory-agent && python3 main.py
```

### Option 3: Use Makefile

```bash
cd /Users/mykalthomas/Documents/work/Hackathon

# Check available targets
make help | grep -E "(store|agent)"

# Start services (if targets exist)
make prompt-store-run
make external-service-store-run
make user-store-run
```

---

## ✅ Verify Services Are Running

```bash
# Test endpoints
curl http://localhost:5087/health && echo " ✅ doc_store"
curl http://localhost:5110/health && echo " ✅ prompt_store"
curl http://localhost:5140/health && echo " ✅ external-service-store"
curl http://localhost:5090/health && echo " ✅ memory-agent"
```

Expected: All should return `{"status": "healthy"}` or similar.

---

## 🎉 Run Demo with Full Persistence

Once all services are running:

```bash
cd /Users/mykalthomas/Documents/work/Hackathon

python demo_hyper_realistic_parameterized.py \
  --feature "expand api functionality to a cats effect scala api such that it can take in user information and display that user information from basic CRUD endpoints. this project has a scala backend and an elm frontend" \
  --tickets 35 \
  --team 8 \
  --tech Scala "Cats Effect" Elm CRUD API \
  --tangential-docs 7 \
  --output scala_elm_crud_demo_with_persistence
```

### Expected Output (Success!)

```
💾 SAVING WORKFLOW EXECUTIONS TO MEMORY-AGENT...
✅ Workflow context saved successfully
✅ Workflow contexts saved: 5  ← Not 0!

📊 Data Persistence Statistics:
| Store | Count | Status |
|-------|-------|--------|
| doc_store | 34 | ✅ |  ← Not ⚠️!
| prompt_store | 8 | ✅ |
| external-service-store | 12 | ✅ |
| memory-agent | 5 | ✅ |
| user-store | 8 | ✅ |
```

---

## 🛑 Stop Services

```bash
# Option 1: Helper script
./stop_demo_services.sh

# Option 2: Manual
# Ctrl+C in each terminal window

# Option 3: Kill processes
pkill -f "services/doc_store/main.py"
pkill -f "services/prompt_store/main.py"
pkill -f "services/external-service-store/main.py"
pkill -f "services/memory-agent/main.py"
```

---

## ⚠️ Troubleshooting

### Services won't start

**Error:** `ModuleNotFoundError: No module named 'services'`  
**Fix:** Make sure to set PYTHONPATH:
```bash
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon
```

### Python not found

**Error:** `python: command not found`  
**Fix:** Use `python3` instead of `python`

### Port already in use

**Error:** `Address already in use`  
**Fix:** Kill existing processes:
```bash
lsof -ti:5087 | xargs kill -9  # doc_store
lsof -ti:5110 | xargs kill -9  # prompt_store
lsof -ti:5140 | xargs kill -9  # external-service-store
lsof -ti:5090 | xargs kill -9  # memory-agent
```

### Docker network conflicts

**Error:** `network has active endpoints`  
**Fix:** Use manual startup (Option 2) instead of Docker

---

## 📝 Files Created

- `start_demo_services.sh` - Helper script to start all services
- `stop_demo_services.sh` - Helper script to stop all services
- `SERVICE_STARTUP_GUIDE.md` - This file
- `demo_data_persistence_client.py` - Updated with correct schema (`memory_type: "context"`)
- `demo_hyper_realistic_parameterized.py` - Updated status logic and explanatory notes

---

## 🎯 Summary

**Problem:** Services not running → Data not persisting  
**Solution:** Start the 4 required services manually  
**Result:** Full persistence with all ✅ instead of ⚠️  

**Time to fix:** ~5 minutes to start services  
**Benefit:** See the ecosystem actually saving data!

---

**Ready to start?** Choose Option 1 or Option 2 above and get started! 🚀

