#!/usr/bin/env python3
"""
Multi-Pass RAG Enhancement Comparison Test

Compares multi-pass RAG queries with and without enhancements
to prove that enhancements (glossary, priorities, templates, exclusions)
are actually impacting the results.
"""

import requests
import time
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

def run_multipass_query(query: str, use_enhancements: bool, label: str):
    """
    Run a multi-pass query and return detailed results.
    """
    print(f"\n{'='*80}")
    print(f"🔍 TEST: {label}")
    print(f"{'='*80}")
    print(f"Query: {query}")
    print(f"Use Enhancements: {use_enhancements}")
    print(f"Started at: {datetime.now().strftime('%H:%M:%S')}")
    print("")
    
    payload = {
        "query": query,
        "num_sections": 2,  # Use new defaults
        "questions_per_section": 2,
        "use_enhancements": use_enhancements,
        "temperature": 0.7,
        "response_length": 1000
    }
    
    start = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE}/query/multi-pass",
            json=payload,
            timeout=180
        )
        elapsed = time.time() - start
        
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text[:300]}")
            return None
        
        result = response.json()
        
        # Extract key metrics
        sections = result.get('num_passes', 0)
        questions = result.get('total_questions_asked', 0)
        duration = result.get('total_duration_seconds', 0)
        synthesis = result.get('final_synthesis', '')
        section_summaries = result.get('section_summaries', [])
        
        # Extract metadata from sections to check for enhancements
        enhancements_applied = []
        matched_templates = set()
        total_documents = 0
        
        for section in result.get('sections', []):
            for question in section.get('questions', []):
                metadata = question.get('metadata', {})
                
                # Check for enhancements metadata
                if 'enhancements_applied' in metadata:
                    enhancements_applied.extend(metadata['enhancements_applied'])
                
                if 'matched_template' in metadata:
                    template = metadata.get('matched_template')
                    if template:
                        matched_templates.add(template)
                
                total_documents += metadata.get('documents_used', 0)
        
        print(f"✅ SUCCESS in {elapsed:.1f}s")
        print(f"")
        print(f"📊 METRICS:")
        print(f"  • Sections: {sections}")
        print(f"  • Questions: {questions}")
        print(f"  • Duration: {duration:.1f}s")
        print(f"  • Total documents used: {total_documents}")
        print(f"  • Answer length: {len(synthesis)} chars")
        
        if enhancements_applied:
            print(f"")
            print(f"✨ ENHANCEMENTS APPLIED:")
            for enhancement in set(enhancements_applied):
                print(f"  • {enhancement}")
        
        if matched_templates:
            print(f"")
            print(f"🎯 MATCHED TEMPLATES:")
            for template in matched_templates:
                print(f"  • {template}")
        
        # Show section details
        print(f"")
        print(f"📑 SECTION BREAKDOWN:")
        for i, section_summary in enumerate(section_summaries):
            print(f"  Section {i+1}: {section_summary.get('section_name', 'Unknown')}")
            print(f"    • Questions: {section_summary.get('questions_count', 0)}")
            print(f"    • Duration: {section_summary.get('duration_seconds', 0):.1f}s")
            print(f"    • Synthesis: {section_summary.get('synthesis_length', 0)} chars")
        
        # Show first 500 chars of answer
        print(f"")
        print(f"📝 ANSWER PREVIEW (first 500 chars):")
        print(f"{synthesis[:500]}...")
        
        return {
            'success': True,
            'elapsed': elapsed,
            'sections': sections,
            'questions': questions,
            'duration': duration,
            'answer_length': len(synthesis),
            'total_documents': total_documents,
            'enhancements_applied': list(set(enhancements_applied)),
            'matched_templates': list(matched_templates),
            'synthesis': synthesis,
            'section_summaries': section_summaries
        }
    
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"❌ TIMEOUT after {elapsed:.1f}s")
        return None
    
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception after {elapsed:.1f}s: {type(e).__name__}: {e}")
        return None


def compare_results(baseline: dict, enhanced: dict):
    """
    Compare baseline vs enhanced results and show differences.
    """
    print(f"\n{'='*80}")
    print(f"📊 COMPARISON: Baseline vs Enhanced")
    print(f"{'='*80}")
    
    if not baseline or not enhanced:
        print("❌ Cannot compare - one or both queries failed")
        return
    
    print(f"\n🔢 QUANTITATIVE COMPARISON:")
    print(f"")
    
    metrics = [
        ('Duration', 'duration', 's'),
        ('Answer Length', 'answer_length', 'chars'),
        ('Total Documents', 'total_documents', 'docs'),
        ('Questions', 'questions', 'questions'),
    ]
    
    for metric_name, metric_key, unit in metrics:
        baseline_val = baseline.get(metric_key, 0)
        enhanced_val = enhanced.get(metric_key, 0)
        
        if baseline_val > 0:
            diff_pct = ((enhanced_val - baseline_val) / baseline_val) * 100
            diff_str = f"{diff_pct:+.1f}%"
        else:
            diff_str = "N/A"
        
        print(f"  {metric_name:20s}: {baseline_val:6.1f} → {enhanced_val:6.1f} {unit:8s} ({diff_str})")
    
    print(f"\n✨ ENHANCEMENTS EVIDENCE:")
    print(f"")
    
    baseline_enhancements = baseline.get('enhancements_applied', [])
    enhanced_enhancements = enhanced.get('enhancements_applied', [])
    
    if not baseline_enhancements and not enhanced_enhancements:
        print("  ⚠️  No enhancements detected in either query")
    elif not baseline_enhancements and enhanced_enhancements:
        print("  ✅ PROOF: Enhanced query shows enhancements applied!")
        for enhancement in enhanced_enhancements:
            print(f"     • {enhancement}")
    else:
        print(f"  Baseline enhancements: {', '.join(baseline_enhancements) if baseline_enhancements else 'None'}")
        print(f"  Enhanced enhancements: {', '.join(enhanced_enhancements) if enhanced_enhancements else 'None'}")
    
    baseline_templates = baseline.get('matched_templates', [])
    enhanced_templates = enhanced.get('matched_templates', [])
    
    if not baseline_templates and enhanced_templates:
        print(f"")
        print(f"  ✅ PROOF: Enhanced query matched templates!")
        for template in enhanced_templates:
            print(f"     • Template: {template}")
    
    # Analyze answer differences
    print(f"\n📝 ANSWER QUALITY COMPARISON:")
    print(f"")
    
    baseline_answer = baseline.get('synthesis', '')
    enhanced_answer = enhanced.get('synthesis', '')
    
    # Word count
    baseline_words = len(baseline_answer.split())
    enhanced_words = len(enhanced_answer.split())
    
    print(f"  Baseline word count: {baseline_words}")
    print(f"  Enhanced word count: {enhanced_words}")
    
    # Check for specific terms that might indicate quality
    quality_indicators = [
        'architecture', 'design', 'implementation', 'testing',
        'pipeline', 'service', 'system', 'component'
    ]
    
    baseline_indicators = sum(1 for word in quality_indicators if word in baseline_answer.lower())
    enhanced_indicators = sum(1 for word in quality_indicators if word in enhanced_answer.lower())
    
    print(f"  Baseline quality keywords: {baseline_indicators}/{len(quality_indicators)}")
    print(f"  Enhanced quality keywords: {enhanced_indicators}/{len(quality_indicators)}")
    
    if enhanced_indicators > baseline_indicators:
        print(f"  ✅ Enhanced answer contains more quality keywords!")
    
    # Show side-by-side preview
    print(f"\n📄 ANSWER PREVIEW COMPARISON:")
    print(f"")
    print(f"{'BASELINE (first 400 chars)':^80}")
    print(f"{'-'*80}")
    print(f"{baseline_answer[:400]}...")
    print(f"")
    print(f"{'ENHANCED (first 400 chars)':^80}")
    print(f"{'-'*80}")
    print(f"{enhanced_answer[:400]}...")


def main():
    """
    Main comparison test.
    """
    print("\n" + "="*80)
    print("🎯 MULTI-PASS RAG ENHANCEMENT COMPARISON TEST")
    print("="*80)
    print("")
    print("This test will:")
    print("  1. Run a multi-pass query WITHOUT enhancements (baseline)")
    print("  2. Run the SAME query WITH enhancements")
    print("  3. Compare results to PROVE enhancements are working")
    print("")
    print("Query will target areas where enhancements should help:")
    print("  • Architecture (should match architecture template)")
    print("  • Testing (should match testing template)")
    print("  • Technical depth (should use glossary)")
    print("")
    input("Press Enter to start the test...")
    
    # Test query designed to trigger enhancements
    test_query = "Explain the architecture and testing strategy of the ecosystem-mcp service"
    
    # Run baseline (no enhancements)
    baseline_result = run_multipass_query(
        query=test_query,
        use_enhancements=False,
        label="BASELINE (No Enhancements)"
    )
    
    if not baseline_result:
        print("\n❌ Baseline query failed - cannot continue comparison")
        return
    
    # Wait a moment before second query
    print("\n⏳ Waiting 3 seconds before enhanced query...")
    time.sleep(3)
    
    # Run enhanced
    enhanced_result = run_multipass_query(
        query=test_query,
        use_enhancements=True,
        label="ENHANCED (With Enhancements)"
    )
    
    if not enhanced_result:
        print("\n❌ Enhanced query failed - cannot complete comparison")
        return
    
    # Compare results
    compare_results(baseline_result, enhanced_result)
    
    # Final verdict
    print(f"\n{'='*80}")
    print(f"🎯 FINAL VERDICT")
    print(f"{'='*80}")
    
    enhancements_detected = enhanced_result.get('enhancements_applied', [])
    templates_matched = enhanced_result.get('matched_templates', [])
    
    if enhancements_detected or templates_matched:
        print(f"✅ PROOF OF ENHANCEMENTS:")
        if enhancements_detected:
            print(f"   • {len(enhancements_detected)} enhancement(s) applied: {', '.join(enhancements_detected)}")
        if templates_matched:
            print(f"   • {len(templates_matched)} template(s) matched: {', '.join(templates_matched)}")
        print(f"")
        print(f"🎉 SUCCESS: Enhancements are WORKING and impacting RAG queries!")
    else:
        print(f"⚠️  WARNING: No enhancements detected in enhanced query")
        print(f"   This could mean:")
        print(f"   • Enhancements not triggering for this query")
        print(f"   • Metadata not being returned properly")
        print(f"   • Check configuration files")
    
    print(f"")


if __name__ == "__main__":
    main()

