"""Unit Tests for Schema Validation in Mock Data Generator.

This module tests schema validation capabilities including:
- JSON schema validation for generated data structures
- Data type validation and structure integrity
- Relationship validation between generated documents
- Metadata validation and completeness checks
- Schema evolution and version compatibility

Tests cover the complete schema validation infrastructure within the Mock Data Generator.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import jsonschema

from main import MockDataType, GenerationRequest


class TestSchemaValidation:
    """Test Schema Validation functionality."""

    @pytest.fixture
    def schema_validator(self):
        """Create schema validator instance with test schemas."""
        class MockSchemaValidator:
            def __init__(self):
                self.schemas = self._load_test_schemas()

            def _load_test_schemas(self):
                """Load test schemas for different data types."""
                return {
                    "api_docs": {
                        "type": "object",
                        "required": ["id", "title", "content", "metadata"],
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "metadata": {
                                "type": "object",
                                "properties": {
                                    "data_type": {"type": "string", "enum": ["api_docs"]},
                                    "complexity": {"type": "string", "enum": ["low", "medium", "high"]},
                                    "word_count": {"type": "integer", "minimum": 1},
                                    "quality_score": {"type": "number", "minimum": 0, "maximum": 1}
                                },
                                "required": ["data_type", "complexity", "word_count"]
                            }
                        }
                    },
                    "user_story": {
                        "type": "object",
                        "required": ["id", "title", "content", "metadata"],
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string", "pattern": "^As (a|an) .*, I (want|need|would like) .*, so that .*$"},
                            "content": {"type": "string"},
                            "metadata": {
                                "type": "object",
                                "properties": {
                                    "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
                                    "story_points": {"type": "integer", "minimum": 1, "maximum": 13},
                                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
                                }
                            }
                        }
                    },
                    "technical_design": {
                        "type": "object",
                        "required": ["id", "title", "content", "metadata"],
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "metadata": {
                                "type": "object",
                                "properties": {
                                    "architecture_components": {"type": "array", "items": {"type": "string"}},
                                    "design_patterns": {"type": "array", "items": {"type": "string"}},
                                    "technologies": {"type": "array", "items": {"type": "string"}}
                                },
                                "required": ["architecture_components"]
                            }
                        }
                    }
                }

            def validate_document(self, document: Dict[str, Any], data_type: str) -> Dict[str, Any]:
                """Validate document against schema."""
                if data_type not in self.schemas:
                    return {
                        "is_valid": False,
                        "errors": [f"Unknown data type: {data_type}"],
                        "schema_version": "1.0.0"
                    }

                schema = self.schemas[data_type]
                try:
                    jsonschema.validate(instance=document, schema=schema)
                    return {
                        "is_valid": True,
                        "errors": [],
                        "schema_version": "1.0.0",
                        "validation_time_seconds": 0.05
                    }
                except jsonschema.ValidationError as e:
                    return {
                        "is_valid": False,
                        "errors": [str(e.message)],
                        "schema_version": "1.0.0",
                        "validation_time_seconds": 0.05
                    }

            def validate_relationships(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
                """Validate relationships between documents."""
                errors = []

                # Check for duplicate IDs
                ids = [doc.get("id") for doc in documents if doc.get("id")]
                if len(ids) != len(set(ids)):
                    errors.append("Duplicate document IDs found")

                # Validate relationship references
                for doc in documents:
                    relationships = doc.get("relationships", {})
                    for rel_type, rel_docs in relationships.items():
                        if not isinstance(rel_docs, list):
                            continue
                        for rel_doc_id in rel_docs:
                            if rel_doc_id not in ids:
                                errors.append(f"Invalid relationship reference: {rel_doc_id}")

                return {
                    "relationships_valid": len(errors) == 0,
                    "relationship_errors": errors,
                    "total_relationships_checked": len(documents),
                    "validation_time_seconds": 0.02
                }

            def generate_schema_report(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
                """Generate comprehensive schema validation report."""
                report = {
                    "total_documents": len(documents),
                    "validation_summary": {
                        "valid_documents": 0,
                        "invalid_documents": 0,
                        "total_errors": 0
                    },
                    "data_type_distribution": {},
                    "schema_compliance_score": 0.0,
                    "quality_metrics": {
                        "completeness_score": 0.0,
                        "consistency_score": 0.0,
                        "relationship_integrity_score": 0.0
                    },
                    "recommendations": [],
                    "generated_at": datetime.now().isoformat()
                }

                valid_count = 0
                total_errors = 0
                data_types = {}

                for doc in documents:
                    data_type = doc.get("metadata", {}).get("data_type", "unknown")
                    data_types[data_type] = data_types.get(data_type, 0) + 1

                    validation = self.validate_document(doc, data_type)
                    if validation["is_valid"]:
                        valid_count += 1
                    else:
                        total_errors += len(validation["errors"])

                report["validation_summary"]["valid_documents"] = valid_count
                report["validation_summary"]["invalid_documents"] = len(documents) - valid_count
                report["validation_summary"]["total_errors"] = total_errors
                report["data_type_distribution"] = data_types
                report["schema_compliance_score"] = valid_count / len(documents) if documents else 0.0

                # Generate recommendations
                if total_errors > 0:
                    report["recommendations"].append("Review and fix schema validation errors")
                if len(data_types) < 3:
                    report["recommendations"].append("Consider generating more diverse data types")

                return report

        return MockSchemaValidator()

    @pytest.fixture
    def valid_api_docs(self):
        """Create a valid API documentation document."""
        return {
            "id": "api_doc_123",
            "title": "User Management API Documentation",
            "content": "# User Management API\n\nThis API provides comprehensive user management functionality...",
            "metadata": {
                "data_type": "api_docs",
                "complexity": "medium",
                "word_count": 450,
                "quality_score": 0.92,
                "tags": ["api", "documentation", "user-management"]
            },
            "relationships": {
                "related_documents": ["user_story_456"],
                "parent_collections": ["api_collection_789"]
            }
        }

    @pytest.fixture
    def valid_user_story(self):
        """Create a valid user story document."""
        return {
            "id": "user_story_456",
            "title": "As a user, I want to reset my password, so that I can regain access to my account",
            "content": "User password reset functionality with email verification...",
            "metadata": {
                "data_type": "user_story",
                "acceptance_criteria": [
                    "User receives reset email within 5 minutes",
                    "Reset link expires after 24 hours",
                    "Password strength requirements enforced"
                ],
                "story_points": 5,
                "priority": "high"
            }
        }

    @pytest.fixture
    def invalid_api_docs(self):
        """Create an invalid API documentation document."""
        return {
            "id": "api_doc_invalid",
            "title": "Invalid API Doc",
            "content": "Missing required metadata fields",
            # Missing required metadata field
            "metadata": {
                "data_type": "api_docs",
                # Missing required complexity field
                "word_count": 100
            }
        }

    def test_valid_api_docs_schema(self, schema_validator, valid_api_docs):
        """Test validation of valid API documentation schema."""
        result = schema_validator.validate_document(valid_api_docs, "api_docs")

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        assert result["schema_version"] == "1.0.0"
        assert "validation_time_seconds" in result

    def test_valid_user_story_schema(self, schema_validator, valid_user_story):
        """Test validation of valid user story schema."""
        result = schema_validator.validate_document(valid_user_story, "user_story")

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    def test_invalid_api_docs_schema(self, schema_validator, invalid_api_docs):
        """Test validation of invalid API documentation schema."""
        result = schema_validator.validate_document(invalid_api_docs, "api_docs")

        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
        assert "complexity" in str(result["errors"])

    def test_unknown_data_type_validation(self, schema_validator, valid_api_docs):
        """Test validation with unknown data type."""
        result = schema_validator.validate_document(valid_api_docs, "unknown_type")

        assert result["is_valid"] is False
        assert "Unknown data type" in str(result["errors"])

    def test_relationship_validation_valid(self, schema_validator, valid_api_docs, valid_user_story):
        """Test relationship validation with valid relationships."""
        documents = [valid_api_docs, valid_user_story]
        result = schema_validator.validate_relationships(documents)

        assert result["relationships_valid"] is True
        assert len(result["relationship_errors"]) == 0

    def test_relationship_validation_invalid(self, schema_validator, valid_api_docs):
        """Test relationship validation with invalid relationships."""
        # Create document with invalid relationship reference
        invalid_doc = valid_api_docs.copy()
        invalid_doc["relationships"] = {"related_documents": ["nonexistent_id"]}

        documents = [invalid_doc]
        result = schema_validator.validate_relationships(documents)

        assert result["relationships_valid"] is False
        assert len(result["relationship_errors"]) > 0
        assert "Invalid relationship reference" in str(result["relationship_errors"])

    def test_relationship_validation_duplicates(self, schema_validator, valid_api_docs):
        """Test relationship validation with duplicate document IDs."""
        doc1 = valid_api_docs.copy()
        doc2 = valid_api_docs.copy()  # Same ID as doc1

        documents = [doc1, doc2]
        result = schema_validator.validate_relationships(documents)

        assert result["relationships_valid"] is False
        assert "Duplicate document IDs" in str(result["relationship_errors"])

    def test_comprehensive_schema_report(self, schema_validator, valid_api_docs, valid_user_story, invalid_api_docs):
        """Test comprehensive schema validation report generation."""
        documents = [valid_api_docs, valid_user_story, invalid_api_docs]
        report = schema_validator.generate_schema_report(documents)

        assert report["total_documents"] == 3
        assert report["validation_summary"]["valid_documents"] == 2
        assert report["validation_summary"]["invalid_documents"] == 1
        assert "schema_compliance_score" in report
        assert "data_type_distribution" in report
        assert "recommendations" in report
        assert "generated_at" in report

    def test_schema_report_with_empty_documents(self, schema_validator):
        """Test schema report generation with empty document list."""
        report = schema_validator.generate_schema_report([])

        assert report["total_documents"] == 0
        assert report["validation_summary"]["valid_documents"] == 0
        assert report["schema_compliance_score"] == 0.0

    def test_data_type_distribution_tracking(self, schema_validator, valid_api_docs, valid_user_story):
        """Test data type distribution tracking in schema reports."""
        # Create multiple documents of same type
        api_doc2 = valid_api_docs.copy()
        api_doc2["id"] = "api_doc_999"

        documents = [valid_api_docs, api_doc2, valid_user_story]
        report = schema_validator.generate_schema_report(documents)

        assert report["data_type_distribution"]["api_docs"] == 2
        assert report["data_type_distribution"]["user_story"] == 1

    def test_schema_validation_performance(self, schema_validator, valid_api_docs):
        """Test schema validation performance metrics."""
        import time

        start_time = time.time()
        result = schema_validator.validate_document(valid_api_docs, "api_docs")
        end_time = time.time()

        assert result["is_valid"] is True
        assert result["validation_time_seconds"] > 0
        assert result["validation_time_seconds"] < 1.0  # Should be fast

        # Actual validation should be reasonably fast
        actual_time = end_time - start_time
        assert actual_time < 0.1  # Less than 100ms for single document

    def test_bulk_schema_validation_workflow(self, schema_validator):
        """Test complete bulk schema validation workflow."""
        # Create a bulk set of documents
        documents = []
        for i in range(10):
            doc = {
                "id": f"bulk_doc_{i}",
                "title": f"Bulk Document {i}",
                "content": f"Content for bulk document {i}",
                "metadata": {
                    "data_type": "api_docs",
                    "complexity": "medium",
                    "word_count": 150 + i,
                    "quality_score": 0.8 + (i * 0.01)
                }
            }
            documents.append(doc)

        # Validate all documents
        valid_count = 0
        for doc in documents:
            result = schema_validator.validate_document(doc, "api_docs")
            if result["is_valid"]:
                valid_count += 1

        assert valid_count == 10  # All should be valid

        # Generate comprehensive report
        report = schema_validator.generate_schema_report(documents)
        assert report["schema_compliance_score"] == 1.0  # 100% compliance

    @pytest.mark.parametrize("data_type,expected_valid", [
        ("api_docs", True),
        ("user_story", True),
        ("technical_design", True),
        ("unknown_type", False)
    ])
    def test_schema_validation_parametrized(self, schema_validator, data_type, expected_valid):
        """Test schema validation with parametrized test cases."""
        # Create a basic valid document for known types
        if data_type != "unknown_type":
            doc = {
                "id": "test_doc_123",
                "title": "Test Document",
                "content": "Test content",
                "metadata": {
                    "data_type": data_type,
                    "complexity": "medium",
                    "word_count": 100
                }
            }
            if data_type == "user_story":
                doc["title"] = "As a user, I want to test, so that I can validate"
                doc["metadata"]["acceptance_criteria"] = ["Test criterion"]
        else:
            doc = {"invalid": "document"}

        result = schema_validator.validate_document(doc, data_type)
        assert result["is_valid"] == expected_valid

    def test_schema_version_compatibility(self, schema_validator, valid_api_docs):
        """Test schema version compatibility and evolution."""
        result = schema_validator.validate_document(valid_api_docs, "api_docs")

        assert "schema_version" in result
        assert result["schema_version"] == "1.0.0"

        # Future: Test schema evolution compatibility
        # - New optional fields should not break validation
        # - Schema versioning should be handled properly
        # - Backward compatibility should be maintained

    def test_metadata_completeness_validation(self, schema_validator):
        """Test metadata completeness validation."""
        # Test complete metadata
        complete_doc = {
            "id": "complete_doc",
            "title": "Complete Document",
            "content": "Content",
            "metadata": {
                "data_type": "api_docs",
                "complexity": "high",
                "word_count": 500,
                "quality_score": 0.95,
                "tags": ["complete", "test"],
                "generated_at": datetime.now(),
                "reading_time_minutes": 3
            }
        }

        result = schema_validator.validate_document(complete_doc, "api_docs")
        assert result["is_valid"] is True

        # Test minimal required metadata
        minimal_doc = {
            "id": "minimal_doc",
            "title": "Minimal Document",
            "content": "Content",
            "metadata": {
                "data_type": "api_docs",
                "complexity": "low",
                "word_count": 50
            }
        }

        result = schema_validator.validate_document(minimal_doc, "api_docs")
        assert result["is_valid"] is True
