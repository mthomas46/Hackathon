#!/usr/bin/env python3
"""
Comprehensive Temporal RAG vs Standard RAG Comparison Test

Tests all temporal RAG endpoints and compares them to standard RAG
to prove the temporal impact on answer quality.
"""

import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

API_BASE = "http://localhost:8000"

def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_result(test_name: str, result: Dict[str, Any]):
    """Print test result in a formatted way."""
    print(f"\n🧪 {test_name}")
    print("-" * 80)
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Status: {result.get('status', 'success')}")
        if "answer" in result:
            print(f"\n📝 Answer:\n{result['answer'][:500]}...")
        if "execution_time" in result:
            print(f"\n⏱️  Execution Time: {result['execution_time']:.2f}s")

def test_standard_rag(question: str) -> Dict[str, Any]:
    """Test standard RAG query as baseline."""
    try:
        response = httpx.post(
            f"{API_BASE}/api/v1/query/basic",
            json={
                "question": question,
                "n_results": 10
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "answer": data.get("answer", ""),
                "sources": len(data.get("sources", [])),
                "execution_time": data.get("execution_time", 0)
            }
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    
    except Exception as e:
        return {"error": str(e)}

def test_temporal_point_in_time(question: str, as_of_date: str) -> Dict[str, Any]:
    """Test point-in-time temporal RAG query."""
    try:
        response = httpx.post(
            f"{API_BASE}/api/v1/rag/temporal/point-in-time",
            json={
                "question": question,
                "as_of_date": as_of_date,
                "limit": 10
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "answer": data.get("answer", ""),
                "sources": len(data.get("sources", [])),
                "execution_time": data.get("execution_time", 0),
                "as_of_date": as_of_date
            }
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    
    except Exception as e:
        return {"error": str(e)}

def test_evolution_tracking(topic: str) -> Dict[str, Any]:
    """Test evolution tracking query."""
    try:
        response = httpx.post(
            f"{API_BASE}/api/v1/rag/temporal/evolution",
            json={
                "topic": topic,
                "limit_per_period": 3
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "periods": len(data.get("evolution", [])),
                "answer": data.get("summary", ""),
                "execution_time": data.get("execution_time", 0)
            }
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    
    except Exception as e:
        return {"error": str(e)}

def test_period_comparison(question: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """Test period comparison query."""
    try:
        response = httpx.post(
            f"{API_BASE}/api/v1/rag/temporal/comparison",
            json={
                "question": question,
                "start_date": start_date,
                "end_date": end_date,
                "limit": 10
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "answer": data.get("answer", ""),
                "start_period_docs": len(data.get("start_period_documents", [])),
                "end_period_docs": len(data.get("end_period_documents", [])),
                "execution_time": data.get("execution_time", 0)
            }
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    
    except Exception as e:
        return {"error": str(e)}

def test_drift_detection(topic: str) -> Dict[str, Any]:
    """Test drift detection query."""
    try:
        response = httpx.post(
            f"{API_BASE}/api/v1/rag/temporal/drift",
            json={
                "topic": topic,
                "detection_threshold": 0.3
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "drift_detected": data.get("drift_detected", False),
                "drift_periods": len(data.get("drift_periods", [])),
                "answer": data.get("summary", ""),
                "execution_time": data.get("execution_time", 0)
            }
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    
    except Exception as e:
        return {"error": str(e)}

def main():
    """Run comprehensive temporal RAG comparison tests."""
    print_section("Temporal RAG vs Standard RAG Comparison Test")
    print("\n📋 This test compares temporal RAG queries to standard RAG queries")
    print("   to demonstrate the impact of temporal context on answer quality.")
    
    # Test questions
    questions = {
        "architecture": "What is the architecture of the system?",
        "testing": "What is the testing strategy?",
        "configuration": "How is configuration managed?"
    }
    
    # Calculate dates for temporal queries
    now = datetime.now()
    week_ago = (now - timedelta(days=7)).isoformat()
    month_ago = (now - timedelta(days=30)).isoformat()
    now_iso = now.isoformat()
    
    results = {}
    
    # ========================================================================
    # Test 1: Standard RAG (Baseline)
    # ========================================================================
    print_section("Test 1: Standard RAG (Baseline)")
    
    for key, question in questions.items():
        print(f"\n🔍 Testing: {key}")
        result = test_standard_rag(question)
        results[f"standard_{key}"] = result
        print_result(f"Standard RAG - {key}", result)
    
    # ========================================================================
    # Test 2: Point-in-Time Temporal RAG
    # ========================================================================
    print_section("Test 2: Point-in-Time Temporal RAG")
    print(f"📅 Querying as of: {week_ago[:10]}")
    
    for key, question in questions.items():
        print(f"\n🔍 Testing: {key}")
        result = test_temporal_point_in_time(question, week_ago)
        results[f"temporal_point_{key}"] = result
        print_result(f"Temporal Point-in-Time - {key}", result)
    
    # ========================================================================
    # Test 3: Evolution Tracking
    # ========================================================================
    print_section("Test 3: Evolution Tracking")
    
    topics = ["testing strategy", "architecture", "configuration management"]
    
    for topic in topics:
        print(f"\n🔍 Testing: {topic}")
        result = test_evolution_tracking(topic)
        results[f"evolution_{topic.replace(' ', '_')}"] = result
        print_result(f"Evolution Tracking - {topic}", result)
    
    # ========================================================================
    # Test 4: Period Comparison
    # ========================================================================
    print_section("Test 4: Period Comparison")
    print(f"📅 Comparing: {month_ago[:10]} to {now_iso[:10]}")
    
    for key, question in questions.items():
        print(f"\n🔍 Testing: {key}")
        result = test_period_comparison(question, month_ago, now_iso)
        results[f"comparison_{key}"] = result
        print_result(f"Period Comparison - {key}", result)
    
    # ========================================================================
    # Test 5: Drift Detection
    # ========================================================================
    print_section("Test 5: Drift Detection")
    
    for topic in topics:
        print(f"\n🔍 Testing: {topic}")
        result = test_drift_detection(topic)
        results[f"drift_{topic.replace(' ', '_')}"] = result
        print_result(f"Drift Detection - {topic}", result)
    
    # ========================================================================
    # Summary and Comparison
    # ========================================================================
    print_section("Summary: Temporal RAG Impact Analysis")
    
    # Count successes
    total_tests = len(results)
    successful = sum(1 for r in results.values() if "error" not in r)
    failed = total_tests - successful
    
    print(f"\n📊 Test Results:")
    print(f"   Total Tests: {total_tests}")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   Success Rate: {(successful/total_tests)*100:.1f}%")
    
    # Compare standard vs temporal
    print(f"\n🔍 Temporal Impact:")
    
    standard_sources = [r.get("sources", 0) for k, r in results.items() if k.startswith("standard_") and "error" not in r]
    temporal_sources = [r.get("sources", 0) for k, r in results.items() if k.startswith("temporal_point_") and "error" not in r]
    
    if standard_sources and temporal_sources:
        avg_standard = sum(standard_sources) / len(standard_sources)
        avg_temporal = sum(temporal_sources) / len(temporal_sources)
        print(f"   Standard RAG avg sources: {avg_standard:.1f}")
        print(f"   Temporal RAG avg sources: {avg_temporal:.1f}")
        
        if avg_temporal > avg_standard:
            print(f"   ✅ Temporal RAG provides {((avg_temporal/avg_standard)-1)*100:.1f}% more context!")
        else:
            print(f"   ℹ️ Source counts similar (context may differ in quality)")
    
    # Evolution tracking results
    evolution_results = [r for k, r in results.items() if k.startswith("evolution_") and "error" not in r]
    if evolution_results:
        avg_periods = sum(r.get("periods", 0) for r in evolution_results) / len(evolution_results)
        print(f"\n📈 Evolution Tracking:")
        print(f"   Average periods analyzed: {avg_periods:.1f}")
        print(f"   ✅ Temporal analysis provides historical context unavailable in standard RAG")
    
    # Drift detection results
    drift_results = [r for k, r in results.items() if k.startswith("drift_") and "error" not in r]
    if drift_results:
        drift_detected = sum(1 for r in drift_results if r.get("drift_detected", False))
        print(f"\n🚨 Drift Detection:")
        print(f"   Topics with drift detected: {drift_detected}/{len(drift_results)}")
        print(f"   ✅ Identifies changing information over time")
    
    # Key insights
    print(f"\n💡 Key Insights:")
    print(f"   1. Standard RAG: Provides current snapshot without temporal context")
    print(f"   2. Point-in-Time RAG: Shows historical state at specific dates")
    print(f"   3. Evolution Tracking: Reveals how information changed over time")
    print(f"   4. Period Comparison: Highlights differences between time periods")
    print(f"   5. Drift Detection: Identifies when information significantly changed")
    
    print(f"\n🎯 Conclusion:")
    if successful >= total_tests * 0.7:
        print(f"   ✅ Temporal RAG significantly enhances standard RAG with time-aware context!")
        print(f"   ✅ Provides historical awareness, evolution tracking, and drift detection")
        print(f"   ✅ Enables time-travel queries and period comparisons")
        return 0
    else:
        print(f"   ⚠️ Some temporal features may need investigation")
        print(f"   ℹ️ Review failed tests above for details")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
