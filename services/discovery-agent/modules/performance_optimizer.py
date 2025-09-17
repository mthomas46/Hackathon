"""Performance Optimization Module for Discovery Agent service.

This module provides Phase 5 performance optimization and tool dependency
mapping capabilities to enhance discovery efficiency and tool orchestration.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import statistics


class PerformanceOptimizer:
    """Performance optimizer for discovery operations and tool dependency mapping"""

    def __init__(self):
        self.performance_history = {}
        self.dependency_graph = defaultdict(list)
        self.optimization_cache = {}

    async def optimize_discovery_workflow(self, discovery_results: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize discovery workflow based on performance analysis"""

        optimization_recommendations = {
            "parallelization_opportunities": [],
            "bottleneck_identification": [],
            "resource_optimization": [],
            "caching_strategies": [],
            "dependency_optimization": []
        }

        performance_data = discovery_results.get("performance_metrics", [])

        if not performance_data:
            return {"optimizations": [], "message": "No performance data available for optimization"}

        print("⚡ Analyzing discovery performance for optimization opportunities...")

        # Analyze response times for bottlenecks
        response_times = [p.get("response_time", 0) for p in performance_data]
        if response_times:
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)
            min_time = min(response_times)

            # Identify slow services (bottlenecks)
            slow_services = [p for p in performance_data if p.get("response_time", 0) > avg_time * 1.5]
            if slow_services:
                optimization_recommendations["bottleneck_identification"].extend([
                    {
                        "type": "slow_service",
                        "services": [s["service"] for s in slow_services],
                        "avg_slow_time": statistics.mean([s["response_time"] for s in slow_services]),
                        "recommendation": "Consider parallel processing or caching for slow services"
                    }
                ])

            # Identify fast services for parallelization
            fast_services = [p for p in performance_data if p.get("response_time", 0) < avg_time * 0.5]
            if len(fast_services) > 1:
                optimization_recommendations["parallelization_opportunities"].append({
                    "type": "parallel_batch",
                    "services": [s["service"] for s in fast_services],
                    "estimated_speedup": f"{len(fast_services)}x faster with parallel processing",
                    "recommendation": "Process these services in parallel batches"
                })

        # Analyze tool discovery patterns
        tools_per_service = [p.get("tools_found", 0) for p in performance_data]
        if tools_per_service:
            avg_tools = statistics.mean(tools_per_service)
            high_tool_services = [p for p in performance_data if p.get("tools_found", 0) > avg_tools * 2]

            if high_tool_services:
                optimization_recommendations["resource_optimization"].append({
                    "type": "high_yield_services",
                    "services": [s["service"] for s in high_tool_services],
                    "recommendation": "Prioritize these services in discovery workflows for maximum tool yield"
                })

        # Caching recommendations
        if len(performance_data) > 5:
            optimization_recommendations["caching_strategies"].append({
                "type": "discovery_results_cache",
                "recommendation": "Cache discovery results for 15-30 minutes to reduce repeated API calls",
                "estimated_benefit": "50-70% reduction in discovery time for repeated operations"
            })

        return {
            "optimizations": optimization_recommendations,
            "performance_summary": {
                "total_services": len(performance_data),
                "avg_response_time": avg_time if 'avg_time' in locals() else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "total_tools_found": sum(p.get("tools_found", 0) for p in performance_data)
            }
        }

    async def analyze_tool_dependencies(self, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze dependencies between discovered tools"""

        dependency_analysis = {
            "dependency_graph": {},
            "circular_dependencies": [],
            "independent_tools": [],
            "critical_path": [],
            "optimization_opportunities": []
        }

        print(f"🔗 Analyzing dependencies between {len(tools)} tools...")

        # Build dependency graph based on tool categories and capabilities
        for tool in tools:
            tool_name = tool["name"]
            category = tool.get("category", "unknown")
            capabilities = tool.get("capabilities", [])

            dependency_analysis["dependency_graph"][tool_name] = {
                "category": category,
                "capabilities": capabilities,
                "depends_on": [],
                "depended_by": []
            }

        # Analyze relationships
        for i, tool1 in enumerate(tools):
            for j, tool2 in enumerate(tools):
                if i == j:
                    continue

                relationship = self._analyze_tool_dependency(tool1, tool2)
                if relationship["depends"]:
                    dependency_analysis["dependency_graph"][tool1["name"]]["depends_on"].append({
                        "tool": tool2["name"],
                        "relationship": relationship["type"],
                        "strength": relationship["strength"]
                    })

        # Find independent tools (no dependencies)
        independent = []
        for tool_name, deps in dependency_analysis["dependency_graph"].items():
            if not deps["depends_on"]:
                independent.append(tool_name)

        dependency_analysis["independent_tools"] = independent

        # Identify optimization opportunities
        if len(independent) > 3:
            dependency_analysis["optimization_opportunities"].append({
                "type": "parallel_processing",
                "description": f"{len(independent)} independent tools can be processed in parallel",
                "tools": independent,
                "estimated_benefit": f"{len(independent)}x speedup for independent operations"
            })

        # Find tools with many dependencies (potential bottlenecks)
        dependency_counts = {}
        for tool_name, deps in dependency_analysis["dependency_graph"].items():
            dependency_counts[tool_name] = len(deps["depends_on"])

        high_dependency_tools = [tool for tool, count in dependency_counts.items() if count > 2]
        if high_dependency_tools:
            dependency_analysis["optimization_opportunities"].append({
                "type": "dependency_reduction",
                "description": f"Tools with high dependencies: {', '.join(high_dependency_tools)}",
                "recommendation": "Consider breaking down complex tools or optimizing dependency chains"
            })

        return dependency_analysis

    def _analyze_tool_dependency(self, tool1: Dict[str, Any], tool2: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze dependency relationship between two tools"""

        # Data flow dependencies
        data_patterns = [
            ("storage", "analysis", "data_dependency"),
            ("analysis", "storage", "result_persistence"),
            ("generation", "analysis", "content_validation"),
            ("search", "analysis", "result_processing"),
            ("processing", "storage", "processed_data_storage")
        ]

        category1 = tool1.get("category", "").lower()
        category2 = tool2.get("category", "").lower()

        for input_cat, output_cat, dep_type in data_patterns:
            if input_cat in category1 and output_cat in category2:
                return {
                    "depends": True,
                    "type": dep_type,
                    "direction": f"{tool1['name']} -> {tool2['name']}",
                    "strength": 0.8
                }
            elif input_cat in category2 and output_cat in category1:
                return {
                    "depends": True,
                    "type": dep_type,
                    "direction": f"{tool2['name']} -> {tool1['name']}",
                    "strength": 0.8
                }

        # Capability-based dependencies
        caps1 = set(tool1.get("capabilities", []))
        caps2 = set(tool2.get("capabilities", []))

        if caps1 & caps2:  # Shared capabilities might indicate dependencies
            return {
                "depends": True,
                "type": "capability_sharing",
                "direction": f"{tool1['name']} ↔ {tool2['name']}",
                "strength": 0.5
            }

        return {"depends": False, "type": "none", "strength": 0.0}

    async def optimize_workflow_execution(self, workflow_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize workflow execution based on dependencies and performance"""

        optimization_result = {
            "original_workflow": workflow_spec,
            "optimized_workflow": workflow_spec.copy(),
            "optimizations_applied": [],
            "estimated_performance_gain": 0,
            "parallelization_suggestions": []
        }

        steps = workflow_spec.get("steps", [])
        if len(steps) < 2:
            return optimization_result  # No optimization needed for single-step workflows

        print(f"⚡ Optimizing workflow with {len(steps)} steps...")

        # Analyze step dependencies
        step_dependencies = self._analyze_step_dependencies(steps)

        # Identify parallelizable steps
        parallel_groups = self._identify_parallel_groups(steps, step_dependencies)

        if len(parallel_groups) > 1:
            optimization_result["parallelization_suggestions"].extend(parallel_groups)
            optimization_result["optimizations_applied"].append("parallel_execution")
            optimization_result["estimated_performance_gain"] += len(parallel_groups) * 0.3  # 30% per parallel group

        # Optimize resource allocation
        resource_optimization = self._optimize_resource_allocation(steps)
        if resource_optimization["optimizations"]:
            optimization_result["optimizations_applied"].extend(resource_optimization["optimizations"])
            optimization_result["estimated_performance_gain"] += resource_optimization["gain"]

        # Create optimized workflow spec
        if optimization_result["optimizations_applied"]:
            optimized_spec = workflow_spec.copy()
            optimized_spec["optimization_metadata"] = {
                "applied_optimizations": optimization_result["optimizations_applied"],
                "estimated_performance_gain": optimization_result["estimated_performance_gain"],
                "parallel_groups": len(parallel_groups),
                "optimized_at": "2025-01-17T21:30:00Z"
            }
            optimization_result["optimized_workflow"] = optimized_spec

        return optimization_result

    def _analyze_step_dependencies(self, steps: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Analyze dependencies between workflow steps"""

        dependencies = {}

        for i, step in enumerate(steps):
            step_name = step.get("step_name", f"step_{i}")
            depends_on = []

            # Simple dependency analysis based on step descriptions
            step_desc = step.get("description", "").lower()

            for j, prev_step in enumerate(steps[:i]):
                prev_desc = prev_step.get("description", "").lower()
                prev_name = prev_step.get("step_name", f"step_{j}")

                # Look for sequential patterns
                if any(word in prev_desc for word in ["generate", "create", "produce"]) and \
                   any(word in step_desc for word in ["analyze", "process", "validate"]):
                    depends_on.append(prev_name)
                elif any(word in prev_desc for word in ["analyze", "process"]) and \
                     any(word in step_desc for word in ["store", "save", "persist"]):
                    depends_on.append(prev_name)

            dependencies[step_name] = depends_on

        return dependencies

    def _identify_parallel_groups(self, steps: List[Dict[str, Any]], dependencies: Dict[str, List[str]]) -> List[List[str]]:
        """Identify groups of steps that can be executed in parallel"""

        parallel_groups = []
        processed_steps = set()

        for step in steps:
            step_name = step.get("step_name", "")
            if step_name in processed_steps:
                continue

            # Find steps with no dependencies that can run in parallel
            independent_steps = []
            for s in steps:
                s_name = s.get("step_name", "")
                if s_name not in processed_steps and not dependencies.get(s_name, []):
                    independent_steps.append(s_name)

            if len(independent_steps) > 1:
                parallel_groups.append(independent_steps)
                processed_steps.update(independent_steps)
            elif independent_steps:
                processed_steps.update(independent_steps)

        return parallel_groups

    def _optimize_resource_allocation(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize resource allocation for workflow steps"""

        optimization = {
            "optimizations": [],
            "gain": 0
        }

        # Analyze tool usage patterns
        tool_usage = defaultdict(int)
        for step in steps:
            tool = step.get("tool", "")
            tool_usage[tool] += 1

        # Identify tools used multiple times
        frequently_used_tools = [tool for tool, count in tool_usage.items() if count > 1]

        if frequently_used_tools:
            optimization["optimizations"].append("connection_pooling")
            optimization["gain"] += 0.2  # 20% performance gain
            optimization["description"] = f"Optimize connection pooling for frequently used tools: {', '.join(frequently_used_tools)}"

        # Check for memory-intensive operations
        memory_intensive_tools = []
        for step in steps:
            tool = step.get("tool", "").lower()
            if any(word in tool for word in ["analyze", "process", "transform"]):
                memory_intensive_tools.append(step.get("step_name", ""))

        if memory_intensive_tools:
            optimization["optimizations"].append("memory_optimization")
            optimization["gain"] += 0.15  # 15% performance gain

        return optimization

    async def create_performance_baseline(self, discovery_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create performance baseline for future optimization comparisons"""

        baseline = {
            "timestamp": "2025-01-17T21:30:00Z",
            "services_tested": discovery_results.get("services_tested", 0),
            "healthy_services": discovery_results.get("healthy_services", 0),
            "total_tools": discovery_results.get("total_tools_discovered", 0),
            "avg_response_time": 0,
            "performance_percentiles": {},
            "service_performance": {},
            "baseline_metrics": {}
        }

        performance_data = discovery_results.get("performance_metrics", [])

        if performance_data:
            response_times = [p.get("response_time", 0) for p in performance_data]

            if response_times:
                baseline["avg_response_time"] = statistics.mean(response_times)
                baseline["performance_percentiles"] = {
                    "p50": statistics.median(response_times),
                    "p95": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times),
                    "p99": statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times)
                }

            # Service-specific baselines
            for metric in performance_data:
                service = metric.get("service", "unknown")
                baseline["service_performance"][service] = {
                    "avg_response_time": metric.get("response_time", 0),
                    "tools_found": metric.get("tools_found", 0),
                    "endpoints_found": metric.get("endpoints_found", 0)
                }

        baseline["baseline_metrics"] = {
            "tools_per_second": baseline["total_tools"] / max(baseline["avg_response_time"], 1),
            "services_per_second": baseline["services_tested"] / max(baseline["avg_response_time"] * baseline["services_tested"], 1),
            "health_rate": baseline["healthy_services"] / max(baseline["services_tested"], 1)
        }

        print("📊 Performance baseline established:")
        print(f"  📈 Avg response time: {baseline['avg_response_time']:.2f}s")
        print(f"  🎯 Tools discovered: {baseline['total_tools']}")
        print(f"  ⚡ Tools/second: {baseline['baseline_metrics']['tools_per_second']:.2f}")

        return baseline

    async def monitor_performance_trends(self, current_results: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor performance trends against baseline"""

        trends = {
            "comparison_timestamp": "2025-01-17T21:30:00Z",
            "baseline_timestamp": baseline.get("timestamp"),
            "performance_changes": {},
            "trend_analysis": [],
            "recommendations": []
        }

        # Compare current performance with baseline
        current_avg_time = current_results.get("summary", {}).get("avg_response_time", 0)
        baseline_avg_time = baseline.get("avg_response_time", 0)

        if baseline_avg_time > 0:
            time_change_pct = ((current_avg_time - baseline_avg_time) / baseline_avg_time) * 100
            trends["performance_changes"]["avg_response_time"] = {
                "change_percent": time_change_pct,
                "trend": "improving" if time_change_pct < 0 else "degrading",
                "significance": "significant" if abs(time_change_pct) > 10 else "minor"
            }

        # Analyze tool discovery efficiency
        current_tools = current_results.get("total_tools_discovered", 0)
        baseline_tools = baseline.get("total_tools")
        tools_change_pct = ((current_tools - baseline_tools) / max(baseline_tools, 1)) * 100

        trends["performance_changes"]["tool_discovery_efficiency"] = {
            "change_percent": tools_change_pct,
            "trend": "improving" if tools_change_pct > 0 else "stable",
            "current_tools": current_tools,
            "baseline_tools": baseline_tools
        }

        # Generate trend analysis
        if trends["performance_changes"].get("avg_response_time", {}).get("trend") == "degrading":
            trends["trend_analysis"].append("Response times are increasing - investigate performance bottlenecks")
            trends["recommendations"].append("Consider implementing caching or optimizing slow services")

        if trends["performance_changes"].get("tool_discovery_efficiency", {}).get("trend") == "improving":
            trends["trend_analysis"].append("Tool discovery efficiency is improving")
            trends["recommendations"].append("Continue monitoring and optimizing discovery patterns")

        return trends


# Create singleton instance
performance_optimizer = PerformanceOptimizer()
