"""Analytics repository for data analysis operations.

Handles analytics queries and aggregations across the document store.
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from ...db.queries import execute_query


@dataclass
class AnalyticsData:
    """Container for analytics data."""
    total_documents: int = 0
    total_analyses: int = 0
    total_ensembles: int = 0
    total_style_examples: int = 0
    storage_stats: Dict[str, Any] = None
    quality_metrics: Dict[str, Any] = None
    temporal_trends: Dict[str, Any] = None
    content_insights: Dict[str, Any] = None
    relationship_insights: Dict[str, Any] = None

    def __post_init__(self):
        if self.storage_stats is None:
            self.storage_stats = {}
        if self.quality_metrics is None:
            self.quality_metrics = {}
        if self.temporal_trends is None:
            self.temporal_trends = {}
        if self.content_insights is None:
            self.content_insights = {}
        if self.relationship_insights is None:
            self.relationship_insights = {}


class AnalyticsRepository:
    """Repository for analytics data operations."""

    def get_basic_counts(self) -> Dict[str, int]:
        """Get basic entity counts."""
        counts = {}

        # Document counts
        result = execute_query("SELECT COUNT(*) as count FROM documents", fetch_one=True)
        counts['documents'] = result['count'] if result else 0

        # Analysis counts
        result = execute_query("SELECT COUNT(*) as count FROM analyses", fetch_one=True)
        counts['analyses'] = result['count'] if result else 0

        # Ensemble counts
        result = execute_query("SELECT COUNT(*) as count FROM ensembles", fetch_one=True)
        counts['ensembles'] = result['count'] if result else 0

        # Style examples counts
        result = execute_query("SELECT COUNT(*) as count FROM style_examples", fetch_one=True)
        counts['style_examples'] = result['count'] if result else 0

        # Version counts
        result = execute_query("SELECT COUNT(*) as count FROM document_versions", fetch_one=True)
        counts['versions'] = result['count'] if result else 0

        # Tag counts
        result = execute_query("SELECT COUNT(*) as count FROM document_tags", fetch_one=True)
        counts['tags'] = result['count'] if result else 0

        return counts

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        stats = {
            'total_size_bytes': 0,
            'avg_document_size': 0,
            'largest_document': 0,
            'smallest_document': 0,
            'size_distribution': {}
        }

        # Calculate document sizes
        rows = execute_query("""
            SELECT LENGTH(content) as size
            FROM documents
            WHERE content IS NOT NULL
        """, fetch_all=True)

        if rows:
            sizes = [row['size'] for row in rows]
            stats['total_size_bytes'] = sum(sizes)
            stats['avg_document_size'] = sum(sizes) // len(sizes) if sizes else 0
            stats['largest_document'] = max(sizes) if sizes else 0
            stats['smallest_document'] = min(sizes) if sizes else 0

            # Size distribution
            bins = [(0, 1000), (1000, 10000), (10000, 100000), (100000, float('inf'))]
            for min_size, max_size in bins:
                if max_size == float('inf'):
                    count = sum(1 for size in sizes if size >= min_size)
                    label = f"{min_size/1000:.0f}KB+"
                else:
                    count = sum(1 for size in sizes if min_size <= size < max_size)
                    label = f"{min_size/1000:.0f}-{max_size/1000:.0f}KB"
                stats['size_distribution'][label] = count

        return stats

    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get document quality metrics."""
        metrics = {
            'stale_documents': 0,
            'redundant_documents': 0,
            'orphaned_analyses': 0,
            'quality_score_distribution': {},
            'content_type_distribution': {}
        }

        # Quality analysis using existing logic
        import sys
        sys.path.append('services/doc_store')
        try:
            from logic import compute_quality_flags
            rows = execute_query("""
                SELECT id, content_hash, metadata, created_at
                FROM documents
                ORDER BY created_at DESC
                LIMIT 1000
            """, fetch_all=True)

            quality_data = compute_quality_flags(rows)

            # Aggregate quality metrics
            for doc in quality_data:
                flags = doc.get('flags', [])
                if 'stale' in flags:
                    metrics['stale_documents'] += 1
                if 'redundant' in flags:
                    metrics['redundant_documents'] += 1

        except Exception:
            # Fallback if quality computation fails
            pass

        # Content type distribution
        rows = execute_query("""
            SELECT json_extract(metadata, '$.type') as content_type, COUNT(*) as count
            FROM documents
            WHERE metadata IS NOT NULL
            GROUP BY json_extract(metadata, '$.type')
        """, fetch_all=True)

        for row in rows:
            content_type = row['content_type'] or 'unknown'
            metrics['content_type_distribution'][content_type] = row['count']

        return metrics

    def get_temporal_trends(self, days_back: int = 30) -> Dict[str, Any]:
        """Get temporal trends and patterns."""
        trends = {
            'daily_document_creation': {},
            'daily_analysis_creation': {},
            'weekly_patterns': {},
            'growth_rate': 0.0
        }

        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()

        # Daily document creation
        rows = execute_query("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM documents
            WHERE created_at >= ?
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (cutoff_date,), fetch_all=True)

        for row in rows:
            trends['daily_document_creation'][row['date']] = row['count']

        # Daily analysis creation
        rows = execute_query("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM analyses
            WHERE created_at >= ?
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (cutoff_date,), fetch_all=True)

        for row in rows:
            trends['daily_analysis_creation'][row['date']] = row['count']

        # Calculate growth rate (simple linear trend)
        doc_counts = list(trends['daily_document_creation'].values())
        if len(doc_counts) > 1:
            trends['growth_rate'] = (doc_counts[-1] - doc_counts[0]) / len(doc_counts)

        return trends

    def get_content_insights(self) -> Dict[str, Any]:
        """Get content analysis insights."""
        insights = {
            'top_languages': {},
            'analysis_coverage': 0.0,
            'popular_tags': {},
            'content_patterns': {}
        }

        # Language distribution
        rows = execute_query("""
            SELECT json_extract(metadata, '$.language') as language, COUNT(*) as count
            FROM documents
            WHERE metadata IS NOT NULL AND json_extract(metadata, '$.language') IS NOT NULL
            GROUP BY json_extract(metadata, '$.language')
            ORDER BY count DESC
            LIMIT 10
        """, fetch_all=True)

        for row in rows:
            insights['top_languages'][row['language']] = row['count']

        # Analysis coverage
        total_docs = execute_query("SELECT COUNT(*) as count FROM documents", fetch_one=True)
        analyzed_docs = execute_query("""
            SELECT COUNT(DISTINCT document_id) as count
            FROM analyses
        """, fetch_one=True)

        if total_docs and total_docs['count'] > 0:
            insights['analysis_coverage'] = (analyzed_docs['count'] / total_docs['count']) * 100

        # Popular tags
        rows = execute_query("""
            SELECT tag, COUNT(*) as count
            FROM document_tags
            GROUP BY tag
            ORDER BY count DESC
            LIMIT 20
        """, fetch_all=True)

        for row in rows:
            insights['popular_tags'][row['tag']] = row['count']

        return insights

    def get_relationship_insights(self) -> Dict[str, Any]:
        """Get relationship and connectivity insights."""
        insights = {
            'total_relationships': 0,
            'relationship_types': {},
            'most_connected_documents': [],
            'connectivity_stats': {}
        }

        # Relationship counts
        result = execute_query("SELECT COUNT(*) as count FROM document_relationships", fetch_one=True)
        insights['total_relationships'] = result['count'] if result else 0

        # Relationship type distribution
        rows = execute_query("""
            SELECT relationship_type, COUNT(*) as count
            FROM document_relationships
            GROUP BY relationship_type
            ORDER BY count DESC
        """, fetch_all=True)

        for row in rows:
            insights['relationship_types'][row['relationship_type']] = row['count']

        # Most connected documents
        rows = execute_query("""
            SELECT document_id, COUNT(*) as connections
            FROM (
                SELECT source_document_id as document_id FROM document_relationships
                UNION ALL
                SELECT target_document_id as document_id FROM document_relationships
            )
            GROUP BY document_id
            ORDER BY connections DESC
            LIMIT 10
        """, fetch_all=True)

        insights['most_connected_documents'] = [
            {'document_id': row['document_id'], 'connections': row['connections']}
            for row in rows
        ]

        return insights

    def generate_comprehensive_analytics(self, days_back: int = 30) -> AnalyticsData:
        """Generate comprehensive analytics data."""
        return AnalyticsData(
            total_documents=self.get_basic_counts()['documents'],
            total_analyses=self.get_basic_counts()['analyses'],
            total_ensembles=self.get_basic_counts()['ensembles'],
            total_style_examples=self.get_basic_counts()['style_examples'],
            storage_stats=self.get_storage_stats(),
            quality_metrics=self.get_quality_metrics(),
            temporal_trends=self.get_temporal_trends(days_back),
            content_insights=self.get_content_insights(),
            relationship_insights=self.get_relationship_insights()
        )
