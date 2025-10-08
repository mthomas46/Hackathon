# Intelligent Corpus-Based Tagging & Graph Building

**Date**: October 8, 2025  
**Purpose**: Preprocess documents to extract contextual tags and build semantic knowledge graphs  
**Approach**: Analyze sample documents before full ingestion to identify important entities, topics, and relationships

---

## 🎯 Objective

Before ingesting a large corpus (e.g., 500-1,000 Horus Heresy pages), **analyze a configurable sample** to:
1. Extract common topics, entities, names
2. Identify domain-specific terminology
3. Build semantic relationships
4. Generate contextual tags
5. Create knowledge graph structure

### Why This Matters

**Without preprocessing**:
```json
{
  "tags": ["source:wikipedia", "file_type:document", "language:en"],
  "entities": []
}
```

**With intelligent preprocessing**:
```json
{
  "tags": [
    "source:wikipedia",
    "file_type:document", 
    "domain:warhammer-40k",
    "topic:horus-heresy",
    "subtopic:space-marine-legions",
    "character:horus-lupercal",
    "character:emperor-of-mankind",
    "faction:traitor-legions",
    "faction:loyalist-legions",
    "event:siege-of-terra",
    "location:terra",
    "entity-type:primarch"
  ],
  "entities": {
    "characters": ["Horus", "Emperor", "Sanguinius", "Abaddon"],
    "factions": ["Luna Wolves", "Blood Angels", "Sons of Horus"],
    "locations": ["Terra", "Isstvan III", "Ullanor"],
    "events": ["Drop Site Massacre", "Siege of Terra"]
  },
  "relationships": [
    {"from": "Horus", "to": "Emperor", "type": "betrayed"},
    {"from": "Luna Wolves", "to": "Sons of Horus", "type": "renamed_to"},
    {"from": "Horus", "to": "Traitor Legions", "type": "leads"}
  ]
}
```

---

## 🏗️ Architecture

### Preprocessing Pipeline

```
┌────────────────────────────────────────────────────────────────┐
│                   Intelligent Tagging Pipeline                  │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   1. Sample Document Collection      │
        │   - Crawl N documents (configurable) │
        │   - Extract text content              │
        │   - Normalize to plain text           │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   2. Entity Extraction (NLP)         │
        │   - Named Entity Recognition (NER)   │
        │   - Part-of-Speech Tagging           │
        │   - Noun Phrase Extraction           │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   3. Frequency Analysis              │
        │   - Count entity occurrences         │
        │   - Identify common terms            │
        │   - Extract domain vocabulary        │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   4. Relationship Extraction         │
        │   - Co-occurrence analysis           │
        │   - Dependency parsing               │
        │   - Pattern matching                 │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   5. Tag Generation                  │
        │   - Create hierarchical tags         │
        │   - Generate entity labels           │
        │   - Build tag taxonomy               │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   6. Knowledge Graph Construction    │
        │   - Create nodes (entities)          │
        │   - Create edges (relationships)     │
        │   - Assign weights (importance)      │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │   7. Apply to Full Corpus            │
        │   - Tag all documents                │
        │   - Build complete graph             │
        │   - Store in Neo4j                   │
        └──────────────────────────────────────┘
```

---

## 📊 Component Design

### 1. Corpus Analyzer

```python
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple
import spacy
from collections import Counter
import networkx as nx

@dataclass
class CorpusAnalysis:
    """Results from corpus preprocessing analysis."""
    
    # Entity statistics
    entities_by_type: Dict[str, List[Tuple[str, int]]]  # {type: [(entity, count), ...]}
    common_topics: List[Tuple[str, int]]  # [(topic, count), ...]
    domain_vocabulary: Set[str]  # Domain-specific terms
    
    # Relationships
    relationships: List[Dict[str, str]]  # [{"from": X, "to": Y, "type": Z}, ...]
    co_occurrences: Dict[Tuple[str, str], int]  # {(entity1, entity2): count}
    
    # Graph structure
    knowledge_graph: nx.DiGraph  # NetworkX graph
    
    # Tag taxonomy
    tag_hierarchy: Dict[str, List[str]]  # {parent: [children]}
    suggested_tags: List[str]  # Flat list of tags
    
    # Metadata
    documents_analyzed: int
    total_entities: int
    unique_entities: int


class CorpusAnalyzer:
    """Analyze document corpus to extract contextual tags and relationships."""
    
    def __init__(self, nlp_model: str = "en_core_web_lg"):
        """Initialize with spaCy NLP model."""
        self.nlp = spacy.load(nlp_model)
        self.min_entity_frequency = 3  # Minimum occurrences to be significant
        self.top_n_entities = 100  # Top entities to track
    
    async def analyze_corpus(
        self,
        documents: List[NormalizedDocument],
        sample_size: int = None
    ) -> CorpusAnalysis:
        """
        Analyze a corpus of documents to extract contextual information.
        
        Args:
            documents: List of normalized documents
            sample_size: Number of documents to analyze (None = all)
        
        Returns:
            CorpusAnalysis with extracted entities, relationships, and tags
        """
        # Sample documents if needed
        if sample_size and len(documents) > sample_size:
            documents = self._sample_documents(documents, sample_size)
        
        self.print_info(f"📊 Analyzing {len(documents)} documents for contextual tagging...")
        
        # Extract entities from all documents
        all_entities = []
        all_relationships = []
        
        for idx, doc in enumerate(documents, 1):
            if idx % 10 == 0:
                self.print_info(f"   Progress: {idx}/{len(documents)} documents...")
            
            # Parse document with spaCy
            parsed_doc = self.nlp(doc.content_md[:100000])  # Limit for performance
            
            # Extract entities
            entities = self._extract_entities(parsed_doc)
            all_entities.extend(entities)
            
            # Extract relationships
            relationships = self._extract_relationships(parsed_doc)
            all_relationships.extend(relationships)
        
        # Aggregate results
        analysis = self._aggregate_analysis(
            all_entities,
            all_relationships,
            len(documents)
        )
        
        self.print_success(f"✓ Analysis complete!")
        self.print_info(f"   Unique entities: {analysis.unique_entities}")
        self.print_info(f"   Total relationships: {len(analysis.relationships)}")
        self.print_info(f"   Suggested tags: {len(analysis.suggested_tags)}")
        
        return analysis
    
    def _extract_entities(self, doc) -> List[Dict]:
        """Extract named entities from spaCy document."""
        entities = []
        
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,  # PERSON, ORG, GPE, EVENT, etc.
                'start': ent.start_char,
                'end': ent.end_char
            })
        
        # Also extract noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= 2:  # Multi-word phrases
                entities.append({
                    'text': chunk.text,
                    'label': 'NOUN_PHRASE',
                    'start': chunk.start_char,
                    'end': chunk.end_char
                })
        
        return entities
    
    def _extract_relationships(self, doc) -> List[Dict]:
        """Extract relationships between entities."""
        relationships = []
        
        # Find entities that co-occur in same sentence
        for sent in doc.sents:
            sent_entities = [ent for ent in doc.ents if sent.start <= ent.start < sent.end]
            
            # Create relationship for each pair
            for i, ent1 in enumerate(sent_entities):
                for ent2 in sent_entities[i+1:]:
                    # Find verb connecting them
                    verb = self._find_connecting_verb(sent, ent1, ent2)
                    
                    relationships.append({
                        'from': ent1.text,
                        'to': ent2.text,
                        'type': verb or 'co-occurs',
                        'context': sent.text
                    })
        
        return relationships
    
    def _find_connecting_verb(self, sent, ent1, ent2):
        """Find verb connecting two entities in a sentence."""
        # Simple heuristic: find verb between entities
        for token in sent:
            if token.pos_ == 'VERB':
                if ent1.end < token.i < ent2.start:
                    return token.lemma_
        return None
    
    def _aggregate_analysis(
        self,
        all_entities: List[Dict],
        all_relationships: List[Dict],
        doc_count: int
    ) -> CorpusAnalysis:
        """Aggregate entity and relationship data into analysis."""
        
        # Count entities by type
        entities_by_type = {}
        for entity in all_entities:
            label = entity['label']
            text = entity['text']
            
            if label not in entities_by_type:
                entities_by_type[label] = Counter()
            entities_by_type[label][text] += 1
        
        # Get top entities per type
        top_entities = {}
        for label, counter in entities_by_type.items():
            top_entities[label] = counter.most_common(self.top_n_entities)
        
        # Count relationships
        relationship_counter = Counter()
        for rel in all_relationships:
            key = (rel['from'], rel['to'], rel['type'])
            relationship_counter[key] += 1
        
        # Build knowledge graph
        graph = nx.DiGraph()
        for (from_ent, to_ent, rel_type), count in relationship_counter.items():
            if count >= self.min_entity_frequency:
                graph.add_edge(from_ent, to_ent, type=rel_type, weight=count)
        
        # Generate tags
        suggested_tags = self._generate_tags(top_entities)
        tag_hierarchy = self._build_tag_hierarchy(top_entities)
        
        # Calculate statistics
        unique_entities = sum(len(counter) for counter in entities_by_type.values())
        total_entities = sum(sum(counter.values()) for counter in entities_by_type.values())
        
        return CorpusAnalysis(
            entities_by_type=top_entities,
            common_topics=self._extract_topics(all_entities),
            domain_vocabulary=self._extract_vocabulary(all_entities),
            relationships=self._format_relationships(relationship_counter),
            co_occurrences=self._calculate_co_occurrences(all_relationships),
            knowledge_graph=graph,
            tag_hierarchy=tag_hierarchy,
            suggested_tags=suggested_tags,
            documents_analyzed=doc_count,
            total_entities=total_entities,
            unique_entities=unique_entities
        )
    
    def _generate_tags(self, entities_by_type: Dict) -> List[str]:
        """Generate tag list from entity analysis."""
        tags = []
        
        # Add entity-based tags
        for entity_type, entity_list in entities_by_type.items():
            # Map spaCy labels to readable tags
            tag_prefix = {
                'PERSON': 'character',
                'ORG': 'faction',
                'GPE': 'location',
                'EVENT': 'event',
                'WORK_OF_ART': 'reference',
                'NOUN_PHRASE': 'topic'
            }.get(entity_type, 'entity')
            
            # Add top entities as tags
            for entity, count in entity_list[:20]:  # Top 20
                tag = f"{tag_prefix}:{self._normalize_tag(entity)}"
                tags.append(tag)
        
        return tags
    
    def _build_tag_hierarchy(self, entities_by_type: Dict) -> Dict[str, List[str]]:
        """Build hierarchical tag structure."""
        hierarchy = {
            'characters': [],
            'factions': [],
            'locations': [],
            'events': [],
            'topics': []
        }
        
        # Populate hierarchy
        if 'PERSON' in entities_by_type:
            hierarchy['characters'] = [e[0] for e in entities_by_type['PERSON'][:50]]
        
        if 'ORG' in entities_by_type:
            hierarchy['factions'] = [e[0] for e in entities_by_type['ORG'][:50]]
        
        if 'GPE' in entities_by_type:
            hierarchy['locations'] = [e[0] for e in entities_by_type['GPE'][:50]]
        
        if 'EVENT' in entities_by_type:
            hierarchy['events'] = [e[0] for e in entities_by_type['EVENT'][:50]]
        
        return hierarchy
    
    def _normalize_tag(self, text: str) -> str:
        """Normalize text to tag format."""
        return text.lower().replace(' ', '-').replace('_', '-')
    
    def _extract_topics(self, entities: List[Dict]) -> List[Tuple[str, int]]:
        """Extract common topics from noun phrases."""
        noun_phrases = [e['text'] for e in entities if e['label'] == 'NOUN_PHRASE']
        counter = Counter(noun_phrases)
        return counter.most_common(50)
    
    def _extract_vocabulary(self, entities: List[Dict]) -> Set[str]:
        """Extract domain-specific vocabulary."""
        vocab = set()
        for entity in entities:
            words = entity['text'].lower().split()
            vocab.update(words)
        return vocab
    
    def _format_relationships(self, counter: Counter) -> List[Dict]:
        """Format relationships for output."""
        relationships = []
        for (from_ent, to_ent, rel_type), count in counter.most_common(200):
            relationships.append({
                'from': from_ent,
                'to': to_ent,
                'type': rel_type,
                'weight': count
            })
        return relationships
    
    def _calculate_co_occurrences(self, relationships: List[Dict]) -> Dict:
        """Calculate entity co-occurrence frequencies."""
        co_occur = Counter()
        for rel in relationships:
            pair = tuple(sorted([rel['from'], rel['to']]))
            co_occur[pair] += 1
        return dict(co_occur.most_common(500))
    
    def _sample_documents(self, documents: List, sample_size: int) -> List:
        """Sample documents evenly across the corpus."""
        if sample_size >= len(documents):
            return documents
        
        # Evenly sample across the corpus
        step = len(documents) / sample_size
        indices = [int(i * step) for i in range(sample_size)]
        return [documents[i] for i in indices]
```

---

## 🔧 Integration with Ingestion

### Enhanced Wikipedia Ingestor

```python
class EnhancedWikipediaIngestor(WikipediaIngestor):
    """Wikipedia ingestor with intelligent tagging."""
    
    def __init__(self, enable_preprocessing: bool = True):
        super().__init__()
        self.enable_preprocessing = enable_preprocessing
        self.corpus_analyzer = CorpusAnalyzer() if enable_preprocessing else None
        self.corpus_analysis = None
    
    async def crawl_and_ingest_with_tagging(
        self,
        original_page_url: str,
        max_surface_links: int = 10,
        max_depth_distance: int = 2,
        preprocessing_sample_size: int = 50  # NEW: Analyze first 50 docs
    ) -> Tuple[List[NormalizedDocument], CorpusAnalysis]:
        """
        Crawl and ingest with intelligent preprocessing.
        
        Workflow:
        1. Crawl all documents
        2. Analyze sample for contextual tags
        3. Apply tags to all documents
        4. Build knowledge graph
        5. Return enhanced documents
        """
        
        # Step 1: Crawl documents
        self.print_header("STEP 1: DOCUMENT CRAWLING")
        documents = await self.crawl_and_ingest(
            original_page_url,
            max_surface_links,
            max_depth_distance
        )
        
        # Step 2: Preprocess for intelligent tagging
        if self.enable_preprocessing and len(documents) > 0:
            self.print_header("STEP 2: CORPUS ANALYSIS")
            
            self.corpus_analysis = await self.corpus_analyzer.analyze_corpus(
                documents,
                sample_size=preprocessing_sample_size
            )
            
            # Step 3: Apply intelligent tags
            self.print_header("STEP 3: APPLYING CONTEXTUAL TAGS")
            documents = self._apply_intelligent_tags(documents, self.corpus_analysis)
            
            # Step 4: Enhance metadata with graph info
            self.print_header("STEP 4: KNOWLEDGE GRAPH ENHANCEMENT")
            documents = self._enhance_with_graph(documents, self.corpus_analysis)
        
        return documents, self.corpus_analysis
    
    def _apply_intelligent_tags(
        self,
        documents: List[NormalizedDocument],
        analysis: CorpusAnalysis
    ) -> List[NormalizedDocument]:
        """Apply contextual tags to all documents."""
        
        for doc in documents:
            # Extract entities mentioned in this document
            doc_text = doc.content_md.lower()
            
            # Add character tags
            for character, _ in analysis.entities_by_type.get('PERSON', [])[:50]:
                if character.lower() in doc_text:
                    doc.tags.append(f"character:{self._normalize_tag(character)}")
            
            # Add faction tags
            for faction, _ in analysis.entities_by_type.get('ORG', [])[:50]:
                if faction.lower() in doc_text:
                    doc.tags.append(f"faction:{self._normalize_tag(faction)}")
            
            # Add location tags
            for location, _ in analysis.entities_by_type.get('GPE', [])[:50]:
                if location.lower() in doc_text:
                    doc.tags.append(f"location:{self._normalize_tag(location)}")
            
            # Add event tags
            for event, _ in analysis.entities_by_type.get('EVENT', [])[:50]:
                if event.lower() in doc_text:
                    doc.tags.append(f"event:{self._normalize_tag(event)}")
            
            # Add topic tags
            for topic, _ in analysis.common_topics[:30]:
                if topic.lower() in doc_text:
                    doc.tags.append(f"topic:{self._normalize_tag(topic)}")
            
            # Deduplicate tags
            doc.tags = list(set(doc.tags))
        
        return documents
    
    def _enhance_with_graph(
        self,
        documents: List[NormalizedDocument],
        analysis: CorpusAnalysis
    ) -> List[NormalizedDocument]:
        """Add knowledge graph information to document metadata."""
        
        graph = analysis.knowledge_graph
        
        for doc in documents:
            # Find entities mentioned in this document
            doc_entities = []
            doc_text = doc.content_md
            
            for node in graph.nodes():
                if node in doc_text:
                    doc_entities.append(node)
            
            # Add graph metrics to metadata
            if doc_entities:
                doc.metadata['graph_entities'] = doc_entities
                doc.metadata['entity_count'] = len(doc_entities)
                
                # Calculate centrality (importance)
                centralities = []
                for entity in doc_entities:
                    if graph.degree(entity) > 0:
                        centrality = graph.degree(entity)
                        centralities.append(centrality)
                
                if centralities:
                    doc.metadata['avg_entity_centrality'] = sum(centralities) / len(centralities)
                    doc.metadata['max_entity_centrality'] = max(centralities)
                
                # Add related entities (neighbors in graph)
                related = set()
                for entity in doc_entities:
                    related.update(graph.neighbors(entity))
                doc.metadata['related_entities'] = list(related - set(doc_entities))
        
        return documents
    
    def _normalize_tag(self, text: str) -> str:
        """Normalize text to tag format."""
        return text.lower().replace(' ', '-').replace('_', '-')
```

---

## 📊 Configuration

### Preprocessing Configuration

```python
@dataclass
class PreprocessingConfig:
    """Configuration for corpus preprocessing."""
    
    # Sampling
    sample_size: int = 50  # Number of documents to analyze
    sample_strategy: str = "even"  # "even", "random", "first", "representative"
    
    # Entity extraction
    min_entity_frequency: int = 3  # Minimum occurrences to be significant
    top_n_entities: int = 100  # Top entities to track per type
    extract_noun_phrases: bool = True  # Extract multi-word phrases
    
    # Relationship extraction
    enable_relationships: bool = True
    relationship_threshold: int = 2  # Minimum co-occurrences
    max_sentence_length: int = 100  # Skip very long sentences
    
    # Tagging
    max_tags_per_document: int = 50  # Limit tags to avoid over-tagging
    tag_types: List[str] = None  # Specific types to tag (None = all)
    
    # Knowledge graph
    build_knowledge_graph: bool = True
    graph_min_edge_weight: int = 2  # Minimum relationship strength
    calculate_centrality: bool = True
    
    # Performance
    nlp_model: str = "en_core_web_lg"  # spaCy model
    batch_size: int = 10  # Documents per batch
    max_doc_length: int = 100000  # Characters to analyze per doc
```

---

## 🎯 Use Case: Horus Heresy

### Preprocessing Configuration

```python
# Configure for Horus Heresy corpus
config = PreprocessingConfig(
    sample_size=50,  # Analyze first 50 pages
    sample_strategy="even",  # Sample evenly across crawl
    min_entity_frequency=5,  # Entities must appear 5+ times
    top_n_entities=200,  # Track top 200 entities per type
    extract_noun_phrases=True,
    enable_relationships=True,
    build_knowledge_graph=True
)

# Crawl with intelligent tagging
ingestor = EnhancedWikipediaIngestor(enable_preprocessing=True)
documents, analysis = await ingestor.crawl_and_ingest_with_tagging(
    original_page_url="https://warhammer40k.fandom.com/wiki/Horus_Heresy",
    max_surface_links=50,
    max_depth_distance=50,
    preprocessing_sample_size=50
)
```

### Expected Results

```python
# Corpus Analysis Results
analysis = {
    "documents_analyzed": 50,
    "unique_entities": 350,
    "entities_by_type": {
        "PERSON": [
            ("Horus", 145),
            ("Emperor of Mankind", 98),
            ("Sanguinius", 67),
            ("Rogal Dorn", 54),
            # ... 196 more
        ],
        "ORG": [
            ("Luna Wolves", 89),
            ("Sons of Horus", 76),
            ("Imperial Army", 65),
            # ... 97 more
        ],
        "GPE": [
            ("Terra", 234),
            ("Isstvan III", 87),
            ("Mars", 56),
            # ... 73 more
        ],
        "EVENT": [
            ("Horus Heresy", 456),
            ("Siege of Terra", 123),
            ("Drop Site Massacre", 67),
            # ... 45 more
        ]
    },
    "suggested_tags": [
        "character:horus",
        "character:emperor-of-mankind",
        "character:sanguinius",
        "faction:luna-wolves",
        "faction:sons-of-horus",
        "location:terra",
        "event:siege-of-terra",
        # ... 193 more
    ],
    "relationships": [
        {"from": "Horus", "to": "Emperor", "type": "betrayed", "weight": 45},
        {"from": "Luna Wolves", "to": "Sons of Horus", "type": "became", "weight": 23},
        # ... 198 more
    ],
    "knowledge_graph": {
        "nodes": 350,
        "edges": 1247,
        "avg_degree": 7.1,
        "max_degree": 67  # "Horus" most connected
    }
}
```

---

## 📋 Implementation Checklist

### Phase 1: Core Components
- [ ] Implement `CorpusAnalyzer` class
- [ ] Add spaCy NLP integration
- [ ] Implement entity extraction
- [ ] Implement relationship extraction
- [ ] Add frequency analysis
- [ ] Create tag generation logic

### Phase 2: Knowledge Graph
- [ ] Integrate NetworkX
- [ ] Build graph from relationships
- [ ] Calculate centrality metrics
- [ ] Add graph visualization export

### Phase 3: Integration
- [ ] Extend `WikipediaIngestor`
- [ ] Add preprocessing step
- [ ] Apply tags to documents
- [ ] Enhance metadata with graph info

### Phase 4: Configuration
- [ ] Create `PreprocessingConfig` dataclass
- [ ] Add configurable sampling strategies
- [ ] Add performance tuning options
- [ ] Add enable/disable flags

### Phase 5: Testing
- [ ] Unit tests for entity extraction
- [ ] Unit tests for relationship extraction
- [ ] Integration test with Wikipedia corpus
- [ ] E2E test with Horus Heresy crawl

---

## 📊 Expected Performance

| Metric | Value |
|--------|-------|
| Sample Size | 50 documents |
| Analysis Time | 30-60 seconds |
| Entities Extracted | 300-500 unique |
| Relationships Found | 1,000-2,000 |
| Tags Generated | 200-300 |
| Graph Nodes | 300-500 |
| Graph Edges | 1,000-2,500 |

---

## 🎉 Benefits

### Before Intelligent Tagging
- Generic tags only
- No entity recognition
- No relationships tracked
- Flat tag structure
- No knowledge graph

### After Intelligent Tagging
- ✅ Contextual, domain-specific tags
- ✅ Named entity recognition
- ✅ Relationship extraction
- ✅ Hierarchical tag taxonomy
- ✅ Rich knowledge graph
- ✅ Entity centrality metrics
- ✅ Related entity suggestions
- ✅ Semantic search capabilities

---

**Status**: ✅ **Plan Complete - Ready for Implementation**  
**Dependencies**: spaCy, NetworkX  
**Estimated Time**: 6-8 hours implementation  
**Priority**: High (significantly improves tagging quality)

