"""Comprehensive Source Agent Tests.

Tests for data ingestion from multiple sources (GitHub, Jira, Confluence),
data normalization, endpoint analysis, and source management in the LLM Documentation Ecosystem.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import json

# Adjust path for local imports
import sys
from pathlib import Path

# Add the Source Agent service directory to Python path
source_agent_path = Path(__file__).parent.parent.parent.parent / "services" / "source-agent"
sys.path.insert(0, str(source_agent_path))

from modules.core.data_ingestor import DataIngestor
from modules.core.source_manager import SourceManager
from modules.core.endpoint_analyzer import EndpointAnalyzer
from modules.core.data_normalizer import DataNormalizer
from modules.models import SourceConfig, IngestionRequest, NormalizationResult

# Test markers for parallel execution and categorization
pytestmark = [
    pytest.mark.unit,
    pytest.mark.parallel_safe,
    pytest.mark.source_agent
]


@pytest.fixture
def mock_source_clients():
    """Mock source clients for testing."""
    with patch('modules.core.data_ingestor.SourceClients') as mock_clients_class:
        mock_clients = MagicMock()
        mock_clients_class.return_value = mock_clients

        # Mock GitHub API responses
        mock_clients.github_get = AsyncMock(return_value={
            "success": True,
            "data": {
                "name": "test-repo",
                "description": "Test repository",
                "language": "Python",
                "readme": "# Test Repository\nThis is a test repository."
            }
        })

        # Mock Jira API responses
        mock_clients.jira_get = AsyncMock(return_value={
            "success": True,
            "data": {
                "issues": [
                    {"key": "PROJ-123", "summary": "Test issue", "description": "Test description"}
                ]
            }
        })

        # Mock Confluence API responses
        mock_clients.confluence_get = AsyncMock(return_value={
            "success": True,
            "data": {
                "results": [
                    {"id": "12345", "title": "Test Page", "body": {"storage": {"value": "Test content"}}}
                ]
            }
        })

        yield mock_clients


@pytest.fixture
def data_ingestor(mock_source_clients):
    """Create DataIngestor instance for testing."""
    return DataIngestor()


@pytest.fixture
def source_manager(mock_source_clients):
    """Create SourceManager instance for testing."""
    return SourceManager()


@pytest.fixture
def endpoint_analyzer():
    """Create EndpointAnalyzer instance for testing."""
    return EndpointAnalyzer()


@pytest.fixture
def data_normalizer():
    """Create DataNormalizer instance for testing."""
    return DataNormalizer()


class TestDataIngestor:
    """Comprehensive tests for data ingestion functionality."""

    def test_ingest_github_repository(self, data_ingestor, mock_source_clients):
        """Test ingestion of GitHub repository data."""
        source_config = SourceConfig(
            source_type="github",
            url="https://github.com/test/repo",
            credentials={"token": "test-token"}
        )

        result = data_ingestor.ingest_github_repository(source_config)

        assert isinstance(result, dict)
        assert "success" in result
        assert "data" in result
        assert "source_type" in result
        assert result["source_type"] == "github"

        data = result["data"]
        assert "repository_info" in data
        assert "readme_content" in data
        assert "metadata" in data

    def test_ingest_jira_issues(self, data_ingestor, mock_source_clients):
        """Test ingestion of Jira issues."""
        source_config = SourceConfig(
            source_type="jira",
            url="https://company.atlassian.net",
            credentials={"username": "test", "password": "test"}
        )

        query_params = {"project": "PROJ", "status": "Open"}

        result = data_ingestor.ingest_jira_issues(source_config, query_params)

        assert isinstance(result, dict)
        assert "success" in result
        assert "data" in result

        data = result["data"]
        assert "issues" in data
        assert "metadata" in data
        assert "query_info" in data

    def test_ingest_confluence_pages(self, data_ingestor, mock_source_clients):
        """Test ingestion of Confluence pages."""
        source_config = SourceConfig(
            source_type="confluence",
            url="https://company.atlassian.net/wiki",
            credentials={"username": "test", "password": "test"}
        )

        space_key = "TECH"

        result = data_ingestor.ingest_confluence_pages(source_config, space_key)

        assert isinstance(result, dict)
        assert "success" in result
        assert "data" in result

        data = result["data"]
        assert "pages" in data
        assert "space_info" in data
        assert "content_stats" in data

    def test_multi_source_ingestion(self, data_ingestor, mock_source_clients):
        """Test ingestion from multiple sources simultaneously."""
        sources = [
            {
                "type": "github",
                "config": SourceConfig(source_type="github", url="https://github.com/test/repo")
            },
            {
                "type": "jira",
                "config": SourceConfig(source_type="jira", url="https://company.atlassian.net")
            }
        ]

        result = data_ingestor.ingest_from_multiple_sources(sources)

        assert isinstance(result, dict)
        assert "success" in result
        assert "results" in result

        results = result["results"]
        assert isinstance(results, list)
        assert len(results) == len(sources)

        # Each source should have its own result
        for source_result in results:
            assert "source_type" in source_result
            assert "success" in source_result

    def test_incremental_ingestion(self, data_ingestor, mock_source_clients):
        """Test incremental ingestion with change detection."""
        source_config = SourceConfig(
            source_type="github",
            url="https://github.com/test/repo"
        )

        # Simulate previous ingestion state
        previous_state = {
            "last_commit": "abc123",
            "last_updated": "2024-01-15T10:00:00Z"
        }

        result = data_ingestor.incremental_ingest(source_config, previous_state)

        assert isinstance(result, dict)
        assert "success" in result
        assert "changes_detected" in result
        assert "new_data" in result
        assert "updated_state" in result

    def test_ingestion_with_filtering(self, data_ingestor, mock_source_clients):
        """Test ingestion with content filtering."""
        source_config = SourceConfig(
            source_type="github",
            url="https://github.com/test/repo"
        )

        filters = {
            "file_types": [".md", ".txt"],
            "exclude_patterns": ["node_modules", ".git"],
            "content_keywords": ["API", "documentation"]
        }

        result = data_ingestor.ingest_with_filters(source_config, filters)

        assert isinstance(result, dict)
        assert "success" in result
        assert "filtered_data" in result
        assert "filter_stats" in result

        filter_stats = result["filter_stats"]
        assert "files_processed" in filter_stats
        assert "files_filtered" in filter_stats
        assert "filter_criteria_applied" in filter_stats

    def test_ingestion_error_handling(self, data_ingestor, mock_source_clients):
        """Test error handling during ingestion."""
        # Mock failure scenario
        mock_source_clients.github_get.side_effect = Exception("Connection timeout")

        source_config = SourceConfig(
            source_type="github",
            url="https://github.com/test/repo"
        )

        result = data_ingestor.ingest_with_error_recovery(source_config)

        assert isinstance(result, dict)
        assert "success" in result  # Should handle error gracefully
        assert "error_handled" in result
        assert "recovery_attempted" in result

    def test_ingestion_rate_limiting(self, data_ingestor, mock_source_clients):
        """Test rate limiting during ingestion."""
        source_config = SourceConfig(
            source_type="github",
            url="https://github.com/test/repo"
        )

        rate_limit_config = {
            "requests_per_minute": 30,
            "burst_limit": 10,
            "backoff_strategy": "exponential"
        }

        result = data_ingestor.ingest_with_rate_limiting(source_config, rate_limit_config)

        assert isinstance(result, dict)
        assert "success" in result
        assert "rate_limiting_applied" in result
        assert "requests_made" in result

    def test_ingestion_progress_tracking(self, data_ingestor, mock_source_clients):
        """Test progress tracking during ingestion."""
        source_config = SourceConfig(
            source_type="github",
            url="https://github.com/test/repo"
        )

        progress_callback = MagicMock()

        result = data_ingestor.ingest_with_progress_tracking(
            source_config,
            progress_callback=progress_callback
        )

        assert isinstance(result, dict)
        assert "success" in result

        # Verify progress callback was called
        progress_callback.assert_called()

    def test_ingestion_data_validation(self, data_ingestor):
        """Test data validation during ingestion."""
        test_data = {
            "source_type": "github",
            "data": {
                "name": "test-repo",
                "description": "Test repository",
                "invalid_field": None,
                "empty_array": []
            }
        }

        validation_result = data_ingestor.validate_ingested_data(test_data)

        assert isinstance(validation_result, dict)
        assert "is_valid" in validation_result
        assert "validation_errors" in validation_result
        assert "data_quality_score" in validation_result

    def test_batch_ingestion_processing(self, data_ingestor, mock_source_clients):
        """Test batch processing of multiple ingestion requests."""
        requests = [
            IngestionRequest(source_type="github", url="https://github.com/test/repo1"),
            IngestionRequest(source_type="github", url="https://github.com/test/repo2"),
            IngestionRequest(source_type="jira", url="https://company.atlassian.net")
        ]

        batch_result = data_ingestor.batch_process_ingestion_requests(requests)

        assert isinstance(batch_result, dict)
        assert "success" in batch_result
        assert "batch_results" in batch_result

        batch_results = batch_result["batch_results"]
        assert isinstance(batch_results, list)
        assert len(batch_results) == len(requests)

    def test_ingestion_caching(self, data_ingestor, mock_source_clients):
        """Test caching of ingested data."""
        source_config = SourceConfig(
            source_type="github",
            url="https://github.com/test/repo"
        )

        # First ingestion
        result1 = data_ingestor.ingest_with_caching(source_config)

        # Second ingestion (should use cache)
        result2 = data_ingestor.ingest_with_caching(source_config)

        assert isinstance(result1, dict)
        assert isinstance(result2, dict)

        # Should indicate cache usage
        assert "cache_used" in result2
        assert result2["cache_used"] is True

    def test_ingestion_metadata_extraction(self, data_ingestor):
        """Test extraction of metadata during ingestion."""
        raw_data = {
            "name": "test-repo",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-20T15:30:00Z",
            "author": "test-user",
            "tags": ["api", "documentation"]
        }

        metadata = data_ingestor.extract_ingestion_metadata(raw_data)

        assert isinstance(metadata, dict)
        assert "ingestion_timestamp" in metadata
        assert "data_freshness" in metadata
        assert "source_characteristics" in metadata
        assert "quality_indicators" in metadata


class TestSourceManager:
    """Comprehensive tests for source management functionality."""

    def test_register_source(self, source_manager):
        """Test registration of data sources."""
        source_config = SourceConfig(
            source_type="github",
            url="https://github.com/test/repo",
            credentials={"token": "test-token"},
            name="test-github-source"
        )

        result = source_manager.register_source(source_config)

        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is True
        assert "source_id" in result

    def test_source_health_monitoring(self, source_manager, mock_source_clients):
        """Test monitoring of source health."""
        source_id = "test-source-123"

        health_status = source_manager.monitor_source_health(source_id)

        assert isinstance(health_status, dict)
        assert "status" in health_status
        assert "response_time" in health_status
        assert "last_successful_check" in health_status
        assert "error_count" in health_status

    def test_source_authentication_validation(self, source_manager):
        """Test validation of source authentication."""
        auth_configs = [
            {"type": "token", "token": "valid-token"},
            {"type": "basic", "username": "user", "password": "pass"},
            {"type": "oauth", "client_id": "id", "client_secret": "secret"}
        ]

        for auth_config in auth_configs:
            validation = source_manager.validate_source_authentication(auth_config)

            assert isinstance(validation, dict)
            assert "is_valid" in validation
            assert "auth_method" in validation

    def test_source_configuration_management(self, source_manager):
        """Test management of source configurations."""
        config_updates = {
            "rate_limit": 100,
            "timeout": 30,
            "retry_count": 3,
            "cache_ttl": 3600
        }

        source_id = "test-source-123"

        config_result = source_manager.update_source_configuration(source_id, config_updates)

        assert isinstance(config_result, dict)
        assert "success" in config_result
        assert "updated_config" in config_result

    def test_source_performance_tracking(self, source_manager):
        """Test tracking of source performance metrics."""
        source_id = "test-source-123"

        performance = source_manager.track_source_performance(source_id)

        assert isinstance(performance, dict)
        assert "average_response_time" in performance
        assert "success_rate" in performance
        assert "data_volume" in performance
        assert "error_patterns" in performance

    def test_source_failover_handling(self, source_manager):
        """Test failover handling for sources."""
        primary_source = "primary-github"
        backup_sources = ["backup-github-1", "backup-github-2"]

        failover_result = source_manager.handle_source_failover(
            primary_source=primary_source,
            backup_sources=backup_sources
        )

        assert isinstance(failover_result, dict)
        assert "failover_performed" in failover_result
        assert "new_primary" in failover_result
        assert "failover_time" in failover_result

    def test_source_data_quality_assessment(self, source_manager):
        """Test assessment of source data quality."""
        source_id = "test-source-123"

        quality_assessment = source_manager.assess_source_data_quality(source_id)

        assert isinstance(quality_assessment, dict)
        assert "overall_quality" in quality_assessment
        assert "data_completeness" in quality_assessment
        assert "data_accuracy" in quality_assessment
        assert "data_consistency" in quality_assessment

    def test_source_integration_testing(self, source_manager, mock_source_clients):
        """Test integration testing of sources."""
        source_config = SourceConfig(
            source_type="github",
            url="https://github.com/test/repo"
        )

        integration_test = source_manager.test_source_integration(source_config)

        assert isinstance(integration_test, dict)
        assert "integration_successful" in integration_test
        assert "test_results" in integration_test
        assert "issues_found" in integration_test

    def test_source_load_balancing(self, source_manager):
        """Test load balancing across multiple sources."""
        sources = ["source-1", "source-2", "source-3"]
        load_distribution = [30, 40, 30]  # percentages

        balancing = source_manager.balance_source_load(sources, load_distribution)

        assert isinstance(balancing, dict)
        assert "load_distribution" in balancing
        assert "balancing_strategy" in balancing
        assert "efficiency_metrics" in balancing

    def test_source_caching_strategy(self, source_manager):
        """Test caching strategies for sources."""
        source_id = "test-source-123"
        cache_config = {
            "ttl": 3600,
            "max_size": 1000,
            "invalidation_strategy": "lru"
        }

        caching = source_manager.configure_source_caching(source_id, cache_config)

        assert isinstance(caching, dict)
        assert "cache_configured" in caching
        assert "cache_strategy" in caching
        assert "expected_performance_gain" in caching


class TestEndpointAnalyzer:
    """Comprehensive tests for endpoint analysis functionality."""

    def test_analyze_api_endpoints(self, endpoint_analyzer):
        """Test analysis of API endpoints from code."""
        code_content = """
        @app.get("/users")
        def get_users():
            return {"users": []}

        @app.post("/users")
        def create_user(user: User):
            return {"user_id": 123}

        @app.get("/users/{user_id}")
        def get_user(user_id: int):
            return {"user": {"id": user_id}}
        """

        analysis = endpoint_analyzer.analyze_api_endpoints(code_content)

        assert isinstance(analysis, dict)
        assert "endpoints" in analysis
        assert "methods" in analysis
        assert "parameters" in analysis

        endpoints = analysis["endpoints"]
        assert len(endpoints) >= 3

        # Should identify HTTP methods
        methods = analysis["methods"]
        assert "GET" in methods
        assert "POST" in methods

    def test_extract_endpoint_patterns(self, endpoint_analyzer):
        """Test extraction of endpoint patterns."""
        endpoints = [
            "/users",
            "/users/{id}",
            "/users/{id}/posts",
            "/posts/{post_id}/comments/{comment_id}"
        ]

        patterns = endpoint_analyzer.extract_endpoint_patterns(endpoints)

        assert isinstance(patterns, dict)
        assert "resource_patterns" in patterns
        assert "parameter_patterns" in patterns
        assert "hierarchy_patterns" in patterns

    def test_endpoint_documentation_generation(self, endpoint_analyzer):
        """Test generation of endpoint documentation."""
        endpoint_data = {
            "path": "/users/{user_id}",
            "method": "GET",
            "parameters": [{"name": "user_id", "type": "integer", "required": True}],
            "responses": [{"status": 200, "description": "User data"}]
        }

        documentation = endpoint_analyzer.generate_endpoint_documentation(endpoint_data)

        assert isinstance(documentation, dict)
        assert "markdown" in documentation
        assert "openapi_spec" in documentation
        assert "usage_examples" in documentation

    def test_endpoint_dependency_analysis(self, endpoint_analyzer):
        """Test analysis of endpoint dependencies."""
        code_content = """
        def get_user(user_id):
            db.query(user_id)

        def get_user_posts(user_id):
            user = get_user(user_id)
            return db.query_posts(user_id)

        @app.get("/users/{user_id}/posts")
        def api_get_user_posts(user_id):
            return get_user_posts(user_id)
        """

        dependencies = endpoint_analyzer.analyze_endpoint_dependencies(code_content)

        assert isinstance(dependencies, dict)
        assert "endpoint_dependencies" in dependencies
        assert "function_dependencies" in dependencies

    def test_endpoint_security_analysis(self, endpoint_analyzer):
        """Test security analysis of endpoints."""
        endpoint_config = {
            "path": "/admin/users",
            "method": "DELETE",
            "auth_required": True,
            "permissions": ["admin"]
        }

        security_analysis = endpoint_analyzer.analyze_endpoint_security(endpoint_config)

        assert isinstance(security_analysis, dict)
        assert "security_level" in security_analysis
        assert "vulnerabilities" in security_analysis
        assert "recommendations" in security_analysis

    def test_endpoint_performance_analysis(self, endpoint_analyzer):
        """Test performance analysis of endpoints."""
        endpoint_metrics = {
            "response_times": [0.1, 0.15, 0.12, 0.18, 0.09],
            "request_count": 1000,
            "error_rate": 0.02,
            "throughput": 50  # requests per second
        }

        performance_analysis = endpoint_analyzer.analyze_endpoint_performance(endpoint_metrics)

        assert isinstance(performance_analysis, dict)
        assert "performance_score" in performance_analysis
        assert "bottlenecks" in performance_analysis
        assert "optimization_suggestions" in performance_analysis

    def test_endpoint_version_analysis(self, endpoint_analyzer):
        """Test analysis of endpoint versioning."""
        versioned_endpoints = [
            "/v1/users",
            "/v2/users",
            "/v1/posts",
            "/v2/posts",
            "/v3/posts"
        ]

        version_analysis = endpoint_analyzer.analyze_endpoint_versions(versioned_endpoints)

        assert isinstance(version_analysis, dict)
        assert "version_distribution" in version_analysis
        assert "deprecated_versions" in version_analysis
        assert "migration_paths" in version_analysis

    def test_endpoint_testing_generation(self, endpoint_analyzer):
        """Test generation of endpoint tests."""
        endpoint_spec = {
            "path": "/users",
            "method": "GET",
            "parameters": [],
            "responses": [{"status": 200, "schema": {"type": "array"}}]
        }

        test_generation = endpoint_analyzer.generate_endpoint_tests(endpoint_spec)

        assert isinstance(test_generation, dict)
        assert "unit_tests" in test_generation
        assert "integration_tests" in test_generation
        assert "load_tests" in test_generation

    def test_endpoint_monitoring_setup(self, endpoint_analyzer):
        """Test setup of endpoint monitoring."""
        endpoints = ["/users", "/posts", "/comments"]

        monitoring = endpoint_analyzer.setup_endpoint_monitoring(endpoints)

        assert isinstance(monitoring, dict)
        assert "monitoring_configured" in monitoring
        assert "metrics_collected" in monitoring
        assert "alerts_configured" in monitoring


class TestDataNormalizer:
    """Comprehensive tests for data normalization functionality."""

    def test_normalize_github_data(self, data_normalizer):
        """Test normalization of GitHub data."""
        raw_github_data = {
            "name": "test-repo",
            "full_name": "user/test-repo",
            "description": "A test repository",
            "language": "Python",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-20T15:30:00Z",
            "owner": {"login": "testuser", "type": "User"},
            "readme": "# Test Repo\nThis is a test repository."
        }

        normalized = data_normalizer.normalize_github_data(raw_github_data)

        assert isinstance(normalized, dict)
        assert "normalized_data" in normalized
        assert "normalization_applied" in normalized
        assert "data_quality" in normalized

        normalized_data = normalized["normalized_data"]
        assert "repository_name" in normalized_data
        assert "description" in normalized_data
        assert "primary_language" in normalized_data

    def test_normalize_jira_data(self, data_normalizer):
        """Test normalization of Jira data."""
        raw_jira_data = {
            "issues": [
                {
                    "key": "PROJ-123",
                    "fields": {
                        "summary": "Implement user authentication",
                        "description": "Need to implement OAuth2 authentication",
                        "status": {"name": "In Progress"},
                        "priority": {"name": "High"},
                        "assignee": {"displayName": "John Doe"},
                        "created": "2024-01-15T10:00:00.000+0000",
                        "updated": "2024-01-20T15:30:00.000+0000"
                    }
                }
            ]
        }

        normalized = data_normalizer.normalize_jira_data(raw_jira_data)

        assert isinstance(normalized, dict)
        assert "normalized_issues" in normalized
        assert "normalization_rules_applied" in normalized

        normalized_issues = normalized["normalized_issues"]
        assert len(normalized_issues) > 0

        issue = normalized_issues[0]
        assert "issue_key" in issue
        assert "title" in issue
        assert "description" in issue
        assert "status" in issue

    def test_normalize_confluence_data(self, data_normalizer):
        """Test normalization of Confluence data."""
        raw_confluence_data = {
            "results": [
                {
                    "id": "12345",
                    "title": "API Documentation",
                    "body": {
                        "storage": {
                            "value": "<p>This is the API documentation content.</p>"
                        }
                    },
                    "version": {"number": 5},
                    "createdDate": "2024-01-15T10:00:00.000Z",
                    "lastModified": "2024-01-20T15:30:00.000Z"
                }
            ]
        }

        normalized = data_normalizer.normalize_confluence_data(raw_confluence_data)

        assert isinstance(normalized, dict)
        assert "normalized_pages" in normalized

        normalized_pages = normalized["normalized_pages"]
        assert len(normalized_pages) > 0

        page = normalized_pages[0]
        assert "page_id" in page
        assert "title" in page
        assert "content" in page
        assert "last_modified" in page

    def test_cross_source_data_consolidation(self, data_normalizer):
        """Test consolidation of data from multiple sources."""
        source_data = {
            "github": [{"repository_name": "api-lib", "description": "API library"}],
            "jira": [{"issue_key": "PROJ-123", "title": "API documentation needed"}],
            "confluence": [{"title": "API Docs", "content": "API documentation content"}]
        }

        consolidated = data_normalizer.consolidate_cross_source_data(source_data)

        assert isinstance(consolidated, dict)
        assert "consolidated_data" in consolidated
        assert "relationships_identified" in consolidated
        assert "data_quality_score" in consolidated

    def test_data_deduplication(self, data_normalizer):
        """Test deduplication of data."""
        duplicate_data = [
            {"title": "API Documentation", "content": "API docs content"},
            {"title": "API Documentation", "content": "API docs content"},  # duplicate
            {"title": "User Guide", "content": "User guide content"}
        ]

        deduplicated = data_normalizer.deduplicate_data(duplicate_data)

        assert isinstance(deduplicated, dict)
        assert "unique_items" in deduplicated
        assert "duplicates_removed" in deduplicated

        unique_items = deduplicated["unique_items"]
        assert len(unique_items) < len(duplicate_data)

    def test_data_validation_and_cleaning(self, data_normalizer):
        """Test validation and cleaning of data."""
        messy_data = {
            "title": "  API Documentation  ",
            "description": None,
            "tags": ["api", "", "documentation", None],
            "created": "2024-01-15",
            "invalid_field": "should_be_removed"
        }

        cleaned = data_normalizer.validate_and_clean_data(messy_data)

        assert isinstance(cleaned, dict)
        assert "cleaned_data" in cleaned
        assert "validation_errors" in cleaned
        assert "data_quality_improved" in cleaned

        cleaned_data = cleaned["cleaned_data"]
        assert cleaned_data["title"] == "API Documentation"  # trimmed
        assert "invalid_field" not in cleaned_data  # removed

    def test_data_schema_mapping(self, data_normalizer):
        """Test mapping of data to target schemas."""
        source_data = {
            "repo_name": "test-repo",
            "repo_description": "A test repository",
            "programming_language": "Python"
        }

        target_schema = {
            "name": "string",
            "description": "string",
            "language": "string",
            "category": "string"
        }

        mapped = data_normalizer.map_data_to_schema(source_data, target_schema)

        assert isinstance(mapped, dict)
        assert "mapped_data" in mapped
        assert "mapping_confidence" in mapped

        mapped_data = mapped["mapped_data"]
        assert "name" in mapped_data
        assert "description" in mapped_data
        assert "language" in mapped_data

    def test_data_enrichment(self, data_normalizer):
        """Test enrichment of data with additional information."""
        base_data = {
            "title": "API Documentation",
            "content": "This documents the API endpoints."
        }

        enrichment_sources = {
            "entity_recognition": ["API", "endpoints"],
            "sentiment_analysis": "neutral",
            "topic_classification": ["technical", "documentation"]
        }

        enriched = data_normalizer.enrich_data(base_data, enrichment_sources)

        assert isinstance(enriched, dict)
        assert "enriched_data" in enriched
        assert "enrichment_sources_used" in enriched
        assert "enrichment_quality" in enriched

    def test_data_quality_assessment(self, data_normalizer):
        """Test assessment of data quality."""
        test_data = {
            "title": "Complete API Documentation",
            "description": "Comprehensive API documentation with examples",
            "content": "Detailed content with proper formatting",
            "metadata": {"author": "expert", "reviewed": True}
        }

        quality_assessment = data_normalizer.assess_data_quality(test_data)

        assert isinstance(quality_assessment, dict)
        assert "overall_quality_score" in quality_assessment
        assert "quality_dimensions" in quality_assessment
        assert "improvement_suggestions" in quality_assessment

        # Should have high quality score for well-structured data
        assert quality_assessment["overall_quality_score"] > 0.7

    def test_data_transformation_pipeline(self, data_normalizer):
        """Test complete data transformation pipeline."""
        raw_data = {
            "source": "github",
            "data": {
                "name": "test-repo",
                "description": "  Test repository with extra spaces  ",
                "language": None,
                "invalid_field": "should_be_removed"
            }
        }

        pipeline_result = data_normalizer.run_transformation_pipeline(raw_data)

        assert isinstance(pipeline_result, dict)
        assert "transformed_data" in pipeline_result
        assert "pipeline_steps_applied" in pipeline_result
        assert "transformation_quality" in pipeline_result

        transformed_data = pipeline_result["transformed_data"]
        assert "name" in transformed_data
        assert transformed_data["description"] == "Test repository with extra spaces"  # cleaned
        assert "invalid_field" not in transformed_data  # removed

    def test_normalization_rule_engine(self, data_normalizer):
        """Test application of normalization rules."""
        custom_rules = [
            {"field": "description", "rule": "trim_whitespace", "priority": 1},
            {"field": "tags", "rule": "remove_empty", "priority": 2},
            {"field": "created_date", "rule": "standardize_format", "priority": 3}
        ]

        test_data = {
            "description": "  Test description  ",
            "tags": ["api", "", "documentation"],
            "created_date": "01/15/2024"
        }

        normalized = data_normalizer.apply_normalization_rules(test_data, custom_rules)

        assert isinstance(normalized, dict)
        assert "normalized_data" in normalized
        assert "rules_applied" in normalized

        normalized_data = normalized["normalized_data"]
        assert normalized_data["description"] == "Test description"  # trimmed
        assert "" not in normalized_data["tags"]  # empty removed
        assert normalized_data["created_date"] == "2024-01-15"  # standardized
