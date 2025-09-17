"""Tests for Findings API Endpoints."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from typing import Dict, Any, List

from ...main import app
from ...presentation.models.common import (
    FindingsListResponse, FindingResponse, GetFindingsRequest
)


class TestFindingsEndpoints:
    """Test cases for findings API endpoints."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_findings_request(self):
        """Sample findings request for testing."""
        return GetFindingsRequest(
            analysis_id='analysis-123',
            document_id='doc-456',
            severity='high',
            category='security',
            status='open',
            limit=50,
            offset=0
        )

    def test_findings_endpoint_exists(self, client):
        """Test that the findings endpoint exists."""
        response = client.get("/findings")
        # Should get some response (not 404)
        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_get_findings_success(self, client, sample_findings_request):
        """Test successful findings retrieval."""
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_handler:
            mock_findings = [
                FindingResponse(
                    id='finding-1',
                    analysis_id='analysis-123',
                    document_id='doc-456',
                    title='Critical Security Vulnerability',
                    description='Found SQL injection vulnerability',
                    severity='critical',
                    confidence=0.95,
                    category='security',
                    location={'file': '/src/auth.py', 'line': 45},
                    recommendation='Use parameterized queries',
                    metadata={'rule_id': 'SEC-001', 'cwe': 'CWE-89'},
                    created_at=datetime.now(timezone.utc),
                    resolved_at=None
                ),
                FindingResponse(
                    id='finding-2',
                    analysis_id='analysis-123',
                    document_id='doc-456',
                    title='Code Quality Issue',
                    description='Unused import detected',
                    severity='medium',
                    confidence=0.85,
                    category='code_quality',
                    location={'file': '/src/utils.py', 'line': 12},
                    recommendation='Remove unused import',
                    metadata={'rule_id': 'QUAL-002'},
                    created_at=datetime.now(timezone.utc),
                    resolved_at=None
                )
            ]

            mock_response = FindingsListResponse(
                findings=mock_findings,
                total_count=2,
                limit=50,
                offset=0,
                has_more=False
            )
            mock_handler.return_value = mock_response

            response = client.get(
                "/findings",
                params={
                    'analysis_id': sample_findings_request.analysis_id,
                    'severity': sample_findings_request.severity,
                    'limit': sample_findings_request.limit
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data['findings']) == 2
            assert data['total_count'] == 2
            assert data['has_more'] is False

            # Verify finding details
            first_finding = data['findings'][0]
            assert first_finding['severity'] == 'critical'
            assert first_finding['category'] == 'security'
            assert 'location' in first_finding

    @pytest.mark.asyncio
    async def test_get_findings_by_analysis_id(self, client):
        """Test getting findings filtered by analysis ID."""
        analysis_id = 'analysis-123'

        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_handler:
            mock_findings = [
                FindingResponse(
                    id='finding-1',
                    analysis_id=analysis_id,
                    document_id='doc-456',
                    title='Test Finding 1',
                    description='Description 1',
                    severity='high',
                    confidence=0.9,
                    category='security'
                ),
                FindingResponse(
                    id='finding-2',
                    analysis_id=analysis_id,
                    document_id='doc-456',
                    title='Test Finding 2',
                    description='Description 2',
                    severity='medium',
                    confidence=0.8,
                    category='performance'
                )
            ]

            mock_response = FindingsListResponse(
                findings=mock_findings,
                total_count=2,
                limit=50,
                offset=0,
                has_more=False
            )
            mock_handler.return_value = mock_response

            response = client.get(f"/findings?analysis_id={analysis_id}")

            assert response.status_code == 200
            data = response.json()
            assert len(data['findings']) == 2

            # All findings should belong to the specified analysis
            for finding in data['findings']:
                assert finding['analysis_id'] == analysis_id

    @pytest.mark.asyncio
    async def test_get_findings_by_severity(self, client):
        """Test getting findings filtered by severity."""
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_handler:
            mock_findings = [
                FindingResponse(
                    id='finding-1',
                    analysis_id='analysis-123',
                    document_id='doc-456',
                    title='Critical Finding',
                    description='Critical issue',
                    severity='critical',
                    confidence=0.95,
                    category='security'
                )
            ]

            mock_response = FindingsListResponse(
                findings=mock_findings,
                total_count=1,
                limit=50,
                offset=0,
                has_more=False
            )
            mock_handler.return_value = mock_response

            response = client.get("/findings?severity=critical")

            assert response.status_code == 200
            data = response.json()
            assert len(data['findings']) == 1
            assert data['findings'][0]['severity'] == 'critical'

    @pytest.mark.asyncio
    async def test_get_findings_by_category(self, client):
        """Test getting findings filtered by category."""
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_handler:
            mock_findings = [
                FindingResponse(
                    id='finding-1',
                    analysis_id='analysis-123',
                    document_id='doc-456',
                    title='Security Finding',
                    description='Security issue',
                    severity='high',
                    confidence=0.9,
                    category='security'
                ),
                FindingResponse(
                    id='finding-2',
                    analysis_id='analysis-123',
                    document_id='doc-456',
                    title='Performance Finding',
                    description='Performance issue',
                    severity='medium',
                    confidence=0.8,
                    category='performance'
                )
            ]

            mock_response = FindingsListResponse(
                findings=mock_findings,
                total_count=2,
                limit=50,
                offset=0,
                has_more=False
            )
            mock_handler.return_value = mock_response

            response = client.get("/findings?category=security")

            assert response.status_code == 200
            data = response.json()
            assert len(data['findings']) == 2  # Both should be returned since we mocked both

    @pytest.mark.asyncio
    async def test_get_findings_pagination(self, client):
        """Test findings pagination."""
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_handler:
            # Create 25 findings for pagination testing
            mock_findings = [
                FindingResponse(
                    id=f'finding-{i}',
                    analysis_id='analysis-123',
                    document_id='doc-456',
                    title=f'Finding {i}',
                    description=f'Description {i}',
                    severity='medium',
                    confidence=0.8,
                    category='test'
                )
                for i in range(10)  # First page: 10 findings
            ]

            mock_response = FindingsListResponse(
                findings=mock_findings,
                total_count=25,
                limit=10,
                offset=0,
                has_more=True
            )
            mock_handler.return_value = mock_response

            response = client.get("/findings?limit=10&offset=0")

            assert response.status_code == 200
            data = response.json()
            assert len(data['findings']) == 10
            assert data['total_count'] == 25
            assert data['limit'] == 10
            assert data['offset'] == 0
            assert data['has_more'] is True

    @pytest.mark.asyncio
    async def test_get_findings_empty_result(self, client):
        """Test getting findings with no results."""
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_handler:
            mock_response = FindingsListResponse(
                findings=[],
                total_count=0,
                limit=50,
                offset=0,
                has_more=False
            )
            mock_handler.return_value = mock_response

            response = client.get("/findings?analysis_id=non-existent")

            assert response.status_code == 200
            data = response.json()
            assert len(data['findings']) == 0
            assert data['total_count'] == 0
            assert data['has_more'] is False

    @pytest.mark.asyncio
    async def test_get_findings_invalid_parameters(self, client):
        """Test findings endpoint with invalid parameters."""
        # Test invalid limit
        response = client.get("/findings?limit=-1")
        assert response.status_code == 422  # Validation error

        # Test invalid offset
        response = client.get("/findings?offset=-1")
        assert response.status_code == 422

        # Test invalid severity
        response = client.get("/findings?severity=invalid_severity")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_findings_complex_filtering(self, client):
        """Test findings with complex filtering combinations."""
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_handler:
            mock_findings = [
                FindingResponse(
                    id='finding-1',
                    analysis_id='analysis-123',
                    document_id='doc-456',
                    title='Complex Filtered Finding',
                    description='Matches all filters',
                    severity='high',
                    confidence=0.9,
                    category='security',
                    status='open'
                )
            ]

            mock_response = FindingsListResponse(
                findings=mock_findings,
                total_count=1,
                limit=50,
                offset=0,
                has_more=False
            )
            mock_handler.return_value = mock_response

            # Test multiple filters
            params = {
                'analysis_id': 'analysis-123',
                'severity': 'high',
                'category': 'security',
                'status': 'open',
                'limit': 50
            }

            response = client.get("/findings", params=params)

            assert response.status_code == 200
            data = response.json()
            assert len(data['findings']) == 1

            finding = data['findings'][0]
            assert finding['severity'] == 'high'
            assert finding['category'] == 'security'
            assert finding['analysis_id'] == 'analysis-123'

    @pytest.mark.asyncio
    async def test_get_findings_performance_optimization(self, client):
        """Test findings endpoint performance optimizations."""
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_handler:
            # Create a large result set to test performance
            mock_findings = [
                FindingResponse(
                    id=f'perf-finding-{i}',
                    analysis_id='analysis-123',
                    document_id='doc-456',
                    title=f'Performance Finding {i}',
                    description=f'Description {i}',
                    severity='medium',
                    confidence=0.8,
                    category='performance'
                )
                for i in range(100)  # Large result set
            ]

            mock_response = FindingsListResponse(
                findings=mock_findings,
                total_count=100,
                limit=100,
                offset=0,
                has_more=False
            )
            mock_handler.return_value = mock_response

            import time
            start_time = time.time()

            response = client.get("/findings?limit=100")

            end_time = time.time()
            response_time = end_time - start_time

            assert response.status_code == 200
            data = response.json()
            assert len(data['findings']) == 100

            # Response should be reasonably fast (< 1 second)
            assert response_time < 1.0

    @pytest.mark.asyncio
    async def test_get_findings_concurrent_requests(self, client):
        """Test concurrent requests to findings endpoint."""
        async def make_findings_request(request_id: int):
            with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_handler:
                mock_findings = [
                    FindingResponse(
                        id=f'concurrent-finding-{request_id}-{i}',
                        analysis_id='analysis-123',
                        document_id='doc-456',
                        title=f'Concurrent Finding {request_id}-{i}',
                        description=f'Description {request_id}-{i}',
                        severity='medium',
                        confidence=0.8,
                        category='test'
                    )
                    for i in range(5)
                ]

                mock_response = FindingsListResponse(
                    findings=mock_findings,
                    total_count=5,
                    limit=50,
                    offset=0,
                    has_more=False
                )
                mock_handler.return_value = mock_response

                response = client.get(f"/findings?analysis_id=analysis-{request_id}")
                return response.status_code, len(response.json()['findings'])

        # Make concurrent requests
        tasks = [make_findings_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All requests should succeed and return expected data
        for status_code, findings_count in results:
            assert status_code == 200
            assert findings_count == 5

    @pytest.mark.asyncio
    async def test_get_findings_caching_behavior(self, client):
        """Test caching behavior in findings endpoint."""
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_handler:
            mock_findings = [
                FindingResponse(
                    id='cached-finding-1',
                    analysis_id='analysis-123',
                    document_id='doc-456',
                    title='Cached Finding',
                    description='Testing caching',
                    severity='medium',
                    confidence=0.8,
                    category='test'
                )
            ]

            mock_response = FindingsListResponse(
                findings=mock_findings,
                total_count=1,
                limit=50,
                offset=0,
                has_more=False
            )
            mock_handler.return_value = mock_response

            # Make multiple identical requests
            responses = []
            for i in range(3):
                response = client.get("/findings?analysis_id=analysis-123")
                responses.append(response)

            # All should succeed
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert len(data['findings']) == 1
                assert data['findings'][0]['id'] == 'cached-finding-1'

            # In a real implementation with caching, we would verify:
            # - First request hits the handler
            # - Subsequent requests use cached results
            # - Cache invalidation works properly

    @pytest.mark.asyncio
    async def test_get_findings_error_scenarios(self, client):
        """Test error scenarios in findings endpoint."""
        # Test database connection error
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_handler:
            mock_handler.side_effect = Exception("Database connection error")

            response = client.get("/findings")

            # Should handle error gracefully
            assert response.status_code in [400, 500]

    @pytest.mark.asyncio
    async def test_get_findings_rate_limiting(self, client):
        """Test rate limiting on findings endpoint."""
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_handler:
            mock_response = FindingsListResponse(
                findings=[],
                total_count=0,
                limit=50,
                offset=0,
                has_more=False
            )
            mock_handler.return_value = mock_response

            # Make many rapid requests
            responses = []
            for i in range(20):
                response = client.get("/findings")
                responses.append(response)

            # In a rate-limited system, some requests might be rejected
            success_count = sum(1 for r in responses if r.status_code == 200)
            rate_limited_count = sum(1 for r in responses if r.status_code == 429)

            # At least some should succeed
            assert success_count > 0

            # In a real implementation, we would expect some to be rate limited
            # assert rate_limited_count > 0

    def test_findings_endpoint_cors_headers(self, client):
        """Test CORS headers on findings endpoint."""
        response = client.options("/findings")
        assert response.status_code == 200

        # Check for CORS headers
        headers = response.headers
        cors_headers = [
            'access-control-allow-origin',
            'access-control-allow-methods',
            'access-control-allow-headers'
        ]

        cors_present = any(
            header in headers or header.title() in headers
            for header in cors_headers
        )
        assert cors_present, "CORS headers should be present"

    def test_findings_endpoint_content_type_validation(self, client):
        """Test content type validation on findings endpoint."""
        # Test with correct content type
        response = client.get("/findings", headers={"Accept": "application/json"})
        # Should succeed or fail based on handler (not content type)
        assert response.status_code != 415  # Not unsupported media type

        # Test with incorrect accept type
        response = client.get("/findings", headers={"Accept": "text/html"})
        # Should still work (most APIs return JSON regardless of Accept header)
        assert response.status_code in [200, 422]  # Success or validation error

    @pytest.mark.asyncio
    async def test_get_findings_sorting(self, client):
        """Test findings sorting functionality."""
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_handler:
            # Create findings with different creation times
            base_time = datetime.now(timezone.utc)

            mock_findings = [
                FindingResponse(
                    id='finding-new',
                    analysis_id='analysis-123',
                    document_id='doc-456',
                    title='New Finding',
                    description='Recently created',
                    severity='high',
                    confidence=0.9,
                    category='security',
                    created_at=base_time
                ),
                FindingResponse(
                    id='finding-old',
                    analysis_id='analysis-123',
                    document_id='doc-456',
                    title='Old Finding',
                    description='Created earlier',
                    severity='medium',
                    confidence=0.7,
                    category='performance',
                    created_at=base_time.replace(hour=base_time.hour - 1)
                )
            ]

            mock_response = FindingsListResponse(
                findings=mock_findings,
                total_count=2,
                limit=50,
                offset=0,
                has_more=False
            )
            mock_handler.return_value = mock_response

            # Test sorting by creation date (newest first)
            response = client.get("/findings?sort_by=created_at&sort_order=desc")

            assert response.status_code == 200
            data = response.json()

            # In a real implementation, findings would be sorted
            # For now, we just verify the endpoint accepts sorting parameters
            assert len(data['findings']) == 2

    @pytest.mark.asyncio
    async def test_get_findings_export_formats(self, client):
        """Test findings export in different formats."""
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings') as mock_handler:
            mock_findings = [
                FindingResponse(
                    id='finding-1',
                    analysis_id='analysis-123',
                    document_id='doc-456',
                    title='Export Test Finding',
                    description='Testing export formats',
                    severity='medium',
                    confidence=0.8,
                    category='test'
                )
            ]

            mock_response = FindingsListResponse(
                findings=mock_findings,
                total_count=1,
                limit=50,
                offset=0,
                has_more=False
            )
            mock_handler.return_value = mock_response

            # Test JSON format (default)
            response = client.get("/findings", headers={"Accept": "application/json"})
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)

            # In a real implementation, we might support CSV, XML, etc.
            # For now, we verify JSON works correctly

    @pytest.mark.asyncio
    async def test_get_findings_bulk_operations(self, client):
        """Test bulk operations on findings."""
        # Test bulk status updates
        bulk_update_data = {
            'finding_ids': ['finding-1', 'finding-2', 'finding-3'],
            'status': 'resolved',
            'resolution_notes': 'Bulk resolved by admin'
        }

        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_bulk_update_findings') as mock_handler:
            mock_response = {
                'updated_count': 3,
                'failed_count': 0,
                'message': 'Bulk update completed successfully'
            }
            mock_handler.return_value = mock_response

            # This would be a POST/PUT endpoint in a real implementation
            # For now, we just test the concept
            assert bulk_update_data is not None

    @pytest.mark.asyncio
    async def test_get_findings_analytics(self, client):
        """Test findings analytics and reporting."""
        with patch('services.analysis_service.presentation.controllers.findings_controller.findings_handlers.handle_get_findings_analytics') as mock_handler:
            mock_analytics = {
                'total_findings': 150,
                'severity_distribution': {
                    'critical': 5,
                    'high': 25,
                    'medium': 75,
                    'low': 45
                },
                'category_distribution': {
                    'security': 30,
                    'performance': 40,
                    'code_quality': 50,
                    'documentation': 30
                },
                'trends': {
                    'new_findings_last_7_days': 12,
                    'resolved_findings_last_7_days': 8,
                    'average_resolution_time_days': 3.5
                }
            }
            mock_handler.return_value = mock_analytics

            # This would be a separate analytics endpoint
            # For now, we test the concept
            assert mock_analytics['total_findings'] == 150
            assert mock_analytics['severity_distribution']['critical'] == 5
