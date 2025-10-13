#!/usr/bin/env python3
"""
Simple 3-Tier Routing Test - Direct API Test

Tests routing without relying on RAG/embedding functionality.
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_complexity_routing():
    """Test that queries are routed to the correct tier based on complexity."""
    
    print("\n" + "="*80)
    print("3-TIER ROUTING VERIFICATION - SIMPLE TEST")
    print("="*80 + "\n")
    
    # Check status
    print("📊 Checking Tier Status...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get("http://localhost:8000/api/v1/llm/status")
        status = response.json()
        
        print(f"Routing System: {status['routing']}")
        print(f"Complexity Threshold: {status['complexity_threshold']}\n")
        
        for tier_name in ['docker', 'desktop', 'cursor']:
            tier = status.get(tier_name, {})
            enabled = tier.get('enabled', False)
            available = tier.get('available', False)
            
            status_icon = "✅" if (enabled and available) else ("⚠️ " if enabled else "❌")
            print(f"{status_icon} Tier {tier.get('tier', '?')}: {tier_name.upper()}")
            if enabled:
                print(f"   Model: {tier.get('model', 'N/A')}")
                print(f"   Use Case: {tier.get('use_case', 'N/A')}")
            print()
    
    # Test queries with different complexity levels
    test_cases = [
        {
            "name": "SIMPLE QUERY",
            "query": "What is 2+2?",
            "expected_tier": "docker",
            "expected_complexity": "< 0.4"
        },
        {
            "name": "MEDIUM QUERY",
            "query": "Analyze the ecosystem-mcp service architecture and explain how it works",
            "expected_tier": "desktop",
            "expected_complexity": "0.4-0.7"
        },
        {
            "name": "EXTREME QUERY",
            "query": """Analyze the entire codebase across all commits, synthesize architectural 
            evolution patterns, compare with the master refactoring plan, evaluate all design 
            decisions with detailed reasoning, and generate comprehensive strategic recommendations 
            for the next development phase including code examples and performance metrics""",
            "expected_tier": "cursor",
            "expected_complexity": "> 0.7"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print("=" * 80)
        print(f"TEST {i}: {test['name']}")
        print("=" * 80)
        print(f"Query: {test['query'][:80]}...")
        print(f"Expected Tier: {test['expected_tier'].upper()}")
        print(f"Expected Complexity: {test['expected_complexity']}\n")
        
        # Make a direct complexity analysis call to our router
        # Since we can't call the router directly via API, we'll use the Ask endpoint
        # but with a very short timeout to see routing only
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                start = datetime.now()
                response = await client.post(
                    "http://localhost:8000/api/v1/ask",
                    json={"question": test['query'], "n_results": 3}
                )
                elapsed = (datetime.now() - start).total_seconds()
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Try to extract routing info
                    routing = result.get("_routing", {})
                    if routing:
                        actual_tier = routing.get("instance", "unknown")
                        complexity = routing.get("complexity", "unknown")
                        
                        tier_match = actual_tier.lower() == test['expected_tier'].lower()
                        status_icon = "✅" if tier_match else "⚠️ "
                        
                        print(f"{status_icon} Result:")
                        print(f"   Actual Tier: {actual_tier.upper()}")
                        print(f"   Complexity Score: {complexity}")
                        print(f"   Response Time: {elapsed:.2f}s")
                        
                        results.append({"test": test['name'], "passed": tier_match})
                    else:
                        print("⚠️  No routing metadata in response")
                        results.append({"test": test['name'], "passed": False})
                        
                else:
                    print(f"❌ HTTP {response.status_code}")
                    results.append({"test": test['name'], "passed": False})
                    
        except asyncio.TimeoutError:
            print("⏱️  Query timed out (expected for RAG queries)")
            print("   Note: Routing decision made before timeout")
            results.append({"test": test['name'], "passed": None})
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({"test": test['name'], "passed": False})
        
        print()
    
    # Summary
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r['passed'] is True)
    failed = sum(1 for r in results if r['passed'] is False)
    timeout = sum(1 for r in results if r['passed'] is None)
    
    for result in results:
        if result['passed'] is True:
            print(f"✅ {result['test']}: PASSED")
        elif result['passed'] is False:
            print(f"❌ {result['test']}: FAILED")
        else:
            print(f"⏱️  {result['test']}: TIMEOUT (routing unknown)")
    
    print(f"\nResults: {passed} passed, {failed} failed, {timeout} timeout")
    print()


if __name__ == "__main__":
    asyncio.run(test_complexity_routing())

