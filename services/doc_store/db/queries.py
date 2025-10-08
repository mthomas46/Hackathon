"""Common database query operations for Doc Store service.

Provides reusable query functions to reduce code duplication.
"""

import json
import struct
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from .connection import doc_store_db_connection


def execute_query(
    query: str,
    params: Optional[Tuple] = None,
    fetch_one: bool = False,
    fetch_all: bool = False,
) -> Union[None, Dict, List[Dict]]:
    """Execute a database query with proper connection management."""
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

        except Exception:
            conn.rollback()
            raise


def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
    """Get document by ID."""
    return execute_query(
        "SELECT * FROM documents WHERE id = ?", (document_id,), fetch_one=True
    )


def get_documents_list(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Get list of documents with pagination."""
    return execute_query(
        "SELECT id, content_hash, metadata, created_at FROM documents ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
        fetch_all=True,
    )


def search_documents(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Enhanced multi-tier search with query expansion and relevance scoring.
    
    Search strategy:
    1. Tag-based search (FAST, HIGH PRECISION)
    2. Metadata search (MEDIUM SPEED, GOOD PRECISION)
    3. FTS search with OR logic (FAST, MEDIUM PRECISION)
    4. Content LIKE search (SLOW, LOW PRECISION but comprehensive)
    """
    import re
    from .query_expansion import extract_keywords_with_synonyms
    
    # Extract keywords with synonym expansion
    keywords = extract_keywords_with_synonyms(query)
    
    if not keywords:
        # If no keywords, return empty (query was all stop words)
        return []
    
    # TIER 1: Tag-based search (FASTEST)
    tag_results = _search_by_tags(keywords[:5], limit)
    if tag_results:
        return _fetch_documents_with_score(tag_results, limit)
    
    # TIER 2: Metadata search
    metadata_results = _search_by_metadata(keywords[:5], limit)
    if metadata_results:
        return _fetch_documents_with_score(metadata_results, limit)
    
    # TIER 3: FTS search with OR'd keywords for flexible matching
    fts_query = ' OR '.join(keywords[:5])  # Use top 5 keywords
    
    fts_results = execute_query(
        "SELECT rowid FROM documents_fts WHERE content MATCH ? LIMIT ?",
        (fts_query, limit),
        fetch_all=True,
    )

    if fts_results:
        doc_ids = [str(row["rowid"]) for row in fts_results]
        placeholders = ",".join("?" for _ in doc_ids)
        return execute_query(
            f"SELECT * FROM documents WHERE rowid IN ({placeholders})",
            tuple(doc_ids),
            fetch_all=True,
        )
    
    # TIER 4: Fallback to content LIKE search
    like_conditions = []
    params = []
    for keyword in keywords[:3]:  # Try top 3 keywords
        like_conditions.append("content LIKE ?")
        params.append(f"%{keyword}%")
    
    if like_conditions:
        like_query = f"SELECT rowid FROM documents WHERE {' OR '.join(like_conditions)} LIMIT ?"
        params.append(limit)
        
        fallback_results = execute_query(
            like_query,
            tuple(params),
            fetch_all=True,
        )
        
        if fallback_results:
            doc_ids = [str(row["rowid"]) for row in fallback_results]
            placeholders = ",".join("?" for _ in doc_ids)
            return execute_query(
                f"SELECT * FROM documents WHERE rowid IN ({placeholders})",
                tuple(doc_ids),
                fetch_all=True,
            )
    
    return []


def _search_by_tags(keywords: List[str], limit: int) -> List[Dict[str, Any]]:
    """Search documents by tags with relevance scoring."""
    if not keywords:
        return []
    
    # Build tag search query with scoring
    conditions = []
    params = []
    
    for idx, keyword in enumerate(keywords[:5]):
        # Give higher weight to earlier keywords (more relevant)
        weight = 10 - (idx * 2)
        conditions.append(f"(CASE WHEN tags LIKE ? THEN {weight} ELSE 0 END)")
        params.append(f"%{keyword}%")
    
    scoring_sql = " + ".join(conditions)
    
    # We use scoring_sql 3 times, so we need params 3 times
    all_params = params + params + params + [limit]
    
    query_sql = f"""
        SELECT rowid, ({scoring_sql}) as relevance_score
        FROM documents
        WHERE tags IS NOT NULL AND tags != '[]'
          AND ({scoring_sql}) > 0
        ORDER BY ({scoring_sql}) DESC
        LIMIT ?
    """
    
    return execute_query(query_sql, tuple(all_params), fetch_all=True)


def _search_by_metadata(keywords: List[str], limit: int) -> List[Dict[str, Any]]:
    """Search documents by metadata with relevance scoring."""
    if not keywords:
        return []
    
    # Build metadata search query with scoring
    conditions = []
    params = []
    
    for idx, keyword in enumerate(keywords[:5]):
        weight = 7 - (idx * 1)  # Lower weight than tags
        conditions.append(f"(CASE WHEN metadata LIKE ? THEN {weight} ELSE 0 END)")
        params.append(f"%{keyword}%")
    
    scoring_sql = " + ".join(conditions)
    
    # We use scoring_sql 3 times, so we need params 3 times
    all_params = params + params + params + [limit]
    
    query_sql = f"""
        SELECT rowid, ({scoring_sql}) as relevance_score
        FROM documents
        WHERE metadata IS NOT NULL
          AND ({scoring_sql}) > 0
        ORDER BY ({scoring_sql}) DESC
        LIMIT ?
    """
    
    return execute_query(query_sql, tuple(all_params), fetch_all=True)


def _fetch_documents_with_score(scored_results: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """Fetch full documents from scored search results."""
    if not scored_results:
        return []
    
    doc_ids = [str(row["rowid"]) for row in scored_results[:limit]]
    
    placeholders = ",".join("?" for _ in doc_ids)
    documents = execute_query(
        f"SELECT * FROM documents WHERE rowid IN ({placeholders})",
        tuple(doc_ids),
        fetch_all=True,
    )
    
    # Add relevance scores to documents
    score_map = {str(row["rowid"]): row.get("relevance_score", 0) for row in scored_results}
    for doc in documents:
        doc["relevance_score"] = score_map.get(str(doc.get("rowid", "")), 0)
    
    # Sort by relevance score
    documents.sort(key=lambda d: d.get("relevance_score", 0), reverse=True)
    
    return documents


def insert_document(
    doc_id: str,
    content: str,
    content_hash: str,
    metadata: Dict[str, Any],
    tags: Optional[List[str]] = None,  # ✅ CRITICAL FIX: Add tags parameter
    correlation_id: Optional[str] = None,
) -> None:
    """Insert a new document."""
    from datetime import datetime, timezone
    
    def utc_now():
        """Get current UTC time."""
        return datetime.now(timezone.utc)

    execute_query(
        """
        INSERT INTO documents (id, content, content_hash, metadata, tags, correlation_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            doc_id,
            content,
            content_hash,
            json.dumps(metadata),
            json.dumps(tags or []),  # ✅ CRITICAL FIX: Store tags as JSON
            correlation_id,
            utc_now().isoformat(),
            utc_now().isoformat(),
        ),
    )


def update_document_metadata(doc_id: str, metadata: Dict[str, Any]) -> None:
    """Update document metadata."""
    from services.shared.utilities import utc_now

    execute_query(
        """
        UPDATE documents SET metadata = ?, updated_at = ? WHERE id = ?
    """,
        (json.dumps(metadata), utc_now().isoformat(), doc_id),
    )


def insert_analysis(
    document_id: str,
    analyzer: str,
    model: str,
    prompt_hash: str,
    result: Dict[str, Any],
    score: Optional[float],
    metadata: Optional[Dict[str, Any]],
) -> str:
    """Insert analysis result."""
    import uuid

    from services.shared.utilities import utc_now

    analysis_id = str(uuid.uuid4())
    execute_query(
        """
        INSERT INTO analyses (id, document_id, analyzer, model, prompt_hash, result, score, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            analysis_id,
            document_id,
            analyzer,
            model,
            prompt_hash,
            json.dumps(result),
            score,
            json.dumps(metadata) if metadata else None,
            utc_now().isoformat(),
        ),
    )

    return analysis_id


def get_analyses_by_document(
    document_id: str, limit: int = 100
) -> List[Dict[str, Any]]:
    """Get analyses for a document."""
    return execute_query(
        "SELECT * FROM analyses WHERE document_id = ? ORDER BY created_at DESC LIMIT ?",
        (document_id, limit),
        fetch_all=True,
    )


def insert_bulk_operation(
    operation_id: str,
    operation_type: str,
    total_items: int,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Insert bulk operation record."""
    from services.shared.utilities import utc_now

    execute_query(
        """
        INSERT INTO bulk_operations (operation_id, operation_type, total_items, metadata, created_at)
        VALUES (?, ?, ?, ?, ?)
    """,
        (
            operation_id,
            operation_type,
            total_items,
            json.dumps(metadata) if metadata else None,
            utc_now().isoformat(),
        ),
    )


def update_bulk_operation_status(
    operation_id: str,
    status: str,
    processed_items: int,
    successful_items: int,
    failed_items: int,
    errors: Optional[List[str]] = None,
) -> None:
    """Update bulk operation status."""
    from services.shared.utilities import utc_now

    completed_at = utc_now().isoformat() if status in ["completed", "failed"] else None

    execute_query(
        """
        UPDATE bulk_operations
        SET status = ?, processed_items = ?, successful_items = ?, failed_items = ?,
            errors = ?, completed_at = ?
        WHERE operation_id = ?
    """,
        (
            status,
            processed_items,
            successful_items,
            failed_items,
            json.dumps(errors) if errors else None,
            completed_at,
            operation_id,
        ),
    )


def get_bulk_operation_status(operation_id: str) -> Optional[Dict[str, Any]]:
    """Get bulk operation status."""
    return execute_query(
        "SELECT * FROM bulk_operations WHERE operation_id = ?",
        (operation_id,),
        fetch_one=True,
    )


def list_bulk_operations(
    status: Optional[str] = None, limit: int = 50
) -> List[Dict[str, Any]]:
    """List bulk operations with optional status filter."""
    if status:
        return execute_query(
            "SELECT * FROM bulk_operations WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit),
            fetch_all=True,
        )
    else:
        return execute_query(
            "SELECT * FROM bulk_operations ORDER BY created_at DESC LIMIT ?",
            (limit,),
            fetch_all=True,
        )


# Vector/Embedding Functions

def serialize_vector(vector: List[float]) -> bytes:
    """Serialize a vector to bytes for storage."""
    return struct.pack(f'{len(vector)}f', *vector)


def deserialize_vector(data: bytes) -> List[float]:
    """Deserialize bytes back to vector."""
    num_floats = len(data) // 4
    return list(struct.unpack(f'{num_floats}f', data))


def insert_document_vector(
    document_id: str,
    embedding: List[float],
    vector_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Insert or update document vector embedding."""
    import uuid
    from datetime import datetime, timezone
    
    def utc_now():
        return datetime.now(timezone.utc)
    
    vector_id = str(uuid.uuid4())
    embedding_blob = serialize_vector(embedding)
    
    # Check if vector already exists for this document and model
    existing = execute_query(
        "SELECT id FROM document_vectors WHERE document_id = ? AND vector_model = ?",
        (document_id, vector_model),
        fetch_one=True,
    )
    
    if existing:
        # Update existing
        execute_query(
            """
            UPDATE document_vectors 
            SET embedding = ?, embedding_dimension = ?, metadata = ?
            WHERE id = ?
            """,
            (embedding_blob, len(embedding), json.dumps(metadata) if metadata else None, existing["id"]),
        )
        return existing["id"]
    else:
        # Insert new
        execute_query(
            """
            INSERT INTO document_vectors (id, document_id, vector_model, embedding_dimension, embedding, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vector_id,
                document_id,
                vector_model,
                len(embedding),
                embedding_blob,
                json.dumps(metadata) if metadata else None,
                utc_now().isoformat(),
            ),
        )
        return vector_id


def get_document_vector(document_id: str, vector_model: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get vector embedding for a document."""
    if vector_model:
        result = execute_query(
            "SELECT * FROM document_vectors WHERE document_id = ? AND vector_model = ?",
            (document_id, vector_model),
            fetch_one=True,
        )
    else:
        result = execute_query(
            "SELECT * FROM document_vectors WHERE document_id = ? ORDER BY created_at DESC LIMIT 1",
            (document_id,),
            fetch_one=True,
        )
    
    if result and result.get("embedding"):
        result["embedding"] = deserialize_vector(result["embedding"])
    
    return result


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    # Normalize
    v1_norm = v1 / (np.linalg.norm(v1) + 1e-10)
    v2_norm = v2 / (np.linalg.norm(v2) + 1e-10)
    
    # Dot product
    similarity = float(np.dot(v1_norm, v2_norm))
    
    return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]


def semantic_search_documents(
    query_embedding: List[float],
    limit: int = 50,
    vector_model: Optional[str] = None,
    min_similarity: float = 0.3,
) -> List[Dict[str, Any]]:
    """
    Perform semantic search using vector similarity.
    
    Args:
        query_embedding: Query vector embedding
        limit: Maximum results to return
        vector_model: Specific model to use (None = any model)
        min_similarity: Minimum similarity threshold
    
    Returns:
        List of documents with similarity scores
    """
    # Get all document vectors
    if vector_model:
        vectors = execute_query(
            "SELECT * FROM document_vectors WHERE vector_model = ?",
            (vector_model,),
            fetch_all=True,
        )
    else:
        vectors = execute_query(
            "SELECT * FROM document_vectors",
            fetch_all=True,
        )
    
    if not vectors:
        return []
    
    # Calculate similarities
    similarities = []
    for vec_record in vectors:
        doc_embedding = deserialize_vector(vec_record["embedding"])
        similarity = cosine_similarity(query_embedding, doc_embedding)
        
        if similarity >= min_similarity:
            similarities.append({
                "document_id": vec_record["document_id"],
                "similarity": similarity,
                "vector_model": vec_record["vector_model"],
            })
    
    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Get top documents
    top_similarities = similarities[:limit]
    
    if not top_similarities:
        return []
    
    # Fetch full document data
    doc_ids = [s["document_id"] for s in top_similarities]
    placeholders = ",".join("?" for _ in doc_ids)
    documents = execute_query(
        f"SELECT * FROM documents WHERE id IN ({placeholders})",
        tuple(doc_ids),
        fetch_all=True,
    )
    
    # Add similarity scores to documents
    similarity_map = {s["document_id"]: s["similarity"] for s in top_similarities}
    for doc in documents:
        doc["semantic_similarity"] = similarity_map.get(doc["id"], 0.0)
    
    # Sort by similarity
    documents.sort(key=lambda d: d.get("semantic_similarity", 0.0), reverse=True)
    
    return documents


def get_documents_without_vectors(limit: int = 100) -> List[Dict[str, Any]]:
    """Get documents that don't have vector embeddings yet."""
    return execute_query(
        """
        SELECT d.* FROM documents d
        LEFT JOIN document_vectors dv ON d.id = dv.document_id
        WHERE dv.id IS NULL
        LIMIT ?
        """,
        (limit,),
        fetch_all=True,
    )

def get_document_count() -> int:
    """Get total count of documents."""
    result = execute_query(
        "SELECT COUNT(*) as count FROM documents",
        fetch_one=True
    )
    return result["count"] if result else 0
