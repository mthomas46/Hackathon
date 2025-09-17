"""Maintenance Forecasting module for Analysis Service.

Predicts when documentation will need updates based on risk assessment,
historical patterns, usage data, and business requirements.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json

try:
    import pandas as pd
    import numpy as np
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.model_selection import train_test_split, TimeSeriesSplit
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from scipy import stats
    import warnings
    warnings.filterwarnings('ignore')
    MAINTENANCE_FORECASTING_AVAILABLE = True
except ImportError:
    MAINTENANCE_FORECASTING_AVAILABLE = False
    pd = None
    np = None
    LinearRegression = None
    Ridge = None
    RandomForestRegressor = None
    GradientBoostingRegressor = None
    StandardScaler = None
    MinMaxScaler = None
    train_test_split = None
    TimeSeriesSplit = None
    mean_absolute_error = None
    mean_squared_error = None
    r2_score = None
    stats = None

from services.shared.core.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes

logger = logging.getLogger(__name__)


class MaintenanceForecaster:
    """Forecasts when documentation will need maintenance and updates."""

    def __init__(self):
        """Initialize the maintenance forecaster."""
        self.initialized = False
        self.maintenance_factors = self._get_default_maintenance_factors()
        self._initialize_forecaster()

    def _initialize_forecaster(self) -> bool:
        """Initialize the maintenance forecasting components."""
        if not MAINTENANCE_FORECASTING_AVAILABLE:
            logger.warning("Maintenance forecasting dependencies not available")
            return False

        self.scaler = StandardScaler()
        self.initialized = True
        return True

    def _get_default_maintenance_factors(self) -> Dict[str, Dict[str, Any]]:
        """Define default maintenance forecasting factors."""
        return {
            'risk_score': {
                'weight': 0.25,
                'description': 'Current risk assessment score',
                'forecast_impact': 'inverse_exponential',  # Higher risk = sooner maintenance
                'base_interval_days': 365,
                'urgency_multiplier': 0.3
            },
            'document_age': {
                'weight': 0.20,
                'description': 'Time since last major update',
                'forecast_impact': 'linear_increase',
                'base_interval_days': 180,
                'urgency_multiplier': 0.5
            },
            'usage_frequency': {
                'weight': 0.15,
                'description': 'How often documentation is accessed',
                'forecast_impact': 'inverse_linear',
                'base_interval_days': 90,
                'urgency_multiplier': 0.2
            },
            'quality_trend': {
                'weight': 0.15,
                'description': 'Rate of quality score change',
                'forecast_impact': 'exponential_decline',
                'base_interval_days': 120,
                'urgency_multiplier': 0.4
            },
            'business_criticality': {
                'weight': 0.10,
                'description': 'Business impact of documentation accuracy',
                'forecast_impact': 'categorical',
                'categories': {'low': 180, 'medium': 120, 'high': 60, 'critical': 30},
                'base_interval_days': 90,
                'urgency_multiplier': 0.6
            },
            'technology_changes': {
                'weight': 0.08,
                'description': 'Related technology or dependency changes',
                'forecast_impact': 'event_based',
                'base_interval_days': 60,
                'urgency_multiplier': 0.7
            },
            'regulatory_requirements': {
                'weight': 0.05,
                'description': 'Regulatory or compliance update requirements',
                'forecast_impact': 'fixed_schedule',
                'base_interval_days': 365,
                'urgency_multiplier': 0.8
            },
            'team_capacity': {
                'weight': 0.02,
                'description': 'Available team capacity for maintenance',
                'forecast_impact': 'capacity_based',
                'base_interval_days': 30,
                'urgency_multiplier': 0.1
            }
        }

    def _calculate_maintenance_urgency(self, factor_name: str, value: Any, factor_config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate maintenance urgency for a specific factor."""
        base_interval = factor_config.get('base_interval_days', 90)
        urgency_multiplier = factor_config.get('urgency_multiplier', 0.5)
        forecast_impact = factor_config.get('forecast_impact', 'linear_increase')

        if value is None:
            return {
                'urgency_score': 0.5,
                'predicted_days': base_interval,
                'confidence': 0.5,
                'recommendation': 'Insufficient data for accurate forecasting'
            }

        if forecast_impact == 'inverse_exponential':
            # Higher values = more urgent (sooner maintenance)
            urgency_score = min(1.0, max(0.0, value * urgency_multiplier))
            days_multiplier = max(0.1, 1.0 - (value * urgency_multiplier))
            predicted_days = int(base_interval * days_multiplier)

        elif forecast_impact == 'linear_increase':
            # Linear relationship with value
            urgency_score = min(1.0, max(0.0, value / 365 * urgency_multiplier))
            days_multiplier = max(0.2, 1.0 - (value / 730))  # Reduce interval as age increases
            predicted_days = int(base_interval * days_multiplier)

        elif forecast_impact == 'inverse_linear':
            # Higher values = less urgent (later maintenance)
            urgency_score = min(1.0, max(0.0, (100 - min(value, 100)) / 100 * urgency_multiplier))
            days_multiplier = 1.0 + (value / 200)  # Increase interval with higher usage
            predicted_days = int(base_interval * days_multiplier)

        elif forecast_impact == 'exponential_decline':
            # Negative trend = more urgent
            if value < -0.01:  # Declining quality
                urgency_score = min(1.0, abs(value) * 100 * urgency_multiplier)
                days_multiplier = max(0.1, 1.0 - abs(value) * 50)
            else:
                urgency_score = 0.2
                days_multiplier = 1.2
            predicted_days = int(base_interval * days_multiplier)

        elif forecast_impact == 'categorical':
            categories = factor_config.get('categories', {})
            if isinstance(value, str):
                predicted_days = categories.get(value.lower(), base_interval)
                urgency_score = min(1.0, (base_interval - predicted_days) / base_interval * urgency_multiplier)
            else:
                predicted_days = base_interval
                urgency_score = 0.5

        else:
            # Default linear approach
            urgency_score = min(1.0, max(0.0, float(value) * urgency_multiplier))
            predicted_days = base_interval

        # Ensure reasonable bounds
        predicted_days = max(7, min(730, predicted_days))  # 1 week to 2 years

        return {
            'urgency_score': round(urgency_score, 3),
            'predicted_days': predicted_days,
            'confidence': 0.8,  # Simplified confidence
            'recommendation': self._generate_factor_recommendation(factor_name, urgency_score, predicted_days)
        }

    def _generate_factor_recommendation(self, factor_name: str, urgency_score: float, predicted_days: int) -> str:
        """Generate recommendation based on factor analysis."""
        if urgency_score >= 0.8:
            urgency_level = "immediate"
        elif urgency_score >= 0.6:
            urgency_level = "high priority"
        elif urgency_score >= 0.4:
            urgency_level = "medium priority"
        elif urgency_score >= 0.2:
            urgency_level = "low priority"
        else:
            urgency_level = "minimal priority"

        if factor_name == 'risk_score':
            return f"{urgency_level.capitalize()} maintenance recommended due to high risk score"
        elif factor_name == 'document_age':
            return f"{urgency_level.capitalize()} update needed - document is {predicted_days} days overdue"
        elif factor_name == 'usage_frequency':
            if urgency_score < 0.3:
                return "Low priority - document has high usage, maintain current schedule"
            else:
                return f"{urgency_level.capitalize()} review recommended despite high usage"
        elif factor_name == 'quality_trend':
            if urgency_score > 0.6:
                return f"{urgency_level.capitalize()} - quality is declining, immediate intervention needed"
            else:
                return "Quality stable - maintain regular monitoring schedule"
        elif factor_name == 'business_criticality':
            return f"{urgency_level.capitalize()} maintenance for business-critical documentation"
        else:
            return f"{urgency_level.capitalize()} maintenance recommended"

    def _forecast_maintenance_schedule(self, document_data: Dict[str, Any], analysis_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Forecast maintenance schedule based on multiple factors."""
        factor_forecasts = {}
        total_weight = 0
        weighted_days = 0
        max_urgency = 0
        urgent_factors = []

        for factor_name, factor_config in self.maintenance_factors.items():
            value = document_data.get(factor_name)

            # Extract or estimate factor values
            if factor_name == 'risk_score':
                if not value and analysis_history:
                    # Use latest risk assessment if available
                    latest_analysis = analysis_history[-1] if analysis_history else {}
                    value = latest_analysis.get('overall_risk', {}).get('overall_score', 0.5)
                elif not value:
                    value = 0.5  # Default moderate risk

            elif factor_name == 'document_age':
                last_modified = document_data.get('last_modified')
                if last_modified and isinstance(last_modified, str):
                    try:
                        last_mod_date = pd.to_datetime(last_modified)
                        value = (pd.Timestamp.now() - last_mod_date).days
                    except:
                        value = 180
                elif not value:
                    value = 180

            elif factor_name == 'usage_frequency':
                if not value:
                    # Estimate based on document type and access patterns
                    doc_type = document_data.get('document_type', '').lower()
                    if 'api' in doc_type:
                        value = 80
                    elif 'tutorial' in doc_type:
                        value = 60
                    elif 'reference' in doc_type:
                        value = 40
                    else:
                        value = 20

            elif factor_name == 'quality_trend':
                if not value and analysis_history and len(analysis_history) >= 3:
                    # Calculate quality trend from history
                    scores = []
                    for entry in analysis_history[-10:]:  # Last 10 entries
                        if 'quality_score' in entry:
                            scores.append(entry['quality_score'])

                    if len(scores) >= 3:
                        X = np.arange(len(scores)).reshape(-1, 1)
                        y = np.array(scores)
                        model = LinearRegression()
                        model.fit(X, y)
                        value = model.coef_[0]  # Trend slope
                    else:
                        value = 0.0
                elif not value:
                    value = 0.0

            elif factor_name == 'business_criticality':
                if not value:
                    # Estimate based on content and metadata
                    stakeholder_impact = document_data.get('stakeholder_impact', 'medium')
                    content = document_data.get('content', '').lower()

                    if 'security' in content or 'compliance' in content:
                        value = 'high'
                    elif stakeholder_impact in ['high', 'critical']:
                        value = stakeholder_impact
                    else:
                        value = 'medium'

            # Calculate forecast for this factor
            forecast = self._calculate_maintenance_urgency(factor_name, value, factor_config)
            factor_forecasts[factor_name] = {
                'value': value,
                'forecast': forecast,
                'weight': factor_config['weight'],
                'description': factor_config['description']
            }

            # Aggregate for overall forecast
            weight = factor_config['weight']
            total_weight += weight
            weighted_days += forecast['predicted_days'] * weight
            max_urgency = max(max_urgency, forecast['urgency_score'])

            if forecast['urgency_score'] >= 0.6:
                urgent_factors.append({
                    'factor': factor_name,
                    'urgency': forecast['urgency_score'],
                    'days': forecast['predicted_days'],
                    'recommendation': forecast['recommendation']
                })

        # Calculate overall forecast
        if total_weight > 0:
            overall_days = int(weighted_days / total_weight)
            overall_urgency = min(1.0, max_urgency)
        else:
            overall_days = 90
            overall_urgency = 0.5

        # Determine maintenance priority level
        if overall_urgency >= 0.8:
            priority_level = 'critical'
        elif overall_urgency >= 0.6:
            priority_level = 'high'
        elif overall_urgency >= 0.4:
            priority_level = 'medium'
        elif overall_urgency >= 0.2:
            priority_level = 'low'
        else:
            priority_level = 'minimal'

        # Calculate confidence based on data completeness
        data_completeness = sum(1 for f in factor_forecasts.values() if f['value'] is not None) / len(factor_forecasts)
        confidence = min(0.95, 0.5 + (data_completeness * 0.4))

        # Generate maintenance schedule
        maintenance_schedule = self._generate_maintenance_schedule(overall_days, priority_level, urgent_factors)

        return {
            'overall_forecast': {
                'predicted_days': overall_days,
                'predicted_date': (datetime.now() + timedelta(days=overall_days)).isoformat(),
                'urgency_score': round(overall_urgency, 3),
                'priority_level': priority_level,
                'confidence': round(confidence, 3),
                'data_completeness': round(data_completeness, 3)
            },
            'factor_forecasts': factor_forecasts,
            'urgent_factors': urgent_factors,
            'maintenance_schedule': maintenance_schedule
        }

    def _generate_maintenance_schedule(self, predicted_days: int, priority_level: str, urgent_factors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a detailed maintenance schedule."""
        now = datetime.now()
        predicted_date = now + timedelta(days=predicted_days)

        schedule = {
            'next_maintenance_date': predicted_date.isoformat(),
            'next_maintenance_days': predicted_days,
            'priority_level': priority_level,
            'maintenance_type': self._determine_maintenance_type(priority_level, urgent_factors),
            'milestones': []
        }

        # Generate milestones based on priority
        if priority_level in ['critical', 'high']:
            # Immediate action required
            schedule['milestones'] = [
                {
                    'date': (now + timedelta(days=7)).isoformat(),
                    'type': 'assessment',
                    'description': 'Complete detailed assessment and planning'
                },
                {
                    'date': (now + timedelta(days=14)).isoformat(),
                    'type': 'review',
                    'description': 'Begin content review and updates'
                },
                {
                    'date': predicted_date.isoformat(),
                    'type': 'completion',
                    'description': 'Complete major maintenance and validation'
                }
            ]
        elif priority_level == 'medium':
            schedule['milestones'] = [
                {
                    'date': (now + timedelta(days=30)).isoformat(),
                    'type': 'planning',
                    'description': 'Plan maintenance activities'
                },
                {
                    'date': predicted_date.isoformat(),
                    'type': 'maintenance',
                    'description': 'Perform scheduled maintenance'
                }
            ]
        else:
            schedule['milestones'] = [
                {
                    'date': predicted_date.isoformat(),
                    'type': 'routine_check',
                    'description': 'Perform routine quality check and minor updates'
                }
            ]

        return schedule

    def _determine_maintenance_type(self, priority_level: str, urgent_factors: List[Dict[str, Any]]) -> str:
        """Determine the type of maintenance required."""
        if priority_level == 'critical':
            return 'major_overhaul'
        elif priority_level == 'high':
            # Check what factors are driving urgency
            risk_drivers = [f['factor'] for f in urgent_factors]
            if 'risk_score' in risk_drivers:
                return 'risk_mitigation'
            elif 'document_age' in risk_drivers:
                return 'content_refresh'
            else:
                return 'comprehensive_update'
        elif priority_level == 'medium':
            return 'targeted_updates'
        else:
            return 'routine_maintenance'

    def _generate_maintenance_recommendations(self, forecast_data: Dict[str, Any]) -> List[str]:
        """Generate actionable maintenance recommendations."""
        recommendations = []
        overall_forecast = forecast_data['overall_forecast']
        urgent_factors = forecast_data['urgent_factors']

        priority_level = overall_forecast['priority_level']
        predicted_days = overall_forecast['predicted_days']

        if priority_level == 'critical':
            recommendations.append("🚨 CRITICAL: Immediate maintenance required - schedule within 1 week")
            recommendations.append("Allocate dedicated resources for comprehensive documentation overhaul")
            recommendations.append("Consider involving multiple stakeholders for critical review")

        elif priority_level == 'high':
            recommendations.append("⚠️ HIGH PRIORITY: Schedule maintenance within 2-4 weeks")
            recommendations.append("Focus on high-risk areas identified in assessment")
            recommendations.append("Prepare rollback plan for significant content changes")

        elif priority_level == 'medium':
            recommendations.append("📅 MEDIUM PRIORITY: Plan maintenance for next quarterly cycle")
            recommendations.append("Monitor closely and escalate if risk factors increase")

        else:
            recommendations.append("✅ LOW PRIORITY: Include in regular maintenance schedule")
            recommendations.append("Monitor for any changes in risk factors")

        # Factor-specific recommendations
        for factor in urgent_factors[:3]:  # Top 3 urgent factors
            factor_name = factor['factor']
            if factor_name == 'risk_score':
                recommendations.append("Address high-risk issues identified in recent assessments")
            elif factor_name == 'document_age':
                recommendations.append("Review content relevance and update outdated information")
            elif factor_name == 'quality_trend':
                recommendations.append("Investigate and correct causes of quality degradation")

        # Add timeline recommendations
        if predicted_days <= 30:
            recommendations.append("Short timeline - consider breaking maintenance into phases")
        elif predicted_days <= 90:
            recommendations.append("Moderate timeline - plan resources accordingly")
        else:
            recommendations.append("Long timeline - monitor risk factors and adjust as needed")

        return recommendations[:8]  # Limit to 8 recommendations

    async def forecast_document_maintenance(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        analysis_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Forecast maintenance needs for a single document."""

        start_time = time.time()

        if not self._initialize_forecaster():
            return {
                'error': 'Maintenance forecasting not available',
                'message': 'Required dependencies not installed or initialization failed'
            }

        try:
            # Generate maintenance forecast
            forecast_data = self._forecast_maintenance_schedule(document_data, analysis_history)

            # Generate recommendations
            recommendations = self._generate_maintenance_recommendations(forecast_data)

            processing_time = time.time() - start_time

            return {
                'document_id': document_id,
                'forecast_data': forecast_data,
                'recommendations': recommendations,
                'processing_time': processing_time,
                'forecast_timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"Maintenance forecasting failed for document {document_id}: {e}")
            return {
                'error': 'Maintenance forecasting failed',
                'message': str(e),
                'document_id': document_id,
                'processing_time': time.time() - start_time
            }

    async def forecast_portfolio_maintenance(
        self,
        documents: List[Dict[str, Any]],
        group_by: str = 'document_type'
    ) -> Dict[str, Any]:
        """Forecast maintenance needs across a portfolio of documents."""

        start_time = time.time()

        if not self._initialize_forecaster():
            return {
                'error': 'Maintenance forecasting not available',
                'message': 'Required dependencies not installed or initialization failed'
            }

        try:
            if not documents:
                return {
                    'portfolio_summary': {},
                    'maintenance_schedule': [],
                    'processing_time': time.time() - start_time
                }

            # Forecast maintenance for each document
            document_forecasts = []
            maintenance_by_date = defaultdict(list)
            priority_distribution = Counter()
            urgency_scores = []

            for doc in documents:
                doc_id = doc.get('document_id', f"doc_{len(document_forecasts)}")
                forecast = await self.forecast_document_maintenance(doc_id, doc, doc.get('analysis_history'))

                if 'error' not in forecast:
                    document_forecasts.append(forecast)
                    forecast_data = forecast['forecast_data']['overall_forecast']

                    # Group by maintenance date (rounded to week)
                    maint_date = forecast_data['predicted_date'][:10]  # YYYY-MM-DD
                    maintenance_by_date[maint_date].append(forecast)

                    # Track priority distribution
                    priority_distribution[forecast_data['priority_level']] += 1

                    # Collect urgency scores
                    urgency_scores.append(forecast_data['urgency_score'])

            if not document_forecasts:
                return {
                    'portfolio_summary': {'total_documents': len(documents), 'forecasted_documents': 0},
                    'maintenance_schedule': [],
                    'processing_time': time.time() - start_time
                }

            # Calculate portfolio summary
            avg_urgency = sum(urgency_scores) / len(urgency_scores) if urgency_scores else 0
            maintenance_schedule = []

            # Sort dates and create maintenance schedule
            sorted_dates = sorted(maintenance_by_date.keys())
            for maint_date in sorted_dates[:12]:  # Next 12 maintenance dates
                docs = maintenance_by_date[maint_date]
                priorities = Counter()
                total_docs = len(docs)

                for doc in docs:
                    forecast_data = doc['forecast_data']['overall_forecast']
                    priorities[forecast_data['priority_level']] += 1

                maintenance_schedule.append({
                    'date': maint_date,
                    'total_documents': total_docs,
                    'priority_breakdown': dict(priorities),
                    'documents': [doc['document_id'] for doc in docs]
                })

            portfolio_summary = {
                'total_documents': len(documents),
                'forecasted_documents': len(document_forecasts),
                'average_urgency': round(avg_urgency, 3),
                'priority_distribution': dict(priority_distribution),
                'maintenance_dates': len(sorted_dates),
                'next_maintenance_date': sorted_dates[0] if sorted_dates else None
            }

            processing_time = time.time() - start_time

            return {
                'portfolio_summary': portfolio_summary,
                'maintenance_schedule': maintenance_schedule,
                'document_forecasts': document_forecasts,
                'processing_time': processing_time,
                'forecast_timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"Portfolio maintenance forecasting failed: {e}")
            return {
                'error': 'Portfolio maintenance forecasting failed',
                'message': str(e),
                'processing_time': time.time() - start_time
            }

    def update_maintenance_factors(self, custom_factors: Dict[str, Dict[str, Any]]) -> bool:
        """Update maintenance forecasting factors configuration."""
        try:
            for factor_name, config in custom_factors.items():
                if factor_name in self.maintenance_factors:
                    self.maintenance_factors[factor_name].update(config)
                else:
                    # Validate new factor configuration
                    required_keys = ['weight', 'description', 'forecast_impact']
                    if all(key in config for key in required_keys):
                        self.maintenance_factors[factor_name] = config
                    else:
                        logger.warning(f"Invalid configuration for maintenance factor {factor_name}")
                        continue

            # Re-normalize weights to ensure they sum to 1.0
            total_weight = sum(factor['weight'] for factor in self.maintenance_factors.values())
            if total_weight > 0:
                for factor in self.maintenance_factors.values():
                    factor['weight'] = factor['weight'] / total_weight

            return True

        except Exception as e:
            logger.error(f"Failed to update maintenance factors: {e}")
            return False


# Global instance for reuse
maintenance_forecaster = MaintenanceForecaster()


async def forecast_document_maintenance(
    document_id: str,
    document_data: Dict[str, Any],
    analysis_history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Convenience function for document maintenance forecasting.

    Args:
        document_id: ID of the document to forecast
        document_data: Document metadata and content
        analysis_history: Historical analysis results

    Returns:
        Maintenance forecast results
    """
    return await maintenance_forecaster.forecast_document_maintenance(document_id, document_data, analysis_history)


async def forecast_portfolio_maintenance(
    documents: List[Dict[str, Any]],
    group_by: str = 'document_type'
) -> Dict[str, Any]:
    """Convenience function for portfolio maintenance forecasting.

    Args:
        documents: List of document data dictionaries
        group_by: Field to group results by

    Returns:
        Portfolio maintenance forecast results
    """
    return await maintenance_forecaster.forecast_portfolio_maintenance(documents, group_by)
