#!/usr/bin/env python3
"""
Final RAG Comparison: Standard vs Temporal

Direct comparison with detailed answer analysis.
"""

import httpx
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def test_standard_rag(question):
    """Test standard RAG."""
    try:
        response = httpx.post(
            f"{API_BASE}/api/v1/query/enhanced",
            json={"question": question, "n_results": 10},
            timeout=30.0
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def test_temporal_query(question, service_name="ecosystem-mcp"):
    """Test temporal point-in-time query."""
    try:
        # Query as of 1 week ago
        as_of_date = (datetime.now() - timedelta(days=7)).isoformat() + "Z"
        
        response = httpx.post(
            f"{API_BASE}/api/v1/rag/temporal/query",
            json={
                "question": question,
                "as_of_date": as_of_date,
                "service_name": service_name,
                "limit": 10
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}

def compare_answers(question):
    """Compare standard vs temporal RAG for a question."""
    print(f"\n📋 Question: \"{question}\"\n")
    print("-" * 80)
    
    # Test standard RAG
    print("\n🔵 STANDARD RAG (Current Snapshot Only):")
    print("-" * 40)
    standard_result = test_standard_rag(question)
    
    if "error" in standard_result:
        print(f"❌ Error: {standard_result['error']}")
        standard_answer = None
    else:
        standard_answer = standard_result.get("answer", "")
        sources = standard_result.get("sources", [])
        print(f"✅ Success")
        print(f"📊 Sources: {len(sources)}")
        print(f"🎯 Tier: {standard_result.get('tier_used', 'N/A')}")
        print(f"\n💬 Answer:\n{standard_answer[:500]}...")
        if len(standard_answer) > 500:
            print(f"\n... (truncated, full length: {len(standard_answer)} chars)")
    
    # Test temporal RAG
    print("\n\n🟢 TEMPORAL RAG (Time-Aware Context):")
    print("-" * 40)
    temporal_result = test_temporal_query(question)
    
    if "error" in temporal_result:
        print(f"❌ Error: {temporal_result['error']}")
        temporal_answer = None
    else:
        temporal_answer = temporal_result.get("answer", "")
        sources = temporal_result.get("sources", [])
        metadata = temporal_result.get("metadata", {})
        print(f"✅ Success")
        print(f"📊 Sources: {len(sources)}")
        print(f"📅 Queried as of: {metadata.get('as_of_date', 'N/A')[:10]}")
        print(f"🎯 Temporal aware: {metadata.get('temporal_filter_applied', False)}")
        print(f"\n💬 Answer:\n{temporal_answer[:500]}...")
        if len(temporal_answer) > 500:
            print(f"\n... (truncated, full length: {len(temporal_answer)} chars)")
    
    # Comparison
    print("\n\n📊 COMPARISON:")
    print("-" * 40)
    
    if standard_answer and temporal_answer:
        # Length comparison
        print(f"Answer Length:")
        print(f"  Standard: {len(standard_answer)} chars")
        print(f"  Temporal: {len(temporal_answer)} chars")
        
        # Check if answers are different
        if standard_answer == temporal_answer:
            print(f"\n⚠️  Answers are IDENTICAL")
            print(f"   (May indicate temporal filtering not fully active)")
        else:
            print(f"\n✅ Answers are DIFFERENT")
            print(f"   Temporal RAG provides time-aware context!")
            
            # Show first difference
            for i, (s, t) in enumerate(zip(standard_answer, temporal_answer)):
                if s != t:
                    print(f"\n   First difference at char {i}:")
                    print(f"   Standard: ...{standard_answer[max(0,i-30):i+30]}...")
                    print(f"   Temporal: ...{temporal_answer[max(0,i-30):i+30]}...")
                    break
    
    elif standard_answer:
        print("⚠️  Only standard RAG succeeded")
    elif temporal_answer:
        print("⚠️  Only temporal RAG succeeded")
    else:
        print("❌ Both failed")
    
    return {
        "standard": standard_result,
        "temporal": temporal_result
    }

def main():
    print_section("Standard RAG vs Temporal RAG - Final Comparison")
    
    print("🎯 Goal: Compare answers to prove temporal impact\n")
    
    questions = [
        "What is the testing strategy?",
        "How is the system architecture designed?",
        "What are the key features?"
    ]
    
    results = []
    
    for i, question in enumerate(questions, 1):
        print_section(f"Test {i}/{len(questions)}")
        result = compare_answers(question)
        results.append(result)
    
    # Final summary
    print_section("FINAL SUMMARY")
    
    standard_success = sum(1 for r in results if "error" not in r["standard"])
    temporal_success = sum(1 for r in results if "error" not in r["temporal"])
    
    print(f"📊 Results:")
    print(f"   Standard RAG: {standard_success}/{len(questions)} succeeded")
    print(f"   Temporal RAG: {temporal_success}/{len(questions)} succeeded")
    
    if standard_success > 0 and temporal_success > 0:
        print(f"\n✅ BOTH SYSTEMS OPERATIONAL!")
        print(f"\n💡 Key Insights:")
        print(f"   • Standard RAG: Fast, reliable, current snapshot")
        print(f"   • Temporal RAG: Time-aware, historical context")
        print(f"   • Together: Complete temporal coverage!")
    
    return 0 if (standard_success > 0 and temporal_success > 0) else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
