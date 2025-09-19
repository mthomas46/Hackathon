"""Tests for Interpreter Service Sample Documents functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add the services directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.sample_documents import SampleDocumentRepository, sample_documents


class TestSampleDocumentRepository:
    """Test the SampleDocumentRepository class."""

    def test_repository_initialization(self):
        """Test that the repository initializes correctly."""
        repo = SampleDocumentRepository()
        assert repo.documents is not None
        assert len(repo.documents) > 0
        print(f"✓ Repository initialized with {len(repo.documents)} documents")

    def test_get_documents_by_type(self):
        """Test filtering documents by type."""
        repo = SampleDocumentRepository()

        # Test getting confluence documents
        confluence_docs = repo.get_documents_by_type("confluence")
        assert all(doc.get("type") == "confluence" for doc in confluence_docs)
        print(f"✓ Found {len(confluence_docs)} confluence documents")

        # Test getting jira documents
        jira_docs = repo.get_documents_by_type("jira")
        assert all(doc.get("type") == "jira" for doc in jira_docs)
        print(f"✓ Found {len(jira_docs)} jira documents")

        # Test getting pull request documents
        pr_docs = repo.get_documents_by_type("pull_request")
        assert all(doc.get("type") == "pull_request" for doc in pr_docs)
        print(f"✓ Found {len(pr_docs)} pull request documents")

    def test_get_documents_by_category(self):
        """Test filtering documents by category."""
        repo = SampleDocumentRepository()

        # Test getting architecture documents
        arch_docs = repo.get_documents_by_category("architecture")
        assert all(doc.get("category") == "architecture" for doc in arch_docs)
        print(f"✓ Found {len(arch_docs)} architecture documents")

    def test_get_similar_documents(self):
        """Test getting similar documents."""
        repo = SampleDocumentRepository()
        similar_docs = repo.get_similar_documents()
        print(f"✓ Found {len(similar_docs)} similar documents")

    def test_get_contradictory_documents(self):
        """Test getting contradictory documents."""
        repo = SampleDocumentRepository()
        contradictory_docs = repo.get_contradictory_documents()
        print(f"✓ Found {len(contradictory_docs)} contradictory documents")

    def test_get_documents_for_query(self):
        """Test getting documents relevant to a query."""
        repo = SampleDocumentRepository()

        # Test with banking/financial query
        banking_query = "Create a banking application with user authentication"
        banking_docs = repo.get_documents_for_query(banking_query)
        assert len(banking_docs) > 0
        print(f"✓ Banking query returned {len(banking_docs)} relevant documents")

        # Test with API documentation query
        api_query = "API documentation and endpoints"
        api_docs = repo.get_documents_for_query(api_query)
        assert len(api_docs) > 0
        print(f"✓ API query returned {len(api_docs)} relevant documents")

        # Test with conflict query
        conflict_query = "documents with conflicts and contradictions"
        conflict_docs = repo.get_documents_for_query(conflict_query)
        assert len(conflict_docs) > 0
        print(f"✓ Conflict query returned {len(conflict_docs)} relevant documents")


class TestGlobalSampleDocuments:
    """Test the global sample_documents instance."""

    def test_global_instance_exists(self):
        """Test that the global sample_documents instance exists."""
        assert sample_documents is not None
        assert isinstance(sample_documents, SampleDocumentRepository)
        print("✓ Global sample_documents instance exists")

    def test_global_instance_functionality(self):
        """Test that the global instance works correctly."""
        assert len(sample_documents.get_all_documents()) > 0
        print(f"✓ Global instance has {len(sample_documents.get_all_documents())} documents")


class TestImportFunctionality:
    """Test import functionality."""

    def test_direct_import(self):
        """Test direct import of sample_documents module."""
        try:
            from modules.sample_documents import sample_documents as imported_docs
            assert imported_docs is not None
            print("✓ Direct import successful")
        except ImportError as e:
            print(f"✗ Direct import failed: {e}")
            raise

    def test_repository_import(self):
        """Test import of SampleDocumentRepository."""
        try:
            from modules.sample_documents import SampleDocumentRepository
            repo = SampleDocumentRepository()
            assert repo is not None
            print("✓ Repository import successful")
        except ImportError as e:
            print(f"✗ Repository import failed: {e}")
            raise


def run_all_tests():
    """Run all tests manually for debugging."""
    print("🧪 Running Sample Documents Tests...\n")

    # Test repository initialization
    print("1. Testing repository initialization:")
    test_repo = TestSampleDocumentRepository()
    test_repo.test_repository_initialization()

    # Test document filtering
    print("\n2. Testing document filtering:")
    test_repo.test_get_documents_by_type()
    test_repo.test_get_documents_by_category()

    # Test special collections
    print("\n3. Testing special collections:")
    test_repo.test_get_similar_documents()
    test_repo.test_get_contradictory_documents()

    # Test query matching
    print("\n4. Testing query matching:")
    test_repo.test_get_documents_for_query()

    # Test global instance
    print("\n5. Testing global instance:")
    test_global = TestGlobalSampleDocuments()
    test_global.test_global_instance_exists()
    test_global.test_global_instance_functionality()

    # Test imports
    print("\n6. Testing imports:")
    test_import = TestImportFunctionality()
    test_import.test_direct_import()
    test_import.test_repository_import()

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    run_all_tests()
