"""
Recoverable Embedding Generator

Generates embeddings with checkpoint support for graceful recovery.
Allows interrupted embedding generation to resume from last checkpoint.
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime

from ...storage import get_database
from ...storage.repositories import DocumentRepository
from ...storage.chromadb_client import get_chroma_client
from .embedding_service import EmbeddingService
from ...utils.job_recovery import (
    JobRecoveryManager,
    RecoverableJob,
    JobType,
    get_recovery_manager
)

logger = logging.getLogger(__name__)


class RecoverableEmbeddingGenerator(RecoverableJob):
    """
    Generates embeddings with checkpoint support.
    
    Features:
    - Checkpoint every N documents (configurable)
    - Resume from last checkpoint
    - Skip already-embedded documents
    - Batch processing with progress tracking
    - Graceful interruption handling
    """
    
    # Checkpoint frequency
    CHECKPOINT_INTERVAL = 50  # Create checkpoint every 50 documents
    BATCH_SIZE = 10  # Process 10 documents at a time
    
    def __init__(self, job_id: Optional[str] = None):
        """
        Initialize recoverable embedding generator.
        
        Args:
            job_id: Optional job ID (generates UUID if not provided)
        """
        if not job_id:
            job_id = str(uuid4())
        
        # Get recovery manager
        db = get_database()
        recovery_manager = get_recovery_manager(db)
        
        super().__init__(job_id, JobType.EMBEDDING, recovery_manager)
        
        self.embedding_service = EmbeddingService()
        
        logger.info(f"RecoverableEmbeddingGenerator initialized: job_id={job_id}")
    
    async def generate_all_missing(
        self,
        batch_size: Optional[int] = None,
        skip_existing: bool = True,
        resume: bool = True
    ) -> Dict[str, Any]:
        """
        Generate embeddings for all documents missing them.
        
        Args:
            batch_size: Number of documents to process in each batch
            skip_existing: Whether to skip documents that already have embeddings
            resume: Whether to attempt resume from last checkpoint
        
        Returns:
            Generation results
        """
        batch_size = batch_size or self.BATCH_SIZE
        
        logger.info(
            f"🔄 Generating missing embeddings (job_id={self.job_id}, "
            f"batch_size={batch_size}, skip_existing={skip_existing}, resume={resume})"
        )
        
        result = {
            "success": False,
            "total_documents": 0,
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "resumed_from_checkpoint": False,
            "checkpoints_created": 0,
            "error": None
        }
        
        try:
            # Load checkpoints from database
            await self.recovery_manager.load_checkpoints(self.job_id)
            
            # Check if we can resume
            can_resume = False
            resume_state = None
            start_offset = 0
            
            if resume:
                can_resume = await self.can_resume()
                
                if can_resume:
                    resume_state = await self.get_resume_state()
                    last_checkpoint_data = resume_state["last_checkpoint"]["data"]
                    start_offset = last_checkpoint_data.get("processed", 0)
                    
                    result["processed"] = start_offset
                    result["skipped"] = last_checkpoint_data.get("skipped", 0)
                    result["failed"] = last_checkpoint_data.get("failed", 0)
                    result["resumed_from_checkpoint"] = True
                    
                    logger.info(
                        f"📂 Resuming from checkpoint: processed={start_offset}, "
                        f"skipped={result['skipped']}, failed={result['failed']}"
                    )
            
            # Get all documents without embeddings
            db = get_database()
            async with db.session() as session:
                doc_repo = DocumentRepository(session)
                
                # Get count first
                total_docs = await doc_repo.count_without_embeddings()
                result["total_documents"] = total_docs
                
                if total_docs == 0:
                    logger.info("✅ No documents missing embeddings")
                    result["success"] = True
                    return result
                
                logger.info(
                    f"📊 Found {total_docs} documents without embeddings "
                    f"(starting from offset {start_offset})"
                )
                
                # Process in batches
                offset = start_offset
                
                while offset < total_docs:
                    # Get batch of documents
                    docs = await doc_repo.get_without_embeddings(
                        limit=batch_size,
                        offset=offset
                    )
                    
                    if not docs:
                        break
                    
                    logger.info(
                        f"📦 Processing batch: {offset + 1}-{offset + len(docs)} "
                        f"of {total_docs}"
                    )
                    
                    # Process each document in batch
                    for doc in docs:
                        try:
                            # Check if already has embedding (if skip_existing)
                            if skip_existing:
                                chroma = get_chroma_client()
                                existing = await chroma.get_document(str(doc.id))
                                
                                if existing:
                                    result["skipped"] += 1
                                    logger.debug(f"⏭️  Skipped {doc.id} (already exists)")
                                    continue
                            
                            # Generate embedding
                            embedding = await self.embedding_service.generate_embedding(
                                doc.normalized_content
                            )
                            
                            # Store in ChromaDB
                            chroma = get_chroma_client()
                            await chroma.add_document(
                                document_id=str(doc.id),
                                embedding=embedding,
                                metadata={
                                    "source_path": doc.source_path,
                                    "service_id": doc.service_id,
                                    "original_format": doc.original_format
                                }
                            )
                            
                            result["processed"] += 1
                            
                            logger.debug(f"✅ Generated embedding for {doc.id}")
                        
                        except Exception as e:
                            result["failed"] += 1
                            logger.error(f"❌ Failed to generate embedding for {doc.id}: {e}")
                    
                    offset += len(docs)
                    
                    # Create checkpoint at intervals
                    if result["processed"] % self.CHECKPOINT_INTERVAL == 0:
                        checkpoint_id = f"batch_{offset}_{result['processed']}"
                        
                        await self.create_checkpoint(
                            checkpoint_id=checkpoint_id,
                            data={
                                "processed": result["processed"],
                                "skipped": result["skipped"],
                                "failed": result["failed"],
                                "offset": offset,
                                "total": total_docs,
                                "progress_pct": round(offset / total_docs * 100, 1)
                            }
                        )
                        
                        await self.complete_checkpoint(data={
                            "processed": result["processed"],
                            "skipped": result["skipped"],
                            "failed": result["failed"]
                        })
                        
                        result["checkpoints_created"] += 1
                        
                        logger.info(
                            f"📌 Checkpoint created: {checkpoint_id} "
                            f"({result['processed']} processed, "
                            f"{round(offset / total_docs * 100, 1)}% complete)"
                        )
            
            result["success"] = True
            
            # Cleanup old checkpoints
            await self.recovery_manager.cleanup_checkpoints(
                job_id=self.job_id,
                keep_last=3
            )
            
            logger.info(
                f"✅ Embedding generation complete: "
                f"{result['processed']} processed, "
                f"{result['skipped']} skipped, "
                f"{result['failed']} failed, "
                f"{result['checkpoints_created']} checkpoints created"
            )
        
        except Exception as e:
            logger.error(f"❌ Error generating embeddings: {e}", exc_info=True)
            result["error"] = str(e)
            
            # Try to save failure checkpoint
            try:
                await self.fail_checkpoint(str(e))
            except:
                pass
        
        return result
    
    async def generate_for_documents(
        self,
        document_ids: List[str],
        resume: bool = True
    ) -> Dict[str, Any]:
        """
        Generate embeddings for specific documents.
        
        Args:
            document_ids: List of document IDs to process
            resume: Whether to attempt resume from last checkpoint
        
        Returns:
            Generation results
        """
        logger.info(
            f"🔄 Generating embeddings for {len(document_ids)} documents "
            f"(job_id={self.job_id}, resume={resume})"
        )
        
        result = {
            "success": False,
            "total_documents": len(document_ids),
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "resumed_from_checkpoint": False,
            "checkpoints_created": 0,
            "error": None
        }
        
        try:
            # Load checkpoints
            await self.recovery_manager.load_checkpoints(self.job_id)
            
            # Check if we can resume
            start_index = 0
            
            if resume:
                can_resume = await self.can_resume()
                
                if can_resume:
                    resume_state = await self.get_resume_state()
                    last_checkpoint_data = resume_state["last_checkpoint"]["data"]
                    start_index = last_checkpoint_data.get("current_index", 0)
                    
                    result["processed"] = last_checkpoint_data.get("processed", 0)
                    result["skipped"] = last_checkpoint_data.get("skipped", 0)
                    result["failed"] = last_checkpoint_data.get("failed", 0)
                    result["resumed_from_checkpoint"] = True
                    
                    logger.info(
                        f"📂 Resuming from index {start_index} "
                        f"(processed={result['processed']})"
                    )
            
            # Process documents
            db = get_database()
            async with db.session() as session:
                doc_repo = DocumentRepository(session)
                
                for i in range(start_index, len(document_ids)):
                    doc_id = document_ids[i]
                    
                    try:
                        # Get document
                        doc = await doc_repo.get_by_id(doc_id)
                        
                        if not doc:
                            result["skipped"] += 1
                            logger.warning(f"⏭️  Document {doc_id} not found")
                            continue
                        
                        # Generate embedding
                        embedding = await self.embedding_service.generate_embedding(
                            doc.normalized_content
                        )
                        
                        # Store in ChromaDB
                        chroma = get_chroma_client()
                        await chroma.add_document(
                            document_id=str(doc.id),
                            embedding=embedding,
                            metadata={
                                "source_path": doc.source_path,
                                "service_id": doc.service_id,
                                "original_format": doc.original_format
                            }
                        )
                        
                        result["processed"] += 1
                        
                        logger.debug(f"✅ Generated embedding for {doc_id}")
                    
                    except Exception as e:
                        result["failed"] += 1
                        logger.error(f"❌ Failed for {doc_id}: {e}")
                    
                    # Create checkpoint at intervals
                    if (i + 1) % self.CHECKPOINT_INTERVAL == 0:
                        checkpoint_id = f"doc_{i + 1}_{result['processed']}"
                        
                        await self.create_checkpoint(
                            checkpoint_id=checkpoint_id,
                            data={
                                "current_index": i + 1,
                                "processed": result["processed"],
                                "skipped": result["skipped"],
                                "failed": result["failed"],
                                "progress_pct": round((i + 1) / len(document_ids) * 100, 1)
                            }
                        )
                        
                        await self.complete_checkpoint()
                        
                        result["checkpoints_created"] += 1
                        
                        logger.info(f"📌 Checkpoint created: {checkpoint_id}")
            
            result["success"] = True
            
            # Cleanup old checkpoints
            await self.recovery_manager.cleanup_checkpoints(
                job_id=self.job_id,
                keep_last=3
            )
            
            logger.info(
                f"✅ Embedding generation complete: "
                f"{result['processed']}/{result['total_documents']} processed"
            )
        
        except Exception as e:
            logger.error(f"❌ Error generating embeddings: {e}", exc_info=True)
            result["error"] = str(e)
            
            try:
                await self.fail_checkpoint(str(e))
            except:
                pass
        
        return result

