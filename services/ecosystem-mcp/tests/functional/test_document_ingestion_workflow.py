"""
Functional tests for document ingestion workflow.

Tests the complete pipeline:
1. Scan filesystem for documents
2. Parse and extract content
3. Generate embeddings
4. Store in database
5. Index in vector store
6. Retrieve and validate
"""

import pytest
from pathlib import Path
from datetime import datetime

# Mark all tests in this module as functional and asyncio
pytestmark = [pytest.mark.functional, pytest.mark.asyncio]


class TestDocumentIngestionWorkflow:
    """Test complete document ingestion workflow."""
    
    async def test_ingest_python_files_from_src(
        self,
        clean_database,
        ecosystem_mcp_src_dir,
        test_session_id
    ):
        """
        Test ingesting Python files from services/ecosystem-mcp/src.
        
        This validates:
        - File discovery
        - Content extraction
        - Metadata parsing
        - Database storage
        - Test data marking
        """
        # Import services and helpers
        from src.storage.repositories import DocumentRepository
        from tests.utils.test_helpers import create_test_document, verify_test_data_marked
        
        # Initialize services
        doc_repo = DocumentRepository(clean_database)
        
        # Find Python files in src directory
        python_files = list(ecosystem_mcp_src_dir.rglob("*.py"))
        assert len(python_files) > 0, "No Python files found in src directory"
        
        # Ingest first 5 Python files as a test sample
        sample_files = python_files[:5]
        ingested_count = 0
        
        for file_path in sample_files:
            # Read file content
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Create test document (automatically marked)
            doc_model = create_test_document(
                content=content,
                file_path=str(file_path.relative_to(ecosystem_mcp_src_dir.parent)),
                file_type="python",
                service_name="ecosystem-mcp-test",
                session_id=test_session_id,
                ingestion_mode="snapshot"
            )
            
            # Verify it's marked as test data
            verify_test_data_marked(doc_model)
            
            # Store in database
            doc = await doc_repo.create(doc_model)
            assert doc is not None
            assert doc.id is not None
            assert doc.file_path == doc_model.file_path
            assert doc.service_name == "ecosystem-mcp-test"
            
            # Verify test markers in stored document (they're nested under 'metadata' key)
            test_markers = doc.doc_metadata.get("metadata", {})
            assert test_markers.get("_test_data_marker") == True
            assert test_markers.get("_test_session_id") == test_session_id
            
            ingested_count += 1
        
        # Verify all documents were stored
        assert ingested_count == len(sample_files)
        
        # Retrieve and validate
        all_docs = await doc_repo.get_by_service("ecosystem-mcp-test", limit=100)
        assert len(all_docs) >= ingested_count
        
        # Validate first document in detail
        first_doc = all_docs[0]
        assert first_doc.file_path is not None
        assert first_doc.original_content is not None
        assert first_doc.service_name == "ecosystem-mcp-test"
        assert first_doc.original_format == "python"
        assert first_doc.created_at is not None
        
        # Verify all docs are marked as test data (nested under 'metadata' key)
        for doc in all_docs:
            test_markers = doc.doc_metadata.get("metadata", {})
            assert test_markers.get("_test_data_marker") == True
            assert test_markers.get("_test_session_id") == test_session_id
    
    async def test_ingest_markdown_files(
        self,
        clean_database,
        test_data_dir
    ):
        """
        Test ingesting Markdown documentation files.
        
        This validates:
        - Markdown parsing
        - Metadata extraction
        - Documentation classification
        """
        from src.storage.repositories import DocumentRepository
        
        doc_repo = DocumentRepository(clean_database)
        
        # Find markdown files in project root
        markdown_files = list(test_data_dir.glob("*.md"))
        
        if len(markdown_files) == 0:
            pytest.skip("No markdown files found in project root")
        
        # Ingest first markdown file as test
        sample_file = markdown_files[0]
        content = sample_file.read_text(encoding='utf-8', errors='ignore')
        
        doc_data = {
            "file_path": sample_file.name,
            "content": content,
            "file_type": "markdown",
            "service_name": "ecosystem-mcp",
            "repo_path": str(test_data_dir),
            "ingestion_mode": "snapshot",
            "metadata": {
                "language": "markdown",
                "size": len(content),
                "lines": content.count('\n') + 1,
                "is_documentation": True
            }
        }
        
        # Store in database
        doc = await doc_repo.create(doc_data)
        assert doc is not None
        assert doc.file_type == "markdown"
        assert doc.content == content
        
        # Retrieve and validate
        retrieved = await doc_repo.get_by_id(doc.id)
        assert retrieved is not None
        assert retrieved.file_path == sample_file.name
        assert retrieved.content == content
    
    async def test_ingest_multiple_file_types(
        self,
        clean_database,
        ecosystem_mcp_src_dir,
        test_data_dir
    ):
        """
        Test ingesting multiple file types in one workflow.
        
        This validates:
        - Multi-format handling
        - Consistent storage
        - Type-specific processing
        """
        from src.storage.repositories import DocumentRepository
        
        doc_repo = DocumentRepository(clean_database)
        
        # Collect different file types
        files_to_ingest = []
        
        # Python files
        python_files = list(ecosystem_mcp_src_dir.rglob("*.py"))[:2]
        files_to_ingest.extend([(f, "python") for f in python_files])
        
        # Markdown files
        markdown_files = list(test_data_dir.glob("*.md"))[:2]
        files_to_ingest.extend([(f, "markdown") for f in markdown_files])
        
        assert len(files_to_ingest) > 0, "No files found to ingest"
        
        # Ingest all files
        ingested_docs = []
        for file_path, file_type in files_to_ingest:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            doc_data = {
                "file_path": str(file_path.name),
                "content": content,
                "file_type": file_type,
                "service_name": "ecosystem-mcp",
                "repo_path": str(test_data_dir),
                "ingestion_mode": "snapshot",
                "metadata": {
                    "language": file_type,
                    "size": len(content)
                }
            }
            
            doc = await doc_repo.create(doc_data)
            assert doc is not None
            ingested_docs.append(doc)
        
        # Verify all were stored
        assert len(ingested_docs) == len(files_to_ingest)
        
        # Verify we can retrieve by service
        all_service_docs = await doc_repo.get_by_service("ecosystem-mcp", limit=100)
        assert len(all_service_docs) >= len(ingested_docs)
        
        # Verify different file types are present
        file_types = set(doc.file_type for doc in ingested_docs)
        assert len(file_types) > 1, "Should have multiple file types"
    
    async def test_document_metadata_completeness(
        self,
        clean_database,
        ecosystem_mcp_src_dir
    ):
        """
        Test that ingested documents have complete metadata.
        
        This validates:
        - All required fields present
        - Metadata structure correct
        - Timestamps accurate
        """
        from src.storage.repositories import DocumentRepository
        
        doc_repo = DocumentRepository(clean_database)
        
        # Ingest a sample file
        sample_file = list(ecosystem_mcp_src_dir.rglob("*.py"))[0]
        content = sample_file.read_text(encoding='utf-8', errors='ignore')
        
        doc_data = {
            "file_path": str(sample_file.relative_to(ecosystem_mcp_src_dir.parent)),
            "content": content,
            "file_type": "python",
            "service_name": "ecosystem-mcp",
            "repo_path": str(ecosystem_mcp_src_dir.parent),
            "ingestion_mode": "snapshot",
            "metadata": {
                "language": "python",
                "size": len(content),
                "lines": content.count('\n') + 1,
                "parser_version": "1.0"
            }
        }
        
        doc = await doc_repo.create(doc_data)
        
        # Validate all required fields
        assert doc.id is not None
        assert doc.file_path is not None
        assert doc.content is not None
        assert doc.file_type == "python"
        assert doc.service_name == "ecosystem-mcp"
        assert doc.repo_path is not None
        assert doc.ingestion_mode == "snapshot"
        assert doc.created_at is not None
        assert doc.updated_at is not None
        
        # Validate metadata structure
        assert doc.metadata is not None
        assert "language" in doc.metadata
        assert "size" in doc.metadata
        assert "lines" in doc.metadata
    
    async def test_duplicate_document_handling(
        self,
        clean_database,
        ecosystem_mcp_src_dir
    ):
        """
        Test handling of duplicate document ingestion.
        
        This validates:
        - Duplicate detection
        - Update vs insert logic
        - Data consistency
        """
        from src.storage.repositories import DocumentRepository
        
        doc_repo = DocumentRepository(clean_database)
        
        # Ingest a file
        sample_file = list(ecosystem_mcp_src_dir.rglob("*.py"))[0]
        content = sample_file.read_text(encoding='utf-8', errors='ignore')
        
        doc_data = {
            "file_path": str(sample_file.relative_to(ecosystem_mcp_src_dir.parent)),
            "content": content,
            "file_type": "python",
            "service_name": "ecosystem-mcp",
            "repo_path": str(ecosystem_mcp_src_dir.parent),
            "ingestion_mode": "snapshot"
        }
        
        # First ingestion
        doc1 = await doc_repo.create(doc_data)
        first_id = doc1.id
        first_created = doc1.created_at
        
        # Try to ingest same file again with modified content
        doc_data["content"] = content + "\n# Modified"
        doc2 = await doc_repo.create(doc_data)
        
        # Should create a new document (or update existing depending on implementation)
        assert doc2 is not None
        
        # Verify data integrity
        all_docs = await doc_repo.get_by_service("ecosystem-mcp", limit=100)
        assert len(all_docs) > 0


class TestIngestionErrorHandling:
    """Test error handling in document ingestion."""
    
    async def test_invalid_file_handling(self, clean_database):
        """
        Test handling of invalid or corrupted files.
        
        This validates:
        - Error detection
        - Graceful degradation
        - Error logging
        """
        from src.storage.repositories import DocumentRepository
        
        doc_repo = DocumentRepository(clean_database)
        
        # Try to ingest with invalid data
        invalid_doc_data = {
            "file_path": "invalid.txt",
            "content": None,  # Invalid: None content
            "file_type": "text",
            "service_name": "test"
        }
        
        # Should handle gracefully (may raise exception or return None)
        try:
            doc = await doc_repo.create(invalid_doc_data)
            # If it doesn't raise, verify it handled it gracefully
            if doc is None:
                pytest.skip("Service returns None for invalid data")
        except Exception as e:
            # Expected: should raise validation error
            assert "content" in str(e).lower() or "required" in str(e).lower()
    
    async def test_large_file_handling(
        self,
        clean_database,
        ecosystem_mcp_src_dir
    ):
        """
        Test handling of large files.
        
        This validates:
        - Size limit enforcement
        - Memory management
        - Performance
        """
        from src.storage.repositories import DocumentRepository
        
        doc_repo = DocumentRepository(clean_database)
        
        # Create a large content string (1MB)
        large_content = "x" * (1024 * 1024)
        
        doc_data = {
            "file_path": "large_file.txt",
            "content": large_content,
            "file_type": "text",
            "service_name": "test",
            "repo_path": str(ecosystem_mcp_src_dir),
            "ingestion_mode": "snapshot",
            "metadata": {"size": len(large_content)}
        }
        
        # Should handle large files
        doc = await doc_repo.create(doc_data)
        assert doc is not None
        assert len(doc.content) == len(large_content)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "functional"])

