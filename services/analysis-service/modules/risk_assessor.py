"""Risk Assessment module for Analysis Service.

Provides comprehensive risk assessment for documentation, identifying areas most
at risk for documentation drift, quality degradation, and maintenance issues.
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
    from sklearn.preprocessing import MinMaxScaler, StandardScaler
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error
    import warnings
    warnings.filterwarnings('ignore')
    RISK_ASSESSMENT_AVAILABLE = True
except ImportError:
    RISK_ASSESSMENT_AVAILABLE = False
    pd = None
    np = None
    MinMaxScaler = None
    StandardScaler = None
    RandomForestRegressor = None
    GradientBoostingRegressor = None
    train_test_split = None
    mean_absolute_error = None

from services.shared.core.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes

logger = logging.getLogger(__name__)


class RiskAssessor:
    """Assesses risk factors for documentation quality and maintenance."""

    def __init__(self):
        """Initialize the risk assessor."""
        self.initialized = False
        self.risk_factors = self._get_default_risk_factors()
        self._initialize_assessor()

    def _initialize_assessor(self) -> bool:
        """Initialize the risk assessment components."""
        if not RISK_ASSESSMENT_AVAILABLE:
            logger.warning("Risk assessment dependencies not available")
            return False

        self.initialized = True
        self.scaler = StandardScaler()
        return True

    def _get_default_risk_factors(self) -> Dict[str, Dict[str, Any]]:
        """Define default risk factors and their weights."""
        return {
            'document_age': {
                'weight': 0.15,
                'description': 'Age of document in days',
                'risk_function': 'linear_increase',
                'thresholds': {'low': 30, 'medium': 180, 'high': 365}
            },
            'complexity_score': {
                'weight': 0.20,
                'description': 'Technical complexity and depth',
                'risk_function': 'linear_increase',
                'thresholds': {'low': 0.3, 'medium': 0.6, 'high': 0.8}
            },
            'change_frequency': {
                'weight': 0.12,
                'description': 'How often document has been modified',
                'risk_function': 'linear_increase',
                'thresholds': {'low': 1, 'medium': 5, 'high': 15}
            },
            'quality_score': {
                'weight': 0.18,
                'description': 'Current documentation quality score',
                'risk_function': 'inverse_linear',
                'thresholds': {'low': 0.8, 'medium': 0.6, 'high': 0.4}
            },
            'trend_decline': {
                'weight': 0.10,
                'description': 'Rate of quality decline over time',
                'risk_function': 'linear_increase',
                'thresholds': {'low': 0.01, 'medium': 0.05, 'high': 0.1}
            },
            'finding_density': {
                'weight': 0.08,
                'description': 'Number of issues per page/content unit',
                'risk_function': 'linear_increase',
                'thresholds': {'low': 0.5, 'medium': 1.5, 'high': 3.0}
            },
            'stakeholder_impact': {
                'weight': 0.12,
                'description': 'Business impact if documentation is incorrect',
                'risk_function': 'categorical',
                'categories': {'low': 1, 'medium': 2, 'high': 3, 'critical': 4},
                'thresholds': {'low': 1, 'medium': 2, 'high': 3}
            },
            'usage_frequency': {
                'weight': 0.05,
                'description': 'How frequently the documentation is accessed',
                'risk_function': 'inverse_linear',
                'thresholds': {'low': 100, 'medium': 25, 'high': 5}
            }
        }

    def _calculate_risk_factor_score(self, factor_name: str, value: Any, factor_config: Dict[str, Any]) -> float:
        """Calculate risk score for a specific factor."""
        if value is None:
            return 0.5  # Neutral score for missing data

        risk_function = factor_config.get('risk_function', 'linear_increase')
        thresholds = factor_config.get('thresholds', {})

        if risk_function == 'linear_increase':
            # Higher values = higher risk
            low = thresholds.get('low', 0)
            medium = thresholds.get('medium', 50)
            high = thresholds.get('high', 100)

            if value <= low:
                return 0.2
            elif value <= medium:
                return 0.5
            elif value <= high:
                return 0.8
            else:
                return 1.0

        elif risk_function == 'inverse_linear':
            # Lower values = higher risk
            low = thresholds.get('low', 0)
            medium = thresholds.get('medium', 50)
            high = thresholds.get('high', 100)

            if value >= low:
                return 0.2
            elif value >= medium:
                return 0.5
            elif value >= high:
                return 0.8
            else:
                return 1.0

        elif risk_function == 'categorical':
            categories = factor_config.get('categories', {})
            if isinstance(value, str):
                return categories.get(value.lower(), 2) / 4.0
            else:
                return min(float(value) / 4.0, 1.0)

        return 0.5  # Default neutral score

    def _assess_individual_risks(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess individual risk factors for a document."""
        risk_scores = {}

        for factor_name, factor_config in self.risk_factors.items():
            value = document_data.get(factor_name)

            if factor_name == 'document_age':
                # Calculate age if not provided
                last_modified = document_data.get('last_modified')
                if last_modified and isinstance(last_modified, str):
                    try:
                        last_mod_date = pd.to_datetime(last_modified)
                        value = (pd.Timestamp.now() - last_mod_date).days
                    except:
                        value = 180  # Default to 6 months
                elif not value:
                    value = 180

            elif factor_name == 'complexity_score':
                # Estimate complexity if not provided
                if not value:
                    # Simple heuristic based on content length and technical terms
                    content = document_data.get('content', '')
                    technical_terms = ['api', 'database', 'algorithm', 'configuration',
                                     'deployment', 'authentication', 'authorization']
                    term_count = sum(1 for term in technical_terms if term.lower() in content.lower())
                    value = min(1.0, len(content) / 10000 + term_count / 10)

            elif factor_name == 'change_frequency':
                # Use modification history if available
                if not value:
                    modifications = document_data.get('modification_history', [])
                    if modifications:
                        days_span = 365  # Last year
                        value = len(modifications) / (days_span / 30)  # Changes per month
                    else:
                        value = 1  # Default monthly change

            elif factor_name == 'quality_score':
                if not value:
                    # Use current analysis if available
                    analysis_results = document_data.get('recent_analysis', [])
                    if analysis_results:
                        latest = analysis_results[-1]
                        value = latest.get('quality_score', 0.7)
                    else:
                        value = 0.7

            elif factor_name == 'trend_decline':
                # Calculate from historical data
                if not value:
                    analysis_results = document_data.get('analysis_history', [])
                    if len(analysis_results) >= 3:
                        scores = [r.get('quality_score', 0.7) for r in analysis_results[-10:]]
                        if scores:
                            from sklearn.linear_model import LinearRegression
                            X = np.arange(len(scores)).reshape(-1, 1)
                            y = np.array(scores)
                            model = LinearRegression()
                            model.fit(X, y)
                            value = max(0, -model.coef_[0])  # Only positive decline rates
                    else:
                        value = 0.01  # Small default decline

            elif factor_name == 'finding_density':
                if not value:
                    analysis_results = document_data.get('recent_analysis', [])
                    if analysis_results:
                        latest = analysis_results[-1]
                        findings = latest.get('total_findings', 0)
                        content_length = len(document_data.get('content', ''))
                        if content_length > 0:
                            value = findings / (content_length / 1000)  # Findings per 1000 chars
                        else:
                            value = 0.5

            elif factor_name == 'stakeholder_impact':
                if not value:
                    # Estimate based on document type and content
                    doc_type = document_data.get('document_type', '').lower()
                    content = document_data.get('content', '').lower()

                    if 'api' in doc_type or 'security' in content:
                        value = 'high'
                    elif 'user' in doc_type or 'guide' in content:
                        value = 'medium'
                    else:
                        value = 'low'

            elif factor_name == 'usage_frequency':
                if not value:
                    # Estimate based on access patterns or document type
                    doc_type = document_data.get('document_type', '').lower()
                    if 'api' in doc_type or 'reference' in doc_type:
                        value = 50  # Higher usage
                    elif 'tutorial' in doc_type or 'getting-started' in doc_type:
                        value = 20  # Moderate usage
                    else:
                        value = 5  # Lower usage

            # Calculate risk score for this factor
            risk_score = self._calculate_risk_factor_score(factor_name, value, factor_config)
            risk_scores[factor_name] = {
                'value': value,
                'risk_score': risk_score,
                'weight': factor_config['weight'],
                'description': factor_config['description']
            }

        return risk_scores

    def _calculate_overall_risk_score(self, risk_scores: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall risk score and risk level."""
        weighted_sum = 0
        total_weight = 0

        for factor_name, factor_data in risk_scores.items():
            weight = factor_data['weight']
            risk_score = factor_data['risk_score']
            weighted_sum += weight * risk_score
            total_weight += weight

        if total_weight == 0:
            overall_score = 0.5
        else:
            overall_score = weighted_sum / total_weight

        # Determine risk level
        if overall_score >= 0.8:
            risk_level = 'critical'
        elif overall_score >= 0.6:
            risk_level = 'high'
        elif overall_score >= 0.4:
            risk_level = 'medium'
        elif overall_score >= 0.2:
            risk_level = 'low'
        else:
            risk_level = 'minimal'

        return {
            'overall_score': round(overall_score, 3),
            'risk_level': risk_level,
            'weighted_sum': round(weighted_sum, 3),
            'total_weight': round(total_weight, 3)
        }

    def _generate_risk_recommendations(self, risk_scores: Dict[str, Any], overall_risk: Dict[str, Any]) -> List[str]:
        """Generate risk mitigation recommendations."""
        recommendations = []

        risk_level = overall_risk['risk_level']

        if risk_level in ['critical', 'high']:
            recommendations.append("Immediate review and update required - high risk of documentation drift")

        # Factor-specific recommendations
        for factor_name, factor_data in risk_scores.items():
            risk_score = factor_data['risk_score']
            value = factor_data['value']

            if factor_name == 'document_age' and risk_score > 0.7:
                recommendations.append(".1f")

            elif factor_name == 'quality_score' and risk_score > 0.7:
                recommendations.append(".2f")

            elif factor_name == 'complexity_score' and risk_score > 0.7:
                recommendations.append("High complexity detected - consider breaking into smaller, focused documents")

            elif factor_name == 'change_frequency' and risk_score > 0.7:
                recommendations.append("High change frequency - implement automated quality checks for updates")

            elif factor_name == 'trend_decline' and risk_score > 0.7:
                recommendations.append(".3f")

            elif factor_name == 'finding_density' and risk_score > 0.7:
                recommendations.append("High issue density - prioritize fixing existing problems before adding new content")

            elif factor_name == 'stakeholder_impact' and risk_score > 0.7:
                recommendations.append("High stakeholder impact - establish stricter review processes and quality gates")

        # General recommendations based on overall risk
        if len(recommendations) == 0:
            if risk_level == 'low':
                recommendations.append("Risk level is low - maintain regular monitoring schedule")
            elif risk_level == 'medium':
                recommendations.append("Medium risk - consider quarterly reviews and quality checks")
            else:
                recommendations.append("Perform comprehensive risk assessment and mitigation planning")

        return recommendations[:5]  # Limit to top 5 recommendations

    def _identify_risk_drivers(self, risk_scores: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify the primary drivers of risk."""
        # Sort factors by their weighted risk contribution
        factor_contributions = []
        for factor_name, factor_data in risk_scores.items():
            contribution = factor_data['weight'] * factor_data['risk_score']
            factor_contributions.append({
                'factor': factor_name,
                'contribution': round(contribution, 3),
                'risk_score': factor_data['risk_score'],
                'weight': factor_data['weight'],
                'description': factor_data['description']
            })

        # Sort by contribution (highest first)
        factor_contributions.sort(key=lambda x: x['contribution'], reverse=True)

        return factor_contributions[:5]  # Top 5 risk drivers

    async def assess_document_risk(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        analysis_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Assess risk for a single document."""

        start_time = time.time()

        if not self._initialize_assessor():
            return {
                'error': 'Risk assessment not available',
                'message': 'Required dependencies not installed or initialization failed'
            }

        try:
            # Prepare document data for assessment
            assessment_data = document_data.copy()
            if analysis_history:
                assessment_data['analysis_history'] = analysis_history
                assessment_data['recent_analysis'] = analysis_history[-5:] if analysis_history else []

            # Assess individual risk factors
            risk_scores = self._assess_individual_risks(assessment_data)

            # Calculate overall risk
            overall_risk = self._calculate_overall_risk_score(risk_scores)

            # Generate recommendations
            recommendations = self._generate_risk_recommendations(risk_scores, overall_risk)

            # Identify risk drivers
            risk_drivers = self._identify_risk_drivers(risk_scores)

            processing_time = time.time() - start_time

            return {
                'document_id': document_id,
                'overall_risk': overall_risk,
                'risk_factors': risk_scores,
                'risk_drivers': risk_drivers,
                'recommendations': recommendations,
                'assessment_timestamp': time.time(),
                'processing_time': processing_time
            }

        except Exception as e:
            logger.error(f"Risk assessment failed for document {document_id}: {e}")
            return {
                'error': 'Risk assessment failed',
                'message': str(e),
                'document_id': document_id,
                'processing_time': time.time() - start_time
            }

    async def assess_portfolio_risks(
        self,
        documents: List[Dict[str, Any]],
        group_by: str = 'document_type'
    ) -> Dict[str, Any]:
        """Assess risks across a portfolio of documents."""

        start_time = time.time()

        if not self._initialize_assessor():
            return {
                'error': 'Risk assessment not available',
                'message': 'Required dependencies not installed or initialization failed'
            }

        try:
            if not documents:
                return {
                    'portfolio_summary': {},
                    'risk_distribution': {},
                    'high_risk_documents': [],
                    'processing_time': time.time() - start_time
                }

            # Assess each document
            document_assessments = []
            for doc in documents:
                doc_id = doc.get('document_id', f"doc_{len(document_assessments)}")
                assessment = await self.assess_document_risk(
                    doc_id, doc, doc.get('analysis_history')
                )
                if 'error' not in assessment:
                    document_assessments.append(assessment)

            if not document_assessments:
                return {
                    'portfolio_summary': {'total_documents': len(documents), 'assessed_documents': 0},
                    'risk_distribution': {},
                    'high_risk_documents': [],
                    'processing_time': time.time() - start_time
                }

            # Calculate portfolio summary
            risk_levels = [doc['overall_risk']['risk_level'] for doc in document_assessments]
            risk_distribution = dict(Counter(risk_levels))

            overall_scores = [doc['overall_risk']['overall_score'] for doc in document_assessments]
            avg_risk_score = sum(overall_scores) / len(overall_scores)

            # Group by specified field
            grouped_risks = defaultdict(list)
            for doc in document_assessments:
                group_key = doc.get(group_by, 'unknown')
                grouped_risks[group_key].append(doc['overall_risk']['overall_score'])

            group_avg_risks = {}
            for group, scores in grouped_risks.items():
                group_avg_risks[group] = round(sum(scores) / len(scores), 3)

            # Identify high-risk documents
            high_risk_docs = [
                doc['document_id'] for doc in document_assessments
                if doc['overall_risk']['risk_level'] in ['critical', 'high']
            ]

            # Calculate risk trends by group
            risk_trends = {}
            for group, scores in grouped_risks.items():
                if len(scores) > 1:
                    sorted_scores = sorted(scores, reverse=True)  # Highest risk first
                    risk_trends[group] = {
                        'highest_risk': sorted_scores[0],
                        'average_risk': round(sum(scores) / len(scores), 3),
                        'document_count': len(scores),
                        'high_risk_count': sum(1 for s in scores if s >= 0.6)
                    }

            portfolio_summary = {
                'total_documents': len(documents),
                'assessed_documents': len(document_assessments),
                'average_risk_score': round(avg_risk_score, 3),
                'risk_distribution': risk_distribution,
                'high_risk_document_count': len(high_risk_docs),
                'group_risk_averages': group_avg_risks,
                'risk_trends': risk_trends
            }

            processing_time = time.time() - start_time

            return {
                'portfolio_summary': portfolio_summary,
                'document_assessments': document_assessments,
                'high_risk_documents': high_risk_docs,
                'processing_time': processing_time,
                'assessment_timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"Portfolio risk assessment failed: {e}")
            return {
                'error': 'Portfolio risk assessment failed',
                'message': str(e),
                'processing_time': time.time() - start_time
            }

    def update_risk_factors(self, custom_factors: Dict[str, Dict[str, Any]]) -> bool:
        """Update risk factors configuration."""
        try:
            for factor_name, config in custom_factors.items():
                if factor_name in self.risk_factors:
                    self.risk_factors[factor_name].update(config)
                else:
                    # Validate new factor configuration
                    required_keys = ['weight', 'description', 'risk_function']
                    if all(key in config for key in required_keys):
                        self.risk_factors[factor_name] = config
                    else:
                        logger.warning(f"Invalid configuration for risk factor {factor_name}")
                        continue

            # Re-normalize weights to ensure they sum to 1.0
            total_weight = sum(factor['weight'] for factor in self.risk_factors.values())
            if total_weight > 0:
                for factor in self.risk_factors.values():
                    factor['weight'] = factor['weight'] / total_weight

            return True

        except Exception as e:
            logger.error(f"Failed to update risk factors: {e}")
            return False


# Global instance for reuse
risk_assessor = RiskAssessor()


async def assess_document_risk(
    document_id: str,
    document_data: Dict[str, Any],
    analysis_history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Convenience function for document risk assessment.

    Args:
        document_id: ID of the document to assess
        document_data: Document metadata and content
        analysis_history: Historical analysis results

    Returns:
        Risk assessment results
    """
    return await risk_assessor.assess_document_risk(document_id, document_data, analysis_history)


async def assess_portfolio_risks(
    documents: List[Dict[str, Any]],
    group_by: str = 'document_type'
) -> Dict[str, Any]:
    """Convenience function for portfolio risk assessment.

    Args:
        documents: List of document data dictionaries
        group_by: Field to group results by

    Returns:
        Portfolio risk assessment results
    """
    return await risk_assessor.assess_portfolio_risks(documents, group_by)
