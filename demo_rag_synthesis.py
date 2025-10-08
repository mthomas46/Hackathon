#!/usr/bin/env python3
"""
Quick RAG Answer Synthesis Demonstration

Demonstrates:
1. Embedding generation
2. Semantic search
3. Hybrid search
4. RAG answer synthesis
"""

import asyncio
import httpx
import json
from typing import Dict, Any

class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


async def demo_rag():
    """Demonstrate RAG capabilities."""
    
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}  RAG (Retrieval-Augmented Generation) Demo{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    doc_store_url = "http://localhost:5087"  # Port from docker-compose
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Step 1: Check service health
        print(f"{Colors.BLUE}🔍 Step 1: Checking doc-store service...{Colors.RESET}")
        try:
            response = await client.get(f"{doc_store_url}/health")
            if response.status_code == 200:
                print(f"{Colors.GREEN}   ✓ Doc-store service is online{Colors.RESET}\n")
            else:
                print(f"{Colors.RED}   ✗ Doc-store returned {response.status_code}{Colors.RESET}\n")
                return
        except Exception as e:
            print(f"{Colors.RED}   ✗ Cannot connect to doc-store: {e}{Colors.RESET}\n")
            print(f"{Colors.YELLOW}   Make sure services are running: docker-compose up{Colors.RESET}\n")
            return
        
        # Step 2: Check embedding coverage
        print(f"{Colors.BLUE}📊 Step 2: Checking embedding coverage...{Colors.RESET}")
        try:
            response = await client.get(f"{doc_store_url}/api/v1/embeddings/stats")
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                total = data.get('total_documents', 0)
                vectorized = data.get('vectorized_documents', 0)
                coverage = data.get('coverage_percentage', 0)
                
                print(f"   • Total documents: {total}")
                print(f"   • Vectorized: {vectorized}")
                print(f"   • Coverage: {coverage:.1f}%")
                
                if vectorized == 0:
                    print(f"\n{Colors.YELLOW}   ⚠️  No embeddings found. Generating now...{Colors.RESET}\n")
                    
                    # Generate embeddings
                    response = await client.post(
                        f"{doc_store_url}/api/v1/embeddings/generate-batch",
                        params={"limit": 100}
                    )
                    if response.status_code == 200:
                        result = response.json()
                        data = result.get("data", {})
                        print(f"{Colors.GREEN}   ✓ Generated embeddings: {data.get('successful', 0)} successful{Colors.RESET}\n")
                    else:
                        print(f"{Colors.RED}   ✗ Embedding generation failed: {response.status_code}{Colors.RESET}\n")
                else:
                    print(f"{Colors.GREEN}   ✓ Embeddings ready!{Colors.RESET}\n")
            else:
                print(f"{Colors.YELLOW}   ⚠ Stats request returned {response.status_code}{Colors.RESET}\n")
        except Exception as e:
            print(f"{Colors.YELLOW}   ⚠ Could not check stats: {e}{Colors.RESET}\n")
        
        # Step 3: Semantic search demonstration
        print(f"{Colors.BLUE}🔎 Step 3: Demonstrating semantic search...{Colors.RESET}")
        test_query = "What is the Imperium of Man?"
        
        try:
            response = await client.post(
                f"{doc_store_url}/api/v1/search/semantic",
                params={"query": test_query, "limit": 3, "min_similarity": 0.3}
            )
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                results = data.get("results", [])
                
                print(f"   Query: '{test_query}'")
                print(f"   Results found: {len(results)}")
                
                if results:
                    for i, doc in enumerate(results[:3], 1):
                        similarity = doc.get("semantic_similarity", 0.0)
                        doc_id = doc.get("id", "unknown")
                        content_preview = doc.get("content", "")[:100]
                        print(f"\n   Result {i}:")
                        print(f"   • Similarity: {similarity:.3f}")
                        print(f"   • Document: {doc_id}")
                        print(f"   • Preview: {content_preview}...")
                    print(f"{Colors.GREEN}\n   ✓ Semantic search successful!{Colors.RESET}\n")
                else:
                    print(f"{Colors.YELLOW}   ⚠ No results found{Colors.RESET}\n")
            else:
                print(f"{Colors.YELLOW}   ⚠ Search returned {response.status_code}{Colors.RESET}\n")
        except Exception as e:
            print(f"{Colors.RED}   ✗ Semantic search failed: {e}{Colors.RESET}\n")
        
        # Step 4: Hybrid search demonstration
        print(f"{Colors.BLUE}🔀 Step 4: Demonstrating hybrid search...{Colors.RESET}")
        
        try:
            response = await client.post(
                f"{doc_store_url}/api/v1/search",
                json={"query": test_query, "limit": 3},
                params={"use_semantic": "true", "semantic_weight": "0.7"}
            )
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                search_mode = data.get("search_mode", "unknown")
                results = data.get("results", [])
                took_ms = data.get("took_ms", 0)
                
                print(f"   Query: '{test_query}'")
                print(f"   Mode: {search_mode}")
                print(f"   Results: {len(results)}")
                print(f"   Time: {took_ms:.1f}ms")
                
                if results:
                    top = results[0]
                    print(f"\n   Top result:")
                    print(f"   • Combined score: {top.get('score', 0.0):.3f}")
                    print(f"   • Semantic: {top.get('semantic_similarity', 0.0):.3f}")
                    print(f"   • Keyword: {top.get('keyword_score', 0.0):.3f}")
                    print(f"{Colors.GREEN}\n   ✓ Hybrid search successful!{Colors.RESET}\n")
                else:
                    print(f"{Colors.YELLOW}   ⚠ No results found{Colors.RESET}\n")
            else:
                print(f"{Colors.YELLOW}   ⚠ Search returned {response.status_code}{Colors.RESET}\n")
        except Exception as e:
            print(f"{Colors.RED}   ✗ Hybrid search failed: {e}{Colors.RESET}\n")
        
        # Step 5: RAG Answer Synthesis (THE MAIN EVENT!)
        print(f"{Colors.BOLD}{Colors.BLUE}🤖 Step 5: RAG Answer Synthesis{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
        
        rag_query = "What is the Horus Heresy and why is it significant?"
        
        print(f"{Colors.BOLD}Question:{Colors.RESET} {rag_query}\n")
        print(f"{Colors.YELLOW}Synthesizing answer (this may take 5-10 seconds)...{Colors.RESET}\n")
        
        try:
            response = await client.post(
                f"{doc_store_url}/api/v1/synthesis/generate",
                params={
                    "query": rag_query,
                    "semantic_weight": "0.7",
                    "temperature": "0.3",
                    "max_tokens": "500"
                },
                timeout=60.0  # RAG can take longer
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                answer = data.get("answer", "No answer generated")
                model = data.get("model", "unknown")
                method = data.get("synthesis_method", "unknown")
                sources = data.get("sources", [])
                search_meta = data.get("search_metadata", {})
                
                print(f"{Colors.GREEN}✓ RAG synthesis completed!{Colors.RESET}\n")
                print(f"{Colors.BOLD}{'─'*70}{Colors.RESET}")
                print(f"{Colors.BOLD}Answer:{Colors.RESET}\n")
                print(f"{answer}\n")
                print(f"{Colors.BOLD}{'─'*70}{Colors.RESET}\n")
                
                print(f"{Colors.BOLD}Metadata:{Colors.RESET}")
                print(f"   • Model: {model}")
                print(f"   • Method: {method}")
                print(f"   • Sources used: {len(sources)}")
                print(f"   • Documents found: {search_meta.get('documents_found', 0)}")
                print(f"   • Search time: {search_meta.get('search_time_ms', 0):.1f}ms")
                
                if sources:
                    print(f"\n{Colors.BOLD}Sources:{Colors.RESET}")
                    for i, source_id in enumerate(sources[:5], 1):
                        print(f"   {i}. {source_id}")
                
                # Save result
                output = {
                    "query": rag_query,
                    "answer": answer,
                    "model": model,
                    "sources": sources,
                    "method": method,
                    "search_metadata": search_meta
                }
                
                with open("rag_demo_result.json", 'w') as f:
                    json.dump(output, f, indent=2)
                
                print(f"\n{Colors.GREEN}✓ Result saved to: rag_demo_result.json{Colors.RESET}\n")
                
            else:
                print(f"{Colors.RED}✗ RAG synthesis failed: HTTP {response.status_code}{Colors.RESET}")
                print(f"   Response: {response.text[:200]}\n")
                
        except httpx.TimeoutException:
            print(f"{Colors.RED}✗ RAG synthesis timed out (may need more time){Colors.RESET}\n")
        except Exception as e:
            print(f"{Colors.RED}✗ RAG synthesis error: {e}{Colors.RESET}\n")
        
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}  Demo Complete!{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
        
        print(f"Key Takeaways:")
        print(f"  🔍 Semantic search understands meaning, not just keywords")
        print(f"  🔀 Hybrid search balances precision and recall")
        print(f"  🤖 RAG synthesizes answers from multiple sources")
        print(f"  ✅ All answers grounded in actual document content\n")


async def main():
    """Main entry point."""
    try:
        await demo_rag()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Demo interrupted by user{Colors.RESET}\n")
    except Exception as e:
        print(f"\n{Colors.RED}Demo error: {e}{Colors.RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())

