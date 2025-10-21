"""
Architecture Detector

Detects architectural patterns and styles in a repository.
"""

import logging
import re
from typing import List, Dict, Set, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ArchitecturePattern:
    """Detected architecture pattern."""
    name: str  # e.g., 'microservices', 'mvc', 'layered'
    confidence: float  # 0.0 to 1.0
    evidence: List[str]  # Supporting evidence
    components: List[str]  # Key components
    description: str


@dataclass
class ArchitectureAnalysis:
    """Complete architecture analysis."""
    primary_pattern: Optional[ArchitecturePattern]
    secondary_patterns: List[ArchitecturePattern]
    layers: List[str]  # Detected layers
    entry_points: List[str]  # Main entry points
    dependencies_flow: str  # 'top-down', 'bottom-up', 'bidirectional'
    modularity_score: float  # 0.0 to 1.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        result = asdict(self)
        if self.primary_pattern:
            result['primary_pattern'] = asdict(self.primary_pattern)
        result['secondary_patterns'] = [asdict(p) for p in self.secondary_patterns]
        return result


class ArchitectureDetector:
    """
    Detects architectural patterns in a repository.
    
    Patterns detected:
    - Microservices
    - Monolithic
    - Layered (N-tier)
    - MVC/MVT
    - Hexagonal (Ports & Adapters)
    - Event-driven
    - Pipeline
    - Client-Server
    """
    
    def __init__(self):
        # Pattern detection rules
        self.pattern_rules = {
            'microservices': {
                'directory_patterns': [
                    r'services?/[^/]+/',
                    r'apps?/[^/]+/',
                    r'microservices?/',
                ],
                'file_indicators': [
                    'docker-compose.yml',
                    'kubernetes/',
                    'k8s/',
                    'service.yaml',
                ],
                'code_patterns': [
                    r'@app\.route',
                    r'@router\.',
                    r'ServiceRegistry',
                    r'service\.discovery',
                ],
            },
            'mvc': {
                'directory_patterns': [
                    r'models?/',
                    r'views?/',
                    r'controllers?/',
                    r'templates?/',
                ],
                'file_indicators': [
                    'models.py',
                    'views.py',
                    'controllers.py',
                ],
                'code_patterns': [
                    r'class.*Model',
                    r'class.*View',
                    r'class.*Controller',
                ],
            },
            'layered': {
                'directory_patterns': [
                    r'presentation/',
                    r'business/',
                    r'data/',
                    r'api/',
                    r'domain/',
                    r'infrastructure/',
                    r'application/',
                ],
                'file_indicators': [
                    'api/',
                    'core/',
                    'infrastructure/',
                ],
                'code_patterns': [],
            },
            'hexagonal': {
                'directory_patterns': [
                    r'domain/',
                    r'adapters?/',
                    r'ports?/',
                    r'infrastructure/',
                ],
                'file_indicators': [
                    'ports/',
                    'adapters/',
                ],
                'code_patterns': [
                    r'class.*Port',
                    r'class.*Adapter',
                ],
            },
            'event_driven': {
                'directory_patterns': [
                    r'events?/',
                    r'handlers?/',
                    r'subscribers?/',
                    r'publishers?/',
                ],
                'file_indicators': [
                    'events.py',
                    'event_bus.py',
                ],
                'code_patterns': [
                    r'@event_handler',
                    r'publish\(',
                    r'subscribe\(',
                    r'EventBus',
                    r'MessageQueue',
                ],
            },
            'pipeline': {
                'directory_patterns': [
                    r'pipeline/',
                    r'stages?/',
                    r'processors?/',
                ],
                'file_indicators': [
                    'pipeline.py',
                    'dag.py',
                ],
                'code_patterns': [
                    r'Pipeline',
                    r'\.pipe\(',
                    r'\.process\(',
                    r'Stage',
                ],
            },
        }
        
        # Layer detection patterns
        self.layer_patterns = {
            'presentation': [r'ui/', r'frontend/', r'views?/', r'templates?/'],
            'api': [r'api/', r'routes?/', r'endpoints?/', r'controllers?/'],
            'business': [r'business/', r'domain/', r'core/', r'services?/'],
            'data': [r'data/', r'persistence/', r'repositories?/', r'database/'],
            'infrastructure': [r'infrastructure/', r'adapters?/', r'external/'],
        }
        
        logger.info("ArchitectureDetector initialized")
    
    async def detect_architecture(
        self,
        files: List[Dict],
        repo_path: str,
        dependency_graph: Optional[Dict] = None
    ) -> ArchitectureAnalysis:
        """
        Detect architectural patterns.
        
        Args:
            files: List of file information
            repo_path: Repository root path
            dependency_graph: Optional dependency graph from DependencyAnalyzer
        
        Returns:
            ArchitectureAnalysis with detected patterns
        """
        logger.info(f"🏗️ Detecting architecture patterns in {len(files)} files...")
        
        # Collect directory structure
        directories = self._extract_directories(files)
        
        # Detect patterns
        patterns = []
        for pattern_name, rules in self.pattern_rules.items():
            score, evidence = await self._check_pattern(
                pattern_name,
                rules,
                directories,
                files,
                repo_path
            )
            
            if score > 0.3:  # Confidence threshold
                pattern = ArchitecturePattern(
                    name=pattern_name,
                    confidence=score,
                    evidence=evidence,
                    components=await self._extract_components(pattern_name, directories),
                    description=self._get_pattern_description(pattern_name)
                )
                patterns.append(pattern)
        
        # Sort by confidence
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        
        # Detect layers
        layers = await self._detect_layers(directories)
        
        # Find entry points
        entry_points = await self._find_entry_points(files, repo_path)
        
        # Analyze dependency flow
        deps_flow = await self._analyze_dependency_flow(
            dependency_graph,
            layers
        ) if dependency_graph else 'unknown'
        
        # Calculate modularity
        modularity = await self._calculate_modularity(
            files,
            dependency_graph
        ) if dependency_graph else 0.5
        
        analysis = ArchitectureAnalysis(
            primary_pattern=patterns[0] if patterns else None,
            secondary_patterns=patterns[1:3],  # Top 2 secondary
            layers=layers,
            entry_points=entry_points,
            dependencies_flow=deps_flow,
            modularity_score=modularity
        )
        
        logger.info(
            f"✅ Architecture detection complete: "
            f"Primary={analysis.primary_pattern.name if analysis.primary_pattern else 'unknown'}, "
            f"Layers={len(layers)}"
        )
        
        return analysis
    
    def _extract_directories(self, files: List[Dict]) -> Set[str]:
        """Extract unique directories from files."""
        directories = set()
        for file_info in files:
            path = file_info.get('path') or file_info.get('relative_path', '')
            if '/' in path:
                parts = path.split('/')[:-1]  # Exclude filename
                for i in range(len(parts)):
                    directories.add('/'.join(parts[:i+1]) + '/')
        return directories
    
    async def _check_pattern(
        self,
        pattern_name: str,
        rules: Dict,
        directories: Set[str],
        files: List[Dict],
        repo_path: str
    ) -> tuple[float, List[str]]:
        """
        Check if pattern matches.
        
        Returns:
            (confidence_score, evidence_list)
        """
        evidence = []
        score = 0.0
        max_score = 0.0
        
        # Check directory patterns
        dir_patterns = rules.get('directory_patterns', [])
        if dir_patterns:
            max_score += 0.4
            matches = []
            for pattern in dir_patterns:
                for directory in directories:
                    if re.search(pattern, directory):
                        matches.append(directory)
            
            if matches:
                score += 0.4 * min(len(matches) / len(dir_patterns), 1.0)
                evidence.append(f"Directory structure: {', '.join(list(set(matches))[:3])}")
        
        # Check file indicators
        file_indicators = rules.get('file_indicators', [])
        if file_indicators:
            max_score += 0.3
            matches = []
            for indicator in file_indicators:
                for file_info in files:
                    path = file_info.get('path') or file_info.get('relative_path', '')
                    if indicator in path:
                        matches.append(indicator)
                        break
            
            if matches:
                score += 0.3 * min(len(matches) / len(file_indicators), 1.0)
                evidence.append(f"Key files: {', '.join(matches)}")
        
        # Check code patterns
        code_patterns = rules.get('code_patterns', [])
        if code_patterns:
            max_score += 0.3
            matches = await self._scan_code_patterns(code_patterns, files, repo_path)
            if matches:
                score += 0.3 * min(len(matches) / len(code_patterns), 1.0)
                evidence.append(f"Code patterns: {', '.join(list(matches)[:3])}")
        
        # Normalize score
        if max_score > 0:
            score = score / max_score
        
        return score, evidence
    
    async def _scan_code_patterns(
        self,
        patterns: List[str],
        files: List[Dict],
        repo_path: str
    ) -> Set[str]:
        """Scan code files for patterns."""
        matches = set()
        
        # Sample files to avoid scanning everything
        sample_size = min(100, len(files))
        sampled_files = [f for f in files if f.get('is_code', False)][:sample_size]
        
        for file_info in sampled_files:
            path = file_info.get('path') or file_info.get('relative_path', '')
            try:
                full_path = Path(repo_path) / path
                if not full_path.exists() or full_path.stat().st_size > 100_000:
                    continue
                
                content = full_path.read_text(encoding='utf-8', errors='ignore')
                
                for pattern in patterns:
                    if re.search(pattern, content):
                        matches.add(pattern)
            
            except Exception as e:
                logger.debug(f"Error scanning {path}: {e}")
        
        return matches
    
    async def _extract_components(
        self,
        pattern_name: str,
        directories: Set[str]
    ) -> List[str]:
        """Extract key components for pattern."""
        if pattern_name == 'microservices':
            # Look for service directories
            services = []
            for directory in directories:
                if re.search(r'services?/([^/]+)/', directory):
                    match = re.search(r'services?/([^/]+)/', directory)
                    if match:
                        services.append(match.group(1))
            return list(set(services))[:10]
        
        elif pattern_name in ['mvc', 'layered']:
            # Return layer directories
            return [d.rstrip('/') for d in directories if any(
                layer in d for layer in ['models', 'views', 'controllers', 'api', 'domain']
            )][:10]
        
        return []
    
    def _get_pattern_description(self, pattern_name: str) -> str:
        """Get pattern description."""
        descriptions = {
            'microservices': 'Independent, loosely-coupled services communicating via APIs',
            'mvc': 'Model-View-Controller pattern separating data, presentation, and logic',
            'layered': 'N-tier architecture with distinct horizontal layers',
            'hexagonal': 'Ports and Adapters pattern isolating business logic',
            'event_driven': 'Event-based communication between components',
            'pipeline': 'Sequential data processing through stages',
        }
        return descriptions.get(pattern_name, 'Unknown pattern')
    
    async def _detect_layers(self, directories: Set[str]) -> List[str]:
        """Detect architectural layers."""
        detected_layers = []
        
        for layer_name, patterns in self.layer_patterns.items():
            for pattern in patterns:
                if any(re.search(pattern, d) for d in directories):
                    detected_layers.append(layer_name)
                    break
        
        return detected_layers
    
    async def _find_entry_points(
        self,
        files: List[Dict],
        repo_path: str
    ) -> List[str]:
        """Find main entry points."""
        entry_point_patterns = [
            r'main\.py$',
            r'app\.py$',
            r'server\.py$',
            r'index\.js$',
            r'index\.ts$',
            r'main\.go$',
            r'Main\.java$',
            r'main\.rs$',
        ]
        
        entry_points = []
        for file_info in files:
            path = file_info.get('path') or file_info.get('relative_path', '')
            for pattern in entry_point_patterns:
                if re.search(pattern, path):
                    entry_points.append(path)
                    break
        
        return entry_points[:10]
    
    async def _analyze_dependency_flow(
        self,
        dependency_graph: Dict,
        layers: List[str]
    ) -> str:
        """Analyze dependency flow direction."""
        # Simplified heuristic
        if not dependency_graph or not layers:
            return 'unknown'
        
        # Check if dependencies follow layer order
        # This is a simplified version
        return 'layered'  # Placeholder
    
    async def _calculate_modularity(
        self,
        files: List[Dict],
        dependency_graph: Dict
    ) -> float:
        """Calculate modularity score."""
        if not dependency_graph:
            return 0.5
        
        # Simplified calculation based on coupling
        nodes = dependency_graph.get('nodes', [])
        edges = dependency_graph.get('edges', [])
        
        if not nodes:
            return 0.5
        
        # Average dependencies per module
        avg_deps = len(edges) / len(nodes) if nodes else 0
        
        # Lower is better (loose coupling)
        # Normalize to 0-1 scale (inverse)
        if avg_deps == 0:
            return 1.0
        
        score = max(0.0, 1.0 - (avg_deps / 10.0))
        return min(1.0, score)


# Singleton
_architecture_detector_instance = None

def get_architecture_detector() -> ArchitectureDetector:
    """Get singleton architecture detector instance."""
    global _architecture_detector_instance
    if _architecture_detector_instance is None:
        _architecture_detector_instance = ArchitectureDetector()
    return _architecture_detector_instance

