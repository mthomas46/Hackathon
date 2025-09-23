"""Unit Tests for Document Search and Filtering in Document Store Service.

This module tests document search capabilities including:
- Full-text search with relevance ranking
- Metadata-based filtering and faceted search
- Semantic search and AI-powered matching
- Search query parsing and optimization
- Search result highlighting and snippets
- Search performance and caching

Tests cover the comprehensive search functionality within the document management system.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from core.models import SearchQuery, SearchResult
from domain.search.handlers import SearchQueryHandler
from domain.search.service import SearchService


class TestSearchQueryParsing:
    """Test Search Query Parsing functionality."""

    @pytest.fixture
    def query_parser(self):
        """Create search query parser instance."""
        return SearchService()

    def test_basic_text_query_parsing(self, query_parser):
        """Test parsing of basic text search queries."""
        test_queries = [
            ("artificial intelligence", ["artificial", "intelligence"]),
            ("machine learning algorithms", ["machine", "learning", "algorithms"]),
            ("deep learning neural networks", ["deep", "learning", "neural", "networks"]),
            ("AI and ML technologies", ["ai", "and", "ml", "technologies"])
        ]

        for query_text, expected_terms in test_queries:
            parsed = query_parser.parse_search_query(query_text)

            assert parsed["query_type"] == "text"
            assert set(parsed["search_terms"]) == set(expected_terms)
            assert len(parsed["search_terms"]) == len(expected_terms)

    def test_advanced_query_parsing(self, query_parser):
        """Test parsing of advanced search queries with operators."""
        test_queries = [
            {
                "query": 'title:"machine learning" AND author:"John Doe"',
                "expected": {
                    "operators": ["AND"],
                    "field_filters": {"title": "machine learning", "author": "John Doe"}
                }
            },
            {
                "query": 'tags:(AI OR ML) AND date:[2024-01-01 TO 2024-12-31]',
                "expected": {
                    "operators": ["AND", "OR"],
                    "field_filters": {"tags": ["AI", "ML"]},
                    "date_range": {"start": "2024-01-01", "end": "2024-12-31"}
                }
            },
            {
                "query": 'content:"neural networks" NOT tags:deprecated',
                "expected": {
                    "operators": ["NOT"],
                    "field_filters": {"content": "neural networks"},
                    "exclude_tags": ["deprecated"]
                }
            }
        ]

        for test_case in test_queries:
            parsed = query_parser.parse_advanced_query(test_case["query"])

            for key, expected_value in test_case["expected"].items():
                if key == "operators":
                    assert all(op in parsed[key] for op in expected_value)
                elif key == "field_filters":
                    for field, value in expected_value.items():
                        assert parsed["field_filters"][field] == value
                else:
                    assert parsed[key] == expected_value

    def test_query_normalization(self, query_parser):
        """Test search query normalization and cleaning."""
        raw_queries = [
            ("  Artificial   Intelligence  ", "artificial intelligence"),
            ("MACHINE LEARNING!!!", "machine learning"),
            ("AI & ML Technologies", "ai and ml technologies"),
            ("Deep-Learning/Neural-Networks", "deep learning neural networks")
        ]

        for raw, expected in raw_queries:
            normalized = query_parser.normalize_search_query(raw)
            assert normalized == expected

    def test_query_expansion(self, query_parser):
        """Test search query expansion with synonyms and related terms."""
        base_queries = [
            ("AI", ["artificial intelligence", "machine intelligence", "computer intelligence"]),
            ("ML", ["machine learning", "statistical learning", "automated learning"]),
            ("neural network", ["neural net", "artificial neural network", "connectionist system"])
        ]

        for base_query, expected_expansions in base_queries:
            expanded = query_parser.expand_query_with_synonyms(base_query)

            # Should include original terms
            assert base_query.lower() in [term.lower() for term in expanded["expanded_terms"]]

            # Should include expected expansions
            expansion_found = any(
                expansion.lower() in [term.lower() for term in expanded["expanded_terms"]]
                for expansion in expected_expansions
            )
            assert expansion_found, f"Expected expansion not found for query: {base_query}"

    def test_query_validation(self, query_parser):
        """Test search query validation."""
        valid_queries = [
            "artificial intelligence",
            'title:"machine learning"',
            "AI OR ML",
            "content:neural networks AND tags:technical"
        ]

        invalid_queries = [
            "",  # Empty query
            "   ",  # Whitespace only
            'invalid_field:"value"',  # Invalid field name
            "unclosed quotes\"",  # Unclosed quotes
            "invalid operator XOR",  # Unsupported operator
            "query with | pipe operator"  # Invalid operator
        ]

        for valid_query in valid_queries:
            assert query_parser.validate_query(valid_query) is True

        for invalid_query in invalid_queries:
            assert query_parser.validate_query(invalid_query) is False


class TestFullTextSearch:
    """Test Full-Text Search functionality."""

    @pytest.fixture
    def search_handler(self, mock_search_engine, mock_repository):
        """Create search handler instance."""
        return SearchQueryHandler(mock_search_engine, mock_repository)

    def test_basic_full_text_search(self, search_handler):
        """Test basic full-text search functionality."""
        query = "artificial intelligence machine learning"

        search_result = search_handler.handle_full_text_search(query)

        assert search_result["success"] is True
        assert "results" in search_result
        assert "total_hits" in search_result
        assert search_result["total_hits"] >= 0
        assert "execution_time_ms" in search_result

    def test_search_with_relevance_ranking(self, search_handler):
        """Test search results with relevance ranking."""
        query = "neural networks"

        result = search_handler.handle_full_text_search(query)

        # Results should be sorted by relevance
        results = result["results"]
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i]["relevance_score"] >= results[i + 1]["relevance_score"]

        # High relevance scores should be > 0.5
        if results:
            assert results[0]["relevance_score"] > 0.5

    def test_search_result_highlighting(self, search_handler):
        """Test search result highlighting and snippets."""
        query = "machine learning algorithms"

        result = search_handler.handle_full_text_search_with_highlighting(query)

        for hit in result["results"]:
            assert "snippets" in hit
            assert "highlighted_content" in hit

            # Snippets should contain highlighted terms
            snippets = hit["snippets"]
            assert len(snippets) > 0

            # Check that at least one snippet contains highlighted terms
            highlighted_found = any(
                "<mark>" in snippet or "<em>" in snippet for snippet in snippets
            )
            assert highlighted_found, f"No highlighting found in snippets for document {hit['document_id']}"

    def test_search_performance_optimization(self, search_handler):
        """Test search performance optimization techniques."""
        complex_query = "artificial intelligence machine learning deep learning neural networks algorithms"

        # Test with different optimization strategies
        optimizations = ["basic", "optimized", "cached"]

        for optimization in optimizations:
            result = search_handler.handle_optimized_search(complex_query, optimization)

            assert result["success"] is True
            assert "optimization_used" in result
            assert result["optimization_used"] == optimization
            assert "performance_metrics" in result

            metrics = result["performance_metrics"]
            assert "execution_time_ms" in metrics
            assert "cache_used" in metrics
            assert "index_optimization" in metrics

            # Optimized search should be faster than basic
            if optimization == "optimized":
                assert metrics["execution_time_ms"] < 1000  # Less than 1 second

    def test_search_with_typo_tolerance(self, search_handler):
        """Test search with typo tolerance and fuzzy matching."""
        typo_queries = [
            ("machin lerning", "machine learning"),  # Common typos
            ("artifical inteligence", "artificial intelligence"),
            ("neural netwoks", "neural networks"),
            ("algorithims", "algorithms")
        ]

        for typo_query, intended_query in typo_queries:
            result = search_handler.handle_fuzzy_search(typo_query)

            assert result["success"] is True
            assert result["typo_correction_applied"] is True
            assert result["corrected_query"] == intended_query
            assert len(result["results"]) > 0

    def test_incremental_search(self, search_handler):
        """Test incremental search as user types."""
        partial_queries = [
            "a",
            "ar",
            "art",
            "arti",
            "artif",
            "artifi",
            "artific",
            "artifici",
            "artificia",
            "artificial"
        ]

        previous_results = set()

        for partial_query in partial_queries:
            result = search_handler.handle_incremental_search(partial_query)

            assert result["success"] is True
            assert "partial_results" in result
            assert "is_complete" in result

            current_result_ids = {hit["document_id"] for hit in result["partial_results"]}

            # Results should be subset or equal to previous results (refining search)
            if previous_results:
                assert current_result_ids.issubset(previous_results) or current_result_ids == previous_results

            previous_results = current_result_ids

            # Should indicate if search is complete
            assert isinstance(result["is_complete"], bool)


class TestMetadataFiltering:
    """Test Metadata-based Filtering functionality."""

    @pytest.fixture
    def filter_service(self, mock_repository):
        """Create filter service instance."""
        return SearchService(repository=mock_repository)

    def test_basic_metadata_filtering(self, filter_service):
        """Test basic metadata-based filtering."""
        filters = {
            "author": "john.doe@company.com",
            "content_type": "text/markdown",
            "tags": ["technical", "ai"]
        }

        filtered_results = filter_service.apply_metadata_filters(filters)

        assert "filtered_documents" in filtered_results
        assert "filter_applied" in filtered_results
        assert filtered_results["filter_applied"] is True

        # Verify filters were applied correctly
        for doc in filtered_results["filtered_documents"]:
            assert doc["metadata"]["author"] == filters["author"]
            assert doc["content_type"] == filters["content_type"]
            assert all(tag in doc["tags"] for tag in filters["tags"])

    def test_date_range_filtering(self, filter_service):
        """Test date range filtering."""
        date_filters = {
            "created_after": "2024-01-01",
            "created_before": "2024-12-31",
            "updated_after": "2024-06-01"
        }

        filtered_results = filter_service.apply_date_filters(date_filters)

        for doc in filtered_results["filtered_documents"]:
            created_date = datetime.fromisoformat(doc["metadata"]["created_at"])
            updated_date = datetime.fromisoformat(doc["metadata"]["updated_at"])

            assert created_date >= datetime.fromisoformat(date_filters["created_after"])
            assert created_date <= datetime.fromisoformat(date_filters["created_before"])
            assert updated_date >= datetime.fromisoformat(date_filters["updated_after"])

    def test_numeric_range_filtering(self, filter_service):
        """Test numeric range filtering (file size, word count, etc.)."""
        numeric_filters = {
            "word_count": {"min": 100, "max": 1000},
            "file_size_bytes": {"min": 1024, "max": 1048576},  # 1KB to 1MB
            "page_count": {"min": 1, "max": 50}
        }

        filtered_results = filter_service.apply_numeric_filters(numeric_filters)

        for doc in filtered_results["filtered_documents"]:
            assert numeric_filters["word_count"]["min"] <= doc["metadata"]["word_count"] <= numeric_filters["word_count"]["max"]
            assert numeric_filters["file_size_bytes"]["min"] <= doc["file_size_bytes"] <= numeric_filters["file_size_bytes"]["max"]
            assert numeric_filters["page_count"]["min"] <= doc["metadata"]["page_count"] <= numeric_filters["page_count"]["max"]

    def test_complex_boolean_filtering(self, filter_service):
        """Test complex boolean filtering with AND/OR/NOT operations."""
        complex_filters = {
            "boolean_expression": "(author:john.doe@company.com OR author:jane.smith@company.com) AND tags:technical AND NOT status:archived",
            "parsed_filters": {
                "or_conditions": [
                    {"author": "john.doe@company.com"},
                    {"author": "jane.smith@company.com"}
                ],
                "and_conditions": [
                    {"tags": "technical"}
                ],
                "not_conditions": [
                    {"status": "archived"}
                ]
            }
        }

        filtered_results = filter_service.apply_boolean_filters(complex_filters)

        assert filtered_results["boolean_logic_applied"] is True

        for doc in filtered_results["filtered_documents"]:
            # Should match OR condition (at least one author)
            author_match = (doc["metadata"]["author"] == "john.doe@company.com" or
                          doc["metadata"]["author"] == "jane.smith@company.com")
            assert author_match

            # Should match AND condition (technical tag)
            assert "technical" in doc["tags"]

            # Should not match NOT condition (not archived)
            assert doc["status"] != "archived"

    def test_faceted_search(self, filter_service):
        """Test faceted search with dynamic filter options."""
        search_query = "artificial intelligence"

        faceted_results = filter_service.perform_faceted_search(search_query)

        assert "facets" in faceted_results
        assert "search_results" in faceted_results

        facets = faceted_results["facets"]

        # Should include common facets
        expected_facets = ["content_type", "author", "tags", "language", "status", "created_date"]
        for facet in expected_facets:
            assert facet in facets

        # Each facet should have counts
        for facet_name, facet_data in facets.items():
            assert "terms" in facet_data
            for term in facet_data["terms"]:
                assert "term" in term
                assert "count" in term
                assert term["count"] >= 0

    def test_dynamic_filter_generation(self, filter_service):
        """Test dynamic filter generation based on search results."""
        search_results = [
            {"tags": ["ai", "technical"], "author": "john@example.com", "content_type": "markdown"},
            {"tags": ["ml", "tutorial"], "author": "jane@example.com", "content_type": "markdown"},
            {"tags": ["ai", "research"], "author": "john@example.com", "content_type": "pdf"}
        ]

        dynamic_filters = filter_service.generate_dynamic_filters(search_results)

        assert "available_filters" in dynamic_filters

        available_filters = dynamic_filters["available_filters"]

        # Should include tag filters
        assert "tags" in available_filters
        tag_options = available_filters["tags"]
        assert "ai" in tag_options
        assert "technical" in tag_options
        assert "ml" in tag_options

        # Should include author filters
        assert "author" in available_filters
        author_options = available_filters["author"]
        assert "john@example.com" in author_options
        assert "jane@example.com" in author_options

        # Should include content type filters
        assert "content_type" in available_filters
        content_type_options = available_filters["content_type"]
        assert "markdown" in content_type_options
        assert "pdf" in content_type_options


class TestSemanticSearch:
    """Test Semantic Search functionality."""

    @pytest.fixture
    def semantic_searcher(self, mock_ai_service, mock_search_engine):
        """Create semantic search instance."""
        return SearchService(ai_service=mock_ai_service, search_engine=mock_search_engine)

    def test_semantic_query_understanding(self, semantic_searcher):
        """Test semantic understanding of search queries."""
        natural_queries = [
            "documents about smart computer systems",
            "papers on teaching machines to learn",
            "research about thinking robots",
            "articles on automated decision making"
        ]

        for query in natural_queries:
            understanding = semantic_searcher.understand_query_semantics(query)

            assert "semantic_intent" in understanding
            assert "key_concepts" in understanding
            assert "related_terms" in understanding

            # Should identify AI/ML concepts
            concepts = understanding["key_concepts"]
            ai_concepts = ["artificial intelligence", "machine learning", "automation", "algorithms"]
            assert any(concept in concepts for concept in ai_concepts)

    def test_vector_similarity_search(self, semantic_searcher):
        """Test vector-based similarity search."""
        query = "machine learning algorithms"

        similarity_results = semantic_searcher.perform_vector_similarity_search(query)

        assert "vector_search_results" in similarity_results
        assert "similarity_scores" in similarity_results

        results = similarity_results["vector_search_results"]
        scores = similarity_results["similarity_scores"]

        # Results should be sorted by similarity
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]

        # High similarity scores should be > 0.7
        if scores:
            assert scores[0] > 0.7

    def test_concept_expansion_search(self, semantic_searcher):
        """Test search with concept expansion."""
        base_query = "AI"

        expanded_search = semantic_searcher.perform_concept_expanded_search(base_query)

        assert "expanded_concepts" in expanded_search
        assert "concept_hierarchy" in expanded_search
        assert "expanded_results" in expanded_search

        expanded_concepts = expanded_search["expanded_concepts"]

        # Should include broader and narrower concepts
        assert "broader_concepts" in expanded_concepts
        assert "narrower_concepts" in expanded_concepts
        assert "related_concepts" in expanded_concepts

        # Should include expected AI concepts
        all_concepts = (expanded_concepts["broader_concepts"] +
                       expanded_concepts["narrower_concepts"] +
                       expanded_concepts["related_concepts"])

        expected_concepts = ["machine learning", "neural networks", "computer science"]
        assert any(concept in all_concepts for concept in expected_concepts)

    def test_context_aware_search(self, semantic_searcher):
        """Test context-aware search based on user history."""
        user_context = {
            "recent_searches": ["machine learning", "neural networks", "deep learning"],
            "preferred_content_types": ["technical_papers", "tutorials"],
            "domain_interests": ["artificial_intelligence", "data_science"],
            "skill_level": "intermediate"
        }

        query = "algorithms"

        context_search = semantic_searcher.perform_context_aware_search(query, user_context)

        assert "context_influence" in context_search
        assert "personalized_results" in context_search
        assert "context_relevance_score" in context_search

        # Should personalize results based on context
        context_influence = context_search["context_influence"]
        assert context_influence["domain_relevance"] > 0.5
        assert context_influence["skill_level_match"] > 0.6

    def test_multilingual_semantic_search(self, semantic_searcher):
        """Test semantic search across multiple languages."""
        multilingual_queries = [
            ("artificial intelligence", "en"),
            ("inteligencia artificial", "es"),
            ("intelligence artificielle", "fr"),
            ("künstliche Intelligenz", "de")
        ]

        for query, language in multilingual_queries:
            multilingual_results = semantic_searcher.perform_multilingual_search(query, language)

            assert "language_detected" in multilingual_results
            assert multilingual_results["language_detected"] == language
            assert "cross_language_results" in multilingual_results
            assert "translation_used" in multilingual_results

            # Should find results in original language and possibly translations
            assert len(multilingual_results["cross_language_results"]) > 0


class TestSearchPerformanceOptimization:
    """Test Search Performance Optimization functionality."""

    @pytest.fixture
    def performance_optimizer(self, mock_cache, mock_search_engine):
        """Create search performance optimizer instance."""
        return SearchService(cache=mock_cache, search_engine=mock_search_engine)

    def test_search_result_caching(self, performance_optimizer):
        """Test search result caching for performance."""
        query = "machine learning algorithms"

        # First search - should cache results
        result1 = performance_optimizer.perform_cached_search(query)
        assert result1["cache_used"] is False
        assert "results" in result1

        # Second search - should use cache
        result2 = performance_optimizer.perform_cached_search(query)
        assert result2["cache_used"] is True
        assert result1["results"] == result2["results"]

        # Should be significantly faster
        assert result2["execution_time_ms"] < result1["execution_time_ms"]

    def test_search_index_optimization(self, performance_optimizer):
        """Test search index optimization techniques."""
        optimization_result = performance_optimizer.optimize_search_index()

        assert "optimization_applied" in optimization_result
        assert "index_performance_metrics" in optimization_result
        assert "optimization_recommendations" in optimization_result

        metrics = optimization_result["index_performance_metrics"]
        assert "index_size_mb" in metrics
        assert "document_count" in metrics
        assert "average_query_time_ms" in metrics

        # Should show performance improvements
        assert metrics["average_query_time_ms"] < 100  # Fast queries

    def test_query_performance_prediction(self, performance_optimizer):
        """Test query performance prediction and optimization."""
        test_queries = [
            "simple word",
            "complex phrase with multiple terms",
            "very long query with many words and specific requirements",
            'field:"value" AND complex:"query with operators"'
        ]

        for query in test_queries:
            prediction = performance_optimizer.predict_query_performance(query)

            assert "estimated_execution_time_ms" in prediction
            assert "complexity_score" in prediction
            assert "optimization_suggestions" in prediction

            # Simple queries should be faster
            if "simple word" in query:
                assert prediction["estimated_execution_time_ms"] < 50
                assert prediction["complexity_score"] < 0.3

    def test_parallel_search_execution(self, performance_optimizer):
        """Test parallel execution of multiple search operations."""
        queries = [
            "machine learning",
            "artificial intelligence",
            "neural networks",
            "deep learning",
            "computer vision"
        ]

        parallel_results = performance_optimizer.execute_parallel_searches(queries)

        assert "parallel_execution_results" in parallel_results
        assert "total_execution_time_ms" in parallel_results
        assert "individual_query_times" in parallel_results

        results = parallel_results["parallel_execution_results"]
        assert len(results) == len(queries)

        individual_times = parallel_results["individual_query_times"]
        assert len(individual_times) == len(queries)

        # Parallel execution should be faster than sequential
        total_parallel_time = parallel_results["total_execution_time_ms"]
        estimated_sequential_time = sum(individual_times)

        assert total_parallel_time < estimated_sequential_time

    def test_search_load_balancing(self, performance_optimizer):
        """Test load balancing across multiple search instances."""
        search_load = {
            "instance_1": {"current_load": 30, "capacity": 100},
            "instance_2": {"current_load": 80, "capacity": 100},
            "instance_3": {"current_load": 10, "capacity": 100}
        }

        queries = ["query_1", "query_2", "query_3", "query_4", "query_5"]

        load_balanced_results = performance_optimizer.balance_search_load(search_load, queries)

        assert "load_distribution" in load_balanced_results
        assert "instance_assignments" in load_balanced_results
        assert "load_balance_efficiency" in load_balanced_results

        assignments = load_balanced_results["instance_assignments"]

        # Should distribute load evenly
        instance_loads = {}
        for assignment in assignments:
            instance = assignment["assigned_instance"]
            instance_loads[instance] = instance_loads.get(instance, 0) + 1

        # No instance should be overloaded
        for instance, load in instance_loads.items():
            max_load = search_load[instance]["capacity"]
            assert load <= max_load

        # Load balance efficiency should be good
        assert load_balanced_results["load_balance_efficiency"] > 0.8

    def test_adaptive_search_optimization(self, performance_optimizer):
        """Test adaptive search optimization based on usage patterns."""
        usage_patterns = {
            "popular_queries": ["machine learning", "artificial intelligence"],
            "slow_queries": ["complex boolean query with many terms"],
            "frequent_filters": ["author:john.doe", "status:published"],
            "peak_usage_hours": [9, 10, 11, 14, 15, 16]
        }

        adaptive_optimization = performance_optimizer.apply_adaptive_optimization(usage_patterns)

        assert "optimizations_applied" in adaptive_optimization
        assert "performance_improvements" in adaptive_optimization
        assert "adaptive_rules" in adaptive_optimization

        optimizations = adaptive_optimization["optimizations_applied"]

        # Should include query result caching for popular queries
        assert "popular_query_caching" in optimizations

        # Should include index optimization for slow queries
        assert "slow_query_optimization" in optimizations

        # Should show performance improvements
        improvements = adaptive_optimization["performance_improvements"]
        assert improvements["average_query_time_improvement_percent"] > 10
        assert improvements["cache_hit_rate_improvement"] > 0.1
