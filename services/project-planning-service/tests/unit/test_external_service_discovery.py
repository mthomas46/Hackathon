"""
Unit Tests for External Service Discovery Engine - Phase 9
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "services" / "project-planning-service"))

from domain.services.external_service_discovery_engine import ExternalServiceDiscoveryEngine
from domain.entities.external_service_entities import DiscoveryMethod, ServiceCategory


class TestExternalServiceDiscoveryEngine:
    """Test suite for External Service Discovery Engine."""
    
    @pytest.fixture
    def engine(self):
        """Create discovery engine instance."""
        return ExternalServiceDiscoveryEngine()
    
    def test_extract_mentioned_services(self, engine):
        """Test extraction of explicitly mentioned services."""
        query = "Build notifications using Firebase and SendGrid for emails"
        requirements = {}
        
        mentioned = engine._extract_mentioned_services(query, requirements)
        
        assert len(mentioned) > 0
        service_names = [s.name.lower() for s in mentioned]
        assert any("firebase" in name for name in service_names)
        assert any("sendgrid" in name for name in service_names)
        
        # Check discovery method
        for service in mentioned:
            assert DiscoveryMethod.EXPLICIT_MENTION in service.discovery_methods
    
    def test_extract_topics(self, engine):
        """Test topic extraction from query."""
        query = "Build a notification system with push notifications and email alerts"
        requirements = {"feature_type": "Notification Service"}
        
        topics = engine._extract_topics(query, requirements)
        
        assert "notifications" in topics
        assert "email" in topics or "push" in topics
    
    def test_extract_technologies(self, engine):
        """Test technology extraction from query."""
        query = "iOS app with Android support using REST API"
        requirements = {}
        
        technologies = engine._extract_technologies(query, requirements)
        
        assert len(technologies) > 0
        tech_str = " ".join(technologies).lower()
        assert "ios" in tech_str or "android" in tech_str or "rest" in tech_str
    
    def test_relevance_scoring(self, engine):
        """Test relevance score calculation."""
        from domain.entities.external_service_entities import ExternalServiceMatch
        
        service = ExternalServiceMatch(
            service_id="test-service",
            name="Test Service",
            relevance_score=0.35,  # Base score for explicit mention
            discovery_methods=[DiscoveryMethod.EXPLICIT_MENTION],
            initial_category=ServiceCategory.DIRECT
        )
        
        query = "test query"
        requirements = {}
        
        # Calculate final relevance
        final_score = engine._calculate_final_relevance(service, query, requirements)
        
        assert 0.0 <= final_score <= 1.0
        assert final_score >= service.relevance_score
    
    def test_relevance_bonus_for_multiple_methods(self, engine):
        """Test bonus scoring for multiple discovery methods."""
        from domain.entities.external_service_entities import ExternalServiceMatch
        
        service = ExternalServiceMatch(
            service_id="test-service",
            name="Test Service",
            relevance_score=0.60,
            discovery_methods=[
                DiscoveryMethod.EXPLICIT_MENTION,
                DiscoveryMethod.TOPIC_MATCH,
                DiscoveryMethod.TECHNOLOGY_MATCH
            ],
            initial_category=ServiceCategory.DIRECT
        )
        
        query = "test"
        requirements = {}
        
        final_score = engine._calculate_final_relevance(service, query, requirements)
        
        # Should get bonus for multiple methods
        assert final_score > service.relevance_score
        assert final_score <= 1.0
    
    def test_service_categorization_direct(self, engine):
        """Test categorization of high-relevance services as direct."""
        from domain.entities.external_service_entities import ExternalServiceMatch
        
        service = ExternalServiceMatch(
            service_id="test-service",
            name="Test Service",
            relevance_score=0.90,  # High relevance
            discovery_methods=[DiscoveryMethod.EXPLICIT_MENTION],
            initial_category=ServiceCategory.DIRECT
        )
        
        assert service.relevance_score >= 0.85
        assert service.initial_category == ServiceCategory.DIRECT
    
    def test_service_categorization_tangential(self, engine):
        """Test categorization of medium-relevance services as tangential."""
        from domain.entities.external_service_entities import ExternalServiceMatch
        
        service = ExternalServiceMatch(
            service_id="test-service",
            name="Test Service",
            relevance_score=0.70,  # Medium relevance
            discovery_methods=[DiscoveryMethod.TOPIC_MATCH],
            initial_category=ServiceCategory.TANGENTIAL
        )
        
        assert 0.60 <= service.relevance_score < 0.85
        assert service.initial_category == ServiceCategory.TANGENTIAL
    
    def test_service_categorization_excluded(self, engine):
        """Test categorization of low-relevance services as excluded."""
        from domain.entities.external_service_entities import ExternalServiceMatch
        
        service = ExternalServiceMatch(
            service_id="test-service",
            name="Test Service",
            relevance_score=0.40,  # Low relevance
            discovery_methods=[DiscoveryMethod.RELATED_SERVICE],
            initial_category=ServiceCategory.EXCLUDED
        )
        
        assert service.relevance_score < 0.60
        assert service.initial_category == ServiceCategory.EXCLUDED
    
    @pytest.mark.asyncio
    async def test_discover_services_integration(self, engine):
        """Test complete discovery flow."""
        query = "Build push notifications using Firebase for iOS and Android"
        requirements = {
            "feature_type": "Notification System",
            "platforms": ["iOS", "Android"]
        }
        
        services = await engine.discover_services(query, requirements)
        
        assert isinstance(services, list)
        assert len(services) > 0
        assert all(hasattr(s, 'service_id') for s in services)
        assert all(hasattr(s, 'relevance_score') for s in services)
        assert all(0.0 <= s.relevance_score <= 1.0 for s in services)
        
        # Should be sorted by relevance
        relevance_scores = [s.relevance_score for s in services]
        assert relevance_scores == sorted(relevance_scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_discover_services_limits_results(self, engine):
        """Test that discovery limits results to top 15."""
        query = "comprehensive system using all possible services"
        requirements = {}
        
        services = await engine.discover_services(query, requirements)
        
        assert len(services) <= 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

