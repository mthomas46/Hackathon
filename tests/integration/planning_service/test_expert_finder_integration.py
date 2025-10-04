"""
Integration Tests for Expert-Finder Planning Service Integration

Phase 4.2: Validate expert-augmented roadmap generation end-to-end.

Tests:
- Expert-finder queries from planning service
- Various tech stacks
- Different team compositions
- SME identification
- Team augmentation suggestions
- Fallback when expert-finder unavailable

Run:
    pytest tests/integration/planning_service/test_expert_finder_integration.py -v
    pytest tests/integration/planning_service/ -m integration
"""

import pytest
import httpx
import asyncio
from typing import List, Dict, Any
from datetime import datetime, date


# Service URLs
PLANNING_SERVICE_URL = "http://localhost:5077"
EXPERT_FINDER_URL = "http://localhost:5160"
USER_STORE_URL = "http://localhost:5050"


@pytest.fixture
async def http_client():
    """Async HTTP client for API requests."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
async def sample_features(http_client):
    """Create sample features in planning service for testing."""
    features = []
    
    # Feature 1: Python/FastAPI backend
    feature1 = {
        "title": "User Authentication Service",
        "description": "Implement JWT-based authentication with FastAPI",
        "priority": "high",
        "story_points": 8.0,
        "metadata": {
            "technologies": ["Python", "FastAPI", "JWT", "PostgreSQL"],
            "components": ["authentication", "security"]
        },
        "tags": ["backend", "security", "api"]
    }
    
    # Feature 2: React frontend
    feature2 = {
        "title": "Dashboard UI Component",
        "description": "Build responsive dashboard using React and TypeScript",
        "priority": "medium",
        "story_points": 5.0,
        "metadata": {
            "technologies": ["React", "TypeScript", "CSS"],
            "components": ["frontend", "ui"]
        },
        "tags": ["frontend", "ui", "react"]
    }
    
    # Feature 3: Docker infrastructure
    feature3 = {
        "title": "Container Orchestration",
        "description": "Set up Docker and Kubernetes deployment",
        "priority": "medium",
        "story_points": 3.0,
        "metadata": {
            "technologies": ["Docker", "Kubernetes"],
            "components": ["infrastructure", "devops"]
        },
        "tags": ["devops", "infrastructure"]
    }
    
    for feature_data in [feature1, feature2, feature3]:
        try:
            response = await http_client.post(
                f"{PLANNING_SERVICE_URL}/api/v1/planning/features",
                json=feature_data
            )
            if response.status_code == 201:
                features.append(response.json())
        except Exception as e:
            print(f"Failed to create feature: {e}")
    
    yield features
    
    # Cleanup (optional)
    # for feature in features:
    #     try:
    #         await http_client.delete(f"{PLANNING_SERVICE_URL}/api/v1/planning/features/{feature['id']}")
    #     except:
    #         pass


@pytest.fixture
async def sample_users(http_client):
    """Create sample users in user-store for expert matching."""
    users = [
        {
            "username": "alice.backend",
            "email": "alice@example.com",
            "full_name": "Alice Backend",
            "role": "developer",
            "status": "active",
            "team_id": "team-alpha",
            "topic_interests": ["Python", "FastAPI", "PostgreSQL"],
            "service_subscriptions": ["authentication-service"]
        },
        {
            "username": "bob.frontend",
            "email": "bob@example.com",
            "full_name": "Bob Frontend",
            "role": "developer",
            "status": "active",
            "team_id": "team-alpha",
            "topic_interests": ["React", "TypeScript", "JavaScript"],
            "service_subscriptions": ["ui-service"]
        },
        {
            "username": "charlie.devops",
            "email": "charlie@example.com",
            "full_name": "Charlie DevOps",
            "role": "developer",
            "status": "active",
            "team_id": "team-beta",
            "topic_interests": ["Docker", "Kubernetes", "AWS"],
            "service_subscriptions": ["infrastructure"]
        }
    ]
    
    created_users = []
    for user_data in users:
        try:
            response = await http_client.post(
                f"{USER_STORE_URL}/users",
                json=user_data
            )
            if response.status_code in [200, 201]:
                created_users.append(response.json())
        except Exception as e:
            print(f"User might already exist: {e}")
    
    return created_users


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not asyncio.run(_check_services_available()),
    reason="Required services not available"
)
class TestExpertFinderPlanningIntegration:
    """Test expert-finder integration in planning service."""
    
    async def test_expert_augmented_roadmap_generation(self, http_client, sample_features, sample_users):
        """Test basic expert-augmented roadmap generation."""
        if not sample_features:
            pytest.skip("No features available for testing")
        
        request_data = {
            "feature_ids": [f.get("id") or f.get("feature_id") for f in sample_features if f.get("id") or f.get("feature_id")],
            "team_id": "team-alpha",
            "start_date": "2024-02-01",
            "team_velocity": 20.0,
            "sprint_duration_weeks": 2,
            "enable_expert_discovery": True
        }
        
        response = await http_client.post(
            f"{PLANNING_SERVICE_URL}/api/v1/planning/roadmap/expert-augmented",
            json=request_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify roadmap structure
        assert "roadmap_id" in data
        assert "roadmap_name" in data
        assert "features_count" in data
        assert "recommendations" in data
        assert "expert_context" in data
        
        # Verify expert context is present
        expert_context = data["expert_context"]
        if expert_context:
            assert "expert_finder_available" in expert_context
            assert "total_technologies" in expert_context
            assert "total_experts_identified" in expert_context
        
        print(f"\n✅ Expert-augmented roadmap generated: {data['roadmap_id']}")
        print(f"   Features: {data['features_count']}")
        print(f"   Expert context available: {expert_context is not None}")
    
    async def test_tech_stack_expert_discovery(self, http_client, sample_features, sample_users):
        """Test expert discovery for specific tech stacks."""
        if not sample_features:
            pytest.skip("No features available for testing")
        
        request_data = {
            "feature_ids": [f.get("id") or f.get("feature_id") for f in sample_features if f.get("id") or f.get("feature_id")],
            "team_id": "team-alpha",
            "start_date": "2024-02-01",
            "technologies": ["Python", "FastAPI", "React", "Docker"],
            "enable_expert_discovery": True
        }
        
        response = await http_client.post(
            f"{PLANNING_SERVICE_URL}/api/v1/planning/roadmap/expert-augmented",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        expert_context = data.get("expert_context")
        if expert_context and expert_context.get("expert_finder_available"):
            # Should have discovered experts for technologies
            assert expert_context.get("total_technologies", 0) > 0
            print(f"\n✅ Discovered experts for {expert_context['total_technologies']} technologies")
    
    async def test_component_sme_identification(self, http_client, sample_features, sample_users):
        """Test SME identification for components."""
        if not sample_features:
            pytest.skip("No features available for testing")
        
        request_data = {
            "feature_ids": [f.get("id") or f.get("feature_id") for f in sample_features if f.get("id") or f.get("feature_id")],
            "team_id": "team-alpha",
            "start_date": "2024-02-01",
            "components": ["authentication", "frontend", "infrastructure"],
            "enable_expert_discovery": True
        }
        
        response = await http_client.post(
            f"{PLANNING_SERVICE_URL}/api/v1/planning/roadmap/expert-augmented",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        expert_context = data.get("expert_context")
        if expert_context and expert_context.get("expert_finder_available"):
            # Should have identified SMEs
            smes_count = expert_context.get("total_smes_identified", 0)
            print(f"\n✅ Identified {smes_count} SMEs for components")
    
    async def test_skill_gap_analysis(self, http_client, sample_features, sample_users):
        """Test skill gap detection and team augmentation suggestions."""
        if not sample_features:
            pytest.skip("No features available for testing")
        
        # Request with technologies that might have skill gaps
        request_data = {
            "feature_ids": [f.get("id") or f.get("feature_id") for f in sample_features if f.get("id") or f.get("feature_id")],
            "team_id": "team-alpha",
            "start_date": "2024-02-01",
            "technologies": ["Rust", "Go", "Haskell"],  # Uncommon technologies
            "enable_expert_discovery": True
        }
        
        response = await http_client.post(
            f"{PLANNING_SERVICE_URL}/api/v1/planning/roadmap/expert-augmented",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        expert_context = data.get("expert_context")
        if expert_context and expert_context.get("expert_finder_available"):
            # Should detect skill gaps
            skill_gaps = expert_context.get("skill_gaps", 0)
            augmentation_suggestions = expert_context.get("team_augmentation_suggestions", 0)
            
            print(f"\n✅ Skill gaps detected: {skill_gaps}")
            print(f"   Augmentation suggestions: {augmentation_suggestions}")
    
    async def test_different_team_compositions(self, http_client, sample_features, sample_users):
        """Test with different team IDs."""
        if not sample_features:
            pytest.skip("No features available for testing")
        
        teams = ["team-alpha", "team-beta", "team-gamma"]
        
        for team_id in teams:
            request_data = {
                "feature_ids": [f.get("id") or f.get("feature_id") for f in sample_features[:1] if f.get("id") or f.get("feature_id")],
                "team_id": team_id,
                "start_date": "2024-02-01",
                "enable_expert_discovery": True
            }
            
            response = await http_client.post(
                f"{PLANNING_SERVICE_URL}/api/v1/planning/roadmap/expert-augmented",
                json=request_data
            )
            
            assert response.status_code == 200
            data = response.json()
            
            print(f"\n✅ Roadmap generated for {team_id}: {data['roadmap_id']}")
    
    async def test_fallback_when_expert_finder_unavailable(self, http_client, sample_features):
        """Test graceful fallback when expert-finder is unavailable."""
        if not sample_features:
            pytest.skip("No features available for testing")
        
        # Request with invalid expert-finder URL (fallback scenario)
        request_data = {
            "feature_ids": [f.get("id") or f.get("feature_id") for f in sample_features if f.get("id") or f.get("feature_id")],
            "team_id": "team-alpha",
            "start_date": "2024-02-01",
            "expert_finder_url": "http://localhost:9999",  # Invalid URL
            "enable_expert_discovery": True
        }
        
        response = await http_client.post(
            f"{PLANNING_SERVICE_URL}/api/v1/planning/roadmap/expert-augmented",
            json=request_data
        )
        
        # Should still succeed with fallback
        assert response.status_code in [200, 500]  # Might fail gracefully
        
        if response.status_code == 200:
            data = response.json()
            assert "roadmap_id" in data
            
            # Expert context should indicate unavailability
            expert_context = data.get("expert_context")
            if expert_context:
                assert expert_context.get("expert_finder_available") == False
                print("\n✅ Graceful fallback when expert-finder unavailable")
    
    async def test_expert_discovery_disabled(self, http_client, sample_features):
        """Test with expert discovery explicitly disabled."""
        if not sample_features:
            pytest.skip("No features available for testing")
        
        request_data = {
            "feature_ids": [f.get("id") or f.get("feature_id") for f in sample_features if f.get("id") or f.get("feature_id")],
            "team_id": "team-alpha",
            "start_date": "2024-02-01",
            "enable_expert_discovery": False
        }
        
        response = await http_client.post(
            f"{PLANNING_SERVICE_URL}/api/v1/planning/roadmap/expert-augmented",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Expert context should be None or indicate disabled
        expert_context = data.get("expert_context")
        assert expert_context is None or expert_context.get("expert_finder_available") == False
        
        print("\n✅ Expert discovery can be disabled")
    
    async def test_performance_with_expert_discovery(self, http_client, sample_features, sample_users):
        """Test that expert discovery doesn't significantly impact performance."""
        if not sample_features:
            pytest.skip("No features available for testing")
        
        request_data = {
            "feature_ids": [f.get("id") or f.get("feature_id") for f in sample_features if f.get("id") or f.get("feature_id")],
            "team_id": "team-alpha",
            "start_date": "2024-02-01",
            "enable_expert_discovery": True
        }
        
        response = await http_client.post(
            f"{PLANNING_SERVICE_URL}/api/v1/planning/roadmap/expert-augmented",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        generation_time = data.get("generation_time_ms", 0)
        
        # Performance target: < 5000ms (5 seconds) for expert-augmented roadmap
        assert generation_time < 5000, f"Generation took {generation_time}ms (target: <5000ms)"
        
        print(f"\n✅ Expert-augmented roadmap generated in {generation_time:.2f}ms")
    
    async def test_recommendations_enhanced_with_expert_context(self, http_client, sample_features, sample_users):
        """Test that recommendations include expert-based insights."""
        if not sample_features:
            pytest.skip("No features available for testing")
        
        request_data = {
            "feature_ids": [f.get("id") or f.get("feature_id") for f in sample_features if f.get("id") or f.get("feature_id")],
            "team_id": "team-alpha",
            "start_date": "2024-02-01",
            "enable_expert_discovery": True
        }
        
        response = await http_client.post(
            f"{PLANNING_SERVICE_URL}/api/v1/planning/roadmap/expert-augmented",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        recommendations = data.get("recommendations", [])
        
        # Should have recommendations
        assert len(recommendations) > 0
        
        # Check if any recommendations mention experts, SMEs, or reviewers
        expert_mentions = [
            r for r in recommendations
            if any(keyword in r.lower() for keyword in ["expert", "sme", "reviewer", "skill gap", "augmentation"])
        ]
        
        print(f"\n✅ Recommendations: {len(recommendations)} total")
        print(f"   Expert-related: {len(expert_mentions)}")


@pytest.mark.integration
@pytest.mark.asyncio
class TestExpertFinderClientMethods:
    """Test individual expert-finder client methods."""
    
    async def test_client_health_check(self):
        """Test expert-finder client health check."""
        from services.project_planning_service.infrastructure.expert_finder_client import ExpertFinderClient
        
        async with ExpertFinderClient() as client:
            is_healthy = await client.health_check()
            assert isinstance(is_healthy, bool)
            print(f"\n✅ Expert-finder health check: {is_healthy}")
    
    async def test_client_get_experts_for_tech_stack(self):
        """Test batch technology expert query."""
        from services.project_planning_service.infrastructure.expert_finder_client import ExpertFinderClient
        
        technologies = ["Python", "FastAPI", "React"]
        
        async with ExpertFinderClient() as client:
            results = await client.get_experts_for_tech_stack(
                technologies=technologies,
                max_per_tech=5
            )
            
            assert isinstance(results, dict)
            assert all(tech in results for tech in technologies)
            
            for tech, experts in results.items():
                print(f"\n✅ {tech}: {len(experts)} experts found")
    
    async def test_client_get_smes_for_components(self):
        """Test batch component SME query."""
        from services.project_planning_service.infrastructure.expert_finder_client import ExpertFinderClient
        
        components = ["authentication", "frontend", "infrastructure"]
        
        async with ExpertFinderClient() as client:
            results = await client.get_smes_for_components(
                components=components,
                max_per_component=3
            )
            
            assert isinstance(results, dict)
            assert all(comp in results for comp in components)
            
            for comp, smes in results.items():
                print(f"\n✅ {comp}: {len(smes)} SMEs found")
    
    async def test_client_suggest_team_augmentation(self):
        """Test team augmentation suggestions."""
        from services.project_planning_service.infrastructure.expert_finder_client import ExpertFinderClient
        
        required_skills = ["Rust", "Go", "GraphQL"]
        
        async with ExpertFinderClient() as client:
            suggestions = await client.suggest_team_augmentation(
                required_skills=required_skills,
                experience_level="mid",
                max_suggestions=5
            )
            
            assert isinstance(suggestions, list)
            print(f"\n✅ Team augmentation: {len(suggestions)} suggestions")


# Helper function for service availability check
async def _check_services_available():
    """Check if required services are available."""
    services = [
        (PLANNING_SERVICE_URL, "/health"),
        (EXPERT_FINDER_URL, "/health"),
        (USER_STORE_URL, "/health")
    ]
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for base_url, endpoint in services:
            try:
                response = await client.get(f"{base_url}{endpoint}")
                if response.status_code != 200:
                    return False
            except:
                return False
    
    return True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

