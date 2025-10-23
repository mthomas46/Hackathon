"""
Functional tests for documentation run management.

These tests validate that documentation runs can be created, persisted,
retrieved, and associated with generated documents using the test database.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Dict, Any

from src.models.documentation import DocumentationRunModel, RunStatus, GeneratedDocumentModel
from src.repositories.documentation_run_repository import DocumentationRunRepository
from src.services.documentation.run_manager import DocumentationRunManager
from tests.utils.test_helpers import create_test_document


pytestmark = pytest.mark.functional


@pytest.fixture
async def run_repo(clean_database):
    """Documentation run repository with test database."""
    return DocumentationRunRepository(clean_database)


@pytest.fixture
async def run_manager(clean_database, run_repo):
    """Documentation run manager with test database."""
    return DocumentationRunManager(clean_database, run_repo)


class TestDocumentationRunCreation:
    """Test documentation run creation and persistence."""

    async def test_create_documentation_run(
        self,
        run_manager,
        test_session_id
    ):
        """Test creating a documentation run."""
        # Create run
        run = await run_manager.create_run(
            repo_path="/test/repo",
            config={
                "model": "llama3.2:latest",
                "passes": 3,
                "skip_review": False
            },
            test_session_id=test_session_id
        )

        assert run is not None
        assert run.id is not None
        assert run.repo_path == "/test/repo"
        assert run.status == RunStatus.PENDING
        assert run.config["passes"] == 3

    async def test_create_run_with_snapshot_id(
        self,
        run_manager,
        test_session_id
    ):
        """Test creating a run with snapshot ID."""
        snapshot_id = str(uuid4())

        run = await run_manager.create_run(
            repo_path="/test/repo",
            snapshot_id=snapshot_id,
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        assert run.snapshot_id == snapshot_id

    async def test_create_run_with_metadata(
        self,
        run_manager,
        test_session_id
    ):
        """Test creating a run with metadata."""
        run = await run_manager.create_run(
            repo_path="/test/repo",
            config={"model": "llama3.2:latest"},
            metadata={
                "user": "test_user",
                "purpose": "testing",
                "tags": ["test", "functional"]
            },
            test_session_id=test_session_id
        )

        assert run.metadata["user"] == "test_user"
        assert "test" in run.metadata["tags"]


class TestDocumentationRunRetrieval:
    """Test retrieving documentation runs."""

    async def test_get_run_by_id(
        self,
        run_manager,
        test_session_id
    ):
        """Test retrieving a run by ID."""
        # Create run
        run = await run_manager.create_run(
            repo_path="/test/repo",
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        # Retrieve run
        retrieved = await run_manager.get_run(run.id)

        assert retrieved is not None
        assert retrieved.id == run.id
        assert retrieved.repo_path == run.repo_path

    async def test_get_runs_by_repo_path(
        self,
        run_manager,
        test_session_id
    ):
        """Test retrieving runs by repository path."""
        repo_path = "/test/repo"

        # Create multiple runs
        for i in range(3):
            await run_manager.create_run(
                repo_path=repo_path,
                config={"model": "llama3.2:latest", "pass": i},
                test_session_id=test_session_id
            )

        # Retrieve runs
        runs = await run_manager.get_runs_by_repo(repo_path)

        assert len(runs) >= 3
        assert all(run.repo_path == repo_path for run in runs)

    async def test_get_runs_by_status(
        self,
        run_manager,
        test_session_id
    ):
        """Test retrieving runs by status."""
        # Create runs with different statuses
        run1 = await run_manager.create_run(
            repo_path="/test/repo1",
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        run2 = await run_manager.create_run(
            repo_path="/test/repo2",
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        # Update status
        await run_manager.update_run_status(run2.id, RunStatus.PROCESSING)

        # Retrieve by status
        pending_runs = await run_manager.get_runs_by_status(RunStatus.PENDING)
        processing_runs = await run_manager.get_runs_by_status(RunStatus.PROCESSING)

        pending_ids = [run.id for run in pending_runs]
        processing_ids = [run.id for run in processing_runs]

        assert run1.id in pending_ids
        assert run2.id in processing_ids

    async def test_get_recent_runs(
        self,
        run_manager,
        test_session_id
    ):
        """Test retrieving recent runs."""
        # Create runs
        for i in range(5):
            await run_manager.create_run(
                repo_path=f"/test/repo{i}",
                config={"model": "llama3.2:latest"},
                test_session_id=test_session_id
            )

        # Get recent runs (limit 3)
        recent = await run_manager.get_recent_runs(limit=3)

        assert len(recent) == 3
        # Should be ordered by created_at desc


class TestDocumentAssociation:
    """Test associating documents with runs."""

    async def test_associate_document_with_run(
        self,
        run_manager,
        test_session_id
    ):
        """Test associating a generated document with a run."""
        # Create run
        run = await run_manager.create_run(
            repo_path="/test/repo",
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        # Generate document
        doc = await run_manager.add_generated_document(
            run_id=run.id,
            file_path="docs/architecture.md",
            content="# Architecture\n\nSystem architecture...",
            doc_type="architecture",
            metadata={"pass": 1}
        )

        assert doc is not None
        assert doc.run_id == run.id
        assert doc.file_path == "docs/architecture.md"

    async def test_get_documents_for_run(
        self,
        run_manager,
        test_session_id
    ):
        """Test retrieving all documents for a run."""
        # Create run
        run = await run_manager.create_run(
            repo_path="/test/repo",
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        # Generate multiple documents
        doc_types = ["architecture", "api", "deployment"]
        for doc_type in doc_types:
            await run_manager.add_generated_document(
                run_id=run.id,
                file_path=f"docs/{doc_type}.md",
                content=f"# {doc_type.title()}\n\nContent...",
                doc_type=doc_type
            )

        # Retrieve documents
        documents = await run_manager.get_run_documents(run.id)

        assert len(documents) == 3
        doc_types_retrieved = [doc.doc_type for doc in documents]
        assert set(doc_types_retrieved) == set(doc_types)

    async def test_document_versioning_across_runs(
        self,
        run_manager,
        test_session_id
    ):
        """Test that documents are versioned across runs."""
        repo_path = "/test/repo"

        # Create first run
        run1 = await run_manager.create_run(
            repo_path=repo_path,
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        doc1 = await run_manager.add_generated_document(
            run_id=run1.id,
            file_path="docs/architecture.md",
            content="# Architecture v1",
            doc_type="architecture"
        )

        # Create second run
        run2 = await run_manager.create_run(
            repo_path=repo_path,
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        doc2 = await run_manager.add_generated_document(
            run_id=run2.id,
            file_path="docs/architecture.md",
            content="# Architecture v2",
            doc_type="architecture"
        )

        # Both documents should exist with different run IDs
        assert doc1.run_id == run1.id
        assert doc2.run_id == run2.id
        assert doc1.content != doc2.content


class TestRunStatusManagement:
    """Test run status updates and lifecycle."""

    async def test_update_run_status(
        self,
        run_manager,
        test_session_id
    ):
        """Test updating run status."""
        # Create run
        run = await run_manager.create_run(
            repo_path="/test/repo",
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        assert run.status == RunStatus.PENDING

        # Update to processing
        await run_manager.update_run_status(run.id, RunStatus.PROCESSING)
        updated = await run_manager.get_run(run.id)
        assert updated.status == RunStatus.PROCESSING

        # Update to completed
        await run_manager.update_run_status(run.id, RunStatus.COMPLETED)
        updated = await run_manager.get_run(run.id)
        assert updated.status == RunStatus.COMPLETED

    async def test_run_progress_tracking(
        self,
        run_manager,
        test_session_id
    ):
        """Test tracking run progress."""
        # Create run
        run = await run_manager.create_run(
            repo_path="/test/repo",
            config={"model": "llama3.2:latest", "passes": 3},
            test_session_id=test_session_id
        )

        # Update progress
        await run_manager.update_run_progress(
            run.id,
            current_pass=1,
            total_passes=3,
            documents_generated=5
        )

        updated = await run_manager.get_run(run.id)
        assert updated.current_pass == 1
        assert updated.total_passes == 3
        assert updated.documents_generated == 5

    async def test_run_error_handling(
        self,
        run_manager,
        test_session_id
    ):
        """Test handling run errors."""
        # Create run
        run = await run_manager.create_run(
            repo_path="/test/repo",
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        # Simulate error
        error_message = "Model connection failed"
        await run_manager.mark_run_failed(
            run.id,
            error_message=error_message
        )

        updated = await run_manager.get_run(run.id)
        assert updated.status == RunStatus.FAILED
        assert updated.error_message == error_message

    async def test_run_completion_time(
        self,
        run_manager,
        test_session_id
    ):
        """Test that completion time is recorded."""
        # Create run
        run = await run_manager.create_run(
            repo_path="/test/repo",
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        # Start processing
        await run_manager.update_run_status(run.id, RunStatus.PROCESSING)

        # Complete run
        await run_manager.update_run_status(run.id, RunStatus.COMPLETED)

        updated = await run_manager.get_run(run.id)
        assert updated.completed_at is not None
        assert updated.completed_at > updated.created_at


class TestRunComparison:
    """Test comparing runs and their outputs."""

    async def test_compare_run_outputs(
        self,
        run_manager,
        test_session_id
    ):
        """Test comparing outputs from different runs."""
        repo_path = "/test/repo"

        # Create two runs
        run1 = await run_manager.create_run(
            repo_path=repo_path,
            config={"model": "llama3.2:latest", "passes": 1},
            test_session_id=test_session_id
        )

        run2 = await run_manager.create_run(
            repo_path=repo_path,
            config={"model": "llama3.2:latest", "passes": 3},
            test_session_id=test_session_id
        )

        # Generate documents for both
        await run_manager.add_generated_document(
            run_id=run1.id,
            file_path="docs/api.md",
            content="# API v1",
            doc_type="api"
        )

        await run_manager.add_generated_document(
            run_id=run2.id,
            file_path="docs/api.md",
            content="# API v2 (improved)",
            doc_type="api"
        )

        # Compare runs
        comparison = await run_manager.compare_runs(run1.id, run2.id)

        assert comparison is not None
        assert comparison["run1_id"] == run1.id
        assert comparison["run2_id"] == run2.id
        assert "documents" in comparison

    async def test_get_run_statistics(
        self,
        run_manager,
        test_session_id
    ):
        """Test getting run statistics."""
        # Create run with documents
        run = await run_manager.create_run(
            repo_path="/test/repo",
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        # Generate documents
        for i in range(5):
            await run_manager.add_generated_document(
                run_id=run.id,
                file_path=f"docs/doc{i}.md",
                content=f"# Document {i}",
                doc_type="general"
            )

        # Get statistics
        stats = await run_manager.get_run_statistics(run.id)

        assert stats["total_documents"] == 5
        assert "total_size" in stats
        assert "doc_types" in stats


class TestRunCleanup:
    """Test run cleanup and maintenance."""

    async def test_delete_old_runs(
        self,
        run_manager,
        run_repo,
        test_session_id
    ):
        """Test deleting old runs."""
        # Create old run
        old_run = await run_manager.create_run(
            repo_path="/test/repo",
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        # Manually set created_at to 31 days ago
        await run_repo.update(old_run.id, {
            "created_at": datetime.utcnow() - timedelta(days=31)
        })

        # Delete runs older than 30 days
        deleted_count = await run_manager.cleanup_old_runs(days=30)

        assert deleted_count >= 1

        # Run should be deleted
        retrieved = await run_manager.get_run(old_run.id)
        assert retrieved is None

    async def test_keep_recent_runs(
        self,
        run_manager,
        test_session_id
    ):
        """Test that recent runs are kept during cleanup."""
        # Create recent run
        recent_run = await run_manager.create_run(
            repo_path="/test/repo",
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        # Cleanup old runs
        await run_manager.cleanup_old_runs(days=30)

        # Recent run should still exist
        retrieved = await run_manager.get_run(recent_run.id)
        assert retrieved is not None


class TestRunExport:
    """Test exporting run data."""

    async def test_export_run_to_json(
        self,
        run_manager,
        test_session_id
    ):
        """Test exporting a run to JSON."""
        # Create run with documents
        run = await run_manager.create_run(
            repo_path="/test/repo",
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        await run_manager.add_generated_document(
            run_id=run.id,
            file_path="docs/api.md",
            content="# API",
            doc_type="api"
        )

        # Export to JSON
        exported = await run_manager.export_run(run.id, format="json")

        assert exported is not None
        assert "id" in exported
        assert "documents" in exported
        assert len(exported["documents"]) == 1

    async def test_export_run_to_archive(
        self,
        run_manager,
        test_session_id
    ):
        """Test exporting a run to archive (zip)."""
        # Create run with documents
        run = await run_manager.create_run(
            repo_path="/test/repo",
            config={"model": "llama3.2:latest"},
            test_session_id=test_session_id
        )

        for i in range(3):
            await run_manager.add_generated_document(
                run_id=run.id,
                file_path=f"docs/doc{i}.md",
                content=f"# Document {i}",
                doc_type="general"
            )

        # Export to archive
        archive_path = await run_manager.export_run(run.id, format="archive")

        assert archive_path is not None
        # Archive should contain all documents

