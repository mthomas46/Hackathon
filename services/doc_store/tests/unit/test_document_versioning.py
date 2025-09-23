"""Unit Tests for Document Versioning in Document Store Service.

This module tests document versioning capabilities including:
- Version creation and management
- Version comparison and diffing
- Version history and lineage tracking
- Version merging and conflict resolution
- Version access control and permissions
- Version archival and cleanup

Tests cover the complete document versioning system within the DDD architecture.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from core.entities import DocumentVersion
from domain.versioning.handlers import VersioningCommandHandler
from domain.versioning.repository import VersioningRepository
from domain.versioning.service import VersioningService


class TestVersionCreation:
    """Test Version Creation functionality."""

    @pytest.fixture
    def versioning_handler(self, mock_repository, mock_event_bus):
        """Create versioning handler instance."""
        return VersioningCommandHandler(mock_repository, mock_event_bus)

    def test_basic_version_creation(self, versioning_handler, sample_document):
        """Test basic version creation from document changes."""
        document_id = sample_document.id

        version_data = {
            "document_id": document_id,
            "title": "Updated Document Title",
            "content": "This is the updated content with new information.",
            "change_summary": "Updated content and title",
            "change_type": "content_update",
            "created_by": "editor@example.com"
        }

        version_result = versioning_handler.handle_create_version(version_data)

        assert version_result["success"] is True
        assert "version_id" in version_result
        assert "version_number" in version_result
        assert version_result["version_number"] == 2  # First version after original

    def test_version_creation_with_metadata(self, versioning_handler):
        """Test version creation with comprehensive metadata."""
        document_id = str(uuid.uuid4())

        version_metadata = {
            "document_id": document_id,
            "title": "Enhanced Technical Document",
            "content": "Updated technical content with additional details and examples.",
            "change_summary": "Enhanced technical content with examples and clarifications",
            "change_type": "enhancement",
            "created_by": "technical.writer@company.com",
            "tags_added": ["examples", "clarification"],
            "tags_removed": ["draft"],
            "metadata_changes": {
                "complexity_level": "intermediate",
                "review_status": "approved",
                "target_audience": "developers"
            },
            "file_changes": {
                "size_delta_bytes": 2048,
                "content_type_unchanged": True
            }
        }

        version_result = versioning_handler.handle_create_version(version_metadata)

        assert version_result["success"] is True
        assert version_result["version"]["change_type"] == "enhancement"
        assert version_result["version"]["created_by"] == "technical.writer@company.com"
        assert "tags_added" in version_result["version"]
        assert "metadata_changes" in version_result["version"]

    def test_automatic_version_numbering(self, versioning_handler):
        """Test automatic version number assignment."""
        document_id = str(uuid.uuid4())

        # Create multiple versions
        versions_created = []
        for i in range(5):
            version_data = {
                "document_id": document_id,
                "title": f"Version {i+1} Title",
                "content": f"Content for version {i+1}",
                "change_summary": f"Version {i+1} changes",
                "created_by": "user@example.com"
            }

            result = versioning_handler.handle_create_version(version_data)
            versions_created.append(result)

        # Verify sequential version numbering
        for i, version in enumerate(versions_created):
            assert version["version_number"] == i + 1

    def test_version_creation_validation(self, versioning_handler):
        """Test version creation input validation."""
        invalid_versions = [
            # Missing document_id
            {"title": "Test", "content": "Content", "created_by": "user@example.com"},
            # Missing content
            {"document_id": str(uuid.uuid4()), "title": "Test", "created_by": "user@example.com"},
            # Invalid change_type
            {
                "document_id": str(uuid.uuid4()),
                "title": "Test",
                "content": "Content",
                "change_type": "invalid_type",
                "created_by": "user@example.com"
            },
            # Empty change summary
            {
                "document_id": str(uuid.uuid4()),
                "title": "Test",
                "content": "Content",
                "change_summary": "",
                "created_by": "user@example.com"
            }
        ]

        for invalid_version in invalid_versions:
            result = versioning_handler.handle_create_version(invalid_version)
            assert result["success"] is False
            assert "validation_errors" in result

    def test_version_creation_with_attachments(self, versioning_handler, mock_file_storage):
        """Test version creation with file attachments."""
        document_id = str(uuid.uuid4())

        attachment_data = {
            "filename": "diagram.png",
            "content_type": "image/png",
            "size_bytes": 51200,
            "checksum": "abc123"
        }

        version_data = {
            "document_id": document_id,
            "title": "Document with Diagram",
            "content": "Updated content with diagram",
            "change_summary": "Added diagram attachment",
            "attachments": [attachment_data],
            "created_by": "user@example.com"
        }

        version_result = versioning_handler.handle_create_version_with_attachments(version_data)

        assert version_result["success"] is True
        assert "attachments" in version_result["version"]
        assert len(version_result["version"]["attachments"]) == 1

        attachment = version_result["version"]["attachments"][0]
        assert attachment["filename"] == "diagram.png"
        assert attachment["storage_path"] is not None


class TestVersionComparison:
    """Test Version Comparison functionality."""

    @pytest.fixture
    def version_comparer(self, mock_repository):
        """Create version comparison service instance."""
        return VersioningService(repository=mock_repository)

    def test_basic_version_diff(self, version_comparer, sample_document_version):
        """Test basic version difference calculation."""
        version1 = sample_document_version
        version2 = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=version1.document_id,
            version_number=3,
            title="Further Updated Document",
            content="This is further updated content with significant changes.",
            content_type="text/markdown",
            change_summary="Major content revision",
            change_type="major_revision",
            created_by="editor@example.com",
            created_at=datetime.now(),
            file_size_bytes=30000,
            checksum="def456",
            is_current=False,
            parent_version_id=version1.id
        )

        diff_result = version_comparer.compare_versions(version1.id, version2.id)

        assert diff_result["success"] is True
        assert "differences" in diff_result
        assert "similarity_score" in diff_result

        differences = diff_result["differences"]
        assert "title_changed" in differences
        assert "content_changed" in differences
        assert "size_changed" in differences

        # Similarity should be less than 1.0 (not identical)
        assert diff_result["similarity_score"] < 1.0

    def test_detailed_content_diff(self, version_comparer):
        """Test detailed content difference analysis."""
        content_v1 = """# Introduction

This is the introduction section.
It contains basic information about the topic.

## Background

The background section provides context."""

        content_v2 = """# Introduction

This is the updated introduction section.
It contains enhanced information about the advanced topic.

## Background

The background section provides detailed context.
This is an additional paragraph."""

        version1 = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=str(uuid.uuid4()),
            version_number=1,
            title="Original Document",
            content=content_v1,
            content_type="text/markdown",
            created_at=datetime.now() - timedelta(days=1)
        )

        version2 = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=version1.document_id,
            version_number=2,
            title="Updated Document",
            content=content_v2,
            content_type="text/markdown",
            created_at=datetime.now()
        )

        detailed_diff = version_comparer.generate_detailed_diff(version1.id, version2.id)

        assert detailed_diff["success"] is True
        assert "content_diff" in detailed_diff
        assert "structural_changes" in detailed_diff

        content_diff = detailed_diff["content_diff"]
        assert "additions" in content_diff
        assert "deletions" in content_diff
        assert "modifications" in content_diff

        # Should detect added content
        assert len(content_diff["additions"]) > 0
        assert "enhanced information" in " ".join(content_diff["additions"])
        assert "additional paragraph" in " ".join(content_diff["additions"])

    def test_version_similarity_scoring(self, version_comparer):
        """Test version similarity scoring algorithms."""
        test_cases = [
            {
                "content1": "Machine learning is a subset of AI",
                "content2": "Machine learning represents a subset of artificial intelligence",
                "expected_similarity": 0.8  # High similarity - rephrased
            },
            {
                "content1": "Python is a programming language",
                "content2": "Java is an object-oriented programming language",
                "expected_similarity": 0.4  # Medium similarity - related but different
            },
            {
                "content1": "The weather is sunny today",
                "content2": "Stock prices fluctuated significantly",
                "expected_similarity": 0.1  # Low similarity - completely different
            }
        ]

        for test_case in test_cases:
            version1 = DocumentVersion(
                id=str(uuid.uuid4()),
                document_id=str(uuid.uuid4()),
                version_number=1,
                content=test_case["content1"]
            )

            version2 = DocumentVersion(
                id=str(uuid.uuid4()),
                document_id=version1.document_id,
                version_number=2,
                content=test_case["content2"]
            )

            similarity = version_comparer.calculate_version_similarity(version1.id, version2.id)

            assert similarity["success"] is True
            assert "similarity_score" in similarity

            # Similarity should be close to expected
            actual_similarity = similarity["similarity_score"]
            expected_similarity = test_case["expected_similarity"]

            assert abs(actual_similarity - expected_similarity) < 0.2

    def test_version_conflict_detection(self, version_comparer):
        """Test version conflict detection for concurrent edits."""
        base_content = "Original content for testing"

        # Version A: Changes first paragraph
        version_a = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=str(uuid.uuid4()),
            version_number=2,
            content="Modified first paragraph content for testing",
            parent_version_id=str(uuid.uuid4())
        )

        # Version B: Changes second paragraph
        version_b = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=version_a.document_id,
            version_number=2,
            content="Original content for testing\nModified second paragraph",
            parent_version_id=version_a.parent_version_id  # Same parent
        )

        conflict_analysis = version_comparer.detect_version_conflicts(version_a.id, version_b.id)

        assert conflict_analysis["success"] is True
        assert "has_conflicts" in conflict_analysis
        assert "conflict_details" in conflict_analysis

        # These versions should not conflict (different sections)
        assert conflict_analysis["has_conflicts"] is False

        # Now test conflicting versions
        version_a_conflict = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=str(uuid.uuid4()),
            version_number=2,
            content="Both versions modified the same content section",
            parent_version_id=str(uuid.uuid4())
        )

        version_b_conflict = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=version_a_conflict.document_id,
            version_number=2,
            content="Both versions changed this exact same section",
            parent_version_id=version_a_conflict.parent_version_id
        )

        conflict_analysis_conflict = version_comparer.detect_version_conflicts(
            version_a_conflict.id, version_b_conflict.id
        )

        assert conflict_analysis_conflict["has_conflicts"] is True
        assert len(conflict_analysis_conflict["conflict_details"]) > 0


class TestVersionHistory:
    """Test Version History functionality."""

    @pytest.fixture
    def history_manager(self, mock_repository):
        """Create version history manager instance."""
        return VersioningService(repository=mock_repository)

    def test_version_history_retrieval(self, history_manager):
        """Test retrieval of complete version history."""
        document_id = str(uuid.uuid4())

        # Simulate version history
        versions = []
        for i in range(5):
            version = DocumentVersion(
                id=str(uuid.uuid4()),
                document_id=document_id,
                version_number=i + 1,
                title=f"Version {i + 1}",
                content=f"Content for version {i + 1}",
                created_at=datetime.now() - timedelta(days=5-i),
                created_by=f"user{i}@example.com"
            )
            versions.append(version)

        history_result = history_manager.get_version_history(document_id)

        assert history_result["success"] is True
        assert "versions" in history_result
        assert len(history_result["versions"]) == 5

        # Should be ordered by version number (ascending)
        for i in range(4):
            assert history_result["versions"][i]["version_number"] < history_result["versions"][i + 1]["version_number"]

    def test_version_lineage_tracking(self, history_manager):
        """Test version lineage and ancestry tracking."""
        # Create a version tree:
        # v1 -> v2 -> v4
        #    -> v3 -> v5

        base_version = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=str(uuid.uuid4()),
            version_number=1,
            title="Base Version",
            created_at=datetime.now() - timedelta(days=4)
        )

        version2 = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=base_version.document_id,
            version_number=2,
            title="Branch A",
            parent_version_id=base_version.id,
            created_at=datetime.now() - timedelta(days=3)
        )

        version3 = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=base_version.document_id,
            version_number=3,
            title="Branch B",
            parent_version_id=base_version.id,
            created_at=datetime.now() - timedelta(days=3)
        )

        version4 = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=base_version.document_id,
            version_number=4,
            title="Branch A Continuation",
            parent_version_id=version2.id,
            created_at=datetime.now() - timedelta(days=2)
        )

        version5 = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=base_version.document_id,
            version_number=5,
            title="Branch B Continuation",
            parent_version_id=version3.id,
            created_at=datetime.now() - timedelta(days=2)
        )

        lineage_result = history_manager.get_version_lineage(base_version.document_id)

        assert lineage_result["success"] is True
        assert "lineage_tree" in lineage_result

        lineage_tree = lineage_result["lineage_tree"]

        # Should have root version
        assert "root_version" in lineage_tree
        assert lineage_tree["root_version"]["id"] == base_version.id

        # Should have branches
        assert "branches" in lineage_tree
        assert len(lineage_tree["branches"]) == 2  # Two main branches

        # Each branch should have correct ancestry
        for branch in lineage_tree["branches"]:
            assert branch["parent_id"] == base_version.id
            assert len(branch["children"]) >= 1

    def test_version_timeline_generation(self, history_manager):
        """Test version timeline generation with events."""
        document_id = str(uuid.uuid4())

        timeline_events = [
            {
                "version_number": 1,
                "event_type": "created",
                "timestamp": datetime.now() - timedelta(days=5),
                "actor": "creator@example.com",
                "description": "Initial document creation"
            },
            {
                "version_number": 2,
                "event_type": "edited",
                "timestamp": datetime.now() - timedelta(days=3),
                "actor": "editor@example.com",
                "description": "Major content revision"
            },
            {
                "version_number": 3,
                "event_type": "reviewed",
                "timestamp": datetime.now() - timedelta(days=2),
                "actor": "reviewer@example.com",
                "description": "Peer review completed"
            },
            {
                "version_number": 4,
                "event_type": "published",
                "timestamp": datetime.now() - timedelta(days=1),
                "actor": "publisher@example.com",
                "description": "Document published"
            }
        ]

        timeline_result = history_manager.generate_version_timeline(document_id)

        assert timeline_result["success"] is True
        assert "timeline" in timeline_result
        assert len(timeline_result["timeline"]) == 4

        # Timeline should be chronological
        for i in range(3):
            current_time = timeline_result["timeline"][i]["timestamp"]
            next_time = timeline_result["timeline"][i + 1]["timestamp"]
            assert current_time <= next_time

        # Should include all event types
        event_types = {event["event_type"] for event in timeline_result["timeline"]}
        assert event_types == {"created", "edited", "reviewed", "published"}

    def test_version_revert_capability(self, history_manager):
        """Test version revert functionality."""
        document_id = str(uuid.uuid4())

        # Create version history
        versions = []
        for i in range(3):
            version = DocumentVersion(
                id=str(uuid.uuid4()),
                document_id=document_id,
                version_number=i + 1,
                title=f"Version {i + 1}",
                content=f"Content version {i + 1}",
                created_at=datetime.now() - timedelta(days=3-i)
            )
            versions.append(version)

        # Revert to version 2
        revert_result = history_manager.revert_to_version(document_id, 2, "admin@example.com")

        assert revert_result["success"] is True
        assert "new_version" in revert_result
        assert revert_result["new_version"]["version_number"] == 4  # Next version number
        assert revert_result["new_version"]["title"] == "Version 2"  # Reverted content
        assert revert_result["new_version"]["reverted_from_version"] == 3

    def test_version_access_audit(self, history_manager):
        """Test version access auditing and tracking."""
        document_id = str(uuid.uuid4())
        version_id = str(uuid.uuid4())
        user_id = "user@example.com"

        # Simulate version access
        access_events = [
            {"action": "viewed", "timestamp": datetime.now() - timedelta(hours=2)},
            {"action": "downloaded", "timestamp": datetime.now() - timedelta(hours=1)},
            {"action": "compared", "timestamp": datetime.now() - timedelta(minutes=30)}
        ]

        for event in access_events:
            history_manager.record_version_access(version_id, user_id, event["action"], event["timestamp"])

        audit_result = history_manager.get_version_access_audit(version_id)

        assert audit_result["success"] is True
        assert "access_events" in audit_result
        assert len(audit_result["access_events"]) == 3

        # Should include all access types
        actions = {event["action"] for event in audit_result["access_events"]}
        assert actions == {"viewed", "downloaded", "compared"}

        # Should be ordered by timestamp
        for i in range(2):
            current_time = audit_result["access_events"][i]["timestamp"]
            next_time = audit_result["access_events"][i + 1]["timestamp"]
            assert current_time <= next_time


class TestVersionMerging:
    """Test Version Merging functionality."""

    @pytest.fixture
    def merge_service(self, mock_repository, mock_event_bus):
        """Create version merge service instance."""
        return VersioningService(repository=mock_repository, event_bus=mock_event_bus)

    def test_three_way_version_merge(self, merge_service):
        """Test three-way merge of conflicting versions."""
        base_content = """# Document Title

## Section 1
Original content in section 1.

## Section 2
Original content in section 2."""

        # Branch A changes section 1
        branch_a_content = """# Document Title

## Section 1
Modified content in section 1 by branch A.

## Section 2
Original content in section 2."""

        # Branch B changes section 2
        branch_b_content = """# Document Title

## Section 1
Original content in section 1.

## Section 2
Modified content in section 2 by branch B."""

        merge_request = {
            "document_id": str(uuid.uuid4()),
            "base_version_id": str(uuid.uuid4()),
            "branch_a_version_id": str(uuid.uuid4()),
            "branch_b_version_id": str(uuid.uuid4()),
            "merge_strategy": "three_way",
            "conflict_resolution": "automatic"
        }

        merge_result = merge_service.perform_three_way_merge(merge_request)

        assert merge_result["success"] is True
        assert "merged_version" in merge_result
        assert "merge_conflicts" in merge_result
        assert "merge_quality_score" in merge_result

        # Should have no conflicts (different sections)
        assert len(merge_result["merge_conflicts"]) == 0

        # Should have high merge quality
        assert merge_result["merge_quality_score"] > 0.8

        merged_content = merge_result["merged_version"]["content"]
        assert "Modified content in section 1 by branch A" in merged_content
        assert "Modified content in section 2 by branch B" in merged_content

    def test_conflict_resolution_strategies(self, merge_service):
        """Test different conflict resolution strategies."""
        # Create conflicting versions
        base_content = "The algorithm is efficient."
        version_a_content = "The algorithm is very efficient."
        version_b_content = "The algorithm is highly efficient."

        conflict_scenarios = [
            {
                "strategy": "prefer_branch_a",
                "expected_content": version_a_content
            },
            {
                "strategy": "prefer_branch_b",
                "expected_content": version_b_content
            },
            {
                "strategy": "manual_resolution",
                "expected_content": "The algorithm is extremely efficient."  # Manual choice
            }
        ]

        for scenario in conflict_scenarios:
            merge_request = {
                "document_id": str(uuid.uuid4()),
                "base_version_id": str(uuid.uuid4()),
                "branch_a_version_id": str(uuid.uuid4()),
                "branch_b_version_id": str(uuid.uuid4()),
                "merge_strategy": "three_way",
                "conflict_resolution": scenario["strategy"]
            }

            merge_result = merge_service.perform_three_way_merge(merge_request)

            assert merge_result["success"] is True
            merged_content = merge_result["merged_version"]["content"]

            # Should resolve according to strategy
            if scenario["strategy"] != "manual_resolution":
                assert merged_content == scenario["expected_content"]

    def test_version_branch_management(self, merge_service):
        """Test version branch creation and management."""
        document_id = str(uuid.uuid4())
        base_version_id = str(uuid.uuid4())

        # Create development branch
        dev_branch = merge_service.create_version_branch(
            document_id, base_version_id, "development", "user@example.com"
        )

        assert dev_branch["success"] is True
        assert dev_branch["branch_name"] == "development"
        assert "branch_id" in dev_branch

        # Create feature branch from development
        feature_branch = merge_service.create_version_branch(
            document_id, dev_branch["branch_id"], "feature/new-feature", "developer@example.com"
        )

        assert feature_branch["success"] is True
        assert feature_branch["branch_name"] == "feature/new-feature"
        assert feature_branch["parent_branch"] == "development"

    def test_version_cleanup_and_archival(self, merge_service):
        """Test version cleanup and archival policies."""
        document_id = str(uuid.uuid4())

        cleanup_config = {
            "max_versions_to_keep": 10,
            "archive_older_than_days": 90,
            "delete_older_than_days": 365,
            "keep_major_versions": True,
            "archive_branches_after_merge": True
        }

        cleanup_result = merge_service.perform_version_cleanup(document_id, cleanup_config)

        assert cleanup_result["success"] is True
        assert "versions_archived" in cleanup_result
        assert "versions_deleted" in cleanup_result
        assert "cleanup_summary" in cleanup_result

        summary = cleanup_result["cleanup_summary"]
        assert "total_versions_processed" in summary
        assert "space_reclaimed_bytes" in summary
        assert "policy_compliance_score" in summary

    def test_version_integrity_verification(self, merge_service):
        """Test version integrity verification and checksum validation."""
        document_id = str(uuid.uuid4())

        integrity_result = merge_service.verify_version_integrity(document_id)

        assert integrity_result["success"] is True
        assert "integrity_checks" in integrity_result
        assert "overall_integrity_score" in integrity_result

        checks = integrity_result["integrity_checks"]
        assert "checksum_validation" in checks
        assert "content_consistency" in checks
        assert "metadata_integrity" in checks
        assert "relationship_consistency" in checks

        # Should have high integrity score
        assert integrity_result["overall_integrity_score"] > 0.95

    def test_version_performance_optimization(self, merge_service):
        """Test version storage and retrieval performance optimization."""
        document_id = str(uuid.uuid4())

        optimization_result = merge_service.optimize_version_performance(document_id)

        assert optimization_result["success"] is True
        assert "optimizations_applied" in optimization_result
        assert "performance_improvements" in optimization_result

        optimizations = optimization_result["optimizations_applied"]
        assert "index_optimization" in optimizations
        assert "caching_strategy" in optimizations
        assert "storage_compaction" in optimizations

        improvements = optimization_result["performance_improvements"]
        assert "retrieval_time_improvement_percent" in improvements
        assert "storage_efficiency_improvement_percent" in improvements
