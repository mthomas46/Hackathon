"""Confluence-specific normalizers for architecture diagrams."""

import re
from typing import Any, Dict, List

import httpx

from .base import BaseNormalizer, BaseFileNormalizer

# Import models from parent module
try:
    from ..models import (
        ArchitectureComponent,
        ArchitectureConnection,
        NormalizedArchitectureData,
    )
except ImportError:
    # Fallback for different import contexts
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    from models import (
        ArchitectureComponent,
        ArchitectureConnection,
        NormalizedArchitectureData,
    )


class ConfluenceNormalizer(BaseNormalizer):
    """Normalizer for Confluence page diagrams."""

    async def normalize(self, board_id: str, token: str) -> NormalizedArchitectureData:
        """Fetch and normalize Confluence page data."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://your-domain.atlassian.net/wiki/rest/api/content/{board_id}"
            headers = {"Authorization": f"Bearer {token}"}

            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                return self._normalize_confluence_data(data)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError("Invalid Confluence API token")
                elif e.response.status_code == 404:
                    raise ValueError(f"Confluence page {board_id} not found")
                else:
                    raise ValueError(f"Confluence API error: {e.response.status_code}")

    def _normalize_confluence_data(
        self, data: Dict[str, Any]
    ) -> NormalizedArchitectureData:
        """Convert Confluence API response to normalized format."""
        components = []
        connections = []

        # Confluence pages may contain embedded diagrams or structured content
        # This is a simplified implementation - in practice, you'd need to parse
        # the page content for diagram data

        # For now, create a basic component representing the page
        page_title = data.get("title", f"Page {data.get('id', '')}")

        component = ArchitectureComponent(
            id=data.get("id", ""),
            type="service",
            name=page_title,
            description=f"Confluence page: {page_title}",
        )
        components.append(component)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,
            metadata={"source": "confluence", "page_id": data.get("id", "")},
        )

    @classmethod
    def get_description(cls) -> str:
        return "Confluence page diagram normalizer"

    @classmethod
    def get_auth_type(cls) -> str:
        return "Bearer token"


class ConfluenceFileNormalizer(BaseFileNormalizer):
    """File-based normalizer for Confluence exports."""

    async def normalize_file(
        self, file_content: bytes, filename: str, file_format: str
    ) -> NormalizedArchitectureData:
        """Normalize Confluence exported file."""
        if file_format.lower() in ["xml", "html"]:
            return await self._normalize_confluence_markup(
                file_content, filename, file_format
            )
        else:
            raise ValueError(
                f"Confluence file normalizer does not support format: {file_format}"
            )

    async def _normalize_confluence_markup(
        self, file_content: bytes, filename: str, file_format: str
    ) -> NormalizedArchitectureData:
        """Normalize Confluence XML/HTML export."""
        try:
            content = file_content.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Invalid {file_format.upper()} file encoding: {e}")

        components = []
        connections = []

        # For Confluence, we'll extract basic page information
        # In a real implementation, you'd parse the XML/HTML structure
        # For now, create a basic component representing the page

        # Extract title from content (basic parsing)
        title = "Unknown Page"
        if file_format.lower() == "xml":
            # Basic XML title extraction
            title_match = re.search(
                r"<title[^>]*>([^<]+)</title>", content, re.IGNORECASE
            )
            if title_match:
                title = title_match.group(1).strip()
        elif file_format.lower() == "html":
            # Basic HTML title extraction
            title_match = re.search(
                r"<title[^>]*>([^<]+)</title>", content, re.IGNORECASE
            )
            if title_match:
                title = title_match.group(1).strip()

        component = ArchitectureComponent(
            id=f"page_{hash(filename)}",
            type="service",
            name=title,
            description=f"Confluence page from {filename}",
        )
        components.append(component)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,
            metadata={
                "source": "confluence",
                "filename": filename,
                "format": file_format,
            },
        )

    @classmethod
    def get_supported_formats(cls) -> List[Dict[str, Any]]:
        return [
            {
                "format": "xml",
                "description": "Confluence XML export",
                "capabilities": ["basic_content"],
                "export_method": "Space Tools > Content Tools > Export > XML",
            },
            {
                "format": "html",
                "description": "Confluence HTML export",
                "capabilities": ["basic_content"],
                "export_method": "Space Tools > Content Tools > Export > HTML",
            },
        ]

