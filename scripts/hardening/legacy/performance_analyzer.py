#!/usr/bin/env python3
"""
Performance Analyzer for Hackathon Ecosystem

This script analyzes performance metrics across all services by measuring
response times, throughput, and identifying potential bottlenecks.
"""

import asyncio
import aiohttp
import time
import statistics
from typing import Dict, List, Tuple
import json

# Services to test
PERFORMANCE_TARGETS = [
    ("discovery-agent", "5045", "/health"),
    ("doc_store", "5087", "/health"),
    ("llm-gateway", "5055", "/health"),
    ("code-analyzer", "5025", "/health"),
    ("unified-api-dashboard", "8000", "/health"),
    ("mock-data-generator", "5065", "/health"),
    ("orchestrator", "5099", "/health"),
]

async def measure_response_time(service_name: str, port: int, endpoint: str,
                               session: aiohttp.ClientSession, num_requests: int = 5) -> Dict:
    """Measure response times for a service endpoint."""
    url = f"http://localhost:{port}{endpoint}"
    response_times = []

    for i in range(num_requests):
        try:
            start_time = time.time()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    response_time = (time.time() - start_time) * 1000  # Convert to ms
                    response_times.append(response_time)
                else:
                    print(f"❌ {service_name} request {i+1}: HTTP {response.status}")
        except Exception as e:
            print(f"❌ {service_name} request {i+1}: {str(e)}")
        await asyncio.sleep(0.1)  # Small delay between requests

    if response_times:
        return {
            "service": service_name,
            "url": url,
            "requests_made": len(response_times),
            "avg_response_time": round(statistics.mean(response_times), 2),
            "min_response_time": round(min(response_times), 2),
            "max_response_time": round(max(response_times), 2),
            "median_response_time": round(statistics.median(response_times), 2),
            "std_dev": round(statistics.stdev(response_times), 2) if len(response_times) > 1 else 0,
            "success_rate": len(response_times) / num_requests * 100
        }
    else:
        return {
            "service": service_name,
            "url": url,
            "requests_made": 0,
            "error": "All requests failed"
        }

async def analyze_service_load(service_name: str, port: int, endpoint: str,
                              session: aiohttp.ClientSession) -> Dict:
    """Analyze how service performs under concurrent load."""
    url = f"http://localhost:{port}{endpoint}"
    num_concurrent = 10

    async def single_request():
        try:
            start_time = time.time()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                response_time = (time.time() - start_time) * 1000
                return response.status == 200, response_time
        except:
            return False, 0

    # Run concurrent requests
    start_time = time.time()
    tasks = [single_request() for _ in range(num_concurrent)]
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time

    successful = sum(1 for success, _ in results if success)
    response_times = [rt for _, rt in results if rt > 0]

    return {
        "service": service_name,
        "concurrent_requests": num_concurrent,
        "successful_requests": successful,
        "success_rate": successful / num_concurrent * 100,
        "total_time": round(total_time * 1000, 2),
        "avg_response_time": round(statistics.mean(response_times), 2) if response_times else 0,
        "throughput": round(num_concurrent / total_time, 2) if total_time > 0 else 0
    }

def analyze_bottlenecks(results: List[Dict]) -> List[str]:
    """Analyze results to identify potential bottlenecks."""
    issues = []

    # Check for slow services
    slow_threshold = 500  # ms
    for result in results:
        if "avg_response_time" in result and result["avg_response_time"] > slow_threshold:
            issues.append(f"⚠️  {result['service']}: High average response time ({result['avg_response_time']}ms)")

    # Check for high variance
    for result in results:
        if "std_dev" in result and result["std_dev"] > 100:
            issues.append(f"⚠️  {result['service']}: High response time variance ({result['std_dev']}ms std dev)")

    # Check for low success rates
    for result in results:
        if "success_rate" in result and result["success_rate"] < 80:
            issues.append(f"❌ {result['service']}: Low success rate ({result['success_rate']}%)")

    return issues

async def main():
    """Main performance analysis function."""
    print("⚡ Performance Analyzer - Hackathon Ecosystem")
    print("=" * 50)

    connector = aiohttp.TCPConnector(limit=20)
    timeout = aiohttp.ClientTimeout(total=10, connect=3)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        print("\n📊 Measuring Individual Response Times...")
        print("-" * 40)

        response_time_results = []
        for service_name, port, endpoint in PERFORMANCE_TARGETS:
            result = await measure_response_time(service_name, int(port), endpoint, session, 3)
            response_time_results.append(result)

            if "avg_response_time" in result:
                print(f"✅ {result['service']:<25} {result['avg_response_time']:>6.1f}ms avg "
                      f"({result['min_response_time']:.1f}-{result['max_response_time']:.1f}ms range)")
            else:
                print(f"❌ {result['service']:<25} Failed to measure")

        print("\n🔄 Testing Concurrent Load Performance...")
        print("-" * 40)

        load_test_results = []
        for service_name, port, endpoint in PERFORMANCE_TARGETS[:3]:  # Test first 3 services
            result = await analyze_service_load(service_name, int(port), endpoint, session)
            load_test_results.append(result)

            throughput = result.get("throughput", 0)
            success_rate = result.get("success_rate", 0)
            print(f"✅ {result['service']:<25} {throughput:>5.1f} req/sec "
                  f"({success_rate:>5.1f}% success)")

        # Analyze bottlenecks
        print("\n🔍 Analyzing Performance Bottlenecks...")
        print("-" * 40)

        all_results = response_time_results + load_test_results
        bottlenecks = analyze_bottlenecks(all_results)

        if bottlenecks:
            print("Found potential performance issues:")
            for issue in bottlenecks:
                print(f"  {issue}")
        else:
            print("✅ No significant performance bottlenecks detected")

        # Performance summary
        print("\n📈 Performance Summary:")
        print("-" * 30)

        successful_services = [r for r in response_time_results if "avg_response_time" in r]
        if successful_services:
            avg_overall = statistics.mean([r["avg_response_time"] for r in successful_services])
            print(f"   Overall Average Response Time: {avg_overall:.1f}ms")
            # Performance grade
            if avg_overall < 100:
                grade = "Excellent"
            elif avg_overall < 200:
                grade = "Good"
            elif avg_overall < 500:
                grade = "Fair"
            else:
                grade = "Needs Improvement"

            print(f"   Performance Grade: {grade}")

        # Recommendations
        print("\n💡 Recommendations:")
        if any(r.get("avg_response_time", 0) > 1000 for r in response_time_results):
            print("   • Consider implementing response caching")
        if any(r.get("std_dev", 0) > 200 for r in response_time_results):
            print("   • Investigate response time variance - may indicate resource contention")
        if any(r.get("success_rate", 100) < 95 for r in load_test_results):
            print("   • Service may need more resources under concurrent load")

        print("   • Monitor these metrics in production environment")

        # Exit with appropriate code
        has_issues = any(r.get("avg_response_time", 0) > 1000 for r in response_time_results) or \
                    any(r.get("success_rate", 100) < 80 for r in load_test_results)

        if has_issues:
            print("\n❌ Performance issues detected!")
            sys.exit(1)
        else:
            print("\n✅ Performance analysis completed successfully!")
            sys.exit(0)

if __name__ == "__main__":
    import sys
    asyncio.run(main())
