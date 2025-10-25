"""
Quick comparison of standard vs enhanced RAG (basic queries, not multi-pass).

This test proves the RAG enhancements are working by comparing:
1. Standard RAG (no enhancements)
2. Enhanced RAG (with glossary, templates, priorities, etc.)
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:8000"

def run_basic_query(question, use_enhancements=False):
    """Run a basic RAG query (fast)."""
    
    url = f"{API_BASE}/api/v1/query/enhanced"
    
    payload = {
        "question": question,
        "use_enhancements": use_enhancements,
        "n_results": 10,
        "temperature": 0.7,
        "response_length": 1000
    }
    
    print(f"\n{'='*70}")
    print(f"Running {'ENHANCED' if use_enhancements else 'STANDARD'} RAG Query")
    print(f"{'='*70}")
    print(f"Question: {question}")
    print(f"Enhancements: {'✅ ENABLED' if use_enhancements else '❌ DISABLED'}")
    print(f"\nSending request...")
    
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        elapsed = time.time() - start_time
        
        print(f"✅ Response received in {elapsed:.2f}s")
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return None, elapsed
        
        result = response.json()
        return result, elapsed
    
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Exception: {e}")
        return None, elapsed


def analyze_result(result, label):
    """Analyze and display query results."""
    
    print(f"\n{'='*70}")
    print(f"{label} - RESULTS ANALYSIS")
    print(f"{'='*70}")
    
    if not result:
        print("❌ No results to analyze")
        return None
    
    # Basic info
    answer = result.get('answer', '')
    print(f"\n📊 Basic Metrics:")
    print(f"  • Answer length: {len(answer)} characters")
    print(f"  • Confidence: {result.get('confidence', 0):.3f}")
    print(f"  • Sources used: {len(result.get('sources', []))}")
    
    # Metadata
    metadata = result.get('metadata', {})
    print(f"\n🔍 Metadata:")
    print(f"  • Query ID: {result.get('query_id', 'N/A')[:20]}...")
    print(f"  • Documents used: {metadata.get('documents_used', 0)}")
    print(f"  • Enhancements applied: {metadata.get('enhancements_applied', False)}")
    print(f"  • Matched template: {metadata.get('matched_template', 'None')}")
    
    # Enhancement-specific metadata
    if metadata.get('enhancements_applied'):
        print(f"\n✨ Enhancement Details:")
        print(f"  • Template matched: {metadata.get('matched_template', 'None')}")
        if 'enhancements_applied' in metadata:
            enhancements = metadata.get('enhancements_applied')
            if isinstance(enhancements, dict):
                for feature, enabled in enhancements.items():
                    print(f"  • {feature}: {enabled}")
    
    # Show top sources with priority info
    sources = result.get('sources', [])
    if sources:
        print(f"\n📄 Top Sources:")
        for i, source in enumerate(sources[:5], 1):  # Show top 5
            path = source.get('file_path', 'Unknown')
            score = source.get('score', 0)
            
            # Show signal breakdown if available
            signals = source.get('signal_breakdown', {})
            if signals:
                priority = signals.get('priority', 1.0)
                priority_marker = ""
                if priority >= 1.5:
                    priority_marker = " 🔥 HIGH PRIORITY"
                elif priority >= 2.0:
                    priority_marker = " ⭐ CRITICAL PRIORITY"
                print(f"  {i}. {path} (score: {score:.3f}){priority_marker}")
                if signals:
                    print(f"     └─ semantic: {signals.get('semantic', 0):.3f}, "
                          f"glossary: {signals.get('glossary', 0):.3f}, "
                          f"quality: {signals.get('quality', 0):.3f}, "
                          f"priority: {signals.get('priority', 1.0):.2f}")
            else:
                print(f"  {i}. {path} (score: {score:.3f})")
    
    # Show answer preview
    if answer:
        print(f"\n💬 Answer Preview (first 400 chars):")
        preview = answer[:400] + "..." if len(answer) > 400 else answer
        print(f"  {preview}")
    
    return {
        'answer_length': len(answer),
        'confidence': result.get('confidence', 0),
        'num_sources': len(sources),
        'documents_used': metadata.get('documents_used', 0),
        'matched_template': metadata.get('matched_template'),
        'enhancements_applied': metadata.get('enhancements_applied', False),
        'top_score': sources[0].get('score', 0) if sources else 0
    }


def compare_results(standard_metrics, enhanced_metrics, standard_time, enhanced_time):
    """Compare standard vs enhanced results."""
    
    print(f"\n{'='*70}")
    print(f"📊 COMPARISON: STANDARD vs ENHANCED")
    print(f"{'='*70}")
    
    print(f"\n⏱️  Performance:")
    print(f"  Standard time:  {standard_time:.2f}s")
    print(f"  Enhanced time:  {enhanced_time:.2f}s")
    time_diff = enhanced_time - standard_time
    time_pct = (time_diff/standard_time*100) if standard_time > 0 else 0
    print(f"  Overhead:       {time_diff:+.2f}s ({time_pct:+.1f}%)")
    
    print(f"\n📝 Answer Quality:")
    print(f"  Standard length:    {standard_metrics['answer_length']} chars")
    print(f"  Enhanced length:    {enhanced_metrics['answer_length']} chars")
    length_diff = enhanced_metrics['answer_length'] - standard_metrics['answer_length']
    length_pct = (length_diff/standard_metrics['answer_length']*100) if standard_metrics['answer_length'] > 0 else 0
    print(f"  Difference:         {length_diff:+d} chars ({length_pct:+.1f}%)")
    
    print(f"\n🎯 Confidence:")
    print(f"  Standard:  {standard_metrics['confidence']:.3f}")
    print(f"  Enhanced:  {enhanced_metrics['confidence']:.3f}")
    conf_diff = enhanced_metrics['confidence'] - standard_metrics['confidence']
    conf_pct = (conf_diff/standard_metrics['confidence']*100) if standard_metrics['confidence'] > 0 else 0
    print(f"  Difference: {conf_diff:+.3f} ({conf_pct:+.1f}%)")
    
    print(f"\n📚 Document Quality:")
    print(f"  Standard top score:  {standard_metrics['top_score']:.3f}")
    print(f"  Enhanced top score:  {enhanced_metrics['top_score']:.3f}")
    score_diff = enhanced_metrics['top_score'] - standard_metrics['top_score']
    print(f"  Improvement:         {score_diff:+.3f}")
    
    print(f"\n🎨 Enhancement Features:")
    print(f"  Matched template:   {enhanced_metrics['matched_template'] or 'None'}")
    print(f"  Enhancements used:  {'✅ Yes' if enhanced_metrics['enhancements_applied'] else '❌ No'}")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"✅ ENHANCEMENT VERIFICATION")
    print(f"{'='*70}")
    
    checks = []
    
    if enhanced_metrics['enhancements_applied']:
        checks.append("✅ Enhancements were successfully applied")
    else:
        checks.append("❌ WARNING: Enhancements were NOT applied!")
    
    if enhanced_metrics['matched_template']:
        checks.append(f"✅ Template matched: '{enhanced_metrics['matched_template']}'")
    else:
        checks.append("ℹ️  No template matched (query may not match patterns)")
    
    if enhanced_metrics['confidence'] >= standard_metrics['confidence']:
        checks.append(f"✅ Confidence improved or maintained ({conf_pct:+.1f}%)")
    else:
        checks.append(f"⚠️  Confidence decreased ({conf_pct:+.1f}%)")
    
    if time_diff < 2.0:  # Less than 2 seconds overhead
        checks.append(f"✅ Performance excellent (< 2s overhead)")
    elif time_diff < 5.0:
        checks.append(f"✅ Performance acceptable (< 5s overhead)")
    else:
        checks.append(f"⚠️  Higher overhead ({time_diff:.1f}s)")
    
    for check in checks:
        print(f"  {check}")
    
    # Overall assessment
    print(f"\n{'='*70}")
    if enhanced_metrics['enhancements_applied'] and enhanced_metrics['confidence'] >= standard_metrics['confidence']:
        print(f"🎉 SUCCESS: Enhancements are working correctly!")
    elif enhanced_metrics['enhancements_applied']:
        print(f"✅ PARTIAL: Enhancements applied but results vary")
    else:
        print(f"❌ FAILED: Enhancements not applied - check configuration")
    print(f"{'='*70}")


def main():
    """Run the comparison test."""
    
    print("\n" + "="*70)
    print("🔬 RAG ENHANCEMENT COMPARISON TEST (FAST)")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test question that should benefit from enhancements
    test_question = "How is the ecosystem-mcp system architected and what are its main components?"
    
    print(f"\n📝 Test Question:")
    print(f"  {test_question}")
    
    print(f"\n🎯 This question should:")
    print(f"  • Match 'architecture' template (pattern: 'architected')")
    print(f"  • Benefit from glossary (MCP, ecosystem terms)")
    print(f"  • Benefit from priorities (README.md, ARCHITECTURE.md)")
    print(f"  • Use multi-signal ranking")
    
    # Test 1: Standard RAG (no enhancements)
    print(f"\n{'='*70}")
    print("TEST 1: STANDARD RAG (NO ENHANCEMENTS)")
    print(f"{'='*70}")
    
    standard_result, standard_time = run_basic_query(
        question=test_question,
        use_enhancements=False
    )
    
    standard_metrics = analyze_result(standard_result, "STANDARD")
    
    if not standard_metrics:
        print("\n❌ Standard query failed - cannot continue")
        return
    
    # Wait a moment
    print("\n⏳ Waiting 2 seconds before enhanced query...")
    time.sleep(2)
    
    # Test 2: Enhanced RAG (with enhancements)
    print(f"\n{'='*70}")
    print("TEST 2: ENHANCED RAG (WITH ENHANCEMENTS)")
    print(f"{'='*70}")
    
    enhanced_result, enhanced_time = run_basic_query(
        question=test_question,
        use_enhancements=True
    )
    
    enhanced_metrics = analyze_result(enhanced_result, "ENHANCED")
    
    if not enhanced_metrics:
        print("\n❌ Enhanced query failed - cannot compare")
        return
    
    # Compare results
    compare_results(standard_metrics, enhanced_metrics, standard_time, enhanced_time)
    
    print(f"\n{'='*70}")
    print("✅ TEST COMPLETE!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()

