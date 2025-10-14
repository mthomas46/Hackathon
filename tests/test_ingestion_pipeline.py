"""
Comprehensive Ingestion Pipeline Tests

Tests the entire ingestion flow from Git → Processing → Storage
to identify where the 319 file failures occurred.
"""

import pytest
import asyncio
import logging
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from uuid import uuid4

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestGitServiceIntegration:
    """Test Git service file retrieval."""
    
    @pytest.mark.asyncio
    async def test_git_repo_accessibility(self):
        """Test if git repository is accessible."""
        logger.info("=" * 70)
        logger.info("TEST 1: Git Repository Accessibility")
        logger.info("=" * 70)
        
        try:
            from src.services.git.git_service import GitService
            
            git = GitService(repo_path="/app")
            logger.info("✅ Git service initialized")
            
            # Test getting recent commits
            commits = await git.get_recent_commits(limit=1)
            assert len(commits) > 0, "No commits found"
            logger.info(f"✅ Found {len(commits)} commit(s)")
            
            commit = commits[0]
            logger.info(f"  Commit SHA: {commit.sha}")
            logger.info(f"  Commit message: {commit.message}")
            logger.info(f"  Commit author: {commit.author}")
            
            return commit.sha
            
        except Exception as e:
            logger.error(f"❌ Git repo accessibility test FAILED: {e}", exc_info=True)
            pytest.fail(f"Git repo not accessible: {e}")
    
    @pytest.mark.asyncio
    async def test_file_listing(self):
        """Test listing files from a commit."""
        logger.info("=" * 70)
        logger.info("TEST 2: File Listing from Commit")
        logger.info("=" * 70)
        
        try:
            from src.services.git.git_service import GitService
            
            git = GitService(repo_path="/app")
            commits = await git.get_recent_commits(limit=1)
            commit_sha = commits[0].sha
            
            logger.info(f"Getting files at commit: {commit_sha}")
            files = await git.get_files_at_commit(commit_sha)
            
            logger.info(f"✅ Found {len(files)} total files")
            logger.info(f"  First 10 files:")
            for i, f in enumerate(files[:10], 1):
                logger.info(f"    {i}. {f}")
            
            assert len(files) > 0, "No files found in commit"
            return files[:5]  # Return first 5 for next test
            
        except Exception as e:
            logger.error(f"❌ File listing test FAILED: {e}", exc_info=True)
            pytest.fail(f"Failed to list files: {e}")
    
    @pytest.mark.asyncio
    async def test_file_content_retrieval(self):
        """Test retrieving content from specific files."""
        logger.info("=" * 70)
        logger.info("TEST 3: File Content Retrieval")
        logger.info("=" * 70)
        
        try:
            from src.services.git.git_service import GitService
            
            git = GitService(repo_path="/app")
            commits = await git.get_recent_commits(limit=1)
            commit_sha = commits[0].sha
            files = await git.get_files_at_commit(commit_sha)
            
            # Test retrieving content from first 5 files
            test_files = files[:5]
            success_count = 0
            failure_count = 0
            
            for file_path in test_files:
                logger.info(f"Testing file: {file_path}")
                try:
                    content = await git.get_file_content_at_commit(commit_sha, file_path)
                    if content:
                        logger.info(f"  ✅ Success - Content length: {len(content)} bytes")
                        logger.info(f"     First 100 chars: {content[:100]}")
                        success_count += 1
                    else:
                        logger.warning(f"  ⚠️  Empty content returned")
                        failure_count += 1
                except Exception as e:
                    logger.error(f"  ❌ Failed to retrieve: {e}")
                    failure_count += 1
            
            logger.info(f"Results: {success_count} success, {failure_count} failures")
            assert success_count > 0, "No files could be retrieved"
            
        except Exception as e:
            logger.error(f"❌ File content retrieval test FAILED: {e}", exc_info=True)
            pytest.fail(f"Failed to retrieve file content: {e}")


class TestDocumentProcessing:
    """Test document normalization and processing."""
    
    @pytest.mark.asyncio
    async def test_normalizer_factory(self):
        """Test if normalizers work for different file types."""
        logger.info("=" * 70)
        logger.info("TEST 4: Normalizer Factory")
        logger.info("=" * 70)
        
        try:
            from src.services.processing.normalizer_factory import NormalizerFactory
            
            factory = NormalizerFactory()
            
            # Test different file types
            test_cases = [
                ('.py', 'print("hello")', 'Python'),
                ('.md', '# Title\nContent', 'Markdown'),
                ('.json', '{"key": "value"}', 'JSON'),
                ('.yaml', 'key: value', 'YAML'),
                ('.txt', 'Plain text', 'Text'),
            ]
            
            for ext, content, name in test_cases:
                logger.info(f"Testing {name} normalizer ({ext})")
                try:
                    normalizer = factory.get_normalizer(ext)
                    result = await normalizer.normalize(
                        content=content,
                        file_path=f"test{ext}",
                        metadata={}
                    )
                    logger.info(f"  ✅ {name} normalizer works")
                    logger.info(f"     Output length: {len(result['content'])} chars")
                except Exception as e:
                    logger.error(f"  ❌ {name} normalizer FAILED: {e}", exc_info=True)
                    raise
            
        except Exception as e:
            logger.error(f"❌ Normalizer factory test FAILED: {e}", exc_info=True)
            pytest.fail(f"Normalizer test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_file_filtering(self):
        """Test file filtering logic."""
        logger.info("=" * 70)
        logger.info("TEST 5: File Filtering")
        logger.info("=" * 70)
        
        try:
            from src.services.ingestion.job_processor import JobProcessor
            
            processor = JobProcessor()
            
            # Mock files with various extensions
            mock_files = [
                'test.py', 'test.md', 'test.yaml', 'test.json', 'test.txt',
                'test.pyc', 'test.jpg', 'test.png', 'binary.so', '.gitignore',
                'node_modules/test.js', '__pycache__/test.pyc', 'README.md'
            ]
            
            filtered = processor._filter_files(mock_files)
            
            logger.info(f"Original files: {len(mock_files)}")
            logger.info(f"Filtered files: {len(filtered)}")
            logger.info(f"Included files:")
            for f in filtered:
                logger.info(f"  ✅ {f}")
            
            logger.info(f"Excluded files:")
            for f in set(mock_files) - set(filtered):
                logger.info(f"  ❌ {f}")
            
            assert len(filtered) > 0, "All files were filtered out"
            
        except Exception as e:
            logger.error(f"❌ File filtering test FAILED: {e}", exc_info=True)
            pytest.fail(f"File filtering failed: {e}")


class TestDatabaseOperations:
    """Test database connectivity and operations."""
    
    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test database connection."""
        logger.info("=" * 70)
        logger.info("TEST 6: Database Connection")
        logger.info("=" * 70)
        
        try:
            from src.storage import get_database
            
            db = get_database()
            logger.info(f"✅ Database instance created")
            
            async with db.session() as session:
                # Try a simple query
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1"))
                value = result.scalar()
                assert value == 1
                logger.info(f"✅ Database connection works")
            
        except Exception as e:
            logger.error(f"❌ Database connection test FAILED: {e}", exc_info=True)
            pytest.fail(f"Database connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_document_repository(self):
        """Test document repository operations."""
        logger.info("=" * 70)
        logger.info("TEST 7: Document Repository")
        logger.info("=" * 70)
        
        try:
            from src.storage import get_database
            from src.storage.repositories import DocumentRepository
            from src.storage.db_models import DocumentModel
            from hashlib import sha256
            
            db = get_database()
            
            async with db.session() as session:
                repo = DocumentRepository(session)
                
                # Create test document
                test_content = "Test content for ingestion test"
                content_hash = sha256(test_content.encode()).hexdigest()
                
                logger.info(f"Creating test document with hash: {content_hash[:16]}...")
                
                # Check if already exists
                existing = await repo.get_by_content_hash(content_hash)
                if existing:
                    logger.info(f"  ⏭️  Document already exists (ID: {existing.id})")
                    return
                
                doc = DocumentModel(
                    id=uuid4(),
                    service_name="test-service",
                    file_path="tests/test_file.txt",
                    original_format="txt",
                    original_content=test_content,
                    normalized_content=test_content,
                    content_hash=content_hash,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    is_latest=True,
                    doc_metadata={"test": True}
                )
                
                created = await repo.create(doc)
                await session.commit()
                
                logger.info(f"  ✅ Document created (ID: {created.id})")
                
                # Verify we can retrieve it
                retrieved = await repo.get_by_id(created.id)
                assert retrieved is not None
                logger.info(f"  ✅ Document retrieved successfully")
                
                # Cleanup - delete by entity, not by ID
                from sqlalchemy import delete
                stmt = delete(DocumentModel).where(DocumentModel.id == created.id)
                await session.execute(stmt)
                await session.commit()
                logger.info(f"  ✅ Test document cleaned up")
            
        except Exception as e:
            logger.error(f"❌ Document repository test FAILED: {e}", exc_info=True)
            pytest.fail(f"Document repository failed: {e}")


class TestEmbeddingService:
    """Test embedding generation."""
    
    @pytest.mark.asyncio
    async def test_embedding_service_connection(self):
        """Test connection to embedding service."""
        logger.info("=" * 70)
        logger.info("TEST 8: Embedding Service Connection")
        logger.info("=" * 70)
        
        try:
            from src.services.embeddings.embedding_service import EmbeddingService
            
            service = EmbeddingService()
            logger.info("✅ Embedding service initialized")
            
            # Test with simple text
            test_text = "This is a test document for embedding generation."
            logger.info(f"Generating embedding for: '{test_text}'")
            
            result = await service.generate_embedding(test_text)
            
            assert "embedding" in result, "No embedding in result"
            assert len(result["embedding"]) > 0, "Empty embedding"
            
            logger.info(f"✅ Embedding generated")
            logger.info(f"  Dimensions: {len(result['embedding'])}")
            logger.info(f"  Cost: ${result.get('cost', 0):.6f}")
            
        except Exception as e:
            logger.error(f"❌ Embedding service test FAILED: {e}", exc_info=True)
            pytest.fail(f"Embedding service failed: {e}")


class TestChromaDBOperations:
    """Test ChromaDB storage."""
    
    @pytest.mark.asyncio
    async def test_chromadb_connection(self):
        """Test ChromaDB connection."""
        logger.info("=" * 70)
        logger.info("TEST 9: ChromaDB Connection")
        logger.info("=" * 70)
        
        try:
            from src.storage.chromadb_client import get_chroma_client
            
            chroma = get_chroma_client()
            logger.info("✅ ChromaDB client initialized")
            
            # Get collection info
            collection = chroma.collection
            count = collection.count()
            logger.info(f"✅ Collection accessible: {collection.name}")
            logger.info(f"  Document count: {count}")
            
        except Exception as e:
            logger.error(f"❌ ChromaDB connection test FAILED: {e}", exc_info=True)
            pytest.fail(f"ChromaDB connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_chromadb_add_embedding(self):
        """Test adding embeddings to ChromaDB."""
        logger.info("=" * 70)
        logger.info("TEST 10: ChromaDB Add Embedding")
        logger.info("=" * 70)
        
        try:
            from src.storage.chromadb_client import get_chroma_client
            import numpy as np
            
            chroma = get_chroma_client()
            
            # Generate test embedding (384 dimensions for all-MiniLM-L6-v2)
            test_id = str(uuid4())
            test_embedding = np.random.rand(384).tolist()
            test_doc = "Test document for ChromaDB"
            test_metadata = {
                "service_name": "test-service",
                "file_path": "tests/test.txt",
                "test": True
            }
            
            logger.info(f"Adding test embedding with ID: {test_id}")
            
            success = await chroma.add_embeddings_with_retry(
                ids=[test_id],
                embeddings=[test_embedding],
                documents=[test_doc],
                metadatas=[test_metadata],
                max_retries=3
            )
            
            if success:
                logger.info(f"✅ Embedding added successfully")
                
                # Cleanup
                try:
                    chroma.collection.delete(ids=[test_id])
                    logger.info(f"✅ Test embedding cleaned up")
                except Exception as cleanup_error:
                    logger.warning(f"Could not clean up test embedding: {cleanup_error}")
            else:
                logger.error(f"❌ Failed to add embedding")
                pytest.fail("Failed to add embedding to ChromaDB")
            
        except Exception as e:
            logger.error(f"❌ ChromaDB add embedding test FAILED: {e}", exc_info=True)
            pytest.fail(f"ChromaDB add failed: {e}")


class TestEndToEndIngestion:
    """End-to-end integration test of a single file."""
    
    @pytest.mark.asyncio
    async def test_single_file_ingestion(self):
        """Test complete ingestion of a single file."""
        logger.info("=" * 70)
        logger.info("TEST 11: Single File End-to-End Ingestion")
        logger.info("=" * 70)
        
        try:
            from src.services.git.git_service import GitService
            from src.services.processing.normalizer_factory import NormalizerFactory
            from src.services.embeddings.embedding_service import EmbeddingService
            from src.storage import get_database
            from src.storage.repositories import DocumentRepository
            from src.storage.db_models import DocumentModel
            from src.storage.chromadb_client import get_chroma_client
            from hashlib import sha256
            from pathlib import Path
            
            # Step 1: Get a file from git
            logger.info("Step 1: Retrieving file from git...")
            git = GitService(repo_path="/app")
            commits = await git.get_recent_commits(limit=1)
            commit = commits[0]
            files = await git.get_files_at_commit(commit.sha)
            
            # Find a markdown file
            test_file = None
            for f in files:
                if f.endswith('.md'):
                    test_file = f
                    break
            
            if not test_file:
                test_file = files[0]  # Use first file if no .md found
            
            logger.info(f"  Testing with file: {test_file}")
            content = await git.get_file_content_at_commit(commit.sha, test_file)
            logger.info(f"  ✅ Retrieved content: {len(content)} bytes")
            
            # Step 2: Normalize
            logger.info("Step 2: Normalizing document...")
            factory = NormalizerFactory()
            path = Path(test_file)
            normalizer = factory.get_normalizer(path.suffix)
            
            normalized = await normalizer.normalize(
                content=content,
                file_path=str(path),
                metadata={
                    "commit_sha": commit.sha,
                    "commit_message": commit.message,
                    "commit_author": commit.author,
                    "commit_date": commit.date.isoformat(),
                }
            )
            logger.info(f"  ✅ Normalized: {len(normalized['content'])} chars")
            
            # Step 3: Generate embedding
            logger.info("Step 3: Generating embedding...")
            embedding_service = EmbeddingService()
            embedding_result = await embedding_service.generate_embedding(
                text=normalized["content"]
            )
            logger.info(f"  ✅ Embedding generated: {len(embedding_result['embedding'])} dimensions")
            
            # Step 4: Store in database
            logger.info("Step 4: Storing in PostgreSQL...")
            content_hash = sha256(normalized["content"].encode()).hexdigest()
            
            db = get_database()
            async with db.session() as session:
                repo = DocumentRepository(session)
                
                # Check for duplicate
                existing = await repo.get_by_content_hash(content_hash)
                if existing:
                    logger.info(f"  ⏭️  Document already exists (ID: {existing.id})")
                    doc_id = existing.id
                else:
                    document = DocumentModel(
                        id=uuid4(),
                        service_name="test-e2e",
                        file_path=str(path),
                        original_format=path.suffix[1:],
                        original_content=content,
                        normalized_content=normalized["content"],
                        content_hash=content_hash,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        git_commit_sha=commit.sha,
                        is_latest=True,
                        doc_metadata=normalized["metadata"]
                    )
                    
                    created = await repo.create(document)
                    await session.commit()
                    doc_id = created.id
                    logger.info(f"  ✅ Document stored (ID: {doc_id})")
            
            # Step 5: Store embedding in ChromaDB
            logger.info("Step 5: Storing embedding in ChromaDB...")
            chroma = get_chroma_client()
            
            embedding_success = await chroma.add_embeddings_with_retry(
                ids=[str(doc_id)],
                embeddings=[embedding_result["embedding"]],
                documents=[normalized["content"]],
                metadatas=[{
                    "service_name": "test-e2e",
                    "file_path": str(path),
                    "commit_sha": commit.sha,
                    "content_hash": content_hash
                }],
                max_retries=3
            )
            
            if embedding_success:
                logger.info(f"  ✅ Embedding stored in ChromaDB")
            else:
                logger.warning(f"  ⚠️  Failed to store embedding, but document saved")
            
            logger.info("=" * 70)
            logger.info("✅ END-TO-END TEST PASSED!")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"❌ End-to-end ingestion test FAILED: {e}", exc_info=True)
            pytest.fail(f"E2E ingestion failed: {e}")


# Test execution order
pytest_plugins = ['pytest_asyncio']

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

