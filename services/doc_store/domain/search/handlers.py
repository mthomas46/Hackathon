"""Search handlers for API endpoints.

Handles search-related HTTP requests and responses.
"""
from typing import Dict, Any
from services.shared.responses import create_success_response, create_error_response
from ...core.models import SearchRequest, SearchResponse
from ...db.queries import search_documents


class SearchHandlers:
    """Handlers for search API endpoints."""

    async def handle_search_documents(self, request: SearchRequest) -> Dict[str, Any]:
        """Handle document search."""
        try:
            # Perform search
            results = search_documents(request.query, request.limit or 50)

            # Format response
            response_data = SearchResponse(
                items=results,
                total=len(results),
                query=request.query
            )

            return create_success_response(
                "Documents searched successfully",
                response_data.dict(),
                {"query": request.query, "results_count": len(results)}
            )

        except ValueError as e:
            return create_error_response(str(e), "VALIDATION_ERROR")
        except Exception as e:
            return create_error_response(f"Failed to search documents: {str(e)}", "INTERNAL_ERROR")


# Global instance for backward compatibility
search_handlers = SearchHandlers()
