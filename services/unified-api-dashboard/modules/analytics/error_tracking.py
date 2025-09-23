"""Error Tracking for Unified API Ecosystem Dashboard.

This module provides comprehensive error tracking and analysis including:
- Error rate monitoring and alerting
- Error pattern identification and classification
- Error correlation with performance metrics
- Root cause analysis and recommendations
- Error trend analysis and forecasting
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter
import json
import statistics
import re

from ..discovery.client import DiscoveryClient
from ..monitoring.health import HealthMonitor


class ErrorTracking:
    """Comprehensive error tracking and analysis for API ecosystem."""

    def __init__(self, discovery_client: DiscoveryClient, health_monitor: HealthMonitor):
        self.discovery_client = discovery_client
        self.health_monitor = health_monitor

        # Error data storage
        self.error_data = defaultdict(lambda: {
            'errors': [],
            'error_patterns': defaultdict(int),
            'error_trends': {},
            'error_correlations': {},
            'root_cause_analysis': {}
        })

        # Error classification and thresholds
        self.error_thresholds = {
            'max_error_rate_percent': 5.0,
            'critical_error_rate_percent': 10.0,
            'error_burst_threshold': 10,  # errors per minute
            'error_pattern_threshold': 5  # minimum occurrences for pattern detection
        }

        # Error categorization rules
        self.error_categories = {
            'client_errors': [400, 401, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 421, 422, 423, 424, 425, 426, 428, 429, 431, 451],
            'server_errors': [500, 501, 502, 503, 504, 505, 506, 507, 508, 510, 511],
            'timeout_errors': [408, 504],
            'authentication_errors': [401, 403],
            'rate_limit_errors': [429],
            'not_found_errors': [404]
        }

    async def record_error(self, service_name: str, endpoint: str, method: str,
                          error_code: int, error_message: str, stack_trace: Optional[str] = None,
                          user_id: Optional[str] = None, client_ip: Optional[str] = None,
                          request_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> None:
        """Record an error for tracking and analysis."""
        timestamp = datetime.now()

        # Create error record
        error_record = {
            'timestamp': timestamp,
            'service': service_name,
            'endpoint': endpoint,
            'method': method,
            'error_code': error_code,
            'error_message': error_message,
            'stack_trace': stack_trace,
            'user_id': user_id,
            'client_ip': client_ip,
            'request_id': request_id,
            'context': context or {},
            'error_category': self._categorize_error(error_code),
            'severity': self._calculate_error_severity(error_code, error_message),
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'month': timestamp.month
        }

        # Store error
        self.error_data[service_name]['errors'].append(error_record)

        # Update error patterns
        await self._update_error_patterns(service_name, error_record)

        # Check for error bursts
        await self._check_error_burst(service_name, error_record)

    def _categorize_error(self, error_code: int) -> str:
        """Categorize error based on HTTP status code."""
        for category, codes in self.error_categories.items():
            if error_code in codes:
                return category
        return 'unknown_error'

    def _calculate_error_severity(self, error_code: int, error_message: str) -> str:
        """Calculate error severity based on code and message."""
        # Server errors are always high severity
        if error_code >= 500:
            return 'critical'

        # Client errors vary by type
        if error_code >= 400:
            if error_code in [401, 403, 429]:  # Security/auth related
                return 'high'
            elif error_code == 404:  # Not found
                return 'medium'
            else:
                return 'low'

        return 'low'

    async def _update_error_patterns(self, service_name: str, error_record: Dict[str, Any]) -> None:
        """Update error pattern analysis."""
        service_patterns = self.error_data[service_name]['error_patterns']

        # Create pattern key based on error characteristics
        pattern_key = f"{error_record['error_code']}_{error_record['endpoint']}_{error_record['error_category']}"

        service_patterns[pattern_key] += 1

        # Clean old patterns (keep only recent patterns)
        # In real implementation, this would have time-based cleanup

    async def _check_error_burst(self, service_name: str, error_record: Dict[str, Any]) -> None:
        """Check for error bursts that might indicate issues."""
        # Get recent errors (last 5 minutes)
        cutoff_time = datetime.now() - timedelta(minutes=5)
        recent_errors = [
            e for e in self.error_data[service_name]['errors']
            if e['timestamp'] > cutoff_time
        ]

        if len(recent_errors) >= self.error_thresholds['error_burst_threshold']:
            # Error burst detected
            await self._handle_error_burst(service_name, recent_errors)

    async def _handle_error_burst(self, service_name: str, recent_errors: List[Dict[str, Any]]) -> None:
        """Handle error burst detection."""
        # In real implementation, this would trigger alerts and mitigation
        burst_info = {
            'service': service_name,
            'error_count': len(recent_errors),
            'time_window_minutes': 5,
            'most_common_error': Counter(e['error_code'] for e in recent_errors).most_common(1)[0][0],
            'detected_at': datetime.now().isoformat()
        }

        print(f"Error burst detected: {burst_info}")

    async def get_error_overview(self, service_name: Optional[str] = None, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive error overview for the specified time range."""
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)

        overview = {
            'time_range_hours': time_range_hours,
            'total_errors': 0,
            'error_rate_percent': 0.0,
            'error_distribution': {},
            'service_breakdown': {},
            'error_categories': {},
            'severity_distribution': {},
            'top_error_patterns': [],
            'error_trends': {},
            'generated_at': datetime.now().isoformat()
        }

        # Get services to analyze
        services_to_analyze = await self._get_services_to_analyze(service_name)

        total_requests = 0
        total_errors = 0

        for svc_name in services_to_analyze:
            service_errors = [
                e for e in self.error_data[svc_name]['errors']
                if e['timestamp'] > cutoff_time
            ]

            if not service_errors:
                continue

            # Get total requests for error rate calculation (simplified)
            # In real system, this would come from usage analytics
            service_requests = len(service_errors) * 20  # Mock: assume 20 requests per error for rate calc
            total_requests += service_requests
            total_errors += len(service_errors)

            # Service breakdown
            overview['service_breakdown'][svc_name] = {
                'total_errors': len(service_errors),
                'error_rate_percent': (len(service_errors) / service_requests) * 100 if service_requests > 0 else 0,
                'most_common_error': Counter(e['error_code'] for e in service_errors).most_common(1)[0][0] if service_errors else None,
                'error_categories': dict(Counter(e['error_category'] for e in service_errors))
            }

        # Calculate overall metrics
        overview['total_errors'] = total_errors
        overview['error_rate_percent'] = (total_errors / total_requests) * 100 if total_requests > 0 else 0

        # Aggregate error distributions
        all_errors = []
        for svc_name in services_to_analyze:
            all_errors.extend([
                e for e in self.error_data[svc_name]['errors']
                if e['timestamp'] > cutoff_time
            ])

        if all_errors:
            overview['error_distribution'] = dict(Counter(e['error_code'] for e in all_errors))
            overview['error_categories'] = dict(Counter(e['error_category'] for e in all_errors))
            overview['severity_distribution'] = dict(Counter(e['severity'] for e in all_errors))

            # Top error patterns
            pattern_counts = Counter()
            for error in all_errors:
                pattern_key = f"{error['error_code']}_{error['endpoint']}_{error['error_category']}"
                pattern_counts[pattern_key] += 1

            overview['top_error_patterns'] = [
                {'pattern': pattern, 'count': count}
                for pattern, count in pattern_counts.most_common(10)
            ]

        return overview

    async def _get_services_to_analyze(self, service_name: Optional[str]) -> List[str]:
        """Get list of services to analyze."""
        if service_name:
            return [service_name]

        try:
            services = await self.discovery_client.get_all_services()
            return list(services.keys()) if services else []
        except Exception:
            return []

    async def analyze_error_patterns(self, service_name: Optional[str] = None, time_range_hours: int = 24) -> Dict[str, Any]:
        """Analyze error patterns and identify root causes."""
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)

        analysis = {
            'pattern_clusters': [],
            'root_cause_candidates': [],
            'correlation_insights': [],
            'predictive_warnings': [],
            'recommendations': []
        }

        services_to_analyze = await self._get_services_to_analyze(service_name)

        for svc_name in services_to_analyze:
            service_errors = [
                e for e in self.error_data[svc_name]['errors']
                if e['timestamp'] > cutoff_time
            ]

            if len(service_errors) < 10:  # Need minimum data for pattern analysis
                continue

            # Identify error patterns
            patterns = await self._identify_error_patterns(service_errors)
            analysis['pattern_clusters'].extend(patterns)

            # Analyze root causes
            root_causes = await self._analyze_root_causes(svc_name, service_errors)
            analysis['root_cause_candidates'].extend(root_causes)

            # Generate recommendations
            recommendations = await self._generate_error_recommendations(svc_name, service_errors, patterns)
            analysis['recommendations'].extend(recommendations)

        return analysis

    async def _identify_error_patterns(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify recurring error patterns."""
        patterns = []

        # Group errors by various dimensions
        error_codes = Counter(e['error_code'] for e in errors)
        endpoints = Counter(e['endpoint'] for e in errors)
        error_messages = Counter(e['error_message'] for e in errors)

        # Identify significant patterns
        for error_code, count in error_codes.items():
            if count >= self.error_thresholds['error_pattern_threshold']:
                code_errors = [e for e in errors if e['error_code'] == error_code]
                endpoints_affected = set(e['endpoint'] for e in code_errors)

                patterns.append({
                    'type': 'error_code_pattern',
                    'error_code': error_code,
                    'frequency': count,
                    'percentage': (count / len(errors)) * 100,
                    'endpoints_affected': list(endpoints_affected),
                    'temporal_pattern': self._analyze_temporal_pattern(code_errors),
                    'severity': 'high' if count > len(errors) * 0.2 else 'medium'
                })

        # Endpoint-specific patterns
        for endpoint, count in endpoints.items():
            if count >= self.error_thresholds['error_pattern_threshold']:
                endpoint_errors = [e for e in errors if e['endpoint'] == endpoint]
                error_codes = Counter(e['error_code'] for e in endpoint_errors)

                patterns.append({
                    'type': 'endpoint_pattern',
                    'endpoint': endpoint,
                    'frequency': count,
                    'percentage': (count / len(errors)) * 100,
                    'error_codes': dict(error_codes),
                    'most_common_error': error_codes.most_common(1)[0][0],
                    'severity': 'high' if count > len(errors) * 0.15 else 'medium'
                })

        return patterns

    def _analyze_temporal_pattern(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal patterns in errors."""
        if not errors:
            return {}

        hours = Counter(e['hour'] for e in errors)
        days = Counter(e['day_of_week'] for e in errors)

        return {
            'peak_hour': hours.most_common(1)[0][0] if hours else None,
            'peak_day': days.most_common(1)[0][0] if days else None,
            'hourly_distribution': dict(hours),
            'daily_distribution': dict(days)
        }

    async def _analyze_root_causes(self, service_name: str, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze potential root causes of errors."""
        root_causes = []

        # Analyze error messages for common patterns
        error_messages = [e['error_message'] for e in errors]

        # Check for database-related errors
        db_errors = [msg for msg in error_messages if re.search(r'database|db|sql|connection', msg, re.I)]
        if len(db_errors) > len(errors) * 0.1:
            root_causes.append({
                'type': 'database_issues',
                'confidence': min(len(db_errors) / len(errors) * 2, 1.0),
                'evidence': f"{len(db_errors)} database-related errors",
                'recommendations': [
                    'Check database connectivity',
                    'Review database performance',
                    'Consider connection pooling'
                ]
            })

        # Check for timeout errors
        timeout_errors = [e for e in errors if e['error_code'] in [408, 504]]
        if len(timeout_errors) > len(errors) * 0.1:
            root_causes.append({
                'type': 'timeout_issues',
                'confidence': min(len(timeout_errors) / len(errors) * 2, 1.0),
                'evidence': f"{len(timeout_errors)} timeout errors",
                'recommendations': [
                    'Increase timeout thresholds',
                    'Optimize slow operations',
                    'Implement async processing'
                ]
            })

        # Check for authentication errors
        auth_errors = [e for e in errors if e['error_code'] in [401, 403]]
        if len(auth_errors) > len(errors) * 0.05:
            root_causes.append({
                'type': 'authentication_issues',
                'confidence': min(len(auth_errors) / len(errors) * 3, 1.0),
                'evidence': f"{len(auth_errors)} authentication errors",
                'recommendations': [
                    'Review authentication logic',
                    'Check token validation',
                    'Verify user permissions'
                ]
            })

        return root_causes

    async def _generate_error_recommendations(self, service_name: str, errors: List[Dict[str, Any]], patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate error mitigation recommendations."""
        recommendations = []

        # Analyze error rate
        error_rate = len(errors) / max(1, len(errors) * 20) * 100  # Mock calculation

        if error_rate > self.error_thresholds['critical_error_rate_percent']:
            recommendations.append({
                'service': service_name,
                'priority': 'critical',
                'type': 'immediate_attention',
                'description': f"Critical error rate: {error_rate:.1f}%",
                'actions': [
                    'Implement circuit breaker pattern',
                    'Set up error rate alerts',
                    'Prepare rollback plan'
                ]
            })
        elif error_rate > self.error_thresholds['max_error_rate_percent']:
            recommendations.append({
                'service': service_name,
                'priority': 'high',
                'type': 'error_rate_monitoring',
                'description': f"High error rate: {error_rate:.1f}%",
                'actions': [
                    'Increase monitoring frequency',
                    'Analyze error patterns',
                    'Implement error recovery mechanisms'
                ]
            })

        # Pattern-based recommendations
        for pattern in patterns:
            if pattern['severity'] == 'high':
                if pattern['type'] == 'endpoint_pattern':
                    recommendations.append({
                        'service': service_name,
                        'priority': 'high',
                        'type': 'endpoint_specific',
                        'description': f"High error rate on endpoint: {pattern['endpoint']}",
                        'actions': [
                            'Review endpoint logic',
                            'Add input validation',
                            'Implement rate limiting'
                        ]
                    })

        return recommendations

    async def get_error_alerts(self, service_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get current error alerts and warnings."""
        alerts = []

        services_to_check = await self._get_services_to_analyze(service_name)

        for svc_name in services_to_check:
            service_alerts = await self._check_service_error_alerts(svc_name)
            alerts.extend(service_alerts)

        return alerts

    async def _check_service_error_alerts(self, service_name: str) -> List[Dict[str, Any]]:
        """Check for error alerts for a specific service."""
        alerts = []

        # Get recent errors (last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_errors = [
            e for e in self.error_data[service_name]['errors']
            if e['timestamp'] > cutoff_time
        ]

        # Check error rate
        error_rate = len(recent_errors) / max(1, len(recent_errors) * 20) * 100  # Mock calculation

        if error_rate > self.error_thresholds['critical_error_rate_percent']:
            alerts.append({
                'service': service_name,
                'severity': 'critical',
                'type': 'high_error_rate',
                'message': f"Critical error rate: {error_rate:.1f}% in last hour",
                'timestamp': datetime.now().isoformat(),
                'recommendations': ['Check service health', 'Review recent deployments', 'Enable circuit breaker']
            })
        elif error_rate > self.error_thresholds['max_error_rate_percent']:
            alerts.append({
                'service': service_name,
                'severity': 'warning',
                'type': 'elevated_error_rate',
                'message': f"Elevated error rate: {error_rate:.1f}% in last hour",
                'timestamp': datetime.now().isoformat(),
                'recommendations': ['Monitor error trends', 'Review error patterns', 'Check resource utilization']
            })

        # Check for error bursts
        burst_cutoff = datetime.now() - timedelta(minutes=5)
        burst_errors = [
            e for e in self.error_data[service_name]['errors']
            if e['timestamp'] > burst_cutoff
        ]

        if len(burst_errors) >= self.error_thresholds['error_burst_threshold']:
            alerts.append({
                'service': service_name,
                'severity': 'warning',
                'type': 'error_burst',
                'message': f"Error burst detected: {len(burst_errors)} errors in last 5 minutes",
                'timestamp': datetime.now().isoformat(),
                'recommendations': ['Check for service degradation', 'Review traffic patterns', 'Enable auto-scaling']
            })

        return alerts

    async def generate_error_report(self, service_name: Optional[str] = None, time_range_hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive error analysis report."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'time_range_hours': time_range_hours,
            'executive_summary': {},
            'error_analysis': {},
            'trends_and_patterns': {},
            'recommendations': {},
            'alerts': []
        }

        # Gather error data
        error_overview = await self.get_error_overview(service_name, time_range_hours)
        error_patterns = await self.analyze_error_patterns(service_name, time_range_hours)
        error_alerts = await self.get_error_alerts(service_name)

        # Generate executive summary
        report['executive_summary'] = await self._generate_error_executive_summary(error_overview)

        # Compile analysis
        report['error_analysis'] = {
            'overview': error_overview,
            'patterns': error_patterns,
            'root_cause_analysis': error_patterns.get('root_cause_candidates', [])
        }

        # Add trends and patterns
        report['trends_and_patterns'] = await self._analyze_error_trends(service_name, time_range_hours)

        # Compile recommendations
        report['recommendations'] = error_patterns.get('recommendations', [])

        # Add alerts
        report['alerts'] = error_alerts

        return report

    async def _generate_error_executive_summary(self, error_overview: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary for error report."""
        error_rate = error_overview.get('error_rate_percent', 0)
        total_errors = error_overview.get('total_errors', 0)

        # Calculate error health score
        health_score = 100
        if error_rate > 10:
            health_score -= 40
        elif error_rate > 5:
            health_score -= 20
        elif error_rate > 1:
            health_score -= 10

        health_score = max(0, health_score)

        return {
            'error_health_score': health_score,
            'error_health_grade': 'A' if health_score >= 90 else 'B' if health_score >= 80 else 'C' if health_score >= 70 else 'D',
            'total_errors': total_errors,
            'error_rate_percent': error_rate,
            'services_with_errors': len(error_overview.get('service_breakdown', {})),
            'most_common_error_category': self._get_most_common_category(error_overview),
            'error_trend': 'improving' if error_rate < 2 else 'stable' if error_rate < 5 else 'concerning'
        }

    def _get_most_common_category(self, error_overview: Dict[str, Any]) -> str:
        """Get the most common error category."""
        categories = error_overview.get('error_categories', {})
        if not categories:
            return 'none'

        return max(categories.items(), key=lambda x: x[1])[0]

    async def _analyze_error_trends(self, service_name: Optional[str], time_range_hours: int) -> Dict[str, Any]:
        """Analyze error trends over time."""
        # Simplified trend analysis (in real system, this would analyze historical data)
        return {
            'error_rate_trend': 'decreasing',
            'error_pattern_stability': 'stable',
            'new_error_types': 0,
            'resolved_error_patterns': 1,
            'predicted_error_rate': 'stable',
            'confidence_level': 'medium'
        }
