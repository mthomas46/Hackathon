"""Analytics service for business logic operations.

Handles analytics processing and business rules.
"""
from typing import Dict, Any
from .repository import AnalyticsRepository, AnalyticsData


class AnalyticsService:
    """Service for analytics business logic."""

    def __init__(self):
        self.repository = AnalyticsRepository()

    def generate_analytics(self, days_back: int = 30) -> AnalyticsData:
        """Generate comprehensive analytics."""
        if days_back <= 0:
            raise ValueError("days_back must be positive")

        if days_back > 365:
            raise ValueError("days_back cannot exceed 365 days")

        return self.repository.generate_comprehensive_analytics(days_back)

    def get_basic_counts(self) -> Dict[str, Any]:
        """Get basic entity counts."""
        counts = self.repository.get_basic_counts()
        return {
            "total_documents": counts['documents'],
            "total_analyses": counts['analyses'],
            "total_ensembles": counts['ensembles'],
            "total_style_examples": counts['style_examples'],
            "total_versions": counts['versions'],
            "total_tags": counts['tags']
        }

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return self.repository.get_storage_stats()

    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get quality metrics."""
        metrics = self.repository.get_quality_metrics()

        # Add computed percentages
        total_docs = self.repository.get_basic_counts()['documents']
        if total_docs > 0:
            metrics['stale_percentage'] = (metrics['stale_documents'] / total_docs) * 100
            metrics['redundant_percentage'] = (metrics['redundant_documents'] / total_docs) * 100
            metrics['analyzed_percentage'] = ((total_docs - metrics['orphaned_analyses']) / total_docs) * 100

        return metrics

    def get_temporal_trends(self, days_back: int = 30) -> Dict[str, Any]:
        """Get temporal trends."""
        return self.repository.get_temporal_trends(days_back)

    def get_content_insights(self) -> Dict[str, Any]:
        """Get content insights."""
        return self.repository.get_content_insights()

    def get_relationship_insights(self) -> Dict[str, Any]:
        """Get relationship insights."""
        return self.repository.get_relationship_insights()

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary with key insights and recommendations."""
        analytics = self.repository.generate_comprehensive_analytics(days_back=7)

        summary = {
            "overview": {
                "total_documents": analytics.total_documents,
                "total_analyses": analytics.total_analyses,
                "analysis_coverage": f"{analytics.content_insights.get('analysis_coverage', 0):.1f}%"
            },
            "quality": {
                "stale_documents": analytics.quality_metrics.get('stale_documents', 0),
                "redundant_documents": analytics.quality_metrics.get('redundant_documents', 0),
                "quality_score": "Good" if analytics.quality_metrics.get('stale_percentage', 0) < 20 else "Needs Attention"
            },
            "storage": {
                "total_size_mb": analytics.storage_stats.get('total_size_bytes', 0) / (1024 * 1024),
                "avg_size_kb": analytics.storage_stats.get('avg_document_size', 0) / 1024
            },
            "insights": []
        }

        # Generate insights and recommendations
        insights = []

        # Quality insights
        if analytics.quality_metrics.get('stale_percentage', 0) > 30:
            insights.append({
                "type": "warning",
                "title": "High Stale Content",
                "description": f"{analytics.quality_metrics.get('stale_percentage', 0):.1f}% of documents are stale",
                "recommendation": "Consider archiving or updating stale documents"
            })

        # Analysis coverage insights
        if analytics.content_insights.get('analysis_coverage', 0) < 50:
            insights.append({
                "type": "info",
                "title": "Low Analysis Coverage",
                "description": f"Only {analytics.content_insights.get('analysis_coverage', 0):.1f}% of documents have analysis",
                "recommendation": "Run analysis on more documents to improve insights"
            })

        # Storage insights
        if analytics.storage_stats.get('avg_document_size', 0) > 100000:  # 100KB
            insights.append({
                "type": "info",
                "title": "Large Document Sizes",
                "description": f"Average document size is {analytics.storage_stats.get('avg_document_size', 0)/1024:.1f}KB",
                "recommendation": "Consider compressing or splitting large documents"
            })

        # Relationship insights
        if analytics.relationship_insights.get('total_relationships', 0) < analytics.total_documents * 0.1:
            insights.append({
                "type": "info",
                "title": "Low Connectivity",
                "description": f"Only {analytics.relationship_insights.get('total_relationships', 0)} relationships found",
                "recommendation": "Add more relationships to improve document connectivity"
            })

        summary["insights"] = insights

        return summary
