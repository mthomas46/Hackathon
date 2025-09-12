"""Peers Routes for Orchestrator Service"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/peers")
async def list_peers():
    """List peer services."""
    return {
        "peers": [
            {"name": "doc-store", "url": "http://doc-store:8080", "status": "healthy"},
            {"name": "analyzer", "url": "http://analyzer:8080", "status": "healthy"},
            {"name": "interpreter", "url": "http://interpreter:8080", "status": "healthy"}
        ],
        "total": 3
    }
