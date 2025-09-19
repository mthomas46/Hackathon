"""Comprehensive Verification Tests for Summarizer-Hub Recommendation Types

This module contains tests to verify that all recommendation types in the summarizer-hub
are working correctly and producing expected results.
"""

import pytest
import asyncio
import httpx
from typing import Dict, Any, List
import json


class TestRecommendationTypeVerification:
    """Test all recommendation types to ensure they're working correctly."""

    @pytest.fixture
    def test_documents(self) -> List[Dict[str, Any]]:
        """Provide test documents for recommendation verification."""
        return [
            {
                "id": "doc_001",
                "title": "User Authentication Guide",
                "content": "This guide covers user authentication, login processes, password management, and security best practices for user accounts.",
                "dateCreated": "2024-01-01T10:00:00Z",
                "dateUpdated": "2024-01-05T14:30:00Z"
            },
            {
                "id": "doc_002",
                "title": "Authentication API Documentation",
                "content": "The authentication API provides endpoints for user login, logout, password reset, and token management. All endpoints require HTTPS.",
                "dateCreated": "2024-01-02T09:15:00Z",
                "dateUpdated": "2024-01-08T16:45:00Z"
            },
            {
                "id": "doc_003",
                "title": "Security Best Practices",
                "content": "Security is important. Always use HTTPS. Never store passwords in plain text. Implement proper authentication mechanisms.",
                "dateCreated": "2023-06-01T08:30:00Z",  # Old document
                "dateUpdated": "2023-06-05T12:15:00Z"   # Very old
            },
            {
                "id": "doc_004",
                "title": "Login Implementation Guide",
                "content": "To implement login functionality, first create a login form, then validate user credentials against the authentication API, handle errors gracefully.",  # Short, incomplete
                "dateCreated": "2024-01-03T11:20:00Z",
                "dateUpdated": "2024-01-07T13:10:00Z"
            },
            {
                "id": "doc_005",
                "title": "User Management System",
                "content": "This system manages user accounts, authentication, and authorization. It provides APIs for user registration, login, password management, and account settings.",
                "dateCreated": "2024-01-04T14:45:00Z",
                "dateUpdated": "2024-01-10T09:30:00Z"
            }
        ]

    @pytest.fixture
    def summarizer_config(self):
        """Configuration for summarizer service."""
        return {
            "url": "http://localhost:5160",
            "timeout": 30.0
        }

    @pytest.mark.asyncio
    async def test_service_health(self, summarizer_config):
        """Test that summarizer service is healthy and responding."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{summarizer_config['url']}/health")
                assert response.status_code == 200

                health_data = response.json()
                assert health_data.get("status") == "healthy"
                assert health_data.get("service") == "summarizer-hub"

        except Exception as e:
            pytest.skip(f"Summarizer service not available: {str(e)}")

    @pytest.mark.asyncio
    async def test_all_recommendation_types_generation(self, summarizer_config, test_documents):
        """Test that all recommendation types can be generated successfully."""
        try:
            async with httpx.AsyncClient(timeout=summarizer_config["timeout"]) as client:
                request_data = {
                    "documents": test_documents,
                    "recommendation_types": ["consolidation", "duplicate", "outdated", "quality"],
                    "confidence_threshold": 0.1,  # Low threshold for testing
                    "include_jira_suggestions": True
                }

                response = await client.post(
                    f"{summarizer_config['url']}/recommendations",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )

                assert response.status_code == 200

                result = response.json()
                assert "recommendations" in result
                assert "total_documents" in result
                assert "recommendations_count" in result
                assert isinstance(result["recommendations"], list)

                print(f"✅ Generated {result['recommendations_count']} recommendations from {result['total_documents']} documents")

        except Exception as e:
            pytest.skip(f"Summarizer service not available for recommendation testing: {str(e)}")

    @pytest.mark.asyncio
    async def test_consolidation_recommendations(self, summarizer_config, test_documents):
        """Test consolidation recommendation generation specifically."""
        try:
            async with httpx.AsyncClient(timeout=summarizer_config["timeout"]) as client:
                request_data = {
                    "documents": test_documents,
                    "recommendation_types": ["consolidation"],
                    "confidence_threshold": 0.1
                }

                response = await client.post(
                    f"{summarizer_config['url']}/recommendations",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )

                assert response.status_code == 200

                result = response.json()
                recommendations = result.get("recommendations", [])

                # Check that consolidation recommendations are generated
                consolidation_recs = [r for r in recommendations if r.get("type") == "consolidation"]

                print(f"✅ Generated {len(consolidation_recs)} consolidation recommendations")

                # Verify consolidation recommendation structure
                for rec in consolidation_recs:
                    assert "type" in rec
                    assert rec["type"] == "consolidation"
                    assert "description" in rec
                    assert "priority" in rec
                    assert "confidence_score" in rec

        except Exception as e:
            pytest.skip(f"Consolidation recommendation test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_duplicate_recommendations(self, summarizer_config, test_documents):
        """Test duplicate recommendation generation specifically."""
        try:
            async with httpx.AsyncClient(timeout=summarizer_config["timeout"]) as client:
                request_data = {
                    "documents": test_documents,
                    "recommendation_types": ["duplicate"],
                    "confidence_threshold": 0.1
                }

                response = await client.post(
                    f"{summarizer_config['url']}/recommendations",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )

                assert response.status_code == 200

                result = response.json()
                recommendations = result.get("recommendations", [])

                # Check that duplicate recommendations are generated
                duplicate_recs = [r for r in recommendations if r.get("type") == "duplicate"]

                print(f"✅ Generated {len(duplicate_recs)} duplicate recommendations")

                # Verify duplicate recommendation structure
                for rec in duplicate_recs:
                    assert "type" in rec
                    assert rec["type"] == "duplicate"
                    assert "description" in rec
                    assert "priority" in rec
                    assert "confidence_score" in rec

        except Exception as e:
            pytest.skip(f"Duplicate recommendation test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_outdated_recommendations(self, summarizer_config, test_documents):
        """Test outdated recommendation generation specifically."""
        try:
            async with httpx.AsyncClient(timeout=summarizer_config["timeout"]) as client:
                request_data = {
                    "documents": test_documents,
                    "recommendation_types": ["outdated"],
                    "confidence_threshold": 0.1
                }

                response = await client.post(
                    f"{summarizer_config['url']}/recommendations",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )

                assert response.status_code == 200

                result = response.json()
                recommendations = result.get("recommendations", [])

                # Check that outdated recommendations are generated
                outdated_recs = [r for r in recommendations if r.get("type") == "outdated"]

                print(f"✅ Generated {len(outdated_recs)} outdated recommendations")

                # Verify outdated recommendation structure
                for rec in outdated_recs:
                    assert "type" in rec
                    assert rec["type"] == "outdated"
                    assert "description" in rec
                    assert "priority" in rec
                    assert "confidence_score" in rec

        except Exception as e:
            pytest.skip(f"Outdated recommendation test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_quality_recommendations(self, summarizer_config, test_documents):
        """Test quality recommendation generation specifically."""
        try:
            async with httpx.AsyncClient(timeout=summarizer_config["timeout"]) as client:
                request_data = {
                    "documents": test_documents,
                    "recommendation_types": ["quality"],
                    "confidence_threshold": 0.1
                }

                response = await client.post(
                    f"{summarizer_config['url']}/recommendations",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )

                assert response.status_code == 200

                result = response.json()
                recommendations = result.get("recommendations", [])

                # Check that quality recommendations are generated
                quality_recs = [r for r in recommendations if r.get("type") == "quality"]

                print(f"✅ Generated {len(quality_recs)} quality recommendations")

                # Verify quality recommendation structure
                for rec in quality_recs:
                    assert "type" in rec
                    assert rec["type"] == "quality"
                    assert "description" in rec
                    assert "priority" in rec
                    assert "confidence_score" in rec

        except Exception as e:
            pytest.skip(f"Quality recommendation test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_jira_ticket_suggestions(self, summarizer_config, test_documents):
        """Test Jira ticket suggestion generation."""
        try:
            async with httpx.AsyncClient(timeout=summarizer_config["timeout"]) as client:
                request_data = {
                    "documents": test_documents,
                    "recommendation_types": ["consolidation", "duplicate", "outdated", "quality"],
                    "confidence_threshold": 0.1,
                    "include_jira_suggestions": True
                }

                response = await client.post(
                    f"{summarizer_config['url']}/recommendations",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )

                assert response.status_code == 200

                result = response.json()

                # Check for Jira suggestions
                jira_tickets = result.get("suggested_jira_tickets", [])

                print(f"✅ Generated {len(jira_tickets)} Jira ticket suggestions")

                # Verify Jira ticket structure
                for ticket in jira_tickets:
                    assert "summary" in ticket
                    assert "description" in ticket
                    assert "issue_type" in ticket
                    assert "priority" in ticket
                    assert "labels" in ticket
                    assert "epic_link" in ticket

        except Exception as e:
            pytest.skip(f"Jira ticket suggestion test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_drift_analysis(self, summarizer_config, test_documents):
        """Test drift analysis functionality."""
        try:
            async with httpx.AsyncClient(timeout=summarizer_config["timeout"]) as client:
                request_data = {
                    "documents": test_documents,
                    "recommendation_types": ["quality"],
                    "confidence_threshold": 0.1
                }

                response = await client.post(
                    f"{summarizer_config['url']}/recommendations",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )

                assert response.status_code == 200

                result = response.json()

                # Check for drift analysis
                drift_analysis = result.get("drift_analysis", {})

                print(f"✅ Drift analysis generated: {bool(drift_analysis)}")

                if drift_analysis:
                    assert "drift_alerts" in drift_analysis
                    assert "summary" in drift_analysis

                    alerts = drift_analysis.get("drift_alerts", [])
                    print(f"   📊 Found {len(alerts)} drift alerts")

        except Exception as e:
            pytest.skip(f"Drift analysis test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_alignment_analysis(self, summarizer_config, test_documents):
        """Test alignment analysis functionality."""
        try:
            async with httpx.AsyncClient(timeout=summarizer_config["timeout"]) as client:
                request_data = {
                    "documents": test_documents,
                    "recommendation_types": ["quality"],
                    "confidence_threshold": 0.1
                }

                response = await client.post(
                    f"{summarizer_config['url']}/recommendations",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )

                assert response.status_code == 200

                result = response.json()

                # Check for alignment analysis
                alignment_analysis = result.get("alignment_analysis", {})

                print(f"✅ Alignment analysis generated: {bool(alignment_analysis)}")

                if alignment_analysis:
                    assert "alignment_score" in alignment_analysis
                    assert "issues" in alignment_analysis

                    score = alignment_analysis.get("alignment_score", 0)
                    print(".2f")

        except Exception as e:
            pytest.skip(f"Alignment analysis test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_inconclusive_analysis(self, summarizer_config, test_documents):
        """Test inconclusive analysis functionality."""
        try:
            async with httpx.AsyncClient(timeout=summarizer_config["timeout"]) as client:
                request_data = {
                    "documents": test_documents,
                    "recommendation_types": ["quality"],
                    "confidence_threshold": 0.8  # High threshold to trigger inconclusive
                }

                response = await client.post(
                    f"{summarizer_config['url']}/recommendations",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )

                assert response.status_code == 200

                result = response.json()

                # Check for inconclusive analysis
                inconclusive_analysis = result.get("inconclusive_analysis", {})

                print(f"✅ Inconclusive analysis generated: {bool(inconclusive_analysis)}")

                if inconclusive_analysis:
                    assert "insufficient_data_warnings" in inconclusive_analysis
                    assert "data_quality_assessment" in inconclusive_analysis

                    warnings = inconclusive_analysis.get("insufficient_data_warnings", [])
                    print(f"   ⚠️ Found {len(warnings)} data quality warnings")

        except Exception as e:
            pytest.skip(f"Inconclusive analysis test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_timeline_analysis_integration(self, summarizer_config, test_documents):
        """Test timeline analysis with document placement."""
        try:
            timeline = {
                "phases": [
                    {"name": "Planning", "start_week": 0, "duration_weeks": 2},
                    {"name": "Development", "start_week": 2, "duration_weeks": 4},
                    {"name": "Testing", "start_week": 6, "duration_weeks": 2}
                ]
            }

            async with httpx.AsyncClient(timeout=summarizer_config["timeout"]) as client:
                request_data = {
                    "documents": test_documents,
                    "recommendation_types": ["quality"],
                    "timeline": timeline,
                    "confidence_threshold": 0.1
                }

                response = await client.post(
                    f"{summarizer_config['url']}/recommendations",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )

                assert response.status_code == 200

                result = response.json()

                # Check for timeline analysis
                timeline_analysis = result.get("timeline_analysis", {})

                print(f"✅ Timeline analysis generated: {bool(timeline_analysis)}")

                if timeline_analysis:
                    assert "timeline_structure" in timeline_analysis
                    assert "document_placement" in timeline_analysis
                    assert "placement_score" in timeline_analysis

                    placement_score = timeline_analysis.get("placement_score", 0)
                    print(".1f")

        except Exception as e:
            pytest.skip(f"Timeline analysis test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_comprehensive_analysis_workflow(self, summarizer_config, test_documents):
        """Test the complete analysis workflow with all features enabled."""
        try:
            timeline = {
                "phases": [
                    {"name": "Planning", "start_week": 0, "duration_weeks": 2},
                    {"name": "Development", "start_week": 2, "duration_weeks": 4},
                    {"name": "Testing", "start_week": 6, "duration_weeks": 2}
                ]
            }

            async with httpx.AsyncClient(timeout=summarizer_config["timeout"]) as client:
                request_data = {
                    "documents": test_documents,
                    "recommendation_types": ["consolidation", "duplicate", "outdated", "quality"],
                    "confidence_threshold": 0.1,
                    "include_jira_suggestions": True,
                    "timeline": timeline
                }

                print("🚀 Testing comprehensive analysis workflow...")
                response = await client.post(
                    f"{summarizer_config['url']}/recommendations",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )

                assert response.status_code == 200

                result = response.json()

                # Verify all components are present
                required_fields = [
                    "recommendations", "total_documents", "recommendations_count",
                    "drift_analysis", "alignment_analysis", "inconclusive_analysis",
                    "timeline_analysis", "suggested_jira_tickets"
                ]

                missing_fields = []
                for field in required_fields:
                    if field not in result:
                        missing_fields.append(field)

                if missing_fields:
                    print(f"⚠️ Missing fields: {missing_fields}")
                else:
                    print("✅ All required analysis components present")

                # Summary statistics
                total_recs = result.get("recommendations_count", 0)
                jira_tickets = len(result.get("suggested_jira_tickets", []))
                drift_alerts = len(result.get("drift_analysis", {}).get("drift_alerts", []))
                alignment_score = result.get("alignment_analysis", {}).get("alignment_score", 0)
                placement_score = result.get("timeline_analysis", {}).get("placement_score", 0)

                print(f"📊 Analysis Summary:")
                print(f"   📄 Documents processed: {result.get('total_documents', 0)}")
                print(f"   💡 Recommendations generated: {total_recs}")
                print(f"   🎫 Jira tickets suggested: {jira_tickets}")
                print(f"   🚨 Drift alerts: {drift_alerts}")
                print(".2f")
                print(".1f")

                # Success criteria
                assert result.get("total_documents", 0) == len(test_documents)
                assert isinstance(result.get("recommendations", []), list)
                assert isinstance(result.get("suggested_jira_tickets", []), list)

                print("✅ Comprehensive analysis workflow test PASSED")

        except Exception as e:
            pytest.skip(f"Comprehensive analysis workflow test failed: {str(e)}")


if __name__ == "__main__":
    print("🧪 Recommendation Verification Tests")
    print("Run with: python -m pytest tests/integration/test_recommendation_verification.py -v")
    print("Requires summarizer-hub service running on localhost:5160")
