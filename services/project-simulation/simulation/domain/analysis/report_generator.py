"""
Report Generator for creating analysis reports.
Following DDD principles with clean, focused functionality.
"""

from typing import List, Dict, Any
from datetime import datetime

from simulation.domain.analysis.analysis_result import AnalysisResult, AnalysisType


class ReportGenerator:
    """Generator for various types of analysis reports."""

    def generate_summary_report(self, simulation_id: str, analysis_results: List[AnalysisResult]) -> Dict[str, Any]:
        """Generate a summary report from multiple analysis results."""
        report = {
            "simulation_id": simulation_id,
            "report_type": "analysis_summary",
            "generated_at": datetime.now().isoformat(),
            "analysis_count": len(analysis_results),
            "analysis_summary": {},
            "recommendations": [],
            "key_metrics": {},
            "overall_confidence": 0.0
        }

        total_confidence = 0
        all_recommendations = []

        for result in analysis_results:
            # Analysis type summary
            analysis_type_str = result.analysis_type.value
            report["analysis_summary"][analysis_type_str] = {
                "findings_count": len(result.findings),
                "recommendations_count": len(result.recommendations),
                "confidence_score": result.confidence_score,
                "processing_time": result.processing_time_seconds
            }

            # Collect recommendations
            all_recommendations.extend(result.recommendations)

            # Aggregate metrics
            for key, value in result.metrics.items():
                if key not in report["key_metrics"]:
                    report["key_metrics"][key] = value
                elif isinstance(value, (int, float)):
                    # For numeric values, keep the latest
                    report["key_metrics"][key] = value

            total_confidence += result.confidence_score

        # Process recommendations (remove duplicates and prioritize)
        unique_recommendations = list(set(all_recommendations))
        report["recommendations"] = self._prioritize_recommendations(unique_recommendations)

        # Calculate overall confidence
        if analysis_results:
            report["overall_confidence"] = total_confidence / len(analysis_results)

        return report

    def generate_detailed_report(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """Generate a detailed report for a single analysis result."""
        report = {
            "simulation_id": analysis_result.simulation_id,
            "analysis_type": analysis_result.analysis_type.value,
            "generated_at": datetime.now().isoformat(),
            "findings": analysis_result.findings,
            "recommendations": analysis_result.recommendations,
            "metrics": analysis_result.metrics,
            "insights": analysis_result.insights,
            "confidence_score": analysis_result.confidence_score,
            "processing_time_seconds": analysis_result.processing_time_seconds,
            "analyzed_at": analysis_result.analyzed_at.isoformat()
        }

        # Add analysis-specific insights
        if analysis_result.analysis_type == AnalysisType.DOCUMENT_ANALYSIS:
            report["insights"].extend(self._generate_document_insights(analysis_result))
        elif analysis_result.analysis_type == AnalysisType.TIMELINE_ANALYSIS:
            report["insights"].extend(self._generate_timeline_insights(analysis_result))
        elif analysis_result.analysis_type == AnalysisType.TEAM_DYNAMICS:
            report["insights"].extend(self._generate_team_insights(analysis_result))

        return report

    def generate_executive_summary(self, simulation_id: str, key_metrics: Dict[str, Any],
                                critical_findings: List[str]) -> Dict[str, Any]:
        """Generate an executive summary for stakeholders."""
        summary = {
            "simulation_id": simulation_id,
            "report_type": "executive_summary",
            "generated_at": datetime.now().isoformat(),
            "key_metrics": key_metrics,
            "critical_findings": critical_findings,
            "recommendations": [],
            "confidence_level": "medium",
            "next_steps": []
        }

        # Generate recommendations based on critical findings
        for finding in critical_findings:
            if "timeline" in finding.lower():
                summary["recommendations"].append("Review project timeline and milestones")
                summary["next_steps"].append("Schedule timeline review meeting within 1 week")
            elif "resource" in finding.lower():
                summary["recommendations"].append("Assess resource allocation and capacity")
                summary["next_steps"].append("Conduct resource capacity analysis")
            elif "documentation" in finding.lower():
                summary["recommendations"].append("Improve documentation completeness")
                summary["next_steps"].append("Prioritize documentation gap closure")

        # Determine confidence level
        if len(critical_findings) == 0:
            summary["confidence_level"] = "high"
        elif len(critical_findings) > 3:
            summary["confidence_level"] = "low"

        return summary

    def _prioritize_recommendations(self, recommendations: List[str]) -> List[Dict[str, Any]]:
        """Prioritize recommendations based on urgency and impact."""
        prioritized = []

        for rec in recommendations:
            priority = self._calculate_priority(rec)
            prioritized.append({
                "recommendation": rec,
                "priority": priority,
                "category": self._categorize_recommendation(rec)
            })

        # Sort by priority (high first)
        return sorted(prioritized, key=lambda x: x["priority"], reverse=True)

    def _calculate_priority(self, recommendation: str) -> str:
        """Calculate priority level for a recommendation."""
        rec_lower = recommendation.lower()

        if any(word in rec_lower for word in ["critical", "urgent", "immediate", "risk"]):
            return "high"
        elif any(word in rec_lower for word in ["consider", "review", "monitor"]):
            return "medium"
        else:
            return "low"

    def _categorize_recommendation(self, recommendation: str) -> str:
        """Categorize recommendation by type."""
        rec_lower = recommendation.lower()

        if any(word in rec_lower for word in ["timeline", "schedule", "duration"]):
            return "timeline"
        elif any(word in rec_lower for word in ["team", "resource", "member"]):
            return "team"
        elif any(word in rec_lower for word in ["document", "documentation"]):
            return "documentation"
        elif any(word in rec_lower for word in ["budget", "cost", "finance"]):
            return "budget"
        elif any(word in rec_lower for word in ["risk", "issue", "problem"]):
            return "risk"
        else:
            return "general"

    def _generate_document_insights(self, analysis_result: AnalysisResult) -> List[str]:
        """Generate insights specific to document analysis."""
        insights = []

        doc_count = analysis_result.metrics.get("document_count", 0)
        if doc_count == 0:
            insights.append("No documentation exists - consider establishing documentation standards")
        elif doc_count < 5:
            insights.append("Limited documentation may impact knowledge transfer and onboarding")
        else:
            insights.append("Good documentation foundation established")

        doc_types = analysis_result.metrics.get("document_types", {})
        if len(doc_types) < 3:
            insights.append("Documentation variety could be improved with additional types")

        return insights

    def _generate_timeline_insights(self, analysis_result: AnalysisResult) -> List[str]:
        """Generate insights specific to timeline analysis."""
        insights = []

        total_duration = analysis_result.metrics.get("total_duration", 0)
        if total_duration < 6:
            insights.append("Compressed timeline may lead to rushed delivery and quality issues")
        elif total_duration > 20:
            insights.append("Extended timeline may impact time-to-market and increase costs")

        phase_count = analysis_result.metrics.get("phase_count", 0)
        if phase_count < 3:
            insights.append("Consider breaking project into more phases for better control")
        elif phase_count > 6:
            insights.append("Many phases may complicate project management")

        return insights

    def _generate_team_insights(self, analysis_result: AnalysisResult) -> List[str]:
        """Generate insights specific to team dynamics analysis."""
        insights = []

        team_size = analysis_result.metrics.get("team_size", 0)
        if team_size < 3:
            insights.append("Small team size may limit capacity and resilience")
        elif team_size > 8:
            insights.append("Large team may require additional coordination overhead")

        total_experience = analysis_result.metrics.get("total_experience_years", 0)
        if team_size > 0:
            avg_experience = total_experience / team_size
            if avg_experience < 2:
                insights.append("Team experience level may benefit from mentorship programs")
            elif avg_experience > 5:
                insights.append("Experienced team provides strong foundation for complex work")

        unique_skills = analysis_result.metrics.get("unique_skills_count", 0)
        if unique_skills < 5:
            insights.append("Expanding skill diversity could improve team capabilities")

        return insights
