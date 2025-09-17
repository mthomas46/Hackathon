"""Tagging repository for data access operations.

Handles tag and taxonomy data operations.
"""
import json
from typing import List, Optional, Dict, Any
from ...core.repository import BaseRepository
from ...db.queries import execute_query
from ...core.entities import DocumentTag, TaxonomyNode


class TaggingRepository(BaseRepository[DocumentTag]):
    """Repository for tagging data access."""

    def __init__(self):
        super().__init__("document_tags")

    def _row_to_entity(self, row: Dict[str, Any]) -> DocumentTag:
        """Convert database row to DocumentTag entity."""
        return DocumentTag(
            id=row['id'],
            document_id=row['document_id'],
            tag=row['tag'],
            confidence=row.get('confidence', 1.0),
            created_at=row['created_at'],
            updated_at=row.get('updated_at')
        )

    def _entity_to_row(self, entity: DocumentTag) -> Dict[str, Any]:
        """Convert DocumentTag entity to database row."""
        return {
            'id': entity.id,
            'document_id': entity.document_id,
            'tag': entity.tag,
            'confidence': entity.confidence,
            'created_at': entity.created_at.isoformat(),
            'updated_at': entity.updated_at.isoformat() if entity.updated_at else None
        }

    def get_tags_for_document(self, document_id: str) -> List[DocumentTag]:
        """Get all tags for a document."""
        rows = execute_query(
            f"SELECT * FROM {self.table_name} WHERE document_id = ? ORDER BY confidence DESC",
            (document_id,),
            fetch_all=True
        )
        return [self._row_to_entity(row) for row in rows]

    def get_documents_by_tag(self, tag: str, min_confidence: float = 0.0) -> List[str]:
        """Get document IDs that have a specific tag."""
        rows = execute_query(
            f"SELECT document_id FROM {self.table_name} WHERE tag = ? AND confidence >= ?",
            (tag, min_confidence),
            fetch_all=True
        )
        return [row['document_id'] for row in rows]

    def search_tags(self, query: str, categories: Optional[List[str]] = None,
                   min_confidence: float = 0.0, limit: int = 50) -> List[Dict[str, Any]]:
        """Search tags with filtering."""
        conditions = ["confidence >= ?"]
        params = [min_confidence]

        if categories:
            placeholders = ','.join(['?'] * len(categories))
            conditions.append(f"category IN ({placeholders})")
            params.extend(categories)

        if query:
            conditions.append("(tag LIKE ? OR description LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        where_clause = " AND ".join(conditions)

        # Join with taxonomy to get category info
        rows = execute_query(f"""
            SELECT dt.*, tn.category, tn.description
            FROM {self.table_name} dt
            LEFT JOIN taxonomy tn ON dt.tag = tn.tag
            WHERE {where_clause}
            ORDER BY dt.confidence DESC
            LIMIT ?
        """, params + [limit], fetch_all=True)

        return rows

    def get_tag_statistics(self) -> Dict[str, Any]:
        """Get comprehensive tag statistics."""
        # Tag frequency distribution
        tag_rows = execute_query("""
            SELECT tag, COUNT(*) as count, AVG(confidence) as avg_confidence
            FROM document_tags
            GROUP BY tag
            ORDER BY count DESC
            LIMIT 100
        """, fetch_all=True)

        # Category distribution
        category_rows = execute_query("""
            SELECT tn.category, COUNT(dt.id) as count
            FROM taxonomy tn
            LEFT JOIN document_tags dt ON tn.tag = dt.tag
            GROUP BY tn.category
            ORDER BY count DESC
        """, fetch_all=True)

        # Confidence distribution
        confidence_rows = execute_query("""
            SELECT
                CASE
                    WHEN confidence >= 0.9 THEN 'high'
                    WHEN confidence >= 0.7 THEN 'medium'
                    ELSE 'low'
                END as confidence_level,
                COUNT(*) as count
            FROM document_tags
            GROUP BY
                CASE
                    WHEN confidence >= 0.9 THEN 'high'
                    WHEN confidence >= 0.7 THEN 'medium'
                    ELSE 'low'
                END
        """, fetch_all=True)

        return {
            "top_tags": [
                {"tag": row['tag'], "count": row['count'], "avg_confidence": row['avg_confidence']}
                for row in tag_rows
            ],
            "category_distribution": {row['category']: row['count'] for row in category_rows},
            "confidence_distribution": {row['confidence_level']: row['count'] for row in confidence_rows}
        }

    def remove_tags_from_document(self, document_id: str, tags: Optional[List[str]] = None) -> int:
        """Remove tags from a document."""
        if tags:
            placeholders = ','.join(['?'] * len(tags))
            result = execute_query(
                f"DELETE FROM {self.table_name} WHERE document_id = ? AND tag IN ({placeholders})",
                [document_id] + tags,
                fetch_one=True
            )
        else:
            result = execute_query(
                f"DELETE FROM {self.table_name} WHERE document_id = ?",
                (document_id,),
                fetch_one=True
            )

        return result['changes'] if result else 0

    # Taxonomy operations
    def save_taxonomy_node(self, node: TaxonomyNode) -> None:
        """Save a taxonomy node."""
        execute_query("""
            INSERT OR REPLACE INTO taxonomy
            (tag, category, description, parent_tag, synonyms, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node.tag,
            node.category,
            node.description,
            node.parent_tag,
            json.dumps(node.synonyms),
            node.created_at.isoformat(),
            node.updated_at.isoformat()
        ))

    def get_taxonomy_node(self, tag: str) -> Optional[TaxonomyNode]:
        """Get a taxonomy node by tag."""
        row = execute_query(
            "SELECT * FROM taxonomy WHERE tag = ?",
            (tag,),
            fetch_one=True
        )

        if not row:
            return None

        return TaxonomyNode(
            tag=row['tag'],
            category=row['category'],
            description=row['description'],
            parent_tag=row.get('parent_tag'),
            synonyms=json.loads(row.get('synonyms', '[]')),
            created_at=row['created_at'],
            updated_at=row.get('updated_at')
        )

    def get_taxonomy_tree(self, root_category: Optional[str] = None) -> Dict[str, Any]:
        """Get taxonomy tree structure."""
        query = "SELECT * FROM taxonomy"
        params = []

        if root_category:
            query += " WHERE category = ?"
            params.append(root_category)

        query += " ORDER BY category, tag"

        rows = execute_query(query, params, fetch_all=True)

        # Build tree structure
        tree = {}
        for row in rows:
            category = row['category']
            if category not in tree:
                tree[category] = []

            tree[category].append({
                "tag": row['tag'],
                "description": row['description'],
                "parent_tag": row.get('parent_tag'),
                "synonyms": json.loads(row.get('synonyms', '[]'))
            })

        return tree

    def get_related_tags(self, tag: str, max_depth: int = 2) -> List[str]:
        """Get related tags through taxonomy relationships."""
        related = set()
        current_level = {tag}
        visited = set()

        for _ in range(max_depth):
            next_level = set()

            for current_tag in current_level:
                if current_tag in visited:
                    continue
                visited.add(current_tag)

                # Get synonyms
                node = self.get_taxonomy_node(current_tag)
                if node:
                    related.update(node.synonyms)

                    # Get parent/child relationships (simplified)
                    # In a full implementation, this would traverse the taxonomy tree

            current_level = next_level
            if not current_level:
                break

        return list(related)
