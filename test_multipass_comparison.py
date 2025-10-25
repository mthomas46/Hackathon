"""
Multi-Pass RAG Comparison: Standard vs Enhanced

Tests the newly implemented enhancement support in multi-pass queries.
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:8000"

def run_multipass_query(question, use_enhancements=False):
    """Run a multi-pass RAG query."""
    
    url = f"{API_BASE}/api/v1/query/multi-pass"
    
    payload = {
        "query": question,
        "num_sections": 2,  # Reduced from 3 to speed up
        "questions_per_section": 2,  # Keep it quick
        "documents_per_question": 10,
        "temperature": 0.7,
        "response_length": 500,
        "use_enhancements": use_enhancements
    }
    
    print(f"\n{'='*70}")
    print(f"{'🎨 ENHANCED' if use_enhancements else '📊 STANDARD'} MULTI-PASS RAG QUERY")
    print(f"{'='*70}")
    print(f"Question: {question}")
    print(f"Sections: {payload['num_sections']}")
    print(f"Questions/section: {payload['questions_per_section']}")
    print(f"Total questions: {payload['num_sections'] * payload['questions_per_section']}")
    print(f"Enhancements: {'✅ ENABLED' if use_enhancements else '❌ DISABLED'}")
    print(f"\nSending request at {datetime.now().strftime('%H:%M:%S')}...")
    print("(This may take 30-60 seconds...)")
    
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, timeout=240)  # Increased from 180s
        elapsed = time.time() - start_time
        
        print(f"✅ Response received in {elapsed:.2f}s")
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(response.text[:500])
            return None, elapsed
        
        result = response.json()
        return result, elapsed
    
    except requests.Timeout:
        elapsed = time.time() - start_time
        print(f"⏱️ Request timed out after {elapsed:.2f}s")
        return None, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Exception: {e}")
        return None, elapsed


def analyze_multipass_result(result, label):
    """Analyze and display multi-pass results."""
    
    print(f"\n{'='*70}")
    print(f"{label} - RESULTS ANALYSIS")
    print(f"{'='*70}")
    
    if not result:
        print("❌ No results to analyze")
        return None
    
    # Basic info
    final_synthesis = result.get('final_synthesis', '')
    sections = result.get('sections', [])
    
    print(f"\n📊 Query Execution:")
    print(f"  • Original query: {result.get('original_query', 'N/A')[:60]}...")
    print(f"  • Sections processed: {result.get('num_passes', 0)}")
    print(f"  • Questions per section: {result.get('num_secondary_questions', 0)}")
    print(f"  • Total questions asked: {result.get('total_questions_asked', 0)}")
    print(f"  • Total sources used: {result.get('total_sources_used', 0)}")
    print(f"  • Total duration: {result.get('total_duration_seconds', 0):.2f}s")
    
    # Metadata
    metadata = result.get('metadata', {})
    print(f"\n🔍 Metadata:")
    print(f"  • Enhancements used: {metadata.get('use_enhancements', False)}")
    print(f"  • Average docs/question: {metadata.get('avg_docs_per_question', 0):.1f}")
    
    # Show sections analyzed
    if sections:
        print(f"\n📚 Sections Analyzed ({len(sections)}):")
        for i, section in enumerate(sections, 1):
            section_name = section.get('section_name', 'Unknown')
            questions_count = len(section.get('questions', []))
            synthesis_length = len(section.get('synthesis', ''))
            print(f"  {i}. {section_name}")
            print(f"     └─ {questions_count} questions, synthesis: {synthesis_length} chars")
    
    # Final synthesis
    print(f"\n💬 Final Synthesis:")
    print(f"  • Length: {len(final_synthesis)} characters")
    preview = final_synthesis[:400] + "..." if len(final_synthesis) > 400 else final_synthesis
    print(f"  • Preview:\n{preview}")
    
    return {
        'synthesis_length': len(final_synthesis),
        'num_sections': len(sections),
        'total_questions': result.get('total_questions_asked', 0),
        'total_sources': result.get('total_sources_used', 0),
        'duration': result.get('total_duration_seconds', 0),
        'use_enhancements': metadata.get('use_enhancements', False)
    }


def compare_multipass_results(standard_metrics, enhanced_metrics, standard_time, enhanced_time):
    """Compare standard vs enhanced multi-pass results."""
    
    print(f"\n{'='*70}")
    print(f"📊 MULTI-PASS COMPARISON: STANDARD vs ENHANCED")
    print(f"{'='*70}")
    
    print(f"\n⏱️  Performance:")
    print(f"  Standard time:  {standard_time:.2f}s")
    print(f"  Enhanced time:  {enhanced_time:.2f}s")
    time_diff = enhanced_time - standard_time
    time_pct = (time_diff/standard_time*100) if standard_time > 0 else 0
    print(f"  Overhead:       {time_diff:+.2f}s ({time_pct:+.1f}%)")
    
    print(f"\n📝 Content Quality:")
    print(f"  Standard synthesis:  {standard_metrics['synthesis_length']} chars")
    print(f"  Enhanced synthesis:  {enhanced_metrics['synthesis_length']} chars")
    length_diff = enhanced_metrics['synthesis_length'] - standard_metrics['synthesis_length']
    length_pct = (length_diff/standard_metrics['synthesis_length']*100) if standard_metrics['synthesis_length'] > 0 else 0
    print(f"  Difference:          {length_diff:+d} chars ({length_pct:+.1f}%)")
    
    print(f"\n📚 Research Depth:")
    print(f"  Standard sections:   {standard_metrics['num_sections']}")
    print(f"  Enhanced sections:   {enhanced_metrics['num_sections']}")
    print(f"  Standard questions:  {standard_metrics['total_questions']}")
    print(f"  Enhanced questions:  {enhanced_metrics['total_questions']}")
    print(f"  Standard sources:    {standard_metrics['total_sources']}")
    print(f"  Enhanced sources:    {enhanced_metrics['total_sources']}")
    
    print(f"\n🎨 Enhancement Status:")
    print(f"  Standard used enhancements: {'✅' if standard_metrics['use_enhancements'] else '❌'} {standard_metrics['use_enhancements']}")
    print(f"  Enhanced used enhancements: {'✅' if enhanced_metrics['use_enhancements'] else '❌'} {enhanced_metrics['use_enhancements']}")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"✅ ENHANCEMENT VERIFICATION")
    print(f"{'='*70}")
    
    checks = []
    
    if not standard_metrics['use_enhancements'] and enhanced_metrics['use_enhancements']:
        checks.append("✅ Enhancement flag correctly applied")
    elif enhanced_metrics['use_enhancements']:
        checks.append("✅ Enhancements enabled in enhanced query")
    else:
        checks.append("❌ WARNING: Enhancement flag not set in enhanced query!")
    
    if time_diff < 10.0:
        checks.append(f"✅ Performance acceptable (< 10s overhead)")
    else:
        checks.append(f"⚠️  Higher overhead ({time_diff:.1f}s)")
    
    if length_diff > 0:
        checks.append(f"✅ Enhanced synthesis is {length_pct:+.1f}% longer (more detail)")
    else:
        checks.append(f"ℹ️  Standard synthesis was longer")
    
    for check in checks:
        print(f"  {check}")
    
    print(f"\n{'='*70}")
    if enhanced_metrics['use_enhancements']:
        print(f"🎉 SUCCESS: Multi-pass enhancements are working!")
    else:
        print(f"⚠️  NOTE: Check logs to verify enhancement application")
    print(f"{'='*70}")


def main():
    """Run the multi-pass comparison test."""
    
    print("\n" + "="*70)
    print("🔬 MULTI-PASS RAG ENHANCEMENT TEST")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test question that should benefit from enhancements
    test_question = "What is the architecture and testing strategy of ecosystem-mcp?"
    
    print(f"\n📝 Test Question:")
    print(f"  {test_question}")
    
    print(f"\n🎯 Expected enhancements:")
    print(f"  • Template matching: 'architecture' + 'testing'")
    print(f"  • Glossary: MCP, ecosystem, architecture, testing terms")
    print(f"  • Priorities: README.md, ARCHITECTURE.md, test files")
    print(f"  • Multi-signal ranking for document selection")
    
    # Test 1: Standard multi-pass (no enhancements)
    print(f"\n{'='*70}")
    print("TEST 1: STANDARD MULTI-PASS RAG")
    print(f"{'='*70}")
    
    standard_result, standard_time = run_multipass_query(
        question=test_question,
        use_enhancements=False
    )
    
    if not standard_result:
        print("\n❌ Standard query failed - cannot continue")
        return
    
    standard_metrics = analyze_multipass_result(standard_result, "STANDARD")
    
    if not standard_metrics:
        print("\n❌ Could not analyze standard results")
        return
    
    # Wait before next query
    print("\n⏳ Waiting 5 seconds before enhanced query...")
    time.sleep(5)
    
    # Test 2: Enhanced multi-pass (with enhancements)
    print(f"\n{'='*70}")
    print("TEST 2: ENHANCED MULTI-PASS RAG")
    print(f"{'='*70}")
    
    enhanced_result, enhanced_time = run_multipass_query(
        question=test_question,
        use_enhancements=True
    )
    
    if not enhanced_result:
        print("\n❌ Enhanced query failed - cannot compare")
        return
    
    enhanced_metrics = analyze_multipass_result(enhanced_result, "ENHANCED")
    
    if not enhanced_metrics:
        print("\n❌ Could not analyze enhanced results")
        return
    
    # Compare results
    compare_multipass_results(standard_metrics, enhanced_metrics, standard_time, enhanced_time)
    
    print(f"\n{'='*70}")
    print("✅ MULTI-PASS COMPARISON TEST COMPLETE!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()

