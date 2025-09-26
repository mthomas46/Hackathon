"""Document handlers for CQRS pattern compliance."""

from typing import Any, Dict, Optional


class DocumentCommandHandler:
    """Handles document commands in CQRS pattern."""

    def __init__(self):
        self._commands_handled = 0

    async def handle_store_document(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle store document command."""
        self._commands_handled += 1
        return {
            "command_type": "store_document",
            "document_id": command.get("document_id"),
            "status": "stored"
        }

    async def handle_update_document(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle update document command."""
        self._commands_handled += 1
        return {
            "command_type": "update_document",
            "document_id": command.get("document_id"),
            "status": "updated"
        }

    async def handle_delete_document(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delete document command."""
        self._commands_handled += 1
        return {
            "command_type": "delete_document",
            "document_id": command.get("document_id"),
            "status": "deleted"
        }


class DocumentQueryHandler:
    """Handles document queries in CQRS pattern."""

    def __init__(self):
        self._queries_handled = 0

    async def handle_get_document_by_id(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get document by ID query."""
        self._queries_handled += 1
        return {
            "query_type": "get_document_by_id",
            "document_id": query.get("document_id"),
            "document": {"id": query.get("document_id"), "status": "found"}
        }

    async def handle_list_documents(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list documents query."""
        self._queries_handled += 1
        return {
            "query_type": "list_documents",
            "documents": [{"id": "doc_1", "title": "Sample"}, {"id": "doc_2", "title": "Example"}],
            "total_count": 2,
            "page": query.get("page", 1)
        }
