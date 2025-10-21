"""
Dependency Analyzer

Analyzes cross-file dependencies, imports, and relationships.
"""

import logging
import re
import ast
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Dependency:
    """Represents a dependency between two files."""
    source_file: str
    target_file: str
    import_type: str  # 'direct', 'from', 'relative'
    items: List[str]  # What was imported
    line_number: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DependencyGraph:
    """Complete dependency graph for a project."""
    nodes: List[str]  # File paths
    edges: List[Dependency]
    cycles: List[List[str]]
    metrics: Dict[str, any]
    topological_order: Optional[List[str]] = None  # PHASE 10 (Gap #2): Processing order
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'nodes': self.nodes,
            'edges': [e.to_dict() for e in self.edges],
            'cycles': self.cycles,
            'metrics': self.metrics,
            'topological_order': self.topological_order  # PHASE 10
        }


class DependencyAnalyzer:
    """
    Analyzes dependencies between files.
    
    Features:
    - Parse import statements (Python, JavaScript)
    - Build dependency graph
    - Detect circular dependencies
    - Calculate coupling metrics
    """
    
    def __init__(self):
        self.dependencies: List[Dependency] = []
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        
        logger.info("DependencyAnalyzer initialized")
    
    async def analyze_dependencies(self, files: List[Dict], repo_path: str) -> DependencyGraph:
        """
        Analyze dependencies across files.
        
        Args:
            files: List of file information dictionaries
            repo_path: Repository root path
        
        Returns:
            DependencyGraph with all dependencies
        """
        logger.info(f"📊 Analyzing dependencies for {len(files)} files...")
        
        self.dependencies = []
        self.graph = defaultdict(set)
        
        # Analyze each file
        for file_info in files:
            if not self._should_analyze(file_info):
                continue
            
            file_path = file_info.get('path') or file_info.get('relative_path', '')
            if not file_path:
                continue
            
            language = file_info.get('language', '').lower()
            
            try:
                full_path = Path(repo_path) / file_path
                if not full_path.exists():
                    continue
                
                content = full_path.read_text(encoding='utf-8', errors='ignore')
                
                if language == 'python':
                    await self._analyze_python_file(file_path, content)
                elif language in ['javascript', 'typescript']:
                    await self._analyze_javascript_file(file_path, content)
                
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
        
        # Build graph
        nodes = list(set(
            [d.source_file for d in self.dependencies] +
            [d.target_file for d in self.dependencies]
        ))
        
        # Detect cycles
        cycles = await self._detect_cycles()
        
        # Calculate metrics
        metrics = await self._calculate_metrics()
        
        # PHASE 10 (Gap #2): Calculate topological order
        topological_order = await self._compute_topological_order(nodes)
        
        graph = DependencyGraph(
            nodes=nodes,
            edges=self.dependencies,
            cycles=cycles,
            metrics=metrics,
            topological_order=topological_order  # PHASE 10
        )
        
        logger.info(
            f"✅ Dependency analysis complete: {len(nodes)} nodes, "
            f"{len(self.dependencies)} dependencies, {len(cycles)} cycles"
        )
        if topological_order:
            logger.info(f"   📋 Topological order computed: {len(topological_order)} files")
        
        return graph
    
    async def _analyze_python_file(self, file_path: str, content: str) -> None:
        """
        Analyze Python file for imports.
        
        Args:
            file_path: Path to the file
            content: File content
        """
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dep = Dependency(
                            source_file=file_path,
                            target_file=self._resolve_module(alias.name, file_path),
                            import_type='direct',
                            items=[alias.asname if alias.asname else alias.name],
                            line_number=node.lineno
                        )
                        self.dependencies.append(dep)
                        self.graph[file_path].add(dep.target_file)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        target = self._resolve_module(node.module, file_path)
                        items = [alias.name for alias in node.names]
                        
                        dep = Dependency(
                            source_file=file_path,
                            target_file=target,
                            import_type='from' if node.level == 0 else 'relative',
                            items=items,
                            line_number=node.lineno
                        )
                        self.dependencies.append(dep)
                        self.graph[file_path].add(target)
        
        except SyntaxError as e:
            logger.debug(f"Syntax error parsing {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error parsing Python file {file_path}: {e}")
    
    async def _analyze_javascript_file(self, file_path: str, content: str) -> None:
        """
        Analyze JavaScript/TypeScript file for imports.
        
        Args:
            file_path: Path to the file
            content: File content
        """
        # ES6 import pattern
        import_pattern = r'import\s+(?:{([^}]+)}|(\w+))\s+from\s+[\'"]([^\'"]+)[\'"]'
        # CommonJS require pattern
        require_pattern = r'(?:const|let|var)\s+(?:{([^}]+)}|(\w+))\s*=\s*require\([\'"]([^\'"]+)[\'"]\)'
        
        line_num = 0
        for line in content.split('\n'):
            line_num += 1
            
            # ES6 imports
            for match in re.finditer(import_pattern, line):
                named_imports = match.group(1)
                default_import = match.group(2)
                module = match.group(3)
                
                items = []
                if named_imports:
                    items = [i.strip() for i in named_imports.split(',')]
                if default_import:
                    items.append(default_import)
                
                dep = Dependency(
                    source_file=file_path,
                    target_file=self._resolve_js_module(module, file_path),
                    import_type='es6',
                    items=items,
                    line_number=line_num
                )
                self.dependencies.append(dep)
                self.graph[file_path].add(dep.target_file)
            
            # CommonJS require
            for match in re.finditer(require_pattern, line):
                destructured = match.group(1)
                simple = match.group(2)
                module = match.group(3)
                
                items = []
                if destructured:
                    items = [i.strip() for i in destructured.split(',')]
                if simple:
                    items.append(simple)
                
                dep = Dependency(
                    source_file=file_path,
                    target_file=self._resolve_js_module(module, file_path),
                    import_type='commonjs',
                    items=items,
                    line_number=line_num
                )
                self.dependencies.append(dep)
                self.graph[file_path].add(dep.target_file)
    
    def _resolve_module(self, module_name: str, current_file: str) -> str:
        """
        Resolve Python module name to file path.
        
        Args:
            module_name: Module name
            current_file: Current file path
        
        Returns:
            Resolved file path
        """
        # For now, return module name as-is
        # TODO: Implement proper module resolution
        return module_name.replace('.', '/') + '.py'
    
    def _resolve_js_module(self, module_path: str, current_file: str) -> str:
        """
        Resolve JavaScript module path.
        
        Args:
            module_path: Module path from import
            current_file: Current file path
        
        Returns:
            Resolved file path
        """
        # Relative imports
        if module_path.startswith('.'):
            base_dir = Path(current_file).parent
            resolved = (base_dir / module_path).resolve()
            return str(resolved)
        
        # Node modules
        if not module_path.startswith('/'):
            return f"node_modules/{module_path}"
        
        return module_path
    
    async def _detect_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies using DFS.
        
        Returns:
            List of cycles (each cycle is a list of file paths)
        """
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)
            
            rec_stack.remove(node)
        
        for node in self.graph.keys():
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    async def _calculate_metrics(self) -> Dict[str, any]:
        """
        Calculate dependency metrics.
        
        Returns:
            Dictionary of metrics
        """
        total_files = len(self.graph)
        total_dependencies = len(self.dependencies)
        
        # Calculate coupling
        if total_files > 0:
            avg_dependencies = total_dependencies / total_files
        else:
            avg_dependencies = 0
        
        # Find most depended upon files
        incoming_deps = defaultdict(int)
        for dep in self.dependencies:
            incoming_deps[dep.target_file] += 1
        
        top_dependencies = sorted(
            incoming_deps.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'total_files': total_files,
            'total_dependencies': total_dependencies,
            'average_dependencies_per_file': round(avg_dependencies, 2),
            'circular_dependency_count': len(await self._detect_cycles()),
            'most_depended_upon': [
                {'file': f, 'count': c} for f, c in top_dependencies
            ]
        }
    
    def _should_analyze(self, file_info: Dict) -> bool:
        """
        Check if file should be analyzed.
        
        Args:
            file_info: File information dictionary
        
        Returns:
            True if file should be analyzed
        """
        # Skip tests, docs, configs
        is_test = file_info.get('is_test', False)
        is_doc = file_info.get('is_doc', False)
        is_config = file_info.get('is_config', False)
        
        if is_test or is_doc or is_config:
            return False
        
        # Only analyze code files
        is_code = file_info.get('is_code', False)
        return is_code
    
    async def _compute_topological_order(self, nodes: List[str]) -> Optional[List[str]]:
        """
        Compute topological order for file processing (PHASE 10 - Gap #2).
        
        Uses Kahn's algorithm for topological sorting. Files with no dependencies
        come first, followed by files that depend on them.
        
        Args:
            nodes: List of file paths
        
        Returns:
            List of files in topological order, or None if cyclic dependencies exist
        """
        try:
            logger.info("📊 Computing topological order...")
            
            # If no dependencies, return original order
            if not self.dependencies:
                logger.info("   No dependencies found, using natural order")
                return nodes
            
            # Build adjacency list and in-degree map
            adj_list: Dict[str, Set[str]] = defaultdict(set)
            in_degree: Dict[str, int] = defaultdict(int)
            
            # Initialize all nodes with 0 in-degree
            for node in nodes:
                if node not in in_degree:
                    in_degree[node] = 0
            
            # Build graph (edge from dependency target to source)
            # If A depends on B, edge is B -> A (B must be processed before A)
            for dep in self.dependencies:
                source = dep.source_file
                target = dep.target_file
                
                # Skip self-references
                if source == target:
                    continue
                
                # Edge: target -> source (target must come before source)
                if source not in adj_list[target]:
                    adj_list[target].add(source)
                    in_degree[source] += 1
            
            # Kahn's algorithm
            queue = [node for node in nodes if in_degree[node] == 0]
            topological_order = []
            
            while queue:
                # Sort for deterministic behavior
                queue.sort()
                
                # Pop node with no incoming edges
                node = queue.pop(0)
                topological_order.append(node)
                
                # Reduce in-degree for neighbors
                for neighbor in adj_list[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            
            # Check if all nodes were processed
            if len(topological_order) < len(nodes):
                # Cyclic dependencies exist
                unprocessed = set(nodes) - set(topological_order)
                logger.warning(
                    f"   ⚠️  Cyclic dependencies detected, "
                    f"{len(unprocessed)} files not in topological order"
                )
                # Add remaining files in arbitrary order
                topological_order.extend(sorted(unprocessed))
            
            logger.info(
                f"   ✅ Topological order computed: {len(topological_order)} files "
                f"({len(topological_order) - len([n for n in nodes if in_degree[n] == 0])} ordered by dependencies)"
            )
            
            return topological_order
            
        except Exception as e:
            logger.error(f"Failed to compute topological order: {e}", exc_info=True)
            # Fallback to original order
            return nodes


# Singleton
_dependency_analyzer_instance = None

def get_dependency_analyzer() -> DependencyAnalyzer:
    """Get singleton dependency analyzer instance."""
    global _dependency_analyzer_instance
    if _dependency_analyzer_instance is None:
        _dependency_analyzer_instance = DependencyAnalyzer()
    return _dependency_analyzer_instance

