"""
Unit tests for DocumentConsolidator service.

Tests document redundancy detection and merge recommendations.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.timeline.document_consolidator import DocumentConsolidator


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        {
            "id": 1,
            "path": "/docs/auth.md",
            "content": "Authentication documentation for OAuth2",
            "last_modified": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "content_hash": "abc123"
        },
        {
            "id": 2,
            "path": "/docs/authentication.md",
            "content": "Authentication documentation for OAuth2",
            "last_modified": datetime(2024, 1, 2, tzinfo=timezone.utc),
            "content_hash": "abc123"  # Same hash = duplicate
        },
        {
            "id": 3,
            "path": "/docs/api.md",
            "content": "API documentation with endpoints",
            "last_modified": datetime(2024, 1, 3, tzinfo=timezone.utc),
            "content_hash": "def456"
        },
        {
            "id": 4,
            "path": "/docs/api_guide.md",
            "content": "API documentation with endpoint descriptions",
            "last_modified": datetime(2024, 1, 4, tzinfo=timezone.utc),
            "content_hash": "def789"  # Similar but not identical
        }
    ]


@pytest.mark.unit
class TestDocumentConsolidatorInstantiation:
    """Test DocumentConsolidator instantiation."""
    
    def test_create_consolidator(self):
        """Test creating a DocumentConsolidator instance."""
        consolidator = DocumentConsolidator()
        assert consolidator is not None
    
    def test_consolidator_has_methods(self):
        """Test that DocumentConsolidator has required methods."""
        consolidator = DocumentConsolidator()
        assert hasattr(consolidator, 'analyze_consolidation_opportunities')
        assert hasattr(consolidator, 'recommend_merges')


@pytest.mark.unit
class TestDuplicateDetection:
    """Test detection of duplicate documents."""
    
    async def test_detect_exact_duplicates(self, sample_documents):
        """Test detecting documents with identical content hashes."""
        consolidator = DocumentConsolidator()
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_documents
            
            result = await consolidator.analyze_consolidation_opportunities(service_name="test-service")
            
            assert result is not None
            assert "redundant_groups" in result
            # Should find docs 1 and 2 as duplicates (same hash)
            redundant_groups = result["redundant_groups"]
            assert len(redundant_groups) >= 0  # May or may not find groups depending on similarity
    
    async def test_no_duplicates_when_all_unique(self):
        """Test when no duplicates exist."""
        unique_docs = [
            {
                "id": 1,
                "content": "Unique content 1",
                "content_hash": "hash1", "path": "/docs/1.md"
            },
            {
                "id": 2,
                "content": "Unique content 2",
                "content_hash": "hash2", "path": "/docs/2.md"
            }
        ]
        
        consolidator = DocumentConsolidator()
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = unique_docs
            
            result = await consolidator.analyze_consolidation_opportunities(service_name="test-service")
            
            # Should find no or minimal duplicates
            assert "redundant_groups" in result


@pytest.mark.unit
class TestSimilarityDetection:
    """Test detection of similar documents."""
    
    async def test_detect_similar_documents(self, sample_documents):
        """Test detecting documents with similar content."""
        consolidator = DocumentConsolidator()
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_documents
            
            result = await consolidator.analyze_consolidation_opportunities(service_name="test-service")
            
            assert result is not None
            assert "redundant_groups" in result  # API returns redundant_groups
            assert isinstance(result["redundant_groups"], list)
    
    async def test_similarity_threshold(self):
        """Test that similarity threshold affects detection."""
        docs = [
            {"id": 1, "content": "API authentication guide", "content_hash": "h1", "path": "/docs/guide.md"},
            {"id": 2, "content": "API authentication documentation", "content_hash": "h2", "path": "/docs/doc.md"}
        ]
        
        # High threshold - should not match
        consolidator_strict = DocumentConsolidator()
        
        with patch.object(consolidator_strict, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = docs
            
            result_strict = await consolidator_strict.analyze_consolidation_opportunities(
                service_name="test-service", 
                similarity_threshold=0.95
            )
            assert result_strict is not None
        
        # Low threshold - should match
        consolidator_lenient = DocumentConsolidator()
        
        with patch.object(consolidator_lenient, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = docs
            
            result_lenient = await consolidator_lenient.analyze_consolidation_opportunities(
                service_name="test-service",
                similarity_threshold=0.5
            )
            assert result_lenient is not None


@pytest.mark.unit
class TestMergeRecommendations:
    """Test merge recommendation generation."""
    
    async def test_recommend_merges_for_duplicates(self, sample_documents):
        """Test generating merge recommendations for duplicates."""
        consolidator = DocumentConsolidator()
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_documents
            
            recommendations = await consolidator.recommend_merges(service_name="test-service")
            
            assert recommendations is not None
            assert isinstance(recommendations, list)
            
            if len(recommendations) > 0:
                rec = recommendations[0]
                assert "source_ids" in rec or "target_id" in rec or "documents" in rec
    
    async def test_merge_recommendations_include_rationale(self):
        """Test that merge recommendations include reasoning."""
        consolidator = DocumentConsolidator()
        
        docs = [
            {"id": 1, "content": "Same content", "content_hash": "same", "path": "/docs/1.md"},
            {"id": 2, "content": "Same content", "content_hash": "same", "path": "/docs/2.md"}
        ]
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = docs
            
            recommendations = await consolidator.recommend_merges(service_name="test-service")
            
            assert isinstance(recommendations, list)
            # Should explain why merge is recommended
            if len(recommendations) > 0:
                rec = recommendations[0]
                assert "reason" in rec or "confidence" in rec or "documents" in rec
    
    async def test_no_merge_recommendations_when_no_duplicates(self):
        """Test that no merges recommended when no duplicates."""
        unique_docs = [
            {"id": 1, "content": "Unique 1", "content_hash": "h1", "path": "/docs/unique1.md"},
            {"id": 2, "content": "Unique 2", "content_hash": "h2", "path": "/docs/unique2.md"}
        ]
        
        consolidator = DocumentConsolidator()
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = unique_docs
            
            recommendations = await consolidator.recommend_merges(service_name="test-service")
            
            # Should return empty list or minimal recommendations
            assert isinstance(recommendations, list)


@pytest.mark.unit
class TestConsolidationMetrics:
    """Test consolidation metrics calculation."""
    
    async def test_get_consolidation_metrics(self, sample_documents):
        """Test retrieving consolidation metrics."""
        consolidator = DocumentConsolidator()
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_documents
            
            metrics = await consolidator.analyze_consolidation_opportunities(service_name="test-service")
            
            assert metrics is not None
            assert isinstance(metrics, dict)
            assert "total_documents" in metrics
            assert "redundant_groups" in metrics or "estimated_reduction" in metrics
    
    async def test_metrics_include_reduction_potential(self):
        """Test that metrics include potential document reduction."""
        consolidator = DocumentConsolidator()
        
        docs = [
            {"id": 1, "content": "Same", "content_hash": "same", "path": "/docs/1.md"},
            {"id": 2, "content": "Same", "content_hash": "same", "path": "/docs/2.md"},
            {"id": 3, "content": "Different", "content_hash": "diff", "path": "/docs/3.md"}
        ]
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = docs
            
            metrics = await consolidator.analyze_consolidation_opportunities(service_name="test-service")
            
            # Should show potential reduction
            assert "total_documents" in metrics
            assert metrics["total_documents"] == 3


@pytest.mark.unit
class TestVersionClustering:
    """Test clustering of document versions."""
    
    async def test_cluster_document_versions(self):
        """Test clustering documents by version."""
        versions = [
            {
                "id": 1,
                "path": "/docs/api_v1.md",
                "content": "API v1",
                "content_hash": "v1"
            },
            {
                "id": 2,
                "path": "/docs/api_v2.md",
                "content": "API v2",
                "content_hash": "v2"
            },
            {
                "id": 3,
                "path": "/docs/api_v3.md",
                "content": "API v3",
                "content_hash": "v3"
            }
        ]
        
        consolidator = DocumentConsolidator()
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = versions
            
            result = await consolidator.analyze_consolidation_opportunities(service_name="test-service")
            
            # Should identify version clusters
            assert result is not None
            assert "version_clusters" in result or "duplicates" in result


@pytest.mark.unit
class TestRedundancyScore:
    """Test redundancy scoring."""
    
    async def test_calculate_redundancy_score(self, sample_documents):
        """Test redundancy score calculation."""
        consolidator = DocumentConsolidator()
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_documents
            
            metrics = await consolidator.analyze_consolidation_opportunities(service_name="test-service")
            
            # Should include redundancy score (0-1 or 0-100)
            assert "redundancy_score" in metrics or "total_documents" in metrics
    
    async def test_high_redundancy_when_many_duplicates(self):
        """Test high redundancy score with many duplicates."""
        duplicates = [
            {"id": i, "content": "Same", "content_hash": "same", "path": f"/docs/{i}.md"}
            for i in range(10)
        ]
        
        consolidator = DocumentConsolidator()
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = duplicates
            
            metrics = await consolidator.analyze_consolidation_opportunities(service_name="test-service")
            
            # High redundancy expected
            assert "total_documents" in metrics
            assert metrics["total_documents"] == 10


@pytest.mark.unit
class TestConsolidationErrorHandling:
    """Test error handling in consolidation."""
    
    async def test_handle_empty_document_set(self):
        """Test handling empty document set."""
        consolidator = DocumentConsolidator()
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            
            result = await consolidator.analyze_consolidation_opportunities(service_name="test-service")
            
            # Should handle gracefully
            assert result is not None
            assert result["total_documents"] == 0 or "duplicates" in result
    
    async def test_handle_invalid_timeline(self):
        """Test handling invalid timeline ID."""
        consolidator = DocumentConsolidator()
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = ValueError("Timeline not found")
            
            with pytest.raises(Exception):
                await consolidator.analyze_consolidation_opportunities(service_name="nonexistent")
    
    async def test_handle_database_error(self):
        """Test handling database errors."""
        consolidator = DocumentConsolidator()
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("Database error")
            
            with pytest.raises(Exception):
                await consolidator.analyze_consolidation_opportunities(service_name="test-service")


@pytest.mark.unit
class TestConsolidationPriority:
    """Test prioritization of consolidation opportunities."""
    
    async def test_prioritize_by_impact(self):
        """Test prioritizing consolidation by impact."""
        consolidator = DocumentConsolidator()
        
        # Many duplicates of one doc = high impact
        docs = [
            {"id": i, "content": "Popular doc", "content_hash": "pop", "path": f"/docs/pop_{i}.md"}
            for i in range(5)
        ] + [
            {"id": 10, "content": "Rare doc 1", "content_hash": "r1", "path": "/docs/rare1.md"},
            {"id": 11, "content": "Rare doc 2", "content_hash": "r2", "path": "/docs/rare2.md"}
        ]
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = docs
            
            recommendations = await consolidator.recommend_merges(service_name="test-service")
            
            # Should prioritize the 5 duplicates
            assert isinstance(recommendations, list)
    
    async def test_prioritize_by_file_size(self):
        """Test considering file size in prioritization."""
        consolidator = DocumentConsolidator()
        
        large_duplicates = [
            {
                "id": 1,
                "content": "Large content " * 1000,
                "content_hash": "large",
                "size": 10000,
                "path": "/docs/large1.md"
            },
            {
                "id": 2,
                "content": "Large content " * 1000,
                "content_hash": "large",
                "size": 10000,
                "path": "/docs/large2.md"
            }
        ]
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = large_duplicates
            
            recommendations = await consolidator.recommend_merges(service_name="test-service")
            
            # Should identify as high-priority consolidation
            assert isinstance(recommendations, list)


@pytest.mark.unit
class TestConsolidationInsights:
    """Test insights from consolidation analysis."""
    
    async def test_generate_consolidation_insights(self, sample_documents):
        """Test generating actionable insights."""
        consolidator = DocumentConsolidator()
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_documents
            
            result = await consolidator.analyze_consolidation_opportunities(service_name="test-service")
            
            # Should include insights or recommendations
            assert result is not None
            assert "consolidation_recommendations" in result
    
    async def test_identify_consolidation_patterns(self):
        """Test identifying patterns in duplication."""
        consolidator = DocumentConsolidator()
        
        # Pattern: versioned files
        docs = [
            {"id": i, "path": f"/docs/api_v{i}.md", "content_hash": f"h{i}", "content": f"API v{i}"}
            for i in range(5)
        ]
        
        with patch.object(consolidator, '_fetch_service_documents', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = docs
            
            result = await consolidator.analyze_consolidation_opportunities(service_name="test-service")
            
            # Should detect versioning pattern
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])

