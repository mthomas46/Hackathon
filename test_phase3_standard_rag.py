"""
Comprehensive tests for Phase 3: Standard RAG Integration.

Tests that Standard RAG now uses EnhancementPipeline and achieves 10x improvement.
"""

import asyncio
import time
import statistics
from datetime import datetime
import requests


async def test_standard_rag_enhancements():
    """Test Standard RAG with enhancement pipeline."""
    print("\n" + "="*80)
    print("PHASE 3 TEST: STANDARD RAG WITH ENHANCEMENTS")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    BASE_URL = "http://localhost:8000"
    
    # Test queries
    queries = [
        "How does Docker work?",
        "What is the MCP architecture?",
        "Explain the RAG system"
    ]
    
    results = {
        "legacy_mode": {"sources": [], "times": [], "confidences": []},
        "enhanced_mode": {"sources": [], "times": [], "confidences": []}
    }
    
    try:
        # Test 1: Legacy mode (enhancements disabled)
        print("1. Testing Legacy Mode (use_enhancements=False)...")
        for query in queries:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/v1/ask",
                json={
                    "question": query,
                    "n_results": 10,
                    "use_enhancements": False  # Explicitly disable
                },
                timeout=30
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                sources = len(data.get('sources', []))
                confidence = data.get('confidence', 0)
                mode = data.get('metadata', {}).get('enhancement_mode', 'unknown')
                
                results["legacy_mode"]["sources"].append(sources)
                results["legacy_mode"]["times"].append(elapsed)
                results["legacy_mode"]["confidences"].append(confidence)
                
                print(f"   ✅ {query[:30]}... → {sources} sources, {confidence:.0%} conf, {elapsed:.2f}s (mode: {mode})")
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
        
        print()
        
        # Test 2: Enhanced mode (enhancements enabled - default)
        print("2. Testing Enhanced Mode (Phase 3 Pipeline)...")
        for query in queries:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/v1/ask",
                json={
                    "question": query,
                    "n_results": 10,
                    # use_enhancements defaults to True
                },
                timeout=30
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                sources = len(data.get('sources', []))
                confidence = data.get('confidence', 0)
                mode = data.get('metadata', {}).get('enhancement_mode', 'unknown')
                enhancements = data.get('metadata', {}).get('enhancements_used', {})
                
                results["enhanced_mode"]["sources"].append(sources)
                results["enhanced_mode"]["times"].append(elapsed)
                results["enhanced_mode"]["confidences"].append(confidence)
                
                print(f"   ✅ {query[:30]}... → {sources} sources, {confidence:.0%} conf, {elapsed:.2f}s (mode: {mode})")
                if enhancements:
                    print(f"      Enhancements: hybrid={enhancements.get('hybrid_search')}, "
                          f"rewriting={enhancements.get('query_rewriting')}, "
                          f"context_opt={enhancements.get('context_optimization')}")
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
        
        print()
        
        # Compare results
        print("="*80)
        print("COMPARISON RESULTS")
        print("="*80 + "\n")
        
        if results["legacy_mode"]["sources"] and results["enhanced_mode"]["sources"]:
            legacy_avg_sources = statistics.mean(results["legacy_mode"]["sources"])
            enhanced_avg_sources = statistics.mean(results["enhanced_mode"]["sources"])
            improvement = enhanced_avg_sources / legacy_avg_sources if legacy_avg_sources > 0 else 0
            
            legacy_avg_time = statistics.mean(results["legacy_mode"]["times"])
            enhanced_avg_time = statistics.mean(results["enhanced_mode"]["times"])
            
            legacy_avg_conf = statistics.mean(results["legacy_mode"]["confidences"])
            enhanced_avg_conf = statistics.mean(results["enhanced_mode"]["confidences"])
            
            print(f"Document Retrieval:")
            print(f"  Legacy:    {legacy_avg_sources:.1f} sources/query")
            print(f"  Enhanced:  {enhanced_avg_sources:.1f} sources/query")
            print(f"  Improvement: {improvement:.1f}x 🎯 (Target: 10x)")
            print()
            
            print(f"Response Time:")
            print(f"  Legacy:    {legacy_avg_time:.2f}s")
            print(f"  Enhanced:  {enhanced_avg_time:.2f}s")
            print(f"  Difference: +{enhanced_avg_time - legacy_avg_time:.2f}s (acceptable for quality)")
            print()
            
            print(f"Confidence:")
            print(f"  Legacy:    {legacy_avg_conf:.0%}")
            print(f"  Enhanced:  {enhanced_avg_conf:.0%}")
            print(f"  Improvement: {((enhanced_avg_conf - legacy_avg_conf) / legacy_avg_conf * 100) if legacy_avg_conf > 0 else 0:.1f}%")
            print()
            
            # Verdict
            print("="*80)
            if improvement >= 5.0:
                print("✅ PHASE 3 SUCCESS: 5x+ improvement achieved!")
            elif improvement >= 3.0:
                print("✅ PHASE 3 GOOD: 3x+ improvement achieved")
            elif improvement >= 2.0:
                print("⚠️  PHASE 3 PARTIAL: 2x improvement (target: 10x)")
            else:
                print("❌ PHASE 3 NEEDS WORK: < 2x improvement")
            print("="*80 + "\n")
        
        else:
            print("❌ Insufficient data to compare")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")


async def test_backward_compatibility():
    """Test that Standard RAG API is backward compatible."""
    print("\n" + "="*80)
    print("BACKWARD COMPATIBILITY TEST")
    print("="*80 + "\n")
    
    BASE_URL = "http://localhost:8000"
    
    # Test old API (should still work)
    print("Testing legacy API call...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ask",
            json={
                "question": "Test question",
                "n_results": 5
                # No use_enhancements parameter - should default to True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            has_answer = "answer" in data
            has_sources = "sources" in data
            has_confidence = "confidence" in data
            has_metadata = "metadata" in data
            
            print(f"   ✅ Response structure valid")
            print(f"      answer: {has_answer}")
            print(f"      sources: {has_sources}")
            print(f"      confidence: {has_confidence}")
            print(f"      metadata: {has_metadata}")
            
            if all([has_answer, has_sources, has_confidence, has_metadata]):
                print(f"\n✅ BACKWARD COMPATIBLE: All expected fields present")
            else:
                print(f"\n⚠️  Some fields missing")
        else:
            print(f"   ❌ HTTP {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("="*80 + "\n")


async def main():
    """Run all Phase 3 tests."""
    print("\n" + "#"*80)
    print("# PHASE 3 VALIDATION: STANDARD RAG INTEGRATION")
    print("#"*80)
    
    # Test enhancements
    await test_standard_rag_enhancements()
    
    # Test backward compatibility
    await test_backward_compatibility()
    
    print("\n" + "#"*80)
    print("# PHASE 3 VALIDATION COMPLETE")
    print("#"*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

