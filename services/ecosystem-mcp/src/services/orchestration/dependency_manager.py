"""
Dependency Manager

Manages sub-job dependencies and execution order.
Performs topological sorting and circular dependency detection.
"""

import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class DependencyNode:
    """Node in dependency graph."""
    sub_job_id: str
    dependencies: List[str]
    dependents: List[str]
    completed: bool = False


@dataclass
class DependencyCycle:
    """Circular dependency cycle."""
    nodes: List[str]
    
    def __str__(self) -> str:
        return " -> ".join(self.nodes + [self.nodes[0]])


class DependencyManager:
    """
    Manages sub-job dependencies and execution order.
    
    Features:
    - Dependency graph construction
    - Topological sorting
    - Circular dependency detection
    - Ready-to-execute queue management
    """
    
    def __init__(self):
        self.graphs: Dict[str, Dict[str, DependencyNode]] = {}
        logger.info("DependencyManager initialized")
    
    def build_graph(self, plan_id: str, sub_jobs: List[Dict]) -> None:
        """
        Build dependency graph for a processing plan.
        
        Args:
            plan_id: Processing plan ID
            sub_jobs: List of sub-job dictionaries with dependencies
        """
        logger.info(f"📊 Building dependency graph for plan {plan_id}")
        
        graph = {}
        
        # Create nodes
        for sub_job in sub_jobs:
            sub_job_id = sub_job["sub_job_id"]
            dependencies = sub_job.get("dependencies", [])
            
            graph[sub_job_id] = DependencyNode(
                sub_job_id=sub_job_id,
                dependencies=dependencies.copy() if dependencies else [],
                dependents=[],
                completed=False
            )
        
        # Build dependent relationships
        for sub_job_id, node in graph.items():
            for dep_id in node.dependencies:
                if dep_id in graph:
                    graph[dep_id].dependents.append(sub_job_id)
        
        self.graphs[plan_id] = graph
        
        logger.info(
            f"✅ Graph built: {len(graph)} nodes, "
            f"{sum(len(n.dependencies) for n in graph.values())} edges"
        )
    
    def topological_sort(self, plan_id: str) -> List[str]:
        """
        Perform topological sort on dependency graph.
        
        Args:
            plan_id: Processing plan ID
        
        Returns:
            List of sub-job IDs in execution order
        
        Raises:
            ValueError: If circular dependencies detected
        """
        if plan_id not in self.graphs:
            raise ValueError(f"No graph found for plan {plan_id}")
        
        graph = self.graphs[plan_id]
        
        # Calculate in-degrees
        in_degree = {node_id: len(node.dependencies) for node_id, node in graph.items()}
        
        # Queue of nodes with no dependencies
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        
        result = []
        
        while queue:
            # Process node with no remaining dependencies
            current = queue.popleft()
            result.append(current)
            
            # Reduce in-degree of dependents
            for dependent in graph[current].dependents:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check if all nodes were processed
        if len(result) != len(graph):
            # Circular dependency detected
            cycles = self.detect_cycles(plan_id)
            cycle_strs = [str(cycle) for cycle in cycles]
            raise ValueError(f"Circular dependencies detected: {', '.join(cycle_strs)}")
        
        logger.info(f"✅ Topological sort complete: {len(result)} nodes ordered")
        return result
    
    def detect_cycles(self, plan_id: str) -> List[DependencyCycle]:
        """
        Detect circular dependencies in graph.
        
        Args:
            plan_id: Processing plan ID
        
        Returns:
            List of detected cycles
        """
        if plan_id not in self.graphs:
            return []
        
        graph = self.graphs[plan_id]
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node_id: str) -> bool:
            """DFS to detect cycles."""
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            for dep_id in graph[node_id].dependencies:
                if dep_id not in visited:
                    if dfs(dep_id):
                        return True
                elif dep_id in rec_stack:
                    # Cycle detected
                    cycle_start = path.index(dep_id)
                    cycle_nodes = path[cycle_start:]
                    cycles.append(DependencyCycle(nodes=cycle_nodes))
                    return True
            
            path.pop()
            rec_stack.remove(node_id)
            return False
        
        for node_id in graph:
            if node_id not in visited:
                dfs(node_id)
        
        if cycles:
            logger.warning(f"⚠️  Detected {len(cycles)} circular dependencies")
        
        return cycles
    
    def get_ready_sub_jobs(self, plan_id: str) -> List[str]:
        """
        Get sub-jobs that are ready to execute (all dependencies completed).
        
        Args:
            plan_id: Processing plan ID
        
        Returns:
            List of sub-job IDs ready to execute
        """
        if plan_id not in self.graphs:
            return []
        
        graph = self.graphs[plan_id]
        ready = []
        
        for sub_job_id, node in graph.items():
            if node.completed:
                continue
            
            # Check if all dependencies are completed
            all_deps_complete = all(
                graph[dep_id].completed
                for dep_id in node.dependencies
                if dep_id in graph
            )
            
            if all_deps_complete:
                ready.append(sub_job_id)
        
        return ready
    
    def mark_completed(self, plan_id: str, sub_job_id: str) -> None:
        """
        Mark a sub-job as completed.
        
        Args:
            plan_id: Processing plan ID
            sub_job_id: Sub-job ID
        """
        if plan_id not in self.graphs:
            logger.warning(f"No graph found for plan {plan_id}")
            return
        
        graph = self.graphs[plan_id]
        if sub_job_id in graph:
            graph[sub_job_id].completed = True
            logger.debug(f"✅ Marked {sub_job_id} as completed")
    
    def is_complete(self, plan_id: str) -> bool:
        """
        Check if all sub-jobs in plan are completed.
        
        Args:
            plan_id: Processing plan ID
        
        Returns:
            True if all sub-jobs completed
        """
        if plan_id not in self.graphs:
            return False
        
        graph = self.graphs[plan_id]
        return all(node.completed for node in graph.values())
    
    def get_progress(self, plan_id: str) -> Tuple[int, int]:
        """
        Get completion progress for plan.
        
        Args:
            plan_id: Processing plan ID
        
        Returns:
            Tuple of (completed_count, total_count)
        """
        if plan_id not in self.graphs:
            return (0, 0)
        
        graph = self.graphs[plan_id]
        completed = sum(1 for node in graph.values() if node.completed)
        total = len(graph)
        
        return (completed, total)
    
    def clear_graph(self, plan_id: str) -> None:
        """
        Clear dependency graph for a plan.
        
        Args:
            plan_id: Processing plan ID
        """
        if plan_id in self.graphs:
            del self.graphs[plan_id]
            logger.info(f"🗑️  Cleared dependency graph for plan {plan_id}")


# Singleton instance
_dependency_manager_instance = None

def get_dependency_manager() -> DependencyManager:
    """Get singleton dependency manager instance."""
    global _dependency_manager_instance
    if _dependency_manager_instance is None:
        _dependency_manager_instance = DependencyManager()
    return _dependency_manager_instance

