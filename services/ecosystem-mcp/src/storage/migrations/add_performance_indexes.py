"""
Add Performance Indexes - Phase 2 Optimization

Creates indexes to speed up:
- Duplicate detection (content_hash)
- Commit queries (commit_sha)
- Service + file lookups (service_name, file_path)
- Time-based queries (created_at)

Expected improvement: 5-10× faster queries
"""

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def add_performance_indexes(session: AsyncSession) -> dict:
    """
    Add performance indexes to documents table.
    
    Args:
        session: Database session
        
    Returns:
        Dict with results
    """
    results = {
        "indexes_created": [],
        "indexes_skipped": [],
        "errors": []
    }
    
    # Define indexes to create
    indexes = [
        {
            "name": "idx_documents_content_hash",
            "table": "documents",
            "columns": ["content_hash"],
            "purpose": "Fast duplicate detection"
        },
        {
            "name": "idx_documents_commit_sha",
            "table": "documents",
            "columns": ["git_commit_sha"],
            "purpose": "Fast commit queries"
        },
        {
            "name": "idx_documents_service_file",
            "table": "documents",
            "columns": ["service_name", "file_path"],
            "purpose": "Fast service + file lookups"
        },
        {
            "name": "idx_documents_created_at_desc",
            "table": "documents",
            "columns": ["created_at DESC"],
            "purpose": "Fast time-based queries"
        },
        {
            "name": "idx_documents_is_latest",
            "table": "documents",
            "columns": ["is_latest"],
            "purpose": "Fast latest version queries"
        },
        {
            "name": "idx_documents_service_latest",
            "table": "documents",
            "columns": ["service_name", "is_latest"],
            "purpose": "Fast service + latest queries"
        }
    ]
    
    logger.info(f"Creating {len(indexes)} performance indexes...")
    
    for index_def in indexes:
        try:
            # Check if index already exists
            check_query = text("""
                SELECT 1 FROM pg_indexes 
                WHERE indexname = :index_name
            """)
            result = await session.execute(check_query, {"index_name": index_def["name"]})
            exists = result.scalar_one_or_none()
            
            if exists:
                logger.info(f"  ⏭️  Index {index_def['name']} already exists, skipping")
                results["indexes_skipped"].append(index_def["name"])
                continue
            
            # Create index
            columns_str = ", ".join(index_def["columns"])
            create_query = text(f"""
                CREATE INDEX CONCURRENTLY {index_def['name']} 
                ON {index_def['table']} ({columns_str})
            """)
            
            logger.info(f"  🔨 Creating index {index_def['name']} ({index_def['purpose']})...")
            await session.execute(create_query)
            await session.commit()
            
            results["indexes_created"].append(index_def["name"])
            logger.info(f"  ✅ Created index {index_def['name']}")
            
        except Exception as e:
            error_msg = f"Failed to create index {index_def['name']}: {str(e)}"
            logger.error(f"  ❌ {error_msg}")
            results["errors"].append(error_msg)
            # Don't fail the whole operation, continue with other indexes
            try:
                await session.rollback()
            except:
                pass
    
    # Summary
    logger.info(f"\n📊 Index creation summary:")
    logger.info(f"  ✅ Created: {len(results['indexes_created'])}")
    logger.info(f"  ⏭️  Skipped: {len(results['indexes_skipped'])}")
    logger.info(f"  ❌ Errors: {len(results['errors'])}")
    
    return results


async def remove_performance_indexes(session: AsyncSession) -> dict:
    """
    Remove performance indexes (for rollback).
    
    Args:
        session: Database session
        
    Returns:
        Dict with results
    """
    results = {
        "indexes_removed": [],
        "errors": []
    }
    
    index_names = [
        "idx_documents_content_hash",
        "idx_documents_commit_sha",
        "idx_documents_service_file",
        "idx_documents_created_at_desc",
        "idx_documents_is_latest",
        "idx_documents_service_latest"
    ]
    
    logger.info(f"Removing {len(index_names)} performance indexes...")
    
    for index_name in index_names:
        try:
            drop_query = text(f"DROP INDEX CONCURRENTLY IF EXISTS {index_name}")
            await session.execute(drop_query)
            await session.commit()
            
            results["indexes_removed"].append(index_name)
            logger.info(f"  ✅ Removed index {index_name}")
            
        except Exception as e:
            error_msg = f"Failed to remove index {index_name}: {str(e)}"
            logger.error(f"  ❌ {error_msg}")
            results["errors"].append(error_msg)
            try:
                await session.rollback()
            except:
                pass
    
    return results


async def analyze_index_usage(session: AsyncSession) -> dict:
    """
    Analyze index usage statistics.
    
    Args:
        session: Database session
        
    Returns:
        Dict with index statistics
    """
    query = text("""
        SELECT 
            schemaname,
            tablename,
            indexname,
            idx_scan as scans,
            idx_tup_read as tuples_read,
            idx_tup_fetch as tuples_fetched,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size
        FROM pg_stat_user_indexes
        WHERE indexname LIKE 'idx_documents_%'
        ORDER BY idx_scan DESC
    """)
    
    result = await session.execute(query)
    rows = result.fetchall()
    
    stats = {
        "indexes": [],
        "total_scans": 0,
        "total_size_bytes": 0
    }
    
    for row in rows:
        index_info = {
            "name": row.indexname,
            "table": row.tablename,
            "scans": row.scans or 0,
            "tuples_read": row.tuples_read or 0,
            "tuples_fetched": row.tuples_fetched or 0,
            "size": row.index_size
        }
        stats["indexes"].append(index_info)
        stats["total_scans"] += index_info["scans"]
    
    return stats

