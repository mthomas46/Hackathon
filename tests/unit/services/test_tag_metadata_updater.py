"""
Unit tests for TagMetadataUpdater.

Tests tag collection metadata creation and management for MCP instances.
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add services directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'mcp-training-coordinator'))

from application.tag_metadata_updater import TagMetadataUpdater


class TestTagMetadataUpdater:
    """Tests for TagMetadataUpdater class."""
    
    def test_create_tag_metadata_basic(self):
        """Test basic tag metadata creation."""
        default_tags = ["source:wikipedia", "file_type:document"]
        contextual_tags = ["character:horus", "location:terra"]
        user_tags = ["domain:warhammer", "project:test"]
        
        metadata = TagMetadataUpdater.create_tag_metadata(
            default_tags, contextual_tags, user_tags
        )
        
        assert metadata["total_count"] == 6
        assert len(metadata["default_tags"]) == 2
        assert len(metadata["contextual_tags"]) == 2
        assert len(metadata["user_defined_tags"]) == 2
        assert metadata["breakdown"]["default"] == 2
        assert metadata["breakdown"]["contextual"] == 2
        assert metadata["breakdown"]["user_defined"] == 2
        assert "last_updated" in metadata
    
    def test_create_tag_metadata_with_duplicates(self):
        """Test tag metadata creation with duplicate tags."""
        default_tags = ["source:wikipedia", "source:wikipedia", "file_type:document"]
        contextual_tags = ["character:horus", "character:horus"]
        user_tags = ["domain:test"]
        
        metadata = TagMetadataUpdater.create_tag_metadata(
            default_tags, contextual_tags, user_tags
        )
        
        # Should deduplicate
        assert metadata["total_count"] == 4
        assert len(metadata["default_tags"]) == 2
        assert len(metadata["contextual_tags"]) == 1
    
    def test_create_tag_metadata_empty(self):
        """Test tag metadata creation with empty lists."""
        metadata = TagMetadataUpdater.create_tag_metadata([], [], [])
        
        assert metadata["total_count"] == 0
        assert len(metadata["default_tags"]) == 0
        assert metadata["breakdown"]["total"] == 0
    
    def test_merge_tag_metadata(self):
        """Test merging new tags into existing metadata."""
        existing = {
            "default_tags": ["source:wikipedia"],
            "contextual_tags": ["character:horus"],
            "user_defined_tags": ["domain:test"],
            "total_count": 3
        }
        
        new_tags = {
            "default_tags": ["file_type:document"],
            "contextual_tags": ["location:terra"],
            "user_defined_tags": ["project:test"]
        }
        
        merged = TagMetadataUpdater.merge_tag_metadata(existing, new_tags)
        
        assert merged["total_count"] == 6
        assert "source:wikipedia" in merged["default_tags"]
        assert "file_type:document" in merged["default_tags"]
        assert "character:horus" in merged["contextual_tags"]
        assert "location:terra" in merged["contextual_tags"]
    
    def test_merge_tag_metadata_no_duplicates(self):
        """Test that merging doesn't create duplicates."""
        existing = {
            "default_tags": ["source:wikipedia"],
            "contextual_tags": ["character:horus"],
            "user_defined_tags": []
        }
        
        new_tags = {
            "default_tags": ["source:wikipedia"],  # Duplicate
            "contextual_tags": ["character:emperor"],
            "user_defined_tags": []
        }
        
        merged = TagMetadataUpdater.merge_tag_metadata(existing, new_tags)
        
        # Should not duplicate
        assert merged["total_count"] == 3
        assert merged["default_tags"].count("source:wikipedia") == 1
    
    def test_extract_tag_collection_from_documents(self):
        """Test extracting tag collection from documents."""
        documents = [
            {
                "tags": [
                    "source:wikipedia",
                    "file_type:document",
                    "character:horus",
                    "domain:test"
                ]
            },
            {
                "tags": [
                    "source:fandom",
                    "location:terra",
                    "project:test"
                ]
            }
        ]
        
        collection = TagMetadataUpdater.extract_tag_collection(documents)
        
        assert "source:wikipedia" in collection["default_tags"]
        assert "source:fandom" in collection["default_tags"]
        assert "character:horus" in collection["contextual_tags"]
        assert "location:terra" in collection["contextual_tags"]
        assert "domain:test" in collection["user_defined_tags"]
        assert "project:test" in collection["user_defined_tags"]
    
    def test_extract_tag_collection_empty(self):
        """Test extracting from empty document list."""
        collection = TagMetadataUpdater.extract_tag_collection([])
        
        assert len(collection["default_tags"]) == 0
        assert len(collection["contextual_tags"]) == 0
        assert len(collection["user_defined_tags"]) == 0
    
    def test_get_tag_summary(self):
        """Test generating tag summary."""
        metadata = {
            "breakdown": {
                "total": 10,
                "default": 3,
                "contextual": 5,
                "user_defined": 2
            },
            "last_updated": "2025-01-01T00:00:00"
        }
        
        summary = TagMetadataUpdater.get_tag_summary(metadata)
        
        assert "Total Unique Tags: 10" in summary
        assert "Default Tags: 3" in summary
        assert "Contextual Tags: 5" in summary
        assert "User-Defined Tags: 2" in summary
        assert "2025-01-01" in summary
    
    def test_validate_tag_metadata_valid(self):
        """Test validation of valid tag metadata."""
        metadata = {
            "default_tags": [],
            "contextual_tags": [],
            "user_defined_tags": [],
            "breakdown": {
                "default": 0,
                "contextual": 0,
                "user_defined": 0,
                "total": 0
            }
        }
        
        assert TagMetadataUpdater.validate_tag_metadata(metadata) is True
    
    def test_validate_tag_metadata_missing_keys(self):
        """Test validation fails with missing keys."""
        metadata = {
            "default_tags": [],
            "contextual_tags": []
            # Missing user_defined_tags and breakdown
        }
        
        assert TagMetadataUpdater.validate_tag_metadata(metadata) is False
    
    def test_validate_tag_metadata_invalid_breakdown(self):
        """Test validation fails with invalid breakdown."""
        metadata = {
            "default_tags": [],
            "contextual_tags": [],
            "user_defined_tags": [],
            "breakdown": {
                "default": 0
                # Missing other breakdown keys
            }
        }
        
        assert TagMetadataUpdater.validate_tag_metadata(metadata) is False
    
    def test_statistics_field(self):
        """Test that statistics field is included."""
        metadata = TagMetadataUpdater.create_tag_metadata(
            ["tag1", "tag2"],
            ["tag3"],
            []
        )
        
        assert "statistics" in metadata
        assert metadata["statistics"]["unique_default"] == 2
        assert metadata["statistics"]["unique_contextual"] == 1
        assert metadata["statistics"]["total_unique"] == 3

