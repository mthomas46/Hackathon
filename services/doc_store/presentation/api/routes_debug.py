"""Debug routes for testing tags flow directly.

This module provides simplified endpoints that bypass complex architecture
to isolate where tags are being lost.
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/debug", tags=["debug"])


@router.post("/documents/direct-sql")
async def create_document_direct_sql(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create document with DIRECT SQL - bypasses ALL layers.
    
    This tests if tags CAN be stored at the database level.
    """
    try:
        db_path = "/app/services/doc_store/data/doc_store.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get tags from request
        tags = body.get('tags', [])
        tags_json = json.dumps(tags)
        
        # Direct SQL insert
        cursor.execute(
            """
            INSERT INTO documents (id, content, content_hash, metadata, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                body['id'],
                body['content'],
                "direct-sql-hash",
                "{}",
                tags_json,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            )
        )
        conn.commit()
        
        # Verify what was stored
        cursor.execute("SELECT id, tags FROM documents WHERE id = ?", (body['id'],))
        result = cursor.fetchone()
        
        conn.close()
        
        return {
            "success": True,
            "method": "direct-sql",
            "tags_sent": tags,
            "tags_json": tags_json,
            "tags_stored": result[1] if result else None,
            "message": "✅ Direct SQL insert successful"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "❌ Direct SQL insert failed"
        }


@router.post("/documents/via-queries")
async def create_document_via_queries(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create document using queries.py functions.
    
    This tests if tags work through the query layer.
    """
    try:
        from services.doc_store.db.queries import insert_document
        
        tags = body.get('tags', [])
        
        # Use the insert_document function from queries.py
        insert_document(
            doc_id=body['id'],
            content=body['content'],
            content_hash="via-queries-hash",
            metadata={},
            tags=tags,
            correlation_id=None
        )
        
        # Verify what was stored
        db_path = "/app/services/doc_store/data/doc_store.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, tags FROM documents WHERE id = ?", (body['id'],))
        result = cursor.fetchone()
        conn.close()
        
        return {
            "success": True,
            "method": "via-queries",
            "tags_sent": tags,
            "tags_stored": result[1] if result else None,
            "message": "✅ Insert via queries.py successful"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": __import__('traceback').format_exc(),
            "message": "❌ Insert via queries.py failed"
        }


@router.post("/documents/via-repository")
async def create_document_via_repository(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create document using Repository layer.
    
    This tests if tags work through the repository.
    """
    try:
        from services.doc_store.domain.documents.repository import DocumentRepository
        from services.doc_store.domain.entities import Document
        from services.doc_store.db.connection import get_document_connection_string
        
        tags = body.get('tags', [])
        
        # Create Document entity
        doc = Document(
            id=body['id'],
            content=body['content'],
            content_hash="via-repo-hash",
            metadata={},
            tags=tags,
            correlation_id=None
        )
        
        # Save via repository
        repo = DocumentRepository(get_document_connection_string())
        saved_doc = await repo.save(doc)
        
        return {
            "success": True,
            "method": "via-repository",
            "tags_sent": tags,
            "tags_in_entity": saved_doc.tags,
            "tags_in_dict": saved_doc.to_dict().get('tags'),
            "message": "✅ Insert via repository successful"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": __import__('traceback').format_exc(),
            "message": "❌ Insert via repository failed"
        }


@router.post("/documents/via-service")
async def create_document_via_service(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create document using Service layer.
    
    This tests if tags work through the service.
    """
    try:
        from services.doc_store.domain.documents.service import DocumentService
        
        tags = body.get('tags', [])
        
        # Create via service
        service = DocumentService()
        doc = await service.create({
            "id": body['id'],
            "content": body['content'],
            "metadata": {},
            "tags": tags,
            "correlation_id": None
        })
        
        return {
            "success": True,
            "method": "via-service",
            "tags_sent": tags,
            "tags_in_doc": doc.tags,
            "tags_in_dict": doc.to_dict().get('tags'),
            "message": "✅ Insert via service successful"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": __import__('traceback').format_exc(),
            "message": "❌ Insert via service failed"
        }


@router.get("/documents/{doc_id}/tags-debug")
async def get_document_tags_debug(doc_id: str) -> Dict[str, Any]:
    """
    Get document with detailed tags debugging info.
    """
    try:
        db_path = "/app/services/doc_store/data/doc_store.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, content, tags, metadata FROM documents WHERE id = ?",
            (doc_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {
                "success": False,
                "message": "Document not found"
            }
        
        tags_raw = result[2]
        
        return {
            "success": True,
            "id": result[0],
            "tags_raw": tags_raw,
            "tags_type": str(type(tags_raw)),
            "tags_length": len(tags_raw) if tags_raw else 0,
            "tags_parsed": json.loads(tags_raw) if tags_raw else None,
            "is_empty_array": tags_raw == "[]",
            "content_length": len(result[1]) if result[1] else 0,
            "metadata": result[3]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/test-flow")
async def test_complete_flow(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test all layers sequentially to find where tags are lost.
    
    Returns detailed results from each layer.
    """
    results = {
        "tags_input": body.get('tags', []),
        "layers": {}
    }
    
    base_id = body.get('id', 'flow-test')
    
    # Test 1: Direct SQL
    try:
        result = await create_document_direct_sql({
            **body,
            "id": f"{base_id}-sql"
        })
        results["layers"]["1_direct_sql"] = result
    except Exception as e:
        results["layers"]["1_direct_sql"] = {"error": str(e)}
    
    # Test 2: Via queries
    try:
        result = await create_document_via_queries({
            **body,
            "id": f"{base_id}-queries"
        })
        results["layers"]["2_via_queries"] = result
    except Exception as e:
        results["layers"]["2_via_queries"] = {"error": str(e)}
    
    # Test 3: Via repository
    try:
        result = await create_document_via_repository({
            **body,
            "id": f"{base_id}-repo"
        })
        results["layers"]["3_via_repository"] = result
    except Exception as e:
        results["layers"]["3_via_repository"] = {"error": str(e)}
    
    # Test 4: Via service
    try:
        result = await create_document_via_service({
            **body,
            "id": f"{base_id}-service"
        })
        results["layers"]["4_via_service"] = result
    except Exception as e:
        results["layers"]["4_via_service"] = {"error": str(e)}
    
    # Summary
    results["summary"] = {
        "layers_tested": 4,
        "layers_successful": sum(1 for layer in results["layers"].values() if layer.get("success")),
        "layers_with_tags": sum(
            1 for layer in results["layers"].values() 
            if layer.get("success") and layer.get("tags_stored") not in [None, "[]", []]
        )
    }
    
    return results

