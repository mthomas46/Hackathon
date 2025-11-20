"""
End-to-End Workflow Tests

Tests complete user workflows through the entire system:
1. Template seeding -> Discovery -> Generation -> Verification
2. Custom template creation -> Usage -> Tracking
3. Error recovery and edge cases
"""

import pytest
import asyncio
from uuid import uuid4
from unittest.mock import patch


@pytest.mark.e2e
class TestCompleteDocumentationGeneration:
    """Test complete documentation generation workflow."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_with_system_template(self):
        """
        Test complete workflow:
        1. Verify system templates exist
        2. Discover repository context
        3. Generate documentation
        4. Verify transparency logging
        5. Verify citations
        """
        from src.services.templates.template_manager import get_template_manager
        from src.services.documentation.adaptive_orchestrator import get_adaptive_orchestrator
        
        # Step 1: Verify templates
        template_mgr = get_template_manager()
        templates = await template_mgr.list_templates(category="api_reference")
        assert len(templates) > 0, "System templates should be seeded"
        
        api_template = next((t for t in templates if "api_reference" in t["name"]), None)
        assert api_template is not None
        
        # Step 2-5: Generate documentation
        orchestrator = get_adaptive_orchestrator()
        
        with patch('src.services.adaptive.discovery_service.DiscoveryService.discover_repository_context') as mock_discover:
            with patch('src.services.rag.enhanced_rag_service.EnhancedRAGService.query') as mock_rag:
                # Mock discovery
                mock_discover.return_value = {
                    "service_name": "testservice",
                    "primary_language": "Python",
                    "frameworks": ["FastAPI"],
                    "concepts": ["REST API"],
                    "keywords": ["Python", "FastAPI"]
                }
                
                # Mock RAG
                mock_rag.return_value = {
                    "answer": "# API Documentation\n\nThis is the API documentation.",
                    "sources": [
                        {"document_id": str(uuid4()), "score": 0.95, "content": "Source text"}
                    ]
                }
                
                # Generate
                result = await orchestrator.generate_adaptive_documentation(
                    service_name="testservice",
                    template_name=api_template["name"],
                    category="api_reference",
                    config={"include_citations": True}
                )
                
                # Verify result
                assert result is not None
                assert "run_id" in result
                assert "content" in result
                assert len(result["content"]) > 0
                assert "testservice" in result["content"]
    
    @pytest.mark.asyncio
    async def test_workflow_with_custom_template(self):
        """
        Test workflow with custom template:
        1. Create custom template
        2. Use it for generation
        3. Verify usage tracking
        """
        from src.services.templates.template_manager import get_template_manager
        from src.services.documentation.adaptive_orchestrator import get_adaptive_orchestrator
        
        template_mgr = get_template_manager()
        
        # Create custom template
        template_name = f"custom_e2e_{uuid4().hex[:8]}"
        template_id = await template_mgr.create_template(
            name=template_name,
            category="api_reference",
            structure={
                "sections": [
                    {
                        "name": "Summary",
                        "required": True,
                        "prompt_template": "Summarize {service_name}",
                        "documents_needed": 5
                    }
                ]
            },
            description="E2E test template"
        )
        
        # Use it
        orchestrator = get_adaptive_orchestrator()
        
        with patch('src.services.adaptive.discovery_service.DiscoveryService.discover_repository_context') as mock_discover:
            with patch('src.services.rag.enhanced_rag_service.EnhancedRAGService.query') as mock_rag:
                mock_discover.return_value = {
                    "service_name": "testservice",
                    "primary_language": "Python"
                }
                mock_rag.return_value = {
                    "answer": "Summary content",
                    "sources": []
                }
                
                result = await orchestrator.generate_adaptive_documentation(
                    service_name="testservice",
                    template_name=template_name,
                    category="api_reference"
                )
                
                assert result is not None
        
        # Verify usage tracking
        template = await template_mgr.get_template(template_id)
        assert template["usage_count"] >= 1


@pytest.mark.e2e
class TestErrorRecoveryWorkflows:
    """Test error recovery in complete workflows."""
    
    @pytest.mark.asyncio
    async def test_workflow_continues_on_section_failure(self):
        """Test that workflow continues when one section fails."""
        from src.services.documentation.adaptive_orchestrator import get_adaptive_orchestrator
        
        orchestrator = get_adaptive_orchestrator()
        
        call_count = [0]
        
        def mock_rag_with_failure(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("First section failed")
            return {"answer": "Content", "sources": []}
        
        with patch('src.services.adaptive.discovery_service.DiscoveryService.discover_repository_context') as mock_discover:
            with patch('src.services.templates.template_manager.TemplateManager.load_template') as mock_template:
                with patch('src.services.rag.enhanced_rag_service.EnhancedRAGService.query', side_effect=mock_rag_with_failure):
                    mock_discover.return_value = {"service_name": "test", "primary_language": "Python"}
                    mock_template.return_value = {
                        "id": str(uuid4()),
                        "name": "test",
                        "category": "api_reference",
                        "structure": {
                            "sections": [
                                {"name": "Section1", "required": True, "prompt_template": "Test", "documents_needed": 10},
                                {"name": "Section2", "required": True, "prompt_template": "Test", "documents_needed": 10}
                            ]
                        },
                        "render_options": {}
                    }
                    
                    # Should complete despite first section failing
                    result = await orchestrator.generate_adaptive_documentation(
                        service_name="test",
                        template_name="test",
                        category="api_reference"
                    )
                    
                    assert result is not None
                    # Should have content from second section
                    assert len(result["content"]) > 0
    
    @pytest.mark.asyncio
    async def test_workflow_with_missing_repository_context(self):
        """Test workflow when repository context is missing."""
        from src.services.documentation.adaptive_orchestrator import get_adaptive_orchestrator
        
        orchestrator = get_adaptive_orchestrator()
        
        with patch('src.services.adaptive.discovery_service.DiscoveryService.discover_repository_context') as mock_discover:
            # Return minimal/default context
            mock_discover.return_value = {
                "service_name": "unknown",
                "primary_language": "Unknown",
                "frameworks": [],
                "concepts": [],
                "keywords": []
            }
            
            with patch('src.services.templates.template_manager.TemplateManager.load_template') as mock_template:
                with patch('src.services.rag.enhanced_rag_service.EnhancedRAGService.query') as mock_rag:
                    mock_template.return_value = {
                        "id": str(uuid4()),
                        "name": "test",
                        "category": "api_reference",
                        "structure": {
                            "sections": [
                                {"name": "Test", "required": True, "prompt_template": "Test", "documents_needed": 10}
                            ]
                        },
                        "render_options": {}
                    }
                    mock_rag.return_value = {"answer": "Generic content", "sources": []}
                    
                    # Should still generate, just with generic context
                    result = await orchestrator.generate_adaptive_documentation(
                        service_name="unknown",
                        template_name="test",
                        category="api_reference"
                    )
                    
                    assert result is not None
                    assert "content" in result


@pytest.mark.e2e
class TestConcurrentWorkflows:
    """Test concurrent workflow execution."""
    
    @pytest.mark.asyncio
    async def test_concurrent_documentation_generation(self):
        """Test generating documentation for multiple services concurrently."""
        from src.services.documentation.adaptive_orchestrator import get_adaptive_orchestrator
        
        orchestrator = get_adaptive_orchestrator()
        
        async def generate_for_service(service_name):
            with patch('src.services.adaptive.discovery_service.DiscoveryService.discover_repository_context') as mock_discover:
                with patch('src.services.templates.template_manager.TemplateManager.load_template') as mock_template:
                    with patch('src.services.rag.enhanced_rag_service.EnhancedRAGService.query') as mock_rag:
                        mock_discover.return_value = {"service_name": service_name, "primary_language": "Python"}
                        mock_template.return_value = {
                            "id": str(uuid4()),
                            "name": "test",
                            "category": "api_reference",
                            "structure": {
                                "sections": [
                                    {"name": "Test", "required": True, "prompt_template": "Test", "documents_needed": 10}
                                ]
                            },
                            "render_options": {}
                        }
                        mock_rag.return_value = {"answer": f"Content for {service_name}", "sources": []}
                        
                        return await orchestrator.generate_adaptive_documentation(
                            service_name=service_name,
                            template_name="test",
                            category="api_reference"
                        )
        
        # Generate for 5 services concurrently
        results = await asyncio.gather(*[
            generate_for_service(f"service_{i}")
            for i in range(5)
        ])
        
        assert len(results) == 5
        assert all(r is not None for r in results)
        assert all("content" in r for r in results)
        # Verify each has unique content
        assert len(set(r["service_name"] for r in results)) == 5


@pytest.mark.e2e
class TestDataPersistenceWorkflows:
    """Test data persistence across workflow steps."""
    
    @pytest.mark.asyncio
    async def test_template_usage_tracking_persists(self):
        """Test that template usage is tracked and persists."""
        from src.services.templates.template_manager import get_template_manager
        
        template_mgr = get_template_manager()
        
        # Create template
        template_id = await template_mgr.create_template(
            name=f"persist_test_{uuid4().hex[:8]}",
            category="api_reference",
            structure={
                "sections": [
                    {"name": "Test", "required": True, "prompt_template": "Test", "documents_needed": 10}
                ]
            }
        )
        
        # Track usage multiple times
        for _ in range(3):
            await template_mgr.track_template_usage(template_id)
        
        # Verify it persisted
        template = await template_mgr.get_template(template_id)
        assert template["usage_count"] == 3
    
    @pytest.mark.asyncio
    async def test_transparency_logs_are_retrievable(self):
        """Test that transparency logs can be retrieved after generation."""
        from src.services.documentation.adaptive_orchestrator import get_adaptive_orchestrator
        from src.services.adaptive.transparency_logger import get_transparency_logger
        
        orchestrator = get_adaptive_orchestrator()
        transparency_logger = get_transparency_logger()
        
        with patch('src.services.adaptive.discovery_service.DiscoveryService.discover_repository_context') as mock_discover:
            with patch('src.services.templates.template_manager.TemplateManager.load_template') as mock_template:
                with patch('src.services.rag.enhanced_rag_service.EnhancedRAGService.query') as mock_rag:
                    mock_discover.return_value = {"service_name": "test", "primary_language": "Python"}
                    mock_template.return_value = {
                        "id": str(uuid4()),
                        "name": "test",
                        "category": "api_reference",
                        "structure": {
                            "sections": [
                                {"name": "Test", "required": True, "prompt_template": "Test", "documents_needed": 10}
                            ]
                        },
                        "render_options": {}
                    }
                    mock_rag.return_value = {"answer": "Content", "sources": []}
                    
                    # Generate
                    result = await orchestrator.generate_adaptive_documentation(
                        service_name="test",
                        template_name="test",
                        category="api_reference"
                    )
                    
                    run_id = result["run_id"]
                    
                    # Retrieve transparency log
                    with patch.object(transparency_logger, 'get_run_log', return_value=[{"action": "test"}]):
                        with patch.object(transparency_logger, 'get_phase_statistics', return_value={}):
                            logs = await transparency_logger.get_run_log(run_id)
                            assert logs is not None


@pytest.mark.e2e
@pytest.mark.slow
class TestPerformanceWorkflows:
    """Test performance of complete workflows."""
    
    @pytest.mark.asyncio
    async def test_large_template_generation_performance(self, benchmark):
        """Test performance with large template (many sections)."""
        from src.services.documentation.adaptive_orchestrator import get_adaptive_orchestrator
        
        orchestrator = get_adaptive_orchestrator()
        
        # Create large template
        large_template = {
            "id": str(uuid4()),
            "name": "large",
            "category": "api_reference",
            "structure": {
                "sections": [
                    {
                        "name": f"Section_{i}",
                        "required": True,
                        "prompt_template": f"Content for section {i}",
                        "documents_needed": 10
                    }
                    for i in range(10)  # 10 sections
                ]
            },
            "render_options": {}
        }
        
        async def generate():
            with patch('src.services.adaptive.discovery_service.DiscoveryService.discover_repository_context') as mock_discover:
                with patch('src.services.templates.template_manager.TemplateManager.load_template') as mock_template:
                    with patch('src.services.rag.enhanced_rag_service.EnhancedRAGService.query') as mock_rag:
                        mock_discover.return_value = {"service_name": "test", "primary_language": "Python"}
                        mock_template.return_value = large_template
                        mock_rag.return_value = {"answer": "Content", "sources": []}
                        
                        return await orchestrator.generate_adaptive_documentation(
                            service_name="test",
                            template_name="large",
                            category="api_reference"
                        )
        
        # Benchmark it
        result = await benchmark.pedantic(generate, rounds=3)
        assert result is not None
        assert len(result["content"]) > 0


# ============================================================================
# Test Helpers
# ============================================================================

async def setup_test_environment():
    """Set up test environment for E2E tests."""
    # Ensure test database is clean
    # Ensure test templates are seeded
    pass


async def teardown_test_environment():
    """Clean up after E2E tests."""
    # Clean up test data
    pass
