"""Tests for Application Validators."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone
from typing import Dict, Any, List

from ...application.validators.base_validator import (
    BaseValidator, ValidationResult, ValidationError, ValidationSeverity
)
from ...application.validators.business_validators import (
    DocumentBusinessValidator, AnalysisBusinessValidator, FindingBusinessValidator
)
from ...application.validators.command_validators import (
    CreateDocumentCommandValidator, PerformAnalysisCommandValidator
)
from ...application.validators.query_validators import (
    GetDocumentQueryValidator, GetDocumentsQueryValidator
)
from ...application.validators.validation_pipeline import ValidationPipeline

from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.confidence import Confidence


class TestBaseValidator:
    """Test cases for BaseValidator."""

    def test_base_validator_creation(self):
        """Test creating base validator."""
        validator = BaseValidator()
        assert validator is not None

    def test_validation_result_creation(self):
        """Test validation result creation."""
        result = ValidationResult()

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

        # Test with errors
        result.add_error(ValidationError(
            message="Test error",
            code="TEST_ERROR",
            severity=ValidationSeverity.ERROR,
            field="test_field"
        ))

        assert result.is_valid is False
        assert len(result.errors) == 1

        # Test with warnings
        result.add_warning(ValidationError(
            message="Test warning",
            code="TEST_WARNING",
            severity=ValidationSeverity.WARNING,
            field="test_field"
        ))

        assert len(result.warnings) == 1

    def test_validation_error_creation(self):
        """Test validation error creation."""
        error = ValidationError(
            message="Test error message",
            code="TEST_ERROR",
            severity=ValidationSeverity.ERROR,
            field="test_field",
            value="invalid_value",
            metadata={"additional": "info"}
        )

        assert error.message == "Test error message"
        assert error.code == "TEST_ERROR"
        assert error.severity == ValidationSeverity.ERROR
        assert error.field == "test_field"
        assert error.value == "invalid_value"
        assert error.metadata == {"additional": "info"}

    def test_validation_severity_enum(self):
        """Test validation severity enumeration."""
        assert ValidationSeverity.ERROR.value == "error"
        assert ValidationSeverity.WARNING.value == "warning"
        assert ValidationSeverity.INFO.value == "info"


class TestDocumentBusinessValidator:
    """Test cases for DocumentBusinessValidator."""

    @pytest.fixture
    def mock_document_repository(self):
        """Mock document repository."""
        return Mock()

    def test_validator_creation(self, mock_document_repository):
        """Test creating document business validator."""
        validator = DocumentBusinessValidator(
            document_repository=mock_document_repository
        )

        assert validator.document_repository == mock_document_repository

    @pytest.mark.asyncio
    async def test_validate_large_document(self):
        """Test validation of large documents."""
        # Create a large document
        large_content = "x" * (15 * 1024 * 1024)  # 15MB

        document = Document(
            id='large-doc',
            title='Large Document',
            content=large_content,
            repository_id='repo-123'
        )

        validator = DocumentBusinessValidator()

        # Mock the content.text attribute
        document.content = Mock()
        document.content.text = large_content

        result = await validator.validate(document)

        # Should have size validation error
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("exceeds maximum size" in error.message for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_normal_document(self):
        """Test validation of normal-sized documents."""
        document = Document(
            id='normal-doc',
            title='Normal Document',
            content='This is normal content',
            repository_id='repo-123'
        )

        # Mock attributes
        document.content = Mock()
        document.content.text = 'This is normal content'
        document.word_count = 50

        validator = DocumentBusinessValidator()

        result = await validator.validate(document)

        # Should pass validation
        assert result.is_valid
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_duplicate_title(self, mock_document_repository):
        """Test validation of duplicate titles."""
        # Setup mock repository
        existing_doc = Mock()
        existing_doc.id = 'existing-doc'
        existing_doc.title = 'Duplicate Title'

        mock_document_repository.find_by_title = AsyncMock(return_value=[existing_doc])

        document = Document(
            id='new-doc',
            title='Duplicate Title',
            content='New content',
            repository_id='repo-123'
        )

        validator = DocumentBusinessValidator(
            document_repository=mock_document_repository
        )

        result = await validator.validate(document)

        # Should have duplicate title warning
        assert len(result.warnings) > 0
        assert any("similar title" in warning.message for warning in result.warnings)


class TestAnalysisBusinessValidator:
    """Test cases for AnalysisBusinessValidator."""

    def test_validator_creation(self):
        """Test creating analysis business validator."""
        validator = AnalysisBusinessValidator()
        assert validator is not None

    @pytest.mark.asyncio
    async def test_validate_analysis_with_results(self):
        """Test validation of analysis with results."""
        analysis = Analysis(
            id='analysis-123',
            document_id='doc-123',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY
        )

        # Set up analysis with results
        analysis.results = {'similarity_score': 0.85}
        analysis.confidence = Confidence(0.85)

        validator = AnalysisBusinessValidator()

        result = await validator.validate(analysis)

        # Should pass validation
        assert result.is_valid

    @pytest.mark.asyncio
    async def test_validate_analysis_without_results(self):
        """Test validation of analysis without results."""
        analysis = Analysis(
            id='analysis-123',
            document_id='doc-123',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
            status=AnalysisStatus.PENDING
        )

        validator = AnalysisBusinessValidator()

        result = await validator.validate(analysis)

        # Should pass validation (pending analyses don't need results)
        assert result.is_valid

    @pytest.mark.asyncio
    async def test_validate_failed_analysis(self):
        """Test validation of failed analysis."""
        analysis = Analysis(
            id='analysis-123',
            document_id='doc-123',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY,
            status=AnalysisStatus.FAILED
        )

        analysis.error_message = "Analysis failed"

        validator = AnalysisBusinessValidator()

        result = await validator.validate(analysis)

        # Should pass validation (failed analyses are valid)
        assert result.is_valid


class TestFindingBusinessValidator:
    """Test cases for FindingBusinessValidator."""

    def test_validator_creation(self):
        """Test creating finding business validator."""
        validator = FindingBusinessValidator()
        assert validator is not None

    @pytest.mark.asyncio
    async def test_validate_high_severity_finding(self):
        """Test validation of high severity finding."""
        finding = Finding(
            id='finding-123',
            analysis_id='analysis-123',
            document_id='doc-123',
            title='Critical Security Issue',
            description='Found critical vulnerability',
            severity=FindingSeverity.HIGH,
            confidence=Confidence(0.9),
            category='security'
        )

        validator = FindingBusinessValidator()

        result = await validator.validate(finding)

        # Should pass validation
        assert result.is_valid

        # High severity findings should generate appropriate warnings
        assert len(result.warnings) > 0

    @pytest.mark.asyncio
    async def test_validate_low_confidence_finding(self):
        """Test validation of low confidence finding."""
        finding = Finding(
            id='finding-123',
            analysis_id='analysis-123',
            document_id='doc-123',
            title='Potential Issue',
            description='Might be an issue',
            severity=FindingSeverity.MEDIUM,
            confidence=Confidence(0.3),  # Low confidence
            category='code_quality'
        )

        validator = FindingBusinessValidator()

        result = await validator.validate(finding)

        # Should pass validation but have warnings about low confidence
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("low confidence" in warning.message.lower() for warning in result.warnings)


class TestCommandValidators:
    """Test cases for Command Validators."""

    def test_create_document_command_validator(self):
        """Test create document command validator."""
        validator = CreateDocumentCommandValidator()

        # Valid command
        valid_command = {
            'title': 'Test Document',
            'content': 'Test content',
            'repository_id': 'repo-123'
        }

        result = validator.validate(valid_command)
        assert result.is_valid

        # Invalid command - missing required fields
        invalid_command = {
            'title': '',  # Empty title
            'content': 'Test content'
        }

        result = validator.validate(invalid_command)
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_perform_analysis_command_validator(self):
        """Test perform analysis command validator."""
        validator = PerformAnalysisCommandValidator()

        # Valid command
        valid_command = {
            'document_id': 'doc-123',
            'analysis_type': 'semantic_similarity',
            'priority': 'normal'
        }

        result = validator.validate(valid_command)
        assert result.is_valid

        # Invalid command - invalid analysis type
        invalid_command = {
            'document_id': 'doc-123',
            'analysis_type': 'invalid_type'
        }

        result = validator.validate(invalid_command)
        assert not result.is_valid


class TestQueryValidators:
    """Test cases for Query Validators."""

    def test_get_document_query_validator(self):
        """Test get document query validator."""
        validator = GetDocumentQueryValidator()

        # Valid query
        valid_query = {
            'document_id': 'doc-123',
            'include_metadata': True
        }

        result = validator.validate(valid_query)
        assert result.is_valid

        # Invalid query - missing document_id
        invalid_query = {
            'include_metadata': True
        }

        result = validator.validate(invalid_query)
        assert not result.is_valid

    def test_get_documents_query_validator(self):
        """Test get documents query validator."""
        validator = GetDocumentsQueryValidator()

        # Valid query
        valid_query = {
            'repository_id': 'repo-123',
            'limit': 50,
            'offset': 0
        }

        result = validator.validate(valid_query)
        assert result.is_valid

        # Invalid query - negative limit
        invalid_query = {
            'repository_id': 'repo-123',
            'limit': -1
        }

        result = validator.validate(invalid_query)
        assert not result.is_valid


class TestValidationPipeline:
    """Test cases for ValidationPipeline."""

    def test_pipeline_creation(self):
        """Test creating validation pipeline."""
        pipeline = ValidationPipeline()
        assert pipeline is not None
        assert len(pipeline._validators) == 0

    def test_add_validator(self):
        """Test adding validators to pipeline."""
        pipeline = ValidationPipeline()
        validator = Mock()

        pipeline.add_validator('test', validator)

        assert 'test' in pipeline._validators
        assert pipeline._validators['test'] == validator

    @pytest.mark.asyncio
    async def test_pipeline_execution(self):
        """Test pipeline execution."""
        pipeline = ValidationPipeline()

        # Mock validator
        mock_validator = Mock()
        mock_validator.validate = AsyncMock(return_value=ValidationResult())

        pipeline.add_validator('mock', mock_validator)

        # Execute pipeline
        data = {'test': 'data'}
        result = await pipeline.validate(data)

        # Assert
        assert result.is_valid
        mock_validator.validate.assert_called_once_with(data)

    @pytest.mark.asyncio
    async def test_pipeline_with_errors(self):
        """Test pipeline execution with validation errors."""
        pipeline = ValidationPipeline()

        # Mock validator that returns errors
        mock_validator = Mock()
        error_result = ValidationResult()
        error_result.add_error(ValidationError(
            message="Validation failed",
            code="VALIDATION_ERROR",
            severity=ValidationSeverity.ERROR
        ))
        mock_validator.validate = AsyncMock(return_value=error_result)

        pipeline.add_validator('mock', mock_validator)

        # Execute pipeline
        data = {'test': 'data'}
        result = await pipeline.validate(data)

        # Assert
        assert not result.is_valid
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_pipeline_multiple_validators(self):
        """Test pipeline with multiple validators."""
        pipeline = ValidationPipeline()

        # First validator - passes
        validator1 = Mock()
        validator1.validate = AsyncMock(return_value=ValidationResult())

        # Second validator - fails
        validator2 = Mock()
        error_result = ValidationResult()
        error_result.add_error(ValidationError(
            message="Second validation failed",
            code="SECOND_ERROR",
            severity=ValidationSeverity.ERROR
        ))
        validator2.validate = AsyncMock(return_value=error_result)

        pipeline.add_validator('first', validator1)
        pipeline.add_validator('second', validator2)

        # Execute pipeline
        data = {'test': 'data'}
        result = await pipeline.validate(data)

        # Assert
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].message == "Second validation failed"

        # Both validators should have been called
        validator1.validate.assert_called_once_with(data)
        validator2.validate.assert_called_once_with(data)


class TestValidatorIntegration:
    """Test integration between validators."""

    @pytest.mark.asyncio
    async def test_complete_validation_workflow(self):
        """Test complete validation workflow."""
        # Create pipeline with multiple validators
        pipeline = ValidationPipeline()

        # Add business validators
        doc_validator = DocumentBusinessValidator()
        analysis_validator = AnalysisBusinessValidator()

        pipeline.add_validator('document', doc_validator)
        pipeline.add_validator('analysis', analysis_validator)

        # Create test data
        document = Document(
            id='test-doc',
            title='Test Document',
            content='Test content',
            repository_id='repo-123'
        )

        # Mock document attributes
        document.content = Mock()
        document.content.text = 'Test content'
        document.word_count = 2

        analysis = Analysis(
            id='test-analysis',
            document_id='test-doc',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY
        )

        # Test document validation
        doc_result = await pipeline.validate(document)
        assert doc_result.is_valid

        # Test analysis validation
        analysis_result = await pipeline.validate(analysis)
        assert analysis_result.is_valid

    @pytest.mark.asyncio
    async def test_validator_error_aggregation(self):
        """Test error aggregation across multiple validators."""
        pipeline = ValidationPipeline()

        # Create validator that produces errors
        class ErrorValidator(BaseValidator):
            async def validate(self, data):
                result = ValidationResult()
                result.add_error(ValidationError(
                    message="Test error",
                    code="TEST_ERROR",
                    severity=ValidationSeverity.ERROR
                ))
                return result

        # Create validator that produces warnings
        class WarningValidator(BaseValidator):
            async def validate(self, data):
                result = ValidationResult()
                result.add_warning(ValidationError(
                    message="Test warning",
                    code="TEST_WARNING",
                    severity=ValidationSeverity.WARNING
                ))
                return result

        pipeline.add_validator('error', ErrorValidator())
        pipeline.add_validator('warning', WarningValidator())

        # Execute validation
        data = {'test': 'data'}
        result = await pipeline.validate(data)

        # Assert aggregation
        assert not result.is_valid
        assert len(result.errors) == 1
        assert len(result.warnings) == 1

    @pytest.mark.asyncio
    async def test_validator_performance(self):
        """Test validator performance."""
        import time

        pipeline = ValidationPipeline()

        # Add multiple validators
        for i in range(5):
            validator = Mock()
            validator.validate = AsyncMock(return_value=ValidationResult())
            pipeline.add_validator(f'validator_{i}', validator)

        # Measure execution time
        start_time = time.time()

        data = {'test': 'data'}
        result = await pipeline.validate(data)

        end_time = time.time()
        execution_time = end_time - start_time

        # Assert reasonable performance (< 1 second for 5 validators)
        assert execution_time < 1.0
        assert result.is_valid
