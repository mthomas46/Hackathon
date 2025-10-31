# 🚀 Embeddings Setup Guide

## ⚠️ Current Status

**Issue:** No embeddings found in ChromaDB  
**Cause:** Documents exist in PostgreSQL (2,367) but haven't been embedded yet  
**Solution:** Follow this guide to populate ChromaDB with embeddings

---

## 📊 Current State

```bash
# Check current state
curl -s "http://localhost:8000/api/v1/embeddings/sample?n=1"
```

**Expected Response:**
```json
{
  "detail": "No documents found in ChromaDB. Ensure documents are ingested and embedded."
}
```

**PostgreSQL:** 2,367 documents ✅  
**ChromaDB:** 0 embeddings ❌ (needs to be populated)

---

##  Option 1: Re-Ingest with Embedding (Recommended)

This will re-process all documents and generate embeddings.

### Step 1: Trigger Ingestion

```bash
curl -X POST "http://localhost:8000/api/v1/admin/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "ecosystem-mcp",
    "base_path": "/path/to/your/code",
    "force_update": true
  }'
```

### Step 2: Monitor Progress

```bash
# Get job ID from Step 1 response, then:
curl "http://localhost:8000/api/v1/admin/ingest/status"
```

### Step 3: Wait for Completion

**Expected Time:** 10-30 minutes for 2,367 documents  
**Progress:** Check status endpoint every 30 seconds

---

## 🔧 Option 2: Manual Embedding Script (Fast)

If you need embeddings NOW, use this Python script to embed existing documents.

### Create Script

```python
# embed_existing_docs.py
import asyncio
import httpx
from tqdm import tqdm

async def embed_all_documents():
    """Embed all documents in PostgreSQL to ChromaDB."""
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Get all documents
        print("📚 Fetching documents from PostgreSQL...")
        docs_response = await client.get(f"{base_url}/api/v1/documents")
        docs_response.raise_for_status()
        docs_data = docs_response.json()
        
        total = docs_data.get("total", 0)
        print(f"Found {total} documents to embed")
        
        # Fetch all document IDs (paginate if needed)
        all_docs = []
        limit = 100
        offset = 0
        
        while offset < total:
            page_response = await client.get(
                f"{base_url}/api/v1/documents",
                params={"limit": limit, "offset": offset}
            )
            page_data = page_response.json()
            all_docs.extend(page_data.get("documents", []))
            offset += limit
            print(f"Loaded {len(all_docs)}/{total} documents...")
        
        print(f"\n🧬 Starting embedding generation for {len(all_docs)} documents...")
        
        # Embed each document
        success_count = 0
        error_count = 0
        
        for doc in tqdm(all_docs, desc="Embedding"):
            try:
                # Trigger embedding via API
                embed_response = await client.post(
                    f"{base_url}/api/v1/embed",
                    json={
                        "document_id": doc["id"],
                        "text": doc.get("normalized_content", "")[:5000]  # Limit size
                    },
                    timeout=60.0
                )
                
                if embed_response.status_code == 200:
                    success_count += 1
                else:
                    error_count += 1
                    print(f"\n❌ Failed to embed {doc['id']}: {embed_response.status_code}")
            
            except Exception as e:
                error_count += 1
                print(f"\n❌ Error embedding {doc['id']}: {e}")
        
        print(f"\n✅ Complete! Success: {success_count}, Errors: {error_count}")
        print(f"\n🔍 Verify embeddings:")
        print(f"   curl \"http://localhost:8000/api/v1/embeddings/sample?n=10\"")

if __name__ == "__main__":
    asyncio.run(embed_all_documents())
```

### Run Script

```bash
cd /Users/mykalthomas/Documents/work/Hackathon
python3 embed_existing_docs.py
```

**Expected Time:** ~15-20 minutes  
**Progress:** Real-time progress bar

---

## 🔍 Option 3: Check if Embedding Queue is Running

The system might already be embedding documents in the background.

### Check Queue Status

```bash
curl "http://localhost:8000/api/v1/admin/queue-status"
```

**Look for:**
- `embedding_queue_length`: Number of documents waiting
- `processed_count`: Number completed
- `error_count`: Number failed

### Check if Ollama is Running

Embeddings require Ollama service to be up.

```bash
# Check Ollama status
curl "http://localhost:8000/api/v1/ollama/status"

# Check if embedding model is available
curl "http://localhost:8000/api/v1/ollama/models"
```

**Required Model:** `nomic-embed-text`

### Pull Embedding Model (if missing)

```bash
docker exec -it ecosystem-mcp-ollama ollama pull nomic-embed-text
```

---

## 🎯 Quickest Solution (5 minutes)

If you just want to **test the embeddings API** with a small sample:

### Ingest a Small Test Directory

```bash
curl -X POST "http://localhost:8000/api/v1/admin/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "test",
    "base_path": "/Users/mykalthomas/Documents/work/Hackathon/docs",
    "recursive": false,
    "force_update": true
  }'
```

**This will:**
1. Scan `/docs` directory (top-level only)
2. Ingest ~50-100 files
3. Generate embeddings
4. Store in ChromaDB

**Time:** ~2-5 minutes

### Then Test

```bash
# Wait 5 minutes, then:
curl "http://localhost:8000/api/v1/embeddings/sample?n=10"
```

You should see embeddings! Then go to the dashboard:
- **URL:** http://localhost:8501
- **Page:** 🔮 ChromaDB Explorer → 🧬 Embedding Explorer
- **Try:** Random Sample with 10 samples

---

## 📊 Verification

### Check if Embeddings Exist

```bash
# Random sample (should return data)
curl "http://localhost:8000/api/v1/embeddings/sample?n=1"

# Batch export (should return embeddings array)
curl "http://localhost:8000/api/v1/embeddings/export/batch?limit=10"
```

### Expected Response

```json
{
  "samples": [
    {
      "id": "abc123...",
      "file_path": "/path/to/file.md",
      "service": "ecosystem-mcp",
      "dimensions": 768,
      "content_preview": "...",
      "embedding_model": "nomic-embed-text"
    }
  ],
  "count": 1,
  "total_documents": 2367,
  "collection": "ecosystem-mcp"
}
```

### Dashboard Test

1. Go to http://localhost:8501
2. Navigate to 🔮 ChromaDB Explorer
3. Click 🧬 Embedding Explorer tab
4. Select "Random Sample"
5. Click "🎲 Get Random Sample"
6. Should see expandable cards with embeddings!

---

## ⚡ Troubleshooting

### Issue: "Ollama is not available"

```bash
# Check if Ollama container is running
docker ps | grep ollama

# If not running, start it
docker-compose -f docker-compose.dev.yml up -d ecosystem-mcp-ollama

# Pull embedding model
docker exec -it ecosystem-mcp-ollama ollama pull nomic-embed-text
```

### Issue: "ChromaDB collection not found"

```bash
# Restart ChromaDB
docker restart ecosystem-mcp-chromadb

# Wait 10 seconds
sleep 10

# Try ingestion again
```

### Issue: "Embedding generation taking too long"

**Cause:** Embedding 2,367 documents takes time  
**Solution:** Start with a smaller batch (Option 3)

**Estimated Times:**
- 50 docs: ~2 minutes
- 100 docs: ~5 minutes
- 500 docs: ~20 minutes
- 2,367 docs: ~45 minutes

### Issue: "Connection refused to ChromaDB"

```bash
# Check ChromaDB is running
docker ps | grep chroma

# Check logs
docker logs ecosystem-mcp-chromadb --tail 50

# Restart if needed
docker restart ecosystem-mcp-chromadb
```

---

## 🎓 Understanding the Flow

### How Documents Become Embeddings

```
1. Ingestion Pipeline
   ├── Scan files from disk
   ├── Parse content (MD, PY, JSON, etc.)
   ├── Normalize text
   └── Store in PostgreSQL

2. Embedding Pipeline
   ├── Read document from PostgreSQL
   ├── Send to Ollama (nomic-embed-text model)
   ├── Receive 768D vector
   └── Store in ChromaDB

3. Retrieval
   ├── Query ChromaDB by vector similarity
   ├── Get document IDs
   └── Fetch full documents from PostgreSQL
```

### Services Involved

- **PostgreSQL:** Stores full document content
- **ChromaDB:** Stores 768D embeddings
- **Ollama:** Generates embeddings
- **Redis:** Queues embedding jobs
- **Backend API:** Orchestrates everything

---

## 🚀 Recommended Approach

### For Testing (5 minutes)

Use **Option 3** - Ingest small test directory

### For Production (30 minutes)

Use **Option 1** - Re-ingest all with proper embedding

### For Immediate Results (15 minutes)

Use **Option 2** - Manual embedding script

---

## 📍 Next Steps After Embeddings Are Ready

Once you have embeddings in ChromaDB:

1. **Random Sampling** ✅
   - Go to Embedding Explorer
   - Select "Random Sample"
   - Get 10-50 random embeddings
   - View stats and content

2. **Document Lookup** ✅
   - Copy a document ID from samples
   - Select "By Document ID"
   - Paste ID and lookup
   - See full details

3. **Visualizations** ✅
   - Scroll to Visualization section
   - Select t-SNE 2D
   - Set 100 documents
   - Generate plot
   - See your embeddings in 2D space!

4. **Advanced Analysis** ✅
   - Try UMAP for better clustering
   - Use PCA for dimensionality
   - Create similarity heatmaps
   - Export to CSV for external analysis

---

## 🎉 Success Criteria

You'll know embeddings are working when:

✅ `/api/v1/embeddings/sample` returns data (not 404)  
✅ `total_documents` > 0  
✅ Random Sample button shows expandable cards  
✅ Visualizations work with real data  
✅ No "mock data" warnings  

---

**Need Help?**

1. Check service status: http://localhost:8501 → 🐳 Container Management
2. View logs: `docker logs ecosystem-mcp-service --tail 100`
3. Check Ollama: `curl http://localhost:8000/api/v1/ollama/status`
4. Verify embeddings: `curl "http://localhost:8000/api/v1/embeddings/sample?n=1"`

**Let's get those embeddings generated!** 🚀

