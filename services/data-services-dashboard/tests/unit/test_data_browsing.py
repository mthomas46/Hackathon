"""Unit Tests for Data Browsing in Data Services Dashboard.

This module tests data browsing capabilities including:
- Service data exploration and visualization
- Advanced search and filtering across services
- Relationship mapping and data correlation
- Real-time data synchronization and updates

Tests cover the complete data browsing infrastructure within the Data Services Dashboard.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from pages.memory_browser import MemoryBrowser
from pages.document_browser import DocumentBrowser
from pages.search import SearchPage


class TestMemoryDataBrowsing:
    """Test Memory Agent Data Browsing functionality."""

    @pytest.fixture
    def memory_browser(self, mock_memory_client):
        """Create memory browser instance."""
        return MemoryBrowser(memory_client=mock_memory_client)

    def test_memory_item_visualization(self, memory_browser):
        """Test memory item data visualization."""
        memory_items = [
            {
                "id": "mem_001",
                "content": "User prefers dark mode interface",
                "category": "user_preference",
                "importance": 0.8,
                "created_at": datetime.now() - timedelta(days=1),
                "tags": ["ui", "theme", "preference"],
                "metadata": {
                    "confidence": 0.95,
                    "source": "user_interaction",
                    "ttl_seconds": 86400
                }
            },
            {
                "id": "mem_002",
                "content": "Document analysis workflow completed successfully",
                "category": "workflow_result",
                "importance": 0.6,
                "created_at": datetime.now() - timedelta(hours=2),
                "tags": ["workflow", "analysis", "success"],
                "metadata": {
                    "workflow_id": "wf_123",
                    "processing_time_ms": 1250,
                    "tokens_used": 450
                }
            }
        ]

        visualization_config = {
            "view_mode": "timeline",
            "group_by": "category",
            "sort_by": "importance",
            "filter_criteria": {"importance_threshold": 0.5}
        }

        visualization_result = memory_browser.visualize_memory_items(memory_items, visualization_config)

        assert visualization_result["success"] is True
        assert "visualization_data" in visualization_result
        assert "metadata" in visualization_result

        viz_data = visualization_result["visualization_data"]

        # Should group by category
        assert "user_preference" in viz_data
        assert "workflow_result" in viz_data

        # Should sort by importance (highest first)
        user_prefs = viz_data["user_preference"]
        assert len(user_prefs) > 0
        assert user_prefs[0]["importance"] >= 0.8

    def test_memory_search_and_filtering(self, memory_browser):
        """Test advanced memory search and filtering."""
        search_query = {
            "text": "workflow",
            "filters": {
                "category": ["workflow_result", "system_event"],
                "importance_range": [0.5, 1.0],
                "date_range": {
                    "start": datetime.now() - timedelta(days=7),
                    "end": datetime.now()
                },
                "tags": ["analysis", "success"]
            },
            "sort": {
                "field": "created_at",
                "direction": "desc"
            },
            "pagination": {
                "page": 1,
                "page_size": 20
            }
        }

        search_result = memory_browser.search_memory_items(search_query)

        assert search_result["success"] is True
        assert "results" in search_result
        assert "total_count" in search_result
        assert "search_metadata" in search_result

        results = search_result["results"]
        assert isinstance(results, list)

        # Verify filtering applied
        for item in results:
            assert "workflow" in item["content"].lower()
            assert item["importance"] >= 0.5
            assert item["importance"] <= 1.0

        # Verify sorting (most recent first)
        if len(results) > 1:
            assert results[0]["created_at"] >= results[1]["created_at"]

    def test_memory_relationship_mapping(self, memory_browser):
        """Test memory item relationship mapping."""
        memory_items = [
            {
                "id": "mem_001",
                "content": "User analyzed document about API design patterns",
                "category": "user_activity",
                "related_items": ["mem_002", "doc_123"],
                "tags": ["analysis", "api", "design"]
            },
            {
                "id": "mem_002",
                "content": "Generated summary of API documentation",
                "category": "system_action",
                "related_items": ["mem_001", "doc_123"],
                "tags": ["summary", "api", "documentation"]
            },
            {
                "id": "mem_003",
                "content": "User preference for JSON response format",
                "category": "user_preference",
                "related_items": [],
                "tags": ["preference", "json", "response"]
            }
        ]

        relationship_result = memory_browser.map_memory_relationships(memory_items)

        assert relationship_result["success"] is True
        assert "relationship_graph" in relationship_result
        assert "clusters" in relationship_result

        graph = relationship_result["relationship_graph"]

        # Should identify relationships
        assert len(graph["nodes"]) == len(memory_items)
        assert len(graph["edges"]) >= 2  # Relationships between mem_001 and mem_002

        # Should find clusters
        clusters = relationship_result["clusters"]
        assert len(clusters) >= 1

        # API-related cluster should exist
        api_cluster = next((c for c in clusters if "api" in c["theme"].lower()), None)
        assert api_cluster is not None
        assert len(api_cluster["items"]) >= 2

    def test_memory_analytics_and_insights(self, memory_browser):
        """Test memory analytics and insights generation."""
        memory_data = {
            "items": [
                {
                    "id": "mem_001",
                    "content": "Error occurred during document processing",
                    "category": "error",
                    "importance": 0.9,
                    "created_at": datetime.now() - timedelta(hours=1),
                    "tags": ["error", "processing"]
                },
                {
                    "id": "mem_002",
                    "content": "User successfully completed workflow",
                    "category": "success",
                    "importance": 0.7,
                    "created_at": datetime.now() - timedelta(hours=2),
                    "tags": ["success", "workflow"]
                }
            ],
            "time_range": {
                "start": datetime.now() - timedelta(days=7),
                "end": datetime.now()
            }
        }

        analytics_result = memory_browser.generate_memory_analytics(memory_data)

        assert analytics_result["success"] is True
        assert "analytics" in analytics_result
        assert "insights" in analytics_result

        analytics = analytics_result["analytics"]

        # Should include category distribution
        assert "category_distribution" in analytics
        assert "error" in analytics["category_distribution"]
        assert "success" in analytics["category_distribution"]

        # Should include temporal patterns
        assert "temporal_patterns" in analytics

        # Should generate insights
        insights = analytics_result["insights"]
        assert len(insights) > 0

        # Should identify error patterns
        error_insights = [i for i in insights if "error" in i["type"].lower()]
        assert len(error_insights) > 0

    def test_memory_bulk_operations(self, memory_browser):
        """Test bulk memory operations."""
        bulk_operations = [
            {
                "operation": "tag",
                "item_ids": ["mem_001", "mem_002", "mem_003"],
                "parameters": {"tags": ["bulk_operation", "test"]}
            },
            {
                "operation": "update_importance",
                "item_ids": ["mem_004", "mem_005"],
                "parameters": {"importance": 0.8}
            },
            {
                "operation": "delete",
                "item_ids": ["mem_006"],
                "parameters": {}
            }
        ]

        bulk_result = memory_browser.execute_bulk_memory_operations(bulk_operations)

        assert bulk_result["success"] is True
        assert "operation_results" in bulk_result
        assert "summary" in bulk_result

        operation_results = bulk_result["operation_results"]
        assert len(operation_results) == len(bulk_operations)

        # Verify each operation succeeded
        for result in operation_results:
            assert result["success"] is True
            assert "affected_items" in result

        # Verify summary
        summary = bulk_result["summary"]
        assert summary["total_operations"] == len(bulk_operations)
        assert summary["successful_operations"] == len(bulk_operations)
        assert summary["total_affected_items"] == 6  # 3 + 2 + 1


class TestDocumentDataBrowsing:
    """Test Document Store Data Browsing functionality."""

    @pytest.fixture
    def document_browser(self, mock_document_client):
        """Create document browser instance."""
        return DocumentBrowser(document_client=mock_document_client)

    def test_document_content_viewer(self, document_browser):
        """Test document content viewing and analysis."""
        document = {
            "id": "doc_001",
            "title": "API Design Patterns",
            "content": "# API Design Patterns\n\nThis document covers essential API design patterns including REST, GraphQL, and gRPC approaches.\n\n## RESTful Design\n\nREST APIs should follow these principles:\n1. Stateless communication\n2. Uniform interface\n3. Client-server architecture\n\n## Best Practices\n\n- Use meaningful HTTP status codes\n- Implement proper error handling\n- Version your APIs appropriately",
            "metadata": {
                "author": "John Doe",
                "created_at": datetime.now() - timedelta(days=5),
                "updated_at": datetime.now() - timedelta(hours=1),
                "tags": ["api", "design", "patterns"],
                "category": "technical_documentation",
                "word_count": 156,
                "reading_time_minutes": 3
            },
            "quality_score": 0.92,
            "version": "1.2.0"
        }

        viewer_config = {
            "view_mode": "rich_text",
            "highlight_search_terms": ["REST", "API"],
            "show_metadata": True,
            "enable_annotations": True
        }

        viewer_result = document_browser.render_document_viewer(document, viewer_config)

        assert viewer_result["success"] is True
        assert "rendered_content" in viewer_result
        assert "content_analysis" in viewer_result

        rendered = viewer_result["rendered_content"]

        # Should include HTML content
        assert "<h1>" in rendered
        assert "<h2>" in rendered

        # Should highlight search terms
        assert "<mark>" in rendered or "highlight" in rendered

        # Should include metadata
        assert "author" in rendered.lower()
        assert "John Doe" in rendered

    def test_document_search_and_filtering(self, document_browser):
        """Test advanced document search and filtering."""
        search_request = {
            "query": "API design patterns",
            "filters": {
                "category": ["technical_documentation", "api_guide"],
                "quality_score_min": 0.8,
                "date_range": {
                    "start": datetime.now() - timedelta(days=30),
                    "end": datetime.now()
                },
                "tags": ["api", "design"],
                "author": ["John Doe", "Jane Smith"]
            },
            "search_options": {
                "search_fields": ["title", "content", "tags"],
                "fuzzy_matching": True,
                "boost_recent": True,
                "include_content_snippets": True
            },
            "sort": {
                "field": "relevance",
                "direction": "desc"
            },
            "pagination": {
                "page": 1,
                "page_size": 25
            }
        }

        search_result = document_browser.search_documents(search_request)

        assert search_result["success"] is True
        assert "results" in search_result
        assert "total_count" in search_result
        assert "search_metadata" in search_result

        results = search_result["results"]

        # Should return document objects
        for doc in results:
            assert "id" in doc
            assert "title" in doc
            assert "metadata" in doc

        # Should include relevance scores
        for doc in results:
            assert "relevance_score" in doc
            assert 0.0 <= doc["relevance_score"] <= 1.0

        # Should include content snippets if requested
        if search_request["search_options"]["include_content_snippets"]:
            for doc in results:
                assert "content_snippet" in doc

    def test_document_relationships_and_linking(self, document_browser):
        """Test document relationship mapping and linking."""
        documents = [
            {
                "id": "doc_001",
                "title": "API Design Patterns",
                "content": "This document covers REST API patterns",
                "relationships": {
                    "references": ["doc_002", "doc_003"],
                    "referenced_by": ["doc_004"],
                    "similar": ["doc_005"]
                }
            },
            {
                "id": "doc_002",
                "title": "REST API Best Practices",
                "content": "Best practices for REST APIs",
                "relationships": {
                    "references": [],
                    "referenced_by": ["doc_001"],
                    "similar": ["doc_003", "doc_006"]
                }
            },
            {
                "id": "doc_003",
                "title": "GraphQL vs REST",
                "content": "Comparison of GraphQL and REST approaches",
                "relationships": {
                    "references": ["doc_002"],
                    "referenced_by": ["doc_001"],
                    "similar": ["doc_002"]
                }
            }
        ]

        relationship_result = document_browser.analyze_document_relationships(documents)

        assert relationship_result["success"] is True
        assert "relationship_graph" in relationship_result
        assert "relationship_insights" in relationship_result

        graph = relationship_result["relationship_graph"]

        # Should have nodes for all documents
        assert len(graph["nodes"]) == len(documents)

        # Should have edges for relationships
        assert len(graph["edges"]) > 0

        # Should identify relationship patterns
        insights = relationship_result["relationship_insights"]

        # Should find central documents
        central_docs = [i for i in insights if i["insight_type"] == "central_document"]
        assert len(central_docs) > 0

        # Should find relationship clusters
        clusters = [i for i in insights if i["insight_type"] == "relationship_cluster"]
        assert len(clusters) > 0

    def test_document_version_comparison(self, document_browser):
        """Test document version comparison and diffing."""
        version_a = {
            "id": "doc_001",
            "version": "1.0",
            "content": "# API Design Patterns\n\nThis covers REST API patterns.\n\n## Best Practices\n\nUse proper HTTP codes.",
            "metadata": {"author": "John Doe", "updated_at": datetime.now() - timedelta(days=7)}
        }

        version_b = {
            "id": "doc_001",
            "version": "1.1",
            "content": "# API Design Patterns\n\nThis document covers REST and GraphQL API patterns.\n\n## REST Best Practices\n\nUse proper HTTP codes and implement HATEOAS.\n\n## GraphQL Considerations\n\nConsider schema design carefully.",
            "metadata": {"author": "Jane Smith", "updated_at": datetime.now()}
        }

        comparison_result = document_browser.compare_document_versions(version_a, version_b)

        assert comparison_result["success"] is True
        assert "diff" in comparison_result
        assert "summary" in comparison_result

        diff = comparison_result["diff"]

        # Should identify additions
        assert len(diff["additions"]) > 0
        assert "GraphQL" in " ".join(diff["additions"])

        # Should identify modifications
        assert len(diff["modifications"]) > 0

        # Should provide summary
        summary = comparison_result["summary"]
        assert "total_changes" in summary
        assert "change_types" in summary

    def test_document_bulk_operations(self, document_browser):
        """Test bulk document operations."""
        bulk_operations = [
            {
                "operation": "tag",
                "document_ids": ["doc_001", "doc_002"],
                "parameters": {"tags": ["bulk_tagged", "reviewed"]}
            },
            {
                "operation": "move_category",
                "document_ids": ["doc_003", "doc_004"],
                "parameters": {"new_category": "archived"}
            },
            {
                "operation": "update_quality",
                "document_ids": ["doc_005"],
                "parameters": {"quality_score": 0.95}
            }
        ]

        bulk_result = document_browser.execute_bulk_document_operations(bulk_operations)

        assert bulk_result["success"] is True
        assert "operation_results" in bulk_result
        assert "bulk_summary" in bulk_result

        operation_results = bulk_result["operation_results"]
        assert len(operation_results) == len(bulk_operations)

        # Verify each operation
        for result in operation_results:
            assert result["success"] is True
            assert "affected_documents" in result

        # Verify bulk summary
        summary = bulk_result["bulk_summary"]
        assert summary["total_operations"] == len(bulk_operations)
        assert summary["successful_operations"] == len(bulk_operations)


class TestUnifiedSearchCapabilities:
    """Test Unified Search Across All Services."""

    @pytest.fixture
    def search_page(self, mock_memory_client, mock_prompt_client, mock_document_client):
        """Create search page instance."""
        return SearchPage(
            memory_client=mock_memory_client,
            prompt_client=mock_prompt_client,
            document_client=mock_document_client
        )

    def test_cross_service_search(self, search_page):
        """Test searching across all services simultaneously."""
        search_request = {
            "query": "API design patterns",
            "services": ["memory", "prompts", "documents"],
            "filters": {
                "memory": {
                    "category": ["user_activity", "system_action"],
                    "importance_min": 0.6
                },
                "prompts": {
                    "category": ["api_design", "technical"],
                    "performance_min": 0.8
                },
                "documents": {
                    "category": ["technical_documentation"],
                    "quality_min": 0.85
                }
            },
            "result_limits": {
                "memory": 10,
                "prompts": 15,
                "documents": 20
            },
            "sort_by": "relevance",
            "include_facets": True
        }

        search_result = search_page.perform_cross_service_search(search_request)

        assert search_result["success"] is True
        assert "results" in search_result
        assert "facets" in search_result
        assert "search_metadata" in search_result

        results = search_result["results"]

        # Should have results from all requested services
        assert "memory" in results
        assert "prompts" in results
        assert "documents" in results

        # Should respect result limits
        assert len(results["memory"]) <= search_request["result_limits"]["memory"]
        assert len(results["prompts"]) <= search_request["result_limits"]["prompts"]
        assert len(results["documents"]) <= search_request["result_limits"]["documents"]

        # Should include facets if requested
        if search_request["include_facets"]:
            facets = search_result["facets"]
            assert "service_distribution" in facets
            assert "category_distribution" in facets

    def test_advanced_search_filters(self, search_page):
        """Test advanced search filtering capabilities."""
        advanced_filters = {
            "query": "machine learning",
            "filters": {
                "date_range": {
                    "start": datetime.now() - timedelta(days=90),
                    "end": datetime.now()
                },
                "numeric_ranges": {
                    "quality_score": {"min": 0.7, "max": 1.0},
                    "importance": {"min": 0.5},
                    "performance_score": {"min": 0.8}
                },
                "text_filters": {
                    "tags": ["ml", "ai", "machine-learning"],
                    "authors": ["john.doe", "jane.smith"],
                    "categories": ["technical", "tutorial"]
                },
                "boolean_filters": {
                    "has_versions": True,
                    "is_featured": False,
                    "requires_auth": False
                }
            },
            "search_options": {
                "fuzzy_matching": True,
                "stemming": True,
                "synonym_expansion": True,
                "field_weighting": {
                    "title": 2.0,
                    "tags": 1.5,
                    "content": 1.0
                }
            }
        }

        filter_result = search_page.apply_advanced_filters(advanced_filters)

        assert filter_result["success"] is True
        assert "filtered_results" in filter_result
        assert "filter_metadata" in filter_result

        filtered = filter_result["filtered_results"]

        # Should apply all filter types
        assert "by_date_range" in filtered
        assert "by_numeric_ranges" in filtered
        assert "by_text_filters" in filtered
        assert "by_boolean_filters" in filtered

        # Should provide filter metadata
        metadata = filter_result["filter_metadata"]
        assert "total_results_before_filtering" in metadata
        assert "total_results_after_filtering" in metadata
        assert "filter_effectiveness" in metadata

    def test_search_result_ranking_and_scoring(self, search_page):
        """Test search result ranking and relevance scoring."""
        search_results = {
            "raw_results": [
                {
                    "id": "doc_001",
                    "title": "Machine Learning Basics",
                    "content": "This is a basic introduction to machine learning",
                    "service": "documents",
                    "metadata": {"quality_score": 0.9, "recency_days": 5}
                },
                {
                    "id": "prompt_001",
                    "title": "ML Model Training Prompt",
                    "content": "Create a machine learning model for classification",
                    "service": "prompts",
                    "metadata": {"performance_score": 0.85, "usage_count": 150}
                },
                {
                    "id": "mem_001",
                    "content": "User searched for machine learning tutorials",
                    "service": "memory",
                    "metadata": {"importance": 0.7, "recency_hours": 2}
                }
            ],
            "query": "machine learning",
            "ranking_config": {
                "algorithm": "weighted_scoring",
                "weights": {
                    "text_relevance": 0.4,
                    "quality_score": 0.2,
                    "recency": 0.15,
                    "popularity": 0.15,
                    "service_priority": 0.1
                },
                "normalization": "min_max",
                "tie_breaking": "service_priority"
            }
        }

        ranking_result = search_page.rank_search_results(search_results)

        assert ranking_result["success"] is True
        assert "ranked_results" in ranking_result
        assert "ranking_metadata" in ranking_result

        ranked = ranking_result["ranked_results"]

        # Should assign relevance scores
        for result in ranked:
            assert "relevance_score" in result
            assert 0.0 <= result["relevance_score"] <= 1.0

        # Should be sorted by relevance (highest first)
        for i in range(len(ranked) - 1):
            assert ranked[i]["relevance_score"] >= ranked[i + 1]["relevance_score"]

        # Should include ranking factors
        for result in ranked:
            assert "ranking_factors" in result
            factors = result["ranking_factors"]
            assert "text_relevance" in factors
            assert "quality_score" in factors

    def test_search_analytics_and_insights(self, search_page):
        """Test search analytics and user behavior insights."""
        search_analytics = {
            "search_queries": [
                {"query": "API design", "count": 45, "avg_relevance": 0.78},
                {"query": "machine learning", "count": 32, "avg_relevance": 0.82},
                {"query": "database optimization", "count": 28, "avg_relevance": 0.75},
                {"query": "security best practices", "count": 21, "avg_relevance": 0.88}
            ],
            "time_range": {
                "start": datetime.now() - timedelta(days=30),
                "end": datetime.now()
            },
            "user_segments": {
                "developers": {"query_count": 156, "avg_session_length": 25},
                "architects": {"query_count": 89, "avg_session_length": 35},
                "managers": {"query_count": 67, "avg_session_length": 15}
            }
        }

        analytics_result = search_page.generate_search_analytics(search_analytics)

        assert analytics_result["success"] is True
        assert "analytics" in analytics_result
        assert "insights" in analytics_result

        analytics = analytics_result["analytics"]

        # Should analyze query patterns
        assert "popular_queries" in analytics
        assert "query_trends" in analytics

        # Should analyze user behavior
        assert "user_segments" in analytics
        assert "search_effectiveness" in analytics

        # Should generate insights
        insights = analytics_result["insights"]
        assert len(insights) > 0

        # Should include recommendations
        recommendations = [i for i in insights if i["type"] == "recommendation"]
        assert len(recommendations) > 0

    def test_search_performance_optimization(self, search_page):
        """Test search performance optimization."""
        performance_config = {
            "indexing_strategy": "incremental",
            "caching_layers": {
                "query_cache": {"ttl_seconds": 300, "max_size_mb": 100},
                "result_cache": {"ttl_seconds": 600, "max_size_mb": 200},
                "facet_cache": {"ttl_seconds": 1800, "max_size_mb": 50}
            },
            "parallel_processing": True,
            "query_optimization": {
                "early_termination": True,
                "result_limits": {"initial": 100, "refined": 50},
                "scoring_optimization": True
            },
            "resource_limits": {
                "max_query_time_ms": 5000,
                "max_memory_mb": 256,
                "max_concurrent_searches": 10
            }
        }

        optimization_result = search_page.optimize_search_performance(performance_config)

        assert optimization_result["success"] is True
        assert "optimization_config" in optimization_result
        assert "performance_projections" in optimization_result

        projections = optimization_result["performance_projections"]

        # Should provide performance estimates
        assert "avg_query_time_ms" in projections
        assert "cache_hit_rate" in projections
        assert "throughput_queries_per_second" in projections

        # Should validate resource limits
        assert "resource_compliance" in projections
        assert projections["resource_compliance"] is True

        # Should provide optimization recommendations
        assert "optimization_recommendations" in optimization_result
