#!/usr/bin/env python3
"""
Basic RAG Enhancement Comparison Test

Proves that enhancements are working by comparing
basic RAG queries with and without enhancements.
"""

import requests
import time
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

def run_basic_rag(question: str, use_enhancements: bool, label: str):
    """Run a basic RAG query and return results."""
    print(f"\n{'='*80}")
    print(f"🔍 {label}")
    print(f"{'='*80}")
    print(f"Question: {question}")
    print(f"Use Enhancements: {use_enhancements}")
    print(f"Started at: {datetime.now().strftime('%H:%M:%S')}")
    
    payload = {
        "question": question,
        "use_enhancements": use_enhancements,
        "n_results": 15,
        "temperature": 0.7
    }
    
    start = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE}/query/enhanced",
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start
        
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text[:300]}")
            return None
        
        result = response.json()
        metadata = result.get('metadata', {})
        
        print(f"✅ SUCCESS in {elapsed:.1f}s")
        print(f"")
        print(f"📊 METRICS:")
        print(f"  • Documents used: {metadata.get('documents_used', 0)}")
        print(f"  • Confidence: {metadata.get('confidence', 0):.3f}")
        print(f"  • Top score: {metadata.get('top_score', 0):.3f}")
        print(f"  • Answer length: {len(result.get('answer', ''))} chars")
        
        enhancements = metadata.get('enhancements_applied', [])
        matched_template = metadata.get('matched_template')
        
        if enhancements:
            print(f"")
            print(f"✨ ENHANCEMENTS APPLIED:")
            for enhancement in enhancements:
                print(f"  ✅ {enhancement}")
        
        if matched_template:
            print(f"")
            print(f"📋 MATCHED TEMPLATE: {matched_template}")
        
        print(f"")
        print(f"📝 ANSWER PREVIEW (first 400 chars):")
        print(f"{result.get('answer', '')[:400]}...")
        
        return {
            'success': True,
            'elapsed': elapsed,
            'documents_used': metadata.get('documents_used', 0),
            'confidence': metadata.get('confidence', 0),
            'top_score': metadata.get('top_score', 0),
            'answer_length': len(result.get('answer', '')),
            'enhancements_applied': enhancements,
            'matched_template': matched_template,
            'answer': result.get('answer', '')
        }
    
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception after {elapsed:.1f}s: {e}")
        return None


def compare_results(baseline: dict, enhanced: dict):
    """Compare results and highlight differences."""
    print(f"\n{'='*80}")
    print(f"📊 PROOF OF ENHANCEMENTS")
    print(f"{'='*80}")
    
    if not baseline or not enhanced:
        print("❌ Cannot compare - one or both queries failed")
        return
    
    # Compare enhancements
    baseline_enhancements = baseline.get('enhancements_applied', [])
    enhanced_enhancements = enhanced.get('enhancements_applied', [])
    
    print(f"\n✨ ENHANCEMENT EVIDENCE:")
    print(f"")
    print(f"Baseline enhancements: {len(baseline_enhancements)}")
    for e in baseline_enhancements:
        print(f"  • {e}")
    
    print(f"")
    print(f"Enhanced enhancements: {len(enhanced_enhancements)}")
    for e in enhanced_enhancements:
        print(f"  ✅ {e}")
    
    if not baseline_enhancements and enhanced_enhancements:
        print(f"")
        print(f"{'='*80}")
        print(f"🎉 PROOF: Enhanced query shows {len(enhanced_enhancements)} enhancements!")
        print(f"{'='*80}")
        print(f"")
        for enhancement in enhanced_enhancements:
            print(f"  ✅ {enhancement}")
    
    # Compare metrics
    print(f"\n📊 QUANTITATIVE COMPARISON:")
    print(f"")
    
    metrics = [
        ('Duration', 'elapsed', 's'),
        ('Documents', 'documents_used', 'docs'),
        ('Confidence', 'confidence', ''),
        ('Top Score', 'top_score', ''),
        ('Answer Length', 'answer_length', 'chars'),
    ]
    
    for metric_name, metric_key, unit in metrics:
        baseline_val = baseline.get(metric_key, 0)
        enhanced_val = enhanced.get(metric_key, 0)
        
        if baseline_val > 0:
            diff_pct = ((enhanced_val - baseline_val) / baseline_val) * 100
            diff_str = f"{diff_pct:+.1f}%"
        else:
            diff_str = "N/A"
        
        print(f"  {metric_name:15s}: {baseline_val:6.1f} → {enhanced_val:6.1f} {unit:5s} ({diff_str})")


def main():
    print("\n" + "="*80)
    print("🎯 BASIC RAG ENHANCEMENT COMPARISON TEST")
    print("="*80)
    print("")
    print("This test will PROVE enhancements are working by:")
    print("  1. Running a query WITHOUT enhancements (baseline)")
    print("  2. Running the SAME query WITH enhancements")
    print("  3. Showing the DIFFERENCE in metadata and results")
    print("")
    input("Press Enter to start...")
    
    test_question = "Explain the architecture and testing strategy of ecosystem-mcp"
    
    # Run baseline
    baseline_result = run_basic_rag(
        question=test_question,
        use_enhancements=False,
        label="BASELINE (Standard RAG)"
    )
    
    if not baseline_result:
        print("\n❌ Baseline query failed")
        return
    
    print("\n⏳ Waiting 2 seconds before enhanced query...")
    time.sleep(2)
    
    # Run enhanced
    enhanced_result = run_basic_rag(
        question=test_question,
        use_enhancements=True,
        label="ENHANCED (With Enhancements)"
    )
    
    if not enhanced_result:
        print("\n❌ Enhanced query failed")
        return
    
    # Compare
    compare_results(baseline_result, enhanced_result)
    
    print(f"\n")


if __name__ == "__main__":
    main()

