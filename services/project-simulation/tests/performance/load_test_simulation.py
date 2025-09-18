"""Load Testing - Concurrent Simulation Execution Performance Validation.

This module provides comprehensive load testing capabilities for the project-simulation
service, including concurrent simulation execution, performance metrics collection,
and scalability validation.
"""

import asyncio
import time
import statistics
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import json
import sys
from pathlib import Path

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.di_container import get_simulation_container
from simulation.domain.value_objects import ProjectType, ComplexityLevel


class SimulationLoadTester:
    """Load testing framework for concurrent simulation execution."""

    def __init__(self,
                 base_url: str = "http://localhost:5075",
                 max_concurrent: int = 10,
                 test_duration_seconds: int = 300):
        """Initialize load tester.

        Args:
            base_url: Base URL of the simulation service
            max_concurrent: Maximum concurrent simulations
            test_duration_seconds: Test duration in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.max_concurrent = max_concurrent
        self.test_duration_seconds = test_duration_seconds
        self.logger = get_simulation_logger()

        # Test metrics
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "total_simulations_created": 0,
            "total_simulations_executed": 0,
            "successful_simulations": 0,
            "failed_simulations": 0,
            "response_times": [],
            "errors": [],
            "throughput": [],
            "resource_usage": []
        }

    async def run_load_test(self) -> Dict[str, Any]:
        """Run comprehensive load test."""
        self.logger.info(
            "Starting simulation load test",
            max_concurrent=self.max_concurrent,
            duration_seconds=self.test_duration_seconds
        )

        self.metrics["start_time"] = datetime.now()

        try:
            # Run different test scenarios
            test_results = []

            # Test 1: Ramp-up concurrent simulations
            ramp_results = await self._test_ramp_up_concurrent()
            test_results.append({"test": "ramp_up_concurrent", "results": ramp_results})

            # Test 2: Sustained concurrent load
            sustained_results = await self._test_sustained_load()
            test_results.append({"test": "sustained_load", "results": sustained_results})

            # Test 3: Burst load testing
            burst_results = await self._test_burst_load()
            test_results.append({"test": "burst_load", "results": burst_results})

            # Test 4: Mixed workload testing
            mixed_results = await self._test_mixed_workload()
            test_results.append({"test": "mixed_workload", "results": mixed_results})

            # Calculate final metrics
            self.metrics["end_time"] = datetime.now()
            final_metrics = self._calculate_final_metrics(test_results)

            self.logger.info(
                "Load test completed",
                total_simulations=self.metrics["total_simulations_created"],
                successful_simulations=self.metrics["successful_simulations"],
                failed_simulations=self.metrics["failed_simulations"],
                average_response_time=final_metrics.get("average_response_time", 0),
                throughput_per_second=final_metrics.get("throughput_per_second", 0)
            )

            return {
                "success": True,
                "test_duration_seconds": self.test_duration_seconds,
                "metrics": self.metrics,
                "final_metrics": final_metrics,
                "test_results": test_results,
                "recommendations": self._generate_recommendations(final_metrics)
            }

        except Exception as e:
            self.logger.error("Load test failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "metrics": self.metrics
            }

    async def _test_ramp_up_concurrent(self) -> Dict[str, Any]:
        """Test gradual increase in concurrent simulations."""
        self.logger.info("Running ramp-up concurrent test")

        results = {
            "test_type": "ramp_up",
            "phases": [],
            "metrics": {}
        }

        # Test phases with increasing concurrency
        concurrency_levels = [1, 2, 5, 10, 15, 20]

        for concurrency in concurrency_levels:
            if concurrency > self.max_concurrent:
                break

            phase_start = time.time()

            # Run concurrent simulations
            tasks = []
            for i in range(concurrency):
                tasks.append(self._run_single_simulation_test())

            # Execute concurrently
            phase_results = await asyncio.gather(*tasks, return_exceptions=True)

            phase_duration = time.time() - phase_start

            # Analyze phase results
            successful = sum(1 for r in phase_results if not isinstance(r, Exception))
            failed = len(phase_results) - successful

            phase_metrics = {
                "concurrency_level": concurrency,
                "phase_duration": phase_duration,
                "successful_simulations": successful,
                "failed_simulations": failed,
                "success_rate": successful / len(phase_results),
                "throughput_per_second": len(phase_results) / phase_duration
            }

            results["phases"].append(phase_metrics)

            self.logger.info(
                "Ramp-up phase completed",
                concurrency=concurrency,
                success_rate=phase_metrics["success_rate"],
                throughput=phase_metrics["throughput_per_second"]
            )

        results["metrics"] = self._analyze_ramp_up_results(results["phases"])
        return results

    async def _test_sustained_load(self) -> Dict[str, Any]:
        """Test sustained concurrent load over time."""
        self.logger.info("Running sustained load test")

        test_start = time.time()
        results = {
            "test_type": "sustained",
            "intervals": [],
            "metrics": {}
        }

        # Run for test duration with sustained concurrency
        concurrency = min(self.max_concurrent, 10)  # Use reasonable sustained load

        while time.time() - test_start < self.test_duration_seconds:
            interval_start = time.time()

            # Run concurrent simulations
            tasks = [self._run_single_simulation_test() for _ in range(concurrency)]
            interval_results = await asyncio.gather(*tasks, return_exceptions=True)

            interval_duration = time.time() - interval_start

            # Record interval metrics
            successful = sum(1 for r in interval_results if not isinstance(r, Exception))
            failed = len(interval_results) - successful

            interval_metrics = {
                "timestamp": datetime.now().isoformat(),
                "concurrency": concurrency,
                "interval_duration": interval_duration,
                "successful_simulations": successful,
                "failed_simulations": failed,
                "success_rate": successful / len(interval_results),
                "throughput_per_second": len(interval_results) / interval_duration
            }

            results["intervals"].append(interval_metrics)

            # Brief pause between intervals
            await asyncio.sleep(1)

        results["metrics"] = self._analyze_sustained_results(results["intervals"])
        return results

    async def _test_burst_load(self) -> Dict[str, Any]:
        """Test burst load scenarios."""
        self.logger.info("Running burst load test")

        results = {
            "test_type": "burst",
            "bursts": [],
            "metrics": {}
        }

        # Run multiple burst scenarios
        burst_scenarios = [
            {"concurrency": 20, "duration": 30},  # High concurrency short duration
            {"concurrency": 50, "duration": 10},  # Very high concurrency very short
            {"concurrency": 5, "duration": 60},   # Low concurrency long duration
        ]

        for scenario in burst_scenarios:
            burst_start = time.time()

            # Create burst of concurrent requests
            tasks = [self._run_single_simulation_test() for _ in range(scenario["concurrency"])]

            # Execute burst
            burst_results = await asyncio.gather(*tasks, return_exceptions=True)

            burst_duration = time.time() - burst_start

            # Analyze burst results
            successful = sum(1 for r in burst_results if not isinstance(r, Exception))
            failed = len(burst_results) - successful

            burst_metrics = {
                "scenario": scenario,
                "burst_duration": burst_duration,
                "successful_simulations": successful,
                "failed_simulations": failed,
                "success_rate": successful / len(burst_results),
                "throughput_per_second": len(burst_results) / burst_duration
            }

            results["bursts"].append(burst_metrics)

            self.logger.info(
                "Burst test completed",
                scenario=scenario,
                success_rate=burst_metrics["success_rate"],
                throughput=burst_metrics["throughput_per_second"]
            )

        results["metrics"] = self._analyze_burst_results(results["bursts"])
        return results

    async def _test_mixed_workload(self) -> Dict[str, Any]:
        """Test mixed workload patterns."""
        self.logger.info("Running mixed workload test")

        results = {
            "test_type": "mixed",
            "workload_patterns": [],
            "metrics": {}
        }

        # Different workload patterns
        patterns = [
            {"name": "read_heavy", "create_ratio": 0.2, "execute_ratio": 0.3, "status_ratio": 0.5},
            {"name": "write_heavy", "create_ratio": 0.6, "execute_ratio": 0.3, "status_ratio": 0.1},
            {"name": "balanced", "create_ratio": 0.4, "execute_ratio": 0.4, "status_ratio": 0.2},
        ]

        for pattern in patterns:
            pattern_start = time.time()

            # Generate mixed workload based on ratios
            total_requests = 100
            create_count = int(total_requests * pattern["create_ratio"])
            execute_count = int(total_requests * pattern["execute_ratio"])
            status_count = int(total_requests * pattern["status_ratio"])

            # Execute mixed workload
            tasks = []

            # Add create simulation tasks
            for i in range(create_count):
                tasks.append(self._run_simulation_creation_only())

            # Add execute simulation tasks (need existing simulations)
            for i in range(min(execute_count, self.metrics["total_simulations_created"])):
                if i < len(self.created_simulation_ids):
                    tasks.append(self._run_simulation_execution_only(self.created_simulation_ids[i]))

            # Add status check tasks
            for i in range(min(status_count, self.metrics["total_simulations_created"])):
                if i < len(self.created_simulation_ids):
                    tasks.append(self._run_simulation_status_only(self.created_simulation_ids[i]))

            # Execute mixed workload
            if tasks:
                mixed_results = await asyncio.gather(*tasks, return_exceptions=True)
                pattern_duration = time.time() - pattern_start

                successful = sum(1 for r in mixed_results if not isinstance(r, Exception))
                failed = len(mixed_results) - successful

                pattern_metrics = {
                    "pattern": pattern,
                    "pattern_duration": pattern_duration,
                    "total_requests": len(tasks),
                    "successful_requests": successful,
                    "failed_requests": failed,
                    "success_rate": successful / len(tasks) if tasks else 0,
                    "throughput_per_second": len(tasks) / pattern_duration if pattern_duration > 0 else 0
                }

                results["workload_patterns"].append(pattern_metrics)

        results["metrics"] = self._analyze_mixed_workload_results(results["workload_patterns"])
        return results

    async def _run_single_simulation_test(self) -> Dict[str, Any]:
        """Run a single complete simulation test (create + execute)."""
        import httpx

        start_time = time.time()

        try:
            # Create simulation
            simulation_data = self._generate_random_simulation_data()

            async with httpx.AsyncClient(timeout=30.0) as client:
                create_response = await client.post(
                    f"{self.base_url}/api/v1/simulations",
                    json=simulation_data
                )

                if create_response.status_code != 201:
                    raise Exception(f"Create failed: {create_response.status_code}")

                create_data = create_response.json()
                simulation_id = create_data["data"]["simulation_id"]

                self.metrics["total_simulations_created"] += 1

                # Execute simulation
                execute_response = await client.post(
                    f"{self.base_url}/api/v1/simulations/{simulation_id}/execute"
                )

                if execute_response.status_code not in [200, 202]:
                    raise Exception(f"Execute failed: {execute_response.status_code}")

                self.metrics["total_simulations_executed"] += 1
                self.metrics["successful_simulations"] += 1

                response_time = time.time() - start_time
                self.metrics["response_times"].append(response_time)

                return {
                    "success": True,
                    "simulation_id": simulation_id,
                    "response_time": response_time
                }

        except Exception as e:
            response_time = time.time() - start_time
            self.metrics["failed_simulations"] += 1
            self.metrics["errors"].append({
                "error": str(e),
                "response_time": response_time,
                "timestamp": datetime.now().isoformat()
            })

            return {
                "success": False,
                "error": str(e),
                "response_time": response_time
            }

    async def _run_simulation_creation_only(self) -> Dict[str, Any]:
        """Run simulation creation only."""
        import httpx

        start_time = time.time()

        try:
            simulation_data = self._generate_random_simulation_data()

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/simulations",
                    json=simulation_data
                )

                if response.status_code != 201:
                    raise Exception(f"Create failed: {response.status_code}")

                self.metrics["total_simulations_created"] += 1
                response_time = time.time() - start_time
                self.metrics["response_times"].append(response_time)

                return {"success": True, "response_time": response_time}

        except Exception as e:
            response_time = time.time() - start_time
            self.metrics["errors"].append({
                "error": str(e),
                "response_time": response_time,
                "operation": "create"
            })
            return {"success": False, "error": str(e)}

    async def _run_simulation_execution_only(self, simulation_id: str) -> Dict[str, Any]:
        """Run simulation execution only."""
        import httpx

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/simulations/{simulation_id}/execute"
                )

                if response.status_code not in [200, 202]:
                    raise Exception(f"Execute failed: {response.status_code}")

                response_time = time.time() - start_time
                self.metrics["response_times"].append(response_time)

                return {"success": True, "response_time": response_time}

        except Exception as e:
            response_time = time.time() - start_time
            self.metrics["errors"].append({
                "error": str(e),
                "response_time": response_time,
                "operation": "execute",
                "simulation_id": simulation_id
            })
            return {"success": False, "error": str(e)}

    async def _run_simulation_status_only(self, simulation_id: str) -> Dict[str, Any]:
        """Run simulation status check only."""
        import httpx

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/simulations/{simulation_id}"
                )

                if response.status_code != 200:
                    raise Exception(f"Status check failed: {response.status_code}")

                response_time = time.time() - start_time
                self.metrics["response_times"].append(response_time)

                return {"success": True, "response_time": response_time}

        except Exception as e:
            response_time = time.time() - start_time
            self.metrics["errors"].append({
                "error": str(e),
                "response_time": response_time,
                "operation": "status",
                "simulation_id": simulation_id
            })
            return {"success": False, "error": str(e)}

    def _generate_random_simulation_data(self) -> Dict[str, Any]:
        """Generate random simulation data for testing."""
        import random

        project_types = ["web_application", "api_service", "mobile_application", "data_science", "devops_tool"]
        complexities = ["simple", "medium", "complex"]

        return {
            "name": f"LoadTest-{datetime.now().strftime('%H%M%S')}-{random.randint(1000, 9999)}",
            "description": f"Load testing simulation created at {datetime.now().isoformat()}",
            "type": random.choice(project_types),
            "team_size": random.randint(3, 8),
            "complexity": random.choice(complexities),
            "duration_weeks": random.randint(4, 12)
        }

    def _calculate_final_metrics(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate final comprehensive metrics."""
        if not self.metrics["response_times"]:
            return {}

        response_times = self.metrics["response_times"]

        return {
            "total_simulations_created": self.metrics["total_simulations_created"],
            "total_simulations_executed": self.metrics["total_simulations_executed"],
            "successful_simulations": self.metrics["successful_simulations"],
            "failed_simulations": self.metrics["failed_simulations"],
            "success_rate": self.metrics["successful_simulations"] / max(self.metrics["total_simulations_created"], 1),

            "average_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "response_time_stddev": statistics.stdev(response_times) if len(response_times) > 1 else 0,

            "total_test_duration_seconds": self.test_duration_seconds,
            "average_throughput_per_second": len(response_times) / self.test_duration_seconds,

            "error_rate": len(self.metrics["errors"]) / max(len(response_times), 1),
            "error_breakdown": self._analyze_errors(),

            "performance_score": self._calculate_performance_score(),
            "scalability_rating": self._calculate_scalability_rating(test_results)
        }

    def _analyze_ramp_up_results(self, phases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze ramp-up test results."""
        if not phases:
            return {}

        success_rates = [p["success_rate"] for p in phases]
        throughputs = [p["throughput_per_second"] for p in phases]

        return {
            "optimal_concurrency": phases[-1]["concurrency_level"] if phases else 0,
            "average_success_rate": statistics.mean(success_rates),
            "max_throughput": max(throughputs),
            "throughput_stability": statistics.stdev(throughputs) / statistics.mean(throughputs) if throughputs else 0,
            "bottleneck_concurrency": self._find_bottleneck_concurrency(phases)
        }

    def _analyze_sustained_results(self, intervals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sustained load test results."""
        if not intervals:
            return {}

        success_rates = [i["success_rate"] for i in intervals]
        throughputs = [i["throughput_per_second"] for i in intervals]

        return {
            "average_success_rate": statistics.mean(success_rates),
            "success_rate_stability": statistics.stdev(success_rates) if len(success_rates) > 1 else 0,
            "average_throughput": statistics.mean(throughputs),
            "throughput_stability": statistics.stdev(throughputs) / statistics.mean(throughputs) if throughputs else 0,
            "performance_degradation": self._calculate_performance_degradation(intervals)
        }

    def _analyze_burst_results(self, bursts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze burst load test results."""
        if not bursts:
            return {}

        success_rates = [b["success_rate"] for b in bursts]
        throughputs = [b["throughput_per_second"] for b in bursts]

        return {
            "burst_success_rate": statistics.mean(success_rates),
            "max_burst_throughput": max(throughputs),
            "burst_resilience_score": self._calculate_burst_resilience(bursts)
        }

    def _analyze_mixed_workload_results(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze mixed workload test results."""
        if not patterns:
            return {}

        pattern_performance = {}
        for pattern in patterns:
            pattern_name = pattern["pattern"]["name"]
            pattern_performance[pattern_name] = {
                "success_rate": pattern["success_rate"],
                "throughput": pattern["throughput_per_second"]
            }

        return {
            "pattern_performance": pattern_performance,
            "best_performing_pattern": max(pattern_performance.items(), key=lambda x: x[1]["throughput"]),
            "worst_performing_pattern": min(pattern_performance.items(), key=lambda x: x[1]["throughput"])
        }

    def _analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns."""
        if not self.metrics["errors"]:
            return {}

        error_types = {}
        for error in self.metrics["errors"]:
            error_type = error.get("operation", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            "total_errors": len(self.metrics["errors"]),
            "error_types": error_types,
            "most_common_error": max(error_types.items(), key=lambda x: x[1]) if error_types else None
        }

    def _find_bottleneck_concurrency(self, phases: List[Dict[str, Any]]) -> int:
        """Find the concurrency level where performance starts degrading."""
        if len(phases) < 2:
            return phases[0]["concurrency_level"] if phases else 0

        for i in range(1, len(phases)):
            current_success = phases[i]["success_rate"]
            previous_success = phases[i-1]["success_rate"]

            # If success rate drops significantly, that's the bottleneck
            if previous_success - current_success > 0.1:  # 10% drop
                return phases[i]["concurrency_level"]

        return phases[-1]["concurrency_level"]

    def _calculate_performance_degradation(self, intervals: List[Dict[str, Any]]) -> float:
        """Calculate performance degradation over time."""
        if len(intervals) < 2:
            return 0.0

        first_throughput = intervals[0]["throughput_per_second"]
        last_throughput = intervals[-1]["throughput_per_second"]

        if first_throughput == 0:
            return 0.0

        return (first_throughput - last_throughput) / first_throughput

    def _calculate_burst_resilience(self, bursts: List[Dict[str, Any]]) -> float:
        """Calculate burst resilience score."""
        if not bursts:
            return 0.0

        success_rates = [b["success_rate"] for b in bursts]
        avg_success = statistics.mean(success_rates)

        # Resilience score based on how well system handles bursts
        resilience_score = min(avg_success * 2, 1.0)  # Scale up to max 1.0

        return resilience_score

    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score."""
        if not self.metrics["response_times"]:
            return 0.0

        response_times = self.metrics["response_times"]

        # Performance score based on response time and success rate
        avg_response_time = statistics.mean(response_times)
        success_rate = self.metrics["successful_simulations"] / max(self.metrics["total_simulations_created"], 1)

        # Normalize response time (faster is better)
        response_score = max(0, 1 - (avg_response_time / 10))  # 10 seconds as baseline

        # Combined score
        performance_score = (response_score * 0.6) + (success_rate * 0.4)

        return min(max(performance_score, 0.0), 1.0)

    def _calculate_scalability_rating(self, test_results: List[Dict[str, Any]]) -> str:
        """Calculate scalability rating based on test results."""
        performance_score = self._calculate_performance_score()

        if performance_score >= 0.9:
            return "excellent"
        elif performance_score >= 0.8:
            return "good"
        elif performance_score >= 0.7:
            return "fair"
        elif performance_score >= 0.6:
            return "poor"
        else:
            return "critical"

    def _generate_recommendations(self, final_metrics: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations based on test results."""
        recommendations = []

        success_rate = final_metrics.get("success_rate", 0)
        avg_response_time = final_metrics.get("average_response_time", 0)
        scalability = final_metrics.get("scalability_rating", "unknown")

        if success_rate < 0.9:
            recommendations.append("Improve error handling and service resilience")
            recommendations.append("Consider implementing circuit breaker patterns")

        if avg_response_time > 5:
            recommendations.append("Optimize database queries and response times")
            recommendations.append("Consider implementing caching mechanisms")

        if scalability in ["poor", "critical"]:
            recommendations.append("Scale infrastructure resources (CPU, memory)")
            recommendations.append("Implement load balancing and horizontal scaling")

        if not recommendations:
            recommendations.append("System performance is excellent - continue monitoring")

        return recommendations

    # Initialize tracking for mixed workload tests
    def __init_tracking(self):
        """Initialize tracking for test operations."""
        self.created_simulation_ids = []

    async def _run_single_simulation_test(self) -> Dict[str, Any]:
        """Run a single complete simulation test (create + execute)."""
        result = await super()._run_single_simulation_test()

        # Track created simulation IDs for mixed workload tests
        if result.get("success") and result.get("simulation_id"):
            self.created_simulation_ids.append(result["simulation_id"])

        return result


# Global load tester instance
_load_tester: Optional[SimulationLoadTester] = None


def get_simulation_load_tester(base_url: str = "http://localhost:5075",
                              max_concurrent: int = 10,
                              test_duration_seconds: int = 300) -> SimulationLoadTester:
    """Get the global simulation load tester instance."""
    global _load_tester
    if _load_tester is None:
        _load_tester = SimulationLoadTester(
            base_url=base_url,
            max_concurrent=max_concurrent,
            test_duration_seconds=test_duration_seconds
        )
        _load_tester.__init_tracking()
    return _load_tester


async def run_load_test(base_url: str = "http://localhost:5075",
                       max_concurrent: int = 10,
                       test_duration_seconds: int = 300) -> Dict[str, Any]:
    """Run a comprehensive load test."""
    tester = get_simulation_load_tester(base_url, max_concurrent, test_duration_seconds)
    return await tester.run_load_test()


__all__ = [
    'SimulationLoadTester',
    'get_simulation_load_tester',
    'run_load_test'
]
