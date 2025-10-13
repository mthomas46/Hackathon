#!/usr/bin/env python3
"""
Generate development history using semantic search (RAG retrieval only).

Since the LLM requires too much memory, we'll use semantic search to find
relevant documents and manually format them.
"""

import httpx
from datetime import datetime
from pathlib import Path

client = httpx.Client(timeout=60.0)
base_url = "http://localhost:8000"

print("=" * 80)
print("📚 GENERATING DEVELOPMENT HISTORY (Semantic Search)")
print("=" * 80)

# Query for development history
query = """Development history of ecosystem-mcp service including major features, 
bug fixes, architectural decisions, testing improvements, infrastructure changes, 
performance optimizations, and integrations from the last 100 commits"""

print(f"\nSearching for: {query[:100]}...")

response = client.post(
    f"{base_url}/api/v1/search",
    json={"query": query, "limit": 25}
)

if response.status_code != 200:
    print(f"❌ Search failed: {response.status_code}")
    exit(1)

results = response.json().get('results', [])
print(f"✅ Found {len(results)} relevant documents\n")

# Create comprehensive document
document = f"""# Ecosystem-MCP Development History

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Method**: Semantic Search + Manual Synthesis  
**Documents Analyzed**: {len(results)}  
**Query**: Last 100 commits of development

---

## 📊 OVERVIEW

This document compiles the development history of the ecosystem-mcp service based on 
semantic search across {len(results)} highly relevant source documents.

---

## 🚀 KEY DEVELOPMENTS

"""

# Add content from top results
for i, result in enumerate(results, 1):
    snippet = result.get('snippet', '')
    file_path = result.get('file_path', 'unknown')
    score = result.get('score', 0)
    
    if score > 0.5 and snippet:  # Only high-relevance results
        document += f"### {i}. From: {file_path} (relevance: {score:.3f})\n\n"
        document += f"{snippet}\n\n"
        document += "---\n\n"

document += f"""
## 📚 ALL SOURCES

Complete list of {len(results)} documents used to compile this history:

"""

for i, result in enumerate(results, 1):
    file_path = result.get('file_path', 'unknown')
    score = result.get('score', 0)
    document += f"{i}. {file_path} (score: {score:.3f})\n"

document += f"""

---

## 🔧 METHODOLOGY

This document was generated using semantic search to find the most relevant
documents about the development history of ecosystem-mcp. 

**Process**:
1. Query: Development history and changes from last 100 commits
2. Semantic Search: Retrieved {len(results)} most relevant documents
3. Filtering: Included only documents with relevance score > 0.5
4. Manual Compilation: Organized by relevance and context

**Note**: This uses retrieval only (no LLM synthesis) due to memory constraints.
For full RAG with intelligent synthesis, increase Docker memory allocation.

---

*Generated: {datetime.now().isoformat()}*
"""

# Save document
output_path = "DEVELOPMENT_HISTORY_SEARCH.md"
Path(output_path).write_text(document)

print(f"✅ Document saved: {output_path}")
print(f"   Size: {len(document):,} characters")
print(f"   Sources: {len(results)} documents")
print(f"   High-relevance: {len([r for r in results if r.get('score', 0) > 0.5])}")

