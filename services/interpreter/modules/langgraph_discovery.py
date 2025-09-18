"""Basic LangGraph Discovery Module for Interpreter Service."""

class LangGraphDiscovery:
    """Provides basic LangGraph workflow discovery."""
    
    async def discover_langgraph_workflows(self):
        """Discover available LangGraph workflows."""
        return {
            "workflows": [],
            "total_count": 0
        }

# Create singleton instance
langgraph_discovery = LangGraphDiscovery()