"""
Discovery Service for Adaptive Documentation

Queries existing repository_contexts to extract knowledge about the codebase
for adaptive documentation generation. Leverages 95% existing infrastructure.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.database import get_database
from ...storage.models_analysis import RepositoryContextModel, DetectedServiceModel
from ...storage.db_models import DocumentModel
from .runtime_framework_detector import get_runtime_detector

logger = logging.getLogger(__name__)


class DiscoveryService:
    """
    Discovers and extracts knowledge from existing repository analysis.
    
    Leverages EXISTING infrastructure:
    - repository_contexts table (frameworks, architecture, languages, tools)
    - detected_services table (services, endpoints, frameworks)
    - file_classifications table (importance, categories)
    
    Provides context for adaptive documentation generation without
    requiring additional analysis or database tables.
    """
    
    def __init__(self):
        """Initialize discovery service."""
        logger.info("DiscoveryService initialized")
    
    async def discover_repository_context(
        self,
        service_name: str,
        repo_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Discover comprehensive repository context.
        
        Args:
            service_name: Service name to discover
            repo_path: Optional repository path filter
        
        Returns:
            Complete repository context including frameworks, architecture,
            languages, tools, patterns, and entities
        """
        # Normalize service_name to match database (case-insensitive)
        original_service_name = service_name
        service_name = await self._normalize_service_name(service_name)
        if service_name != original_service_name:
            logger.info(f"📝 Normalized: '{original_service_name}' → '{service_name}'")
        
        logger.info(f"🔍 Discovering context for service: {service_name}")
        
        async with get_database().session() as session:
            # Query repository_contexts (EXISTING table)
            query = select(RepositoryContextModel).filter(
                RepositoryContextModel.repo_name == service_name
            )
            
            if repo_path:
                query = query.filter(RepositoryContextModel.repo_path == repo_path)
            
            result = await session.execute(query)
            repo_context = result.scalar_one_or_none()
            
            if not repo_context:
                logger.warning(f"No repository context found for {service_name}, attempting runtime detection")
                # Fall back to runtime detection from documents
                return await self._detect_context_from_documents(service_name, session)
            
            # Extract knowledge from existing data
            context = {
                "service_name": service_name,
                "root_path": repo_context.repo_path,
                
                # Framework information (EXISTING)
                "frameworks": repo_context.frameworks or [],
                "primary_framework": repo_context.frameworks[0] if repo_context.frameworks else None,
                
                # Architecture information (EXISTING)
                "architecture_type": repo_context.architecture_type,
                "architecture_patterns": repo_context.architecture_patterns or [],
                
                # Language information (EXISTING)
                "languages": repo_context.languages or {},
                "primary_language": self._get_primary_language(repo_context.languages),
                
                # Technology stack (EXISTING)
                "databases": repo_context.databases or [],
                "message_queues": repo_context.message_queues or [],
                "cache_systems": repo_context.cache_systems or [],
                "external_services": repo_context.external_services or [],
                "build_tools": repo_context.build_tools or [],
                
                # API information (EXISTING)
                "has_rest_api": repo_context.has_rest_api,
                "has_graphql_api": repo_context.has_graphql_api,
                "has_grpc_api": repo_context.has_grpc_api,
                "api_endpoints": repo_context.api_endpoints or [],
                
                # File statistics (EXISTING)
                "total_files": repo_context.total_files,
                "total_size_bytes": repo_context.total_size_bytes,
                
                # Metadata
                "context_version": repo_context.context_version,
                "last_analyzed_at": repo_context.last_analyzed_at.isoformat() if repo_context.last_analyzed_at else None,
            }
            
            # Discover detected services (EXISTING table)
            services = await self._discover_services(session, service_name)
            context["detected_services"] = services
            
            # Extract concepts and keywords from existing data
            context["concepts"] = self._extract_concepts(repo_context)
            context["keywords"] = self._extract_keywords(repo_context)
            
            logger.info(
                f"✅ Discovered context: {len(context['frameworks'])} frameworks, "
                f"{len(context['languages'])} languages, {len(context['concepts'])} concepts"
            )
            
            return context
    
    async def _detect_context_from_documents(
        self,
        service_name: str,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Fallback: Detect context from document file paths when repository_contexts is empty.
        
        Args:
            service_name: Service name
            session: Database session
        
        Returns:
            Context detected from document analysis
        """
        logger.info(f"🔍 Performing runtime detection for {service_name}")
        
        # Get all document file paths for this service (case-insensitive)
        query = select(DocumentModel.file_path).filter(
            func.lower(DocumentModel.service_name) == service_name.lower(),
            DocumentModel.is_latest == True
        )
        result = await session.execute(query)
        file_paths = [row[0] for row in result.fetchall()]
        
        if not file_paths:
            logger.warning(f"No documents found for {service_name}")
            return self._empty_context(service_name)
        
        logger.info(f"Analyzing {len(file_paths)} files for framework detection")
        
        # Use runtime detector
        detector = get_runtime_detector()
        detection = await detector.detect_from_file_paths(file_paths)
        
        # Get framework guidance
        frameworks = detection.get("frameworks", [])
        guidance = detector.get_framework_guidance(frameworks) if frameworks else {"guidance": "generic"}
        
        # Build context from detection
        context = {
            "service_name": service_name,
            "frameworks": frameworks,
            "primary_framework": frameworks[0] if frameworks else None,
            "languages": detection.get("languages", {}),
            "primary_language": detection.get("primary_language", "Unknown"),
            "architecture_type": self._infer_architecture_type(frameworks),
            "total_files": detection.get("file_count", 0),
            "detection_confidence": detection.get("confidence", 0.0),
            "framework_guidance": guidance,
            "concepts": self._extract_concepts_from_detection(detection),
            "keywords": frameworks + [detection.get("primary_language", "")],
            "detected_services": [],
            "runtime_detected": True  # Flag to indicate this was runtime detected
        }
        
        logger.info(
            f"✅ Runtime detection complete: "
            f"frameworks={frameworks}, "
            f"language={context['primary_language']}, "
            f"confidence={context['detection_confidence']:.2f}"
        )
        
        return context
    
    def _infer_architecture_type(self, frameworks: List[str]) -> str:
        """Infer architecture type from frameworks."""
        if not frameworks:
            return "unknown"
        
        framework_architecture_map = {
            "Play Framework": "mvc",
            "Spring Boot": "mvc",
            "Django": "mvc",
            "Flask": "microservice",
            "FastAPI": "microservice",
            "Express.js": "microservice"
        }
        
        for framework in frameworks:
            if framework in framework_architecture_map:
                return framework_architecture_map[framework]
        
        return "monolithic"
    
    def _extract_concepts_from_detection(self, detection: Dict[str, Any]) -> List[str]:
        """Extract concepts from runtime detection."""
        concepts = set()
        
        # Add frameworks as concepts
        frameworks = detection.get("frameworks", [])
        concepts.update(frameworks)
        
        # Add primary language
        primary_lang = detection.get("primary_language")
        if primary_lang and primary_lang != "Unknown":
            concepts.add(primary_lang)
        
        # Add language names
        languages = detection.get("languages", {})
        concepts.update(languages.keys())
        
        return sorted(list(concepts))
    
    def _empty_context(self, service_name: str) -> Dict[str, Any]:
        """Return empty context when no repository data found."""
        return {
            "service_name": service_name,
            "frameworks": [],
            "architecture_type": "unknown",
            "languages": {},
            "concepts": [],
            "keywords": [],
            "detected_services": [],
        }
    
    def _get_primary_language(self, languages: Dict[str, int]) -> Optional[str]:
        """Get primary language from language stats."""
        if not languages:
            return None
        
        # Return language with most files
        return max(languages.items(), key=lambda x: x[1])[0]
    
    async def _discover_services(
        self,
        session: AsyncSession,
        service_name: str
    ) -> List[Dict[str, Any]]:
        """
        Discover detected services from EXISTING detected_services table.
        
        Args:
            session: Database session
            service_name: Service name
        
        Returns:
            List of detected services with details
        """
        query = select(DetectedServiceModel).filter(
            func.lower(DetectedServiceModel.service_name) == service_name.lower()
        )
        
        result = await session.execute(query)
        services = result.scalars().all()
        
        return [
            {
                "name": s.name,
                "type": s.service_type,
                "root_path": s.root_path,
                "framework": s.framework,
                "has_api": s.has_api,
                "has_database": s.has_database,
                "has_tests": s.has_tests,
                "confidence_score": s.confidence_score,
            }
            for s in services
        ]
    
    def _extract_concepts(self, repo_context: RepositoryContextModel) -> List[str]:
        """
        Extract high-level concepts from repository context.
        
        Concepts are domain-specific terms derived from existing data:
        - Framework names
        - Architecture patterns
        - Database types
        - API types
        
        These will be used for adaptive re-embedding in future phases.
        """
        concepts = set()
        
        # Add frameworks as concepts
        if repo_context.frameworks:
            concepts.update(repo_context.frameworks)
        
        # Add architecture type
        if repo_context.architecture_type:
            concepts.add(repo_context.architecture_type)
        
        # Add architecture patterns
        if repo_context.architecture_patterns:
            concepts.update(repo_context.architecture_patterns)
        
        # Add technology concepts
        if repo_context.databases:
            concepts.update(repo_context.databases)
        
        if repo_context.message_queues:
            concepts.update(repo_context.message_queues)
        
        # Add API types
        if repo_context.has_rest_api:
            concepts.add("REST API")
        if repo_context.has_graphql_api:
            concepts.add("GraphQL API")
        if repo_context.has_grpc_api:
            concepts.add("gRPC API")
        
        return sorted(list(concepts))
    
    def _extract_keywords(self, repo_context: RepositoryContextModel) -> List[str]:
        """
        Extract keywords from repository context for prompt enhancement.
        
        Keywords are more granular terms that can be used in prompts
        to make them more specific to this codebase.
        """
        keywords = set()
        
        # Language keywords
        if repo_context.languages:
            keywords.update(repo_context.languages.keys())
        
        # Build tool keywords
        if repo_context.build_tools:
            keywords.update(repo_context.build_tools)
        
        # External service keywords
        if repo_context.external_services:
            keywords.update(repo_context.external_services)
        
        # Cache system keywords
        if repo_context.cache_systems:
            keywords.update(repo_context.cache_systems)
        
        return sorted(list(keywords))
    
    async def get_framework_specific_guidance(
        self,
        service_name: str
    ) -> Dict[str, Any]:
        """
        Get framework-specific guidance for documentation generation.
        
        Returns prompts and tips specific to detected frameworks,
        helping the LLM generate more accurate documentation.
        
        Args:
            service_name: Service name
        
        Returns:
            Framework-specific guidance including:
            - Recommended sections
            - Common patterns to look for
            - Framework-specific terminology
            - Example structures
        """
        context = await self.discover_repository_context(service_name)
        frameworks = context.get("frameworks", [])
        
        if not frameworks:
            return {"guidance": "generic"}
        
        primary_framework = frameworks[0]
        
        # Framework-specific guidance (extensible)
        guidance_map = {
            "Play Framework": {
                "recommended_sections": [
                    "Routes Configuration",
                    "Controllers",
                    "Actions",
                    "Models",
                    "Services",
                    "Configuration (application.conf)",
                ],
                "patterns_to_find": [
                    "Action composition",
                    "Dependency injection",
                    "Async actions",
                    "Form handling",
                    "WS client usage",
                ],
                "terminology": {
                    "controller": "Controller class handling HTTP requests",
                    "action": "Method that handles a specific route",
                    "routes": "URL routing configuration",
                    "conf": "Application configuration",
                },
                "file_extensions": [".scala", ".routes", ".conf"],
            },
            "Spring": {
                "recommended_sections": [
                    "Controllers",
                    "Services",
                    "Repositories",
                    "Configuration",
                    "Security",
                ],
                "patterns_to_find": [
                    "@RestController",
                    "@Service",
                    "@Repository",
                    "@Configuration",
                    "Dependency Injection",
                ],
                "terminology": {
                    "bean": "Spring-managed component",
                    "autowired": "Dependency injection",
                    "repository": "Data access layer",
                },
                "file_extensions": [".java", ".xml", ".properties"],
            },
            "Django": {
                "recommended_sections": [
                    "Views",
                    "Models",
                    "URLs",
                    "Templates",
                    "Middleware",
                ],
                "patterns_to_find": [
                    "Class-based views",
                    "ORM models",
                    "URL patterns",
                    "Middleware classes",
                ],
                "terminology": {
                    "view": "Request handler",
                    "model": "Database model",
                    "migration": "Database schema change",
                },
                "file_extensions": [".py", ".html"],
            },
        }
        
        return guidance_map.get(primary_framework, {"guidance": "generic"})
    
    async def extract_entity_relationships(
        self,
        service_name: str
    ) -> Dict[str, Any]:
        """
        Extract entity relationships from existing data.
        
        This prepares the foundation for knowledge graph building
        without requiring additional analysis.
        
        Args:
            service_name: Service name
        
        Returns:
            Entity relationships including:
            - Services and their dependencies
            - APIs and their endpoints
            - Databases and their connections
        """
        context = await self.discover_repository_context(service_name)
        
        relationships = {
            "service": service_name,
            "dependencies": {
                "databases": context.get("databases", []),
                "message_queues": context.get("message_queues", []),
                "cache_systems": context.get("cache_systems", []),
                "external_services": context.get("external_services", []),
            },
            "provides": {
                "rest_api": context.get("has_rest_api", False),
                "graphql_api": context.get("has_graphql_api", False),
                "grpc_api": context.get("has_grpc_api", False),
                "endpoints": context.get("api_endpoints", []),
            },
            "implements": {
                "frameworks": context.get("frameworks", []),
                "patterns": context.get("architecture_patterns", []),
            },
        }
        
        return relationships
    
    async def _normalize_service_name(self, service_name: str) -> str:
        """
        Normalize service_name to match actual casing in database.
        
        Args:
            service_name: Service name (any case)
        
        Returns:
            Service name with correct casing from database
        """
        import asyncio
        
        try:
            # 10 second timeout for database query
            async with asyncio.timeout(10):
                async with get_database().session() as session:
                    # Find actual service name in database (case-insensitive)
                    query = select(DocumentModel.service_name).filter(
                        func.lower(DocumentModel.service_name) == service_name.lower(),
                        DocumentModel.is_latest == True
                    ).limit(1)
                    
                    result = await session.execute(query)
                    actual_service_name = result.scalar_one_or_none()
                    
                    if actual_service_name:
                        return actual_service_name
                    else:
                        # If not found in documents, keep original
                        return service_name
        except asyncio.TimeoutError:
            logger.warning(f"⏱️  Service name normalization timed out after 10s, using original: {service_name}")
            return service_name
        except Exception as e:
            logger.warning(f"Failed to normalize service name: {e}, using original: {service_name}")
            return service_name


# Singleton instance
_discovery_service: Optional[DiscoveryService] = None


def get_discovery_service() -> DiscoveryService:
    """Get or create singleton discovery service."""
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = DiscoveryService()
    return _discovery_service

