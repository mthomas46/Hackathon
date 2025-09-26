"""
AuditService Domain Service

Core business logic for orchestrating audit operations across services.
Contains the main audit workflow and coordination logic.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..entities.service_info import ServiceInfo
from ..entities.analysis_result import AnalysisResult
from ..value_objects.audit_profile import AuditProfile
from ..value_objects.thresholds import ThresholdConfig

logger = logging.getLogger(__name__)


class AuditService:
    """Domain service for orchestrating audit operations.

    This service contains the core business logic for coordinating
    audits across different dimensions and services.
    """

    def __init__(self, thresholds: ThresholdConfig):
        """Initialize the audit service with configuration."""
        self.thresholds = thresholds
        self._audit_history: Dict[str, List[AnalysisResult]] = {}

    async def audit_service(
        self,
        service: ServiceInfo,
        profile: AuditProfile,
        analyzer_providers: Dict[str, Any],
        full_audit: bool = False
    ) -> AnalysisResult:
        """Execute a complete audit of a service.

        Args:
            service: The service to audit
            profile: The audit profile to use
            analyzer_providers: Dictionary of analyzer instances by dimension

        Returns:
            Complete analysis result

        Raises:
            ValueError: If service or profile is invalid
        """
        if not self._validate_audit_inputs(service, profile):
            raise ValueError("Invalid audit inputs")

        logger.info(f"Starting audit of service '{service.name}' with profile '{profile.name}'")

        try:
            # Execute analysis for each dimension
            results = {}
            for dimension, analyzer in analyzer_providers.items():
                logger.debug(f"Analyzing {dimension} for service {service.name}")
                results[dimension] = await analyzer.analyze(service, full_audit)

            # Calculate overall scores
            overall_score = self._calculate_overall_score(results, profile)
            dimensions = self._extract_dimension_scores(results)

            # Apply strict mode penalties for low-scoring dimensions
            if hasattr(profile, 'name') and profile.name == 'strict':
                overall_score = self._apply_strict_mode_penalties(overall_score, dimensions)

            recommendations = self._aggregate_recommendations(results)
            critical_issues = self._aggregate_critical_issues(results)
            detailed_issues = self._aggregate_detailed_issues(results)

            # Create analysis result
            result = AnalysisResult(
                service_name=service.name,
                overall_score=overall_score,
                dimensions=dimensions,
                architecture=results.get('architecture', {}),
                code_quality=results.get('code_quality', {}),
                performance=results.get('performance', {}),
                maintainability=results.get('maintainability', {}),
                documentation_quality=results.get('documentation_quality', {}),
                dry_principles=results.get('dry_principles', {}),
                kiss_principles=results.get('kiss_principles', {}),
                recommendations=recommendations,
                critical_issues=critical_issues,
                detailed_issues=detailed_issues,
                metadata=self._create_metadata(service, profile)
            )

            # Update service audit history
            service.mark_as_audited()
            self._record_audit_result(service.name, result)

            logger.info(f"Completed audit of service '{service.name}' with score {overall_score:.1f}")
            return result

        except Exception as e:
            logger.error(f"Audit failed for service '{service.name}': {e}")
            raise

    def _validate_audit_inputs(self, service: ServiceInfo, profile: AuditProfile) -> bool:
        """Validate audit inputs according to business rules."""
        if not service or not service.name:
            logger.error("Invalid service: missing or empty name")
            return False

        if not service.path or not service.path.exists():
            logger.error(f"Invalid service path: {service.path}")
            return False

        if not profile or not profile.name:
            logger.error("Invalid audit profile")
            return False

        return True

    def _calculate_overall_score(
        self,
        results: Dict[str, Any],
        profile: AuditProfile
    ) -> float:
        """Calculate overall audit score using profile weights."""
        total_score = 0.0
        total_weight = 0.0

        for dimension, weight in profile.dimension_weights.items():
            if dimension in results:
                result = results[dimension]
                dimension_score = result.score if hasattr(result, 'score') else 0.0
                total_score += dimension_score * (weight / 100.0)
                total_weight += weight / 100.0

        # Normalize to ensure score is between 0-100
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 0.0

        return round(max(0.0, min(100.0, final_score)), 2)

    def _apply_strict_mode_penalties(self, overall_score: float, dimensions: Dict[str, float]) -> float:
        """Apply additional penalties in strict mode for low-scoring dimensions."""
        penalty = 0.0

        # Heavy penalties for poor performance in key quality areas
        if 'dry_principles' in dimensions and dimensions['dry_principles'] < 70:
            penalty += (70 - dimensions['dry_principles']) * 0.8  # Up to 24 point penalty

        if 'documentation_quality' in dimensions and dimensions['documentation_quality'] < 75:
            penalty += (75 - dimensions['documentation_quality']) * 0.6  # Up to 18 point penalty

        if 'kiss_principles' in dimensions and dimensions['kiss_principles'] < 85:
            penalty += (85 - dimensions['kiss_principles']) * 0.4  # Up to 12 point penalty

        # Additional penalty for multiple failing dimensions
        failing_dimensions = sum(1 for score in dimensions.values() if score < 70)
        if failing_dimensions >= 2:
            penalty += failing_dimensions * 3  # Additional 3 points per failing dimension

        logger.debug(f"Strict mode penalties applied: {penalty:.1f} points")

        return max(0.0, overall_score - penalty)

    def _extract_dimension_scores(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Extract dimension scores from analysis results."""
        scores = {}

        # Extract scores from main analyzers
        for dimension, result in results.items():
            if hasattr(result, 'score'):
                scores[dimension] = result.score
            else:
                scores[dimension] = 0.0

        # Scores are now extracted from dedicated analyzers
        # No need to extract sub-dimensions from architecture anymore

        return scores

    def _aggregate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Aggregate recommendations from all dimensions."""
        recommendations = []
        for result in results.values():
            if hasattr(result, 'recommendations') and result.recommendations:
                recommendations.extend(result.recommendations)

            # Also check for issues that should become recommendations
            if hasattr(result, 'issues') and result.issues:
                for issue in result.issues:
                    if isinstance(issue, str):
                        recommendations.append(f"Address: {issue}")

        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                unique_recommendations.append(rec)
                seen.add(rec)

        return unique_recommendations

    def _aggregate_critical_issues(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Aggregate critical issues from all dimensions."""
        critical_issues = []
        for dimension, result in results.items():
            if hasattr(result, 'critical_issues') and result.critical_issues:
                for issue in result.critical_issues:
                    if isinstance(issue, dict):
                        issue_copy = issue.copy()
                        issue_copy['dimension'] = dimension
                        critical_issues.append(issue_copy)
                    elif isinstance(issue, str):
                        critical_issues.append({
                            'description': issue,
                            'dimension': dimension,
                            'severity': 'critical'
                        })

        return critical_issues

    def _aggregate_detailed_issues(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Aggregate detailed issues with location information from all dimensions."""
        detailed_issues = []
        for dimension, result in results.items():
            if hasattr(result, 'detailed_issues') and result.detailed_issues:
                for issue in result.detailed_issues:
                    if isinstance(issue, dict):
                        issue_copy = issue.copy()
                        if 'dimension' not in issue_copy:
                            issue_copy['dimension'] = dimension
                        detailed_issues.append(issue_copy)

        return detailed_issues

    def _create_metadata(self, service: ServiceInfo, profile: AuditProfile) -> Dict[str, Any]:
        """Create metadata for the audit result."""
        return {
            'service_info': service.to_dict(),
            'profile_used': profile.name,
            'profile_intensity': profile.intensity.value,
            'thresholds_applied': self.thresholds.to_dict(),
            'audit_timestamp': service.last_audited_at.isoformat() if service.last_audited_at else None,
        }

    def _record_audit_result(self, service_name: str, result: AnalysisResult) -> None:
        """Record audit result in history."""
        if service_name not in self._audit_history:
            self._audit_history[service_name] = []
        self._audit_history[service_name].append(result)

        # Keep only last 10 audits per service
        if len(self._audit_history[service_name]) > 10:
            self._audit_history[service_name] = self._audit_history[service_name][-10:]

    def get_audit_history(self, service_name: str) -> List[AnalysisResult]:
        """Get audit history for a service."""
        return self._audit_history.get(service_name, [])

    def get_latest_audit(self, service_name: str) -> Optional[AnalysisResult]:
        """Get the most recent audit for a service."""
        history = self.get_audit_history(service_name)
        return history[-1] if history else None

    def get_audit_trends(self, service_name: str, limit: int = 5) -> Dict[str, Any]:
        """Get audit trends for a service."""
        history = self.get_audit_history(service_name)[-limit:]

        if not history:
            return {'error': 'No audit history available'}

        scores = [result.overall_score for result in history]
        trend = 'stable'

        if len(scores) >= 2:
            first_avg = sum(scores[:len(scores)//2]) / (len(scores)//2)
            second_avg = sum(scores[len(scores)//2:]) / (len(scores)//2)

            if second_avg > first_avg + 5:
                trend = 'improving'
            elif first_avg > second_avg + 5:
                trend = 'declining'

        return {
            'service_name': service_name,
            'audit_count': len(history),
            'latest_score': scores[-1] if scores else 0,
            'average_score': sum(scores) / len(scores) if scores else 0,
            'trend': trend,
            'score_range': f"{min(scores)} - {max(scores)}" if scores else "N/A"
        }
