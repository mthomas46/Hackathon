"""
Hierarchical Context Manager

Extends flat repository contexts with hierarchical structure for:
- Service-level contexts (microservices)
- Module-level contexts (packages/directories)
- Component-level contexts (classes/functions)

This enables more granular context-aware RAG queries like:
- "ecosystem-mcp/services/ingestion" (service level)
- "ecosystem-mcp/services/ingestion/job_processor" (module level)
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .context_generator import RepositoryContext
from .analysis_engine import AnalysisReport
from .service_analyzer import ServiceMap

logger = logging.getLogger(__name__)


class ContextLevel(Enum):
    """Hierarchy levels for contexts."""
    ROOT = 0  # Repository root
    SERVICE = 1  # Service/microservice
    MODULE = 2  # Package/directory
    COMPONENT = 3  # File/class


@dataclass
class HierarchicalContext(RepositoryContext):
    """
    Context with hierarchical structure.
    
    Extends RepositoryContext with:
    - Parent-child relationships
    - Hierarchical levels
    - File pattern matching
    - Sub-context queries
    """
    # Hierarchy
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    level: ContextLevel = ContextLevel.ROOT
    
    # Filtering
    file_patterns: List[str] = field(default_factory=list)  # Glob patterns
    file_paths: List[str] = field(default_factory=list)  # Exact paths
    
    # Metrics (for this level only)
    level_files: int = 0
    level_lines: int = 0
    
    # Navigation
    full_path: str = ""  # Full hierarchical path (e.g., "repo/service/module")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'parent_id': self.parent_id,
            'children': self.children,
            'level': self.level.name,
            'file_patterns': self.file_patterns,
            'file_paths': self.file_paths,
            'level_files': self.level_files,
            'level_lines': self.level_lines,
            'full_path': self.full_path
        })
        return base_dict


class HierarchicalContextManager:
    """
    Manages hierarchical repository contexts.
    
    Features:
    - Build context hierarchy from flat contexts
    - Service-level sub-contexts
    - Module-level sub-contexts
    - Context traversal and queries
    - Chromadb filtering by hierarchy
    """
    
    def __init__(self):
        self.contexts: Dict[str, HierarchicalContext] = {}
        logger.info("HierarchicalContextManager initialized")
    
    async def build_hierarchy(
        self,
        base_context: RepositoryContext,
        analysis_report: AnalysisReport
    ) -> HierarchicalContext:
        """
        Build context hierarchy from flat context.
        
        Args:
            base_context: Base repository context
            analysis_report: Full analysis report
        
        Returns:
            Root hierarchical context with children
        """
        logger.info(f"🌳 Building context hierarchy for {base_context.repo_name}")
        
        # Level 0: Repository root
        root = self._create_root_context(base_context)
        self.contexts[root.repo_id] = root
        
        # Level 1: Services (if microservices)
        if base_context.is_microservices and analysis_report.service_map:
            logger.info(f"  Building {len(analysis_report.service_map.services)} service contexts")
            await self._build_service_contexts(root, analysis_report.service_map)
        
        # Level 2: Modules (directories/packages)
        logger.info("  Building module contexts")
        await self._build_module_contexts(root, analysis_report)
        
        logger.info(f"✅ Built hierarchy: {len(self.contexts)} total contexts")
        return root
    
    def _create_root_context(self, base_context: RepositoryContext) -> HierarchicalContext:
        """Create root-level context."""
        root = HierarchicalContext(
            **{k: v for k, v in base_context.to_dict().items()},
            parent_id=None,
            children=[],
            level=ContextLevel.ROOT,
            file_patterns=["**/*"],  # Matches all files
            full_path=base_context.repo_name,
            level_files=base_context.total_files,
            level_lines=base_context.total_lines
        )
        return root
    
    async def _build_service_contexts(
        self,
        root: HierarchicalContext,
        service_map: ServiceMap
    ) -> None:
        """Build service-level contexts."""
        for service in service_map.services:
            # Create service context
            service_id = f"{root.repo_id}/service/{service.name}"
            
            service_ctx = HierarchicalContext(
                repo_id=service_id,
                repo_name=service.name,
                repo_path=service.path,
                parent_id=root.repo_id,
                children=[],
                level=ContextLevel.SERVICE,
                full_path=f"{root.full_path}/{service.name}",
                
                # Technology stack (service-specific)
                languages=[service.language] if service.language else [],
                primary_language=service.language,
                frameworks=service.dependencies[:5] if service.dependencies else [],
                databases=[],
                tools=[],
                
                # Architecture (inherited from root)
                architecture_type=root.architecture_type,
                architecture_confidence=root.architecture_confidence,
                architecture_description=f"Service: {service.name}",
                service_count=1,
                is_microservices=True,
                layers=service.layers if service.layers else [],
                
                # API (service-specific)
                endpoints=[{'path': ep, 'service': service.name} for ep in service.endpoints] if service.endpoints else [],
                endpoint_count=len(service.endpoints) if service.endpoints else 0,
                has_rest_api=service.has_api,
                has_graphql=False,
                
                # Metrics
                total_files=0,  # TODO: Calculate from file list
                code_files=0,
                test_files=0,
                doc_files=0,
                total_lines=0,
                modularity_score=root.modularity_score,
                level_files=0,
                level_lines=0,
                
                # Entry points
                entry_points=service.entry_points if service.entry_points else [],
                
                # Summaries
                brief_description=f"{service.name} service",
                key_features=[],
                technical_highlights=[],
                recommended_starting_points=[],
                
                # Filtering
                file_patterns=[f"{service.path}/**/*"],
                file_paths=[]
            )
            
            # Add to parent's children
            root.children.append(service_id)
            
            # Store
            self.contexts[service_id] = service_ctx
            
            logger.info(f"    Created service context: {service.name}")
    
    async def _build_module_contexts(
        self,
        root: HierarchicalContext,
        analysis_report: AnalysisReport
    ) -> None:
        """Build module-level contexts (directories/packages)."""
        # For now, create module contexts for major directories
        # In a full implementation, this would analyze the directory structure
        
        # Common module patterns
        common_modules = [
            "src",
            "lib",
            "tests",
            "docs",
            "scripts",
            "config",
            "api",
            "models",
            "services",
            "utils",
            "core"
        ]
        
        # Check if these directories exist in the repo
        # (In practice, would scan actual file structure)
        for module_name in common_modules[:5]:  # Limit to 5 for now
            module_id = f"{root.repo_id}/module/{module_name}"
            
            module_ctx = HierarchicalContext(
                repo_id=module_id,
                repo_name=module_name,
                repo_path=f"{root.repo_path}/{module_name}",
                parent_id=root.repo_id,
                children=[],
                level=ContextLevel.MODULE,
                full_path=f"{root.full_path}/{module_name}",
                
                # Inherit from root
                languages=root.languages,
                primary_language=root.primary_language,
                frameworks=root.frameworks,
                databases=root.databases,
                tools=root.tools,
                architecture_type=root.architecture_type,
                architecture_confidence=root.architecture_confidence,
                architecture_description=f"Module: {module_name}",
                service_count=0,
                is_microservices=False,
                layers=[],
                
                # API
                endpoints=[],
                endpoint_count=0,
                has_rest_api=False,
                has_graphql=False,
                
                # Metrics
                total_files=0,
                code_files=0,
                test_files=0,
                doc_files=0,
                total_lines=0,
                modularity_score=root.modularity_score,
                level_files=0,
                level_lines=0,
                
                # Entry points
                entry_points=[],
                
                # Summaries
                brief_description=f"{module_name} module",
                key_features=[],
                technical_highlights=[],
                recommended_starting_points=[],
                
                # Filtering
                file_patterns=[f"**/{module_name}/**/*"],
                file_paths=[]
            )
            
            # Add to parent's children
            root.children.append(module_id)
            
            # Store
            self.contexts[module_id] = module_ctx
            
            logger.info(f"    Created module context: {module_name}")
    
    def get_context(self, context_id: str) -> Optional[HierarchicalContext]:
        """Get context by ID."""
        return self.contexts.get(context_id)
    
    def get_children(self, context_id: str) -> List[HierarchicalContext]:
        """Get all child contexts."""
        context = self.get_context(context_id)
        if not context:
            return []
        
        return [self.contexts[child_id] for child_id in context.children if child_id in self.contexts]
    
    def get_parent(self, context_id: str) -> Optional[HierarchicalContext]:
        """Get parent context."""
        context = self.get_context(context_id)
        if not context or not context.parent_id:
            return None
        
        return self.get_context(context.parent_id)
    
    def get_path_to_root(self, context_id: str) -> List[HierarchicalContext]:
        """Get path from context to root."""
        path = []
        current = self.get_context(context_id)
        
        while current:
            path.append(current)
            current = self.get_parent(current.repo_id) if current.parent_id else None
        
        return path[::-1]  # Reverse to root-first
    
    def get_all_descendants(self, context_id: str) -> List[HierarchicalContext]:
        """Get all descendant contexts recursively."""
        descendants = []
        
        def collect_descendants(ctx_id: str):
            children = self.get_children(ctx_id)
            for child in children:
                descendants.append(child)
                collect_descendants(child.repo_id)
        
        collect_descendants(context_id)
        return descendants
    
    def find_context_by_path(self, full_path: str) -> Optional[HierarchicalContext]:
        """Find context by full hierarchical path."""
        for context in self.contexts.values():
            if context.full_path == full_path:
                return context
        return None
    
    def get_chromadb_filter(self, context: HierarchicalContext) -> Dict:
        """
        Get ChromaDB filter for hierarchical context.
        
        Filters documents to only those in this context's scope.
        
        Args:
            context: Hierarchical context
        
        Returns:
            ChromaDB where filter
        """
        # Base filter: repository
        base_filter = {"repo_id": context.repo_id.split('/')[0]}  # Root repo ID
        
        # Add file path filters based on level
        if context.level == ContextLevel.ROOT:
            # Root context: all files in repo
            return base_filter
        
        elif context.level == ContextLevel.SERVICE:
            # Service context: filter by service path
            return {
                **base_filter,
                "file_path": {"$glob": context.file_patterns[0]} if context.file_patterns else None
            }
        
        elif context.level == ContextLevel.MODULE:
            # Module context: filter by module path
            return {
                **base_filter,
                "file_path": {"$glob": context.file_patterns[0]} if context.file_patterns else None
            }
        
        return base_filter
    
    def get_context_summary(self, context: HierarchicalContext) -> str:
        """Get human-readable context summary."""
        path = self.get_path_to_root(context.repo_id)
        path_str = " > ".join([ctx.repo_name for ctx in path])
        
        children_count = len(context.children)
        level_name = context.level.name.lower()
        
        summary = f"""
Context: {context.repo_name}
Level: {level_name}
Path: {path_str}
Full Path: {context.full_path}
Children: {children_count}
Files: {context.level_files} (at this level)
Primary Language: {context.primary_language or 'N/A'}
"""
        if context.level == ContextLevel.SERVICE:
            summary += f"\nEndpoints: {context.endpoint_count}"
        
        return summary.strip()


# Singleton
_hierarchical_context_manager_instance = None

def get_hierarchical_context_manager() -> HierarchicalContextManager:
    """Get singleton hierarchical context manager instance."""
    global _hierarchical_context_manager_instance
    if _hierarchical_context_manager_instance is None:
        _hierarchical_context_manager_instance = HierarchicalContextManager()
    return _hierarchical_context_manager_instance

