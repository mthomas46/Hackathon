"""
Unit tests for TagCollection.
"""
import pytest
from ingestion.tagging import TagCollection, TagType


class TestTagCollection:
    """Unit tests for TagCollection dataclass."""
    
    def test_empty_collection(self):
        """Test creating empty collection."""
        collection = TagCollection.empty()
        
        assert len(collection.default_tags) == 0
        assert len(collection.contextual_tags) == 0
        assert len(collection.user_defined_tags) == 0
        assert collection.total_count() == 0
    
    def test_all_tags(self):
        """Test getting all tags combined."""
        collection = TagCollection(
            default_tags=["source:github", "file_type:code"],
            contextual_tags=["author:john-doe", "topic:auth"],
            user_defined_tags=["priority:high"]
        )
        
        all_tags = collection.all_tags()
        
        assert len(all_tags) == 5
        assert "source:github" in all_tags
        assert "author:john-doe" in all_tags
        assert "priority:high" in all_tags
    
    def test_unique_tags(self):
        """Test getting unique tags (with duplicates)."""
        collection = TagCollection(
            default_tags=["source:github", "source:github"],  # Duplicate
            contextual_tags=["topic:auth"],
            user_defined_tags=["priority:high", "priority:high"]  # Duplicate
        )
        
        unique = collection.unique_tags()
        
        assert len(unique) == 3
        assert "source:github" in unique
        assert "topic:auth" in unique
        assert "priority:high" in unique
    
    def test_total_count(self):
        """Test total count of unique tags."""
        collection = TagCollection(
            default_tags=["source:github", "file_type:code"],
            contextual_tags=["author:john", "topic:auth"],
            user_defined_tags=["priority:high"]
        )
        
        assert collection.total_count() == 5
    
    def test_breakdown(self):
        """Test tag breakdown by type."""
        collection = TagCollection(
            default_tags=["source:github", "file_type:code"],
            contextual_tags=["author:john", "topic:auth", "topic:api"],
            user_defined_tags=["priority:high"]
        )
        
        breakdown = collection.breakdown()
        
        assert breakdown["default"] == 2
        assert breakdown["contextual"] == 3
        assert breakdown["user_defined"] == 1
        assert breakdown["total"] == 6
    
    def test_tags_by_prefix(self):
        """Test grouping tags by prefix."""
        collection = TagCollection(
            default_tags=["source:github", "source:jira", "file_type:code"],
            contextual_tags=["author:john", "author:jane", "topic:auth"],
            user_defined_tags=["priority:high", "team:backend"]
        )
        
        by_prefix = collection.tags_by_prefix()
        
        assert len(by_prefix["source"]) == 2
        assert len(by_prefix["author"]) == 2
        assert len(by_prefix["file_type"]) == 1
        assert len(by_prefix["topic"]) == 1
        assert len(by_prefix["priority"]) == 1
        assert len(by_prefix["team"]) == 1
    
    def test_filter_by_type(self):
        """Test filtering tags by type."""
        collection = TagCollection(
            default_tags=["source:github", "file_type:code"],
            contextual_tags=["author:john", "topic:auth"],
            user_defined_tags=["priority:high"]
        )
        
        default = collection.filter_by_type(TagType.DEFAULT)
        contextual = collection.filter_by_type(TagType.CONTEXTUAL)
        user = collection.filter_by_type(TagType.USER_DEFINED)
        
        assert len(default) == 2
        assert "source:github" in default
        
        assert len(contextual) == 2
        assert "author:john" in contextual
        
        assert len(user) == 1
        assert "priority:high" in user
    
    def test_filter_by_prefix(self):
        """Test filtering tags by prefix."""
        collection = TagCollection(
            default_tags=["source:github", "source:jira"],
            contextual_tags=["author:john", "topic:auth"],
            user_defined_tags=["priority:high"]
        )
        
        source_tags = collection.filter_by_prefix("source")
        author_tags = collection.filter_by_prefix("author")
        
        assert len(source_tags) == 2
        assert all(t.startswith("source:") for t in source_tags)
        
        assert len(author_tags) == 1
        assert "author:john" in author_tags
    
    def test_add_tags(self):
        """Test adding tags to collection."""
        collection = TagCollection.empty()
        
        collection.add_tags(["source:github"], TagType.DEFAULT)
        collection.add_tags(["author:john"], TagType.CONTEXTUAL)
        collection.add_tags(["priority:high"], TagType.USER_DEFINED)
        
        assert len(collection.default_tags) == 1
        assert len(collection.contextual_tags) == 1
        assert len(collection.user_defined_tags) == 1
    
    def test_merge(self):
        """Test merging two collections."""
        collection1 = TagCollection(
            default_tags=["source:github"],
            contextual_tags=["author:john"],
            user_defined_tags=["priority:high"]
        )
        
        collection2 = TagCollection(
            default_tags=["source:jira"],
            contextual_tags=["author:jane"],
            user_defined_tags=["team:backend"]
        )
        
        collection1.merge(collection2)
        
        assert len(collection1.default_tags) == 2
        assert len(collection1.contextual_tags) == 2
        assert len(collection1.user_defined_tags) == 2
    
    def test_deduplicate(self):
        """Test removing duplicates."""
        collection = TagCollection(
            default_tags=["source:github", "source:github", "file_type:code"],
            contextual_tags=["author:john", "author:john"],
            user_defined_tags=["priority:high", "priority:high", "priority:high"]
        )
        
        collection.deduplicate()
        
        assert len(collection.default_tags) == 2
        assert len(collection.contextual_tags) == 1
        assert len(collection.user_defined_tags) == 1
    
    def test_to_dict(self):
        """Test exporting to dictionary."""
        collection = TagCollection(
            default_tags=["source:github"],
            contextual_tags=["author:john"],
            user_defined_tags=["priority:high"]
        )
        
        data = collection.to_dict()
        
        assert "default" in data
        assert "contextual" in data
        assert "user_defined" in data
        assert "breakdown" in data
        assert "by_prefix" in data
        
        assert data["breakdown"]["total"] == 3
    
    def test_from_dict(self):
        """Test creating collection from dictionary."""
        data = {
            "default": ["source:github", "file_type:code"],
            "contextual": ["author:john"],
            "user_defined": ["priority:high"]
        }
        
        collection = TagCollection.from_dict(data)
        
        assert len(collection.default_tags) == 2
        assert len(collection.contextual_tags) == 1
        assert len(collection.user_defined_tags) == 1
    
    def test_to_summary(self):
        """Test creating human-readable summary."""
        collection = TagCollection(
            default_tags=["source:github", "file_type:code"],
            contextual_tags=["author:john", "topic:auth"],
            user_defined_tags=["priority:high"]
        )
        
        summary = collection.to_summary()
        
        assert "Tag Collection Summary" in summary
        assert "Total unique tags: 5" in summary
        assert "Default tags: 2" in summary
        assert "Contextual tags: 2" in summary
        assert "User-defined tags: 1" in summary
    
    def test_tags_without_prefix(self):
        """Test handling tags without prefix."""
        collection = TagCollection(
            default_tags=["nosource"],  # No prefix
            contextual_tags=["author:john"],
            user_defined_tags=["priority:high"]
        )
        
        by_prefix = collection.tags_by_prefix()
        
        assert "other" in by_prefix
        assert "nosource" in by_prefix["other"]
    
    def test_empty_breakdown(self):
        """Test breakdown of empty collection."""
        collection = TagCollection.empty()
        
        breakdown = collection.breakdown()
        
        assert breakdown["default"] == 0
        assert breakdown["contextual"] == 0
        assert breakdown["user_defined"] == 0
        assert breakdown["total"] == 0
    
    @pytest.mark.parametrize("tag_type,expected_list", [
        (TagType.DEFAULT, ["source:github", "file_type:code"]),
        (TagType.CONTEXTUAL, ["author:john"]),
        (TagType.USER_DEFINED, ["priority:high"])
    ])
    def test_filter_by_type_parameterized(self, tag_type, expected_list):
        """Test filtering by type with various inputs."""
        collection = TagCollection(
            default_tags=["source:github", "file_type:code"],
            contextual_tags=["author:john"],
            user_defined_tags=["priority:high"]
        )
        
        filtered = collection.filter_by_type(tag_type)
        
        assert len(filtered) == len(expected_list)
        for tag in expected_list:
            assert tag in filtered

