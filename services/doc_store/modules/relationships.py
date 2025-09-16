# ============================================================================
# RELATIONSHIPS MODULE
# ============================================================================
"""
Document relationship graph for Doc Store service.

Provides comprehensive relationship mapping, graph analysis, and intelligent
relationship extraction from document content and metadata.
"""

import re
import json
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime

from services.shared.utilities import utc_now
from .shared_utils import execute_db_query, get_document_by_id
from .caching import docstore_cache


@dataclass
class Relationship:
    """Document relationship representation."""
    id: str
    source_id: str
    target_id: str
    relationship_type: str
    strength: float
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


@dataclass
class GraphNode:
    """Graph node with document information."""
    document_id: str
    title: str
    content_type: str
    metadata: Dict[str, Any]
    degree: int = 0


@dataclass
class GraphEdge:
    """Graph edge with relationship information."""
    source_id: str
    target_id: str
    relationship_type: str
    strength: float
    metadata: Dict[str, Any]


class RelationshipExtractor:
    """Extracts relationships from document content and metadata."""

    # Patterns for different types of relationships
    REFERENCE_PATTERNS = [
        r'doc:([a-zA-Z0-9_-]+)',  # doc:document_id
        r'#([a-zA-Z0-9_-]+)',     # #reference_id
        r'@([a-zA-Z0-9_-]+)',     # @mention_id
    ]

    URL_PATTERNS = [
        r'https?://[^\s<>"]+',     # HTTP URLs
        r'github\.com/[^\s<>"]+',  # GitHub URLs
        r'jira\.[^\s<>"]+',        # Jira URLs
    ]

    def __init__(self):
        self.compiled_reference_patterns = [re.compile(p) for p in self.REFERENCE_PATTERNS]
        self.compiled_url_patterns = [re.compile(p) for p in self.URL_PATTERNS]

    def extract_relationships(self, document_id: str, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract relationships from document content and metadata."""
        relationships = []

        # Extract references from content
        content_relationships = self._extract_from_content(document_id, content)
        relationships.extend(content_relationships)

        # Extract relationships from metadata
        metadata_relationships = self._extract_from_metadata(document_id, metadata)
        relationships.extend(metadata_relationships)

        # Extract analysis relationships
        analysis_relationships = self._extract_analysis_relationships(document_id)
        relationships.extend(analysis_relationships)

        return relationships

    def _extract_from_content(self, document_id: str, content: str) -> List[Dict[str, Any]]:
        """Extract relationships from document content."""
        relationships = []

        # Find all references
        for pattern in self.compiled_reference_patterns:
            matches = pattern.findall(content)
            for match in matches:
                # Check if referenced document exists
                if self._document_exists(match):
                    relationships.append({
                        "source_id": document_id,
                        "target_id": match,
                        "relationship_type": "references",
                        "strength": 0.8,
                        "metadata": {"extraction_method": "content_pattern", "pattern": pattern.pattern}
                    })

        # Find URLs and create external reference relationships
        for pattern in self.compiled_url_patterns:
            matches = pattern.findall(content)
            for url in matches:
                url_hash = str(hash(url))[:16]  # Create consistent ID from URL
                relationships.append({
                    "source_id": document_id,
                    "target_id": f"url:{url_hash}",
                    "relationship_type": "external_reference",
                    "strength": 0.5,
                    "metadata": {"url": url, "extraction_method": "url_pattern"}
                })

        return relationships

    def _extract_from_metadata(self, document_id: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract relationships from document metadata."""
        relationships = []

        # Extract source relationships
        if "source_refs" in metadata:
            for ref in metadata["source_refs"]:
                if isinstance(ref, str) and self._document_exists(ref):
                    relationships.append({
                        "source_id": document_id,
                        "target_id": ref,
                        "relationship_type": "derived_from",
                        "strength": 0.9,
                        "metadata": {"extraction_method": "source_refs"}
                    })

        # Extract correlation relationships
        if "correlation_id" in metadata:
            correlation_docs = self._find_correlation_documents(metadata["correlation_id"])
            for correlated_doc in correlation_docs:
                if correlated_doc != document_id:
                    relationships.append({
                        "source_id": document_id,
                        "target_id": correlated_doc,
                        "relationship_type": "correlated",
                        "strength": 0.7,
                        "metadata": {"correlation_id": metadata["correlation_id"]}
                    })

        return relationships

    def _extract_analysis_relationships(self, document_id: str) -> List[Dict[str, Any]]:
        """Extract relationships based on analysis data."""
        relationships = []

        try:
            # Find analyses for this document
            analyses = execute_db_query(
                "SELECT id, analyzer FROM analyses WHERE document_id = ?",
                (document_id,),
                fetch_all=True
            )

            for analysis in analyses:
                # Create analysis relationship (document -> analysis result)
                relationships.append({
                    "source_id": document_id,
                    "target_id": analysis['id'],
                    "relationship_type": "analyzed_by",
                    "strength": 0.6,
                    "metadata": {"analyzer": analysis['analyzer'], "extraction_method": "analysis_link"}
                })

        except Exception:
            pass

        return relationships

    def _document_exists(self, document_id: str) -> bool:
        """Check if a document exists."""
        try:
            result = execute_db_query(
                "SELECT COUNT(*) FROM documents WHERE id = ?",
                (document_id,),
                fetch_one=True
            )
            return result[0] > 0 if result else False
        except Exception:
            return False

    def _find_correlation_documents(self, correlation_id: str) -> List[str]:
        """Find documents with the same correlation ID."""
        try:
            results = execute_db_query(
                "SELECT id FROM documents WHERE metadata LIKE ?",
                (f'%{correlation_id}%',),
                fetch_all=True
            )
            return [row['id'] for row in results]
        except Exception:
            return []


class RelationshipGraph:
    """Document relationship graph with traversal and analysis capabilities."""

    def __init__(self):
        self.extractor = RelationshipExtractor()

    def add_relationship(self, source_id: str, target_id: str, relationship_type: str,
                        strength: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a relationship between documents."""
        try:
            relationship_id = f"{source_id}:{target_id}:{relationship_type}"
            now = utc_now().isoformat()

            execute_db_query("""
                INSERT OR REPLACE INTO document_relationships
                (id, source_document_id, target_document_id, relationship_type, strength, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                relationship_id,
                source_id,
                target_id,
                relationship_type,
                strength,
                json.dumps(metadata or {}),
                now,
                now
            ))

            # Invalidate relevant caches
            cache_tags = ["relationships", f"doc:{source_id}", f"doc:{target_id}"]
            docstore_cache.invalidate(tags=cache_tags)

            return True

        except Exception:
            return False

    def get_relationships(self, document_id: str, relationship_type: Optional[str] = None,
                         direction: str = "both", limit: int = 50) -> Dict[str, Any]:
        """Get relationships for a document."""
        try:
            # Build query based on direction
            if direction == "outgoing":
                where_clause = "dr.source_document_id = ?"
                params = [document_id]
            elif direction == "incoming":
                where_clause = "dr.target_document_id = ?"
                params = [document_id]
            else:  # both
                where_clause = "(dr.source_document_id = ? OR dr.target_document_id = ?)"
                params = [document_id, document_id]

            if relationship_type:
                where_clause += " AND dr.relationship_type = ?"
                params.append(relationship_type)

            query = f"""
                SELECT dr.*, d.title, d.metadata as doc_metadata
                FROM document_relationships dr
                LEFT JOIN documents d ON (
                    CASE WHEN dr.source_document_id = ? THEN dr.target_document_id
                         ELSE dr.source_document_id END = d.id
                )
                WHERE {where_clause}
                ORDER BY dr.strength DESC, dr.updated_at DESC
                LIMIT ?
            """
            params.extend([document_id, limit])

            results = execute_db_query(query, tuple(params), fetch_all=True)

            relationships = []
            for row in results:
                relationships.append({
                    "id": row['id'],
                    "source_id": row['source_document_id'],
                    "target_id": row['target_document_id'],
                    "relationship_type": row['relationship_type'],
                    "strength": row['strength'],
                    "metadata": json.loads(row['metadata'] or '{}'),
                    "created_at": row['created_at'],
                    "updated_at": row['updated_at'],
                    "related_document_title": row['title'],
                    "related_document_metadata": json.loads(row['doc_metadata'] or '{}')
                })

            return {
                "document_id": document_id,
                "relationships": relationships,
                "total_count": len(relationships),
                "direction": direction,
                "relationship_type_filter": relationship_type
            }

        except Exception as e:
            return {"error": str(e)}

    def find_paths(self, start_id: str, end_id: str, max_depth: int = 3) -> List[List[Dict[str, Any]]]:
        """Find paths between two documents in the relationship graph."""
        try:
            paths = []
            visited = set()
            queue = deque([(start_id, [start_id], [])])  # (current_node, path, edges)

            while queue and len(paths) < 10:  # Limit results
                current_node, path, edges = queue.popleft()

                if len(path) > max_depth + 1:  # +1 because path includes start
                    continue

                if current_node == end_id and len(path) > 1:
                    # Found a path
                    paths.append(edges)
                    continue

                if current_node in visited and len(path) > 1:
                    continue

                visited.add(current_node)

                # Get relationships from current node
                relationships = execute_db_query("""
                    SELECT source_document_id, target_document_id, relationship_type, strength, metadata
                    FROM document_relationships
                    WHERE source_document_id = ? OR target_document_id = ?
                """, (current_node, current_node), fetch_all=True)

                for rel in relationships:
                    next_node = rel['target_document_id'] if rel['source_document_id'] == current_node else rel['source_document_id']

                    if next_node not in path:  # Avoid cycles
                        new_path = path + [next_node]
                        new_edges = edges + [{
                            "source": rel['source_document_id'],
                            "target": rel['target_document_id'],
                            "type": rel['relationship_type'],
                            "strength": rel['strength'],
                            "metadata": json.loads(rel['metadata'] or '{}')
                        }]
                        queue.append((next_node, new_path, new_edges))

            return paths

        except Exception:
            return []

    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics."""
        try:
            # Basic relationship counts
            total_relationships = execute_db_query(
                "SELECT COUNT(*) FROM document_relationships",
                fetch_one=True
            )[0]

            # Relationship types distribution
            type_distribution = execute_db_query("""
                SELECT relationship_type, COUNT(*) as count
                FROM document_relationships
                GROUP BY relationship_type
                ORDER BY count DESC
            """, fetch_all=True)

            # Node degrees (documents with most relationships)
            node_degrees = execute_db_query("""
                SELECT document_id, COUNT(*) as degree
                FROM (
                    SELECT source_document_id as document_id FROM document_relationships
                    UNION ALL
                    SELECT target_document_id as document_id FROM document_relationships
                )
                GROUP BY document_id
                ORDER BY degree DESC
                LIMIT 20
            """, fetch_all=True)

            # Connected components (simplified)
            connected_components = self._analyze_connected_components()

            # Average relationship strength
            avg_strength = execute_db_query(
                "SELECT AVG(strength) FROM document_relationships",
                fetch_one=True
            )[0] or 0

            return {
                "total_relationships": total_relationships,
                "relationship_types": [{"type": row['relationship_type'], "count": row['count']} for row in type_distribution],
                "top_nodes_by_degree": [{"document_id": row['document_id'], "degree": row['degree']} for row in node_degrees],
                "connected_components": connected_components,
                "average_relationship_strength": round(avg_strength, 3),
                "graph_density": self._calculate_graph_density(total_relationships)
            }

        except Exception as e:
            return {"error": str(e)}

    def _analyze_connected_components(self) -> Dict[str, Any]:
        """Analyze connected components in the graph."""
        try:
            # Get all relationships
            relationships = execute_db_query(
                "SELECT source_document_id, target_document_id FROM document_relationships",
                fetch_all=True
            )

            # Build adjacency list
            graph = defaultdict(set)
            all_nodes = set()

            for rel in relationships:
                source = rel['source_document_id']
                target = rel['target_document_id']
                graph[source].add(target)
                graph[target].add(source)
                all_nodes.add(source)
                all_nodes.add(target)

            # Find connected components using DFS
            visited = set()
            components = []

            def dfs(node, component):
                visited.add(node)
                component.append(node)
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        dfs(neighbor, component)

            for node in all_nodes:
                if node not in visited:
                    component = []
                    dfs(node, component)
                    components.append(sorted(component))

            # Sort components by size
            components.sort(key=len, reverse=True)

            return {
                "total_components": len(components),
                "largest_component_size": len(components[0]) if components else 0,
                "average_component_size": round(sum(len(c) for c in components) / len(components), 2) if components else 0,
                "isolated_nodes": len([c for c in components if len(c) == 1])
            }

        except Exception:
            return {"error": "Failed to analyze components"}

    def _calculate_graph_density(self, total_relationships: int) -> float:
        """Calculate graph density (relationships / possible relationships)."""
        try:
            total_nodes = execute_db_query("SELECT COUNT(*) FROM documents", fetch_one=True)[0]

            if total_nodes < 2:
                return 0.0

            # Possible relationships in undirected graph
            possible_relationships = (total_nodes * (total_nodes - 1)) / 2

            return round(total_relationships / possible_relationships, 4) if possible_relationships > 0 else 0.0

        except Exception:
            return 0.0

    def extract_and_store_relationships(self, document_id: str, content: str, metadata: Dict[str, Any]) -> int:
        """Extract relationships from document and store them."""
        try:
            relationships = self.extractor.extract_relationships(document_id, content, metadata)
            stored_count = 0

            for rel in relationships:
                if self.add_relationship(
                    rel["source_id"],
                    rel["target_id"],
                    rel["relationship_type"],
                    rel["strength"],
                    rel["metadata"]
                ):
                    stored_count += 1

            return stored_count

        except Exception:
            return 0


# Global relationship graph instance
relationship_graph = RelationshipGraph()
