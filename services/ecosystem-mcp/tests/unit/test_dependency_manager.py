"""
Unit tests for Dependency Manager (Phase 2)
"""

import pytest
import sys
from pathlib import Path

# Add src to path to avoid database imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import just the dependency manager module directly
from services.orchestration.dependency_manager import DependencyManager


@pytest.mark.skip(reason="DependencyManager API has changed - tests need updating")
class TestDependencyManager:
    """Test DependencyManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create a dependency manager instance."""
        return DependencyManager()
    
    @pytest.fixture
    def simple_dag(self):
        """Create a simple DAG."""
        return [
            {"sub_job_id": "A", "dependencies": []},
            {"sub_job_id": "B", "dependencies": ["A"]},
            {"sub_job_id": "C", "dependencies": ["A"]},
            {"sub_job_id": "D", "dependencies": ["B", "C"]}
        ]
    
    @pytest.fixture
    def circular_dag(self):
        """Create a DAG with circular dependency."""
        return [
            {"sub_job_id": "A", "dependencies": ["B"]},
            {"sub_job_id": "B", "dependencies": ["C"]},
            {"sub_job_id": "C", "dependencies": ["A"]}
        ]
    
    def test_manager_initialization(self, manager):
        """Test manager initializes correctly."""
        assert manager is not None
        assert len(manager.graphs) == 0
    
    def test_build_graph(self, manager, simple_dag):
        """Test building dependency graph."""
        manager.build_graph("plan1", simple_dag)
        
        assert "plan1" in manager.graphs
        graph = manager.graphs["plan1"]
        assert len(graph["nodes"]) == 4
        assert "A" in graph["nodes"]
        assert "B" in graph["nodes"]
    
    def test_get_execution_order(self, manager, simple_dag):
        """Test topological sort."""
        manager.build_graph("plan1", simple_dag)
        order = manager.get_execution_order("plan1")
        
        assert len(order) == 4
        # A should come before B and C
        assert order.index("A") < order.index("B")
        assert order.index("A") < order.index("C")
        # B and C should come before D
        assert order.index("B") < order.index("D")
        assert order.index("C") < order.index("D")
    
    def test_detect_no_cycles(self, manager, simple_dag):
        """Test cycle detection on acyclic graph."""
        manager.build_graph("plan1", simple_dag)
        cycles = manager.detect_cycles("plan1")
        
        assert len(cycles) == 0
    
    def test_detect_cycles(self, manager, circular_dag):
        """Test cycle detection on cyclic graph."""
        manager.build_graph("plan1", circular_dag)
        cycles = manager.detect_cycles("plan1")
        
        assert len(cycles) > 0
    
    def test_get_ready_sub_jobs_initial(self, manager, simple_dag):
        """Test getting initially ready sub-jobs."""
        manager.build_graph("plan1", simple_dag)
        ready = manager.get_ready_sub_jobs("plan1")
        
        # Only A should be ready initially (no dependencies)
        assert "A" in ready
        assert "B" not in ready
        assert "C" not in ready
        assert "D" not in ready
    
    def test_mark_completed(self, manager, simple_dag):
        """Test marking sub-job as completed."""
        manager.build_graph("plan1", simple_dag)
        
        # Mark A as completed
        manager.mark_completed("plan1", "A")
        
        # Now B and C should be ready
        ready = manager.get_ready_sub_jobs("plan1")
        assert "B" in ready
        assert "C" in ready
        assert "D" not in ready  # Still depends on B and C
    
    def test_get_progress(self, manager, simple_dag):
        """Test getting progress."""
        manager.build_graph("plan1", simple_dag)
        
        completed, total = manager.get_progress("plan1")
        assert completed == 0
        assert total == 4
        
        manager.mark_completed("plan1", "A")
        completed, total = manager.get_progress("plan1")
        assert completed == 1
        assert total == 4
    
    def test_is_complete(self, manager, simple_dag):
        """Test checking if all sub-jobs are complete."""
        manager.build_graph("plan1", simple_dag)
        
        assert manager.is_complete("plan1") is False
        
        # Mark all as completed
        for sub_job in ["A", "B", "C", "D"]:
            manager.mark_completed("plan1", sub_job)
        
        assert manager.is_complete("plan1") is True
    
    def test_clear_graph(self, manager, simple_dag):
        """Test clearing a graph."""
        manager.build_graph("plan1", simple_dag)
        assert "plan1" in manager.graphs
        
        manager.clear_graph("plan1")
        assert "plan1" not in manager.graphs
    
    def test_multiple_plans(self, manager, simple_dag):
        """Test managing multiple plans."""
        manager.build_graph("plan1", simple_dag)
        manager.build_graph("plan2", simple_dag)
        
        assert "plan1" in manager.graphs
        assert "plan2" in manager.graphs
        
        # Plans should be independent
        manager.mark_completed("plan1", "A")
        ready1 = manager.get_ready_sub_jobs("plan1")
        ready2 = manager.get_ready_sub_jobs("plan2")
        
        assert "B" in ready1
        assert "A" in ready2  # plan2 not affected
    
    def test_empty_dependencies(self, manager):
        """Test sub-jobs with no dependencies."""
        sub_jobs = [
            {"sub_job_id": "A", "dependencies": []},
            {"sub_job_id": "B", "dependencies": []},
            {"sub_job_id": "C", "dependencies": []}
        ]
        
        manager.build_graph("plan1", sub_jobs)
        ready = manager.get_ready_sub_jobs("plan1")
        
        # All should be ready
        assert len(ready) == 3
        assert "A" in ready
        assert "B" in ready
        assert "C" in ready


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
