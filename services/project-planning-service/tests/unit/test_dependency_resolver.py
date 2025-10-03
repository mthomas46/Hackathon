"""
Tests for Dependency Resolution Engine
======================================

Unit tests for graph-based dependency management.
"""

import pytest
import sys
from pathlib import Path

# Add service root to path
service_root = str(Path(__file__).parent.parent.parent)
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from domain.services.dependency_resolver import (
    DependencyResolver,
    DependencyGraph,
    DependencyNode,
    DependencyEdge,
    DependencyType,
    DependencyAnalysisResult
)
from domain.entities.feature import Feature, FeaturePriority
from domain.entities.task import Task, TaskType


@pytest.fixture
def resolver():
    """Create dependency resolver instance."""
    return DependencyResolver()


@pytest.fixture
def linear_features():
    """Create features with linear dependencies."""
    return [
        Feature("f1", "Database Schema", "Setup database", estimated_effort=5.0),
        Feature("f2", "API Layer", "Build API", dependencies=["f1"], estimated_effort=8.0),
        Feature("f3", "Frontend", "Build UI", dependencies=["f2"], estimated_effort=13.0)
    ]


@pytest.fixture
def parallel_features():
    """Create features that can run in parallel."""
    return [
        Feature("f1", "Database", "Setup DB", estimated_effort=5.0),
        Feature("f2", "API", "Build API", dependencies=["f1"], estimated_effort=8.0),
        Feature("f3", "Frontend", "Build UI", dependencies=["f1"], estimated_effort=10.0),
        Feature("f4", "Mobile", "Build Mobile", dependencies=["f1"], estimated_effort=12.0)
    ]


@pytest.fixture
def circular_features():
    """Create features with circular dependencies."""
    return [
        Feature("f1", "Feature 1", "Desc", dependencies=["f2"]),
        Feature("f2", "Feature 2", "Desc", dependencies=["f3"]),
        Feature("f3", "Feature 3", "Desc", dependencies=["f1"])
    ]


class TestDependencyResolver:
    """Test suite for Dependency Resolver."""
    
    def test_resolver_initialization(self, resolver):
        """Test resolver initialization."""
        assert resolver is not None
    
    def test_analyze_linear_dependencies(self, resolver, linear_features):
        """Test analysis of linear dependencies."""
        result = resolver.analyze_dependencies(linear_features)
        
        assert isinstance(result, DependencyAnalysisResult)
        assert result.is_valid
        assert len(result.sorted_order) == 3
        assert not result.has_cycles()
    
    def test_topological_sort_linear(self, resolver, linear_features):
        """Test topological sort with linear dependencies."""
        result = resolver.analyze_dependencies(linear_features)
        
        # Should be sorted: f1 -> f2 -> f3
        assert result.sorted_order == ["f1", "f2", "f3"]
    
    def test_topological_sort_parallel(self, resolver, parallel_features):
        """Test topological sort with parallel dependencies."""
        result = resolver.analyze_dependencies(parallel_features)
        
        # f1 must be first, others can be in any order but after f1
        assert result.sorted_order[0] == "f1"
        assert set(result.sorted_order[1:]) == {"f2", "f3", "f4"}
    
    def test_circular_dependency_detection(self, resolver, circular_features):
        """Test detection of circular dependencies."""
        result = resolver.analyze_dependencies(circular_features)
        
        assert not result.is_valid
        assert result.has_cycles()
        assert len(result.circular_dependencies) > 0
    
    def test_critical_path_linear(self, resolver, linear_features):
        """Test critical path identification in linear graph."""
        result = resolver.analyze_dependencies(linear_features)
        
        # All features are on critical path in linear dependency
        assert len(result.critical_path) == 3
        assert "f1" in result.critical_path
        assert "f2" in result.critical_path
        assert "f3" in result.critical_path
        
        # Duration should be sum of all efforts: 5 + 8 + 13 = 26
        assert result.critical_path_duration == 26.0
    
    def test_critical_path_parallel(self, resolver, parallel_features):
        """Test critical path with parallel tracks."""
        result = resolver.analyze_dependencies(parallel_features)
        
        # Critical path should include f1 and longest parallel branch (f4: 12)
        assert "f1" in result.critical_path
        # Duration should be 5 + 12 = 17 (f1 + longest branch)
        assert result.critical_path_duration == 17.0
    
    def test_parallel_tracks_identification(self, resolver, parallel_features):
        """Test identification of parallel tracks."""
        result = resolver.analyze_dependencies(parallel_features)
        
        # f2, f3, f4 can run in parallel after f1
        assert len(result.parallel_tracks) > 0
        
        # Find the parallel group
        parallel_group = None
        for track in result.parallel_tracks:
            if "f2" in track and "f3" in track and "f4" in track:
                parallel_group = track
                break
        
        assert parallel_group is not None
        # The parallel group includes the root node (f1) plus its dependents (f2, f3, f4)
        assert len(parallel_group) == 4
    
    def test_bottleneck_detection(self, resolver):
        """Test bottleneck detection."""
        # Create a bottleneck scenario
        features = [
            Feature("f1", "Base", "Base feature", estimated_effort=5.0),
            Feature("f2", "Feature 2", "Desc", dependencies=["f1"]),
            Feature("f3", "Feature 3", "Desc", dependencies=["f1"]),
            Feature("f4", "Feature 4", "Desc", dependencies=["f1"]),
        ]
        
        result = resolver.analyze_dependencies(features)
        
        # f1 is a bottleneck (3 features depend on it)
        bottleneck_ids = [node.id for node in result.bottlenecks]
        assert "f1" in bottleneck_ids
    
    def test_independent_nodes_identification(self, resolver, parallel_features):
        """Test identification of independent nodes."""
        result = resolver.analyze_dependencies(parallel_features)
        
        # Only f1 has no dependencies
        assert len(result.independent_nodes) == 1
        assert "f1" in result.independent_nodes
    
    def test_warning_generation_circular(self, resolver, circular_features):
        """Test warning generation for circular dependencies."""
        result = resolver.analyze_dependencies(circular_features)
        
        assert len(result.warnings) > 0
        assert any("circular" in w.lower() for w in result.warnings)
    
    def test_warning_generation_bottleneck(self, resolver):
        """Test warning generation for bottlenecks."""
        features = [
            Feature("f1", "Base", "Base", estimated_effort=5.0),
            Feature("f2", "F2", "Desc", dependencies=["f1"]),
            Feature("f3", "F3", "Desc", dependencies=["f1"]),
            Feature("f4", "F4", "Desc", dependencies=["f1"]),
        ]
        
        result = resolver.analyze_dependencies(features)
        
        assert any("bottleneck" in w.lower() for w in result.warnings)
    
    def test_empty_features(self, resolver):
        """Test analysis with no features."""
        result = resolver.analyze_dependencies([])
        
        assert result.is_valid
        assert len(result.sorted_order) == 0
        assert len(result.circular_dependencies) == 0
    
    def test_single_feature(self, resolver):
        """Test analysis with single feature."""
        features = [Feature("f1", "Single Feature", "Description")]
        
        result = resolver.analyze_dependencies(features)
        
        assert result.is_valid
        assert result.sorted_order == ["f1"]
        assert "f1" in result.independent_nodes
    
    def test_validate_dependency_valid(self, resolver):
        """Test validation of valid dependency."""
        features = [
            Feature("f1", "Feature 1", "Desc"),
            Feature("f2", "Feature 2", "Desc")
        ]
        
        is_valid, message = resolver.validate_dependency(
            features[0], features[1], features
        )
        
        assert is_valid
        assert "valid" in message.lower()
    
    def test_validate_dependency_circular(self, resolver):
        """Test validation detects circular dependency."""
        f1 = Feature("f1", "Feature 1", "Desc", dependencies=["f2"])
        f2 = Feature("f2", "Feature 2", "Desc")
        
        # Try to add f2 depending on f1, which would create a cycle
        # (f1 already depends on f2, so f2->f1 would create f1->f2->f1)
        is_valid, message = resolver.validate_dependency(
            f1, f2, [f1, f2]
        )
        
        assert not is_valid
        assert "circular" in message.lower()
    
    def test_suggest_dependency_order(self, resolver, linear_features):
        """Test suggestion of dependency order."""
        suggested_order = resolver.suggest_dependency_order(linear_features)
        
        assert len(suggested_order) == 3
        assert suggested_order[0] == "f1"  # No dependencies
    
    def test_suggest_order_with_cycles(self, resolver, circular_features):
        """Test order suggestion with circular dependencies."""
        suggested_order = resolver.suggest_dependency_order(circular_features)
        
        # Should return empty list when there are cycles
        assert len(suggested_order) == 0


class TestDependencyGraph:
    """Test suite for DependencyGraph."""
    
    def test_graph_initialization(self):
        """Test graph initialization."""
        graph = DependencyGraph()
        
        assert graph.node_count() == 0
        assert graph.edge_count() == 0
    
    def test_add_node(self):
        """Test adding node to graph."""
        graph = DependencyGraph()
        node = DependencyNode("n1", "Node 1", 5.0)
        
        graph.add_node(node)
        
        assert graph.node_count() == 1
        assert graph.get_node("n1") == node
    
    def test_add_edge(self):
        """Test adding edge to graph."""
        graph = DependencyGraph()
        node1 = DependencyNode("n1", "Node 1", 5.0)
        node2 = DependencyNode("n2", "Node 2", 8.0)
        
        graph.add_node(node1)
        graph.add_node(node2)
        
        edge = DependencyEdge("n1", "n2")
        graph.add_edge(edge)
        
        assert graph.edge_count() == 1
        assert "n1" in node2.dependencies
        assert "n2" in node1.dependents
    
    def test_get_nonexistent_node(self):
        """Test getting nonexistent node."""
        graph = DependencyGraph()
        
        assert graph.get_node("nonexistent") is None


class TestDependencyNode:
    """Test suite for DependencyNode."""
    
    def test_node_creation(self):
        """Test node creation."""
        node = DependencyNode(
            id="n1",
            title="Test Node",
            estimated_effort=10.0,
            dependencies=["n0"],
            level=1
        )
        
        assert node.id == "n1"
        assert node.title == "Test Node"
        assert node.estimated_effort == 10.0
        assert "n0" in node.dependencies
        assert node.level == 1
    
    def test_node_defaults(self):
        """Test node default values."""
        node = DependencyNode("n1", "Node", 5.0)
        
        assert node.dependencies == []
        assert node.dependents == []
        assert node.level == 0


class TestDependencyEdge:
    """Test suite for DependencyEdge."""
    
    def test_edge_creation(self):
        """Test edge creation."""
        edge = DependencyEdge(
            from_id="n1",
            to_id="n2",
            dependency_type=DependencyType.FINISH_TO_START,
            lag_days=2
        )
        
        assert edge.from_id == "n1"
        assert edge.to_id == "n2"
        assert edge.dependency_type == DependencyType.FINISH_TO_START
        assert edge.lag_days == 2
    
    def test_edge_defaults(self):
        """Test edge default values."""
        edge = DependencyEdge("n1", "n2")
        
        assert edge.dependency_type == DependencyType.FINISH_TO_START
        assert edge.lag_days == 0


class TestComplexDependencies:
    """Test complex dependency scenarios."""
    
    def test_diamond_dependency(self, resolver):
        """Test diamond-shaped dependency."""
        features = [
            Feature("f1", "Base", "Base", estimated_effort=5.0),
            Feature("f2", "Left", "Left path", dependencies=["f1"], estimated_effort=8.0),
            Feature("f3", "Right", "Right path", dependencies=["f1"], estimated_effort=10.0),
            Feature("f4", "Merge", "Merge paths", dependencies=["f2", "f3"], estimated_effort=6.0)
        ]
        
        result = resolver.analyze_dependencies(features)
        
        assert result.is_valid
        assert not result.has_cycles()
        
        # f1 must be first
        assert result.sorted_order[0] == "f1"
        # f4 must be last
        assert result.sorted_order[-1] == "f4"
        
        # f2 and f3 can be parallel
        parallel_found = False
        for track in result.parallel_tracks:
            if "f2" in track and "f3" in track:
                parallel_found = True
        assert parallel_found
    
    def test_deep_dependency_chain(self, resolver):
        """Test deep dependency chain."""
        features = [
            Feature(f"f{i}", f"Feature {i}", "Desc",
                   dependencies=[f"f{i-1}"] if i > 0 else [],
                   estimated_effort=5.0)
            for i in range(10)
        ]
        
        result = resolver.analyze_dependencies(features)
        
        assert result.is_valid
        assert len(result.sorted_order) == 10
        
        # No specific warning about deep chains in current implementation
        # Just verify it completes successfully
    
    def test_multiple_cycles(self, resolver):
        """Test detection of multiple cycles."""
        features = [
            # Cycle 1: f1 -> f2 -> f3 -> f1
            Feature("f1", "F1", "Desc", dependencies=["f3"]),
            Feature("f2", "F2", "Desc", dependencies=["f1"]),
            Feature("f3", "F3", "Desc", dependencies=["f2"]),
            # Cycle 2: f4 -> f5 -> f4
            Feature("f4", "F4", "Desc", dependencies=["f5"]),
            Feature("f5", "F5", "Desc", dependencies=["f4"])
        ]
        
        result = resolver.analyze_dependencies(features)
        
        assert not result.is_valid
        assert len(result.circular_dependencies) > 0


class TestWithTasks:
    """Test dependency resolution with tasks."""
    
    def test_features_and_tasks(self, resolver):
        """Test analysis with both features and tasks."""
        features = [
            Feature("f1", "Feature 1", "Desc", estimated_effort=10.0)
        ]
        
        tasks = [
            Task("t1", "f1", "system", "Task 1", "Desc",
                 TaskType.DESIGN, estimated_hours=8.0),
            Task("t2", "f1", "system", "Task 2", "Desc",
                 TaskType.DEVELOPMENT, dependencies=["t1"], estimated_hours=16.0),
            Task("t3", "f1", "system", "Task 3", "Desc",
                 TaskType.TESTING, dependencies=["t2"], estimated_hours=8.0)
        ]
        
        result = resolver.analyze_dependencies(features, tasks)
        
        assert result.is_valid
        # Should have feature + tasks
        assert result.graph.node_count() == 4
        
        # Tasks should be in order
        assert result.sorted_order.index("t1") < result.sorted_order.index("t2")
        assert result.sorted_order.index("t2") < result.sorted_order.index("t3")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

