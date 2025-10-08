"""
Unit tests for UniversalTaggingManager.
"""
import pytest
from ingestion.tagging import UniversalTaggingManager, UniversalTaggingConfig, TagCollection
from ingestion.models import NormalizedDocument


class TestUniversalTaggingManager:
    """Unit tests for UniversalTaggingManager."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.config = UniversalTaggingConfig(
            enable_user_tags=True,
            user_tags=["priority:high", "team:backend"],
            enable_preprocessing=False  # No corpus analysis for now
        )
        self.manager = UniversalTaggingManager(self.config)
    
    @pytest.mark.asyncio
    async def test_tag_documents_github(self):
        """Test tagging GitHub documents."""
        docs = [
            NormalizedDocument(
                document_id="doc1",
                title="auth.py",
                content_md="# Authentication Module",
                original_format="python",
                metadata={"file_type": "code", "language": "python"},
                tags=[]
            )
        ]
        
        tagged_docs, tag_collection = await self.manager.tag_documents(
            documents=docs,
            source_type='github'
        )
        
        assert len(tagged_docs) == 1
        doc = tagged_docs[0]
        
        # Should have base tags
        assert any(tag.startswith("source:") for tag in doc.tags)
        assert "source:github" in doc.tags
        assert "file_type:code" in doc.tags
        assert "language:python" in doc.tags
        
        # Should have user tags
        assert "priority:high" in doc.tags
        assert "team:backend" in doc.tags
    
    @pytest.mark.asyncio
    async def test_tag_documents_wikipedia(self):
        """Test tagging Wikipedia documents."""
        docs = [
            NormalizedDocument(
                document_id="doc1",
                title="Machine Learning",
                content_md="# Machine Learning Overview",
                original_format="wikipedia",
                metadata={"file_type": "document"},
                tags=[]
            )
        ]
        
        tagged_docs, tag_collection = await self.manager.tag_documents(
            documents=docs,
            source_type='wikipedia'
        )
        
        doc = tagged_docs[0]
        
        assert "source:wikipedia" in doc.tags
        assert "file_type:document" in doc.tags
    
    @pytest.mark.asyncio
    async def test_tag_enrichment_not_replacement(self):
        """Test that tags enrich but don't replace existing tags."""
        docs = [
            NormalizedDocument(
                document_id="doc1",
                title="test.py",
                content_md="# Test",
                original_format="python",
                metadata={"file_type": "code"},
                tags=["existing:tag", "another:tag"]  # Pre-existing tags
            )
        ]
        
        tagged_docs, _ = await self.manager.tag_documents(
            documents=docs,
            source_type='github'
        )
        
        doc = tagged_docs[0]
        
        # Pre-existing tags should still be there
        assert "existing:tag" in doc.tags
        assert "another:tag" in doc.tags
        
        # New tags should be added
        assert "source:github" in doc.tags
        assert "file_type:code" in doc.tags
    
    @pytest.mark.asyncio
    async def test_tag_deduplication(self):
        """Test that duplicate tags are removed."""
        docs = [
            NormalizedDocument(
                document_id="doc1",
                title="test.py",
                content_md="# Test",
                original_format="python",
                metadata={"file_type": "code"},
                tags=["source:github", "file_type:code"]  # Duplicates of what will be added
            )
        ]
        
        tagged_docs, _ = await self.manager.tag_documents(
            documents=docs,
            source_type='github'
        )
        
        doc = tagged_docs[0]
        
        # Should have only one of each tag
        assert doc.tags.count("source:github") == 1
        assert doc.tags.count("file_type:code") == 1
    
    @pytest.mark.asyncio
    async def test_tag_collection_building(self):
        """Test that TagCollection is built correctly."""
        docs = [
            NormalizedDocument(
                document_id="doc1",
                title="test.py",
                content_md="# Test",
                original_format="python",
                metadata={"file_type": "code", "language": "python"},
                tags=[]
            )
        ]
        
        _, tag_collection = await self.manager.tag_documents(
            documents=docs,
            source_type='github'
        )
        
        assert isinstance(tag_collection, TagCollection)
        assert len(tag_collection.default_tags) > 0
        assert len(tag_collection.user_defined_tags) > 0
        
        # Should have source, file_type in default
        assert any("source:" in t for t in tag_collection.default_tags)
        assert any("file_type:" in t for t in tag_collection.default_tags)
        
        # Should have user tags
        assert "priority:high" in tag_collection.user_defined_tags
        assert "team:backend" in tag_collection.user_defined_tags
    
    @pytest.mark.asyncio
    async def test_timestamp_tags(self):
        """Test that timestamp presence tags are added."""
        docs = [
            NormalizedDocument(
                document_id="doc1",
                title="test.py",
                content_md="# Test",
                original_format="python",
                metadata={
                    "file_type": "code",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-02T00:00:00Z"
                },
                tags=[]
            )
        ]
        
        tagged_docs, _ = await self.manager.tag_documents(
            documents=docs,
            source_type='github'
        )
        
        doc = tagged_docs[0]
        
        assert "has_created_date:true" in doc.tags
        assert "has_updated_date:true" in doc.tags
    
    @pytest.mark.asyncio
    async def test_no_user_tags(self):
        """Test tagging without user tags."""
        config = UniversalTaggingConfig(
            enable_user_tags=False,
            user_tags=[]
        )
        manager = UniversalTaggingManager(config)
        
        docs = [
            NormalizedDocument(
                document_id="doc1",
                title="test.py",
                content_md="# Test",
                original_format="python",
                metadata={"file_type": "code"},
                tags=[]
            )
        ]
        
        tagged_docs, tag_collection = await manager.tag_documents(
            documents=docs,
            source_type='github'
        )
        
        # Should have no user-defined tags
        assert len(tag_collection.user_defined_tags) == 0
    
    @pytest.mark.asyncio
    async def test_custom_user_tags(self):
        """Test passing custom user tags at runtime."""
        docs = [
            NormalizedDocument(
                document_id="doc1",
                title="test.py",
                content_md="# Test",
                original_format="python",
                metadata={"file_type": "code"},
                tags=[]
            )
        ]
        
        custom_tags = ["sprint:23", "feature:auth"]
        
        tagged_docs, tag_collection = await self.manager.tag_documents(
            documents=docs,
            source_type='github',
            user_tags=custom_tags
        )
        
        doc = tagged_docs[0]
        
        # Should have custom tags
        assert "sprint:23" in doc.tags
        assert "feature:auth" in doc.tags
    
    @pytest.mark.asyncio
    async def test_tag_metadata_in_document(self):
        """Test that tag metadata is added to documents."""
        docs = [
            NormalizedDocument(
                document_id="doc1",
                title="test.py",
                content_md="# Test",
                original_format="python",
                metadata={"file_type": "code"},
                tags=[]
            )
        ]
        
        tagged_docs, _ = await self.manager.tag_documents(
            documents=docs,
            source_type='github'
        )
        
        doc = tagged_docs[0]
        
        # Should have tag metadata
        assert 'tag_count' in doc.metadata
        assert 'tag_types' in doc.metadata
        assert 'has_user_tags' in doc.metadata
        assert 'user_tag_count' in doc.metadata
        
        # Tag count should match actual tags
        assert doc.metadata['tag_count'] == len(doc.tags)
    
    @pytest.mark.asyncio
    async def test_tag_sorting(self):
        """Test that tags are sorted consistently."""
        docs = [
            NormalizedDocument(
                document_id="doc1",
                title="test.py",
                content_md="# Test",
                original_format="python",
                metadata={"file_type": "code"},
                tags=["zzz:last", "aaa:first"]
            )
        ]
        
        tagged_docs, _ = await self.manager.tag_documents(
            documents=docs,
            source_type='github'
        )
        
        doc = tagged_docs[0]
        
        # Tags should be sorted
        assert doc.tags == sorted(doc.tags)
    
    @pytest.mark.asyncio
    async def test_multiple_documents(self):
        """Test tagging multiple documents."""
        docs = [
            NormalizedDocument(
                document_id=f"doc{i}",
                title=f"test{i}.py",
                content_md=f"# Test {i}",
                original_format="python",
                metadata={"file_type": "code"},
                tags=[]
            )
            for i in range(5)
        ]
        
        tagged_docs, tag_collection = await self.manager.tag_documents(
            documents=docs,
            source_type='github'
        )
        
        assert len(tagged_docs) == 5
        
        # All docs should have base tags
        for doc in tagged_docs:
            assert "source:github" in doc.tags
            assert "file_type:code" in doc.tags
    
    @pytest.mark.asyncio
    async def test_tag_normalize(self):
        """Test tag normalization."""
        result = self.manager._normalize_tag("Test Tag")
        assert result == "test-tag"
        
        result = self.manager._normalize_tag("test_tag")
        assert result == "test-tag"
        
        result = self.manager._normalize_tag("  Test  ")
        assert result == "test"
    
    def test_get_tag_collection(self):
        """Test getting tag collection."""
        collection = self.manager.get_tag_collection()
        
        assert isinstance(collection, TagCollection)
    
    def test_get_tag_metadata(self):
        """Test getting tag metadata for MCP storage."""
        metadata = self.manager.get_tag_metadata()
        
        assert "tag_collection" in metadata
        assert "config" in metadata
        assert "enable_user_tags" in metadata["config"]
    
    @pytest.mark.parametrize("source,expected_prefix", [
        ("github", "author"),
        ("jira", "assignee"),
        ("wikipedia", "character"),
        ("confluence", "author"),
        ("local", "author")
    ])
    def test_source_specific_prefixes(self, source, expected_prefix):
        """Test source-specific entity prefixes."""
        prefixes = self.manager.SOURCE_ENTITY_PREFIXES.get(source)
        
        assert 'PERSON' in prefixes
        assert prefixes['PERSON'] == expected_prefix

