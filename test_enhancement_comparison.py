"""
Compare multi-pass RAG query results with and without enhancements.

This test proves the RAG enhancements are working by comparing:
1. Standard RAG (no enhancements)
2. Enhanced RAG (with glossary, templates, priorities, etc.)
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:8000"

def run_multipass_query(question, use_enhancements=False, num_sections=3, questions_per_section=3):
    """Run a multi-pass RAG query."""
    
    url = f"{API_BASE}/api/v1/query/multi-pass"
    
    payload = {
        "query": question,  # Multi-pass uses 'query' not 'question'
        "use_enhancements": use_enhancements,
        "num_sections": num_sections,
        "questions_per_section": questions_per_section,
        "documents_per_question": 10,
        "temperature": 0.7,
        "response_length": 500
    }
    
    print(f"\n{'='*70}")
    print(f"Running {'ENHANCED' if use_enhancements else 'STANDARD'} Multi-Pass RAG Query")
    print(f"{'='*70}")
    print(f"Question: {question}")
    print(f"Sections: {num_sections}, Questions/section: {questions_per_section}")
    print(f"Enhancements: {'✅ ENABLED' if use_enhancements else '❌ DISABLED'}")
    print(f"\nSending request...")
    
    start_time = time.time()
    response = requests.post(url, json=payload, timeout=300)
    elapsed = time.time() - start_time
    
    print(f"Response time: {elapsed:.2f}s")
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None, elapsed
    
    result = response.json()
    return result, elapsed


def analyze_result(result, label):
    """Analyze and display query results."""
    
    print(f"\n{'='*70}")
    print(f"{label} - RESULTS ANALYSIS")
    print(f"{'='*70}")
    
    if not result:
        print("❌ No results to analyze")
        return
    
    # Basic info
    print(f"\n📊 Basic Metrics:")
    print(f"  • Answer length: {len(result.get('answer', ''))} characters")
    print(f"  • Confidence: {result.get('confidence', 0):.2f}")
    print(f"  • Sources used: {len(result.get('sources', []))}")
    
    # Metadata
    metadata = result.get('metadata', {})
    print(f"\n🔍 Metadata:")
    print(f"  • Query ID: {result.get('query_id', 'N/A')}")
    print(f"  • Documents used: {metadata.get('documents_used', 0)}")
    print(f"  • Enhancements applied: {metadata.get('enhancements_applied', False)}")
    print(f"  • Matched template: {metadata.get('matched_template', 'None')}")
    
    # Show sections analyzed
    sections = result.get('sections_analyzed', [])
    if sections:
        print(f"\n📚 Sections Analyzed: {len(sections)}")
        for i, section in enumerate(sections[:5], 1):  # Show first 5
            print(f"  {i}. {section}")
    
    # Show top sources
    sources = result.get('sources', [])
    if sources:
        print(f"\n📄 Top Sources:")
        for i, source in enumerate(sources[:3], 1):  # Show top 3
            path = source.get('file_path', 'Unknown')
            score = source.get('score', 0)
            print(f"  {i}. {path} (score: {score:.3f})")
    
    # Show answer preview
    answer = result.get('answer', '')
    if answer:
        print(f"\n💬 Answer Preview:")
        preview = answer[:300] + "..." if len(answer) > 300 else answer
        print(f"  {preview}")
    
    return {
        'answer_length': len(answer),
        'confidence': result.get('confidence', 0),
        'num_sources': len(sources),
        'documents_used': metadata.get('documents_used', 0),
        'matched_template': metadata.get('matched_template'),
        'enhancements_applied': metadata.get('enhancements_applied', False)
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
    print(f"  Difference:     {time_diff:+.2f}s ({time_diff/standard_time*100:+.1f}%)")
    
    print(f"\n📝 Answer Quality:")
    print(f"  Standard length:    {standard_metrics['answer_length']} chars")
    print(f"  Enhanced length:    {enhanced_metrics['answer_length']} chars")
    length_diff = enhanced_metrics['answer_length'] - standard_metrics['answer_length']
    print(f"  Difference:         {length_diff:+d} chars ({length_diff/standard_metrics['answer_length']*100:+.1f}%)")
    
    print(f"\n🎯 Confidence:")
    print(f"  Standard:  {standard_metrics['confidence']:.3f}")
    print(f"  Enhanced:  {enhanced_metrics['confidence']:.3f}")
    conf_diff = enhanced_metrics['confidence'] - standard_metrics['confidence']
    print(f"  Difference: {conf_diff:+.3f} ({conf_diff/standard_metrics['confidence']*100:+.1f}%)")
    
    print(f"\n📚 Sources:")
    print(f"  Standard sources:   {standard_metrics['num_sources']}")
    print(f"  Enhanced sources:   {enhanced_metrics['num_sources']}")
    
    print(f"\n🎨 Enhancement Features:")
    print(f"  Matched template:   {enhanced_metrics['matched_template'] or 'None'}")
    print(f"  Enhancements used:  {enhanced_metrics['enhancements_applied']}")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"✅ ENHANCEMENT VERIFICATION")
    print(f"{'='*70}")
    
    checks = []
    
    if enhanced_metrics['enhancements_applied']:
        checks.append("✅ Enhancements were applied")
    else:
        checks.append("❌ Enhancements were NOT applied")
    
    if enhanced_metrics['matched_template']:
        checks.append(f"✅ Template matched: '{enhanced_metrics['matched_template']}'")
    else:
        checks.append("⚠️  No template matched")
    
    if enhanced_metrics['confidence'] >= standard_metrics['confidence']:
        checks.append(f"✅ Confidence improved or maintained")
    else:
        checks.append(f"⚠️  Confidence decreased")
    
    if time_diff < 5.0:  # Less than 5 seconds overhead
        checks.append(f"✅ Performance acceptable (< 5s overhead)")
    else:
        checks.append(f"⚠️  Higher overhead ({time_diff:.1f}s)")
    
    for check in checks:
        print(f"  {check}")


def main():
    """Run the comparison test."""
    
    print("\n" + "="*70)
    print("RAG ENHANCEMENT COMPARISON TEST")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test question that should benefit from enhancements
    test_question = "How is the ecosystem-mcp system architected and what are its main components?"
    
    print(f"\nThis question should:")
    print(f"  • Match 'architecture' template")
    print(f"  • Benefit from glossary (MCP, architecture terms)")
    print(f"  • Benefit from priorities (README, ARCHITECTURE docs)")
    
    # Test 1: Standard RAG (no enhancements)
    print(f"\n{'='*70}")
    print("TEST 1: STANDARD RAG (NO ENHANCEMENTS)")
    print(f"{'='*70}")
    
    standard_result, standard_time = run_multipass_query(
        question=test_question,
        use_enhancements=False,
        num_sections=3,
        questions_per_section=3
    )
    
    standard_metrics = analyze_result(standard_result, "STANDARD")
    
    # Wait a moment
    time.sleep(2)
    
    # Test 2: Enhanced RAG (with enhancements)
    print(f"\n{'='*70}")
    print("TEST 2: ENHANCED RAG (WITH ENHANCEMENTS)")
    print(f"{'='*70}")
    
    enhanced_result, enhanced_time = run_multipass_query(
        question=test_question,
        use_enhancements=True,
        num_sections=3,
        questions_per_section=3
    )
    
    enhanced_metrics = analyze_result(enhanced_result, "ENHANCED")
    
    # Compare results
    if standard_metrics and enhanced_metrics:
        compare_results(standard_metrics, enhanced_metrics, standard_time, enhanced_time)
    
    print(f"\n{'='*70}")
    print("TEST COMPLETE!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()

