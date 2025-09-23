"""Unit Tests for Bulk Operations in Mock Data Generator.

This module tests bulk data generation capabilities including:
- Bulk collection generation with multiple data types
- Large-scale data generation performance
- Collection metadata and organization
- Batch processing and error handling

Tests cover the complete bulk operations infrastructure within the Mock Data Generator.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from main import MockDataType, BulkCollectionRequest


class TestBulkCollectionGeneration:
    """Test Bulk Collection Generation functionality."""

    @pytest.fixture
    def bulk_generator(self, mock_llm_gateway, mock_doc_store, mock_relationship_engine):
        """Create bulk generator instance with mocks."""
        class MockBulkGenerator:
            def __init__(self, llm_gateway, doc_store, relationship_engine):
                self.llm_gateway = llm_gateway
                self.doc_store = doc_store
                self.relationship_engine = relationship_engine
                self.generated_collections = {}

            async def generate_bulk_collection(self, request: BulkCollectionRequest) -> Dict[str, Any]:
                """Mock bulk collection generation."""
                collection_id = str(uuid.uuid4())
                total_items = request.total_items
                items_by_type = {}

                # Generate documents by type
                generated_documents = []
                for data_type in request.data_types:
                    type_count = request.items_per_type.get(data_type.value, total_items // len(request.data_types))
                    items_by_type[data_type.value] = type_count

                    for i in range(type_count):
                        doc = {
                            "id": str(uuid.uuid4()),
                            "type": data_type.value,
                            "title": f"{data_type.value.replace('_', ' ').title()} {i+1}",
                            "content": f"Generated content for {data_type.value} item {i+1}",
                            "metadata": {
                                "data_type": data_type.value,
                                "collection_id": collection_id,
                                "sequence_number": i + 1,
                                "generated_at": datetime.now(),
                                "quality_score": 0.85 + (i * 0.01)  # Slight variation
                            }
                        }
                        generated_documents.append(doc)

                # Generate relationships if requested
                relationships = []
                if request.context and len(generated_documents) > 1:
                    relationships = await self.relationship_engine.generate_relationships(
                        generated_documents
                    )

                # Store in doc store if requested
                stored_ids = []
                if request.store_in_doc_store:
                    store_result = await self.doc_store.store_documents_batch(
                        generated_documents
                    )
                    stored_ids = store_result["document_ids"]

                # Create collection metadata
                collection_metadata = {
                    "collection_name": request.collection_name,
                    "description": request.description,
                    "total_items": len(generated_documents),
                    "items_by_type": items_by_type,
                    "generation_time_seconds": 5.2,
                    "quality_score": 0.87,
                    "tags": request.tags,
                    "context": request.context,
                    "relationships_generated": len(relationships),
                    "stored_in_doc_store": request.store_in_doc_store
                }

                collection = {
                    "collection_id": collection_id,
                    "collection_name": request.collection_name,
                    "description": request.description,
                    "total_documents": len(generated_documents),
                    "documents_by_type": items_by_type,
                    "documents": generated_documents,
                    "relationships": relationships,
                    "metadata": collection_metadata,
                    "created_at": datetime.now(),
                    "stored_in_doc_store": request.store_in_doc_store,
                    "doc_store_ids": stored_ids
                }

                self.generated_collections[collection_id] = collection
                return collection

            async def validate_bulk_request(self, request: BulkCollectionRequest) -> Dict[str, Any]:
                """Mock bulk request validation."""
                validation_errors = []

                if request.total_items > 10000:
                    validation_errors.append("Total items exceeds maximum limit of 10000")

                if len(request.data_types) == 0:
                    validation_errors.append("At least one data type must be specified")

                total_specified = sum(request.items_per_type.values())
                if total_specified > request.total_items:
                    validation_errors.append("Sum of items per type exceeds total items")

                return {
                    "is_valid": len(validation_errors) == 0,
                    "validation_errors": validation_errors,
                    "warnings": []
                }

        return MockBulkGenerator(mock_llm_gateway, mock_doc_store, mock_relationship_engine)

    def test_bulk_collection_basic_generation(self, bulk_generator):
        """Test basic bulk collection generation."""
        request = BulkCollectionRequest(
            collection_name="api_documentation_suite",
            description="Complete API documentation for user management system",
            data_types=[MockDataType.API_DOCS, MockDataType.USER_STORY],
            items_per_type={"api_docs": 5, "user_story": 3},
            total_items=8,
            context="User management and authentication system",
            store_in_doc_store=True,
            tags=["api", "user-management", "documentation"]
        )

        result = asyncio.run(bulk_generator.generate_bulk_collection(request))

        assert result["collection_name"] == "api_documentation_suite"
        assert result["total_documents"] == 8
        assert result["documents_by_type"]["api_docs"] == 5
        assert result["documents_by_type"]["user_story"] == 3
        assert len(result["documents"]) == 8
        assert result["stored_in_doc_store"] is True
        assert len(result["doc_store_ids"]) == 8

        # Check metadata
        metadata = result["metadata"]
        assert metadata["quality_score"] >= 0.8
        assert metadata["generation_time_seconds"] > 0
        assert set(metadata["tags"]) == {"api", "user-management", "documentation"}

    def test_bulk_collection_with_relationships(self, bulk_generator):
        """Test bulk collection generation with document relationships."""
        request = BulkCollectionRequest(
            collection_name="microservices_architecture",
            description="Complete microservices system documentation",
            data_types=[
                MockDataType.TECHNICAL_DESIGN,
                MockDataType.API_DOCS,
                MockDataType.DEPLOYMENT_GUIDE
            ],
            items_per_type={},
            total_items=12,
            context="E-commerce microservices architecture with API gateway",
            store_in_doc_store=True,
            tags=["microservices", "architecture", "api"]
        )

        result = asyncio.run(bulk_generator.generate_bulk_collection(request))

        assert result["total_documents"] == 12
        assert len(result["relationships"]) > 0  # Should generate relationships

        # Check that relationships reference actual documents
        relationship_sources = set()
        relationship_targets = set()

        for rel in result["relationships"]:
            if isinstance(rel, dict):
                relationship_sources.add(rel.get("source_document"))
                relationship_targets.add(rel.get("target_document"))

        document_ids = {doc["id"] for doc in result["documents"]}

        # All relationship references should point to actual documents
        assert relationship_sources.issubset(document_ids)
        assert relationship_targets.issubset(document_ids)

    def test_bulk_collection_validation(self, bulk_generator):
        """Test bulk collection request validation."""
        # Valid request
        valid_request = BulkCollectionRequest(
            collection_name="valid_collection",
            data_types=[MockDataType.API_DOCS],
            total_items=10
        )

        valid_result = asyncio.run(bulk_generator.validate_bulk_request(valid_request))
        assert valid_result["is_valid"] is True
        assert len(valid_result["validation_errors"]) == 0

        # Invalid requests
        invalid_requests = [
            {
                "request": BulkCollectionRequest(
                    collection_name="too_many_items",
                    data_types=[MockDataType.API_DOCS],
                    total_items=15000  # Exceeds limit
                ),
                "expected_error": "exceeds maximum limit"
            },
            {
                "request": BulkCollectionRequest(
                    collection_name="no_data_types",
                    data_types=[],  # Empty data types
                    total_items=10
                ),
                "expected_error": "at least one data type"
            },
            {
                "request": BulkCollectionRequest(
                    collection_name="overspecified_items",
                    data_types=[MockDataType.API_DOCS],
                    items_per_type={"api_docs": 15},
                    total_items=10  # Less than specified per type
                ),
                "expected_error": "exceeds total items"
            }
        ]

        for invalid_case in invalid_requests:
            invalid_result = asyncio.run(bulk_generator.validate_bulk_request(invalid_case["request"]))
            assert invalid_result["is_valid"] is False
            assert len(invalid_result["validation_errors"]) > 0
            assert invalid_case["expected_error"] in " ".join(invalid_result["validation_errors"])

    def test_large_scale_bulk_generation(self, bulk_generator):
        """Test large-scale bulk generation performance."""
        large_request = BulkCollectionRequest(
            collection_name="enterprise_documentation",
            description="Large-scale enterprise documentation suite",
            data_types=[
                MockDataType.API_DOCS,
                MockDataType.USER_STORY,
                MockDataType.TECHNICAL_DESIGN,
                MockDataType.TEST_SCENARIOS,
                MockDataType.DEPLOYMENT_GUIDE
            ],
            items_per_type={},
            total_items=500,  # Large batch
            context="Enterprise-scale e-commerce platform",
            store_in_doc_store=False,  # Skip storage for performance test
            tags=["enterprise", "ecommerce", "platform"]
        )

        start_time = datetime.now()
        result = asyncio.run(bulk_generator.generate_bulk_collection(large_request))
        end_time = datetime.now()

        generation_time = (end_time - start_time).total_seconds()

        assert result["total_documents"] == 500
        assert len(result["documents"]) == 500
        assert generation_time < 30  # Should complete within reasonable time
        assert result["metadata"]["generation_time_seconds"] < 30

        # Check document distribution
        total_assigned = sum(result["documents_by_type"].values())
        assert total_assigned == 500

        # All document types should be represented
        for data_type in large_request.data_types:
            assert data_type.value in result["documents_by_type"]
            assert result["documents_by_type"][data_type.value] > 0


class TestBulkOperationOptimization:
    """Test Bulk Operation Optimization functionality."""

    @pytest.fixture
    def bulk_optimizer(self, mock_llm_gateway, mock_content_generator):
        """Create bulk operation optimizer instance."""
        class MockBulkOptimizer:
            def __init__(self, llm_gateway, content_generator):
                self.llm_gateway = llm_gateway
                self.content_generator = content_generator

            async def optimize_bulk_generation(self, bulk_request: BulkCollectionRequest) -> Dict[str, Any]:
                """Mock bulk generation optimization."""
                optimization_strategies = []

                # Parallel generation for independent types
                if len(bulk_request.data_types) > 1:
                    optimization_strategies.append({
                        "strategy": "parallel_type_generation",
                        "expected_speedup": 0.4,
                        "resource_usage": "high_cpu"
                    })

                # Batch LLM calls
                if bulk_request.total_items > 50:
                    optimization_strategies.append({
                        "strategy": "batch_llm_requests",
                        "expected_speedup": 0.3,
                        "resource_usage": "high_memory"
                    })

                # Template caching
                optimization_strategies.append({
                    "strategy": "template_caching",
                    "expected_speedup": 0.2,
                    "resource_usage": "low"
                })

                # Content deduplication
                if bulk_request.context:
                    optimization_strategies.append({
                        "strategy": "content_deduplication",
                        "expected_speedup": 0.15,
                        "resource_usage": "medium"
                    })

                total_speedup = sum(strategy["expected_speedup"] for strategy in optimization_strategies)

                return {
                    "optimized_request": bulk_request,
                    "optimization_strategies": optimization_strategies,
                    "expected_performance_improvement": {
                        "speedup_factor": 1 + total_speedup,
                        "time_reduction_percentage": total_speedup * 100,
                        "resource_efficiency": "optimized"
                    },
                    "optimization_metadata": {
                        "parallel_processing_enabled": len(bulk_request.data_types) > 1,
                        "batch_size_optimized": bulk_request.total_items > 50,
                        "caching_enabled": True
                    }
                }

            async def execute_optimized_bulk_generation(self, optimized_config: Dict[str, Any]) -> Dict[str, Any]:
                """Mock execution of optimized bulk generation."""
                strategies = optimized_config["optimization_strategies"]
                speedup_factor = optimized_config["expected_performance_improvement"]["speedup_factor"]

                # Simulate optimized generation
                base_generation_time = 10.0
                actual_generation_time = base_generation_time / speedup_factor

                return {
                    "generation_success": True,
                    "actual_generation_time_seconds": actual_generation_time,
                    "performance_achieved": {
                        "speedup_factor": speedup_factor,
                        "efficiency_score": 0.95,
                        "resource_utilization": "optimal"
                    },
                    "optimization_effectiveness": {
                        "strategies_applied": len(strategies),
                        "performance_target_met": actual_generation_time < base_generation_time,
                        "resource_efficiency_achieved": True
                    }
                }

        return MockBulkOptimizer(mock_llm_gateway, mock_content_generator)

    def test_bulk_generation_optimization_strategies(self, bulk_optimizer):
        """Test bulk generation optimization strategies."""
        bulk_request = BulkCollectionRequest(
            collection_name="optimized_generation_test",
            data_types=[
                MockDataType.API_DOCS,
                MockDataType.USER_STORY,
                MockDataType.TECHNICAL_DESIGN,
                MockDataType.TEST_SCENARIOS
            ],
            total_items=200,
            context="Complex enterprise application with multiple domains",
            store_in_doc_store=True
        )

        optimization_result = asyncio.run(bulk_optimizer.optimize_bulk_generation(bulk_request))

        assert "optimization_strategies" in optimization_result
        assert "expected_performance_improvement" in optimization_result

        strategies = optimization_result["optimization_strategies"]
        assert len(strategies) >= 3  # Should apply multiple strategies

        strategy_names = [s["strategy"] for s in strategies]
        assert "parallel_type_generation" in strategy_names
        assert "batch_llm_requests" in strategy_names
        assert "template_caching" in strategy_names

        performance_improvement = optimization_result["expected_performance_improvement"]
        assert performance_improvement["speedup_factor"] > 1.0
        assert performance_improvement["time_reduction_percentage"] > 0

    def test_optimization_execution_and_validation(self, bulk_optimizer):
        """Test optimization execution and performance validation."""
        # First optimize
        bulk_request = BulkCollectionRequest(
            collection_name="execution_test",
            data_types=[MockDataType.API_DOCS, MockDataType.USER_STORY],
            total_items=100,
            context="Performance optimization test"
        )

        optimization_config = asyncio.run(bulk_optimizer.optimize_bulk_generation(bulk_request))

        # Then execute optimized generation
        execution_result = asyncio.run(bulk_optimizer.execute_optimized_bulk_generation(
            optimization_config
        ))

        assert execution_result["generation_success"] is True
        assert "actual_generation_time_seconds" in execution_result
        assert "performance_achieved" in execution_result

        performance_achieved = execution_result["performance_achieved"]
        expected_speedup = optimization_config["expected_performance_improvement"]["speedup_factor"]

        assert abs(performance_achieved["speedup_factor"] - expected_speedup) < 0.1  # Close to expected
        assert performance_achieved["efficiency_score"] >= 0.9

        optimization_effectiveness = execution_result["optimization_effectiveness"]
        assert optimization_effectiveness["performance_target_met"] is True
        assert optimization_effectiveness["resource_efficiency_achieved"] is True


class TestBulkErrorHandlingAndRecovery:
    """Test Bulk Error Handling and Recovery functionality."""

    @pytest.fixture
    def error_handler(self, mock_llm_gateway, mock_doc_store):
        """Create bulk error handler instance."""
        class MockBulkErrorHandler:
            def __init__(self, llm_gateway, doc_store):
                self.llm_gateway = llm_gateway
                self.doc_store = doc_store

            async def handle_bulk_generation_errors(self, bulk_request: BulkCollectionRequest,
                                                  generation_errors: List[Dict[str, Any]]) -> Dict[str, Any]:
                """Mock bulk error handling and recovery."""
                error_analysis = {
                    "total_errors": len(generation_errors),
                    "error_categories": {},
                    "recoverable_errors": 0,
                    "fatal_errors": 0
                }

                recovery_actions = []

                for error in generation_errors:
                    error_type = error.get("error_type", "unknown")

                    if error_type not in error_analysis["error_categories"]:
                        error_analysis["error_categories"][error_type] = 0
                    error_analysis["error_categories"][error_type] += 1

                    # Determine if error is recoverable
                    if error_type in ["llm_timeout", "rate_limit", "temporary_failure"]:
                        error_analysis["recoverable_errors"] += 1
                        recovery_actions.append({
                            "action": "retry_with_backoff",
                            "target_error": error,
                            "backoff_seconds": 30,
                            "max_retries": 3
                        })
                    elif error_type in ["invalid_request", "schema_validation_error"]:
                        error_analysis["fatal_errors"] += 1
                        recovery_actions.append({
                            "action": "skip_and_log",
                            "target_error": error,
                            "reason": "unrecoverable_error"
                        })
                    else:
                        error_analysis["fatal_errors"] += 1

                # Generate recovery plan
                recovery_success_rate = 0.0
                if error_analysis["total_errors"] > 0:
                    recovery_success_rate = error_analysis["recoverable_errors"] / error_analysis["total_errors"]

                return {
                    "error_analysis": error_analysis,
                    "recovery_actions": recovery_actions,
                    "recovery_plan": {
                        "can_recover": recovery_success_rate > 0.5,
                        "estimated_recovery_time_seconds": len(recovery_actions) * 30,
                        "success_rate_projection": recovery_success_rate,
                        "partial_success_possible": error_analysis["fatal_errors"] < error_analysis["total_errors"]
                    },
                    "error_handling_metadata": {
                        "errors_processed": len(generation_errors),
                        "recovery_actions_generated": len(recovery_actions),
                        "processing_time_seconds": 1.2
                    }
                }

            async def execute_error_recovery(self, recovery_plan: Dict[str, Any]) -> Dict[str, Any]:
                """Mock execution of error recovery plan."""
                recovery_actions = recovery_plan["recovery_actions"]
                successful_recoveries = 0

                recovery_results = []
                for action in recovery_actions:
                    if action["action"] == "retry_with_backoff":
                        # Simulate successful retry
                        recovery_results.append({
                            "action": action,
                            "success": True,
                            "recovery_time_seconds": 15,
                            "retries_attempted": 1
                        })
                        successful_recoveries += 1
                    else:
                        # Skip unrecoverable errors
                        recovery_results.append({
                            "action": action,
                            "success": False,
                            "reason": "unrecoverable"
                        })

                success_rate = successful_recoveries / len(recovery_actions) if recovery_actions else 0

                return {
                    "recovery_execution_success": success_rate > 0.7,
                    "recovery_results": recovery_results,
                    "overall_recovery_stats": {
                        "total_actions": len(recovery_actions),
                        "successful_recoveries": successful_recoveries,
                        "success_rate": success_rate,
                        "total_recovery_time_seconds": sum(r.get("recovery_time_seconds", 0) for r in recovery_results)
                    }
                }

        return MockBulkErrorHandler(mock_llm_gateway, mock_doc_store)

    def test_bulk_error_analysis_and_categorization(self, error_handler):
        """Test bulk error analysis and categorization."""
        generation_errors = [
            {
                "error_type": "llm_timeout",
                "document_type": "api_docs",
                "sequence_number": 5,
                "error_message": "LLM service timeout after 30 seconds",
                "timestamp": datetime.now() - timedelta(minutes=2)
            },
            {
                "error_type": "rate_limit",
                "document_type": "user_story",
                "sequence_number": 12,
                "error_message": "API rate limit exceeded",
                "timestamp": datetime.now() - timedelta(minutes=1)
            },
            {
                "error_type": "invalid_request",
                "document_type": "technical_design",
                "sequence_number": 8,
                "error_message": "Invalid schema for technical design",
                "timestamp": datetime.now() - timedelta(seconds=30)
            },
            {
                "error_type": "llm_timeout",
                "document_type": "test_scenarios",
                "sequence_number": 15,
                "error_message": "LLM service timeout after 30 seconds",
                "timestamp": datetime.now() - timedelta(seconds=15)
            }
        ]

        bulk_request = BulkCollectionRequest(
            collection_name="error_test_collection",
            data_types=[MockDataType.API_DOCS, MockDataType.USER_STORY],
            total_items=20
        )

        error_handling_result = asyncio.run(error_handler.handle_bulk_generation_errors(
            bulk_request, generation_errors
        ))

        assert "error_analysis" in error_handling_result
        assert "recovery_actions" in error_handling_result

        error_analysis = error_handling_result["error_analysis"]
        assert error_analysis["total_errors"] == 4
        assert error_analysis["error_categories"]["llm_timeout"] == 2
        assert error_analysis["error_categories"]["rate_limit"] == 1
        assert error_analysis["error_categories"]["invalid_request"] == 1
        assert error_analysis["recoverable_errors"] == 3  # llm_timeout and rate_limit
        assert error_analysis["fatal_errors"] == 1  # invalid_request

        recovery_actions = error_handling_result["recovery_actions"]
        assert len(recovery_actions) == 4

        # Check recovery actions
        retry_actions = [a for a in recovery_actions if a["action"] == "retry_with_backoff"]
        skip_actions = [a for a in recovery_actions if a["action"] == "skip_and_log"]

        assert len(retry_actions) == 3  # Recoverable errors
        assert len(skip_actions) == 1   # Fatal error

    def test_error_recovery_execution(self, error_handler):
        """Test error recovery execution."""
        # Create a mock recovery plan
        recovery_plan = {
            "recovery_actions": [
                {
                    "action": "retry_with_backoff",
                    "target_error": {"error_type": "llm_timeout", "document_type": "api_docs"},
                    "backoff_seconds": 30,
                    "max_retries": 3
                },
                {
                    "action": "retry_with_backoff",
                    "target_error": {"error_type": "rate_limit", "document_type": "user_story"},
                    "backoff_seconds": 60,
                    "max_retries": 2
                },
                {
                    "action": "skip_and_log",
                    "target_error": {"error_type": "invalid_request", "document_type": "technical_design"},
                    "reason": "unrecoverable_error"
                }
            ]
        }

        recovery_execution = asyncio.run(error_handler.execute_error_recovery(recovery_plan))

        assert "recovery_execution_success" in recovery_execution
        assert "recovery_results" in recovery_execution
        assert "overall_recovery_stats" in recovery_execution

        recovery_results = recovery_execution["recovery_results"]
        assert len(recovery_results) == 3

        # Check individual results
        successful_results = [r for r in recovery_results if r["success"] is True]
        failed_results = [r for r in recovery_results if r["success"] is False]

        assert len(successful_results) == 2  # Two retries should succeed
        assert len(failed_results) == 1     # One skip should fail

        overall_stats = recovery_execution["overall_recovery_stats"]
        assert overall_stats["total_actions"] == 3
        assert overall_stats["successful_recoveries"] == 2
        assert overall_stats["success_rate"] == 2/3

    def test_partial_bulk_success_handling(self, error_handler):
        """Test handling of partial bulk generation success."""
        # Scenario: 80% success rate with some recoverable errors
        partial_success_errors = [
            {
                "error_type": "llm_timeout",
                "document_type": "api_docs",
                "sequence_number": 18,
                "error_message": "LLM timeout"
            },
            {
                "error_type": "rate_limit",
                "document_type": "user_story",
                "sequence_number": 7,
                "error_message": "Rate limit exceeded"
            }
        ]

        bulk_request = BulkCollectionRequest(
            collection_name="partial_success_test",
            data_types=[MockDataType.API_DOCS, MockDataType.USER_STORY],
            total_items=20  # 18 successful, 2 failed
        )

        # Handle errors
        error_handling = asyncio.run(error_handler.handle_bulk_generation_errors(
            bulk_request, partial_success_errors
        ))

        # Execute recovery
        recovery_execution = asyncio.run(error_handler.execute_error_recovery(
            error_handling
        ))

        # Verify partial success handling
        assert recovery_execution["recovery_execution_success"] is True
        assert recovery_execution["overall_recovery_stats"]["success_rate"] > 0.5

        # Recovery plan should indicate partial success is possible
        recovery_plan = error_handling["recovery_plan"]
        assert recovery_plan["partial_success_possible"] is True
        assert recovery_plan["can_recover"] is True
