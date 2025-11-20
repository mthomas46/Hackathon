#!/usr/bin/env python3
"""
Simple Service Metadata Backfill for ChromaDB

Updates ChromaDB metadata with service names from PostgreSQL.
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.storage import get_database, get_chroma_client
from src.storage.db_models import DocumentModel
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def backfill():
    """Backfill service metadata."""
    logger.info("=" * 70)
    logger.info("SERVICE METADATA BACKFILL (Simplified)")
    logger.info("=" * 70)
    
    # Step 1: Get documents from PostgreSQL
    logger.info("\n📊 Fetching documents from PostgreSQL...")
    db = get_database()
    async with db.session() as session:
        query = select(DocumentModel).where(
            DocumentModel.is_latest == True,
            DocumentModel.service_name != None
        ).limit(1000)
        
        result = await session.execute(query)
        documents = list(result.scalars().all())
        
    logger.info(f"   Found {len(documents)} documents")
    
    # Track services
    services = {}
    for doc in documents:
        services[doc.service_name] = services.get(doc.service_name, 0) + 1
    
    logger.info(f"   Services: {dict(services)}")
    
    # Step 2: Update ChromaDB using raw client
    logger.info("\n✨ Updating ChromaDB metadata...")
    chroma = get_chroma_client()
    
    updated = 0
    failed = 0
    batch_size = 50
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        batch_ids = []
        batch_metadatas = []
        
        for doc in batch:
            doc_id = str(doc.id)
            
            # Get current document from ChromaDB
            try:
                current = await chroma.get_by_ids(
                    ids=[doc_id],
                    include=["metadatas"]
                )
                
                if current and current.get("ids") and len(current["ids"]) > 0:
                    # Document exists - prepare update
                    current_metadata = current["metadatas"][0]
                    
                    # Update service field
                    updated_metadata = {**current_metadata}
                    updated_metadata["service"] = doc.service_name
                    
                    batch_ids.append(doc_id)
                    batch_metadatas.append(updated_metadata)
                    
            except Exception as e:
                logger.error(f"   Error checking {doc.file_path}: {e}")
                failed += 1
        
        # Update batch using raw ChromaDB client
        if batch_ids:
            try:
                # Use the raw ChromaDB collection.update() method
                await asyncio.to_thread(
                    chroma.collection.update,
                    ids=batch_ids,
                    metadatas=batch_metadatas
                )
                updated += len(batch_ids)
                logger.info(f"   ✅ Batch {i // batch_size + 1}: Updated {len(batch_ids)} documents")
            except Exception as e:
                logger.error(f"   ❌ Batch update failed: {e}")
                failed += len(batch_ids)
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total documents:  {len(documents)}")
    logger.info(f"Updated:          {updated}")
    logger.info(f"Failed:           {failed}")
    logger.info(f"Success rate:     {(updated / len(documents) * 100):.1f}%")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(backfill())

