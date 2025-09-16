# ============================================================================
# ANALYTICS HANDLERS MODULE
# ============================================================================
"""
Analytics handlers for Doc Store service.

Provides comprehensive analytics endpoints for insights into document storage,
quality trends, usage patterns, and content relationships.
"""

from typing import Dict, Any, Optional
from .analytics import DocStoreAnalytics
from .shared_utils import (
    build_doc_store_context,
    create_doc_store_success_response,
    handle_doc_store_error,
    get_doc_store_connection
)
from .models import AnalyticsResponse, AnalyticsSummaryResponse
from .caching import docstore_cache


class AnalyticsHandlers:
    """Handles analytics operations."""

    @staticmethod
    async def handle_analytics(days_back: int = 30) -> Dict[str, Any]:
        """Generate comprehensive analytics for the document store."""
        try:
            # Check cache first
            cache_key = f"analytics:{days_back}"
            cached_result = await docstore_cache.get("analytics", {"days_back": days_back}, tags=["analytics"])

            if cached_result:
                context = build_doc_store_context("analytics_generation", days_back=days_back, cached=True)
                return create_doc_store_success_response("analytics retrieved from cache", cached_result, **context)

            # Get database path
            conn = get_doc_store_connection()
            db_path = conn.execute("PRAGMA database_list").fetchone()['file']
            conn.close()

            # Generate analytics
            analytics_engine = DocStoreAnalytics(db_path)
            result = analytics_engine.generate_analytics(days_back)

            # Convert to response format
            response_data = {
                "total_documents": result.total_documents,
                "total_analyses": result.total_analyses,
                "total_ensembles": result.total_ensembles,
                "total_style_examples": result.total_style_examples,
                "storage_stats": result.storage_stats,
                "quality_metrics": result.quality_metrics,
                "temporal_trends": result.temporal_trends,
                "content_insights": result.content_insights,
                "relationship_insights": result.relationship_insights
            }

            # Cache the result for 5 minutes
            await docstore_cache.set("analytics", {"days_back": days_back}, response_data, ttl=300, tags=["analytics"])

            context = build_doc_store_context("analytics_generation", days_back=days_back)
            return create_doc_store_success_response("analytics generated", response_data, **context)

        except Exception as e:
            context = build_doc_store_context("analytics_generation", days_back=days_back)
            return handle_doc_store_error("generate analytics", e, **context)

    @staticmethod
    async def handle_analytics_summary() -> Dict[str, Any]:
        """Generate a summary of key analytics insights and recommendations."""
        try:
            # Get database path
            conn = get_doc_store_connection()
            db_path = conn.execute("PRAGMA database_list").fetchone()['file']
            conn.close()

            # Generate full analytics
            analytics_engine = DocStoreAnalytics(db_path)
            result = analytics_engine.generate_analytics(days_back=30)

            # Generate summary and insights
            summary, insights, recommendations = AnalyticsHandlers._generate_summary_and_insights(result)

            response_data = {
                "summary": summary,
                "key_insights": insights,
                "recommendations": recommendations
            }

            context = build_doc_store_context("analytics_summary_generation")
            return create_doc_store_success_response("analytics summary generated", response_data, **context)

        except Exception as e:
            context = build_doc_store_context("analytics_summary_generation")
            return handle_doc_store_error("generate analytics summary", e, **context)

    @staticmethod
    def _generate_summary_and_insights(result) -> tuple[Dict[str, Any], list[str], list[str]]:
        """Generate summary, insights, and recommendations from analytics result."""
        summary = {
            "total_content": {
                "documents": result.total_documents,
                "analyses": result.total_analyses,
                "ensembles": result.total_ensembles,
                "style_examples": result.total_style_examples
            },
            "storage_overview": {
                "total_size_mb": round(result.storage_stats.get("total_content_size_bytes", 0) / 1024 / 1024, 2),
                "database_size_mb": round(result.storage_stats.get("database_file_size_bytes", 0) / 1024 / 1024, 2),
                "compression_ratio": round(result.storage_stats.get("compression_ratio_estimate", 1.0), 2)
            },
            "quality_overview": {
                "analysis_coverage": round(result.relationship_insights.get("relationship_coverage", {}).get("analysis_coverage_percentage", 0), 1),
                "stale_content_percentage": round(result.quality_metrics.get("content_freshness", {}).get("stale_percentage", 0), 1),
                "overall_quality_score": round(result.quality_metrics.get("overall_quality_score", 0), 2)
            }
        }

        insights = []
        recommendations = []

        # Generate insights
        if result.total_documents > 0:
            insights.append(f"Document store contains {result.total_documents} documents with {result.total_analyses} analyses performed")

        analysis_coverage = result.relationship_insights.get("relationship_coverage", {}).get("analysis_coverage_percentage", 0)
        if analysis_coverage > 80:
            insights.append("Excellent analysis coverage - most documents have been analyzed")
        elif analysis_coverage > 50:
            insights.append("Good analysis coverage - many documents have analysis results")
        else:
            insights.append("Limited analysis coverage - consider analyzing more documents")

        quality_score = result.quality_metrics.get("overall_quality_score", 0)
        if quality_score > 0.8:
            insights.append("High quality content - analysis scores are consistently strong")
        elif quality_score > 0.6:
            insights.append("Moderate quality content - room for quality improvements")
        else:
            insights.append("Quality concerns identified - review analysis results")

        stale_percentage = result.quality_metrics.get("content_freshness", {}).get("stale_percentage", 0)
        if stale_percentage > 50:
            insights.append("Significant amount of stale content - consider content refresh")
        elif stale_percentage > 20:
            insights.append("Some stale content detected - monitor content freshness")

        # Generate recommendations
        if analysis_coverage < 70:
            recommendations.append("Increase analysis coverage by running analysis on more documents")
        if quality_score < 0.7:
            recommendations.append("Improve content quality by addressing analysis findings")
        if stale_percentage > 30:
            recommendations.append("Refresh stale content or implement automated content validation")
        if result.storage_stats.get("compression_ratio_estimate", 1.0) < 2.0:
            recommendations.append("Consider optimizing storage efficiency or compression strategies")

        # Content type insights
        content_types = result.storage_stats.get("content_type_distribution", {})
        if content_types:
            top_type = max(content_types.items(), key=lambda x: x[1])
            insights.append(f"Primary content type: {top_type[0]} ({top_type[1]} documents)")

        # Growth insights
        doc_growth = result.temporal_trends.get("growth_rate_documents", 0)
        if abs(doc_growth) > 10:
            trend = "increasing" if doc_growth > 0 else "decreasing"
            insights.append(f"Document creation is {trend} at {abs(round(doc_growth, 1))}% per period")

        return summary, insights, recommendations
