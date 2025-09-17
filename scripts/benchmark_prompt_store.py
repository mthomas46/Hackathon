#!/usr/bin/env python3
"""Performance benchmarking script for prompt_store service.

This script provides detailed performance analysis including:
- Response time percentiles
- Throughput measurements
- Memory usage tracking
- Concurrent load testing
- Performance regression detection

Usage:
    python scripts/benchmark_prompt_store.py --help
    python scripts/benchmark_prompt_store.py --quick
    python scripts/benchmark_prompt_store.py --full
    python scripts/benchmark_prompt_store.py --load-test
"""

import asyncio
import time
import statistics
import psutil
import argparse
import sys
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import aiohttp
import matplotlib.pyplot as plt
import numpy as np


class PerformanceBenchmarker:
    """Comprehensive performance benchmarking for prompt_store."""

    def __init__(self, base_url: str = "http://localhost:5110", verbose: bool = False):
        self.base_url = base_url
        self.verbose = verbose
        self.session: Optional[aiohttp.ClientSession] = None
        self.results = {}

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def make_request(self, method: str, endpoint: str,
                          data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request with timing."""
        if not self.session:
            raise RuntimeError("Use async context manager")

        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    response_time = time.time() - start_time
                    if response.status == 200:
                        response_data = await response.json()
                        return {"success": True, "response_time": response_time, "data": response_data}
                    else:
                        return {"success": False, "response_time": response_time, "status": response.status}
            elif method.upper() == "POST":
                async with self.session.post(url, json=data) as response:
                    response_time = time.time() - start_time
                    if response.status in [200, 201]:
                        response_data = await response.json()
                        return {"success": True, "response_time": response_time, "data": response_data}
                    else:
                        return {"success": False, "response_time": response_time, "status": response.status}
        except Exception as e:
            response_time = time.time() - start_time
            return {"success": False, "response_time": response_time, "error": str(e)}

    def log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)

    async def check_service_health(self) -> bool:
        """Check if prompt_store service is running."""
        try:
            result = await self.make_request("GET", "/health")
            return result["success"]
        except:
            return False

    async def benchmark_health_endpoint(self, iterations: int = 100) -> Dict[str, Any]:
        """Benchmark health endpoint performance."""
        self.log(f"Benchmarking health endpoint ({iterations} iterations)...")

        response_times = []
        success_count = 0

        for i in range(iterations):
            result = await self.make_request("GET", "/health")
            if result["success"]:
                response_times.append(result["response_time"])
                success_count += 1
            if self.verbose and (i + 1) % 20 == 0:
                print(f"  Completed {i + 1}/{iterations} requests")

        if response_times:
            stats = self.calculate_stats(response_times)
            stats.update({
                "total_requests": iterations,
                "successful_requests": success_count,
                "success_rate": success_count / iterations
            })
            return stats
        else:
            return {"error": "No successful requests"}

    async def benchmark_prompt_operations(self, iterations: int = 50) -> Dict[str, Any]:
        """Benchmark prompt CRUD operations."""
        self.log(f"Benchmarking prompt operations ({iterations} iterations)...")

        results = {
            "create": {"times": [], "successes": 0},
            "read": {"times": [], "successes": 0},
            "update": {"times": [], "successes": 0}
        }

        created_prompts = []

        # Create prompts
        for i in range(iterations):
            prompt_data = {
                "name": f"bench_prompt_{int(time.time() * 1000)}_{i}",
                "category": "benchmark",
                "content": f"This is benchmark prompt {i} for performance testing.",
                "created_by": "benchmark_script"
            }

            result = await self.make_request("POST", "/api/v1/prompts", prompt_data)
            if result["success"]:
                results["create"]["times"].append(result["response_time"])
                results["create"]["successes"] += 1
                created_prompts.append(result["data"]["id"])
            if self.verbose and (i + 1) % 10 == 0:
                print(f"  Created {i + 1}/{iterations} prompts")

        # Read prompts
        for prompt_id in created_prompts[:min(20, len(created_prompts))]:  # Test first 20 reads
            result = await self.make_request("GET", f"/api/v1/prompts/{prompt_id}")
            if result["success"]:
                results["read"]["times"].append(result["response_time"])
                results["read"]["successes"] += 1

        # Update prompts
        for prompt_id in created_prompts[:min(20, len(created_prompts))]:  # Test first 20 updates
            update_data = {
                "content": "Updated content for benchmark testing.",
                "updated_by": "benchmark_script"
            }
            result = await self.make_request("PUT", f"/api/v1/prompts/{prompt_id}", update_data)
            if result["success"]:
                results["update"]["times"].append(result["response_time"])
                results["update"]["successes"] += 1

        # Calculate statistics for each operation
        for operation, data in results.items():
            if data["times"]:
                data.update(self.calculate_stats(data["times"]))

        return results

    async def load_test_concurrent_requests(self, concurrent_users: int = 10,
                                          duration_seconds: int = 30) -> Dict[str, Any]:
        """Perform load testing with concurrent users."""
        self.log(f"Load testing with {concurrent_users} concurrent users for {duration_seconds}s...")

        request_count = 0
        response_times = []
        start_time = time.time()
        end_time = start_time + duration_seconds

        async def user_simulation(user_id: int):
            nonlocal request_count, response_times
            local_requests = 0
            local_times = []

            while time.time() < end_time:
                # Alternate between different operations
                if local_requests % 3 == 0:
                    result = await self.make_request("GET", "/health")
                elif local_requests % 3 == 1:
                    # Try to create a prompt
                    prompt_data = {
                        "name": f"load_test_{user_id}_{int(time.time() * 1000)}",
                        "category": "load_test",
                        "content": f"Load test prompt from user {user_id}",
                        "created_by": f"user_{user_id}"
                    }
                    result = await self.make_request("POST", "/api/v1/prompts", prompt_data)
                else:
                    # Health check
                    result = await self.make_request("GET", "/health")

                if result["success"]:
                    local_times.append(result["response_time"])

                local_requests += 1
                await asyncio.sleep(0.1)  # 100ms between requests

            return {"requests": local_requests, "times": local_times}

        # Run concurrent users
        tasks = [user_simulation(i) for i in range(concurrent_users)]
        user_results = await asyncio.gather(*tasks)

        total_requests = sum(r["requests"] for r in user_results)
        all_response_times = []
        for r in user_results:
            all_response_times.extend(r["times"])

        actual_duration = time.time() - start_time

        results = {
            "concurrent_users": concurrent_users,
            "target_duration": duration_seconds,
            "actual_duration": actual_duration,
            "total_requests": total_requests,
            "requests_per_second": total_requests / actual_duration,
            "successful_requests": len(all_response_times)
        }

        if all_response_times:
            results.update(self.calculate_stats(all_response_times))

        return results

    def calculate_stats(self, times: List[float]) -> Dict[str, float]:
        """Calculate comprehensive statistics from timing data."""
        if not times:
            return {}

        sorted_times = sorted(times)
        return {
            "count": len(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "min": min(times),
            "max": max(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "95th_percentile": sorted_times[int(len(times) * 0.95)],
            "99th_percentile": sorted_times[int(len(times) * 0.99)],
            "p50": statistics.median(times),
            "p95": sorted_times[int(len(times) * 0.95)],
            "p99": sorted_times[int(len(times) * 0.99)]
        }

    def monitor_memory_usage(self, operation_name: str) -> Dict[str, float]:
        """Monitor memory usage during an operation."""
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "operation": operation_name,
            "timestamp": time.time()
        }

    async def run_quick_benchmark(self) -> Dict[str, Any]:
        """Run quick performance benchmark."""
        print("Running Quick Performance Benchmark...")
        print("=" * 50)

        if not await self.check_service_health():
            return {"error": "Prompt store service is not running"}

        results = {}

        # Health endpoint benchmark
        print("\n1. Health Endpoint Performance:")
        health_results = await self.benchmark_health_endpoint(50)
        results["health"] = health_results
        self.print_stats("Health Endpoint", health_results)

        # Basic prompt operations
        print("\n2. Prompt Operations Performance:")
        prompt_results = await self.benchmark_prompt_operations(20)
        results["prompts"] = prompt_results

        for operation, stats in prompt_results.items():
            if isinstance(stats, dict) and "mean" in stats:
                self.print_stats(f"Prompt {operation.title()}", stats)

        return results

    async def run_full_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive performance benchmark."""
        print("Running Full Performance Benchmark...")
        print("=" * 50)

        if not await self.check_service_health():
            return {"error": "Prompt store service is not running"}

        results = {}

        # Health endpoint benchmark
        print("\n1. Health Endpoint Performance (200 requests):")
        health_results = await self.benchmark_health_endpoint(200)
        results["health"] = health_results
        self.print_stats("Health Endpoint", health_results)

        # Comprehensive prompt operations
        print("\n2. Prompt Operations Performance (100 operations):")
        prompt_results = await self.benchmark_prompt_operations(100)
        results["prompts"] = prompt_results

        for operation, stats in prompt_results.items():
            if isinstance(stats, dict) and "mean" in stats:
                self.print_stats(f"Prompt {operation.title()}", stats)

        # Load testing
        print("\n3. Load Testing (20 concurrent users, 30 seconds):")
        load_results = await self.load_test_concurrent_requests(20, 30)
        results["load_test"] = load_results
        self.print_load_stats(load_results)

        return results

    async def run_load_test(self) -> Dict[str, Any]:
        """Run dedicated load testing."""
        print("Running Load Testing...")
        print("=" * 30)

        if not await self.check_service_health():
            return {"error": "Prompt store service is not running"}

        print("\nTesting different concurrency levels...")

        concurrency_levels = [5, 10, 20, 50]
        results = {}

        for concurrent_users in concurrency_levels:
            print(f"\nTesting with {concurrent_users} concurrent users (30 seconds):")
            load_results = await self.load_test_concurrent_requests(concurrent_users, 30)
            results[f"concurrency_{concurrent_users}"] = load_results
            self.print_load_stats(load_results)

        return results

    def print_stats(self, operation: str, stats: Dict[str, Any]):
        """Print formatted statistics."""
        if "error" in stats:
            print(f"  ❌ {operation}: {stats['error']}")
            return

        print(f"  ✓ {operation}:")
        print(".1f")
        print(".3f")
        print(".3f")
        print(".1f")
        if "95th_percentile" in stats:
            print(".3f")

    def print_load_stats(self, stats: Dict[str, Any]):
        """Print formatted load testing statistics."""
        print(".1f")
        print(".1f")
        if "mean" in stats:
            print(".3f")
            print(".3f")
            print(".1f")

    def save_results(self, results: Dict[str, Any], filename: str):
        """Save benchmark results to JSON file."""
        timestamp = int(time.time())
        filepath = Path(f"benchmark_results_{timestamp}.json")

        with open(filepath, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "results": results
            }, f, indent=2, default=str)

        print(f"\n📊 Results saved to {filepath}")


async def main():
    """Main benchmarking function."""
    parser = argparse.ArgumentParser(description="Prompt Store Performance Benchmarking")
    parser.add_argument("--url", default="http://localhost:5110",
                       help="Base URL of prompt_store service")
    parser.add_argument("--quick", action="store_true",
                       help="Run quick benchmark (fast, basic metrics)")
    parser.add_argument("--full", action="store_true",
                       help="Run full benchmark (comprehensive, takes longer)")
    parser.add_argument("--load-test", action="store_true",
                       help="Run load testing (stress testing with concurrency)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--save", action="store_true",
                       help="Save results to JSON file")

    args = parser.parse_args()

    if not any([args.quick, args.full, args.load_test]):
        args.quick = True  # Default to quick benchmark

    async with PerformanceBenchmarker(args.url, args.verbose) as benchmarker:
        try:
            if args.quick:
                results = await benchmarker.run_quick_benchmark()
            elif args.full:
                results = await benchmarker.run_full_benchmark()
            elif args.load_test:
                results = await benchmarker.run_load_test()

            if args.save:
                benchmarker.save_results(results, "benchmark_results.json")

        except KeyboardInterrupt:
            print("\n⚠️  Benchmark interrupted by user")
        except Exception as e:
            print(f"\n❌ Benchmark failed: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    print("Prompt Store Performance Benchmarking Tool")
    print("=" * 50)
    asyncio.run(main())
