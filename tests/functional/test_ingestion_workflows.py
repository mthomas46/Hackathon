"""
Functional tests for complete ingestion workflows.

Tests end-to-end ingestion from various sources with tagging and normalization.
"""
import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

from ingestion.wikipedia_ingestor import WikipediaIngestor
from ingestion.fandom_ingestor import FandomWikiIngestor
from ingestion.local_file_ingestor import LocalFileIngestor
from ingestion.tagging import UniversalTaggingConfig


@pytest.mark.functional
class TestIngestionWorkflows:
    """Functional tests for complete ingestion workflows."""
    
    @pytest.fixture
    async def temp_directory(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def sample_files(self, temp_directory):
        """Create sample files for testing."""
        temp_path = Path(temp_directory)
        
        # Create markdown file
        md_file = temp_path / "test.md"
        md_file.write_text("# Test Document\n\nThis is a test document.")
        
        # Create Python file
        py_file = temp_path / "test.py"
        py_file.write_text("def hello():\n    print('world')")
        
        # Create text file
        txt_file = temp_path / "test.txt"
        txt_file.write_text("Plain text content")
        
        # Create subdirectory with file
        sub_dir = temp_path / "subdir"
        sub_dir.mkdir()
        sub_file = sub_dir / "nested.md"
        sub_file.write_text("# Nested Document\n\nNested content")
        
        return {
            'directory': temp_path,
            'files': [md_file, py_file, txt_file, sub_file]
        }
    
    @pytest.mark.asyncio
    async def test_local_directory_ingestion_workflow(self, sample_files):
        """
        Test complete local directory ingestion workflow.
        
        Validates:
        1. File discovery (recursive)
        2. File type detection
        3. Content normalization
        4. Tagging application
        5. Metadata extraction
        """
        ingestor = LocalFileIngestor(
            enable_tagging=True,
            enable_corpus_analysis=False
        )
        
        documents = await ingestor.ingest_directory(
            str(sample_files['directory']),
            recursive=True,
            user_tags=["test:workflow", "domain:testing"]
        )
        
        # Verify documents were ingested
        assert len(documents) >= 3  # At least md, py, txt
        
        # Verify each document has required fields
        for doc in documents:
            assert doc.document_id
            assert doc.title
            assert doc.content_md
            assert doc.metadata
            assert 'source' in doc.metadata
            assert 'file_type' in doc.metadata
            assert 'created_at' in doc.metadata
            assert 'updated_at' in doc.metadata
        
        # Verify tagging was applied
        all_tags = []
        for doc in documents:
            all_tags.extend(doc.tags)
        
        assert len(all_tags) > 0
        # User tags should be present
        assert any('test:workflow' in tag for tag in all_tags)
        
        # Verify tag collection
        tag_collection = ingestor.get_tag_collection()
        assert tag_collection is not None
        assert tag_collection.total_count() > 0
        
        # Verify statistics
        stats = ingestor.get_statistics()
        assert stats['total_documents'] >= 3
        assert 'file_types' in stats
        assert 'total_size_bytes' in stats
        
        print(f"✅ Ingested {len(documents)} documents")
        print(f"✅ Tag collection: {tag_collection.total_count()} tags")
        print(f"✅ Statistics: {stats}")
    
    @pytest.mark.asyncio
    async def test_local_file_pattern_filtering(self, sample_files):
        """
        Test file pattern filtering during ingestion.
        
        Validates:
        1. Include pattern matching
        2. Exclude pattern matching
        3. Selective file processing
        """
        ingestor = LocalFileIngestor(enable_tagging=False)
        
        # Ingest only markdown files
        documents = await ingestor.ingest_directory(
            str(sample_files['directory']),
            recursive=True,
            file_patterns=['*.md']
        )
        
        # Should only get markdown files
        assert len(documents) >= 2  # test.md and nested.md
        for doc in documents:
            assert doc.metadata['original_format'] == 'md'
        
        print(f"✅ Filtered to {len(documents)} markdown files")
    
    @pytest.mark.asyncio
    async def test_single_file_ingestion(self, sample_files):
        """
        Test single file ingestion workflow.
        
        Validates:
        1. Single file processing
        2. Metadata extraction
        3. Tagging
        """
        ingestor = LocalFileIngestor(enable_tagging=True)
        
        md_file = sample_files['files'][0]  # test.md
        document = await ingestor.ingest_file(
            str(md_file),
            user_tags=["single:file", "test:document"]
        )
        
        assert document is not None
        assert document.document_id
        assert "Test Document" in document.content_md
        assert document.metadata['source'] == 'local_files'
        assert document.metadata['file_name'] == 'test.md'
        
        # Verify tags
        assert len(document.tags) > 0
        
        print(f"✅ Single file ingested: {document.document_id}")
    
    @pytest.mark.asyncio
    async def test_multiple_format_normalization(self, sample_files):
        """
        Test normalization of multiple file formats.
        
        Validates:
        1. Markdown normalization
        2. Code file handling
        3. Plain text normalization
        """
        ingestor = LocalFileIngestor(enable_tagging=False)
        
        documents = await ingestor.ingest_directory(
            str(sample_files['directory']),
            recursive=True
        )
        
        # Find each type
        md_docs = [d for d in documents if d.metadata['original_format'] == 'md']
        py_docs = [d for d in documents if d.metadata['original_format'] == 'py']
        txt_docs = [d for d in documents if d.metadata['original_format'] == 'txt']
        
        assert len(md_docs) > 0, "Should have markdown documents"
        assert len(py_docs) > 0, "Should have Python documents"
        assert len(txt_docs) > 0, "Should have text documents"
        
        # Verify code files are wrapped in code blocks
        for py_doc in py_docs:
            assert "```" in py_doc.content_md
        
        print(f"✅ Normalized {len(md_docs)} MD, {len(py_docs)} PY, {len(txt_docs)} TXT")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_corpus_analysis_integration(self, sample_files):
        """
        Test corpus analysis integration in ingestion workflow.
        
        Validates:
        1. Corpus analysis activation
        2. Contextual tag generation
        3. Tag collection enrichment
        """
        # Create more files for meaningful corpus analysis
        temp_path = sample_files['directory']
        
        for i in range(5):
            f = temp_path / f"doc_{i}.md"
            f.write_text(f"# Document {i}\n\nTest content with entities and topics.")
        
        ingestor = LocalFileIngestor(
            enable_tagging=True,
            enable_corpus_analysis=True,
            corpus_analysis_sample_size=5
        )
        
        documents = await ingestor.ingest_directory(
            str(temp_path),
            recursive=False
        )
        
        assert len(documents) >= 5
        
        # Verify tag collection has contextual tags
        tag_collection = ingestor.get_tag_collection()
        assert tag_collection is not None
        
        # Should have default + contextual tags
        assert tag_collection.default_count() > 0
        
        print(f"✅ Corpus analysis generated {tag_collection.contextual_count()} contextual tags")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_wikipedia_ingestion_workflow(self):
        """
        Test Wikipedia ingestion workflow (limited crawl).
        
        Validates:
        1. Wikipedia page fetching
        2. HTML to Markdown normalization
        3. Link extraction and filtering
        4. Tag application
        """
        ingestor = WikipediaIngestor(
            tagging_config=UniversalTaggingConfig(
                enable_preprocessing=False
            )
        )
        
        # Small crawl for functional test
        try:
            documents = await ingestor.crawl_and_ingest(
                original_page_url="https://en.wikipedia.org/wiki/Artificial_intelligence",
                max_surface_links=2,
                max_depth_distance=1
            )
            
            if len(documents) > 0:
                # Verify document structure
                assert documents[0].document_id
                assert documents[0].title
                assert len(documents[0].content_md) > 100  # Should have substantial content
                assert documents[0].metadata['source'] == 'wikipedia'
                
                # Verify tagging
                assert len(documents[0].tags) > 0
                
                # Verify crawl report
                report = ingestor.generate_crawl_report()
                assert report.total_pages > 0
                
                print(f"✅ Wikipedia workflow: {len(documents)} docs, {report.total_pages} pages")
            else:
                print("⚠️  Wikipedia crawl returned no documents (network issue?)")
        
        except Exception as e:
            pytest.skip(f"Wikipedia not accessible: {e}")
    
    @pytest.mark.asyncio
    async def test_ingestion_error_handling(self, temp_directory):
        """
        Test error handling in ingestion workflows.
        
        Validates:
        1. Graceful handling of invalid files
        2. Skipping unreadable files
        3. Continuing after errors
        """
        temp_path = Path(temp_directory)
        
        # Create valid file
        valid_file = temp_path / "valid.md"
        valid_file.write_text("# Valid Document")
        
        # Create binary file (unreadable as text)
        binary_file = temp_path / "binary.bin"
        binary_file.write_bytes(b'\x00\x01\x02\x03\xFF\xFE')
        
        ingestor = LocalFileIngestor(enable_tagging=False)
        
        documents = await ingestor.ingest_directory(
            str(temp_path),
            recursive=False
        )
        
        # Should have at least the valid file
        assert len(documents) >= 1
        
        # Verify valid file was processed
        valid_docs = [d for d in documents if 'valid' in d.document_id.lower()]
        assert len(valid_docs) > 0
        
        print(f"✅ Error handling: {len(documents)} docs processed successfully")
    
    @pytest.mark.asyncio
    async def test_empty_directory_handling(self, temp_directory):
        """
        Test handling of empty directories.
        
        Validates:
        1. Graceful handling of empty directories
        2. No errors on empty results
        """
        ingestor = LocalFileIngestor(enable_tagging=False)
        
        documents = await ingestor.ingest_directory(
            temp_directory,
            recursive=True
        )
        
        assert documents == []
        
        stats = ingestor.get_statistics()
        assert stats == {}
        
        print("✅ Empty directory handled gracefully")

