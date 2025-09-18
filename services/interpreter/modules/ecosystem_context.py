"""Basic Ecosystem Context Module for Interpreter Service."""

class EcosystemContext:
    """Provides basic ecosystem context information."""
    
    async def get_service_capabilities(self):
        """Get basic service capabilities."""
        return [
            {"service": "doc_store", "capabilities": ["document_storage", "search"]},
            {"service": "prompt_store", "capabilities": ["prompt_management"]},
            {"service": "analysis_service", "capabilities": ["content_analysis"]},
            {"service": "orchestrator", "capabilities": ["workflow_execution"]},
            {"service": "interpreter", "capabilities": ["query_processing"]}
        ]

# Create singleton instance
ecosystem_context = EcosystemContext()