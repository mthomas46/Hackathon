#!/usr/bin/env python3
"""
Comprehensive RAG Validation Suite
Tests ALL RAG query types with all enhancements.
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000"

# Test query for all RAG types
TEST_QUERY = "How to configure Docker networking and security?"

class RAGValidator:
    def __init__(self):
        self.results = {}
        self.test_start = datetime.now()
    
    def test_standard_rag(self) -> Dict[str, Any]:
        """Test standard RAG (no enhancements)."""
        print("\n" + "="*80)
        print("1. STANDARD RAG (Baseline)")
        print("="*80)
        
        start = time.time()
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/rag/ask/standard",
                json={
                    "question": TEST_QUERY,
                    "n_results": 10
                },
                timeout=30
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Standard RAG: {elapsed:.2f}s")
                print(f"   Sources: {len(data.get('sources', []))}")
                print(f"   Answer: {len(data.get('answer', ''))} chars")
                return {"success": True, "time": elapsed, "data": data}
            else:
                print(f"❌ Standard RAG: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}", "time": elapsed}
        except Exception as e:
            print(f"❌ Standard RAG: {str(e)[:100]}")
            return {"success": False, "error": str(e), "time": time.time() - start}
    
    def test_enhanced_rag_phase1(self) -> Dict[str, Any]:
        """Test enhanced RAG with Phase 1 only."""
        print("\n" + "="*80)
        print("2. ENHANCED RAG - Phase 1 (Hybrid + Query Rewrite + Confidence)")
        print("="*80)
        
        start = time.time()
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/rag/ask/enhanced",
                json={
                    "question": TEST_QUERY,
                    "n_results": 10,
                    "enable_hybrid_search": True,
                    "enable_query_rewriting": True,
                    "enable_confidence_scoring": True,
                    "semantic_weight": 0.7,
                    "keyword_weight": 0.3
                },
                timeout=35
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Enhanced Phase 1: {elapsed:.2f}s")
                print(f"   Sources: {len(data.get('sources', []))}")
                print(f"   Confidence: {data.get('confidence_score', 'N/A')}")
                print(f"   Query variants: {data.get('query_variants_used', 0)}")
                return {"success": True, "time": elapsed, "data": data}
            else:
                print(f"❌ Enhanced Phase 1: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}", "time": elapsed}
        except Exception as e:
            print(f"❌ Enhanced Phase 1: {str(e)[:100]}")
            return {"success": False, "error": str(e), "time": time.time() - start}
    
    def test_enhanced_rag_phase1_2(self) -> Dict[str, Any]:
        """Test enhanced RAG with Phase 1+2 (all optimizations)."""
        print("\n" + "="*80)
        print("3. ENHANCED RAG - Phase 1+2 (All Optimizations)")
        print("="*80)
        
        start = time.time()
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/rag/ask/enhanced",
                json={
                    "question": TEST_QUERY,
                    "n_results": 10,
                    # Phase 1
                    "enable_hybrid_search": True,
                    "enable_query_rewriting": True,
                    "enable_confidence_scoring": True,
                    "semantic_weight": 0.7,
                    "keyword_weight": 0.3,
                    # Phase 2
                    "enable_reranking": True,
                    "enable_context_optimization": True,
                    "context_strategy": "balanced",
                    # Phase 5R & 7R
                    "enable_intent_classification": True,
                    "enable_difficulty_estimation": True
                },
                timeout=40
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Enhanced Phase 1+2: {elapsed:.2f}s")
                print(f"   Sources: {len(data.get('sources', []))}")
                print(f"   Confidence: {data.get('confidence_score', 'N/A')}")
                print(f"   Intent: {data.get('intent', {}).get('intent_type', 'N/A')}")
                print(f"   Difficulty: {data.get('difficulty', {}).get('difficulty_level', 'N/A')}")
                return {"success": True, "time": elapsed, "data": data}
            else:
                print(f"❌ Enhanced Phase 1+2: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}", "time": elapsed}
        except Exception as e:
            print(f"❌ Enhanced Phase 1+2: {str(e)[:100]}")
            return {"success": False, "error": str(e), "time": time.time() - start}
    
    def test_temporal_rag(self) -> Dict[str, Any]:
        """Test temporal RAG (timeline-based)."""
        print("\n" + "="*80)
        print("4. TEMPORAL RAG (Timeline-based)")
        print("="*80)
        
        start = time.time()
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/temporal/query",
                json={
                    "query": TEST_QUERY,
                    "n_results": 10,
                    "time_weight": 0.3
                },
                timeout=35
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Temporal RAG: {elapsed:.2f}s")
                print(f"   Sources: {len(data.get('sources', []))}")
                print(f"   Temporal context: {'Yes' if data.get('temporal_context') else 'No'}")
                return {"success": True, "time": elapsed, "data": data}
            else:
                print(f"❌ Temporal RAG: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}", "time": elapsed}
        except Exception as e:
            print(f"❌ Temporal RAG: {str(e)[:100]}")
            return {"success": False, "error": str(e), "time": time.time() - start}
    
    def test_contextual_query(self) -> Dict[str, Any]:
        """Test contextual query (simple context + LLM)."""
        print("\n" + "="*80)
        print("5. CONTEXTUAL QUERY (Simple context + LLM)")
        print("="*80)
        
        start = time.time()
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/query/enhanced",
                json={
                    "question": TEST_QUERY,
                    "mode": "contextual",
                    "n_results": 10
                },
                timeout=30
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Contextual Query: {elapsed:.2f}s")
                print(f"   Sources: {len(data.get('sources', []))}")
                print(f"   Mode: {data.get('metadata', {}).get('mode', 'N/A')}")
                return {"success": True, "time": elapsed, "data": data}
            else:
                print(f"❌ Contextual Query: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}", "time": elapsed}
        except Exception as e:
            print(f"❌ Contextual Query: {str(e)[:100]}")
            return {"success": False, "error": str(e), "time": time.time() - start}
    
    def test_multipass_rag(self) -> Dict[str, Any]:
        """Test multi-pass RAG (iterative refinement)."""
        print("\n" + "="*80)
        print("6. MULTI-PASS RAG (Iterative refinement)")
        print("="*80)
        
        start = time.time()
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/query/multi-pass",
                json={
                    "query": TEST_QUERY,
                    "max_passes": 2,
                    "n_results": 10
                },
                timeout=60
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Multi-pass RAG: {elapsed:.2f}s")
                print(f"   Passes completed: {data.get('passes_completed', 0)}")
                print(f"   Sources: {len(data.get('sources', []))}")
                return {"success": True, "time": elapsed, "data": data}
            else:
                print(f"❌ Multi-pass RAG: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}", "time": elapsed}
        except Exception as e:
            print(f"❌ Multi-pass RAG: {str(e)[:100]}")
            return {"success": False, "error": str(e), "time": time.time() - start}
    
    def test_context_aware_query(self) -> Dict[str, Any]:
        """Test context-aware query with directory tree filtering."""
        print("\n" + "="*80)
        print("7. CONTEXT-AWARE QUERY (With directory tree filtering)")
        print("="*80)
        
        start = time.time()
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/query/context-aware",
                json={
                    "query": TEST_QUERY,
                    "include_paths": ["docker", "docs"],
                    "n_results": 10
                },
                timeout=35
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Context-aware Query: {elapsed:.2f}s")
                print(f"   Sources: {len(data.get('sources', []))}")
                print(f"   Context filters: {data.get('context_info', {}).get('filters_applied', 'N/A')}")
                return {"success": True, "time": elapsed, "data": data}
            else:
                print(f"❌ Context-aware Query: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}", "time": elapsed}
        except Exception as e:
            print(f"❌ Context-aware Query: {str(e)[:100]}")
            return {"success": False, "error": str(e), "time": time.time() - start}
    
    def test_dynamic_temporal_rag(self) -> Dict[str, Any]:
        """Test dynamic temporal RAG."""
        print("\n" + "="*80)
        print("8. DYNAMIC TEMPORAL RAG (Auto timeline construction)")
        print("="*80)
        
        start = time.time()
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/dynamic-rag/query?query={TEST_QUERY}&use_cache=true",
                timeout=40
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Dynamic Temporal RAG: {elapsed:.2f}s")
                print(f"   Timeline events: {len(data.get('timeline', {}).get('events', []))}")
                print(f"   Success: {data.get('success', False)}")
                return {"success": True, "time": elapsed, "data": data}
            else:
                print(f"❌ Dynamic Temporal RAG: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}", "time": elapsed}
        except Exception as e:
            print(f"❌ Dynamic Temporal RAG: {str(e)[:100]}")
            return {"success": False, "error": str(e), "time": time.time() - start}
    
    def run_all_tests(self):
        """Run all RAG validation tests."""
        print("\n" + "╔" + "="*78 + "╗")
        print("║" + " "*28 + "RAG VALIDATION SUITE" + " "*29 + "║")
        print("╚" + "="*78 + "╝")
        print(f"\nTest Query: '{TEST_QUERY}'")
        print(f"Start Time: {self.test_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Run all tests
        self.results["standard"] = self.test_standard_rag()
        time.sleep(1)
        
        self.results["enhanced_phase1"] = self.test_enhanced_rag_phase1()
        time.sleep(1)
        
        self.results["enhanced_phase1_2"] = self.test_enhanced_rag_phase1_2()
        time.sleep(1)
        
        self.results["temporal"] = self.test_temporal_rag()
        time.sleep(1)
        
        self.results["contextual"] = self.test_contextual_query()
        time.sleep(1)
        
        self.results["multipass"] = self.test_multipass_rag()
        time.sleep(1)
        
        self.results["context_aware"] = self.test_context_aware_query()
        time.sleep(1)
        
        self.results["dynamic_temporal"] = self.test_dynamic_temporal_rag()
        
        # Generate summary
        self.print_summary()
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        
        successful = sum(1 for r in self.results.values() if r.get("success", False))
        total = len(self.results)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {total - successful}")
        print(f"Success Rate: {success_rate:.1f}%\n")
        
        print("Detailed Results:")
        print("-" * 80)
        
        for name, result in self.results.items():
            status = "✅" if result.get("success") else "❌"
            time_str = f"{result.get('time', 0):.2f}s" if result.get("success") else "Failed"
            error = result.get("error", "")
            
            print(f"{status} {name:25} {time_str:>10}  {error[:30]}")
        
        print("\n" + "="*80)
        
        if success_rate == 100:
            print("🎉 ALL RAG TYPES VALIDATED SUCCESSFULLY!")
        elif success_rate >= 75:
            print("⚠️  MOST RAG TYPES WORKING (some issues)")
        else:
            print("❌ SIGNIFICANT ISSUES DETECTED")
        
        print("="*80 + "\n")
        
        # Time summary
        successful_times = [r["time"] for r in self.results.values() if r.get("success")]
        if successful_times:
            avg_time = sum(successful_times) / len(successful_times)
            print(f"Average Response Time: {avg_time:.2f}s")
            print(f"Fastest: {min(successful_times):.2f}s")
            print(f"Slowest: {max(successful_times):.2f}s\n")


if __name__ == "__main__":
    # Check service health
    print("Checking service health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Service is not healthy!")
            exit(1)
        print("✅ Service is healthy\n")
    except Exception as e:
        print(f"❌ Cannot connect to service: {e}")
        exit(1)
    
    # Run validation
    validator = RAGValidator()
    validator.run_all_tests()

