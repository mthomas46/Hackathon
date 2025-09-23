"""Usage Patterns Analysis for Unified API Ecosystem Dashboard.

This module analyzes usage patterns and trends across the API ecosystem including:
- Temporal usage patterns (hourly, daily, weekly)
- User behavior analysis and segmentation
- API consumption patterns and forecasting
- Service dependency and interaction analysis
- Usage anomaly detection and alerting
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter
import json
import statistics
from sklearn.cluster import KMeans
import numpy as np

from ..discovery.client import DiscoveryClient
from ..monitoring.health import HealthMonitor


class UsagePatterns:
    """Advanced usage pattern analysis and behavioral insights."""

    def __init__(self, discovery_client: DiscoveryClient, health_monitor: HealthMonitor):
        self.discovery_client = discovery_client
        self.health_monitor = health_monitor

        # Pattern data storage
        self.pattern_data = defaultdict(lambda: {
            'temporal_patterns': defaultdict(list),
            'user_behaviors': defaultdict(list),
            'api_sequences': defaultdict(list),
            'usage_anomalies': [],
            'trend_forecasts': {}
        })

        # Pattern analysis configuration
        self.pattern_config = {
            'temporal_resolution_hours': 1,
            'user_segmentation_clusters': 5,
            'sequence_analysis_window_days': 7,
            'anomaly_detection_sensitivity': 0.95,
            'forecast_horizon_days': 30,
            'pattern_retention_days': 90
        }

    async def record_usage_pattern(self, service_name: str, user_id: str, session_id: str,
                                  endpoint: str, method: str, timestamp: datetime,
                                  client_info: Optional[Dict[str, Any]] = None) -> None:
        """Record usage pattern data for analysis."""
        pattern_record = {
            'service': service_name,
            'user_id': user_id,
            'session_id': session_id,
            'endpoint': endpoint,
            'method': method,
            'timestamp': timestamp,
            'client_info': client_info or {},
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'month': timestamp.month,
            'quarter': (timestamp.month - 1) // 3 + 1
        }

        # Update temporal patterns
        await self._update_temporal_patterns(service_name, pattern_record)

        # Update user behavior patterns
        await self._update_user_behaviors(user_id, pattern_record)

        # Update API sequences
        await self._update_api_sequences(session_id, pattern_record)

    async def _update_temporal_patterns(self, service_name: str, pattern_record: Dict[str, Any]) -> None:
        """Update temporal usage patterns."""
        service_patterns = self.pattern_data[service_name]['temporal_patterns']

        # Hourly patterns
        hour_key = pattern_record['hour']
        service_patterns['hourly'].append({
            'hour': hour_key,
            'timestamp': pattern_record['timestamp'],
            'endpoint': pattern_record['endpoint']
        })

        # Daily patterns
        day_key = pattern_record['day_of_week']
        service_patterns['daily'].append({
            'day': day_key,
            'timestamp': pattern_record['timestamp'],
            'endpoint': pattern_record['endpoint']
        })

        # Weekly patterns (rolling 7-day windows)
        week_start = pattern_record['timestamp'] - timedelta(days=pattern_record['timestamp'].weekday())
        week_key = week_start.date().isoformat()
        if week_key not in service_patterns['weekly']:
            service_patterns['weekly'][week_key] = []
        service_patterns['weekly'][week_key].append(pattern_record)

        # Clean old data
        cutoff_time = datetime.now() - timedelta(days=self.pattern_config['pattern_retention_days'])
        for pattern_type in service_patterns.values():
            if isinstance(pattern_type, list):
                pattern_type[:] = [p for p in pattern_type if p['timestamp'] > cutoff_time]

    async def _update_user_behaviors(self, user_id: str, pattern_record: Dict[str, Any]) -> None:
        """Update user behavior patterns."""
        user_patterns = self.pattern_data[user_id]['user_behaviors']

        user_patterns.append({
            'timestamp': pattern_record['timestamp'],
            'service': pattern_record['service'],
            'endpoint': pattern_record['endpoint'],
            'method': pattern_record['method'],
            'session_id': pattern_record['session_id']
        })

        # Limit user behavior history
        if len(user_patterns) > 1000:  # Keep last 1000 actions
            user_patterns[:] = user_patterns[-1000:]

    async def _update_api_sequences(self, session_id: str, pattern_record: Dict[str, Any]) -> None:
        """Update API call sequences within sessions."""
        if session_id not in self.pattern_data:
            self.pattern_data[session_id]['api_sequences'] = []

        session_sequences = self.pattern_data[session_id]['api_sequences']
        session_sequences.append({
            'timestamp': pattern_record['timestamp'],
            'service': pattern_record['service'],
            'endpoint': pattern_record['endpoint'],
            'method': pattern_record['method']
        })

        # Sort by timestamp
        session_sequences.sort(key=lambda x: x['timestamp'])

    async def analyze_temporal_patterns(self, service_name: Optional[str] = None, time_range_days: int = 30) -> Dict[str, Any]:
        """Analyze temporal usage patterns and trends."""
        cutoff_time = datetime.now() - timedelta(days=time_range_days)

        analysis = {
            'hourly_patterns': {},
            'daily_patterns': {},
            'weekly_patterns': {},
            'seasonal_patterns': {},
            'peak_usage_times': [],
            'usage_forecasts': {}
        }

        services_to_analyze = await self._get_services_to_analyze(service_name)

        for svc_name in services_to_analyze:
            if svc_name not in self.pattern_data:
                continue

            service_patterns = self.pattern_data[svc_name]['temporal_patterns']

            # Analyze hourly patterns
            hourly_data = [p for p in service_patterns.get('hourly', []) if p['timestamp'] > cutoff_time]
            if hourly_data:
                analysis['hourly_patterns'][svc_name] = await self._analyze_hourly_patterns(hourly_data)

            # Analyze daily patterns
            daily_data = [p for p in service_patterns.get('daily', []) if p['timestamp'] > cutoff_time]
            if daily_data:
                analysis['daily_patterns'][svc_name] = await self._analyze_daily_patterns(daily_data)

            # Analyze weekly patterns
            weekly_data = service_patterns.get('weekly', {})
            if weekly_data:
                analysis['weekly_patterns'][svc_name] = await self._analyze_weekly_patterns(weekly_data)

        # Identify peak usage times across all services
        analysis['peak_usage_times'] = await self._identify_peak_usage_times(analysis)

        # Generate usage forecasts
        analysis['usage_forecasts'] = await self._generate_usage_forecasts(analysis, time_range_days)

        return analysis

    async def _analyze_hourly_patterns(self, hourly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze hourly usage patterns."""
        hour_counts = Counter(item['hour'] for item in hourly_data)

        # Calculate peak hours
        peak_hours = hour_counts.most_common(3)

        # Calculate hourly distribution
        total_requests = len(hourly_data)
        hourly_distribution = {
            hour: {
                'count': count,
                'percentage': (count / total_requests) * 100,
                'endpoints': Counter(item['endpoint'] for item in hourly_data if item['hour'] == hour)
            }
            for hour, count in hour_counts.items()
        }

        # Identify usage patterns
        morning_hours = sum(hourly_distribution.get(h, {}).get('count', 0) for h in range(6, 12))
        afternoon_hours = sum(hourly_distribution.get(h, {}).get('count', 0) for h in range(12, 18))
        evening_hours = sum(hourly_distribution.get(h, {}).get('count', 0) for h in range(18, 24))
        night_hours = sum(hourly_distribution.get(h, {}).get('count', 0) for h in range(0, 6))

        return {
            'peak_hours': [{'hour': h, 'requests': c, 'percentage': (c/total_requests)*100} for h, c in peak_hours],
            'hourly_distribution': hourly_distribution,
            'usage_segments': {
                'morning': {'requests': morning_hours, 'percentage': (morning_hours/total_requests)*100},
                'afternoon': {'requests': afternoon_hours, 'percentage': (afternoon_hours/total_requests)*100},
                'evening': {'requests': evening_hours, 'percentage': (evening_hours/total_requests)*100},
                'night': {'requests': night_hours, 'percentage': (night_hours/total_requests)*100}
            },
            'total_requests': total_requests
        }

    async def _analyze_daily_patterns(self, daily_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze daily usage patterns."""
        day_counts = Counter(item['day'] for item in daily_data)

        # Day name mapping
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # Calculate weekday vs weekend patterns
        weekday_requests = sum(day_counts.get(d, 0) for d in range(5))  # Mon-Fri
        weekend_requests = sum(day_counts.get(d, 0) for d in [5, 6])   # Sat-Sun
        total_requests = len(daily_data)

        return {
            'daily_distribution': {
                day_names[day]: {
                    'count': count,
                    'percentage': (count / total_requests) * 100 if total_requests > 0 else 0
                }
                for day, count in day_counts.items()
            },
            'weekday_vs_weekend': {
                'weekday': {
                    'requests': weekday_requests,
                    'percentage': (weekday_requests / total_requests) * 100 if total_requests > 0 else 0
                },
                'weekend': {
                    'requests': weekend_requests,
                    'percentage': (weekend_requests / total_requests) * 100 if total_requests > 0 else 0
                }
            },
            'peak_days': [day_names[d] for d, _ in day_counts.most_common(2)],
            'total_requests': total_requests
        }

    async def _analyze_weekly_patterns(self, weekly_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze weekly usage patterns."""
        weekly_stats = {}

        for week_start, week_data in weekly_data.items():
            if not week_data:
                continue

            weekly_stats[week_start] = {
                'total_requests': len(week_data),
                'unique_endpoints': len(set(item['endpoint'] for item in week_data)),
                'daily_average': len(week_data) / 7,
                'start_date': week_start
            }

        # Calculate weekly trends
        if len(weekly_stats) >= 2:
            weekly_counts = [stats['total_requests'] for stats in weekly_stats.values()]
            trend = self._calculate_trend_slope(weekly_counts)

            trend_direction = 'increasing' if trend > 0.05 else 'decreasing' if trend < -0.05 else 'stable'
        else:
            trend_direction = 'insufficient_data'

        return {
            'weekly_stats': weekly_stats,
            'trend_direction': trend_direction,
            'total_weeks': len(weekly_stats),
            'avg_weekly_requests': sum(s['total_requests'] for s in weekly_stats.values()) / max(1, len(weekly_stats))
        }

    def _calculate_trend_slope(self, values: List[float]) -> float:
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

    async def _identify_peak_usage_times(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify peak usage times across all services."""
        peak_times = []

        # Collect all peak hours from services
        for service_name, hourly_patterns in analysis.get('hourly_patterns', {}).items():
            for peak_info in hourly_patterns.get('peak_hours', []):
                peak_times.append({
                    'service': service_name,
                    'hour': peak_info['hour'],
                    'requests': peak_info['requests'],
                    'percentage': peak_info['percentage']
                })

        # Sort by request volume and return top peaks
        peak_times.sort(key=lambda x: x['requests'], reverse=True)
        return peak_times[:10]  # Top 10 peak times

    async def _generate_usage_forecasts(self, analysis: Dict[str, Any], time_range_days: int) -> Dict[str, Any]:
        """Generate usage forecasts based on historical patterns."""
        forecasts = {
            'hourly_forecast': {},
            'daily_forecast': {},
            'weekly_forecast': {},
            'confidence_intervals': {}
        }

        # Simple forecasting based on recent trends (in real system, use time series analysis)
        for service_name, weekly_patterns in analysis.get('weekly_patterns', {}).items():
            trend_direction = weekly_patterns.get('trend_direction', 'stable')

            if trend_direction == 'increasing':
                growth_rate = 1.1  # 10% growth
            elif trend_direction == 'decreasing':
                growth_rate = 0.9  # 10% decline
            else:
                growth_rate = 1.0  # Stable

            current_avg = weekly_patterns.get('avg_weekly_requests', 0)
            forecast_avg = current_avg * growth_rate

            forecasts['weekly_forecast'][service_name] = {
                'current_average': current_avg,
                'forecast_average': forecast_avg,
                'growth_rate': (growth_rate - 1) * 100,
                'confidence_level': 'medium'
            }

        return forecasts

    async def analyze_user_behaviors(self, time_range_days: int = 30) -> Dict[str, Any]:
        """Analyze user behavior patterns and segmentation."""
        cutoff_time = datetime.now() - timedelta(days=time_range_days)

        analysis = {
            'user_segments': {},
            'behavior_patterns': {},
            'engagement_metrics': {},
            'user_journey_analysis': {},
            'recommendations': []
        }

        # Collect user behavior data
        user_behaviors = defaultdict(list)
        for key, data in self.pattern_data.items():
            if 'user_behaviors' in data:
                behaviors = [b for b in data['user_behaviors'] if b['timestamp'] > cutoff_time]
                if behaviors:
                    user_behaviors[key].extend(behaviors)

        if not user_behaviors:
            return analysis

        # Analyze user engagement
        analysis['engagement_metrics'] = await self._analyze_user_engagement(user_behaviors)

        # Segment users based on behavior
        analysis['user_segments'] = await self._segment_users(user_behaviors)

        # Analyze behavior patterns
        analysis['behavior_patterns'] = await self._analyze_behavior_patterns(user_behaviors)

        # Analyze user journeys
        analysis['user_journey_analysis'] = await self._analyze_user_journeys(user_behaviors)

        # Generate recommendations
        analysis['recommendations'] = await self._generate_user_recommendations(analysis)

        return analysis

    async def _analyze_user_engagement(self, user_behaviors: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze user engagement metrics."""
        engagement = {
            'total_users': len(user_behaviors),
            'active_users': 0,
            'highly_active_users': 0,
            'average_sessions_per_user': 0,
            'average_requests_per_session': 0,
            'user_retention': {}
        }

        total_sessions = 0
        total_requests = 0

        for user_id, behaviors in user_behaviors.items():
            if not behaviors:
                continue

            # Count active users (users with activity in last 7 days)
            recent_activity = [b for b in behaviors if b['timestamp'] > datetime.now() - timedelta(days=7)]
            if recent_activity:
                engagement['active_users'] += 1

            # Count highly active users (users with > 50 requests in time period)
            if len(behaviors) > 50:
                engagement['highly_active_users'] += 1

            # Count sessions for this user
            sessions = set(b['session_id'] for b in behaviors)
            total_sessions += len(sessions)
            total_requests += len(behaviors)

        engagement['average_sessions_per_user'] = total_sessions / max(1, engagement['total_users'])
        engagement['average_requests_per_session'] = total_requests / max(1, total_sessions)

        return engagement

    async def _segment_users(self, user_behaviors: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Segment users based on behavior patterns."""
        if len(user_behaviors) < 10:  # Need minimum users for segmentation
            return {'segments': {}, 'note': 'Insufficient data for segmentation'}

        # Extract features for clustering
        user_features = []
        user_ids = []

        for user_id, behaviors in user_behaviors.items():
            if len(behaviors) < 5:  # Skip users with too few actions
                continue

            # Calculate user features
            session_count = len(set(b['session_id'] for b in behaviors))
            request_count = len(behaviors)
            service_diversity = len(set(b['service'] for b in behaviors))
            time_span = (max(b['timestamp'] for b in behaviors) - min(b['timestamp'] for b in behaviors)).total_seconds() / 3600  # hours

            features = [
                request_count,  # Total requests
                session_count,  # Session count
                request_count / max(1, session_count),  # Avg requests per session
                service_diversity,  # Service diversity
                time_span  # Activity time span
            ]

            user_features.append(features)
            user_ids.append(user_id)

        if len(user_features) < self.pattern_config['user_segmentation_clusters']:
            return {'segments': {}, 'note': 'Insufficient users for clustering'}

        # Perform clustering
        try:
            X = np.array(user_features)
            kmeans = KMeans(n_clusters=self.pattern_config['user_segmentation_clusters'], random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X)

            # Analyze cluster characteristics
            segments = {}
            for i in range(self.pattern_config['user_segmentation_clusters']):
                cluster_users = [user_ids[j] for j in range(len(user_ids)) if clusters[j] == i]
                cluster_features = [user_features[j] for j in range(len(user_features)) if clusters[j] == i]

                if cluster_features:
                    avg_features = np.mean(cluster_features, axis=0)

                    segments[f'segment_{i}'] = {
                        'user_count': len(cluster_users),
                        'percentage': (len(cluster_users) / len(user_ids)) * 100,
                        'avg_requests': avg_features[0],
                        'avg_sessions': avg_features[1],
                        'avg_requests_per_session': avg_features[2],
                        'service_diversity': avg_features[3],
                        'activity_span_hours': avg_features[4],
                        'characteristics': self._describe_segment(avg_features)
                    }

            return {'segments': segments}

        except Exception:
            return {'segments': {}, 'note': 'Clustering failed'}

    def _describe_segment(self, features: np.ndarray) -> str:
        """Generate human-readable description of user segment."""
        requests, sessions, requests_per_session, service_diversity, activity_span = features

        descriptions = []

        if requests > 100:
            descriptions.append("high-volume user")
        elif requests > 50:
            descriptions.append("medium-volume user")
        else:
            descriptions.append("low-volume user")

        if service_diversity > 3:
            descriptions.append("with high service diversity")
        elif service_diversity > 1:
            descriptions.append("with moderate service diversity")
        else:
            descriptions.append("focused on single service")

        if requests_per_session > 10:
            descriptions.append("making many requests per session")
        elif requests_per_session > 5:
            descriptions.append("moderately active per session")
        else:
            descriptions.append("lightly active per session")

        return ", ".join(descriptions)

    async def _analyze_behavior_patterns(self, user_behaviors: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze common behavior patterns."""
        patterns = {
            'common_service_sequences': [],
            'peak_usage_times': {},
            'preferred_endpoints': {},
            'session_durations': {}
        }

        # Analyze common service sequences (simplified)
        service_sequences = []
        for user_id, behaviors in user_behaviors.items():
            user_services = [b['service'] for b in sorted(behaviors, key=lambda x: x['timestamp'])]
            if len(user_services) >= 3:
                # Get sequences of 3 services
                for i in range(len(user_services) - 2):
                    sequence = tuple(user_services[i:i+3])
                    service_sequences.append(sequence)

        if service_sequences:
            sequence_counts = Counter(service_sequences)
            patterns['common_service_sequences'] = [
                {'sequence': seq, 'count': count, 'frequency': count / len(service_sequences)}
                for seq, count in sequence_counts.most_common(5)
            ]

        # Analyze preferred endpoints
        all_endpoints = []
        for behaviors in user_behaviors.values():
            all_endpoints.extend(b['endpoint'] for b in behaviors)

        endpoint_counts = Counter(all_endpoints)
        patterns['preferred_endpoints'] = dict(endpoint_counts.most_common(10))

        return patterns

    async def _analyze_user_journeys(self, user_behaviors: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze user journey patterns."""
        journeys = {
            'common_paths': [],
            'drop_off_points': [],
            'conversion_funnels': {}
        }

        # Simplified journey analysis (in real system, use more sophisticated methods)
        service_transitions = defaultdict(lambda: defaultdict(int))

        for user_id, behaviors in user_behaviors.items():
            sorted_behaviors = sorted(behaviors, key=lambda x: x['timestamp'])

            for i in range(len(sorted_behaviors) - 1):
                current_service = sorted_behaviors[i]['service']
                next_service = sorted_behaviors[i + 1]['service']
                service_transitions[current_service][next_service] += 1

        # Identify common transition paths
        common_paths = []
        for from_service, transitions in service_transitions.items():
            total_transitions = sum(transitions.values())
            for to_service, count in transitions.items():
                if count > total_transitions * 0.1:  # > 10% of transitions
                    common_paths.append({
                        'from_service': from_service,
                        'to_service': to_service,
                        'count': count,
                        'percentage': (count / total_transitions) * 100
                    })

        journeys['common_paths'] = sorted(common_paths, key=lambda x: x['count'], reverse=True)[:10]

        return journeys

    async def _generate_user_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on user behavior analysis."""
        recommendations = []

        engagement = analysis.get('engagement_metrics', {})

        # Engagement-based recommendations
        active_user_rate = engagement.get('active_users', 0) / max(1, engagement.get('total_users', 1))
        if active_user_rate < 0.3:
            recommendations.append({
                'type': 'engagement_improvement',
                'priority': 'high',
                'description': f"Only {active_user_rate:.1f}% of users are active in the last 7 days",
                'actions': [
                    'Implement user engagement campaigns',
                    'Send personalized usage reminders',
                    'Improve onboarding experience'
                ]
            })

        # Segmentation-based recommendations
        segments = analysis.get('user_segments', {}).get('segments', {})
        if segments:
            # Check for high-value user segment
            high_value_segments = [
                seg for seg in segments.values()
                if seg.get('avg_requests', 0) > 100
            ]

            if high_value_segments:
                recommendations.append({
                    'type': 'high_value_user_retention',
                    'priority': 'high',
                    'description': f"Identified {len(high_value_segments)} high-value user segments",
                    'actions': [
                        'Implement premium features for high-volume users',
                        'Create loyalty programs',
                        'Provide dedicated support channels'
                    ]
                })

        return recommendations

    async def detect_usage_anomalies(self, service_name: Optional[str] = None, sensitivity: float = 0.95) -> Dict[str, Any]:
        """Detect usage anomalies using statistical analysis."""
        anomalies = {
            'spike_anomalies': [],
            'drop_anomalies': [],
            'unusual_pattern_anomalies': [],
            'user_behavior_anomalies': []
        }

        # Simplified anomaly detection (in real system, use more sophisticated methods)
        services_to_check = await self._get_services_to_analyze(service_name)

        for svc_name in services_to_check:
            if svc_name not in self.pattern_data:
                continue

            # Check for temporal pattern anomalies
            temporal_patterns = self.pattern_data[svc_name]['temporal_patterns']

            # Simple spike detection
            hourly_data = temporal_patterns.get('hourly', [])
            if len(hourly_data) >= 24:  # Need at least 24 hours of data
                recent_hour = hourly_data[-1]
                baseline_hours = hourly_data[-25:-1]  # Previous 24 hours

                if baseline_hours:
                    baseline_avg = sum(len([h for h in baseline_hours if h['hour'] == recent_hour['hour']]) for h in baseline_hours) / len(baseline_hours)
                    current_count = 1  # Simplified

                    if current_count > baseline_avg * 3:  # 3x spike
                        anomalies['spike_anomalies'].append({
                            'service': svc_name,
                            'type': 'usage_spike',
                            'current_value': current_count,
                            'baseline_average': baseline_avg,
                            'multiplier': current_count / baseline_avg,
                            'timestamp': recent_hour['timestamp']
                        })

        return anomalies

    async def _get_services_to_analyze(self, service_name: Optional[str]) -> List[str]:
        """Get list of services to analyze."""
        if service_name:
            return [service_name]

        try:
            services = await self.discovery_client.get_all_services()
            return list(services.keys()) if services else []
        except Exception:
            return []

    async def generate_usage_insights_report(self, service_name: Optional[str] = None, time_range_days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive usage insights report."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'time_range_days': time_range_days,
            'executive_summary': {},
            'temporal_analysis': {},
            'user_behavior_analysis': {},
            'anomaly_detection': {},
            'forecasts_and_predictions': {},
            'recommendations': []
        }

        # Gather all analysis data
        temporal_analysis = await self.analyze_temporal_patterns(service_name, time_range_days)
        user_behavior_analysis = await self.analyze_user_behaviors(time_range_days)
        anomaly_detection = await self.detect_usage_anomalies(service_name)

        # Generate executive summary
        report['executive_summary'] = await self._generate_usage_executive_summary(
            temporal_analysis, user_behavior_analysis, anomaly_detection
        )

        # Compile analysis sections
        report['temporal_analysis'] = temporal_analysis
        report['user_behavior_analysis'] = user_behavior_analysis
        report['anomaly_detection'] = anomaly_detection

        # Add forecasts
        report['forecasts_and_predictions'] = temporal_analysis.get('usage_forecasts', {})

        # Generate recommendations
        report['recommendations'] = await self._generate_usage_recommendations(
            temporal_analysis, user_behavior_analysis, anomaly_detection
        )

        return report

    async def _generate_usage_executive_summary(self, temporal: Dict, user_behavior: Dict, anomalies: Dict) -> Dict[str, Any]:
        """Generate executive summary for usage insights report."""
        summary = {
            'key_insights': [],
            'usage_health_score': 100,
            'total_services_analyzed': len(temporal.get('hourly_patterns', {})),
            'active_users': user_behavior.get('engagement_metrics', {}).get('active_users', 0),
            'anomaly_count': len(anomalies.get('spike_anomalies', [])) + len(anomalies.get('drop_anomalies', []))
        }

        # Deduct points for anomalies
        if summary['anomaly_count'] > 0:
            summary['usage_health_score'] -= summary['anomaly_count'] * 10

        # Generate key insights
        if temporal.get('peak_usage_times'):
            peak_time = temporal['peak_usage_times'][0]
            summary['key_insights'].append(f"Peak usage occurs at {peak_time['hour']}:00 with {peak_time['requests']} requests")

        engagement = user_behavior.get('engagement_metrics', {})
        if engagement.get('active_users', 0) > 0:
            active_rate = engagement['active_users'] / max(1, engagement.get('total_users', 1)) * 100
            summary['key_insights'].append(f"{active_rate:.1f}% of users are active in the last 7 days")

        return summary

    async def _generate_usage_recommendations(self, temporal: Dict, user_behavior: Dict, anomalies: Dict) -> List[Dict[str, Any]]:
        """Generate usage-based recommendations."""
        recommendations = []

        # Temporal-based recommendations
        peak_times = temporal.get('peak_usage_times', [])
        if peak_times:
            top_peak = peak_times[0]
            recommendations.append({
                'type': 'capacity_planning',
                'priority': 'medium',
                'description': f"Plan for peak usage at {top_peak['hour']}:00",
                'actions': ['Scale resources during peak hours', 'Implement load balancing']
            })

        # User behavior recommendations
        user_recs = user_behavior.get('recommendations', [])
        recommendations.extend(user_recs)

        # Anomaly-based recommendations
        spike_anomalies = anomalies.get('spike_anomalies', [])
        if spike_anomalies:
            recommendations.append({
                'type': 'anomaly_response',
                'priority': 'high',
                'description': f"Detected {len(spike_anomalies)} usage spikes requiring attention",
                'actions': ['Investigate spike causes', 'Implement rate limiting if needed']
            })

        return recommendations
