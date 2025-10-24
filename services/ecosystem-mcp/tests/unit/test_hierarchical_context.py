"""
Unit tests for Hierarchical Context Manager (Week 2, Day 5-6).

Tests:
- Context hierarchy building
- Parent-child relationships
- Context traversal
- Context search
- ChromaDB filtering
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from src.services.analysis.hierarchical_context_manager import (
    HierarchicalContextManager,
    HierarchicalContext,
    ContextLevel,
    get_hierarchical_context_manager
)
from src.services.analysis.context_generator import RepositoryContext
from src.services.analysis.analysis_engine import AnalysisReport
from src.services.analysis.service_detector import ServiceMap, Service


@pytest.fixture
def base_context():
    """Create a base repository context."""
    return RepositoryContext(
        repo_id="test_repo",
        repo_name="TestRepo",
        repo_path="/app/test_repo",
        languages=["Python", "JavaScript"],
        primary_language="Python",
        frameworks=["FastAPI", "React"],
        databases=["PostgreSQL"],
        tools=["Docker"],
        architecture_type="microservices",
        architecture_confidence=0.9,
        architecture_description="Microservices architecture",
        service_count=3,
        is_microservices=True,
        layers=["api", "services", "storage"],
        endpoints=[],
        endpoint_count=0,
        has_rest_api=True,
        has_graphql=False,
        total_files=100,
        code_files=60,
        test_files=30,
        doc_files=10,
        total_lines=10000,
        modularity_score=0.8,
        entry_points=["main.py"],
        brief_description="Test repository",
        key_features=["FastAPI backend", "React frontend"],
        technical_highlights=["Microservices", "REST API"],
        recommended_starting_points=["Start at main.py"]
    )


@pytest.fixture
def service_map():
    """Create a mock service map."""
    service1 = Service(
        name="auth-service",
        path="/app/test_repo/services/auth",
        language="Python",
        dependencies=["FastAPI", "JWT"],
        has_api=True,
        endpoints=["/api/auth/login", "/api/auth/logout"],
        layers=["api", "services"],
        entry_points=["app.py"]
    )
    
    service2 = Service(
        name="user-service",
        path="/app/test_repo/services/user",
        language="Python",
        dependencies=["FastAPI", "SQLAlchemy"],
        has_api=True,
        endpoints=["/api/users", "/api/users/{id}"],
        layers=["api", "services", "storage"],
        entry_points=["main.py"]
    )
    
    return ServiceMap(
        is_microservices=True,
        services=[service1, service2],
        service_count=2,
        confidence=0.9
    )


@pytest.fixture
def analysis_report(service_map):
    """Create a mock analysis report."""
    report = Mock(spec=AnalysisReport)
    report.repo_path = "/app/test_repo"
    report.total_services = 2
    report.total_files = 100
    report.modularity_score = 0.8
    report.service_map = service_map
    return report


@pytest.mark.unit
@pytest.mark.asyncio
class TestHierarchicalContextManager:
    """Test HierarchicalContextManager class."""
    
    async def test_create_root_context(self, base_context):
        """Test creating root context."""
        manager = HierarchicalContextManager()
        
        root = manager._create_root_context(base_context)
        
        assert root.repo_id == "test_repo"
        assert root.repo_name == "TestRepo"
        assert root.level == ContextLevel.ROOT
        assert root.parent_id is None
        assert root.full_path == "TestRepo"
        assert root.file_patterns == ["**/*"]
        assert root.level_files == base_context.total_files
    
    async def test_build_hierarchy(self, base_context, analysis_report):
        """Test building complete hierarchy."""
        manager = HierarchicalContextManager()
        
        root = await manager.build_hierarchy(base_context, analysis_report)
        
        # Check root
        assert root.level == ContextLevel.ROOT
        assert root.repo_id in manager.contexts
        
        # Check children were created
        assert len(root.children) > 0
        
        # Check service contexts created
        service_contexts = [ctx for ctx in manager.contexts.values() if ctx.level == ContextLevel.SERVICE]
        assert len(service_contexts) == 2  # From service_map
        
        # Check module contexts created
        module_contexts = [ctx for ctx in manager.contexts.values() if ctx.level == ContextLevel.MODULE]
        assert len(module_contexts) > 0
    
    async def test_build_service_contexts(self, base_context, service_map):
        """Test building service-level contexts."""
        manager = HierarchicalContextManager()
        root = manager._create_root_context(base_context)
        manager.contexts[root.repo_id] = root
        
        await manager._build_service_contexts(root, service_map)
        
        # Check services were added to root's children
        service_children = [child_id for child_id in root.children if "/service/" in child_id]
        assert len(service_children) == 2
        
        # Check auth-service context
        auth_ctx = manager.get_context(f"{root.repo_id}/service/auth-service")
        assert auth_ctx is not None
        assert auth_ctx.level == ContextLevel.SERVICE
        assert auth_ctx.parent_id == root.repo_id
        assert auth_ctx.repo_name == "auth-service"
        assert auth_ctx.full_path == "TestRepo/auth-service"
        assert auth_ctx.endpoint_count == 2
    
    async def test_get_children(self, base_context, analysis_report):
        """Test getting child contexts."""
        manager = HierarchicalContextManager()
        root = await manager.build_hierarchy(base_context, analysis_report)
        
        children = manager.get_children(root.repo_id)
        
        assert len(children) > 0
        for child in children:
            assert child.parent_id == root.repo_id
            assert isinstance(child, HierarchicalContext)
    
    async def test_get_parent(self, base_context, analysis_report):
        """Test getting parent context."""
        manager = HierarchicalContextManager()
        root = await manager.build_hierarchy(base_context, analysis_report)
        
        children = manager.get_children(root.repo_id)
        if children:
            child = children[0]
            parent = manager.get_parent(child.repo_id)
            
            assert parent is not None
            assert parent.repo_id == root.repo_id
    
    async def test_get_path_to_root(self, base_context, analysis_report):
        """Test getting path from context to root."""
        manager = HierarchicalContextManager()
        root = await manager.build_hierarchy(base_context, analysis_report)
        
        children = manager.get_children(root.repo_id)
        if children:
            child = children[0]
            path = manager.get_path_to_root(child.repo_id)
            
            assert len(path) >= 2  # At least root and child
            assert path[0].repo_id == root.repo_id  # First is root
            assert path[-1].repo_id == child.repo_id  # Last is child
    
    async def test_get_all_descendants(self, base_context, analysis_report):
        """Test getting all descendant contexts."""
        manager = HierarchicalContextManager()
        root = await manager.build_hierarchy(base_context, analysis_report)
        
        descendants = manager.get_all_descendants(root.repo_id)
        
        # Should include all service and module contexts
        assert len(descendants) > 0
        
        # All descendants should have root as ancestor
        for desc in descendants:
            path = manager.get_path_to_root(desc.repo_id)
            assert path[0].repo_id == root.repo_id
    
    async def test_find_context_by_path(self, base_context, analysis_report):
        """Test finding context by full path."""
        manager = HierarchicalContextManager()
        root = await manager.build_hierarchy(base_context, analysis_report)
        
        # Find root by path
        found = manager.find_context_by_path("TestRepo")
        assert found is not None
        assert found.repo_id == root.repo_id
        
        # Find service by path
        found = manager.find_context_by_path("TestRepo/auth-service")
        assert found is not None
        assert found.level == ContextLevel.SERVICE
    
    async def test_chromadb_filter_root(self, base_context, analysis_report):
        """Test ChromaDB filter for root context."""
        manager = HierarchicalContextManager()
        root = await manager.build_hierarchy(base_context, analysis_report)
        
        filter_dict = manager.get_chromadb_filter(root)
        
        assert "repo_id" in filter_dict
        assert filter_dict["repo_id"] == "test_repo"
    
    async def test_chromadb_filter_service(self, base_context, analysis_report):
        """Test ChromaDB filter for service context."""
        manager = HierarchicalContextManager()
        root = await manager.build_hierarchy(base_context, analysis_report)
        
        service_ctx = manager.get_context(f"{root.repo_id}/service/auth-service")
        if service_ctx:
            filter_dict = manager.get_chromadb_filter(service_ctx)
            
            assert "repo_id" in filter_dict
            assert filter_dict["repo_id"] == "test_repo"
    
    async def test_context_summary(self, base_context, analysis_report):
        """Test context summary generation."""
        manager = HierarchicalContextManager()
        root = await manager.build_hierarchy(base_context, analysis_report)
        
        summary = manager.get_context_summary(root)
        
        assert "Context: TestRepo" in summary
        assert "Level: root" in summary
        assert "Path: TestRepo" in summary
        assert "Children:" in summary
    
    async def test_hierarchy_levels(self, base_context, analysis_report):
        """Test all hierarchy levels are created correctly."""
        manager = HierarchicalContextManager()
        root = await manager.build_hierarchy(base_context, analysis_report)
        
        # Check root level
        assert root.level == ContextLevel.ROOT
        
        # Check service level exists
        service_contexts = [ctx for ctx in manager.contexts.values() if ctx.level == ContextLevel.SERVICE]
        assert len(service_contexts) > 0
        for ctx in service_contexts:
            assert ctx.parent_id == root.repo_id
        
        # Check module level exists
        module_contexts = [ctx for ctx in manager.contexts.values() if ctx.level == ContextLevel.MODULE]
        assert len(module_contexts) > 0
        for ctx in module_contexts:
            assert ctx.parent_id == root.repo_id
    
    async def test_context_to_dict(self, base_context):
        """Test converting hierarchical context to dict."""
        manager = HierarchicalContextManager()
        root = manager._create_root_context(base_context)
        
        context_dict = root.to_dict()
        
        assert "repo_id" in context_dict
        assert "level" in context_dict
        assert context_dict["level"] == "ROOT"
        assert "full_path" in context_dict
        assert "children" in context_dict
        assert "file_patterns" in context_dict
    
    async def test_singleton_manager(self):
        """Test singleton pattern for manager."""
        manager1 = get_hierarchical_context_manager()
        manager2 = get_hierarchical_context_manager()
        
        assert manager1 is manager2


@pytest.mark.unit
@pytest.mark.asyncio
class TestContextHierarchyTraversal:
    """Test context hierarchy traversal operations."""
    
    async def test_depth_first_traversal(self, base_context, analysis_report):
        """Test depth-first traversal of hierarchy."""
        manager = HierarchicalContextManager()
        root = await manager.build_hierarchy(base_context, analysis_report)
        
        visited = []
        
        def dfs(context_id):
            visited.append(context_id)
            children = manager.get_children(context_id)
            for child in children:
                dfs(child.repo_id)
        
        dfs(root.repo_id)
        
        # Should visit all contexts
        assert len(visited) == len(manager.contexts)
        # Root should be first
        assert visited[0] == root.repo_id
    
    async def test_breadth_first_traversal(self, base_context, analysis_report):
        """Test breadth-first traversal of hierarchy."""
        manager = HierarchicalContextManager()
        root = await manager.build_hierarchy(base_context, analysis_report)
        
        visited = []
        queue = [root.repo_id]
        
        while queue:
            current_id = queue.pop(0)
            visited.append(current_id)
            
            children = manager.get_children(current_id)
            queue.extend([child.repo_id for child in children])
        
        # Should visit all contexts
        assert len(visited) == len(manager.contexts)
        # Root should be first
        assert visited[0] == root.repo_id
    
    async def test_level_order_grouping(self, base_context, analysis_report):
        """Test grouping contexts by level."""
        manager = HierarchicalContextManager()
        root = await manager.build_hierarchy(base_context, analysis_report)
        
        by_level = {
            ContextLevel.ROOT: [],
            ContextLevel.SERVICE: [],
            ContextLevel.MODULE: [],
            ContextLevel.COMPONENT: []
        }
        
        for context in manager.contexts.values():
            by_level[context.level].append(context)
        
        # Root should have 1 context
        assert len(by_level[ContextLevel.ROOT]) == 1
        
        # Services should exist
        assert len(by_level[ContextLevel.SERVICE]) > 0
        
        # Modules should exist
        assert len(by_level[ContextLevel.MODULE]) > 0


@pytest.mark.unit
class TestContextLevel:
    """Test ContextLevel enum."""
    
    def test_context_level_values(self):
        """Test context level enum values."""
        assert ContextLevel.ROOT.value == 0
        assert ContextLevel.SERVICE.value == 1
        assert ContextLevel.MODULE.value == 2
        assert ContextLevel.COMPONENT.value == 3
    
    def test_context_level_names(self):
        """Test context level enum names."""
        assert ContextLevel.ROOT.name == "ROOT"
        assert ContextLevel.SERVICE.name == "SERVICE"
        assert ContextLevel.MODULE.name == "MODULE"
        assert ContextLevel.COMPONENT.name == "COMPONENT"
    
    def test_context_level_ordering(self):
        """Test context level ordering."""
        assert ContextLevel.ROOT.value < ContextLevel.SERVICE.value
        assert ContextLevel.SERVICE.value < ContextLevel.MODULE.value
        assert ContextLevel.MODULE.value < ContextLevel.COMPONENT.value


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

