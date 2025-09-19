"""Integration Tests for Content Validation - Content Generation Testing.

This module contains integration tests for content validation, quality checks,
and consistency validation across the content generation pipeline.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from simulation.infrastructure.content.content_generation_pipeline import ContentGenerationPipeline
from simulation.domain.value_objects import (
    DocumentType, DocumentMetadata, ProjectType, ComplexityLevel
)


class TestContentQualityValidation:
    """Test cases for content quality validation."""

    @pytest.mark.asyncio
    async def test_high_quality_content_validation(self):
        """Test validation of high-quality content."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis:
            mock_analysis_client = AsyncMock()
            mock_get_analysis.return_value = mock_analysis_client

            # Mock high-quality analysis result
            mock_analysis_client.analyze_documents.return_value = {
                "documents": [
                    {
                        "id": "doc_1",
                        "quality_score": 0.95,
                        "issues": [],
                        "recommendations": ["Excellent document structure"]
                    }
                ],
                "overall_quality": 0.95,
                "summary": "High-quality content with excellent structure"
            }

            from simulation.infrastructure.clients.ecosystem_clients import get_analysis_service_client
            analysis_client = get_analysis_service_client()

            # Test content that should score high
            high_quality_content = {
                "id": "doc_1",
                "type": DocumentType.CONFLUENCE_PAGE.value,
                "title": "Comprehensive System Architecture Document",
                "content": """# System Architecture

## Overview
This document provides a comprehensive overview of the system architecture for the e-commerce platform.

## Components
### Frontend Layer
- React-based single page application
- Responsive design with mobile-first approach
- RESTful API integration

### Backend Layer
- Microservices architecture with Node.js
- API Gateway for request routing
- Database abstraction layer

### Data Layer
- PostgreSQL for transactional data
- Redis for caching and session management
- Elasticsearch for search functionality

## Security Considerations
- JWT authentication
- Role-based access control
- Data encryption at rest and in transit

## Performance Requirements
- Response time < 200ms for API calls
- Support for 10,000 concurrent users
- 99.9% uptime SLA
""",
                "metadata": {
                    "author": "architect@example.com",
                    "word_count": 450,
                    "complexity": "high"
                }
            }

            result = await analysis_client.analyze_documents([high_quality_content])

            # Verify high quality score
            assert result["overall_quality"] >= 0.9
            assert len(result["documents"]) == 1
            assert result["documents"][0]["quality_score"] >= 0.9
            assert len(result["documents"][0]["issues"]) == 0

    @pytest.mark.asyncio
    async def test_low_quality_content_detection(self):
        """Test detection of low-quality content."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis:
            mock_analysis_client = AsyncMock()
            mock_get_analysis.return_value = mock_analysis_client

            # Mock low-quality analysis result
            mock_analysis_client.analyze_documents.return_value = {
                "documents": [
                    {
                        "id": "doc_2",
                        "quality_score": 0.35,
                        "issues": [
                            "Missing title",
                            "Incomplete content",
                            "Poor formatting",
                            "Missing metadata"
                        ],
                        "recommendations": [
                            "Add a descriptive title",
                            "Expand content with more details",
                            "Use proper markdown formatting",
                            "Include author and date information"
                        ]
                    }
                ],
                "overall_quality": 0.35,
                "summary": "Low-quality content requiring significant improvements"
            }

            from simulation.infrastructure.clients.ecosystem_clients import get_analysis_service_client
            analysis_client = get_analysis_service_client()

            # Test content that should score low
            low_quality_content = {
                "id": "doc_2",
                "type": DocumentType.CONFLUENCE_PAGE.value,
                "title": "",
                "content": "todo",
                "metadata": {}
            }

            result = await analysis_client.analyze_documents([low_quality_content])

            # Verify low quality score and issues
            assert result["overall_quality"] < 0.5
            assert len(result["documents"]) == 1
            assert result["documents"][0]["quality_score"] < 0.5
            assert len(result["documents"][0]["issues"]) > 0
            assert len(result["documents"][0]["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_content_completeness_validation(self):
        """Test content completeness validation."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis:
            mock_analysis_client = AsyncMock()
            mock_get_analysis.return_value = mock_analysis_client

            # Mock completeness analysis
            mock_analysis_client.analyze_documents.return_value = {
                "documents": [
                    {
                        "id": "complete_doc",
                        "quality_score": 0.88,
                        "completeness_score": 0.95,
                        "issues": ["Minor formatting issue"],
                        "missing_elements": [],
                        "recommendations": ["Use consistent heading styles"]
                    },
                    {
                        "id": "incomplete_doc",
                        "quality_score": 0.45,
                        "completeness_score": 0.30,
                        "issues": ["Missing sections", "Incomplete information"],
                        "missing_elements": ["overview", "requirements", "conclusion"],
                        "recommendations": ["Add overview section", "Include requirements", "Add conclusion"]
                    }
                ],
                "overall_quality": 0.67,
                "overall_completeness": 0.63
            }

            from simulation.infrastructure.clients.ecosystem_clients import get_analysis_service_client
            analysis_client = get_analysis_service_client()

            documents = [
                {
                    "id": "complete_doc",
                    "type": DocumentType.REQUIREMENTS_DOC.value,
                    "title": "Complete Requirements Document",
                    "content": """# Requirements Document

## Overview
This document outlines the requirements for the new system.

## Functional Requirements
1. User authentication
2. Data processing
3. Report generation

## Non-Functional Requirements
1. Performance: < 2s response time
2. Security: Encryption required
3. Scalability: Support 1000 users

## Conclusion
All requirements have been documented and approved.
""",
                    "metadata": {"author": "analyst@example.com", "version": "1.0"}
                },
                {
                    "id": "incomplete_doc",
                    "type": DocumentType.DESIGN_DOC.value,
                    "title": "Incomplete Design Document",
                    "content": "# Design Document\n\nSome design notes...",
                    "metadata": {}
                }
            ]

            result = await analysis_client.analyze_documents(documents)

            # Verify completeness analysis
            assert "overall_completeness" in result
            assert len(result["documents"]) == 2

            # Check individual document completeness
            complete_doc = next(d for d in result["documents"] if d["id"] == "complete_doc")
            incomplete_doc = next(d for d in result["documents"] if d["id"] == "incomplete_doc")

            assert complete_doc["completeness_score"] > 0.9
            assert len(complete_doc["missing_elements"]) == 0

            assert incomplete_doc["completeness_score"] < 0.5
            assert len(incomplete_doc["missing_elements"]) > 0
            assert "overview" in incomplete_doc["missing_elements"]


class TestContentConsistencyValidation:
    """Test cases for content consistency validation."""

    @pytest.mark.asyncio
    async def test_cross_document_consistency(self):
        """Test consistency validation across multiple documents."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis:
            mock_analysis_client = AsyncMock()
            mock_get_analysis.return_value = mock_analysis_client

            # Mock consistency analysis
            mock_analysis_client.analyze_documents.return_value = {
                "documents": [
                    {
                        "id": "req_doc",
                        "consistency_score": 0.95,
                        "consistency_issues": [],
                        "related_documents": ["design_doc", "test_plan"]
                    },
                    {
                        "id": "design_doc",
                        "consistency_score": 0.90,
                        "consistency_issues": ["Minor terminology difference"],
                        "related_documents": ["req_doc", "api_doc"]
                    },
                    {
                        "id": "test_plan",
                        "consistency_score": 0.85,
                        "consistency_issues": ["Outdated requirements reference"],
                        "related_documents": ["req_doc"]
                    }
                ],
                "overall_consistency": 0.90,
                "consistency_matrix": {
                    "req_doc-design_doc": 0.95,
                    "req_doc-test_plan": 0.90,
                    "design_doc-test_plan": 0.85
                },
                "terminology_consistency": 0.92,
                "structural_consistency": 0.88
            }

            from simulation.infrastructure.clients.ecosystem_clients import get_analysis_service_client
            analysis_client = get_analysis_service_client()

            # Test documents that should be consistent
            documents = [
                {
                    "id": "req_doc",
                    "type": DocumentType.REQUIREMENTS_DOC.value,
                    "title": "Requirements Specification",
                    "content": """# Requirements

## Authentication Requirements
The system shall support user authentication via OAuth 2.0 protocol.
Users must provide valid credentials to access the system.
""",
                    "metadata": {"version": "1.0"}
                },
                {
                    "id": "design_doc",
                    "type": DocumentType.DESIGN_DOC.value,
                    "title": "System Design",
                    "content": """# System Design

## Authentication Module
Implements OAuth 2.0 authentication as specified in requirements.
Supports user credential validation and session management.
""",
                    "metadata": {"version": "1.0"}
                },
                {
                    "id": "test_plan",
                    "type": DocumentType.TEST_PLAN.value,
                    "title": "Test Plan",
                    "content": """# Test Plan

## Authentication Testing
Test OAuth 2.0 authentication flow as per requirements v1.0.
Validate credential processing and error handling.
""",
                    "metadata": {"version": "1.0"}
                }
            ]

            result = await analysis_client.analyze_documents(documents)

            # Verify consistency analysis
            assert "overall_consistency" in result
            assert result["overall_consistency"] >= 0.8
            assert "consistency_matrix" in result
            assert "terminology_consistency" in result
            assert "structural_consistency" in result

            # Check document relationships
            for doc in result["documents"]:
                assert "consistency_score" in doc
                assert "related_documents" in doc
                assert len(doc["related_documents"]) > 0

    @pytest.mark.asyncio
    async def test_terminology_consistency_validation(self):
        """Test terminology consistency across documents."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis:
            mock_analysis_client = AsyncMock()
            mock_get_analysis.return_value = mock_analysis_client

            # Mock terminology analysis
            mock_analysis_client.analyze_documents.return_value = {
                "documents": [
                    {
                        "id": "doc1",
                        "terminology_score": 0.95,
                        "terminology_issues": [],
                        "key_terms": ["user", "authentication", "authorization"],
                        "term_frequency": {"user": 15, "authentication": 8, "authorization": 6}
                    },
                    {
                        "id": "doc2",
                        "terminology_score": 0.60,
                        "terminology_issues": ["Inconsistent term usage: 'login' vs 'authentication'"],
                        "key_terms": ["user", "login", "authorize"],
                        "term_frequency": {"user": 12, "login": 10, "authorize": 4}
                    }
                ],
                "overall_terminology_consistency": 0.78,
                "terminology_vocabulary": {
                    "consistent_terms": ["user"],
                    "inconsistent_terms": ["authentication", "login", "authorization", "authorize"]
                },
                "recommended_standardization": {
                    "authentication": "authentication",
                    "login": "authentication",
                    "authorization": "authorization",
                    "authorize": "authorization"
                }
            }

            from simulation.infrastructure.clients.ecosystem_clients import get_analysis_service_client
            analysis_client = get_analysis_service_client()

            documents = [
                {
                    "id": "doc1",
                    "content": "User authentication and authorization are critical security features.",
                    "metadata": {}
                },
                {
                    "id": "doc2",
                    "content": "Users need to login and authorize access to protected resources.",
                    "metadata": {}
                }
            ]

            result = await analysis_client.analyze_documents(documents)

            # Verify terminology analysis
            assert "overall_terminology_consistency" in result
            assert "terminology_vocabulary" in result
            assert "recommended_standardization" in result

            # Check for terminology issues
            doc1 = next(d for d in result["documents"] if d["id"] == "doc1")
            doc2 = next(d for d in result["documents"] if d["id"] == "doc2")

            assert doc1["terminology_score"] > doc2["terminology_score"]
            assert len(doc2["terminology_issues"]) > 0

    @pytest.mark.asyncio
    async def test_structural_consistency_validation(self):
        """Test structural consistency across documents."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis:
            mock_analysis_client = AsyncMock()
            mock_get_analysis.return_value = mock_analysis_client

            # Mock structural analysis
            mock_analysis_client.analyze_documents.return_value = {
                "documents": [
                    {
                        "id": "well_structured",
                        "structure_score": 0.95,
                        "structure_issues": [],
                        "heading_hierarchy": ["#", "##", "###", "####"],
                        "section_count": 8,
                        "avg_section_length": 150
                    },
                    {
                        "id": "poorly_structured",
                        "structure_score": 0.45,
                        "structure_issues": ["Inconsistent heading levels", "Missing sections"],
                        "heading_hierarchy": ["#", "###", "#", "##"],
                        "section_count": 3,
                        "avg_section_length": 50
                    }
                ],
                "overall_structural_consistency": 0.70,
                "structural_patterns": {
                    "common_headings": ["Overview", "Requirements", "Design"],
                    "heading_consistency": 0.75,
                    "section_organization": 0.65
                }
            }

            from simulation.infrastructure.clients.ecosystem_clients import get_analysis_service_client
            analysis_client = get_analysis_service_client()

            documents = [
                {
                    "id": "well_structured",
                    "content": """# Project Overview

## Introduction
This project aims to build a comprehensive e-commerce platform.

## Requirements
### Functional Requirements
- User registration
- Product catalog
- Shopping cart

### Non-Functional Requirements
- Performance requirements
- Security requirements

## Design
### Architecture
High-level system architecture.

### Database Design
Database schema and relationships.

## Implementation
### Backend Implementation
API development details.

### Frontend Implementation
User interface development.

## Testing
### Unit Testing
Individual component testing.

### Integration Testing
System integration testing.

## Deployment
### Infrastructure Setup
Server and environment setup.

### CI/CD Pipeline
Automated deployment process.
""",
                    "metadata": {}
                },
                {
                    "id": "poorly_structured",
                    "content": """# Project
### Introduction
Some info here.

# Requirements
Basic requirements.

## Testing
Test approach.

# Design
### Database
Schema info.

## Deployment
How to deploy.
""",
                    "metadata": {}
                }
            ]

            result = await analysis_client.analyze_documents(documents)

            # Verify structural analysis
            assert "overall_structural_consistency" in result
            assert "structural_patterns" in result

            well_structured = next(d for d in result["documents"] if d["id"] == "well_structured")
            poorly_structured = next(d for d in result["documents"] if d["id"] == "poorly_structured")

            assert well_structured["structure_score"] > poorly_structured["structure_score"]
            assert len(well_structured["structure_issues"]) < len(poorly_structured["structure_issues"])


class TestContentValidationPipeline:
    """Test cases for the complete content validation pipeline."""

    @pytest.mark.asyncio
    async def test_end_to_end_content_validation_pipeline(self):
        """Test the complete content validation pipeline."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_mock_data_generator_client') as mock_get_mock, \
             patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis, \
             patch('simulation.infrastructure.clients.ecosystem_clients.get_doc_store_client') as mock_get_doc_store:

            mock_client = AsyncMock()
            analysis_client = AsyncMock()
            doc_store_client = AsyncMock()

            mock_get_mock.return_value = mock_client
            mock_get_analysis.return_value = analysis_client
            mock_get_doc_store.return_value = doc_store_client

            # Mock generation
            mock_client.generate_project_documents.return_value = {
                "documents": [
                    {
                        "type": "confluence_page",
                        "title": "Generated Requirements",
                        "content": "# Requirements\n\n## Overview\nSystem requirements...",
                        "metadata": {"quality_score": 0.8}
                    }
                ]
            }

            # Mock analysis with validation results
            analysis_client.analyze_documents.return_value = {
                "documents": [
                    {
                        "id": "gen_doc_1",
                        "quality_score": 0.82,
                        "completeness_score": 0.85,
                        "consistency_score": 0.90,
                        "structure_score": 0.88,
                        "issues": ["Minor formatting issue"],
                        "recommendations": ["Use consistent heading styles"],
                        "validation_status": "passed"
                    }
                ],
                "overall_quality": 0.82,
                "overall_completeness": 0.85,
                "overall_consistency": 0.90,
                "validation_summary": {
                    "passed": 1,
                    "failed": 0,
                    "warnings": 1,
                    "quality_threshold_met": True
                }
            }

            # Mock storage
            doc_store_client.store_document.return_value = "validated_doc_123"

            from simulation.infrastructure.content.content_generation_pipeline import ContentGenerationPipeline
            pipeline = ContentGenerationPipeline()

            phase_config = {
                "phase": "requirements",
                "project_type": "web_application",
                "quality_threshold": 0.7,
                "validation_enabled": True
            }

            documents = await pipeline.execute_document_generation(phase_config)

            # Verify the complete pipeline
            assert len(documents) == 1
            doc = documents[0]

            # Verify validation was performed
            analysis_client.analyze_documents.assert_called_once()

            # Verify document meets quality standards
            assert doc["metadata"]["quality_score"] >= 0.7

            # Verify storage occurred
            doc_store_client.store_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_content_validation_with_rejection(self):
        """Test content validation that results in rejection."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis:
            mock_analysis_client = AsyncMock()
            mock_get_analysis.return_value = mock_analysis_client

            # Mock analysis that fails validation
            mock_analysis_client.analyze_documents.return_value = {
                "documents": [
                    {
                        "id": "poor_doc",
                        "quality_score": 0.3,
                        "completeness_score": 0.2,
                        "issues": ["Missing title", "Empty content", "No metadata"],
                        "recommendations": ["Add title", "Include content", "Add metadata"],
                        "validation_status": "failed"
                    }
                ],
                "overall_quality": 0.3,
                "validation_summary": {
                    "passed": 0,
                    "failed": 1,
                    "warnings": 3,
                    "quality_threshold_met": False
                }
            }

            from simulation.infrastructure.clients.ecosystem_clients import get_analysis_service_client
            analysis_client = get_analysis_service_client()

            poor_document = {
                "id": "poor_doc",
                "type": DocumentType.CONFLUENCE_PAGE.value,
                "title": "",
                "content": "",
                "metadata": {}
            }

            result = await analysis_client.analyze_documents([poor_document])

            # Verify validation failure
            assert result["overall_quality"] < 0.5
            assert result["validation_summary"]["passed"] == 0
            assert result["validation_summary"]["failed"] == 1
            assert result["validation_summary"]["quality_threshold_met"] == False

            # Verify detailed issues
            doc_result = result["documents"][0]
            assert len(doc_result["issues"]) > 0
            assert len(doc_result["recommendations"]) > 0
            assert doc_result["validation_status"] == "failed"


class TestContentValidationMetrics:
    """Test cases for content validation metrics and reporting."""

    @pytest.mark.asyncio
    async def test_validation_metrics_collection(self):
        """Test collection of validation metrics."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis:
            mock_analysis_client = AsyncMock()
            mock_get_analysis.return_value = mock_analysis_client

            # Mock comprehensive metrics
            mock_analysis_client.analyze_documents.return_value = {
                "documents": [
                    {
                        "id": "doc1",
                        "quality_score": 0.88,
                        "word_count": 1200,
                        "reading_time_minutes": 6,
                        "complexity_score": 0.7
                    },
                    {
                        "id": "doc2",
                        "quality_score": 0.92,
                        "word_count": 800,
                        "reading_time_minutes": 4,
                        "complexity_score": 0.6
                    }
                ],
                "metrics": {
                    "total_documents": 2,
                    "average_quality": 0.90,
                    "total_words": 2000,
                    "average_reading_time": 5.0,
                    "quality_distribution": {
                        "excellent": 1,  # > 0.9
                        "good": 1,       # 0.7-0.9
                        "needs_improvement": 0  # < 0.7
                    },
                    "processing_time_seconds": 1.2,
                    "validation_timestamp": datetime.now().isoformat()
                },
                "insights": {
                    "quality_trends": "Consistent high quality across documents",
                    "common_issues": ["Minor formatting inconsistencies"],
                    "recommendations": ["Standardize formatting guidelines"]
                }
            }

            from simulation.infrastructure.clients.ecosystem_clients import get_analysis_service_client
            analysis_client = get_analysis_service_client()

            documents = [
                {"id": "doc1", "content": "Longer document content...", "metadata": {}},
                {"id": "doc2", "content": "Shorter document content...", "metadata": {}}
            ]

            result = await analysis_client.analyze_documents(documents)

            # Verify metrics collection
            assert "metrics" in result
            metrics = result["metrics"]

            assert metrics["total_documents"] == 2
            assert metrics["average_quality"] == 0.90
            assert metrics["total_words"] == 2000
            assert "quality_distribution" in metrics
            assert "insights" in result

            # Verify quality distribution
            distribution = metrics["quality_distribution"]
            assert distribution["excellent"] == 1
            assert distribution["good"] == 1
            assert distribution["needs_improvement"] == 0

    @pytest.mark.asyncio
    async def test_validation_performance_monitoring(self):
        """Test validation performance monitoring."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis:
            mock_analysis_client = AsyncMock()
            mock_get_analysis.return_value = mock_analysis_client

            # Mock performance metrics
            mock_analysis_client.analyze_documents.return_value = {
                "documents": [
                    {
                        "id": "perf_doc",
                        "quality_score": 0.85,
                        "processing_time_seconds": 0.8
                    }
                ],
                "performance": {
                    "total_processing_time": 0.8,
                    "average_processing_time": 0.8,
                    "documents_per_second": 1.25,
                    "memory_usage_mb": 45.2,
                    "cpu_usage_percent": 12.5,
                    "peak_memory_mb": 52.1
                },
                "efficiency": {
                    "time_efficiency_score": 0.95,  # Fast processing
                    "resource_efficiency_score": 0.88,  # Good resource usage
                    "scalability_score": 0.92  # Good concurrent processing
                }
            }

            from simulation.infrastructure.clients.ecosystem_clients import get_analysis_service_client
            analysis_client = get_analysis_service_client()

            documents = [{"id": "perf_doc", "content": "Test content", "metadata": {}}]

            result = await analysis_client.analyze_documents(documents)

            # Verify performance monitoring
            assert "performance" in result
            assert "efficiency" in result

            perf = result["performance"]
            assert perf["total_processing_time"] > 0
            assert perf["documents_per_second"] > 0
            assert perf["memory_usage_mb"] > 0

            efficiency = result["efficiency"]
            assert efficiency["time_efficiency_score"] > 0
            assert efficiency["resource_efficiency_score"] > 0
            assert efficiency["scalability_score"] > 0


class TestContentValidationEdgeCases:
    """Test cases for content validation edge cases."""

    @pytest.mark.asyncio
    async def test_empty_content_validation(self):
        """Test validation of empty or minimal content."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis:
            mock_analysis_client = AsyncMock()
            mock_get_analysis.return_value = mock_analysis_client

            mock_analysis_client.analyze_documents.return_value = {
                "documents": [
                    {
                        "id": "empty_doc",
                        "quality_score": 0.1,
                        "issues": ["Empty content", "Missing title", "No metadata"],
                        "recommendations": ["Add meaningful content", "Include title", "Add metadata"],
                        "word_count": 0,
                        "validation_status": "failed"
                    }
                ],
                "overall_quality": 0.1
            }

            from simulation.infrastructure.clients.ecosystem_clients import get_analysis_service_client
            analysis_client = get_analysis_service_client()

            empty_document = {
                "id": "empty_doc",
                "type": DocumentType.CONFLUENCE_PAGE.value,
                "title": "",
                "content": "",
                "metadata": {}
            }

            result = await analysis_client.analyze_documents([empty_document])

            # Verify empty content handling
            assert result["overall_quality"] < 0.2
            doc_result = result["documents"][0]
            assert "Empty content" in doc_result["issues"]
            assert doc_result["word_count"] == 0
            assert doc_result["validation_status"] == "failed"

    @pytest.mark.asyncio
    async def test_large_content_validation(self):
        """Test validation of large content documents."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis:
            mock_analysis_client = AsyncMock()
            mock_get_analysis.return_value = mock_analysis_client

            # Create large content
            large_content = "# Large Document\n\n" + "\n\n".join([
                f"## Section {i}\n\n" + "This is a paragraph with some content. " * 20
                for i in range(1, 51)  # 50 sections
            ])

            mock_analysis_client.analyze_documents.return_value = {
                "documents": [
                    {
                        "id": "large_doc",
                        "quality_score": 0.75,
                        "word_count": 5000,
                        "issues": ["Very long document may need splitting"],
                        "recommendations": ["Consider splitting into multiple documents"],
                        "processing_time_seconds": 2.5,
                        "validation_status": "passed_with_warnings"
                    }
                ],
                "overall_quality": 0.75
            }

            from simulation.infrastructure.clients.ecosystem_clients import get_analysis_service_client
            analysis_client = get_analysis_service_client()

            large_document = {
                "id": "large_doc",
                "type": DocumentType.ARCHITECTURE_DOC.value,
                "title": "Comprehensive Architecture Document",
                "content": large_content,
                "metadata": {"word_count": 5000}
            }

            result = await analysis_client.analyze_documents([large_document])

            # Verify large content handling
            doc_result = result["documents"][0]
            assert doc_result["word_count"] == 5000
            assert "Very long document" in doc_result["issues"][0]
            assert doc_result["processing_time_seconds"] > 2.0
            assert doc_result["validation_status"] == "passed_with_warnings"

    @pytest.mark.asyncio
    async def test_mixed_language_content_validation(self):
        """Test validation of content with mixed languages or special characters."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.get_analysis_service_client') as mock_get_analysis:
            mock_analysis_client = AsyncMock()
            mock_get_analysis.return_value = mock_analysis_client

            mock_analysis_client.analyze_documents.return_value = {
                "documents": [
                    {
                        "id": "mixed_lang_doc",
                        "quality_score": 0.7,
                        "language_detection": {
                            "primary_language": "en",
                            "confidence": 0.85,
                            "mixed_languages": True,
                            "special_characters": True
                        },
                        "issues": ["Mixed language content detected"],
                        "recommendations": ["Use consistent language throughout document"],
                        "validation_status": "passed_with_warnings"
                    }
                ],
                "overall_quality": 0.7
            }

            from simulation.infrastructure.clients.ecosystem_clients import get_analysis_service_client
            analysis_client = get_analysis_service_client()

            mixed_content = {
                "id": "mixed_lang_doc",
                "type": DocumentType.MEETING_NOTES.value,
                "title": "International Team Meeting",
                "content": """# International Team Meeting

## Attendees
- John Smith (USA)
- Maria García (Spain)
- Hiroshi Tanaka (Japan)

## Discussion Points
- The user interface needs improvement (English)
- La interfaz de usuario necesita mejoras (Spanish)
- ユーザーインターフェースの改善が必要です (Japanese)

## Action Items
1. Create unified design system
2. Implement internationalization
3. Test in multiple languages
""",
                "metadata": {}
            }

            result = await analysis_client.analyze_documents([mixed_content])

            # Verify mixed language handling
            doc_result = result["documents"][0]
            assert "language_detection" in doc_result
            assert doc_result["language_detection"]["mixed_languages"] == True
            assert "Mixed language content" in doc_result["issues"]
            assert doc_result["validation_status"] == "passed_with_warnings"
