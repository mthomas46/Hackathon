#!/usr/bin/env python3
"""
Test RAG (Ask) endpoint with intelligent answer generation.
"""

import httpx
import json
from datetime import datetime

client = httpx.Client(timeout=180.0)  # 3 minutes for LLM generation
base_url = "http://localhost:8000"

print("=" * 80)
print("🧪 TESTING RAG ENDPOINT")
print("=" * 80)

# Test 1: Check endpoint info
print("\n1. Testing /api/v1/ask/info...")
try:
    response = client.get(f"{base_url}/api/v1/ask/info")
    if response.status_code == 200:
        info = response.json()
        print("✅ RAG endpoint is available")
        print(f"   Features: {len(info.get('features', []))}")
        print(f"   Rate limit: {info.get('rate_limit')}")
    else:
        print(f"❌ Status: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Simple question
print("\n2. Testing simple question...")
question1 = "What is ecosystem-mcp and what are its main capabilities?"

try:
    print(f"   Question: {question1}")
    print("   Generating answer (this may take 10-30 seconds)...")
    
    response = client.post(
        f"{base_url}/api/v1/ask",
        json={
            "question": question1,
            "n_results": 10,
            "prefer_recent": True,
            "temperature": 0.7
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n✅ RAG Answer Generated!")
        print(f"\n📝 ANSWER ({len(result['answer'])} characters):")
        print("-" * 80)
        print(result['answer'])
        print("-" * 80)
        
        print(f"\n📚 SOURCES ({len(result['sources'])} documents):")
        for source in result['sources'][:5]:  # Show top 5
            print(f"  [{source['id']}] {source['file_path'][:60]}")
            print(f"      Relevance: {source['relevance_score']:.3f} → "
                  f"Adjusted: {source['adjusted_score']:.3f}")
            if source.get('recency_days') is not None:
                print(f"      Age: {source['recency_days']} days")
        
        print(f"\n🎯 CONFIDENCE: {result['confidence']:.1%}")
        print(f"\n📊 METADATA:")
        for key, value in result['metadata'].items():
            print(f"   {key}: {value}")
    else:
        print(f"❌ Status: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Version-aware question
print("\n" + "=" * 80)
print("3. Testing version-aware scoring...")
question2 = "What bugs were fixed in the ingestion worker?"

try:
    print(f"   Question: {question2}")
    print("   Generating answer...")
    
    response = client.post(
        f"{base_url}/api/v1/ask",
        json={
            "question": question2,
            "n_results": 8,
            "prefer_recent": True,  # Should boost recent fixes
            "temperature": 0.5  # More deterministic
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n✅ Answer Generated!")
        print(f"\n📝 ANSWER:")
        print("-" * 80)
        print(result['answer'][:500] + "..." if len(result['answer']) > 500 else result['answer'])
        print("-" * 80)
        
        print(f"\n📚 TOP 3 SOURCES:")
        for source in result['sources'][:3]:
            print(f"  [{source['id']}] {source['file_path']}")
            print(f"      Scores: {source['relevance_score']:.3f} → {source['adjusted_score']:.3f}")
            print(f"      Age: {source.get('recency_days', 'unknown')} days")
        
        print(f"\n🎯 CONFIDENCE: {result['confidence']:.1%}")
    else:
        print(f"❌ Status: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Conversational follow-up
print("\n" + "=" * 80)
print("4. Testing conversational context...")

try:
    # First question
    question_a = "What services are in the ecosystem?"
    print(f"   Question A: {question_a}")
    
    response_a = client.post(
        f"{base_url}/api/v1/ask",
        json={"question": question_a, "n_results": 5, "temperature": 0.7}
    )
    
    if response_a.status_code == 200:
        result_a = response_a.json()
        print(f"   Answer A: {result_a['answer'][:150]}...")
        
        # Follow-up question with context
        question_b = "Which ones handle data ingestion?"
        print(f"\n   Question B (follow-up): {question_b}")
        print("   Using previous answer as context...")
        
        response_b = client.post(
            f"{base_url}/api/v1/ask",
            json={
                "question": question_b,
                "n_results": 5,
                "temperature": 0.7,
                "context": [
                    {"question": question_a, "answer": result_a['answer']}
                ]
            }
        )
        
        if response_b.status_code == 200:
            result_b = response_b.json()
            print("\n✅ Follow-up Answer Generated!")
            print(f"\n📝 ANSWER:")
            print("-" * 80)
            print(result_b['answer'][:300] + "..." if len(result_b['answer']) > 300 else result_b['answer'])
            print("-" * 80)
            print(f"\n🎯 CONFIDENCE: {result_b['confidence']:.1%}")
        else:
            print(f"❌ Follow-up failed: {response_b.status_code}")
    else:
        print(f"❌ Initial question failed: {response_a.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("✅ RAG TESTING COMPLETE")
print("=" * 80)

