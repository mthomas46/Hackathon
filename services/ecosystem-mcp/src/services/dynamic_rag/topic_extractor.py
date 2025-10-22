"""
Topic Extractor (Phase 6.1)

Extracts topics, entities, and concepts from natural language queries using NLP.
"""

import logging
import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TopicType(Enum):
    """Types of topics that can be extracted."""
    ENDPOINT = "endpoint"
    PARAMETER = "parameter"
    SERVICE = "service"
    TECHNOLOGY = "technology"
    CONCEPT = "concept"
    FILE_PATH = "file_path"


@dataclass
class ExtractedTopic:
    """A single extracted topic with metadata."""
    value: str
    type: TopicType
    confidence: float
    context: Optional[str] = None


@dataclass
class ExtractedTopics:
    """Collection of extracted topics from a query."""
    endpoints: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    concepts: List[str] = field(default_factory=list)
    file_paths: List[str] = field(default_factory=list)
    all_topics: List[ExtractedTopic] = field(default_factory=list)
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'endpoints': self.endpoints,
            'parameters': self.parameters,
            'services': self.services,
            'technologies': self.technologies,
            'concepts': self.concepts,
            'file_paths': self.file_paths,
            'topic_count': len(self.all_topics),
            'confidence': self.confidence
        }


class TopicExtractor:
    """
    Extracts topics and entities from natural language queries.
    
    Features:
    - Endpoint detection (e.g., /api/auth)
    - Parameter extraction (e.g., refresh_token)
    - Service identification (e.g., authentication)
    - Technology recognition (e.g., JWT, OAuth)
    - Concept extraction (e.g., token refresh)
    - File path detection (e.g., src/api/auth.py)
    - Confidence scoring
    """
    
    # Known technologies/frameworks
    KNOWN_TECHNOLOGIES = {
        'jwt', 'oauth', 'oauth2', 'rest', 'graphql', 'grpc',
        'postgres', 'postgresql', 'redis', 'mongodb', 'mysql',
        'docker', 'kubernetes', 'k8s',
        'fastapi', 'flask', 'django', 'express', 'react', 'vue',
        'python', 'javascript', 'typescript', 'go', 'rust', 'java',
        'http', 'https', 'websocket', 'sse',
        'json', 'xml', 'yaml', 'protobuf'
    }
    
    # Common API-related terms
    API_TERMS = {
        'endpoint', 'route', 'api', 'rest', 'graphql',
        'request', 'response', 'method', 'header', 'body',
        'get', 'post', 'put', 'patch', 'delete'
    }
    
    # Authentication/authorization terms
    AUTH_TERMS = {
        'auth', 'authentication', 'authorization', 'login', 'logout',
        'token', 'jwt', 'session', 'cookie', 'oauth', 'refresh',
        'access', 'permission', 'role', 'user', 'credential'
    }
    
    # Service-related terms
    SERVICE_TERMS = {
        'service', 'microservice', 'api', 'backend', 'frontend',
        'database', 'cache', 'queue', 'worker', 'scheduler'
    }
    
    def __init__(self):
        logger.info("TopicExtractor initialized")
    
    def extract(self, query: str) -> ExtractedTopics:
        """
        Extract topics from a natural language query.
        
        Args:
            query: Natural language query
        
        Returns:
            ExtractedTopics with all identified topics
        """
        logger.info(f"Extracting topics from query: {query[:100]}...")
        
        # Normalize query
        query_lower = query.lower()
        
        # Extract different topic types
        endpoints = self._extract_endpoints(query)
        parameters = self._extract_parameters(query, query_lower)
        services = self._extract_services(query_lower)
        technologies = self._extract_technologies(query_lower)
        file_paths = self._extract_file_paths(query)
        concepts = self._extract_concepts(query_lower)
        
        # Build all topics list with confidence
        all_topics = []
        
        for endpoint in endpoints:
            all_topics.append(ExtractedTopic(
                value=endpoint,
                type=TopicType.ENDPOINT,
                confidence=0.95
            ))
        
        for param in parameters:
            all_topics.append(ExtractedTopic(
                value=param,
                type=TopicType.PARAMETER,
                confidence=0.85
            ))
        
        for service in services:
            all_topics.append(ExtractedTopic(
                value=service,
                type=TopicType.SERVICE,
                confidence=0.75
            ))
        
        for tech in technologies:
            all_topics.append(ExtractedTopic(
                value=tech,
                type=TopicType.TECHNOLOGY,
                confidence=0.80
            ))
        
        for path in file_paths:
            all_topics.append(ExtractedTopic(
                value=path,
                type=TopicType.FILE_PATH,
                confidence=0.90
            ))
        
        for concept in concepts:
            all_topics.append(ExtractedTopic(
                value=concept,
                type=TopicType.CONCEPT,
                confidence=0.65
            ))
        
        # Calculate overall confidence
        overall_confidence = self._calculate_confidence(all_topics)
        
        result = ExtractedTopics(
            endpoints=endpoints,
            parameters=parameters,
            services=services,
            technologies=technologies,
            concepts=concepts,
            file_paths=file_paths,
            all_topics=all_topics,
            confidence=overall_confidence
        )
        
        logger.info(f"✅ Extracted {len(all_topics)} topics with {overall_confidence:.2f} confidence")
        
        return result
    
    def _extract_endpoints(self, query: str) -> List[str]:
        """Extract API endpoints from query."""
        endpoints = []
        
        # Pattern: /api/something or /v1/something
        pattern = r'/[a-z0-9_/-]+'
        matches = re.findall(pattern, query)
        
        for match in matches:
            # Filter out common false positives
            if not match.endswith('/'):
                endpoints.append(match)
        
        return list(set(endpoints))
    
    def _extract_parameters(self, query: str, query_lower: str) -> List[str]:
        """Extract parameter names from query."""
        parameters = []
        
        # Pattern 1: 'parameter_name' or "parameter_name"
        pattern1 = r"['\"]([a-z_][a-z0-9_]*)['\"]"
        matches1 = re.findall(pattern1, query_lower)
        parameters.extend(matches1)
        
        # Pattern 2: snake_case or camelCase parameters
        # Look for words that look like parameters
        words = query.split()
        for word in words:
            # Clean word
            clean = word.strip('.,!?()[]{}:;')
            
            # Check if it looks like a parameter
            if '_' in clean and clean.replace('_', '').isalnum():
                parameters.append(clean.lower())
            elif re.match(r'^[a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*$', clean):
                # camelCase
                parameters.append(clean)
        
        # Pattern 3: Common parameter patterns
        param_keywords = ['token', 'key', 'id', 'name', 'type', 'status']
        for keyword in param_keywords:
            if keyword in query_lower:
                # Look for compound parameters
                for word in words:
                    clean = word.strip('.,!?()[]{}:;').lower()
                    if keyword in clean:
                        parameters.append(clean)
        
        return list(set(parameters))
    
    def _extract_services(self, query_lower: str) -> List[str]:
        """Extract service names from query."""
        services = []
        
        # Check for service-related terms
        words = query_lower.split()
        
        for i, word in enumerate(words):
            clean_word = word.strip('.,!?()[]{}:;')
            
            # Pattern: "X service"
            if clean_word in self.SERVICE_TERMS:
                if i > 0:
                    prev_word = words[i-1].strip('.,!?()[]{}:;')
                    if prev_word.isalpha() and len(prev_word) > 2:
                        services.append(prev_word)
            
            # Known service patterns
            if 'auth' in clean_word and len(clean_word) > 4:
                services.append(clean_word)
            
            # Check for microservice naming
            if clean_word.endswith('-service') or clean_word.endswith('_service'):
                services.append(clean_word)
        
        # Add auth-related services
        if any(term in query_lower for term in self.AUTH_TERMS):
            services.append('authentication')
        
        return list(set(services))
    
    def _extract_technologies(self, query_lower: str) -> List[str]:
        """Extract technology names from query."""
        technologies = []
        
        words = query_lower.split()
        
        for word in words:
            clean_word = word.strip('.,!?()[]{}:;')
            
            # Check against known technologies
            if clean_word in self.KNOWN_TECHNOLOGIES:
                technologies.append(clean_word)
            
            # Check for technology variations
            for tech in self.KNOWN_TECHNOLOGIES:
                if tech in clean_word and len(clean_word) < len(tech) + 5:
                    technologies.append(tech)
        
        return list(set(technologies))
    
    def _extract_file_paths(self, query: str) -> List[str]:
        """Extract file paths from query."""
        file_paths = []
        
        # Pattern: src/path/to/file.py or similar
        pattern = r'[a-z_][a-z0-9_/.-]*\.[a-z]{2,4}'
        matches = re.findall(pattern, query.lower())
        
        for match in matches:
            # Filter out URLs
            if '://' not in match:
                file_paths.append(match)
        
        return list(set(file_paths))
    
    def _extract_concepts(self, query_lower: str) -> List[str]:
        """Extract conceptual topics from query."""
        concepts = []
        
        # Common multi-word concepts
        concept_patterns = [
            r'token\s+refresh',
            r'session\s+management',
            r'access\s+control',
            r'rate\s+limiting',
            r'api\s+versioning',
            r'error\s+handling',
            r'request\s+validation',
            r'response\s+format',
            r'authentication\s+flow',
            r'authorization\s+flow',
        ]
        
        for pattern in concept_patterns:
            if re.search(pattern, query_lower):
                concept = pattern.replace(r'\s+', ' ')
                concepts.append(concept)
        
        # Question-based concepts
        if 'why' in query_lower:
            concepts.append('rationale')
            concepts.append('design decision')
        
        if 'how' in query_lower:
            concepts.append('implementation')
            concepts.append('workflow')
        
        if 'when' in query_lower:
            concepts.append('timeline')
            concepts.append('history')
        
        return list(set(concepts))
    
    def _calculate_confidence(self, topics: List[ExtractedTopic]) -> float:
        """Calculate overall confidence score."""
        if not topics:
            return 0.0
        
        # Weight by topic type importance
        weights = {
            TopicType.ENDPOINT: 1.0,
            TopicType.FILE_PATH: 0.9,
            TopicType.PARAMETER: 0.8,
            TopicType.TECHNOLOGY: 0.7,
            TopicType.SERVICE: 0.7,
            TopicType.CONCEPT: 0.5
        }
        
        total_weighted_confidence = 0.0
        total_weight = 0.0
        
        for topic in topics:
            weight = weights.get(topic.type, 0.5)
            total_weighted_confidence += topic.confidence * weight
            total_weight += weight
        
        return total_weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def get_search_terms(self, extracted_topics: ExtractedTopics) -> List[str]:
        """
        Convert extracted topics to search terms for document finding.
        
        Args:
            extracted_topics: Extracted topics
        
        Returns:
            List of search terms
        """
        search_terms = []
        
        # Add all topic values
        search_terms.extend(extracted_topics.endpoints)
        search_terms.extend(extracted_topics.parameters)
        search_terms.extend(extracted_topics.services)
        search_terms.extend(extracted_topics.technologies)
        search_terms.extend(extracted_topics.file_paths)
        search_terms.extend(extracted_topics.concepts)
        
        return search_terms

