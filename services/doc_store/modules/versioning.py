# ============================================================================
# VERSIONING MODULE
# ============================================================================
"""
Document versioning and history tracking for Doc Store service.

Provides comprehensive version control capabilities including:
- Automatic version creation on document updates
- Version history retrieval and comparison
- Version metadata and change tracking
- Rollback and version management operations
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from services.shared.utilities import utc_now

from .shared_utils import execute_db_query, safe_json_loads


def create_document_version(
    document_id: str,
    content: str,
    content_hash: str,
    metadata: Optional[Dict[str, Any]] = None,
    change_summary: Optional[str] = None,
    changed_by: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new version of a document."""
    try:
        # Get the next version number
        version_result = execute_db_query(
            "SELECT COALESCE(MAX(version_number), 0) + 1 as next_version FROM document_versions WHERE document_id = ?",
            (document_id,),
            fetch_one=True
        )
        next_version = version_result['next_version'] if version_result else 1

        # Create version record
        version_id = f"{document_id}:v{next_version}"
        version_data = {
            "id": version_id,
            "document_id": document_id,
            "version_number": next_version,
            "content": content,
            "content_hash": content_hash,
            "metadata": json.dumps(metadata or {}),
            "change_summary": change_summary or "Document update",
            "changed_by": changed_by or "system",
            "created_at": utc_now().isoformat()
        }

        # Insert version record
        execute_db_query("""
            INSERT INTO document_versions
            (id, document_id, version_number, content, content_hash, metadata, change_summary, changed_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            version_data["id"],
            version_data["document_id"],
            version_data["version_number"],
            version_data["content"],
            version_data["content_hash"],
            version_data["metadata"],
            version_data["change_summary"],
            version_data["changed_by"],
            version_data["created_at"]
        ))

        return version_data

    except Exception as e:
        raise Exception(f"Failed to create document version: {str(e)}")


def get_document_versions(document_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Get version history for a document."""
    try:
        # Get version count
        count_result = execute_db_query(
            "SELECT COUNT(*) as total FROM document_versions WHERE document_id = ?",
            (document_id,),
            fetch_one=True
        )
        total_count = count_result['total'] if count_result else 0

        # Get versions
        versions = execute_db_query("""
            SELECT id, version_number, content_hash, change_summary, changed_by, created_at,
                   LENGTH(content) as content_size
            FROM document_versions
            WHERE document_id = ?
            ORDER BY version_number DESC
            LIMIT ? OFFSET ?
        """, (document_id, limit, offset), fetch_all=True)

        version_list = []
        for row in versions:
            version_list.append({
                "id": row['id'],
                "version_number": row['version_number'],
                "content_hash": row['content_hash'],
                "change_summary": row['change_summary'],
                "changed_by": row['changed_by'],
                "created_at": row['created_at'],
                "content_size": row['content_size']
            })

        return {
            "document_id": document_id,
            "total_versions": total_count,
            "versions": version_list,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise Exception(f"Failed to retrieve document versions: {str(e)}")


def get_document_version(document_id: str, version_number: int) -> Dict[str, Any]:
    """Get a specific version of a document."""
    try:
        result = execute_db_query("""
            SELECT id, document_id, version_number, content, content_hash, metadata,
                   change_summary, changed_by, created_at
            FROM document_versions
            WHERE document_id = ? AND version_number = ?
        """, (document_id, version_number), fetch_one=True)

        if not result:
            raise Exception(f"Version {version_number} not found for document {document_id}")

        return {
            "id": result['id'],
            "document_id": result['document_id'],
            "version_number": result['version_number'],
            "content": result['content'],
            "content_hash": result['content_hash'],
            "metadata": safe_json_loads(result['metadata']),
            "change_summary": result['change_summary'],
            "changed_by": result['changed_by'],
            "created_at": result['created_at']
        }

    except Exception as e:
        raise Exception(f"Failed to retrieve document version: {str(e)}")


def compare_document_versions(document_id: str, version_a: int, version_b: int) -> Dict[str, Any]:
    """Compare two versions of a document."""
    try:
        # Get both versions
        version_a_data = get_document_version(document_id, version_a)
        version_b_data = get_document_version(document_id, version_b)

        # Basic comparison
        comparison = {
            "document_id": document_id,
            "version_a": {
                "number": version_a,
                "created_at": version_a_data["created_at"],
                "changed_by": version_a_data["changed_by"],
                "change_summary": version_a_data["change_summary"]
            },
            "version_b": {
                "number": version_b,
                "created_at": version_b_data["created_at"],
                "changed_by": version_b_data["changed_by"],
                "change_summary": version_b_data["change_summary"]
            },
            "differences": {}
        }

        # Content comparison (simplified)
        if version_a_data["content"] != version_b_data["content"]:
            comparison["differences"]["content_changed"] = True
            comparison["differences"]["content_size_change"] = (
                len(version_b_data["content"]) - len(version_a_data["content"])
            )
        else:
            comparison["differences"]["content_changed"] = False

        # Metadata comparison
        metadata_a = version_a_data["metadata"]
        metadata_b = version_b_data["metadata"]

        if metadata_a != metadata_b:
            comparison["differences"]["metadata_changed"] = True
            # Find specific metadata differences
            metadata_diff = {}
            all_keys = set(metadata_a.keys()) | set(metadata_b.keys())

            for key in all_keys:
                val_a = metadata_a.get(key)
                val_b = metadata_b.get(key)
                if val_a != val_b:
                    metadata_diff[key] = {"from": val_a, "to": val_b}

            comparison["differences"]["metadata_changes"] = metadata_diff
        else:
            comparison["differences"]["metadata_changed"] = False

        # Hash comparison
        comparison["differences"]["hash_changed"] = (
            version_a_data["content_hash"] != version_b_data["content_hash"]
        )

        return comparison

    except Exception as e:
        raise Exception(f"Failed to compare document versions: {str(e)}")


def rollback_document_to_version(document_id: str, version_number: int, changed_by: Optional[str] = None) -> Dict[str, Any]:
    """Rollback a document to a previous version."""
    try:
        # Get the target version
        target_version = get_document_version(document_id, version_number)

        # Update the current document
        execute_db_query("""
            UPDATE documents
            SET content = ?, content_hash = ?, metadata = ?
            WHERE id = ?
        """, (
            target_version["content"],
            target_version["content_hash"],
            json.dumps(target_version["metadata"]),
            document_id
        ))

        # Create a new version record for the rollback
        rollback_summary = f"Rolled back to version {version_number}"
        create_document_version(
            document_id=document_id,
            content=target_version["content"],
            content_hash=target_version["content_hash"],
            metadata=target_version["metadata"],
            change_summary=rollback_summary,
            changed_by=changed_by or "system"
        )

        return {
            "document_id": document_id,
            "rolled_back_to_version": version_number,
            "rollback_summary": rollback_summary,
            "content_hash": target_version["content_hash"]
        }

    except Exception as e:
        raise Exception(f"Failed to rollback document: {str(e)}")


def cleanup_old_versions(document_id: str, keep_versions: int = 10) -> Dict[str, Any]:
    """Clean up old versions, keeping only the most recent ones."""
    try:
        # Count total versions
        count_result = execute_db_query(
            "SELECT COUNT(*) as total FROM document_versions WHERE document_id = ?",
            (document_id,),
            fetch_one=True
        )
        total_versions = count_result['total'] if count_result else 0

        if total_versions <= keep_versions:
            return {"message": f"No cleanup needed. Total versions: {total_versions}, keep: {keep_versions}"}

        # Delete old versions
        versions_to_delete = total_versions - keep_versions
        execute_db_query("""
            DELETE FROM document_versions
            WHERE document_id = ? AND version_number NOT IN (
                SELECT version_number FROM document_versions
                WHERE document_id = ?
                ORDER BY version_number DESC
                LIMIT ?
            )
        """, (document_id, document_id, keep_versions))

        return {
            "document_id": document_id,
            "versions_deleted": versions_to_delete,
            "versions_kept": keep_versions,
            "total_versions_before": total_versions
        }

    except Exception as e:
        raise Exception(f"Failed to cleanup old versions: {str(e)}")
