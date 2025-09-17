"""Relationships repository for data access operations.

Handles relationship data queries and graph operations.
"""
from typing import List, Optional, Dict, Any
from ...core.repository import BaseRepository
from ...db.queries import execute_query
from ...core.entities import DocumentRelationship, GraphNode, GraphEdge


class RelationshipsRepository(BaseRepository[DocumentRelationship]):
    """Repository for relationship data access."""

    def __init__(self):
        super().__init__("document_relationships")

    def _row_to_entity(self, row: Dict[str, Any]) -> DocumentRelationship:
        """Convert database row to DocumentRelationship entity."""
        return DocumentRelationship(
            id=row['id'],
            source_document_id=row['source_document_id'],
            target_document_id=row['target_document_id'],
            relationship_type=row['relationship_type'],
            strength=row.get('strength', 1.0),
            metadata=row.get('metadata', {}),
            created_at=row['created_at'],
            updated_at=row.get('updated_at')
        )

    def _entity_to_row(self, entity: DocumentRelationship) -> Dict[str, Any]:
        """Convert DocumentRelationship entity to database row."""
        return {
            'id': entity.id,
            'source_document_id': entity.source_document_id,
            'target_document_id': entity.target_document_id,
            'relationship_type': entity.relationship_type,
            'strength': entity.strength,
            'metadata': entity.metadata,
            'created_at': entity.created_at.isoformat(),
            'updated_at': entity.updated_at.isoformat() if entity.updated_at else None
        }

    def get_relationships_for_document(self, document_id: str, relationship_type: Optional[str] = None,
                                     direction: str = "both", limit: int = 50) -> List[DocumentRelationship]:
        """Get relationships for a specific document."""
        query_conditions = []
        params = []

        if direction in ["outgoing", "both"]:
            query_conditions.append("source_document_id = ?")
            params.append(document_id)

        if direction in ["incoming", "both"]:
            if query_conditions:
                query_conditions[0] = f"({query_conditions[0]} OR target_document_id = ?)"
            else:
                query_conditions.append("target_document_id = ?")
            params.append(document_id)

        if relationship_type:
            query_conditions.append("relationship_type = ?")
            params.append(relationship_type)

        where_clause = " AND ".join(query_conditions) if query_conditions else "1=1"

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
        """
        params.append(limit)

        rows = execute_query(query, params, fetch_all=True)
        return [self._row_to_entity(row) for row in rows]

    def get_relationship_types(self) -> Dict[str, int]:
        """Get distribution of relationship types."""
        rows = execute_query("""
            SELECT relationship_type, COUNT(*) as count
            FROM document_relationships
            GROUP BY relationship_type
            ORDER BY count DESC
        """, fetch_all=True)

        return {row['relationship_type']: row['count'] for row in rows}

    def find_paths(self, start_id: str, end_id: str, max_depth: int = 3) -> List[List[str]]:
        """Find paths between two documents."""
        # Simplified path finding - in a full implementation this would use graph algorithms
        paths = []
        visited = set()

        def dfs(current_id: str, target_id: str, path: List[str], depth: int):
            if depth > max_depth or current_id in visited:
                return

            visited.add(current_id)
            path.append(current_id)

            if current_id == target_id and len(path) > 1:
                paths.append(path.copy())
            else:
                # Get outgoing relationships
                relationships = self.get_relationships_for_document(current_id, direction="outgoing")
                for rel in relationships:
                    if rel.target_document_id not in path:
                        dfs(rel.target_document_id, target_id, path, depth + 1)

            path.pop()
            visited.remove(current_id)

        dfs(start_id, end_id, [], 0)
        return paths

    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics."""
        stats = {
            'total_relationships': 0,
            'unique_documents': 0,
            'relationship_types': {},
            'avg_degree': 0.0,
            'density': 0.0
        }

        # Basic counts
        result = execute_query("SELECT COUNT(*) as count FROM document_relationships", fetch_one=True)
        stats['total_relationships'] = result['count'] if result else 0

        # Unique documents
        result = execute_query("""
            SELECT COUNT(DISTINCT document_id) as count FROM (
                SELECT source_document_id as document_id FROM document_relationships
                UNION
                SELECT target_document_id as document_id FROM document_relationships
            )
        """, fetch_one=True)
        stats['unique_documents'] = result['count'] if result else 0

        # Relationship types
        stats['relationship_types'] = self.get_relationship_types()

        # Calculate average degree
        if stats['unique_documents'] > 0:
            total_connections = execute_query("""
                SELECT COUNT(*) as count FROM (
                    SELECT source_document_id FROM document_relationships
                    UNION ALL
                    SELECT target_document_id FROM document_relationships
                )
            """, fetch_one=True)
            total_connections_count = total_connections['count'] if total_connections else 0
            stats['avg_degree'] = total_connections_count / stats['unique_documents']

        return stats

    def get_related_documents(self, document_id: str, depth: int = 1) -> List[Dict[str, Any]]:
        """Get related documents up to specified depth."""
        related = set()
        current_level = {document_id}

        for _ in range(depth):
            next_level = set()
            for doc_id in current_level:
                relationships = self.get_relationships_for_document(doc_id)
                for rel in relationships:
                    if rel.source_document_id == doc_id:
                        next_level.add(rel.target_document_id)
                        related.add(rel.target_document_id)
                    elif rel.target_document_id == doc_id:
                        next_level.add(rel.source_document_id)
                        related.add(rel.source_document_id)

            current_level = next_level
            if not current_level:
                break

        # Get document details for related documents
        if related:
            placeholders = ','.join(['?'] * len(related))
            rows = execute_query(
                f"SELECT id, content_hash, metadata FROM documents WHERE id IN ({placeholders})",
                list(related),
                fetch_all=True
            )
            return rows

        return []
