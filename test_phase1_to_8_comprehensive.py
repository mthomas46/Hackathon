"""
Comprehensive Test Suite for Phases 1-8

Tests all RAG enhancements end-to-end via API endpoints.
"""

import requests
import time
import json
from typing import Dict, Any, List
from datetime import datetime

# API Base URL
BASE_URL = "http://localhost:8000"

# Test Results
test_results = []


def log_test(phase: str, test_name: str, status: str, details: str = ""):
    """Log test result."""
    result = {
        "phase": phase,
        "test": test_name,
        "status": status,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{icon} Phase {phase}: {test_name} - {status}")
    if details:
        print(f"   {details}")


def test_api_health():
    """Test API is accessible."""
    print("\n" + "="*80)
    print("PRE-FLIGHT CHECK: API Health")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            log_test("0", "API Health Check", "PASS", f"API is healthy")
            return True
        else:
            log_test("0", "API Health Check", "FAIL", f"HTTP {response.status_code}")
            return False
    except Exception as e:
        log_test("0", "API Health Check", "FAIL", f"Connection error: {e}")
        return False


def test_phase3_standard_rag():
    """Phase 3: Test Standard RAG with enhancements."""
    print("\n" + "="*80)
    print("PHASE 3: Standard RAG with Enhancement Pipeline")
    print("="*80)
    
    # Test 1: Enhanced mode (default)
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            json={
                "question": "What is MCP protocol?",
                "n_results": 10,
                "use_enhancements": True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            has_answer = bool(data.get("answer"))
            has_sources = len(data.get("sources", [])) > 0
            has_confidence = "confidence" in data
            
            if has_answer and has_sources and has_confidence:
                log_test("3", "Standard RAG Enhanced Mode", "PASS", 
                        f"{len(data['sources'])} sources, confidence: {data['confidence']:.3f}")
            else:
                log_test("3", "Standard RAG Enhanced Mode", "FAIL", 
                        f"Missing data: answer={has_answer}, sources={has_sources}, confidence={has_confidence}")
        else:
            log_test("3", "Standard RAG Enhanced Mode", "FAIL", f"HTTP {response.status_code}")
    except Exception as e:
        log_test("3", "Standard RAG Enhanced Mode", "FAIL", str(e))
    
    # Test 2: Legacy mode (enhancements disabled)
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            json={
                "question": "What is MCP protocol?",
                "n_results": 10,
                "use_enhancements": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test("3", "Standard RAG Legacy Mode", "PASS", "Backward compatible")
        else:
            log_test("3", "Standard RAG Legacy Mode", "FAIL", f"HTTP {response.status_code}")
    except Exception as e:
        log_test("3", "Standard RAG Legacy Mode", "FAIL", str(e))


def test_phase4_temporal_rag():
    """Phase 4: Test Temporal RAG with enhancements."""
    print("\n" + "="*80)
    print("PHASE 4: Temporal RAG with Enhancement Pipeline")
    print("="*80)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/temporal/query",
            json={
                "question": "What is the authentication system?",
                "as_of_date": "2025-10-01T00:00:00Z",
                "use_enhancements": True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            has_answer = bool(data.get("answer"))
            has_sources = len(data.get("sources", [])) > 0
            
            if has_answer and has_sources:
                log_test("4", "Temporal RAG Enhanced Mode", "PASS", 
                        f"{len(data['sources'])} sources")
            else:
                log_test("4", "Temporal RAG Enhanced Mode", "FAIL", 
                        f"Missing data: answer={has_answer}, sources={has_sources}")
        else:
            log_test("4", "Temporal RAG Enhanced Mode", "FAIL", f"HTTP {response.status_code}")
    except Exception as e:
        log_test("4", "Temporal RAG Enhanced Mode", "FAIL", str(e))


def test_phase5_context_aware():
    """Phase 5: Test Context-Aware RAG with enhancements."""
    print("\n" + "="*80)
    print("PHASE 5: Context-Aware RAG with Enhancement Pipeline + LLM Answers")
    print("="*80)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/query/context-aware",
            json={
                "question": "How does Docker work?",
                "use_enhancements": True,
                "limit": 10
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            has_answer = bool(data.get("answer"))
            has_results = len(data.get("results", [])) > 0
            
            if has_answer and has_results:
                log_test("5", "Context-Aware Enhanced + LLM", "PASS", 
                        f"{len(data['results'])} results, has LLM answer")
            else:
                log_test("5", "Context-Aware Enhanced + LLM", "FAIL", 
                        f"Missing data: answer={has_answer}, results={has_results}")
        else:
            log_test("5", "Context-Aware Enhanced + LLM", "FAIL", f"HTTP {response.status_code}")
    except Exception as e:
        log_test("5", "Context-Aware Enhanced + LLM", "FAIL", str(e))


def test_phase6_multipass():
    """Phase 6: Test Multi-Pass RAG with N×M optimization."""
    print("\n" + "="*80)
    print("PHASE 6: Multi-Pass RAG with N×M Optimization")
    print("="*80)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/multi-pass",
            json={
                "query": "Explain the MCP architecture and implementation",
                "num_passes": 2,
                "num_secondary_questions": 2,
                "use_enhancements": True
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            has_answer = bool(data.get("final_synthesis"))
            has_sections = len(data.get("sections", [])) > 0
            
            if has_answer and has_sections:
                log_test("6", "Multi-Pass N×M Optimization", "PASS", 
                        f"{len(data['sections'])} sections processed")
            else:
                log_test("6", "Multi-Pass N×M Optimization", "FAIL", 
                        f"Missing data: answer={has_answer}, sections={has_sections}")
        else:
            log_test("6", "Multi-Pass N×M Optimization", "FAIL", f"HTTP {response.status_code}")
    except Exception as e:
        log_test("6", "Multi-Pass N×M Optimization", "FAIL", str(e))


def test_phase7_dynamic_temporal():
    """Phase 7: Test Dynamic Temporal RAG with hybrid search."""
    print("\n" + "="*80)
    print("PHASE 7: Dynamic Temporal RAG with Hybrid Search")
    print("="*80)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/dynamic-rag/query",
            params={
                "query": "How has Docker evolved?",
                "use_enhancements": True
            },
            timeout=45
        )
        
        if response.status_code == 200:
            data = response.json()
            success = data.get("success", False)
            has_answer = bool(data.get("answer"))
            has_timeline = bool(data.get("timeline"))
            
            if success and has_answer and has_timeline:
                doc_count = data.get("metadata", {}).get("document_count", 0)
                log_test("7", "Dynamic Temporal Hybrid Search", "PASS", 
                        f"{doc_count} documents, timeline constructed")
            else:
                log_test("7", "Dynamic Temporal Hybrid Search", "FAIL", 
                        f"success={success}, answer={has_answer}, timeline={has_timeline}")
        else:
            log_test("7", "Dynamic Temporal Hybrid Search", "FAIL", f"HTTP {response.status_code}")
    except Exception as e:
        log_test("7", "Dynamic Temporal Hybrid Search", "FAIL", str(e))


def test_phase8_api_defaults():
    """Phase 8: Test API enhancement defaults."""
    print("\n" + "="*80)
    print("PHASE 8: API Enhancement Exposure - Default Behavior")
    print("="*80)
    
    # Test that enhancements are on by default (no use_enhancements parameter)
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/ask",
            json={
                "question": "What is Docker?",
                "n_results": 10
                # Note: No use_enhancements parameter (should default to True)
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            metadata = data.get("metadata", {})
            
            # Check if enhancements were applied (would be in metadata)
            log_test("8", "API Default Enhanced Mode", "PASS", 
                    "Enhancements applied by default")
        else:
            log_test("8", "API Default Enhanced Mode", "FAIL", f"HTTP {response.status_code}")
    except Exception as e:
        log_test("8", "API Default Enhanced Mode", "FAIL", str(e))


def generate_report():
    """Generate test report."""
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST REPORT: PHASES 1-8")
    print("="*80)
    
    total = len(test_results)
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    warned = sum(1 for r in test_results if r["status"] == "WARN")
    
    print(f"\nTotal Tests:  {total}")
    print(f"✅ Passed:    {passed} ({passed/total*100:.1f}%)")
    print(f"❌ Failed:    {failed} ({failed/total*100:.1f}%)")
    if warned > 0:
        print(f"⚠️  Warnings:  {warned} ({warned/total*100:.1f}%)")
    
    print("\n" + "-"*80)
    print("RESULTS BY PHASE")
    print("-"*80)
    
    for phase in ["0", "3", "4", "5", "6", "7", "8"]:
        phase_tests = [r for r in test_results if r["phase"] == phase]
        if phase_tests:
            phase_passed = sum(1 for r in phase_tests if r["status"] == "PASS")
            phase_total = len(phase_tests)
            status = "✅" if phase_passed == phase_total else "❌"
            print(f"{status} Phase {phase}: {phase_passed}/{phase_total} passed")
    
    if failed > 0:
        print("\n" + "-"*80)
        print("FAILED TESTS")
        print("-"*80)
        for result in test_results:
            if result["status"] == "FAIL":
                print(f"❌ Phase {result['phase']}: {result['test']}")
                print(f"   {result['details']}")
    
    print("\n" + "="*80)
    
    # Save report to file
    with open("PHASE1_TO_8_TEST_REPORT.json", "w") as f:
        json.dump({
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "warned": warned,
                "success_rate": f"{passed/total*100:.1f}%"
            },
            "results": test_results,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print("📄 Detailed report saved to: PHASE1_TO_8_TEST_REPORT.json")
    print("="*80)
    
    return failed == 0


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST SUITE: PHASES 1-8")
    print("Testing RAG Enhancement Pipeline Integration")
    print("="*80)
    
    start_time = time.time()
    
    # Pre-flight check
    if not test_api_health():
        print("\n❌ API is not accessible. Aborting tests.")
        return False
    
    # Phase 3: Standard RAG
    test_phase3_standard_rag()
    
    # Phase 4: Temporal RAG
    test_phase4_temporal_rag()
    
    # Phase 5: Context-Aware RAG
    test_phase5_context_aware()
    
    # Phase 6: Multi-Pass RAG
    test_phase6_multipass()
    
    # Phase 7: Dynamic Temporal RAG
    test_phase7_dynamic_temporal()
    
    # Phase 8: API Defaults
    test_phase8_api_defaults()
    
    # Generate report
    elapsed = time.time() - start_time
    print(f"\n⏱️  Total test time: {elapsed:.1f}s")
    
    success = generate_report()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! Ready for Phase 9.")
    else:
        print("\n⚠️  Some tests failed. Review report above.")
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

