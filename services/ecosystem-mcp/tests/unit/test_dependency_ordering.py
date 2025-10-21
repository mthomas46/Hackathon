"""
Unit Tests for Dependency Topological Ordering (Gap #2)

Tests the implementation of Kahn's algorithm for topological sorting
and integration with sub-job execution.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import List

from src.services.analysis.dependency_analyzer import (
    DependencyAnalyzer,
    Dependency,
    DependencyGraph
)
from src.services.orchestration.sub_job_executor import SubJobExecutor
from src.storage.models_discovery import FileClassificationModel


class TestTopologicalOrdering:
    """Test topological ordering computation."""
    
    @pytest.fixture
    def analyzer(self):
        """Create dependency analyzer."""
        return DependencyAnalyzer()
    
    async def test_no_dependencies(self, analyzer):
        """Test topological order with no dependencies."""
        nodes = ["file1.py", "file2.py", "file3.py"]
        analyzer.dependencies = []
        
        order = await analyzer._compute_topological_order(nodes)
        
        # All files present
        assert set(order) == set(nodes)
        assert len(order) == len(nodes)
    
    async def test_simple_chain(self, analyzer):
        """Test topological order with simple chain: A -> B -> C."""
        nodes = ["file_a.py", "file_b.py", "file_c.py"]
        analyzer.dependencies = [
            Dependency(
                source_file="file_c.py",
                target_file="file_b.py",
                import_type="direct",
                items=["b"],
                line_number=1
            ),
            Dependency(
                source_file="file_b.py",
                target_file="file_a.py",
                import_type="direct",
                items=["a"],
                line_number=1
            )
        ]
        
        order = await analyzer._compute_topological_order(nodes)
        
        # A comes before B, B comes before C
        assert order.index("file_a.py") < order.index("file_b.py")
        assert order.index("file_b.py") < order.index("file_c.py")
    
    async def test_multiple_roots(self, analyzer):
        """Test topological order with multiple root nodes."""
        nodes = ["root1.py", "root2.py", "child1.py", "child2.py"]
        analyzer.dependencies = [
            Dependency(
                source_file="child1.py",
                target_file="root1.py",
                import_type="direct",
                items=["root1"],
                line_number=1
            ),
            Dependency(
                source_file="child2.py",
                target_file="root2.py",
                import_type="direct",
                items=["root2"],
                line_number=1
            )
        ]
        
        order = await analyzer._compute_topological_order(nodes)
        
        # Roots come before children
        assert order.index("root1.py") < order.index("child1.py")
        assert order.index("root2.py") < order.index("child2.py")
    
    async def test_cyclic_dependencies(self, analyzer):
        """Test topological order with cycles (should handle gracefully)."""
        nodes = ["file_a.py", "file_b.py", "file_c.py"]
        analyzer.dependencies = [
            Dependency(
                source_file="file_a.py",
                target_file="file_b.py",
                import_type="direct",
                items=["b"],
                line_number=1
            ),
            Dependency(
                source_file="file_b.py",
                target_file="file_c.py",
                import_type="direct",
                items=["c"],
                line_number=1
            ),
            Dependency(
                source_file="file_c.py",
                target_file="file_a.py",  # Cycle!
                import_type="direct",
                items=["a"],
                line_number=1
            )
        ]
        
        order = await analyzer._compute_topological_order(nodes)
        
        # Should still return all nodes (cycle handled)
        assert set(order) == set(nodes)
        assert len(order) == len(nodes)
    
    async def test_self_reference(self, analyzer):
        """Test that self-references are skipped."""
        nodes = ["file_a.py"]
        analyzer.dependencies = [
            Dependency(
                source_file="file_a.py",
                target_file="file_a.py",  # Self-reference
                import_type="direct",
                items=["a"],
                line_number=1
            )
        ]
        
        order = await analyzer._compute_topological_order(nodes)
        
        # Should return the node
        assert order == ["file_a.py"]
    
    async def test_complex_graph(self, analyzer):
        """Test topological order with complex dependency graph."""
        #     A    B
        #     |    |
        #     C    D
        #      \  /
        #       E
        nodes = ["a.py", "b.py", "c.py", "d.py", "e.py"]
        analyzer.dependencies = [
            Dependency(source_file="c.py", target_file="a.py", import_type="direct", items=["a"], line_number=1),
            Dependency(source_file="d.py", target_file="b.py", import_type="direct", items=["b"], line_number=1),
            Dependency(source_file="e.py", target_file="c.py", import_type="direct", items=["c"], line_number=1),
            Dependency(source_file="e.py", target_file="d.py", import_type="direct", items=["d"], line_number=1),
        ]
        
        order = await analyzer._compute_topological_order(nodes)
        
        # A and B are roots (can be in any order)
        # C depends on A, D depends on B
        # E depends on both C and D
        assert order.index("a.py") < order.index("c.py")
        assert order.index("b.py") < order.index("d.py")
        assert order.index("c.py") < order.index("e.py")
        assert order.index("d.py") < order.index("e.py")


class TestSubJobExecutorOrdering:
    """Test sub-job executor file ordering."""
    
    def test_order_files_by_dependencies(self):
        """Test ordering files by dependency order."""
        executor = SubJobExecutor()
        
        # Create mock files
        files = [
            Mock(file_path="file_c.py"),
            Mock(file_path="file_a.py"),
            Mock(file_path="file_b.py"),
        ]
        
        # Dependency order: A -> B -> C
        dependency_order = ["file_a.py", "file_b.py", "file_c.py"]
        
        ordered = executor._order_files_by_dependencies(files, dependency_order)
        
        # Check order
        assert ordered[0].file_path == "file_a.py"
        assert ordered[1].file_path == "file_b.py"
        assert ordered[2].file_path == "file_c.py"
    
    def test_order_files_with_missing(self):
        """Test ordering when some files aren't in dependency order."""
        executor = SubJobExecutor()
        
        # Create mock files
        files = [
            Mock(file_path="file_c.py"),
            Mock(file_path="file_a.py"),
            Mock(file_path="file_b.py"),
            Mock(file_path="file_d.py"),  # Not in dependency order
        ]
        
        # Dependency order only includes A, B, C
        dependency_order = ["file_a.py", "file_b.py", "file_c.py"]
        
        ordered = executor._order_files_by_dependencies(files, dependency_order)
        
        # First three should be in order
        assert ordered[0].file_path == "file_a.py"
        assert ordered[1].file_path == "file_b.py"
        assert ordered[2].file_path == "file_c.py"
        # Last one should be file_d (not in order)
        assert ordered[3].file_path == "file_d.py"
    
    def test_order_files_with_extra_in_order(self):
        """Test ordering when dependency order has files not in file list."""
        executor = SubJobExecutor()
        
        # Create mock files (only A and B)
        files = [
            Mock(file_path="file_b.py"),
            Mock(file_path="file_a.py"),
        ]
        
        # Dependency order includes C (not in files)
        dependency_order = ["file_a.py", "file_b.py", "file_c.py"]
        
        ordered = executor._order_files_by_dependencies(files, dependency_order)
        
        # Should only have A and B in correct order
        assert len(ordered) == 2
        assert ordered[0].file_path == "file_a.py"
        assert ordered[1].file_path == "file_b.py"
    
    def test_order_files_empty_dependency_order(self):
        """Test ordering with empty dependency order."""
        executor = SubJobExecutor()
        
        files = [
            Mock(file_path="file_c.py"),
            Mock(file_path="file_a.py"),
        ]
        
        ordered = executor._order_files_by_dependencies(files, [])
        
        # Should return files in original order
        assert ordered == files


class TestDependencyGraphDataclass:
    """Test DependencyGraph dataclass with topological_order field."""
    
    def test_dependency_graph_with_order(self):
        """Test creating DependencyGraph with topological order."""
        graph = DependencyGraph(
            nodes=["a.py", "b.py"],
            edges=[],
            cycles=[],
            metrics={},
            topological_order=["a.py", "b.py"]
        )
        
        assert graph.topological_order == ["a.py", "b.py"]
    
    def test_dependency_graph_without_order(self):
        """Test creating DependencyGraph without topological order."""
        graph = DependencyGraph(
            nodes=["a.py", "b.py"],
            edges=[],
            cycles=[],
            metrics={}
        )
        
        assert graph.topological_order is None
    
    def test_dependency_graph_to_dict(self):
        """Test converting DependencyGraph to dict includes topological_order."""
        graph = DependencyGraph(
            nodes=["a.py"],
            edges=[],
            cycles=[],
            metrics={},
            topological_order=["a.py"]
        )
        
        graph_dict = graph.to_dict()
        
        assert "topological_order" in graph_dict
        assert graph_dict["topological_order"] == ["a.py"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

