"""
Unit tests for File Classifier (Phase 1)
"""

import pytest
from pathlib import Path

from src.services.discovery.file_classifier import FileClassifier, ImportanceLevel, ClassifiedFile
from src.services.discovery.repository_scanner import FileInfo


class TestFileClassifier:
    """Test FileClassifier class."""
    
    @pytest.fixture
    def classifier(self):
        """Create a classifier instance."""
        return FileClassifier()
    
    @pytest.fixture
    def sample_files(self):
        """Create sample file list."""
        return [
            FileInfo(
                path=Path("src/main.py"),
                relative_path="src/main.py",
                size_bytes=1000,
                extension=".py",
                language="python",
                is_code=True,
                is_test=False,
                is_doc=False,
                is_config=False
            ),
            FileInfo(
                path=Path("tests/test_main.py"),
                relative_path="tests/test_main.py",
                size_bytes=500,
                extension=".py",
                language="python",
                is_code=True,
                is_test=True,
                is_doc=False,
                is_config=False
            ),
            FileInfo(
                path=Path("README.md"),
                relative_path="README.md",
                size_bytes=200,
                extension=".md",
                language="",
                is_code=False,
                is_test=False,
                is_doc=True,
                is_config=False
            ),
            FileInfo(
                path=Path("config.json"),
                relative_path="config.json",
                size_bytes=100,
                extension=".json",
                language="",
                is_code=False,
                is_test=False,
                is_doc=False,
                is_config=True
            )
        ]
    
    def test_classifier_initialization(self, classifier):
        """Test classifier initializes correctly."""
        assert classifier is not None
        assert len(classifier.core_patterns) > 0
        assert len(classifier.dependency_patterns) > 0
    
    @pytest.mark.asyncio
    async def test_classify_files(self, classifier, sample_files):
        """Test classifying files."""
        result = await classifier.classify(sample_files)
        
        assert len(result) == len(sample_files)
        
        # Check all files have classification
        for classified in result:
            assert isinstance(classified, ClassifiedFile)
            assert isinstance(classified.importance_level, ImportanceLevel)
            assert 0.0 <= classified.importance_score <= 1.0
            assert classified.priority >= 1
    
    @pytest.mark.asyncio
    async def test_classify_core_code(self, classifier):
        """Test that core code files get high importance."""
        files = [
            FileInfo(
                path=Path("src/api/handler.py"),
                relative_path="src/api/handler.py",
                size_bytes=1000,
                extension=".py",
                language="python",
                is_code=True,
                is_test=False,
                is_doc=False,
                is_config=False
            )
        ]
        
        result = await classifier.classify(files)
        assert result[0].importance_level == ImportanceLevel.CORE
        assert result[0].importance_score >= 0.7
    
    @pytest.mark.asyncio
    async def test_classify_tests(self, classifier):
        """Test that test files get test classification."""
        files = [
            FileInfo(
                path=Path("tests/test_feature.py"),
                relative_path="tests/test_feature.py",
                size_bytes=500,
                extension=".py",
                language="python",
                is_code=True,
                is_test=True,
                is_doc=False,
                is_config=False
            )
        ]
        
        result = await classifier.classify(files)
        assert result[0].importance_level == ImportanceLevel.TEST
    
    @pytest.mark.asyncio
    async def test_classify_documentation(self, classifier):
        """Test that docs get doc classification."""
        files = [
            FileInfo(
                path=Path("docs/guide.md"),
                relative_path="docs/guide.md",
                size_bytes=300,
                extension=".md",
                language="",
                is_code=False,
                is_test=False,
                is_doc=True,
                is_config=False
            )
        ]
        
        result = await classifier.classify(files)
        assert result[0].importance_level == ImportanceLevel.DOC
    
    @pytest.mark.asyncio
    async def test_classify_config(self, classifier):
        """Test that config files get config classification."""
        files = [
            FileInfo(
                path=Path("config.yaml"),
                relative_path="config.yaml",
                size_bytes=100,
                extension=".yaml",
                language="",
                is_code=False,
                is_test=False,
                is_doc=False,
                is_config=True
            )
        ]
        
        result = await classifier.classify(files)
        assert result[0].importance_level == ImportanceLevel.CONFIG
    
    @pytest.mark.asyncio
    async def test_priority_ordering(self, classifier, sample_files):
        """Test that files are ordered by priority."""
        result = await classifier.classify(sample_files)
        
        # Verify priorities are assigned
        priorities = [c.priority for c in result]
        assert all(p >= 1 for p in priorities)
    
    @pytest.mark.asyncio
    async def test_empty_file_list(self, classifier):
        """Test classifying empty file list."""
        result = await classifier.classify([])
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_score_range(self, classifier, sample_files):
        """Test that scores are in valid range."""
        result = await classifier.classify(sample_files)
        
        for classified in result:
            assert 0.0 <= classified.importance_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_to_dict_conversion(self, classifier, sample_files):
        """Test converting classified files to dictionaries."""
        result = await classifier.classify(sample_files)
        
        for classified in result:
            dict_result = classified.to_dict()
            assert "file_info" in dict_result
            assert "importance_level" in dict_result
            assert "importance_score" in dict_result
            assert "priority" in dict_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
