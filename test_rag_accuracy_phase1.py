#!/usr/bin/env python3
"""
RAG Accuracy Phase 1 Testing Script

Tests all Phase 1 enhancements:
1. Hybrid Search (semantic + keyword BM25)
2. Query Rewriting (synonym expansion + LLM clarification)
3. Confidence Scoring (multi-factor assessment)

Compares standard vs enhanced RAG to measure accuracy improvements.
"""

import asyncio
import httpx
import json
from typing import List, Dict, Any
from datetime import datetime
import sys

# API configuration
API_BASE_URL = "http://localhost:8001/api/v1"
TIMEOUT = 120.0


# Test queries (variety of difficulty levels)
TEST_QUERIES = [
    # Simple queries (should work well with both)
    {
        "question": "What is an ingestion job?",
        "category": "simple",
        "expected_topics": ["ingestion", "job", "document"]
    },
    {
        "question": "How do I start the ingestion worker?",
        "category": "simple",
        "expected_topics": ["worker", "start", "ingestion"]
    },
    
    # Vague queries (should benefit from query rewriting)
    {
        "question": "Why is it slow?",
        "category": "vague",
        "expected_topics": ["performance", "slow", "optimization"]
    },
    {
        "question": "How does it work?",
        "category": "vague",
        "expected_topics": ["architecture", "process", "system"]
    },
    
    # Technical queries (should benefit from keyword search)
    {
        "question": "What does the BM25 algorithm do?",
        "category": "technical",
        "expected_topics": ["bm25", "algorithm", "search"]
    },
    {
        "question": "How to fix ChromaDB error 500?",
        "category": "technical",
        "expected_topics": ["chromadb", "error", "500"]
    },
    
    # Complex queries (should benefit from all enhancements)
    {
        "question": "How does the ingestion worker process documents and what database does it use?",
        "category": "complex",
        "expected_topics": ["ingestion", "worker", "document", "database"]
    },
    {
        "question": "What are the differences between semantic search and keyword search and when should I use each?",
        "category": "complex",
        "expected_topics": ["semantic", "keyword", "search", "difference"]
    },
]


class RAGTester:
    """Test suite for RAG accuracy improvements."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=TIMEOUT)
        self.results = []
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def test_rag_health(self) -> Dict[str, Any]:
        """Test RAG system health."""
        print("🏥 Checking RAG system health...")
        
        try:
            response = await self.client.get("/rag/health")
            health = response.json()
            
            if health.get("healthy"):
                print("   ✅ RAG system healthy")
                print(f"   📊 BM25 Index: {'Built' if health['components']['bm25_index']['indexed'] else 'Not built'}")
                print(f"   📊 Index Size: {health['components']['bm25_index']['index_size']} documents")
            else:
                print("   ⚠️  RAG system unhealthy")
            
            return health
            
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            return {"healthy": False, "error": str(e)}
    
    async def test_single_query_standard(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single query with standard RAG."""
        try:
            response = await self.client.post(
                "/rag/ask/standard",
                json={
                    "question": query["question"],
                    "n_results": 10,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "answer": "ERROR"}
    
    async def test_single_query_enhanced(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single query with enhanced RAG."""
        try:
            response = await self.client.post(
                "/rag/ask/enhanced",
                json={
                    "question": query["question"],
                    "n_results": 10,
                    "temperature": 0.7,
                    "enable_hybrid_search": True,
                    "enable_query_rewriting": True,
                    "enable_confidence_scoring": True
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "answer": "ERROR"}
    
    async def test_query_comparison(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Compare standard vs enhanced for a single query."""
        print(f"\n📝 Testing: {query['question']}")
        print(f"   Category: {query['category']}")
        
        # Run both approaches
        standard_result = await self.test_single_query_standard(query)
        enhanced_result = await self.test_single_query_enhanced(query)
        
        # Analyze results
        standard_conf = standard_result.get("confidence", 0.0)
        enhanced_conf = enhanced_result.get("confidence", 0.0)
        
        improvement = enhanced_conf - standard_conf
        
        print(f"   📊 Standard Confidence: {standard_conf:.1f}%")
        print(f"   📊 Enhanced Confidence: {enhanced_conf:.1f}% ({'+' if improvement > 0 else ''}{improvement:.1f}%)")
        print(f"   📊 Confidence Level: {enhanced_result.get('confidence_level', 'Unknown')}")
        
        if enhanced_result.get("recommendation"):
            print(f"   💡 {enhanced_result['recommendation']}")
        
        result = {
            "query": query["question"],
            "category": query["category"],
            "standard": {
                "confidence": standard_conf,
                "answer_length": len(standard_result.get("answer", "")),
                "sources_count": len(standard_result.get("sources", []))
            },
            "enhanced": {
                "confidence": enhanced_conf,
                "confidence_level": enhanced_result.get("confidence_level"),
                "confidence_breakdown": enhanced_result.get("confidence_breakdown", {}),
                "answer_length": len(enhanced_result.get("answer", "")),
                "sources_count": len(enhanced_result.get("sources", [])),
                "enhancements_used": enhanced_result.get("metadata", {}).get("enhancements_used", {})
            },
            "improvement": improvement,
            "better": "enhanced" if improvement > 0 else "standard" if improvement < 0 else "tie"
        }
        
        self.results.append(result)
        return result
    
    async def run_all_tests(self):
        """Run all test queries."""
        print("\n" + "=" * 80)
        print("RAG ACCURACY PHASE 1 TESTING")
        print("=" * 80)
        
        # Check health first
        health = await self.test_rag_health()
        if not health.get("healthy"):
            print("\n⚠️  RAG system not healthy. Results may be unreliable.")
            print("   Try rebuilding BM25 index: POST /api/v1/rag/bm25/build-index")
        
        # Run all test queries
        print("\n" + "=" * 80)
        print("RUNNING TEST QUERIES")
        print("=" * 80)
        
        for query in TEST_QUERIES:
            try:
                await self.test_query_comparison(query)
            except Exception as e:
                print(f"   ❌ Test failed: {e}")
        
        # Generate summary
        self.print_summary()
    
    def print_summary(self):
        """Print summary of test results."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        if not self.results:
            print("No results to summarize.")
            return
        
        # Overall statistics
        total = len(self.results)
        enhanced_better = sum(1 for r in self.results if r["better"] == "enhanced")
        standard_better = sum(1 for r in self.results if r["better"] == "standard")
        tie = sum(1 for r in self.results if r["better"] == "tie")
        
        avg_standard_conf = sum(r["standard"]["confidence"] for r in self.results) / total
        avg_enhanced_conf = sum(r["enhanced"]["confidence"] for r in self.results) / total
        avg_improvement = avg_enhanced_conf - avg_standard_conf
        
        print(f"\n📊 Overall Statistics:")
        print(f"   Total Queries: {total}")
        print(f"   Enhanced Better: {enhanced_better} ({enhanced_better/total*100:.1f}%)")
        print(f"   Standard Better: {standard_better} ({standard_better/total*100:.1f}%)")
        print(f"   Tie: {tie} ({tie/total*100:.1f}%)")
        print(f"\n   Avg Standard Confidence: {avg_standard_conf:.1f}%")
        print(f"   Avg Enhanced Confidence: {avg_enhanced_conf:.1f}%")
        print(f"   Avg Improvement: {'+' if avg_improvement > 0 else ''}{avg_improvement:.1f}%")
        
        # By category
        print(f"\n📊 By Category:")
        for category in ["simple", "vague", "technical", "complex"]:
            cat_results = [r for r in self.results if r["category"] == category]
            if cat_results:
                cat_avg_imp = sum(r["improvement"] for r in cat_results) / len(cat_results)
                print(f"   {category.capitalize()}: {'+' if cat_avg_imp > 0 else ''}{cat_avg_imp:.1f}% improvement")
        
        # Confidence levels
        print(f"\n📊 Confidence Levels (Enhanced):")
        levels = {}
        for r in self.results:
            level = r["enhanced"].get("confidence_level", "Unknown")
            levels[level] = levels.get(level, 0) + 1
        
        for level, count in sorted(levels.items(), key=lambda x: x[1], reverse=True):
            print(f"   {level}: {count} ({count/total*100:.1f}%)")
        
        # Best improvements
        print(f"\n🏆 Top Improvements:")
        sorted_results = sorted(self.results, key=lambda x: x["improvement"], reverse=True)
        for i, r in enumerate(sorted_results[:3], 1):
            print(f"   {i}. {r['query'][:60]}...")
            print(f"      Improvement: +{r['improvement']:.1f}% ({r['standard']['confidence']:.1f}% → {r['enhanced']['confidence']:.1f}%)")
        
        # Worst performance
        if any(r["improvement"] < 0 for r in self.results):
            print(f"\n⚠️  Cases Where Standard Was Better:")
            for r in [r for r in self.results if r["improvement"] < 0]:
                print(f"   - {r['query'][:60]}...")
                print(f"     Change: {r['improvement']:.1f}% ({r['standard']['confidence']:.1f}% → {r['enhanced']['confidence']:.1f}%)")
        
        # Overall verdict
        print("\n" + "=" * 80)
        print("VERDICT")
        print("=" * 80)
        
        if avg_improvement >= 20:
            verdict = "🎉 EXCELLENT! Phase 1 improvements are highly effective."
        elif avg_improvement >= 10:
            verdict = "✅ GOOD! Phase 1 improvements show solid gains."
        elif avg_improvement >= 5:
            verdict = "👍 MODERATE! Phase 1 improvements help somewhat."
        elif avg_improvement >= 0:
            verdict = "⚠️  MARGINAL! Phase 1 improvements have minimal impact."
        else:
            verdict = "❌ NEGATIVE! Enhanced RAG is performing worse. Check configuration."
        
        print(f"\n{verdict}")
        print(f"Expected: +25-35% accuracy improvement")
        print(f"Actual: {'+' if avg_improvement > 0 else ''}{avg_improvement:.1f}% confidence improvement")
        
        if avg_improvement < 10:
            print("\n💡 Suggestions:")
            print("   - Ensure BM25 index is fully built")
            print("   - Check if ChromaDB has sufficient documents")
            print("   - Try rebuilding embeddings")
            print("   - Review query rewriting effectiveness")
    
    def save_results(self, filename: str = "rag_phase1_test_results.json"):
        """Save results to JSON file."""
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.results,
                "summary": {
                    "total": len(self.results),
                    "enhanced_better": sum(1 for r in self.results if r["better"] == "enhanced"),
                    "avg_improvement": sum(r["improvement"] for r in self.results) / len(self.results) if self.results else 0
                }
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")


async def main():
    """Main test execution."""
    tester = RAGTester()
    
    try:
        await tester.run_all_tests()
        tester.save_results()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.close()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   RAG ACCURACY PHASE 1 TEST SUITE                           ║
║                                                                              ║
║  Tests all Phase 1 improvements:                                            ║
║  • Hybrid Search (semantic + keyword BM25)                                  ║
║  • Query Rewriting (synonym expansion + LLM clarification)                  ║
║  • Confidence Scoring (multi-factor assessment)                             ║
║                                                                              ║
║  Expected: +25-35% accuracy improvement                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())

