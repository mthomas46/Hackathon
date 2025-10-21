"""
Service Boundary Detector

Detects microservice boundaries in large systems.
"""

import logging
import re
from typing import List, Dict, Set, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Service:
    """Detected microservice."""
    name: str
    root_path: str
    files: List[str]
    file_count: int
    entry_point: Optional[str]
    
    # Dependencies
    internal_dependencies: List[str]  # Other services in repo
    external_dependencies: List[str]  # External packages
    
    # Technology
    languages: List[str]
    frameworks: List[str]
    databases: List[str]
    
    # API
    has_api: bool
    endpoints: List[str]
    
    # Deployment
    has_dockerfile: bool
    has_k8s_config: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ServiceMap:
    """Service dependency map."""
    services: List[Service]
    dependencies: Dict[str, List[str]]  # service_name -> [dependent_services]
    service_count: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'services': [s.to_dict() for s in self.services],
            'dependencies': self.dependencies,
            'service_count': self.service_count
        }


class ServiceBoundaryDetector:
    """
    Detects microservice boundaries in repositories.
    
    Detection strategies:
    1. Directory structure (services/, apps/)
    2. Separate entry points (main.py, app.py)
    3. Docker configurations
    4. Kubernetes manifests
    5. Different database connections
    6. Distinct API prefixes
    """
    
    def __init__(self):
        # Service detection heuristics
        self.service_directory_patterns = [
            r'^services?/([^/]+)/?',
            r'^apps?/([^/]+)/?',
            r'^microservices?/([^/]+)/?',
            r'^packages?/([^/]+)/?',
        ]
        
        self.entry_point_files = [
            'main.py',
            'app.py',
            'server.py',
            '__main__.py',
            'index.js',
            'index.ts',
            'main.go',
            'Main.java',
            'main.rs',
        ]
        
        self.deployment_indicators = [
            'Dockerfile',
            'docker-compose.yml',
            'deployment.yaml',
            'service.yaml',
            'Chart.yaml',
        ]
        
        logger.info("ServiceBoundaryDetector initialized")
    
    async def detect_services(
        self,
        files: List[Dict],
        repo_path: str,
        dependency_graph: Optional[Dict] = None
    ) -> ServiceMap:
        """
        Detect microservices in repository.
        
        Args:
            files: List of file information
            repo_path: Repository root path
            dependency_graph: Optional dependency graph
        
        Returns:
            ServiceMap with all detected services
        """
        logger.info(f"🔍 Detecting service boundaries in {len(files)} files...")
        
        # Strategy 1: Directory-based detection
        dir_services = await self._detect_by_directory(files, repo_path)
        
        # Strategy 2: Entry point detection (for monorepos without service dirs)
        if not dir_services:
            dir_services = await self._detect_by_entry_points(files, repo_path)
        
        # Strategy 3: Docker-based detection
        docker_services = await self._detect_by_docker(files, repo_path)
        
        # Merge strategies
        services = self._merge_service_detections(dir_services, docker_services)
        
        # If still no services, treat as single service
        if not services:
            services = [await self._create_single_service(files, repo_path)]
        
        # Enrich service information
        for service in services:
            await self._enrich_service(service, files, repo_path)
        
        # Build dependency map
        dependencies = await self._build_dependency_map(
            services,
            dependency_graph
        ) if dependency_graph else {}
        
        service_map = ServiceMap(
            services=services,
            dependencies=dependencies,
            service_count=len(services)
        )
        
        logger.info(f"✅ Detected {len(services)} service(s)")
        
        return service_map
    
    async def _detect_by_directory(
        self,
        files: List[Dict],
        repo_path: str
    ) -> List[Service]:
        """Detect services by directory structure."""
        service_dirs = defaultdict(list)
        
        for file_info in files:
            path = file_info.get('path') or file_info.get('relative_path', '')
            
            for pattern in self.service_directory_patterns:
                match = re.match(pattern, path)
                if match:
                    service_name = match.group(1)
                    service_dirs[service_name].append(path)
                    break
        
        services = []
        for service_name, service_files in service_dirs.items():
            if len(service_files) >= 3:  # Minimum files for a service
                service = Service(
                    name=service_name,
                    root_path=f"services/{service_name}",  # Normalized
                    files=service_files,
                    file_count=len(service_files),
                    entry_point=None,
                    internal_dependencies=[],
                    external_dependencies=[],
                    languages=[],
                    frameworks=[],
                    databases=[],
                    has_api=False,
                    endpoints=[],
                    has_dockerfile=False,
                    has_k8s_config=False
                )
                services.append(service)
        
        return services
    
    async def _detect_by_entry_points(
        self,
        files: List[Dict],
        repo_path: str
    ) -> List[Service]:
        """Detect services by entry points."""
        entry_points = []
        
        for file_info in files:
            path = file_info.get('path') or file_info.get('relative_path', '')
            filename = Path(path).name
            
            if filename in self.entry_point_files:
                entry_points.append(path)
        
        # Group by parent directory
        service_dirs = defaultdict(list)
        for ep in entry_points:
            parent = str(Path(ep).parent)
            if parent and parent != '.':
                service_dirs[parent].append(ep)
        
        services = []
        for root_path, eps in service_dirs.items():
            service_name = Path(root_path).name
            service_files = [
                f.get('path') or f.get('relative_path', '')
                for f in files
                if (f.get('path') or f.get('relative_path', '')).startswith(root_path)
            ]
            
            if service_files:
                service = Service(
                    name=service_name,
                    root_path=root_path,
                    files=service_files,
                    file_count=len(service_files),
                    entry_point=eps[0] if eps else None,
                    internal_dependencies=[],
                    external_dependencies=[],
                    languages=[],
                    frameworks=[],
                    databases=[],
                    has_api=False,
                    endpoints=[],
                    has_dockerfile=False,
                    has_k8s_config=False
                )
                services.append(service)
        
        return services
    
    async def _detect_by_docker(
        self,
        files: List[Dict],
        repo_path: str
    ) -> List[Service]:
        """Detect services by Docker configurations."""
        services = []
        
        # Look for docker-compose.yml
        compose_files = [
            f.get('path') or f.get('relative_path', '')
            for f in files
            if 'docker-compose' in (f.get('path') or f.get('relative_path', ''))
        ]
        
        if compose_files:
            # Parse docker-compose to extract services
            # Simplified: Just detect that Docker is used
            pass
        
        # Look for Dockerfiles in subdirectories
        dockerfiles = [
            f.get('path') or f.get('relative_path', '')
            for f in files
            if 'Dockerfile' in (f.get('path') or f.get('relative_path', ''))
        ]
        
        for dockerfile in dockerfiles:
            parent = str(Path(dockerfile).parent)
            if parent and parent != '.':
                service_name = Path(parent).name
                # Mark this as a service directory
                # Will be merged with other detections
        
        return services
    
    def _merge_service_detections(
        self,
        dir_services: List[Service],
        docker_services: List[Service]
    ) -> List[Service]:
        """Merge service detections from different strategies."""
        # For now, prioritize directory-based detection
        return dir_services if dir_services else docker_services
    
    async def _create_single_service(
        self,
        files: List[Dict],
        repo_path: str
    ) -> Service:
        """Create a single service for monolithic repos."""
        repo_name = Path(repo_path).name
        
        return Service(
            name=repo_name,
            root_path='.',
            files=[f.get('path') or f.get('relative_path', '') for f in files],
            file_count=len(files),
            entry_point=None,
            internal_dependencies=[],
            external_dependencies=[],
            languages=[],
            frameworks=[],
            databases=[],
            has_api=False,
            endpoints=[],
            has_dockerfile=False,
            has_k8s_config=False
        )
    
    async def _enrich_service(
        self,
        service: Service,
        all_files: List[Dict],
        repo_path: str
    ) -> None:
        """Enrich service with additional information."""
        service_files = [
            f for f in all_files
            if (f.get('path') or f.get('relative_path', '')).startswith(service.root_path)
        ]
        
        # Detect languages
        languages = set()
        for f in service_files:
            lang = f.get('language', '').lower()
            if lang and lang != 'unknown':
                languages.add(lang)
        service.languages = list(languages)
        
        # Find entry point if not set
        if not service.entry_point:
            for f in service_files:
                path = f.get('path') or f.get('relative_path', '')
                filename = Path(path).name
                if filename in self.entry_point_files:
                    service.entry_point = path
                    break
        
        # Check for Docker
        for f in service_files:
            path = f.get('path') or f.get('relative_path', '')
            if 'Dockerfile' in path:
                service.has_dockerfile = True
            if any(k8s in path for k8s in ['deployment.yaml', 'service.yaml', 'k8s/']):
                service.has_k8s_config = True
        
        # Check for API (simplified)
        for f in service_files:
            if f.get('is_code', False):
                path = f.get('path') or f.get('relative_path', '')
                try:
                    full_path = Path(repo_path) / path
                    if full_path.exists() and full_path.stat().st_size < 100_000:
                        content = full_path.read_text(encoding='utf-8', errors='ignore')
                        
                        # Detect API frameworks
                        api_patterns = [
                            r'@app\.route',
                            r'@router\.',
                            r'@get\(',
                            r'@post\(',
                            r'FastAPI\(',
                            r'express\(\)',
                        ]
                        
                        for pattern in api_patterns:
                            if re.search(pattern, content):
                                service.has_api = True
                                break
                        
                        if service.has_api:
                            break
                
                except Exception as e:
                    logger.debug(f"Error enriching service {service.name}: {e}")
    
    async def _build_dependency_map(
        self,
        services: List[Service],
        dependency_graph: Dict
    ) -> Dict[str, List[str]]:
        """Build service-to-service dependency map."""
        dependencies = defaultdict(list)
        
        if not dependency_graph:
            return dict(dependencies)
        
        edges = dependency_graph.get('edges', [])
        
        # Map files to services
        file_to_service = {}
        for service in services:
            for file_path in service.files:
                file_to_service[file_path] = service.name
        
        # Build service dependencies
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            
            if source and target:
                source_service = file_to_service.get(source)
                target_service = file_to_service.get(target)
                
                if (source_service and target_service and
                    source_service != target_service and
                    target_service not in dependencies[source_service]):
                    dependencies[source_service].append(target_service)
        
        return dict(dependencies)
    
    async def get_service_by_name(
        self,
        service_map: ServiceMap,
        name: str
    ) -> Optional[Service]:
        """Get service by name."""
        for service in service_map.services:
            if service.name == name:
                return service
        return None
    
    async def get_dependent_services(
        self,
        service_map: ServiceMap,
        service_name: str
    ) -> List[str]:
        """Get services that depend on this service."""
        dependents = []
        for svc, deps in service_map.dependencies.items():
            if service_name in deps:
                dependents.append(svc)
        return dependents


# Singleton
_service_detector_instance = None

def get_service_detector() -> ServiceBoundaryDetector:
    """Get singleton service boundary detector instance."""
    global _service_detector_instance
    if _service_detector_instance is None:
        _service_detector_instance = ServiceBoundaryDetector()
    return _service_detector_instance

