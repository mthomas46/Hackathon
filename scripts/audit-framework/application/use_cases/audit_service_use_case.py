"""
AuditServiceUseCase - Application Use Case

Orchestrates the complex business operation of auditing a service,
coordinating between domain services and infrastructure.
"""

import logging
from typing import Dict, Any, Optional

from ...domain.entities.service_info import ServiceInfo
from ...domain.entities.analysis_result import AnalysisResult
from ...domain.value_objects.audit_profile import AuditProfile
from ...domain.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class AuditServiceUseCase:
    """Use case for auditing a single service.

    This use case orchestrates the complete audit process including:
    - Service validation and discovery
    - Multi-dimensional analysis execution
    - Result aggregation and scoring
    - Audit history recording
    """

    def __init__(
        self,
        audit_service: AuditService,
        analyzer_providers: Dict[str, Any]
    ):
        """Initialize the use case with dependencies.

        Args:
            audit_service: Domain service for audit orchestration
            analyzer_providers: Dictionary of analyzer instances by dimension
        """
        self.audit_service = audit_service
        self.analyzer_providers = analyzer_providers

    async def execute(
        self,
        service_info: ServiceInfo,
        audit_profile: AuditProfile
    ) -> AnalysisResult:
        """Execute the audit service use case.

        Args:
            service_info: Information about the service to audit
            audit_profile: Profile defining audit parameters

        Returns:
            Complete analysis result

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If audit execution fails
        """
        logger.info(f"Executing audit use case for service '{service_info.name}'")

        try:
            # Validate inputs
            self._validate_inputs(service_info, audit_profile)

            # Execute the audit through domain service
            result = self.audit_service.audit_service(
                service=service_info,
                profile=audit_profile,
                analyzer_providers=self.analyzer_providers
            )

            # Post-processing
            self._post_process_result(result, service_info)

            logger.info(f"Audit use case completed for service '{service_info.name}' with score {result.overall_score}")
            return result

        except Exception as e:
            logger.error(f"Audit use case failed for service '{service_info.name}': {e}")
            raise RuntimeError(f"Audit execution failed: {e}") from e

    def _validate_inputs(
        self,
        service_info: ServiceInfo,
        audit_profile: AuditProfile
    ) -> None:
        """Validate use case inputs.

        Args:
            service_info: Service information to validate
            audit_profile: Audit profile to validate

        Raises:
            ValueError: If inputs are invalid
        """
        if not service_info:
            raise ValueError("Service information is required")

        if not service_info.name or not service_info.path:
            raise ValueError("Service name and path are required")

        if not service_info.path.exists():
            raise ValueError(f"Service path does not exist: {service_info.path}")

        if not audit_profile:
            raise ValueError("Audit profile is required")

        if not audit_profile.name:
            raise ValueError("Audit profile name is required")

        # Validate that required analyzers are available
        required_dimensions = ['architecture', 'code_quality', 'performance', 'maintainability']
        missing_analyzers = [
            dim for dim in required_dimensions
            if dim not in self.analyzer_providers
        ]

        if missing_analyzers:
            raise ValueError(f"Missing required analyzers: {missing_analyzers}")

    def _post_process_result(
        self,
        result: AnalysisResult,
        service_info: ServiceInfo
    ) -> None:
        """Post-process the audit result.

        Args:
            result: The audit result to post-process
            service_info: Original service information
        """
        # Add any use-case specific metadata
        result.metadata.update({
            'use_case': 'audit_service',
            'service_discovered_at': service_info.discovered_at.isoformat() if service_info.discovered_at else None,
            'audit_duration_seconds': (result.analysis_timestamp - service_info.last_audited_at).total_seconds()
            if service_info.last_audited_at else None,
        })

        # Add business logic recommendations based on result
        if result.overall_score < 60:
            result.recommendations.insert(0, "🚨 CRITICAL: Service requires immediate attention - score below 60")
        elif result.overall_score < 70:
            result.recommendations.insert(0, "⚠️ HIGH PRIORITY: Service needs improvement - score below 70")

        if result.has_critical_issues():
            result.recommendations.insert(0, f"🔥 URGENT: Address {result.get_critical_issue_count()} critical issues immediately")

        # Add trend analysis if available
        trends = self.audit_service.get_audit_trends(service_info.name)
        if 'trend' in trends and trends['trend'] != 'stable':
            trend_indicator = "📈" if trends['trend'] == 'improving' else "📉"
            result.recommendations.append(f"{trend_indicator} Trend: Service quality is {trends['trend']}")
