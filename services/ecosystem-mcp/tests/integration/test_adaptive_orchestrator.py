"""
Integration tests for Adaptive Documentation Orchestrator

Tests the complete integration of all Phase 1-4 components:
- Template Manager
- Discovery Service
- Prompt Tracker
- Citation Manager
- Transparency Logger
- RAG Service
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from src.services.documentation.adaptive_orchestrator import (
    AdaptiveDocumentationOrchestrator,
    get_adaptive_orchestrator
)


class TestAdaptiveOrchestrator:
    """Integration tests for Adaptive Documentation Orchestrator."""
    
    @pytest.fixture
    async def orchestrator(self):
        """Get orchestrator instance."""
        return get_adaptive_orchestrator()
    
    @pytest.fixture
    def mock_context(self):
        """Mock repository context."""
        return {
            "service_name": "adminservice",
            "primary_language": "Scala",
            "primary_framework": "Play Framework",
            "languages": {"Scala": 245},
            "frameworks": ["Play Framework"],
            "concepts": ["REST API", "MVC", "PostgreSQL"],
            "keywords": ["Scala", "Play", "Akka"],
            "framework_guidance": {
                "recommended_sections": ["Routes", "Controllers"],
                "patterns_to_find": ["Action composition"],
                "terminology": {"controller": "HTTP request handler"}
            }
        }
    
    @pytest.fixture
    def mock_template(self):
        """Mock template."""
        return {
            "id": str(uuid4()),
            "name": "test_template",
            "category": "api_reference",
            "structure": {
                "sections": [
                    {
                        "name": "Overview",
                        "required": True,
                        "prompt_template": "What is {service_name}?",
                        "documents_needed": 10,
                        "subsections": []
                    },
                    {
                        "name": "API Endpoints",
                        "required": True,
                        "prompt_template": "List API endpoints in {service_name}",
                        "documents_needed": 20,
                        "subsections": []
                    }
                ]
            },
            "render_options": {
                "include_toc": True
            }
        }
    
    # ============================================================================
    # Discovery Phase Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_discovery_phase(self, orchestrator, mock_context):
        """Test discovery phase integration."""
        run_id = uuid4()
        
        with patch.object(orchestrator.discovery_service, 'discover_repository_context',
                         return_value=mock_context):
            with patch.object(orchestrator.discovery_service, 'get_framework_specific_guidance',
                             return_value=mock_context["framework_guidance"]):
                
                context = await orchestrator._discovery_phase(run_id, "adminservice")
                
                assert context is not None
                assert context["service_name"] == "adminservice"
                assert "frameworks" in context
                assert "framework_guidance" in context
    
    # ============================================================================
    # Generation Phase Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_generation_phase_single_section(self, orchestrator, mock_template, mock_context):
        """Test generating a single section."""
        run_id = uuid4()
        
        # Mock RAG response
        mock_rag_response = {
            "answer": "# Overview\n\nThis is a REST API service built with Play Framework.",
            "sources": [
                {"document_id": str(uuid4()), "score": 0.95, "content": "API overview text"}
            ]
        }
        
        # Mock all dependencies
        with patch.object(orchestrator.rag_service, 'query', return_value=mock_rag_response):
            with patch.object(orchestrator.prompt_tracker, 'track_prompt_execution',
                             return_value=uuid4()):
                with patch.object(orchestrator.template_manager, 'validate_generated_content',
                                 return_value={"valid": True, "adherence_score": 0.9}):
                    with patch.object(orchestrator.template_manager, 'render_section',
                                     return_value="## Overview\n\nRendered content"):
                        
                        sections = await orchestrator._generation_phase(
                            run_id=run_id,
                            template=mock_template,
                            context=mock_context,
                            service_name="adminservice",
                            config={}
                        )
                        
                        assert len(sections) == 2  # Two sections in mock template
                        assert all("name" in s for s in sections)
                        assert all("content" in s for s in sections)
    
    # ============================================================================
    # Assembly Phase Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_assembly_phase_with_citations(self, orchestrator, mock_template, mock_context):
        """Test assembling documentation with citations."""
        run_id = uuid4()
        
        sections = [
            {
                "name": "Overview",
                "content": "# Overview\n\nService overview.",
                "validation": {"valid": True},
                "sources": [
                    {
                        "document_id": str(uuid4()),
                        "relevance_score": 0.95,
                        "content": "Source text"
                    }
                ]
            }
        ]
        
        documentation = await orchestrator._assembly_phase(
            run_id=run_id,
            template=mock_template,
            sections=sections,
            context=mock_context,
            config={"include_citations": True, "citation_style": "endnotes"}
        )
        
        assert "content" in documentation
        assert "citation_count" in documentation
        assert documentation["citation_count"] > 0
        assert "Sources & References" in documentation["content"]
    
    @pytest.mark.asyncio
    async def test_assembly_phase_without_citations(self, orchestrator, mock_template, mock_context):
        """Test assembling documentation without citations."""
        run_id = uuid4()
        
        sections = [
            {
                "name": "Overview",
                "content": "# Overview\n\nService overview.",
                "validation": {"valid": True},
                "sources": []
            }
        ]
        
        documentation = await orchestrator._assembly_phase(
            run_id=run_id,
            template=mock_template,
            sections=sections,
            context=mock_context,
            config={"include_citations": False}
        )
        
        assert "content" in documentation
        assert documentation["citation_count"] == 0
        assert "Sources & References" not in documentation["content"]
    
    # ============================================================================
    # End-to-End Generation Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_generate_adaptive_documentation_success(self, orchestrator, mock_context, mock_template):
        """Test complete adaptive documentation generation."""
        # Mock all service calls
        with patch.object(orchestrator.discovery_service, 'discover_repository_context',
                         return_value=mock_context):
            with patch.object(orchestrator.discovery_service, 'get_framework_specific_guidance',
                             return_value={}):
                with patch.object(orchestrator.template_manager, 'load_template',
                                 return_value=mock_template):
                    with patch.object(orchestrator.rag_service, 'query',
                                     return_value={"answer": "Test content", "sources": []}):
                        with patch.object(orchestrator.prompt_tracker, 'track_prompt_execution',
                                         return_value=uuid4()):
                            with patch.object(orchestrator.template_manager, 'validate_generated_content',
                                             return_value={"valid": True, "adherence_score": 0.9}):
                                with patch.object(orchestrator.template_manager, 'render_section',
                                                 return_value="Rendered"):
                                    
                                    result = await orchestrator.generate_adaptive_documentation(
                                        service_name="adminservice",
                                        template_name="test_template",
                                        category="api_reference",
                                        config={"include_citations": True}
                                    )
                                    
                                    assert result is not None
                                    assert "run_id" in result
                                    assert "content" in result
                                    assert "metadata" in result
                                    assert result["service_name"] == "adminservice"
    
    @pytest.mark.asyncio
    async def test_generate_documentation_with_optional_sections(self, orchestrator, mock_context):
        """Test generation with optional sections enabled."""
        template_with_optional = {
            **orchestrator, **{
                "structure": {
                    "sections": [
                        {
                            "name": "Required",
                            "required": True,
                            "prompt_template": "Test",
                            "documents_needed": 10
                        },
                        {
                            "name": "Optional",
                            "required": False,
                            "prompt_template": "Test",
                            "documents_needed": 5
                        }
                    ]
                }
            }
        }
        
        with patch.object(orchestrator.discovery_service, 'discover_repository_context',
                         return_value=mock_context):
            with patch.object(orchestrator.template_manager, 'load_template',
                             return_value=template_with_optional):
                with patch.object(orchestrator.rag_service, 'query',
                                 return_value={"answer": "Content", "sources": []}):
                    with patch.object(orchestrator.prompt_tracker, 'track_prompt_execution',
                                     return_value=uuid4()):
                        with patch.object(orchestrator.template_manager, 'validate_generated_content',
                                         return_value={"valid": True, "adherence_score": 0.9}):
                            with patch.object(orchestrator.template_manager, 'render_section',
                                             return_value="Rendered"):
                                
                                # Test with optional sections included
                                result = await orchestrator.generate_adaptive_documentation(
                                    service_name="test",
                                    template_name="test",
                                    category="api_reference",
                                    config={"include_optional_sections": True}
                                )
                                
                                # Should generate more content
                                assert result is not None
    
    # ============================================================================
    # Error Handling Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_handles_discovery_failure(self, orchestrator):
        """Test orchestrator handles discovery failures gracefully."""
        with patch.object(orchestrator.discovery_service, 'discover_repository_context',
                         side_effect=Exception("Discovery failed")):
            with pytest.raises(Exception):
                await orchestrator.generate_adaptive_documentation(
                    service_name="test",
                    template_name="test",
                    category="api_reference"
                )
    
    @pytest.mark.asyncio
    async def test_handles_template_not_found(self, orchestrator, mock_context):
        """Test orchestrator handles missing template."""
        with patch.object(orchestrator.discovery_service, 'discover_repository_context',
                         return_value=mock_context):
            with patch.object(orchestrator.template_manager, 'load_template',
                             side_effect=ValueError("Template not found")):
                with pytest.raises(ValueError, match="not found"):
                    await orchestrator.generate_adaptive_documentation(
                        service_name="test",
                        template_name="nonexistent",
                        category="api_reference"
                    )
    
    @pytest.mark.asyncio
    async def test_continues_on_section_failure(self, orchestrator, mock_context, mock_template):
        """Test that generation continues even if one section fails."""
        call_count = [0]
        
        def mock_query(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("First section failed")
            return {"answer": "Content", "sources": []}
        
        with patch.object(orchestrator.discovery_service, 'discover_repository_context',
                         return_value=mock_context):
            with patch.object(orchestrator.template_manager, 'load_template',
                             return_value=mock_template):
                with patch.object(orchestrator.rag_service, 'query',
                                 side_effect=mock_query):
                    with patch.object(orchestrator.prompt_tracker, 'track_prompt_execution',
                                     return_value=uuid4()):
                        with patch.object(orchestrator.template_manager, 'validate_generated_content',
                                         return_value={"valid": True, "adherence_score": 0.9}):
                            with patch.object(orchestrator.template_manager, 'render_section',
                                             return_value="Rendered"):
                                
                                result = await orchestrator.generate_adaptive_documentation(
                                    service_name="test",
                                    template_name="test",
                                    category="api_reference"
                                )
                                
                                # Should still complete with remaining sections
                                assert result is not None
                                assert "content" in result


class TestOrchestratorPromptBuilding:
    """Test prompt building with context enhancement."""
    
    @pytest.mark.asyncio
    async def test_build_prompt_basic(self):
        """Test basic prompt building."""
        orchestrator = get_adaptive_orchestrator()
        
        section = {
            "name": "Overview",
            "prompt_template": "Describe {service_name}"
        }
        context = {"service_name": "TestService"}
        
        prompt = await orchestrator._build_prompt(section, context, "TestService")
        
        assert "TestService" in prompt
        assert "Describe" in prompt
    
    @pytest.mark.asyncio
    async def test_build_prompt_with_framework_context(self):
        """Test prompt enhancement with framework context."""
        orchestrator = get_adaptive_orchestrator()
        
        section = {
            "name": "API",
            "prompt_template": "List API endpoints in {service_name}"
        }
        context = {
            "service_name": "TestService",
            "primary_framework": "Play Framework",
            "framework_guidance": {
                "patterns_to_find": ["Routes", "Controllers"]
            }
        }
        
        prompt = await orchestrator._build_prompt(section, context, "TestService")
        
        assert "TestService" in prompt
        assert "Framework-Specific Context" in prompt or "Play Framework" in prompt
    
    @pytest.mark.asyncio
    async def test_build_prompt_with_concepts(self):
        """Test prompt enhancement with discovered concepts."""
        orchestrator = get_adaptive_orchestrator()
        
        section = {
            "name": "Architecture",
            "prompt_template": "Describe architecture of {service_name}"
        }
        context = {
            "service_name": "TestService",
            "concepts": ["REST API", "PostgreSQL", "Redis"]
        }
        
        prompt = await orchestrator._build_prompt(section, context, "TestService")
        
        assert "TestService" in prompt
        # Should include key concepts
        assert "Key Concepts" in prompt or any(c in prompt for c in context["concepts"])


class TestOrchestratorCitationFormatting:
    """Test citation formatting."""
    
    def test_format_citations_endnotes(self):
        """Test endnotes citation formatting."""
        orchestrator = get_adaptive_orchestrator()
        
        citations = [
            {
                "section_name": "Overview",
                "document_id": uuid4(),
                "relevance_score": 0.95,
                "content": "Test content for overview"
            },
            {
                "section_name": "API",
                "document_id": uuid4(),
                "relevance_score": 0.87,
                "content": "Test content for API"
            }
        ]
        
        formatted = orchestrator._format_citations(citations, style="endnotes")
        
        assert "Sources & References" in formatted
        assert "Overview" in formatted
        assert "API" in formatted
        assert "95%" in formatted  # Relevance percentages
    
    def test_format_citations_groups_by_section(self):
        """Test citations are grouped by section."""
        orchestrator = get_adaptive_orchestrator()
        
        citations = [
            {"section_name": "A", "document_id": uuid4(), "relevance_score": 0.9, "content": ""},
            {"section_name": "A", "document_id": uuid4(), "relevance_score": 0.8, "content": ""},
            {"section_name": "B", "document_id": uuid4(), "relevance_score": 0.95, "content": ""}
        ]
        
        formatted = orchestrator._format_citations(citations, style="endnotes")
        
        # Should have sections A and B
        assert formatted.count("### A") >= 1
        assert formatted.count("### B") >= 1


# ============================================================================
# Performance Tests
# ============================================================================

class TestOrchestratorPerformance:
    """Performance tests for orchestrator."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generation_performance(self, benchmark):
        """Test full generation performance."""
        orchestrator = get_adaptive_orchestrator()
        
        # Mock all dependencies for consistent benchmarking
        mock_context = {"service_name": "test", "primary_language": "Python"}
        mock_template = {
            "id": str(uuid4()),
            "name": "test",
            "category": "api_reference",
            "structure": {"sections": [{"name": "Test", "required": True, "prompt_template": "Test"}]},
            "render_options": {}
        }
        
        with patch.object(orchestrator.discovery_service, 'discover_repository_context',
                         return_value=mock_context):
            with patch.object(orchestrator.template_manager, 'load_template',
                             return_value=mock_template):
                with patch.object(orchestrator.rag_service, 'query',
                                 return_value={"answer": "Content", "sources": []}):
                    with patch.object(orchestrator.prompt_tracker, 'track_prompt_execution',
                                     return_value=uuid4()):
                        with patch.object(orchestrator.template_manager, 'validate_generated_content',
                                         return_value={"valid": True, "adherence_score": 0.9}):
                            with patch.object(orchestrator.template_manager, 'render_section',
                                             return_value="Rendered"):
                                
                                async def generate():
                                    return await orchestrator.generate_adaptive_documentation(
                                        service_name="test",
                                        template_name="test",
                                        category="api_reference"
                                    )
                                
                                result = await benchmark.pedantic(generate, rounds=5)
                                assert result is not None

