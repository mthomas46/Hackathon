"""API Usage Analytics for Unified API Ecosystem Dashboard.

This module provides comprehensive API usage analytics including:
- Request volume and patterns over time
- Service usage distribution and trends
- User/client activity monitoring
- Geographic and temporal usage patterns
- Peak usage analysis and capacity planning
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, deque
import json
import statistics

from ..discovery.client import DiscoveryClient
from ..monitoring.health import HealthMonitor


class UsageAnalytics:
    """Comprehensive API usage analytics and reporting."""

    def __init__(self, discovery_client: DiscoveryClient, health_monitor: HealthMonitor):
        self.discovery_client = discovery_client
        self.health_monitor = health_monitor

        # Analytics data storage
        self.usage_data = defaultdict(lambda: {
            'requests': deque(maxlen=10000),  # Rolling window of requests
            'daily_stats': {},
            'hourly_patterns': defaultdict(list),
            'user_activity': defaultdict(int),
            'endpoint_usage': defaultdict(int),
            'response_codes': defaultdict(int),
            'geographic_usage': defaultdict(int),
            'peak_usage_times': []
        })

        # Analytics configuration
        self.analytics_config = {
            'retention_days': 30,
            'peak_detection_threshold': 0.8,  # 80% of capacity
            'anomaly_detection_sensitivity': 0.95,
            'real_time_window_minutes': 5
        }

        # Real-time metrics
        self.real_time_metrics = {
            'current_rps': 0,
            'peak_rps_today': 0,
            'total_requests_today': 0,
            'active_users': set(),
            'last_updated': datetime.now()
        }

    async def record_api_request(self, service_name: str, endpoint: str, method: str,
                               user_id: Optional[str] = None, client_ip: Optional[str] = None,
                               user_agent: Optional[str] = None, response_code: int = 200,
                               response_time_ms: float = 0.0, request_size_bytes: int = 0,
                               response_size_bytes: int = 0) -> None:
        """Record an API request for analytics processing."""
        timestamp = datetime.now()

        # Create request record
        request_record = {
            'timestamp': timestamp,
            'service': service_name,
            'endpoint': endpoint,
            'method': method,
            'user_id': user_id,
            'client_ip': client_ip,
            'user_agent': user_agent,
            'response_code': response_code,
            'response_time_ms': response_time_ms,
            'request_size_bytes': request_size_bytes,
            'response_size_bytes': response_size_bytes,
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'month': timestamp.month
        }

        # Store in rolling window
        self.usage_data[service_name]['requests'].append(request_record)

        # Update real-time metrics
        self._update_real_time_metrics(request_record)

        # Update aggregations
        await self._update_aggregations(service_name, request_record)

    def _update_real_time_metrics(self, request_record: Dict[str, Any]) -> None:
        """Update real-time metrics with new request data."""
        current_time = datetime.now()

        # Update active users (rolling window)
        if request_record['user_id']:
            self.real_time_metrics['active_users'].add(request_record['user_id'])

            # Clean old active users (inactive for 30 minutes)
            cutoff_time = current_time - timedelta(minutes=30)
            # Note: In real implementation, track last activity time per user

        # Update RPS calculation
        time_window_start = current_time - timedelta(minutes=self.analytics_config['real_time_window_minutes'])
        recent_requests = []

        for service_data in self.usage_data.values():
            recent_requests.extend([
                r for r in service_data['requests']
                if r['timestamp'] > time_window_start
            ])

        self.real_time_metrics['current_rps'] = len(recent_requests) / (self.analytics_config['real_time_window_minutes'] * 60)
        self.real_time_metrics['peak_rps_today'] = max(self.real_time_metrics['peak_rps_today'], self.real_time_metrics['current_rps'])
        self.real_time_metrics['last_updated'] = current_time

    async def _update_aggregations(self, service_name: str, request_record: Dict[str, Any]) -> None:
        """Update aggregated analytics data."""
        service_data = self.usage_data[service_name]

        # Update endpoint usage
        endpoint_key = f"{request_record['method']} {request_record['endpoint']}"
        service_data['endpoint_usage'][endpoint_key] += 1

        # Update response codes
        service_data['response_codes'][request_record['response_code']] += 1

        # Update user activity
        if request_record['user_id']:
            service_data['user_activity'][request_record['user_id']] += 1

        # Update geographic usage (simplified - in real impl, use IP geolocation)
        if request_record['client_ip']:
            # Simplified geographic categorization
            if request_record['client_ip'].startswith(('192.168.', '10.', '172.')):
                geo_key = 'internal_network'
            else:
                geo_key = 'external_network'  # In real impl, use actual geolocation
            service_data['geographic_usage'][geo_key] += 1

        # Update hourly patterns
        hour = request_record['hour']
        service_data['hourly_patterns'][hour].append(request_record)

        # Limit hourly patterns to last 7 days
        for hour_patterns in service_data['hourly_patterns'].values():
            cutoff_time = datetime.now() - timedelta(days=7)
            hour_patterns[:] = [r for r in hour_patterns if r['timestamp'] > cutoff_time]

    async def get_usage_overview(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive usage overview for the specified time range."""
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)

        # Aggregate data across all services
        total_requests = 0
        service_breakdown = {}
        endpoint_breakdown = defaultdict(int)
        response_code_breakdown = defaultdict(int)
        geographic_breakdown = defaultdict(int)

        for service_name, service_data in self.usage_data.items():
            # Filter requests by time range
            recent_requests = [r for r in service_data['requests'] if r['timestamp'] > cutoff_time]

            if not recent_requests:
                continue

            total_requests += len(recent_requests)

            # Service breakdown
            service_breakdown[service_name] = {
                'total_requests': len(recent_requests),
                'avg_response_time': sum(r['response_time_ms'] for r in recent_requests) / len(recent_requests),
                'success_rate': len([r for r in recent_requests if r['response_code'] < 400]) / len(recent_requests),
                'unique_users': len(set(r['user_id'] for r in recent_requests if r['user_id']))
            }

            # Aggregate endpoint usage
            for endpoint, count in service_data['endpoint_usage'].items():
                endpoint_breakdown[endpoint] += count

            # Aggregate response codes
            for code, count in service_data['response_codes'].items():
                response_code_breakdown[code] += count

            # Aggregate geographic usage
            for geo, count in service_data['geographic_usage'].items():
                geographic_breakdown[geo] += count

        return {
            'time_range_hours': time_range_hours,
            'total_requests': total_requests,
            'average_rps': total_requests / (time_range_hours * 3600),
            'service_breakdown': dict(service_breakdown),
            'top_endpoints': dict(sorted(endpoint_breakdown.items(), key=lambda x: x[1], reverse=True)[:10]),
            'response_code_distribution': dict(response_code_breakdown),
            'geographic_distribution': dict(geographic_breakdown),
            'generated_at': datetime.now().isoformat()
        }

    async def get_performance_insights(self, service_name: Optional[str] = None, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get performance insights and recommendations."""
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)

        insights = {
            'performance_metrics': {},
            'bottlenecks': [],
            'recommendations': [],
            'trends': {},
            'anomalies': []
        }

        # Analyze services (all or specific)
        services_to_analyze = [service_name] if service_name else list(self.usage_data.keys())

        for svc_name in services_to_analyze:
            if svc_name not in self.usage_data:
                continue

            service_data = self.usage_data[svc_name]
            recent_requests = [r for r in service_data['requests'] if r['timestamp'] > cutoff_time]

            if not recent_requests:
                continue

            # Calculate performance metrics
            response_times = [r['response_time_ms'] for r in recent_requests]
            insights['performance_metrics'][svc_name] = {
                'avg_response_time': statistics.mean(response_times),
                'median_response_time': statistics.median(response_times),
                'p95_response_time': statistics.quantiles(response_times, n=20)[18],
                'p99_response_time': statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'total_requests': len(recent_requests)
            }

            # Identify bottlenecks
            slow_requests = [r for r in recent_requests if r['response_time_ms'] > 1000]  # > 1 second
            if len(slow_requests) > len(recent_requests) * 0.1:  # > 10% slow
                insights['bottlenecks'].append({
                    'service': svc_name,
                    'issue': 'high_latency',
                    'percentage_slow': len(slow_requests) / len(recent_requests),
                    'avg_slow_time': statistics.mean([r['response_time_ms'] for r in slow_requests])
                })

            # Generate recommendations
            avg_response_time = insights['performance_metrics'][svc_name]['avg_response_time']
            if avg_response_time > 500:
                insights['recommendations'].append({
                    'service': svc_name,
                    'type': 'performance_optimization',
                    'priority': 'high',
                    'recommendation': 'Consider implementing response caching or optimizing database queries',
                    'expected_impact': f"Estimated {30-50}% response time improvement"
                })

        return insights

    async def get_usage_patterns(self, service_name: Optional[str] = None, time_range_days: int = 7) -> Dict[str, Any]:
        """Analyze usage patterns and trends."""
        cutoff_time = datetime.now() - timedelta(days=time_range_days)

        patterns = {
            'hourly_patterns': {},
            'daily_patterns': {},
            'weekly_patterns': {},
            'peak_usage_times': [],
            'usage_trends': {},
            'seasonal_patterns': {}
        }

        # Analyze services (all or specific)
        services_to_analyze = [service_name] if service_name else list(self.usage_data.keys())

        for svc_name in services_to_analyze:
            if svc_name not in self.usage_data:
                continue

            service_data = self.usage_data[svc_name]
            recent_requests = [r for r in service_data['requests'] if r['timestamp'] > cutoff_time]

            if len(recent_requests) < 10:  # Need minimum data
                continue

            # Hourly patterns
            hourly_counts = defaultdict(int)
            for request in recent_requests:
                hourly_counts[request['hour']] += 1

            patterns['hourly_patterns'][svc_name] = dict(hourly_counts)

            # Daily patterns
            daily_counts = defaultdict(int)
            for request in recent_requests:
                day_key = request['timestamp'].date().isoformat()
                daily_counts[day_key] += 1

            patterns['daily_patterns'][svc_name] = dict(daily_counts)

            # Identify peak usage times
            peak_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            patterns['peak_usage_times'].extend([{
                'service': svc_name,
                'hour': hour,
                'requests': count,
                'percentage_of_peak': count / max(hourly_counts.values())
            } for hour, count in peak_hours])

            # Usage trends (simple linear trend)
            if len(daily_counts) >= 3:
                daily_values = list(daily_counts.values())
                trend_slope = self._calculate_trend_slope(daily_values)
                patterns['usage_trends'][svc_name] = {
                    'slope': trend_slope,
                    'direction': 'increasing' if trend_slope > 0.1 else 'decreasing' if trend_slope < -0.1 else 'stable',
                    'confidence': min(abs(trend_slope) * 10, 1.0)
                }

        return patterns

    def _calculate_trend_slope(self, values: List[int]) -> float:
        """Calculate simple linear trend slope."""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x = list(range(n))
        y = values

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi * xi for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
        return slope

    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time usage metrics."""
        # Clean up old active users (simulate activity tracking)
        current_time = datetime.now()
        # In real implementation, track last activity per user and remove inactive ones

        return {
            'current_rps': round(self.real_time_metrics['current_rps'], 2),
            'peak_rps_today': round(self.real_time_metrics['peak_rps_today'], 2),
            'total_requests_today': self.real_time_metrics['total_requests_today'],
            'active_users_count': len(self.real_time_metrics['active_users']),
            'last_updated': self.real_time_metrics['last_updated'].isoformat(),
            'services_monitored': len(self.usage_data)
        }

    async def detect_anomalies(self, service_name: Optional[str] = None, sensitivity: float = 0.95) -> Dict[str, Any]:
        """Detect usage anomalies using statistical analysis."""
        anomalies = {
            'spike_anomalies': [],
            'drop_anomalies': [],
            'unusual_patterns': [],
            'error_rate_anomalies': []
        }

        services_to_check = [service_name] if service_name else list(self.usage_data.keys())

        for svc_name in services_to_check:
            if svc_name not in self.usage_data:
                continue

            service_data = self.usage_data[svc_name]

            # Check for request volume anomalies
            recent_requests = list(service_data['requests'])
            if len(recent_requests) >= 50:  # Need minimum data
                # Simple anomaly detection based on recent vs historical average
                recent_avg = len(recent_requests) / max(1, (datetime.now() - recent_requests[0]['timestamp']).total_seconds() / 3600)

                # Calculate baseline (earlier period)
                baseline_cutoff = datetime.now() - timedelta(hours=24)
                baseline_requests = [r for r in recent_requests if r['timestamp'] < baseline_cutoff]
                if baseline_requests:
                    baseline_avg = len(baseline_requests) / 24  # requests per hour

                    if recent_avg > baseline_avg * 2:  # 2x spike
                        anomalies['spike_anomalies'].append({
                            'service': svc_name,
                            'current_rps': recent_avg,
                            'baseline_rps': baseline_avg,
                            'multiplier': recent_avg / baseline_avg,
                            'severity': 'high' if recent_avg / baseline_avg > 5 else 'medium'
                        })

        return anomalies

    async def export_analytics_data(self, service_name: Optional[str] = None, format: str = 'json') -> str:
        """Export analytics data for external analysis or backup."""
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'services': {},
            'real_time_metrics': self.real_time_metrics
        }

        services_to_export = [service_name] if service_name else list(self.usage_data.keys())

        for svc_name in services_to_export:
            if svc_name not in self.usage_data:
                continue

            service_data = self.usage_data[svc_name]
            export_data['services'][svc_name] = {
                'total_requests': len(service_data['requests']),
                'endpoint_usage': dict(service_data['endpoint_usage']),
                'response_codes': dict(service_data['response_codes']),
                'user_activity_count': len(service_data['user_activity']),
                'geographic_usage': dict(service_data['geographic_usage']),
                'hourly_patterns_summary': {
                    hour: len(patterns) for hour, patterns in service_data['hourly_patterns'].items()
                }
            }

        if format == 'json':
            return json.dumps(export_data, indent=2, default=str)
        else:
            # Could implement other formats (CSV, etc.)
            return json.dumps(export_data, default=str)
