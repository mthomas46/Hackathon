#!/usr/bin/env python3
"""Test and analyze search capabilities with tagging/normalization context."""

import httpx
import json
import asyncio
from typing import List, Dict, Any

async def test_search_queries():
    """Test various search queries and analyze results."""
    
    test_queries = [
        "horus heresy overview",
        "traitor legions",
        "emperor primarchs",
        "space marine legions",
        "chaos gods corruption",
        "Tell me about the Horus Heresy",
        "What caused the heresy?",
        "Who were the traitor primarchs?"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        results = []
        
        for query in test_queries:
            print(f"\n{'='*70}")
            print(f"Query: {query}")
            print(f"{'='*70}")
            
            try:
                response = await client.post(
                    "http://localhost:5087/api/v1/search",
                    json={"query": query, "limit": 3}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    total = data.get("total", 0)
                    items = data.get("items", [])
                    
                    print(f"✅ Found: {total} documents, showing {len(items)}")
                    
                    for idx, item in enumerate(items, 1):
                        doc_id = item.get("id", "unknown")
                        content_len = len(item.get("content", ""))
                        metadata = item.get("metadata", "{}")
                        tags = item.get("tags", "[]")
                        
                        print(f"\n  {idx}. Document: {doc_id}")
                        print(f"     Content: {content_len} chars")
                        print(f"     Metadata: {metadata[:100]}...")
                        print(f"     Tags: {tags[:100]}...")
                        
                        # Show snippet
                        content = item.get("content", "")
                        if content:
                            snippet = content[:200].replace('\n', ' ')
                            print(f"     Snippet: {snippet}...")
                    
                    results.append({
                        "query": query,
                        "total": total,
                        "items": len(items),
                        "success": True
                    })
                else:
                    print(f"❌ Error: {response.status_code}")
                    results.append({
                        "query": query,
                        "total": 0,
                        "items": 0,
                        "success": False
                    })
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
                results.append({
                    "query": query,
                    "total": 0,
                    "items": 0,
                    "success": False,
                    "error": str(e)
                })
        
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        successful = sum(1 for r in results if r["success"] and r["total"] > 0)
        print(f"Successful queries: {successful}/{len(test_queries)}")
        print(f"Success rate: {successful/len(test_queries)*100:.1f}%")
        
        for r in results:
            status = "✅" if r["success"] and r["total"] > 0 else "❌"
            print(f"{status} '{r['query']}': {r['total']} results")

if __name__ == "__main__":
    asyncio.run(test_search_queries())
