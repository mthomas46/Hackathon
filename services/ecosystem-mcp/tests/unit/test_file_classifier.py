"""
Unit tests for File Classifier (Phase 1)
"""

import pytest
from src.services.discovery.file_classifier import FileClassifier


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
            {
                "path": "src/main.py",
                "size": 1000,
                "file_type": "python",
                "language": "python"
            },
            {
                "path": "tests/test_main.py",
                "size": 500,
                "file_type": "python",
                "language": "python"
            },
            {
                "path": "README.md",
                "size": 200,
                "file_type": "markdown",
                "language": None
            },
            {
                "path": "docs/api.md",
                "size": 300,
                "file_type": "markdown",
                "language": None
            },
            {
                "path": "config.json",
                "size": 100,
                "file_type": "json",
                "language": None
            }
        ]
    
    def test_classifier_initialization(self, classifier):
        """Test classifier initializes correctly."""
        assert classifier is not None
    
    def test_classify_files(self, classifier, sample_files):
        """Test classifying files."""
        result = classifier.classify(sample_files)
        
        assert "success" is True
        assert len(result) == len(sample_files)
        
        # Check all files have classification
        for file_info in result:
            assert "importance_level" in file_info
            assert "importance_score" in file_info
            assert "priority" in file_info
    
    def test_classify_core_code(self, classifier):
        """Test that core code files get high importance."""
        files = [
            {
                "path": "src/core/engine.py",
                "size": 1000,
                "file_type": "python",
                "language": "python"
            }
        ]
        
        result = classifier.classify(files)
        assert result[0]["importance_level"] in ["critical", "high"]
        assert result[0]["importance_score"] >= 7
    
    def test_classify_tests(self, classifier):
        """Test that test files get medium importance."""
        files = [
            {
                "path": "tests/test_feature.py",
                "size": 500,
                "file_type": "python",
                "language": "python"
            }
        ]
        
        result = classifier.classify(files)
        assert result[0]["importance_level"] == "medium"
        assert 4 <= result[0]["importance_score"] < 7
    
    def test_classify_documentation(self, classifier):
        """Test that docs get low importance."""
        files = [
            {
                "path": "docs/guide.md",
                "size": 300,
                "file_type": "markdown",
                "language": None
            }
        ]
        
        result = classifier.classify(files)
        assert result[0]["importance_level"] == "low"
        assert result[0]["importance_score"] < 4
    
    def test_calculate_score_by_path(self, classifier):
        """Test score calculation based on path."""
        # Core source file
        score1 = classifier._calculate_score({
            "path": "src/main.py",
            "size": 1000,
            "file_type": "python"
        })
        
        # Test file
        score2 = classifier._calculate_score({
            "path": "tests/test.py",
            "size": 1000,
            "file_type": "python"
        })
        
        # Doc file
        score3 = classifier._calculate_score({
            "path": "docs/readme.md",
            "size": 1000,
            "file_type": "markdown"
        })
        
        assert score1 > score2 > score3
    
    def test_calculate_score_by_size(self, classifier):
        """Test that larger files get higher scores."""
        score1 = classifier._calculate_score({
            "path": "src/large.py",
            "size": 10000,
            "file_type": "python"
        })
        
        score2 = classifier._calculate_score({
            "path": "src/small.py",
            "size": 100,
            "file_type": "python"
        })
        
        assert score1 > score2
    
    def test_get_importance_level(self, classifier):
        """Test importance level assignment."""
        assert classifier._get_importance_level(9) == "critical"
        assert classifier._get_importance_level(7) == "high"
        assert classifier._get_importance_level(5) == "medium"
        assert classifier._get_importance_level(3) == "low"
        assert classifier._get_importance_level(1) == "minimal"
    
    def test_get_priority(self, classifier):
        """Test priority assignment."""
        assert classifier._get_priority("critical") == 1
        assert classifier._get_priority("high") == 2
        assert classifier._get_priority("medium") == 3
        assert classifier._get_priority("low") == 4
        assert classifier._get_priority("minimal") == 5
    
    def test_empty_file_list(self, classifier):
        """Test classifying empty file list."""
        result = classifier.classify([])
        assert len(result) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

