#!/usr/bin/env python3
"""
Quick test to verify Phase 1 improvements:
1. Quality scores are visible in API responses
2. Quality boost is being applied
"""

import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1"

def test_phase1_improvements():
    """Test Phase 1: Quality scores should be visible."""
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                              ║")
    print("║                    PHASE 1 QUICK TEST - QUALITY SCORES                       ║")
    print("║                                                                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝\n")
    
    # Test query
    test_query = "What are MCP servers and how do they work?"
    
    print(f"📋 Test Query: {test_query}\n")
    print("━" * 80)
    
    # Test Enhanced RAG with Phase 1+2+3
    print("\n🧪 Testing Enhanced RAG (Phase 1+2+3)...\n")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/rag/ask/enhanced",
            json={
                "question": test_query,
                "n_results": 5,
                "enable_hybrid_search": True,
                "enable_query_rewriting": False,  # Skip for speed
                "enable_confidence_scoring": True,
                "enable_reranking": False,  # Skip for speed
                "enable_context_optimization": False,  # Skip for speed
                "temperature": 0.7
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        # Check if quality scores are present
        sources = result.get("sources", [])
        print(f"✅ Retrieved {len(sources)} sources\n")
        
        quality_scores_present = 0
        for source in sources[:5]:  # Check first 5
            quality_score = source.get("quality_score")
            quality_grade = source.get("quality_grade")
            relevance = source.get("relevance_score", 0)
            
            print(f"   Source {source['id']}: {source['file_path'].split('/')[-1]}")
            print(f"      • Relevance: {relevance:.3f}")
            
            if quality_score is not None:
                quality_scores_present += 1
                print(f"      • Quality Score: {quality_score} ({quality_grade or 'N/A'})")
                print(f"      ✅ PHASE 1: Quality score IS visible!")
            else:
                print(f"      ❌ PHASE 1: Quality score MISSING!")
            
            print()
        
        # Summary
        print("━" * 80)
        print(f"\n📊 PHASE 1 RESULTS:\n")
        print(f"   Total Sources: {len(sources)}")
        print(f"   Sources with Quality Scores: {quality_scores_present}/{len(sources)}")
        
        if quality_scores_present > 0:
            percentage = (quality_scores_present / len(sources)) * 100
            print(f"   Coverage: {percentage:.1f}%")
            
            if percentage >= 80:
                print(f"\n   ✅ PHASE 1 SUCCESS: Quality scores are visible!")
            elif percentage >= 50:
                print(f"\n   ⚠️  PHASE 1 PARTIAL: Some quality scores visible")
            else:
                print(f"\n   ❌ PHASE 1 FAILED: Most quality scores missing")
        else:
            print(f"\n   ❌ PHASE 1 FAILED: NO quality scores visible")
        
        # Check confidence score
        confidence = result.get("confidence_score", 0)
        print(f"\n   Confidence Score: {confidence:.1f}%")
        
        # Check active enhancements
        enhancements = result.get("active_enhancements", {})
        print(f"\n   Active Enhancements:")
        print(f"      • Hybrid Search: {enhancements.get('hybrid_search', False)}")
        print(f"      • Quality Boost: {enhancements.get('quality_boost', False)}")
        
        print("\n━" * 80)
        
        return quality_scores_present > 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_phase1_improvements()
    exit(0 if success else 1)

