"""
Integration Tests for Temporal Versioning API

Tests full API workflows including:
- Creating versions
- Querying timelines
- As-of-date queries
- Content deduplication
- Activity summaries
"""

import pytest
import httpx
from datetime import datetime, timedelta
import json


@pytest.mark.integration
class TestTemporalVersioningAPI:
    """Integration tests for temporal versioning API endpoints."""
    
    @pytest.fixture
    def api_client(self):
        """Create HTTP client for API."""
        return httpx.Client(base_url="http://localhost:8000", timeout=30.0)
    
    def test_health_check(self, api_client):
        """Test that API is accessible."""
        response = api_client.get("/health")
        assert response.status_code == 200
    
    def test_deduplication_stats_endpoint(self, api_client):
        """Test deduplication stats endpoint."""
        response = api_client.get("/api/v1/versioning/deduplication-stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "unique_content_items" in data
        assert "total_versions" in data
        assert "space_saved" in data
        assert "deduplication_ratio" in data
        
        # Verify data types
        assert isinstance(data["unique_content_items"], int)
        assert isinstance(data["total_versions"], int)
        assert isinstance(data["space_saved"], int)
        assert isinstance(data["deduplication_ratio"], (int, float))
    
    def test_activity_summary_endpoint(self, api_client):
        """Test activity summary endpoint."""
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
        end_date = datetime.now().isoformat()
        
        response = api_client.get(
            "/api/v1/versioning/activity-summary",
            params={"start_date": start_date, "end_date": end_date}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_versions" in data
        assert "unique_documents" in data
        assert "unique_contributors" in data
        assert "activity_by_day" in data
        assert "top_contributors" in data
        
        # Verify data types
        assert isinstance(data["total_versions"], int)
        assert isinstance(data["unique_documents"], int)
        assert isinstance(data["unique_contributors"], int)
        assert isinstance(data["activity_by_day"], dict)
        assert isinstance(data["top_contributors"], dict)
    
    def test_as_of_query_endpoint(self, api_client):
        """Test 'as of' date query endpoint."""
        payload = {
            "as_of_date": datetime(2025, 10, 1).isoformat(),
            "filters": {},
            "limit": 50,
            "offset": 0
        }
        
        response = api_client.post(
            "/api/v1/versioning/as-of",
            json=payload
        )
        
        # Should return 200 even if no documents found
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "as_of_date" in data
            assert "total_documents" in data
            assert "documents" in data
            assert isinstance(data["documents"], list)
    
    def test_timeline_query_validation(self, api_client):
        """Test timeline query with invalid document ID."""
        payload = {
            "document_id": "invalid-uuid",
            "start_date": None,
            "end_date": None
        }
        
        response = api_client.post(
            "/api/v1/versioning/timeline",
            json=payload
        )
        
        # Should return 400 for invalid UUID
        assert response.status_code in [400, 422]
    
    def test_changes_query_endpoint(self, api_client):
        """Test changes between dates endpoint."""
        payload = {
            "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "limit": 100
        }
        
        response = api_client.post(
            "/api/v1/versioning/changes",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "start_date" in data
        assert "end_date" in data
        assert "total_changes" in data
        assert "changes" in data
        assert isinstance(data["changes"], list)
    
    def test_pagination(self, api_client):
        """Test pagination in as-of queries."""
        # Query with limit 10, offset 0
        payload1 = {
            "as_of_date": datetime.now().isoformat(),
            "filters": {},
            "limit": 10,
            "offset": 0
        }
        
        response1 = api_client.post(
            "/api/v1/versioning/as-of",
            json=payload1
        )
        
        # Query with limit 10, offset 10
        payload2 = {
            "as_of_date": datetime.now().isoformat(),
            "filters": {},
            "limit": 10,
            "offset": 10
        }
        
        response2 = api_client.post(
            "/api/v1/versioning/as-of",
            json=payload2
        )
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            # If there are enough documents, pages should be different
            if data1["total_documents"] > 10:
                docs1_ids = {doc["document_id"] for doc in data1["documents"]}
                docs2_ids = {doc["document_id"] for doc in data2["documents"]}
                
                # Should have different documents (no overlap)
                assert docs1_ids.isdisjoint(docs2_ids)


@pytest.mark.integration
class TestContentDeduplicationWorkflow:
    """Integration tests for content deduplication workflows."""
    
    @pytest.fixture
    def api_client(self):
        """Create HTTP client for API."""
        return httpx.Client(base_url="http://localhost:8000", timeout=30.0)
    
    def test_cleanup_unreferenced_content_dry_run(self, api_client):
        """Test cleanup in dry-run mode."""
        response = api_client.post(
            "/api/v1/versioning/content/cleanup",
            params={"dry_run": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_items" in data
        assert "total_size_bytes" in data
        assert "total_size_mb" in data
        assert "dry_run" in data
        assert "deleted" in data
        
        # In dry run, nothing should be deleted
        assert data["dry_run"] is True
        assert data["deleted"] == 0
    
    def test_content_info_nonexistent(self, api_client):
        """Test getting info for non-existent content."""
        fake_hash = "0" * 64
        
        response = api_client.get(
            f"/api/v1/versioning/content/{fake_hash}"
        )
        
        # Should return 404
        assert response.status_code == 404
    
    def test_content_integrity_verification(self, api_client):
        """Test content integrity verification."""
        fake_hash = "0" * 64
        
        response = api_client.get(
            f"/api/v1/versioning/content/{fake_hash}/verify"
        )
        
        # Should return 200 with verification result (even if content doesn't exist)
        assert response.status_code == 200
        data = response.json()
        
        assert "content_hash" in data
        assert "integrity_verified" in data
        assert isinstance(data["integrity_verified"], bool)


@pytest.mark.integration
class TestTimelineVisualization:
    """Integration tests for timeline visualization data."""
    
    @pytest.fixture
    def api_client(self):
        """Create HTTP client for API."""
        return httpx.Client(base_url="http://localhost:8000", timeout=30.0)
    
    def test_activity_by_day_format(self, api_client):
        """Test that activity_by_day returns properly formatted data."""
        response = api_client.get("/api/v1/versioning/activity-summary")
        
        if response.status_code == 200:
            data = response.json()
            activity = data.get("activity_by_day", {})
            
            # Verify all keys are date strings
            for date_str in activity.keys():
                # Should be parseable as date
                datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Verify all values are integers
            for count in activity.values():
                assert isinstance(count, int)
                assert count >= 0
    
    def test_top_contributors_format(self, api_client):
        """Test that top_contributors returns properly formatted data."""
        response = api_client.get("/api/v1/versioning/activity-summary")
        
        if response.status_code == 200:
            data = response.json()
            contributors = data.get("top_contributors", {})
            
            # Verify all keys are strings (contributor names)
            for name in contributors.keys():
                assert isinstance(name, str)
            
            # Verify all values are integers (contribution counts)
            for count in contributors.values():
                assert isinstance(count, int)
                assert count > 0


@pytest.mark.integration
class TestErrorHandling:
    """Integration tests for error handling."""
    
    @pytest.fixture
    def api_client(self):
        """Create HTTP client for API."""
        return httpx.Client(base_url="http://localhost:8000", timeout=30.0)
    
    def test_invalid_date_format(self, api_client):
        """Test handling of invalid date format."""
        payload = {
            "as_of_date": "not-a-date",
            "filters": {},
            "limit": 10,
            "offset": 0
        }
        
        response = api_client.post(
            "/api/v1/versioning/as-of",
            json=payload
        )
        
        # Should return 422 (validation error)
        assert response.status_code == 422
    
    def test_negative_pagination(self, api_client):
        """Test handling of negative pagination values."""
        payload = {
            "as_of_date": datetime.now().isoformat(),
            "filters": {},
            "limit": -10,  # Invalid
            "offset": -5   # Invalid
        }
        
        response = api_client.post(
            "/api/v1/versioning/as-of",
            json=payload
        )
        
        # Should return 422 (validation error)
        assert response.status_code == 422
    
    def test_excessive_limit(self, api_client):
        """Test handling of excessive limit values."""
        payload = {
            "as_of_date": datetime.now().isoformat(),
            "filters": {},
            "limit": 10000,  # Should be capped at 1000
            "offset": 0
        }
        
        response = api_client.post(
            "/api/v1/versioning/as-of",
            json=payload
        )
        
        # Should return 422 (validation error) due to max limit
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

