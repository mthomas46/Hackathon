"""
Document Persistence Performance Benchmarking

Comprehensive performance tests for document generation workflows
including throughput, latency, memory usage, and scalability testing.
"""

import pytest
import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime
from typing import Dict, Any, List, Tuple
import uuid
import resource
import psutil
import gc


class DocumentPersistencePerformanceBenchmark:
    """Performance benchmark suite for document persistence."""

    def __init__(self):
        self.interpreter_url = "http://localhost:5120"
        self.doc_store_url = "http://localhost:5087"
        self.test_user_id = f"perf_test_{uuid.uuid4().hex[:8]}"
        self.performance_metrics = []
        self.generated_documents = []

    async def run_comprehensive_benchmark(self):
        """Run comprehensive performance benchmark suite."""
        print("🚀 Document Persistence Performance Benchmark")
        print("=" * 60)
        print(f"⏰ Benchmark started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Benchmark suites
        await self._benchmark_response_times()
        await self._benchmark_throughput()
        await self._benchmark_concurrent_load()
        await self._benchmark_memory_usage()
        await self._benchmark_format_performance()
        await self._benchmark_document_size_scaling()
        await self._benchmark_sustained_load()

        # Generate performance report
        await self._generate_performance_report()

    async def _benchmark_response_times(self):
        """Benchmark response times for different document types."""
        print("📊 Benchmarking Response Times...")
        
        test_cases = [
            {"name": "Simple JSON", "query": "Create simple API endpoint doc", "format": "json"},
            {"name": "Markdown Doc", "query": "Create comprehensive API documentation", "format": "markdown"},
            {"name": "CSV Report", "query": "Create usage statistics report", "format": "csv"},
            {"name": "Complex PDF", "query": "Create detailed technical specification", "format": "pdf"}
        ]

        async with aiohttp.ClientSession() as session:
            for test_case in test_cases:
                response_times = []
                
                # Run multiple iterations for statistical significance
                for i in range(5):
                    start_time = time.time()
                    
                    query_data = {
                        "query": test_case["query"],
                        "format": test_case["format"],
                        "user_id": f"{self.test_user_id}_rt_{i}"
                    }
                    
                    try:
                        async with session.post(f"{self.interpreter_url}/execute-query",
                                              json=query_data,
                                              timeout=aiohttp.ClientTimeout(total=60)) as response:
                            await response.json()  # Ensure response is fully received
                            end_time = time.time()
                            
                            if response.status in [200, 202]:
                                response_times.append(end_time - start_time)
                    except Exception as e:
                        print(f"Error in response time test: {e}")

                if response_times:
                    avg_time = statistics.mean(response_times)
                    min_time = min(response_times)
                    max_time = max(response_times)
                    
                    self.performance_metrics.append({
                        "category": "response_time",
                        "test_name": test_case["name"],
                        "format": test_case["format"],
                        "avg_response_time": avg_time,
                        "min_response_time": min_time,
                        "max_response_time": max_time,
                        "samples": len(response_times)
                    })
                    
                    print(f"  {test_case['name']}: {avg_time:.2f}s avg (min: {min_time:.2f}s, max: {max_time:.2f}s)")

    async def _benchmark_throughput(self):
        """Benchmark throughput under normal load."""
        print("📈 Benchmarking Throughput...")
        
        concurrent_requests = 10
        total_requests = 50
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            completed_requests = 0
            failed_requests = 0
            
            # Process requests in batches
            for batch_start in range(0, total_requests, concurrent_requests):
                batch_end = min(batch_start + concurrent_requests, total_requests)
                batch_tasks = []
                
                for i in range(batch_start, batch_end):
                    query_data = {
                        "query": f"Create throughput test document {i}",
                        "format": "json",
                        "user_id": f"{self.test_user_id}_tp_{i}"
                    }
                    
                    task = session.post(f"{self.interpreter_url}/execute-query", 
                                      json=query_data,
                                      timeout=aiohttp.ClientTimeout(total=30))
                    batch_tasks.append(task)
                
                # Wait for batch completion
                batch_responses = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for response in batch_responses:
                    if isinstance(response, Exception):
                        failed_requests += 1
                    else:
                        async with response as resp:
                            if resp.status in [200, 202]:
                                completed_requests += 1
                            else:
                                failed_requests += 1

            end_time = time.time()
            total_time = end_time - start_time
            
            throughput = completed_requests / total_time if total_time > 0 else 0
            success_rate = (completed_requests / total_requests) * 100
            
            self.performance_metrics.append({
                "category": "throughput",
                "test_name": "Normal Load Throughput",
                "total_requests": total_requests,
                "completed_requests": completed_requests,
                "failed_requests": failed_requests,
                "total_time": total_time,
                "throughput_rps": throughput,
                "success_rate": success_rate
            })
            
            print(f"  Throughput: {throughput:.2f} requests/second")
            print(f"  Success Rate: {success_rate:.1f}%")
            print(f"  Total Time: {total_time:.2f}s")

    async def _benchmark_concurrent_load(self):
        """Benchmark performance under high concurrent load."""
        print("⚡ Benchmarking Concurrent Load...")
        
        concurrent_levels = [5, 10, 20, 30]
        
        async with aiohttp.ClientSession() as session:
            for concurrent_count in concurrent_levels:
                print(f"  Testing {concurrent_count} concurrent requests...")
                
                start_time = time.time()
                tasks = []
                
                for i in range(concurrent_count):
                    query_data = {
                        "query": f"Create concurrent load test document {i}",
                        "format": "json",
                        "user_id": f"{self.test_user_id}_cl_{concurrent_count}_{i}"
                    }
                    
                    task = session.post(f"{self.interpreter_url}/execute-query",
                                      json=query_data,
                                      timeout=aiohttp.ClientTimeout(total=45))
                    tasks.append(task)
                
                # Execute all concurrent requests
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()
                
                successful = 0
                failed = 0
                response_times = []
                
                for i, response in enumerate(responses):
                    if isinstance(response, Exception):
                        failed += 1
                    else:
                        async with response as resp:
                            if resp.status in [200, 202]:
                                successful += 1
                                # Approximate response time (not perfectly accurate for concurrent)
                                response_times.append((end_time - start_time) / concurrent_count)
                            else:
                                failed += 1

                avg_response_time = statistics.mean(response_times) if response_times else 0
                success_rate = (successful / concurrent_count) * 100
                
                self.performance_metrics.append({
                    "category": "concurrent_load",
                    "test_name": f"Concurrent Load ({concurrent_count} requests)",
                    "concurrent_requests": concurrent_count,
                    "successful_requests": successful,
                    "failed_requests": failed,
                    "avg_response_time": avg_response_time,
                    "success_rate": success_rate,
                    "total_time": end_time - start_time
                })
                
                print(f"    Success Rate: {success_rate:.1f}%")
                print(f"    Avg Response Time: {avg_response_time:.2f}s")

    async def _benchmark_memory_usage(self):
        """Benchmark memory usage during document generation."""
        print("💾 Benchmarking Memory Usage...")
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        async with aiohttp.ClientSession() as session:
            memory_measurements = [initial_memory]
            
            # Generate documents and measure memory
            for i in range(10):
                query_data = {
                    "query": f"Create memory benchmark document {i} with substantial content for memory testing",
                    "format": "markdown",
                    "user_id": f"{self.test_user_id}_mem_{i}"
                }
                
                try:
                    async with session.post(f"{self.interpreter_url}/execute-query",
                                          json=query_data,
                                          timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status in [200, 202]:
                            result = await response.json()
                            if "document_id" in result:
                                self.generated_documents.append(result["document_id"])
                        
                        # Measure memory after each request
                        current_memory = process.memory_info().rss / 1024 / 1024
                        memory_measurements.append(current_memory)
                        
                except Exception as e:
                    print(f"Memory test request failed: {e}")

            # Force garbage collection
            gc.collect()
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_measurements.append(final_memory)
            
            max_memory = max(memory_measurements)
            avg_memory = statistics.mean(memory_measurements)
            memory_growth = final_memory - initial_memory
            
            self.performance_metrics.append({
                "category": "memory_usage",
                "test_name": "Memory Usage During Generation",
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "max_memory_mb": max_memory,
                "avg_memory_mb": avg_memory,
                "memory_growth_mb": memory_growth,
                "samples": len(memory_measurements)
            })
            
            print(f"  Initial Memory: {initial_memory:.1f} MB")
            print(f"  Final Memory: {final_memory:.1f} MB")
            print(f"  Peak Memory: {max_memory:.1f} MB")
            print(f"  Memory Growth: {memory_growth:.1f} MB")

    async def _benchmark_format_performance(self):
        """Benchmark performance across different output formats."""
        print("📋 Benchmarking Format Performance...")
        
        formats = ["json", "markdown", "csv", "txt"]
        base_query = "Create format performance test document with comprehensive content"
        
        async with aiohttp.ClientSession() as session:
            for format_type in formats:
                format_times = []
                
                for i in range(3):  # Multiple samples per format
                    start_time = time.time()
                    
                    query_data = {
                        "query": f"{base_query} in {format_type} format",
                        "format": format_type,
                        "user_id": f"{self.test_user_id}_fmt_{format_type}_{i}"
                    }
                    
                    try:
                        async with session.post(f"{self.interpreter_url}/execute-query",
                                              json=query_data,
                                              timeout=aiohttp.ClientTimeout(total=45)) as response:
                            await response.json()
                            end_time = time.time()
                            
                            if response.status in [200, 202]:
                                format_times.append(end_time - start_time)
                    except Exception as e:
                        print(f"Format test failed for {format_type}: {e}")

                if format_times:
                    avg_time = statistics.mean(format_times)
                    
                    self.performance_metrics.append({
                        "category": "format_performance",
                        "test_name": f"Format Performance ({format_type})",
                        "format": format_type,
                        "avg_generation_time": avg_time,
                        "samples": len(format_times)
                    })
                    
                    print(f"  {format_type.upper()}: {avg_time:.2f}s avg")

    async def _benchmark_document_size_scaling(self):
        """Benchmark performance scaling with document size."""
        print("📏 Benchmarking Document Size Scaling...")
        
        size_tests = [
            {"name": "Small", "query": "Create small API doc", "complexity": 1},
            {"name": "Medium", "query": "Create comprehensive API documentation with examples and detailed explanations", "complexity": 2},
            {"name": "Large", "query": "Create extensive API documentation covering authentication, all endpoints, data models, error handling, rate limiting, webhooks, SDKs, and comprehensive examples", "complexity": 3}
        ]
        
        async with aiohttp.ClientSession() as session:
            for test_case in size_tests:
                size_times = []
                
                for i in range(2):  # Fewer samples for larger documents
                    start_time = time.time()
                    
                    query_data = {
                        "query": test_case["query"],
                        "format": "markdown",
                        "user_id": f"{self.test_user_id}_size_{test_case['name']}_{i}"
                    }
                    
                    try:
                        async with session.post(f"{self.interpreter_url}/execute-query",
                                              json=query_data,
                                              timeout=aiohttp.ClientTimeout(total=90)) as response:
                            result = await response.json()
                            end_time = time.time()
                            
                            if response.status in [200, 202]:
                                size_times.append(end_time - start_time)
                                
                                # Track document size if available
                                document_size = result.get("size_bytes", 0)
                                if document_size > 0:
                                    print(f"    {test_case['name']} document: {document_size} bytes")
                    except Exception as e:
                        print(f"Size scaling test failed for {test_case['name']}: {e}")

                if size_times:
                    avg_time = statistics.mean(size_times)
                    
                    self.performance_metrics.append({
                        "category": "size_scaling",
                        "test_name": f"Size Scaling ({test_case['name']})",
                        "document_size": test_case["name"],
                        "complexity": test_case["complexity"],
                        "avg_generation_time": avg_time,
                        "samples": len(size_times)
                    })
                    
                    print(f"  {test_case['name']}: {avg_time:.2f}s avg")

    async def _benchmark_sustained_load(self):
        """Benchmark performance under sustained load."""
        print("🔄 Benchmarking Sustained Load...")
        
        duration_seconds = 60  # 1 minute sustained load
        request_interval = 2   # Request every 2 seconds
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            request_count = 0
            successful_requests = 0
            failed_requests = 0
            response_times = []
            
            while time.time() - start_time < duration_seconds:
                request_start = time.time()
                
                query_data = {
                    "query": f"Create sustained load test document {request_count}",
                    "format": "json",
                    "user_id": f"{self.test_user_id}_sustained_{request_count}"
                }
                
                try:
                    async with session.post(f"{self.interpreter_url}/execute-query",
                                          json=query_data,
                                          timeout=aiohttp.ClientTimeout(total=30)) as response:
                        request_end = time.time()
                        request_count += 1
                        
                        if response.status in [200, 202]:
                            successful_requests += 1
                            response_times.append(request_end - request_start)
                        else:
                            failed_requests += 1
                            
                except Exception as e:
                    failed_requests += 1
                    print(f"Sustained load request failed: {e}")
                
                # Wait for next request interval
                elapsed = time.time() - request_start
                if elapsed < request_interval:
                    await asyncio.sleep(request_interval - elapsed)

            total_time = time.time() - start_time
            avg_response_time = statistics.mean(response_times) if response_times else 0
            throughput = successful_requests / total_time
            success_rate = (successful_requests / request_count) * 100 if request_count > 0 else 0
            
            self.performance_metrics.append({
                "category": "sustained_load",
                "test_name": "Sustained Load Test",
                "duration_seconds": total_time,
                "total_requests": request_count,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "avg_response_time": avg_response_time,
                "throughput_rps": throughput,
                "success_rate": success_rate
            })
            
            print(f"  Duration: {total_time:.1f}s")
            print(f"  Total Requests: {request_count}")
            print(f"  Success Rate: {success_rate:.1f}%")
            print(f"  Throughput: {throughput:.2f} requests/second")
            print(f"  Avg Response Time: {avg_response_time:.2f}s")

    async def _generate_performance_report(self):
        """Generate comprehensive performance report."""
        print("\n📋 Performance Benchmark Report")
        print("=" * 60)
        
        # Organize metrics by category
        categories = {}
        for metric in self.performance_metrics:
            category = metric["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(metric)
        
        # Generate report sections
        for category, metrics in categories.items():
            print(f"\n🔍 {category.replace('_', ' ').title()}")
            print("-" * 40)
            
            for metric in metrics:
                print(f"  {metric['test_name']}:")
                
                # Display relevant metrics based on category
                if category == "response_time":
                    print(f"    Average: {metric['avg_response_time']:.2f}s")
                    print(f"    Range: {metric['min_response_time']:.2f}s - {metric['max_response_time']:.2f}s")
                
                elif category == "throughput":
                    print(f"    Throughput: {metric['throughput_rps']:.2f} req/s")
                    print(f"    Success Rate: {metric['success_rate']:.1f}%")
                
                elif category == "concurrent_load":
                    print(f"    Concurrent Requests: {metric['concurrent_requests']}")
                    print(f"    Success Rate: {metric['success_rate']:.1f}%")
                    print(f"    Avg Response Time: {metric['avg_response_time']:.2f}s")
                
                elif category == "memory_usage":
                    print(f"    Memory Growth: {metric['memory_growth_mb']:.1f} MB")
                    print(f"    Peak Memory: {metric['max_memory_mb']:.1f} MB")
                
                elif category == "format_performance":
                    print(f"    Format: {metric['format']}")
                    print(f"    Avg Generation Time: {metric['avg_generation_time']:.2f}s")
                
                elif category == "size_scaling":
                    print(f"    Document Size: {metric['document_size']}")
                    print(f"    Avg Generation Time: {metric['avg_generation_time']:.2f}s")
                
                elif category == "sustained_load":
                    print(f"    Duration: {metric['duration_seconds']:.1f}s")
                    print(f"    Throughput: {metric['throughput_rps']:.2f} req/s")
                    print(f"    Success Rate: {metric['success_rate']:.1f}%")
                
                print()
        
        # Performance summary
        print("\n🏆 Performance Summary")
        print("-" * 40)
        
        # Calculate overall metrics
        response_time_metrics = [m for m in self.performance_metrics if m["category"] == "response_time"]
        if response_time_metrics:
            avg_response_times = [m["avg_response_time"] for m in response_time_metrics]
            overall_avg_response = statistics.mean(avg_response_times)
            print(f"Overall Avg Response Time: {overall_avg_response:.2f}s")
        
        throughput_metrics = [m for m in self.performance_metrics if m["category"] == "throughput"]
        if throughput_metrics:
            max_throughput = max(m["throughput_rps"] for m in throughput_metrics)
            print(f"Peak Throughput: {max_throughput:.2f} req/s")
        
        memory_metrics = [m for m in self.performance_metrics if m["category"] == "memory_usage"]
        if memory_metrics:
            memory_growth = memory_metrics[0]["memory_growth_mb"]
            print(f"Memory Growth: {memory_growth:.1f} MB")
        
        print(f"Generated Documents: {len(self.generated_documents)}")
        print(f"Total Metrics Collected: {len(self.performance_metrics)}")
        
        # Save detailed report to file
        report_data = {
            "benchmark_timestamp": datetime.now().isoformat(),
            "performance_metrics": self.performance_metrics,
            "generated_documents": self.generated_documents,
            "summary": {
                "total_metrics": len(self.performance_metrics),
                "total_documents": len(self.generated_documents)
            }
        }
        
        report_file = f"document_persistence_performance_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")


# Pytest-compatible test classes

class TestDocumentPersistencePerformance:
    """Pytest-compatible performance tests."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup performance test environment."""
        self.benchmark = DocumentPersistencePerformanceBenchmark()

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_response_time_performance(self):
        """Test response time performance benchmarks."""
        await self.benchmark._benchmark_response_times()
        
        # Verify we collected performance metrics
        response_time_metrics = [m for m in self.benchmark.performance_metrics 
                               if m["category"] == "response_time"]
        assert len(response_time_metrics) > 0
        
        # Verify response times are reasonable (under 30 seconds)
        for metric in response_time_metrics:
            assert metric["avg_response_time"] < 30.0

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_throughput_performance(self):
        """Test throughput performance benchmarks."""
        await self.benchmark._benchmark_throughput()
        
        # Verify throughput metrics were collected
        throughput_metrics = [m for m in self.benchmark.performance_metrics 
                            if m["category"] == "throughput"]
        assert len(throughput_metrics) > 0
        
        # Verify reasonable success rate
        for metric in throughput_metrics:
            assert metric["success_rate"] >= 50.0  # At least 50% success

    @pytest.mark.asyncio
    @pytest.mark.performance  
    async def test_concurrent_load_performance(self):
        """Test concurrent load performance benchmarks."""
        await self.benchmark._benchmark_concurrent_load()
        
        # Verify concurrent load metrics were collected
        concurrent_metrics = [m for m in self.benchmark.performance_metrics 
                            if m["category"] == "concurrent_load"]
        assert len(concurrent_metrics) > 0
        
        # Verify system handles some level of concurrency
        for metric in concurrent_metrics:
            if metric["concurrent_requests"] <= 10:
                assert metric["success_rate"] >= 80.0  # Higher success rate for lower concurrency

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_memory_usage_performance(self):
        """Test memory usage performance benchmarks."""
        await self.benchmark._benchmark_memory_usage()
        
        # Verify memory metrics were collected
        memory_metrics = [m for m in self.benchmark.performance_metrics 
                         if m["category"] == "memory_usage"]
        assert len(memory_metrics) > 0
        
        # Verify memory growth is reasonable (under 500MB)
        for metric in memory_metrics:
            assert metric["memory_growth_mb"] < 500.0

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_format_performance_comparison(self):
        """Test performance comparison across different formats."""
        await self.benchmark._benchmark_format_performance()
        
        # Verify format performance metrics were collected
        format_metrics = [m for m in self.benchmark.performance_metrics 
                         if m["category"] == "format_performance"]
        assert len(format_metrics) > 0
        
        # Verify all major formats were tested
        tested_formats = {m["format"] for m in format_metrics}
        expected_formats = {"json", "markdown", "csv", "txt"}
        assert len(tested_formats.intersection(expected_formats)) >= 2


@pytest.mark.performance
class TestDocumentPersistenceStressTest:
    """Stress tests for document persistence system."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup stress test environment."""
        self.interpreter_url = "http://localhost:5120"
        self.test_user_id = f"stress_test_{uuid.uuid4().hex[:8]}"

    @pytest.mark.asyncio
    async def test_high_concurrency_stress(self):
        """Stress test with high concurrency."""
        concurrent_requests = 50
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for i in range(concurrent_requests):
                query_data = {
                    "query": f"Create stress test document {i}",
                    "format": "json",
                    "user_id": f"{self.test_user_id}_stress_{i}"
                }
                
                task = session.post(f"{self.interpreter_url}/execute-query",
                                  json=query_data,
                                  timeout=aiohttp.ClientTimeout(total=60))
                tasks.append(task)
            
            # Execute all concurrent requests
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = 0
            for response in responses:
                if not isinstance(response, Exception):
                    async with response as resp:
                        if resp.status in [200, 202]:
                            successful += 1

            success_rate = (successful / concurrent_requests) * 100
            
            # Should handle at least 30% of high concurrency requests
            assert success_rate >= 30.0, f"Success rate too low: {success_rate}%"

    @pytest.mark.asyncio
    async def test_sustained_high_load_stress(self):
        """Stress test with sustained high load."""
        duration = 30  # 30 seconds of sustained load
        request_interval = 0.5  # Request every 0.5 seconds
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            request_count = 0
            successful = 0
            
            while time.time() - start_time < duration:
                query_data = {
                    "query": f"Create sustained stress test document {request_count}",
                    "format": "json",
                    "user_id": f"{self.test_user_id}_sustained_{request_count}"
                }
                
                try:
                    async with session.post(f"{self.interpreter_url}/execute-query",
                                          json=query_data,
                                          timeout=aiohttp.ClientTimeout(total=20)) as response:
                        request_count += 1
                        if response.status in [200, 202]:
                            successful += 1
                except Exception:
                    request_count += 1
                
                await asyncio.sleep(request_interval)

            success_rate = (successful / request_count) * 100 if request_count > 0 else 0
            
            # Should maintain reasonable success rate under sustained load
            assert success_rate >= 25.0, f"Sustained load success rate too low: {success_rate}%"


if __name__ == "__main__":
    # Run benchmark directly
    benchmark = DocumentPersistencePerformanceBenchmark()
    asyncio.run(benchmark.run_comprehensive_benchmark())
