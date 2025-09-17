"""Business rule validators for application layer."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from .base_validator import BaseValidator, ValidationResult, ValidationError, ValidationSeverity
from ...domain.entities.document import Document
from ...domain.entities.analysis import Analysis
from ...domain.entities.finding import Finding


class DocumentBusinessValidator(BaseValidator):
    """Validator for document business rules."""

    def __init__(self, document_repository=None):
        """Initialize document business validator."""
        super().__init__()
        self.document_repository = document_repository

    async def validate(self, document: Document) -> ValidationResult:
        """Validate document business rules."""
        errors = []
        warnings = []

        # Check document size limits
        content_size = len(document.content.text.encode('utf-8'))
        if content_size > 10 * 1024 * 1024:  # 10MB
            errors.append(self.create_error(
                "Document content exceeds maximum size limit of 10MB",
                "DOCUMENT_TOO_LARGE"
            ))

        # Check word count limits
        word_count = document.word_count
        if word_count > 100000:  # 100K words
            warnings.append(self.create_warning(
                f"Document has {word_count} words, which may impact analysis performance",
                "LARGE_DOCUMENT"
            ))

        # Check for duplicate titles (if repository available)
        if self.document_repository:
            try:
                existing_docs = await self.document_repository.find_by_title(document.title)
                existing_docs = [doc for doc in existing_docs if doc.id != document.id]

                if existing_docs:
                    warnings.append(self.create_warning(
                        f"Found {len(existing_docs)} document(s) with similar title",
                        "POTENTIAL_DUPLICATE_TITLE"
                    ))
            except Exception:
                # Repository not available or error, skip this check
                pass

        # Validate metadata consistency
        if document.metadata.created_at > document.metadata.updated_at:
            errors.append(self.create_error(
                "Document creation date cannot be after update date",
                "INVALID_DATE_ORDER"
            ))

        # Check for stale content
        days_since_update = (datetime.now(timezone.utc) - document.metadata.updated_at).days
        if days_since_update > 365:  # 1 year
            warnings.append(self.create_warning(
                f"Document has not been updated for {days_since_update} days",
                "STALE_CONTENT"
            ))

        # Validate tag consistency
        tags = document.metadata.tags or []
        if len(tags) > 20:
            warnings.append(self.create_warning(
                f"Document has {len(tags)} tags, consider consolidating",
                "TOO_MANY_TAGS"
            ))

        # Check for empty or meaningless tags
        meaningless_tags = ['test', 'temp', 'draft', 'old']
        for tag in tags:
            if tag.lower() in meaningless_tags:
                warnings.append(self.create_warning(
                    f"Tag '{tag}' may not provide meaningful categorization",
                    "MEANINGLESS_TAG"
                ))

        if errors:
            return ValidationResult.failure(errors, warnings)
        elif warnings:
            return ValidationResult.success(metadata={'warnings': warnings})

        return ValidationResult.success()


class AnalysisBusinessValidator(BaseValidator):
    """Validator for analysis business rules."""

    def __init__(self, document_repository=None, analysis_repository=None):
        """Initialize analysis business validator."""
        super().__init__()
        self.document_repository = document_repository
        self.analysis_repository = analysis_repository

    async def validate(self, analysis: Analysis) -> ValidationResult:
        """Validate analysis business rules."""
        errors = []
        warnings = []

        # Validate document exists
        if self.document_repository:
            try:
                document = await self.document_repository.get_by_id(analysis.document_id.value)
                if not document:
                    errors.append(self.create_error(
                        f"Document {analysis.document_id.value} does not exist",
                        "DOCUMENT_NOT_FOUND"
                    ))
                else:
                    # Check if document is suitable for analysis
                    if document.word_count < 10:
                        warnings.append(self.create_warning(
                            "Document has very few words, analysis may not be meaningful",
                            "INSUFFICIENT_CONTENT"
                        ))
            except Exception:
                errors.append(self.create_error(
                    "Could not verify document existence",
                    "DOCUMENT_VERIFICATION_FAILED"
                ))

        # Validate analysis type is supported
        supported_types = [
            'semantic_similarity', 'sentiment', 'content_quality',
            'trend_analysis', 'risk_assessment', 'maintenance_forecast',
            'quality_degradation', 'change_impact', 'cross_repository',
            'automated_remediation'
        ]

        if analysis.analysis_type not in supported_types:
            errors.append(self.create_error(
                f"Analysis type '{analysis.analysis_type}' is not supported",
                "UNSUPPORTED_ANALYSIS_TYPE"
            ))

        # Validate configuration
        if analysis.configuration:
            # Check timeout is reasonable
            timeout = analysis.configuration.get('timeout_seconds', 300)
            if timeout > 1800:  # 30 minutes
                warnings.append(self.create_warning(
                    f"Analysis timeout of {timeout}s is quite long",
                    "LONG_TIMEOUT"
                ))

            # Check priority is valid
            priority = analysis.configuration.get('priority', 'normal')
            if priority not in ['low', 'normal', 'high', 'critical']:
                errors.append(self.create_error(
                    f"Invalid priority: {priority}",
                    "INVALID_PRIORITY"
                ))

        # Validate status transitions
        if analysis.status.value == 'completed' and not analysis.result:
            warnings.append(self.create_warning(
                "Analysis is marked as completed but has no results",
                "MISSING_RESULTS"
            ))

        if analysis.status.value == 'failed' and not analysis.error_message:
            warnings.append(self.create_warning(
                "Analysis is marked as failed but has no error message",
                "MISSING_ERROR_MESSAGE"
            ))

        # Check for duplicate analyses
        if self.analysis_repository and analysis.status.value == 'pending':
            try:
                recent_analyses = await self.analysis_repository.find_by_document_and_type(
                    analysis.document_id.value, analysis.analysis_type
                )

                # Filter for recent analyses (last 24 hours)
                recent_cutoff = datetime.now(timezone.utc).timestamp() - (24 * 60 * 60)
                recent_similar = [
                    a for a in recent_analyses
                    if a.created_at.timestamp() > recent_cutoff and a.id != analysis.id
                ]

                if recent_similar:
                    warnings.append(self.create_warning(
                        f"Found {len(recent_similar)} similar analysis in the last 24 hours",
                        "POTENTIAL_DUPLICATE_ANALYSIS"
                    ))
            except Exception:
                # Repository not available or error, skip this check
                pass

        # Validate execution time
        if analysis.started_at and analysis.completed_at:
            execution_time = (analysis.completed_at - analysis.started_at).total_seconds()
            if execution_time > 3600:  # 1 hour
                warnings.append(self.create_warning(
                    f"Analysis took {execution_time:.0f} seconds, which is unusually long",
                    "LONG_EXECUTION_TIME"
                ))
            elif execution_time < 1:  # Less than 1 second
                warnings.append(self.create_warning(
                    "Analysis completed very quickly, results may not be comprehensive",
                    "FAST_EXECUTION"
                ))

        if errors:
            return ValidationResult.failure(errors, warnings)
        elif warnings:
            return ValidationResult.success(metadata={'warnings': warnings})

        return ValidationResult.success()


class FindingBusinessValidator(BaseValidator):
    """Validator for finding business rules."""

    def __init__(self, document_repository=None, analysis_repository=None, finding_repository=None):
        """Initialize finding business validator."""
        super().__init__()
        self.document_repository = document_repository
        self.analysis_repository = analysis_repository
        self.finding_repository = finding_repository

    async def validate(self, finding: Finding) -> ValidationResult:
        """Validate finding business rules."""
        errors = []
        warnings = []

        # Validate document exists
        if self.document_repository:
            try:
                document = await self.document_repository.get_by_id(finding.document_id.value)
                if not document:
                    errors.append(self.create_error(
                        f"Document {finding.document_id.value} does not exist",
                        "DOCUMENT_NOT_FOUND"
                    ))
            except Exception:
                errors.append(self.create_error(
                    "Could not verify document existence",
                    "DOCUMENT_VERIFICATION_FAILED"
                ))

        # Validate analysis exists
        if self.analysis_repository:
            try:
                analysis = await self.analysis_repository.get_by_id(finding.analysis_id.value)
                if not analysis:
                    errors.append(self.create_error(
                        f"Analysis {finding.analysis_id.value} does not exist",
                        "ANALYSIS_NOT_FOUND"
                    ))
                elif analysis.status.value != 'completed':
                    warnings.append(self.create_warning(
                        f"Analysis {finding.analysis_id.value} is not completed",
                        "ANALYSIS_NOT_COMPLETED"
                    ))
            except Exception:
                errors.append(self.create_error(
                    "Could not verify analysis existence",
                    "ANALYSIS_VERIFICATION_FAILED"
                ))

        # Validate severity levels
        severity_scores = {
            'critical': 1.0,
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4,
            'info': 0.2
        }

        expected_score = severity_scores.get(finding.severity)
        if expected_score and abs(finding.confidence.value - expected_score) > 0.3:
            warnings.append(self.create_warning(
                f"Confidence score {finding.confidence.value} doesn't match severity {finding.severity}",
                "CONFIDENCE_SEVERITY_MISMATCH"
            ))

        # Validate category consistency
        valid_categories = [
            'consistency', 'quality', 'security', 'performance',
            'maintainability', 'usability', 'accessibility', 'compatibility'
        ]

        if finding.category not in valid_categories:
            errors.append(self.create_error(
                f"Invalid category: {finding.category}",
                "INVALID_CATEGORY"
            ))

        # Validate description quality
        if len(finding.description) < 10:
            warnings.append(self.create_warning(
                "Finding description is very short",
                "SHORT_DESCRIPTION"
            ))

        if len(finding.description) > 500:
            warnings.append(self.create_warning(
                "Finding description is very long",
                "LONG_DESCRIPTION"
            ))

        # Check for duplicate findings
        if self.finding_repository:
            try:
                similar_findings = await self.finding_repository.find_similar(
                    document_id=finding.document_id.value,
                    category=finding.category,
                    description=finding.description[:100]  # First 100 chars
                )

                if similar_findings:
                    warnings.append(self.create_warning(
                        f"Found {len(similar_findings)} similar finding(s)",
                        "POTENTIAL_DUPLICATE_FINDING"
                    ))
            except Exception:
                # Repository not available or error, skip this check
                pass

        # Validate location information
        if finding.location:
            # Check if location is within document bounds
            # This would require access to document content, simplified for now
            pass

        # Validate suggestion quality
        if finding.suggestion:
            if len(finding.suggestion) < 5:
                warnings.append(self.create_warning(
                    "Finding suggestion is very brief",
                    "BRIEF_SUGGESTION"
                ))

        # Check for stale findings
        finding_age_days = finding.age_days
        if finding_age_days > 30 and finding.status == 'open':
            warnings.append(self.create_warning(
                f"Finding has been open for {finding_age_days} days",
                "STALE_FINDING"
            ))

        if errors:
            return ValidationResult.failure(errors, warnings)
        elif warnings:
            return ValidationResult.success(metadata={'warnings': warnings})

        return ValidationResult.success()
