"""
Unit tests for VersionComparator service.
Tests version comparison and migration path analysis.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from src.services.maintenance.version_comparator import VersionComparator

@pytest.mark.unit
class TestComparatorInstantiation:
    def test_create_comparator(self):
        comparator = VersionComparator()
        assert comparator is not None
    
    def test_comparator_has_methods(self):
        comparator = VersionComparator()
        assert hasattr(comparator, 'compare_versions')

@pytest.mark.unit
class TestVersionComparison:
    async def test_compare_versions(self):
        comparator = VersionComparator()
        doc_id = uuid4()
        version1_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        version2_date = datetime(2024, 6, 1, tzinfo=timezone.utc)
        
        with patch.object(comparator, '_get_document_version', new_callable=AsyncMock) as mock_version:
            mock_version.side_effect = [
                {"content": "Version 1 content", "date": version1_date, "commit": "abc123"},
                {"content": "Version 2 content", "date": version2_date, "commit": "def456"}
            ]
            
            result = await comparator.compare_versions(doc_id, version1_date, version2_date)
            assert result is not None
            assert "document_id" in result

    async def test_compare_same_versions(self):
        comparator = VersionComparator()
        doc_id = uuid4()
        version_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        
        with patch.object(comparator, '_get_document_version', new_callable=AsyncMock) as mock_version:
            mock_version.return_value = {
                "content": "Same content",
                "date": version_date,
                "commit": "abc123"
            }
            
            result = await comparator.compare_versions(doc_id, version_date, version_date)
            assert result is not None

@pytest.mark.unit
class TestDiffGeneration:
    async def test_generate_unified_diff(self):
        comparator = VersionComparator()
        doc_id = uuid4()
        version1_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        version2_date = datetime(2024, 6, 1, tzinfo=timezone.utc)
        
        with patch.object(comparator, '_get_document_version', new_callable=AsyncMock) as mock_version:
            mock_version.side_effect = [
                {"content": "Old content\nLine 2", "date": version1_date},
                {"content": "New content\nLine 2", "date": version2_date}
            ]
            
            result = await comparator.compare_versions(doc_id, version1_date, version2_date)
            assert "diff" in result

    async def test_calculate_change_statistics(self):
        comparator = VersionComparator()
        doc_id = uuid4()
        version1_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        version2_date = datetime(2024, 6, 1, tzinfo=timezone.utc)
        
        with patch.object(comparator, '_get_document_version', new_callable=AsyncMock) as mock_version:
            mock_version.side_effect = [
                {"content": "Version 1", "date": version1_date},
                {"content": "Version 2", "date": version2_date}
            ]
            
            result = await comparator.compare_versions(doc_id, version1_date, version2_date)
            assert "statistics" in result

@pytest.mark.unit
class TestSemanticAnalysis:
    async def test_detect_semantic_changes(self):
        comparator = VersionComparator()
        doc_id = uuid4()
        version1_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        version2_date = datetime(2024, 6, 1, tzinfo=timezone.utc)
        
        with patch.object(comparator, '_get_document_version', new_callable=AsyncMock) as mock_version:
            mock_version.side_effect = [
                {"content": "API v1.0", "date": version1_date},
                {"content": "API v2.0 - Breaking changes", "date": version2_date}
            ]
            
            result = await comparator.compare_versions(doc_id, version1_date, version2_date)
            assert "semantic_changes" in result

    async def test_identify_breaking_changes(self):
        comparator = VersionComparator()
        doc_id = uuid4()
        version1_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        version2_date = datetime(2024, 6, 1, tzinfo=timezone.utc)
        
        with patch.object(comparator, '_get_document_version', new_callable=AsyncMock) as mock_version:
            mock_version.side_effect = [
                {"content": "Method A()", "date": version1_date},
                {"content": "Method B() - replaces A()", "date": version2_date}
            ]
            
            result = await comparator.compare_versions(doc_id, version1_date, version2_date)
            assert result is not None

@pytest.mark.unit
class TestMigrationPaths:
    async def test_identify_migration_path(self):
        comparator = VersionComparator()
        doc_id = uuid4()
        version1_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        version2_date = datetime(2024, 6, 1, tzinfo=timezone.utc)
        
        with patch.object(comparator, '_get_document_version', new_callable=AsyncMock) as mock_version:
            mock_version.side_effect = [
                {"content": "Old API", "date": version1_date},
                {"content": "New API", "date": version2_date}
            ]
            
            result = await comparator.compare_versions(doc_id, version1_date, version2_date)
            assert "metadata" in result

@pytest.mark.unit
class TestVersionErrorHandling:
    async def test_handle_missing_version(self):
        comparator = VersionComparator()
        doc_id = uuid4()
        version1_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        version2_date = datetime(2024, 6, 1, tzinfo=timezone.utc)
        
        with patch.object(comparator, '_get_document_version', new_callable=AsyncMock) as mock_version:
            mock_version.side_effect = [None, {"content": "V2", "date": version2_date}]
            
            result = await comparator.compare_versions(doc_id, version1_date, version2_date)
            assert "error" in result

    async def test_handle_comparator_error(self):
        comparator = VersionComparator()
        doc_id = uuid4()
        version1_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        version2_date = datetime(2024, 6, 1, tzinfo=timezone.utc)
        
        with patch.object(comparator, '_get_document_version', new_callable=AsyncMock) as mock_version:
            mock_version.side_effect = Exception("Version retrieval error")
            
            with pytest.raises(Exception):
                await comparator.compare_versions(doc_id, version1_date, version2_date)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])
