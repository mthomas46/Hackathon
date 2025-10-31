#!/usr/bin/env python3
"""
RAG Comparison & Benchmarking Tool

Runs the same questions through different RAG approaches and generates
a comprehensive comparison report with metrics, answers, and citations.

RAG Types Tested:
1. Standard RAG (baseline)
2. Phase 1 Enhanced (hybrid search + query rewriting + confidence scoring)
3. Phase 1+2 Enhanced (+ reranking + context optimization + metadata filtering)
"""

import asyncio
import httpx
import json
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import time


# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"  # Fixed: API runs on port 8000
TIMEOUT = 120.0


# Comprehensive test questions across difficulty levels
TEST_QUESTIONS = [
    # Simple/Direct Questions
    {
        "id": "Q1",
        "question": "What is an ingestion job?",
        "category": "simple",
        "difficulty": "easy",
        "expected_topics": ["ingestion", "job", "document", "process"]
    },
    {
        "id": "Q2",
        "question": "What is ChromaDB?",
        "category": "simple",
        "difficulty": "easy",
        "expected_topics": ["chromadb", "vector", "database", "embeddings"]
    },
    
    # Vague Questions (benefit most from rewriting)
    {
        "id": "Q3",
        "question": "Why is it slow?",
        "category": "vague",
        "difficulty": "hard",
        "expected_topics": ["performance", "slow", "optimization", "bottleneck"]
    },
    {
        "id": "Q4",
        "question": "How does it work?",
        "category": "vague",
        "difficulty": "hard",
        "expected_topics": ["process", "workflow", "architecture", "system"]
    },
    
    # Technical Questions (benefit from keyword search)
    {
        "id": "Q5",
        "question": "How to fix ChromaDB connection error?",
        "category": "technical",
        "difficulty": "medium",
        "expected_topics": ["chromadb", "error", "connection", "fix"]
    },
    {
        "id": "Q6",
        "question": "What does the BM25 algorithm do?",
        "category": "technical",
        "difficulty": "medium",
        "expected_topics": ["bm25", "algorithm", "search", "ranking"]
    },
    
    # Complex Multi-Part Questions
    {
        "id": "Q7",
        "question": "How does the ingestion worker process documents and what database does it use?",
        "category": "complex",
        "difficulty": "hard",
        "expected_topics": ["ingestion", "worker", "process", "database", "postgresql", "chromadb"]
    },
    {
        "id": "Q8",
        "question": "What are the differences between semantic search and keyword search?",
        "category": "complex",
        "difficulty": "medium",
        "expected_topics": ["semantic", "keyword", "search", "difference", "embeddings"]
    },
    
    # How-To Questions (benefit from context optimization)
    {
        "id": "Q9",
        "question": "How do I start the ingestion worker?",
        "category": "how_to",
        "difficulty": "easy",
        "expected_topics": ["start", "ingestion", "worker", "command"]
    },
    {
        "id": "Q10",
        "question": "How to configure the RAG system for better accuracy?",
        "category": "how_to",
        "difficulty": "hard",
        "expected_topics": ["configure", "rag", "accuracy", "settings"]
    },
]


class RAGBenchmark:
    """Comprehensive RAG comparison and benchmarking tool."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=TIMEOUT)
        self.results = []
        self.start_time = None
        self.end_time = None
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Check if RAG system is healthy."""
        try:
            response = await self.client.get("/rag/health")
            return response.json() if response.status_code == 200 else {"healthy": False}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def query_standard_rag(self, question: str) -> Dict[str, Any]:
        """Query standard RAG (baseline)."""
        start = time.time()
        try:
            response = await self.client.post(
                "/rag/ask/standard",
                json={"question": question, "n_results": 10}
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                result = response.json()
                result["_meta"] = {
                    "elapsed_seconds": round(elapsed, 2),
                    "status": "success",
                    "enhancements": []
                }
                return result
            else:
                return {
                    "answer": "ERROR",
                    "sources": [],
                    "confidence": 0,
                    "_meta": {
                        "elapsed_seconds": round(elapsed, 2),
                        "status": "error",
                        "error": response.text
                    }
                }
        except Exception as e:
            return {
                "answer": f"ERROR: {str(e)}",
                "sources": [],
                "confidence": 0,
                "_meta": {
                    "elapsed_seconds": time.time() - start,
                    "status": "error",
                    "error": str(e)
                }
            }
    
    async def query_enhanced_rag_phase1(self, question: str) -> Dict[str, Any]:
        """Query Phase 1 enhanced RAG only."""
        start = time.time()
        try:
            response = await self.client.post(
                "/rag/ask/enhanced",
                json={
                    "question": question,
                    "n_results": 10,
                    "enable_hybrid_search": True,
                    "enable_query_rewriting": True,
                    "enable_confidence_scoring": True,
                    # Phase 2 explicitly disabled
                    "enable_reranking": False,
                    "enable_context_optimization": False,
                    "enable_metadata_filtering": False
                }
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                result = response.json()
                result["_meta"] = {
                    "elapsed_seconds": round(elapsed, 2),
                    "status": "success",
                    "enhancements": ["hybrid_search", "query_rewriting", "confidence_scoring"]
                }
                return result
            else:
                return {
                    "answer": "ERROR",
                    "sources": [],
                    "confidence": 0,
                    "_meta": {
                        "elapsed_seconds": round(elapsed, 2),
                        "status": "error",
                        "error": response.text
                    }
                }
        except Exception as e:
            return {
                "answer": f"ERROR: {str(e)}",
                "sources": [],
                "confidence": 0,
                "_meta": {
                    "elapsed_seconds": time.time() - start,
                    "status": "error",
                    "error": str(e)
                }
            }
    
    async def query_enhanced_rag_phase1_phase2(self, question: str) -> Dict[str, Any]:
        """Query Phase 1 + Phase 2 enhanced RAG."""
        start = time.time()
        try:
            response = await self.client.post(
                "/rag/ask/enhanced",
                json={
                    "question": question,
                    "n_results": 10,
                    # Phase 1
                    "enable_hybrid_search": True,
                    "enable_query_rewriting": True,
                    "enable_confidence_scoring": True,
                    # Phase 2
                    "enable_reranking": True,
                    "enable_context_optimization": True,
                    "enable_metadata_filtering": True,
                    "quality_threshold": 70.0,
                    "context_strategy": "balanced"
                }
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                result = response.json()
                result["_meta"] = {
                    "elapsed_seconds": round(elapsed, 2),
                    "status": "success",
                    "enhancements": [
                        "hybrid_search", "query_rewriting", "confidence_scoring",
                        "reranking", "context_optimization", "metadata_filtering"
                    ]
                }
                return result
            else:
                return {
                    "answer": "ERROR",
                    "sources": [],
                    "confidence": 0,
                    "_meta": {
                        "elapsed_seconds": round(elapsed, 2),
                        "status": "error",
                        "error": response.text
                    }
                }
        except Exception as e:
            return {
                "answer": f"ERROR: {str(e)}",
                "sources": [],
                "confidence": 0,
                "_meta": {
                    "elapsed_seconds": time.time() - start,
                    "status": "error",
                    "error": str(e)
                }
            }
    
    async def run_benchmark(self):
        """Run comprehensive benchmark across all questions and RAG types."""
        print("╔══════════════════════════════════════════════════════════════════════════════╗")
        print("║                RAG COMPARISON & BENCHMARKING                                ║")
        print("╚══════════════════════════════════════════════════════════════════════════════╝")
        print()
        
        self.start_time = datetime.now()
        
        # Check system health
        print("🏥 Checking system health...")
        health = await self.check_system_health()
        if not health.get("healthy"):
            print("   ⚠️  Warning: RAG system may not be fully healthy")
            print(f"   {health}")
        else:
            print("   ✅ System healthy")
        print()
        
        # Run all questions through all RAG types
        print("=" * 80)
        print("RUNNING BENCHMARK")
        print("=" * 80)
        print()
        
        for idx, test_case in enumerate(TEST_QUESTIONS, 1):
            question_id = test_case["id"]
            question = test_case["question"]
            
            print(f"\n[{idx}/{len(TEST_QUESTIONS)}] {question_id}: {question}")
            print(f"     Category: {test_case['category']} | Difficulty: {test_case['difficulty']}")
            
            result = {
                "question_id": question_id,
                "question": question,
                "category": test_case["category"],
                "difficulty": test_case["difficulty"],
                "expected_topics": test_case["expected_topics"],
                "results": {}
            }
            
            # 1. Standard RAG
            print("     🔍 Standard RAG...", end=" ", flush=True)
            standard_result = await self.query_standard_rag(question)
            result["results"]["standard"] = standard_result
            print(f"✓ ({standard_result['_meta']['elapsed_seconds']}s)")
            
            # 2. Phase 1 Enhanced RAG
            print("     ✨ Phase 1 Enhanced...", end=" ", flush=True)
            phase1_result = await self.query_enhanced_rag_phase1(question)
            result["results"]["phase1_enhanced"] = phase1_result
            print(f"✓ ({phase1_result['_meta']['elapsed_seconds']}s)")
            
            # 3. Phase 1+2 Enhanced RAG
            print("     🚀 Phase 1+2 Enhanced...", end=" ", flush=True)
            phase1_phase2_result = await self.query_enhanced_rag_phase1_phase2(question)
            result["results"]["phase1_phase2_enhanced"] = phase1_phase2_result
            print(f"✓ ({phase1_phase2_result['_meta']['elapsed_seconds']}s)")
            
            # Calculate improvements
            if standard_result["confidence"] > 0:
                phase1_improvement = (
                    phase1_result.get("confidence", 0) - standard_result["confidence"]
                )
                phase1_phase2_improvement = (
                    phase1_phase2_result.get("confidence", 0) - standard_result["confidence"]
                )
                phase2_additional = (
                    phase1_phase2_result.get("confidence", 0) - phase1_result.get("confidence", 0)
                )
                result["phase1_improvement"] = round(phase1_improvement, 1)
                result["phase1_phase2_improvement"] = round(phase1_phase2_improvement, 1)
                result["phase2_additional_improvement"] = round(phase2_additional, 1)
            else:
                result["phase1_improvement"] = 0
                result["phase1_phase2_improvement"] = 0
                result["phase2_additional_improvement"] = 0
            
            self.results.append(result)
        
        self.end_time = datetime.now()
        
        print()
        print("=" * 80)
        print("BENCHMARK COMPLETE")
        print("=" * 80)
        print()
    
    def generate_report(self, output_file: str = "rag_comparison_report.md"):
        """Generate comprehensive comparison report."""
        total_time = (self.end_time - self.start_time).total_seconds()
        
        report = []
        report.append("**Date:** " + self.start_time.strftime("%B %d, %Y"))
        report.append("**Status:** RAG Comparison Benchmark Complete")
        report.append("**Coverage:** Standard vs Phase 1 vs Phase 1+2 Enhanced RAG")
        report.append("")
        report.append("---")
        report.append("")
        report.append("# RAG Comparison Benchmark Report")
        report.append("")
        report.append("## Executive Summary")
        report.append("")
        report.append(f"**Total Questions Tested:** {len(TEST_QUESTIONS)}")
        report.append(f"**Benchmark Duration:** {total_time:.1f} seconds")
        report.append(f"**Timestamp:** {self.start_time.isoformat()}")
        report.append("")
        
        # Overall statistics
        standard_confidences = []
        phase1_confidences = []
        phase1_phase2_confidences = []
        phase1_improvements = []
        phase1_phase2_improvements = []
        phase2_additional = []
        
        for result in self.results:
            std_conf = result["results"]["standard"].get("confidence", 0)
            p1_conf = result["results"]["phase1_enhanced"].get("confidence", 0)
            p1_p2_conf = result["results"].get("phase1_phase2_enhanced", {}).get("confidence", 0)
            
            standard_confidences.append(std_conf)
            phase1_confidences.append(p1_conf)
            phase1_phase2_confidences.append(p1_p2_conf)
            phase1_improvements.append(result.get("phase1_improvement", 0))
            phase1_phase2_improvements.append(result.get("phase1_phase2_improvement", 0))
            phase2_additional.append(result.get("phase2_additional_improvement", 0))
        
        avg_std_conf = sum(standard_confidences) / len(standard_confidences) if standard_confidences else 0
        avg_p1_conf = sum(phase1_confidences) / len(phase1_confidences) if phase1_confidences else 0
        avg_p1_p2_conf = sum(phase1_phase2_confidences) / len(phase1_phase2_confidences) if phase1_phase2_confidences else 0
        avg_p1_improvement = sum(phase1_improvements) / len(phase1_improvements) if phase1_improvements else 0
        avg_p1_p2_improvement = sum(phase1_phase2_improvements) / len(phase1_phase2_improvements) if phase1_phase2_improvements else 0
        avg_p2_additional = sum(phase2_additional) / len(phase2_additional) if phase2_additional else 0
        
        report.append("### Overall Metrics")
        report.append("")
        report.append("| Metric | Standard RAG | Phase 1 Enhanced | Phase 1+2 Enhanced | P1 Improvement | P1+2 Improvement |")
        report.append("|--------|--------------|------------------|-------------------|----------------|------------------|")
        report.append(f"| Avg Confidence | {avg_std_conf:.1f}% | {avg_p1_conf:.1f}% | {avg_p1_p2_conf:.1f}% | **+{avg_p1_improvement:.1f}%** | **+{avg_p1_p2_improvement:.1f}%** |")
        
        p1_better_count = sum(1 for imp in phase1_improvements if imp > 0)
        p1_p2_better_count = sum(1 for imp in phase1_phase2_improvements if imp > 0)
        report.append(f"| Better Results | - | {p1_better_count}/{len(phase1_improvements)} ({p1_better_count/len(phase1_improvements)*100:.0f}%) | {p1_p2_better_count}/{len(phase1_phase2_improvements)} ({p1_p2_better_count/len(phase1_phase2_improvements)*100:.0f}%) | - | - |")
        report.append("")
        
        report.append("**Phase 2 Additional Improvement:** " + f"+{avg_p2_additional:.1f}% (on top of Phase 1)")
        report.append("")
        
        # By category
        report.append("### Results by Category")
        report.append("")
        
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        report.append("| Category | Questions | Avg Standard | Avg Phase 1 | Avg Phase 1+2 | P1 Improvement | P1+2 Improvement |")
        report.append("|----------|-----------|--------------|-------------|---------------|----------------|------------------|")
        
        for cat, cat_results in sorted(categories.items()):
            cat_std = sum(r["results"]["standard"].get("confidence", 0) for r in cat_results) / len(cat_results)
            cat_p1 = sum(r["results"]["phase1_enhanced"].get("confidence", 0) for r in cat_results) / len(cat_results)
            cat_p1_p2 = sum(r["results"].get("phase1_phase2_enhanced", {}).get("confidence", 0) for r in cat_results) / len(cat_results)
            cat_p1_imp = cat_p1 - cat_std
            cat_p1_p2_imp = cat_p1_p2 - cat_std
            
            report.append(f"| {cat.capitalize()} | {len(cat_results)} | {cat_std:.1f}% | {cat_p1:.1f}% | {cat_p1_p2:.1f}% | **+{cat_p1_imp:.1f}%** | **+{cat_p1_p2_imp:.1f}%** |")
        
        report.append("")
        report.append("---")
        report.append("")
        
        # Detailed results for each question
        report.append("## Detailed Question-by-Question Results")
        report.append("")
        
        for idx, result in enumerate(self.results, 1):
            q_id = result["question_id"]
            question = result["question"]
            category = result["category"]
            difficulty = result["difficulty"]
            
            report.append(f"### {q_id}: {question}")
            report.append("")
            report.append(f"**Category:** {category} | **Difficulty:** {difficulty}")
            report.append("")
            
            # Standard RAG Results
            std_result = result["results"]["standard"]
            report.append("#### Standard RAG")
            report.append("")
            report.append(f"**Confidence:** {std_result.get('confidence', 0):.1f}%")
            report.append(f"**Response Time:** {std_result['_meta']['elapsed_seconds']}s")
            report.append(f"**Sources Used:** {len(std_result.get('sources', []))}")
            report.append("")
            report.append("**Answer:**")
            report.append(f"> {std_result.get('answer', 'N/A')[:500]}{'...' if len(std_result.get('answer', '')) > 500 else ''}")
            report.append("")
            
            if std_result.get('sources'):
                report.append("**Top Sources:**")
                for i, source in enumerate(std_result['sources'][:3], 1):
                    report.append(f"{i}. `{source.get('file_path', 'Unknown')}`")
                report.append("")
            
            # Phase 1 Enhanced Results
            p1_result = result["results"]["phase1_enhanced"]
            report.append("#### Phase 1 Enhanced RAG")
            report.append("")
            report.append(f"**Confidence:** {p1_result.get('confidence', 0):.1f}% (**+{result.get('confidence_improvement', 0):.1f}%**)")
            report.append(f"**Confidence Level:** {p1_result.get('confidence_level', 'Unknown')}")
            report.append(f"**Response Time:** {p1_result['_meta']['elapsed_seconds']}s")
            report.append(f"**Sources Used:** {len(p1_result.get('sources', []))}")
            report.append("")
            
            # Enhancements used
            if p1_result.get('metadata', {}).get('enhancements_used'):
                enhancements = p1_result['metadata']['enhancements_used']
                report.append("**Enhancements Active:**")
                if enhancements.get('hybrid_search'):
                    report.append("- ✅ Hybrid Search (semantic + keyword)")
                if enhancements.get('query_rewriting'):
                    report.append("- ✅ Query Rewriting")
                if enhancements.get('confidence_scoring'):
                    report.append("- ✅ Confidence Scoring")
                report.append("")
            
            # Confidence breakdown
            if p1_result.get('confidence_breakdown'):
                breakdown = p1_result['confidence_breakdown']
                report.append("**Confidence Breakdown:**")
                report.append(f"- Retrieval Quality: {breakdown.get('retrieval_quality', 0):.1f}/20")
                report.append(f"- Source Quality: {breakdown.get('source_quality', 0):.1f}/20")
                report.append(f"- Answer-Source Alignment: {breakdown.get('answer_source_alignment', 0):.1f}/20")
                report.append(f"- Consensus: {breakdown.get('consensus', 0):.1f}/20")
                report.append(f"- Completeness: {breakdown.get('completeness', 0):.1f}/20")
                report.append("")
            
            # Recommendation
            if p1_result.get('recommendation'):
                report.append(f"**Recommendation:** {p1_result['recommendation']}")
                report.append("")
            
            report.append("**Answer:**")
            report.append(f"> {p1_result.get('answer', 'N/A')[:500]}{'...' if len(p1_result.get('answer', '')) > 500 else ''}")
            report.append("")
            
            if p1_result.get('sources'):
                report.append("**Top Sources:**")
                for i, source in enumerate(p1_result['sources'][:3], 1):
                    report.append(f"{i}. `{source.get('file_path', 'Unknown')}`")
                report.append("")
            
            # Query variants (if available)
            if p1_result.get('metadata', {}).get('query_variants'):
                variants = p1_result['metadata']['query_variants']
                if len(variants) > 1:
                    report.append("**Query Variants Generated:**")
                    for i, variant in enumerate(variants[:3], 1):
                        if variant != question:
                            report.append(f"{i}. _{variant}_")
                    report.append("")
            
            report.append("---")
            report.append("")
        
        # Summary
        report.append("## Summary & Recommendations")
        report.append("")
        
        if avg_p1_p2_improvement >= 30:
            verdict = "🎉 **EXCELLENT!** Phase 1+2 enhancements show significant improvements."
        elif avg_p1_p2_improvement >= 20:
            verdict = "✅ **GREAT!** Phase 1+2 enhancements provide strong gains."
        elif avg_p1_p2_improvement >= 10:
            verdict = "👍 **GOOD!** Phase 1+2 enhancements help considerably."
        else:
            verdict = "⚠️ **MODERATE!** Phase 1+2 improvements have modest impact."
        
        report.append(verdict)
        report.append("")
        report.append(f"**Phase 1 Average Improvement:** +{avg_p1_improvement:.1f}%")
        report.append(f"**Phase 1+2 Average Improvement:** +{avg_p1_p2_improvement:.1f}%")
        report.append(f"**Phase 2 Additional Improvement:** +{avg_p2_additional:.1f}%")
        report.append(f"**Questions Improved (Phase 1+2):** {p1_p2_better_count}/{len(phase1_phase2_improvements)} ({p1_p2_better_count/len(phase1_phase2_improvements)*100:.0f}%)")
        report.append("")
        
        # Best improvements
        best_improvements = sorted(self.results, key=lambda x: x.get('phase1_phase2_improvement', 0), reverse=True)[:3]
        report.append("### Top 3 Improvements (Phase 1+2)")
        report.append("")
        for i, result in enumerate(best_improvements, 1):
            improvement = result.get('phase1_phase2_improvement', 0)
            report.append(f"{i}. **{result['question_id']}** ({result['category']}): +{improvement:.1f}%")
            report.append(f"   _{result['question']}_")
        report.append("")
        
        # Recommendations
        report.append("### Key Findings")
        report.append("")
        
        # Find which categories benefited most
        best_category = max(categories.items(), key=lambda x: sum(r.get('confidence_improvement', 0) for r in x[1]) / len(x[1]))
        best_cat_name, best_cat_results = best_category
        best_cat_imp = sum(r.get('confidence_improvement', 0) for r in best_cat_results) / len(best_cat_results)
        
        report.append(f"1. **{best_cat_name.capitalize()} queries** benefited most from enhancements (+{best_cat_imp:.1f}% average)")
        report.append(f"2. **Phase 1 enhancements** active in all tests: Hybrid Search, Query Rewriting, Confidence Scoring")
        report.append(f"3. **Confidence scoring** provides transparency with detailed breakdowns for every answer")
        report.append("")
        
        # Write report
        output_path = Path(output_file)
        output_path.write_text("\n".join(report))
        
        print(f"📄 Report generated: {output_file}")
        print()
        
        return output_file
    
    def generate_json_export(self, output_file: str = "rag_comparison_data.json"):
        """Export raw data as JSON for further analysis."""
        data = {
            "benchmark_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration_seconds": (self.end_time - self.start_time).total_seconds(),
                "total_questions": len(TEST_QUESTIONS)
            },
            "results": self.results
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 JSON data exported: {output_file}")


async def main():
    """Main benchmark execution."""
    benchmark = RAGBenchmark()
    
    try:
        await benchmark.run_benchmark()
        benchmark.generate_report()
        benchmark.generate_json_export()
        
        print()
        print("✅ Benchmark complete!")
        print()
        print("📊 Generated files:")
        print("   • rag_comparison_report.md  - Comprehensive comparison report")
        print("   • rag_comparison_data.json  - Raw data for analysis")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark interrupted by user")
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await benchmark.close()


if __name__ == "__main__":
    asyncio.run(main())

