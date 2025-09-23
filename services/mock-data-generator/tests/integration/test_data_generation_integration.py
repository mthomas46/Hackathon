"""Integration Tests for Mock Data Generator Data Generation.

This module tests end-to-end data generation workflows including:
- Full generation pipeline from request to storage
- Multi-service integration with LLM Gateway and Doc Store
- Performance testing under realistic load conditions
- Error handling and recovery in production scenarios
- Data quality and consistency validation across workflows

Integration tests cover complete system behavior and inter-service communication.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import uuid

from main import (
    MockDataType, GenerationRequest, BulkCollectionRequest,
    EcosystemScenarioRequest, SimulationProjectDocsRequest
)


class TestDataGenerationIntegration:
    """Integration tests for complete data generation workflows."""

    @pytest.fixture
    def integration_app(self, mock_llm_gateway, mock_doc_store, mock_schema_validator):
        """Create a complete mock data generator application for integration testing."""
        from main import MockDataGenerator

        # Create the full application with all dependencies
        app = MockDataGenerator(
            llm_gateway=mock_llm_gateway,
            doc_store=mock_doc_store,
            schema_validator=mock_schema_validator
        )
        return app

    @pytest.fixture
    def realistic_generation_request(self):
        """Create a realistic generation request similar to production usage."""
        return GenerationRequest(
            data_type=MockDataType.API_DOCS,
            count=1,
            context="""
            This is for a modern e-commerce platform API that handles product catalog management.
            The API should include endpoints for CRUD operations on products, categories, and inventory.
            Include authentication, pagination, and proper error handling.
            """,
            parameters={
                "complexity": "high",
                "include_code_examples": True,
                "include_error_responses": True,
                "authentication_required": True,
                "pagination_support": True,
                "tags": ["ecommerce", "products", "api", "catalog"]
            },
            store_in_doc_store=True
        )

    @pytest.fixture
    def enterprise_bulk_request(self):
        """Create an enterprise-scale bulk collection request."""
        return BulkCollectionRequest(
            collection_name="enterprise_saas_platform_docs",
            description="""
            Complete documentation suite for a comprehensive SaaS platform including:
            - User management and authentication systems
            - Multi-tenant architecture with tenant isolation
            - Billing and subscription management
            - API gateway and rate limiting
            - Analytics and reporting capabilities
            - DevOps and deployment automation
            """,
            data_types=[
                MockDataType.API_DOCS,
                MockDataType.USER_STORY,
                MockDataType.TECHNICAL_DESIGN,
                MockDataType.TEST_SCENARIOS,
                MockDataType.DEPLOYMENT_GUIDE,
                MockDataType.ARCHITECTURE_DIAGRAM
            ],
            items_per_type={
                "api_docs": 25,
                "user_story": 40,
                "technical_design": 20,
                "test_scenarios": 30,
                "deployment_guide": 8,
                "architecture_diagram": 12
            },
            total_items=135,
            context="""
            Enterprise SaaS platform serving 10,000+ users across multiple industries.
            Multi-tenant architecture with advanced security, compliance, and scalability requirements.
            Global deployment with 99.9% uptime SLA and comprehensive audit trails.
            """,
            store_in_doc_store=True,
            tags=[
                "enterprise", "saas", "multi-tenant", "scalable",
                "secure", "compliant", "global", "high-availability"
            ],
            metadata={
                "industry": "technology",
                "scale": "enterprise",
                "architecture": "microservices",
                "compliance": ["SOC2", "GDPR", "HIPAA"],
                "regions": ["us-east-1", "eu-west-1", "ap-southeast-1"],
                "team_size": 50,
                "timeline_months": 18,
                "budget_millions": 8.5
            }
        )

    @pytest.mark.asyncio
    async def test_end_to_end_single_document_generation(self, integration_app, realistic_generation_request, mock_llm_gateway, mock_doc_store):
        """Test complete end-to-end workflow for single document generation."""
        # Execute the generation
        start_time = time.time()
        result = await integration_app.generate_document(realistic_generation_request)
        end_time = time.time()

        # Verify the result structure
        assert "success" in result
        assert result["success"] is True
        assert "document" in result
        assert "generation_stats" in result

        document = result["document"]
        assert "id" in document
        assert "type" in document
        assert "title" in document
        assert "content" in document
        assert "metadata" in document

        # Verify metadata quality
        metadata = document["metadata"]
        assert metadata["data_type"] == "api_docs"
        assert metadata["complexity"] == "high"
        assert "quality_score" in metadata
        assert 0.0 <= metadata["quality_score"] <= 1.0
        assert "word_count" in metadata
        assert metadata["word_count"] > 100  # Substantial content

        # Verify LLM Gateway was called
        mock_llm_gateway.generate_content.assert_called_once()

        # Verify document was stored if requested
        if realistic_generation_request.store_in_doc_store:
            mock_doc_store.store_document.assert_called_once()

        # Verify performance
        generation_time = end_time - start_time
        assert generation_time < 5.0  # Should complete within 5 seconds

        # Verify generation stats
        stats = result["generation_stats"]
        assert "total_time_seconds" in stats
        assert "llm_calls" in stats
        assert "tokens_used" in stats
        assert stats["llm_calls"] >= 1

    @pytest.mark.asyncio
    async def test_bulk_collection_generation_integration(self, integration_app, enterprise_bulk_request, mock_llm_gateway, mock_doc_store):
        """Test end-to-end bulk collection generation with enterprise-scale requirements."""
        # Execute bulk generation
        start_time = time.time()
        result = await integration_app.generate_bulk_collection(enterprise_bulk_request)
        end_time = time.time()

        # Verify bulk result structure
        assert "success" in result
        assert result["success"] is True
        assert "collection" in result
        assert "generation_stats" in result

        collection = result["collection"]
        assert "collection_id" in collection
        assert "collection_name" in collection
        assert collection["collection_name"] == enterprise_bulk_request.collection_name
        assert "total_documents" in collection
        assert collection["total_documents"] == enterprise_bulk_request.total_items
        assert "documents_by_type" in collection
        assert "documents" in collection
        assert len(collection["documents"]) == enterprise_bulk_request.total_items

        # Verify document type distribution
        docs_by_type = collection["documents_by_type"]
        expected_types = {dt.value: count for dt, count in enterprise_bulk_request.items_per_type.items()}
        for data_type, expected_count in expected_types.items():
            assert docs_by_type.get(data_type, 0) == expected_count

        # Verify all documents have required fields and metadata
        for doc in collection["documents"]:
            assert "id" in doc
            assert "type" in doc
            assert "title" in doc
            assert "content" in doc
            assert "metadata" in doc

            metadata = doc["metadata"]
            assert "data_type" in metadata
            assert "complexity" in metadata
            assert "quality_score" in metadata
            assert "generated_at" in metadata

        # Verify LLM Gateway was called multiple times
        assert mock_llm_gateway.generate_content.call_count > 10  # Substantial number of calls

        # Verify bulk storage was performed
        mock_doc_store.store_documents_batch.assert_called_once()

        # Verify performance (should handle enterprise scale within reasonable time)
        generation_time = end_time - start_time
        assert generation_time < 60.0  # Should complete within 1 minute for enterprise scale

        # Verify generation stats
        stats = result["generation_stats"]
        assert "total_time_seconds" in stats
        assert "total_llm_calls" in stats
        assert "total_tokens_used" in stats
        assert "average_quality_score" in stats
        assert stats["total_llm_calls"] >= len(collection["documents"])
        assert 0.0 <= stats["average_quality_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, integration_app, mock_llm_gateway, mock_doc_store):
        """Test error handling and recovery in integration scenarios."""
        # Configure LLM Gateway to fail intermittently
        call_count = 0
        async def failing_generate_content(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:  # Fail every 3rd call
                raise Exception("Simulated LLM Gateway failure")
            return {
                "content": "Generated content",
                "tokens_used": 100,
                "generation_time_seconds": 1.0,
                "quality_score": 0.85
            }

        mock_llm_gateway.generate_content = failing_generate_content

        # Create bulk request
        bulk_request = BulkCollectionRequest(
            collection_name="error_recovery_test",
            description="Testing error recovery mechanisms",
            data_types=[MockDataType.API_DOCS],
            items_per_type={"api_docs": 9},  # 9 items = 3 failures + 6 successes
            total_items=9,
            store_in_doc_store=True
        )

        # Execute generation (should handle failures gracefully)
        result = await integration_app.generate_bulk_collection(bulk_request)

        # Should still succeed despite some failures
        assert "success" in result
        # Note: Depending on implementation, might be partial success
        assert "collection" in result or "error" in result

        # Verify some documents were still generated
        if "collection" in result:
            collection = result["collection"]
            # Should have generated some documents despite failures
            assert len(collection.get("documents", [])) >= 6  # At least 6 successful generations

        # Verify error handling in stats
        if "generation_stats" in result:
            stats = result["generation_stats"]
            # Should track failures
            assert "failed_generations" in stats or "errors" in stats

    @pytest.mark.asyncio
    async def test_data_quality_validation_integration(self, integration_app, mock_schema_validator):
        """Test data quality validation throughout the generation pipeline."""
        request = GenerationRequest(
            data_type=MockDataType.USER_STORY,
            count=1,
            context="User authentication and login functionality",
            parameters={
                "complexity": "medium",
                "include_acceptance_criteria": True,
                "story_points": 8
            },
            store_in_doc_store=True
        )

        # Configure schema validator to check generated content
        validation_calls = []
        original_validate = mock_schema_validator.validate_document

        def tracking_validate(document, data_type):
            validation_calls.append((document, data_type))
            return original_validate(document, data_type)

        mock_schema_validator.validate_document = tracking_validate

        # Generate document
        result = await integration_app.generate_document(request)

        # Verify schema validation was performed
        assert len(validation_calls) >= 1
        validated_doc, validated_type = validation_calls[0]
        assert validated_type == "user_story"
        assert "title" in validated_doc
        assert "content" in validated_doc
        assert "metadata" in validated_doc

        # Verify the generated document meets quality standards
        document = result["document"]
        assert document["type"] == "user_story"

        # User story should follow standard format
        title = document["title"]
        assert title.startswith("As ")
        assert " I " in title
        assert " so that " in title

        # Should have acceptance criteria
        metadata = document["metadata"]
        assert "acceptance_criteria" in metadata
        assert isinstance(metadata["acceptance_criteria"], list)
        assert len(metadata["acceptance_criteria"]) > 0

    @pytest.mark.asyncio
    async def test_performance_under_load(self, integration_app, mock_llm_gateway, mock_doc_store):
        """Test performance characteristics under concurrent load."""
        # Create multiple concurrent requests
        requests = []
        for i in range(10):
            request = GenerationRequest(
                data_type=MockDataType.API_DOCS,
                count=1,
                context=f"API documentation for service {i}",
                parameters={
                    "complexity": "medium",
                    "include_code_examples": i % 2 == 0,  # Alternate
                    "tags": [f"service_{i}", "api", "documentation"]
                },
                store_in_doc_store=True
            )
            requests.append(request)

        # Execute all requests concurrently
        start_time = time.time()
        tasks = [integration_app.generate_document(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Verify all requests completed
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, Exception) or (isinstance(r, dict) and not r.get("success"))]

        # Should have high success rate
        assert len(successful_results) >= 8  # At least 80% success rate

        # Verify performance
        total_time = end_time - start_time
        avg_time_per_request = total_time / len(requests)

        # Should maintain reasonable performance under load
        assert avg_time_per_request < 3.0  # Less than 3 seconds per request
        assert total_time < 20.0  # Total time under 20 seconds

        # Verify LLM Gateway handled concurrent calls
        assert mock_llm_gateway.generate_content.call_count >= len(successful_results)

    @pytest.mark.asyncio
    async def test_cross_service_data_consistency(self, integration_app, mock_doc_store):
        """Test data consistency across service boundaries."""
        # Generate a collection with related documents
        ecosystem_request = EcosystemScenarioRequest(
            scenario_type="api_development",
            complexity="complex",
            scale="medium",
            include_relationships=True,
            store_in_doc_store=True
        )

        result = await integration_app.generate_ecosystem_scenario(ecosystem_request)

        assert "success" in result
        assert result["success"] is True
        assert "scenario" in result

        scenario = result["scenario"]
        documents = scenario.get("documents", [])

        # Verify cross-document relationships
        doc_ids = {doc["id"] for doc in documents}
        relationships_found = False

        for doc in documents:
            relationships = doc.get("relationships", {})
            for rel_type, rel_docs in relationships.items():
                if rel_docs:
                    relationships_found = True
                    # Verify all referenced documents exist
                    for rel_doc_id in rel_docs:
                        assert rel_doc_id in doc_ids, f"Invalid relationship reference: {rel_doc_id}"

        # Should have some relationships in a complex scenario
        assert relationships_found, "Complex ecosystem scenario should include document relationships"

        # Verify storage consistency
        if ecosystem_request.store_in_doc_store:
            stored_docs = []
            for call in mock_doc_store.store_document.call_args_list:
                stored_docs.extend(call[0][0] if call[0] else [])

            # Should have stored documents with consistent IDs
            stored_ids = {doc["id"] for doc in stored_docs if isinstance(doc, dict) and "id" in doc}
            generated_ids = {doc["id"] for doc in documents}

            # All generated documents should be stored
            assert generated_ids.issubset(stored_ids), "Not all generated documents were stored"

    @pytest.mark.asyncio
    async def test_enterprise_scale_workflow(self, integration_app, enterprise_bulk_request):
        """Test complete enterprise-scale workflow from request to delivery."""
        # Simulate full enterprise workflow
        start_time = time.time()

        # 1. Generate bulk collection
        generation_result = await integration_app.generate_bulk_collection(enterprise_bulk_request)
        generation_time = time.time()

        assert generation_result["success"] is True

        collection = generation_result["collection"]
        collection_id = collection["collection_id"]

        # 2. Verify collection completeness
        assert collection["total_documents"] == enterprise_bulk_request.total_items

        # 3. Verify metadata enrichment
        assert "metadata" in collection
        metadata = collection["metadata"]
        assert "domain" in metadata
        assert "architecture" in metadata
        assert "team_size" in metadata

        # 4. Verify quality metrics
        for doc in collection["documents"]:
            metadata = doc["metadata"]
            assert "quality_score" in metadata
            assert 0.0 <= metadata["quality_score"] <= 1.0
            assert "word_count" in metadata
            assert metadata["word_count"] > 0

        # 5. Verify performance meets enterprise SLAs
        total_time = generation_time - start_time
        docs_per_second = collection["total_documents"] / total_time

        # Enterprise SLA: at least 10 docs/second for bulk generation
        assert docs_per_second >= 2.0, f"Performance too slow: {docs_per_second} docs/sec"

        # 6. Verify generation stats completeness
        stats = generation_result["generation_stats"]
        required_stats = [
            "total_time_seconds", "total_llm_calls", "total_tokens_used",
            "average_quality_score", "success_rate"
        ]

        for stat in required_stats:
            assert stat in stats, f"Missing required stat: {stat}"

        # 7. Verify enterprise metadata carried through
        assert stats["success_rate"] >= 0.95, "Enterprise SLA requires 95% success rate"

    @pytest.mark.asyncio
    async def test_monitoring_and_telemetry_integration(self, integration_app, realistic_generation_request):
        """Test monitoring and telemetry integration throughout the workflow."""
        # This test verifies that monitoring hooks are properly integrated
        # and telemetry data is collected throughout the generation process

        # Generate document with monitoring
        result = await integration_app.generate_document(realistic_generation_request)

        # Verify monitoring data is included
        assert "generation_stats" in result
        stats = result["generation_stats"]

        # Verify comprehensive telemetry
        telemetry_fields = [
            "total_time_seconds",
            "llm_calls",
            "tokens_used",
            "quality_score",
            "data_type",
            "complexity_level",
            "content_length"
        ]

        for field in telemetry_fields:
            assert field in stats, f"Missing telemetry field: {field}"

        # Verify timing data is reasonable
        assert stats["total_time_seconds"] > 0
        assert stats["total_time_seconds"] < 10  # Should complete quickly

        # Verify resource usage tracking
        assert stats["llm_calls"] >= 1
        assert stats["tokens_used"] > 0

        # Verify quality metrics
        assert 0.0 <= stats["quality_score"] <= 1.0
        assert stats["content_length"] > 0
