"""Quality Degradation Detection module for Analysis Service.

Monitors documentation quality over time and detects when quality is degrading,
providing alerts, analysis, and recommendations for quality maintenance.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

try:
    import pandas as pd
    import numpy as np
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from scipy import stats
    from scipy.signal import find_peaks
    import warnings
    warnings.filterwarnings('ignore')
    QUALITY_DEGRADATION_AVAILABLE = True
except ImportError:
    QUALITY_DEGRADATION_AVAILABLE = False
    pd = None
    np = None
    LinearRegression = None
    Ridge = None
    StandardScaler = None
    mean_absolute_error = None
    mean_squared_error = None
    stats = None
    find_peaks = None

from services.shared.core.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes

logger = logging.getLogger(__name__)


class QualityDegradationDetector:
    """Detects and analyzes quality degradation in documentation over time."""

    def __init__(self):
        """Initialize the quality degradation detector."""
        self.initialized = False
        self.degradation_thresholds = self._get_default_thresholds()
        self.baseline_periods = {
            'short_term': 30,    # 30 days
            'medium_term': 90,   # 90 days
            'long_term': 365     # 365 days
        }
        self._initialize_detector()

    def _initialize_detector(self) -> bool:
        """Initialize the quality degradation detection components."""
        if not QUALITY_DEGRADATION_AVAILABLE:
            logger.warning("Quality degradation detection dependencies not available")
            return False

        self.scaler = StandardScaler()
        self.initialized = True
        return True

    def _get_default_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Define default quality degradation detection thresholds."""
        return {
            'quality_score_decline': {
                'warning_threshold': -0.05,    # 5% decline
                'critical_threshold': -0.10,   # 10% decline
                'minimum_samples': 3,
                'confidence_required': 0.7
            },
            'trend_slope': {
                'warning_threshold': -0.001,   # Negative slope per day
                'critical_threshold': -0.005,  # Steep negative slope
                'minimum_samples': 5,
                'confidence_required': 0.8
            },
            'volatility_increase': {
                'warning_threshold': 1.5,       # 50% increase in volatility
                'critical_threshold': 2.0,      # 100% increase in volatility
                'minimum_samples': 7,
                'confidence_required': 0.75
            },
            'finding_rate_increase': {
                'warning_threshold': 0.2,       # 20% increase in findings
                'critical_threshold': 0.5,      # 50% increase in findings
                'minimum_samples': 3,
                'confidence_required': 0.7
            },
            'statistical_significance': {
                'p_value_threshold': 0.05,       # 95% confidence
                'effect_size_threshold': 0.3,    # Medium effect size
                'minimum_samples': 5
            }
        }

    def _extract_quality_metrics(self, analysis_history: List[Dict[str, Any]]) -> pd.DataFrame:
        """Extract and structure quality metrics from analysis history."""
        if not analysis_history:
            return pd.DataFrame()

        metrics_data = []
        for entry in analysis_history:
            if not isinstance(entry, dict):
                continue

            # Extract timestamp
            timestamp = entry.get('timestamp') or entry.get('analysis_timestamp')
            if not timestamp:
                continue

            try:
                if isinstance(timestamp, str):
                    timestamp = pd.to_datetime(timestamp)
                elif isinstance(timestamp, (int, float)):
                    timestamp = pd.to_datetime(timestamp, unit='s')
                else:
                    continue
            except:
                continue

            # Extract quality metrics
            metrics_entry = {
                'timestamp': timestamp,
                'quality_score': entry.get('quality_score', np.nan),
                'readability_score': entry.get('readability_score', np.nan),
                'sentiment_score': entry.get('sentiment_score', np.nan),
                'consistency_score': entry.get('consistency_score', np.nan),
                'total_findings': entry.get('total_findings', 0),
                'critical_findings': entry.get('critical_findings', 0),
                'high_findings': entry.get('high_findings', 0),
                'medium_findings': entry.get('medium_findings', 0),
                'low_findings': entry.get('low_findings', 0),
                'semantic_similarity_score': entry.get('semantic_similarity_score', np.nan)
            }

            # Calculate derived metrics
            total_findings = metrics_entry['total_findings']
            if total_findings > 0:
                metrics_entry['finding_severity_ratio'] = (
                    metrics_entry['critical_findings'] * 3 +
                    metrics_entry['high_findings'] * 2 +
                    metrics_entry['medium_findings'] * 1
                ) / total_findings

            metrics_data.append(metrics_entry)

        if not metrics_data:
            return pd.DataFrame()

        df = pd.DataFrame(metrics_data)
        df = df.set_index('timestamp').sort_index()

        return df

    def _calculate_trend_analysis(self, quality_scores: pd.Series, window_days: int = 30) -> Dict[str, Any]:
        """Calculate trend analysis for quality scores."""
        if len(quality_scores) < 3:
            return {
                'slope': 0.0,
                'intercept': quality_scores.mean() if len(quality_scores) > 0 else 0.0,
                'r_squared': 0.0,
                'p_value': 1.0,
                'trend_direction': 'insufficient_data',
                'confidence': 0.0
            }

        # Prepare data for linear regression
        X = np.arange(len(quality_scores)).reshape(-1, 1)
        y = quality_scores.values

        # Fit linear regression
        model = LinearRegression()
        model.fit(X, y)

        # Calculate statistics
        slope = model.coef_[0]
        intercept = model.intercept_
        r_squared = model.score(X, y)

        # Calculate p-value for slope significance
        try:
            _, p_value = stats.linregress(X.flatten(), y)
        except:
            p_value = 1.0

        # Determine trend direction
        if slope > 0.001:
            trend_direction = 'improving'
        elif slope < -0.001:
            trend_direction = 'degrading'
        else:
            trend_direction = 'stable'

        # Calculate confidence based on r-squared and sample size
        sample_confidence = min(1.0, len(quality_scores) / 10)
        statistical_confidence = r_squared
        confidence = (sample_confidence + statistical_confidence) / 2

        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_squared': float(r_squared),
            'p_value': float(p_value),
            'trend_direction': trend_direction,
            'confidence': float(confidence)
        }

    def _calculate_volatility_analysis(self, quality_scores: pd.Series) -> Dict[str, Any]:
        """Calculate volatility analysis for quality scores."""
        if len(quality_scores) < 3:
            return {
                'current_volatility': 0.0,
                'baseline_volatility': 0.0,
                'volatility_change': 0.0,
                'volatility_ratio': 1.0
            }

        # Calculate current volatility (recent period)
        recent_scores = quality_scores.tail(min(10, len(quality_scores)))
        current_volatility = recent_scores.std()

        # Calculate baseline volatility (earlier period)
        baseline_scores = quality_scores.head(max(1, len(quality_scores) - 10))
        baseline_volatility = baseline_scores.std() if len(baseline_scores) > 1 else current_volatility

        # Calculate volatility change
        if baseline_volatility > 0:
            volatility_ratio = current_volatility / baseline_volatility
            volatility_change = current_volatility - baseline_volatility
        else:
            volatility_ratio = 1.0
            volatility_change = 0.0

        return {
            'current_volatility': float(current_volatility),
            'baseline_volatility': float(baseline_volatility),
            'volatility_change': float(volatility_change),
            'volatility_ratio': float(volatility_ratio)
        }

    def _detect_degradation_events(self, quality_scores: pd.Series, threshold: float = -0.05) -> List[Dict[str, Any]]:
        """Detect significant degradation events in quality scores."""
        if len(quality_scores) < 5:
            return []

        degradation_events = []
        scores_array = quality_scores.values

        # Calculate rolling means for smoothing
        window_size = min(5, len(scores_array))
        rolling_mean = pd.Series(scores_array).rolling(window=window_size, center=True).mean()

        # Find significant drops
        for i in range(window_size, len(scores_array)):
            current_score = scores_array[i]
            previous_score = rolling_mean.iloc[i - window_size] if i >= window_size else scores_array[i - 1]

            if not (np.isnan(current_score) or np.isnan(previous_score)):
                change = current_score - previous_score
                change_percent = change / previous_score if previous_score > 0 else 0

                if change_percent <= threshold:
                    degradation_events.append({
                        'timestamp': quality_scores.index[i],
                        'score_change': float(change),
                        'percent_change': float(change_percent),
                        'previous_score': float(previous_score),
                        'current_score': float(current_score),
                        'severity': 'critical' if change_percent <= threshold * 2 else 'warning'
                    })

        return degradation_events

    def _assess_degradation_severity(self, trend_analysis: Dict[str, Any],
                                   volatility_analysis: Dict[str, Any],
                                   degradation_events: List[Dict[str, Any]],
                                   finding_trend: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall degradation severity and generate recommendations."""

        severity_score = 0.0
        severity_factors = []

        # Trend-based severity
        trend_slope = trend_analysis.get('slope', 0)
        trend_confidence = trend_analysis.get('confidence', 0)

        if trend_slope < self.degradation_thresholds['trend_slope']['critical_threshold'] and trend_confidence > 0.7:
            severity_score += 0.4
            severity_factors.append({
                'factor': 'trend_slope',
                'severity': 'critical',
                'description': f'Steep negative trend (slope: {trend_slope:.4f})'
            })
        elif trend_slope < self.degradation_thresholds['trend_slope']['warning_threshold'] and trend_confidence > 0.6:
            severity_score += 0.2
            severity_factors.append({
                'factor': 'trend_slope',
                'severity': 'warning',
                'description': f'Moderate negative trend (slope: {trend_slope:.4f})'
            })

        # Volatility-based severity
        volatility_ratio = volatility_analysis.get('volatility_ratio', 1.0)

        if volatility_ratio >= self.degradation_thresholds['volatility_increase']['critical_threshold']:
            severity_score += 0.3
            severity_factors.append({
                'factor': 'volatility_increase',
                'severity': 'critical',
                'description': f'High volatility increase ({volatility_ratio:.1f}x baseline)'
            })
        elif volatility_ratio >= self.degradation_thresholds['volatility_increase']['warning_threshold']:
            severity_score += 0.15
            severity_factors.append({
                'factor': 'volatility_increase',
                'severity': 'warning',
                'description': f'Moderate volatility increase ({volatility_ratio:.1f}x baseline)'
            })

        # Finding rate severity
        finding_slope = finding_trend.get('slope', 0)
        if finding_slope > self.degradation_thresholds['finding_rate_increase']['critical_threshold']:
            severity_score += 0.2
            severity_factors.append({
                'factor': 'finding_rate_increase',
                'severity': 'critical',
                'description': f'Significant increase in findings (slope: {finding_slope:.2f})'
            })
        elif finding_slope > self.degradation_thresholds['finding_rate_increase']['warning_threshold']:
            severity_score += 0.1
            severity_factors.append({
                'factor': 'finding_rate_increase',
                'severity': 'warning',
                'description': f'Moderate increase in findings (slope: {finding_slope:.2f})'
            })

        # Degradation events severity
        if degradation_events:
            event_severity = len(degradation_events) * 0.05
            severity_score += min(0.2, event_severity)
            severity_factors.append({
                'factor': 'degradation_events',
                'severity': 'warning' if len(degradation_events) < 3 else 'critical',
                'description': f'{len(degradation_events)} significant degradation events detected'
            })

        # Determine overall severity level
        if severity_score >= 0.7:
            overall_severity = 'critical'
        elif severity_score >= 0.4:
            overall_severity = 'high'
        elif severity_score >= 0.2:
            overall_severity = 'medium'
        elif severity_score >= 0.1:
            overall_severity = 'low'
        else:
            overall_severity = 'minimal'

        return {
            'overall_severity': overall_severity,
            'severity_score': round(severity_score, 3),
            'severity_factors': severity_factors,
            'requires_attention': severity_score >= 0.2
        }

    def _generate_degradation_alerts(self, severity_assessment: Dict[str, Any],
                                   trend_analysis: Dict[str, Any],
                                   time_since_last_alert: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generate alerts based on degradation severity."""

        alerts = []
        overall_severity = severity_assessment['overall_severity']
        severity_score = severity_assessment['severity_score']

        # Base alert configuration
        alert_config = {
            'minimal': {'priority': 'low', 'message': 'Minor quality variations detected'},
            'low': {'priority': 'low', 'message': 'Quality degradation detected - monitor closely'},
            'medium': {'priority': 'medium', 'message': 'Moderate quality degradation - review recommended'},
            'high': {'priority': 'high', 'message': 'Significant quality degradation - action required'},
            'critical': {'priority': 'critical', 'message': 'Critical quality degradation - immediate intervention required'}
        }

        if overall_severity in alert_config:
            config = alert_config[overall_severity]

            alert = {
                'alert_type': 'quality_degradation',
                'severity': overall_severity,
                'priority': config['priority'],
                'message': config['message'],
                'severity_score': severity_score,
                'timestamp': time.time(),
                'recommendations': self._generate_alert_recommendations(overall_severity, severity_assessment)
            }

            # Add escalation logic based on time since last alert
            if time_since_last_alert:
                if time_since_last_alert < 7 * 24 * 3600:  # Less than 7 days
                    alert['escalation'] = 'Recent alert exists - monitor trend'
                elif time_since_last_alert > 30 * 24 * 3600:  # More than 30 days
                    alert['escalation'] = 'Long time since last alert - review monitoring'

            alerts.append(alert)

        return alerts

    def _generate_alert_recommendations(self, severity: str, severity_assessment: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on alert severity."""

        recommendations = []
        severity_factors = severity_assessment.get('severity_factors', [])

        if severity == 'critical':
            recommendations.append("🚨 IMMEDIATE ACTION REQUIRED: Schedule comprehensive quality review within 1 week")
            recommendations.append("Allocate dedicated resources for quality improvement")
            recommendations.append("Consider involving senior technical writers or subject matter experts")

        elif severity == 'high':
            recommendations.append("⚠️ HIGH PRIORITY: Schedule quality assessment within 2-4 weeks")
            recommendations.append("Review recent changes and their impact on quality")
            recommendations.append("Implement targeted quality improvement measures")

        elif severity == 'medium':
            recommendations.append("📊 MEDIUM PRIORITY: Include in next quarterly quality review cycle")
            recommendations.append("Monitor quality metrics closely for further degradation")

        elif severity == 'low':
            recommendations.append("👁️ LOW PRIORITY: Continue regular quality monitoring")
            recommendations.append("Note quality variations for trend analysis")

        # Factor-specific recommendations
        for factor in severity_factors:
            factor_type = factor['factor']
            factor_severity = factor['severity']

            if factor_type == 'trend_slope':
                recommendations.append("Analyze causes of quality decline and implement corrective measures")
            elif factor_type == 'volatility_increase':
                recommendations.append("Investigate sources of quality instability and stabilize processes")
            elif factor_type == 'finding_rate_increase':
                recommendations.append("Address increasing documentation issues proactively")
            elif factor_type == 'degradation_events':
                recommendations.append("Review recent changes that may have caused quality drops")

        return recommendations[:6]  # Limit to 6 recommendations

    async def detect_quality_degradation(
        self,
        document_id: str,
        analysis_history: List[Dict[str, Any]],
        baseline_period_days: int = 90,
        alert_threshold: float = 0.1
    ) -> Dict[str, Any]:
        """Detect quality degradation for a single document."""

        start_time = time.time()

        if not self._initialize_detector():
            return {
                'error': 'Quality degradation detection not available',
                'message': 'Required dependencies not installed or initialization failed'
            }

        try:
            # Extract quality metrics from history
            metrics_df = self._extract_quality_metrics(analysis_history)

            if metrics_df.empty or len(metrics_df) < 3:
                return {
                    'document_id': document_id,
                    'degradation_detected': False,
                    'severity_assessment': {'overall_severity': 'insufficient_data'},
                    'analysis_period_days': 0,
                    'data_points': len(metrics_df),
                    'alerts': [],
                    'processing_time': time.time() - start_time
                }

            # Analyze quality score trends
            quality_scores = metrics_df['quality_score'].dropna()
            trend_analysis = self._calculate_trend_analysis(quality_scores, baseline_period_days)

            # Analyze volatility
            volatility_analysis = self._calculate_volatility_analysis(quality_scores)

            # Detect degradation events
            degradation_events = self._detect_degradation_events(quality_scores, -alert_threshold)

            # Analyze finding trends
            finding_counts = metrics_df['total_findings'].dropna()
            finding_trend = self._calculate_trend_analysis(finding_counts, baseline_period_days) if len(finding_counts) >= 3 else {'slope': 0.0}

            # Assess overall degradation severity
            severity_assessment = self._assess_degradation_severity(
                trend_analysis, volatility_analysis, degradation_events, finding_trend
            )

            # Generate alerts if degradation detected
            alerts = []
            if severity_assessment['requires_attention']:
                alerts = self._generate_degradation_alerts(severity_assessment, trend_analysis)

            # Calculate analysis period
            if len(metrics_df) > 0:
                analysis_period = (metrics_df.index.max() - metrics_df.index.min()).days
            else:
                analysis_period = 0

            processing_time = time.time() - start_time

            return {
                'document_id': document_id,
                'degradation_detected': severity_assessment['requires_attention'],
                'severity_assessment': severity_assessment,
                'trend_analysis': trend_analysis,
                'volatility_analysis': volatility_analysis,
                'degradation_events': degradation_events,
                'finding_trend': finding_trend,
                'analysis_period_days': analysis_period,
                'data_points': len(metrics_df),
                'baseline_period_days': baseline_period_days,
                'alert_threshold': alert_threshold,
                'alerts': alerts,
                'processing_time': processing_time,
                'detection_timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"Quality degradation detection failed for document {document_id}: {e}")
            return {
                'error': 'Quality degradation detection failed',
                'message': str(e),
                'document_id': document_id,
                'processing_time': time.time() - start_time
            }

    async def monitor_portfolio_degradation(
        self,
        documents: List[Dict[str, Any]],
        baseline_period_days: int = 90,
        alert_threshold: float = 0.1
    ) -> Dict[str, Any]:
        """Monitor quality degradation across a portfolio of documents."""

        start_time = time.time()

        if not self._initialize_detector():
            return {
                'error': 'Quality degradation monitoring not available',
                'message': 'Required dependencies not installed or initialization failed'
            }

        try:
            if not documents:
                return {
                    'portfolio_summary': {},
                    'degradation_summary': {},
                    'processing_time': time.time() - start_time
                }

            # Monitor each document
            degradation_results = []
            severity_distribution = defaultdict(int)
            alerts_summary = []

            for doc in documents:
                doc_id = doc.get('document_id', f"doc_{len(degradation_results)}")
                analysis_history = doc.get('analysis_history', [])

                result = await self.detect_quality_degradation(
                    doc_id, analysis_history, baseline_period_days, alert_threshold
                )

                if 'error' not in result:
                    degradation_results.append(result)

                    # Track severity distribution
                    severity = result['severity_assessment']['overall_severity']
                    severity_distribution[severity] += 1

                    # Collect alerts
                    alerts_summary.extend(result.get('alerts', []))

            if not degradation_results:
                return {
                    'portfolio_summary': {'total_documents': len(documents), 'analyzed_documents': 0},
                    'degradation_summary': {},
                    'processing_time': time.time() - start_time
                }

            # Calculate portfolio summary
            total_documents = len(documents)
            analyzed_documents = len(degradation_results)

            degradation_detected = sum(1 for r in degradation_results if r['degradation_detected'])
            degradation_rate = degradation_detected / analyzed_documents if analyzed_documents > 0 else 0

            avg_severity_score = sum(
                r['severity_assessment']['severity_score'] for r in degradation_results
            ) / analyzed_documents if analyzed_documents > 0 else 0

            # Identify high-risk documents
            high_risk_documents = [
                r['document_id'] for r in degradation_results
                if r['severity_assessment']['overall_severity'] in ['critical', 'high']
            ]

            portfolio_summary = {
                'total_documents': total_documents,
                'analyzed_documents': analyzed_documents,
                'degradation_detected': degradation_detected,
                'degradation_rate': round(degradation_rate, 3),
                'average_severity_score': round(avg_severity_score, 3),
                'severity_distribution': dict(severity_distribution),
                'high_risk_documents': high_risk_documents,
                'baseline_period_days': baseline_period_days,
                'alert_threshold': alert_threshold
            }

            processing_time = time.time() - start_time

            return {
                'portfolio_summary': portfolio_summary,
                'degradation_results': degradation_results,
                'alerts_summary': alerts_summary,
                'processing_time': processing_time,
                'monitoring_timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"Portfolio degradation monitoring failed: {e}")
            return {
                'error': 'Portfolio degradation monitoring failed',
                'message': str(e),
                'processing_time': time.time() - start_time
            }

    def update_detection_thresholds(self, custom_thresholds: Dict[str, Dict[str, Any]]) -> bool:
        """Update quality degradation detection thresholds."""
        try:
            for threshold_name, config in custom_thresholds.items():
                if threshold_name in self.degradation_thresholds:
                    self.degradation_thresholds[threshold_name].update(config)
                else:
                    logger.warning(f"Unknown threshold type: {threshold_name}")
                    continue

            return True

        except Exception as e:
            logger.error(f"Failed to update detection thresholds: {e}")
            return False


# Global instance for reuse
quality_degradation_detector = QualityDegradationDetector()


async def detect_document_degradation(
    document_id: str,
    analysis_history: List[Dict[str, Any]],
    baseline_period_days: int = 90,
    alert_threshold: float = 0.1
) -> Dict[str, Any]:
    """Convenience function for document quality degradation detection.

    Args:
        document_id: ID of the document to analyze
        analysis_history: Historical analysis results
        baseline_period_days: Period for baseline comparison
        alert_threshold: Threshold for degradation alerts

    Returns:
        Quality degradation analysis results
    """
    return await quality_degradation_detector.detect_quality_degradation(
        document_id=document_id,
        analysis_history=analysis_history,
        baseline_period_days=baseline_period_days,
        alert_threshold=alert_threshold
    )


async def monitor_portfolio_degradation(
    documents: List[Dict[str, Any]],
    baseline_period_days: int = 90,
    alert_threshold: float = 0.1
) -> Dict[str, Any]:
    """Convenience function for portfolio quality degradation monitoring.

    Args:
        documents: List of document data dictionaries
        baseline_period_days: Period for baseline comparison
        alert_threshold: Threshold for degradation alerts

    Returns:
        Portfolio degradation monitoring results
    """
    return await quality_degradation_detector.monitor_portfolio_degradation(
        documents=documents,
        baseline_period_days=baseline_period_days,
        alert_threshold=alert_threshold
    )
