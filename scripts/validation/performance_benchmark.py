"""Performance Benchmarking Script

Benchmarks the performance of key components before and after the DDD refactor
to ensure the architectural changes haven't introduced performance regressions.
"""

import time
import asyncio
import psutil
import os
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from statistics import mean, median, stdev
import tracemalloc
import gc


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    operation: str
    iterations: int
    total_time: float
    avg_time: float
    median_time: float
    min_time: float
    max_time: float
    memory_usage_mb: float
    cpu_percent: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation": self.operation,
            "iterations": self.iterations,
            "total_time": self.total_time,
            "avg_time": self.avg_time,
            "median_time": self.median_time,
            "min_time": self.min_time,
            "max_time": self.max_time,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_percent": self.cpu_percent
        }


class PerformanceBenchmarker:
    """Comprehensive performance benchmarking suite."""

    def __init__(self):
        """Initialize benchmarker."""
        self.process = psutil.Process()
        self.results = []

    def run_full_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive performance benchmarks."""
        print("🚀 Starting Performance Benchmark Suite")
        print("=" * 50)

        # Benchmark key operations
        benchmarks = [
            ("semantic_similarity", self._benchmark_semantic_similarity),
            ("sentiment_analysis", self._benchmark_sentiment_analysis),
            ("risk_assessment", self._benchmark_risk_assessment),
            ("maintenance_forecast", self._benchmark_maintenance_forecast),
            ("quality_degradation", self._benchmark_quality_degradation),
            ("cross_repository", self._benchmark_cross_repository),
            ("distributed_processing", self._benchmark_distributed_processing),
            ("memory_usage", self._benchmark_memory_usage),
            ("import_performance", self._benchmark_import_performance)
        ]

        results = []
        for name, benchmark_func in benchmarks:
            print(f"\n📊 Benchmarking: {name}")
            try:
                result = benchmark_func()
                results.append(result)
                print(".3f")
            except Exception as e:
                print(f"❌ Failed: {e}")
                results.append({
                    "operation": name,
                    "error": str(e),
                    "status": "failed"
                })

        # Calculate summary statistics
        successful_results = [r for r in results if isinstance(r, BenchmarkResult)]
        summary = self._calculate_summary_stats(successful_results)

        final_result = {
            "summary": summary,
            "detailed_results": [r.to_dict() if isinstance(r, BenchmarkResult) else r for r in results],
            "system_info": self._get_system_info(),
            "benchmark_timestamp": time.time()
        }

        print("\n📈 BENCHMARK SUMMARY:")
        print(".1f")
        print(f"   Best Performance: {summary['best_operation']}")
        print(f"   Memory Usage: {summary['avg_memory_mb']:.1f} MB")
        print(".1f")

        return final_result

    def _benchmark_semantic_similarity(self) -> BenchmarkResult:
        """Benchmark semantic similarity analysis."""
        try:
            from services.analysis_service.modules.semantic_analyzer import SemanticAnalyzer

            analyzer = SemanticAnalyzer()
            test_texts = [
                "This is a test document about API design",
                "This document discusses REST API patterns",
                "Here we talk about database architecture",
                "This covers microservices design principles"
            ]

            return self._run_benchmark(
                "semantic_similarity",
                lambda: analyzer.calculate_similarity(test_texts[0], test_texts[1]),
                iterations=50
            )
        except Exception as e:
            raise Exception(f"Semantic analyzer benchmark failed: {e}")

    def _benchmark_sentiment_analysis(self) -> BenchmarkResult:
        """Benchmark sentiment analysis."""
        try:
            from services.analysis_service.modules.sentiment_analyzer import SentimentAnalyzer

            analyzer = SentimentAnalyzer()
            test_text = "This documentation is excellent and very helpful for developers."

            return self._run_benchmark(
                "sentiment_analysis",
                lambda: analyzer.analyze_sentiment(test_text),
                iterations=100
            )
        except Exception as e:
            raise Exception(f"Sentiment analyzer benchmark failed: {e}")

    def _benchmark_risk_assessment(self) -> BenchmarkResult:
        """Benchmark risk assessment."""
        try:
            from services.analysis_service.modules.risk_assessor import RiskAssessor

            assessor = RiskAssessor()
            test_data = {
                "document_age": 365,
                "complexity_score": 0.7,
                "quality_score": 0.8,
                "change_frequency": 12
            }

            return self._run_benchmark(
                "risk_assessment",
                lambda: assessor._assess_individual_risks(test_data),
                iterations=50
            )
        except Exception as e:
            raise Exception(f"Risk assessment benchmark failed: {e}")

    def _benchmark_maintenance_forecast(self) -> BenchmarkResult:
        """Benchmark maintenance forecasting."""
        try:
            from services.analysis_service.modules.maintenance_forecaster import MaintenanceForecaster

            forecaster = MaintenanceForecaster()
            test_data = {
                "document_age": 180,
                "quality_score": 0.75,
                "usage_frequency": 25
            }

            return self._run_benchmark(
                "maintenance_forecast",
                lambda: forecaster._forecast_maintenance_schedule(test_data),
                iterations=30
            )
        except Exception as e:
            raise Exception(f"Maintenance forecast benchmark failed: {e}")

    def _benchmark_quality_degradation(self) -> BenchmarkResult:
        """Benchmark quality degradation detection."""
        try:
            from services.analysis_service.modules.quality_degradation_detector import QualityDegradationDetector

            detector = QualityDegradationDetector()
            test_history = [
                {"quality_score": 0.9, "timestamp": time.time() - i * 86400}
                for i in range(10)
            ]

            return self._run_benchmark(
                "quality_degradation",
                lambda: detector._calculate_trend_analysis(pd.Series([h["quality_score"] for h in test_history])),
                iterations=20
            )
        except Exception as e:
            raise Exception(f"Quality degradation benchmark failed: {e}")

    def _benchmark_cross_repository(self) -> BenchmarkResult:
        """Benchmark cross-repository analysis."""
        try:
            from services.analysis_service.modules.cross_repository_analyzer import CrossRepositoryAnalyzer

            analyzer = CrossRepositoryAnalyzer()
            test_repos = [
                {"repo_id": "repo1", "name": "test-repo-1", "url": "https://github.com/test/repo1"},
                {"repo_id": "repo2", "name": "test-repo-2", "url": "https://github.com/test/repo2"}
            ]

            return self._run_benchmark(
                "cross_repository",
                lambda: asyncio.run(analyzer.analyze_repositories(test_repos)),
                iterations=5
            )
        except Exception as e:
            raise Exception(f"Cross-repository benchmark failed: {e}")

    def _benchmark_distributed_processing(self) -> BenchmarkResult:
        """Benchmark distributed processing."""
        try:
            from services.analysis_service.modules.distributed_processor import DistributedProcessor

            processor = DistributedProcessor()
            test_task = {
                "task_type": "analysis",
                "payload": {"data": "test"},
                "priority": "normal"
            }

            return self._run_benchmark(
                "distributed_processing",
                lambda: asyncio.run(processor.submit_task(test_task)),
                iterations=10
            )
        except Exception as e:
            raise Exception(f"Distributed processing benchmark failed: {e}")

    def _benchmark_memory_usage(self) -> BenchmarkResult:
        """Benchmark memory usage patterns."""
        try:
            # Force garbage collection
            gc.collect()

            # Measure baseline memory
            tracemalloc.start()
            baseline_snapshot = tracemalloc.take_snapshot()

            # Perform memory-intensive operations
            large_data = []
            for i in range(1000):
                large_data.append({"data": "x" * 1000, "metadata": {"id": i, "complex": [j for j in range(100)]}})

            # Process the data
            processed = []
            for item in large_data:
                processed.append({
                    "id": item["metadata"]["id"],
                    "size": len(item["data"]),
                    "complexity": len(item["metadata"]["complex"])
                })

            # Measure memory usage
            current_snapshot = tracemalloc.take_snapshot()
            tracemalloc.stop()

            # Calculate memory difference
            stats = current_snapshot.compare_to(baseline_snapshot, 'lineno')
            total_memory = sum(stat.size_diff for stat in stats[:10])  # Top 10 memory users

            return BenchmarkResult(
                operation="memory_usage",
                iterations=1,
                total_time=0.0,
                avg_time=0.0,
                median_time=0.0,
                min_time=0.0,
                max_time=0.0,
                memory_usage_mb=total_memory / (1024 * 1024),
                cpu_percent=self.process.cpu_percent()
            )
        except Exception as e:
            raise Exception(f"Memory usage benchmark failed: {e}")

    def _benchmark_import_performance(self) -> BenchmarkResult:
        """Benchmark module import performance."""
        def import_operation():
            # Clear modules to force re-import
            modules_to_clear = [
                'services.analysis_service.modules.semantic_analyzer',
                'services.analysis_service.modules.sentiment_analyzer',
                'services.analysis_service.modules.risk_assessor'
            ]

            for module in modules_to_clear:
                if module in sys.modules:
                    del sys.modules[module]

            # Import modules
            import services.analysis_service.modules.semantic_analyzer
            import services.analysis_service.modules.sentiment_analyzer
            import services.analysis_service.modules.risk_assessor

        return self._run_benchmark(
            "import_performance",
            import_operation,
            iterations=10
        )

    def _run_benchmark(self, operation: str, func, iterations: int = 100) -> BenchmarkResult:
        """Run a benchmark operation multiple times."""
        times = []

        # Warm up
        for _ in range(min(5, iterations // 10)):
            try:
                func()
            except:
                pass

        # Actual benchmark
        for _ in range(iterations):
            start_time = time.perf_counter()
            try:
                func()
                end_time = time.perf_counter()
                times.append(end_time - start_time)
            except Exception as e:
                # If function fails, still record a time (but mark as failed)
                end_time = time.perf_counter()
                times.append(end_time - start_time)

        # Calculate statistics
        total_time = sum(times)
        avg_time = mean(times)
        median_time = median(times)
        min_time = min(times)
        max_time = max(times)

        # Get resource usage
        memory_info = self.process.memory_info()
        memory_usage_mb = memory_info.rss / (1024 * 1024)
        cpu_percent = self.process.cpu_percent()

        return BenchmarkResult(
            operation=operation,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            median_time=median_time,
            min_time=min_time,
            max_time=max_time,
            memory_usage_mb=memory_usage_mb,
            cpu_percent=cpu_percent
        )

    def _calculate_summary_stats(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Calculate summary statistics from benchmark results."""
        if not results:
            return {"error": "No successful benchmarks"}

        # Find best and worst performers
        sorted_by_avg = sorted(results, key=lambda x: x.avg_time)
        best_result = sorted_by_avg[0]
        worst_result = sorted_by_avg[-1]

        # Calculate averages
        avg_times = [r.avg_time for r in results]
        avg_memory = mean([r.memory_usage_mb for r in results])
        avg_cpu = mean([r.cpu_percent for r in results])

        return {
            "total_operations": len(results),
            "best_operation": best_result.operation,
            "worst_operation": worst_result.operation,
            "avg_response_time": mean(avg_times),
            "median_response_time": median(avg_times),
            "avg_memory_mb": avg_memory,
            "avg_cpu_percent": avg_cpu,
            "performance_score": self._calculate_performance_score(results)
        }

    def _calculate_performance_score(self, results: List[BenchmarkResult]) -> float:
        """Calculate an overall performance score (0-100)."""
        if not results:
            return 0.0

        # Score based on average response time (lower is better)
        avg_times = [r.avg_time for r in results]
        mean_time = mean(avg_times)

        # Normalize score (assuming good performance is < 0.1s, poor is > 1.0s)
        if mean_time < 0.01:
            score = 100
        elif mean_time < 0.1:
            score = 80
        elif mean_time < 0.5:
            score = 60
        elif mean_time < 1.0:
            score = 40
        else:
            score = 20

        # Adjust for memory usage
        avg_memory = mean([r.memory_usage_mb for r in results])
        if avg_memory < 50:  # Less than 50MB
            score += 10
        elif avg_memory > 200:  # More than 200MB
            score -= 10

        return max(0, min(100, score))

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
            "cpu_count": os.cpu_count(),
            "memory_total": psutil.virtual_memory().total / (1024**3),  # GB
            "memory_available": psutil.virtual_memory().available / (1024**3),  # GB
        }


def main():
    """Main benchmark execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Performance Benchmarking")
    parser.add_argument("--output", default="performance_benchmark_results.json",
                       help="Output file for results")
    parser.add_argument("--iterations", type=int, default=50,
                       help="Default number of iterations per benchmark")

    args = parser.parse_args()

    print("🚀 Performance Benchmarking Suite")
    print("=" * 50)

    benchmarker = PerformanceBenchmarker()
    results = benchmarker.run_full_benchmark()

    # Save results
    import json
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Results saved to: {args.output}")

    # Performance assessment
    summary = results.get("summary", {})
    perf_score = summary.get("performance_score", 0)

    if perf_score >= 80:
        print("🚀 EXCELLENT: Performance is outstanding!")
    elif perf_score >= 60:
        print("✅ GOOD: Performance is acceptable")
    elif perf_score >= 40:
        print("⚠️  FAIR: Performance could be improved")
    else:
        print("❌ CONCERNS: Performance needs optimization")

    return 0


if __name__ == "__main__":
    sys.exit(main())
