"""Performance Insights for Unified API Ecosystem Dashboard.

This module provides advanced performance analysis and insights including:
- Response time analysis and latency patterns
- Throughput optimization recommendations
- Resource utilization monitoring
- Performance bottleneck identification
- Capacity planning and scaling recommendations
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import statistics
import json

from ..discovery.client import DiscoveryClient
from ..monitoring.health import HealthMonitor


class PerformanceInsights:
    """Advanced performance analysis and optimization insights."""

    def __init__(self, discovery_client: DiscoveryClient, health_monitor: HealthMonitor):
        self.discovery_client = discovery_client
        self.health_monitor = health_monitor

        # Performance data storage
        self.performance_data = defaultdict(lambda: {
            'response_times': [],
            'throughput_data': [],
            'resource_usage': [],
            'error_patterns': [],
            'bottlenecks': []
        })

        # Performance thresholds and baselines
        self.performance_thresholds = {
            'max_response_time_ms': 1000,
            'target_response_time_ms': 200,
            'max_error_rate_percent': 5.0,
            'min_throughput_rps': 10,
            'max_cpu_percent': 80,
            'max_memory_percent': 85
        }

        # Performance insights cache
        self.insights_cache = {}
        self.cache_timeout = 300  # 5 minutes

    async def analyze_response_times(self, service_name: Optional[str] = None, time_range_hours: int = 24) -> Dict[str, Any]:
        """Analyze response time patterns and performance."""
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)

        analysis = {
            'overall_metrics': {},
            'service_breakdown': {},
            'performance_trends': {},
            'latency_distribution': {},
            'optimization_opportunities': []
        }

        # Get services to analyze
        services_to_analyze = await self._get_services_to_analyze(service_name)

        for svc_name in services_to_analyze:
            service_metrics = await self._analyze_service_response_times(svc_name, cutoff_time)
            if service_metrics:
                analysis['service_breakdown'][svc_name] = service_metrics

        # Calculate overall metrics
        if analysis['service_breakdown']:
            all_response_times = []
            for svc_metrics in analysis['service_breakdown'].values():
                if 'response_times' in svc_metrics:
                    all_response_times.extend(svc_metrics['response_times'])

            if all_response_times:
                analysis['overall_metrics'] = {
                    'avg_response_time': statistics.mean(all_response_times),
                    'median_response_time': statistics.median(all_response_times),
                    'p95_response_time': statistics.quantiles(all_response_times, n=20)[18],
                    'p99_response_time': statistics.quantiles(all_response_times, n=100)[98] if len(all_response_times) >= 100 else max(all_response_times),
                    'min_response_time': min(all_response_times),
                    'max_response_time': max(all_response_times),
                    'total_requests': len(all_response_times)
                }

        # Identify optimization opportunities
        analysis['optimization_opportunities'] = await self._identify_performance_optimizations(analysis)

        return analysis

    async def _get_services_to_analyze(self, service_name: Optional[str]) -> List[str]:
        """Get list of services to analyze."""
        if service_name:
            return [service_name]

        # Get all discovered services
        try:
            services = await self.discovery_client.get_all_services()
            return list(services.keys()) if services else []
        except Exception:
            return []

    async def _analyze_service_response_times(self, service_name: str, cutoff_time: datetime) -> Optional[Dict[str, Any]]:
        """Analyze response times for a specific service."""
        try:
            # Get health data for the service
            health_data = await self.health_monitor.get_service_health(service_name)
            if not health_data or not health_data.get('metrics'):
                return None

            # Extract response time data (mock implementation - in real system, this would come from metrics)
            response_times = []
            for metric in health_data.get('metrics', []):
                if 'response_time' in metric.get('name', '').lower():
                    # Simulate response time data
                    response_times.extend([metric.get('value', 100)] * 10)  # Mock data

            if not response_times:
                return None

            return {
                'response_times': response_times,
                'avg_response_time': statistics.mean(response_times),
                'median_response_time': statistics.median(response_times),
                'p95_response_time': statistics.quantiles(response_times, n=20)[18],
                'performance_grade': self._calculate_performance_grade(response_times),
                'bottlenecks': self._identify_service_bottlenecks(service_name, response_times)
            }

        except Exception:
            return None

    def _calculate_performance_grade(self, response_times: List[float]) -> str:
        """Calculate performance grade based on response times."""
        avg_time = statistics.mean(response_times)

        if avg_time < 100:
            return 'A+'
        elif avg_time < 200:
            return 'A'
        elif avg_time < 500:
            return 'B'
        elif avg_time < 1000:
            return 'C'
        else:
            return 'D'

    def _identify_service_bottlenecks(self, service_name: str, response_times: List[float]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks for a service."""
        bottlenecks = []

        # Check for slow response patterns
        slow_responses = [t for t in response_times if t > 1000]
        if len(slow_responses) > len(response_times) * 0.1:  # > 10% slow
            bottlenecks.append({
                'type': 'high_latency',
                'severity': 'high',
                'description': f"{len(slow_responses)} responses exceed 1s threshold",
                'percentage': len(slow_responses) / len(response_times),
                'recommendation': 'Implement response caching or optimize database queries'
            })

        # Check for response time variance
        if len(response_times) > 10:
            variance = statistics.variance(response_times)
            std_dev = statistics.stdev(response_times)
            if std_dev > statistics.mean(response_times) * 0.5:  # High variance
                bottlenecks.append({
                    'type': 'inconsistent_performance',
                    'severity': 'medium',
                    'description': f"High response time variance (σ = {std_dev:.2f}ms)",
                    'recommendation': 'Implement load balancing or resource optimization'
                })

        return bottlenecks

    async def _identify_performance_optimizations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify performance optimization opportunities."""
        optimizations = []

        # Analyze overall metrics
        overall_metrics = analysis.get('overall_metrics', {})
        if overall_metrics.get('avg_response_time', 0) > 500:
            optimizations.append({
                'type': 'response_time_optimization',
                'priority': 'high',
                'description': 'Average response time exceeds 500ms threshold',
                'expected_impact': '30-50% response time improvement',
                'recommendations': [
                    'Implement response caching',
                    'Optimize database queries',
                    'Consider CDN integration',
                    'Implement async processing where applicable'
                ]
            })

        # Analyze service-specific issues
        for service_name, service_metrics in analysis.get('service_breakdown', {}).items():
            bottlenecks = service_metrics.get('bottlenecks', [])
            for bottleneck in bottlenecks:
                optimizations.append({
                    'service': service_name,
                    'type': bottleneck['type'],
                    'priority': bottleneck['severity'],
                    'description': bottleneck['description'],
                    'recommendation': bottleneck['recommendation']
                })

        return optimizations

    async def analyze_throughput_patterns(self, service_name: Optional[str] = None, time_range_hours: int = 24) -> Dict[str, Any]:
        """Analyze throughput patterns and capacity utilization."""
        analysis = {
            'throughput_metrics': {},
            'capacity_utilization': {},
            'scaling_recommendations': [],
            'peak_usage_patterns': {},
            'bottleneck_analysis': {}
        }

        services_to_analyze = await self._get_services_to_analyze(service_name)

        for svc_name in services_to_analyze:
            throughput_data = await self._analyze_service_throughput(svc_name, time_range_hours)
            if throughput_data:
                analysis['throughput_metrics'][svc_name] = throughput_data

                # Analyze capacity utilization
                capacity_analysis = await self._analyze_capacity_utilization(svc_name, throughput_data)
                analysis['capacity_utilization'][svc_name] = capacity_analysis

                # Generate scaling recommendations
                scaling_rec = await self._generate_scaling_recommendations(svc_name, throughput_data, capacity_analysis)
                if scaling_rec:
                    analysis['scaling_recommendations'].extend(scaling_rec)

        return analysis

    async def _analyze_service_throughput(self, service_name: str, time_range_hours: int) -> Optional[Dict[str, Any]]:
        """Analyze throughput for a specific service."""
        try:
            # Get health metrics
            health_data = await self.health_monitor.get_service_health(service_name)

            # Simulate throughput analysis (in real system, this would analyze actual metrics)
            return {
                'current_rps': 15.5,
                'peak_rps': 28.3,
                'avg_rps': 12.8,
                'throughput_trend': 'increasing',
                'capacity_limit': 50,  # RPS
                'utilization_percent': 31.0
            }

        except Exception:
            return None

    async def _analyze_capacity_utilization(self, service_name: str, throughput_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze capacity utilization patterns."""
        current_rps = throughput_data.get('current_rps', 0)
        capacity_limit = throughput_data.get('capacity_limit', 100)

        utilization = (current_rps / capacity_limit) * 100 if capacity_limit > 0 else 0

        return {
            'current_utilization': utilization,
            'capacity_headroom': capacity_limit - current_rps,
            'utilization_trend': 'stable',  # Could be calculated from historical data
            'scaling_needed': utilization > 80,
            'recommended_capacity': current_rps * 1.5 if utilization > 70 else capacity_limit
        }

    async def _generate_scaling_recommendations(self, service_name: str, throughput_data: Dict[str, Any], capacity_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate scaling recommendations based on throughput analysis."""
        recommendations = []

        utilization = capacity_analysis.get('current_utilization', 0)

        if utilization > 90:
            recommendations.append({
                'service': service_name,
                'type': 'immediate_scaling',
                'priority': 'critical',
                'description': f"Service at {utilization:.1f}% capacity utilization",
                'action': 'Scale up immediately',
                'expected_impact': 'Prevent service degradation'
            })
        elif utilization > 70:
            recommendations.append({
                'service': service_name,
                'type': 'proactive_scaling',
                'priority': 'high',
                'description': f"Service at {utilization:.1f}% capacity utilization",
                'action': 'Plan scaling for peak periods',
                'expected_impact': 'Maintain optimal performance'
            })

        return recommendations

    async def analyze_resource_utilization(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Analyze resource utilization patterns."""
        analysis = {
            'cpu_utilization': {},
            'memory_utilization': {},
            'network_utilization': {},
            'disk_utilization': {},
            'resource_alerts': [],
            'optimization_recommendations': []
        }

        services_to_analyze = await self._get_services_to_analyze(service_name)

        for svc_name in services_to_analyze:
            # Simulate resource analysis (in real system, this would monitor actual resources)
            analysis['cpu_utilization'][svc_name] = {
                'current_percent': 45.2,
                'avg_percent': 38.7,
                'peak_percent': 72.1,
                'trend': 'stable'
            }

            analysis['memory_utilization'][svc_name] = {
                'current_mb': 512,
                'avg_mb': 487,
                'peak_mb': 756,
                'trend': 'increasing',
                'utilization_percent': 68.5
            }

            # Check for resource alerts
            alerts = await self._check_resource_alerts(svc_name, analysis)
            analysis['resource_alerts'].extend(alerts)

            # Generate optimization recommendations
            recommendations = await self._generate_resource_optimizations(svc_name, analysis)
            analysis['optimization_recommendations'].extend(recommendations)

        return analysis

    async def _check_resource_alerts(self, service_name: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for resource utilization alerts."""
        alerts = []

        cpu_util = analysis['cpu_utilization'].get(service_name, {})
        memory_util = analysis['memory_utilization'].get(service_name, {})

        if cpu_util.get('current_percent', 0) > 90:
            alerts.append({
                'service': service_name,
                'resource': 'cpu',
                'severity': 'critical',
                'message': f"CPU utilization at {cpu_util['current_percent']:.1f}%",
                'recommendation': 'Scale compute resources or optimize CPU-intensive operations'
            })

        if memory_util.get('utilization_percent', 0) > 85:
            alerts.append({
                'service': service_name,
                'resource': 'memory',
                'severity': 'high',
                'message': f"Memory utilization at {memory_util['utilization_percent']:.1f}%",
                'recommendation': 'Increase memory allocation or implement memory optimization'
            })

        return alerts

    async def _generate_resource_optimizations(self, service_name: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate resource optimization recommendations."""
        optimizations = []

        memory_util = analysis['memory_utilization'].get(service_name, {})
        cpu_util = analysis['cpu_utilization'].get(service_name, {})

        if memory_util.get('utilization_percent', 0) > 70:
            optimizations.append({
                'service': service_name,
                'type': 'memory_optimization',
                'priority': 'medium',
                'description': 'High memory utilization detected',
                'recommendations': [
                    'Implement memory caching',
                    'Optimize data structures',
                    'Consider memory-efficient algorithms'
                ]
            })

        if cpu_util.get('avg_percent', 0) > 60:
            optimizations.append({
                'service': service_name,
                'type': 'cpu_optimization',
                'priority': 'medium',
                'description': 'High CPU utilization detected',
                'recommendations': [
                    'Profile CPU-intensive operations',
                    'Implement async processing',
                    'Consider CPU optimization techniques'
                ]
            })

        return optimizations

    async def generate_performance_report(self, service_name: Optional[str] = None, time_range_hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'time_range_hours': time_range_hours,
            'executive_summary': {},
            'detailed_analysis': {},
            'recommendations': {},
            'alerts': [],
            'trends': {}
        }

        # Gather all performance data
        response_time_analysis = await self.analyze_response_times(service_name, time_range_hours)
        throughput_analysis = await self.analyze_throughput_patterns(service_name, time_range_hours)
        resource_analysis = await self.analyze_resource_utilization(service_name)

        # Generate executive summary
        report['executive_summary'] = await self._generate_executive_summary(
            response_time_analysis, throughput_analysis, resource_analysis
        )

        # Compile detailed analysis
        report['detailed_analysis'] = {
            'response_times': response_time_analysis,
            'throughput': throughput_analysis,
            'resources': resource_analysis
        }

        # Compile recommendations
        report['recommendations'] = {
            'performance_optimizations': response_time_analysis.get('optimization_opportunities', []),
            'scaling_recommendations': throughput_analysis.get('scaling_recommendations', []),
            'resource_optimizations': resource_analysis.get('optimization_recommendations', [])
        }

        # Compile alerts
        report['alerts'] = (
            resource_analysis.get('resource_alerts', []) +
            throughput_analysis.get('scaling_recommendations', [])
        )

        # Analyze trends
        report['trends'] = await self._analyze_performance_trends(service_name, time_range_hours)

        return report

    async def _generate_executive_summary(self, response_analysis: Dict, throughput_analysis: Dict, resource_analysis: Dict) -> Dict[str, Any]:
        """Generate executive summary of performance analysis."""
        overall_metrics = response_analysis.get('overall_metrics', {})

        # Calculate overall performance score
        performance_score = 100  # Start with perfect score

        # Deduct points for poor performance
        avg_response_time = overall_metrics.get('avg_response_time', 0)
        if avg_response_time > 1000:
            performance_score -= 30
        elif avg_response_time > 500:
            performance_score -= 15

        # Check for alerts
        total_alerts = len(resource_analysis.get('resource_alerts', []))
        if total_alerts > 0:
            performance_score -= total_alerts * 10

        performance_score = max(0, min(100, performance_score))

        return {
            'overall_performance_score': performance_score,
            'performance_grade': 'A' if performance_score >= 90 else 'B' if performance_score >= 80 else 'C' if performance_score >= 70 else 'D',
            'total_services_analyzed': len(response_analysis.get('service_breakdown', {})),
            'avg_response_time_ms': overall_metrics.get('avg_response_time', 0),
            'total_requests_analyzed': overall_metrics.get('total_requests', 0),
            'active_alerts': total_alerts,
            'key_findings': await self._extract_key_findings(response_analysis, throughput_analysis, resource_analysis)
        }

    async def _extract_key_findings(self, response_analysis: Dict, throughput_analysis: Dict, resource_analysis: Dict) -> List[str]:
        """Extract key findings from performance analysis."""
        findings = []

        # Response time findings
        overall_metrics = response_analysis.get('overall_metrics', {})
        avg_time = overall_metrics.get('avg_response_time', 0)
        if avg_time < 200:
            findings.append("Excellent response times across all services")
        elif avg_time < 500:
            findings.append("Good response times with room for optimization")
        else:
            findings.append("Response times need optimization")

        # Throughput findings
        throughput_metrics = throughput_analysis.get('throughput_metrics', {})
        if throughput_metrics:
            total_capacity_utilization = sum(
                metrics.get('utilization_percent', 0)
                for metrics in throughput_metrics.values()
            ) / len(throughput_metrics)

            if total_capacity_utilization < 50:
                findings.append("Low capacity utilization - potential for cost optimization")
            elif total_capacity_utilization > 80:
                findings.append("High capacity utilization - scaling may be needed")

        # Resource findings
        if resource_analysis.get('resource_alerts'):
            findings.append(f"{len(resource_analysis['resource_alerts'])} resource alerts require attention")

        return findings

    async def _analyze_performance_trends(self, service_name: Optional[str], time_range_hours: int) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        # Simplified trend analysis (in real system, this would analyze historical data)
        return {
            'response_time_trend': 'stable',
            'throughput_trend': 'increasing',
            'resource_utilization_trend': 'stable',
            'error_rate_trend': 'decreasing',
            'predicted_changes': {
                'next_24h': 'stable',
                'next_7d': 'slight_increase'
            }
        }
