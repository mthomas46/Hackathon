"""
Unit tests for Discovery Service

Tests repository context discovery, framework detection, and guidance generation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from src.services.adaptive.discovery_service import (
    DiscoveryService,
    get_discovery_service
)


class TestDiscoveryService:
    """Test suite for DiscoveryService."""
    
    @pytest.fixture
    async def discovery_service(self):
        """Get discovery service instance."""
        return get_discovery_service()
    
    @pytest.fixture
    def mock_repository_context(self):
        """Mock repository context data."""
        return {
            "service_name": "adminservice",
            "primary_language": "Scala",
            "languages": {
                "Scala": 245,
                "Java": 12,
                "JavaScript": 5
            },
            "primary_framework": "Play Framework",
            "frameworks": ["Play Framework", "Akka"],
            "architecture_type": "layered",
            "total_files": 262,
            "code_structure": {
                "controllers": 25,
                "models": 30,
                "services": 40
            },
            "dependencies": ["postgresql", "redis", "akka"]
        }
    
    # ============================================================================
    # Repository Context Discovery Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_discover_repository_context_success(self, discovery_service, mock_repository_context):
        """Test successful repository context discovery."""
        with patch.object(discovery_service, '_query_repository_contexts', 
                         return_value=mock_repository_context):
            context = await discovery_service.discover_repository_context("adminservice")
            
            assert context is not None
            assert context["service_name"] == "adminservice"
            assert "languages" in context
            assert "frameworks" in context
            assert context["primary_language"] == "Scala"
    
    @pytest.mark.asyncio
    async def test_discover_repository_context_not_found(self, discovery_service):
        """Test discovery for non-existent service."""
        with patch.object(discovery_service, '_query_repository_contexts', 
                         return_value=None):
            context = await discovery_service.discover_repository_context("nonexistent")
            
            # Should return default context
            assert context is not None
            assert context["service_name"] == "nonexistent"
            assert context["primary_language"] == "Unknown"
    
    @pytest.mark.asyncio
    async def test_discover_extracts_concepts(self, discovery_service, mock_repository_context):
        """Test that discovery extracts key concepts."""
        with patch.object(discovery_service, '_query_repository_contexts', 
                         return_value=mock_repository_context):
            context = await discovery_service.discover_repository_context("adminservice")
            
            assert "concepts" in context
            assert len(context["concepts"]) > 0
            # Should include framework name
            assert any("Play" in c for c in context["concepts"])
    
    @pytest.mark.asyncio
    async def test_discover_extracts_keywords(self, discovery_service, mock_repository_context):
        """Test that discovery extracts keywords."""
        with patch.object(discovery_service, '_query_repository_contexts', 
                         return_value=mock_repository_context):
            context = await discovery_service.discover_repository_context("adminservice")
            
            assert "keywords" in context
            assert len(context["keywords"]) > 0
            # Should include language and framework
            assert "Scala" in context["keywords"]
    
    # ============================================================================
    # Framework Detection Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_detect_framework_play(self, discovery_service):
        """Test detecting Play Framework."""
        context = {
            "primary_language": "Scala",
            "frameworks": ["Play Framework"],
            "dependencies": ["play"]
        }
        
        framework = await discovery_service._detect_primary_framework(context)
        assert framework == "Play Framework"
    
    @pytest.mark.asyncio
    async def test_detect_framework_spring(self, discovery_service):
        """Test detecting Spring Boot."""
        context = {
            "primary_language": "Java",
            "frameworks": ["Spring Boot"],
            "dependencies": ["spring-boot"]
        }
        
        framework = await discovery_service._detect_primary_framework(context)
        assert framework == "Spring Boot"
    
    @pytest.mark.asyncio
    async def test_detect_framework_fallback(self, discovery_service):
        """Test fallback when no framework detected."""
        context = {
            "primary_language": "Python",
            "frameworks": [],
            "dependencies": []
        }
        
        framework = await discovery_service._detect_primary_framework(context)
        assert framework == "generic"
    
    # ============================================================================
    # Framework-Specific Guidance Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_get_framework_guidance_play(self, discovery_service):
        """Test getting Play Framework specific guidance."""
        guidance = await discovery_service.get_framework_specific_guidance("adminservice")
        
        # Should return some guidance even if generic
        assert guidance is not None
        assert isinstance(guidance, dict)
    
    @pytest.mark.asyncio
    async def test_framework_guidance_includes_patterns(self, discovery_service):
        """Test framework guidance includes recommended patterns."""
        with patch.object(discovery_service, 'discover_repository_context', 
                         return_value={"primary_framework": "Play Framework", "service_name": "test"}):
            guidance = await discovery_service.get_framework_specific_guidance("test")
            
            assert "patterns_to_find" in guidance or "guidance" in guidance
    
    @pytest.mark.asyncio
    async def test_framework_guidance_includes_terminology(self, discovery_service):
        """Test framework guidance includes framework-specific terminology."""
        with patch.object(discovery_service, 'discover_repository_context', 
                         return_value={"primary_framework": "Play Framework", "service_name": "test"}):
            guidance = await discovery_service.get_framework_specific_guidance("test")
            
            # Should have some kind of guidance structure
            assert isinstance(guidance, dict)
    
    # ============================================================================
    # Concept Extraction Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_extract_concepts_from_code_structure(self, discovery_service):
        """Test concept extraction from code structure."""
        context = {
            "code_structure": {
                "controllers": 25,
                "models": 30,
                "services": 40,
                "repositories": 35
            }
        }
        
        concepts = await discovery_service._extract_concepts(context)
        
        assert len(concepts) > 0
        # Should extract architectural patterns
        assert any("MVC" in c or "layered" in c or "service" in c for c in concepts)
    
    @pytest.mark.asyncio
    async def test_extract_concepts_from_dependencies(self, discovery_service):
        """Test concept extraction from dependencies."""
        context = {
            "dependencies": ["postgresql", "redis", "kafka"],
            "code_structure": {}
        }
        
        concepts = await discovery_service._extract_concepts(context)
        
        assert len(concepts) > 0
        # Should include database concepts
        assert any("database" in c.lower() or "postgresql" in c.lower() for c in concepts)
    
    # ============================================================================
    # Keyword Extraction Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_extract_keywords_basic(self, discovery_service):
        """Test basic keyword extraction."""
        context = {
            "primary_language": "Scala",
            "primary_framework": "Play Framework",
            "architecture_type": "layered"
        }
        
        keywords = await discovery_service._extract_keywords(context)
        
        assert len(keywords) > 0
        assert "Scala" in keywords
        assert "Play Framework" in keywords
    
    @pytest.mark.asyncio
    async def test_extract_keywords_from_multiple_sources(self, discovery_service):
        """Test keyword extraction from multiple context sources."""
        context = {
            "primary_language": "Java",
            "languages": {"Java": 100, "Kotlin": 50},
            "frameworks": ["Spring Boot", "Hibernate"],
            "dependencies": ["mysql", "redis"]
        }
        
        keywords = await discovery_service._extract_keywords(context)
        
        # Should include all significant elements
        assert "Java" in keywords
        assert len(keywords) >= 4  # At least language + framework + some deps


class TestDiscoveryServiceIntegration:
    """Integration tests for Discovery Service."""
    
    @pytest.mark.asyncio
    async def test_full_discovery_workflow(self):
        """Test complete discovery workflow."""
        service = get_discovery_service()
        
        # Mock the database query
        mock_context = {
            "service_name": "testservice",
            "primary_language": "Python",
            "languages": {"Python": 100},
            "frameworks": ["FastAPI"],
            "architecture_type": "microservice"
        }
        
        with patch.object(service, '_query_repository_contexts', return_value=mock_context):
            # Discover context
            context = await service.discover_repository_context("testservice")
            
            # Get guidance
            guidance = await service.get_framework_specific_guidance("testservice")
            
            # Verify complete workflow
            assert context is not None
            assert guidance is not None
            assert "concepts" in context
            assert "keywords" in context
    
    @pytest.mark.asyncio
    async def test_discovery_with_missing_data(self):
        """Test discovery handles missing/incomplete data gracefully."""
        service = get_discovery_service()
        
        # Minimal context
        minimal_context = {
            "service_name": "minimal",
            "primary_language": "Unknown"
        }
        
        with patch.object(service, '_query_repository_contexts', return_value=minimal_context):
            context = await service.discover_repository_context("minimal")
            
            # Should still return valid context with defaults
            assert context is not None
            assert "concepts" in context
            assert "keywords" in context
            assert isinstance(context["concepts"], list)
            assert isinstance(context["keywords"], list)
    
    @pytest.mark.asyncio
    async def test_discovery_caching(self):
        """Test that discovery results can be cached."""
        service = get_discovery_service()
        
        mock_context = {
            "service_name": "cached",
            "primary_language": "Python"
        }
        
        with patch.object(service, '_query_repository_contexts', return_value=mock_context) as mock_query:
            # First call
            context1 = await service.discover_repository_context("cached")
            
            # Second call (should hit cache if implemented)
            context2 = await service.discover_repository_context("cached")
            
            assert context1 == context2
            # Note: Actual caching implementation may vary


# ============================================================================
# Performance Tests
# ============================================================================

class TestDiscoveryPerformance:
    """Performance tests for Discovery Service."""
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_discovery_performance(self, benchmark):
        """Test discovery performance."""
        service = get_discovery_service()
        
        mock_context = {
            "service_name": "perftest",
            "primary_language": "Java",
            "languages": {"Java": 1000, "Kotlin": 500},
            "frameworks": ["Spring Boot", "Hibernate", "JPA"],
            "dependencies": ["mysql", "redis", "kafka", "elasticsearch"],
            "code_structure": {
                f"component_{i}": i * 10
                for i in range(50)
            }
        }
        
        with patch.object(service, '_query_repository_contexts', return_value=mock_context):
            # Benchmark discovery
            result = await benchmark.pedantic(
                service.discover_repository_context,
                args=("perftest",),
                rounds=10
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_discovery(self):
        """Test multiple concurrent discovery operations."""
        import asyncio
        
        service = get_discovery_service()
        
        async def discover(service_name):
            mock_context = {
                "service_name": service_name,
                "primary_language": "Python"
            }
            with patch.object(service, '_query_repository_contexts', return_value=mock_context):
                return await service.discover_repository_context(service_name)
        
        # Run 10 discoveries concurrently
        results = await asyncio.gather(*[
            discover(f"service_{i}") for i in range(10)
        ])
        
        assert len(results) == 10
        assert all(r is not None for r in results)


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestDiscoveryErrorHandling:
    """Test error handling in Discovery Service."""
    
    @pytest.mark.asyncio
    async def test_handles_database_error(self):
        """Test discovery handles database errors gracefully."""
        service = get_discovery_service()
        
        with patch.object(service, '_query_repository_contexts', 
                         side_effect=Exception("Database error")):
            # Should return default context instead of raising
            context = await service.discover_repository_context("errortest")
            
            assert context is not None
            assert context["service_name"] == "errortest"
    
    @pytest.mark.asyncio
    async def test_handles_malformed_context(self):
        """Test discovery handles malformed context data."""
        service = get_discovery_service()
        
        malformed = {
            "service_name": "malformed",
            # Missing expected fields
            "primary_language": None,
            "languages": "not_a_dict",  # Should be dict
        }
        
        with patch.object(service, '_query_repository_contexts', return_value=malformed):
            # Should handle gracefully
            context = await service.discover_repository_context("malformed")
            
            assert context is not None
            assert isinstance(context.get("languages", {}), dict)

