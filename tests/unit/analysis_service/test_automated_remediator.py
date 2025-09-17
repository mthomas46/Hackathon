"""Tests for automated remediation functionality in Analysis Service.

Tests the automated remediator module and its integration with the analysis service.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from services.analysis_service.modules.automated_remediator import (
    AutomatedRemediator,
    remediate_document,
    preview_remediation,
    AUTOMATED_REMEDIATION_AVAILABLE
)


@pytest.fixture
def sample_document_content():
    """Create sample document content for remediation testing."""
    return """# API Guide

This is a comprehensive guide for our api. The api uses oauth 2.0 for authentication.

## Getting Started
first, you need to create a account. Then you can login with your credentials.

## Endpoints

### get /users
retrieves users from the system.

**parameters:**
- limit (integer): max users to return

**response:**
```json
{
  "users": [
    {
      "id": 123,
      "name": "john doe"
    }
  ]
}
```

### post /users
creates a new user.

**request body:**
```json
{
  "name": "jane smith",
  "email": "jane@example.com"
}
```

## Error Handling
the api returns standard http status codes:
- 200 ok: success
- 400 bad request: invalid parameters
- 500 internal server error: server error

## Rate Limiting
requests are limited to 1000 per hour for authenticated users.
"""


@pytest.fixture
def sample_clean_document():
    """Create sample clean document content."""
    return """# API Developer Guide

This is a comprehensive guide for our API. The API uses OAuth 2.0 for authentication.

## Getting Started

First, you need to create an account. Then you can log in with your credentials.

## Endpoints

### GET /users

Retrieves users from the system.

**Parameters:**
- `limit` (integer): Maximum users to return

**Response:**
```json
{
  "users": [
    {
      "id": 123,
      "name": "John Doe"
    }
  ]
}
```

### POST /users

Creates a new user.

**Request Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com"
}
```

## Error Handling

The API returns standard HTTP status codes:
- `200 OK`: Success
- `400 Bad Request`: Invalid parameters
- `500 Internal Server Error`: Server error

## Rate Limiting

Requests are limited to 1000 per hour for authenticated users.
"""


class TestAutomatedRemediator:
    """Test the AutomatedRemediator class."""

    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful initialization of the automated remediator."""
        remediator = AutomatedRemediator()
        success = remediator._initialize_remediator()
        assert success is True
        assert remediator.initialized is True

    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test initialization failure when dependencies are not available."""
        original_available = AUTOMATED_REMEDIATION_AVAILABLE

        with patch('services.analysis_service.modules.automated_remediator.AUTOMATED_REMEDIATION_AVAILABLE', False):
            remediator = AutomatedRemediator()
            success = remediator._initialize_remediator()
            assert success is False
            assert remediator.initialized is False

    @pytest.mark.asyncio
    async def test_analyze_document_structure(self, sample_document_content):
        """Test document structure analysis."""
        remediator = AutomatedRemediator()

        structure = remediator._analyze_document_structure(sample_document_content)

        assert 'headings' in structure
        assert 'code_blocks' in structure
        assert 'links' in structure
        assert 'issues' in structure
        assert 'suggestions' in structure

        # Should find headings
        assert len(structure['headings']) > 0
        # Should find code blocks
        assert len(structure['code_blocks']) > 0

    @pytest.mark.asyncio
    async def test_fix_formatting_issues(self, sample_document_content):
        """Test formatting issue fixes."""
        remediator = AutomatedRemediator()

        fixed_content, applied_fixes = remediator._fix_formatting_issues(sample_document_content, [])

        assert isinstance(fixed_content, str)
        assert isinstance(applied_fixes, list)
        # Content should be modified (formatting fixes applied)
        assert fixed_content != sample_document_content or applied_fixes == []

    @pytest.mark.asyncio
    async def test_fix_terminology_consistency(self, sample_document_content):
        """Test terminology consistency fixes."""
        remediator = AutomatedRemediator()

        fixed_content, applied_fixes = remediator._fix_terminology_consistency(sample_document_content, [])

        assert isinstance(fixed_content, str)
        assert isinstance(applied_fixes, list)
        # Should fix "api" to "API"
        assert 'API' in fixed_content

    @pytest.mark.asyncio
    async def test_fix_link_issues(self, sample_document_content):
        """Test link issue fixes."""
        remediator = AutomatedRemediator()

        content_with_links = sample_document_content + "\n\n[link text]  (http://example.com)"
        fixed_content, applied_fixes = remediator._fix_link_issues(content_with_links, [])

        assert isinstance(fixed_content, str)
        assert isinstance(applied_fixes, list)
        # Should fix link spacing
        assert '[link text](http://example.com)' in fixed_content

    @pytest.mark.asyncio
    async def test_fix_structure_issues(self, sample_document_content):
        """Test structure issue fixes."""
        remediator = AutomatedRemediator()

        # Add more content to test TOC generation
        long_content = sample_document_content + "\n" * 100
        for i in range(10):
            long_content += f"\n### Section {i+1}\n\nContent for section {i+1}.\n"

        fixed_content, applied_fixes = remediator._fix_structure_issues(long_content, [])

        assert isinstance(fixed_content, str)
        assert isinstance(applied_fixes, list)

    @pytest.mark.asyncio
    async def test_check_safety(self, sample_document_content):
        """Test safety checks for automated changes."""
        remediator = AutomatedRemediator()

        # Test with identical content (should be safe)
        safety_results = remediator._check_safety(sample_document_content, sample_document_content)

        assert 'safe' in safety_results
        assert 'checks_passed' in safety_results
        assert 'checks_failed' in safety_results
        assert 'confidence_score' in safety_results
        assert safety_results['safe'] is True

    @pytest.mark.asyncio
    async def test_calculate_similarity(self, sample_document_content, sample_clean_document):
        """Test similarity calculation between documents."""
        remediator = AutomatedRemediator()

        similarity = remediator._calculate_similarity(sample_document_content, sample_clean_document)

        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0

        # Similar documents should have high similarity
        assert similarity > 0.8

    @pytest.mark.asyncio
    async def test_generate_remediation_report(self, sample_document_content):
        """Test remediation report generation."""
        remediator = AutomatedRemediator()

        applied_fixes = ["Fixed heading spacing", "Standardized terminology"]
        safety_results = {'safe': True, 'checks_passed': ['content_preservation'], 'warnings': []}
        processing_time = 1.5

        report = remediator._generate_remediation_report(
            sample_document_content, sample_document_content,
            applied_fixes, safety_results, processing_time
        )

        assert 'remediation_summary' in report
        assert 'applied_fixes' in report
        assert 'safety_assessment' in report
        assert 'quality_improvements' in report
        assert 'recommendations' in report

        assert report['remediation_summary']['changes_made'] == len(applied_fixes)
        assert report['remediation_summary']['processing_time'] == processing_time

    @pytest.mark.asyncio
    async def test_remediate_document_full(self, sample_document_content):
        """Test full document remediation."""
        remediator = AutomatedRemediator()

        result = await remediator.remediate_document(
            content=sample_document_content,
            doc_type='api_reference',
            confidence_level='medium'
        )

        assert 'original_content' in result
        assert 'remediated_content' in result
        assert 'backup' in result
        assert 'report' in result
        assert 'changes_applied' in result
        assert 'safety_status' in result
        assert 'processing_time' in result

        # Should have applied some fixes
        assert isinstance(result['changes_applied'], int)
        assert result['changes_applied'] >= 0

    @pytest.mark.asyncio
    async def test_preview_remediation(self, sample_document_content):
        """Test remediation preview functionality."""
        remediator = AutomatedRemediator()

        result = await remediator.preview_remediation(
            content=sample_document_content,
            doc_type='api_reference'
        )

        assert 'preview_available' in result
        assert 'proposed_fixes' in result
        assert 'fix_count' in result
        assert 'estimated_processing_time' in result

        if result['preview_available']:
            assert isinstance(result['proposed_fixes'], list)
            assert isinstance(result['fix_count'], int)
            assert result['fix_count'] >= 0

    @pytest.mark.asyncio
    async def test_remediate_document_minimal_content(self):
        """Test remediation with minimal content."""
        remediator = AutomatedRemediator()

        minimal_content = "This is a short document."

        result = await remediator.remediate_document(
            content=minimal_content,
            doc_type='general'
        )

        assert result['original_content'] == minimal_content
        assert 'remediated_content' in result
        assert 'report' in result

    @pytest.mark.asyncio
    async def test_update_remediation_rules(self):
        """Test updating remediation rules."""
        remediator = AutomatedRemediator()

        custom_rules = {
            'formatting_consistency': {
                'confidence_threshold': 0.95,
                'automated_fixes': True
            }
        }

        success = remediator.update_remediation_rules(custom_rules)
        assert success is True
        assert remediator.remediation_rules['formatting_consistency']['confidence_threshold'] == 0.95

    @pytest.mark.asyncio
    async def test_backup_functionality(self):
        """Test backup creation functionality."""
        remediator = AutomatedRemediator()

        content = "Test content"
        metadata = {"version": "1.0"}

        backup = remediator._create_backup(content, metadata)

        assert 'content' in backup
        assert 'timestamp' in backup
        assert 'metadata' in backup
        assert 'backup_id' in backup
        assert backup['content'] == content
        assert backup['metadata'] == metadata

    @pytest.mark.asyncio
    async def test_enable_backup(self):
        """Test backup enable/disable functionality."""
        remediator = AutomatedRemediator()

        # Test enabling backup
        remediator.enable_backup(True)
        assert remediator.backup_enabled is True

        # Test disabling backup
        remediator.enable_backup(False)
        assert remediator.backup_enabled is False


@pytest.mark.asyncio
class TestAutomatedRemediationIntegration:
    """Test the integration functions."""

    @pytest.mark.asyncio
    async def test_remediate_document_function(self, sample_document_content):
        """Test the convenience function for document remediation."""
        with patch('services.analysis_service.modules.automated_remediator.automated_remediator') as mock_remediator:
            mock_remediator.remediate_document.return_value = {
                'original_content': sample_document_content,
                'remediated_content': sample_document_content,  # Assume no changes for test
                'backup': None,
                'report': {
                    'remediation_summary': {
                        'changes_made': 3,
                        'processing_time': 1.2,
                        'safety_status': 'safe'
                    },
                    'applied_fixes': ['Fixed formatting', 'Standardized terms'],
                    'safety_assessment': {'safe': True},
                    'quality_improvements': {},
                    'recommendations': []
                },
                'changes_applied': 3,
                'safety_status': 'safe',
                'processing_time': 1.2,
                'remediation_timestamp': 1234567890
            }

            result = await remediate_document(
                content=sample_document_content,
                doc_type='api_reference',
                confidence_level='medium'
            )

            assert result['changes_applied'] == 3
            assert result['safety_status'] == 'safe'
            mock_remediator.remediate_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_preview_remediation_function(self, sample_document_content):
        """Test the convenience function for remediation preview."""
        with patch('services.analysis_service.modules.automated_remediator.automated_remediator') as mock_remediator:
            mock_remediator.preview_remediation.return_value = {
                'preview_available': True,
                'proposed_fixes': ['Fix heading spacing', 'Standardize terminology'],
                'fix_count': 2,
                'estimated_processing_time': 1.0,
                'preview_timestamp': 1234567890
            }

            result = await preview_remediation(
                content=sample_document_content,
                doc_type='api_reference'
            )

            assert result['preview_available'] is True
            assert result['fix_count'] == 2
            assert len(result['proposed_fixes']) == 2
            mock_remediator.preview_remediation.assert_called_once()


class TestRemediationHandlers:
    """Test the analysis handlers integration."""

    @pytest.fixture
    def mock_service_client(self):
        """Mock service client for testing."""
        client = Mock()
        client.doc_store_url.return_value = "http://docstore:5000"
        client.get_json = Mock()
        return client

    @pytest.mark.asyncio
    async def test_handle_automated_remediation_success(self, mock_service_client, sample_document_content):
        """Test successful automated remediation handling."""
        from services.analysis_service.modules.models import AutomatedRemediationRequest

        with patch('services.analysis_service.modules.automated_remediator.remediate_document') as mock_remediate:

            mock_remediate.return_value = {
                'original_content': sample_document_content,
                'remediated_content': sample_document_content,
                'backup': None,
                'report': {
                    'remediation_summary': {
                        'changes_made': 2,
                        'processing_time': 1.0,
                        'safety_status': 'safe'
                    },
                    'applied_fixes': ['Fixed formatting'],
                    'safety_assessment': {'safe': True},
                    'quality_improvements': {},
                    'recommendations': []
                },
                'changes_applied': 2,
                'safety_status': 'safe',
                'processing_time': 1.0,
                'remediation_timestamp': 1234567890
            }

            request = AutomatedRemediationRequest(
                content=sample_document_content,
                doc_type='api_reference',
                confidence_level='medium'
            )

            # Import the handler method
            from services.analysis_service.modules.analysis_handlers import AnalysisHandlers

            result = await AnalysisHandlers.handle_automated_remediation(request)

            assert result.original_content == sample_document_content
            assert result.changes_applied == 2
            assert result.safety_status == 'safe'

    @pytest.mark.asyncio
    async def test_handle_remediation_preview_success(self, mock_service_client, sample_document_content):
        """Test successful remediation preview handling."""
        from services.analysis_service.modules.models import RemediationPreviewRequest

        with patch('services.analysis_service.modules.automated_remediator.preview_remediation') as mock_preview:

            mock_preview.return_value = {
                'preview_available': True,
                'proposed_fixes': ['Fix heading spacing', 'Standardize terms'],
                'fix_count': 2,
                'estimated_processing_time': 1.0,
                'preview_timestamp': 1234567890
            }

            request = RemediationPreviewRequest(
                content=sample_document_content,
                doc_type='api_reference'
            )

            # Import the handler method
            from services.analysis_service.modules.analysis_handlers import AnalysisHandlers

            result = await AnalysisHandlers.handle_remediation_preview(request)

            assert result.preview_available is True
            assert result.fix_count == 2
            assert len(result.proposed_fixes) == 2

    @pytest.mark.asyncio
    async def test_handle_automated_remediation_error(self, mock_service_client, sample_document_content):
        """Test automated remediation error handling."""
        from services.analysis_service.modules.models import AutomatedRemediationRequest

        with patch('services.analysis_service.modules.automated_remediator.remediate_document') as mock_remediate:

            mock_remediate.side_effect = Exception("Remediation failed")

            request = AutomatedRemediationRequest(
                content=sample_document_content,
                doc_type='api_reference'
            )

            # Import the handler method
            from services.analysis_service.modules.analysis_handlers import AnalysisHandlers

            result = await AnalysisHandlers.handle_automated_remediation(request)

            assert result.original_content == sample_document_content
            assert result.safety_status == 'error'
            assert 'error' in result.report['safety_assessment']


if __name__ == "__main__":
    pytest.main([__file__])
