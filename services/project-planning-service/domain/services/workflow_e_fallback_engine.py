"""
Workflow E Fallback Engine - Smart Defaults for Demo Mode

Provides realistic fallback data when service clients aren't available.
Uses actual external-service-store database and intelligent tech stack analysis.
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from ..entities.external_service_entities import (
    ExternalServiceMatch, DiscoveryMethod, ServiceCategory,
    ServiceCatalogEntry, ComplianceValidationResult, ValidationIssue, IssueSeverity,
    KnowledgeGap, KnowledgeGapAnalysis,
    DevelopmentBlindspot, BlindspotAnalysis,
    AccuracyEnhancementResult, WorkflowEResult
)


class WorkflowEFallbackEngine:
    """
    Provides intelligent fallback data for Workflow E when services aren't running.
    
    Strategy:
    1. Query actual external-service-store database
    2. Analyze tech stack to determine relevance
    3. Generate realistic validation issues based on common patterns
    4. Provide sensible knowledge gaps and blindspots
    5. Calculate accuracy adjustments based on findings
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize with path to external-service-store database."""
        if db_path is None:
            # Default path relative to this file
            project_root = Path(__file__).parent.parent.parent.parent.parent
            db_path = str(project_root / "services" / "external-service-store" / "data" / "external_services.db")
        
        self.db_path = db_path
        self.db_exists = Path(db_path).exists()
    
    def generate_realistic_workflow_e_result(
        self,
        feature_query: str,
        extracted_requirements: Dict[str, Any],
        original_plan: Dict[str, Any]
    ) -> WorkflowEResult:
        """
        Generate realistic Workflow E result using database and tech stack analysis.
        """
        tech_stack = extracted_requirements.get("tech_stack", [])
        
        # Phase 1: Discover services from database
        discovered_services = self._discover_services_from_db(tech_stack, feature_query)
        
        # Phase 2: Catalog (add relationships)
        cataloged_services = self._catalog_services(discovered_services)
        
        # Phase 3: Validate (find realistic issues)
        validation_results = self._generate_validation_results(cataloged_services, tech_stack)
        
        # Phase 4: Knowledge gap analysis
        gap_analyses = self._generate_gap_analyses(cataloged_services, tech_stack)
        
        # Phase 5: Blindspot analysis
        blindspot_analyses = self._generate_blindspot_analyses(cataloged_services, tech_stack)
        
        # Phase 6: Accuracy enhancement
        accuracy_enhancement = self._calculate_accuracy_enhancement(
            original_plan,
            len(discovered_services),
            validation_results,
            gap_analyses,
            blindspot_analyses
        )
        
        return WorkflowEResult(
            discovered_services=discovered_services,
            cataloged_services=cataloged_services,
            validation_results=validation_results,
            gap_analyses=gap_analyses,
            blindspot_analyses=blindspot_analyses,
            accuracy_enhancement=accuracy_enhancement,
            execution_time_seconds=0.5  # Simulated fast execution
        )
    
    def _discover_services_from_db(
        self,
        tech_stack: List[str],
        feature_query: str
    ) -> List[ExternalServiceMatch]:
        """Query actual database for relevant services."""
        if not self.db_exists:
            return self._generate_fallback_services(tech_stack)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query to find relevant services
            tech_terms = [tech.lower() for tech in tech_stack]
            query_terms = feature_query.lower()
            
            cursor.execute("""
                SELECT id, name, display_name, description, service_type, 
                       version, technologies, tags
                FROM external_services
                WHERE status = 'ACTIVE'
            """)
            
            matches = []
            for row in cursor.fetchall():
                service_id, name, display_name, description, service_type, version, tech_json, tags_json = row
                
                technologies = json.loads(tech_json) if tech_json else []
                tags = json.loads(tags_json) if tags_json else []
                
                # Calculate relevance score
                relevance = self._calculate_relevance(
                    tech_stack, technologies, tags, description, query_terms
                )
                
                if relevance > 0.3:  # Only include if somewhat relevant
                    matches.append(ExternalServiceMatch(
                        service_id=service_id,
                        name=display_name,  # Use display name
                        relevance_score=relevance,
                        discovery_methods=[DiscoveryMethod.TOPIC_MATCH, DiscoveryMethod.TECHNOLOGY_MATCH],
                        initial_category=ServiceCategory.DIRECT if relevance >= 0.7 else ServiceCategory.TANGENTIAL,
                        technologies=technologies,
                        topics=tags[:3],  # Use tags as topics
                        metadata={"db_source": name}
                    ))
            
            conn.close()
            
            # Sort by relevance and return top 10
            matches.sort(key=lambda m: m.relevance_score, reverse=True)
            return matches[:10]
            
        except Exception as e:
            print(f"⚠️  Database query failed: {e}")
            return self._generate_fallback_services(tech_stack)
    
    def _calculate_relevance(
        self,
        tech_stack: List[str],
        technologies: List[str],
        tags: List[str],
        description: str,
        query_terms: str
    ) -> float:
        """Calculate relevance score (0.0 to 1.0)."""
        score = 0.0
        
        # Tech stack matching (weight: 0.5)
        tech_lower = [t.lower() for t in tech_stack]
        service_tech_lower = [t.lower() for t in technologies]
        service_tags_lower = [t.lower() for t in tags]
        
        tech_matches = sum(1 for t in tech_lower if any(st in t or t in st for st in service_tech_lower))
        if tech_stack:
            score += (tech_matches / len(tech_stack)) * 0.5
        
        # Tag matching (weight: 0.3)
        tag_matches = sum(1 for t in tech_lower if any(tag in t or t in tag for tag in service_tags_lower))
        if tech_stack:
            score += (tag_matches / len(tech_stack)) * 0.3
        
        # Query term matching (weight: 0.2)
        desc_lower = description.lower()
        query_word_matches = sum(1 for word in query_terms.split() if word in desc_lower and len(word) > 3)
        if query_terms:
            score += min(query_word_matches / 10, 1.0) * 0.2
        
        return min(score, 1.0)
    
    def _generate_fallback_services(self, tech_stack: List[str]) -> List[ExternalServiceMatch]:
        """Generate reasonable fallback services if database unavailable."""
        fallback_services = []
        
        if any("scala" in tech.lower() for tech in tech_stack):
            fallback_services.append(ExternalServiceMatch(
                service_id="fallback-scala-http4s",
                name="Scala HTTP4s API",
                relevance_score=0.95,
                discovery_methods=[DiscoveryMethod.EXPLICIT_MENTION],
                initial_category=ServiceCategory.DIRECT,
                technologies=["Scala", "Cats Effect", "HTTP4s"],
                topics=["backend", "api", "functional"],
                metadata={"fallback": True}
            ))
        
        if any("elm" in tech.lower() for tech in tech_stack):
            fallback_services.append(ExternalServiceMatch(
                service_id="fallback-elm-frontend",
                name="Elm Frontend Framework",
                relevance_score=0.93,
                discovery_methods=[DiscoveryMethod.EXPLICIT_MENTION],
                initial_category=ServiceCategory.DIRECT,
                technologies=["Elm", "Frontend"],
                topics=["frontend", "ui"],
                metadata={"fallback": True}
            ))
        
        return fallback_services[:5]
    
    def _catalog_services(
        self,
        discovered_services: List[ExternalServiceMatch]
    ) -> List[ServiceCatalogEntry]:
        """Add cataloging information to services."""
        cataloged = []
        
        for service in discovered_services:
            cataloged.append(ServiceCatalogEntry(
                service_match=service,
                skills_coverage={"matched": 2, "total": 3},
                historical_tickets=[],
                documentation_links=[],
                team_members=[],
                coverage_score=0.75 + (service.relevance_score * 0.20),
                documentation_quality="Good" if service.relevance_score > 0.7 else "Fair"
            ))
        
        return cataloged
    
    def _generate_validation_results(
        self,
        cataloged_services: List[ServiceCatalogEntry],
        tech_stack: List[str]
    ) -> List[ComplianceValidationResult]:
        """Generate realistic validation issues."""
        results = []
        
        for service in cataloged_services[:5]:  # Validate top 5
            issues = []
            
            # Common validation patterns
            if "api" in service.service_match.name.lower():
                issues.append(ValidationIssue(
                    severity=IssueSeverity.MEDIUM,
                    category="api_contract",
                    issue="API version compatibility",
                    impact="May require code changes",
                    detection_method="Schema analysis",
                    remediation="Review migration guide",
                    story_points_to_add=2,
                    timeline_impact_days=1.0,
                    sprint="Sprint 2"
                ))
            
            if service.service_match.relevance_score < 0.8:
                issues.append(ValidationIssue(
                    severity=IssueSeverity.LOW,
                    category="documentation",
                    issue="Limited integration documentation",
                    impact="Slower integration",
                    detection_method="Doc analysis",
                    remediation="Create integration guide",
                    story_points_to_add=1,
                    timeline_impact_days=0.5,
                    sprint="Sprint 1"
                ))
            
            total_sp = sum(i.story_points_to_add for i in issues)
            total_days = sum(i.timeline_impact_days for i in issues)
            
            results.append(ComplianceValidationResult(
                service_id=service.service_match.service_id,
                service_name=service.service_match.name,
                api_compliant=len(issues) == 0,
                security_compliant=True,
                version_compatible=True,
                rate_limits_sufficient=True,
                issues=issues,
                total_story_points_to_add=total_sp,
                total_timeline_impact_days=total_days,
                validation_confidence=0.85
            ))
        
        return results
    
    def _generate_gap_analyses(
        self,
        cataloged_services: List[ServiceCatalogEntry],
        tech_stack: List[str]
    ) -> List[KnowledgeGapAnalysis]:
        """Generate realistic knowledge gap analyses."""
        analyses = []
        
        if cataloged_services:
            doc_gaps = [KnowledgeGap(
                gap_type="documentation",
                severity=IssueSeverity.MEDIUM,
                description=f"Integration patterns for {cataloged_services[0].service_match.name}",
                impact="Slower development",
                remediation_actions=[{"action": "Create integration guide", "owner": "Tech Lead"}],
                story_points_to_add=3,
                timeline_impact_days=2.0
            )]
            
            skill_gaps = [KnowledgeGap(
                gap_type="skills",
                severity=IssueSeverity.LOW,
                description=f"Team proficiency in {tech_stack[0] if tech_stack else 'technology'}",
                impact="Learning curve",
                remediation_actions=[{"action": "Training sessions", "owner": "Team"}],
                story_points_to_add=2,
                timeline_impact_days=1.5
            )] if tech_stack else []
            
            analyses.append(KnowledgeGapAnalysis(
                service_id=cataloged_services[0].service_match.service_id,
                service_name=cataloged_services[0].service_match.name,
                documentation_gaps=doc_gaps,
                skills_gaps=skill_gaps,
                configuration_gaps=[],
                total_story_points_to_add=sum(g.story_points_to_add for g in doc_gaps + skill_gaps),
                total_timeline_impact_days=sum(g.timeline_impact_days for g in doc_gaps + skill_gaps),
                enrichment_actions=[]
            ))
        
        return analyses
    
    def _generate_blindspot_analyses(
        self,
        cataloged_services: List[ServiceCatalogEntry],
        tech_stack: List[str]
    ) -> List[BlindspotAnalysis]:
        """Generate realistic blindspot analyses."""
        analyses = []
        
        if cataloged_services:
            blindspots = [
                DevelopmentBlindspot(
                    blindspot_type="hidden_dependency",
                    severity=IssueSeverity.MEDIUM,
                    description="Transitive dependency risk",
                    why_missed="Not visible in initial analysis",
                    impact="Potential runtime failures",
                    detection_method="Static analysis",
                    story_points_to_add=3,
                    timeline_impact_days=2.0,
                    mitigation="Pin dependency versions",
                    sprint="Sprint 1"
                )
            ]
            
            if len(tech_stack) >= 2:
                blindspots.append(DevelopmentBlindspot(
                    blindspot_type="scale_issue",
                    severity=IssueSeverity.HIGH,
                    description="Performance testing gap",
                    why_missed="Not part of initial requirements",
                    impact="May fail under load",
                    detection_method="Performance analysis",
                    story_points_to_add=5,
                    timeline_impact_days=3.0,
                    mitigation="Add load testing",
                    sprint="Sprint 2"
                ))
            
            total_sp = sum(b.story_points_to_add for b in blindspots)
            total_days = sum(b.timeline_impact_days for b in blindspots)
            
            analyses.append(BlindspotAnalysis(
                service_id=cataloged_services[0].service_match.service_id,
                service_name=cataloged_services[0].service_match.name,
                blindspots=blindspots,
                severity_distribution={"HIGH": 1, "MEDIUM": 1},
                total_story_points_missed=total_sp,
                total_timeline_impact_days=total_days,
                detection_confidence=0.75
            ))
        
        return analyses
    
    def _calculate_accuracy_enhancement(
        self,
        original_plan: Dict[str, Any],
        services_found: int,
        validation_results: List[ComplianceValidationResult],
        gap_analyses: List[KnowledgeGapAnalysis],
        blindspot_analyses: List[BlindspotAnalysis]
    ) -> AccuracyEnhancementResult:
        """Calculate plan adjustments based on findings."""
        original_sp = original_plan.get("story_points", 0)
        original_weeks = original_plan.get("weeks", 0)
        original_confidence = original_plan.get("confidence", 0)
        
        # Calculate story points to add
        validation_sp = sum(vr.total_story_points_to_add for vr in validation_results)
        gap_sp = sum(ga.total_story_points_to_add for ga in gap_analyses)
        blindspot_sp = sum(ba.total_story_points_missed for ba in blindspot_analyses)
        
        sp_added = validation_sp + gap_sp + blindspot_sp
        adjusted_sp = original_sp + sp_added
        
        # Calculate timeline impact
        validation_days = sum(vr.total_timeline_impact_days for vr in validation_results)
        gap_days = sum(ga.total_timeline_impact_days for ga in gap_analyses)
        blindspot_days = sum(ba.total_timeline_impact_days for ba in blindspot_analyses)
        
        weeks_added = (validation_days + gap_days + blindspot_days) / 5  # Convert days to weeks
        adjusted_weeks = original_weeks + weeks_added
        
        # Confidence improves with discovery
        confidence_boost = min(10 + (services_found * 2), 20)
        adjusted_confidence = min(original_confidence + confidence_boost, 95)
        
        # Risk reduction
        original_risk = original_plan.get("risk_level", "MEDIUM")
        adjusted_risk = "LOW" if len(blindspot_analyses) > 0 else "MEDIUM"
        risk_reduction = 40.0 if adjusted_risk == "LOW" else 0.0
        
        # Create dummy results for the structure
        validation_finding = validation_results[0] if validation_results else ComplianceValidationResult(
            service_id="none", service_name="None", api_compliant=True, security_compliant=True,
            version_compatible=True, rate_limits_sufficient=True, issues=[],
            total_story_points_to_add=0, total_timeline_impact_days=0.0, validation_confidence=1.0
        )
        
        gap_finding = gap_analyses[0] if gap_analyses else KnowledgeGapAnalysis(
            service_id="none", service_name="None", documentation_gaps=[], skills_gaps=[], configuration_gaps=[],
            total_story_points_to_add=0, total_timeline_impact_days=0.0, enrichment_actions=[]
        )
        
        blindspot_finding = blindspot_analyses[0] if blindspot_analyses else BlindspotAnalysis(
            service_id="none", service_name="None", blindspots=[], severity_distribution={},
            total_story_points_missed=0, total_timeline_impact_days=0.0, detection_confidence=1.0
        )
        
        return AccuracyEnhancementResult(
            original_story_points=original_sp,
            adjusted_story_points=adjusted_sp,
            story_points_added=sp_added,
            story_points_change_percent=(sp_added / original_sp * 100) if original_sp > 0 else 0,
            original_weeks=original_weeks,
            adjusted_weeks=adjusted_weeks,
            weeks_added=weeks_added,
            timeline_change_percent=(weeks_added / original_weeks * 100) if original_weeks > 0 else 0,
            original_confidence=original_confidence,
            adjusted_confidence=adjusted_confidence,
            confidence_improvement=adjusted_confidence - original_confidence,
            original_risk_level=original_risk,
            adjusted_risk_level=adjusted_risk,
            risk_reduction_percent=risk_reduction,
            validation_findings=validation_finding,
            gap_findings=gap_finding,
            blindspot_findings=blindspot_finding,
            services_discovered=services_found,
            high_relevance_services=sum(1 for _ in validation_results),
            issues_found_total=sum(len(vr.issues) for vr in validation_results),
            blindspots_detected=sum(len(ba.blindspots) for ba in blindspot_analyses)
        )
