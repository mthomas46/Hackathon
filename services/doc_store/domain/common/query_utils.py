"""Common database query utilities for Doc Store service.

Reduces code duplication by providing reusable query patterns
and database operation helpers.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timezone

from services.doc_store.db.connection import doc_store_db_connection


def execute_query_safe(
    query: str,
    params: Optional[Tuple] = None,
    fetch_one: bool = False,
    fetch_all: bool = False,
) -> Union[None, Dict, List[Dict]]:
    """Execute database query with automatic connection management and error handling.

    Args:
        query: SQL query string
        params: Query parameters
        fetch_one: Whether to fetch a single row
        fetch_all: Whether to fetch all rows

    Returns:
        Query result(s) or None

    Raises:
        DatabaseException: If query execution fails
    """
    from .error_utils import handle_database_error

    with doc_store_db_connection() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute(query, params or ())

            if fetch_one:
                row = cursor.fetchone()
                return dict(row) if row else None
            elif fetch_all:
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                conn.commit()
                return None

        except Exception as e:
            conn.rollback()
            handle_database_error(f"query_execution: {query}", str(e))


def build_where_clause(conditions: Dict[str, Any]) -> Tuple[str, Tuple]:
    """Build WHERE clause from conditions dictionary.

    Args:
        conditions: Dictionary of field -> value conditions

    Returns:
        Tuple of (where_clause, params)
    """
    if not conditions:
        return "", ()

    clauses = []
    params = []

    for field, value in conditions.items():
        if isinstance(value, (list, tuple)):
            # IN clause
            placeholders = ",".join("?" * len(value))
            clauses.append(f"{field} IN ({placeholders})")
            params.extend(value)
        elif value is None:
            # IS NULL
            clauses.append(f"{field} IS NULL")
        else:
            # Equality
            clauses.append(f"{field} = ?")
            params.append(value)

    where_clause = " WHERE " + " AND ".join(clauses)
    return where_clause, tuple(params)


def build_pagination_clause(page: int = 1, page_size: int = 50) -> Tuple[str, Tuple]:
    """Build pagination clause.

    Args:
        page: Page number (1-based)
        page_size: Number of items per page

    Returns:
        Tuple of (limit_clause, params)
    """
    offset = (page - 1) * page_size
    return " LIMIT ? OFFSET ?", (page_size, offset)


def get_documents_with_filters(
    filters: Optional[Dict[str, Any]] = None,
    page: int = 1,
    page_size: int = 50,
    order_by: str = "created_at DESC"
) -> Tuple[List[Dict], int]:
    """Get documents with filtering, pagination, and total count.

    Args:
        filters: Optional filters to apply
        page: Page number
        page_size: Items per page
        order_by: Sort order

    Returns:
        Tuple of (documents, total_count)
    """
    base_query = """
        SELECT id, content_hash, metadata, correlation_id, created_at, updated_at
        FROM documents
    """

    # Build WHERE clause
    where_clause, where_params = build_where_clause(filters or {})

    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM documents{where_clause}"
    count_result = execute_query_safe(count_query, where_params, fetch_one=True)
    total_count = count_result["total"] if count_result else 0

    # Get paginated results
    pagination_clause, pagination_params = build_pagination_clause(page, page_size)
    data_query = f"{base_query}{where_clause} ORDER BY {order_by}{pagination_clause}"

    params = where_params + pagination_params
    documents = execute_query_safe(data_query, params, fetch_all=True) or []

    return documents, total_count


def get_document_versions(document_id: str, page: int = 1, page_size: int = 20) -> List[Dict]:
    """Get versions for a specific document.

    Args:
        document_id: Document ID to get versions for
        page: Page number
        page_size: Items per page

    Returns:
        List of document versions
    """
    query = """
        SELECT id, document_id, version_number, content_hash, metadata,
               change_description, created_at
        FROM document_versions
        WHERE document_id = ?
        ORDER BY version_number DESC
    """

    pagination_clause, pagination_params = build_pagination_clause(page, page_size)
    full_query = f"{query}{pagination_clause}"

    return execute_query_safe(full_query, (document_id,) + pagination_params, fetch_all=True) or []


def search_documents_by_content(
    search_term: str,
    filters: Optional[Dict[str, Any]] = None,
    page: int = 1,
    page_size: int = 50
) -> Tuple[List[Dict], int]:
    """Search documents by content with optional filters.

    Args:
        search_term: Term to search for in document content
        filters: Optional additional filters
        page: Page number
        page_size: Items per page

    Returns:
        Tuple of (documents, total_count)
    """
    # Note: This is a simplified search. In production, you'd want FTS (Full-Text Search)
    base_query = """
        SELECT id, content_hash, metadata, correlation_id, created_at, updated_at
        FROM documents
        WHERE content LIKE ?
    """

    search_param = f"%{search_term}%"
    params = [search_param]

    # Add additional filters
    if filters:
        where_clause, filter_params = build_where_clause(filters)
        base_query += where_clause
        params.extend(filter_params)

    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM ({base_query})"
    count_result = execute_query_safe(count_query, tuple(params), fetch_one=True)
    total_count = count_result["total"] if count_result else 0

    # Get paginated results
    pagination_clause, pagination_params = build_pagination_clause(page, page_size)
    full_query = f"{base_query} ORDER BY created_at DESC{pagination_clause}"

    params.extend(pagination_params)
    documents = execute_query_safe(full_query, tuple(params), fetch_all=True) or []

    return documents, total_count


def get_document_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Get document analytics data.

    Args:
        start_date: Optional start date for analytics
        end_date: Optional end date for analytics

    Returns:
        Analytics data dictionary
    """
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date.replace(day=end_date.day - 30)

    params = (start_date, end_date)

    # Document count over time
    count_query = """
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM documents
        WHERE created_at BETWEEN ? AND ?
        GROUP BY DATE(created_at)
        ORDER BY date
    """
    daily_counts = execute_query_safe(count_query, params, fetch_all=True) or []

    # Total documents
    total_query = """
        SELECT COUNT(*) as total
        FROM documents
        WHERE created_at BETWEEN ? AND ?
    """
    total_result = execute_query_safe(total_query, params, fetch_one=True)
    total_docs = total_result["total"] if total_result else 0

    # Documents by type (if type field exists)
    type_query = """
        SELECT
            CASE
                WHEN json_extract(metadata, '$.type') IS NOT NULL
                THEN json_extract(metadata, '$.type')
                ELSE 'unknown'
            END as doc_type,
            COUNT(*) as count
        FROM documents
        WHERE created_at BETWEEN ? AND ?
        GROUP BY doc_type
    """
    type_counts = execute_query_safe(type_query, params, fetch_all=True) or []

    return {
        "total_documents": total_docs,
        "daily_counts": daily_counts,
        "type_breakdown": type_counts,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    }


def get_documents_with_relationships(
    document_id: str,
    relationship_types: Optional[List[str]] = None
) -> List[Dict]:
    """Get documents related to the given document.

    Args:
        document_id: Document ID to find relationships for
        relationship_types: Optional list of relationship types to filter by

    Returns:
        List of related documents with relationship info
    """
    query = """
        SELECT
            r.relationship_type,
            r.strength,
            r.metadata as relationship_metadata,
            d.id,
            d.content_hash,
            d.metadata,
            d.created_at
        FROM document_relationships r
        JOIN documents d ON (
            (r.source_document_id = ? AND r.target_document_id = d.id) OR
            (r.target_document_id = ? AND r.source_document_id = d.id)
        )
        WHERE r.source_document_id = ? OR r.target_document_id = ?
    """

    params = [document_id, document_id, document_id, document_id]

    if relationship_types:
        placeholders = ",".join("?" * len(relationship_types))
        query += f" AND r.relationship_type IN ({placeholders})"
        params.extend(relationship_types)

    query += " ORDER BY r.strength DESC"

    return execute_query_safe(query, tuple(params), fetch_all=True) or []


def cleanup_old_documents(days_to_keep: int = 90) -> int:
    """Clean up old documents based on retention policy.

    Args:
        days_to_keep: Number of days to keep documents

    Returns:
        Number of documents deleted
    """
    from datetime import timedelta

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

    # First, delete related records
    related_queries = [
        "DELETE FROM document_versions WHERE document_id IN (SELECT id FROM documents WHERE created_at < ?)",
        "DELETE FROM document_relationships WHERE source_document_id IN (SELECT id FROM documents WHERE created_at < ?) OR target_document_id IN (SELECT id FROM documents WHERE created_at < ?)",
        "DELETE FROM document_tags WHERE document_id IN (SELECT id FROM documents WHERE created_at < ?)",
        "DELETE FROM notifications WHERE document_id IN (SELECT id FROM documents WHERE created_at < ?)",
        "DELETE FROM lifecycle_events WHERE document_id IN (SELECT id FROM documents WHERE created_at < ?)",
    ]

    for query in related_queries:
        if "target_document_id" in query:
            execute_query_safe(query, (cutoff_date, cutoff_date))
        else:
            execute_query_safe(query, (cutoff_date,))

    # Finally, delete the documents themselves
    delete_query = "DELETE FROM documents WHERE created_at < ?"
    result = execute_query_safe(delete_query, (cutoff_date,))

    # Return number of deleted documents (this is approximate since we don't return row counts)
    return 0  # In a real implementation, you'd track this


def get_system_metrics() -> Dict[str, Any]:
    """Get system metrics for monitoring.

    Returns:
        Dictionary of system metrics
    """
    # Document counts by status/type
    status_query = """
        SELECT
            COUNT(*) as total_documents,
            COUNT(CASE WHEN created_at > datetime('now', '-1 day') THEN 1 END) as documents_last_24h,
            COUNT(CASE WHEN created_at > datetime('now', '-7 day') THEN 1 END) as documents_last_7d,
            COUNT(CASE WHEN updated_at > datetime('now', '-1 hour') THEN 1 END) as recently_updated
        FROM documents
    """

    doc_metrics = execute_query_safe(status_query, fetch_one=True) or {}

    # Database size
    size_query = "SELECT page_count * page_size as size_bytes FROM pragma_page_count(), pragma_page_size()"
    size_result = execute_query_safe(size_query, fetch_one=True)
    db_size = size_result["size_bytes"] if size_result else 0

    # Table row counts
    tables = ["documents", "document_versions", "document_relationships", "document_tags"]
    table_counts = {}

    for table in tables:
        count_query = f"SELECT COUNT(*) as count FROM {table}"
        result = execute_query_safe(count_query, fetch_one=True)
        table_counts[table] = result["count"] if result else 0

    return {
        "documents": doc_metrics,
        "database": {
            "size_bytes": db_size,
            "size_mb": round(db_size / (1024 * 1024), 2)
        },
        "tables": table_counts,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
