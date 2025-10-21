"""
Repository Context Generator

Generates repository-level contexts for context-aware RAG queries.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from .analysis_engine import AnalysisReport

logger = logging.getLogger(__name__)


@dataclass
class RepositoryContext:
    """
    Repository context for RAG filtering.
    
    Used to provide context-aware RAG queries that are scoped to specific repositories.
    """
    repo_id: str
    repo_name: str
    repo_path: str
    
    # Technology Stack
    languages: List[str]
    primary_language: Optional[str]
    frameworks: List[str]
    databases: List[str]
    tools: List[str]
    
    # Architecture
    architecture_type: Optional[str]
    architecture_confidence: Optional[float]
    architecture_description: str
    service_count: int
    is_microservices: bool
    layers: List[str]
    
    # API Summary
    endpoints: List[Dict]
    endpoint_count: int
    has_rest_api: bool
    has_graphql: bool
    
    # Code Metrics
    total_files: int
    code_files: int
    test_files: int
    doc_files: int
    total_lines: int
    modularity_score: float
    
    # Entry Points
    entry_points: List[str]
    
    # AI Summary
    brief_description: str
    key_features: List[str]
    technical_highlights: List[str]
    recommended_starting_points: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'repo_id': self.repo_id,
            'repo_name': self.repo_name,
            'repo_path': self.repo_path,
            'languages': self.languages,
            'primary_language': self.primary_language,
            'frameworks': self.frameworks,
            'databases': self.databases,
            'tools': self.tools,
            'architecture_type': self.architecture_type,
            'architecture_confidence': self.architecture_confidence,
            'architecture_description': self.architecture_description,
            'service_count': self.service_count,
            'is_microservices': self.is_microservices,
            'layers': self.layers,
            'endpoints': self.endpoints,
            'endpoint_count': self.endpoint_count,
            'has_rest_api': self.has_rest_api,
            'has_graphql': self.has_graphql,
            'total_files': self.total_files,
            'code_files': self.code_files,
            'test_files': self.test_files,
            'doc_files': self.doc_files,
            'total_lines': self.total_lines,
            'modularity_score': self.modularity_score,
            'entry_points': self.entry_points,
            'brief_description': self.brief_description,
            'key_features': self.key_features,
            'technical_highlights': self.technical_highlights,
            'recommended_starting_points': self.recommended_starting_points
        }


class ContextGenerator:
    """
    Generates repository contexts from analysis reports.
    
    Features:
    - Aggregates analysis results into context
    - Generates AI-powered summaries
    - Creates ChromaDB filter metadata
    - Provides recommended starting points
    """
    
    def __init__(self):
        logger.info("ContextGenerator initialized")
    
    async def generate_context(
        self,
        analysis_report: AnalysisReport,
        repo_name: Optional[str] = None
    ) -> RepositoryContext:
        """
        Generate repository context from analysis report.
        
        Args:
            analysis_report: Complete analysis report
            repo_name: Optional repository name (default: extract from path)
        
        Returns:
            RepositoryContext with all metadata
        """
        logger.info(f"🎯 Generating context for {analysis_report.repo_path}")
        
        # Extract basic info
        repo_id = self._generate_repo_id(analysis_report.repo_path)
        if not repo_name:
            repo_name = self._extract_repo_name(analysis_report.repo_path)
        
        # Extract technology stack
        languages, primary_language, frameworks, databases, tools = self._extract_technology_stack(analysis_report)
        
        # Extract architecture info
        arch_type, arch_confidence, arch_description, layers, is_microservices = self._extract_architecture(analysis_report)
        
        # Extract API info
        endpoints, endpoint_count, has_rest, has_graphql = self._extract_api_info(analysis_report)
        
        # Extract metrics
        code_files, test_files, doc_files = self._classify_files(analysis_report)
        
        # Extract entry points
        entry_points = self._extract_entry_points(analysis_report)
        
        # Generate AI summaries
        brief_description = await self._generate_brief_description(
            repo_name, languages, frameworks, arch_type, analysis_report
        )
        
        key_features = await self._generate_key_features(
            frameworks, arch_type, has_rest, has_graphql, is_microservices, analysis_report
        )
        
        technical_highlights = await self._generate_technical_highlights(
            languages, frameworks, databases, analysis_report
        )
        
        recommended_starting_points = await self._generate_starting_points(
            entry_points, arch_type, analysis_report
        )
        
        context = RepositoryContext(
            repo_id=repo_id,
            repo_name=repo_name,
            repo_path=analysis_report.repo_path,
            languages=languages,
            primary_language=primary_language,
            frameworks=frameworks,
            databases=databases,
            tools=tools,
            architecture_type=arch_type,
            architecture_confidence=arch_confidence,
            architecture_description=arch_description,
            service_count=analysis_report.total_services,
            is_microservices=is_microservices,
            layers=layers,
            endpoints=endpoints,
            endpoint_count=endpoint_count,
            has_rest_api=has_rest,
            has_graphql=has_graphql,
            total_files=analysis_report.total_files,
            code_files=code_files,
            test_files=test_files,
            doc_files=doc_files,
            total_lines=0,  # TODO: Calculate from files
            modularity_score=analysis_report.modularity_score,
            entry_points=entry_points,
            brief_description=brief_description,
            key_features=key_features,
            technical_highlights=technical_highlights,
            recommended_starting_points=recommended_starting_points
        )
        
        logger.info(f"✅ Generated context for {repo_name}")
        return context
    
    def _generate_repo_id(self, repo_path: str) -> str:
        """Generate repo ID from path."""
        # Convert path to safe ID
        repo_id = repo_path.replace("/", "_").replace("\\", "_").replace(" ", "_")
        return repo_id[-500:]  # Truncate if too long
    
    def _extract_repo_name(self, repo_path: str) -> str:
        """Extract repository name from path."""
        # Get last component of path
        parts = repo_path.replace("\\", "/").split("/")
        return parts[-1] if parts else "unknown"
    
    def _extract_technology_stack(
        self,
        report: AnalysisReport
    ) -> tuple[List[str], Optional[str], List[str], List[str], List[str]]:
        """Extract technology stack information."""
        if not report.technology_stack:
            return [], None, [], [], []
        
        stack = report.technology_stack
        
        languages = list(stack.languages.keys()) if stack.languages else []
        primary_language = max(stack.languages.items(), key=lambda x: x[1])[0] if stack.languages else None
        frameworks = list(stack.frameworks.keys()) if stack.frameworks else []
        databases = stack.databases if stack.databases else []
        tools = stack.tools if stack.tools else []
        
        return languages, primary_language, frameworks, databases, tools
    
    def _extract_architecture(
        self,
        report: AnalysisReport
    ) -> tuple[Optional[str], Optional[float], str, List[str], bool]:
        """Extract architecture information."""
        if not report.architecture:
            return None, None, "Unknown architecture", [], False
        
        arch = report.architecture
        
        arch_type = arch.primary_pattern.name if arch.primary_pattern else None
        arch_confidence = arch.primary_pattern.confidence if arch.primary_pattern else None
        arch_description = arch.primary_pattern.description if arch.primary_pattern else "Unknown architecture"
        layers = arch.layers if arch.layers else []
        is_microservices = arch_type == "microservices" if arch_type else False
        
        return arch_type, arch_confidence, arch_description, layers, is_microservices
    
    def _extract_api_info(
        self,
        report: AnalysisReport
    ) -> tuple[List[Dict], int, bool, bool]:
        """Extract API information."""
        endpoints = []
        has_rest = False
        has_graphql = False
        
        if report.service_map:
            for service in report.service_map.services:
                if service.has_api and service.endpoints:
                    for endpoint in service.endpoints:
                        endpoints.append({
                            'service': service.name,
                            'path': endpoint
                        })
                    has_rest = True
        
        return endpoints, len(endpoints), has_rest, has_graphql
    
    def _classify_files(self, report: AnalysisReport) -> tuple[int, int, int]:
        """Classify files by type."""
        # This is a simplified version - would need actual file classification
        total = report.total_files
        
        # Estimate based on typical ratios
        code_files = int(total * 0.6)
        test_files = int(total * 0.2)
        doc_files = int(total * 0.1)
        
        return code_files, test_files, doc_files
    
    def _extract_entry_points(self, report: AnalysisReport) -> List[str]:
        """Extract entry points."""
        if not report.architecture or not report.architecture.entry_points:
            return []
        
        return report.architecture.entry_points[:5]  # Limit to 5
    
    async def _generate_brief_description(
        self,
        repo_name: str,
        languages: List[str],
        frameworks: List[str],
        arch_type: Optional[str],
        report: AnalysisReport
    ) -> str:
        """Generate brief description."""
        # Rule-based for now (could be LLM-powered later)
        
        lang_str = ", ".join(languages[:3]) if languages else "unknown languages"
        fw_str = ", ".join(frameworks[:3]) if frameworks else "no major frameworks"
        arch_str = arch_type or "unknown architecture"
        
        description = (
            f"{repo_name} is a {lang_str} project using {fw_str}. "
            f"It follows a {arch_str} architecture with {report.total_services} service(s) "
            f"and {report.total_files} files."
        )
        
        return description
    
    async def _generate_key_features(
        self,
        frameworks: List[str],
        arch_type: Optional[str],
        has_rest: bool,
        has_graphql: bool,
        is_microservices: bool,
        report: AnalysisReport
    ) -> List[str]:
        """Generate key features list."""
        features = []
        
        # Architecture features
        if is_microservices:
            features.append(f"Microservices architecture with {report.total_services} services")
        elif arch_type:
            features.append(f"{arch_type.upper()} architecture pattern")
        
        # API features
        if has_rest:
            features.append("RESTful API endpoints")
        if has_graphql:
            features.append("GraphQL API")
        
        # Framework features
        for fw in frameworks[:3]:
            features.append(f"{fw} framework integration")
        
        # Modularity
        if report.modularity_score > 0.7:
            features.append("High modularity (well-decoupled)")
        elif report.modularity_score < 0.4:
            features.append("Tight coupling (refactoring opportunity)")
        
        return features[:5]  # Limit to 5
    
    async def _generate_technical_highlights(
        self,
        languages: List[str],
        frameworks: List[str],
        databases: List[str],
        report: AnalysisReport
    ) -> List[str]:
        """Generate technical highlights."""
        highlights = []
        
        # Multi-language
        if len(languages) > 2:
            highlights.append(f"Polyglot codebase: {', '.join(languages)}")
        
        # Database diversity
        if len(databases) > 1:
            highlights.append(f"Multiple data stores: {', '.join(databases)}")
        
        # Circular dependencies
        if report.dependency_graph and report.dependency_graph.circular_dependencies:
            cycle_count = len(report.dependency_graph.circular_dependencies)
            highlights.append(f"⚠️ {cycle_count} circular dependency cycles detected")
        
        # Complex architecture
        if report.total_services > 5:
            highlights.append(f"Complex system with {report.total_services} services")
        
        return highlights[:5]
    
    async def _generate_starting_points(
        self,
        entry_points: List[str],
        arch_type: Optional[str],
        report: AnalysisReport
    ) -> List[str]:
        """Generate recommended starting points."""
        starting_points = []
        
        # Entry points
        for ep in entry_points[:2]:
            starting_points.append(f"Start at {ep}")
        
        # Architecture-specific recommendations
        if arch_type == "microservices":
            starting_points.append("Review service-to-service communication patterns")
        elif arch_type == "mvc":
            starting_points.append("Begin with model definitions")
        
        # API endpoints
        if report.service_map:
            for service in report.service_map.services[:1]:
                if service.has_api:
                    starting_points.append(f"Explore {service.name} API endpoints")
        
        return starting_points[:3]  # Limit to 3
    
    async def get_chromadb_filter(self, context: RepositoryContext) -> Dict:
        """
        Get ChromaDB filter for context-aware queries.
        
        Args:
            context: Repository context
        
        Returns:
            ChromaDB where filter
        """
        return {
            "repo_id": context.repo_id
        }
    
    async def enrich_query_with_context(
        self,
        query: str,
        context: RepositoryContext
    ) -> str:
        """
        Enrich user query with repository context.
        
        Args:
            query: User's original query
            context: Repository context
        
        Returns:
            Enriched query with context
        """
        context_info = f"""
Repository Context: {context.repo_name}
Primary Language: {context.primary_language or 'N/A'}
Architecture: {context.architecture_type or 'N/A'}
Key Technologies: {', '.join(context.frameworks[:3])}

User Question: {query}
"""
        return context_info.strip()


# Singleton
_context_generator_instance = None

def get_context_generator() -> ContextGenerator:
    """Get singleton context generator instance."""
    global _context_generator_instance
    if _context_generator_instance is None:
        _context_generator_instance = ContextGenerator()
    return _context_generator_instance

