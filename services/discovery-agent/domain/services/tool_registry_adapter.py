"""
Tool Registry Adapter - Simplified interface for test compatibility.

Provides tool registry management for storing and retrieving discovered tools.
"""

from typing import Dict, Any, List, Optional


class ToolRegistry:
    """
    Tool registry for managing discovered LangGraph tools.
    
    Provides in-memory storage and retrieval of tools.
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._tools_by_service: Dict[str, List[str]] = {}
        self._tools_by_category: Dict[str, List[str]] = {}
    
    async def register_tool(self, tool: Dict[str, Any]) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool: Tool definition dictionary
        """
        tool_name = tool["name"]
        service_name = tool.get("service_name", "unknown")
        categories = tool.get("categories", [])
        
        # Store the tool
        self._tools[tool_name] = tool
        
        # Index by service
        if service_name not in self._tools_by_service:
            self._tools_by_service[service_name] = []
        if tool_name not in self._tools_by_service[service_name]:
            self._tools_by_service[service_name].append(tool_name)
        
        # Index by categories
        for category in categories:
            if category not in self._tools_by_category:
                self._tools_by_category[category] = []
            if tool_name not in self._tools_by_category[category]:
                self._tools_by_category[category].append(tool_name)
    
    def has_tool(self, tool_name: str) -> bool:
        """
        Check if a tool is registered.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            True if tool is registered
        """
        return tool_name in self._tools
    
    async def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool definition or None if not found
        """
        return self._tools.get(tool_name)
    
    async def list_all_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools.
        
        Returns:
            List of all tool definitions
        """
        return list(self._tools.values())
    
    async def get_tools_by_service(self, service_name: str) -> List[Dict[str, Any]]:
        """
        Get all tools for a specific service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            List of tool definitions for the service
        """
        tool_names = self._tools_by_service.get(service_name, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    async def get_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all tools in a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of tool definitions in the category
        """
        tool_names = self._tools_by_category.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    async def update_tool(self, tool_name: str, updated_tool: Dict[str, Any]) -> None:
        """
        Update a registered tool.
        
        Args:
            tool_name: Name of the tool to update
            updated_tool: Updated tool definition
        """
        if tool_name in self._tools:
            # Remove old indexing
            old_tool = self._tools[tool_name]
            old_service = old_tool.get("service_name")
            old_categories = old_tool.get("categories", [])
            
            # Remove from service index
            if old_service in self._tools_by_service and tool_name in self._tools_by_service[old_service]:
                self._tools_by_service[old_service].remove(tool_name)
            
            # Remove from category indexes
            for category in old_categories:
                if category in self._tools_by_category and tool_name in self._tools_by_category[category]:
                    self._tools_by_category[category].remove(tool_name)
            
            # Re-register with new data
            await self.register_tool(updated_tool)
    
    async def unregister_tool(self, tool_name: str) -> None:
        """
        Unregister a tool from the registry.
        
        Args:
            tool_name: Name of the tool to unregister
        """
        if tool_name in self._tools:
            tool = self._tools[tool_name]
            service_name = tool.get("service_name")
            categories = tool.get("categories", [])
            
            # Remove from main storage
            del self._tools[tool_name]
            
            # Remove from service index
            if service_name in self._tools_by_service and tool_name in self._tools_by_service[service_name]:
                self._tools_by_service[service_name].remove(tool_name)
                
                # Clean up empty service entries
                if not self._tools_by_service[service_name]:
                    del self._tools_by_service[service_name]
            
            # Remove from category indexes
            for category in categories:
                if category in self._tools_by_category and tool_name in self._tools_by_category[category]:
                    self._tools_by_category[category].remove(tool_name)
                    
                    # Clean up empty category entries
                    if not self._tools_by_category[category]:
                        del self._tools_by_category[category]
    
    async def clear_service_tools(self, service_name: str) -> None:
        """
        Clear all tools for a specific service.
        
        Args:
            service_name: Name of the service
        """
        tool_names = self._tools_by_service.get(service_name, []).copy()
        
        for tool_name in tool_names:
            await self.unregister_tool(tool_name)
    
    def get_tool_count(self) -> int:
        """
        Get the total number of registered tools.
        
        Returns:
            Number of tools in registry
        """
        return len(self._tools)
    
    def get_service_count(self) -> int:
        """
        Get the number of services with registered tools.
        
        Returns:
            Number of services
        """
        return len(self._tools_by_service)
    
    def get_category_count(self) -> int:
        """
        Get the number of categories with registered tools.
        
        Returns:
            Number of categories
        """
        return len(self._tools_by_category)

