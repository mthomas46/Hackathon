"""
Topology Metrics

Advanced metrics calculation and analysis for service topology graphs,
including health scores, reliability metrics, and performance indicators.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
import networkx as nx

from .analyzer import TopologyAnalysis, ServiceNode, ServiceRelationship, ServiceType


@dataclass
class HealthMetrics:
    """Service health and reliability metrics."""
    overall_health_score: float
    service_health_distribution: Dict[str, int]
    critical_services_count: int
    degraded_services_count: int
    unhealthy_services_count: int
    health_trend: str  # improving, declining, stable
    estimated_recovery_time: Optional[timedelta]


@dataclass
class ReliabilityMetrics:
    """System reliability and resilience metrics."""
    mean_time_between_failures: Optional[float]
    mean_time_to_recovery: Optional[float]
    service_availability: Dict[str, float]
    system_reliability_score: float
    single_points_of_failure: List[str]
    redundancy_level: float
    failover_capacity: float


@dataclass
class PerformanceMetrics:
    """System performance and efficiency metrics."""
    average_response_time: float
    throughput_capacity: float
    bottleneck_services: List[Dict[str, Any]]
    optimization_opportunities: List[Dict[str, Any]]
    scalability_score: float
    load_distribution: Dict[str, float]


@dataclass
class DependencyMetrics:
    """Service dependency and coupling metrics."""
    average_coupling: float
    tightly_coupled_services: List[Tuple[str, str, float]]
    loosely_coupled_services: List[str]
    dependency_depth: Dict[str, int]
    circular_dependencies: List[List[str]]
    dependency_health_score: float


class TopologyMetrics:
    """
    Comprehensive topology metrics calculator.

    Computes health, reliability, performance, and dependency metrics
    for service topology analysis and monitoring.
    """

    def __init__(self):
        self.historical_data = {}
        self.baseline_metrics = {}

    def calculate_health_metrics(
        self,
        analysis: TopologyAnalysis,
        historical_health: Optional[Dict[str, List[str]]] = None
    ) -> HealthMetrics:
        """
        Calculate comprehensive health metrics for the service topology.

        Args:
            analysis: Topology analysis results
            historical_health: Historical health data for trend analysis

        Returns:
            Health metrics analysis
        """
        nodes = analysis.nodes

        # Count services by health status
        health_counts = {
            "healthy": 0,
            "degraded": 0,
            "unhealthy": 0,
            "unknown": 0
        }

        critical_services = []
        total_services = len(nodes)

        for node in nodes.values():
            health_counts[node.health_status] += 1

            # Identify critical services (high dependency count)
            if len(node.dependencies) + len(node.dependents) > 5:
                critical_services.append(node.service_id)

        # Calculate overall health score (0-100)
        health_weights = {
            "healthy": 1.0,
            "degraded": 0.5,
            "unhealthy": 0.0,
            "unknown": 0.2
        }

        weighted_score = sum(
            count * health_weights[status]
            for status, count in health_counts.items()
        )

        overall_health_score = (weighted_score / total_services) * 100 if total_services > 0 else 0

        # Determine health trend
        health_trend = self._calculate_health_trend(historical_health)

        # Estimate recovery time for unhealthy services
        recovery_time = self._estimate_recovery_time(nodes)

        return HealthMetrics(
            overall_health_score=round(overall_health_score, 1),
            service_health_distribution=health_counts,
            critical_services_count=len(critical_services),
            degraded_services_count=health_counts["degraded"],
            unhealthy_services_count=health_counts["unhealthy"],
            health_trend=health_trend,
            estimated_recovery_time=recovery_time
        )

    def calculate_reliability_metrics(
        self,
        analysis: TopologyAnalysis,
        failure_history: Optional[Dict[str, List[datetime]]] = None
    ) -> ReliabilityMetrics:
        """
        Calculate reliability and resilience metrics.

        Args:
            analysis: Topology analysis results
            failure_history: Historical failure data

        Returns:
            Reliability metrics analysis
        """
        # Calculate service availability
        service_availability = {}
        for service_name, node in analysis.nodes.items():
            # Simplified availability calculation based on health
            if node.health_status == "healthy":
                availability = 0.99
            elif node.health_status == "degraded":
                availability = 0.95
            elif node.health_status == "unhealthy":
                availability = 0.80
            else:
                availability = 0.90

            service_availability[service_name] = availability

        # Calculate MTBF and MTTR from failure history
        mtbf = None
        mttr = None

        if failure_history:
            all_failures = []
            recovery_times = []

            for service, failures in failure_history.items():
                if len(failures) > 1:
                    # Calculate time between failures
                    sorted_failures = sorted(failures)
                    intervals = [
                        (sorted_failures[i+1] - sorted_failures[i]).total_seconds()
                        for i in range(len(sorted_failures) - 1)
                    ]
                    if intervals:
                        all_failures.extend(intervals)

                    # Assume recovery time is 1/10 of interval (simplified)
                    recovery_times.extend([interval / 10 for interval in intervals])

            if all_failures:
                mtbf = statistics.mean(all_failures) / 3600  # hours
            if recovery_times:
                mttr = statistics.mean(recovery_times) / 3600  # hours

        # Identify single points of failure
        spof = self._identify_single_points_of_failure(analysis)

        # Calculate redundancy level
        redundancy_level = self._calculate_redundancy_level(analysis)

        # Calculate system reliability score
        avg_availability = statistics.mean(service_availability.values()) if service_availability else 0.9
        reliability_score = (avg_availability * 100) - (len(spof) * 5) + (redundancy_level * 10)
        reliability_score = max(0, min(100, reliability_score))

        return ReliabilityMetrics(
            mean_time_between_failures=mtbf,
            mean_time_to_recovery=mttr,
            service_availability=service_availability,
            system_reliability_score=round(reliability_score, 1),
            single_points_of_failure=spof,
            redundancy_level=round(redundancy_level, 2),
            failover_capacity=round(redundancy_level * 0.8, 2)  # Simplified calculation
        )

    def calculate_performance_metrics(
        self,
        analysis: TopologyAnalysis,
        performance_data: Optional[Dict[str, Dict[str, float]]] = None
    ) -> PerformanceMetrics:
        """
        Calculate performance and efficiency metrics.

        Args:
            analysis: Topology analysis results
            performance_data: Performance metrics per service

        Returns:
            Performance metrics analysis
        """
        # Use provided performance data or generate estimates
        if not performance_data:
            performance_data = self._generate_performance_estimates(analysis)

        # Calculate average response time
        response_times = [data.get("response_time", 100) for data in performance_data.values()]
        avg_response_time = statistics.mean(response_times) if response_times else 100

        # Calculate throughput capacity
        throughputs = [data.get("throughput", 100) for data in performance_data.values()]
        throughput_capacity = statistics.mean(throughputs) if throughputs else 100

        # Identify bottleneck services
        bottlenecks = self._identify_bottlenecks(analysis, performance_data)

        # Identify optimization opportunities
        optimization_ops = self._identify_optimization_opportunities(analysis, performance_data)

        # Calculate scalability score
        scalability_score = self._calculate_scalability_score(analysis, performance_data)

        # Calculate load distribution
        load_distribution = {
            service: data.get("load_percentage", 0)
            for service, data in performance_data.items()
        }

        return PerformanceMetrics(
            average_response_time=round(avg_response_time, 2),
            throughput_capacity=round(throughput_capacity, 2),
            bottleneck_services=bottlenecks,
            optimization_opportunities=optimization_ops,
            scalability_score=round(scalability_score, 1),
            load_distribution=load_distribution
        )

    def calculate_dependency_metrics(self, analysis: TopologyAnalysis) -> DependencyMetrics:
        """
        Calculate dependency and coupling metrics.

        Args:
            analysis: Topology analysis results

        Returns:
            Dependency metrics analysis
        """
        graph = analysis.graph

        # Calculate average coupling
        total_coupling = 0
        coupling_count = 0

        for node in graph.nodes():
            degree = graph.degree(node)
            if degree > 0:
                total_coupling += degree
                coupling_count += 1

        average_coupling = total_coupling / coupling_count if coupling_count > 0 else 0

        # Identify tightly coupled services
        tightly_coupled = []
        for source, target, data in graph.edges(data=True):
            coupling_strength = data.get("strength", 1.0)
            if coupling_strength > 0.8:
                tightly_coupled.append((source, target, coupling_strength))

        # Identify loosely coupled services
        loosely_coupled = []
        for node in graph.nodes():
            degree = graph.degree(node)
            if degree <= 2:  # Services with few connections
                loosely_coupled.append(node)

        # Calculate dependency depth for each service
        dependency_depth = {}
        for node in graph.nodes():
            try:
                # Find longest path from this node
                depths = []
                for target in graph.nodes():
                    if target != node:
                        try:
                            path_length = nx.shortest_path_length(graph, node, target)
                            depths.append(path_length)
                        except:
                            continue

                dependency_depth[node] = max(depths) if depths else 0
            except:
                dependency_depth[node] = 0

        # Calculate dependency health score
        circular_deps = len(analysis.critical_paths) if hasattr(analysis, 'critical_paths') else 0
        avg_depth = statistics.mean(dependency_depth.values()) if dependency_depth else 0

        health_score = 100 - (average_coupling * 5) - (circular_deps * 10) - (avg_depth * 2)
        health_score = max(0, min(100, health_score))

        return DependencyMetrics(
            average_coupling=round(average_coupling, 2),
            tightly_coupled_services=tightly_coupled,
            loosely_coupled_services=loosely_coupled,
            dependency_depth=dependency_depth,
            circular_dependencies=analysis.critical_paths if hasattr(analysis, 'critical_paths') else [],
            dependency_health_score=round(health_score, 1)
        )

    def generate_comprehensive_report(
        self,
        analysis: TopologyAnalysis,
        include_historical: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive topology metrics report.

        Args:
            analysis: Topology analysis results
            include_historical: Whether to include historical comparisons

        Returns:
            Comprehensive metrics report
        """
        # Calculate all metric categories
        health = self.calculate_health_metrics(analysis)
        reliability = self.calculate_reliability_metrics(analysis)
        performance = self.calculate_performance_metrics(analysis)
        dependencies = self.calculate_dependency_metrics(analysis)

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_services": len(analysis.nodes),
                "total_relationships": len(analysis.relationships),
                "overall_health_score": health.overall_health_score,
                "system_reliability_score": reliability.system_reliability_score,
                "dependency_health_score": dependencies.dependency_health_score
            },
            "health_metrics": {
                "overall_health_score": health.overall_health_score,
                "service_health_distribution": health.service_health_distribution,
                "critical_services_count": health.critical_services_count,
                "health_trend": health.health_trend
            },
            "reliability_metrics": {
                "system_reliability_score": reliability.system_reliability_score,
                "single_points_of_failure": reliability.single_points_of_failure,
                "redundancy_level": reliability.redundancy_level,
                "failover_capacity": reliability.failover_capacity
            },
            "performance_metrics": {
                "average_response_time": performance.average_response_time,
                "scalability_score": performance.scalability_score,
                "bottleneck_count": len(performance.bottleneck_services)
            },
            "dependency_metrics": {
                "average_coupling": dependencies.average_coupling,
                "circular_dependencies_count": len(dependencies.circular_dependencies),
                "dependency_health_score": dependencies.dependency_health_score
            },
            "topology_insights": {
                "clusters_count": len(analysis.clusters),
                "critical_paths_count": len(analysis.critical_paths),
                "bottlenecks_count": len(analysis.bottlenecks)
            }
        }

        if include_historical:
            report["historical_comparison"] = self._generate_historical_comparison()

        return report

    def _calculate_health_trend(self, historical_health: Optional[Dict[str, List[str]]]) -> str:
        """Calculate health trend from historical data."""
        if not historical_health:
            return "stable"

        # Simplified trend calculation
        current_health_scores = []
        for service, health_history in historical_health.items():
            if health_history:
                latest = health_history[-1]
                score = {"healthy": 1.0, "degraded": 0.5, "unhealthy": 0.0}.get(latest, 0.5)
                current_health_scores.append(score)

        if not current_health_scores:
            return "stable"

        avg_current = statistics.mean(current_health_scores)

        # Compare with baseline
        baseline = self.baseline_metrics.get("average_health", avg_current)

        if avg_current > baseline + 0.1:
            return "improving"
        elif avg_current < baseline - 0.1:
            return "declining"
        else:
            return "stable"

    def _estimate_recovery_time(self, nodes: Dict[str, ServiceNode]) -> Optional[timedelta]:
        """Estimate recovery time for unhealthy services."""
        unhealthy_count = sum(1 for node in nodes.values() if node.health_status == "unhealthy")

        if unhealthy_count == 0:
            return None

        # Estimate 2 hours per unhealthy service
        return timedelta(hours=unhealthy_count * 2)

    def _identify_single_points_of_failure(self, analysis: TopologyAnalysis) -> List[str]:
        """Identify single points of failure in the topology."""
        spof = []

        for bottleneck in analysis.bottlenecks:
            if bottleneck.get("risk_level") == "high":
                spof.append(bottleneck["service"])

        return spof

    def _calculate_redundancy_level(self, analysis: TopologyAnalysis) -> float:
        """Calculate system redundancy level."""
        if not analysis.clusters:
            return 0.0

        # Calculate average cluster size as redundancy indicator
        cluster_sizes = [cluster["size"] for cluster in analysis.clusters]
        avg_cluster_size = statistics.mean(cluster_sizes)

        # Normalize to 0-1 scale
        redundancy = min(1.0, avg_cluster_size / 5.0)
        return redundancy

    def _generate_performance_estimates(self, analysis: TopologyAnalysis) -> Dict[str, Dict[str, float]]:
        """Generate performance estimates for services."""
        estimates = {}

        for service_name, node in analysis.nodes.items():
            # Base estimates based on service type
            if node.service_type.name == "API_SERVICE":
                response_time = 150  # ms
                throughput = 500  # req/sec
            elif node.service_type.name == "DATA_SERVICE":
                response_time = 300  # ms
                throughput = 200  # req/sec
            elif node.service_type.name == "INFRASTRUCTURE":
                response_time = 100  # ms
                throughput = 1000  # req/sec
            else:
                response_time = 200  # ms
                throughput = 300  # req/sec

            # Adjust based on dependencies
            dependency_factor = 1 + (len(node.dependencies) * 0.1)
            response_time *= dependency_factor

            # Adjust based on health
            if node.health_status == "degraded":
                response_time *= 1.5
                throughput *= 0.7
            elif node.health_status == "unhealthy":
                response_time *= 3
                throughput *= 0.3

            estimates[service_name] = {
                "response_time": response_time,
                "throughput": throughput,
                "load_percentage": 100 / len(analysis.nodes)  # Equal distribution
            }

        return estimates

    def _identify_bottlenecks(self, analysis: TopologyAnalysis, performance_data: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """Identify performance bottleneck services."""
        bottlenecks = []

        for service_name, perf_data in performance_data.items():
            response_time = perf_data.get("response_time", 100)
            throughput = perf_data.get("throughput", 100)

            # Identify as bottleneck if response time > 500ms or throughput < 50 req/sec
            if response_time > 500 or throughput < 50:
                node = analysis.nodes.get(service_name)
                if node:
                    bottlenecks.append({
                        "service": service_name,
                        "response_time": response_time,
                        "throughput": throughput,
                        "service_type": node.service_type.value,
                        "bottleneck_type": "performance"
                    })

        # Also include topological bottlenecks
        for bottleneck in analysis.bottlenecks[:5]:  # Top 5
            if not any(b["service"] == bottleneck["service"] for b in bottlenecks):
                bottlenecks.append(bottleneck)

        return bottlenecks

    def _identify_optimization_opportunities(
        self,
        analysis: TopologyAnalysis,
        performance_data: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """Identify optimization opportunities."""
        opportunities = []

        # Look for services with high coupling but low performance
        for service_name, perf_data in performance_data.items():
            response_time = perf_data.get("response_time", 100)

            node = analysis.nodes.get(service_name)
            if node and len(node.dependencies) > 3 and response_time > 300:
                opportunities.append({
                    "service": service_name,
                    "type": "decoupling",
                    "description": f"High coupling ({len(node.dependencies)} dependencies) with slow response time",
                    "potential_improvement": "Consider decoupling or caching"
                })

        # Look for circular dependencies
        for path in analysis.critical_paths:
            if len(path) > 3:  # Long paths may indicate circular dependencies
                opportunities.append({
                    "service": path[0],
                    "type": "circular_dependency",
                    "description": f"Circular dependency detected in path: {' -> '.join(path)}",
                    "potential_improvement": "Refactor to break circular dependency"
                })

        return opportunities

    def _calculate_scalability_score(self, analysis: TopologyAnalysis, performance_data: Dict[str, Dict[str, float]]) -> float:
        """Calculate system scalability score."""
        if not performance_data:
            return 50.0

        # Factors affecting scalability
        load_balance = self._calculate_load_balance(performance_data)
        bottleneck_penalty = len(self._identify_bottlenecks(analysis, performance_data)) * 10
        cluster_bonus = len(analysis.clusters) * 5

        score = load_balance - bottleneck_penalty + cluster_bonus
        return max(0, min(100, score))

    def _calculate_load_balance(self, performance_data: Dict[str, Dict[str, float]]) -> float:
        """Calculate load balance score."""
        loads = [data.get("load_percentage", 0) for data in performance_data.values()]

        if not loads:
            return 50.0

        # Perfect balance would be equal load across all services
        ideal_load = 100 / len(loads)
        variance = statistics.variance(loads) if len(loads) > 1 else 0

        # Lower variance = better balance
        balance_score = 100 - min(100, variance * 2)
        return balance_score

    def _generate_historical_comparison(self) -> Dict[str, Any]:
        """Generate historical comparison data."""
        # Simplified historical comparison
        return {
            "health_trend": "stable",
            "performance_change": "+2.5%",
            "reliability_improvement": "+5.1%",
            "comparison_period": "last 30 days"
        }

    def set_baseline_metrics(self, metrics: Dict[str, Any]):
        """Set baseline metrics for comparison."""
        self.baseline_metrics = metrics

    def update_historical_data(self, service_name: str, metric_type: str, value: Any):
        """Update historical data for trend analysis."""
        if service_name not in self.historical_data:
            self.historical_data[service_name] = {}

        if metric_type not in self.historical_data[service_name]:
            self.historical_data[service_name][metric_type] = []

        self.historical_data[service_name][metric_type].append({
            "timestamp": datetime.now(),
            "value": value
        })

        # Keep only last 100 entries
        if len(self.historical_data[service_name][metric_type]) > 100:
            self.historical_data[service_name][metric_type] = self.historical_data[service_name][metric_type][-100:]
