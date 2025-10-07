# 🔍 **Hierarchical Retrieval Guide**

## **Complete Guide to Multi-Tier MCP Retrieval**

---

## **Table of Contents**

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [API Reference](#api-reference)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)
7. [UI Guide](#ui-guide)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## **Overview**

Hierarchical Retrieval enables intelligent querying across multiple MCP (Model Context Protocol) tiers with automatic cascading, token budget management, and customizable prioritization.

### **Key Features**

✅ **Multi-Tier Retrieval** - Query across 5 MCP tiers  
✅ **Automatic Cascading** - Intelligent tier-by-tier search  
✅ **Token Budget Management** - Distribute tokens across tiers  
✅ **Custom Weights** - Configure tier prioritization  
✅ **Score-Based Ranking** - Results ordered by relevance  
✅ **Production-Ready** - Comprehensive tests & error handling  

### **Use Cases**

- Query client-specific knowledge with company-wide fallback
- Progressive context refinement from specific to general
- Cost-effective retrieval with strict token budgets
- Multi-level documentation search
- Hierarchical knowledge base queries

---

## **Architecture**

### **MCP Tier Hierarchy**

```
Priority (High → Low):

1. CLIENT      👤  Most specific, client-focused
   ↓
2. PROJECT     📁  Project-specific information
   ↓
3. COMPANY     🏢  Company-wide knowledge
   ↓
4. TEAM        👥  Team-specific context
   ↓
5. ECOSYSTEM   🌐  Broadest, industry knowledge
```

### **Retrieval Flow**

```
Query Input
    ↓
[Tier Selection]
    ↓
[Token Budget Distribution]
    ↓
┌─────────────────────┐
│ Client Tier (40%)   │ ← Highest Priority
├─────────────────────┤
│ Project Tier (30%)  │
├─────────────────────┤
│ Company Tier (15%)  │
├─────────────────────┤
│ Team Tier (10%)     │
├─────────────────────┤
│ Ecosystem Tier (5%) │ ← Lowest Priority
└─────────────────────┘
    ↓
[Score-Based Ranking]
    ↓
Results Output
```

---

## **Quick Start**

### **Basic Usage**

```python
from mcp_retrieval.src.hierarchical_retrieval import HierarchicalRetriever

# Initialize retriever
retriever = HierarchicalRetriever(
    tiers=["client", "project", "company"],
    token_budget=4000
)

# Execute query
results = retriever.retrieve(
    query="What are our customer support policies?",
    max_results=10
)

# Process results
for result in results:
    print(f"[{result.tier}] {result.content}")
    print(f"Score: {result.score}, Tokens: {result.token_count}")
```

### **Budget-Constrained Retrieval**

```python
# Retrieve with strict token budget
results = retriever.retrieve_with_budget(
    query="Comprehensive technical documentation"
)

# Verify budget respected
total_tokens = sum(r.token_count for r in results)
print(f"Used {total_tokens} / {retriever.token_budget} tokens")
```

---

## **API Reference**

### **HierarchicalRetriever**

#### **Constructor**

```python
HierarchicalRetriever(
    tiers: List[str],
    token_budget: int = 4000,
    tier_weights: Optional[Dict[str, float]] = None
)
```

**Parameters:**
- `tiers` - List of tier names to search (e.g., `["client", "project"]`)
- `token_budget` - Maximum tokens to retrieve (default: 4000)
- `tier_weights` - Custom weights per tier (default: `{"client": 0.4, ...}`)

**Valid Tier Names:**
- `"client"` - Client-specific tier
- `"project"` - Project-specific tier
- `"company"` - Company-wide tier
- `"team"` - Team-specific tier
- `"ecosystem"` - Ecosystem-wide tier

#### **Methods**

##### **retrieve()**

```python
retrieve(
    query: str,
    tiers: Optional[List[str]] = None,
    max_results: int = 10
) -> List[RetrievalResult]
```

Retrieve results with cascading across tiers.

**Parameters:**
- `query` - Search query (required)
- `tiers` - Specific tiers to search (optional, defaults to all)
- `max_results` - Maximum number of results (default: 10)

**Returns:**
- List of `RetrievalResult` objects ordered by score

**Example:**
```python
results = retriever.retrieve(
    query="API authentication requirements",
    tiers=["client", "project"],  # Focus on specific tiers
    max_results=5
)
```

##### **retrieve_with_budget()**

```python
retrieve_with_budget(
    query: str,
    tiers: Optional[List[str]] = None
) -> List[RetrievalResult]
```

Retrieve results respecting token budget.

**Parameters:**
- `query` - Search query (required)
- `tiers` - Specific tiers to search (optional)

**Returns:**
- List of results within token budget

**Example:**
```python
results = retriever.retrieve_with_budget(
    query="Complete project specifications"
)

total_tokens = sum(r.token_count for r in results)
print(f"Budget utilization: {total_tokens / retriever.token_budget:.1%}")
```

### **RetrievalResult**

```python
@dataclass
class RetrievalResult:
    content: str          # Result content
    tier: str            # Source tier
    score: float         # Relevance score (0.0-1.0)
    token_count: int     # Token count
    metadata: Dict       # Additional metadata
```

---

## **Configuration**

### **Default Tier Weights**

```python
DEFAULT_WEIGHTS = {
    "client": 0.4,      # 40%
    "project": 0.3,     # 30%
    "company": 0.15,    # 15%
    "team": 0.1,        # 10%
    "ecosystem": 0.05,  # 5%
}
```

### **Custom Weights**

```python
# Client-focused configuration
retriever = HierarchicalRetriever(
    tiers=["client", "project", "company"],
    tier_weights={
        "client": 0.7,     # 70% - Highest priority
        "project": 0.2,    # 20%
        "company": 0.1,    # 10%
    }
)
```

### **Token Budget Distribution**

Token budget is distributed across tiers based on weights:

```python
# Total budget: 1000 tokens
# Weights: client=0.4, project=0.3, company=0.3

Budget allocation:
- Client: 400 tokens (40%)
- Project: 300 tokens (30%)
- Company: 300 tokens (30%)
```

---

## **Usage Examples**

### **Example 1: Client-Specific Query**

```python
# Focus on client and project tiers
retriever = HierarchicalRetriever(
    tiers=["client", "project"],
    token_budget=2000,
    tier_weights={"client": 0.8, "project": 0.2}
)

results = retriever.retrieve(
    query="What are the specific requirements for Client X's API integration?",
    max_results=5
)

# Results will prioritize client-tier knowledge
for result in results:
    print(f"[{result.tier.upper()}] Score: {result.score:.3f}")
    print(result.content)
    print()
```

### **Example 2: Company-Wide Search**

```python
# Search across all company tiers
retriever = HierarchicalRetriever(
    tiers=["company", "team", "ecosystem"],
    token_budget=3000
)

results = retriever.retrieve(
    query="What are our company's core values and culture?",
    max_results=15
)

# Group results by tier
from collections import defaultdict
by_tier = defaultdict(list)
for result in results:
    by_tier[result.tier].append(result)

for tier, tier_results in by_tier.items():
    print(f"\n{tier.upper()} ({len(tier_results)} results):")
    for r in tier_results[:3]:  # Top 3
        print(f"  - {r.content[:80]}...")
```

### **Example 3: Budget-Constrained Retrieval**

```python
# Strict budget for cost control
retriever = HierarchicalRetriever(
    tiers=["client", "project", "company"],
    token_budget=1000  # Very tight budget
)

results = retriever.retrieve_with_budget(
    query="Quick summary of project status"
)

# Analyze budget usage
total_tokens = sum(r.token_count for r in results)
print(f"Retrieved {len(results)} results")
print(f"Tokens used: {total_tokens} / 1000")
print(f"Budget utilization: {total_tokens/10:.1f}%")

# Verify no over-budget
assert total_tokens <= 1000, "Budget exceeded!"
```

### **Example 4: Progressive Refinement**

```python
# Start broad, then narrow down
retriever = HierarchicalRetriever(
    tiers=["client", "project", "company", "ecosystem"]
)

# Initial broad query
broad_results = retriever.retrieve(
    query="software development best practices",
    max_results=10
)

# Refine to specific tiers based on results
if any(r.tier == "client" for r in broad_results):
    # Found client-specific info, focus there
    specific_results = retriever.retrieve(
        query="client-specific development guidelines",
        tiers=["client", "project"],
        max_results=5
    )
else:
    # Use general knowledge
    specific_results = retriever.retrieve(
        query="general development standards",
        tiers=["company", "ecosystem"],
        max_results=5
    )
```

### **Example 5: Multi-Query Pattern**

```python
# Multiple related queries
retriever = HierarchicalRetriever(
    tiers=["client", "project", "company"]
)

queries = [
    "authentication requirements",
    "authorization policies",
    "session management"
]

all_results = []
for query in queries:
    results = retriever.retrieve(query, max_results=3)
    all_results.extend(results)

# Deduplicate and rank
seen = set()
unique_results = []
for result in sorted(all_results, key=lambda r: r.score, reverse=True):
    if result.content not in seen:
        seen.add(result.content)
        unique_results.append(result)

print(f"Retrieved {len(unique_results)} unique results across {len(queries)} queries")
```

---

## **UI Guide**

### **Accessing the UI**

Navigate to the Hierarchical Retrieval page in the MCP Dashboard.

### **Configuration**

1. **Select Tiers** - Check boxes for desired tiers
2. **Set Budget** - Use slider to set token budget (500-8000)
3. **Adjust Weights** - Fine-tune tier prioritization

### **Executing Queries**

1. **Enter Query** - Type your search query
2. **Choose Mode**:
   - **Standard**: Retrieve up to max results
   - **Budget-Constrained**: Respect token budget strictly
3. **Set Max Results** - (Standard mode only)
4. **Click Execute** - Run the query

### **Viewing Results**

**Summary Metrics:**
- Total results
- Total tokens used
- Number of tiers
- Average score

**Visualizations:**
- Pie charts: Result/token distribution by tier
- Scatter plot: Score distribution
- Histogram: Score analysis

**Detailed Results:**
- Grouped by tier
- Expandable sections
- Top 5 results per tier shown

### **Analytics**

- Token efficiency tracking
- Budget utilization percentage
- Score statistics (min, max, mean, median)
- Tier performance comparison

---

## **Best Practices**

### **1. Choose Appropriate Tiers**

✅ **Good:**
```python
# Client-specific query → Focus on client/project tiers
retriever = HierarchicalRetriever(tiers=["client", "project"])
```

❌ **Avoid:**
```python
# Client query but searching all tiers (unnecessary)
retriever = HierarchicalRetriever(tiers=["client", "project", "company", "team", "ecosystem"])
```

### **2. Set Realistic Token Budgets**

```python
# Small queries: 1000-2000 tokens
# Medium queries: 2000-4000 tokens
# Large queries: 4000-8000 tokens

# Budget should match use case
quick_retriever = HierarchicalRetriever(token_budget=1000)  # Quick answers
comprehensive_retriever = HierarchicalRetriever(token_budget=8000)  # Deep research
```

### **3. Use Budget-Constrained Mode for Cost Control**

```python
# For production with cost constraints
results = retriever.retrieve_with_budget(query)  # Strict budget
# vs
results = retriever.retrieve(query, max_results=100)  # May exceed budget
```

### **4. Adjust Weights Based on Use Case**

```python
# Client support queries → High client weight
support_retriever = HierarchicalRetriever(
    tiers=["client", "company"],
    tier_weights={"client": 0.8, "company": 0.2}
)

# General knowledge queries → Balanced weights
knowledge_retriever = HierarchicalRetriever(
    tiers=["company", "team", "ecosystem"],
    tier_weights={"company": 0.4, "team": 0.3, "ecosystem": 0.3}
)
```

### **5. Handle Empty Results Gracefully**

```python
results = retriever.retrieve(query)

if not results:
    # Fallback: Try broader tiers
    results = retriever.retrieve(
        query,
        tiers=["company", "ecosystem"],
        max_results=5
    )
    
if not results:
    print("No results found. Try rephrasing your query.")
```

### **6. Monitor Performance**

```python
import time

start = time.time()
results = retriever.retrieve(query)
duration = time.time() - start

print(f"Retrieved {len(results)} results in {duration:.2f}s")

# Alert if slow
if duration > 5.0:
    logger.warning(f"Slow retrieval: {duration:.2f}s")
```

---

## **Troubleshooting**

### **No Results Returned**

**Problem:** Query returns empty list

**Solutions:**
1. Try broader query terms
2. Add more tiers to search
3. Check tier data is populated
4. Reduce specificity of query

```python
# Too specific
results = retriever.retrieve("very specific client requirement X.Y.Z")

# Better
results = retriever.retrieve("client requirement X")
```

### **Budget Always Exceeded**

**Problem:** Token budget consistently exceeded

**Solutions:**
1. Increase token budget
2. Use `retrieve_with_budget()` instead of `retrieve()`
3. Reduce number of tiers
4. Lower max_results

```python
# Problem
retriever = HierarchicalRetriever(token_budget=500)
results = retriever.retrieve(query, max_results=100)  # Likely exceeds

# Solution
results = retriever.retrieve_with_budget(query)  # Respects budget
```

### **Low Relevance Scores**

**Problem:** Results have low scores

**Solutions:**
1. Rephrase query for better matching
2. Check tier weights are appropriate
3. Verify data quality in tiers
4. Use more specific query terms

### **Slow Performance**

**Problem:** Retrieval takes too long

**Solutions:**
1. Reduce number of tiers
2. Lower max_results
3. Implement caching
4. Optimize data store queries

---

## **Advanced Topics**

### **Custom Tier Implementation**

In production, replace mock retrieval with actual data store queries:

```python
def _retrieve_from_tier(self, query, tier, tier_weight, max_results):
    # Query ChromaDB
    vector_results = chromadb_client.query(
        query_text=query,
        n_results=max_results,
        where={"tier": tier}
    )
    
    # Query Neo4j
    graph_results = neo4j_client.query(
        "MATCH (n:Knowledge {tier: $tier}) ...",
        tier=tier
    )
    
    # Combine and rank results
    combined = combine_results(vector_results, graph_results)
    
    # Apply tier weight to scores
    for result in combined:
        result.score *= (0.5 + tier_weight * 0.5)
    
    return combined
```

### **Caching**

Implement caching for frequently accessed results:

```python
from functools import lru_cache

class CachedHierarchicalRetriever(HierarchicalRetriever):
    @lru_cache(maxsize=1000)
    def retrieve(self, query, tiers=None, max_results=10):
        return super().retrieve(query, tiers, max_results)
```

---

## **Resources**

- **Source Code:** `services/mcp_retrieval/src/hierarchical_retrieval.py`
- **Unit Tests:** `tests/unit/test_hierarchical_retrieval.py`
- **Integration Tests:** `tests/integration/test_hierarchical_retrieval_integration.py`
- **UI Page:** `dashboard/pages/hierarchical_retrieval.py`

---

**For support or questions, refer to the MCP documentation or contact the development team.**

---

**Happy Retrieving! 🔍**
