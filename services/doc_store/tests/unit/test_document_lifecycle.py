"""Unit Tests for Document Lifecycle Management in Document Store Service.

This module tests the complete document lifecycle including:
- Document creation and validation
- Content processing and metadata extraction
- Status management and workflow transitions
- Access control and permissions
- Document archival and deletion
- Lifecycle event handling and notifications

Tests cover the core document management capabilities within the DDD architecture.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from core.entities import Document
from core.models import DocumentContent, DocumentMetadata
from domain.documents.handlers import DocumentCommandHandler
from domain.documents.repository import DocumentRepository
from domain.documents.service import DocumentService
from domain.lifecycle.handlers import LifecycleEventHandler
from domain.lifecycle.service import LifecycleService


class TestDocumentCreation:
    """Test Document Creation functionality."""

    @pytest.fixture
    def document_handler(self, mock_repository, mock_event_bus):
        """Create document command handler instance."""
        return DocumentCommandHandler(mock_repository, mock_event_bus)

    def test_basic_document_creation(self, document_handler, sample_document):
        """Test basic document creation with minimal required fields."""
        create_command = {
            "title": "Test Document",
            "content": "This is a test document content.",
            "content_type": "text/plain",
            "author": "test@example.com"
        }

        result = document_handler.handle_create_document(create_command)

        assert result["success"] is True
        assert "document_id" in result
        assert result["document_id"] is not None

    def test_document_creation_with_full_metadata(self, document_handler):
        """Test document creation with comprehensive metadata."""
        create_command = {
            "title": "Comprehensive Test Document",
            "content": "# Test Document\n\nThis document has comprehensive metadata.",
            "content_type": "text/markdown",
            "author": "john.doe@company.com",
            "tags": ["test", "documentation", "comprehensive"],
            "custom_metadata": {
                "category": "testing",
                "priority": "high",
                "department": "engineering"
            },
            "access_control": {
                "owner": "john.doe@company.com",
                "readers": ["team@company.com"],
                "writers": ["john.doe@company.com"]
            }
        }

        result = document_handler.handle_create_document(create_command)

        assert result["success"] is True
        assert result["document"]["title"] == create_command["title"]
        assert result["document"]["metadata"]["author"] == create_command["author"]
        assert set(result["document"]["tags"]) == set(create_command["tags"])

    def test_document_creation_validation(self, document_handler):
        """Test document creation input validation."""
        invalid_commands = [
            # Missing title
            {"content": "Content without title", "content_type": "text/plain"},
            # Missing content
            {"title": "Title without content", "content_type": "text/plain"},
            # Invalid content type
            {"title": "Test", "content": "Content", "content_type": "invalid/type"},
            # Empty title
            {"title": "", "content": "Content", "content_type": "text/plain"},
            # Title too long
            {"title": "A" * 1000, "content": "Content", "content_type": "text/plain"}
        ]

        for invalid_command in invalid_commands:
            result = document_handler.handle_create_document(invalid_command)
            assert result["success"] is False
            assert "validation_errors" in result
            assert len(result["validation_errors"]) > 0

    def test_document_creation_with_file_upload(self, document_handler, mock_file_storage):
        """Test document creation with file upload."""
        file_content = b"This is binary file content for testing."
        file_metadata = {
            "filename": "test_document.pdf",
            "content_type": "application/pdf",
            "size_bytes": len(file_content)
        }

        create_command = {
            "title": "Uploaded Document",
            "file_content": file_content,
            "file_metadata": file_metadata,
            "author": "test@example.com",
            "extract_metadata": True,
            "generate_preview": True
        }

        result = document_handler.handle_create_document_with_file(create_command)

        assert result["success"] is True
        assert result["document"]["content_type"] == "application/pdf"
        assert "file_storage_path" in result["document"]
        assert "extracted_metadata" in result

    def test_document_creation_idempotency(self, document_handler):
        """Test idempotent document creation (preventing duplicates)."""
        create_command = {
            "title": "Unique Document",
            "content": "Unique content for testing",
            "content_type": "text/plain",
            "author": "test@example.com",
            "idempotency_key": "unique_key_123"
        }

        # First creation
        result1 = document_handler.handle_create_document(create_command)
        assert result1["success"] is True
        document_id = result1["document_id"]

        # Second creation with same idempotency key
        result2 = document_handler.handle_create_document(create_command)
        assert result2["success"] is True
        assert result2["document_id"] == document_id  # Same document returned

        # Verify only one document was actually created
        assert document_handler.repository.save_document.call_count == 1


class TestDocumentContentProcessing:
    """Test Document Content Processing functionality."""

    @pytest.fixture
    def content_processor(self, mock_ai_service, mock_file_storage):
        """Create content processor instance."""
        return DocumentService(ai_service=mock_ai_service, file_storage=mock_file_storage)

    def test_text_content_processing(self, content_processor, sample_document_content):
        """Test processing of text-based document content."""
        processing_result = content_processor.process_document_content(sample_document_content)

        assert processing_result["success"] is True
        assert "processed_content" in processing_result
        assert "extracted_metadata" in processing_result
        assert "quality_metrics" in processing_result

        # Verify content analysis
        processed = processing_result["processed_content"]
        assert "tokens" in processed
        assert processed["sentences"] > 0
        assert len(processed["headings"]) > 0

        # Verify metadata extraction
        metadata = processing_result["extracted_metadata"]
        assert "title" in metadata
        assert "keywords" in metadata
        assert len(metadata["keywords"]) > 0

    def test_multilingual_content_processing(self, content_processor):
        """Test processing of multilingual document content."""
        multilingual_content = DocumentContent(
            document_id=str(uuid.uuid4()),
            content="""# Intelligence Artificielle

## Introduction
L'Intelligence Artificielle désigne la simulation de l'intelligence humaine dans les machines.

## Apprentissage Automatique
L'apprentissage automatique est une sous-catégorie de l'IA permettant aux systèmes d'apprendre automatiquement.""",
            content_type="text/markdown",
            encoding="utf-8"
        )

        processing_result = content_processor.process_document_content(multilingual_content)

        assert processing_result["success"] is True
        assert processing_result["detected_language"] == "fr"
        assert "french_keywords" in processing_result["extracted_metadata"]
        assert processing_result["translation_available"] is True

    def test_binary_content_processing(self, content_processor):
        """Test processing of binary document content (PDF, DOCX, etc.)."""
        binary_content = DocumentContent(
            document_id=str(uuid.uuid4()),
            content=b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n...",
            content_type="application/pdf",
            encoding="binary"
        )

        processing_result = content_processor.process_document_content(binary_content)

        assert processing_result["success"] is True
        assert processing_result["content_type"] == "application/pdf"
        assert "text_extracted" in processing_result
        assert "page_count" in processing_result
        assert "file_size_bytes" in processing_result

    def test_content_quality_assessment(self, content_processor):
        """Test content quality assessment during processing."""
        test_contents = [
            {
                "content": "This is a very short document.",
                "expected_quality": "low",
                "issues": ["insufficient_length", "low_complexity"]
            },
            {
                "content": "This is a well-written document with proper structure, clear language, and comprehensive coverage of the topic. It includes multiple paragraphs, proper grammar, and meaningful content.",
                "expected_quality": "high",
                "issues": []
            },
            {
                "content": "This document has some good content but also contains several errors, unclear sections, and could be better organized. It needs improvement in clarity and structure.",
                "expected_quality": "medium",
                "issues": ["clarity_issues", "structure_problems"]
            }
        ]

        for test_case in test_contents:
            content = DocumentContent(
                document_id=str(uuid.uuid4()),
                content=test_case["content"],
                content_type="text/plain"
            )

            result = content_processor.process_document_content(content)

            assert result["quality_metrics"]["overall_quality"] == test_case["expected_quality"]
            for issue in test_case["issues"]:
                assert issue in result["quality_metrics"]["issues"]

    def test_content_security_scanning(self, content_processor):
        """Test content security scanning during processing."""
        malicious_content = DocumentContent(
            document_id=str(uuid.uuid4()),
            content="""<script>alert('XSS Attack')</script>
            This document contains malicious scripts and potential security threats.
            <?php system('rm -rf /'); ?>
            """,
            content_type="text/html"
        )

        processing_result = content_processor.process_document_content(malicious_content)

        assert processing_result["security_scan"]["passed"] is False
        assert "security_violations" in processing_result["security_scan"]
        assert len(processing_result["security_scan"]["security_violations"]) > 0
        assert "xss_attempts" in processing_result["security_scan"]["security_violations"]
        assert "system_commands" in processing_result["security_scan"]["security_violations"]


class TestDocumentStatusManagement:
    """Test Document Status Management functionality."""

    @pytest.fixture
    def status_manager(self, mock_repository, mock_event_bus):
        """Create status manager instance."""
        return LifecycleEventHandler(mock_repository, mock_event_bus)

    def test_document_status_transitions(self, status_manager):
        """Test valid document status transitions."""
        document_id = str(uuid.uuid4())

        # Initial creation -> draft
        status_manager.handle_status_transition(document_id, "draft", "created", "user@example.com")
        assert status_manager.get_document_status(document_id) == "draft"

        # Draft -> review
        status_manager.handle_status_transition(document_id, "review", "draft", "user@example.com")
        assert status_manager.get_document_status(document_id) == "review"

        # Review -> published
        status_manager.handle_status_transition(document_id, "published", "review", "user@example.com")
        assert status_manager.get_document_status(document_id) == "published"

        # Published -> archived
        status_manager.handle_status_transition(document_id, "archived", "published", "admin@example.com")
        assert status_manager.get_document_status(document_id) == "archived"

    def test_invalid_status_transitions(self, status_manager):
        """Test invalid document status transitions are rejected."""
        document_id = str(uuid.uuid4())
        status_manager.handle_status_transition(document_id, "draft", "created", "user@example.com")

        invalid_transitions = [
            ("draft", "published"),  # Cannot skip review
            ("archived", "draft"),   # Cannot unarchive to draft
            ("deleted", "published"), # Cannot publish deleted document
        ]

        for from_status, to_status in invalid_transitions:
            with pytest.raises(ValueError, match="Invalid status transition"):
                status_manager.handle_status_transition(document_id, to_status, from_status, "user@example.com")

    def test_status_transition_permissions(self, status_manager):
        """Test status transition permission controls."""
        document_id = str(uuid.uuid4())
        status_manager.handle_status_transition(document_id, "draft", "created", "user@example.com")

        # Regular user cannot archive
        with pytest.raises(PermissionError):
            status_manager.handle_status_transition(document_id, "archived", "draft", "user@example.com")

        # Admin can archive
        status_manager.handle_status_transition(document_id, "archived", "draft", "admin@example.com")
        assert status_manager.get_document_status(document_id) == "archived"

    def test_status_transition_auditing(self, status_manager):
        """Test status transition auditing and logging."""
        document_id = str(uuid.uuid4())

        # Perform several transitions
        transitions = [
            ("draft", "created", "user@example.com"),
            ("review", "draft", "reviewer@example.com"),
            ("published", "review", "publisher@example.com"),
        ]

        for to_status, from_status, user in transitions:
            status_manager.handle_status_transition(document_id, to_status, from_status, user)

        # Verify audit trail
        audit_trail = status_manager.get_status_transition_history(document_id)

        assert len(audit_trail) == 3
        for i, transition in enumerate(audit_trail):
            expected_to, expected_from, expected_user = transitions[i]
            assert transition["to_status"] == expected_to
            assert transition["from_status"] == expected_from
            assert transition["changed_by"] == expected_user
            assert "timestamp" in transition


class TestDocumentAccessControl:
    """Test Document Access Control functionality."""

    @pytest.fixture
    def access_controller(self, mock_repository):
        """Create access controller instance."""
        return DocumentService(repository=mock_repository)

    def test_basic_access_control(self, access_controller, sample_document):
        """Test basic access control permissions."""
        user_permissions = {
            "user@example.com": ["read"],
            "editor@example.com": ["read", "write"],
            "admin@example.com": ["read", "write", "delete", "admin"]
        }

        document = sample_document

        # Test read permissions
        assert access_controller.check_permission(document, "user@example.com", "read") is True
        assert access_controller.check_permission(document, "unauthorized@example.com", "read") is False

        # Test write permissions
        assert access_controller.check_permission(document, "editor@example.com", "write") is True
        assert access_controller.check_permission(document, "user@example.com", "write") is False

        # Test admin permissions
        assert access_controller.check_permission(document, "admin@example.com", "delete") is True
        assert access_controller.check_permission(document, "editor@example.com", "delete") is False

    def test_role_based_access_control(self, access_controller):
        """Test role-based access control."""
        document = {
            "access_control": {
                "owner": "owner@example.com",
                "roles": {
                    "viewer": ["viewer1@example.com", "viewer2@example.com"],
                    "editor": ["editor1@example.com"],
                    "admin": ["admin@example.com"]
                },
                "permissions": {
                    "viewer": ["read"],
                    "editor": ["read", "write"],
                    "admin": ["read", "write", "delete", "manage_permissions"]
                }
            }
        }

        # Test role-based permissions
        assert access_controller.check_role_permission(document, "viewer1@example.com", "read") is True
        assert access_controller.check_role_permission(document, "editor1@example.com", "write") is True
        assert access_controller.check_role_permission(document, "admin@example.com", "delete") is True

        # Test role restrictions
        assert access_controller.check_role_permission(document, "viewer1@example.com", "write") is False
        assert access_controller.check_role_permission(document, "editor1@example.com", "delete") is False

    def test_access_control_inheritance(self, access_controller):
        """Test access control inheritance from parent documents."""
        parent_document = {
            "id": str(uuid.uuid4()),
            "access_control": {
                "owner": "parent_owner@example.com",
                "readers": ["inherited_reader@example.com"],
                "inherit_permissions": True
            }
        }

        child_document = {
            "id": str(uuid.uuid4()),
            "parent_id": parent_document["id"],
            "access_control": {
                "owner": "child_owner@example.com",
                "inherit_permissions": True
            }
        }

        # Child should inherit permissions from parent
        assert access_controller.check_inherited_permission(
            child_document, parent_document, "inherited_reader@example.com", "read"
        ) is True

        # Child owner should have full permissions
        assert access_controller.check_inherited_permission(
            child_document, parent_document, "child_owner@example.com", "write"
        ) is True

    def test_temporary_access_grants(self, access_controller):
        """Test temporary access grants with expiration."""
        document_id = str(uuid.uuid4())

        # Grant temporary access
        grant = {
            "user": "temp_user@example.com",
            "permissions": ["read", "write"],
            "expires_at": datetime.now() + timedelta(hours=1),
            "granted_by": "admin@example.com",
            "reason": "Temporary edit access for review"
        }

        access_controller.grant_temporary_access(document_id, grant)

        # Verify access during validity period
        assert access_controller.check_temporary_permission(
            document_id, "temp_user@example.com", "read"
        ) is True

        assert access_controller.check_temporary_permission(
            document_id, "temp_user@example.com", "write"
        ) is True

        # Simulate expiration
        expired_grant = grant.copy()
        expired_grant["expires_at"] = datetime.now() - timedelta(hours=1)

        assert access_controller.check_temporary_permission(
            document_id, "temp_user@example.com", "read"
        ) is False


class TestDocumentArchivalAndDeletion:
    """Test Document Archival and Deletion functionality."""

    @pytest.fixture
    def lifecycle_manager(self, mock_repository, mock_file_storage, mock_event_bus):
        """Create lifecycle manager instance."""
        return LifecycleService(mock_repository, mock_file_storage, mock_event_bus)

    def test_document_archival(self, lifecycle_manager, sample_document):
        """Test document archival process."""
        document = sample_document

        archival_result = lifecycle_manager.archive_document(document.id, "admin@example.com", "End of lifecycle")

        assert archival_result["success"] is True
        assert archival_result["archival_status"] == "completed"
        assert "archival_metadata" in archival_result

        # Verify archival metadata
        metadata = archival_result["archival_metadata"]
        assert metadata["archived_by"] == "admin@example.com"
        assert metadata["archival_reason"] == "End of lifecycle"
        assert "archival_date" in metadata
        assert "retention_period_days" in metadata

    def test_archival_with_retention_policy(self, lifecycle_manager):
        """Test document archival with retention policy enforcement."""
        document_id = str(uuid.uuid4())

        retention_policy = {
            "retention_period_days": 2555,  # 7 years
            "archive_medium": "cold_storage",
            "compliance_requirements": ["gdpr", "industry_regulation"],
            "auto_delete_after_retention": True
        }

        archival_result = lifecycle_manager.archive_with_retention_policy(
            document_id, retention_policy, "compliance@example.com"
        )

        assert archival_result["success"] is True
        assert archival_result["retention_policy_applied"] is True
        assert archival_result["estimated_deletion_date"] > datetime.now()

        # Verify compliance metadata
        compliance = archival_result["compliance_metadata"]
        assert "gdpr" in compliance["requirements_met"]
        assert compliance["retention_calculated"] is True

    def test_document_deletion_cascade(self, lifecycle_manager):
        """Test document deletion with cascade to related entities."""
        document_id = str(uuid.uuid4())

        related_entities = {
            "versions": [str(uuid.uuid4()), str(uuid.uuid4())],
            "relationships": [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())],
            "attachments": [str(uuid.uuid4())],
            "comments": [str(uuid.uuid4()), str(uuid.uuid4())]
        }

        deletion_result = lifecycle_manager.delete_document_cascade(
            document_id, related_entities, "admin@example.com", "User requested deletion"
        )

        assert deletion_result["success"] is True
        assert deletion_result["cascade_deletion"] is True

        # Verify all related entities were deleted
        cascade_results = deletion_result["cascade_results"]
        assert cascade_results["versions_deleted"] == len(related_entities["versions"])
        assert cascade_results["relationships_deleted"] == len(related_entities["relationships"])
        assert cascade_results["attachments_deleted"] == len(related_entities["attachments"])
        assert cascade_results["comments_deleted"] == len(related_entities["comments"])

    def test_soft_deletion_and_recovery(self, lifecycle_manager, sample_document):
        """Test soft deletion and recovery functionality."""
        document = sample_document

        # Soft delete
        delete_result = lifecycle_manager.soft_delete_document(
            document.id, "user@example.com", "Temporary removal"
        )

        assert delete_result["success"] is True
        assert delete_result["deletion_type"] == "soft"
        assert delete_result["recoverable"] is True

        # Verify document is marked as deleted but not actually removed
        assert lifecycle_manager.is_document_deleted(document.id) is True
        assert lifecycle_manager.get_document(document.id) is not None  # Still exists

        # Recover document
        recovery_result = lifecycle_manager.recover_document(document.id, "admin@example.com")

        assert recovery_result["success"] is True
        assert recovery_result["recovered"] is True
        assert lifecycle_manager.is_document_deleted(document.id) is False

    def test_permanent_deletion_with_verification(self, lifecycle_manager):
        """Test permanent deletion with verification requirements."""
        document_id = str(uuid.uuid4())

        # Require verification for permanent deletion
        verification_requirements = {
            "require_admin_approval": True,
            "require_reason": True,
            "require_backup_verification": True,
            "confirmation_code_required": True
        }

        deletion_request = {
            "document_id": document_id,
            "deletion_type": "permanent",
            "reason": "Legal compliance requirement",
            "requested_by": "legal@example.com",
            "admin_approval": "admin@example.com",
            "backup_verified": True,
            "confirmation_code": "DELETE-12345"
        }

        deletion_result = lifecycle_manager.permanent_delete_with_verification(
            deletion_request, verification_requirements
        )

        assert deletion_result["success"] is True
        assert deletion_result["deletion_type"] == "permanent"
        assert deletion_result["verification_completed"] is True

        # Verify all verification steps were completed
        verification = deletion_result["verification_results"]
        assert verification["admin_approved"] is True
        assert verification["reason_provided"] is True
        assert verification["backup_verified"] is True
        assert verification["confirmation_code_valid"] is True

    def test_lifecycle_event_notifications(self, lifecycle_manager):
        """Test lifecycle event notifications."""
        document_id = str(uuid.uuid4())

        # Archive document
        lifecycle_manager.archive_document(document_id, "admin@example.com", "Lifecycle end")

        # Verify notifications were sent
        notifications_sent = lifecycle_manager.get_notification_history(document_id)

        assert len(notifications_sent) > 0

        # Should include archival notification
        archival_notifications = [n for n in notifications_sent if n["event_type"] == "document_archived"]
        assert len(archival_notifications) == 1

        archival_notification = archival_notifications[0]
        assert archival_notification["recipient"] == "admin@example.com"
        assert "archival" in archival_notification["message"].lower()

    def test_lifecycle_audit_trail(self, lifecycle_manager):
        """Test comprehensive lifecycle audit trail."""
        document_id = str(uuid.uuid4())

        # Perform various lifecycle operations
        operations = [
            ("create", "user@example.com"),
            ("update", "editor@example.com"),
            ("publish", "publisher@example.com"),
            ("archive", "admin@example.com"),
            ("delete", "admin@example.com")
        ]

        for operation, user in operations:
            if operation == "create":
                lifecycle_manager.create_document(document_id, user)
            elif operation == "update":
                lifecycle_manager.update_document(document_id, user, "Content update")
            elif operation == "publish":
                lifecycle_manager.publish_document(document_id, user)
            elif operation == "archive":
                lifecycle_manager.archive_document(document_id, user, "End of life")
            elif operation == "delete":
                lifecycle_manager.delete_document(document_id, user, "Cleanup")

        # Get complete audit trail
        audit_trail = lifecycle_manager.get_lifecycle_audit_trail(document_id)

        assert len(audit_trail) == len(operations)

        # Verify chronological order and completeness
        for i, entry in enumerate(audit_trail):
            expected_operation, expected_user = operations[i]
            assert entry["operation"] == expected_operation
            assert entry["performed_by"] == expected_user
            assert "timestamp" in entry
            assert entry["timestamp"] <= datetime.now()

        # Verify audit trail integrity
        assert lifecycle_manager.verify_audit_trail_integrity(document_id) is True
