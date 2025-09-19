"""Integration Tests for Mock Data Generator Workflow - Content Generation Testing.

This module contains integration tests for mock-data-generator service workflows,
testing end-to-end content generation, validation, and storage integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from simulation.infrastructure.clients.ecosystem_clients import (
    MockDataGeneratorClient, get_mock_data_generator_client
)
from simulation.infrastructure.content.content_generation_pipeline import (
    ContentGenerationPipeline
)
from simulation.domain.value_objects import (
    ProjectType, ComplexityLevel, DocumentType, DocumentMetadata
)


class TestMockDataGeneratorClientIntegration:
    """Test cases for Mock Data Generator client integration."""

    @pytest.fixture
    async def mock_client(self):
        """Create Mock Data Generator client for testing."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="mock_data_generator", endpoint=Mock(base_url="http://mock-service:5065", timeout_seconds=30))
        ]):
            client = MockDataGeneratorClient()
            yield client

    @pytest.mark.asyncio
    async def test_mock_client_initialization(self, mock_client):
        """Test Mock Data Generator client initialization."""
        assert mock_client is not None
        assert hasattr(mock_client, 'generate_project_documents')
        assert hasattr(mock_client, 'generate_timeline_events')
        assert hasattr(mock_client, 'generate_team_activities')
        assert hasattr(mock_client, 'generate_phase_documents')

    @pytest.mark.asyncio
    async def test_generate_project_documents_workflow(self, mock_client):
        """Test end-to-end project documents generation workflow."""
        # Mock the HTTP response
        with patch.object(mock_client, '_client') as mock_http_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "documents": [
                    {
                        "type": "confluence_page",
                        "title": "Project Requirements",
                        "content": "# Project Requirements\n\n## Overview\nDetailed requirements...",
                        "metadata": {
                            "author": "product@example.com",
                            "quality_score": 0.9
                        }
                    },
                    {
                        "type": "jira_ticket",
                        "title": "Setup CI/CD Pipeline",
                        "content": "Implement automated deployment pipeline...",
                        "metadata": {
                            "assignee": "dev@example.com",
                            "priority": "high"
                        }
                    }
                ],
                "generation_stats": {
                    "total_documents": 2,
                    "generation_time": 1.5,
                    "quality_score": 0.85
                }
            }
            mock_http_client.post.return_value = mock_response

            # Test the workflow
            request_data = {
                "project_type": "web_application",
                "complexity": "medium",
                "team_size": 5,
                "duration_weeks": 8
            }

            result = await mock_client.generate_project_documents(request_data)

            # Verify the request was made correctly
            mock_http_client.post.assert_called_once_with("/simulation/project-docs", request_data)

            # Verify the response structure
            assert "documents" in result
            assert len(result["documents"]) == 2
            assert "generation_stats" in result

            # Verify document structure
            first_doc = result["documents"][0]
            assert first_doc["type"] == "confluence_page"
            assert "title" in first_doc
            assert "content" in first_doc
            assert "metadata" in first_doc

    @pytest.mark.asyncio
    async def test_generate_timeline_events_integration(self, mock_client):
        """Test timeline events generation integration."""
        with patch.object(mock_client, '_client') as mock_http_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "events": [
                    {
                        "event_type": "milestone",
                        "title": "Sprint 1 Complete",
                        "date": (datetime.now() + timedelta(days=14)).isoformat(),
                        "description": "Completed first sprint with all planned features"
                    },
                    {
                        "event_type": "phase_start",
                        "title": "Development Phase Begins",
                        "date": (datetime.now() + timedelta(days=21)).isoformat(),
                        "description": "Starting development of core features"
                    }
                ],
                "timeline_stats": {
                    "total_events": 2,
                    "date_range": "4 weeks",
                    "event_types": ["milestone", "phase_start"]
                }
            }
            mock_http_client.post.return_value = mock_response

            request_data = {
                "project_id": "test-123",
                "duration_weeks": 8,
                "milestones": ["Sprint 1", "Development Start", "Beta Release"]
            }

            result = await mock_client.generate_timeline_events(request_data)

            assert "events" in result
            assert len(result["events"]) == 2
            assert "timeline_stats" in result

            # Verify event structure
            first_event = result["events"][0]
            assert first_event["event_type"] == "milestone"
            assert "date" in first_event
            assert "description" in first_event

    @pytest.mark.asyncio
    async def test_generate_team_activities_integration(self, mock_client):
        """Test team activities generation integration."""
        with patch.object(mock_client, '_client') as mock_http_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "activities": [
                    {
                        "member_id": "dev_001",
                        "activity_type": "code_commit",
                        "description": "Committed authentication module",
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"lines_changed": 150}
                    },
                    {
                        "member_id": "qa_001",
                        "activity_type": "test_execution",
                        "description": "Executed regression test suite",
                        "timestamp": (datetime.now() + timedelta(hours=2)).isoformat(),
                        "metadata": {"tests_passed": 45, "tests_failed": 2}
                    }
                ],
                "activity_stats": {
                    "total_activities": 2,
                    "unique_members": 2,
                    "activity_types": ["code_commit", "test_execution"],
                    "time_span": "2 hours"
                }
            }
            mock_http_client.post.return_value = mock_response

            request_data = {
                "team_members": ["dev_001", "qa_001", "pm_001"],
                "duration_hours": 8,
                "activity_types": ["code_commit", "test_execution", "meeting"]
            }

            result = await mock_client.generate_team_activities(request_data)

            assert "activities" in result
            assert len(result["activities"]) == 2
            assert "activity_stats" in result

            # Verify activity structure
            first_activity = result["activities"][0]
            assert "member_id" in first_activity
            assert "activity_type" in first_activity
            assert "timestamp" in first_activity

    @pytest.mark.asyncio
    async def test_generate_phase_documents_integration(self, mock_client):
        """Test phase-specific documents generation integration."""
        with patch.object(mock_client, '_client') as mock_http_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "phase_documents": [
                    {
                        "phase": "planning",
                        "documents": [
                            {
                                "type": "requirements_doc",
                                "title": "Requirements Specification",
                                "content": "# Requirements\n\n## Functional Requirements...",
                                "word_count": 1200
                            }
                        ]
                    },
                    {
                        "phase": "development",
                        "documents": [
                            {
                                "type": "design_doc",
                                "title": "System Architecture",
                                "content": "# Architecture\n\n## Overview...",
                                "word_count": 800
                            },
                            {
                                "type": "api_documentation",
                                "title": "API Reference",
                                "content": "# API Documentation\n\n## Endpoints...",
                                "word_count": 600
                            }
                        ]
                    }
                ],
                "phase_stats": {
                    "total_phases": 2,
                    "total_documents": 3,
                    "avg_quality_score": 0.88
                }
            }
            mock_http_client.post.return_value = mock_response

            request_data = {
                "project_phases": ["planning", "development", "testing"],
                "phase_requirements": {
                    "planning": ["requirements_doc"],
                    "development": ["design_doc", "api_documentation"],
                    "testing": ["test_plan"]
                }
            }

            result = await mock_client.generate_phase_documents(request_data)

            assert "phase_documents" in result
            assert len(result["phase_documents"]) == 2
            assert "phase_stats" in result

            # Verify phase document structure
            planning_phase = result["phase_documents"][0]
            assert planning_phase["phase"] == "planning"
            assert len(planning_phase["documents"]) == 1

    @pytest.mark.asyncio
    async def test_generate_ecosystem_scenario_integration(self, mock_client):
        """Test ecosystem scenario generation integration."""
        with patch.object(mock_client, '_client') as mock_http_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "scenario": {
                    "name": "E-commerce Platform Development",
                    "description": "Comprehensive e-commerce platform with microservices",
                    "components": [
                        {
                            "service": "user_service",
                            "documents": ["api_doc", "deployment_guide"],
                            "complexity": "medium"
                        },
                        {
                            "service": "payment_service",
                            "documents": ["security_audit", "compliance_report"],
                            "complexity": "high"
                        }
                    ],
                    "integration_points": [
                        "user_authentication",
                        "payment_processing",
                        "order_management"
                    ]
                },
                "scenario_stats": {
                    "total_services": 2,
                    "total_documents": 4,
                    "complexity_distribution": {"medium": 1, "high": 1}
                }
            }
            mock_http_client.post.return_value = mock_response

            request_data = {
                "scenario_type": "ecommerce_platform",
                "services": ["user_service", "payment_service", "order_service"],
                "integration_requirements": ["authentication", "payment", "inventory"]
            }

            result = await mock_client.generate_ecosystem_scenario(request_data)

            assert "scenario" in result
            assert "scenario_stats" in result

            # Verify scenario structure
            scenario = result["scenario"]
            assert "name" in scenario
            assert "components" in scenario
            assert len(scenario["components"]) == 2


class TestContentGenerationPipelineIntegration:
    """Test cases for Content Generation Pipeline integration."""

    @pytest.fixture
    async def pipeline(self):
        """Create Content Generation Pipeline for testing."""
        with patch('simulation.infrastructure.content.content_generation_pipeline.get_mock_data_generator_client') as mock_get_client, \
             patch('simulation.infrastructure.content.content_generation_pipeline.get_doc_store_client') as mock_get_doc_store, \
             patch('simulation.infrastructure.content.content_generation_pipeline.get_analysis_service_client') as mock_get_analysis:

            # Create mock clients
            mock_client = AsyncMock()
            mock_doc_store = AsyncMock()
            mock_analysis = AsyncMock()

            mock_get_client.return_value = mock_client
            mock_get_doc_store.return_value = mock_doc_store
            mock_get_analysis.return_value = mock_analysis

            pipeline = ContentGenerationPipeline()
            yield pipeline

    @pytest.mark.asyncio
    async def test_pipeline_execute_document_generation(self, pipeline):
        """Test pipeline document generation execution."""
        # Mock the mock-data-generator response
        pipeline.mock_data_client.generate_project_documents.return_value = {
            "documents": [
                {
                    "type": "confluence_page",
                    "title": "Test Document",
                    "content": "# Test Content",
                    "metadata": {"quality_score": 0.9}
                }
            ]
        }

        # Mock analysis response
        pipeline.analysis_client.analyze_documents.return_value = {
            "overall_quality": 0.9,
            "issues": [],
            "recommendations": ["Good quality document"]
        }

        # Mock doc store response
        pipeline.doc_store_client.store_document.return_value = "doc_123"

        phase_config = {
            "phase": "planning",
            "project_type": "web_application",
            "complexity": "medium",
            "team_size": 5
        }

        result = await pipeline.execute_document_generation(phase_config)

        assert isinstance(result, list)
        assert len(result) > 0

        # Verify interactions
        pipeline.mock_data_client.generate_project_documents.assert_called_once()
        pipeline.analysis_client.analyze_documents.assert_called_once()
        pipeline.doc_store_client.store_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_pipeline_confluence_documents_generation(self, pipeline):
        """Test Confluence documents generation in pipeline."""
        # Setup mock responses
        pipeline.mock_data_client.generate_project_documents.return_value = {
            "documents": [
                {
                    "type": "confluence_page",
                    "title": "Requirements Document",
                    "content": "# Requirements\n\n## Overview\nRequirements here...",
                    "metadata": {"space": "Engineering", "quality_score": 0.85}
                }
            ]
        }

        pipeline.analysis_client.analyze_documents.return_value = {
            "overall_quality": 0.85,
            "issues": [],
            "recommendations": ["Well-structured document"]
        }

        pipeline.doc_store_client.store_document.return_value = "confluence_doc_123"

        phase_config = {
            "phase": "planning",
            "document_types": ["confluence_page"],
            "project_name": "Test Project"
        }

        documents = await pipeline.execute_document_generation(phase_config)

        assert len(documents) == 1
        doc = documents[0]
        assert doc["type"] == "confluence_page"
        assert "Requirements Document" in doc["title"]
        assert "# Requirements" in doc["content"]

    @pytest.mark.asyncio
    async def test_pipeline_jira_tickets_generation(self, pipeline):
        """Test JIRA tickets generation in pipeline."""
        pipeline.mock_data_client.generate_project_documents.return_value = {
            "documents": [
                {
                    "type": "jira_ticket",
                    "title": "Implement User Authentication",
                    "content": "As a user, I want to login...",
                    "metadata": {"priority": "high", "assignee": "dev@example.com"}
                }
            ]
        }

        pipeline.analysis_client.analyze_documents.return_value = {
            "overall_quality": 0.9,
            "issues": [],
            "recommendations": ["Clear acceptance criteria"]
        }

        pipeline.doc_store_client.store_document.return_value = "jira_ticket_123"

        phase_config = {
            "phase": "development",
            "document_types": ["jira_ticket"],
            "project_key": "PROJ"
        }

        documents = await pipeline.execute_document_generation(phase_config)

        assert len(documents) == 1
        doc = documents[0]
        assert doc["type"] == "jira_ticket"
        assert "Authentication" in doc["title"]

    @pytest.mark.asyncio
    async def test_pipeline_github_prs_generation(self, pipeline):
        """Test GitHub PRs generation in pipeline."""
        pipeline.mock_data_client.generate_project_documents.return_value = {
            "documents": [
                {
                    "type": "github_pr",
                    "title": "feat: Add user authentication",
                    "content": "## Description\nImplements user login functionality...",
                    "metadata": {"base_branch": "main", "head_branch": "feature/auth"}
                }
            ]
        }

        pipeline.analysis_client.analyze_documents.return_value = {
            "overall_quality": 0.88,
            "issues": [],
            "recommendations": ["Good PR description"]
        }

        pipeline.doc_store_client.store_document.return_value = "github_pr_123"

        phase_config = {
            "phase": "development",
            "document_types": ["github_pr"],
            "repository": "myorg/myproject"
        }

        documents = await pipeline.execute_document_generation(phase_config)

        assert len(documents) == 1
        doc = documents[0]
        assert doc["type"] == "github_pr"
        assert doc["title"].startswith("feat:")


class TestContentValidationIntegration:
    """Test cases for content validation integration."""

    @pytest.mark.asyncio
    async def test_content_quality_validation_integration(self):
        """Test content quality validation with analysis service."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis:
            mock_analysis_client = AsyncMock()
            mock_get_analysis.return_value = mock_analysis_client

            # Mock analysis response
            mock_analysis_client.analyze_documents.return_value = {
                "documents": [
                    {
                        "id": "doc_1",
                        "quality_score": 0.85,
                        "issues": ["Minor formatting issue"],
                        "recommendations": ["Use consistent heading styles"]
                    }
                ],
                "overall_quality": 0.85,
                "summary": "Good quality with minor issues"
            }

            from simulation.infrastructure.clients.ecosystem_clients import get_analysis_service_client
            analysis_client = get_analysis_service_client()

            documents = [
                {
                    "id": "doc_1",
                    "content": "# Test Document\n\n## Section\nContent here...",
                    "type": "confluence_page"
                }
            ]

            result = await analysis_client.analyze_documents(documents)

            assert "overall_quality" in result
            assert result["overall_quality"] == 0.85
            assert len(result["documents"]) == 1

    @pytest.mark.asyncio
    async def test_content_storage_validation_integration(self):
        """Test content storage validation with doc store."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_doc_store_client') as mock_get_doc_store:
            mock_doc_store_client = AsyncMock()
            mock_get_doc_store.return_value = mock_doc_store_client

            # Mock storage response
            mock_doc_store_client.store_document.return_value = "stored_doc_123"

            from simulation.infrastructure.clients.ecosystem_clients import get_doc_store_client
            doc_store_client = get_doc_store_client()

            document_id = await doc_store_client.store_document(
                title="Test Document",
                content="# Test Content",
                metadata={"quality_score": 0.9, "author": "test@example.com"}
            )

            assert document_id == "stored_doc_123"
            mock_doc_store_client.store_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_content_retrieval_validation_integration(self):
        """Test content retrieval validation."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_doc_store_client') as mock_get_doc_store:
            mock_doc_store_client = AsyncMock()
            mock_get_doc_store.return_value = mock_doc_store_client

            # Mock retrieval response
            mock_doc_store_client.get_document.return_value = {
                "id": "doc_123",
                "title": "Retrieved Document",
                "content": "# Retrieved Content",
                "metadata": {"quality_score": 0.9}
            }

            from simulation.infrastructure.clients.ecosystem_clients import get_doc_store_client
            doc_store_client = get_doc_store_client()

            document = await doc_store_client.get_document("doc_123")

            assert document is not None
            assert document["title"] == "Retrieved Document"
            assert document["metadata"]["quality_score"] == 0.9


class TestEndToEndContentGenerationWorkflow:
    """Test cases for end-to-end content generation workflow."""

    @pytest.mark.asyncio
    async def test_complete_content_generation_workflow(self):
        """Test complete content generation workflow from request to storage."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_mock_data_generator_client') as mock_get_mock_client, \
             patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis, \
             patch('simulation.infrastructure.clients.ecosystem_clients.get_doc_store_client') as mock_get_doc_store:

            # Setup mock clients
            mock_client = AsyncMock()
            analysis_client = AsyncMock()
            doc_store_client = AsyncMock()

            mock_get_mock_client.return_value = mock_client
            mock_get_analysis.return_value = analysis_client
            mock_get_doc_store.return_value = doc_store_client

            # Mock the generation response
            mock_client.generate_project_documents.return_value = {
                "documents": [
                    {
                        "type": "confluence_page",
                        "title": "Project Architecture",
                        "content": "# Architecture\n\n## Overview\nSystem architecture...",
                        "metadata": {"quality_score": 0.9}
                    }
                ],
                "generation_stats": {"total_documents": 1}
            }

            # Mock analysis response
            analysis_client.analyze_documents.return_value = {
                "overall_quality": 0.9,
                "issues": [],
                "recommendations": ["Excellent document quality"]
            }

            # Mock storage response
            doc_store_client.store_document.return_value = "arch_doc_123"

            # Execute the workflow
            from simulation.infrastructure.content.content_generation_pipeline import ContentGenerationPipeline
            pipeline = ContentGenerationPipeline()

            phase_config = {
                "phase": "design",
                "project_type": "web_application",
                "document_types": ["architecture_doc"],
                "complexity": "high"
            }

            generated_documents = await pipeline.execute_document_generation(phase_config)

            # Verify the complete workflow
            assert len(generated_documents) == 1
            doc = generated_documents[0]
            assert doc["type"] == "confluence_page"
            assert doc["title"] == "Project Architecture"
            assert "Architecture" in doc["content"]

            # Verify all service interactions occurred
            mock_client.generate_project_documents.assert_called_once()
            analysis_client.analyze_documents.assert_called_once()
            doc_store_client.store_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_content_generation_error_handling(self):
        """Test error handling in content generation workflow."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_mock_data_generator_client') as mock_get_mock_client:
            mock_client = AsyncMock()
            mock_get_mock_client.return_value = mock_client

            # Mock a failure in generation
            mock_client.generate_project_documents.side_effect = Exception("Generation service unavailable")

            from simulation.infrastructure.content.content_generation_pipeline import ContentGenerationPipeline
            pipeline = ContentGenerationPipeline()

            phase_config = {"phase": "planning", "project_type": "web_app"}

            # Should handle the error gracefully
            with pytest.raises(Exception, match="Generation service unavailable"):
                await pipeline.execute_document_generation(phase_config)

    @pytest.mark.asyncio
    async def test_content_generation_with_validation_failures(self):
        """Test content generation with validation failures."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_mock_data_generator_client') as mock_get_mock_client, \
             patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis:

            mock_client = AsyncMock()
            analysis_client = AsyncMock()

            mock_get_mock_client.return_value = mock_client
            mock_get_analysis.return_value = analysis_client

            # Mock generation success
            mock_client.generate_project_documents.return_value = {
                "documents": [{"type": "invalid_doc", "title": "", "content": ""}]
            }

            # Mock analysis failure (low quality)
            analysis_client.analyze_documents.return_value = {
                "overall_quality": 0.3,
                "issues": ["Missing title", "Empty content", "Poor formatting"],
                "recommendations": ["Add proper title", "Include meaningful content"]
            }

            from simulation.infrastructure.content.content_generation_pipeline import ContentGenerationPipeline
            pipeline = ContentGenerationPipeline()

            phase_config = {"phase": "planning", "quality_threshold": 0.7}

            # This should complete but with warnings about quality
            documents = await pipeline.execute_document_generation(phase_config)

            assert len(documents) == 1
            # In a real implementation, this might filter out low-quality documents
            # or mark them for revision


class TestContentGenerationPerformance:
    """Test cases for content generation performance."""

    @pytest.mark.asyncio
    async def test_content_generation_performance(self):
        """Test content generation performance metrics."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_mock_data_generator_client') as mock_get_mock_client, \
             patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis, \
             patch('simulation.infrastructure.clients.ecosystem_clients.get_doc_store_client') as mock_get_doc_store:

            mock_client = AsyncMock()
            analysis_client = AsyncMock()
            doc_store_client = AsyncMock()

            mock_get_mock_client.return_value = mock_client
            mock_get_analysis.return_value = analysis_client
            mock_get_doc_store.return_value = doc_store_client

            # Mock responses with timing data
            mock_client.generate_project_documents.return_value = {
                "documents": [
                    {"type": "confluence_page", "title": "Test", "content": "Content", "metadata": {}}
                ],
                "generation_time": 0.5
            }

            analysis_client.analyze_documents.return_value = {
                "overall_quality": 0.9,
                "analysis_time": 0.2
            }

            doc_store_client.store_document.return_value = "doc_123"

            from simulation.infrastructure.content.content_generation_pipeline import ContentGenerationPipeline
            pipeline = ContentGenerationPipeline()

            import time
            start_time = time.time()

            phase_config = {"phase": "planning", "performance_tracking": True}
            documents = await pipeline.execute_document_generation(phase_config)

            end_time = time.time()
            total_time = end_time - start_time

            # Verify performance is reasonable
            assert total_time < 2.0  # Should complete within 2 seconds
            assert len(documents) == 1

    @pytest.mark.asyncio
    async def test_concurrent_content_generation(self):
        """Test concurrent content generation for multiple phases."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_mock_data_generator_client') as mock_get_mock_client:
            mock_client = AsyncMock()
            mock_get_mock_client.return_value = mock_client

            # Mock responses for different phases
            def mock_generate(request_data):
                phase = request_data.get("phase", "unknown")
                return {
                    "documents": [
                        {
                            "type": "confluence_page",
                            "title": f"{phase.title()} Phase Document",
                            "content": f"# {phase.title()} Content",
                            "metadata": {"phase": phase}
                        }
                    ]
                }

            mock_client.generate_project_documents.side_effect = mock_generate

            from simulation.infrastructure.content.content_generation_pipeline import ContentGenerationPipeline

            async def generate_phase_docs(phase: str):
                pipeline = ContentGenerationPipeline()
                config = {"phase": phase, "project_type": "web_app"}
                return await pipeline.execute_document_generation(config)

            # Generate documents for multiple phases concurrently
            phases = ["planning", "design", "development", "testing"]
            tasks = [generate_phase_docs(phase) for phase in phases]
            results = await asyncio.gather(*tasks)

            # Verify all phases generated documents
            assert len(results) == 4
            for result in results:
                assert len(result) == 1
                doc = result[0]
                assert doc["type"] == "confluence_page"
                assert "Phase Document" in doc["title"]
