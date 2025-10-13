#!/usr/bin/env python3
"""
Test 3-Tier LLM Routing System

Verifies:
1. Docker Ollama (Tier 3) - Simple queries
2. Desktop Ollama (Tier 2) - Heavy queries  
3. Cursor IDE (Tier 1) - Extreme complexity queries
4. MCP source citation

Checks routing decisions and verifies each tier is working.
"""

import asyncio
import httpx
import json
from datetime import datetime


class Color:
    """Terminal colors."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


async def check_tier_availability():
    """Check which tiers are available."""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.HEADER}🔍 CHECKING TIER AVAILABILITY{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}\n")
    
    base_url = "http://localhost:8000"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/api/v1/llm/status")
            status = response.json()
            
            print(f"{Color.CYAN}Routing System:{Color.END} {status.get('routing', 'unknown')}")
            print(f"{Color.CYAN}Complexity Threshold:{Color.END} {status.get('complexity_threshold', 'unknown')}\n")
            
            # Check each tier
            tiers = ['docker', 'desktop', 'cursor']
            results = {}
            
            for tier_name in tiers:
                tier_data = status.get(tier_name, {})
                tier_num = tier_data.get('tier', '?')
                enabled = tier_data.get('enabled', False)
                available = tier_data.get('available', False)
                model = tier_data.get('model', 'N/A')
                use_case = tier_data.get('use_case', 'N/A')
                
                results[tier_name] = available
                
                # Format output
                if available:
                    status_icon = f"{Color.GREEN}✅ AVAILABLE{Color.END}"
                elif enabled:
                    status_icon = f"{Color.YELLOW}⚠️  ENABLED BUT NOT AVAILABLE{Color.END}"
                else:
                    status_icon = f"{Color.RED}❌ DISABLED{Color.END}"
                
                print(f"{Color.BOLD}Tier {tier_num}: {tier_name.upper()}{Color.END}")
                print(f"  Status: {status_icon}")
                print(f"  Model: {model}")
                print(f"  Use Case: {use_case}")
                print()
            
            return results
    
    except Exception as e:
        print(f"{Color.RED}❌ Error checking status: {e}{Color.END}")
        return {}


async def test_simple_query():
    """Test Tier 3 (Docker) with simple query."""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.HEADER}🧪 TEST 1: SIMPLE QUERY (Should use Tier 3 - Docker){Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}\n")
    
    query = "What is 2 + 2?"
    
    print(f"{Color.CYAN}Query:{Color.END} {query}")
    print(f"{Color.CYAN}Expected Complexity:{Color.END} < 0.4 (SIMPLE)")
    print(f"{Color.CYAN}Expected Tier:{Color.END} Docker Ollama (CPU)\n")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            start_time = datetime.now()
            
            response = await client.post(
                "http://localhost:8000/api/v1/ask",
                json={
                    "question": query,
                    "n_results": 5
                }
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract routing info
                routing = result.get("_routing", {})
                complexity = routing.get("complexity", "unknown")
                instance = routing.get("instance", "unknown")
                model = routing.get("model", "unknown")
                
                print(f"{Color.GREEN}✅ SUCCESS{Color.END}")
                print(f"{Color.CYAN}Actual Complexity:{Color.END} {complexity}")
                print(f"{Color.CYAN}Routed To:{Color.END} {instance.upper()}")
                print(f"{Color.CYAN}Model Used:{Color.END} {model}")
                print(f"{Color.CYAN}Response Time:{Color.END} {elapsed:.2f}s")
                print(f"\n{Color.BOLD}Answer:{Color.END} {result.get('answer', 'N/A')[:200]}...")
                
                # Check sources
                sources = result.get("sources", [])
                if sources:
                    print(f"\n{Color.BOLD}Sources Cited ({len(sources)}):{Color.END}")
                    for i, source in enumerate(sources[:3], 1):
                        print(f"  {i}. {source.get('file_path', 'Unknown')} (score: {source.get('score', 0):.2f})")
                
                return instance == "docker"
            else:
                print(f"{Color.RED}❌ FAILED: HTTP {response.status_code}{Color.END}")
                print(f"{Color.RED}Response: {response.text[:200]}{Color.END}")
                return False
    
    except Exception as e:
        print(f"{Color.RED}❌ ERROR: {e}{Color.END}")
        return False


async def test_heavy_query():
    """Test Tier 2 (Desktop GPU) with heavy query."""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.HEADER}🧪 TEST 2: HEAVY QUERY (Should use Tier 2 - Desktop GPU){Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}\n")
    
    query = """Analyze the ecosystem-mcp service architecture and explain how the 
    3-tier routing system works. Include details about complexity analysis and 
    model selection."""
    
    print(f"{Color.CYAN}Query:{Color.END} {query[:100]}...")
    print(f"{Color.CYAN}Expected Complexity:{Color.END} 0.4-0.7 (HEAVY)")
    print(f"{Color.CYAN}Expected Tier:{Color.END} Desktop Ollama (GPU)\n")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            start_time = datetime.now()
            
            response = await client.post(
                "http://localhost:8000/api/v1/ask",
                json={
                    "question": query,
                    "n_results": 10
                }
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract routing info
                routing = result.get("_routing", {})
                complexity = routing.get("complexity", "unknown")
                instance = routing.get("instance", "unknown")
                model = routing.get("model", "unknown")
                
                print(f"{Color.GREEN}✅ SUCCESS{Color.END}")
                print(f"{Color.CYAN}Actual Complexity:{Color.END} {complexity}")
                print(f"{Color.CYAN}Routed To:{Color.END} {instance.upper()}")
                print(f"{Color.CYAN}Model Used:{Color.END} {model}")
                print(f"{Color.CYAN}Response Time:{Color.END} {elapsed:.2f}s")
                print(f"\n{Color.BOLD}Answer:{Color.END} {result.get('answer', 'N/A')[:300]}...")
                
                # Check sources
                sources = result.get("sources", [])
                if sources:
                    print(f"\n{Color.BOLD}Sources Cited ({len(sources)}):{Color.END}")
                    for i, source in enumerate(sources[:5], 1):
                        print(f"  {i}. {source.get('file_path', 'Unknown')} (score: {source.get('score', 0):.2f})")
                
                return instance == "desktop"
            else:
                print(f"{Color.RED}❌ FAILED: HTTP {response.status_code}{Color.END}")
                print(f"{Color.RED}Response: {response.text[:200]}{Color.END}")
                return False
    
    except Exception as e:
        print(f"{Color.RED}❌ ERROR: {e}{Color.END}")
        return False


async def test_extreme_query():
    """Test Tier 1 (Cursor) with extreme complexity query."""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.HEADER}🧪 TEST 3: EXTREME QUERY (Should use Tier 1 - Cursor IDE){Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}\n")
    
    query = """Analyze the entire ecosystem-mcp codebase across all commits, synthesize 
    the architectural evolution, compare it with the master refactoring plan, evaluate 
    the design decisions, and generate comprehensive recommendations for further 
    optimization. Include code examples, performance metrics, and strategic suggestions 
    for the next development phase."""
    
    print(f"{Color.CYAN}Query:{Color.END} {query[:100]}...")
    print(f"{Color.CYAN}Expected Complexity:{Color.END} > 0.7 (EXTREME)")
    print(f"{Color.CYAN}Expected Tier:{Color.END} Cursor IDE (Claude 4.5)\n")
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            start_time = datetime.now()
            
            response = await client.post(
                "http://localhost:8000/api/v1/ask",
                json={
                    "question": query,
                    "n_results": 15
                }
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract routing info
                routing = result.get("_routing", {})
                complexity = routing.get("complexity", "unknown")
                instance = routing.get("instance", "unknown")
                model = routing.get("model", "unknown")
                
                print(f"{Color.GREEN}✅ SUCCESS{Color.END}")
                print(f"{Color.CYAN}Actual Complexity:{Color.END} {complexity}")
                print(f"{Color.CYAN}Routed To:{Color.END} {instance.upper()}")
                print(f"{Color.CYAN}Model Used:{Color.END} {model}")
                print(f"{Color.CYAN}Response Time:{Color.END} {elapsed:.2f}s")
                print(f"\n{Color.BOLD}Answer:{Color.END} {result.get('answer', 'N/A')[:300]}...")
                
                # Check sources
                sources = result.get("sources", [])
                if sources:
                    print(f"\n{Color.BOLD}Sources Cited ({len(sources)}):{Color.END}")
                    for i, source in enumerate(sources[:5], 1):
                        print(f"  {i}. {source.get('file_path', 'Unknown')} (score: {source.get('score', 0):.2f})")
                
                return instance == "cursor"
            else:
                print(f"{Color.RED}❌ FAILED: HTTP {response.status_code}{Color.END}")
                print(f"{Color.RED}Response: {response.text[:200]}{Color.END}")
                return False
    
    except Exception as e:
        print(f"{Color.RED}❌ ERROR: {e}{Color.END}")
        return False


async def test_mcp_source_citation():
    """Test that MCP properly cites sources."""
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.HEADER}🧪 TEST 4: MCP SOURCE CITATION{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}\n")
    
    query = "What are the key features of ecosystem-mcp?"
    
    print(f"{Color.CYAN}Query:{Color.END} {query}\n")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:8000/api/v1/ask",
                json={
                    "question": query,
                    "n_results": 10
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                sources = result.get("sources", [])
                
                if sources:
                    print(f"{Color.GREEN}✅ MCP IS CITING SOURCES{Color.END}")
                    print(f"{Color.CYAN}Total Sources:{Color.END} {len(sources)}\n")
                    
                    print(f"{Color.BOLD}Source Details:{Color.END}")
                    for i, source in enumerate(sources, 1):
                        file_path = source.get('file_path', 'Unknown')
                        score = source.get('score', 0)
                        adjusted_score = source.get('adjusted_score', score)
                        snippet = source.get('content', '')[:100]
                        
                        print(f"\n{Color.BOLD}{i}. {file_path}{Color.END}")
                        print(f"   Similarity: {score:.3f} | Adjusted: {adjusted_score:.3f}")
                        print(f"   Snippet: {snippet}...")
                    
                    return True
                else:
                    print(f"{Color.YELLOW}⚠️  No sources cited (might not have ingested documents){Color.END}")
                    return False
            else:
                print(f"{Color.RED}❌ FAILED: HTTP {response.status_code}{Color.END}")
                return False
    
    except Exception as e:
        print(f"{Color.RED}❌ ERROR: {e}{Color.END}")
        return False


async def main():
    """Run all tests."""
    print(f"\n{Color.BOLD}{Color.HEADER}")
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "3-TIER LLM ROUTING VERIFICATION" + " "*32 + "║")
    print("╚" + "="*78 + "╝")
    print(f"{Color.END}\n")
    
    # Check availability
    availability = await check_tier_availability()
    
    # Run tests
    results = {
        "tier3_docker": None,
        "tier2_desktop": None,
        "tier1_cursor": None,
        "mcp_citation": None
    }
    
    # Test 1: Simple query (Docker)
    results["tier3_docker"] = await test_simple_query()
    
    # Test 2: Heavy query (Desktop)
    if availability.get("desktop"):
        results["tier2_desktop"] = await test_heavy_query()
    else:
        print(f"\n{Color.YELLOW}⏭️  SKIPPING Test 2: Desktop Ollama not available{Color.END}")
    
    # Test 3: Extreme query (Cursor)
    if availability.get("cursor"):
        results["tier1_cursor"] = await test_extreme_query()
    else:
        print(f"\n{Color.YELLOW}⏭️  SKIPPING Test 3: Cursor IDE not available{Color.END}")
    
    # Test 4: MCP citation
    results["mcp_citation"] = await test_mcp_source_citation()
    
    # Summary
    print(f"\n{Color.HEADER}{'='*80}{Color.END}")
    print(f"{Color.HEADER}📊 TEST SUMMARY{Color.END}")
    print(f"{Color.HEADER}{'='*80}{Color.END}\n")
    
    total_tests = 0
    passed_tests = 0
    
    for test_name, result in results.items():
        if result is not None:
            total_tests += 1
            if result:
                passed_tests += 1
                print(f"{Color.GREEN}✅ {test_name.replace('_', ' ').title()}: PASSED{Color.END}")
            else:
                print(f"{Color.RED}❌ {test_name.replace('_', ' ').title()}: FAILED{Color.END}")
        else:
            print(f"{Color.YELLOW}⏭️  {test_name.replace('_', ' ').title()}: SKIPPED{Color.END}")
    
    print(f"\n{Color.BOLD}Results: {passed_tests}/{total_tests} tests passed{Color.END}")
    
    if passed_tests == total_tests and total_tests > 0:
        print(f"\n{Color.GREEN}{Color.BOLD}🎉 ALL TESTS PASSED!{Color.END}")
    elif passed_tests > 0:
        print(f"\n{Color.YELLOW}{Color.BOLD}⚠️  SOME TESTS FAILED{Color.END}")
    else:
        print(f"\n{Color.RED}{Color.BOLD}❌ ALL TESTS FAILED{Color.END}")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())

