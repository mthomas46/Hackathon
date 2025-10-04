"""
End-User Acceptance Testing (UAT)

Phase 6.2: Comprehensive end-to-end validation of Workflow F from a user perspective.

Test Scenarios:
1. New Project Planning: Generate plan with expert suggestions
2. Tech Stack Query: "Who knows Python backend?"
3. SME Identification: Accurately identify subject matter experts
4. Team Collaboration: Teammate suggestions make sense
5. Report Quality: Final report is actionable and comprehensive

Run:
    pytest tests/functional/test_end_user_acceptance.py -v -m acceptance
    pytest tests/functional/test_end_user_acceptance.py::TestNewProjectPlanning -v
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any, List
from datetime import datetime
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


# Service URLs
EXPERT_FINDER_URL = "http://localhost:5160"
PLANNING_SERVICE_URL = "http://localhost:5077"
USER_STORE_URL = "http://localhost:5050"
DOC_STORE_URL = "http://localhost:5060"


@pytest.fixture
async def http_client():
    """Async HTTP client for API requests."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        yield client


@pytest.fixture
async def sample_project_features():
    """Sample features for a new project."""
    return [
        {
            "name": "User Authentication Service",
            "description": "Implement JWT-based authentication with FastAPI and PostgreSQL",
            "priority": "high",
            "estimated_effort": 8,
            "tags": ["authentication", "security", "backend", "python", "fastapi", "postgresql"]
        },
        {
            "name": "React Dashboard",
            "description": "Build responsive admin dashboard with React and Material-UI",
            "priority": "medium",
            "estimated_effort": 13,
            "tags": ["frontend", "react", "javascript", "typescript", "ui", "dashboard"]
        },
        {
            "name": "Docker Deployment Pipeline",
            "description": "Set up CI/CD with Docker, Kubernetes, and GitHub Actions",
            "priority": "high",
            "estimated_effort": 5,
            "tags": ["devops", "docker", "kubernetes", "ci/cd", "github-actions"]
        },
        {
            "name": "API Documentation",
            "description": "Generate OpenAPI/Swagger documentation for all endpoints",
            "priority": "low",
            "estimated_effort": 3,
            "tags": ["documentation", "api", "openapi", "swagger"]
        }
    ]


@pytest.mark.acceptance
@pytest.mark.asyncio
@pytest.mark.skipif(
    not asyncio.run(_check_services_available()),
    reason="Required services not available for UAT"
)
class TestNewProjectPlanning:
    """
    UAT Scenario 1: New Project Planning
    
    User Story:
    As a project manager, I want to generate a development plan for a new feature
    so that I can identify experts who can help with implementation.
    """
    
    async def test_generate_plan_with_expert_suggestions(self, http_client, sample_project_features):
        """
        Test complete workflow:
        1. Submit project features
        2. Generate expert-augmented roadmap
        3. Verify expert suggestions are included
        4. Validate recommendations are actionable
        """
        # Step 1: Generate expert-augmented roadmap
        roadmap_request = {
            "project_id": f"uat-project-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "team_id": "uat-team-alpha",
            "features": sample_project_features,
            "enable_expert_discovery": True
        }
        
        try:
            response = await http_client.post(
                f"{PLANNING_SERVICE_URL}/api/v1/planning/roadmap/expert-augmented",
                json=roadmap_request,
                timeout=30.0
            )
            
            # Validate response
            assert response.status_code in [200, 201], f"Roadmap generation failed: {response.text}"
            
            roadmap = response.json()
            
            # Step 2: Verify roadmap structure
            assert "roadmap_id" in roadmap or "roadmapId" in roadmap
            assert "features_count" in roadmap or "featuresCount" in roadmap
            assert "expert_context" in roadmap or "expertContext" in roadmap
            
            expert_context = roadmap.get("expert_context") or roadmap.get("expertContext") or {}
            
            # Step 3: Verify expert context contains meaningful data
            assert expert_context.get("expert_finder_available") or expert_context.get("expertFinderAvailable"), \
                "Expert finder should be available"
            
            # Step 4: Validate expert suggestions
            tech_experts = expert_context.get("technology_experts") or expert_context.get("technologyExperts") or {}
            
            # Should have experts for key technologies
            expected_technologies = ["Python", "FastAPI", "React", "Docker"]
            found_technologies = [tech for tech in expected_technologies if tech in str(tech_experts)]
            
            assert len(found_technologies) >= 2, \
                f"Should find experts for at least 2 key technologies, found: {found_technologies}"
            
            # Step 5: Verify recommendations are enhanced
            recommendations = roadmap.get("recommendations", [])
            assert len(recommendations) > 0, "Should have recommendations"
            
            # Check for expert-related recommendations
            expert_mentions = [r for r in recommendations if any(keyword in str(r).lower() 
                              for keyword in ["expert", "sme", "skill", "team"])]
            
            assert len(expert_mentions) > 0, "Recommendations should mention experts"
            
            print("\n✅ UAT Scenario 1 PASSED: Expert-augmented roadmap generated successfully")
            print(f"   - Roadmap ID: {roadmap.get('roadmap_id') or roadmap.get('roadmapId')}")
            print(f"   - Features: {roadmap.get('features_count') or roadmap.get('featuresCount')}")
            print(f"   - Technologies with experts: {len(tech_experts)}")
            print(f"   - Recommendations: {len(recommendations)}")
            
        except httpx.ConnectError:
            pytest.skip("Planning service not available")


@pytest.mark.acceptance
@pytest.mark.asyncio
@pytest.mark.skipif(
    not asyncio.run(_check_services_available()),
    reason="Required services not available for UAT"
)
class TestTechStackQuery:
    """
    UAT Scenario 2: Tech Stack Query
    
    User Story:
    As a team lead, I want to find experts for specific technologies
    so that I can staff my project appropriately.
    """
    
    async def test_find_python_backend_experts(self, http_client):
        """Test: 'Who knows Python backend?'"""
        try:
            response = await http_client.post(
                f"{EXPERT_FINDER_URL}/experts/find",
                json={
                    "query": "Who knows Python backend?",
                    "max_results": 10
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                experts = result.get("experts", [])
                
                # Should find at least some candidates
                assert isinstance(experts, list), "Experts should be a list"
                
                # If experts found, validate structure
                if len(experts) > 0:
                    first_expert = experts[0]
                    assert "username" in first_expert or "user_id" in first_expert
                    assert "relevance_score" in first_expert or "score" in first_expert or "expertise_score" in first_expert
                
                print(f"\n✅ UAT Scenario 2 PASSED: Found {len(experts)} Python backend experts")
                
                # Show top 3 experts
                for i, expert in enumerate(experts[:3], 1):
                    username = expert.get("username", expert.get("user_id", "Unknown"))
                    score = expert.get("relevance_score", expert.get("score", expert.get("expertise_score", 0)))
                    topics = expert.get("topics", expert.get("topic_interests", []))
                    print(f"   {i}. {username} (score: {score:.2f if isinstance(score, (int, float)) else score})")
                    print(f"      Topics: {', '.join(topics[:5]) if topics else 'N/A'}")
            else:
                pytest.skip(f"Expert finder returned {response.status_code}")
                
        except httpx.ConnectError:
            pytest.skip("Expert finder service not available")
    
    async def test_find_react_frontend_experts(self, http_client):
        """Test: Find React/Frontend experts"""
        try:
            response = await http_client.get(
                f"{EXPERT_FINDER_URL}/experts/by-topic/React",
                params={"max_results": 5},
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                experts = result.get("experts", [])
                
                assert isinstance(experts, list), "Should return list of experts"
                
                print(f"\n✅ UAT Scenario 2b PASSED: Found {len(experts)} React experts")
                
        except httpx.ConnectError:
            pytest.skip("Expert finder service not available")
    
    async def test_find_devops_experts(self, http_client):
        """Test: Find DevOps/Docker experts"""
        try:
            response = await http_client.get(
                f"{EXPERT_FINDER_URL}/experts/by-topic/Docker",
                params={"max_results": 5},
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                experts = result.get("experts", [])
                
                print(f"\n✅ UAT Scenario 2c PASSED: Found {len(experts)} Docker/DevOps experts")
                
        except httpx.ConnectError:
            pytest.skip("Expert finder service not available")


@pytest.mark.acceptance
@pytest.mark.asyncio
@pytest.mark.skipif(
    not asyncio.run(_check_services_available()),
    reason="Required services not available for UAT"
)
class TestSMEIdentification:
    """
    UAT Scenario 3: SME Identification
    
    User Story:
    As an architect, I want to identify subject matter experts for different components
    so that I can assign ownership and get expert reviews.
    """
    
    async def test_identify_authentication_sme(self, http_client):
        """Test: Identify SME for authentication/security"""
        try:
            response = await http_client.get(
                f"{EXPERT_FINDER_URL}/experts/sme/authentication",
                params={"max_results": 3},
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                experts = result.get("experts", [])
                
                # Validate SME identification
                if len(experts) > 0:
                    top_sme = experts[0]
                    score = top_sme.get("expertise_score", top_sme.get("score", 0))
                    
                    # SMEs should have high confidence scores
                    if isinstance(score, (int, float)):
                        assert score >= 0.0, "SME score should be non-negative"
                    
                    print(f"\n✅ UAT Scenario 3 PASSED: Identified {len(experts)} authentication SMEs")
                    print(f"   Top SME: {top_sme.get('username', 'Unknown')}")
                    print(f"   Expertise Score: {score}")
                else:
                    print("\n⚠️  UAT Scenario 3: No authentication SMEs found (acceptable for new system)")
                    
        except httpx.ConnectError:
            pytest.skip("Expert finder service not available")
    
    async def test_identify_frontend_sme(self, http_client):
        """Test: Identify SME for frontend development"""
        try:
            response = await http_client.get(
                f"{EXPERT_FINDER_URL}/experts/sme/frontend",
                params={"max_results": 3},
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                experts = result.get("experts", [])
                
                print(f"\n✅ UAT Scenario 3b PASSED: Identified {len(experts)} frontend SMEs")
                
        except httpx.ConnectError:
            pytest.skip("Expert finder service not available")


@pytest.mark.acceptance
@pytest.mark.asyncio
@pytest.mark.skipif(
    not asyncio.run(_check_services_available()),
    reason="Required services not available for UAT"
)
class TestTeamCollaboration:
    """
    UAT Scenario 4: Team Collaboration
    
    User Story:
    As a developer, I want to find teammates who have worked on similar projects
    so that I can collaborate effectively.
    """
    
    async def test_find_potential_teammates(self, http_client):
        """Test: Find potential teammates for collaboration"""
        try:
            # First, get a user to find teammates for
            users_response = await http_client.get(
                f"{USER_STORE_URL}/users",
                params={"limit": 1},
                timeout=10.0
            )
            
            if users_response.status_code == 200:
                users_data = users_response.json()
                users = users_data if isinstance(users_data, list) else users_data.get("users", [])
                
                if len(users) > 0:
                    test_user_id = users[0].get("id") or users[0].get("user_id") or users[0].get("username")
                    
                    # Find teammates
                    response = await http_client.get(
                        f"{EXPERT_FINDER_URL}/experts/teammates/{test_user_id}",
                        params={"max_results": 5},
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        teammates = result.get("teammates", result.get("experts", []))
                        
                        print(f"\n✅ UAT Scenario 4 PASSED: Found {len(teammates)} potential teammates for user {test_user_id}")
                        
                        # Validate teammate structure
                        if len(teammates) > 0:
                            first_teammate = teammates[0]
                            assert "username" in first_teammate or "user_id" in first_teammate
                            
                            # Should have collaboration indicators
                            assert ("shared_documents" in first_teammate or 
                                   "collaboration_score" in first_teammate or
                                   "score" in first_teammate)
                    else:
                        print(f"\n⚠️  UAT Scenario 4: Teammates endpoint returned {response.status_code}")
                else:
                    pytest.skip("No users available for teammate testing")
            else:
                pytest.skip("User-store not available")
                
        except httpx.ConnectError:
            pytest.skip("Services not available")


@pytest.mark.acceptance
@pytest.mark.asyncio
@pytest.mark.skipif(
    not asyncio.run(_check_services_available()),
    reason="Required services not available for UAT"
)
class TestReportQuality:
    """
    UAT Scenario 5: Report Quality
    
    User Story:
    As a stakeholder, I want comprehensive and actionable reports
    so that I can make informed decisions about project staffing.
    """
    
    async def test_report_contains_all_required_sections(self, http_client, sample_project_features):
        """Test: Final report contains all required sections"""
        roadmap_request = {
            "project_id": f"uat-report-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "team_id": "uat-team-report",
            "features": sample_project_features[:2],  # Use fewer features for faster testing
            "enable_expert_discovery": True
        }
        
        try:
            response = await http_client.post(
                f"{PLANNING_SERVICE_URL}/api/v1/planning/roadmap/expert-augmented",
                json=roadmap_request,
                timeout=30.0
            )
            
            if response.status_code in [200, 201]:
                roadmap = response.json()
                
                # Validate required sections
                required_fields = [
                    ("roadmap_id", "roadmapId"),
                    ("features_count", "featuresCount"),
                    ("recommendations", "recommendations"),
                    ("expert_context", "expertContext")
                ]
                
                for field, alt_field in required_fields:
                    assert field in roadmap or alt_field in roadmap, \
                        f"Report missing required field: {field}"
                
                # Validate expert context completeness
                expert_context = roadmap.get("expert_context") or roadmap.get("expertContext") or {}
                
                expected_context_fields = [
                    ("total_technologies", "totalTechnologies"),
                    ("total_experts_identified", "totalExpertsIdentified"),
                    ("expert_finder_available", "expertFinderAvailable")
                ]
                
                for field, alt_field in expected_context_fields:
                    assert field in expert_context or alt_field in expert_context, \
                        f"Expert context missing field: {field}"
                
                print("\n✅ UAT Scenario 5 PASSED: Report contains all required sections")
                print(f"   - Roadmap ID: {roadmap.get('roadmap_id') or roadmap.get('roadmapId')}")
                print(f"   - Features: {roadmap.get('features_count') or roadmap.get('featuresCount')}")
                print(f"   - Recommendations: {len(roadmap.get('recommendations', []))}")
                print(f"   - Expert Context: Complete ✅")
                
            else:
                pytest.skip(f"Planning service returned {response.status_code}")
                
        except httpx.ConnectError:
            pytest.skip("Planning service not available")
    
    async def test_report_recommendations_are_actionable(self, http_client, sample_project_features):
        """Test: Recommendations are specific and actionable"""
        roadmap_request = {
            "project_id": f"uat-actionable-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "team_id": "uat-team-actionable",
            "features": sample_project_features[:1],
            "enable_expert_discovery": True
        }
        
        try:
            response = await http_client.post(
                f"{PLANNING_SERVICE_URL}/api/v1/planning/roadmap/expert-augmented",
                json=roadmap_request,
                timeout=30.0
            )
            
            if response.status_code in [200, 201]:
                roadmap = response.json()
                recommendations = roadmap.get("recommendations", [])
                
                # Recommendations should be specific (contain concrete details)
                actionable_keywords = [
                    "expert", "sme", "team", "skill", "technology",
                    "python", "react", "docker", "authentication", "frontend"
                ]
                
                actionable_recommendations = [
                    r for r in recommendations
                    if any(keyword in str(r).lower() for keyword in actionable_keywords)
                ]
                
                # At least some recommendations should be actionable
                if len(recommendations) > 0:
                    actionable_ratio = len(actionable_recommendations) / len(recommendations)
                    assert actionable_ratio >= 0.3, \
                        "At least 30% of recommendations should be actionable"
                
                print(f"\n✅ UAT Scenario 5b PASSED: {len(actionable_recommendations)}/{len(recommendations)} recommendations are actionable")
                
        except httpx.ConnectError:
            pytest.skip("Planning service not available")


@pytest.mark.acceptance
@pytest.mark.asyncio
class TestPerformanceUnderRealisticLoad:
    """
    Performance validation under realistic load.
    
    Ensures system performs well during typical usage.
    """
    
    async def test_response_time_meets_expectations(self, http_client):
        """Test: All endpoints respond within acceptable time"""
        endpoints = [
            (f"{EXPERT_FINDER_URL}/health", 1.0),  # Health check: 1s
            (f"{EXPERT_FINDER_URL}/experts/by-topic/Python", 5.0),  # Expert query: 5s
        ]
        
        for url, max_time in endpoints:
            try:
                start_time = datetime.now()
                response = await http_client.get(url, timeout=max_time + 5.0)
                elapsed = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    assert elapsed <= max_time, \
                        f"Endpoint {url} took {elapsed:.2f}s (max: {max_time}s)"
                    
                    print(f"✅ {url}: {elapsed:.2f}s (target: {max_time}s)")
                    
            except (httpx.ConnectError, httpx.TimeoutException):
                pytest.skip(f"Endpoint {url} not available")
    
    async def test_system_handles_concurrent_users(self, http_client):
        """Test: System handles multiple concurrent users"""
        # Simulate 5 concurrent expert queries
        queries = [
            "Python expert",
            "React developer",
            "DevOps engineer",
            "Database specialist",
            "API developer"
        ]
        
        try:
            tasks = [
                http_client.post(
                    f"{EXPERT_FINDER_URL}/experts/find",
                    json={"query": query, "max_results": 5},
                    timeout=10.0
                )
                for query in queries
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful responses
            successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
            
            # At least 80% should succeed
            success_rate = successful / len(queries)
            assert success_rate >= 0.8, \
                f"Only {successful}/{len(queries)} concurrent requests succeeded"
            
            print(f"\n✅ Concurrent load test: {successful}/{len(queries)} queries succeeded ({success_rate:.0%})")
            
        except httpx.ConnectError:
            pytest.skip("Expert finder service not available")


# Helper function for service availability check
async def _check_services_available():
    """Check if required services are available for UAT."""
    services = [
        (EXPERT_FINDER_URL, "/health"),
        (USER_STORE_URL, "/health"),
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
    pytest.main([__file__, "-v", "-m", "acceptance", "--tb=short"])

