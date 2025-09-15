"""Normalizers for different architectural diagram systems."""

import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from services.shared.logging import fire_and_forget
from .models import NormalizedArchitectureData, ArchitectureComponent, ArchitectureConnection


class BaseNormalizer(ABC):
    """Base class for architecture diagram normalizers."""

    @abstractmethod
    async def normalize(self, board_id: str, token: str) -> NormalizedArchitectureData:
        """Normalize diagram data into standard format."""
        pass

    @classmethod
    def get_description(cls) -> str:
        """Get description of this normalizer."""
        return "Base architecture diagram normalizer"

    @classmethod
    def get_auth_type(cls) -> str:
        """Get authentication type required."""
        return "Bearer token"


class MiroNormalizer(BaseNormalizer):
    """Normalizer for Miro whiteboard diagrams."""

    async def normalize(self, board_id: str, token: str) -> NormalizedArchitectureData:
        """Fetch and normalize Miro board data."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://api.miro.com/v2/boards/{board_id}/items"
            headers = {"Authorization": f"Bearer {token}"}

            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                return self._normalize_miro_data(data)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError("Invalid Miro API token")
                elif e.response.status_code == 404:
                    raise ValueError(f"Miro board {board_id} not found")
                else:
                    raise ValueError(f"Miro API error: {e.response.status_code}")

    def _normalize_miro_data(self, data: Dict[str, Any]) -> NormalizedArchitectureData:
        """Convert Miro API response to normalized format."""
        components = []
        connections = []

        # Process Miro items (widgets)
        for item in data.get("data", []):
            item_type = item.get("type", "").lower()

            # Map Miro widget types to architecture components
            if item_type in ["sticky_note", "text"]:
                # Text/sticky notes become components
                component = ArchitectureComponent(
                    id=item.get("id", ""),
                    type="service",  # Default type
                    name=item.get("data", {}).get("content", "").strip()[:50] or f"Component {item.get('id', '')}",
                    description=item.get("data", {}).get("content", "")
                )
                components.append(component)

            elif item_type == "shape":
                # Shapes represent architectural components
                shape_data = item.get("data", {})
                component_type = self._map_shape_to_component_type(shape_data)

                component = ArchitectureComponent(
                    id=item.get("id", ""),
                    type=component_type,
                    name=shape_data.get("content", "").strip()[:50] or f"Component {item.get('id', '')}",
                    description=shape_data.get("content", "")
                )
                components.append(component)

            elif item_type == "line":
                # Lines represent connections
                start_widget = item.get("startWidget", {})
                end_widget = item.get("endWidget", {})

                if start_widget and end_widget:
                    connection = ArchitectureConnection(
                        from_id=start_widget.get("id", ""),
                        to_id=end_widget.get("id", ""),
                        label=item.get("data", {}).get("content", "").strip() or "connects"
                    )
                    connections.append(connection)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,
            metadata={"source": "miro", "board_id": data.get("id", "")}
        )

    def _map_shape_to_component_type(self, shape_data: Dict[str, Any]) -> str:
        """Map Miro shape properties to architecture component types."""
        content = shape_data.get("content", "").lower()

        # Simple content-based mapping
        if any(keyword in content for keyword in ["database", "db", "storage"]):
            return "database"
        elif any(keyword in content for keyword in ["queue", "message", "kafka", "rabbit"]):
            return "queue"
        elif any(keyword in content for keyword in ["ui", "frontend", "web", "app"]):
            return "ui"
        elif any(keyword in content for keyword in ["gateway", "api", "proxy"]):
            return "gateway"
        elif any(keyword in content for keyword in ["function", "lambda", "serverless"]):
            return "function"

        return "service"  # Default

    @classmethod
    def get_description(cls) -> str:
        return "Miro whiteboard diagram normalizer"

    @classmethod
    def get_auth_type(cls) -> str:
        return "Bearer token"


class FigJamNormalizer(BaseNormalizer):
    """Normalizer for Figma FigJam diagrams."""

    async def normalize(self, board_id: str, token: str) -> NormalizedArchitectureData:
        """Fetch and normalize FigJam file data."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://api.figma.com/v1/files/{board_id}"
            headers = {"X-FIGMA-TOKEN": token}

            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                return self._normalize_figjam_data(data)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    raise ValueError("Invalid Figma API token or insufficient permissions")
                elif e.response.status_code == 404:
                    raise ValueError(f"FigJam file {board_id} not found")
                else:
                    raise ValueError(f"Figma API error: {e.response.status_code}")

    def _normalize_figjam_data(self, data: Dict[str, Any]) -> NormalizedArchitectureData:
        """Convert Figma API response to normalized format."""
        components = []
        connections = []

        # Process Figma document nodes
        def process_node(node: Dict[str, Any]):
            node_type = node.get("type", "")

            if node_type in ["FRAME", "GROUP"]:
                # Frames/groups represent components
                component_type = self._map_figma_node_to_component(node)

                component = ArchitectureComponent(
                    id=node.get("id", ""),
                    type=component_type,
                    name=node.get("name", "").strip()[:50] or f"Component {node.get('id', '')}",
                    description=node.get("name", "")
                )
                components.append(component)

            # Process child nodes
            for child in node.get("children", []):
                process_node(child)

        # Process the document
        document = data.get("document", {})
        process_node(document)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,  # FigJam connections would need additional processing
            metadata={"source": "figjam", "file_id": data.get("name", "")}
        )

    def _map_figma_node_to_component(self, node: Dict[str, Any]) -> str:
        """Map Figma node properties to architecture component types."""
        name = node.get("name", "").lower()

        if any(keyword in name for keyword in ["database", "db", "storage", "data"]):
            return "database"
        elif any(keyword in name for keyword in ["queue", "message", "stream"]):
            return "queue"
        elif any(keyword in name for keyword in ["ui", "screen", "page", "frontend"]):
            return "ui"
        elif any(keyword in name for keyword in ["api", "gateway", "proxy"]):
            return "gateway"

        return "service"

    @classmethod
    def get_description(cls) -> str:
        return "Figma FigJam diagram normalizer"

    @classmethod
    def get_auth_type(cls) -> str:
        return "X-FIGMA-TOKEN"


class LucidNormalizer(BaseNormalizer):
    """Normalizer for Lucidchart diagrams."""

    async def normalize(self, board_id: str, token: str) -> NormalizedArchitectureData:
        """Fetch and normalize Lucid document data."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://lucid.app/api/documents/{board_id}/export/json"
            headers = {"Authorization": f"Bearer {token}"}

            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                return self._normalize_lucid_data(data)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError("Invalid Lucid API token")
                elif e.response.status_code == 404:
                    raise ValueError(f"Lucid document {board_id} not found")
                else:
                    raise ValueError(f"Lucid API error: {e.response.status_code}")

    def _normalize_lucid_data(self, data: Dict[str, Any]) -> NormalizedArchitectureData:
        """Convert Lucid API response to normalized format."""
        components = []
        connections = []

        # Lucid returns structured JSON with layers and objects
        layers = data.get("layers", [])
        for layer in layers:
            for obj in layer.get("objects", []):
                obj_type = obj.get("type", "")

                if obj_type in ["rectangle", "circle", "shape"]:
                    # Shapes represent components
                    component_type = self._map_lucid_object_to_component(obj)

                    component = ArchitectureComponent(
                        id=obj.get("id", ""),
                        type=component_type,
                        name=obj.get("text", "").strip()[:50] or f"Component {obj.get('id', '')}",
                        description=obj.get("text", "")
                    )
                    components.append(component)

                elif obj_type == "line":
                    # Lines represent connections
                    connection = ArchitectureConnection(
                        from_id=obj.get("startObjectId", ""),
                        to_id=obj.get("endObjectId", ""),
                        label=obj.get("text", "").strip() or "connects"
                    )
                    connections.append(connection)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,
            metadata={"source": "lucid", "document_id": data.get("id", "")}
        )

    def _map_lucid_object_to_component(self, obj: Dict[str, Any]) -> str:
        """Map Lucid object properties to architecture component types."""
        text = obj.get("text", "").lower()

        if any(keyword in text for keyword in ["database", "db", "storage"]):
            return "database"
        elif any(keyword in text for keyword in ["queue", "message", "event"]):
            return "queue"
        elif any(keyword in text for keyword in ["ui", "frontend", "web"]):
            return "ui"
        elif any(keyword in text for keyword in ["gateway", "api", "proxy"]):
            return "gateway"

        return "service"

    @classmethod
    def get_description(cls) -> str:
        return "Lucidchart diagram normalizer"

    @classmethod
    def get_auth_type(cls) -> str:
        return "Bearer token"


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

    def _normalize_confluence_data(self, data: Dict[str, Any]) -> NormalizedArchitectureData:
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
            description=f"Confluence page: {page_title}"
        )
        components.append(component)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,
            metadata={"source": "confluence", "page_id": data.get("id", "")}
        )

    @classmethod
    def get_description(cls) -> str:
        return "Confluence page diagram normalizer"

    @classmethod
    def get_auth_type(cls) -> str:
        return "Bearer token"


class BaseFileNormalizer(ABC):
    """Base class for file-based architecture diagram normalizers."""

    @abstractmethod
    async def normalize_file(self, file_content: bytes, filename: str, file_format: str) -> NormalizedArchitectureData:
        """Normalize diagram data from uploaded file."""
        pass

    @classmethod
    def get_supported_formats(cls) -> List[Dict[str, Any]]:
        """Get supported file formats for this normalizer."""
        return []

    @classmethod
    def supports_format(cls, file_format: str) -> bool:
        """Check if this normalizer supports the given file format."""
        return file_format.lower() in [fmt["format"] for fmt in cls.get_supported_formats()]


class MiroFileNormalizer(BaseFileNormalizer):
    """File-based normalizer for Miro diagram exports."""

    async def normalize_file(self, file_content: bytes, filename: str, file_format: str) -> NormalizedArchitectureData:
        """Normalize Miro exported file."""
        if file_format.lower() == "json":
            return await self._normalize_miro_json(file_content, filename)
        else:
            raise ValueError(f"Miro file normalizer does not support format: {file_format}")

    async def _normalize_miro_json(self, file_content: bytes, filename: str) -> NormalizedArchitectureData:
        """Normalize Miro JSON export."""
        import json
        try:
            data = json.loads(file_content.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid Miro JSON file: {e}")

        # Miro JSON export structure
        components = []
        connections = []

        # Process Miro widgets/items
        items = data.get("widgets", data.get("data", []))
        for item in items:
            item_type = item.get("type", "").lower()

            # Map Miro widget types to architecture components
            if item_type in ["sticky_note", "text", "shape"]:
                # Text/sticky notes and shapes become components
                component_type = self._map_miro_widget_to_component(item)

                component = ArchitectureComponent(
                    id=item.get("id", ""),
                    type=component_type,
                    name=item.get("text", "").strip()[:50] or f"Component {item.get('id', '')}",
                    description=item.get("text", "")
                )
                components.append(component)

            elif item_type == "line":
                # Lines represent connections
                start_widget = item.get("startWidget", {})
                end_widget = item.get("endWidget", {})

                if start_widget and end_widget:
                    connection = ArchitectureConnection(
                        from_id=start_widget.get("id", ""),
                        to_id=end_widget.get("id", ""),
                        label=item.get("text", "").strip() or "connects"
                    )
                    connections.append(connection)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,
            metadata={"source": "miro", "filename": filename, "format": "json"}
        )

    def _map_miro_widget_to_component(self, widget: Dict[str, Any]) -> str:
        """Map Miro widget properties to architecture component types."""
        text = widget.get("text", "").lower()

        # Simple content-based mapping
        if any(keyword in text for keyword in ["database", "db", "storage"]):
            return "database"
        elif any(keyword in text for keyword in ["queue", "message", "kafka", "rabbit"]):
            return "queue"
        elif any(keyword in text for keyword in ["ui", "frontend", "web", "app"]):
            return "ui"
        elif any(keyword in text for keyword in ["gateway", "api", "proxy"]):
            return "gateway"
        elif any(keyword in text for keyword in ["function", "lambda", "serverless"]):
            return "function"

        return "service"  # Default

    @classmethod
    def get_supported_formats(cls) -> List[Dict[str, Any]]:
        return [
            {
                "format": "json",
                "description": "Miro JSON export (developer format)",
                "capabilities": ["full_structural_data"],
                "export_method": "Miro Developer API or manual export"
            }
        ]


class FigJamFileNormalizer(BaseFileNormalizer):
    """File-based normalizer for Figma FigJam exports."""

    async def normalize_file(self, file_content: bytes, filename: str, file_format: str) -> NormalizedArchitectureData:
        """Normalize FigJam exported file."""
        if file_format.lower() == "json":
            return await self._normalize_figjam_json(file_content, filename)
        else:
            raise ValueError(f"FigJam file normalizer does not support format: {file_format}")

    async def _normalize_figjam_json(self, file_content: bytes, filename: str) -> NormalizedArchitectureData:
        """Normalize FigJam JSON export."""
        import json
        try:
            data = json.loads(file_content.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid FigJam JSON file: {e}")

        components = []
        connections = []

        # Process Figma document nodes
        def process_node(node: Dict[str, Any]):
            node_type = node.get("type", "")

            if node_type in ["FRAME", "GROUP", "RECTANGLE", "ELLIPSE"]:
                # Frames/groups represent components
                component_type = self._map_figma_node_to_component(node)

                component = ArchitectureComponent(
                    id=node.get("id", ""),
                    type=component_type,
                    name=node.get("name", "").strip()[:50] or f"Component {node.get('id', '')}",
                    description=node.get("name", "")
                )
                components.append(component)

            # Process child nodes
            for child in node.get("children", []):
                process_node(child)

        # Process the document
        document = data.get("document", data)
        process_node(document)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,  # FigJam connections would need additional processing
            metadata={"source": "figjam", "filename": filename, "format": "json"}
        )

    def _map_figma_node_to_component(self, node: Dict[str, Any]) -> str:
        """Map Figma node properties to architecture component types."""
        name = node.get("name", "").lower()

        if any(keyword in name for keyword in ["database", "db", "storage", "data"]):
            return "database"
        elif any(keyword in name for keyword in ["queue", "message", "stream"]):
            return "queue"
        elif any(keyword in name for keyword in ["ui", "screen", "page", "frontend"]):
            return "ui"
        elif any(keyword in name for keyword in ["api", "gateway", "proxy"]):
            return "gateway"

        return "service"

    @classmethod
    def get_supported_formats(cls) -> List[Dict[str, Any]]:
        return [
            {
                "format": "json",
                "description": "Figma FigJam JSON export",
                "capabilities": ["structural_data"],
                "export_method": "Figma API or File > Export > JSON"
            }
        ]


class LucidFileNormalizer(BaseFileNormalizer):
    """File-based normalizer for Lucidchart exports."""

    async def normalize_file(self, file_content: bytes, filename: str, file_format: str) -> NormalizedArchitectureData:
        """Normalize Lucid exported file."""
        if file_format.lower() == "json":
            return await self._normalize_lucid_json(file_content, filename)
        else:
            raise ValueError(f"Lucid file normalizer does not support format: {file_format}")

    async def _normalize_lucid_json(self, file_content: bytes, filename: str) -> NormalizedArchitectureData:
        """Normalize Lucid JSON export."""
        import json
        try:
            data = json.loads(file_content.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid Lucid JSON file: {e}")

        components = []
        connections = []

        # Lucid JSON export structure varies, but typically has objects array
        objects = data.get("objects", data.get("data", []))
        for obj in objects:
            obj_type = obj.get("type", "").lower()

            if obj_type in ["rectangle", "circle", "shape", "text"]:
                # Shapes represent components
                component_type = self._map_lucid_object_to_component(obj)

                component = ArchitectureComponent(
                    id=obj.get("id", ""),
                    type=component_type,
                    name=obj.get("text", "").strip()[:50] or f"Component {obj.get('id', '')}",
                    description=obj.get("text", "")
                )
                components.append(component)

            elif obj_type in ["line", "connector"]:
                # Lines represent connections
                connection = ArchitectureConnection(
                    from_id=obj.get("startObjectId", ""),
                    to_id=obj.get("endObjectId", ""),
                    label=obj.get("text", "").strip() or "connects"
                )
                connections.append(connection)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,
            metadata={"source": "lucid", "filename": filename, "format": "json"}
        )

    def _map_lucid_object_to_component(self, obj: Dict[str, Any]) -> str:
        """Map Lucid object properties to architecture component types."""
        text = obj.get("text", "").lower()

        if any(keyword in text for keyword in ["database", "db", "storage"]):
            return "database"
        elif any(keyword in text for keyword in ["queue", "message", "event"]):
            return "queue"
        elif any(keyword in text for keyword in ["ui", "frontend", "web"]):
            return "ui"
        elif any(keyword in text for keyword in ["gateway", "api", "proxy"]):
            return "gateway"

        return "service"

    @classmethod
    def get_supported_formats(cls) -> List[Dict[str, Any]]:
        return [
            {
                "format": "json",
                "description": "Lucidchart JSON export",
                "capabilities": ["full_structural_data"],
                "export_method": "Lucid API or manual JSON export"
            }
        ]


class ConfluenceFileNormalizer(BaseFileNormalizer):
    """File-based normalizer for Confluence exports."""

    async def normalize_file(self, file_content: bytes, filename: str, file_format: str) -> NormalizedArchitectureData:
        """Normalize Confluence exported file."""
        if file_format.lower() in ["xml", "html"]:
            return await self._normalize_confluence_markup(file_content, filename, file_format)
        else:
            raise ValueError(f"Confluence file normalizer does not support format: {file_format}")

    async def _normalize_confluence_markup(self, file_content: bytes, filename: str, file_format: str) -> NormalizedArchitectureData:
        """Normalize Confluence XML/HTML export."""
        try:
            content = file_content.decode('utf-8')
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
            import re
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
        elif file_format.lower() == "html":
            # Basic HTML title extraction
            import re
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()

        component = ArchitectureComponent(
            id=f"page_{hash(filename)}",
            type="service",
            name=title,
            description=f"Confluence page from {filename}"
        )
        components.append(component)

        return NormalizedArchitectureData(
            components=components,
            connections=connections,
            metadata={"source": "confluence", "filename": filename, "format": file_format}
        )

    @classmethod
    def get_supported_formats(cls) -> List[Dict[str, Any]]:
        return [
            {
                "format": "xml",
                "description": "Confluence XML export",
                "capabilities": ["basic_content"],
                "export_method": "Space Tools > Content Tools > Export > XML"
            },
            {
                "format": "html",
                "description": "Confluence HTML export",
                "capabilities": ["basic_content"],
                "export_method": "Space Tools > Content Tools > Export > HTML"
            }
        ]


# Registry of supported normalizers
SUPPORTED_SYSTEMS = {
    "miro": MiroNormalizer,
    "figjam": FigJamNormalizer,
    "lucid": LucidNormalizer,
    "confluence": ConfluenceNormalizer,
}

# Registry of supported file normalizers
SUPPORTED_FILE_SYSTEMS = {
    "miro": MiroFileNormalizer,
    "figjam": FigJamFileNormalizer,
    "lucid": LucidFileNormalizer,
    "confluence": ConfluenceFileNormalizer,
}


def get_normalizer(system: str) -> Optional[BaseNormalizer]:
    """Get the appropriate normalizer for a system."""
    normalizer_class = SUPPORTED_SYSTEMS.get(system.lower())
    if normalizer_class:
        return normalizer_class()
    return None


def get_file_normalizer(system: str) -> Optional[BaseFileNormalizer]:
    """Get the appropriate file normalizer for a system."""
    normalizer_class = SUPPORTED_FILE_SYSTEMS.get(system.lower())
    if normalizer_class:
        return normalizer_class()
    return None
