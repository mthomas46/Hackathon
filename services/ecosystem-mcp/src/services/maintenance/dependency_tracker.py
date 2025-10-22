"""
Dependency Tracker Service

Tracks dependencies between documentation:
- Cross-references between documents
- Documentation dependency graph
- Impact analysis for changes
- Orphaned document detection
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from uuid import UUID
from collections import defaultdict
import re

from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.db_models import DocumentModel
from ...storage.repositories import DocumentRepository
from ...storage import get_database

logger = logging.getLogger(__name__)


class DocumentDependency:
    """Represents a dependency between documents."""
    
    def __init__(
        self,
        source_doc_id: UUID,
        target_doc_id: UUID,
        dependency_type: str,
        reference_text: str
    ):
        self.source_doc_id = source_doc_id
        self.target_doc_id = target_doc_id
        self.dependency_type = dependency_type  # link, reference, import, etc.
        self.reference_text = reference_text
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_doc_id": str(self.source_doc_id),
            "target_doc_id": str(self.target_doc_id),
            "dependency_type": self.dependency_type,
            "reference_text": self.reference_text
        }


class DependencyTracker:
    """
    Track documentation dependencies.
    
    Features:
    - Build dependency graph
    - Find cross-references
    - Impact analysis
    - Orphaned document detection
    - Circular dependency detection
    """
    
    def __init__(self):
        """Initialize dependency tracker."""
        self.logger = logging.getLogger(__name__)
    
    async def build_dependency_graph(
        self,
        service_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build documentation dependency graph.
        
        Args:
            service_name: Optional service filter
        
        Returns:
            Dependency graph with nodes and edges
        """
        try:
            self.logger.info(f"🕸️ Building dependency graph (service={service_name})")
            
            async with get_database().session() as session:
                doc_repo = DocumentRepository(session)
                
                # Get all documents
                if service_name:
                    documents = await doc_repo.get_by_service(service_name, limit=10000)
                else:
                    documents = await doc_repo.get_all(limit=10000)
                
                self.logger.info(f"   📄 Analyzing {len(documents)} documents")
                
                # Extract dependencies
                dependencies = await self._extract_dependencies(documents)
                
                # Build graph structure
                nodes = self._build_nodes(documents)
                edges = self._build_edges(dependencies)
                
                # Analyze graph
                stats = self._analyze_graph(nodes, edges, documents)
                
                return {
                    "nodes": nodes,
                    "edges": edges,
                    "statistics": stats,
                    "metadata": {
                        "service_name": service_name,
                        "generated_at": datetime.utcnow().isoformat()
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to build dependency graph: {e}", exc_info=True)
            raise
    
    async def _extract_dependencies(
        self,
        documents: List[DocumentModel]
    ) -> List[DocumentDependency]:
        """Extract dependencies from documents."""
        dependencies = []
        
        # Build path-to-document mapping
        doc_map = {doc.file_path: doc for doc in documents}
        
        # Patterns to find references
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
        code_ref_pattern = re.compile(r'see `([^`]+)`|refer to `([^`]+)`', re.IGNORECASE)
        
        for doc in documents:
            if not doc.content:
                continue
            
            # Find markdown links
            links = link_pattern.findall(doc.content)
            for text, path in links:
                if path.startswith(('http://', 'https://', '#')):
                    continue  # Skip external links and anchors
                
                # Try to find target document
                target_doc = doc_map.get(path)
                if target_doc:
                    dependencies.append(DocumentDependency(
                        source_doc_id=doc.id,
                        target_doc_id=target_doc.id,
                        dependency_type="link",
                        reference_text=text
                    ))
            
            # Find code references
            refs = code_ref_pattern.findall(doc.content)
            for ref_groups in refs:
                for ref in ref_groups:
                    if ref:  # Non-empty capture group
                        # Try to match to a document
                        for target_doc in documents:
                            if ref.lower() in target_doc.file_path.lower():
                                dependencies.append(DocumentDependency(
                                    source_doc_id=doc.id,
                                    target_doc_id=target_doc.id,
                                    dependency_type="reference",
                                    reference_text=ref
                                ))
                                break
        
        return dependencies
    
    def _build_nodes(self, documents: List[DocumentModel]) -> List[Dict[str, Any]]:
        """Build graph nodes."""
        return [
            {
                "id": str(doc.id),
                "file_path": doc.file_path,
                "service_name": doc.service_name,
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            }
            for doc in documents
        ]
    
    def _build_edges(
        self,
        dependencies: List[DocumentDependency]
    ) -> List[Dict[str, Any]]:
        """Build graph edges."""
        return [dep.to_dict() for dep in dependencies]
    
    def _analyze_graph(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        documents: List[DocumentModel]
    ) -> Dict[str, Any]:
        """Analyze graph structure."""
        # Build adjacency lists
        outgoing = defaultdict(list)  # source -> targets
        incoming = defaultdict(list)  # target -> sources
        
        for edge in edges:
            source = edge["source_doc_id"]
            target = edge["target_doc_id"]
            outgoing[source].append(target)
            incoming[target].append(source)
        
        # Find orphaned documents (no incoming or outgoing references)
        orphaned = []
        for node in nodes:
            node_id = node["id"]
            if node_id not in outgoing and node_id not in incoming:
                orphaned.append(node)
        
        # Find hub documents (many incoming references)
        hubs = []
        for node in nodes:
            node_id = node["id"]
            incoming_count = len(incoming.get(node_id, []))
            if incoming_count >= 5:  # Threshold for hub
                hubs.append({
                    "node": node,
                    "incoming_references": incoming_count
                })
        
        hubs.sort(key=lambda x: x["incoming_references"], reverse=True)
        
        # Calculate connectivity
        connected_nodes = set(outgoing.keys()) | set(incoming.keys())
        connectivity = (len(connected_nodes) / len(nodes) * 100) if nodes else 0
        
        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "orphaned_documents": len(orphaned),
            "hub_documents": len(hubs),
            "connectivity_percentage": round(connectivity, 1),
            "top_hubs": hubs[:10],
            "sample_orphaned": orphaned[:10]
        }
    
    async def find_impact(
        self,
        document_id: UUID
    ) -> Dict[str, Any]:
        """
        Find impact of changing a document.
        
        Args:
            document_id: Document to analyze
        
        Returns:
            Impact analysis showing affected documents
        """
        try:
            self.logger.info(f"🎯 Analyzing impact of document {document_id}")
            
            # Build graph
            graph = await self.build_dependency_graph()
            
            # Find all documents that reference this one
            affected = []
            for edge in graph["edges"]:
                if edge["target_doc_id"] == str(document_id):
                    # Find source document info
                    source_node = next(
                        (n for n in graph["nodes"] if n["id"] == edge["source_doc_id"]),
                        None
                    )
                    if source_node:
                        affected.append({
                            "document_id": source_node["id"],
                            "file_path": source_node["file_path"],
                            "dependency_type": edge["dependency_type"],
                            "reference_text": edge["reference_text"]
                        })
            
            return {
                "document_id": str(document_id),
                "directly_affected": len(affected),
                "affected_documents": affected,
                "impact_level": self._calculate_impact_level(len(affected)),
                "recommendation": self._get_impact_recommendation(len(affected))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze impact: {e}", exc_info=True)
            raise
    
    def _calculate_impact_level(self, affected_count: int) -> str:
        """Calculate impact level based on affected documents."""
        if affected_count == 0:
            return "NONE"
        elif affected_count <= 2:
            return "LOW"
        elif affected_count <= 5:
            return "MEDIUM"
        elif affected_count <= 10:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _get_impact_recommendation(self, affected_count: int) -> str:
        """Get recommendation based on impact."""
        if affected_count == 0:
            return "No dependencies - safe to modify or delete"
        elif affected_count <= 2:
            return "Low impact - review affected documents after changes"
        elif affected_count <= 5:
            return "Medium impact - update cross-references in affected documents"
        else:
            return "High impact - coordinate changes with affected documents"
    
    async def detect_circular_dependencies(
        self,
        service_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect circular dependencies in documentation.
        
        Args:
            service_name: Optional service filter
        
        Returns:
            List of circular dependency chains
        """
        try:
            self.logger.info(f"🔄 Detecting circular dependencies (service={service_name})")
            
            graph = await self.build_dependency_graph(service_name=service_name)
            
            # Build adjacency list
            adj_list = defaultdict(list)
            for edge in graph["edges"]:
                adj_list[edge["source_doc_id"]].append(edge["target_doc_id"])
            
            # Detect cycles using DFS
            cycles = []
            visited = set()
            rec_stack = set()
            
            def dfs(node: str, path: List[str]):
                visited.add(node)
                rec_stack.add(node)
                path.append(node)
                
                for neighbor in adj_list.get(node, []):
                    if neighbor not in visited:
                        dfs(neighbor, path.copy())
                    elif neighbor in rec_stack:
                        # Found cycle
                        cycle_start = path.index(neighbor)
                        cycle = path[cycle_start:]
                        cycles.append(cycle)
                
                rec_stack.remove(node)
            
            # Run DFS from each node
            for node in graph["nodes"]:
                if node["id"] not in visited:
                    dfs(node["id"], [])
            
            # Get node details for cycles
            cycles_with_details = []
            for cycle in cycles:
                cycle_details = []
                for node_id in cycle:
                    node = next((n for n in graph["nodes"] if n["id"] == node_id), None)
                    if node:
                        cycle_details.append({
                            "document_id": node_id,
                            "file_path": node["file_path"]
                        })
                cycles_with_details.append(cycle_details)
            
            return {
                "total_cycles": len(cycles_with_details),
                "cycles": cycles_with_details,
                "recommendation": (
                    "✅ No circular dependencies found"
                    if not cycles_with_details
                    else f"⚠️ Found {len(cycles_with_details)} circular dependencies - review and break cycles"
                ),
                "metadata": {
                    "service_name": service_name,
                    "analyzed_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to detect circular dependencies: {e}", exc_info=True)
            raise

