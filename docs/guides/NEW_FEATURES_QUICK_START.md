# 🚀 Quick Start: New Features

**Date:** October 14, 2025  
**Status:** ✅ Ready to Use

---

## 🎉 What's New?

Two powerful new features are now available in your dashboard:

1. **📥 Ingestion Manager** - Control document ingestion and data management
2. **📖 Documentation Generator** - Generate AI-powered documentation

---

## 📥 Feature 1: Ingestion Manager

### Quick Access
```
Dashboard: http://localhost:8501
Navigate to: 📥 Ingestion Manager
```

### Common Tasks

#### Task 1: Ingest Documents (First Time)
```
1. Go to: "🚀 Start Ingestion" tab
2. Path: /app (already set as default)
3. Mode: full (select from dropdown)
4. Service: ecosystem-mcp (already set)
5. Click: "🚀 Start Ingestion"
6. Result: Job ID displayed, processing starts
7. Monitor: Switch to "📊 Job Status" tab
```

**Expected Time:** 5-15 minutes (depending on document count)

#### Task 2: Monitor Ingestion Progress
```
1. Go to: "📊 Job Status" tab
2. Enable: "Auto-refresh (5s)" checkbox
3. Watch: Progress updates in real-time
4. When complete: Status changes to "COMPLETED"
5. Check counts: Processed documents, embeddings generated
```

#### Task 3: Clear Old Data (Start Fresh)
```
1. Go to: "🗑️ Clear Data" tab
2. Scroll to: "💣 Nuclear Option"
3. Click: "💣 Clear ALL Data"
4. Type: "DELETE EVERYTHING"
5. Confirm: Click "💥 YES, DELETE EVERYTHING"
6. Result: All data cleared, system is empty
```

**⚠️ Warning:** This deletes ALL data from PostgreSQL, ChromaDB, and Redis!

---

## 📖 Feature 2: Documentation Generator

### Quick Access
```
Dashboard: http://localhost:8501
Navigate to: 📖 Documentation Generator
```

### Common Tasks

#### Task 1: Generate Simple Documentation
```
1. Go to: "⚙️ Configure" tab
2. Select sections: OVERVIEW, API
3. Enable multi-pass: ✓ (checked)
4. Select passes: initial, deep_dive
5. Queries per pass: 10
6. Response length: L
7. Click: "💾 Save Configuration"
8. Go to: "🚀 Generate" tab
9. Review: Generation plan (2 sections × 2 passes × 10 queries = 40 queries)
10. Click: "🚀 Start Generation"
11. Wait: ~2-3 minutes
12. Result: Documentation generated!
```

#### Task 2: View Generated Documentation
```
1. Go to: "📄 View Output" tab
2. Select: Section from dropdown (e.g., "OVERVIEW")
3. Read: Generated content (rendered Markdown)
4. Download: Click "📥 Download OVERVIEW"
5. Result: Markdown file downloaded to your computer
```

#### Task 3: Generate Complete Documentation
```
1. Go to: "⚙️ Configure" tab
2. Select ALL sections:
   - OVERVIEW
   - ARCHITECTURE
   - API
   - FEATURES
   - DEVELOPMENT
   - DEPLOYMENT
   - PERFORMANCE
   - TROUBLESHOOTING
3. Select ALL passes:
   - initial
   - deep_dive
   - practical
4. Queries per pass: 10
5. Click: "💾 Save Configuration"
6. Note: 8 sections × 3 passes × 10 queries = 240 queries
7. Estimated time: 12-20 minutes
8. Go to: "🚀 Generate" tab
9. Click: "🚀 Start Generation"
10. Watch: Progress bar (section by section)
11. Download: "📥 Download Complete Documentation" when done
```

---

## 🎯 Complete Workflow Example

### Scenario: Fresh Start with New Data

**Step 1: Clear Everything**
```
Ingestion Manager → Clear Data → Nuclear Option
→ Type "DELETE EVERYTHING" → Confirm
Result: System is now empty (0 documents, 0 embeddings)
```

**Step 2: Ingest New Documents**
```
Ingestion Manager → Start Ingestion
→ Path: /app
→ Mode: full
→ Click: Start Ingestion
→ Monitor in Job Status tab
Result: 2,492 documents ingested with embeddings
```

**Step 3: Verify Data**
```
ChromaDB Explorer → Embedding Explorer
→ Check: "Found 2,492 embeddings"
→ Try: Random Sample (10 embeddings)
→ Try: t-SNE 2D Visualization (100 documents)
Result: All features working with new data
```

**Step 4: Generate Documentation**
```
Documentation Generator → Configure
→ Select: OVERVIEW, ARCHITECTURE, API
→ Passes: initial, deep_dive, practical
→ Save Configuration → Generate
Result: Comprehensive documentation in 5-8 minutes
```

**Step 5: Use Documentation**
```
Documentation Generator → View Output
→ Download complete documentation
→ Use for: Project README, API docs, onboarding
Result: Professional documentation ready to use
```

---

## 📊 Current System Status

**Run this to check your data:**
```bash
curl http://localhost:8000/api/v1/admin/data/stats
```

**Example Output:**
```json
{
  "documents": 0,
  "embeddings": 0,
  "cache_keys": 0
}
```

**What it means:**
- `documents: 0` = No documents in PostgreSQL yet
- `embeddings: 0` = No embeddings in ChromaDB yet
- `cache_keys: 0` = No cached responses yet

**Next step:** Use Ingestion Manager to ingest documents!

---

## 🎨 Dashboard Navigation

**Your dashboard now has these pages:**

### Core Features
- 🏠 Home
- 🏥 Health & Infrastructure
- 🔬 Diagnostics

### Query Interfaces
- 🤖 RAG Query
- 🎯 Enhanced Query
- 🔬 Multi-Pass RAG Query

### **Data Management** ⭐ NEW
- 📚 Documents
- **📥 Ingestion Manager** ⭐
- **📖 Documentation Generator** ⭐

### Infrastructure
- 🐳 Container Management
- 🔍 Redis Explorer
- 🗄️ PostgreSQL Explorer
- 🔮 ChromaDB Explorer

### Monitoring
- ⚡ Cache Performance
- 📊 Metrics & Analytics
- 📋 Logs Viewer

### Tools
- 🔌 API Explorer
- ⚙️ Configuration
- 🔌 LLM Tier Management
- 🔧 Settings

---

## 🔧 API Endpoints (For Power Users)

### Ingestion
```bash
# Start ingestion
curl -X POST "http://localhost:8000/api/v1/admin/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/app",
    "mode": "full"
  }'

# Check job status
curl http://localhost:8000/api/v1/admin/ingest/status

# Get data stats
curl http://localhost:8000/api/v1/admin/data/stats
```

### Data Clearing
```bash
# Clear PostgreSQL (DESTRUCTIVE!)
curl -X DELETE http://localhost:8000/api/v1/admin/data/postgres

# Clear ChromaDB (DESTRUCTIVE!)
curl -X DELETE http://localhost:8000/api/v1/admin/data/chromadb

# Clear Redis cache (safe)
curl -X DELETE http://localhost:8000/api/v1/admin/clear-all-cache
```

---

## 💡 Tips & Tricks

### Ingestion Tips

**Tip 1:** Use `full` mode on first run
- Generates embeddings for all documents
- Enables RAG queries and visualizations
- Takes longer but worth it

**Tip 2:** Use `incremental` mode for updates
- Only processes new/changed files
- Much faster
- Maintains existing embeddings

**Tip 3:** Monitor job status
- Enable auto-refresh for real-time updates
- Check error messages if any
- Verify final counts match expectations

### Documentation Tips

**Tip 1:** Start small
- Try 2-3 sections first
- Verify quality before generating all
- Adjust temperature if needed

**Tip 2:** Use appropriate response length
- S (512 tokens): Quick summaries
- M (1024 tokens): Standard documentation
- L (2048 tokens): Detailed documentation ⭐ Recommended
- XL (4096 tokens): Extremely detailed

**Tip 3:** Enable cache
- Speeds up regeneration
- Saves LLM costs
- Consistent results

**Tip 4:** Include sources
- Adds credibility
- Shows document count
- Useful for verification

---

## 🐛 Quick Troubleshooting

### Problem: Dashboard not loading
**Solution:**
```bash
# Restart dashboard
pkill -f "streamlit run app.py"
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-dashboard
python3 -m streamlit run app.py --server.headless=true &
```

### Problem: Backend API not responding
**Solution:**
```bash
# Restart backend
docker restart ecosystem-mcp-service
sleep 5
curl http://localhost:8000/health
```

### Problem: Ingestion job stuck
**Solution:**
```bash
# Check ingestion worker logs
docker logs ecosystem-mcp-worker --tail 50

# Restart worker if needed
docker restart ecosystem-mcp-worker
```

### Problem: Documentation generation slow
**Solution:**
- Reduce queries per pass (try 5-7)
- Use fewer passes (just initial + deep_dive)
- Enable cache
- Lower response length (M instead of L)

---

## ✅ What You Can Do RIGHT NOW

1. **Open Dashboard:** http://localhost:8501

2. **Ingest Documents:**
   - Ingestion Manager → Start Ingestion
   - Mode: full
   - Wait 10 minutes
   - Result: 2,492 documents with embeddings

3. **Generate Documentation:**
   - Documentation Generator → Configure
   - Sections: OVERVIEW, API
   - Generate (2-3 minutes)
   - Download result

4. **Explore Data:**
   - ChromaDB Explorer → Visualizations
   - Try t-SNE 2D with 100 documents
   - See your data visualized!

5. **Test RAG:**
   - RAG Query page
   - Ask: "What is the architecture of ecosystem-mcp?"
   - Get AI-powered answer from your documents

---

## 🎉 Status

```
╔═══════════════════════════════════════════╗
║                                           ║
║   ✅ ALL FEATURES DEPLOYED & WORKING!    ║
║                                           ║
║   📥 Ingestion Manager:    Ready         ║
║   📖 Documentation Gen:    Ready         ║
║   🗑️ Data Clearing:        Ready         ║
║   📊 Statistics:           Ready         ║
║                                           ║
║         START USING NOW! 🚀              ║
║                                           ║
╚═══════════════════════════════════════════╝
```

**Dashboard:** http://localhost:8501  
**API:** http://localhost:8000  
**Docs:** Full guide in `INGESTION_AND_DOCS_FEATURES.md`

**Ready to revolutionize your documentation workflow!** 🎊

