#!/usr/bin/env python3
"""
RAG Current System Benchmark

Tests the currently deployed RAG system (before Phase 1+2 enhancements).
This establishes a baseline for comparison once enhancements are deployed.
"""

import asyncio
import httpx
import json
from datetime import datetime
from pathlib import Path
import time


# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 120.0


# Test questions
TEST_QUESTIONS = [
    {"id": "Q1", "question": "What is an ingestion job?", "category": "simple"},
    {"id": "Q2", "question": "What is ChromaDB?", "category": "simple"},
    {"id": "Q3", "question": "Why is it slow?", "category": "vague"},
    {"id": "Q4", "question": "How does it work?", "category": "vague"},
    {"id": "Q5", "question": "How to fix ChromaDB connection error?", "category": "technical"},
    {"id": "Q6", "question": "What does the BM25 algorithm do?", "category": "technical"},
    {"id": "Q7", "question": "How does the ingestion worker process documents and what database does it use?", "category": "complex"},
    {"id": "Q8", "question": "What are the differences between semantic search and keyword search?", "category": "complex"},
    {"id": "Q9", "question": "How do I start the ingestion worker?", "category": "how_to"},
    {"id": "Q10", "question": "How to configure the RAG system for better accuracy?", "category": "how_to"},
]


class CurrentRAGBenchmark:
    """Benchmark current RAG system."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=TIMEOUT)
        self.results = []
        self.start_time = None
    
    async def close(self):
        await self.client.aclose()
    
    async def query_rag(self, question: str) -> dict:
        """Query current RAG system."""
        start = time.time()
        try:
            response = await self.client.post(
                "/ask",
                json={"question": question, "n_results": 10}
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                result = response.json()
                result["_meta"] = {
                    "elapsed_seconds": round(elapsed, 2),
                    "status": "success"
                }
                return result
            else:
                return {
                    "answer": "ERROR",
                    "sources": [],
                    "_meta": {"elapsed_seconds": round(elapsed, 2), "status": "error"}
                }
        except Exception as e:
            return {
                "answer": f"ERROR: {str(e)}",
                "sources": [],
                "_meta": {"elapsed_seconds": time.time() - start, "status": "error"}
            }
    
    async def run_benchmark(self):
        print("╔══════════════════════════════════════════════════════════════════════════════╗")
        print("║              CURRENT RAG SYSTEM BENCHMARK (Baseline)                        ║")
        print("╚══════════════════════════════════════════════════════════════════════════════╝")
        print()
        
        self.start_time = datetime.now()
        
        print("📊 Testing current RAG system (before Phase 1+2 enhancements)...")
        print()
        
        for idx, test_case in enumerate(TEST_QUESTIONS, 1):
            print(f"[{idx}/{len(TEST_QUESTIONS)}] {test_case['id']}: {test_case['question']}")
            print(f"     Category: {test_case['category']}")
            
            result = await self.query_rag(test_case['question'])
            
            self.results.append({
                "question_id": test_case["id"],
                "question": test_case["question"],
                "category": test_case["category"],
                "result": result
            })
            
            status = "✓" if result["_meta"]["status"] == "success" else "✗"
            time_str = f"({result['_meta']['elapsed_seconds']}s)"
            sources_count = len(result.get('sources', []))
            
            print(f"     {status} {time_str} - {sources_count} sources")
            print()
        
        print("✅ Benchmark complete!")
        print()
    
    def generate_report(self):
        """Generate baseline report."""
        report = []
        report.append("**Date:** " + self.start_time.strftime("%B %d, %Y"))
        report.append("**Status:** Current RAG System Benchmark (Baseline)")
        report.append("**Coverage:** Pre-Enhancement Baseline")
        report.append("")
        report.append("---")
        report.append("")
        report.append("# Current RAG System Benchmark Report")
        report.append("")
        report.append("## Overview")
        report.append("")
        report.append("This benchmark establishes a **baseline** for the current RAG system")
        report.append("**before** deploying Phase 1+2 accuracy enhancements.")
        report.append("")
        report.append(f"**Total Questions:** {len(TEST_QUESTIONS)}")
        report.append(f"**Timestamp:** {self.start_time.isoformat()}")
        report.append("")
        
        # Stats
        successful = sum(1 for r in self.results if r["result"]["_meta"]["status"] == "success")
        avg_time = sum(r["result"]["_meta"]["elapsed_seconds"] for r in self.results) / len(self.results)
        avg_sources = sum(len(r["result"].get("sources", [])) for r in self.results) / len(self.results)
        
        report.append("### System Performance")
        report.append("")
        report.append("| Metric | Value |")
        report.append("|--------|-------|")
        report.append(f"| Successful Queries | {successful}/{len(TEST_QUESTIONS)} ({successful/len(TEST_QUESTIONS)*100:.0f}%) |")
        report.append(f"| Avg Response Time | {avg_time:.2f}s |")
        report.append(f"| Avg Sources per Query | {avg_sources:.1f} |")
        report.append("")
        
        # By category
        categories = {}
        for r in self.results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)
        
        report.append("### Performance by Category")
        report.append("")
        report.append("| Category | Questions | Avg Time | Avg Sources |")
        report.append("|----------|-----------|----------|-------------|")
        
        for cat, cat_results in sorted(categories.items()):
            cat_time = sum(r["result"]["_meta"]["elapsed_seconds"] for r in cat_results) / len(cat_results)
            cat_sources = sum(len(r["result"].get("sources", [])) for r in cat_results) / len(cat_results)
            report.append(f"| {cat.capitalize()} | {len(cat_results)} | {cat_time:.2f}s | {cat_sources:.1f} |")
        
        report.append("")
        report.append("---")
        report.append("")
        
        # Detailed results
        report.append("## Detailed Results")
        report.append("")
        
        for r in self.results:
            q_id = r["question_id"]
            question = r["question"]
            category = r["category"]
            result = r["result"]
            
            report.append(f"### {q_id}: {question}")
            report.append("")
            report.append(f"**Category:** {category}")
            report.append(f"**Response Time:** {result['_meta']['elapsed_seconds']}s")
            report.append(f"**Sources:** {len(result.get('sources', []))}")
            report.append("")
            
            if result["_meta"]["status"] == "success":
                report.append("**Answer:**")
                answer = result.get('answer', 'N/A')
                report.append(f"> {answer[:400]}{'...' if len(answer) > 400 else ''}")
                report.append("")
                
                if result.get('sources'):
                    report.append("**Top Sources:**")
                    for i, source in enumerate(result['sources'][:5], 1):
                        report.append(f"{i}. `{source.get('file_path', 'Unknown')}` (score: {source.get('relevance_score', 0):.3f})")
                    report.append("")
            else:
                report.append("**Status:** ERROR")
                report.append("")
            
            report.append("---")
            report.append("")
        
        # Next steps
        report.append("## Next Steps")
        report.append("")
        report.append("### To Deploy Phase 1+2 Enhancements:")
        report.append("")
        report.append("```bash")
        report.append("# Deploy enhanced RAG system")
        report.append("./DEPLOY_RAG_ACCURACY_PHASE1.sh")
        report.append("")
        report.append("# Then run full comparison")
        report.append("python3 rag_comparison_benchmark.py")
        report.append("```")
        report.append("")
        report.append("### Expected Improvements:")
        report.append("")
        report.append("- **Overall Accuracy:** +35-55%")
        report.append("- **Vague Queries:** +35-50% (biggest gain)")
        report.append("- **Technical Queries:** +30-40%")
        report.append("- **Complex Queries:** +40-55%")
        report.append("- **Confidence Scores:** 0-100 with detailed breakdowns")
        report.append("- **Better Source Selection:** Quality-weighted ranking")
        report.append("- **Query Rewriting:** Automatic clarification of vague queries")
        report.append("")
        
        # Write report
        Path("rag_current_baseline_report.md").write_text("\n".join(report))
        print("📄 Baseline report: rag_current_baseline_report.md")
        
        # JSON export
        data = {
            "timestamp": self.start_time.isoformat(),
            "type": "baseline",
            "results": self.results
        }
        with open("rag_current_baseline_data.json", 'w') as f:
            json.dump(data, f, indent=2)
        print("💾 Baseline data: rag_current_baseline_data.json")


async def main():
    benchmark = CurrentRAGBenchmark()
    try:
        await benchmark.run_benchmark()
        benchmark.generate_report()
        
        print()
        print("=" * 80)
        print("BASELINE ESTABLISHED")
        print("=" * 80)
        print()
        print("✅ Current system baseline captured successfully!")
        print()
        print("📋 Next: Deploy Phase 1+2 enhancements to see improvements")
        print("   Run: ./DEPLOY_RAG_ACCURACY_PHASE1.sh")
        print()
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await benchmark.close()


if __name__ == "__main__":
    asyncio.run(main())

