"""
Corpus analyzer for intelligent contextual tagging.

Analyzes a corpus of documents to extract:
- Named entities (people, organizations, locations, events)
- Noun phrases (topics, concepts)
- Co-occurrence relationships
- Knowledge graph structure
- Contextual tags based on entity importance
"""
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Any, Optional
from collections import Counter, defaultdict
import re

from ingestion.models import NormalizedDocument

logger = logging.getLogger(__name__)


@dataclass
class CorpusAnalysisConfig:
    """Configuration for corpus analysis."""
    
    # Sampling
    sample_size: int = 50  # Number of documents to analyze
    
    # Entity extraction
    min_entity_frequency: int = 3  # Minimum occurrences to consider entity
    max_entities_per_type: int = 50  # Max entities per type to track
    
    # Noun phrase extraction
    extract_noun_phrases: bool = True
    min_phrase_frequency: int = 2
    max_phrases: int = 100
    
    # Relationship extraction
    extract_relationships: bool = True
    co_occurrence_window: int = 50  # Character window for co-occurrence
    
    # Knowledge graph
    build_knowledge_graph: bool = True
    min_edge_weight: int = 2  # Minimum co-occurrences for edge
    
    # Tag generation
    max_contextual_tags: int = 100  # Total contextual tags to generate


@dataclass
class CorpusAnalysisResult:
    """Result of corpus analysis."""
    
    # Entities by type
    entities_by_type: Dict[str, List[Tuple[str, int]]] = field(default_factory=dict)
    
    # Noun phrases (topics)
    common_topics: List[Tuple[str, int]] = field(default_factory=list)
    
    # Relationships (co-occurrences)
    relationships: List[Tuple[str, str, int]] = field(default_factory=list)
    
    # Knowledge graph
    knowledge_graph: Optional[Dict[str, Any]] = None
    
    # Statistics
    documents_analyzed: int = 0
    total_entities: int = 0
    total_relationships: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return {
            'entities_by_type': {
                entity_type: [(entity, count) for entity, count in entities]
                for entity_type, entities in self.entities_by_type.items()
            },
            'common_topics': [(topic, count) for topic, count in self.common_topics],
            'relationships': [(e1, e2, count) for e1, e2, count in self.relationships],
            'knowledge_graph': self.knowledge_graph,
            'documents_analyzed': self.documents_analyzed,
            'total_entities': self.total_entities,
            'total_relationships': self.total_relationships
        }


class CorpusAnalyzer:
    """
    Analyze a corpus of documents to extract entities, relationships, and generate
    contextual tags.
    
    Uses lightweight NLP techniques (regex patterns, frequency analysis) instead of
    heavy NLP libraries for speed and simplicity.
    """
    
    # Entity type patterns
    ENTITY_PATTERNS = {
        'PERSON': [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # FirstName LastName
            r'\b(?:Emperor|Lord|Captain|Commander|General|Admiral)\s+[A-Z][a-z]+\b',
        ],
        'ORGANIZATION': [
            r'\b[A-Z][a-z]+\s+(?:Legion|Chapter|Company|Corps|Army|Fleet)\b',
            r'\b(?:Space Marines?|Imperial\s+Guard|Chaos|Imperium)\b',
        ],
        'LOCATION': [
            r'\b(?:Planet|System|Sector)\s+[A-Z][a-z]+\b',
            r'\bTerra\b',
            r'\b[A-Z][a-z]+\s+(?:Prime|System|Sector)\b',
        ],
        'EVENT': [
            r'\b(?:Great\s+Crusade|Heresy|Siege|Battle|War)\s+(?:of\s+)?[A-Z][a-z]+\b',
            r'\b[A-Z][a-z]+\s+(?:Campaign|Crusade|Heresy)\b',
        ]
    }
    
    def __init__(self, config: Optional[CorpusAnalysisConfig] = None):
        """
        Initialize corpus analyzer.
        
        Args:
            config: Configuration for analysis
        """
        self.config = config or CorpusAnalysisConfig()
        logger.info(f"CorpusAnalyzer initialized (sample_size={self.config.sample_size})")
    
    async def analyze(
        self,
        documents: List[NormalizedDocument]
    ) -> CorpusAnalysisResult:
        """
        Analyze a corpus of documents.
        
        Args:
            documents: List of normalized documents to analyze
        
        Returns:
            CorpusAnalysisResult with entities, topics, relationships
        """
        logger.info(f"📊 Starting corpus analysis on {len(documents)} documents...")
        
        # Sample documents if needed
        docs_to_analyze = self._sample_documents(documents)
        logger.info(f"   Analyzing {len(docs_to_analyze)} documents")
        
        # Extract entities
        logger.info("   Step 1/5: Extracting entities...")
        entities_by_type = self._extract_entities(docs_to_analyze)
        logger.info(f"   ✓ Found {sum(len(ents) for ents in entities_by_type.values())} unique entities")
        
        # Extract noun phrases (topics)
        logger.info("   Step 2/5: Extracting topics...")
        topics = self._extract_topics(docs_to_analyze)
        logger.info(f"   ✓ Found {len(topics)} common topics")
        
        # Extract relationships
        logger.info("   Step 3/5: Extracting relationships...")
        relationships = self._extract_relationships(docs_to_analyze, entities_by_type)
        logger.info(f"   ✓ Found {len(relationships)} relationships")
        
        # Build knowledge graph
        knowledge_graph = None
        if self.config.build_knowledge_graph:
            logger.info("   Step 4/5: Building knowledge graph...")
            knowledge_graph = self._build_knowledge_graph(entities_by_type, relationships)
            logger.info(f"   ✓ Graph: {knowledge_graph['node_count']} nodes, {knowledge_graph['edge_count']} edges")
        
        # Create result
        result = CorpusAnalysisResult(
            entities_by_type=entities_by_type,
            common_topics=topics,
            relationships=relationships,
            knowledge_graph=knowledge_graph,
            documents_analyzed=len(docs_to_analyze),
            total_entities=sum(len(ents) for ents in entities_by_type.values()),
            total_relationships=len(relationships)
        )
        
        logger.info(f"✅ Corpus analysis complete!")
        logger.info(f"   Documents: {result.documents_analyzed}")
        logger.info(f"   Entities: {result.total_entities}")
        logger.info(f"   Relationships: {result.total_relationships}")
        
        return result
    
    def _sample_documents(
        self,
        documents: List[NormalizedDocument]
    ) -> List[NormalizedDocument]:
        """Sample documents if corpus is too large."""
        if len(documents) <= self.config.sample_size:
            return documents
        
        # Take first N documents (could be randomized if needed)
        return documents[:self.config.sample_size]
    
    def _extract_entities(
        self,
        documents: List[NormalizedDocument]
    ) -> Dict[str, List[Tuple[str, int]]]:
        """
        Extract entities from documents using pattern matching.
        
        Returns:
            Dict mapping entity type to list of (entity, count) tuples
        """
        entity_counts = defaultdict(Counter)
        
        for doc in documents:
            text = doc.content_md
            
            # Extract entities by type
            for entity_type, patterns in self.ENTITY_PATTERNS.items():
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.MULTILINE)
                    for match in matches:
                        # Normalize entity name
                        entity = self._normalize_entity(match)
                        if entity and len(entity) > 2:  # Filter very short entities
                            entity_counts[entity_type][entity] += 1
        
        # Filter by frequency and limit count
        filtered = {}
        for entity_type, counter in entity_counts.items():
            # Filter by minimum frequency
            filtered_entities = [
                (entity, count) for entity, count in counter.most_common()
                if count >= self.config.min_entity_frequency
            ]
            # Limit to max entities per type
            filtered[entity_type] = filtered_entities[:self.config.max_entities_per_type]
        
        return filtered
    
    def _extract_topics(
        self,
        documents: List[NormalizedDocument]
    ) -> List[Tuple[str, int]]:
        """
        Extract noun phrases as topics using pattern matching.
        
        Returns:
            List of (topic, count) tuples
        """
        if not self.config.extract_noun_phrases:
            return []
        
        phrase_counter = Counter()
        
        # Common noun phrase patterns
        patterns = [
            r'\b(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b',  # Capitalized phrases
            r'\b([a-z]+ing\s+[a-z]+)\b',  # Gerund phrases
            r'\b([a-z]+\s+(?:system|method|process|technique|strategy))\b',  # Technical phrases
        ]
        
        for doc in documents:
            text = doc.content_md.lower()
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    phrase = self._normalize_entity(match)
                    if phrase and len(phrase.split()) >= 2:  # Multi-word phrases only
                        phrase_counter[phrase] += 1
        
        # Filter by frequency
        filtered_topics = [
            (phrase, count) for phrase, count in phrase_counter.most_common()
            if count >= self.config.min_phrase_frequency
        ]
        
        return filtered_topics[:self.config.max_phrases]
    
    def _extract_relationships(
        self,
        documents: List[NormalizedDocument],
        entities_by_type: Dict[str, List[Tuple[str, int]]]
    ) -> List[Tuple[str, str, int]]:
        """
        Extract relationships via co-occurrence analysis.
        
        Returns:
            List of (entity1, entity2, co_occurrence_count) tuples
        """
        if not self.config.extract_relationships:
            return []
        
        # Build entity lookup
        all_entities = set()
        for entities in entities_by_type.values():
            for entity, _ in entities:
                all_entities.add(entity.lower())
        
        # Track co-occurrences
        co_occurrences = Counter()
        
        for doc in documents:
            text = doc.content_md.lower()
            
            # Find entity positions
            entity_positions = []
            for entity in all_entities:
                pos = 0
                while True:
                    pos = text.find(entity, pos)
                    if pos == -1:
                        break
                    entity_positions.append((pos, entity))
                    pos += len(entity)
            
            # Sort by position
            entity_positions.sort()
            
            # Find co-occurrences within window
            for i, (pos1, entity1) in enumerate(entity_positions):
                for pos2, entity2 in entity_positions[i+1:]:
                    # Check if within window
                    if pos2 - pos1 > self.config.co_occurrence_window:
                        break
                    
                    # Skip if same entity
                    if entity1 == entity2:
                        continue
                    
                    # Record co-occurrence (ordered)
                    pair = tuple(sorted([entity1, entity2]))
                    co_occurrences[pair] += 1
        
        # Filter by minimum edge weight
        relationships = [
            (e1, e2, count) for (e1, e2), count in co_occurrences.most_common()
            if count >= self.config.min_edge_weight
        ]
        
        return relationships
    
    def _build_knowledge_graph(
        self,
        entities_by_type: Dict[str, List[Tuple[str, int]]],
        relationships: List[Tuple[str, str, int]]
    ) -> Dict[str, Any]:
        """
        Build knowledge graph from entities and relationships.
        
        Returns:
            Graph statistics (nodes, edges, centrality)
        """
        nodes = []
        for entity_type, entities in entities_by_type.items():
            for entity, count in entities:
                nodes.append({
                    'id': entity.lower(),
                    'label': entity,
                    'type': entity_type,
                    'frequency': count
                })
        
        edges = []
        for entity1, entity2, weight in relationships:
            edges.append({
                'source': entity1,
                'target': entity2,
                'weight': weight
            })
        
        # Calculate basic graph statistics
        node_degrees = defaultdict(int)
        for edge in edges:
            node_degrees[edge['source']] += 1
            node_degrees[edge['target']] += 1
        
        # Find most central nodes (highest degree)
        central_nodes = sorted(
            [(node, degree) for node, degree in node_degrees.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'nodes': nodes,
            'edges': edges,
            'node_count': len(nodes),
            'edge_count': len(edges),
            'central_nodes': central_nodes
        }
    
    def _normalize_entity(self, text: str) -> str:
        """Normalize entity text."""
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Trim
        text = text.strip()
        # Remove common stop words from ends
        stop_words = ['the', 'a', 'an', 'of', 'in', 'on', 'at']
        words = text.lower().split()
        if words and words[0] in stop_words:
            words = words[1:]
        if words and words[-1] in stop_words:
            words = words[:-1]
        
        return ' '.join(words)
    
    def generate_contextual_tags(
        self,
        analysis: CorpusAnalysisResult,
        source_type: str = 'wikipedia'
    ) -> List[str]:
        """
        Generate contextual tags from analysis results.
        
        Args:
            analysis: Corpus analysis result
            source_type: Source type for tag prefixes
        
        Returns:
            List of contextual tags
        """
        tags = []
        
        # Entity prefixes by type
        type_prefixes = {
            'PERSON': 'character' if source_type == 'wikipedia' else 'author',
            'ORGANIZATION': 'faction' if source_type == 'wikipedia' else 'organization',
            'LOCATION': 'location',
            'EVENT': 'event'
        }
        
        # Add entity tags
        for entity_type, entities in analysis.entities_by_type.items():
            prefix = type_prefixes.get(entity_type, 'entity')
            
            # Take top entities by frequency
            for entity, count in entities[:30]:  # Top 30 per type
                tag = f"{prefix}:{self._tag_format(entity)}"
                tags.append(tag)
        
        # Add topic tags
        for topic, count in analysis.common_topics[:50]:  # Top 50 topics
            tag = f"topic:{self._tag_format(topic)}"
            tags.append(tag)
        
        # Limit total tags
        return tags[:self.config.max_contextual_tags]
    
    def _tag_format(self, text: str) -> str:
        """Format text as tag."""
        return text.lower().replace(' ', '-').replace('_', '-').strip('-')

