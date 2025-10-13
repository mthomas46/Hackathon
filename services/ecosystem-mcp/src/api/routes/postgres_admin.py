"""
PostgreSQL administration and exploration endpoints.

Provides API for viewing database schema and running queries.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...storage import get_database

logger = logging.getLogger(__name__)

router = APIRouter()


class QueryRequest(BaseModel):
    """Model for executing SQL queries."""
    query: str = Field(..., description="SQL query to execute", max_length=5000)
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum rows to return")


@router.get(
    "/postgres/info",
    summary="Get PostgreSQL server info",
    description="Get PostgreSQL server version and connection information"
)
async def get_postgres_info():
    """
    Get PostgreSQL server information.
    
    Returns:
        Server version, database name, and connection details.
    """
    try:
        db = get_database()
        
        async with db.session() as session:
            from sqlalchemy import text
            
            # Get version
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            
            # Get current database
            result = await session.execute(text("SELECT current_database()"))
            database = result.scalar()
            
            # Get database size
            result = await session.execute(text(
                "SELECT pg_size_pretty(pg_database_size(current_database()))"
            ))
            db_size = result.scalar()
            
            # Get connection info
            result = await session.execute(text(
                """
                SELECT count(*) as connections,
                       max(backend_start) as oldest_connection
                FROM pg_stat_activity
                WHERE datname = current_database()
                """
            ))
            conn_info = result.fetchone()
            
            # Get database stats
            result = await session.execute(text(
                """
                SELECT numbackends, xact_commit, xact_rollback,
                       blks_read, blks_hit, tup_returned, tup_fetched,
                       tup_inserted, tup_updated, tup_deleted
                FROM pg_stat_database
                WHERE datname = current_database()
                """
            ))
            stats = result.fetchone()
            
            # Calculate cache hit ratio
            blks_hit = stats[4] if stats and len(stats) > 4 else 0
            blks_read = stats[3] if stats and len(stats) > 3 else 0
            total_blks = blks_hit + blks_read
            cache_hit_ratio = (blks_hit / total_blks * 100) if total_blks > 0 else 0
            
            return JSONResponse(content={
                "timestamp": datetime.now().isoformat(),
                "server": {
                    "version": version,
                    "database": database,
                    "size": db_size
                },
                "connections": {
                    "active": conn_info[0] if conn_info else 0,
                    "oldest": conn_info[1].isoformat() if conn_info and conn_info[1] else None
                },
                "stats": {
                    "active_backends": stats[0] if stats else 0,
                    "transactions_committed": stats[1] if stats and len(stats) > 1 else 0,
                    "transactions_rolled_back": stats[2] if stats and len(stats) > 2 else 0,
                    "blocks_read": stats[3] if stats and len(stats) > 3 else 0,
                    "blocks_hit": stats[4] if stats and len(stats) > 4 else 0,
                    "cache_hit_ratio": cache_hit_ratio,
                    "tuples_returned": stats[5] if stats and len(stats) > 5 else 0,
                    "tuples_fetched": stats[6] if stats and len(stats) > 6 else 0,
                    "tuples_inserted": stats[7] if stats and len(stats) > 7 else 0,
                    "tuples_updated": stats[8] if stats and len(stats) > 8 else 0,
                    "tuples_deleted": stats[9] if stats and len(stats) > 9 else 0,
                }
            })
    
    except Exception as e:
        logger.error(f"Error getting PostgreSQL info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get PostgreSQL info: {str(e)}"
        )


@router.get(
    "/postgres/tables",
    summary="List database tables",
    description="Get list of all tables in the current database"
)
async def list_postgres_tables():
    """
    List all tables in the database.
    
    Returns:
        List of tables with row counts and sizes.
    """
    try:
        db = get_database()
        
        async with db.session() as session:
            from sqlalchemy import text
            
            # Get all tables with stats
            result = await session.execute(text(
                """
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
                    n_live_tup as row_count,
                    n_dead_tup as dead_rows,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """
            ))
            
            tables = []
            for row in result:
                tables.append({
                    "schema": row[0],
                    "name": row[1],
                    "size": row[2],
                    "size_bytes": row[3],
                    "row_count": row[4],
                    "dead_rows": row[5],
                    "last_vacuum": row[6].isoformat() if row[6] else None,
                    "last_autovacuum": row[7].isoformat() if row[7] else None,
                    "last_analyze": row[8].isoformat() if row[8] else None,
                    "last_autoanalyze": row[9].isoformat() if row[9] else None,
                })
            
            return JSONResponse(content={
                "timestamp": datetime.now().isoformat(),
                "total_tables": len(tables),
                "tables": tables
            })
    
    except Exception as e:
        logger.error(f"Error listing PostgreSQL tables: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list PostgreSQL tables: {str(e)}"
        )


@router.get(
    "/postgres/table/{table_name}",
    summary="Get table details",
    description="Get detailed information about a specific table"
)
async def get_postgres_table(table_name: str):
    """
    Get detailed information about a table.
    
    Args:
        table_name: Name of the table
    
    Returns:
        Table schema, columns, indexes, and sample data.
    """
    try:
        db = get_database()
        
        async with db.session() as session:
            from sqlalchemy import text
            
            # Get columns
            result = await session.execute(text(
                """
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = :table_name
                ORDER BY ordinal_position
                """
            ), {"table_name": table_name})
            
            columns = []
            for row in result:
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "max_length": row[2],
                    "nullable": row[3] == "YES",
                    "default": row[4]
                })
            
            if not columns:
                raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
            
            # Get indexes
            result = await session.execute(text(
                """
                SELECT
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE tablename = :table_name
                """
            ), {"table_name": table_name})
            
            indexes = []
            for row in result:
                indexes.append({
                    "name": row[0],
                    "definition": row[1]
                })
            
            # Get row count
            result = await session.execute(text(
                f"SELECT COUNT(*) FROM {table_name}"
            ))
            row_count = result.scalar()
            
            # Get sample data (first 10 rows)
            result = await session.execute(text(
                f"SELECT * FROM {table_name} LIMIT 10"
            ))
            
            sample_data = []
            for row in result:
                sample_data.append(dict(row._mapping))
            
            return JSONResponse(content={
                "table_name": table_name,
                "row_count": row_count,
                "columns": columns,
                "indexes": indexes,
                "sample_data": sample_data,
                "timestamp": datetime.now().isoformat()
            })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PostgreSQL table details: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get table details: {str(e)}"
        )


@router.post(
    "/postgres/query",
    summary="Execute SQL query",
    description="Execute a read-only SQL query"
)
async def execute_postgres_query(request: QueryRequest):
    """
    Execute a SQL query.
    
    NOTE: Only SELECT queries are allowed for safety.
    
    Args:
        request: Query string and limit
    
    Returns:
        Query results with column names and rows.
    """
    try:
        # Basic safety check - only allow SELECT queries
        query_upper = request.query.strip().upper()
        if not query_upper.startswith("SELECT") and not query_upper.startswith("WITH"):
            raise HTTPException(
                status_code=400,
                detail="Only SELECT and WITH queries are allowed"
            )
        
        # Block dangerous keywords
        dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE"]
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise HTTPException(
                    status_code=400,
                    detail=f"Query contains forbidden keyword: {keyword}"
                )
        
        db = get_database()
        
        async with db.session() as session:
            from sqlalchemy import text
            
            # Add LIMIT if not present
            query = request.query.strip()
            if "LIMIT" not in query_upper:
                query += f" LIMIT {request.limit}"
            
            # Execute query
            result = await session.execute(text(query))
            
            # Get column names
            columns = list(result.keys()) if result.keys() else []
            
            # Get rows
            rows = []
            for row in result:
                rows.append(dict(row._mapping))
            
            return JSONResponse(content={
                "query": request.query,
                "columns": columns,
                "row_count": len(rows),
                "rows": rows,
                "timestamp": datetime.now().isoformat()
            })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing PostgreSQL query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )


@router.get(
    "/postgres/activity",
    summary="Get active connections",
    description="Get list of active database connections and queries"
)
async def get_postgres_activity():
    """
    Get active database connections.
    
    Returns:
        List of active connections with their queries and durations.
    """
    try:
        db = get_database()
        
        async with db.session() as session:
            from sqlalchemy import text
            
            result = await session.execute(text(
                """
                SELECT 
                    pid,
                    usename,
                    application_name,
                    client_addr,
                    backend_start,
                    state,
                    query_start,
                    query,
                    EXTRACT(EPOCH FROM (NOW() - query_start)) as duration_seconds
                FROM pg_stat_activity
                WHERE datname = current_database()
                  AND pid != pg_backend_pid()
                ORDER BY query_start DESC NULLS LAST
                LIMIT 50
                """
            ))
            
            connections = []
            for row in result:
                connections.append({
                    "pid": row[0],
                    "user": row[1],
                    "application": row[2],
                    "client_addr": str(row[3]) if row[3] else None,
                    "backend_start": row[4].isoformat() if row[4] else None,
                    "state": row[5],
                    "query_start": row[6].isoformat() if row[6] else None,
                    "query": row[7][:200] if row[7] else None,  # Truncate long queries
                    "duration_seconds": float(row[8]) if row[8] else None
                })
            
            return JSONResponse(content={
                "timestamp": datetime.now().isoformat(),
                "total_connections": len(connections),
                "connections": connections
            })
    
    except Exception as e:
        logger.error(f"Error getting PostgreSQL activity: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get database activity: {str(e)}"
        )


@router.get(
    "/postgres/locks",
    summary="Get database locks",
    description="Get information about current database locks"
)
async def get_postgres_locks():
    """
    Get database lock information.
    
    Returns:
        List of active locks and blocked queries.
    """
    try:
        db = get_database()
        
        async with db.session() as session:
            from sqlalchemy import text
            
            result = await session.execute(text(
                """
                SELECT 
                    l.locktype,
                    l.relation::regclass as relation,
                    l.mode,
                    l.granted,
                    a.pid,
                    a.usename,
                    a.query,
                    a.state
                FROM pg_locks l
                LEFT JOIN pg_stat_activity a ON l.pid = a.pid
                WHERE l.database = (SELECT oid FROM pg_database WHERE datname = current_database())
                ORDER BY l.granted, a.query_start
                LIMIT 100
                """
            ))
            
            locks = []
            for row in result:
                locks.append({
                    "type": row[0],
                    "relation": str(row[1]) if row[1] else None,
                    "mode": row[2],
                    "granted": row[3],
                    "pid": row[4],
                    "user": row[5],
                    "query": row[6][:200] if row[6] else None,
                    "state": row[7]
                })
            
            # Get blocked queries
            result = await session.execute(text(
                """
                SELECT 
                    blocked_locks.pid AS blocked_pid,
                    blocked_activity.usename AS blocked_user,
                    blocking_locks.pid AS blocking_pid,
                    blocking_activity.usename AS blocking_user,
                    blocked_activity.query AS blocked_query,
                    blocking_activity.query AS blocking_query
                FROM pg_catalog.pg_locks blocked_locks
                JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
                JOIN pg_catalog.pg_locks blocking_locks 
                    ON blocking_locks.locktype = blocked_locks.locktype
                    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
                    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                    AND blocking_locks.pid != blocked_locks.pid
                JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
                WHERE NOT blocked_locks.granted
                """
            ))
            
            blocked = []
            for row in result:
                blocked.append({
                    "blocked_pid": row[0],
                    "blocked_user": row[1],
                    "blocking_pid": row[2],
                    "blocking_user": row[3],
                    "blocked_query": row[4][:200] if row[4] else None,
                    "blocking_query": row[5][:200] if row[5] else None,
                })
            
            return JSONResponse(content={
                "timestamp": datetime.now().isoformat(),
                "total_locks": len(locks),
                "locks": locks,
                "blocked_queries": blocked
            })
    
    except Exception as e:
        logger.error(f"Error getting PostgreSQL locks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get database locks: {str(e)}"
        )

