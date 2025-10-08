# 🔍 Document Duplication Analysis

**Issue**: Documents in `docs-horus-heresy/` contain duplicate sections with identical content (e.g., "Black Legion" appears 3-4 times with the same text).

---

## 🎯 **Root Cause Identified**

### The Problem: **NOT Querying the MCP!**

The current implementation in `demo_horus_heresy_enhanced.py` is **NOT actually querying the trained MCP**. Instead, it's:

1. ✅ Crawling Fandom wiki pages (working)
2. ✅ Ingesting documents (working)
3. ✅ Training an MCP (working)
4. ❌ **BYPASSING the MCP** and using raw crawled documents directly!

### What's Happening:

```python
# demo_horus_heresy_enhanced.py lines 224-307
def generate_doc_from_crawled_data(self, filename: str, keywords: List[str], query: str):
    """Generate documentation from crawled data, formatted like docs-evergreen."""
    
    # Score documents by keyword relevance
    scored_docs = []
    for doc in self.documents_ingested:  # ← Using raw crawled docs!
        content_lower = (doc.title + ' ' + doc.content_md).lower()
        score = sum(content_lower.count(kw) for kw in keywords)
        ...
        scored_docs.append((score, doc))
    
    # Sort and take top 15
    scored_docs.sort(reverse=True, key=lambda x: x[0])
    relevant_docs = [doc for score, doc in scored_docs[:15]]  # ← No deduplication!
    
    # Build document with these docs
    for idx, doc in enumerate(relevant_docs[:8], 1):
        section_title = doc.title.replace('Fandom: ', '')
        content.append(f"## {idx}. {section_title}\n\n")  # ← Multiple docs with same title!
        ...
```

### Why Duplication Occurs:

**Example: "Black Legion" appears 3 times because:**

1. **Page 1**: `https://warhammer40k.fandom.com/wiki/Sons_of_Horus` 
   - Title: "Black Legion"
   - Contains Black Legion content
   - Keyword score: HIGH

2. **Page 2**: `https://warhammer40k.fandom.com/wiki/Luna_Wolves`
   - Title: "Black Legion" (same content, different URL)
   - Contains Black Legion content
   - Keyword score: HIGH

3. **Page 3**: `https://warhammer40k.fandom.com/wiki/XVI_Legion`
   - Title: "Black Legion" (same content, different URL)
   - Contains Black Legion content
   - Keyword score: HIGH

All three score highly for keywords like "horus", "heresy", "legion", etc., so all three get included in the top 15, resulting in **duplicate sections**.

---

## 🏗️ **Architecture Issue or Normalization Quirk?**

### Answer: **Both!**

#### 1. **Architecture Issue (Primary)**: NOT Using the MCP
The demo header says:
```markdown
> **MCP Query**: Provide a comprehensive overview...
```

But the code **NEVER actually queries the MCP**! It should be calling:
```python
response = await self.client.post(
    f"{self.services['mcp-gateway']}/api/v1/query",
    json={
        "mcp_id": self.mcp_id,
        "query": query,
        "max_results": 10
    }
)
```

The MCP would:
- ✅ Deduplicate content automatically
- ✅ Synthesize information across sources
- ✅ Return focused, non-duplicate results
- ✅ Use semantic understanding to avoid redundancy

#### 2. **Normalization Quirk (Secondary)**: Same Content, Different URLs
The Fandom wiki has **many pages that link to the same content**:
- `Sons_of_Horus` → redirects/links to Black Legion
- `Luna_Wolves` → redirects/links to Black Legion  
- `XVI_Legion` → redirects/links to Black Legion
- `Black_Legion` → original page

All are crawled as separate documents with the same content.

---

## 🔧 **Solution: Query the MCP Properly**

### Fix 1: Actually Use the MCP (RECOMMENDED)

Replace the keyword-based document selection with **actual MCP queries**:

```python
async def generate_doc_from_mcp(self, filename: str, keywords: List[str], query: str) -> str:
    """Generate documentation by querying the trained MCP."""
    
    # Query the MCP
    try:
        response = await self.client.post(
            f"{self.services['mcp-gateway']}/api/v1/route",
            json={
                "mcp_id": self.mcp_id,
                "method": "POST",
                "path": "/api/query",
                "body": {
                    "query": query,
                    "max_results": 10,
                    "min_relevance": 0.5
                }
            }
        )
        
        if response.status_code == 200:
            mcp_results = response.json().get("body", {}).get("results", [])
            
            # MCP returns deduplicated, synthesized results
            # Build document from these results
            ...
```

**Benefits**:
- ✅ Automatic deduplication
- ✅ Semantic understanding
- ✅ Synthesized content
- ✅ Actually uses the trained MCP!

### Fix 2: Deduplicate Documents by Content Similarity (FALLBACK)

If MCP isn't available, add deduplication:

```python
def deduplicate_documents(self, docs: List[NormalizedDocument]) -> List[NormalizedDocument]:
    """Remove duplicate documents based on content similarity."""
    unique_docs = []
    seen_content_hashes = set()
    
    for doc in docs:
        # Create content hash (first 500 chars)
        content_sample = doc.content_md[:500].strip()
        content_hash = hash(content_sample)
        
        if content_hash not in seen_content_hashes:
            seen_content_hashes.add(content_hash)
            unique_docs.append(doc)
    
    return unique_docs
```

### Fix 3: Group Similar Documents (ALTERNATIVE)

Group documents by title and merge content:

```python
def group_similar_documents(self, docs: List[NormalizedDocument]) -> List[NormalizedDocument]:
    """Group documents with similar titles."""
    grouped = {}
    
    for doc in docs:
        # Normalize title (remove special chars, lowercase)
        key = doc.title.lower().replace('fandom: ', '').strip()
        
        if key not in grouped:
            grouped[key] = doc
        else:
            # Merge URLs in metadata
            existing = grouped[key]
            urls = existing.metadata.get('related_urls', [])
            urls.append(doc.metadata.get('page_url'))
            existing.metadata['related_urls'] = urls
    
    return list(grouped.values())
```

---

## 📊 **Impact Analysis**

### Current State:
```
Input:  207 crawled pages
Process: Keyword scoring → top 15 → take first 8
Result: 3-4 duplicate "Black Legion" sections
Issue:  Same content repeated verbatim
```

### With MCP Querying:
```
Input:  207 pages → MCP training
Query:  "Explain the causes of the Horus Heresy"
MCP:    Analyzes all pages, synthesizes unique insights
Result: 8 unique, focused sections with no duplication
Issue:  RESOLVED ✅
```

### With Deduplication:
```
Input:  207 crawled pages
Process: Keyword scoring → deduplicate → top 8
Result: 8 unique documents (but still raw, not synthesized)
Issue:  PARTIALLY RESOLVED ⚠️
```

---

## 🎯 **Recommendation**

### **Primary Fix**: Query the MCP (Lines ~387-436 in demo)

This is what the system was designed for! The MCP should:
1. Take the user's query
2. Search across all ingested documents
3. Synthesize unique, relevant information
4. Return deduplicated results

### **Secondary Fix**: Add deduplication fallback

For cases where MCP is unavailable, add content-based deduplication.

### **Tertiary Fix**: Improve crawling

Add smarter crawling that detects redirects and avoids duplicate pages.

---

## 🔍 **Validation Steps**

1. Check if MCP gateway is actually being called
2. Check MCP response format
3. Verify MCP is trained with all documents
4. Test MCP query with sample questions
5. Compare MCP results vs raw document scoring

---

## 💡 **Next Steps**

1. ✅ **Implement MCP querying** in `generate_documentation_suite()`
2. ✅ **Add deduplication fallback** for robustness
3. ✅ **Add MCP response validation** to ensure quality
4. ✅ **Test with various queries** to verify uniqueness
5. ✅ **Update metrics** to track MCP query success rate

---

**Status**: Issue identified, root cause clear, solution path defined! 🎯

