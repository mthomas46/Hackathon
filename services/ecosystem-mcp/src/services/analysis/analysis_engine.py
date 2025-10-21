"""
Analysis Engine

Orchestrates all analysis components for comprehensive repository analysis.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from .dependency_analyzer import get_dependency_analyzer, DependencyGraph
from .stack_detector import get_stack_detector, TechnologyStack
from .architecture_detector import get_architecture_detector, ArchitectureAnalysis
from .service_detector import get_service_detector, ServiceMap

logger = logging.getLogger(__name__)


@dataclass
class AnalysisReport:
    """Comprehensive analysis report for a repository."""
    plan_id: str
    repo_path: str
    
    # Core Analysis
    dependency_graph: Optional[DependencyGraph]
    technology_stack: Optional[TechnologyStack]
    architecture: Optional[ArchitectureAnalysis]
    service_map: Optional[ServiceMap]
    
    # Summary Metrics
    total_files: int
    total_languages: int
    total_frameworks: int
    total_services: int
    modularity_score: float
    
    # Status
    analysis_complete: bool
    errors: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        result = {
            'plan_id': self.plan_id,
            'repo_path': self.repo_path,
            'dependency_graph': self.dependency_graph.to_dict() if self.dependency_graph else None,
            'technology_stack': self.technology_stack.to_dict() if self.technology_stack else None,
            'architecture': self.architecture.to_dict() if self.architecture else None,
            'service_map': self.service_map.to_dict() if self.service_map else None,
            'total_files': self.total_files,
            'total_languages': self.total_languages,
            'total_frameworks': self.total_frameworks,
            'total_services': self.total_services,
            'modularity_score': self.modularity_score,
            'analysis_complete': self.analysis_complete,
            'errors': self.errors
        }
        return result


class AnalysisEngine:
    """
    Orchestrates multi-file analysis for repositories.
    
    Integrates:
    - Dependency analysis
    - Technology stack detection
    - Architecture pattern detection
    - Service boundary detection
    """
    
    def __init__(self):
        self.dependency_analyzer = get_dependency_analyzer()
        self.stack_detector = get_stack_detector()
        self.architecture_detector = get_architecture_detector()
        self.service_detector = get_service_detector()
        
        logger.info("AnalysisEngine initialized")
    
    async def analyze(
        self,
        plan_id: str,
        files: List[Dict],
        repo_path: str
    ) -> AnalysisReport:
        """
        Perform comprehensive analysis.
        
        Args:
            plan_id: Processing plan ID
            files: List of file information from Phase 1
            repo_path: Repository root path
        
        Returns:
            Complete analysis report
        """
        logger.info(f"🔬 Starting comprehensive analysis for plan {plan_id}")
        logger.info(f"   Files: {len(files)}, Repo: {repo_path}")
        
        errors = []
        
        # Step 1: Dependency Analysis
        dependency_graph = None
        try:
            logger.info("📊 Step 1/4: Dependency analysis...")
            dependency_graph = await self.dependency_analyzer.analyze_repository(
                repo_path=repo_path,
                files=files
            )
            logger.info(
                f"   ✅ Found {len(dependency_graph.nodes)} nodes, "
                f"{len(dependency_graph.edges)} edges"
            )
        except Exception as e:
            logger.error(f"   ❌ Dependency analysis failed: {e}")
            errors.append(f"Dependency analysis: {str(e)}")
        
        # Step 2: Technology Stack Detection
        technology_stack = None
        try:
            logger.info("🔧 Step 2/4: Technology stack detection...")
            technology_stack = await self.stack_detector.detect_stack(
                files=files,
                repo_path=repo_path
            )
            logger.info(
                f"   ✅ Detected {len(technology_stack.languages)} languages, "
                f"{len(technology_stack.frameworks)} frameworks"
            )
        except Exception as e:
            logger.error(f"   ❌ Stack detection failed: {e}")
            errors.append(f"Stack detection: {str(e)}")
        
        # Step 3: Architecture Detection
        architecture = None
        try:
            logger.info("🏗️ Step 3/4: Architecture detection...")
            architecture = await self.architecture_detector.detect_architecture(
                files=files,
                repo_path=repo_path,
                dependency_graph=dependency_graph.to_dict() if dependency_graph else None
            )
            
            primary = architecture.primary_pattern.name if architecture.primary_pattern else "unknown"
            logger.info(
                f"   ✅ Primary pattern: {primary}, "
                f"Layers: {len(architecture.layers)}"
            )
        except Exception as e:
            logger.error(f"   ❌ Architecture detection failed: {e}")
            errors.append(f"Architecture detection: {str(e)}")
        
        # Step 4: Service Boundary Detection
        service_map = None
        try:
            logger.info("🎯 Step 4/4: Service boundary detection...")
            service_map = await self.service_detector.detect_services(
                files=files,
                repo_path=repo_path,
                dependency_graph=dependency_graph.to_dict() if dependency_graph else None
            )
            logger.info(f"   ✅ Detected {service_map.service_count} service(s)")
        except Exception as e:
            logger.error(f"   ❌ Service detection failed: {e}")
            errors.append(f"Service detection: {str(e)}")
        
        # Build summary metrics
        total_languages = len(technology_stack.languages) if technology_stack else 0
        total_frameworks = len(technology_stack.frameworks) if technology_stack else 0
        total_services = service_map.service_count if service_map else 1
        modularity_score = architecture.modularity_score if architecture else 0.5
        
        report = AnalysisReport(
            plan_id=plan_id,
            repo_path=repo_path,
            dependency_graph=dependency_graph,
            technology_stack=technology_stack,
            architecture=architecture,
            service_map=service_map,
            total_files=len(files),
            total_languages=total_languages,
            total_frameworks=total_frameworks,
            total_services=total_services,
            modularity_score=modularity_score,
            analysis_complete=len(errors) == 0,
            errors=errors
        )
        
        logger.info(f"✅ Analysis complete for plan {plan_id}")
        logger.info(f"   Total files: {report.total_files}")
        logger.info(f"   Languages: {report.total_languages}")
        logger.info(f"   Frameworks: {report.total_frameworks}")
        logger.info(f"   Services: {report.total_services}")
        logger.info(f"   Modularity: {report.modularity_score:.2f}")
        
        if errors:
            logger.warning(f"   ⚠️ {len(errors)} error(s) occurred")
        
        return report
    
    async def get_topological_order(
        self,
        report: AnalysisReport
    ) -> Optional[List[str]]:
        """
        Get topological processing order from dependency graph.
        
        Args:
            report: Analysis report
        
        Returns:
            List of file paths in topological order, or None
        """
        if not report.dependency_graph or not report.dependency_graph.topological_order:
            return None
        
        return report.dependency_graph.topological_order
    
    async def get_primary_language(
        self,
        report: AnalysisReport
    ) -> Optional[str]:
        """Get primary language."""
        if not report.technology_stack:
            return None
        
        return await self.stack_detector.get_primary_language(
            report.technology_stack
        )
    
    async def is_microservices(
        self,
        report: AnalysisReport
    ) -> bool:
        """Check if repository uses microservices architecture."""
        if not report.architecture or not report.architecture.primary_pattern:
            return False
        
        return report.architecture.primary_pattern.name == 'microservices'
    
    async def get_service_for_file(
        self,
        report: AnalysisReport,
        file_path: str
    ) -> Optional[str]:
        """Get service name for a file."""
        if not report.service_map:
            return None
        
        for service in report.service_map.services:
            if file_path in service.files:
                return service.name
        
        return None


# Singleton
_analysis_engine_instance = None

def get_analysis_engine() -> AnalysisEngine:
    """Get singleton analysis engine instance."""
    global _analysis_engine_instance
    if _analysis_engine_instance is None:
        _analysis_engine_instance = AnalysisEngine()
    return _analysis_engine_instance

