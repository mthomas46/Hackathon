"""
Unit Tests for Summarizer-Hub Recommendation Engine (TDD RED Phase)
Following TDD principles: RED -> GREEN -> REFACTOR

These tests are written FIRST (RED phase) and will initially FAIL.
They define the expected behavior before implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Import the modules we'll be testing
from simulation.domain.recommendations.recommendation import Recommendation, RecommendationType
from simulation.infrastructure.recommendations.summarizer_hub_client import SummarizerHubClient
from simulation.application.analysis.simulation_analyzer import SimulationAnalyzer


class TestSummarizerHubClient:
    """Test the SummarizerHub client recommendation functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = SummarizerHubClient()

    @pytest.mark.asyncio
    async def test_get_consolidation_recommendations(self):
        """Test getting consolidation recommendations from summarizer-hub."""
        # Arrange
        documents = [
            {"id": "doc1", "title": "API Guide", "content": "API documentation", "type": "api_docs"},
            {"id": "doc2", "title": "API Reference", "content": "API reference guide", "type": "api_docs"},
            {"id": "doc3", "title": "API Examples", "content": "API usage examples", "type": "api_docs"}
        ]

        mock_response = {
            "success": True,
            "recommendations": [
                {
                    "id": "rec1",
                    "type": "consolidation",
                    "description": "Consolidate 3 api_docs documents into a comprehensive guide",
                    "affected_documents": ["doc1", "doc2", "doc3"],
                    "confidence_score": 0.8,
                    "priority": "high",
                    "rationale": "Multiple api_docs documents with 75.0% average similarity",
                    "expected_impact": "Reduce maintenance overhead by 45%",
                    "effort_level": "medium",
                    "tags": ["consolidation", "api_docs"],
                    "metadata": {
                        "document_type": "api_docs",
                        "document_count": 3,
                        "average_similarity": 0.75,
                        "consolidation_strategy": "merge_into_comprehensive_guide"
                    }
                }
            ],
            "total_documents": 3,
            "recommendations_count": 1,
            "processing_time": 0.5,
            "recommendation_types": ["consolidation"],
            "confidence_threshold": 0.4
        }

        # Act & Assert
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = AsyncMock()
            mock_instance.post.return_value.status_code = 200
            mock_instance.post.return_value.json.return_value = mock_response

            recommendations = await self.client.get_consolidation_recommendations(documents)

            # Assert
            assert isinstance(recommendations, list)
            assert len(recommendations) == 1

            rec = recommendations[0]
            assert isinstance(rec, Recommendation)
            assert rec.type == RecommendationType.CONSOLIDATION
            assert "consolidat" in rec.description.lower()
            assert rec.confidence_score == 0.8
            assert rec.priority == "high"
            assert rec.affected_documents == ["doc1", "doc2", "doc3"]

    @pytest.mark.asyncio
    async def test_get_duplicate_recommendations(self):
        """Test getting duplicate detection recommendations from summarizer-hub."""
        # Arrange
        documents = [
            {"id": "doc1", "title": "User Guide", "content": "How to use the system"},
            {"id": "doc2", "title": "User Manual", "content": "How to use the system"},
            {"id": "doc3", "title": "Getting Started", "content": "How to use the system"}
        ]

        mock_response = {
            "success": True,
            "recommendations": [
                {
                    "id": "rec1",
                    "type": "duplicate",
                    "description": "Documents 'User Guide' and 'User Manual' appear to be duplicates",
                    "affected_documents": ["doc1", "doc2"],
                    "confidence_score": 0.92,
                    "priority": "medium",
                    "rationale": "Content similarity score: 0.92",
                    "expected_impact": "Eliminate redundancy and reduce maintenance burden",
                    "effort_level": "low",
                    "tags": ["duplicate", "redundancy"],
                    "metadata": {"similarity_score": 0.92}
                }
            ],
            "total_documents": 3,
            "recommendations_count": 1,
            "processing_time": 0.3,
            "recommendation_types": ["duplicate"],
            "confidence_threshold": 0.4
        }

        # Act & Assert
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = AsyncMock()
            mock_instance.post.return_value.status_code = 200
            mock_instance.post.return_value.json.return_value = mock_response

            recommendations = await self.client.get_duplicate_recommendations(documents)

            # Assert
            assert isinstance(recommendations, list)
            assert len(recommendations) == 1

            rec = recommendations[0]
            assert isinstance(rec, Recommendation)
            assert rec.type == RecommendationType.DUPLICATE
            assert "duplicate" in rec.description.lower()
            assert len(rec.affected_documents) == 2
            assert rec.confidence_score == 0.92

    @pytest.mark.asyncio
    async def test_get_outdated_recommendations(self):
        """Test getting outdated document recommendations from summarizer-hub."""
        # Arrange
        current_time = datetime.now()
        old_time = current_time - timedelta(days=365*2)  # 2 years old

        documents = [
            {
                "id": "doc1",
                "title": "Old API Guide",
                "content": "Outdated API information",
                "dateCreated": old_time.isoformat(),
                "dateUpdated": old_time.isoformat()
            },
            {
                "id": "doc2",
                "title": "Current API Guide",
                "content": "Current API information",
                "dateCreated": current_time.isoformat(),
                "dateUpdated": current_time.isoformat()
            }
        ]

        mock_response = {
            "success": True,
            "recommendations": [
                {
                    "id": "rec1",
                    "type": "outdated",
                    "description": "Document 'Old API Guide' is 730 days old and may be outdated",
                    "affected_documents": ["doc1"],
                    "confidence_score": 0.85,
                    "priority": "high",
                    "rationale": "Document last updated 730 days ago",
                    "expected_impact": "Ensure users have access to current information",
                    "effort_level": "medium",
                    "tags": ["outdated", "maintenance"],
                    "age_days": 730,
                    "metadata": {"last_updated": old_time.isoformat()}
                }
            ],
            "total_documents": 2,
            "recommendations_count": 1,
            "processing_time": 0.2,
            "recommendation_types": ["outdated"],
            "confidence_threshold": 0.4
        }

        # Act & Assert
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = AsyncMock()
            mock_instance.post.return_value.status_code = 200
            mock_instance.post.return_value.json.return_value = mock_response

            recommendations = await self.client.get_outdated_recommendations(documents)

            # Assert
            assert isinstance(recommendations, list)
            assert len(recommendations) == 1

            rec = recommendations[0]
            assert isinstance(rec, Recommendation)
            assert rec.type == RecommendationType.OUTDATED
            assert "outdated" in rec.description.lower()
            assert rec.age_days == 730

    @pytest.mark.asyncio
    async def test_get_quality_recommendations(self):
        """Test getting quality improvement recommendations from summarizer-hub."""
        # Arrange
        documents = [
            {
                "id": "doc1",
                "title": "Poor Documentation",
                "content": "This is very short and unclear.",
                "word_count": 10
            },
            {
                "id": "doc2",
                "title": "Good Documentation",
                "content": "This is a comprehensive and clear explanation of the topic with detailed examples and thorough coverage.",
                "word_count": 500
            }
        ]

        mock_response = {
            "success": True,
            "recommendations": [
                {
                    "id": "rec1",
                    "type": "quality",
                    "description": "Improve quality of 'Poor Documentation' - content too short",
                    "affected_documents": ["doc1"],
                    "confidence_score": 0.75,
                    "priority": "medium",
                    "rationale": "Quality analysis identified 2 potential improvements",
                    "expected_impact": "Enhanced user understanding and satisfaction",
                    "effort_level": "low",
                    "tags": ["quality", "improvement"],
                    "metadata": {"issues": ["content too short"], "word_count": 10}
                }
            ],
            "total_documents": 2,
            "recommendations_count": 1,
            "processing_time": 0.15,
            "recommendation_types": ["quality"],
            "confidence_threshold": 0.4
        }

        # Act & Assert
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = AsyncMock()
            mock_instance.post.return_value.status_code = 200
            mock_instance.post.return_value.json.return_value = mock_response

            recommendations = await self.client.get_quality_recommendations(documents)

            # Assert
            assert isinstance(recommendations, list)
            assert len(recommendations) == 1

            rec = recommendations[0]
            assert isinstance(rec, Recommendation)
            assert rec.type == RecommendationType.QUALITY
            assert "improve" in rec.description.lower()

    @pytest.mark.asyncio
    async def test_get_comprehensive_recommendations(self):
        """Test getting comprehensive recommendations across all types from summarizer-hub."""
        # Arrange
        documents = [
            {"id": "doc1", "title": "API Guide", "content": "API info", "type": "api_docs"},
            {"id": "doc2", "title": "API Reference", "content": "API info", "type": "api_docs"},
            {"id": "doc3", "title": "Old Guide", "content": "Old content", "dateCreated": "2020-01-01"}
        ]

        mock_response = {
            "success": True,
            "recommendations": [
                {
                    "id": "rec1",
                    "type": "consolidation",
                    "description": "Consolidate 2 api_docs documents into a comprehensive guide",
                    "affected_documents": ["doc1", "doc2"],
                    "confidence_score": 0.7,
                    "priority": "medium",
                    "rationale": "Multiple api_docs documents with 85.0% average similarity",
                    "expected_impact": "Reduce maintenance overhead by 30%",
                    "effort_level": "medium",
                    "tags": ["consolidation", "api_docs"],
                    "metadata": {
                        "document_type": "api_docs",
                        "document_count": 2,
                        "average_similarity": 0.85,
                        "consolidation_strategy": "merge_into_comprehensive_guide"
                    }
                },
                {
                    "id": "rec2",
                    "type": "outdated",
                    "description": "Document 'Old Guide' is 1461 days old and may be outdated",
                    "affected_documents": ["doc3"],
                    "confidence_score": 0.9,
                    "priority": "high",
                    "rationale": "Document last updated 1461 days ago",
                    "expected_impact": "Ensure users have access to current information",
                    "effort_level": "medium",
                    "tags": ["outdated", "maintenance"],
                    "age_days": 1461,
                    "metadata": {"last_updated": "2020-01-01"}
                }
            ],
            "total_documents": 3,
            "recommendations_count": 2,
            "processing_time": 0.5,
            "recommendation_types": ["consolidation", "duplicate", "outdated", "quality"],
            "confidence_threshold": 0.4
        }

        # Act & Assert
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = AsyncMock()
            mock_instance.post.return_value.status_code = 200
            mock_instance.post.return_value.json.return_value = mock_response

            recommendations = await self.client.get_comprehensive_recommendations(documents)

            # Assert
            assert isinstance(recommendations, list)
            assert len(recommendations) == 2

            # Should include multiple types of recommendations
            recommendation_types = set(rec.type for rec in recommendations)
            assert len(recommendation_types) > 1

            # Check that we have both consolidation and outdated recommendations
            types_found = [rec.type for rec in recommendations]
            assert RecommendationType.CONSOLIDATION in types_found
            assert RecommendationType.OUTDATED in types_found

        # All recommendations should have required fields
        for rec in recommendations:
            assert rec.id is not None
            assert rec.description is not None
            assert rec.priority is not None
            assert rec.confidence_score >= 0
            assert rec.confidence_score <= 1

    @pytest.mark.asyncio
    async def test_recommendation_prioritization(self):
        """Test that recommendations are properly prioritized."""
        # Arrange
        documents = [
            {"id": "doc1", "title": "Critical API", "content": "Critical API documentation"},
            {"id": "doc2", "title": "Minor Guide", "content": "Minor guide content"}
        ]

        # Act
        recommendations = await self.engine.generate_comprehensive_recommendations(documents)

        # Assert
        # Sort by priority (high first)
        high_priority = [r for r in recommendations if r.priority == "high"]
        medium_priority = [r for r in recommendations if r.priority == "medium"]
        low_priority = [r for r in recommendations if r.priority == "low"]

        # High priority should come first in sorted list
        sorted_recs = sorted(recommendations, key=lambda r: ["high", "medium", "low"].index(r.priority))
        assert sorted_recs == recommendations or len(high_priority) == 0


class TestSummarizerHubClient:
    """Test the Summarizer-Hub client integration."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = SummarizerHubClient()

    @pytest.mark.asyncio
    async def test_analyze_document_with_summarizer_hub(self):
        """Test document analysis using summarizer-hub service."""
        # Arrange
        document = {
            "id": "doc1",
            "content": "This is a test document about API usage.",
            "title": "API Documentation"
        }

        # Act
        analysis_result = await self.client.analyze_document(document)

        # Assert
        assert isinstance(analysis_result, dict)
        assert "summary" in analysis_result
        assert "key_points" in analysis_result
        assert "sentiment" in analysis_result or "quality_score" in analysis_result

    @pytest.mark.asyncio
    async def test_generate_recommendations_from_analysis(self):
        """Test recommendation generation from analysis results."""
        # Arrange
        analysis_results = [
            {
                "document_id": "doc1",
                "summary": "API documentation",
                "quality_score": 0.3,
                "issues": ["unclear", "incomplete"]
            }
        ]

        # Act
        recommendations = await self.client.generate_recommendations(analysis_results)

        # Assert
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        for rec in recommendations:
            assert "type" in rec
            assert "description" in rec
            assert "priority" in rec

    @pytest.mark.asyncio
    async def test_batch_document_analysis(self):
        """Test batch processing of multiple documents."""
        # Arrange
        documents = [
            {"id": "doc1", "content": "Document 1 content", "title": "Doc 1"},
            {"id": "doc2", "content": "Document 2 content", "title": "Doc 2"},
            {"id": "doc3", "content": "Document 3 content", "title": "Doc 3"}
        ]

        # Act
        batch_results = await self.client.analyze_documents_batch(documents)

        # Assert
        assert isinstance(batch_results, list)
        assert len(batch_results) == len(documents)

        for result in batch_results:
            assert "document_id" in result
            assert "analysis" in result

    @pytest.mark.asyncio
    async def test_service_fallback_handling(self):
        """Test fallback handling when summarizer-hub is unavailable."""
        # This test should verify that the client gracefully handles service unavailability
        # and provides meaningful fallback recommendations

        # Act - This should work even if the service is down
        fallback_result = await self.client.get_fallback_analysis()

        # Assert
        assert isinstance(fallback_result, dict)
        assert "fallback_mode" in fallback_result
        assert fallback_result["fallback_mode"] is True


class TestRecommendationTypes:
    """Test different types of recommendations."""

    def test_recommendation_type_enum_values(self):
        """Test that all expected recommendation types are defined."""
        expected_types = [
            "CONSOLIDATION",
            "DUPLICATE",
            "OUTDATED",
            "QUALITY",
            "CONTENT_GAP",
            "STRUCTURAL_IMPROVEMENT",
            "PRIORITY_REORDERING"
        ]

        for expected_type in expected_types:
            assert hasattr(RecommendationType, expected_type)

    def test_recommendation_creation(self):
        """Test creation of recommendation objects."""
        rec = Recommendation(
            type=RecommendationType.QUALITY,
            description="Improve documentation clarity",
            affected_documents=["doc1", "doc2"],
            confidence_score=0.85,
            priority="high"
        )

        assert rec.type == RecommendationType.QUALITY
        assert rec.description == "Improve documentation clarity"
        assert rec.affected_documents == ["doc1", "doc2"]
        assert rec.confidence_score == 0.85
        assert rec.priority == "high"
        assert rec.id is not None  # Should be auto-generated

    def test_recommendation_priority_sorting(self):
        """Test that recommendations can be sorted by priority."""
        recommendations = [
            Recommendation(type=RecommendationType.QUALITY, description="Low priority", priority="low"),
            Recommendation(type=RecommendationType.CONSOLIDATION, description="High priority", priority="high"),
            Recommendation(type=RecommendationType.DUPLICATE, description="Medium priority", priority="medium")
        ]

        # Sort by priority
        sorted_recs = sorted(recommendations, key=lambda r: ["high", "medium", "low"].index(r.priority))

        assert sorted_recs[0].priority == "high"
        assert sorted_recs[1].priority == "medium"
        assert sorted_recs[2].priority == "low"


class TestAnalysisServiceReportIntegration:
    """Test the analysis-service report generation and storage functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.summarizer = SimulationAnalyzer()

    @pytest.mark.asyncio
    async def test_get_analysis_report_from_analysis_service(self):
        """Test getting analysis report from analysis-service."""
        documents = [
            {
                "id": "doc1",
                "content": "This is a comprehensive API documentation with clear examples and proper structure.",
                "title": "API Guide",
                "type": "api_docs"
            },
            {
                "id": "doc2",
                "content": "This is a short document.",
                "title": "Brief Note",
                "type": "note"
            }
        ]

        # Mock the analysis-service response
        mock_report = {
            "report_id": "analysis_report_sim_123_1234567890",
            "simulation_id": "sim_123",
            "timestamp": "2024-01-01T10:00:00",
            "documents_analyzed": 2,
            "summary": {
                "total_analyses": 2,
                "analysis_types": ["comprehensive_document_analysis"],
                "documents_with_issues": 1,
                "average_quality_score": 0.75
            },
            "analysis_results": [
                {
                    "document_id": "doc1",
                    "quality_score": 0.9,
                    "issues_found": 0
                },
                {
                    "document_id": "doc2",
                    "quality_score": 0.6,
                    "issues_found": 1
                }
            ]
        }

        with patch.object(self.summarizer, '_request_analysis_report_from_service', return_value=mock_report):
            with patch.object(self.summarizer, '_store_received_analysis_report', return_value="analysis_report_sim_123_1234567890"):
                # Test analysis report reception
                analysis_report = await self.summarizer._get_analysis_report_from_analysis_service("sim_123", documents)

                # Should return a report with proper structure
                assert analysis_report is not None
                assert analysis_report["report_id"] == "analysis_report_sim_123_1234567890"
                assert "summary" in analysis_report
                assert analysis_report["summary"]["total_analyses"] == 2

    @pytest.mark.asyncio
    async def test_get_analysis_from_analysis_service_empty_documents(self):
        """Test analysis with empty document list."""
        with patch.object(self.summarizer, '_request_analysis_report_from_service', return_value=None):
            analysis_report = await self.summarizer._get_analysis_report_from_analysis_service("sim_123", [])

            assert analysis_report is None

    @pytest.mark.asyncio
    async def test_store_received_analysis_report(self):
        """Test storing received analysis report in doc-store."""
        analysis_report = {
            "report_id": "analysis_report_sim_123_1234567890",
            "simulation_id": "sim_123",
            "timestamp": "2024-01-01T10:00:00",
            "documents_analyzed": 2,
            "markdown_content": "# Analysis Report\n\nThis is a test report.",
            "summary": {
                "total_analyses": 2,
                "analysis_types": ["comprehensive_document_analysis"],
                "documents_with_issues": 1,
                "average_quality_score": 0.8
            },
            "metadata": {
                "source": "analysis-service",
                "processing_time": "2.5s"
            }
        }

        # Mock the doc-store saving
        with patch.object(self.summarizer, '_save_to_doc_store') as mock_save:
            with patch.object(self.summarizer, '_save_markdown_report') as mock_save_md:
                with patch.object(self.summarizer, '_link_analysis_report_to_simulation') as mock_link:
                    mock_save.return_value = None
                    mock_save_md.return_value = None
                    mock_link.return_value = None

                    report_id = await self.summarizer._store_received_analysis_report(analysis_report, "sim_123")

                    assert report_id == "analysis_report_sim_123_1234567890"
                    mock_save.assert_called()
                    mock_save_md.assert_called()
                    mock_link.assert_called()


    @pytest.mark.asyncio
    async def test_link_analysis_report_to_simulation(self):
        """Test linking analysis report to simulation."""
        # Mock simulation repository
        mock_simulation = Mock()
        mock_simulation.metadata = {}

        mock_repo = Mock()
        mock_repo.find_by_id.return_value = mock_simulation
        mock_repo.save.return_value = None

        with patch.object(self.summarizer, '_get_simulation_repository', return_value=mock_repo):
            await self.summarizer._link_analysis_report_to_simulation("analysis_report_123", "sim_123")

            # Verify the simulation was updated
            assert mock_simulation.metadata['analysis_report_id'] == "analysis_report_123"
            assert 'analysis_report_timestamp' in mock_simulation.metadata
            mock_repo.save.assert_called_once_with(mock_simulation)

    @pytest.mark.asyncio
    async def test_link_analysis_report_simulation_not_found(self):
        """Test linking analysis report when simulation is not found."""
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = None

        with patch.object(self.summarizer, '_get_simulation_repository', return_value=mock_repo):
            await self.summarizer._link_analysis_report_to_simulation("analysis_report_123", "sim_123")

            # Should not attempt to save when simulation not found
            mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_request_analysis_report_from_service_with_service_error(self):
        """Test handling analysis service errors gracefully."""
        documents = [
            {
                "id": "doc1",
                "content": "Test content",
                "title": "Test Doc",
                "type": "test"
            }
        ]

        # Mock httpx to simulate service error
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await self.summarizer._request_analysis_report_from_service("sim_123", documents)

            # Should handle error gracefully and return None
            assert result is None

    @pytest.mark.asyncio
    async def test_place_documents_on_timeline(self):
        """Test placing documents on simulation timeline."""
        documents = [
            {
                "id": "doc1",
                "title": "Early Document",
                "type": "guide",
                "dateCreated": "2024-01-01T10:00:00",
                "dateUpdated": "2024-01-02T10:00:00"
            },
            {
                "id": "doc2",
                "title": "Later Document",
                "type": "api",
                "dateCreated": "2024-02-01T10:00:00"
            }
        ]

        timeline = {
            "phases": [
                {
                    "id": "phase1",
                    "name": "Planning",
                    "start_date": "2024-01-01T00:00:00",
                    "end_date": "2024-01-15T00:00:00"
                },
                {
                    "id": "phase2",
                    "name": "Development",
                    "start_date": "2024-01-15T00:00:00",
                    "end_date": "2024-02-15T00:00:00"
                }
            ]
        }

        result = await self.summarizer.place_documents_on_timeline("sim_123", documents, timeline)

        assert result["simulation_id"] == "sim_123"
        assert result["timeline_phases"] == 2
        assert result["total_documents"] == 2
        assert result["placed_documents"] >= 1  # At least one document should be placed
        assert "phase_breakdown" in result
        assert "placement_report" in result

    def test_parse_timestamp_iso_format(self):
        """Test parsing ISO format timestamps."""
        timestamp_str = "2024-01-01T10:00:00"
        result = self.summarizer._parse_timestamp(timestamp_str)

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1

    def test_parse_timestamp_with_zulu(self):
        """Test parsing ISO format timestamps with Z suffix."""
        timestamp_str = "2024-01-01T10:00:00Z"
        result = self.summarizer._parse_timestamp(timestamp_str)

        assert result is not None
        assert result.year == 2024

    def test_parse_timestamp_various_formats(self):
        """Test parsing various timestamp formats."""
        formats = [
            "2024-01-01",
            "01/01/2024",
            "2024-01-01 10:00:00"
        ]

        for fmt in formats:
            result = self.summarizer._parse_timestamp(fmt)
            assert result is not None, f"Failed to parse format: {fmt}"

    def test_find_relevant_timeline_phase_within_dates(self):
        """Test finding relevant phase when document date is within phase dates."""
        doc_date = datetime(2024, 1, 10)
        timeline_phases = [
            {
                "id": "phase1",
                "name": "Planning",
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-01-15T00:00:00"
            }
        ]

        result = self.summarizer._find_relevant_timeline_phase(doc_date, timeline_phases)

        assert result is not None
        assert result["id"] == "phase1"

    def test_find_relevant_timeline_phase_closest_match(self):
        """Test finding relevant phase when document date doesn't overlap any phase."""
        doc_date = datetime(2024, 3, 1)  # March 1st
        timeline_phases = [
            {
                "id": "phase1",
                "name": "Planning",
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-01-15T00:00:00"
            },
            {
                "id": "phase2",
                "name": "Development",
                "start_date": "2024-02-01T00:00:00",  # February 1st - closest to March 1st
                "end_date": "2024-02-15T00:00:00"
            }
        ]

        result = self.summarizer._find_relevant_timeline_phase(doc_date, timeline_phases)

        # Should find phase2 as it's closer to the document date
        assert result is not None
        assert result["id"] == "phase2"

    def test_determine_placement_reason_within_phase(self):
        """Test placement reason for documents within phase dates."""
        doc_date = datetime(2024, 1, 10)
        phase = {
            "id": "phase1",
            "name": "Planning",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-15T00:00:00"
        }

        reason = self.summarizer._determine_placement_reason(doc_date, phase)

        assert reason == "within_phase_dates"

    def test_determine_placement_reason_before_phase(self):
        """Test placement reason for documents before phase start."""
        doc_date = datetime(2023, 12, 25)  # Before phase starts
        phase = {
            "id": "phase1",
            "name": "Planning",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-15T00:00:00"
        }

        reason = self.summarizer._determine_placement_reason(doc_date, phase)

        assert "before_phase_start" in reason

    def test_calculate_timeline_relevance_perfect_match(self):
        """Test relevance calculation for perfect date match."""
        doc_date = datetime(2024, 1, 10)
        phase = {
            "id": "phase1",
            "name": "Planning",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-15T00:00:00"
        }

        relevance = self.summarizer._calculate_timeline_relevance(doc_date, phase)

        assert relevance == 1.0

    def test_calculate_timeline_relevance_outside_phase(self):
        """Test relevance calculation for dates outside phase range."""
        doc_date = datetime(2024, 3, 1)  # March 1st
        phase = {
            "id": "phase1",
            "name": "Planning",
            "start_date": "2024-01-01T00:00:00",  # January 1st
            "end_date": "2024-01-15T00:00:00"    # January 15th
        }

        relevance = self.summarizer._calculate_timeline_relevance(doc_date, phase)

        # Should be less than 1.0 but greater than 0
        assert 0 < relevance < 1.0

    def test_group_documents_by_phases(self):
        """Test grouping documents by timeline phases."""
        document_placements = [
            {
                "document_id": "doc1",
                "timeline_phase": "phase1",
                "relevance_score": 0.9
            },
            {
                "document_id": "doc2",
                "timeline_phase": "phase1",
                "relevance_score": 0.8
            },
            {
                "document_id": "doc3",
                "timeline_phase": "phase2",
                "relevance_score": 0.7
            }
        ]

        timeline_phases = [
            {
                "id": "phase1",
                "name": "Planning",
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-01-15T00:00:00"
            },
            {
                "id": "phase2",
                "name": "Development",
                "start_date": "2024-01-15T00:00:00",
                "end_date": "2024-02-15T00:00:00"
            }
        ]

        result = self.summarizer._group_documents_by_phases(document_placements, timeline_phases)

        assert "phase1" in result
        assert "phase2" in result
        assert result["phase1"]["document_count"] == 2
        assert result["phase2"]["document_count"] == 1
        assert result["phase1"]["avg_relevance"] == 0.85  # (0.9 + 0.8) / 2
        assert result["phase2"]["avg_relevance"] == 0.7

    def test_generate_timeline_recommendations_good_coverage(self):
        """Test timeline recommendations with good document coverage."""
        phase_documents = {
            "phase1": {"phase_name": "Planning", "document_count": 5, "avg_relevance": 0.8},
            "phase2": {"phase_name": "Development", "document_count": 3, "avg_relevance": 0.7}
        }
        timeline_phases = [
            {"id": "phase1", "name": "Planning"},
            {"id": "phase2", "name": "Development"}
        ]

        recommendations = self.summarizer._generate_timeline_recommendations(phase_documents, timeline_phases)

        # Should have positive recommendations
        assert len(recommendations) > 0
        assert any("good" in rec.lower() or "adequate" in rec.lower() for rec in recommendations)

    def test_generate_timeline_recommendations_poor_coverage(self):
        """Test timeline recommendations with poor document coverage."""
        phase_documents = {
            "phase1": {"phase_name": "Planning", "document_count": 0, "avg_relevance": 0.0},
            "phase2": {"phase_name": "Development", "document_count": 0, "avg_relevance": 0.0},
            "phase3": {"phase_name": "Testing", "document_count": 1, "avg_relevance": 0.3}
        }
        timeline_phases = [
            {"id": "phase1", "name": "Planning"},
            {"id": "phase2", "name": "Development"},
            {"id": "phase3", "name": "Testing"}
        ]

        recommendations = self.summarizer._generate_timeline_recommendations(phase_documents, timeline_phases)

        # Should have recommendations for improvement
        assert len(recommendations) > 0
        assert any("coverage is low" in rec.lower() or "consider adding" in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_generate_comprehensive_summary_report(self):
        """Test generating comprehensive summary report."""
        documents = [
            {
                "id": "doc1",
                "title": "API Documentation",
                "type": "api",
                "content": "This is API documentation content...",
                "dateCreated": "2024-01-01T10:00:00"
            },
            {
                "id": "doc2",
                "title": "User Guide",
                "type": "guide",
                "content": "This is user guide content...",
                "dateCreated": "2024-01-15T10:00:00"
            }
        ]

        timeline = {
            "phases": [
                {
                    "id": "phase1",
                    "name": "Planning",
                    "start_date": "2024-01-01T00:00:00",
                    "end_date": "2024-01-15T00:00:00"
                },
                {
                    "id": "phase2",
                    "name": "Development",
                    "start_date": "2024-01-15T00:00:00",
                    "end_date": "2024-02-15T00:00:00"
                }
            ]
        }

        result = await self.summarizer.generate_comprehensive_summary_report("sim_123", documents, timeline)

        assert result["simulation_id"] == "sim_123"
        assert result["report_generated"] is True
        assert "comprehensive_report_id" in result
        assert "sections_included" in result
        assert result["total_documents"] == 2

    def test_generate_executive_summary(self):
        """Test generating executive summary from report data."""
        recommendations = {
            "recommendations": [
                {"priority": "high", "description": "Critical recommendation"},
                {"priority": "medium", "description": "Medium recommendation"}
            ]
        }

        analysis = {
            "summary_statistics": {
                "average_quality_score": 0.75,
                "total_issues_found": 3
            }
        }

        timeline = {
            "placement_report": {
                "timeline_coverage": 0.8,
                "placed_documents": 8
            }
        }

        documents = [{"id": "doc1"}, {"id": "doc2"}]

        summary = self.summarizer._generate_executive_summary(recommendations, analysis, timeline, documents)

        assert summary["total_documents"] == 2
        assert summary["critical_issues"] == 1  # High priority recommendation
        assert summary["improvement_opportunities"] == 2
        assert len(summary["key_findings"]) > 0

    def test_generate_overall_assessment_high_score(self):
        """Test overall assessment generation with high scores."""
        sections = {
            "recommendations": {
                "total_recommendations": 3,
                "source": "summarizer-hub"
            },
            "analysis": {
                "average_quality_score": 0.9,
                "documents_with_issues": 0,
                "source": "analysis-service"
            },
            "timeline": {
                "timeline_coverage": 0.95,
                "source": "simulation-service"
            }
        }

        assessment = self.summarizer._generate_overall_assessment(sections)

        assert assessment["overall_health_score"] > 0.8
        assert assessment["risk_level"] == "low"
        assert len(assessment["strengths"]) > 0
        assert len(assessment["weaknesses"]) == 0

    def test_generate_overall_assessment_low_score(self):
        """Test overall assessment generation with low scores."""
        sections = {
            "recommendations": {
                "total_recommendations": 15,
                "source": "summarizer-hub"
            },
            "analysis": {
                "average_quality_score": 0.4,
                "documents_with_issues": 5,
                "source": "analysis-service"
            },
            "timeline": {
                "timeline_coverage": 0.3,
                "source": "simulation-service"
            }
        }

        assessment = self.summarizer._generate_overall_assessment(sections)

        assert assessment["overall_health_score"] < 0.6
        assert assessment["risk_level"] == "high"
        assert len(assessment["weaknesses"]) > 0
        assert len(assessment["strengths"]) >= 0

    def test_generate_action_items_from_sections(self):
        """Test generating action items from all report sections."""
        sections = {
            "recommendations": {
                "details": {
                    "recommendations": [
                        {
                            "priority": "high",
                            "description": "Critical recommendation",
                            "type": "consolidation",
                            "estimated_effort": "medium"
                        }
                    ]
                }
            },
            "analysis": {
                "details": {
                    "quality_analysis": [
                        {
                            "document_id": "doc1",
                            "quality_score": 0.3,
                            "issues_found": 2,
                            "issues": ["Issue 1", "Issue 2"]
                        }
                    ]
                }
            },
            "timeline": {
                "recommendations": ["Consider adding documentation for phase X"]
            }
        }

        action_items = self.summarizer._generate_action_items(sections)

        assert len(action_items) > 0
        # Should be sorted by priority (high first)
        assert action_items[0]["priority"] == "high"

        # Check that different types of action items are included
        action_types = {item["type"] for item in action_items}
        assert "recommendation" in action_types
        assert "quality_fix" in action_types
        assert "timeline_optimization" in action_types

    def test_combine_reports_into_summary_all_sections(self):
        """Test combining all report types into comprehensive summary."""
        recommendations = {
            "source": "summarizer-hub",
            "recommendations": [{"description": "Test recommendation"}],
            "consolidation_suggestions": [],
            "duplicate_analysis": [],
            "outdated_analysis": [],
            "quality_improvements": []
        }

        analysis = {
            "source": "analysis-service",
            "quality_analysis": [{"document_id": "doc1", "quality_score": 0.8}],
            "summary_statistics": {
                "average_quality_score": 0.8,
                "documents_with_issues": 1,
                "total_issues_found": 2
            },
            "processing_metadata": {
                "documents_processed": 1,
                "processing_time": "completed"
            }
        }

        timeline = {
            "timeline_phases": 2,
            "placed_documents": 1,
            "placement_report": {
                "timeline_coverage": 0.5,
                "recommendations": ["Add more documentation"]
            },
            "phase_breakdown": {}
        }

        documents = [{"id": "doc1"}]

        summary_report = self.summarizer._combine_reports_into_summary(
            "sim_123", recommendations, analysis, timeline, documents
        )

        assert summary_report["simulation_id"] == "sim_123"
        assert "executive_summary" in summary_report
        assert "overall_assessment" in summary_report
        assert "action_items" in summary_report
        assert "sections" in summary_report

        # Check all sections are included
        sections = summary_report["sections"]
        assert "recommendations" in sections
        assert "analysis" in sections
        assert "timeline" in sections

    def test_generate_comprehensive_markdown_report(self):
        """Test generating comprehensive markdown report."""
        report_data = {
            "report_id": "comprehensive_test_123",
            "simulation_id": "sim_123",
            "generated_at": "2024-01-01T10:00:00",
            "executive_summary": {
                "total_documents": 2,
                "critical_issues": 1,
                "improvement_opportunities": 3,
                "key_findings": ["Test finding 1", "Test finding 2"]
            },
            "overall_assessment": {
                "overall_health_score": 0.75,
                "risk_level": "medium",
                "strengths": ["Good coverage"],
                "weaknesses": ["Low quality scores"]
            },
            "sections": {
                "recommendations": {
                    "total_recommendations": 3,
                    "consolidation_opportunities": 1,
                    "duplicate_issues": 0,
                    "outdated_documents": 1,
                    "quality_improvements": 1
                },
                "analysis": {
                    "documents_analyzed": 2,
                    "average_quality_score": 0.75,
                    "documents_with_issues": 1,
                    "total_issues_found": 3
                },
                "timeline": {
                    "total_phases": 2,
                    "documents_placed": 2,
                    "timeline_coverage": 1.0
                }
            },
            "action_items": [
                {
                    "priority": "high",
                    "description": "Critical action",
                    "category": "quality",
                    "estimated_effort": "medium"
                }
            ]
        }

        markdown = self.summarizer._generate_comprehensive_markdown_report(report_data)

        # Check markdown structure
        assert "# 📊 Comprehensive Simulation Summary Report" in markdown
        assert "**Simulation ID:** sim_123" in markdown
        assert "## 📈 Executive Summary" in markdown
        assert "## 🎯 Overall Assessment" in markdown
        assert "## 💡 Recommendations" in markdown
        assert "## 🔍 Quality Analysis" in markdown
        assert "## 📅 Timeline Analysis" in markdown
        assert "## ✅ Action Items" in markdown
        assert "🚨 **High** - Critical action" in markdown  # Priority emoji and formatting

