# ============================================================================
# ANALYTICS MODULE
# ============================================================================
"""
Advanced analytics and insights for the Doc Store service.

Provides comprehensive analytics on document storage patterns, quality trends,
usage statistics, and insights into content relationships and evolution.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass


@dataclass
class AnalyticsResult:
    """Container for analytics results."""
    total_documents: int
    total_analyses: int
    total_ensembles: int
    total_style_examples: int
    storage_stats: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    temporal_trends: Dict[str, Any]
    content_insights: Dict[str, Any]
    relationship_insights: Dict[str, Any]


class DocStoreAnalytics:
    """Analytics engine for document store insights."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def generate_analytics(self, days_back: int = 30) -> AnalyticsResult:
        """Generate comprehensive analytics for the document store."""
        with self.get_connection() as conn:
            # Basic counts
            total_docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            total_analyses = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
            total_ensembles = conn.execute("SELECT COUNT(*) FROM ensembles").fetchone()[0]
            total_style_examples = conn.execute("SELECT COUNT(*) FROM style_examples").fetchone()[0]

            # Storage statistics
            storage_stats = self._calculate_storage_stats(conn)

            # Quality metrics
            quality_metrics = self._calculate_quality_metrics(conn, days_back)

            # Temporal trends
            temporal_trends = self._calculate_temporal_trends(conn, days_back)

            # Content insights
            content_insights = self._analyze_content_insights(conn)

            # Relationship insights
            relationship_insights = self._analyze_relationships(conn)

            return AnalyticsResult(
                total_documents=total_docs,
                total_analyses=total_analyses,
                total_ensembles=total_ensembles,
                total_style_examples=total_style_examples,
                storage_stats=storage_stats,
                quality_metrics=quality_metrics,
                temporal_trends=temporal_trends,
                content_insights=content_insights,
                relationship_insights=relationship_insights
            )

    def _calculate_storage_stats(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Calculate storage statistics."""
        # Document size distribution
        doc_sizes = conn.execute("""
            SELECT LENGTH(content) as size,
                   metadata,
                   created_at
            FROM documents
            ORDER BY created_at DESC
            LIMIT 1000
        """).fetchall()

        sizes = [row['size'] for row in doc_sizes]
        total_size = sum(sizes) if sizes else 0
        avg_size = total_size / len(sizes) if sizes else 0

        # Content type distribution
        content_types = defaultdict(int)
        for row in doc_sizes:
            metadata = json.loads(row['metadata'] or '{}')
            content_type = metadata.get('type', metadata.get('source_type', 'unknown'))
            content_types[content_type] += 1

        # Database file size (approximate)
        try:
            import os
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        except:
            db_size = 0

        return {
            "total_content_size_bytes": total_size,
            "average_document_size_bytes": avg_size,
            "largest_document_bytes": max(sizes) if sizes else 0,
            "smallest_document_bytes": min(sizes) if sizes else 0,
            "database_file_size_bytes": db_size,
            "compression_ratio_estimate": total_size / db_size if db_size > 0 else 1.0,
            "content_type_distribution": dict(content_types),
            "documents_analyzed": len(doc_sizes)
        }

    def _calculate_quality_metrics(self, conn: sqlite3.Connection, days_back: int) -> Dict[str, Any]:
        """Calculate quality metrics and trends."""
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        # Quality scores over time
        quality_trend = conn.execute("""
            SELECT DATE(created_at) as date,
                   AVG(score) as avg_score,
                   COUNT(*) as analysis_count
            FROM analyses
            WHERE created_at > ?
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (cutoff_date,)).fetchall()

        # Analysis distribution by type
        analysis_types = conn.execute("""
            SELECT analyzer, COUNT(*) as count
            FROM analyses
            GROUP BY analyzer
            ORDER BY count DESC
        """).fetchall()

        # Model performance comparison
        model_performance = conn.execute("""
            SELECT model, AVG(score) as avg_score, COUNT(*) as analysis_count
            FROM analyses
            WHERE score IS NOT NULL
            GROUP BY model
            ORDER BY avg_score DESC
        """).fetchall()

        # Content freshness analysis
        fresh_content = conn.execute("""
            SELECT COUNT(*) as fresh_count
            FROM documents
            WHERE created_at > ?
        """, (cutoff_date,)).fetchone()['fresh_count']

        total_docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        stale_percentage = ((total_docs - fresh_content) / total_docs * 100) if total_docs > 0 else 0

        return {
            "quality_score_trend": [{"date": row['date'], "avg_score": row['avg_score'], "count": row['analysis_count']} for row in quality_trend],
            "analysis_type_distribution": [{"analyzer": row['analyzer'], "count": row['count']} for row in analysis_types],
            "model_performance_ranking": [{"model": row['model'], "avg_score": row['avg_score'], "analysis_count": row['analysis_count']} for row in model_performance],
            "content_freshness": {
                "fresh_documents": fresh_content,
                "stale_percentage": stale_percentage,
                "analysis_period_days": days_back
            },
            "overall_quality_score": sum(row['avg_score'] for row in model_performance) / len(model_performance) if model_performance else 0
        }

    def _calculate_temporal_trends(self, conn: sqlite3.Connection, days_back: int) -> Dict[str, Any]:
        """Calculate temporal trends in document creation and analysis."""
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        # Document creation trends
        doc_trends = conn.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM documents
            WHERE created_at > ?
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (cutoff_date,)).fetchall()

        # Analysis trends
        analysis_trends = conn.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM analyses
            WHERE created_at > ?
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (cutoff_date,)).fetchall()

        # Ensemble trends
        ensemble_trends = conn.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM ensembles
            WHERE created_at > ?
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (cutoff_date,)).fetchall()

        return {
            "document_creation_trend": [{"date": row['date'], "count": row['count']} for row in doc_trends],
            "analysis_trend": [{"date": row['date'], "count": row['count']} for row in analysis_trends],
            "ensemble_trend": [{"date": row['date'], "count": row['count']} for row in ensemble_trends],
            "period_days": days_back,
            "growth_rate_documents": self._calculate_growth_rate([row['count'] for row in doc_trends]),
            "growth_rate_analyses": self._calculate_growth_rate([row['count'] for row in analysis_trends])
        }

    def _analyze_content_insights(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Analyze content patterns and insights."""
        # Most analyzed documents
        most_analyzed = conn.execute("""
            SELECT d.id, d.metadata, COUNT(a.id) as analysis_count,
                   AVG(a.score) as avg_score, MAX(a.created_at) as last_analysis
            FROM documents d
            LEFT JOIN analyses a ON d.id = a.document_id
            GROUP BY d.id
            ORDER BY analysis_count DESC
            LIMIT 10
        """).fetchall()

        # Content duplication analysis
        duplicates = conn.execute("""
            SELECT content_hash, COUNT(*) as count
            FROM documents
            GROUP BY content_hash
            HAVING count > 1
            ORDER BY count DESC
            LIMIT 10
        """).fetchall()

        # Source type distribution
        source_types = conn.execute("""
            SELECT json_extract(metadata, '$.source_type') as source_type, COUNT(*) as count
            FROM documents
            WHERE json_extract(metadata, '$.source_type') IS NOT NULL
            GROUP BY source_type
            ORDER BY count DESC
        """).fetchall()

        # Language distribution (for code documents)
        languages = conn.execute("""
            SELECT json_extract(metadata, '$.language') as language, COUNT(*) as count
            FROM documents
            WHERE json_extract(metadata, '$.language') IS NOT NULL
            GROUP BY language
            ORDER BY count DESC
        """).fetchall()

        return {
            "most_analyzed_documents": [
                {
                    "id": row['id'],
                    "analysis_count": row['analysis_count'],
                    "avg_score": row['avg_score'],
                    "last_analysis": row['last_analysis'],
                    "metadata": json.loads(row['metadata'] or '{}')
                } for row in most_analyzed
            ],
            "content_duplication": [
                {"content_hash": row['content_hash'], "duplicate_count": row['count']}
                for row in duplicates
            ],
            "source_type_distribution": [
                {"source_type": row['source_type'], "count": row['count']}
                for row in source_types
            ],
            "programming_language_distribution": [
                {"language": row['language'], "count": row['count']}
                for row in languages
            ],
            "duplication_rate": sum(row['count'] for row in duplicates) / len(duplicates) if duplicates else 1.0
        }

    def _analyze_relationships(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Analyze document relationships and connections."""
        # Documents with analyses
        docs_with_analyses = conn.execute("""
            SELECT COUNT(DISTINCT document_id) as docs_with_analyses
            FROM analyses
        """).fetchone()['docs_with_analyses']

        total_docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

        # Analysis coverage
        analysis_coverage = (docs_with_analyses / total_docs * 100) if total_docs > 0 else 0

        # Ensemble coverage
        docs_with_ensembles = conn.execute("""
            SELECT COUNT(DISTINCT document_id) as docs_with_ensembles
            FROM ensembles
        """).fetchone()['docs_with_ensembles']

        ensemble_coverage = (docs_with_ensembles / total_docs * 100) if total_docs > 0 else 0

        # Cross-references (documents referencing other documents)
        cross_refs = conn.execute("""
            SELECT COUNT(*) as cross_ref_count
            FROM documents
            WHERE content LIKE '%doc:%' OR content LIKE '%analysis:%'
        """).fetchone()['cross_ref_count']

        return {
            "relationship_coverage": {
                "documents_with_analyses": docs_with_analyses,
                "analysis_coverage_percentage": analysis_coverage,
                "documents_with_ensembles": docs_with_ensembles,
                "ensemble_coverage_percentage": ensemble_coverage,
                "documents_with_cross_references": cross_refs,
                "total_documents": total_docs
            },
            "analysis_depth": self._calculate_analysis_depth(conn),
            "collaboration_patterns": self._analyze_collaboration_patterns(conn)
        }

    def _calculate_growth_rate(self, values: List[int]) -> float:
        """Calculate compound growth rate from a series of values."""
        if len(values) < 2:
            return 0.0

        initial = values[0]
        final = values[-1]

        if initial == 0:
            return float('inf') if final > 0 else 0.0

        periods = len(values) - 1
        return ((final / initial) ** (1 / periods) - 1) * 100

    def _calculate_analysis_depth(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Calculate how deeply documents are analyzed."""
        analysis_counts = conn.execute("""
            SELECT document_id, COUNT(*) as analysis_count
            FROM analyses
            GROUP BY document_id
        """).fetchall()

        if not analysis_counts:
            return {"average_analyses_per_document": 0, "max_analyses": 0, "analysis_depth_distribution": {}}

        counts = [row['analysis_count'] for row in analysis_counts]
        avg_depth = sum(counts) / len(counts)
        max_depth = max(counts)

        # Distribution
        distribution = defaultdict(int)
        for count in counts:
            if count <= 5:
                distribution[f"{count}"] += 1
            else:
                distribution["6+"] += 1

        return {
            "average_analyses_per_document": avg_depth,
            "max_analyses_on_single_document": max_depth,
            "analysis_depth_distribution": dict(distribution)
        }

    def _analyze_collaboration_patterns(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Analyze collaboration patterns in document analysis."""
        # Multiple analyzers on same document
        multi_analyzer_docs = conn.execute("""
            SELECT document_id, COUNT(DISTINCT analyzer) as analyzer_count
            FROM analyses
            GROUP BY document_id
            HAVING analyzer_count > 1
        """).fetchall()

        # Ensemble analysis patterns
        ensemble_patterns = conn.execute("""
            SELECT COUNT(*) as ensemble_count,
                   AVG(json_array_length(json_extract(config, '$.analyzers'))) as avg_analyzers_per_ensemble
            FROM ensembles
        """).fetchall()

        return {
            "documents_with_multiple_analyzers": len(multi_analyzer_docs),
            "ensemble_analysis_patterns": {
                "total_ensembles": ensemble_patterns[0]['ensemble_count'] if ensemble_patterns else 0,
                "average_analyzers_per_ensemble": ensemble_patterns[0]['avg_analyzers_per_ensemble'] if ensemble_patterns else 0
            }
        }
