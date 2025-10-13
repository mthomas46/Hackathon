#!/usr/bin/env python3
"""
Test Multi-Pass Query System.

Tests the complex query decomposition and synthesis workflow.
"""

import httpx
import json
from datetime import datetime
import sys


def test_multi_pass_query(
    query: str = "How does the caching system work and what are the best practices?",
    num_passes: int = 3,
    num_secondary_questions: int = 3
):
    """Test multi-pass query processing."""
    
    query_request = {
        "query": query,
        "num_passes": num_passes,
        "num_secondary_questions": num_secondary_questions,
        "n_results": 10,
        "temperature": 0.7,
        "stream": False
    }
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║              🔬 MULTI-PASS QUERY SYSTEM TEST 🔬                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝\n")
    
    print(f"📝 Query: {query_request['query']}")
    print(f"⚙️  Configuration:")
    print(f"   • Passes (sections): {query_request['num_passes']}")
    print(f"   • Questions per section: {query_request['num_secondary_questions']}")
    print(f"   • Total questions: {query_request['num_passes'] * query_request['num_secondary_questions']}")
    print(f"   • Documents per question: {query_request['n_results']}")
    print(f"   • Temperature: {query_request['temperature']}")
    print(f"\n{'=' * 80}\n")
    
    start_time = datetime.now()
    
    try:
        print("🚀 Sending request to API...")
        print("⏳ This may take 30-120 seconds depending on configuration...\n")
        
        response = httpx.post(
            "http://localhost:8000/api/v1/query/multi-pass",
            json=query_request,
            timeout=900.0  # 15 minutes
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Multi-Pass Query Complete!")
            print(f"⏱️  Total Duration: {duration:.2f}s")
            print(f"\n{'=' * 80}\n")
            
            # Show sections
            print(f"📂 Sections Processed: {len(result['sections'])}\n")
            
            for section in result['sections']:
                print(f"  ┌─ Section {section['section_index'] + 1}: {section['section_name']}")
                print(f"  │  Description: {section['section_description'][:70]}...")
                print(f"  │  Questions: {len(section['questions'])}")
                print(f"  │  Synthesis Length: {len(section['synthesis'])} chars")
                print(f"  │  Duration: {section['duration_seconds']:.2f}s")
                print(f"  │")
                
                # Show questions
                for i, q in enumerate(section['questions'], 1):
                    print(f"  │  Q{i}: {q['question'][:60]}...")
                    print(f"  │      ➜ Answer: {len(q['answer'])} chars, "
                          f"Confidence: {q['confidence']:.2f}, "
                          f"Sources: {len(q['sources'])}")
                
                print(f"  │")
                print(f"  │  Section Synthesis Preview:")
                synthesis_preview = section['synthesis'][:200].replace('\n', '\n  │      ')
                print(f"  │      {synthesis_preview}...")
                print(f"  └{'─' * 70}\n")
            
            # Statistics
            print(f"{'=' * 80}\n")
            print(f"📊 Overall Statistics:")
            print(f"   • Total Questions Asked: {result['total_questions_asked']}")
            print(f"   • Total Sources Used: {result['total_sources_used']}")
            print(f"   • Total Duration: {result['total_duration_seconds']:.2f}s")
            print(f"   • Average per Question: {result['total_duration_seconds'] / result['total_questions_asked']:.2f}s")
            print(f"\n{'=' * 80}\n")
            
            # Final synthesis
            print(f"📝 Final Comprehensive Synthesis:\n")
            synthesis = result['final_synthesis']
            
            # Print with nice formatting
            lines = synthesis.split('\n')
            for line in lines[:20]:  # First 20 lines
                print(f"   {line}")
            
            if len(lines) > 20:
                print(f"\n   ... ({len(lines) - 20} more lines) ...")
            
            print(f"\n{'=' * 80}\n")
            
            # Save full result
            output_file = f"multi_pass_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"💾 Full result saved to: {output_file}")
            print(f"\n✅ Test completed successfully!")
            
            return result
            
        else:
            print(f"❌ Query failed: HTTP {response.status_code}")
            print(f"\n{response.text}")
            return None
    
    except httpx.TimeoutException:
        print(f"❌ Query timed out after {duration:.2f}s")
        print(f"   Try reducing num_passes or num_secondary_questions")
        return None
    
    except httpx.ConnectError:
        print(f"❌ Cannot connect to API at http://localhost:8000")
        print(f"   Make sure the service is running:")
        print(f"   docker compose up -d ecosystem-mcp")
        return None
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_quick_query():
    """Test with quick configuration."""
    print("\n🏃 Running QUICK test (2 passes × 2 questions = 4 total)...\n")
    return test_multi_pass_query(
        query="What is ChromaDB and how do we use it?",
        num_passes=2,
        num_secondary_questions=2
    )


def test_standard_query():
    """Test with standard configuration."""
    print("\n🚶 Running STANDARD test (3 passes × 3 questions = 9 total)...\n")
    return test_multi_pass_query(
        query="How does the caching system work and what are the best practices?",
        num_passes=3,
        num_secondary_questions=3
    )


def test_deep_query():
    """Test with deep configuration."""
    print("\n🔬 Running DEEP test (5 passes × 4 questions = 20 total)...\n")
    return test_multi_pass_query(
        query="Explain the complete RAG system architecture including retrieval, augmentation, and generation",
        num_passes=5,
        num_secondary_questions=4
    )


def main():
    """Main test runner."""
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == "quick":
            test_quick_query()
        elif test_type == "standard":
            test_standard_query()
        elif test_type == "deep":
            test_deep_query()
        elif test_type == "custom":
            if len(sys.argv) >= 5:
                query = sys.argv[2]
                num_passes = int(sys.argv[3])
                num_questions = int(sys.argv[4])
                test_multi_pass_query(query, num_passes, num_questions)
            else:
                print("Usage: python test_multi_pass.py custom 'YOUR QUERY' NUM_PASSES NUM_QUESTIONS")
        else:
            print(f"Unknown test type: {test_type}")
            print("Available: quick, standard, deep, custom")
    else:
        # Default: run standard test
        test_standard_query()


if __name__ == "__main__":
    main()

