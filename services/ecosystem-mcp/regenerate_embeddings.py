#!/usr/bin/env python3
"""
Regenerate Missing Embeddings

This script finds all documents in PostgreSQL that don't have
corresponding embeddings in ChromaDB and generates them.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to regenerate missing embeddings."""
    from src.storage import get_database
    from src.storage.chromadb_client import get_chroma_client
    from src.services.embeddings.embedding_service import EmbeddingService
    from src.storage.repositories import DocumentRepository
    
    logger.info("🚀 Starting embedding regeneration...")
    
    # Initialize clients
    db = get_database()
    chroma = get_chroma_client()
    embedding_service = EmbeddingService()
    
    # Get counts
    async with db.session() as session:
        doc_repo = DocumentRepository(session)
        
        # Get all documents
        all_docs = await doc_repo.get_all(limit=10000)
        total_docs = len(all_docs)
        
        logger.info(f"📚 Found {total_docs} documents in PostgreSQL")
    
    # Get ChromaDB count
    chroma_count = await chroma.count()
    logger.info(f"📊 Found {chroma_count} embeddings in ChromaDB")
    
    missing_count = total_docs - chroma_count
    logger.info(f"⚠️  Missing embeddings: {missing_count}")
    
    if missing_count <= 0:
        logger.info("✅ All documents have embeddings!")
        return
    
    # Get existing embedding IDs from ChromaDB
    logger.info("📋 Fetching existing embedding IDs from ChromaDB...")
    try:
        existing_result = await asyncio.to_thread(
            chroma.collection.get,
            include=[]  # Just get IDs
        )
        existing_ids = set(existing_result['ids'])
        logger.info(f"✅ Found {len(existing_ids)} existing embedding IDs")
    except Exception as e:
        logger.warning(f"Could not fetch existing IDs: {e}")
        existing_ids = set()
    
    # Process documents in batches
    batch_size = 10
    processed = 0
    succeeded = 0
    failed = 0
    skipped = 0
    
    logger.info(f"\n🔄 Processing {total_docs} documents in batches of {batch_size}...")
    
    async with db.session() as session:
        doc_repo = DocumentRepository(session)
        
        for i in range(0, total_docs, batch_size):
            batch = all_docs[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_docs + batch_size - 1) // batch_size
            
            logger.info(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} documents)")
            
            for doc in batch:
                processed += 1
                doc_id = str(doc.id)
                
                # Check if embedding already exists
                if doc_id in existing_ids:
                    skipped += 1
                    logger.debug(f"⏭️  Skipped (has embedding): {doc.file_path}")
                    continue
                
                try:
                    # Generate embedding
                    logger.info(f"🔄 [{processed}/{total_docs}] Generating embedding: {doc.file_path}")
                    
                    embedding_result = await embedding_service.generate_embedding(
                        text=doc.normalized_content or doc.original_content
                    )
                    
                    if not embedding_result or not embedding_result.get("embedding"):
                        logger.error(f"❌ Failed to generate embedding: {doc.file_path}")
                        failed += 1
                        continue
                    
                    # Store embedding in ChromaDB
                    embeddings = [embedding_result["embedding"]]
                    metadata = {
                        "file_path": doc.file_path,
                        "service_name": doc.service_name or "unknown",
                        "file_type": doc.file_type or "unknown",
                        "commit_sha": doc.git_commit_sha or "unknown",
                        "content_hash": doc.content_hash
                    }
                    
                    success = await chroma.add_embeddings_with_retry(
                        embeddings=embeddings,
                        metadatas=[metadata],
                        ids=[doc_id],
                        documents=[doc.normalized_content or doc.original_content],
                        max_retries=3
                    )
                    
                    if success:
                        succeeded += 1
                        logger.info(f"✅ Stored embedding: {doc.file_path}")
                    else:
                        failed += 1
                        logger.error(f"❌ Failed to store embedding: {doc.file_path}")
                
                except Exception as e:
                    failed += 1
                    logger.error(f"❌ Error processing {doc.file_path}: {e}")
            
            # Progress update
            logger.info(
                f"\n📊 Progress: {processed}/{total_docs} "
                f"(✅ {succeeded} | ❌ {failed} | ⏭️  {skipped})"
            )
            
            # Small delay between batches
            if i + batch_size < total_docs:
                await asyncio.sleep(1)
    
    # Final summary
    logger.info("\n" + "=" * 70)
    logger.info("🎉 Embedding Regeneration Complete!")
    logger.info("=" * 70)
    logger.info(f"Total documents:     {total_docs}")
    logger.info(f"Processed:           {processed}")
    logger.info(f"✅ Succeeded:         {succeeded}")
    logger.info(f"❌ Failed:            {failed}")
    logger.info(f"⏭️  Skipped:          {skipped}")
    logger.info(f"\nFinal ChromaDB count: {await chroma.count()}")
    logger.info(f"Coverage:            {(await chroma.count() / total_docs * 100):.1f}%")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

