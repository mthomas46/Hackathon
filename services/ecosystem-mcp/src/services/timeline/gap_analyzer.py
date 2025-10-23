"""
Gap Analyzer Service

Detects documentation gaps with root cause analysis:
- Identify missing documentation
- Detect topic gaps
- Analyze root causes
- Use timeline data for temporal context
- Confidence-aware analysis
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from uuid import UUID
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.db_models import DocumentModel
from ...storage.repositories import DocumentRepository
from ...storage.repositories.timeline_repository import TimelineRepository, TimePeriodRepository
from ...storage import get_database
from ..maintenance import CoverageAnalyzer
from .confidence_calculator import TemporalConfidenceCalculator

logger = logging.getLogger(__name__)


class DocumentationGap:
    """Represents a documentation gap."""
    
    def __init__(
        self,
        gap_type: str,
        severity: str,
        description: str,
        affected_area: str,
        root_cause: str,
        recommendation: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.gap_type = gap_type
        self.severity = severity
        self.description = description
        self.affected_area = affected_area
        self.root_cause = root_cause
        self.recommendation = recommendation
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gap_type": self.gap_type,
            "severity": self.severity,
            "description": self.description,
            "affected_area": self.affected_area,
            "root_cause": self.root_cause,
            "recommendation": self.recommendation,
            "metadata": self.metadata
        }


class GapAnalyzer:
    """
    Analyze documentation gaps.
    
    Features:
    - Missing documentation detection
    - Topic gap identification
    - Root cause analysis
    - Timeline-aware gap detection
    - Confidence-based recommendations
    """
    
    def __init__(self, db_session: AsyncSession = None):
        """Initialize gap analyzer."""
        self.logger = logging.getLogger(__name__)
        self.db_session = db_session
        self.coverage_analyzer = CoverageAnalyzer()
        self.confidence_calculator = TemporalConfidenceCalculator(db_session) if db_session else None
    
    async def analyze_gaps(
        self,
        service_name: Optional[str] = None,
        timeline_id: Optional[UUID] = None,
        include_root_cause: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze documentation gaps.
        
        Args:
            service_name: Optional service filter
            timeline_id: Optional timeline filter
            include_root_cause: Whether to perform root cause analysis
        
        Returns:
            Gap analysis results with recommendations
        """
        try:
            self.logger.info(f"🔍 Analyzing documentation gaps (service={service_name})")
            
            gaps = []
            
            # Analyze coverage gaps
            coverage_gaps = await self._analyze_coverage_gaps(service_name)
            gaps.extend(coverage_gaps)
            
            # Analyze topic gaps
            topic_gaps = await self._analyze_topic_gaps(service_name)
            gaps.extend(topic_gaps)
            
            # Analyze temporal gaps (if timeline provided)
            if timeline_id:
                temporal_gaps = await self._analyze_temporal_gaps(timeline_id)
                gaps.extend(temporal_gaps)
            
            # Perform root cause analysis
            if include_root_cause:
                gaps = await self._add_root_cause_analysis(gaps, service_name)
            
            # Categorize by severity
            categorized = {
                "CRITICAL": [g for g in gaps if g.severity == "CRITICAL"],
                "HIGH": [g for g in gaps if g.severity == "HIGH"],
                "MEDIUM": [g for g in gaps if g.severity == "MEDIUM"],
                "LOW": [g for g in gaps if g.severity == "LOW"]
            }
            
            # Generate recommendations
            recommendations = self._generate_gap_recommendations(gaps)
            
            return {
                "total_gaps": len(gaps),
                "by_severity": {
                    "CRITICAL": len(categorized["CRITICAL"]),
                    "HIGH": len(categorized["HIGH"]),
                    "MEDIUM": len(categorized["MEDIUM"]),
                    "LOW": len(categorized["LOW"])
                },
                "by_type": self._group_by_type(gaps),
                "gaps": {
                    "CRITICAL": [g.to_dict() for g in categorized["CRITICAL"]],
                    "HIGH": [g.to_dict() for g in categorized["HIGH"]],
                    "MEDIUM": [g.to_dict() for g in categorized["MEDIUM"]],
                    "LOW": [g.to_dict() for g in categorized["LOW"]]
                },
                "recommendations": recommendations,
                "metadata": {
                    "service_name": service_name,
                    "timeline_id": str(timeline_id) if timeline_id else None,
                    "analyzed_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze gaps: {e}", exc_info=True)
            raise
    
    async def _analyze_coverage_gaps(
        self,
        service_name: Optional[str]
    ) -> List[DocumentationGap]:
        """Analyze coverage-related gaps."""
        gaps = []
        
        # Get coverage analysis
        coverage = await self.coverage_analyzer.analyze_coverage(service_name=service_name)
        
        # Check overall coverage
        coverage_score = coverage["overall_coverage"]["coverage_score"]
        if coverage_score < 50:
            gaps.append(DocumentationGap(
                gap_type="low_coverage",
                severity="CRITICAL",
                description=f"Overall documentation coverage is critically low ({coverage_score:.1f}%)",
                affected_area="entire_codebase",
                root_cause="Insufficient documentation effort",
                recommendation="Prioritize documenting core APIs and frequently used modules"
            ))
        elif coverage_score < 70:
            gaps.append(DocumentationGap(
                gap_type="low_coverage",
                severity="HIGH",
                description=f"Documentation coverage is below target ({coverage_score:.1f}%)",
                affected_area="entire_codebase",
                root_cause="Incomplete documentation",
                recommendation="Focus on documenting public APIs and main features"
            ))
        
        # Check service-specific gaps
        services = coverage["service_coverage"]["by_service"]
        for service in services:
            if service["document_count"] < 5:  # Arbitrary threshold
                gaps.append(DocumentationGap(
                    gap_type="service_gap",
                    severity="MEDIUM",
                    description=f"Service '{service['service_name']}' has minimal documentation",
                    affected_area=service['service_name'],
                    root_cause="Service not well documented",
                    recommendation=f"Add comprehensive documentation for {service['service_name']}"
                ))
        
        return gaps
    
    async def _analyze_topic_gaps(
        self,
        service_name: Optional[str]
    ) -> List[DocumentationGap]:
        """Analyze topic-related gaps."""
        gaps = []
        
        # Expected topics that should be documented
        expected_topics = [
            "authentication",
            "authorization",
            "configuration",
            "deployment",
            "api",
            "architecture",
            "getting_started",
            "troubleshooting"
        ]
        
        async with get_database().session() as session:
            doc_repo = DocumentRepository(session)
            
            # Get all documents
            if service_name:
                documents = await doc_repo.get_by_service(service_name, limit=10000)
            else:
                documents = await doc_repo.get_all(limit=10000)
            
            # Check which topics are covered
            covered_topics = set()
            for doc in documents:
                if not doc.normalized_content:
                    continue
                
                content_lower = doc.normalized_content.lower()
                for topic in expected_topics:
                    if topic in content_lower or topic in doc.file_path.lower():
                        covered_topics.add(topic)
            
            # Identify missing topics
            missing_topics = set(expected_topics) - covered_topics
            
            for topic in missing_topics:
                gaps.append(DocumentationGap(
                    gap_type="missing_topic",
                    severity=self._topic_severity(topic),
                    description=f"No documentation found for topic: {topic}",
                    affected_area=topic,
                    root_cause="Topic not covered",
                    recommendation=f"Create documentation for {topic}"
                ))
        
        return gaps
    
    async def _analyze_temporal_gaps(
        self,
        timeline_id: UUID
    ) -> List[DocumentationGap]:
        """Analyze gaps using timeline data."""
        gaps = []
        
        async with get_database().session() as session:
            timeline_repo = TimelineRepository(session)
            period_repo = TimePeriodRepository(session)
            
            # Get timeline
            timeline = await timeline_repo.get_by_id(timeline_id)
            if not timeline:
                return gaps
            
            # Get all periods
            periods = await period_repo.get_by_timeline(timeline_id, order_by_sequence=True)
            
            # Check for periods with no documents
            for period in periods:
                if period.document_count == 0:
                    gaps.append(DocumentationGap(
                        gap_type="empty_period",
                        severity="MEDIUM",
                        description=f"Period '{period.name}' has no documented content",
                        affected_area=f"time_period_{period.sequence_number}",
                        root_cause="No activity or documentation in this period",
                        recommendation=f"Review if period {period.name} should have documentation"
                    ))
            
            # Check for periods with very few documents
            avg_doc_count = sum(p.document_count for p in periods) / len(periods) if periods else 0
            for period in periods:
                if period.document_count > 0 and period.document_count < avg_doc_count * 0.3:
                    gaps.append(DocumentationGap(
                        gap_type="sparse_period",
                        severity="LOW",
                        description=f"Period '{period.name}' has unusually few documents",
                        affected_area=f"time_period_{period.sequence_number}",
                        root_cause="Low activity or documentation gaps in this period",
                        recommendation=f"Consider if {period.name} needs more documentation"
                    ))
        
        return gaps
    
    async def _add_root_cause_analysis(
        self,
        gaps: List[DocumentationGap],
        service_name: Optional[str]
    ) -> List[DocumentationGap]:
        """Add root cause analysis to gaps."""
        # This is a simplified version
        # In production, you'd use more sophisticated analysis
        
        # Group gaps by type
        gap_types = defaultdict(list)
        for gap in gaps:
            gap_types[gap.gap_type].append(gap)
        
        # Enhance root cause based on patterns
        if len(gap_types.get("service_gap", [])) > 3:
            for gap in gap_types["service_gap"]:
                gap.root_cause = "Systematic lack of service-level documentation"
                gap.recommendation = "Implement documentation standards for all services"
        
        if len(gap_types.get("missing_topic", [])) > 5:
            for gap in gap_types["missing_topic"]:
                gap.root_cause = "Incomplete documentation strategy"
                gap.recommendation = "Create comprehensive documentation plan covering all topics"
        
        return gaps
    
    def _topic_severity(self, topic: str) -> str:
        """Determine severity based on topic importance."""
        critical_topics = ["authentication", "authorization", "security"]
        high_topics = ["api", "configuration", "deployment"]
        
        if topic in critical_topics:
            return "CRITICAL"
        elif topic in high_topics:
            return "HIGH"
        else:
            return "MEDIUM"
    
    def _group_by_type(self, gaps: List[DocumentationGap]) -> Dict[str, int]:
        """Group gaps by type."""
        types = defaultdict(int)
        for gap in gaps:
            types[gap.gap_type] += 1
        return dict(types)
    
    def _generate_gap_recommendations(
        self,
        gaps: List[DocumentationGap]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations."""
        recommendations = []
        
        critical_gaps = [g for g in gaps if g.severity == "CRITICAL"]
        high_gaps = [g for g in gaps if g.severity == "HIGH"]
        
        if critical_gaps:
            recommendations.append({
                "priority": "CRITICAL",
                "title": f"Address {len(critical_gaps)} critical documentation gaps",
                "actions": list(set([g.recommendation for g in critical_gaps[:5]]))
            })
        
        if high_gaps:
            recommendations.append({
                "priority": "HIGH",
                "title": f"Address {len(high_gaps)} high-priority gaps",
                "actions": list(set([g.recommendation for g in high_gaps[:5]]))
            })
        
        # General recommendations
        if len(gaps) > 10:
            recommendations.append({
                "priority": "MEDIUM",
                "title": "Implement systematic documentation process",
                "actions": [
                    "Create documentation templates",
                    "Set up documentation reviews",
                    "Establish documentation standards"
                ]
            })
        
        return recommendations
    
    async def get_gap_trend(
        self,
        service_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Track gap trends over time.
        
        Args:
            service_name: Service to analyze
            days: Days to look back
        
        Returns:
            Gap trend data
        """
        try:
            self.logger.info(f"📈 Tracking gap trend for {service_name} ({days} days)")
            
            # Get current gaps
            current = await self.analyze_gaps(service_name=service_name, include_root_cause=False)
            
            return {
                "service_name": service_name,
                "period_days": days,
                "current_gaps": current["total_gaps"],
                "trend": "stable",  # Would calculate from historical data
                "note": "Historical gap tracking requires time-series data storage"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to track gap trend: {e}", exc_info=True)
            raise

