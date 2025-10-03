"""
Integration Compliance Validator - Phase 9.3
Validates integration compliance (API contracts, security, versions, rate limits).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..entities.external_service_entities import (
    ServiceCatalogEntry,
    ValidationIssue,
    ComplianceValidationResult,
    IssueSeverity
)


class IntegrationComplianceValidator:
    """
    Validates external service integrations for:
    - API contract compliance
    - Security & compliance requirements
    - Version compatibility
    - Rate limit sufficiency
    """
    
    def __init__(
        self,
        secure_analyzer_client=None,
        code_analyzer_client=None,
        analysis_service_client=None,
        log_client=None
    ):
        """Initialize the validator."""
        self.secure_analyzer = secure_analyzer_client
        self.code_analyzer = code_analyzer_client
        self.analysis_service = analysis_service_client
        self.log_client = log_client
    
    async def validate_services(
        self,
        cataloged_services: List[ServiceCatalogEntry],
        feature_requirements: Dict[str, Any]
    ) -> List[ComplianceValidationResult]:
        """
        Validate all cataloged services for compliance.
        
        Args:
            cataloged_services: Services to validate
            feature_requirements: Feature requirements (e.g., expected load)
        
        Returns:
            List of validation results with issues
        """
        if self.log_client:
            await self.log_client.log_info(
                f"Starting compliance validation for {len(cataloged_services)} services"
            )
        
        results = []
        
        for entry in cataloged_services:
            service = entry.service_match
            
            issues: List[ValidationIssue] = []
            
            # Validate API contracts
            api_issues = await self._validate_api_contracts(service, feature_requirements)
            issues.extend(api_issues)
            
            # Validate security compliance
            security_issues = await self._validate_security_compliance(service)
            issues.extend(security_issues)
            
            # Validate version compatibility
            version_issues = await self._validate_version_compatibility(service)
            issues.extend(version_issues)
            
            # Validate rate limits
            rate_limit_issues = await self._validate_rate_limits(service, feature_requirements)
            issues.extend(rate_limit_issues)
            
            # Calculate totals
            total_sp = sum(issue.story_points_to_add for issue in issues)
            total_days = sum(issue.timeline_impact_days for issue in issues)
            
            # Create result
            result = ComplianceValidationResult(
                service_id=service.service_id,
                service_name=service.name,
                api_compliant=not any(i.category == "api_contract" for i in issues),
                security_compliant=not any(i.category == "security" for i in issues),
                version_compatible=not any(i.category == "version" for i in issues),
                rate_limits_sufficient=not any(i.category == "rate_limits" for i in issues),
                issues=issues,
                total_story_points_to_add=total_sp,
                total_timeline_impact_days=total_days,
                validation_confidence=0.95 if issues else 1.0
            )
            
            results.append(result)
            
            if self.log_client and issues:
                await self.log_client.log_warning(
                    f"Validation issues found for {service.name}: {len(issues)} issues",
                    context={
                        "service_id": service.service_id,
                        "total_sp": total_sp,
                        "total_days": total_days
                    }
                )
        
        if self.log_client:
            total_issues = sum(len(r.issues) for r in results)
            await self.log_client.log_info(
                f"Compliance validation complete: {total_issues} issues found",
                context={
                    "total_sp_to_add": sum(r.total_story_points_to_add for r in results),
                    "total_days_impact": sum(r.total_timeline_impact_days for r in results)
                }
            )
        
        return results
    
    async def _validate_api_contracts(
        self,
        service: Any,
        requirements: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate API contracts."""
        issues = []
        
        # Mock implementation - would use code-analyzer
        if "firebase" in service.service_id.lower():
            # Check rate limits
            issues.append(ValidationIssue(
                severity=IssueSeverity.HIGH,
                category="rate_limits",
                issue="FCM rate limit (60 msg/min) insufficient for 100K users at peak",
                impact="Cannot meet performance requirements",
                detection_method="Rate limit analysis vs requirements",
                remediation="Implement message queue with batching",
                story_points_to_add=8,
                timeline_impact_days=1.0,
                sprint="Sprint 1"
            ))
            
            # Check payload size
            issues.append(ValidationIssue(
                severity=IssueSeverity.MEDIUM,
                category="data_contract",
                issue="Planned payload size (6KB) exceeds FCM limit (4KB)",
                impact="Large notifications will fail",
                detection_method="Payload size analysis",
                remediation="Implement image URL references instead of inline",
                story_points_to_add=3,
                timeline_impact_days=0.5,
                sprint="Sprint 1"
            ))
        
        return issues
    
    async def _validate_security_compliance(
        self,
        service: Any
    ) -> List[ValidationIssue]:
        """Validate security compliance."""
        issues = []
        
        # Mock implementation - would use secure-analyzer
        if "sendgrid" in service.service_id.lower():
            issues.append(ValidationIssue(
                severity=IssueSeverity.MEDIUM,
                category="credential_management",
                issue="SendGrid API key rotation process not documented",
                impact="Risk of credential exposure, policy non-compliance",
                detection_method="Secure-Analyzer policy check",
                remediation="Document API key rotation procedure",
                story_points_to_add=2,
                timeline_impact_days=0.3,
                sprint="Sprint 1",
                assignee="Sarah Chen + Security Team"
            ))
        
        return issues
    
    async def _validate_version_compatibility(
        self,
        service: Any
    ) -> List[ValidationIssue]:
        """Validate version compatibility."""
        issues = []
        
        # Mock implementation - typically no issues
        # Real implementation would check SDK versions against project requirements
        
        return issues
    
    async def _validate_rate_limits(
        self,
        service: Any,
        requirements: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate rate limits are sufficient."""
        issues = []
        
        # This is typically caught in API contract validation
        # Separate method for clarity
        
        return issues

