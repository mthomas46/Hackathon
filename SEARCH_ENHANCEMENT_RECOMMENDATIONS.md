# Search Enhancement Recommendations

**Date**: October 8, 2025  
**Status**: 📋 **ANALYSIS & RECOMMENDATIONS**  
**Current Success Rate**: 25% (2/8 test queries successful)

---

## 🔍 Test Results Analysis

### Current Performance

```
✅ 'traitor legions': 3 results  
✅ 'space marine legions': 3 results  
❌ 'horus heresy overview': 0 results  
❌ 'emperor primarchs': 0 results  
❌ 'chaos gods corruption': 0 results  
❌ 'Tell me about the Horus Heresy': 0 results  
❌ 'What caused the heresy?': 0 results  
❌ 'Who were the traitor primarchs?': 0 results  

Success Rate: 25%
```

### Key Findings

1. **✅ Working**: Multi-word exact matches ("traitor legions", "space marine legions")
2. **❌ Failing**: Phrase combinations ("horus heresy overview"), natural language
3. **⚠️ Critical Issue**: Documents have **EMPTY TAGS AND METADATA**
   ```json
   "metadata": "{}"
   "tags": "[]"
   ```

---

## 🎯 PRIMARY RECOMMENDATIONS

### 1. Leverage Tagging Infrastructure (HIGH PRIORITY)

**Problem**: Universal Tagging Manager exists but tags aren't being populated in stored documents.

**Solution**: Ensure tags flow through to doc_store

#### Implementation Steps:

**A. Verify Tag Generation**
```python
# In ingestion/fandom_ingestor.py or kafka-ingestion-service
# Ensure tags are applied BEFORE sending to doc_store

async def crawl(self, origin_url: str, ...):
    # ... crawling logic ...
    
    # ✅ ENSURE THIS HAPPENS:
    if self.tagging_manager:
        tagged_docs, tag_collection = await self.tagging_manager.tag_documents(
            documents=documents,
            source_type='wikipedia',  # or 'fandom'
            user_tags=user_tags,
            corpus_analysis=corpus_results if enable_corpus_analysis else None
        )
        documents = tagged_docs  # ✅ Use tagged documents!
```

**B. Store Tags in doc_store**
```python
# In services/kafka-ingestion-service/main_simple.py
# CURRENT: Only content + metadata
doc_payload = {
    "content": content,
    "metadata": metadata,
}

# ENHANCED: Include tags
doc_payload = {
    "content": content,
    "metadata": metadata,
    "tags": document.get("tags", []),  # ✅ ADD THIS
}
```

**C. Search with Tags**
```python
# In services/doc_store/db/queries.py
def search_documents(query: str, limit: int = 50):
    """Enhanced search with tag matching."""
    # ... keyword extraction ...
    
    # NEW: Try tag-based search first
    tag_results = execute_query(
        """
        SELECT DISTINCT d.rowid 
        FROM documents d
        WHERE d.tags LIKE ? OR d.tags LIKE ? OR d.tags LIKE ?
        LIMIT ?
        """,
        (f'%{keywords[0]}%', f'%{keywords[1]}%', f'%{keywords[2]}%', limit),
        fetch_all=True
    )
    
    if tag_results:
        return fetch_documents(tag_results)
    
    # FALLBACK: Continue with FTS...
```

### 2. Enhanced Search with Semantic Layers (MEDIUM PRIORITY)

**Problem**: Queries like "horus heresy overview" should match "horus" OR "heresy" OR "overview".

**Solution**: Multi-tier search strategy

```python
def search_documents_enhanced(query: str, limit: int = 50):
    """Multi-tier search with tag, FTS, and content matching."""
    keywords = extract_keywords(query)  # Existing
    
    results = []
    
    # TIER 1: Tag-based search (FAST, HIGH PRECISION)
    results = search_by_tags(keywords, limit)
    if results:
        return results
    
    # TIER 2: Metadata search (MEDIUM SPEED, GOOD PRECISION)
    results = search_by_metadata(keywords, limit)
    if results:
        return results
    
    # TIER 3: FTS search (FAST, MEDIUM PRECISION)
    results = search_by_fts_or(keywords, limit)
    if results:
        return results
    
    # TIER 4: Content LIKE search (SLOW, LOW PRECISION)
    results = search_by_content_like(keywords, limit)
    
    return results
```

### 3. Query Expansion & Synonyms (MEDIUM PRIORITY)

**Problem**: "emperor" doesn't match "Emperor of Mankind", "primarchs" doesn't match "Primarch".

**Solution**: Domain-specific synonym expansion

```python
# In services/doc_store/db/query_expansion.py
WARHAMMER_SYNONYMS = {
    'emperor': ['Emperor of Mankind', 'Master of Mankind', 'God-Emperor'],
    'primarch': ['Primarchs', 'gene-son', 'gene-sons', 'gene-father'],
    'space marine': ['Astartes', 'Legiones Astartes', 'Space Marines'],
    'heresy': ['Horus Heresy', 'Great Betrayal', 'civil war'],
    'chaos': ['Chaos Gods', 'Ruinous Powers', 'Dark Gods', 'Warp'],
    'traitor': ['Traitor Legions', 'Fallen', 'Heretic Astartes'],
    'loyalist': ['Loyalist Legions', 'Faithful'],
}

def expand_query(query: str) -> List[str]:
    """Expand query with domain synonyms."""
    expanded = [query]  # Original
    
    words = query.lower().split()
    for word in words:
        if word in WARHAMMER_SYNONYMS:
            for synonym in WARHAMMER_SYNONYMS[word]:
                # Add variants
                expanded.append(synonym)
    
    return expanded

def search_with_expansion(query: str, limit: int):
    """Search with query expansion."""
    expansions = expand_query(query)
    
    results = []
    for expanded_query in expansions:
        results.extend(search_documents(expanded_query, limit // len(expansions)))
        if len(results) >= limit:
            break
    
    # Deduplicate by document ID
    seen = set()
    unique_results = []
    for doc in results:
        if doc['id'] not in seen:
            seen.add(doc['id'])
            unique_results.append(doc)
    
    return unique_results[:limit]
```

### 4. Metadata-Enhanced Search (HIGH PRIORITY)

**Problem**: Rich metadata exists but isn't being used for search.

**Solution**: Multi-field search across content + metadata

```python
# In services/doc_store/db/queries.py
def search_documents_multifield(query: str, limit: int = 50):
    """Search across content, metadata, and tags."""
    keywords = extract_keywords(query)
    
    # Build comprehensive search query
    search_conditions = []
    params = []
    
    for keyword in keywords[:5]:
        # Search in content
        search_conditions.append("content LIKE ?")
        params.append(f"%{keyword}%")
        
        # Search in metadata (JSON fields)
        search_conditions.append("metadata LIKE ?")
        params.append(f"%{keyword}%")
        
        # Search in tags
        search_conditions.append("tags LIKE ?")
        params.append(f"%{keyword}%")
    
    query_sql = f"""
        SELECT DISTINCT rowid, 
               (
                   (CASE WHEN content LIKE ? THEN 10 ELSE 0 END) +
                   (CASE WHEN tags LIKE ? THEN 5 ELSE 0 END) +
                   (CASE WHEN metadata LIKE ? THEN 3 ELSE 0 END)
               ) as relevance_score
        FROM documents
        WHERE {' OR '.join(search_conditions)}
        ORDER BY relevance_score DESC
        LIMIT ?
    """
    
    # Add scoring params + original params
    scoring_params = []
    for keyword in keywords[:3]:
        scoring_params.extend([f"%{keyword}%"] * 3)  # content, tags, metadata
    
    params = tuple(scoring_params + params + [limit])
    
    return execute_query(query_sql, params, fetch_all=True)
```

---

## 🤖 MCP RESPONSE CONTEXTUALIZATION

### Current Problem

**Generic Response**:
```
No relevant training documents found for query: Provide a comprehensive 
overview of the Horus Heresy, including what it was, when it occurred, 
and its significance

Confidence: 0.0
Sources: 
```

**Issues**:
- ❌ Doesn't address the question
- ❌ No helpful context
- ❌ Doesn't guide user
- ❌ Poor user experience

### Recommended Solution: Contextual Response Generation

#### Implementation in MCP Base Image

```python
# In docker/mcp-base/Dockerfile or MCP query handler
def generate_contextual_response(query_text: str, docs: List[Dict], confidence: float) -> str:
    """Generate contextual response based on query and results."""
    
    # Case 1: No documents found
    if not docs or len(docs) == 0:
        return generate_no_results_response(query_text)
    
    # Case 2: Low confidence
    if confidence < 0.3:
        return generate_low_confidence_response(query_text, docs)
    
    # Case 3: Good results
    return generate_synthesis_response(query_text, docs, confidence)

def generate_no_results_response(query: str) -> str:
    """Generate helpful response when no documents found."""
    # Extract key terms
    key_terms = extract_key_terms(query)
    
    # Suggest alternatives
    suggestions = generate_search_suggestions(key_terms)
    
    return f"""
I couldn't find specific documents matching your query about "{query}".

This could mean:
• The training data doesn't include information on this specific topic
• The query terms might need to be rephrased
• Related information might be under different terminology

Suggested searches:
{chr(10).join(f'• {s}' for s in suggestions)}

Would you like to try a more specific or different query?
"""

def generate_synthesis_response(query: str, docs: List[Dict], confidence: float) -> str:
    """Synthesize documents into contextual answer."""
    # Extract relevant snippets
    snippets = extract_relevant_snippets(query, docs, max_snippets=3)
    
    # Identify query intent
    intent = classify_query_intent(query)  # 'overview', 'specific', 'comparison', etc.
    
    # Generate contextual intro
    intro = generate_intent_based_intro(intent, query)
    
    # Combine snippets with context
    response = f"{intro}\n\n"
    
    for i, snippet in enumerate(snippets, 1):
        source_doc = snippet['doc_id']
        content = snippet['content']
        response += f"**From {source_doc}:**\n{content}\n\n"
    
    # Add confidence and sources
    response += f"\n**Confidence**: {confidence:.2f}\n"
    response += f"**Sources**: {', '.join(d['id'] for d in docs[:3])}\n"
    
    return response

def classify_query_intent(query: str) -> str:
    """Classify query intent for contextual responses."""
    query_lower = query.lower()
    
    # Overview/General
    if any(w in query_lower for w in ['overview', 'what is', 'tell me about', 'explain']):
        return 'overview'
    
    # Cause/Reason
    if any(w in query_lower for w in ['why', 'cause', 'reason', 'led to']):
        return 'causation'
    
    # Timeline/Chronology
    if any(w in query_lower for w in ['when', 'timeline', 'chronology', 'sequence']):
        return 'temporal'
    
    # Comparison
    if any(w in query_lower for w in ['compare', 'difference', 'versus', 'vs']):
        return 'comparison'
    
    # Specific detail
    if any(w in query_lower for w in ['who', 'which', 'name', 'list']):
        return 'specific'
    
    return 'general'

def generate_intent_based_intro(intent: str, query: str) -> str:
    """Generate contextual introduction based on query intent."""
    intros = {
        'overview': f"Here's an overview based on the training documents about {extract_topic(query)}:",
        'causation': f"Based on the training documents, here's what led to {extract_topic(query)}:",
        'temporal': f"Here's the timeline of events related to {extract_topic(query)}:",
        'comparison': f"Here's a comparison based on the available training documents:",
        'specific': f"Here's specific information about {extract_topic(query)}:",
        'general': f"Based on the training documents, here's what I found:"
    }
    
    return intros.get(intent, intros['general'])

def extract_relevant_snippets(query: str, docs: List[Dict], max_snippets: int = 3) -> List[Dict]:
    """Extract most relevant snippets from documents."""
    keywords = extract_keywords(query)
    snippets = []
    
    for doc in docs:
        content = doc.get('content', '')
        
        # Find paragraphs containing keywords
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            keyword_count = sum(1 for kw in keywords if kw.lower() in para.lower())
            if keyword_count > 0:
                snippets.append({
                    'doc_id': doc['id'],
                    'content': para[:500] + '...' if len(para) > 500 else para,
                    'relevance': keyword_count
                })
        
        if len(snippets) >= max_snippets * 2:
            break
    
    # Sort by relevance and return top snippets
    snippets.sort(key=lambda x: x['relevance'], reverse=True)
    return snippets[:max_snippets]
```

---

## 📊 IMPLEMENTATION PRIORITY MATRIX

| Enhancement | Priority | Impact | Effort | ROI |
|-------------|----------|--------|--------|-----|
| **1. Populate Tags in doc_store** | 🔴 HIGH | 🟢 HIGH | 🟡 MEDIUM | ⭐⭐⭐⭐⭐ |
| **2. Multi-field Search** | 🔴 HIGH | 🟢 HIGH | 🟢 LOW | ⭐⭐⭐⭐⭐ |
| **3. Contextual MCP Responses** | 🔴 HIGH | 🟢 HIGH | 🟡 MEDIUM | ⭐⭐⭐⭐⭐ |
| **4. Query Expansion/Synonyms** | 🟡 MEDIUM | 🟢 HIGH | 🟡 MEDIUM | ⭐⭐⭐⭐ |
| **5. Relevance Scoring** | 🟡 MEDIUM | 🟡 MEDIUM | 🟡 MEDIUM | ⭐⭐⭐ |
| **6. Semantic Embeddings** | 🟢 LOW | 🟢 HIGH | 🔴 HIGH | ⭐⭐⭐ |

---

## 🚀 QUICK WINS (Implement First)

### Quick Win #1: Tag Population (2-3 hours)

**File**: `services/kafka-ingestion-service/main_simple.py`

```python
# Line ~90 (in ingest_document endpoint)
doc_payload = {
    "content": content,
    "metadata": metadata,
    "tags": event_data.get("tags", []),  # ✅ ADD THIS LINE
}
```

**Expected Impact**: Tags become searchable, 50-75% success rate improvement

### Quick Win #2: Multi-keyword OR Search (1 hour)

Already implemented! Just needs FTS table properly populated.

### Quick Win #3: Contextual No-Results Response (2 hours)

**File**: `docker/mcp-base/Dockerfile`

```python
# Replace generic "No relevant training documents" with:
if not docs or len(docs) == 0:
    suggestions = generate_suggestions(query_keywords)
    answer = f"""
I couldn't find documents specifically about {extract_main_topic(query)}.

Suggestions:
• Try more specific terms
• Break down the question into parts
• Related topics: {', '.join(suggestions)}

Would you like to rephrase your query?
"""
```

**Expected Impact**: Better user experience, actionable feedback

---

## 📈 EXPECTED OUTCOMES

### After Quick Wins

```
Before:  25% success rate
After:   75-85% success rate

Test Results (Expected):
✅ 'traitor legions': 3 results  
✅ 'space marine legions': 3 results  
✅ 'horus heresy overview': 2+ results  ← FIXED
✅ 'emperor primarchs': 2+ results      ← FIXED
✅ 'chaos gods corruption': 1+ results  ← FIXED
✅ 'Tell me about the Horus Heresy': 2+ results  ← FIXED
⚠️ 'What caused the heresy?': 1+ results (needs synonyms)
⚠️ 'Who were the traitor primarchs?': 1+ results (needs synonyms)
```

### After Full Implementation

```
Success Rate: 90%+
Contextual Responses: 100%
User Satisfaction: HIGH
```

---

## 🧪 TESTING STRATEGY

### Test Suite Enhancement

```python
# tests/integration/test_search_quality.py
import pytest

@pytest.mark.integration
class TestSearchQuality:
    """Test search quality with various query types."""
    
    async def test_multi_word_queries(self):
        """Test multi-word keyword queries."""
        queries = [
            "horus heresy overview",
            "traitor legions",
            "space marine legions"
        ]
        
        for query in queries:
            results = await search(query)
            assert len(results) > 0, f"Failed: {query}"
    
    async def test_natural_language_queries(self):
        """Test natural language queries."""
        queries = [
            "Tell me about the Horus Heresy",
            "What caused the heresy?",
            "Who were the traitor primarchs?"
        ]
        
        for query in queries:
            results = await search(query)
            assert len(results) > 0, f"Failed: {query}"
    
    async def test_tag_based_search(self):
        """Test tag-based search."""
        # Assuming documents are tagged
        results = await search("source:fandom-wiki character:Horus")
        assert len(results) > 0
    
    async def test_contextual_responses(self):
        """Test MCP contextual response generation."""
        response = await query_mcp("What is the Horus Heresy?")
        
        # Should not be generic "No relevant documents"
        assert "No relevant training documents" not in response.content
        
        # Should have contextual intro
        assert any(phrase in response.content.lower() for phrase in [
            "here's", "based on", "overview", "according to"
        ])
```

---

## 💡 ADVANCED ENHANCEMENTS (Future)

### 1. Vector Embeddings for Semantic Search

```python
# Using sentence-transformers
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_documents(documents):
    """Generate embeddings for documents."""
    embeddings = model.encode([d['content'] for d in documents])
    return embeddings

def search_by_similarity(query: str, limit: int = 10):
    """Search by semantic similarity."""
    query_embedding = model.encode([query])[0]
    
    # Retrieve all document embeddings (from cache/db)
    doc_embeddings = load_document_embeddings()
    
    # Calculate cosine similarity
    similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
    
    # Get top-k most similar
    top_indices = similarities.argsort()[-limit:][::-1]
    
    return fetch_documents_by_indices(top_indices)
```

### 2. Query Understanding with LLM

```python
async def enhance_query_with_llm(query: str) -> Dict:
    """Use LLM to understand and enhance query."""
    prompt = f"""
    Analyze this query and extract:
    1. Main topic
    2. Intent (overview, specific detail, comparison, etc.)
    3. Key entities
    4. Suggested search terms
    
    Query: {query}
    
    Return JSON format.
    """
    
    response = await llm_client.complete(prompt)
    return json.loads(response)
```

### 3. Learning from User Interactions

```python
def log_search_interaction(query: str, results: List, user_clicked: List[str]):
    """Log search quality for improvement."""
    SearchLog.create({
        'query': query,
        'results_count': len(results),
        'clicked_docs': user_clicked,
        'success': len(user_clicked) > 0
    })

def analyze_failed_searches():
    """Analyze patterns in failed searches."""
    failed = SearchLog.filter(success=False)
    
    # Identify common failure patterns
    common_terms = extract_common_terms([s.query for s in failed])
    
    # Suggest synonym additions
    return generate_synonym_suggestions(common_terms)
```

---

## ✅ ACTION ITEMS

### Immediate (Next 1-2 Days)

1. ✅ Verify tags are generated during ingestion
2. ✅ Ensure tags flow to doc_store
3. ✅ Update search to use tags
4. ✅ Implement contextual MCP responses
5. ✅ Test with existing documents

### Short-term (Next Week)

1. Add query expansion with synonyms
2. Implement multi-field search with scoring
3. Add comprehensive test suite
4. Document search best practices for users

### Long-term (Next Month)

1. Evaluate semantic search (embeddings)
2. Implement query understanding
3. Add analytics and search quality metrics
4. Build feedback loop for continuous improvement

---

**Summary**: The infrastructure is excellent, but tags/metadata aren't being populated in stored documents. Fixing this + adding contextual MCP responses will dramatically improve search quality and user experience.

**ROI**: ~8 hours of implementation = 60% improvement in search success rate + 100% better UX

🎯 **Ready to implement? Start with Quick Win #1!**

