"""
Summary Processor for consolidating analysis results.
Following DDD principles with clean, focused functionality.
"""

from typing import List, Dict, Any
from datetime import datetime


class SummaryProcessor:
    """Processor for consolidating and summarizing analysis results."""

    def process_summaries(self, summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple analysis summaries into a consolidated result."""
        consolidated = {
            "consolidated_findings": [],
            "consolidated_recommendations": [],
            "priority_level": "medium",
            "processing_timestamp": datetime.now().isoformat(),
            "summary_metrics": {},
            "confidence_score": 0.0
        }

        all_findings = []
        all_recommendations = []
        total_confidence = 0

        for summary in summaries:
            findings = summary.get("key_findings", [])
            recommendations = summary.get("priority_recommendations", [])

            all_findings.extend(findings)
            all_recommendations.extend(recommendations)

            # Aggregate confidence
            confidence = summary.get("confidence_score", 0.5)
            total_confidence += confidence

        # Remove duplicates while preserving order
        consolidated["consolidated_findings"] = self._remove_duplicates(all_findings)
        consolidated["consolidated_recommendations"] = self._remove_duplicates(all_recommendations)

        # Calculate overall confidence
        if summaries:
            consolidated["confidence_score"] = total_confidence / len(summaries)

        # Determine priority level
        high_priority_indicators = ["critical", "urgent", "immediate", "risk", "issue"]
        high_priority_count = sum(
            1 for rec in consolidated["consolidated_recommendations"]
            if any(indicator in rec.lower() for indicator in high_priority_indicators)
        )

        if high_priority_count > len(consolidated["consolidated_recommendations"]) * 0.5:
            consolidated["priority_level"] = "high"
        elif high_priority_count == 0:
            consolidated["priority_level"] = "low"

        return consolidated

    def identify_action_items(self, summary_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify actionable items from summary data."""
        action_items = []
        findings = summary_data.get("findings", [])
        recommendations = summary_data.get("recommendations", [])

        # Create action items from recommendations
        for rec in recommendations:
            action_item = {
                "description": rec,
                "priority": self._determine_action_priority(rec),
                "category": self._categorize_action(rec),
                "estimated_effort": self._estimate_effort(rec),
                "dependencies": []
            }
            action_items.append(action_item)

        return action_items

    def calculate_confidence_score(self, analysis_results: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score from multiple analysis results."""
        if not analysis_results:
            return 0.0

        total_confidence = 0
        weights = []

        for result in analysis_results:
            confidence = result.get("confidence", 0.5)
            data_quality = result.get("data_quality", "medium")

            # Weight by data quality
            if data_quality == "high":
                weight = 1.0
            elif data_quality == "medium":
                weight = 0.7
            else:
                weight = 0.4

            total_confidence += confidence * weight
            weights.append(weight)

        if weights:
            return total_confidence / sum(weights)
        return 0.0

    def _remove_duplicates(self, items: List[str]) -> List[str]:
        """Remove duplicate items while preserving order."""
        seen = set()
        result = []

        for item in items:
            # Create a normalized version for comparison
            normalized = item.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                result.append(item)

        return result

    def _determine_action_priority(self, recommendation: str) -> str:
        """Determine priority level for an action item."""
        rec_lower = recommendation.lower()

        # High priority indicators
        if any(word in rec_lower for word in ["critical", "urgent", "immediate", "fix", "resolve"]):
            return "high"

        # Medium priority indicators
        if any(word in rec_lower for word in ["review", "consider", "monitor", "improve"]):
            return "medium"

        # Low priority indicators
        return "low"

    def _categorize_action(self, recommendation: str) -> str:
        """Categorize action item by type."""
        rec_lower = recommendation.lower()

        categories = {
            "timeline": ["timeline", "schedule", "duration", "deadline"],
            "team": ["team", "resource", "member", "capacity"],
            "documentation": ["document", "documentation", "docs", "manual"],
            "budget": ["budget", "cost", "finance", "spending"],
            "risk": ["risk", "issue", "problem", "mitigation"],
            "quality": ["quality", "testing", "review", "standards"],
            "technical": ["technical", "architecture", "design", "implementation"]
        }

        for category, keywords in categories.items():
            if any(keyword in rec_lower for keyword in keywords):
                return category

        return "general"

    def _estimate_effort(self, recommendation: str) -> str:
        """Estimate effort level for an action item."""
        rec_lower = recommendation.lower()

        # High effort indicators
        if any(word in rec_lower for word in ["redesign", "restructure", "rebuild", "comprehensive"]):
            return "high"

        # Medium effort indicators
        if any(word in rec_lower for word in ["review", "update", "modify", "implement"]):
            return "medium"

        # Low effort indicators
        if any(word in rec_lower for word in ["monitor", "check", "verify", "document"]):
            return "low"

        return "medium"
