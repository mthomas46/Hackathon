"""Data browser infrastructure for Frontend service.

Provides read-only browsing capabilities for doc_store and prompt-store data
with caching, filtering, and pagination support.
"""
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from services.shared.utilities import utc_now
from .shared_utils import get_doc_store_url, get_prompt_store_url, get_frontend_clients


class DataBrowser:
    """Read-only data browser for doc_store and prompt-store services."""

    def __init__(self):
        self._cache = {
            "doc_store": {
                "documents": [],
                "analyses": [],
                "quality": {},
                "style_examples": {},
                "last_updated": None
            },
            "prompt_store": {
                "prompts": [],
                "analytics": {},
                "ab_tests": [],
                "last_updated": None
            }
        }
        self._cache_ttl = 60  # Cache for 60 seconds

    def is_cache_fresh(self, store: str) -> bool:
        """Check if cache is still fresh for a given store."""
        last_updated = self._cache[store]["last_updated"]
        if not last_updated:
            return False
        return (utc_now() - last_updated).total_seconds() < self._cache_ttl

    async def get_doc_store_documents(
        self,
        limit: int = 50,
        offset: int = 0,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get documents from doc_store with pagination."""
        if not force_refresh and self.is_cache_fresh("doc_store"):
            documents = self._cache["doc_store"]["documents"]
            start_idx = offset
            end_idx = offset + limit
            return {
                "documents": documents[start_idx:end_idx] if start_idx < len(documents) else [],
                "total": len(documents),
                "limit": limit,
                "offset": offset,
                "cached": True
            }

        try:
            clients = get_frontend_clients()
            doc_store_url = get_doc_store_url()

            # Get document list
            list_response = await clients.get_json(f"{doc_store_url}/documents/_list", {"limit": 1000})
            documents = list_response.get("items", [])

            # Update cache
            self._cache["doc_store"]["documents"] = documents
            self._cache["doc_store"]["last_updated"] = utc_now()

            # Return paginated results
            start_idx = offset
            end_idx = offset + limit
            return {
                "documents": documents[start_idx:end_idx] if start_idx < len(documents) else [],
                "total": len(documents),
                "limit": limit,
                "offset": offset,
                "cached": False
            }

        except Exception as e:
            return {
                "documents": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "error": str(e),
                "cached": False
            }

    async def get_doc_store_document(self, doc_id: str) -> Dict[str, Any]:
        """Get a specific document by ID."""
        try:
            clients = get_frontend_clients()
            doc_store_url = get_doc_store_url()

            response = await clients.get_json(f"{doc_store_url}/documents/{doc_id}")
            return {"document": response, "error": None}

        except Exception as e:
            return {"document": None, "error": str(e)}

    async def get_doc_store_analyses(
        self,
        document_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get analyses from doc_store with optional filtering."""
        if not force_refresh and self.is_cache_fresh("doc_store"):
            analyses = self._cache["doc_store"]["analyses"]
            # Filter by document_id if provided
            if document_id:
                analyses = [a for a in analyses if a.get("document_id") == document_id]

            start_idx = offset
            end_idx = offset + limit
            return {
                "analyses": analyses[start_idx:end_idx] if start_idx < len(analyses) else [],
                "total": len(analyses),
                "limit": limit,
                "offset": offset,
                "cached": True
            }

        try:
            clients = get_frontend_clients()
            doc_store_url = get_doc_store_url()

            params = {"limit": 1000}
            if document_id:
                params["document_id"] = document_id

            response = await clients.get_json(f"{doc_store_url}/analyses", params)
            analyses = response.get("items", [])

            # Update cache if no document filter
            if not document_id:
                self._cache["doc_store"]["analyses"] = analyses
                self._cache["doc_store"]["last_updated"] = utc_now()

            # Return paginated results
            start_idx = offset
            end_idx = offset + limit
            return {
                "analyses": analyses[start_idx:end_idx] if start_idx < len(analyses) else [],
                "total": len(analyses),
                "limit": limit,
                "offset": offset,
                "cached": False
            }

        except Exception as e:
            return {
                "analyses": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "error": str(e),
                "cached": False
            }

    async def get_doc_store_quality(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get document quality metrics."""
        if not force_refresh and self.is_cache_fresh("doc_store"):
            return {"quality": self._cache["doc_store"]["quality"], "cached": True}

        try:
            clients = get_frontend_clients()
            doc_store_url = get_doc_store_url()

            response = await clients.get_json(f"{doc_store_url}/documents/quality")

            # Update cache
            self._cache["doc_store"]["quality"] = response
            self._cache["doc_store"]["last_updated"] = utc_now()

            return {"quality": response, "cached": False}

        except Exception as e:
            return {"quality": {}, "error": str(e), "cached": False}

    async def get_doc_store_style_examples(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get style examples by programming language."""
        if not force_refresh and self.is_cache_fresh("doc_store"):
            return {"style_examples": self._cache["doc_store"]["style_examples"], "cached": True}

        try:
            clients = get_frontend_clients()
            doc_store_url = get_doc_store_url()

            response = await clients.get_json(f"{doc_store_url}/style/examples")

            # Update cache
            self._cache["doc_store"]["style_examples"] = response
            self._cache["doc_store"]["last_updated"] = utc_now()

            return {"style_examples": response, "cached": False}

        except Exception as e:
            return {"style_examples": {}, "error": str(e), "cached": False}

    async def get_prompt_store_prompts(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Get prompts from prompt-store with optional filtering."""
        if not force_refresh and self.is_cache_fresh("prompt_store"):
            prompts = self._cache["prompt_store"]["prompts"]
            # Filter by category if provided
            if category:
                prompts = [p for p in prompts if p.get("category") == category]

            start_idx = offset
            end_idx = offset + limit
            return {
                "prompts": prompts[start_idx:end_idx] if start_idx < len(prompts) else [],
                "total": len(prompts),
                "limit": limit,
                "offset": offset,
                "cached": True
            }

        try:
            clients = get_frontend_clients()
            prompt_store_url = get_prompt_store_url()

            params = {"limit": 1000}
            if category:
                params["category"] = category

            response = await clients.get_json(f"{prompt_store_url}/prompts", params)
            prompts = response.get("prompts", [])

            # Update cache if no category filter
            if not category:
                self._cache["prompt_store"]["prompts"] = prompts
                self._cache["prompt_store"]["last_updated"] = utc_now()

            # Return paginated results
            start_idx = offset
            end_idx = offset + limit
            return {
                "prompts": prompts[start_idx:end_idx] if start_idx < len(prompts) else [],
                "total": len(prompts),
                "limit": limit,
                "offset": offset,
                "cached": False
            }

        except Exception as e:
            return {
                "prompts": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "error": str(e),
                "cached": False
            }

    async def get_prompt_store_analytics(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get prompt store analytics."""
        if not force_refresh and self.is_cache_fresh("prompt_store"):
            return {"analytics": self._cache["prompt_store"]["analytics"], "cached": True}

        try:
            clients = get_frontend_clients()
            prompt_store_url = get_prompt_store_url()

            response = await clients.get_json(f"{prompt_store_url}/analytics")

            # Update cache
            self._cache["prompt_store"]["analytics"] = response
            self._cache["prompt_store"]["last_updated"] = utc_now()

            return {"analytics": response, "cached": False}

        except Exception as e:
            return {"analytics": {}, "error": str(e), "cached": False}

    async def get_doc_store_search(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search documents in doc_store."""
        try:
            clients = get_frontend_clients()
            doc_store_url = get_doc_store_url()

            params = {"q": query, "limit": limit}
            response = await clients.get_json(f"{doc_store_url}/search", params)

            return {
                "results": response.get("results", []),
                "total": response.get("total", 0),
                "query": query,
                "limit": limit
            }

        except Exception as e:
            return {
                "results": [],
                "total": 0,
                "query": query,
                "limit": limit,
                "error": str(e)
            }

    def get_doc_store_categories(self) -> List[str]:
        """Get unique categories from cached documents."""
        documents = self._cache["doc_store"]["documents"]
        categories = set()
        for doc in documents:
            if doc.get("metadata", {}).get("category"):
                categories.add(doc["metadata"]["category"])
        return sorted(list(categories))

    def get_doc_store_languages(self) -> List[str]:
        """Get unique programming languages from cached style examples."""
        style_examples = self._cache["doc_store"]["style_examples"]
        languages = set()
        for lang_data in style_examples.values():
            if isinstance(lang_data, dict) and "language" in lang_data:
                languages.add(lang_data["language"])
        return sorted(list(languages))

    def get_prompt_store_categories(self) -> List[str]:
        """Get unique categories from cached prompts."""
        prompts = self._cache["prompt_store"]["prompts"]
        categories = set()
        for prompt in prompts:
            if prompt.get("category"):
                categories.add(prompt["category"])
        return sorted(list(categories))


# Global instance
data_browser = DataBrowser()


def get_doc_store_summary() -> Dict[str, Any]:
    """Get a summary of doc_store data."""
    docs = data_browser._cache["doc_store"]["documents"]
    analyses = data_browser._cache["doc_store"]["analyses"]
    quality = data_browser._cache["doc_store"]["quality"]

    return {
        "total_documents": len(docs),
        "total_analyses": len(analyses),
        "categories": data_browser.get_doc_store_categories(),
        "languages": data_browser.get_doc_store_languages(),
        "quality_metrics": quality.get("metrics", {}),
        "stale_documents": quality.get("stale_documents", []),
        "last_updated": data_browser._cache["doc_store"]["last_updated"]
    }


def get_prompt_store_summary() -> Dict[str, Any]:
    """Get a summary of prompt-store data."""
    prompts = data_browser._cache["prompt_store"]["prompts"]
    analytics = data_browser._cache["prompt_store"]["analytics"]

    return {
        "total_prompts": len(prompts),
        "categories": data_browser.get_prompt_store_categories(),
        "analytics": analytics,
        "last_updated": data_browser._cache["prompt_store"]["last_updated"]
    }
