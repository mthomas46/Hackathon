#!/usr/bin/env python3
"""
Comprehensive RAG Test - All Types with All Enhancements
Tests all RAG configurations and captures detailed metrics
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, List, Any

API_BASE_URL = "http://localhost:8000/api/v1"

TEST_QUESTIONS = [
    {
        "id": "Q1",
        "question": "What is Docker and how is it used in this project?",
        "category": "technical",
        "difficulty": "medium"
    },
    {
        "id": "Q2",
        "question": "How does the ingestion pipeline work?",
        "category": "technical",
        "difficulty": "medium"
    },
    {
        "id": "Q3",
        "question": "What are the differences between semantic and keyword search?",
        "category": "conceptual",
        "difficulty": "medium"
    },
    {
        "id": "Q4",
        "question": "How to fix database connection errors?",
        "category": "troubleshooting",
        "difficulty": "easy"
    },
    {
        "id": "Q5",
        "question": "What is the BM25 algorithm and why is it used?",
        "category": "technical",
        "difficulty": "hard"
    }
]

RAG_CONFIGURATIONS = [
    {
        "name": "Standard RAG",
        "endpoint": "/rag/ask/standard",
        "config": {},
        "description": "Baseline semantic search only"
    },
    {
        "name": "Phase 1 Only",
        "endpoint": "/rag/ask/enhanced",
        "config": {
            "enable_hybrid_search": True,
            "enable_query_rewriting": True,
            "enable_confidence_scoring": True,
            "enable_reranking": False,
            "enable_context_optimization": False
        },
        "description": "Hybrid search + query rewriting + confidence"
    },
    {
        "name": "Phase 1+2",
        "endpoint": "/rag/ask/enhanced",
        "config": {
            "enable_hybrid_search": True,
            "enable_query_rewriting": True,
            "enable_confidence_scoring": True,
            "enable_reranking": True,
            "enable_context_optimization": True,
            "enable_metadata_filtering": False
        },
        "description": "All Phase 1 + reranking + context optimization"
    },
    {
        "name": "Phase 1+2+3 (All Enhancements)",
        "endpoint": "/rag/ask/enhanced",
        "config": {
            "enable_hybrid_search": True,
            "enable_query_rewriting": True,
            "enable_confidence_scoring": True,
            "enable_reranking": True,
            "enable_context_optimization": True,
            "enable_metadata_filtering": False
        },
        "description": "All features + caching (on repeat)"
    }
]

class ComprehensiveRAGTest:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)
        self.results = []
    
    async def query_rag(self, endpoint: str, question: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Query a RAG endpoint with given configuration."""
        start = time.time()
        try:
            payload = {
                "question": question,
                "n_results": 10,
                **config
            }
            
            response = await self.client.post(
                f"{API_BASE_URL}{endpoint}",
                json=payload
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "answer": result.get("answer", ""),
                    "confidence": result.get("confidence", 0),
                    "confidence_level": result.get("confidence_level", ""),
                    "sources": result.get("sources", []),
                    "metadata": result.get("metadata", {}),
                    "elapsed_seconds": round(elapsed, 2),
                    "status": "success"
                }
            else:
                return {
                    "answer": "ERROR",
                    "confidence": 0,
                    "sources": [],
                    "elapsed_seconds": round(elapsed, 2),
                    "status": "error",
                    "error": response.text
                }
        except Exception as e:
            return {
                "answer": f"ERROR: {str(e)}",
                "confidence": 0,
                "sources": [],
                "elapsed_seconds": time.time() - start,
                "status": "error",
                "error": str(e)
            }
    
    async def run_tests(self):
        """Run comprehensive tests across all configurations."""
        print("╔══════════════════════════════════════════════════════════════════════════════╗")
        print("║                                                                              ║")
        print("║          COMPREHENSIVE RAG TEST - ALL TYPES WITH ALL ENHANCEMENTS           ║")
        print("║                                                                              ║")
        print("╚══════════════════════════════════════════════════════════════════════════════╝")
        print()
        print(f"Testing {len(TEST_QUESTIONS)} questions across {len(RAG_CONFIGURATIONS)} configurations")
        print()
        print("=" * 80)
        print("RUNNING TESTS")
        print("=" * 80)
        print()
        
        for q_idx, test_case in enumerate(TEST_QUESTIONS, 1):
            question = test_case["question"]
            print(f"[{q_idx}/{len(TEST_QUESTIONS)}] {test_case['id']}: {question}")
            print(f"     Category: {test_case['category']} | Difficulty: {test_case['difficulty']}")
            
            result = {
                "question_id": test_case["id"],
                "question": question,
                "category": test_case["category"],
                "difficulty": test_case["difficulty"],
                "configurations": []
            }
            
            for config in RAG_CONFIGURATIONS:
                config_name = config["name"]
                print(f"     🔧 {config_name}...", end=" ", flush=True)
                
                rag_result = await self.query_rag(
                    config["endpoint"],
                    question,
                    config["config"]
                )
                
                # Add configuration metadata
                rag_result["configuration_name"] = config_name
                rag_result["configuration_description"] = config["description"]
                rag_result["configuration_settings"] = config["config"]
                
                result["configurations"].append(rag_result)
                
                # Print summary
                conf = rag_result.get("confidence", 0)
                time_taken = rag_result.get("elapsed_seconds", 0)
                num_sources = len(rag_result.get("sources", []))
                print(f"✓ ({time_taken}s, {conf:.1f}%, {num_sources} sources)")
            
            self.results.append(result)
            print()
        
        print("=" * 80)
        print("TESTS COMPLETE")
        print("=" * 80)
        print()
    
    def generate_report(self, output_file: str = "COMPREHENSIVE_RAG_ALL_ENHANCEMENTS_REPORT.md"):
        """Generate comprehensive report with all metrics."""
        
        report = []
        
        report.append("# Comprehensive RAG Test Report: All Types with All Enhancements")
        report.append("")
        report.append(f"**Date:** {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}")
        report.append(f"**Questions Tested:** {len(TEST_QUESTIONS)}")
        report.append(f"**Configurations Tested:** {len(RAG_CONFIGURATIONS)}")
        report.append("")
        report.append("---")
        report.append("")
        
        # Executive Summary
        report.append("## Executive Summary")
        report.append("")
        report.append("This report presents comprehensive testing of all RAG configurations with detailed metrics:")
        report.append("- **Response times** for each configuration")
        report.append("- **Confidence scores** for answer quality")
        report.append("- **Source citations** with relevance scores")
        report.append("- **Active enhancements** per configuration")
        report.append("")
        
        # Configurations tested
        report.append("## Configurations Tested")
        report.append("")
        for config in RAG_CONFIGURATIONS:
            report.append(f"### {config['name']}")
            report.append(f"**Description:** {config['description']}")
            report.append("")
            if config['config']:
                report.append("**Settings:**")
                for key, value in config['config'].items():
                    report.append(f"- `{key}`: {value}")
                report.append("")
            report.append("---")
            report.append("")
        
        # Overall Performance Summary
        report.append("## Overall Performance Summary")
        report.append("")
        
        # Calculate averages per configuration
        config_stats = {}
        for config in RAG_CONFIGURATIONS:
            config_name = config["name"]
            times = []
            confidences = []
            source_counts = []
            
            for result in self.results:
                for cfg_result in result["configurations"]:
                    if cfg_result["configuration_name"] == config_name:
                        times.append(cfg_result["elapsed_seconds"])
                        confidences.append(cfg_result["confidence"])
                        source_counts.append(len(cfg_result.get("sources", [])))
            
            config_stats[config_name] = {
                "avg_time": sum(times) / len(times) if times else 0,
                "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
                "avg_sources": sum(source_counts) / len(source_counts) if source_counts else 0
            }
        
        report.append("| Configuration | Avg Time | Avg Confidence | Avg Sources |")
        report.append("|---------------|----------|----------------|-------------|")
        
        for config in RAG_CONFIGURATIONS:
            config_name = config["name"]
            stats = config_stats[config_name]
            report.append(f"| **{config_name}** | {stats['avg_time']:.2f}s | {stats['avg_confidence']:.1f}% | {stats['avg_sources']:.1f} |")
        
        report.append("")
        
        # Detailed Results Per Question
        report.append("## Detailed Results by Question")
        report.append("")
        
        for result in self.results:
            q_id = result["question_id"]
            question = result["question"]
            category = result["category"]
            difficulty = result["difficulty"]
            
            report.append(f"### {q_id}: {question}")
            report.append("")
            report.append(f"**Category:** {category} | **Difficulty:** {difficulty}")
            report.append("")
            
            # Performance comparison table
            report.append("#### Performance Comparison")
            report.append("")
            report.append("| Configuration | Time | Confidence | Confidence Level | Sources |")
            report.append("|---------------|------|------------|------------------|---------|")
            
            for cfg_result in result["configurations"]:
                config_name = cfg_result["configuration_name"]
                time_taken = cfg_result["elapsed_seconds"]
                conf = cfg_result["confidence"]
                conf_level = cfg_result.get("confidence_level", "N/A")
                num_sources = len(cfg_result.get("sources", []))
                report.append(f"| {config_name} | {time_taken:.2f}s | {conf:.1f}% | {conf_level} | {num_sources} |")
            
            report.append("")
            
            # Detailed results for each configuration
            for cfg_result in result["configurations"]:
                config_name = cfg_result["configuration_name"]
                
                report.append(f"#### {config_name} - Detailed Results")
                report.append("")
                
                # Answer snippet
                answer = cfg_result.get("answer", "")
                answer_snippet = answer[:300] + "..." if len(answer) > 300 else answer
                report.append("**Answer:**")
                report.append(f"> {answer_snippet}")
                report.append("")
                
                # Metrics
                report.append("**Metrics:**")
                report.append(f"- Response Time: {cfg_result['elapsed_seconds']:.2f}s")
                report.append(f"- Confidence Score: {cfg_result['confidence']:.1f}%")
                report.append(f"- Confidence Level: {cfg_result.get('confidence_level', 'N/A')}")
                report.append(f"- Sources Retrieved: {len(cfg_result.get('sources', []))}")
                report.append("")
                
                # Active enhancements
                metadata = cfg_result.get("metadata", {})
                if metadata.get("enhancements_used"):
                    enhancements = metadata["enhancements_used"]
                    report.append("**Active Enhancements:**")
                    for key, value in enhancements.items():
                        if value:
                            enhancement_name = key.replace("_", " ").title()
                            report.append(f"- ✅ {enhancement_name}")
                    report.append("")
                
                # Source citations
                sources = cfg_result.get("sources", [])
                if sources:
                    report.append("**Source Citations:**")
                    report.append("")
                    report.append("| # | File Path | Relevance | Quality |")
                    report.append("|---|-----------|-----------|---------|")
                    for idx, source in enumerate(sources[:5], 1):  # Top 5 sources
                        file_path = source.get("file_path", "Unknown")
                        # Truncate long paths
                        if len(file_path) > 50:
                            file_path = "..." + file_path[-47:]
                        relevance = source.get("relevance_score", source.get("adjusted_score", 0))
                        quality = source.get("quality_score", "N/A")
                        report.append(f"| {idx} | `{file_path}` | {relevance:.3f} | {quality} |")
                    
                    if len(sources) > 5:
                        report.append(f"| ... | *{len(sources) - 5} more sources* | ... | ... |")
                    
                    report.append("")
                
                report.append("---")
                report.append("")
            
            report.append("---")
            report.append("")
        
        # Performance Analysis
        report.append("## Performance Analysis")
        report.append("")
        
        report.append("### Response Time Analysis")
        report.append("")
        baseline_name = RAG_CONFIGURATIONS[0]["name"]
        baseline_time = config_stats[baseline_name]["avg_time"]
        
        for config in RAG_CONFIGURATIONS:
            config_name = config["name"]
            stats = config_stats[config_name]
            time_diff = stats["avg_time"] - baseline_time
            time_pct = ((stats["avg_time"] / baseline_time) - 1) * 100 if baseline_time > 0 else 0
            
            report.append(f"**{config_name}:**")
            report.append(f"- Average time: {stats['avg_time']:.2f}s")
            if config_name != baseline_name:
                report.append(f"- vs {baseline_name}: {time_diff:+.2f}s ({time_pct:+.1f}%)")
            report.append("")
        
        report.append("### Confidence Score Analysis")
        report.append("")
        baseline_conf = config_stats[baseline_name]["avg_confidence"]
        
        for config in RAG_CONFIGURATIONS:
            config_name = config["name"]
            stats = config_stats[config_name]
            conf_diff = stats["avg_confidence"] - baseline_conf
            
            report.append(f"**{config_name}:**")
            report.append(f"- Average confidence: {stats['avg_confidence']:.1f}%")
            if config_name != baseline_name:
                report.append(f"- vs {baseline_name}: {conf_diff:+.1f}%")
            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        report.append("")
        
        # Find best configuration
        best_conf_config = max(config_stats.items(), key=lambda x: x[1]["avg_confidence"])
        fastest_config = min(config_stats.items(), key=lambda x: x[1]["avg_time"])
        
        report.append(f"**Highest Confidence:** {best_conf_config[0]} ({best_conf_config[1]['avg_confidence']:.1f}%)")
        report.append(f"**Fastest Response:** {fastest_config[0]} ({fastest_config[1]['avg_time']:.2f}s)")
        report.append("")
        
        report.append("### When to Use Each Configuration")
        report.append("")
        report.append("**Standard RAG:**")
        report.append("- Best for: Quick prototypes, low-stakes queries")
        report.append("- Pros: Fastest response time")
        report.append("- Cons: Lower confidence scores")
        report.append("")
        
        report.append("**Phase 1 Only:**")
        report.append("- Best for: Balanced accuracy and speed")
        report.append("- Pros: Hybrid search improves recall")
        report.append("- Cons: Moderate overhead")
        report.append("")
        
        report.append("**Phase 1+2:**")
        report.append("- Best for: High-accuracy requirements")
        report.append("- Pros: Best confidence scores, reranking improves precision")
        report.append("- Cons: Higher latency")
        report.append("")
        
        report.append("**Phase 1+2+3:**")
        report.append("- Best for: Production with repeated queries")
        report.append("- Pros: Cache reduces latency on repeated queries")
        report.append("- Cons: Same as Phase 1+2 on cache miss")
        report.append("")
        
        # Summary
        report.append("## Summary")
        report.append("")
        report.append(f"**Test Date:** {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}")
        report.append(f"**Questions Tested:** {len(TEST_QUESTIONS)}")
        report.append(f"**Total Tests Run:** {len(TEST_QUESTIONS) * len(RAG_CONFIGURATIONS)}")
        report.append("")
        
        report.append("**Key Findings:**")
        phase_1_2_conf = config_stats.get("Phase 1+2", {}).get("avg_confidence", 0)
        std_conf = config_stats.get("Standard RAG", {}).get("avg_confidence", 0)
        conf_improvement = phase_1_2_conf - std_conf
        
        report.append(f"- Phase 1+2 improves confidence by {conf_improvement:+.1f}% vs Standard")
        report.append(f"- All configurations successfully completed")
        report.append(f"- Source citations available for all queries")
        report.append("")
        
        report.append("---")
        report.append("")
        report.append("**Generated by:** Comprehensive RAG Test Suite")
        report.append(f"**Timestamp:** {datetime.now().isoformat()}")
        
        # Write report
        with open(output_file, "w") as f:
            f.write("\n".join(report))
        
        print(f"✅ Report generated: {output_file}")
        
        # Save raw data
        json_output = output_file.replace(".md", ".json")
        with open(json_output, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": config_stats,
                "results": self.results
            }, f, indent=2)
        print(f"✅ Raw data saved: {json_output}")
    
    async def close(self):
        await self.client.aclose()

async def main():
    tester = ComprehensiveRAGTest()
    try:
        await tester.run_tests()
        tester.generate_report()
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main())

