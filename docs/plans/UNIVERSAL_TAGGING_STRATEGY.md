# Universal Intelligent Tagging Strategy

**Date**: October 8, 2025  
**Purpose**: Apply corpus-based intelligent tagging to ALL ingestion methods  
**Scope**: GitHub, Jira, Confluence, Wikipedia, Local Files, and future sources

---

## 🎯 Core Principles

### 1. **Universal Application**
All ingestion methods use the same intelligent tagging pipeline:
- GitHub commits → Extract code entities, function names, module topics
- Jira tickets → Extract project names, user stories, status labels
- Confluence pages → Extract team names, project terminology, document types
- Wikipedia pages → Extract named entities, topics, relationships
- Local files → Extract based on file content (code or document)

### 2. **Tag Enrichment (Not Replacement)**
```
Base Tags (Always Present)
    ↓
+ Contextual Tags (From Corpus Analysis)
    ↓
+ User-Defined Tags (Manual Additions)
    ↓
= Final Tag Set
```

### 3. **MCP Tag Metadata**
Each trained MCP stores:
```json
{
  "tag_collection": {
    "total_tags": 347,
    "default_tags": 12,      // source, file_type, etc.
    "contextual_tags": 287,   // From corpus analysis
    "user_defined_tags": 48   // Manually added
  },
  "tag_breakdown": {
    "default": ["source:github", "file_type:code", ...],
    "contextual": ["character:horus", "faction:luna-wolves", ...],
    "user_defined": ["priority:high", "team:backend", ...]
  },
  "tag_sources": {
    "corpus_analysis": {
      "sample_size": 50,
      "documents_analyzed": 50,
      "entities_extracted": 350
    }
  }
}
```

---

## 🏗️ Architecture

### Universal Tagging Pipeline

```
┌────────────────────────────────────────────────────────────┐
│              Universal Tagging Pipeline                     │
└────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
  ┌──────────┐       ┌──────────┐       ┌──────────┐
  │  GitHub  │       │   Jira   │       │Wikipedia │
  │ Ingestor │       │ Ingestor │       │ Ingestor │
  └────┬─────┘       └────┬─────┘       └────┬─────┘
       │                  │                   │
       └──────────────────┼───────────────────┘
                          ▼
              ┌───────────────────────┐
              │  1. Base Tagging      │
              │  - source:*           │
              │  - file_type:*        │
              │  - created_at         │
              │  - updated_at         │
              └───────────────────────┘
                          ▼
              ┌───────────────────────┐
              │  2. Corpus Analysis   │
              │  - Sample N docs      │
              │  - Extract entities   │
              │  - Find relationships │
              │  - Build graph        │
              └───────────────────────┘
                          ▼
              ┌───────────────────────┐
              │  3. Contextual Tags   │
              │  - Add entity tags    │
              │  - Add topic tags     │
              │  - Add relationship   │
              │  - Enrich (not replace)│
              └───────────────────────┘
                          ▼
              ┌───────────────────────┐
              │  4. User-Defined Tags │
              │  - Apply user tags    │
              │  - Merge with existing│
              │  - Deduplicate        │
              └───────────────────────┘
                          ▼
              ┌───────────────────────┐
              │  5. Final Tag Set     │
              │  - Store in document  │
              │  - Track metadata     │
              │  - Store in Neo4j     │
              └───────────────────────┘
                          ▼
              ┌───────────────────────┐
              │  6. MCP Training      │
              │  - Include tag        │
              │    collection         │
              │  - Store breakdown    │
              └───────────────────────┘
```

---

## 📊 Implementation

### 1. Universal Tagging Manager

```python
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from enum import Enum

class TagType(Enum):
    """Type of tag."""
    DEFAULT = "default"         # Built-in tags (source, file_type, etc.)
    CONTEXTUAL = "contextual"   # From corpus analysis
    USER_DEFINED = "user_defined"  # Manually added


@dataclass
class TagCollection:
    """Complete tag collection for a corpus."""
    
    default_tags: List[str] = field(default_factory=list)
    contextual_tags: List[str] = field(default_factory=list)
    user_defined_tags: List[str] = field(default_factory=list)
    
    def all_tags(self) -> List[str]:
        """Get all tags combined."""
        return self.default_tags + self.contextual_tags + self.user_defined_tags
    
    def total_count(self) -> int:
        """Total number of unique tags."""
        return len(set(self.all_tags()))
    
    def breakdown(self) -> Dict[str, int]:
        """Tag count by type."""
        return {
            "default": len(self.default_tags),
            "contextual": len(self.contextual_tags),
            "user_defined": len(self.user_defined_tags),
            "total": self.total_count()
        }
    
    def to_dict(self) -> Dict:
        """Export to dictionary."""
        return {
            "default": self.default_tags,
            "contextual": self.contextual_tags,
            "user_defined": self.user_defined_tags,
            "breakdown": self.breakdown()
        }


class UniversalTaggingManager:
    """Manages tagging across all ingestion methods."""
    
    def __init__(self, corpus_analyzer: CorpusAnalyzer):
        self.corpus_analyzer = corpus_analyzer
        self.user_tags: Set[str] = set()  # User-defined tags
        self.tag_collection = TagCollection()
    
    async def tag_documents(
        self,
        documents: List[NormalizedDocument],
        source_type: str,  # 'github', 'jira', 'wikipedia', etc.
        preprocessing_config: PreprocessingConfig = None,
        user_tags: List[str] = None
    ) -> Tuple[List[NormalizedDocument], TagCollection]:
        """
        Apply universal tagging to documents from any source.
        
        Args:
            documents: List of normalized documents
            source_type: Type of source (github, jira, etc.)
            preprocessing_config: Config for corpus analysis
            user_tags: Optional user-defined tags to add
        
        Returns:
            Tuple of (tagged_documents, tag_collection)
        """
        self.print_header(f"UNIVERSAL TAGGING: {source_type.upper()}")
        
        # Step 1: Ensure base tags exist
        self.print_info("Step 1: Applying base tags...")
        documents = self._ensure_base_tags(documents, source_type)
        self._collect_tags(documents, TagType.DEFAULT)
        
        # Step 2: Corpus analysis for contextual tags
        if preprocessing_config and preprocessing_config.enable_preprocessing:
            self.print_info("Step 2: Analyzing corpus for contextual tags...")
            analysis = await self.corpus_analyzer.analyze_corpus(
                documents,
                sample_size=preprocessing_config.sample_size
            )
            documents = self._apply_contextual_tags(documents, analysis, source_type)
            self._collect_tags(documents, TagType.CONTEXTUAL)
        
        # Step 3: Apply user-defined tags
        if user_tags:
            self.print_info(f"Step 3: Applying {len(user_tags)} user-defined tags...")
            documents = self._apply_user_tags(documents, user_tags)
            self._collect_tags(documents, TagType.USER_DEFINED)
        
        # Step 4: Final processing
        self.print_info("Step 4: Finalizing tags...")
        documents = self._finalize_tags(documents)
        
        self.print_success(f"✓ Tagging complete!")
        self.print_info(f"   Total tags: {self.tag_collection.total_count()}")
        self.print_info(f"   Default: {len(self.tag_collection.default_tags)}")
        self.print_info(f"   Contextual: {len(self.tag_collection.contextual_tags)}")
        self.print_info(f"   User-defined: {len(self.tag_collection.user_defined_tags)}")
        
        return documents, self.tag_collection
    
    def _ensure_base_tags(
        self,
        documents: List[NormalizedDocument],
        source_type: str
    ) -> List[NormalizedDocument]:
        """Ensure all documents have base tags."""
        for doc in documents:
            # Ensure source tag exists
            if not any(tag.startswith('source:') for tag in doc.tags):
                doc.tags.append(f"source:{source_type}")
            
            # Ensure file_type tag exists
            if not any(tag.startswith('file_type:') for tag in doc.tags):
                file_type = doc.metadata.get('file_type', 'unknown')
                doc.tags.append(f"file_type:{file_type}")
            
            # Add timestamp tags if available
            if 'created_at' in doc.metadata:
                doc.tags.append(f"has_created_date:true")
            if 'updated_at' in doc.metadata:
                doc.tags.append(f"has_updated_date:true")
        
        return documents
    
    def _apply_contextual_tags(
        self,
        documents: List[NormalizedDocument],
        analysis: CorpusAnalysis,
        source_type: str
    ) -> List[NormalizedDocument]:
        """Apply contextual tags based on corpus analysis."""
        
        # Source-specific tag prefixes
        entity_prefixes = {
            'github': {
                'PERSON': 'author',
                'ORG': 'organization',
                'NOUN_PHRASE': 'topic'
            },
            'jira': {
                'PERSON': 'assignee',
                'ORG': 'team',
                'NOUN_PHRASE': 'story'
            },
            'wikipedia': {
                'PERSON': 'character',
                'ORG': 'faction',
                'GPE': 'location',
                'EVENT': 'event',
                'NOUN_PHRASE': 'topic'
            },
            'confluence': {
                'PERSON': 'author',
                'ORG': 'team',
                'NOUN_PHRASE': 'topic'
            },
            'local': {
                'PERSON': 'author',
                'ORG': 'organization',
                'NOUN_PHRASE': 'topic'
            }
        }
        
        prefixes = entity_prefixes.get(source_type, {
            'PERSON': 'person',
            'ORG': 'organization',
            'NOUN_PHRASE': 'topic'
        })
        
        # Apply tags to each document
        for doc in documents:
            doc_text = doc.content_md.lower()
            contextual_tags = []
            
            # Add entity-based tags
            for entity_type, entities in analysis.entities_by_type.items():
                prefix = prefixes.get(entity_type, 'entity')
                
                for entity, count in entities[:30]:  # Top 30 entities per type
                    if entity.lower() in doc_text:
                        tag = f"{prefix}:{self._normalize_tag(entity)}"
                        contextual_tags.append(tag)
            
            # Add topic tags
            for topic, count in analysis.common_topics[:20]:
                if topic.lower() in doc_text:
                    tag = f"topic:{self._normalize_tag(topic)}"
                    contextual_tags.append(tag)
            
            # Add graph-based tags
            if hasattr(doc.metadata, 'graph_entities') and doc.metadata.get('graph_entities'):
                contextual_tags.append(f"graph_connected:true")
                contextual_tags.append(f"entity_count:{len(doc.metadata['graph_entities'])}")
            
            # Enrich existing tags (don't overwrite)
            doc.tags.extend(contextual_tags)
            doc.tags = list(set(doc.tags))  # Deduplicate
        
        return documents
    
    def _apply_user_tags(
        self,
        documents: List[NormalizedDocument],
        user_tags: List[str]
    ) -> List[NormalizedDocument]:
        """Apply user-defined tags to all documents."""
        for doc in documents:
            # Add user tags
            doc.tags.extend(user_tags)
            doc.tags = list(set(doc.tags))  # Deduplicate
            
            # Store in metadata that these are user-defined
            doc.metadata['has_user_tags'] = True
            doc.metadata['user_tag_count'] = len([t for t in doc.tags if t in user_tags])
        
        return documents
    
    def _finalize_tags(
        self,
        documents: List[NormalizedDocument]
    ) -> List[NormalizedDocument]:
        """Final tag processing."""
        for doc in documents:
            # Sort tags for consistency
            doc.tags = sorted(set(doc.tags))
            
            # Add tag metadata
            doc.metadata['tag_count'] = len(doc.tags)
            doc.metadata['tag_types'] = {
                'default': len([t for t in doc.tags if any(t.startswith(p) for p in ['source:', 'file_type:', 'has_'])]),
                'contextual': len([t for t in doc.tags if any(t.startswith(p) for p in ['character:', 'faction:', 'topic:', 'author:'])]),
                'user_defined': doc.metadata.get('user_tag_count', 0)
            }
        
        return documents
    
    def _collect_tags(self, documents: List[NormalizedDocument], tag_type: TagType):
        """Collect tags from documents by type."""
        all_tags = []
        for doc in documents:
            all_tags.extend(doc.tags)
        
        unique_tags = list(set(all_tags))
        
        if tag_type == TagType.DEFAULT:
            # Only collect base tags
            self.tag_collection.default_tags = [
                t for t in unique_tags 
                if any(t.startswith(p) for p in ['source:', 'file_type:', 'has_', 'language:'])
            ]
        elif tag_type == TagType.CONTEXTUAL:
            # Collect contextual tags (not base tags)
            base_prefixes = ['source:', 'file_type:', 'has_', 'language:']
            self.tag_collection.contextual_tags = [
                t for t in unique_tags 
                if not any(t.startswith(p) for p in base_prefixes)
                and t not in self.tag_collection.user_defined_tags
            ]
        elif tag_type == TagType.USER_DEFINED:
            # User tags stored separately
            pass
    
    def _normalize_tag(self, text: str) -> str:
        """Normalize text to tag format."""
        return text.lower().replace(' ', '-').replace('_', '-')
    
    def add_user_tags(self, tags: List[str]):
        """Add user-defined tags to the collection."""
        self.user_tags.update(tags)
        self.tag_collection.user_defined_tags = list(self.user_tags)
    
    def get_tag_collection(self) -> TagCollection:
        """Get complete tag collection."""
        return self.tag_collection
```

---

## 🔧 Source-Specific Tagging

### GitHub Ingestion

```python
class GitHubIngestor:
    """GitHub ingestion with intelligent tagging."""
    
    async def ingest_with_tagging(
        self,
        repo: str,
        branch: str = "main",
        preprocessing_config: PreprocessingConfig = None,
        user_tags: List[str] = None
    ) -> Tuple[List[NormalizedDocument], TagCollection]:
        
        # Step 1: Fetch documents
        documents = await self._fetch_github_documents(repo, branch)
        
        # Step 2: Apply base tags
        for doc in documents:
            doc.tags.extend([
                f"source:github",
                f"repo:{repo.replace('/', '-')}",
                f"branch:{branch}",
                f"file_type:{self._detect_file_type(doc)}"
            ])
        
        # Step 3: Universal tagging
        tagging_manager = UniversalTaggingManager(CorpusAnalyzer())
        documents, tag_collection = await tagging_manager.tag_documents(
            documents,
            source_type='github',
            preprocessing_config=preprocessing_config,
            user_tags=user_tags
        )
        
        return documents, tag_collection
```

**Example Tags**:
```python
[
    # Default
    "source:github",
    "repo:mycompany-backend",
    "branch:main",
    "file_type:code",
    "language:python",
    
    # Contextual (from corpus analysis)
    "author:john-doe",
    "topic:authentication",
    "topic:user-management",
    "module:auth-service",
    "function:validate-token",
    
    # User-defined
    "priority:high",
    "team:backend",
    "sprint:23"
]
```

### Jira Ingestion

```python
class JiraIngestor:
    """Jira ingestion with intelligent tagging."""
    
    async def ingest_with_tagging(
        self,
        project_key: str,
        preprocessing_config: PreprocessingConfig = None,
        user_tags: List[str] = None
    ) -> Tuple[List[NormalizedDocument], TagCollection]:
        
        # Step 1: Fetch tickets
        documents = await self._fetch_jira_tickets(project_key)
        
        # Step 2: Apply base tags
        for doc in documents:
            ticket_data = doc.metadata
            doc.tags.extend([
                f"source:jira",
                f"project:{project_key}",
                f"ticket_type:{ticket_data.get('issue_type', 'unknown')}",
                f"status:{ticket_data.get('status', 'unknown')}",
                f"priority:{ticket_data.get('priority', 'medium')}"
            ])
        
        # Step 3: Universal tagging
        tagging_manager = UniversalTaggingManager(CorpusAnalyzer())
        documents, tag_collection = await tagging_manager.tag_documents(
            documents,
            source_type='jira',
            preprocessing_config=preprocessing_config,
            user_tags=user_tags
        )
        
        return documents, tag_collection
```

**Example Tags**:
```python
[
    # Default
    "source:jira",
    "project:HACK",
    "ticket_type:story",
    "status:done",
    "priority:high",
    
    # Contextual
    "assignee:jane-smith",
    "team:frontend",
    "story:user-authentication",
    "epic:security-hardening",
    
    # User-defined
    "release:v2.0",
    "customer:acme-corp"
]
```

### Confluence Ingestion

```python
class ConfluenceIngestor:
    """Confluence ingestion with intelligent tagging."""
    
    async def ingest_with_tagging(
        self,
        space_key: str,
        preprocessing_config: PreprocessingConfig = None,
        user_tags: List[str] = None
    ) -> Tuple[List[NormalizedDocument], TagCollection]:
        
        # Fetch pages
        documents = await self._fetch_confluence_pages(space_key)
        
        # Base tags
        for doc in documents:
            doc.tags.extend([
                f"source:confluence",
                f"space:{space_key}",
                f"file_type:document"
            ])
        
        # Universal tagging
        tagging_manager = UniversalTaggingManager(CorpusAnalyzer())
        documents, tag_collection = await tagging_manager.tag_documents(
            documents,
            source_type='confluence',
            preprocessing_config=preprocessing_config,
            user_tags=user_tags
        )
        
        return documents, tag_collection
```

---

## 📦 MCP Tag Metadata Storage

### Enhanced MCP Metadata

```python
class MCPTagMetadata:
    """Tag metadata stored with trained MCP."""
    
    def __init__(self, tag_collection: TagCollection, corpus_analysis: CorpusAnalysis):
        self.tag_collection = tag_collection
        self.corpus_analysis = corpus_analysis
    
    def to_dict(self) -> Dict:
        """Export complete tag metadata."""
        return {
            "tag_collection": {
                "total_tags": self.tag_collection.total_count(),
                "breakdown": self.tag_collection.breakdown(),
                "default_tags": self.tag_collection.default_tags,
                "contextual_tags": self.tag_collection.contextual_tags,
                "user_defined_tags": self.tag_collection.user_defined_tags
            },
            "corpus_analysis": {
                "documents_analyzed": self.corpus_analysis.documents_analyzed,
                "unique_entities": self.corpus_analysis.unique_entities,
                "total_entities": self.corpus_analysis.total_entities,
                "relationships_found": len(self.corpus_analysis.relationships),
                "graph_nodes": self.corpus_analysis.knowledge_graph.number_of_nodes(),
                "graph_edges": self.corpus_analysis.knowledge_graph.number_of_edges()
            },
            "tag_sources": {
                "base_tagging": "automated",
                "contextual_tagging": "corpus_analysis",
                "user_tagging": "manual"
            },
            "tag_categories": self._categorize_tags()
        }
    
    def _categorize_tags(self) -> Dict[str, List[str]]:
        """Categorize all tags by prefix."""
        categories = {}
        
        all_tags = self.tag_collection.all_tags()
        for tag in all_tags:
            if ':' in tag:
                prefix = tag.split(':')[0]
                if prefix not in categories:
                    categories[prefix] = []
                categories[prefix].append(tag)
        
        return categories


# Store with MCP
async def train_mcp_with_tags(
    mcp_id: str,
    documents: List[NormalizedDocument],
    tag_collection: TagCollection,
    corpus_analysis: CorpusAnalysis
):
    """Train MCP and store tag metadata."""
    
    # Create tag metadata
    tag_metadata = MCPTagMetadata(tag_collection, corpus_analysis)
    
    # Train MCP
    await train_mcp(mcp_id, documents)
    
    # Store tag metadata with MCP
    await store_mcp_metadata(mcp_id, {
        "tag_metadata": tag_metadata.to_dict(),
        "training_timestamp": datetime.now().isoformat(),
        "document_count": len(documents)
    })
```

---

## 🎛️ Configuration

### Universal Tagging Configuration

```python
@dataclass
class UniversalTaggingConfig:
    """Configuration for universal tagging."""
    
    # Preprocessing
    enable_preprocessing: bool = True
    preprocessing_config: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    
    # User tags
    enable_user_tags: bool = True
    user_tags: List[str] = field(default_factory=list)
    
    # Tag limits
    max_tags_per_document: int = 100
    max_contextual_tags: int = 50
    
    # Source-specific
    source_specific_prefixes: bool = True  # Use source-specific tag prefixes
    
    # Storage
    store_tag_metadata_with_mcp: bool = True
    export_tag_collection: bool = True


# Usage
config = UniversalTaggingConfig(
    enable_preprocessing=True,
    preprocessing_config=PreprocessingConfig(
        sample_size=50,
        min_entity_frequency=5
    ),
    enable_user_tags=True,
    user_tags=[
        "priority:high",
        "team:backend",
        "sprint:23",
        "release:v2.0"
    ],
    store_tag_metadata_with_mcp=True
)
```

---

## 📊 Demo Integration

### Complete Demo with Universal Tagging

```python
class MCPLifecycleDemo:
    
    async def run_complete_demo(self):
        """Run demo with universal intelligent tagging."""
        
        # Configure universal tagging
        tagging_config = UniversalTaggingConfig(
            enable_preprocessing=True,
            preprocessing_config=PreprocessingConfig(sample_size=50),
            user_tags=[
                "demo:true",
                "environment:staging",
                "iteration:v11"
            ]
        )
        
        # Phase 2: Multi-Source Ingestion with Tagging
        self.print_header("PHASE 2: MULTI-SOURCE INGESTION WITH INTELLIGENT TAGGING")
        
        # GitHub ingestion
        github_docs, github_tags = await self.ingest_github_with_tagging(
            repo="mycompany/backend",
            config=tagging_config
        )
        
        # Jira ingestion
        jira_docs, jira_tags = await self.ingest_jira_with_tagging(
            project="HACK",
            config=tagging_config
        )
        
        # Wikipedia ingestion
        wiki_docs, wiki_tags = await self.ingest_wikipedia_with_tagging(
            url="https://en.wikipedia.org/wiki/Machine_learning",
            config=tagging_config
        )
        
        # Horus Heresy (specialized)
        horus_docs, horus_tags = await self.ingest_horus_heresy_with_tagging(
            config=tagging_config
        )
        
        # Combine all documents
        all_documents = github_docs + jira_docs + wiki_docs + horus_docs
        combined_tags = self._merge_tag_collections([
            github_tags, jira_tags, wiki_tags, horus_tags
        ])
        
        # Phase 4: Train MCP with Tag Metadata
        self.print_header("PHASE 4: MCP TRAINING WITH TAG METADATA")
        
        mcp_id = await self.train_mcp_with_complete_metadata(
            documents=all_documents,
            tag_collection=combined_tags,
            corpus_analyses=[github_analysis, jira_analysis, ...]
        )
        
        # Display tag statistics
        self._display_tag_statistics(combined_tags)
```

---

## 📋 Implementation Checklist

### Phase 1: Core Universal Tagging
- [ ] Create `UniversalTaggingManager` class
- [ ] Implement `TagCollection` dataclass
- [ ] Add tag type enum (DEFAULT, CONTEXTUAL, USER_DEFINED)
- [ ] Implement tag enrichment (not replacement) logic
- [ ] Add tag deduplication

### Phase 2: Source Integration
- [ ] Update `GitHubIngestor` with universal tagging
- [ ] Update `JiraIngestor` with universal tagging
- [ ] Update `ConfluenceIngestor` with universal tagging
- [ ] Update `WikipediaIngestor` with universal tagging
- [ ] Update `LocalFileIngestor` with universal tagging

### Phase 3: User-Defined Tags
- [ ] Add user tag input mechanism
- [ ] Implement user tag validation
- [ ] Add user tag storage
- [ ] Track user tag count in metadata

### Phase 4: MCP Metadata Storage
- [ ] Create `MCPTagMetadata` class
- [ ] Store tag collection with MCP
- [ ] Store tag breakdown (default/contextual/user)
- [ ] Store corpus analysis summary
- [ ] Add tag retrieval from MCP

### Phase 5: Testing
- [ ] Unit test tag enrichment logic
- [ ] Unit test tag deduplication
- [ ] Integration test multi-source tagging
- [ ] E2E test complete workflow
- [ ] Test tag metadata storage/retrieval

---

## 🎯 Success Criteria

- [ ] All 5 ingestion sources use universal tagging
- [ ] Base tags preserved (not overwritten)
- [ ] Contextual tags applied from corpus analysis
- [ ] User-defined tags applied correctly
- [ ] Tag metadata stored with MCP
- [ ] Tag breakdown tracked (default/contextual/user)
- [ ] No tag duplication
- [ ] Tag collection exportable

---

**Status**: ✅ **Plan Complete - Ready for Implementation**  
**Scope**: Universal (all ingestion methods)  
**Estimated Time**: 8-10 hours implementation  
**Priority**: Critical (foundational for all ingestion)

