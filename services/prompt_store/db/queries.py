"""Database query utilities for Prompt Store service.

Provides common database operations and query helpers.
"""

import json
from typing import Union, Dict, List, Any, Optional, Tuple
from .connection import prompt_store_db_connection


def execute_query(query: str, params: Optional[Tuple] = None,
                  fetch_one: bool = False, fetch_all: bool = False) -> Union[None, Dict, List[Dict]]:
    """Execute a database query with proper connection management."""
    with prompt_store_db_connection() as conn:
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
            raise e


def serialize_json(obj: Any) -> str:
    """Serialize object to JSON string."""
    if obj is None:
        return 'null'
    return json.dumps(obj, default=str)


def deserialize_json(json_str: str) -> Any:
    """Deserialize JSON string to object."""
    if not json_str or json_str == 'null':
        return None
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None


def build_where_clause(filters: Dict[str, Any]) -> Tuple[str, Tuple]:
    """Build WHERE clause from filters dictionary."""
    if not filters:
        return "", ()

    conditions = []
    params = []

    for key, value in filters.items():
        if value is not None:
            if key.endswith('__gt'):
                field = key[:-4]
                conditions.append(f"{field} > ?")
                params.append(value)
            elif key.endswith('__gte'):
                field = key[:-5]
                conditions.append(f"{field} >= ?")
                params.append(value)
            elif key.endswith('__lt'):
                field = key[:-4]
                conditions.append(f"{field} < ?")
                params.append(value)
            elif key.endswith('__lte'):
                field = key[:-5]
                conditions.append(f"{field} <= ?")
                params.append(value)
            elif key.endswith('__in'):
                field = key[:-4]
                if isinstance(value, list) and value:
                    placeholders = ','.join('?' * len(value))
                    conditions.append(f"{field} IN ({placeholders})")
                    params.extend(value)
            elif key.endswith('__contains'):
                field = key[:-10]
                conditions.append(f"{field} LIKE ?")
                params.append(f"%{value}%")
            else:
                conditions.append(f"{key} = ?")
                params.append(value)

    where_clause = " AND ".join(conditions) if conditions else ""
    return where_clause, tuple(params)


def build_order_clause(order_by: Optional[str] = None, order_direction: str = 'ASC') -> str:
    """Build ORDER BY clause."""
    if not order_by:
        return ""

    direction = 'DESC' if order_direction.upper() == 'DESC' else 'ASC'
    return f"ORDER BY {order_by} {direction}"


def build_limit_clause(limit: Optional[int] = None, offset: Optional[int] = 0) -> Tuple[str, Tuple]:
    """Build LIMIT and OFFSET clause."""
    if not limit:
        return "", ()

    return "LIMIT ? OFFSET ?", (limit, offset or 0)


def execute_paged_query(table: str, filters: Optional[Dict[str, Any]] = None,
                       order_by: Optional[str] = None, order_direction: str = 'ASC',
                       limit: Optional[int] = None, offset: Optional[int] = 0) -> Dict[str, Any]:
    """Execute a paged query with filtering and sorting."""
    where_clause, where_params = build_where_clause(filters or {})
    order_clause = build_order_clause(order_by, order_direction)
    limit_clause, limit_params = build_limit_clause(limit, offset)

    # Build count query
    count_query = f"SELECT COUNT(*) as total FROM {table}"
    if where_clause:
        count_query += f" WHERE {where_clause}"

    # Build data query
    data_query = f"SELECT * FROM {table}"
    if where_clause:
        data_query += f" WHERE {where_clause}"
    if order_clause:
        data_query += f" {order_clause}"
    if limit_clause:
        data_query += f" {limit_clause}"

    # Execute queries
    count_result = execute_query(count_query, where_params, fetch_one=True)
    total = count_result['total'] if count_result else 0

    all_params = where_params + limit_params
    items = execute_query(data_query, all_params, fetch_all=True) or []

    has_more = limit and offset is not None and (offset + limit) < total

    return {
        "items": items,
        "total": total,
        "has_more": has_more,
        "limit": limit,
        "offset": offset or 0
    }


def execute_search_query(search_term: str, table: str = 'prompts',
                        search_fields: Optional[List[str]] = None,
                        filters: Optional[Dict[str, Any]] = None,
                        limit: int = 50) -> List[Dict[str, Any]]:
    """Execute a full-text search query."""
    if not search_term:
        return []

    # Use FTS table for content search
    fts_table = f"{table}_fts"
    search_fields = search_fields or ['name', 'category', 'description', 'content', 'tags']

    # Build FTS query
    fts_query = f"SELECT rowid FROM {fts_table} WHERE {' OR '.join([f'{field} MATCH ?' for field in search_fields])}"
    search_params = [f'"{search_term}"'] * len(search_fields)

    # Execute FTS query to get rowids
    fts_results = execute_query(fts_query, tuple(search_params), fetch_all=True)
    if not fts_results:
        return []

    rowids = [str(row['rowid']) for row in fts_results]

    # Get actual records
    placeholders = ','.join('?' * len(rowids))
    data_query = f"SELECT * FROM {table} WHERE rowid IN ({placeholders})"

    # Apply additional filters
    if filters:
        where_clause, filter_params = build_where_clause(filters)
        if where_clause:
            data_query += f" AND {where_clause}"
            search_params.extend(filter_params)

    data_query += f" LIMIT {limit}"

    return execute_query(data_query, tuple(rowids), fetch_all=True) or []
