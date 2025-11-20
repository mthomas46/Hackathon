**Date:** November 19, 2025  
**Status:** Service Filtering Added to Documentation Generator  
**Coverage:** Dashboard now filters queries by service_name  

---

# Service Filtering Fix - Documentation Generator

## Problem

After ingesting adminservice documents (868 docs), generated documentation was still showing ecosystem-mcp/Hackathon content instead of adminservice content.

### Root Cause

**The documentation generator was NOT filtering by service_name**, causing queries to:
1. Pull from all services in the database
2. Return mixed results (Hackathon + adminservice)
3. Often prioritize Hackathon documents (higher relevance or indexed first)

### Evidence

```sql
-- What's in the database
SELECT COUNT(*), service_name FROM documents WHERE is_latest = true GROUP BY service_name;

 count | service_name 
-------+--------------
   955 | Hackathon    
   868 | adminservice  

-- Both services have documents and embeddings
-- But queries were not filtering by service_name!
```

**Query Code (BEFORE FIX)**:
```python
# doc_generator.py line 800
response = httpx.post(
    f"{api_base_url}/api/v1/query/enhanced",
    json={
        "question": question,
        "mode": "rag",
        "tier": tier,
        "n_results": config['n_results'],
        # ❌ NO SERVICE_NAME FILTER!
    }
)
```

**Result**: Queries returned documents from both services, mixing adminservice and Hackathon content.

---

## Solution

### ✅ Added Service Selector to Documentation Generator

**1. Prominent Service Selection UI** (Configuration Tab)

```python
# New UI section added after directory selection
st.markdown("### 🎯 Service Selection")
st.warning("⚠️ **IMPORTANT**: Select which service's documents to use for generation")

service_name = st.selectbox(
    "Target Service",
    options=["adminservice", "Hackathon", "All Services (No Filter)"],
    index=0,  # ✅ DEFAULT TO ADMINSERVICE
    help="""
    **Choose which service to generate documentation for:**
    - **adminservice**: Use only adminservice documents (Scala/Play Framework)
    - **Hackathon**: Use only Hackathon/ecosystem-mcp documents
    - **All Services**: Query across all services (may mix results)
    
    ⚠️ If you recently ingested new documents, make sure to select the correct service!
    """
)

# Show what's in the database
st.caption(f"📊 Currently in database: Hackathon (955 docs), adminservice (868 docs)")

# Convert to API format
service_filter = None if service_name == "All Services (No Filter)" else service_name

if service_filter:
    st.success(f"✅ Will query **{service_filter}** documents only")
```

**2. Pass Service Filter to Config**

```python
# Save to session state
st.session_state.doc_config = {
    "directory": directory,
    "service_filter": service_filter,  # ✅ NEW
    "sections": sections,
    # ... other config
}
```

**3. Add Service Filter to Queries**

```python
# In generate_pass() function
query_payload = {
    "question": question,
    "mode": "rag",
    "tier": tier,
    "n_results": config['n_results'],
    "temperature": config['temperature'],
    "max_tokens": max_tokens,
    "max_retries": max_retries
}

# ✅ ADD SERVICE FILTER IF CONFIGURED
if config.get('service_filter'):
    query_payload["service_name"] = config['service_filter']

response = httpx.post(
    f"{api_base_url}/api/v1/query/enhanced",
    json=query_payload,
    timeout=query_timeout
)
```

**4. Display Service in Generation Plan**

```python
# In Generation tab
st.markdown("### 📋 Generation Plan")

# ✅ SHOW SERVICE FILTER PROMINENTLY
if config.get('service_filter'):
    st.success(f"🎯 **Target Service:** {config['service_filter']}")
else:
    st.warning("⚠️ **No service filter** - queries will span all services")
```

---

## How to Use

### Step 1: Configure Documentation Generator

1. Go to **Documentation Generator** page in dashboard
2. Open the **⚙️ Configure** tab
3. **Look for the new "🎯 Service Selection" section**

### Step 2: Select Target Service

**For adminservice documentation**:
```
Target Service: [adminservice] ← SELECT THIS
```

**For Hackathon/ecosystem-mcp documentation**:
```
Target Service: [Hackathon]
```

**For mixed results (not recommended)**:
```
Target Service: [All Services (No Filter)]
```

### Step 3: Verify Selection

You should see:
```
✅ Will query **adminservice** documents only
📊 Currently in database: Hackathon (955 docs), adminservice (868 docs)
```

### Step 4: Save Configuration

Click **💾 Save Configuration**

### Step 5: Generate Documentation

1. Go to **📊 Generate** tab
2. Verify service filter is shown:
   ```
   🎯 Target Service: adminservice
   ```
3. Click **🚀 Generate Documentation**

---

## Before vs After

### Before Fix

```
User: Generate documentation
Dashboard: [Sends queries without service_name]
API: [Returns top results from ALL services]
Result: ❌ Mixed content from Hackathon + adminservice
```

### After Fix

```
User: Generate documentation
User: [Selects "adminservice" in dropdown]
Dashboard: [Sends queries with service_name="adminservice"]
API: [Returns results ONLY from adminservice]
Result: ✅ Pure adminservice content
```

---

## API Endpoint Support

The API already supported service filtering via the `service_name` parameter:

### `/api/v1/query/enhanced`

```python
# In enhanced query endpoint
class EnhancedQueryRequest(BaseModel):
    question: str
    mode: QueryMode
    service_name: Optional[str] = None  # ✅ ALREADY SUPPORTED
    # ... other fields
```

### `/api/v1/search`

```python
# In search endpoint
class SearchRequest(BaseModel):
    query: str
    limit: int = 20
    service_name: Optional[str] = None  # ✅ ALREADY SUPPORTED
```

**The dashboard just wasn't using it!**

---

## Testing

### Test Case: Generate Adminservice Documentation

**1. Verify Documents**:
```bash
# Check adminservice is in DB with embeddings
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c "
  SELECT service_name, COUNT(*) as total, COUNT(embedding_id) as with_embeddings
  FROM documents
  WHERE is_latest = true
  GROUP BY service_name;
"

# Expected:
#  service_name | total | with_embeddings
# --------------+-------+-----------------
#  adminservice |   868 |             867
#  Hackathon    |   955 |             954
```

**2. Configure Generator**:
- Open Documentation Generator
- Select "adminservice" from dropdown
- Save configuration
- Verify "🎯 Target Service: adminservice" appears

**3. Generate Documentation**:
- Click "Generate Documentation"
- Watch queries execute
- All queries should specify `service_name: adminservice`

**4. Verify Results**:
- Generated content should reference:
  - ✅ Scala files
  - ✅ Play Framework
  - ✅ `conf/application.conf`
  - ✅ `routes` files
  - ✅ adminservice-specific classes

- Should NOT reference:
  - ❌ ecosystem-mcp
  - ❌ Hackathon project files
  - ❌ Python files
  - ❌ FastAPI code

---

## Related Endpoints

All these endpoints support `service_name` filtering:

| Endpoint | Parameter | Purpose |
|----------|-----------|---------|
| `/api/v1/query/enhanced` | `service_name` | Enhanced RAG query |
| `/api/v1/search` | `service_name` | Semantic search |
| `/api/v1/dynamic-rag/query` | `service_name` | Dynamic temporal RAG |
| `/api/v1/query` | `service_name` | Basic document query |
| `/api/v1/query/context-aware` | `service_filter` | Context-aware query |

---

## Files Modified

| File | Changes | Lines |
|------|---------|-------|
| `dashboard_views/doc_generator.py` | Added service selector UI | 91-117 |
| `dashboard_views/doc_generator.py` | Added to config dict | 321 |
| `dashboard_views/doc_generator.py` | Added service filter display | 358-362 |
| `dashboard_views/doc_generator.py` | Added service_name to queries | 799-817 |

---

## Troubleshooting

### Issue: Still seeing mixed content

**Check**:
1. Did you select "adminservice" in the dropdown?
2. Did you see "✅ Will query **adminservice** documents only"?
3. Did you click "💾 Save Configuration"?
4. In the Generate tab, do you see "🎯 Target Service: adminservice"?

**Verify Query**:
```bash
# Watch API logs to see if service_name is being sent
docker logs -f ecosystem-mcp-service 2>&1 | grep "service_name"
```

### Issue: No adminservice documents

**Verify Database**:
```bash
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c "
  SELECT COUNT(*) FROM documents WHERE service_name = 'adminservice' AND is_latest = true;
"
```

**Expected**: `868`

**If 0**: Re-run ingestion for `/work/adminservice`

### Issue: Embeddings missing

**Check**:
```bash
docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c "
  SELECT COUNT(*) as total, COUNT(embedding_id) as with_embeddings
  FROM documents
  WHERE service_name = 'adminservice' AND is_latest = true;
"
```

**Expected**: `total: 868, with_embeddings: 867` (1 missing is OK)

---

## Future Enhancements

### Dynamic Service List

Currently hardcoded:
```python
options=["adminservice", "Hackathon", "All Services (No Filter)"]
```

**Enhancement**: Query API for available services:
```python
# Fetch from API
result = make_api_request(api_base_url, "/api/v1/services", method="GET")
services = result.get("services", [])

options = services + ["All Services (No Filter)"]
```

### Per-Query Service Override

Allow specifying different service for different sections:
```python
service_overrides = {
    "OVERVIEW": "adminservice",
    "ARCHITECTURE": "All Services",  # Compare across services
    "API": "adminservice"
}
```

### Service Comparison Mode

Generate documentation comparing implementations across services:
```python
comparison_mode = st.checkbox("Enable Service Comparison")
if comparison_mode:
    services_to_compare = st.multiselect(
        "Services to Compare",
        ["adminservice", "Hackathon", "authservice"]
    )
```

---

## Summary

### What Was Fixed

✅ **Service Selector Added**: Prominent UI to choose target service  
✅ **Config Persistence**: Service filter saved in session state  
✅ **Query Filtering**: All queries now include `service_name` parameter  
✅ **Visual Feedback**: Clear display of active service filter  
✅ **Documentation**: Help text and warnings guide users  

### Impact

- **Before**: Queries returned mixed results from all services
- **After**: Queries filtered to selected service only

### Test Status

- ✅ UI changes deployed
- ✅ Config persistence implemented
- ✅ Query filtering added
- ✅ Dashboard restarted
- ⏳ Ready for user testing

---

**Deployment Status**: ✅ **SERVICE FILTERING DEPLOYED**  
**Dashboard URL**: **http://localhost:8501**  
**Next Steps**: 
1. 🔄 **Refresh dashboard** in browser (hard reload: Cmd+Shift+R)
2. 🎯 **Select "adminservice"** in service dropdown
3. 📖 **Generate documentation** and verify adminservice content

