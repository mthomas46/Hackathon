"""
Semantic Analyzer Adapter - Simplified interface for test compatibility.

Provides semantic analysis of endpoints to categorize them and extract meaning.
"""

from typing import Dict, Any, List


class SemanticAnalyzer:
    """
    Semantic analyzer for endpoints to extract categories and meaning.
    """
    
    def __init__(self):
        """Initialize the semantic analyzer."""
        pass
    
    async def analyze_endpoint(self, endpoint) -> Dict[str, Any]:
        """
        Perform semantic analysis on an endpoint.
        
        Args:
            endpoint: Endpoint entity
            
        Returns:
            Analysis results with categories and other semantic information
        """
        path = endpoint.path.lower()
        method = endpoint.method.lower()
        summary = (endpoint.summary or "").lower()
        description = (endpoint.description or "").lower()
        tags = [tag.lower() for tag in endpoint.tags]
        
        categories = []
        
        # CRUD operations
        crud_categories = self._analyze_crud(path, method, summary)
        categories.extend(crud_categories)
        
        # Business operations
        business_categories = self._analyze_business_operations(path, summary, description)
        categories.extend(business_categories)
        
        # From tags
        for tag in tags:
            if tag and tag not in categories:
                categories.append(tag)
        
        # Remove duplicates
        categories = list(dict.fromkeys(categories))
        
        return {
            "categories": categories,
            "complexity": self._estimate_complexity(endpoint),
            "security_level": self._estimate_security_level(endpoint),
            "operation_type": self._determine_operation_type(method)
        }
    
    def _analyze_crud(self, path: str, method: str, summary: str) -> List[str]:
        """Analyze CRUD operations."""
        categories = []
        
        # Create operations
        if method == "post" or "create" in path or "create" in summary:
            categories.append("create")
            categories.append("crud")
        
        # Read operations
        if method == "get" or "get" in path or "retrieve" in summary or "list" in path:
            categories.append("read")
            categories.append("crud")
        
        # Update operations
        if method in ["put", "patch"] or "update" in path or "update" in summary:
            categories.append("update")
            categories.append("crud")
        
        # Delete operations
        if method == "delete" or "delete" in path or "remove" in summary:
            categories.append("delete")
            categories.append("crud")
        
        return categories
    
    def _analyze_business_operations(self, path: str, summary: str, description: str) -> List[str]:
        """Analyze business operations."""
        categories = []
        text = f"{path} {summary} {description}"
        
        # Search operations
        if any(keyword in text for keyword in ["search", "query", "find"]):
            categories.append("search")
            categories.append("query")
        
        # Health/monitoring
        if any(keyword in text for keyword in ["health", "status", "ping", "ready"]):
            categories.append("monitoring")
            categories.append("health")
        
        # Analysis
        if any(keyword in text for keyword in ["analyze", "analysis", "check", "validate", "inspect"]):
            categories.append("analysis")
        
        # Code operations
        if any(keyword in text for keyword in ["code", "repository", "repo", "source"]):
            categories.append("code")
        
        # Document operations
        if any(keyword in text for keyword in ["document", "doc", "file"]):
            categories.append("document")
        
        # Workflow operations
        if any(keyword in text for keyword in ["workflow", "process", "pipeline"]):
            categories.append("workflow")
        
        return categories
    
    def _estimate_complexity(self, endpoint) -> str:
        """Estimate the complexity of an endpoint."""
        param_count = len(endpoint.parameters)
        
        if param_count == 0:
            return "simple"
        elif param_count <= 3:
            return "moderate"
        else:
            return "complex"
    
    def _estimate_security_level(self, endpoint) -> str:
        """Estimate the security level required for an endpoint."""
        method = endpoint.method.lower()
        path = endpoint.path.lower()
        
        # Write operations are higher security
        if method in ["post", "put", "patch", "delete"]:
            return "medium"
        
        # Admin or sensitive paths
        if any(keyword in path for keyword in ["admin", "secure", "auth", "password"]):
            return "high"
        
        # Read operations are lower security
        return "low"
    
    def _determine_operation_type(self, method: str) -> str:
        """Determine the operation type from HTTP method."""
        method = method.lower()
        
        if method == "get":
            return "read"
        elif method == "post":
            return "create"
        elif method in ["put", "patch"]:
            return "update"
        elif method == "delete":
            return "delete"
        else:
            return "other"

