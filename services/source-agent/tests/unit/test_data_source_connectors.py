"""Unit Tests for Data Source Connectors in Source Agent Service.

This module tests data source connector capabilities including:
- GitHub repository integration and document fetching
- Web scraping and URL content extraction
- Database connection and query execution
- API endpoint integration and data retrieval
- File system access and document processing
- Authentication and authorization handling

Tests cover the complete data source ecosystem within the Source Agent service.
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any, List

from main import FetchRequest, FetchResponse


class TestDataSourceConnectors:
    """Test Data Source Connectors functionality."""

    @pytest.fixture
    def fetch_handler(self):
        """Create fetch handler instance with test configuration."""
        from main import FetchHandler
        return FetchHandler()

    @pytest.fixture
    def intelligent_ingestion(self):
        """Create intelligent ingestion instance with test configuration."""
        from main import IntelligentIngestion
        return IntelligentIngestion()

    @pytest.fixture
    def normalize_handler(self):
        """Create normalize handler instance with test configuration."""
        from main import NormalizeHandler
        return NormalizeHandler()

    @pytest.fixture
    def enterprise_data_sources(self):
        """Enterprise data sources for comprehensive testing."""
        return {
            "github_enterprise": {
                "type": "github",
                "config": {
                    "base_url": "https://github.company.com/api/v3",
                    "organization": "enterprise-org",
                    "repositories": ["api-gateway", "user-service", "order-service", "payment-service"],
                    "auth_token": "ghp_enterprise_token_1234567890abcdef",
                    "fetch_types": ["readme", "docs", "code", "issues", "pull_requests"]
                },
                "sample_data": {
                    "readme": "# Enterprise API Gateway\n\nA robust API gateway service for enterprise applications.",
                    "docs": "# API Documentation\n\n## Endpoints\n- GET /users\n- POST /orders\n- PUT /payments",
                    "code": "class ApiGateway:\n    def route_request(self, request):\n        # Enterprise routing logic\n        return self.apply_policies(request)",
                    "issues": [{"title": "High Memory Usage", "body": "API Gateway consuming excessive memory", "labels": ["bug", "performance"]}],
                    "pull_requests": [{"title": "Add Circuit Breaker", "body": "Implement circuit breaker pattern", "status": "open"}]
                }
            },
            "confluence_wiki": {
                "type": "confluence",
                "config": {
                    "base_url": "https://company.atlassian.net/wiki",
                    "space_key": "ARCH",
                    "username": "api_user@company.com",
                    "api_token": "ATLASSIAN_TOKEN_abcdef1234567890",
                    "pages": ["System Architecture", "API Specifications", "Deployment Guide", "Security Policies"]
                },
                "sample_data": {
                    "System Architecture": "# System Architecture\n\n## Components\n- API Gateway\n- Microservices\n- Database Cluster\n- Cache Layer",
                    "API Specifications": "# API Specifications\n\n## REST APIs\nGET /api/v1/users\nPOST /api/v1/orders",
                    "Deployment Guide": "# Deployment Guide\n\n## Kubernetes\n1. Build containers\n2. Deploy to k8s\n3. Configure ingress",
                    "Security Policies": "# Security Policies\n\n## Authentication\n- JWT tokens\n- OAuth2 flow\n## Authorization\n- RBAC\n- ABAC"
                }
            },
            "database_system": {
                "type": "database",
                "config": {
                    "connection_string": "postgresql://app_user:secure_password@db.company.com:5432/enterprise_db",
                    "schema": "public",
                    "tables": ["users", "orders", "products", "audit_logs"],
                    "query_timeout": 30,
                    "max_rows": 10000
                },
                "sample_data": {
                    "users": [
                        {"id": 1, "email": "john.doe@company.com", "role": "admin", "department": "IT"},
                        {"id": 2, "jane.smith@company.com", "role": "user", "department": "Sales"}
                    ],
                    "orders": [
                        {"id": 1001, "user_id": 1, "amount": 299.99, "status": "completed"},
                        {"id": 1002, "user_id": 2, "amount": 149.50, "status": "pending"}
                    ],
                    "schema_info": {
                        "tables": ["users", "orders", "products"],
                        "relationships": ["users.id -> orders.user_id"]
                    }
                }
            },
            "rest_api_endpoints": {
                "type": "rest_api",
                "config": {
                    "base_url": "https://api.company.com/v1",
                    "endpoints": ["/users", "/orders", "/products", "/analytics"],
                    "auth_type": "bearer",
                    "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "rate_limit": 100,
                    "timeout": 30
                },
                "sample_data": {
                    "/users": {"users": [{"id": 1, "name": "John Doe"}, {"id": 2, "name": "Jane Smith"}]},
                    "/orders": {"orders": [{"id": 1001, "total": 299.99}, {"id": 1002, "total": 149.50}]},
                    "/products": {"products": [{"id": 2001, "name": "Widget A"}, {"id": 2002, "name": "Widget B"}]},
                    "/analytics": {"metrics": {"total_users": 1250, "total_orders": 5432, "revenue": 1250000.00}}
                }
            },
            "file_system_share": {
                "type": "filesystem",
                "config": {
                    "base_path": "/mnt/company_docs",
                    "allowed_extensions": [".md", ".txt", ".pdf", ".docx", ".xlsx"],
                    "max_file_size": 10485760,  # 10MB
                    "recursive": True,
                    "exclude_patterns": ["*.tmp", "*.bak", "node_modules/**"]
                },
                "sample_data": {
                    "architecture.md": "# System Architecture\n\nEnterprise system design and documentation.",
                    "requirements.txt": "# Python Dependencies\nfastapi==0.100.0\nuvicorn==0.23.0\npydantic==2.0.0",
                    "deployment.pdf": "b'%PDF-1.4\\n1 0 obj\\n<<\\n/Type /Catalog\\n/Pages 2 0 R\\n>>\\nendobj\\n...'",
                    "api_spec.yaml": "openapi: 3.0.0\ninfo:\n  title: Company API\n  version: 1.0.0\npaths:\n  /users:\n    get:\n      summary: Get users"
                }
            }
        }

    def test_github_connector_integration(self, fetch_handler, enterprise_data_sources):
        """Test GitHub connector integration and document fetching."""
        github_config = enterprise_data_sources["github_enterprise"]

        # Test README fetching
        with patch("main.FetchHandler._make_github_request") as mock_request:
            mock_request.return_value = {
                "content": github_config["sample_data"]["readme"],
                "encoding": "utf-8"
            }

            result = fetch_handler.fetch_github_document(
                owner="enterprise-org",
                repo="api-gateway",
                doc_type="readme",
                auth_token=github_config["config"]["auth_token"]
            )

            assert result["success"] is True
            assert result["content"] == github_config["sample_data"]["readme"]
            assert result["metadata"]["source"] == "github"
            assert result["metadata"]["owner"] == "enterprise-org"
            assert result["metadata"]["repo"] == "api-gateway"

        # Test repository structure analysis
        with patch("main.FetchHandler._get_repo_contents") as mock_contents:
            mock_contents.return_value = [
                {"name": "README.md", "type": "file", "path": "README.md"},
                {"name": "docs", "type": "dir", "path": "docs"},
                {"name": "src", "type": "dir", "path": "src"}
            ]

            structure = fetch_handler.analyze_github_structure(
                owner="enterprise-org",
                repo="api-gateway",
                auth_token=github_config["config"]["auth_token"]
            )

            assert structure["total_files"] >= 3
            assert "docs" in structure["directories"]
            assert "src" in structure["directories"]

    def test_confluence_wiki_integration(self, fetch_handler, enterprise_data_sources):
        """Test Confluence wiki integration and page fetching."""
        confluence_config = enterprise_data_sources["confluence_wiki"]

        # Test page fetching
        with patch("main.FetchHandler._make_confluence_request") as mock_request:
            mock_request.return_value = {
                "body": {
                    "storage": {
                        "value": confluence_config["sample_data"]["System Architecture"]
                    }
                },
                "title": "System Architecture",
                "space": {"key": "ARCH"}
            }

            result = fetch_handler.fetch_confluence_page(
                base_url=confluence_config["config"]["base_url"],
                space_key=confluence_config["config"]["space_key"],
                page_title="System Architecture",
                username=confluence_config["config"]["username"],
                api_token=confluence_config["config"]["api_token"]
            )

            assert result["success"] is True
            assert "System Architecture" in result["content"]
            assert result["metadata"]["source"] == "confluence"
            assert result["metadata"]["space_key"] == "ARCH"

        # Test space content analysis
        with patch("main.FetchHandler._get_space_content") as mock_space:
            mock_space.return_value = [
                {"title": "System Architecture", "type": "page"},
                {"title": "API Specifications", "type": "page"},
                {"title": "Deployment Guide", "type": "page"}
            ]

            space_analysis = fetch_handler.analyze_confluence_space(
                base_url=confluence_config["config"]["base_url"],
                space_key=confluence_config["config"]["space_key"],
                username=confluence_config["config"]["username"],
                api_token=confluence_config["config"]["api_token"]
            )

            assert space_analysis["total_pages"] >= 3
            assert "System Architecture" in space_analysis["page_titles"]

    def test_database_connector_integration(self, fetch_handler, enterprise_data_sources):
        """Test database connector integration and query execution."""
        db_config = enterprise_data_sources["database_system"]

        # Test table data fetching
        with patch("main.FetchHandler._execute_db_query") as mock_query:
            mock_query.return_value = db_config["sample_data"]["users"]

            result = fetch_handler.fetch_database_table(
                connection_string=db_config["config"]["connection_string"],
                table_name="users",
                schema="public",
                max_rows=1000
            )

            assert result["success"] is True
            assert len(result["data"]) == 2
            assert result["metadata"]["table"] == "users"
            assert result["metadata"]["row_count"] == 2

        # Test schema analysis
        with patch("main.FetchHandler._get_table_schema") as mock_schema:
            mock_schema.return_value = db_config["sample_data"]["schema_info"]

            schema_result = fetch_handler.analyze_database_schema(
                connection_string=db_config["config"]["connection_string"],
                schema="public"
            )

            assert schema_result["success"] is True
            assert len(schema_result["tables"]) >= 3
            assert "relationships" in schema_result["schema_info"]

        # Test query execution with parameters
        with patch("main.FetchHandler._execute_parameterized_query") as mock_param_query:
            mock_param_query.return_value = [
                {"user_id": 1, "order_count": 5, "total_spent": 1499.50}
            ]

            query_result = fetch_handler.execute_database_query(
                connection_string=db_config["config"]["connection_string"],
                query="SELECT user_id, COUNT(*) as order_count, SUM(amount) as total_spent FROM orders WHERE user_id = $1 GROUP BY user_id",
                parameters=[1]
            )

            assert query_result["success"] is True
            assert len(query_result["data"]) == 1
            assert query_result["data"][0]["user_id"] == 1

    def test_rest_api_connector_integration(self, fetch_handler, enterprise_data_sources):
        """Test REST API connector integration and endpoint fetching."""
        api_config = enterprise_data_sources["rest_api_endpoints"]

        # Test endpoint data fetching
        with patch("main.FetchHandler._make_api_request") as mock_api:
            mock_api.return_value = api_config["sample_data"]["/users"]

            result = fetch_handler.fetch_rest_api_endpoint(
                base_url=api_config["config"]["base_url"],
                endpoint="/users",
                auth_type="bearer",
                auth_token=api_config["config"]["auth_token"],
                method="GET"
            )

            assert result["success"] is True
            assert "users" in result["data"]
            assert len(result["data"]["users"]) == 2
            assert result["metadata"]["endpoint"] == "/users"
            assert result["metadata"]["method"] == "GET"

        # Test API specification discovery
        with patch("main.FetchHandler._discover_api_endpoints") as mock_discover:
            mock_discover.return_value = {
                "endpoints": api_config["config"]["endpoints"],
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "auth_required": True
            }

            discovery_result = fetch_handler.discover_api_specification(
                base_url=api_config["config"]["base_url"],
                auth_token=api_config["config"]["auth_token"]
            )

            assert discovery_result["success"] is True
            assert len(discovery_result["endpoints"]) >= 4
            assert "GET" in discovery_result["supported_methods"]

    def test_filesystem_connector_integration(self, fetch_handler, enterprise_data_sources):
        """Test filesystem connector integration and file processing."""
        fs_config = enterprise_data_sources["file_system_share"]

        # Test file content fetching
        with patch("main.FetchHandler._read_file_content") as mock_read:
            mock_read.return_value = fs_config["sample_data"]["architecture.md"]

            result = fetch_handler.fetch_filesystem_document(
                file_path="/mnt/company_docs/architecture.md",
                base_path=fs_config["config"]["base_path"],
                allowed_extensions=fs_config["config"]["allowed_extensions"]
            )

            assert result["success"] is True
            assert "System Architecture" in result["content"]
            assert result["metadata"]["file_path"] == "/mnt/company_docs/architecture.md"
            assert result["metadata"]["extension"] == ".md"

        # Test directory structure analysis
        with patch("main.FetchHandler._list_directory") as mock_list:
            mock_list.return_value = [
                {"name": "architecture.md", "type": "file", "size": 1024},
                {"name": "api_docs", "type": "directory", "size": 0},
                {"name": "deployment.pdf", "type": "file", "size": 2048576}
            ]

            structure_result = fetch_handler.analyze_filesystem_structure(
                base_path=fs_config["config"]["base_path"],
                recursive=True,
                allowed_extensions=fs_config["config"]["allowed_extensions"],
                exclude_patterns=fs_config["config"]["exclude_patterns"]
            )

            assert structure_result["success"] is True
            assert structure_result["total_files"] >= 3
            assert "architecture.md" in structure_result["files"]
            assert "api_docs" in structure_result["directories"]

    def test_authentication_and_authorization(self, fetch_handler, enterprise_data_sources):
        """Test authentication and authorization handling across connectors."""
        # Test GitHub authentication
        github_config = enterprise_data_sources["github_enterprise"]

        with patch("main.FetchHandler._validate_github_token") as mock_validate:
            mock_validate.return_value = {"valid": True, "permissions": ["read", "write"], "user": "api_user"}

            auth_result = fetch_handler.validate_github_authentication(
                token=github_config["config"]["auth_token"]
            )

            assert auth_result["valid"] is True
            assert "read" in auth_result["permissions"]

        # Test API token authentication
        api_config = enterprise_data_sources["rest_api_endpoints"]

        with patch("main.FetchHandler._validate_jwt_token") as mock_jwt:
            mock_jwt.return_value = {"valid": True, "exp": 1640995200, "user": "service_account"}

            jwt_result = fetch_handler.validate_api_authentication(
                token=api_config["config"]["auth_token"],
                auth_type="bearer"
            )

            assert jwt_result["valid"] is True
            assert jwt_result["user"] == "service_account"

        # Test database connection authentication
        db_config = enterprise_data_sources["database_system"]

        with patch("main.FetchHandler._test_db_connection") as mock_db_test:
            mock_db_test.return_value = {"connected": True, "user": "app_user", "database": "enterprise_db"}

            db_auth_result = fetch_handler.validate_database_authentication(
                connection_string=db_config["config"]["connection_string"]
            )

            assert db_auth_result["connected"] is True
            assert db_auth_result["user"] == "app_user"

    def test_error_handling_and_resilience(self, fetch_handler):
        """Test error handling and resilience across data source connectors."""
        # Test GitHub rate limiting
        with patch("main.FetchHandler._make_github_request") as mock_request:
            mock_request.side_effect = Exception("API rate limit exceeded")

            with pytest.raises(Exception) as exc_info:
                fetch_handler.fetch_github_document(
                    owner="test",
                    repo="test",
                    doc_type="readme"
                )

            assert "rate limit" in str(exc_info.value).lower()

        # Test network timeouts
        with patch("main.FetchHandler._make_http_request") as mock_http:
            mock_http.side_effect = asyncio.TimeoutError("Connection timeout")

            with pytest.raises(asyncio.TimeoutError):
                fetch_handler.fetch_rest_api_endpoint(
                    base_url="https://api.example.com",
                    endpoint="/test"
                )

        # Test database connection failures
        with patch("main.FetchHandler._execute_db_query") as mock_db:
            mock_db.side_effect = Exception("Connection refused")

            with pytest.raises(Exception) as exc_info:
                fetch_handler.fetch_database_table(
                    connection_string="postgresql://invalid:connection@localhost:5432/test",
                    table_name="test"
                )

            assert "connection" in str(exc_info.value).lower()

        # Test file system access errors
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = PermissionError("Permission denied")

            with pytest.raises(PermissionError):
                fetch_handler.fetch_filesystem_document(
                    file_path="/restricted/file.txt"
                )

    def test_data_transformation_and_normalization(self, normalize_handler, enterprise_data_sources):
        """Test data transformation and normalization across sources."""
        # Test GitHub content normalization
        github_data = {
            "content": enterprise_data_sources["github_enterprise"]["sample_data"]["readme"],
            "metadata": {"source": "github", "owner": "test", "repo": "test"}
        }

        normalized_github = normalize_handler.normalize_github_content(github_data)

        assert normalized_github["success"] is True
        assert "normalized_content" in normalized_github
        assert normalized_github["metadata"]["content_type"] == "markdown"
        assert "document_structure" in normalized_github

        # Test Confluence content normalization
        confluence_data = {
            "content": enterprise_data_sources["confluence_wiki"]["sample_data"]["API Specifications"],
            "metadata": {"source": "confluence", "space": "ARCH"}
        }

        normalized_confluence = normalize_handler.normalize_confluence_content(confluence_data)

        assert normalized_confluence["success"] is True
        assert normalized_confluence["metadata"]["content_type"] == "wiki_markup"
        assert "sections" in normalized_confluence

        # Test database data normalization
        db_data = {
            "data": enterprise_data_sources["database_system"]["sample_data"]["users"],
            "metadata": {"source": "database", "table": "users"}
        }

        normalized_db = normalize_handler.normalize_database_content(db_data)

        assert normalized_db["success"] is True
        assert "structured_data" in normalized_db
        assert normalized_db["metadata"]["data_format"] == "tabular"

    def test_intelligent_ingestion_engine(self, intelligent_ingestion, enterprise_data_sources):
        """Test intelligent ingestion engine and content processing."""
        # Test content type detection
        test_contents = [
            (enterprise_data_sources["github_enterprise"]["sample_data"]["readme"], "markdown"),
            (enterprise_data_sources["confluence_wiki"]["sample_data"]["System Architecture"], "wiki"),
            (json.dumps(enterprise_data_sources["rest_api_endpoints"]["sample_data"]["/users"]), "json"),
            (enterprise_data_sources["database_system"]["sample_data"]["users"], "structured_data")
        ]

        for content, expected_type in test_contents:
            detected_type = intelligent_ingestion.detect_content_type(content)
            assert detected_type["content_type"] == expected_type

        # Test content quality assessment
        quality_result = intelligent_ingestion.assess_content_quality(
            content=enterprise_data_sources["github_enterprise"]["sample_data"]["readme"],
            source="github"
        )

        assert "quality_score" in quality_result
        assert "readability_score" in quality_result
        assert "completeness_score" in quality_result
        assert 0.0 <= quality_result["quality_score"] <= 1.0

        # Test content enrichment
        enrichment_result = intelligent_ingestion.enrich_content(
            content=enterprise_data_sources["github_enterprise"]["sample_data"]["readme"],
            metadata={"source": "github", "repo": "api-gateway"}
        )

        assert enrichment_result["success"] is True
        assert "enriched_metadata" in enrichment_result
        assert "content_insights" in enrichment_result

    def test_performance_and_scalability(self, fetch_handler, enterprise_data_sources):
        """Test connector performance and scalability."""
        import time

        # Test concurrent GitHub fetching
        github_config = enterprise_data_sources["github_enterprise"]

        async def fetch_single_repo(repo_name):
            with patch("main.FetchHandler._make_github_request") as mock_request:
                mock_request.return_value = {"content": f"# {repo_name}\nRepository content"}
                return await fetch_handler.fetch_github_document_async(
                    owner="enterprise-org",
                    repo=repo_name,
                    doc_type="readme",
                    auth_token=github_config["config"]["auth_token"]
                )

        # Test concurrent fetching performance
        start_time = time.time()

        tasks = [
            fetch_single_repo(repo)
            for repo in github_config["config"]["repositories"][:3]  # First 3 repos
        ]

        results = asyncio.run(asyncio.gather(*tasks))

        end_time = time.time()
        concurrent_time = end_time - start_time

        assert len(results) == 3
        assert all(r["success"] for r in results)
        assert concurrent_time < 5.0  # Should complete within 5 seconds

        # Test batch database queries
        db_config = enterprise_data_sources["database_system"]

        batch_start_time = time.time()

        with patch("main.FetchHandler._execute_db_query") as mock_query:
            mock_query.return_value = db_config["sample_data"]["orders"]

            batch_results = fetch_handler.batch_fetch_database_tables(
                connection_string=db_config["config"]["connection_string"],
                tables=db_config["config"]["tables"][:2],  # First 2 tables
                max_workers=2
            )

            batch_end_time = time.time()
            batch_time = batch_end_time - batch_start_time

            assert len(batch_results) == 2
            assert batch_time < 3.0  # Should complete within 3 seconds

    @pytest.mark.parametrize("source_type,config_key", [
        ("github", "github_enterprise"),
        ("confluence", "confluence_wiki"),
        ("database", "database_system"),
        ("rest_api", "rest_api_endpoints"),
        ("filesystem", "file_system_share"),
    ])
    def test_connector_initialization_and_validation(self, fetch_handler, enterprise_data_sources, source_type, config_key):
        """Test connector initialization and configuration validation."""
        config = enterprise_data_sources[config_key]["config"]

        # Test connector initialization
        connector = fetch_handler.initialize_connector(source_type, config)

        assert connector is not None
        assert connector["type"] == source_type
        assert "config" in connector
        assert connector["initialized"] is True

        # Test configuration validation
        validation_result = fetch_handler.validate_connector_config(source_type, config)

        assert validation_result["valid"] is True
        assert "required_fields_present" in validation_result
        assert validation_result["required_fields_present"] is True

        # Test missing required fields
        invalid_config = config.copy()
        if source_type == "github":
            del invalid_config["base_url"]
        elif source_type == "database":
            del invalid_config["connection_string"]

        invalid_validation = fetch_handler.validate_connector_config(source_type, invalid_config)

        assert invalid_validation["valid"] is False
        assert "missing_fields" in invalid_validation

    def test_cross_source_data_correlation(self, intelligent_ingestion, enterprise_data_sources):
        """Test cross-source data correlation and relationship discovery."""
        # Simulate data from multiple sources
        correlation_data = {
            "github_repos": [
                {"name": "api-gateway", "language": "Python", "topics": ["api", "gateway", "microservice"]},
                {"name": "user-service", "language": "Java", "topics": ["user", "authentication", "microservice"]}
            ],
            "confluence_pages": [
                {"title": "API Gateway Documentation", "content": "API Gateway service documentation"},
                {"title": "User Service API", "content": "User management service API specs"}
            ],
            "database_tables": [
                {"name": "users", "columns": ["id", "email", "name"]},
                {"name": "orders", "columns": ["id", "user_id", "amount"]}
            ]
        }

        # Test relationship discovery
        relationships = intelligent_ingestion.discover_relationships(correlation_data)

        assert "entity_relationships" in relationships
        assert "data_flows" in relationships
        assert len(relationships["entity_relationships"]) >= 2

        # Verify discovered relationships
        user_relationships = [r for r in relationships["entity_relationships"]
                            if "user" in r["from"].lower() and "user" in r["to"].lower()]

        assert len(user_relationships) >= 1  # Should find user-related relationships

        # Test data lineage tracking
        lineage_result = intelligent_ingestion.track_data_lineage(
            source_entity="users",
            target_entity="orders",
            correlation_data=correlation_data
        )

        assert lineage_result["lineage_found"] is True
        assert "path" in lineage_result
        assert len(lineage_result["path"]) >= 2
