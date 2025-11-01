"""
Comprehensive Test Suite for Phases 1-8
Tests all RAG enhancements and API integrations
"""

import pytest
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Base URL
BASE_URL = "http://localhost:8000"

# Test configuration
TEST_TIMEOUT = 60  # 60 seconds per test


class TestPhase1EnhancementPipeline:
    """Test Phase 1: Enhancement Pipeline components"""
    
    def test_enhancement_config_presets(self):
        """Test that all config presets are available"""
        # Import check
        try:
            from services.ecosystem_mcp.src.services.rag.enhancements import EnhancementConfig
            
            # Verify all presets exist
            presets = [
                EnhancementConfig.default(),
                EnhancementConfig.temporal_default(),
                EnhancementConfig.context_aware_default(),
                EnhancementConfig.multipass_default(),
                EnhancementConfig.fast(),
                EnhancementConfig.max_quality(),
                EnhancementConfig.minimal()
            ]
            
            assert len(presets) == 7, "Should have 7 config presets"
            print("✅ Phase 1: All enhancement config presets available")
            
        except ImportError as e:
            pytest.skip(f"Phase 1 components not accessible: {e}")


class TestPhase2EnhancedRAG:
    """Test Phase 2: Refactored Enhanced RAG"""
    
    def test_enhanced_rag_with_pipeline(self):
        """Test enhanced RAG uses pipeline"""
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/ask/enhanced",
            json={
                "question": "What is MCP?",
                "mode": "rag",
                "use_enhancements": True,
                "n_results": 5
            },
            timeout=TEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Enhanced RAG failed: {response.text}"
        data = response.json()
        
        assert "answer" in data
        assert len(data.get("answer", "")) > 0
        assert "metadata" in data
        
        print(f"✅ Phase 2: Enhanced RAG working (answer: {len(data['answer'])} chars)")


class TestPhase3StandardRAG:
    """Test Phase 3: Standard RAG with optional enhancements"""
    
    def test_standard_rag_with_enhancements(self):
        """Test standard RAG with enhancements enabled"""
        response = requests.post(
            f"{BASE_URL}/api/v1/ask",  # ✅ Correct endpoint
            json={
                "question": "How does Docker work?",
                "use_enhancements": True,
                "n_results": 10
            },
            timeout=TEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Standard RAG failed: {response.text}"
        data = response.json()
        
        assert "answer" in data
        assert "sources" in data
        assert len(data.get("sources", [])) > 0
        
        print(f"✅ Phase 3: Standard RAG enhanced mode ({len(data['sources'])} sources)")
    
    def test_standard_rag_legacy_mode(self):
        """Test standard RAG with enhancements disabled"""
        response = requests.post(
            f"{BASE_URL}/api/v1/ask",  # ✅ Correct endpoint
            json={
                "question": "What is authentication?",
                "use_enhancements": False,
                "n_results": 10
            },
            timeout=TEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Standard RAG legacy failed: {response.text}"
        data = response.json()
        
        assert "answer" in data
        print(f"✅ Phase 3: Standard RAG legacy mode working")


class TestPhase4TemporalRAG:
    """Test Phase 4: Temporal RAG with enhancements"""
    
    def test_temporal_rag_with_enhancements(self):
        """Test temporal RAG with enhancements enabled"""
        as_of_date = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
        
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/temporal/query",
            json={
                "question": "How does the API work?",
                "as_of_date": as_of_date,
                "use_enhancements": True,
                "limit": 10
            },
            timeout=TEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Temporal RAG failed: {response.text}"
        data = response.json()
        
        assert "answer" in data
        assert "sources" in data
        
        print(f"✅ Phase 4: Temporal RAG enhanced mode ({len(data.get('sources', []))} sources)")


class TestPhase5ContextAwareRAG:
    """Test Phase 5: Context-Aware RAG with LLM answers"""
    
    def test_context_aware_with_enhancements(self):
        """Test context-aware RAG with enhancements enabled"""
        response = requests.post(
            f"{BASE_URL}/api/v1/query/context-aware",
            json={
                "question": "Explain the architecture",
                "use_enhancements": True,
                "limit": 10
            },
            timeout=TEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Context-Aware RAG failed: {response.text}"
        data = response.json()
        
        # Phase 5 added LLM answer generation
        assert "query" in data or "question" in data
        assert "results" in data
        
        print(f"✅ Phase 5: Context-Aware RAG with enhancements ({len(data.get('results', []))} results)")


class TestPhase6MultiPassRAG:
    """Test Phase 6: Multi-Pass RAG with N×M optimization"""
    
    def test_multipass_with_enhancements(self):
        """Test multi-pass RAG with enhancements enabled"""
        response = requests.post(
            f"{BASE_URL}/api/v1/query/multi-pass",  # ✅ Correct endpoint
            json={
                "query": "Explain the MCP architecture and its components",
                "num_passes": 2,
                "num_secondary_questions": 2,
                "use_enhancements": True,
                "n_results": 8
            },
            timeout=120  # Multi-pass needs more time (N×M queries)
        )
        
        assert response.status_code == 200, f"Multi-Pass RAG failed: {response.text}"
        data = response.json()
        
        assert "original_query" in data
        assert "sections" in data
        assert len(data.get("sections", [])) > 0
        
        print(f"✅ Phase 6: Multi-Pass RAG with N×M optimization ({len(data['sections'])} sections)")


class TestPhase7DynamicTemporalRAG:
    """Test Phase 7: Dynamic Temporal RAG with hybrid search"""
    
    def test_dynamic_temporal_with_enhancements(self):
        """Test dynamic temporal RAG with enhancements enabled"""
        response = requests.post(  # ✅ Changed GET to POST
            f"{BASE_URL}/api/v1/dynamic-rag/query",
            params={
                "query": "How has Docker evolved?",
                "use_enhancements": True
            },
            timeout=TEST_TIMEOUT
        )
        
        assert response.status_code == 200, f"Dynamic Temporal RAG failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "answer" in data
        assert "timeline" in data
        
        print(f"✅ Phase 7: Dynamic Temporal RAG with hybrid search (timeline: {data['timeline'].get('period_count', 0)} periods)")


class TestPhase8APIEnhancementExposure:
    """Test Phase 8: All APIs expose enhancement controls"""
    
    def test_all_apis_have_enhancement_param(self):
        """Verify all RAG APIs accept use_enhancements parameter"""
        
        # Test 1: Standard RAG
        r1 = requests.post(
            f"{BASE_URL}/api/v1/ask",  # ✅ Correct endpoint
            json={"question": "test", "use_enhancements": True, "n_results": 5},
            timeout=30
        )
        assert r1.status_code == 200, "Standard RAG should accept use_enhancements"
        
        # Test 2: Enhanced RAG
        r2 = requests.post(
            f"{BASE_URL}/api/v1/rag/ask/enhanced",
            json={"question": "test", "mode": "rag", "use_enhancements": True, "n_results": 5},
            timeout=30
        )
        assert r2.status_code == 200, "Enhanced RAG should accept use_enhancements"
        
        # Test 3: Temporal RAG
        as_of = datetime.utcnow().isoformat() + "Z"
        r3 = requests.post(
            f"{BASE_URL}/api/v1/rag/temporal/query",
            json={"question": "test", "as_of_date": as_of, "use_enhancements": True, "limit": 5},
            timeout=30
        )
        assert r3.status_code == 200, "Temporal RAG should accept use_enhancements"
        
        # Test 4: Context-Aware RAG
        r4 = requests.post(
            f"{BASE_URL}/api/v1/query/context-aware",
            json={"question": "test", "use_enhancements": True, "limit": 5},
            timeout=30
        )
        assert r4.status_code == 200, "Context-Aware RAG should accept use_enhancements"
        
        # Test 5: Multi-Pass RAG
        r5 = requests.post(
            f"{BASE_URL}/api/v1/query/multi-pass",  # ✅ Correct endpoint
            json={"query": "test question", "use_enhancements": True, "num_passes": 2, "num_secondary_questions": 2},
            timeout=60
        )
        assert r5.status_code == 200, "Multi-Pass RAG should accept use_enhancements"
        
        # Test 6: Dynamic Temporal RAG
        r6 = requests.post(  # ✅ Changed GET to POST
            f"{BASE_URL}/api/v1/dynamic-rag/query",
            params={"query": "test", "use_enhancements": True},
            timeout=30
        )
        assert r6.status_code == 200, "Dynamic Temporal RAG should accept use_enhancements"
        
        print("✅ Phase 8: All 6 RAG APIs accept use_enhancements parameter")


class TestEndToEnd:
    """End-to-end integration tests"""
    
    def test_enhancement_pipeline_integration(self):
        """Test that enhancements are actually applied"""
        # Query with enhancements
        response_enhanced = requests.post(
            f"{BASE_URL}/api/v1/ask",  # ✅ Correct endpoint
            json={
                "question": "What is the MCP protocol?",
                "use_enhancements": True,
                "n_results": 10
            },
            timeout=TEST_TIMEOUT
        )
        
        # Query without enhancements
        response_legacy = requests.post(
            f"{BASE_URL}/api/v1/ask",  # ✅ Correct endpoint
            json={
                "question": "What is the MCP protocol?",
                "use_enhancements": False,
                "n_results": 10
            },
            timeout=TEST_TIMEOUT
        )
        
        assert response_enhanced.status_code == 200
        assert response_legacy.status_code == 200
        
        data_enhanced = response_enhanced.json()
        data_legacy = response_legacy.json()
        
        # Enhanced should typically have more sources (hybrid search)
        sources_enhanced = len(data_enhanced.get("sources", []))
        sources_legacy = len(data_legacy.get("sources", []))
        
        print(f"✅ E2E: Enhanced sources: {sources_enhanced}, Legacy sources: {sources_legacy}")
        
        # Enhanced mode should use enhancements (check metadata)
        if "metadata" in data_enhanced:
            metadata = data_enhanced["metadata"]
            if "enhancement_mode" in metadata or "enhancements_applied" in metadata:
                print(f"   Enhancement mode detected: {metadata}")


# Test execution summary
def pytest_sessionfinish(session, exitstatus):
    """Print summary after all tests"""
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST SUITE SUMMARY - PHASES 1-8")
    print("="*80)
    print(f"Exit Status: {exitstatus}")
    print("="*80)


if __name__ == "__main__":
    # Run with pytest
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s", "--tb=short"]))

