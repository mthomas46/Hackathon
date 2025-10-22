"""
Quality Dashboard Service

Provides real-time documentation quality metrics:
- Aggregated quality scores
- Quality trends over time
- Top issues and recommendations
- Service-level quality breakdowns
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from .staleness_detector import StalenessDetector
from .coverage_analyzer import CoverageAnalyzer
from .consistency_checker import ConsistencyChecker

logger = logging.getLogger(__name__)


class QualityDashboard:
    """
    Documentation quality dashboard.
    
    Features:
    - Real-time quality metrics
    - Quality score calculation
    - Issue prioritization
    - Trend analysis
    - Actionable recommendations
    """
    
    def __init__(self):
        """Initialize quality dashboard."""
        self.logger = logging.getLogger(__name__)
        self.staleness_detector = StalenessDetector()
        self.coverage_analyzer = CoverageAnalyzer()
        self.consistency_checker = ConsistencyChecker()
    
    async def get_quality_overview(
        self,
        service_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive quality overview.
        
        Args:
            service_name: Optional service filter
        
        Returns:
            Quality overview with all metrics
        """
        try:
            self.logger.info(f"📊 Generating quality overview (service={service_name})")
            
            # Gather all metrics in parallel (simplified sequential for now)
            staleness_summary = await self.staleness_detector.get_staleness_summary(
                service_name=service_name
            )
            
            coverage_analysis = await self.coverage_analyzer.analyze_coverage(
                service_name=service_name
            )
            
            consistency_results = await self.consistency_checker.check_consistency(
                service_name=service_name,
                limit=100
            )
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(
                staleness_summary,
                coverage_analysis,
                consistency_results
            )
            
            # Identify top issues
            top_issues = self._identify_top_issues(
                staleness_summary,
                coverage_analysis,
                consistency_results
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                quality_score,
                staleness_summary,
                coverage_analysis,
                consistency_results
            )
            
            return {
                "quality_score": quality_score,
                "staleness": {
                    "summary": staleness_summary["summary"],
                    "recommendations": staleness_summary["recommendations"]
                },
                "coverage": {
                    "overall": coverage_analysis["overall_coverage"],
                    "by_service": coverage_analysis["service_coverage"].get("top_services", [])[:5],
                    "recommendations": coverage_analysis["recommendations"]
                },
                "consistency": {
                    "total_issues": consistency_results["total_issues"],
                    "by_severity": consistency_results["by_severity"],
                    "recommendations": consistency_results["recommendations"]
                },
                "top_issues": top_issues,
                "recommendations": recommendations,
                "metadata": {
                    "service_name": service_name,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate quality overview: {e}", exc_info=True)
            raise
    
    def _calculate_quality_score(
        self,
        staleness_summary: Dict[str, Any],
        coverage_analysis: Dict[str, Any],
        consistency_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate overall documentation quality score.
        
        Score breakdown:
        - Freshness (40%): Based on staleness metrics
        - Coverage (30%): Based on coverage analysis
        - Consistency (30%): Based on consistency checks
        """
        # Freshness score (0-100, inverse of staleness)
        stale_pct = staleness_summary["summary"]["stale_percentage"]
        critical_count = staleness_summary["summary"]["critical_issues"]
        
        if critical_count > 10:
            freshness_score = 0
        elif critical_count > 0:
            freshness_score = max(0, 50 - (critical_count * 5))
        else:
            freshness_score = max(0, 100 - stale_pct)
        
        # Coverage score (0-100)
        coverage_score = coverage_analysis["overall_coverage"]["coverage_score"]
        
        # Consistency score (0-100, based on issues)
        total_checked = consistency_results["total_checked"]
        total_issues = consistency_results["total_issues"]
        
        if total_checked == 0:
            consistency_score = 100
        else:
            issue_rate = (total_issues / total_checked) * 100
            consistency_score = max(0, 100 - (issue_rate * 2))  # Penalize issues
        
        # Weighted overall score
        overall_score = (
            freshness_score * 0.4 +
            coverage_score * 0.3 +
            consistency_score * 0.3
        )
        
        return {
            "overall": round(overall_score, 1),
            "grade": self._score_to_grade(overall_score),
            "components": {
                "freshness": {
                    "score": round(freshness_score, 1),
                    "weight": 0.4
                },
                "coverage": {
                    "score": round(coverage_score, 1),
                    "weight": 0.3
                },
                "consistency": {
                    "score": round(consistency_score, 1),
                    "weight": 0.3
                }
            }
        }
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _identify_top_issues(
        self,
        staleness_summary: Dict[str, Any],
        coverage_analysis: Dict[str, Any],
        consistency_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify top issues across all categories."""
        issues = []
        
        # Staleness issues
        critical_stale = staleness_summary["summary"]["critical_issues"]
        if critical_stale > 0:
            issues.append({
                "category": "staleness",
                "severity": "CRITICAL",
                "title": f"{critical_stale} critically outdated documents",
                "description": "Documents not updated in 180+ days",
                "action": "Review and update immediately"
            })
        
        # Coverage issues
        coverage_level = coverage_analysis["overall_coverage"]["coverage_level"]
        if coverage_level in ["POOR", "CRITICAL"]:
            issues.append({
                "category": "coverage",
                "severity": "HIGH",
                "title": f"{coverage_level.lower().capitalize()} documentation coverage",
                "description": "Large portions of codebase lack documentation",
                "action": "Prioritize documenting core APIs"
            })
        
        # Consistency issues
        critical_consistency = consistency_results["by_severity"]["CRITICAL"]
        if critical_consistency > 0:
            issues.append({
                "category": "consistency",
                "severity": "CRITICAL",
                "title": f"{critical_consistency} critical consistency issues",
                "description": "Conflicting information in documentation",
                "action": "Resolve conflicts immediately"
            })
        
        # Sort by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        issues.sort(key=lambda x: severity_order[x["severity"]])
        
        return issues[:10]  # Top 10 issues
    
    def _generate_recommendations(
        self,
        quality_score: Dict[str, Any],
        staleness_summary: Dict[str, Any],
        coverage_analysis: Dict[str, Any],
        consistency_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations."""
        recommendations = []
        
        overall_score = quality_score["overall"]
        
        # Priority 1: Critical issues
        if overall_score < 60:
            recommendations.append({
                "priority": "CRITICAL",
                "title": "Documentation quality is below acceptable level",
                "actions": [
                    "Address critical staleness issues immediately",
                    "Review and fix consistency problems",
                    "Establish documentation standards"
                ]
            })
        
        # Priority 2: Component-specific recommendations
        freshness_score = quality_score["components"]["freshness"]["score"]
        if freshness_score < 70:
            recommendations.append({
                "priority": "HIGH",
                "title": "Documentation freshness needs improvement",
                "actions": [
                    "Enable automated refresh for critical services",
                    "Review documents not updated in 90+ days",
                    "Set up staleness alerts"
                ]
            })
        
        coverage_score = quality_score["components"]["coverage"]["score"]
        if coverage_score < 70:
            recommendations.append({
                "priority": "HIGH",
                "title": "Documentation coverage is insufficient",
                "actions": [
                    "Document core APIs and frequently used modules",
                    "Add documentation to new features",
                    "Track coverage metrics regularly"
                ]
            })
        
        consistency_score = quality_score["components"]["consistency"]["score"]
        if consistency_score < 80:
            recommendations.append({
                "priority": "MEDIUM",
                "title": "Improve documentation consistency",
                "actions": [
                    "Standardize terminology across documents",
                    "Fix broken cross-references",
                    "Review similar documents for conflicts"
                ]
            })
        
        # Priority 3: Maintenance recommendations
        if overall_score >= 60:
            recommendations.append({
                "priority": "LOW",
                "title": "Maintain documentation quality",
                "actions": [
                    "Schedule regular documentation reviews",
                    "Monitor quality metrics weekly",
                    "Continue following documentation standards"
                ]
            })
        
        return recommendations
    
    async def get_quality_trend(
        self,
        service_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get quality trend over time.
        
        Args:
            service_name: Service to analyze
            days: Days to look back
        
        Returns:
            Quality trend data
        """
        try:
            self.logger.info(f"📈 Generating quality trend for {service_name} ({days} days)")
            
            # This is a placeholder - in production, you'd store historical data
            current_quality = await self.get_quality_overview(service_name=service_name)
            
            return {
                "service_name": service_name,
                "period_days": days,
                "current_quality": current_quality["quality_score"],
                "trend": "stable",  # Would calculate from historical data
                "note": "Historical tracking requires time-series data storage"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get quality trend: {e}", exc_info=True)
            raise
    
    async def compare_services(
        self,
        service_names: List[str]
    ) -> Dict[str, Any]:
        """
        Compare quality across multiple services.
        
        Args:
            service_names: Services to compare
        
        Returns:
            Comparative quality analysis
        """
        try:
            self.logger.info(f"⚖️ Comparing quality across {len(service_names)} services")
            
            comparisons = []
            for service in service_names:
                quality = await self.get_quality_overview(service_name=service)
                comparisons.append({
                    "service_name": service,
                    "quality_score": quality["quality_score"]["overall"],
                    "grade": quality["quality_score"]["grade"],
                    "top_issue": quality["top_issues"][0] if quality["top_issues"] else None
                })
            
            # Sort by quality score
            comparisons.sort(key=lambda x: x["quality_score"], reverse=True)
            
            return {
                "services_compared": len(service_names),
                "comparisons": comparisons,
                "best_service": comparisons[0] if comparisons else None,
                "needs_attention": [c for c in comparisons if c["quality_score"] < 70],
                "metadata": {
                    "compared_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to compare services: {e}", exc_info=True)
            raise

