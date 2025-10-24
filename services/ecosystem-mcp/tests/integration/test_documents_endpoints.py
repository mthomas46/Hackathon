"""
Integration tests for document management endpoints.

Tests document listing, retrieval, and ensures unique IDs for Streamlit compatibility.
"""

import pytest
from typing import Dict, Any
import httpx

# Skip entire module - requires running server
pytestmark = pytest.mark.skip(reason="Requires running server - end-to-end test")



class TestDocumentList:
    """Tests for listing documents."""
    
    def test_list_documents_default(self, api_base_url):
        """Test listing documents with default parameters."""
        response = httpx.get(
            f"{api_base_url}/api/v1/documents",
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "documents" in data
        assert isinstance(data["documents"], list)
    
    def test_list_documents_with_limit(self, api_base_url):
        """Test listing documents with limit parameter."""
        limit = 5
        response = httpx.get(
            f"{api_base_url}/api/v1/documents?limit={limit}",
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "documents" in data
        assert len(data["documents"]) <= limit
    
    def test_list_documents_with_offset(self, api_base_url):
        """Test listing documents with offset parameter."""
        # Get first page
        response1 = httpx.get(
            f"{api_base_url}/api/v1/documents?limit=10&offset=0",
            timeout=10.0
        )
        
        # Get second page
        response2 = httpx.get(
            f"{api_base_url}/api/v1/documents?limit=10&offset=10",
            timeout=10.0
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Documents should be different (if enough documents exist)
        if data1["documents"] and data2["documents"]:
            ids1 = {doc["id"] for doc in data1["documents"]}
            ids2 = {doc["id"] for doc in data2["documents"]}
            assert ids1 != ids2
    
    def test_documents_have_required_fields(self, api_base_url):
        """Test that documents have all required fields."""
        response = httpx.get(
            f"{api_base_url}/api/v1/documents?limit=1",
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["documents"]:
            doc = data["documents"][0]
            
            # Required fields
            assert "id" in doc
            assert "file_path" in doc
            assert "created_at" in doc
            
            # Validate types
            assert isinstance(doc["id"], str)
            assert isinstance(doc["file_path"], str)
            assert len(doc["id"]) > 0  # ID should not be empty


class TestDocumentUniqueIds:
    """
    Tests to ensure documents have unique IDs.
    
    This is critical for Streamlit widget keys to avoid duplicate key errors.
    """
    
    def test_all_documents_have_unique_ids(self, api_base_url):
        """Test that all documents have unique IDs."""
        response = httpx.get(
            f"{api_base_url}/api/v1/documents?limit=100",
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        documents = data["documents"]
        
        if len(documents) > 1:
            # Extract all IDs
            ids = [doc.get("id") for doc in documents]
            
            # Check for None/empty IDs
            assert all(doc_id is not None for doc_id in ids), "Found None IDs"
            assert all(len(str(doc_id)) > 0 for doc_id in ids), "Found empty IDs"
            
            # Check for duplicates
            unique_ids = set(ids)
            assert len(unique_ids) == len(ids), (
                f"Found duplicate IDs! Total: {len(ids)}, Unique: {len(unique_ids)}. "
                f"Duplicates: {[id for id in ids if ids.count(id) > 1]}"
            )
    
    def test_document_ids_are_valid_uuids_or_strings(self, api_base_url):
        """Test that document IDs are valid strings (preferably UUIDs)."""
        response = httpx.get(
            f"{api_base_url}/api/v1/documents?limit=10",
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for doc in data["documents"]:
            doc_id = doc.get("id")
            
            # ID must be a string
            assert isinstance(doc_id, str), f"ID is not a string: {doc_id}"
            
            # ID should not be empty
            assert len(doc_id) > 0, "ID is empty"
            
            # ID should not be a simple integer (like "1", "2", etc.)
            # which could cause collisions
            assert not doc_id.isdigit(), (
                f"ID '{doc_id}' is a simple integer which may cause collisions"
            )
    
    def test_same_document_keeps_same_id(self, api_base_url):
        """Test that fetching documents multiple times returns consistent IDs."""
        # Fetch documents twice
        response1 = httpx.get(
            f"{api_base_url}/api/v1/documents?limit=5",
            timeout=10.0
        )
        
        response2 = httpx.get(
            f"{api_base_url}/api/v1/documents?limit=5",
            timeout=10.0
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        docs1 = response1.json()["documents"]
        docs2 = response2.json()["documents"]
        
        if docs1 and docs2:
            # Create mapping of file_path -> id for both responses
            id_map1 = {doc["file_path"]: doc["id"] for doc in docs1}
            id_map2 = {doc["file_path"]: doc["id"] for doc in docs2}
            
            # Same files should have same IDs
            common_paths = set(id_map1.keys()) & set(id_map2.keys())
            
            for path in common_paths:
                assert id_map1[path] == id_map2[path], (
                    f"Document '{path}' has different IDs: "
                    f"{id_map1[path]} vs {id_map2[path]}"
                )


class TestDocumentContent:
    """Tests for document content retrieval."""
    
    def test_documents_with_content(self, api_base_url):
        """Test that documents include content when requested."""
        response = httpx.get(
            f"{api_base_url}/api/v1/documents?limit=5",
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Documents may or may not include content in list view
        # But structure should be consistent
        for doc in data["documents"]:
            assert isinstance(doc, dict)
            assert "id" in doc
            assert "file_path" in doc


class TestDocumentFiltering:
    """Tests for document filtering and search."""
    
    def test_filter_by_file_type(self, api_base_url):
        """Test filtering documents by file type if supported."""
        # Try to filter by markdown files
        response = httpx.get(
            f"{api_base_url}/api/v1/documents?limit=20",
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check if we have file type information
        if data["documents"]:
            has_file_type = any("file_type" in doc or "original_format" in doc 
                              for doc in data["documents"])
            
            if has_file_type:
                # Verify file type is consistent with file path
                for doc in data["documents"]:
                    file_path = doc["file_path"]
                    file_type = doc.get("file_type") or doc.get("original_format")
                    
                    if file_type and file_path:
                        # File extension should match file type
                        assert file_path.endswith(f".{file_type}") or \
                               file_type in file_path.lower()


class TestDocumentErrorHandling:
    """Tests for error handling in document endpoints."""
    
    def test_invalid_limit_parameter(self, api_base_url):
        """Test handling of invalid limit parameter."""
        response = httpx.get(
            f"{api_base_url}/api/v1/documents?limit=-1",
            timeout=10.0
        )
        
        # Should either reject with 422 or default to valid limit
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            data = response.json()
            # Should not return negative number of documents
            assert len(data["documents"]) >= 0
    
    def test_very_large_limit(self, api_base_url):
        """Test handling of very large limit values."""
        response = httpx.get(
            f"{api_base_url}/api/v1/documents?limit=10000",
            timeout=15.0
        )
        
        # Should either accept or reject gracefully
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            data = response.json()
            # Server may cap the limit
            assert len(data["documents"]) >= 0


class TestDocumentPagination:
    """Tests for document pagination."""
    
    def test_pagination_consistency(self, api_base_url):
        """Test that pagination returns consistent results."""
        page_size = 10
        
        # Get multiple pages
        pages = []
        for page_num in range(3):
            response = httpx.get(
                f"{api_base_url}/api/v1/documents?limit={page_size}&offset={page_num * page_size}",
                timeout=10.0
            )
            
            assert response.status_code == 200
            data = response.json()
            pages.append(data["documents"])
        
        # Collect all IDs across pages
        all_ids = []
        for page in pages:
            all_ids.extend([doc["id"] for doc in page])
        
        # No duplicates across pages
        if len(all_ids) > 1:
            assert len(all_ids) == len(set(all_ids)), "Found duplicate IDs across pages"


@pytest.mark.integration
class TestDocumentsIntegration:
    """End-to-end integration tests for document management."""
    
    def test_documents_ready_for_streamlit(self, api_base_url):
        """
        Test that documents API returns data in a format suitable for Streamlit.
        
        This ensures:
        1. All documents have unique IDs
        2. IDs are stable (same document = same ID)
        3. No None/empty IDs
        4. Structure is consistent
        """
        response = httpx.get(
            f"{api_base_url}/api/v1/documents?limit=20",
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        documents = data["documents"]
        
        # Must have documents list
        assert isinstance(documents, list)
        
        if documents:
            # Check unique IDs
            ids = [doc["id"] for doc in documents]
            assert len(ids) == len(set(ids)), "Duplicate IDs found"
            
            # Check no None/empty IDs
            assert all(doc_id for doc_id in ids), "Found None/empty IDs"
            
            # Check consistent structure
            first_doc_keys = set(documents[0].keys())
            for doc in documents:
                # All documents should have same keys
                assert set(doc.keys()) == first_doc_keys, (
                    "Inconsistent document structure"
                )
            
            # Verify we can use IDs as widget keys
            for doc in documents:
                widget_key = f"doc_content_{doc['id']}"
                
                # Key should be valid (non-empty, no special chars that break Streamlit)
                assert len(widget_key) > len("doc_content_")
                assert widget_key.isprintable()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

