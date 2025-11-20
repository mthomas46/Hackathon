"""
Functional tests for Adaptive Documentation API endpoints

Tests all API endpoints for:
- Template Management
- Adaptive Documentation Generation
- Transparency & Citations
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from uuid import uuid4

from src.api.app import create_app


class TestTemplateAPI:
    """Functional tests for Template Management API."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def valid_template_payload(self):
        """Valid template creation payload."""
        return {
            "name": f"test_api_template_{uuid4().hex[:8]}",
            "category": "api_reference",
            "structure": {
                "sections": [
                    {
                        "name": "Overview",
                        "required": True,
                        "prompt_template": "What is {service_name}?",
                        "documents_needed": 10
                    }
                ]
            },
            "description": "Test API template",
            "target_framework": "scala_play",
            "target_audience": "developers"
        }
    
    # ============================================================================
    # Template Creation Tests
    # ============================================================================
    
    def test_create_template_success(self, client, valid_template_payload):
        """Test POST /api/v1/templates/ - successful creation."""
        response = client.post(
            "/api/v1/templates/",
            json=valid_template_payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "template_id" in data
        assert "message" in data
    
    def test_create_template_invalid_category(self, client, valid_template_payload):
        """Test POST /api/v1/templates/ - invalid category."""
        invalid_payload = {
            **valid_template_payload,
            "category": "invalid_category"
        }
        
        response = client.post(
            "/api/v1/templates/",
            json=invalid_payload
        )
        
        assert response.status_code in [400, 422]
    
    def test_create_template_missing_required_fields(self, client):
        """Test POST /api/v1/templates/ - missing required fields."""
        incomplete_payload = {
            "name": "test",
            # Missing category and structure
        }
        
        response = client.post(
            "/api/v1/templates/",
            json=incomplete_payload
        )
        
        assert response.status_code == 422  # Validation error
    
    # ============================================================================
    # Template Listing Tests
    # ============================================================================
    
    def test_list_templates(self, client):
        """Test GET /api/v1/templates/ - list all templates."""
        response = client.get("/api/v1/templates/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the 3 system templates
        assert len(data) >= 3
    
    def test_list_templates_by_category(self, client):
        """Test GET /api/v1/templates/category/{category}."""
        response = client.get("/api/v1/templates/category/api_reference")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all(t["category"] == "api_reference" for t in data)
    
    # ============================================================================
    # Template Retrieval Tests
    # ============================================================================
    
    def test_get_template_by_id(self, client, valid_template_payload):
        """Test GET /api/v1/templates/{template_id}."""
        # First create a template
        create_response = client.post(
            "/api/v1/templates/",
            json=valid_template_payload
        )
        template_id = create_response.json()["template_id"]
        
        # Then retrieve it
        response = client.get(f"/api/v1/templates/{template_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert "structure" in data
    
    def test_get_template_not_found(self, client):
        """Test GET /api/v1/templates/{template_id} - not found."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/templates/{fake_id}")
        
        assert response.status_code == 404
    
    # ============================================================================
    # Template Update Tests
    # ============================================================================
    
    def test_update_template(self, client, valid_template_payload):
        """Test PUT /api/v1/templates/{template_id}."""
        # Create template
        create_response = client.post(
            "/api/v1/templates/",
            json=valid_template_payload
        )
        template_id = create_response.json()["template_id"]
        
        # Update it
        update_payload = {
            "description": "Updated description",
            "target_audience": "operators"
        }
        
        response = client.put(
            f"/api/v1/templates/{template_id}",
            json=update_payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Template updated successfully"
    
    # ============================================================================
    # Template Validation Tests
    # ============================================================================
    
    def test_validate_content(self, client, valid_template_payload):
        """Test POST /api/v1/templates/{template_id}/validate."""
        # Create template
        create_response = client.post(
            "/api/v1/templates/",
            json=valid_template_payload
        )
        template_id = create_response.json()["template_id"]
        
        # Validate content
        content_payload = {
            "section_name": "Overview",
            "content": "# Overview\n\nThis is the overview section."
        }
        
        response = client.post(
            f"/api/v1/templates/{template_id}/validate",
            json=content_payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "adherence_score" in data


class TestAdaptiveDocumentationAPI:
    """Functional tests for Adaptive Documentation API."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    # ============================================================================
    # Context Preview Tests
    # ============================================================================
    
    def test_preview_generation_context(self, client):
        """Test GET /api/v1/documentation/adaptive/preview/{service_name}."""
        with patch('src.services.adaptive.discovery_service.DiscoveryService.discover_repository_context',
                  return_value={"service_name": "adminservice", "primary_language": "Scala"}):
            
            response = client.get(
                "/api/v1/documentation/adaptive/preview/adminservice",
                params={
                    "template_name": "api_reference_openapi_style",
                    "category": "api_reference"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "service_name" in data
            assert "context" in data
            assert "template" in data
    
    def test_preview_template_not_found(self, client):
        """Test preview with non-existent template."""
        response = client.get(
            "/api/v1/documentation/adaptive/preview/test",
            params={
                "template_name": "nonexistent",
                "category": "api_reference"
            }
        )
        
        assert response.status_code == 404
    
    # ============================================================================
    # Documentation Generation Tests
    # ============================================================================
    
    def test_generate_documentation_minimal(self, client):
        """Test POST /api/v1/documentation/adaptive/generate - minimal config."""
        payload = {
            "service_name": "adminservice",
            "template_name": "api_reference_openapi_style",
            "category": "api_reference"
        }
        
        # Mock all service dependencies
        with patch('src.services.documentation.adaptive_orchestrator.AdaptiveDocumentationOrchestrator.generate_adaptive_documentation',
                  return_value={
                      "run_id": str(uuid4()),
                      "service_name": "adminservice",
                      "content": "# Documentation",
                      "metadata": {},
                      "transparency_report_url": "/api/v1/transparency/...",
                      "citations": []
                  }):
            
            response = client.post(
                "/api/v1/documentation/adaptive/generate",
                json=payload
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "run_id" in data
            assert "content" in data
            assert data["service_name"] == "adminservice"
    
    def test_generate_documentation_full_config(self, client):
        """Test POST /api/v1/documentation/adaptive/generate - full config."""
        payload = {
            "service_name": "adminservice",
            "template_name": "api_reference_openapi_style",
            "category": "api_reference",
            "include_citations": True,
            "citation_style": "endnotes",
            "transparency_mode": "verbose",
            "include_optional_sections": True
        }
        
        with patch('src.services.documentation.adaptive_orchestrator.AdaptiveDocumentationOrchestrator.generate_adaptive_documentation',
                  return_value={
                      "run_id": str(uuid4()),
                      "service_name": "adminservice",
                      "content": "# Documentation\n\n## Sources",
                      "metadata": {"citations_added": 10},
                      "transparency_report_url": "/api/v1/transparency/...",
                      "citations": []
                  }):
            
            response = client.post(
                "/api/v1/documentation/adaptive/generate",
                json=payload
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "run_id" in data
            assert data["metadata"]["citations_added"] > 0
    
    def test_generate_documentation_invalid_service(self, client):
        """Test generation with invalid service name."""
        payload = {
            "service_name": "",  # Empty service name
            "template_name": "api_reference_openapi_style",
            "category": "api_reference"
        }
        
        response = client.post(
            "/api/v1/documentation/adaptive/generate",
            json=payload
        )
        
        assert response.status_code in [400, 422]
    
    # ============================================================================
    # Transparency Report Tests
    # ============================================================================
    
    def test_get_transparency_report_json(self, client):
        """Test GET /api/v1/documentation/adaptive/transparency/{run_id}."""
        run_id = uuid4()
        
        with patch('src.services.adaptive.transparency_logger.TransparencyLogger.get_run_log',
                  return_value=[{"action": "test", "timestamp": "2025-01-01"}]):
            with patch('src.services.adaptive.transparency_logger.TransparencyLogger.get_phase_statistics',
                      return_value={"discovery": {"total_actions": 1}}):
                
                response = client.get(
                    f"/api/v1/documentation/adaptive/transparency/{run_id}",
                    params={"format": "json"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "log_entries" in data
                assert "statistics" in data
    
    def test_get_transparency_report_markdown(self, client):
        """Test transparency report in markdown format."""
        run_id = uuid4()
        
        with patch('src.services.adaptive.transparency_logger.TransparencyLogger.format_transparency_report',
                  return_value="# Transparency Report\n\nDetails..."):
            
            response = client.get(
                f"/api/v1/documentation/adaptive/transparency/{run_id}",
                params={"format": "markdown"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["format"] == "markdown"
            assert "content" in data
    
    def test_get_failed_actions(self, client):
        """Test GET /api/v1/documentation/adaptive/transparency/{run_id}/failed."""
        run_id = uuid4()
        
        with patch('src.services.adaptive.transparency_logger.TransparencyLogger.get_failed_actions',
                  return_value=[{"action": "generation", "error": "Test error"}]):
            
            response = client.get(
                f"/api/v1/documentation/adaptive/transparency/{run_id}/failed"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "failed_count" in data
            assert "failed_actions" in data
    
    # ============================================================================
    # Citation Tests
    # ============================================================================
    
    def test_get_artifact_citations(self, client):
        """Test GET /api/v1/documentation/adaptive/citations/{artifact_id}."""
        artifact_id = uuid4()
        
        with patch('src.services.adaptive.citation_manager.CitationManager.get_citations_for_artifact',
                  return_value=[{"document_id": str(uuid4()), "relevance_score": 0.9}]):
            with patch('src.services.adaptive.citation_manager.CitationManager.get_citation_statistics',
                      return_value={"total_citations": 5, "avg_relevance": 0.85}):
                
                response = client.get(
                    f"/api/v1/documentation/adaptive/citations/{artifact_id}"
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "citations" in data
                assert "statistics" in data
    
    def test_verify_citations(self, client):
        """Test GET /api/v1/documentation/adaptive/citations/{artifact_id}/verify."""
        artifact_id = uuid4()
        
        with patch('src.services.adaptive.citation_manager.CitationManager.verify_citations',
                  return_value={
                      "valid": True,
                      "total_citations": 10,
                      "low_relevance_count": 1,
                      "missing_sections": []
                  }):
            
            response = client.get(
                f"/api/v1/documentation/adaptive/citations/{artifact_id}/verify",
                params={"min_relevance": 0.7}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "valid" in data
            assert "total_citations" in data


class TestAPIErrorHandling:
    """Test API error handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_404_for_invalid_endpoint(self, client):
        """Test 404 for non-existent endpoint."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_405_for_wrong_method(self, client):
        """Test 405 for unsupported HTTP method."""
        response = client.post("/api/v1/templates/nonexistent")
        # Should be 404 (not found) or 405 (method not allowed)
        assert response.status_code in [404, 405]
    
    def test_422_for_invalid_json(self, client):
        """Test 422 for malformed request body."""
        response = client.post(
            "/api/v1/templates/",
            json={"invalid": "structure"}  # Missing required fields
        )
        assert response.status_code == 422


class TestAPIAuthentication:
    """Test API authentication/authorization (if implemented)."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    @pytest.mark.skip(reason="Authentication not yet implemented")
    def test_requires_authentication(self, client):
        """Test that protected endpoints require authentication."""
        response = client.post(
            "/api/v1/templates/",
            json={}
        )
        # Would check for 401 if auth is implemented
        pass


class TestAPICORS:
    """Test CORS configuration (if needed)."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/v1/templates/")
        # Check if CORS headers are configured
        # This depends on your CORS setup
        pass

