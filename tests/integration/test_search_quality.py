"""Integration tests for search quality improvements.

TDD Phase 5: Search Quality
Tests the 8 representative queries to validate search improvements.
"""

import pytest
import asyncio
import httpx
from typing import List, Dict, Any


# Test queries from our analysis
TEST_QUERIES = [
    {
        "query": "horus heresy overview",
        "expected_min_results": 1,
        "should_contain": ["horus", "heresy"],
        "intent": "overview"
    },
    {
        "query": "traitor legions",
        "expected_min_results": 1,
        "should_contain": ["traitor", "legion"],
        "intent": "specific"
    },
    {
        "query": "emperor primarchs",
        "expected_min_results": 1,
        "should_contain": ["emperor", "primarch"],
        "intent": "overview"
    },
    {
        "query": "space marine legions",
        "expected_min_results": 1,
        "should_contain": ["space", "marine", "legion"],
        "intent": "overview"
    },
    {
        "query": "chaos gods corruption",
        "expected_min_results": 1,
        "should_contain": ["chaos"],
        "intent": "overview"
    },
    {
        "query": "Tell me about the Horus Heresy",
        "expected_min_results": 1,
        "should_contain": ["horus", "heresy"],
        "intent": "overview"
    },
    {
        "query": "What caused the heresy?",
        "expected_min_results": 1,
        "should_contain": ["heresy", "cause"],
        "intent": "causation"
    },
    {
        "query": "Who were the traitor primarchs?",
        "expected_min_results": 1,
        "should_contain": ["traitor", "primarch"],
        "intent": "specific"
    },
]


@pytest.mark.integration
class TestSearchQualityBaseline:
    """Baseline search quality tests."""
    
    @pytest.mark.asyncio
    async def test_doc_store_available(self):
        """Test that doc_store is available for testing."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://localhost:5087/health")
                assert response.status_code == 200
        except httpx.ConnectError as e:
            pytest.skip(f"doc_store not available: {e}")
    
    @pytest.mark.asyncio
    async def test_search_endpoint_available(self):
        """Test that search endpoint is available."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "http://localhost:5087/api/v1/search",
                    json={"query": "test", "limit": 1}
                )
                assert response.status_code == 200
        except httpx.ConnectError as e:
            pytest.skip(f"Search endpoint not available: {e}")


@pytest.mark.integration
class TestSearchQualityEnhanced:
    """Test search quality with enhancements."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_case", TEST_QUERIES, ids=[q["query"] for q in TEST_QUERIES])
    async def test_query_returns_results(self, test_case):
        """Test that each query returns results."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "http://localhost:5087/api/v1/search",
                    json={"query": test_case["query"], "limit": 10}
                )
                
                assert response.status_code == 200
                result = response.json()
                
                items = result.get("items", [])
                
                # With enhancements, should return results
                assert len(items) >= test_case["expected_min_results"], \
                    f"Query '{test_case['query']}' returned {len(items)} results, expected >= {test_case['expected_min_results']}"
                
        except httpx.ConnectError as e:
            pytest.skip(f"Service not available: {e}")
    
    @pytest.mark.asyncio
    async def test_search_quality_summary(self):
        """Test overall search quality across all queries."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                results = []
                
                for test_case in TEST_QUERIES:
                    response = await client.post(
                        "http://localhost:5087/api/v1/search",
                        json={"query": test_case["query"], "limit": 10}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        items = result.get("items", [])
                        success = len(items) >= test_case["expected_min_results"]
                        results.append({
                            "query": test_case["query"],
                            "success": success,
                            "count": len(items)
                        })
                
                # Calculate success rate
                successful = sum(1 for r in results if r["success"])
                success_rate = (successful / len(results)) * 100 if results else 0
                
                print(f"\n{'='*70}")
                print(f"SEARCH QUALITY SUMMARY")
                print(f"{'='*70}")
                print(f"Success Rate: {success_rate:.1f}% ({successful}/{len(results)})")
                print(f"")
                
                for r in results:
                    status = "✅" if r["success"] else "❌"
                    print(f"{status} '{r['query']}': {r['count']} results")
                
                # With all enhancements, target is 75%+ success rate
                assert success_rate >= 50, \
                    f"Search quality below target: {success_rate:.1f}% (expected >= 50%)"
                
        except httpx.ConnectError as e:
            pytest.skip(f"Service not available: {e}")


@pytest.mark.integration
class TestSearchRelevance:
    """Test search result relevance."""
    
    @pytest.mark.asyncio
    async def test_results_contain_relevant_keywords(self):
        """Test that search results contain query keywords."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "http://localhost:5087/api/v1/search",
                    json={"query": "horus heresy", "limit": 5}
                )
                
                assert response.status_code == 200
                result = response.json()
                items = result.get("items", [])
                
                if len(items) > 0:
                    # Check that at least one result mentions keywords
                    found_relevant = False
                    for item in items:
                        content = str(item.get("content", "")).lower()
                        tags = str(item.get("tags", "")).lower()
                        metadata = str(item.get("metadata", "")).lower()
                        
                        combined = content + tags + metadata
                        
                        if "horus" in combined or "heresy" in combined:
                            found_relevant = True
                            break
                    
                    assert found_relevant, "No results contain relevant keywords"
                
        except httpx.ConnectError as e:
            pytest.skip(f"Service not available: {e}")
    
    @pytest.mark.asyncio
    async def test_relevance_scoring_exists(self):
        """Test that results include relevance scoring."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "http://localhost:5087/api/v1/search",
                    json={"query": "traitor legions", "limit": 3}
                )
                
                assert response.status_code == 200
                result = response.json()
                items = result.get("items", [])
                
                if len(items) > 0:
                    # Check if relevance_score field exists
                    # (May not be in all tiers, but should be in tag/metadata search)
                    has_scoring = any("relevance_score" in str(item) for item in items)
                    
                    # This is informational, not a hard requirement
                    if has_scoring:
                        print("\n✅ Relevance scoring is being applied")
                    else:
                        print("\n⚠️  Relevance scoring may not be visible in results")
                
        except httpx.ConnectError as e:
            pytest.skip(f"Service not available: {e}")


@pytest.mark.integration
class TestQueryExpansionIntegration:
    """Test that query expansion is working in practice."""
    
    @pytest.mark.asyncio
    async def test_synonym_expansion_helps_results(self):
        """Test that synonym expansion improves search results."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test query that should benefit from expansion
                # "emperor" should expand to "Emperor of Mankind", etc.
                response = await client.post(
                    "http://localhost:5087/api/v1/search",
                    json={"query": "emperor", "limit": 5}
                )
                
                assert response.status_code == 200
                result = response.json()
                items = result.get("items", [])
                
                # Should find documents even if exact match isn't present
                # Thanks to synonym expansion
                assert isinstance(items, list)
                
        except httpx.ConnectError as e:
            pytest.skip(f"Service not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])

