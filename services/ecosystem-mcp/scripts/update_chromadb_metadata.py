#!/usr/bin/env python3
"""
Update ChromaDB Metadata from PostgreSQL

This script updates git_date metadata in ChromaDB by reading from PostgreSQL,
avoiding the need for full re-ingestion.

Usage:
    python3 update_chromadb_metadata.py [--dry-run] [--batch-size 100]
"""

import asyncio
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Any
import logging

# Add app to path
sys.path.insert(0, '/app')

from src.storage.chromadb_client import get_chroma_client
from src.storage.database import get_database
from sqlalchemy import select, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_chromadb_metadata(dry_run: bool = False, batch_size: int = 100):
    """
    Update ChromaDB metadata with git_date from PostgreSQL.
    
    Args:
        dry_run: If True, don't actually update, just report what would be done
        batch_size: Number of documents to process per batch
    """
    print("\n" + "="*80)
    print("ChromaDB Metadata Update from PostgreSQL")
    print("="*80)
    print(f"\nMode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    print(f"Batch Size: {batch_size}\n")
    
    try:
        # Get clients
        chroma = get_chroma_client()
        collection = chroma.collection
        db = get_database()
        
        # Statistics
        total_processed = 0
        total_updated = 0
        total_skipped = 0
        total_errors = 0
        
        async with db.session() as session:
            # Get all documents with git_date from PostgreSQL
            logger.info("📊 Fetching documents from PostgreSQL...")
            
            result = await session.execute(
                text("""
                    SELECT 
                        id, 
                        file_path, 
                        git_date, 
                        git_commit_sha, 
                        git_author,
                        git_author_email
                    FROM documents 
                    WHERE git_date IS NOT NULL
                    ORDER BY id
                """)
            )
            
            documents = result.fetchall()
            total_docs = len(documents)
            
            logger.info(f"✅ Found {total_docs} documents with git_date in PostgreSQL")
            
            # Process in batches
            for i in range(0, total_docs, batch_size):
                batch = documents[i:i+batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_docs + batch_size - 1) // batch_size
                
                logger.info(f"\n📦 Processing Batch {batch_num}/{total_batches} ({len(batch)} documents)")
                
                # Prepare updates
                ids_to_update = []
                metadatas_to_update = []
                
                for doc in batch:
                    doc_id, file_path, git_date, sha, author, email = doc
                    total_processed += 1
                    
                    try:
                        # Convert git_date to timestamp
                        if git_date:
                            timestamp = git_date.timestamp()
                        else:
                            total_skipped += 1
                            continue
                        
                        # Get existing metadata from ChromaDB
                        try:
                            existing = collection.get(
                                ids=[str(doc_id)],
                                include=["metadatas"]
                            )
                            
                            if not existing or not existing.get("ids"):
                                logger.debug(f"   ⚠️ Document {doc_id} not found in ChromaDB, skipping")
                                total_skipped += 1
                                continue
                            
                            # Get existing metadata and update it
                            existing_metadata = existing["metadatas"][0] if existing["metadatas"] else {}
                            
                            # Update with git metadata as timestamps
                            updated_metadata = existing_metadata.copy()
                            updated_metadata.update({
                                "git_date": timestamp,  # ✅ Unix timestamp
                                "git_commit_sha": sha[:8] if sha else "",
                                "git_author": author if author else ""
                            })
                            
                            ids_to_update.append(str(doc_id))
                            metadatas_to_update.append(updated_metadata)
                            total_updated += 1
                            
                        except Exception as e:
                            logger.warning(f"   ⚠️ Error getting document {doc_id}: {e}")
                            total_errors += 1
                            continue
                        
                    except Exception as e:
                        logger.error(f"   ❌ Error processing document {doc_id}: {e}")
                        total_errors += 1
                        continue
                
                # Update batch in ChromaDB
                if ids_to_update and not dry_run:
                    try:
                        logger.info(f"   ✅ Updating {len(ids_to_update)} documents in ChromaDB...")
                        await chroma.update_embeddings(
                            embeddings=[],  # Empty, we're only updating metadata
                            metadatas=metadatas_to_update,
                            ids=ids_to_update,
                            documents=None
                        )
                        logger.info(f"   ✅ Batch {batch_num} updated successfully")
                    except Exception as e:
                        logger.error(f"   ❌ Error updating batch: {e}")
                        total_errors += len(ids_to_update)
                elif ids_to_update and dry_run:
                    logger.info(f"   🔍 [DRY RUN] Would update {len(ids_to_update)} documents")
                
                # Progress report
                progress = (i + len(batch)) / total_docs * 100
                logger.info(f"   Progress: {progress:.1f}% ({i + len(batch)}/{total_docs})")
        
        # Final report
        print("\n" + "="*80)
        print("FINAL REPORT")
        print("="*80)
        print(f"\n📊 Statistics:")
        print(f"   Total Processed: {total_processed}")
        print(f"   Successfully Updated: {total_updated}")
        print(f"   Skipped: {total_skipped}")
        print(f"   Errors: {total_errors}")
        
        if dry_run:
            print(f"\n🔍 DRY RUN: No changes were made")
            print(f"   Run without --dry-run to apply changes")
        else:
            print(f"\n✅ UPDATE COMPLETE!")
            print(f"   {total_updated} documents now have git_date as timestamps")
        
        # Verify a sample
        if not dry_run and total_updated > 0:
            print(f"\n🔍 Verification (sample of 3 documents):")
            sample = collection.get(limit=3, include=["metadatas"])
            for i, (doc_id, meta) in enumerate(zip(sample["ids"], sample["metadatas"]), 1):
                git_date = meta.get('git_date')
                print(f"\n   Document {i}:")
                print(f"   ID: {doc_id}")
                print(f"   git_date: {git_date}")
                if isinstance(git_date, (int, float)):
                    readable = datetime.fromtimestamp(git_date)
                    print(f"   ✅ TIMESTAMP (readable: {readable})")
                else:
                    print(f"   ⚠️ {type(git_date).__name__}")
        
        print("\n" + "="*80)
        return total_updated, total_errors
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 0, 1


async def main():
    parser = argparse.ArgumentParser(
        description="Update ChromaDB metadata from PostgreSQL"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually update, just report what would be done"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of documents to process per batch (default: 100)"
    )
    
    args = parser.parse_args()
    
    updated, errors = await update_chromadb_metadata(
        dry_run=args.dry_run,
        batch_size=args.batch_size
    )
    
    # Exit code
    if errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

