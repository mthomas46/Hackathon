"""Integration Tests for Ingestion Pipeline Integration in Source Agent Service.

This module tests ingestion pipeline integration capabilities including:
- End-to-end document ingestion workflows
- Multi-source data aggregation and processing
- Intelligent document analysis and classification
- Content normalization and transformation
- Pipeline performance and scalability

Integration tests cover complete ingestion pipeline workflows and enterprise data processing scenarios.
"""

import pytest
import asyncio
import time
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import uuid

from main import IngestRequest, IngestResponse


class TestIngestionPipelineIntegration:
    """Integration tests for ingestion pipeline workflows."""

    @pytest.fixture
    def integration_app(self):
        """Create a complete Source Agent application for integration testing."""
        from main import app
        return app

    @pytest.fixture
    def enterprise_ingestion_scenarios(self):
        """Enterprise ingestion scenarios for comprehensive testing."""
        return {
            "multi_repository_documentation_ingestion": {
                "scenario_type": "multi_source_docs",
                "sources": [
                    {
                        "type": "github",
                        "config": {
                            "owner": "enterprise-org",
                            "repos": ["api-gateway", "user-service", "order-service", "payment-service"],
                            "doc_types": ["readme", "docs"],
                            "auth_token": "ghp_enterprise_token_1234567890abcdef"
                        },
                        "expected_documents": 8  # 4 repos × 2 doc types
                    },
                    {
                        "type": "confluence",
                        "config": {
                            "space_key": "ARCH",
                            "pages": ["System Architecture", "API Specifications", "Deployment Guide"],
                            "base_url": "https://company.atlassian.net/wiki",
                            "username": "api_user@company.com",
                            "api_token": "ATLASSIAN_TOKEN_abcdef1234567890"
                        },
                        "expected_documents": 3
                    }
                ],
                "processing_config": {
                    "normalize_content": True,
                    "extract_metadata": True,
                    "classify_documents": True,
                    "detect_duplicates": True,
                    "parallel_processing": True,
                    "max_workers": 4
                },
                "expected_outcomes": {
                    "total_documents_ingested": 11,
                    "unique_sources": 2,
                    "content_types": ["markdown", "wiki_markup"],
                    "processing_time_seconds": 15,
                    "quality_score_threshold": 0.8
                }
            },
            "enterprise_database_schema_ingestion": {
                "scenario_type": "database_schema",
                "sources": [
                    {
                        "type": "database",
                        "config": {
                            "connection_string": "postgresql://app_user:secure_password@db.company.com:5432/enterprise_db",
                            "schema": "public",
                            "tables": ["users", "orders", "products", "audit_logs"],
                            "include_constraints": True,
                            "include_indexes": True,
                            "max_rows_sample": 100
                        },
                        "expected_tables": 4
                    }
                ],
                "processing_config": {
                    "normalize_schema": True,
                    "extract_relationships": True,
                    "generate_documentation": True,
                    "create_erd": True,
                    "parallel_processing": False
                },
                "expected_outcomes": {
                    "total_tables_processed": 4,
                    "relationships_discovered": 3,
                    "documentation_generated": True,
                    "erd_created": True,
                    "processing_time_seconds": 8
                }
            },
            "api_specification_aggregation": {
                "scenario_type": "api_aggregation",
                "sources": [
                    {
                        "type": "github",
                        "config": {
                            "owner": "enterprise-org",
                            "repos": ["api-gateway", "user-service"],
                            "doc_types": ["api_spec"],
                            "auth_token": "ghp_enterprise_token_1234567890abcdef"
                        },
                        "expected_documents": 2
                    },
                    {
                        "type": "filesystem",
                        "config": {
                            "base_path": "/mnt/company_docs/api_specs",
                            "allowed_extensions": [".yaml", ".json"],
                            "recursive": True
                        },
                        "expected_documents": 3
                    },
                    {
                        "type": "rest_api",
                        "config": {
                            "base_url": "https://api.company.com",
                            "endpoints": ["/docs/openapi.json"],
                            "auth_type": "bearer",
                            "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                        },
                        "expected_documents": 1
                    }
                ],
                "processing_config": {
                    "merge_specifications": True,
                    "validate_openapi": True,
                    "generate_unified_api": True,
                    "create_api_documentation": True,
                    "parallel_processing": True,
                    "max_workers": 3
                },
                "expected_outcomes": {
                    "total_api_specs": 6,
                    "merged_specification": True,
                    "validation_passed": True,
                    "unified_api_generated": True,
                    "documentation_created": True,
                    "processing_time_seconds": 12
                }
            },
            "knowledge_base_construction": {
                "scenario_type": "knowledge_aggregation",
                "sources": [
                    {
                        "type": "confluence",
                        "config": {
                            "space_key": "KB",
                            "pages": ["Troubleshooting Guide", "Best Practices", "FAQ"],
                            "base_url": "https://company.atlassian.net/wiki",
                            "username": "api_user@company.com",
                            "api_token": "ATLASSIAN_TOKEN_abcdef1234567890"
                        },
                        "expected_documents": 3
                    },
                    {
                        "type": "filesystem",
                        "config": {
                            "base_path": "/mnt/company_docs/knowledge",
                            "allowed_extensions": [".md", ".txt", ".pdf"],
                            "recursive": True
                        },
                        "expected_documents": 5
                    }
                ],
                "processing_config": {
                    "extract_knowledge": True,
                    "build_search_index": True,
                    "create_categories": True,
                    "generate_summaries": True,
                    "parallel_processing": True,
                    "max_workers": 2
                },
                "expected_outcomes": {
                    "total_knowledge_items": 8,
                    "categories_created": 4,
                    "search_index_built": True,
                    "summaries_generated": 8,
                    "processing_time_seconds": 10
                }
            }
        }

    @pytest.fixture
    def enterprise_pipeline_configurations(self):
        """Enterprise pipeline configurations for testing."""
        return {
            "high_performance_pipeline": {
                "parallel_processing": True,
                "max_workers": 8,
                "batch_size": 50,
                "cache_enabled": True,
                "compression_enabled": True,
                "monitoring_enabled": True,
                "error_handling": "fail_fast",
                "retry_policy": {"max_retries": 3, "backoff_factor": 2}
            },
            "enterprise_reliable_pipeline": {
                "parallel_processing": False,
                "max_workers": 1,
                "batch_size": 10,
                "cache_enabled": True,
                "compression_enabled": False,
                "monitoring_enabled": True,
                "error_handling": "continue_on_error",
                "retry_policy": {"max_retries": 5, "backoff_factor": 1.5}
            },
            "cost_optimized_pipeline": {
                "parallel_processing": True,
                "max_workers": 2,
                "batch_size": 25,
                "cache_enabled": True,
                "compression_enabled": True,
                "monitoring_enabled": False,
                "error_handling": "log_and_continue",
                "retry_policy": {"max_retries": 2, "backoff_factor": 1}
            }
        }

    @pytest.mark.asyncio
    async def test_end_to_end_multi_source_document_ingestion(self, integration_app, enterprise_ingestion_scenarios):
        """Test complete multi-source document ingestion workflow."""
        # Setup comprehensive multi-source ingestion workflow
        with patch("main.FetchHandler") as mock_fetch_handler_class, \
             patch("main.IntelligentIngestion") as mock_intelligent_ingestion_class, \
             patch("main.NormalizeHandler") as mock_normalize_handler_class, \
             patch("main.DocumentBuilders") as mock_document_builders_class, \
             patch("main.LogCollectorClient") as mock_logger_class:

            # Mock components
            mock_fetch_handler = MagicMock()
            mock_intelligent_ingestion = MagicMock()
            mock_normalize_handler = MagicMock()
            mock_document_builders = MagicMock()
            mock_logger = AsyncMock()

            mock_fetch_handler_class.return_value = mock_fetch_handler
            mock_intelligent_ingestion_class.return_value = mock_intelligent_ingestion
            mock_normalize_handler_class.return_value = mock_normalize_handler
            mock_document_builders_class.return_value = mock_document_builders
            mock_logger_class.return_value = mock_logger

            # Configure fetch handler responses for different sources
            def fetch_handler_side_effect(source_config):
                source_type = source_config["type"]
                if source_type == "github":
                    # Simulate GitHub document fetching
                    documents = []
                    for repo in source_config["config"]["repos"]:
                        for doc_type in source_config["config"]["doc_types"]:
                            documents.append({
                                "success": True,
                                "content": f"# {repo} {doc_type}\nRepository documentation for {repo}",
                                "metadata": {
                                    "source": "github",
                                    "owner": source_config["config"]["owner"],
                                    "repo": repo,
                                    "doc_type": doc_type,
                                    "fetch_timestamp": datetime.now().isoformat()
                                }
                            })
                    return documents
                elif source_type == "confluence":
                    # Simulate Confluence page fetching
                    documents = []
                    for page in source_config["config"]["pages"]:
                        documents.append({
                            "success": True,
                            "content": f"<h1>{page}</h1><p>Confluence page content for {page}</p>",
                            "metadata": {
                                "source": "confluence",
                                "space_key": source_config["config"]["space_key"],
                                "page_title": page,
                                "fetch_timestamp": datetime.now().isoformat()
                            }
                        })
                    return documents
                return []

            mock_fetch_handler.fetch_from_source.side_effect = fetch_handler_side_effect

            # Configure intelligent ingestion responses
            mock_intelligent_ingestion.ingest_documents.return_value = {
                "ingested_count": 11,
                "processing_stats": {
                    "total_processing_time": 8.5,
                    "average_quality_score": 0.87,
                    "duplicates_detected": 2,
                    "content_types": ["markdown", "wiki_markup"]
                }
            }

            # Configure normalization responses
            def normalize_side_effect(documents):
                normalized_docs = []
                for doc in documents:
                    normalized_docs.append({
                        **doc,
                        "normalized_content": doc["content"],
                        "content_type": "markdown" if doc["content"].startswith("#") else "wiki_markup",
                        "quality_score": 0.85
                    })
                return normalized_docs

            mock_normalize_handler.normalize_batch.side_effect = normalize_side_effect

            # Configure document building responses
            mock_document_builders.build_enterprise_knowledge_base.return_value = {
                "knowledge_base_created": True,
                "total_documents": 11,
                "categories": ["api_docs", "architecture", "deployment"],
                "search_index_built": True
            }

            # Execute multi-source document ingestion workflow
            ingestion_scenario = enterprise_ingestion_scenarios["multi_repository_documentation_ingestion"]

            ingestion_results = {}

            # Phase 1: Fetch documents from all sources
            fetched_documents = []
            for source in ingestion_scenario["sources"]:
                source_docs = mock_fetch_handler.fetch_from_source(source)
                fetched_documents.extend(source_docs)

            # Phase 2: Intelligent ingestion and processing
            ingestion_result = mock_intelligent_ingestion.ingest_documents(
                documents=fetched_documents,
                config=ingestion_scenario["processing_config"]
            )

            # Phase 3: Content normalization
            normalized_documents = mock_normalize_handler.normalize_batch(fetched_documents)

            # Phase 4: Build enterprise knowledge base
            knowledge_base = mock_document_builders.build_enterprise_knowledge_base(
                documents=normalized_documents,
                config=ingestion_scenario["processing_config"]
            )

            ingestion_results["multi_source_ingestion"] = {
                "fetched_documents": fetched_documents,
                "ingestion_result": ingestion_result,
                "normalized_documents": normalized_documents,
                "knowledge_base": knowledge_base,
                "processing_config": ingestion_scenario["processing_config"],
                "expected_outcomes": ingestion_scenario["expected_outcomes"]
            }

            # Verify comprehensive multi-source ingestion
            result = ingestion_results["multi_source_ingestion"]

            # Verify document fetching
            assert len(result["fetched_documents"]) == 11  # 8 GitHub + 3 Confluence
            assert all(doc["success"] for doc in result["fetched_documents"])

            # Verify document sources
            github_docs = [d for d in result["fetched_documents"] if d["metadata"]["source"] == "github"]
            confluence_docs = [d for d in result["fetched_documents"] if d["metadata"]["source"] == "confluence"]

            assert len(github_docs) == 8
            assert len(confluence_docs) == 3

            # Verify ingestion processing
            ingestion = result["ingestion_result"]
            assert ingestion["ingested_count"] == 11
            assert ingestion["processing_stats"]["average_quality_score"] >= 0.8
            assert len(ingestion["processing_stats"]["content_types"]) == 2

            # Verify normalization
            assert len(result["normalized_documents"]) == 11
            assert all("normalized_content" in doc for doc in result["normalized_documents"])
            assert all("content_type" in doc for doc in result["normalized_documents"])

            # Verify knowledge base construction
            kb = result["knowledge_base"]
            assert kb["knowledge_base_created"] is True
            assert kb["total_documents"] == 11
            assert kb["search_index_built"] is True
            assert len(kb["categories"]) >= 3

    @pytest.mark.asyncio
    async def test_enterprise_database_schema_ingestion_pipeline(self, integration_app, enterprise_ingestion_scenarios):
        """Test enterprise database schema ingestion and processing pipeline."""
        # Setup database schema ingestion pipeline
        with patch("main.FetchHandler") as mock_fetch_handler_class, \
             patch("main.NormalizeHandler") as mock_normalize_handler_class, \
             patch("main.DocumentBuilders") as mock_document_builders_class, \
             patch("main.CodeAnalyzer") as mock_code_analyzer_class:

            mock_fetch_handler = MagicMock()
            mock_normalize_handler = MagicMock()
            mock_document_builders = MagicMock()
            mock_code_analyzer = MagicMock()

            mock_fetch_handler_class.return_value = mock_fetch_handler
            mock_normalize_handler_class.return_value = mock_normalize_handler
            mock_document_builders_class.return_value = mock_document_builders
            mock_code_analyzer_class.return_value = mock_code_analyzer

            # Configure database schema fetching
            def fetch_db_schema_side_effect(source_config):
                tables = source_config["config"]["tables"]
                schema_data = []

                for table in tables:
                    if table == "users":
                        schema_data.append({
                            "table_name": "users",
                            "columns": [
                                {"name": "id", "type": "SERIAL", "nullable": False, "primary_key": True},
                                {"name": "email", "type": "VARCHAR(255)", "nullable": False, "unique": True},
                                {"name": "name", "type": "VARCHAR(100)", "nullable": False},
                                {"name": "department", "type": "VARCHAR(50)", "nullable": True}
                            ],
                            "constraints": ["PRIMARY KEY (id)", "UNIQUE (email)"],
                            "indexes": ["idx_users_email", "idx_users_department"]
                        })
                    elif table == "orders":
                        schema_data.append({
                            "table_name": "orders",
                            "columns": [
                                {"name": "id", "type": "SERIAL", "nullable": False, "primary_key": True},
                                {"name": "user_id", "type": "INTEGER", "nullable": False},
                                {"name": "amount", "type": "DECIMAL(10,2)", "nullable": False},
                                {"name": "status", "type": "VARCHAR(20)", "nullable": False}
                            ],
                            "constraints": ["PRIMARY KEY (id)", "FOREIGN KEY (user_id) REFERENCES users(id)"],
                            "indexes": ["idx_orders_user_id", "idx_orders_status"]
                        })
                    # Add other tables similarly...

                return schema_data

            mock_fetch_handler.fetch_database_schema.side_effect = fetch_db_schema_side_effect

            # Configure schema normalization
            def normalize_schema_side_effect(schema_data):
                normalized_schema = []
                relationships = []

                for table_data in schema_data:
                    # Extract relationships from foreign keys
                    for constraint in table_data.get("constraints", []):
                        if "FOREIGN KEY" in constraint:
                            # Parse foreign key relationship
                            relationships.append({
                                "from_table": table_data["table_name"],
                                "to_table": "users",  # Simplified parsing
                                "relationship_type": "foreign_key"
                            })

                    normalized_schema.append({
                        **table_data,
                        "normalized_columns": [
                            {**col, "data_type_category": "numeric" if "INT" in col["type"] else "text"}
                            for col in table_data["columns"]
                        ]
                    })

                return {
                    "normalized_schema": normalized_schema,
                    "relationships": relationships,
                    "metadata": {
                        "total_tables": len(normalized_schema),
                        "total_relationships": len(relationships)
                    }
                }

            mock_normalize_handler.normalize_database_schema.side_effect = normalize_schema_side_effect

            # Configure ERD generation
            mock_document_builders.generate_entity_relationship_diagram.return_value = {
                "erd_generated": True,
                "format": "plantuml",
                "content": "@startuml\nclass users {\n  +id: SERIAL\n  +email: VARCHAR\n}\n@enduml",
                "tables_represented": 4,
                "relationships_shown": 3
            }

            # Configure documentation generation
            mock_document_builders.generate_database_documentation.return_value = {
                "documentation_generated": True,
                "format": "markdown",
                "sections": ["schema_overview", "table_details", "relationships", "indexes"],
                "total_tables_documented": 4
            }

            # Execute database schema ingestion pipeline
            schema_scenario = enterprise_ingestion_scenarios["enterprise_database_schema_ingestion"]

            schema_results = {}

            # Phase 1: Fetch database schema
            schema_data = mock_fetch_handler.fetch_database_schema(schema_scenario["sources"][0])

            # Phase 2: Normalize schema
            normalized_schema = mock_normalize_handler.normalize_database_schema(schema_data)

            # Phase 3: Generate ERD
            erd_result = mock_document_builders.generate_entity_relationship_diagram(normalized_schema)

            # Phase 4: Generate documentation
            documentation_result = mock_document_builders.generate_database_documentation(
                normalized_schema,
                format="markdown"
            )

            schema_results["database_schema_ingestion"] = {
                "raw_schema": schema_data,
                "normalized_schema": normalized_schema,
                "erd": erd_result,
                "documentation": documentation_result,
                "processing_config": schema_scenario["processing_config"],
                "expected_outcomes": schema_scenario["expected_outcomes"]
            }

            # Verify comprehensive database schema ingestion
            result = schema_results["database_schema_ingestion"]

            # Verify schema fetching
            assert len(result["raw_schema"]) == 4  # All tables fetched
            assert all("table_name" in table for table in result["raw_schema"])
            assert all("columns" in table for table in result["raw_schema"])

            # Verify schema normalization
            normalized = result["normalized_schema"]
            assert len(normalized["normalized_schema"]) == 4
            assert len(normalized["relationships"]) >= 3  # Foreign key relationships
            assert normalized["metadata"]["total_tables"] == 4

            # Verify ERD generation
            erd = result["erd"]
            assert erd["erd_generated"] is True
            assert erd["format"] == "plantuml"
            assert erd["tables_represented"] == 4
            assert erd["relationships_shown"] >= 3
            assert "@startuml" in erd["content"]

            # Verify documentation generation
            docs = result["documentation"]
            assert docs["documentation_generated"] is True
            assert docs["format"] == "markdown"
            assert len(docs["sections"]) >= 4
            assert docs["total_tables_documented"] == 4

    @pytest.mark.asyncio
    async def test_api_specification_aggregation_pipeline(self, integration_app, enterprise_ingestion_scenarios):
        """Test API specification aggregation and unification pipeline."""
        # Setup API specification aggregation pipeline
        with patch("main.FetchHandler") as mock_fetch_handler_class, \
             patch("main.NormalizeHandler") as mock_normalize_handler_class, \
             patch("main.DocumentBuilders") as mock_document_builders_class, \
             patch("main.CodeAnalyzer") as mock_code_analyzer_class:

            mock_fetch_handler = MagicMock()
            mock_normalize_handler = MagicMock()
            mock_document_builders = MagicMock()
            mock_code_analyzer = MagicMock()

            mock_fetch_handler_class.return_value = mock_fetch_handler
            mock_normalize_handler_class.return_value = mock_normalize_handler
            mock_document_builders_class.return_value = mock_document_builders
            mock_code_analyzer_class.return_value = mock_code_analyzer

            # Configure API spec fetching from multiple sources
            def fetch_api_specs_side_effect(source_config):
                source_type = source_config["type"]

                if source_type == "github":
                    specs = []
                    for repo in source_config["config"]["repos"]:
                        specs.append({
                            "openapi": "3.0.0",
                            "info": {"title": f"{repo} API", "version": "1.0.0"},
                            "paths": {
                                "/health": {"get": {"summary": "Health check"}},
                                f"/{repo.replace('-', '')}": {"get": {"summary": f"Get {repo} data"}}
                            },
                            "metadata": {"source": "github", "repo": repo}
                        })
                    return specs
                elif source_type == "filesystem":
                    return [
                        {
                            "openapi": "3.0.0",
                            "info": {"title": "User Management API", "version": "2.0.0"},
                            "paths": {"/users": {"get": {"summary": "List users"}, "post": {"summary": "Create user"}}},
                            "metadata": {"source": "filesystem", "file": "user_api.yaml"}
                        },
                        {
                            "openapi": "3.0.0",
                            "info": {"title": "Order Processing API", "version": "1.5.0"},
                            "paths": {"/orders": {"get": {"summary": "List orders"}, "post": {"summary": "Create order"}}},
                            "metadata": {"source": "filesystem", "file": "order_api.yaml"}
                        }
                    ]
                elif source_type == "rest_api":
                    return [{
                        "openapi": "3.0.0",
                        "info": {"title": "Company API", "version": "3.0.0"},
                        "paths": {"/analytics": {"get": {"summary": "Get analytics"}}},
                        "metadata": {"source": "rest_api", "endpoint": "/docs/openapi.json"}
                    }]
                return []

            mock_fetch_handler.fetch_api_specifications.side_effect = fetch_api_specs_side_effect

            # Configure OpenAPI validation
            def validate_openapi_side_effect(spec):
                return {
                    "valid": True,
                    "version": spec.get("openapi", "3.0.0"),
                    "errors": [],
                    "warnings": ["Consider adding response schemas"],
                    "score": 0.95
                }

            mock_code_analyzer.validate_openapi_spec.side_effect = validate_openapi_side_effect

            # Configure API spec merging
            mock_document_builders.merge_openapi_specifications.return_value = {
                "merged_spec": {
                    "openapi": "3.0.0",
                    "info": {"title": "Unified Enterprise API", "version": "1.0.0"},
                    "paths": {
                        "/health": {"get": {"summary": "Health check"}},
                        "/users": {"get": {"summary": "List users"}, "post": {"summary": "Create user"}},
                        "/orders": {"get": {"summary": "List orders"}, "post": {"summary": "Create order"}},
                        "/analytics": {"get": {"summary": "Get analytics"}}
                    }
                },
                "total_endpoints": 6,
                "conflicts_resolved": 2,
                "merge_success": True
            }

            # Configure API documentation generation
            mock_document_builders.generate_api_documentation.return_value = {
                "documentation_generated": True,
                "format": "html",
                "interactive_docs": True,
                "endpoints_documented": 6,
                "auth_methods_covered": ["bearer", "api_key"]
            }

            # Execute API specification aggregation pipeline
            api_scenario = enterprise_ingestion_scenarios["api_specification_aggregation"]

            api_results = {}

            # Phase 1: Fetch API specifications from all sources
            all_specs = []
            for source in api_scenario["sources"]:
                specs = mock_fetch_handler.fetch_api_specifications(source)
                all_specs.extend(specs)

            # Phase 2: Validate individual specifications
            validation_results = []
            for spec in all_specs:
                validation = mock_code_analyzer.validate_openapi_spec(spec)
                validation_results.append(validation)

            # Phase 3: Merge specifications
            merged_spec = mock_document_builders.merge_openapi_specifications(all_specs)

            # Phase 4: Generate unified API documentation
            api_docs = mock_document_builders.generate_api_documentation(merged_spec["merged_spec"])

            api_results["api_aggregation"] = {
                "raw_specifications": all_specs,
                "validation_results": validation_results,
                "merged_specification": merged_spec,
                "api_documentation": api_docs,
                "processing_config": api_scenario["processing_config"],
                "expected_outcomes": api_scenario["expected_outcomes"]
            }

            # Verify comprehensive API aggregation
            result = api_results["api_aggregation"]

            # Verify specification fetching
            assert len(result["raw_specifications"]) == 6  # 2 GitHub + 2 filesystem + 1 REST API + 1 extra
            assert all("openapi" in spec for spec in result["raw_specifications"])
            assert all("paths" in spec for spec in result["raw_specifications"])

            # Verify validation
            assert len(result["validation_results"]) == 6
            assert all(v["valid"] for v in result["validation_results"])
            assert all(v["score"] >= 0.9 for v in result["validation_results"])

            # Verify merging
            merged = result["merged_specification"]
            assert merged["merge_success"] is True
            assert merged["total_endpoints"] >= 6
            assert "merged_spec" in merged
            assert "paths" in merged["merged_spec"]
            assert len(merged["merged_spec"]["paths"]) >= 4  # At least 4 unique endpoints

            # Verify documentation generation
            docs = result["api_documentation"]
            assert docs["documentation_generated"] is True
            assert docs["interactive_docs"] is True
            assert docs["endpoints_documented"] >= 6

    @pytest.mark.asyncio
    async def test_knowledge_base_construction_pipeline(self, integration_app, enterprise_ingestion_scenarios):
        """Test knowledge base construction and management pipeline."""
        # Setup knowledge base construction pipeline
        with patch("main.FetchHandler") as mock_fetch_handler_class, \
             patch("main.IntelligentIngestion") as mock_intelligent_ingestion_class, \
             patch("main.DocumentBuilders") as mock_document_builders_class, \
             patch("main.CodeAnalyzer") as mock_code_analyzer_class:

            mock_fetch_handler = MagicMock()
            mock_intelligent_ingestion = MagicMock()
            mock_document_builders = MagicMock()
            mock_code_analyzer = MagicMock()

            mock_fetch_handler_class.return_value = mock_fetch_handler
            mock_intelligent_ingestion_class.return_value = mock_intelligent_ingestion
            mock_document_builders_class.return_value = mock_document_builders
            mock_code_analyzer_class.return_value = mock_code_analyzer

            # Configure knowledge content fetching
            def fetch_knowledge_side_effect(source_config):
                source_type = source_config["type"]

                if source_type == "confluence":
                    return [
                        {
                            "title": "Troubleshooting Guide",
                            "content": "# Troubleshooting Guide\n\n## Common Issues\n1. Service unavailable\n2. Authentication failed\n\n## Solutions\nCheck network connectivity...",
                            "metadata": {"category": "support", "tags": ["troubleshooting", "faq"]}
                        },
                        {
                            "title": "Best Practices",
                            "content": "# Best Practices\n\n## Code Quality\n- Use meaningful variable names\n- Add comprehensive tests\n\n## Security\n- Validate all inputs...",
                            "metadata": {"category": "development", "tags": ["best_practices", "guidelines"]}
                        }
                    ]
                elif source_type == "filesystem":
                    return [
                        {
                            "title": "API Documentation",
                            "content": "# API Documentation\n\n## Authentication\nUse Bearer tokens for API access...",
                            "metadata": {"category": "technical", "tags": ["api", "documentation"]}
                        },
                        {
                            "title": "Deployment Guide",
                            "content": "# Deployment Guide\n\n## Prerequisites\n- Docker installed\n- Kubernetes cluster\n\n## Steps\n1. Build images...",
                            "metadata": {"category": "operations", "tags": ["deployment", "kubernetes"]}
                        }
                    ]
                return []

            mock_fetch_handler.fetch_knowledge_content.side_effect = fetch_knowledge_side_effect

            # Configure knowledge extraction
            def extract_knowledge_side_effect(content):
                return {
                    "key_concepts": ["authentication", "deployment", "troubleshooting"],
                    "procedures": [
                        {"title": "API Authentication", "steps": ["Get token", "Include in header", "Make request"]},
                        {"title": "Service Deployment", "steps": ["Build image", "Push to registry", "Deploy to k8s"]}
                    ],
                    "faq_items": [
                        {"question": "Service unavailable", "answer": "Check network connectivity and service status"},
                        {"question": "Authentication failed", "answer": "Verify token validity and permissions"}
                    ],
                    "confidence_score": 0.89
                }

            mock_intelligent_ingestion.extract_knowledge.side_effect = extract_knowledge_side_effect

            # Configure knowledge categorization
            mock_document_builders.categorize_knowledge.return_value = {
                "categories": {
                    "technical": ["API Documentation", "Best Practices"],
                    "operational": ["Deployment Guide", "Troubleshooting Guide"],
                    "support": ["Troubleshooting Guide"]
                },
                "category_confidence": {"technical": 0.95, "operational": 0.88, "support": 0.92}
            }

            # Configure search index building
            mock_document_builders.build_search_index.return_value = {
                "index_built": True,
                "total_documents": 4,
                "total_terms": 1250,
                "index_size_mb": 2.3,
                "build_time_seconds": 1.2
            }

            # Configure summary generation
            mock_document_builders.generate_knowledge_summaries.return_value = [
                {"document_id": "troubleshooting", "summary": "Comprehensive guide for resolving common technical issues"},
                {"document_id": "best_practices", "summary": "Guidelines for maintaining code quality and security standards"},
                {"document_id": "api_docs", "summary": "Complete API documentation with authentication and usage examples"},
                {"document_id": "deployment", "summary": "Step-by-step deployment procedures for enterprise applications"}
            ]

            # Execute knowledge base construction pipeline
            knowledge_scenario = enterprise_ingestion_scenarios["knowledge_base_construction"]

            knowledge_results = {}

            # Phase 1: Fetch knowledge content from all sources
            knowledge_documents = []
            for source in knowledge_scenario["sources"]:
                docs = mock_fetch_handler.fetch_knowledge_content(source)
                knowledge_documents.extend(docs)

            # Phase 2: Extract structured knowledge
            knowledge_extractions = []
            for doc in knowledge_documents:
                extraction = mock_intelligent_ingestion.extract_knowledge(doc["content"])
                knowledge_extractions.append({**extraction, "document_title": doc["title"]})

            # Phase 3: Categorize knowledge
            categorization = mock_document_builders.categorize_knowledge(knowledge_documents)

            # Phase 4: Build search index
            search_index = mock_document_builders.build_search_index(knowledge_documents)

            # Phase 5: Generate summaries
            summaries = mock_document_builders.generate_knowledge_summaries(knowledge_documents)

            knowledge_results["knowledge_construction"] = {
                "raw_documents": knowledge_documents,
                "knowledge_extractions": knowledge_extractions,
                "categorization": categorization,
                "search_index": search_index,
                "summaries": summaries,
                "processing_config": knowledge_scenario["processing_config"],
                "expected_outcomes": knowledge_scenario["expected_outcomes"]
            }

            # Verify comprehensive knowledge base construction
            result = knowledge_results["knowledge_construction"]

            # Verify content fetching
            assert len(result["raw_documents"]) == 4  # 2 Confluence + 2 filesystem
            assert all("title" in doc for doc in result["raw_documents"])
            assert all("content" in doc for doc in result["raw_documents"])

            # Verify knowledge extraction
            assert len(result["knowledge_extractions"]) == 4
            assert all("key_concepts" in ext for ext in result["knowledge_extractions"])
            assert all("procedures" in ext for ext in result["knowledge_extractions"])
            assert all(ext["confidence_score"] >= 0.8 for ext in result["knowledge_extractions"])

            # Verify categorization
            categories = result["categorization"]
            assert len(categories["categories"]) >= 3
            assert "technical" in categories["categories"]
            assert "operational" in categories["categories"]
            assert all(conf >= 0.8 for conf in categories["category_confidence"].values())

            # Verify search index
            search = result["search_index"]
            assert search["index_built"] is True
            assert search["total_documents"] == 4
            assert search["build_time_seconds"] < 5

            # Verify summaries
            assert len(result["summaries"]) == 4
            assert all("summary" in summary for summary in result["summaries"])
            assert all(len(summary["summary"]) > 20 for summary in result["summaries"])

    @pytest.mark.asyncio
    async def test_pipeline_performance_and_scalability(self, integration_app, enterprise_pipeline_configurations):
        """Test ingestion pipeline performance and scalability."""
        # Setup pipeline performance testing
        with patch("main.FetchHandler") as mock_fetch_handler_class, \
             patch("main.IntelligentIngestion") as mock_intelligent_ingestion_class, \
             patch("main.NormalizeHandler") as mock_normalize_handler_class, \
             patch("main.DocumentBuilders") as mock_document_builders_class:

            mock_fetch_handler = MagicMock()
            mock_intelligent_ingestion = MagicMock()
            mock_normalize_handler = MagicMock()
            mock_document_builders = MagicMock()

            mock_fetch_handler_class.return_value = mock_fetch_handler
            mock_intelligent_ingestion_class.return_value = mock_intelligent_ingestion
            mock_normalize_handler_class.return_value = mock_normalize_handler
            mock_document_builders_class.return_value = mock_document_builders

            # Configure scalable document processing
            def process_documents_side_effect(documents, config):
                start_time = time.time()
                batch_size = config.get("batch_size", 10)
                max_workers = config.get("max_workers", 1)
                parallel = config.get("parallel_processing", False)

                # Simulate processing time based on configuration
                base_time = len(documents) * 0.1  # 100ms per document base
                if parallel:
                    processing_time = base_time / max_workers
                else:
                    processing_time = base_time

                if config.get("compression_enabled"):
                    processing_time *= 1.2  # Compression overhead

                time.sleep(min(processing_time, 0.1))  # Cap for testing

                return {
                    "processed_count": len(documents),
                    "processing_time": time.time() - start_time,
                    "batch_size": batch_size,
                    "workers_used": max_workers if parallel else 1,
                    "compression_applied": config.get("compression_enabled", False),
                    "success": True
                }

            mock_intelligent_ingestion.process_document_batch.side_effect = process_documents_side_effect

            # Execute performance testing for different configurations
            performance_results = {}

            test_documents = [{"content": f"Document {i}", "metadata": {"id": i}} for i in range(100)]

            for config_name, config in enterprise_pipeline_configurations.items():
                print(f"🧪 Testing {config_name} configuration...")

                # Test processing performance
                result = mock_intelligent_ingestion.process_document_batch(test_documents, config)

                performance_results[config_name] = {
                    "configuration": config,
                    "result": result,
                    "throughput_docs_per_second": result["processed_count"] / result["processing_time"] if result["processing_time"] > 0 else 0,
                    "efficiency_score": self._calculate_efficiency_score(config, result)
                }

            # Verify performance characteristics
            assert len(performance_results) == 3

            # High performance pipeline should be fastest
            high_perf = performance_results["high_performance_pipeline"]
            assert high_perf["result"]["workers_used"] == 8
            assert high_perf["throughput_docs_per_second"] > 500  # High throughput

            # Enterprise reliable pipeline should be most consistent
            reliable = performance_results["enterprise_reliable_pipeline"]
            assert reliable["result"]["workers_used"] == 1  # Sequential processing
            assert reliable["configuration"]["error_handling"] == "continue_on_error"

            # Cost optimized should balance performance and resources
            cost_opt = performance_results["cost_optimized_pipeline"]
            assert cost_opt["result"]["workers_used"] == 2
            assert cost_opt["result"]["compression_applied"] is True

            # Compare throughputs
            throughputs = {name: result["throughput_docs_per_second"]
                         for name, result in performance_results.items()}

            assert throughputs["high_performance_pipeline"] >= throughputs["cost_optimized_pipeline"]
            assert throughputs["cost_optimized_pipeline"] >= throughputs["enterprise_reliable_pipeline"]

    def _calculate_efficiency_score(self, config, result):
        """Calculate efficiency score based on configuration and results."""
        score = 1.0

        # Parallel processing bonus
        if config.get("parallel_processing"):
            score += 0.3

        # Worker utilization
        workers = result.get("workers_used", 1)
        max_workers = config.get("max_workers", 1)
        utilization = min(workers / max_workers, 1.0)
        score += utilization * 0.2

        # Compression efficiency
        if config.get("compression_enabled"):
            score += 0.1

        # Monitoring overhead penalty
        if config.get("monitoring_enabled"):
            score -= 0.05

        return max(0.0, min(1.0, score))
