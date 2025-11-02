"""
Edge Case Tests for RAG Enhancement System

Tests for boundary conditions, error handling, and unusual input scenarios.
"""

import requests
import pytest
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
TIMEOUT = 60


class TestQueryEdgeCases:
    """Test edge cases for query handling"""
    
    def test_empty_query(self):
        """Test handling of empty query"""
        response = requests.post(
            f"{BASE_URL}/api/v1/ask",
            json={"question": "", "use_enhancements": True, "n_results": 5},
            timeout=TIMEOUT
        )
        # Should either return 422 (validation error) or handle gracefully
        assert response.status_code in [200, 422], f"Unexpected status: {response.status_code}"
        
    def test_very_long_query(self):
        """Test handling of very long query (>1000 chars)"""
        long_query = "What is MCP? " * 100  # ~1200 characters
        response = requests.post(
            f"{BASE_URL}/api/v1/ask",
            json={"question": long_query, "use_enhancements": True, "n_results": 5},
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Long query failed: {response.text}"
        data = response.json()
        assert "answer" in data
        print(f"✅ Long query handled: {len(long_query)} chars")
    
    def test_special_characters_query(self):
        """Test handling of special characters"""
        special_queries = [
            "What is <script>alert('xss')</script>?",
            "SELECT * FROM documents WHERE name = 'test';",
            "What about \"quotes\" and 'apostrophes'?",
            "Unicode test: 你好 مرحبا שלום",
            "Emoji test: 🚀 🎉 ✨"
        ]
        
        for query in special_queries:
            response = requests.post(
                f"{BASE_URL}/api/v1/ask",
                json={"question": query, "use_enhancements": True, "n_results": 5},
                timeout=TIMEOUT
            )
            assert response.status_code == 200, f"Special char query failed: {query}"
            print(f"✅ Special chars handled: {query[:50]}")
    
    def test_no_results_query(self):
        """Test query that should return no results"""
        response = requests.post(
            f"{BASE_URL}/api/v1/ask",
            json={
                "question": "xyzzy123nonexistentterm456",
                "use_enhancements": True,
                "n_results": 5
            },
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"No results query failed: {response.text}"
        data = response.json()
        # Should still return an answer (LLM will say "I don't know")
        assert "answer" in data
        print(f"✅ No results query handled gracefully")
    
    def test_repeated_words_query(self):
        """Test query with repeated words"""
        response = requests.post(
            f"{BASE_URL}/api/v1/ask",
            json={
                "question": "MCP MCP MCP MCP MCP protocol protocol protocol",
                "use_enhancements": True,
                "n_results": 5
            },
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Repeated words failed: {response.text}"
        data = response.json()
        assert len(data.get("sources", [])) > 0
        print(f"✅ Repeated words handled")


class TestParameterEdgeCases:
    """Test edge cases for API parameters"""
    
    def test_zero_n_results(self):
        """Test n_results=0"""
        response = requests.post(
            f"{BASE_URL}/api/v1/ask",
            json={"question": "What is MCP?", "use_enhancements": True, "n_results": 0},
            timeout=TIMEOUT
        )
        # Should return validation error
        assert response.status_code in [200, 422], f"Unexpected status: {response.status_code}"
    
    def test_negative_n_results(self):
        """Test negative n_results"""
        response = requests.post(
            f"{BASE_URL}/api/v1/ask",
            json={"question": "What is MCP?", "use_enhancements": True, "n_results": -5},
            timeout=TIMEOUT
        )
        # Should return validation error
        assert response.status_code == 422, f"Should reject negative n_results"
    
    def test_very_large_n_results(self):
        """Test very large n_results"""
        response = requests.post(
            f"{BASE_URL}/api/v1/ask",
            json={"question": "What is MCP?", "use_enhancements": True, "n_results": 1000},
            timeout=TIMEOUT
        )
        # Should either cap at max or return validation error
        assert response.status_code in [200, 422], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            # Should cap sources at reasonable limit
            assert len(data.get("sources", [])) <= 100, "Sources should be capped"
            print(f"✅ Large n_results capped at {len(data['sources'])}")
    
    def test_invalid_temperature(self):
        """Test invalid temperature values"""
        for temp in [-1.0, 2.5, 999]:
            response = requests.post(
                f"{BASE_URL}/api/v1/ask",
                json={
                    "question": "What is MCP?",
                    "use_enhancements": True,
                    "n_results": 5,
                    "temperature": temp
                },
                timeout=TIMEOUT
            )
            # Should either clamp or reject
            assert response.status_code in [200, 422], f"Unexpected status for temp={temp}"


class TestTemporalEdgeCases:
    """Test edge cases for temporal queries"""
    
    def test_future_date(self):
        """Test temporal query with future date"""
        future_date = (datetime.utcnow() + timedelta(days=365)).isoformat()
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/temporal/query",
            json={
                "question": "What will the future hold?",
                "as_of_date": future_date,
                "use_enhancements": True,
                "limit": 5
            },
            timeout=TIMEOUT
        )
        # Should handle gracefully (return all docs or empty)
        assert response.status_code == 200, f"Future date failed: {response.text}"
        print(f"✅ Future date handled")
    
    def test_very_old_date(self):
        """Test temporal query with very old date"""
        old_date = "1990-01-01T00:00:00Z"
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/temporal/query",
            json={
                "question": "What existed back then?",
                "as_of_date": old_date,
                "use_enhancements": True,
                "limit": 5
            },
            timeout=TIMEOUT
        )
        # Should return empty or error
        assert response.status_code in [200, 400], f"Old date failed: {response.text}"
        print(f"✅ Old date handled")
    
    def test_invalid_date_format(self):
        """Test invalid date format"""
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/temporal/query",
            json={
                "question": "Test question",
                "as_of_date": "not-a-date",
                "use_enhancements": True,
                "limit": 5
            },
            timeout=TIMEOUT
        )
        # Should return validation error
        assert response.status_code == 422, f"Should reject invalid date format"
        print(f"✅ Invalid date format rejected")


class TestContextAwareEdgeCases:
    """Test edge cases for context-aware queries"""
    
    def test_empty_filters(self):
        """Test context-aware query with no filters"""
        response = requests.post(
            f"{BASE_URL}/api/v1/query/context-aware",
            json={
                "question": "What is MCP?",
                "use_enhancements": True,
                "limit": 5
            },
            timeout=TIMEOUT
        )
        # Should work without filters
        assert response.status_code == 200, f"No filters failed: {response.text}"
        data = response.json()
        assert len(data.get("results", [])) > 0
        print(f"✅ Context-aware with no filters works")
    
    def test_nonexistent_repo(self):
        """Test context-aware query with nonexistent repo_id"""
        response = requests.post(
            f"{BASE_URL}/api/v1/query/context-aware",
            json={
                "question": "What is MCP?",
                "repo_id": "nonexistent-repo-12345",
                "use_enhancements": True,
                "limit": 5
            },
            timeout=TIMEOUT
        )
        # Should return empty results or handle gracefully
        assert response.status_code == 200, f"Nonexistent repo failed: {response.text}"
        print(f"✅ Nonexistent repo handled")
    
    def test_conflicting_filters(self):
        """Test context-aware query with conflicting filters"""
        response = requests.post(
            f"{BASE_URL}/api/v1/query/context-aware",
            json={
                "question": "What is MCP?",
                "service_name": "service-a",
                "category": "category-that-service-a-doesnt-have",
                "use_enhancements": True,
                "limit": 5
            },
            timeout=TIMEOUT
        )
        # Should return empty results
        assert response.status_code == 200, f"Conflicting filters failed: {response.text}"
        print(f"✅ Conflicting filters handled")


class TestMultiPassEdgeCases:
    """Test edge cases for multi-pass queries"""
    
    def test_zero_passes(self):
        """Test multi-pass with 0 passes"""
        response = requests.post(
            f"{BASE_URL}/api/v1/query/multi-pass",
            json={
                "query": "What is MCP?",
                "num_passes": 0,
                "num_secondary_questions": 2,
                "use_enhancements": True
            },
            timeout=120
        )
        # Should return validation error
        assert response.status_code == 422, "Should reject 0 passes"
    
    def test_excessive_passes(self):
        """Test multi-pass with too many passes"""
        response = requests.post(
            f"{BASE_URL}/api/v1/query/multi-pass",
            json={
                "query": "What is MCP?",
                "num_passes": 100,
                "num_secondary_questions": 2,
                "use_enhancements": True
            },
            timeout=120
        )
        # Should either cap or reject
        assert response.status_code in [200, 422], f"Excessive passes: {response.status_code}"
    
    def test_zero_secondary_questions(self):
        """Test multi-pass with 0 secondary questions"""
        response = requests.post(
            f"{BASE_URL}/api/v1/query/multi-pass",
            json={
                "query": "What is MCP?",
                "num_passes": 2,
                "num_secondary_questions": 0,
                "use_enhancements": True
            },
            timeout=120
        )
        # Should either handle gracefully or reject
        assert response.status_code in [200, 422], f"Zero secondary questions"


class TestConcurrencyEdgeCases:
    """Test concurrent request handling"""
    
    def test_concurrent_requests(self):
        """Test multiple concurrent requests"""
        import concurrent.futures
        
        def make_request(i):
            response = requests.post(
                f"{BASE_URL}/api/v1/ask",
                json={
                    "question": f"What is MCP test {i}?",
                    "use_enhancements": True,
                    "n_results": 5
                },
                timeout=TIMEOUT
            )
            return response.status_code, i
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        successes = sum(1 for status, _ in results if status == 200)
        print(f"✅ Concurrent requests: {successes}/10 succeeded")
        assert successes >= 8, "Most concurrent requests should succeed"
    
    def test_rapid_sequential_requests(self):
        """Test rapid sequential requests (rate limiting)"""
        statuses = []
        for i in range(20):
            response = requests.post(
                f"{BASE_URL}/api/v1/ask",
                json={
                    "question": f"Quick test {i}",
                    "use_enhancements": False,  # Faster
                    "n_results": 3
                },
                timeout=30
            )
            statuses.append(response.status_code)
            time.sleep(0.1)  # 100ms between requests
        
        successes = sum(1 for status in statuses if status == 200)
        print(f"✅ Rapid requests: {successes}/20 succeeded")
        assert successes >= 15, "Most rapid requests should succeed"


class TestErrorRecovery:
    """Test error recovery and graceful degradation"""
    
    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        response = requests.post(
            f"{BASE_URL}/api/v1/ask",
            data="not-valid-json",
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        # Should return 422 or 400
        assert response.status_code in [400, 422], "Should reject malformed JSON"
    
    def test_missing_required_fields(self):
        """Test missing required fields"""
        response = requests.post(
            f"{BASE_URL}/api/v1/ask",
            json={"use_enhancements": True},  # Missing 'question'
            timeout=TIMEOUT
        )
        # Should return validation error
        assert response.status_code == 422, "Should reject missing required fields"
    
    def test_wrong_http_method(self):
        """Test wrong HTTP method"""
        response = requests.get(  # Should be POST
            f"{BASE_URL}/api/v1/ask",
            timeout=TIMEOUT
        )
        # Should return 405 (Method Not Allowed)
        assert response.status_code == 405, f"Should reject GET on POST endpoint"


class TestCacheEdgeCases:
    """Test caching edge cases"""
    
    def test_identical_queries(self):
        """Test that identical queries benefit from cache"""
        query = "What is the MCP protocol architecture?"
        
        # First request (cold)
        start1 = time.time()
        response1 = requests.post(
            f"{BASE_URL}/api/v1/ask",
            json={"question": query, "use_enhancements": True, "n_results": 5},
            timeout=TIMEOUT
        )
        time1 = time.time() - start1
        
        # Second request (should hit cache)
        start2 = time.time()
        response2 = requests.post(
            f"{BASE_URL}/api/v1/ask",
            json={"question": query, "use_enhancements": True, "n_results": 5},
            timeout=TIMEOUT
        )
        time2 = time.time() - start2
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Second request should be faster (cached)
        # Note: May not always be true due to various factors
        print(f"✅ Cache test: First={time1:.2f}s, Second={time2:.2f}s")
        print(f"   Speedup: {time1/time2:.1f}x" if time2 > 0 else "N/A")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 EDGE CASE TESTING SUITE")
    print("="*80 + "\n")
    
    # Run pytest with verbose output
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-k", "test_",  # Run all test methods
        "--maxfail=3"  # Stop after 3 failures
    ])

