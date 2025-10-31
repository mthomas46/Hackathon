---
title: "Non-Git Repository Document Ingestion Guide"
service: "ecosystem-mcp"
category: "features"
tags: ['capabilities', 'database', 'features', 'functionality', 'health', 'ingestion', 'monitoring', 'pipeline', 'postgresql', 'rag']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "beginner"
semantic_keywords: ['capabilities', 'database', 'features', 'functionality', 'health']
llm_search_hints: ['what is non-git repository document ingestion guide', 'how does non-git repository document ingestion guide work', 'guide to non-git repository document ingestion guide']
---

# Non-Git Repository Document Ingestion Guide

**Purpose:** Document how to ingest documents from non-git repositories using content-based versioning.

---

## 🔍 **The Challenge**

Standard ingestion requires a git repository for version tracking. But what about:
- Standalone documents (PDFs, Word docs)
- Legacy systems without git
- External document sources
- File shares and network drives
- User-uploaded content

**Solution:** Content-based versioning with temporal ordering (already implemented!)

---

## ✅ **System Capabilities**

Our system **already supports** non-git document ingestion through:

1. **Content-Addressable Storage** (`temporal_versioning.py`)
2. **Hybrid Versioning** (content hash + temporal metadata)
3. **Duplicate Detection** (SHA-256 content hashing)
4. **Version Chains** (track document evolution)

---

## 🏗️ **Architecture**

### **Content-Based Versioning**

Instead of git commits, we use:
- **Content Hash:** SHA-256 of document content
- **Temporal Metadata:** Upload time, modification time
- **Source Tracking:** Where document came from
- **User Attribution:** Who added/modified it

### **How It Works**

```
Document → Content Hash → Check if exists
  ↓                              ↓
  New?                         Exists?
  ↓                              ↓
Store with metadata          Update metadata
Create version 1             Increment version
```

---

## 📊 **Implementation Status**

### **✅ Already Implemented**

#### **1. Temporal Versioning Service** (`temporal_versioning.py`)

```python
class TemporalVersioningService:
    async def store_document_version(
        document_id: UUID,
        content: str,
        metadata: Dict,
        source_info: Dict
    ):
        # Compute content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Check for duplicates
        existing = await self.get_by_content_hash(content_hash)
        
        if existing:
            # Duplicate - update metadata
            await self.enrich_existing(existing, metadata)
        else:
            # New content - create version
            await self.create_new_version(...)
```

**Features:**
- Content hash generation (SHA-256)
- Duplicate detection
- Version chain tracking
- Metadata enrichment
- Temporal ordering

#### **2. Content-Addressable Storage**

**Database Schema:**
```sql
CREATE TABLE document_versions (
    id UUID PRIMARY KEY,
    document_id UUID,
    content_hash VARCHAR(64),  -- SHA-256
    version_number INTEGER,
    created_at TIMESTAMP,
    modified_at TIMESTAMP,
    source_type VARCHAR(50),
    source_path TEXT,
    uploader_id VARCHAR(100),
    metadata JSONB
);

CREATE INDEX idx_content_hash ON document_versions(content_hash);
```

**Benefits:**
- Fast duplicate detection (O(1) hash lookup)
- Deduplication (same content stored once)
- Version history (multiple versions per document)
- Temporal ordering (timestamps)

---

## 🚀 **How to Use**

### **Option 1: Direct API (Already Available)**

```bash
# Upload document without git
POST /api/v1/documents/upload

{
    "content": "Document content here...",
    "filename": "report.pdf",
    "source_type": "manual_upload",
    "uploader": "user@example.com",
    "metadata": {
        "title": "Quarterly Report",
        "category": "finance",
        "tags": ["Q4", "2025"]
    }
}
```

**Response:**
```json
{
    "document_id": "abc-123",
    "content_hash": "sha256:a1b2c3...",
    "version": 1,
    "is_duplicate": false,
    "status": "stored"
}
```

### **Option 2: File System Ingestion (Future)**

```bash
# Ingest from local directory (no git required)
POST /api/v1/admin/ingest

{
    "repo_path": "/path/to/documents",
    "mode": "filesystem",  # Not git mode
    "use_content_versioning": true,
    "source_metadata": {
        "source_type": "file_share",
        "source_name": "Document Library"
    }
}
```

### **Option 3: Bulk Upload (Future)**

```bash
# Upload multiple files
POST /api/v1/documents/bulk-upload

files: [
    {file: report1.pdf},
    {file: report2.pdf},
    ...
]
metadata: {
    "source_type": "bulk_upload",
    "batch_id": "batch-123"
}
```

---

## 📋 **Version Tracking**

### **Git vs Content-Based**

| Feature | Git-Based | Content-Based |
|---------|-----------|---------------|
| Version ID | Commit SHA | Content Hash |
| Timestamp | Commit time | Upload/modify time |
| Author | Git committer | Uploader ID |
| History | Git log | Version chain |
| Branching | Git branches | N/A |
| Merging | Git merge | N/A |
| Dedup | Manual | Automatic |

### **Version Chain Example**

```
Document: "Quarterly Report"

Version 1:
  content_hash: abc123...
  created_at: 2025-01-01
  uploader: alice@example.com
  
Version 2:
  content_hash: def456...  (different content)
  created_at: 2025-01-15
  uploader: bob@example.com
  previous_version: Version 1
  
Version 3:
  content_hash: abc123...  (same as V1!)
  created_at: 2025-02-01
  uploader: carol@example.com
  duplicate_of: Version 1
```

**Result:** 
- Only 2 unique contents stored
- 3 versions tracked
- Full temporal history preserved

---

## 🔍 **Duplicate Detection**

### **How It Works**

1. **Content Hash Calculation**
   ```python
   content_hash = hashlib.sha256(content.encode()).hexdigest()
   ```

2. **Database Lookup**
   ```sql
   SELECT * FROM document_versions 
   WHERE content_hash = 'abc123...'
   ```

3. **Decision**
   - If exists: Mark as duplicate, update metadata
   - If new: Store content, create new version

### **Benefits**

- **Storage Efficiency:** Same content stored once
- **Fast Detection:** O(1) hash lookup
- **Cross-Source:** Detect duplicates across sources
- **Automatic:** No manual intervention

### **Example**

```
User A uploads "report.pdf"
→ Stored with hash abc123...

User B uploads "report_copy.pdf" (same content)
→ Hash matches: abc123...
→ Marked as duplicate
→ Metadata enriched (2 uploaders tracked)
→ Storage: 1 copy, not 2!
```

---

## 📊 **Metadata Enrichment**

### **What Gets Tracked**

**Per Document:**
- Content hash (SHA-256)
- Original filename
- File size, type
- Upload timestamp
- Modification timestamp
- Source type (upload, api, bulk, etc.)
- Source path/URL

**Per Version:**
- Version number (1, 2, 3, ...)
- Uploader ID/email
- Upload timestamp
- Previous version link
- Duplicate flag
- Custom metadata (tags, categories, etc.)

### **Enrichment on Duplicate**

When duplicate detected:
```python
{
    "is_duplicate": true,
    "original_version": 1,
    "duplicate_uploads": [
        {"uploader": "alice", "timestamp": "2025-01-01"},
        {"uploader": "bob", "timestamp": "2025-01-15"}
    ],
    "access_count": 2,
    "last_accessed": "2025-01-15"
}
```

---

## 🔧 **Current Limitations**

### **1. No File System Scanner (Yet)**

**Status:** Temporal versioning implemented, but no automatic file system scanner.

**Workaround:** Use API to upload documents

**Future:** Add file system ingestion mode

### **2. No Bulk Upload UI (Yet)**

**Status:** API supports individual uploads

**Workaround:** Use API with scripts

**Future:** Add bulk upload interface to dashboard

### **3. No Source Tracking UI (Yet)**

**Status:** Metadata tracked in database

**Workaround:** Query database directly

**Future:** Add source filtering in UI

---

## 🎯 **Use Cases**

### **1. Legacy Document Migration**

**Scenario:** Migrate 10,000 PDFs from old system

**Approach:**
```bash
for file in /legacy/docs/*.pdf; do
    curl -X POST /api/v1/documents/upload \
      -F "file=@$file" \
      -F "source_type=legacy_migration" \
      -F "source_name=OldSystem"
done
```

**Benefits:**
- Automatic deduplication
- Version history preserved
- Source tracked

### **2. User-Generated Content**

**Scenario:** Users upload documents via web app

**Approach:**
- Web form → API → Temporal versioning
- Each user tracked separately
- Duplicates detected automatically

**Benefits:**
- No git repository needed
- User attribution preserved
- Storage optimized

### **3. External Document Sync**

**Scenario:** Sync documents from SharePoint/Dropbox

**Approach:**
```python
async def sync_external_documents():
    for doc in external_api.get_documents():
        content = await doc.download()
        
        await temporal_versioning.store_document_version(
            content=content,
            metadata={
                "source_type": "sharepoint",
                "source_id": doc.id,
                "modified_at": doc.modified_time
            }
        )
```

**Benefits:**
- Automatic duplicate detection across sources
- Temporal ordering preserved
- Source attribution maintained

---

## 🔮 **Future Enhancements**

### **1. File System Scanner**

**Plan:**
```python
class FileSystemScanner:
    async def scan_directory(path: str, recursive: bool = True):
        """
        Scan directory and ingest all files using content-based versioning.
        """
        for file in os.walk(path):
            content = read_file(file)
            await temporal_versioning.store_document_version(
                content=content,
                source_info={
                    "source_type": "filesystem",
                    "source_path": file.path,
                    "discovered_at": datetime.now()
                }
            )
```

### **2. Watch Mode**

**Plan:**
```python
class FileSystemWatcher:
    async def watch_directory(path: str):
        """
        Watch directory for changes and auto-ingest.
        """
        async for event in file_watcher.events(path):
            if event.type == "created" or event.type == "modified":
                await ingest_file(event.path)
```

### **3. Cloud Storage Integration**

**Plan:**
- S3 bucket monitoring
- Google Drive sync
- Dropbox integration
- OneDrive sync

### **4. Advanced Deduplication**

**Current:** Exact content match (SHA-256)

**Future:**
- Fuzzy matching (similar but not identical)
- Content fingerprinting
- Semantic similarity
- Image perceptual hashing

---

## ✅ **Summary**

### **What Works Today**

✅ Content-based versioning (fully implemented)  
✅ Duplicate detection (SHA-256)  
✅ Version chains (temporal ordering)  
✅ Metadata tracking (comprehensive)  
✅ API uploads (individual documents)

### **What Needs Work**

📋 File system scanner (not implemented)  
📋 Bulk upload UI (not implemented)  
📋 Source filtering UI (not implemented)  
📋 Cloud storage integration (not implemented)

### **Recommendation**

For non-git document ingestion:
1. Use the API for now (fully functional)
2. Scripts for bulk uploads (workaround)
3. Wait for file system scanner (Phase 4+)

### **Key Insight**

**The core versioning system is production-ready!**  
We just need convenience features (scanners, UI, bulk operations).

---

## 📚 **Related Documentation**

- `services/ecosystem-mcp/src/services/temporal_versioning.py` - Implementation
- `DATABASE_UPDATE_FIX_COMPLETE.md` - JSONB handling
- `SYSTEM_PROTECTIONS_AND_FALLBACKS.md` - Overall architecture

---

## 🎉 **Conclusion**

**Non-git document ingestion is fully supported through content-based versioning!**

The system provides:
- ✅ Automatic versioning
- ✅ Duplicate detection
- ✅ Temporal ordering
- ✅ Metadata tracking
- ✅ Source attribution

**You can ingest non-git documents today using the API.**

Future enhancements will add convenience features (file system scanner, bulk upload UI, etc.), but the core functionality is production-ready!

---

**Need to ingest non-git documents? Use the temporal versioning API!** 🚀

