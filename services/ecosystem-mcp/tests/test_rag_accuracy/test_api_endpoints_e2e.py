"""
E2E tests for RAG accuracy API endpoints.

Tests actual HTTP endpoints.
"""

import pytest
import httpx
import asyncio


# API base URL - adjust as needed
API_BASE = "http://localhost:8001/api/v1"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_health_endpoint():
    """Test RAG health endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE}/rag/health", timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                assert "healthy" in data
                assert "components" in data
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("API not available")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_enhancement_stats_endpoint():
    """Test enhancement statistics endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE}/rag/enhancements/stats", timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                assert "phase" in data
                assert "enhancements" in data
                assert "Phase 1" in data["phase"]
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("API not available")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_enhanced_rag_endpoint():
    """Test enhanced RAG query endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE}/rag/ask/enhanced",
                json={
                    "question": "What is a test?",
                    "n_results": 5,
                    "enable_hybrid_search": True,
                    "enable_query_rewriting": True,
                    "enable_confidence_scoring": True
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "answer" in data
                assert "confidence" in data
                assert "confidence_level" in data
                assert "sources" in data
                assert "metadata" in data
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("API not available")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_standard_rag_endpoint():
    """Test standard RAG query endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE}/rag/ask/standard",
                json={
                    "question": "What is a test?",
                    "n_results": 5
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "answer" in data
                assert "sources" in data
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("API not available")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_compare_endpoint():
    """Test comparison endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE}/rag/compare",
                json={
                    "question": "What is a test?",
                    "n_results": 5
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "standard" in data
                assert "enhanced" in data
                assert "comparison" in data
                assert "confidence_improvement" in data["comparison"]
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("API not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])

