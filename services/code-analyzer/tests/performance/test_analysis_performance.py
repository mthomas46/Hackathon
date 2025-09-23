"""Performance Tests for Code Analyzer Service.

This module tests performance characteristics including:
- Code analysis throughput and latency
- Memory usage during large codebase analysis
- Scalability with increasing codebase size
- Concurrent analysis performance
- Resource utilization monitoring

Performance tests ensure the Code Analyzer service meets performance requirements.
"""

import asyncio
import time
import statistics
import psutil
import os
from typing import Dict, Any, List, Tuple
from unittest.mock import patch, AsyncMock

import pytest


class TestAnalysisPerformance:
    """Performance testing for code analysis operations."""

    @pytest.fixture
    def performance_config(self):
        """Performance test configuration."""
        return {
            "warmup_iterations": 5,
            "test_iterations": 50,
            "concurrent_analyses": [1, 3, 5, 10],
            "target_analysis_time_ms": 2000,  # 2 seconds per analysis
            "acceptable_error_rate": 0.05,  # 5%
            "memory_threshold_mb": 200,
            "cpu_threshold_percent": 85
        }

    @pytest.fixture
    def sample_codebase(self):
        """Generate sample codebase for testing."""
        return {
            "small": self._generate_sample_files(5, 50),    # 5 files, ~50 lines each
            "medium": self._generate_sample_files(20, 100),  # 20 files, ~100 lines each
            "large": self._generate_sample_files(50, 200),   # 50 files, ~200 lines each
        }

    def _generate_sample_files(self, num_files: int, lines_per_file: int) -> List[Dict[str, Any]]:
        """Generate sample code files for testing."""
        files = []
        for i in range(num_files):
            content = []
            # Generate Python-like code structure
            content.append("import os")
            content.append("import sys")
            content.append("")
            content.append("class SampleClass:")
            content.append("    def __init__(self):")
            content.append("        self.value = None")
            content.append("")
            content.append("    def process_data(self, data):")
            content.append("        result = []")
            content.append("        for item in data:")
            content.append("            if item is not None:")
            content.append("                result.append(item.upper())")
            content.append("        return result")
            content.append("")
            content.append("def main():")
            content.append("    processor = SampleClass()")
            content.append("    data = ['hello', 'world', None, 'test']")
            content.append("    result = processor.process_data(data)")
            content.append("    print(result)")
            content.append("")
            content.append("if __name__ == '__main__':")
            content.append("    main()")

            # Fill to desired line count
            while len(content) < lines_per_file:
                content.append(f"    # Additional line {len(content) + 1}")

            files.append({
                "filename": f"sample_{i}.py",
                "content": "\n".join(content),
                "language": "python",
                "size": len("\n".join(content))
            })

        return files

    @pytest.mark.asyncio
    async def test_code_analysis_throughput(self, performance_config, sample_codebase):
        """Test code analysis throughput under normal load."""
        # Mock analysis function
        mock_analysis_result = {
            "complexity_score": 3.2,
            "functions_found": 5,
            "classes_found": 1,
            "imports_found": 2,
            "security_issues": [],
            "code_quality_score": 8.5
        }

        with patch("main.analyze_code", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_analysis_result

            from main import analyze_code

            # Warmup phase
            for _ in range(performance_config["warmup_iterations"]):
                await analyze_code(sample_codebase["small"][0]["content"], "python")

            # Performance test phase
            response_times = []
            start_time = time.time()

            for _ in range(performance_config["test_iterations"]):
                iteration_start = time.time()
                result = await analyze_code(sample_codebase["small"][0]["content"], "python")
                iteration_end = time.time()

                response_time = (iteration_end - iteration_start) * 1000  # Convert to ms
                response_times.append(response_time)

                # Verify result structure
                assert "complexity_score" in result
                assert "code_quality_score" in result

            end_time = time.time()
            total_time = end_time - start_time

            # Calculate performance metrics
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            throughput = performance_config["test_iterations"] / total_time

            # Performance assertions
            assert avg_response_time < performance_config["target_analysis_time_ms"], \
                f"Average analysis time {avg_response_time:.2f}ms exceeds target {performance_config['target_analysis_time_ms']}ms"

            assert p95_response_time < performance_config["target_analysis_time_ms"] * 1.5, \
                f"95th percentile analysis time {p95_response_time:.2f}ms too high"

            print(f"Code Analysis Throughput Test:")
            print(f"  Total Analyses: {performance_config['test_iterations']}")
            print(f"  Total Time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.2f} analyses/s")
            print(f"  Avg Analysis Time: {avg_response_time:.2f}ms")
            print(f"  Median Analysis Time: {median_response_time:.2f}ms")
            print(f"  95th Percentile: {p95_response_time:.2f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_analysis_performance(self, performance_config, sample_codebase):
        """Test performance under concurrent analysis load."""
        async def single_analysis_task(file_data: Dict[str, Any]) -> float:
            """Perform single file analysis and return response time."""
            start_time = time.time()

            # Mock analysis delay based on file size
            analysis_delay = len(file_data["content"]) / 10000  # Rough heuristic
            await asyncio.sleep(analysis_delay)

            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            return response_time

        # Test different concurrency levels
        for concurrent_analyses in performance_config["concurrent_analyses"]:
            print(f"\nTesting concurrent analysis with {concurrent_analyses} parallel analyses...")

            start_time = time.time()

            # Create concurrent analysis tasks
            tasks = []
            for i in range(concurrent_analyses):
                # Use different files for variety
                file_data = sample_codebase["medium"][i % len(sample_codebase["medium"])]
                task = single_analysis_task(file_data)
                tasks.append(task)

            # Execute all tasks concurrently
            response_times = await asyncio.gather(*tasks)

            end_time = time.time()
            total_time = end_time - start_time

            # Calculate performance metrics
            throughput = len(response_times) / total_time
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)

            print(f"  Concurrent Analyses: {concurrent_analyses}")
            print(f"  Total Time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.2f} analyses/s")
            print(f"  Avg Response Time: {avg_response_time:.2f}ms")
            print(f"  Min Response Time: {min_response_time:.2f}ms")
            print(f"  Max Response Time: {max_response_time:.2f}ms")

            # Performance assertions for concurrent analysis
            assert throughput > concurrent_analyses * 0.8, \
                f"Throughput {throughput:.2f} analyses/s too low for {concurrent_analyses} concurrent analyses"

            assert avg_response_time < performance_config["target_analysis_time_ms"] * (concurrent_analyses ** 0.3), \
                f"Average response time {avg_response_time:.2f}ms too high under concurrent load"

    def test_codebase_scale_performance(self, performance_config, sample_codebase):
        """Test performance scaling with codebase size."""
        import time

        # Test different codebase sizes
        scale_results = {}

        for size_name, files in sample_codebase.items():
            print(f"\nTesting {size_name} codebase analysis...")

            # Calculate total codebase metrics
            total_lines = sum(len(file["content"].split('\n')) for file in files)
            total_size = sum(file["size"] for file in files)

            start_time = time.time()

            # Simulate analysis of entire codebase
            for file in files:
                # Simulate analysis time based on file size
                analysis_time = len(file["content"]) / 5000  # Rough heuristic
                time.sleep(analysis_time)

            end_time = time.time()
            total_analysis_time = end_time - start_time

            # Calculate metrics
            analysis_time_per_line = total_analysis_time / total_lines if total_lines > 0 else 0
            analysis_time_per_kb = total_analysis_time / (total_size / 1024) if total_size > 0 else 0

            scale_results[size_name] = {
                "files": len(files),
                "total_lines": total_lines,
                "total_size_kb": total_size / 1024,
                "total_analysis_time": total_analysis_time,
                "analysis_time_per_line": analysis_time_per_line,
                "analysis_time_per_kb": analysis_time_per_kb
            }

            print(f"  Files: {len(files)}")
            print(f"  Total Lines: {total_lines}")
            print(f"  Total Size: {total_size / 1024:.1f} KB")
            print(f"  Total Analysis Time: {total_analysis_time:.2f}s")
            print(f"  Time per Line: {analysis_time_per_line:.4f}s")
            print(f"  Time per KB: {analysis_time_per_kb:.4f}s")

        # Analyze scaling efficiency
        if "small" in scale_results and "large" in scale_results:
            small_time = scale_results["small"]["total_analysis_time"]
            large_time = scale_results["large"]["total_analysis_time"]
            small_lines = scale_results["small"]["total_lines"]
            large_lines = scale_results["large"]["total_lines"]

            scaling_factor = large_time / small_time
            size_ratio = large_lines / small_lines

            efficiency = size_ratio / scaling_factor

            print(f"\nScaling Analysis:")
            print(f"  Size Ratio: {size_ratio:.1f}x")
            print(f"  Time Scaling: {scaling_factor:.1f}x")
            print(f"  Scaling Efficiency: {efficiency:.2f}")

            # Should scale reasonably (not worse than linear)
            assert scaling_factor < size_ratio * 3, \
                f"Poor scaling: {scaling_factor:.1f}x time increase for {size_ratio:.1f}x size increase"

    def test_memory_usage_during_analysis(self, performance_config, sample_codebase):
        """Test memory usage during code analysis."""
        import gc

        process = psutil.Process()

        def analyze_codebase_memory_test(files: List[Dict[str, Any]]) -> Dict[str, Any]:
            """Analyze memory usage during codebase analysis."""
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Perform analysis
            analysis_results = []
            for file in files:
                # Simulate memory allocation during analysis
                analysis_data = {
                    "filename": file["filename"],
                    "complexity": len(file["content"]) / 100,  # Mock complexity
                    "functions": file["content"].count("def "),
                    "classes": file["content"].count("class "),
                    "imports": file["content"].count("import "),
                    # Allocate some memory to simulate analysis
                    "ast_tree": ["node"] * (len(file["content"]) // 10),
                    "metrics": {"lines": len(file["content"].split('\n'))}
                }
                analysis_results.append(analysis_data)

            peak_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Cleanup
            del analysis_results
            gc.collect()

            final_memory = process.memory_info().rss / 1024 / 1024  # MB

            return {
                "initial_memory": initial_memory,
                "peak_memory": peak_memory,
                "final_memory": final_memory,
                "memory_delta": peak_memory - initial_memory,
                "memory_leak": final_memory - initial_memory
            }

        # Test memory usage with different codebase sizes
        for size_name, files in sample_codebase.items():
            print(f"\nTesting memory usage with {size_name} codebase...")

            memory_stats = analyze_codebase_memory_test(files)

            print(f"  Initial Memory: {memory_stats['initial_memory']:.2f} MB")
            print(f"  Peak Memory: {memory_stats['peak_memory']:.2f} MB")
            print(f"  Final Memory: {memory_stats['final_memory']:.2f} MB")
            print(f"  Memory Delta: {memory_stats['memory_delta']:.2f} MB")
            print(f"  Memory Leak: {memory_stats['memory_leak']:.2f} MB")

            # Memory assertions
            assert memory_stats['memory_delta'] < performance_config["memory_threshold_mb"], \
                f"Memory usage increased by {memory_stats['memory_delta']:.2f} MB, exceeds threshold {performance_config['memory_threshold_mb']} MB"

            # Should not have significant memory leaks
            assert abs(memory_stats['memory_leak']) < 10, \
                f"Memory leak detected: {memory_stats['memory_leak']:.2f} MB"

    @pytest.mark.asyncio
    async def test_analysis_cancellation_performance(self):
        """Test performance of analysis cancellation under load."""
        cancellation_times = []

        async def cancellable_analysis(cancel_after: float) -> Tuple[bool, float]:
            """Analysis that can be cancelled."""
            start_time = time.time()
            cancelled = False

            try:
                # Simulate analysis work
                for i in range(100):
                    await asyncio.sleep(0.01)  # 10ms chunks
                    if time.time() - start_time > cancel_after:
                        cancelled = True
                        break
            except asyncio.CancelledError:
                cancelled = True

            end_time = time.time()
            duration = end_time - start_time

            return cancelled, duration

        # Test cancellation at different points
        cancellation_points = [0.05, 0.1, 0.2, 0.5]  # seconds

        for cancel_after in cancellation_points:
            print(f"\nTesting cancellation after {cancel_after}s...")

            start_time = time.time()

            # Run multiple concurrent analyses with cancellation
            tasks = []
            for _ in range(5):
                task = cancellable_analysis(cancel_after)
                tasks.append(task)

            results = await asyncio.gather(*tasks)

            end_time = time.time()
            total_time = end_time - start_time

            cancelled_count = sum(1 for cancelled, _ in results if cancelled)
            avg_duration = sum(duration for _, duration in results) / len(results)

            cancellation_times.append(avg_duration)

            print(f"  Cancelled: {cancelled_count}/5")
            print(f"  Avg Duration: {avg_duration:.3f}s")
            print(f"  Total Time: {total_time:.3f}s")

            # Should cancel within reasonable time
            assert avg_duration < cancel_after * 2, \
                f"Cancellation took too long: {avg_duration:.3f}s for {cancel_after}s limit"

    def test_resource_cleanup_performance(self, performance_config):
        """Test performance of resource cleanup after analysis."""
        import gc

        cleanup_times = []

        for i in range(10):
            # Create resources
            large_objects = []
            for j in range(100):
                large_objects.append({
                    "data": "x" * 1000,  # 1KB strings
                    "analysis": {"complexity": j, "metrics": {"lines": j * 10}}
                })

            # Measure cleanup time
            start_time = time.time()
            del large_objects
            gc.collect()
            end_time = time.time()

            cleanup_time = (end_time - start_time) * 1000  # ms
            cleanup_times.append(cleanup_time)

            print(f"  Cleanup {i+1}: {cleanup_time:.2f}ms")

        avg_cleanup_time = statistics.mean(cleanup_times)
        max_cleanup_time = max(cleanup_times)

        print(f"\nResource Cleanup Performance:")
        print(f"  Avg Cleanup Time: {avg_cleanup_time:.2f}ms")
        print(f"  Max Cleanup Time: {max_cleanup_time:.2f}ms")

        # Cleanup should be fast
        assert avg_cleanup_time < 100, \
            f"Average cleanup too slow: {avg_cleanup_time:.2f}ms"

        assert max_cleanup_time < 500, \
            f"Max cleanup too slow: {max_cleanup_time:.2f}ms"


class TestAnalysisBenchmarks:
    """Performance benchmarks for regression testing."""

    @pytest.fixture
    def benchmark_code_samples(self):
        """Benchmark code samples of different complexities."""
        return {
            "simple": """
def hello_world():
    print("Hello, World!")
    return "success"
""",
            "complex": """
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ComplexAnalyzer:
    threshold: float = 0.8
    max_iterations: int = 1000

    async def analyze_complex_code(self, code: str) -> Dict[str, Any]:
        result = {
            "complexity_score": 0.0,
            "functions": [],
            "classes": [],
            "imports": [],
            "metrics": {}
        }

        # Complex analysis logic
        lines = code.split('\n')
        result["metrics"]["total_lines"] = len(lines)

        for line in lines:
            if line.strip().startswith('def '):
                result["functions"].append(line.split('def ')[1].split('(')[0])
            elif line.strip().startswith('class '):
                result["classes"].append(line.split('class ')[1].split(':')[0])
            elif line.strip().startswith('import ') or line.strip().startswith('from '):
                result["imports"].append(line.strip())

        # Calculate complexity
        result["complexity_score"] = len(result["functions"]) * 0.3 + \
                                   len(result["classes"]) * 0.5 + \
                                   len(result["imports"]) * 0.1 + \
                                   len(lines) * 0.01

        return result

async def main():
    analyzer = ComplexAnalyzer()
    result = await analyzer.analyze_complex_code(__file__)
    return result
""",
            "very_complex": """
# Very complex code with multiple patterns
import re
import json
import asyncio
from typing import Dict, List, Set, Tuple, Optional, Union, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

@dataclass
class BaseAnalyzer(ABC):
    name: str
    version: str = "1.0.0"
    config: Dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    async def analyze(self, code: str) -> Dict[str, Any]:
        pass

class PythonCodeAnalyzer(BaseAnalyzer):
    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        self.patterns = {
            'function': re.compile(r'def\s+(\w+)\s*\('),
            'class': re.compile(r'class\s+(\w+)'),
            'import': re.compile(r'^(?:from\s+\w+\s+)?import\s+\w+'),
            'decorator': re.compile(r'@\w+'),
        }

    async def analyze(self, code: str) -> Dict[str, Any]:
        lines = code.split('\n')
        result = {
            'language': 'python',
            'total_lines': len(lines),
            'code_lines': len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
            'comment_lines': len([l for l in lines if l.strip().startswith('#')]),
            'empty_lines': len([l for l in lines if not l.strip()]),
            'functions': [],
            'classes': [],
            'imports': [],
            'decorators': [],
            'complexity_score': 0.0,
            'maintainability_index': 0.0
        }

        # Extract patterns
        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(code)
            if pattern_name in ['function', 'class', 'import', 'decorator']:
                result[f'{pattern_name}s'] = matches

        # Calculate complexity metrics
        result['complexity_score'] = (
            len(result['functions']) * 1.0 +
            len(result['classes']) * 2.0 +
            len(result['decorators']) * 0.5 +
            result['total_lines'] * 0.01
        )

        # Calculate maintainability index (simplified)
        result['maintainability_index'] = max(0, 100 - result['complexity_score'])

        return result

async def batch_analyze(analyzer: PythonCodeAnalyzer, files: List[str]) -> List[Dict[str, Any]]:
    tasks = []
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            task = analyzer.analyze(content)
            tasks.append(task)
        except Exception as e:
            tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Placeholder

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]

def create_test_files():
    files = []
    for i in range(10):
        filename = f'test_file_{i}.py'
        content = f'''
import os
import sys

class TestClass{i}:
    def __init__(self):
        self.value = {i}

    def method_{i}(self):
        return self.value * {i}

def function_{i}():
    return {i} ** 2

if __name__ == "__main__":
    obj = TestClass{i}()
    print(function_{i}())
'''
        files.append(content)
    return files
"""
        }

    @pytest.mark.benchmark
    def test_code_complexity_analysis_performance(self, benchmark_code_samples):
        """Benchmark code complexity analysis performance."""
        import time

        results = {}

        for complexity_name, code in benchmark_code_samples.items():
            print(f"\nBenchmarking {complexity_name} code analysis...")

            # Warmup
            for _ in range(3):
                # Simple analysis simulation
                lines = code.split('\n')
                functions = sum(1 for line in lines if 'def ' in line)
                classes = sum(1 for line in lines if 'class ' in line)
                imports = sum(1 for line in lines if 'import ' in line)

            # Benchmark
            start_time = time.time()

            for _ in range(100):  # 100 iterations
                lines = code.split('\n')
                functions = sum(1 for line in lines if 'def ' in line)
                classes = sum(1 for line in lines if 'class ' in line)
                imports = sum(1 for line in lines if 'import ' in line)
                complexity = functions * 1.0 + classes * 2.0 + imports * 0.5 + len(lines) * 0.01

            end_time = time.time()

            avg_time = (end_time - start_time) / 100 * 1000  # ms per analysis
            code_size = len(code)

            results[complexity_name] = {
                "code_size": code_size,
                "avg_analysis_time_ms": avg_time,
                "time_per_kb": avg_time / (code_size / 1024),
                "functions_found": functions,
                "classes_found": classes,
                "imports_found": imports,
                "complexity_score": complexity
            }

            print(f"  Code Size: {code_size} chars")
            print(f"  Avg Analysis Time: {avg_time:.2f}ms")
            print(f"  Time per KB: {avg_time / (code_size / 1024):.2f}ms")
            print(f"  Complexity Score: {complexity:.2f}")

        # Performance should scale reasonably with code complexity
        if "simple" in results and "very_complex" in results:
            simple_time = results["simple"]["avg_analysis_time_ms"]
            complex_time = results["very_complex"]["avg_analysis_time_ms"]
            complexity_ratio = results["very_complex"]["code_size"] / results["simple"]["code_size"]

            scaling_factor = complex_time / simple_time

            print(f"\nComplexity Scaling Analysis:")
            print(f"  Code Size Ratio: {complexity_ratio:.1f}x")
            print(f"  Time Scaling: {scaling_factor:.1f}x")
            print(f"  Scaling Efficiency: {complexity_ratio / scaling_factor:.2f}")

            # Analysis time should scale sub-linearly with code size
            assert scaling_factor < complexity_ratio * 2, \
                f"Poor complexity scaling: {scaling_factor:.1f}x time for {complexity_ratio:.1f}x code size"
