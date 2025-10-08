"""
Universal tagging manager for all ingestion sources.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
import logging

from ingestion.models import NormalizedDocument
from ingestion.tagging.tag_collection import TagCollection, TagType

logger = logging.getLogger(__name__)


# Import CorpusAnalyzer conditionally to avoid circular imports
try:
    from ingestion.analysis import CorpusAnalyzer, CorpusAnalysisConfig
    CORPUS_ANALYSIS_AVAILABLE = True
except ImportError:
    CORPUS_ANALYSIS_AVAILABLE = False
    logger.warning("CorpusAnalyzer not available - contextual tagging will be limited")


@dataclass
class UniversalTaggingConfig:
    """Configuration for universal tagging."""
    
    # User-defined tags
    enable_user_tags: bool = True
    user_tags: List[str] = field(default_factory=list)
    
    # Tag limits
    max_tags_per_document: int = 100
    max_contextual_tags: int = 50
    
    # Corpus analysis / Preprocessing
    enable_preprocessing: bool = True  # Enable intelligent contextual tagging
    preprocessing_sample_size: int = 50
    min_entity_frequency: int = 3
    enable_relationships: bool = True
    enable_knowledge_graph: bool = True
    
    # Source-specific
    source_specific_prefixes: bool = True  # Use source-specific tag prefixes
    
    # Storage
    store_tag_metadata: bool = True
    export_tag_collection: bool = True


class UniversalTaggingManager:
    """
    Manages tagging across all ingestion methods.
    
    Applies three-layer tagging:
    1. Default tags (always present)
    2. Contextual tags (from corpus analysis)
    3. User-defined tags (manual additions)
    
    Tags enrich but never overwrite existing tags.
    """
    
    # Default tag prefixes (always added)
    DEFAULT_TAG_PREFIXES = ['source:', 'file_type:', 'has_', 'language:']
    
    # Source-specific entity prefixes
    SOURCE_ENTITY_PREFIXES = {
        'github': {
            'PERSON': 'author',
            'ORG': 'organization',
            'NOUN_PHRASE': 'topic',
            'CODE': 'module'
        },
        'jira': {
            'PERSON': 'assignee',
            'ORG': 'team',
            'NOUN_PHRASE': 'story',
            'WORK_ITEM': 'epic'
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
            'NOUN_PHRASE': 'topic',
            'PAGE': 'space'
        },
        'local': {
            'PERSON': 'author',
            'ORG': 'organization',
            'NOUN_PHRASE': 'topic',
            'FILE': 'directory'
        }
    }
    
    def __init__(self, config: UniversalTaggingConfig = None):
        """
        Initialize universal tagging manager.
        
        Args:
            config: Configuration for tagging behavior
        """
        self.config = config or UniversalTaggingConfig()
        self.tag_collection = TagCollection.empty()
        self.corpus_analyzer = None  # Set later when CorpusAnalyzer is available
    
    async def tag_documents(
        self,
        documents: List[NormalizedDocument],
        source_type: str,
        user_tags: Optional[List[str]] = None,
        corpus_analysis: Optional[Dict] = None
    ) -> Tuple[List[NormalizedDocument], TagCollection]:
        """
        Apply universal tagging to documents from any source.
        
        Args:
            documents: List of normalized documents
            source_type: Type of source (github, jira, wikipedia, etc.)
            user_tags: Optional user-defined tags to add
            corpus_analysis: Optional pre-computed corpus analysis results
        
        Returns:
            Tuple of (tagged_documents, tag_collection)
        """
        logger.info(f"🏷️  Universal Tagging: {source_type.upper()}")
        logger.info(f"   Documents: {len(documents)}")
        
        # Reset tag collection for this batch
        self.tag_collection = TagCollection.empty()
        
        # Step 1: Ensure base tags exist
        logger.info("   Step 1/5: Applying base tags...")
        documents = self._ensure_base_tags(documents, source_type)
        self._collect_tags(documents, TagType.DEFAULT)
        logger.info(f"   ✓ Base tags: {len(self.tag_collection.default_tags)} unique")
        
        # Step 2: Run corpus analysis if enabled and not provided
        if self.config.enable_preprocessing and not corpus_analysis and CORPUS_ANALYSIS_AVAILABLE:
            logger.info("   Step 2/5: Running corpus analysis...")
            corpus_analysis = await self._run_corpus_analysis(documents, source_type)
            logger.info(f"   ✓ Analysis complete: {corpus_analysis.get('total_entities', 0)} entities found")
        elif corpus_analysis:
            logger.info("   Step 2/5: Using provided corpus analysis...")
        else:
            logger.info("   Step 2/5: Skipping corpus analysis (disabled or unavailable)")
        
        # Step 3: Apply contextual tags (if corpus analysis available)
        if corpus_analysis:
            logger.info("   Step 3/5: Applying contextual tags...")
            documents = self._apply_contextual_tags(documents, corpus_analysis, source_type)
            self._collect_tags(documents, TagType.CONTEXTUAL)
            logger.info(f"   ✓ Contextual tags: {len(self.tag_collection.contextual_tags)} unique")
        else:
            logger.info("   Step 3/5: No contextual tags")
        
        # Step 4: Apply user-defined tags
        tags_to_apply = user_tags or self.config.user_tags
        if tags_to_apply and self.config.enable_user_tags:
            logger.info(f"   Step 4/5: Applying {len(tags_to_apply)} user-defined tags...")
            documents = self._apply_user_tags(documents, tags_to_apply)
            self.tag_collection.user_defined_tags = tags_to_apply
            logger.info(f"   ✓ User-defined tags: {len(tags_to_apply)}")
        else:
            logger.info("   Step 4/5: No user-defined tags")
        
        # Step 5: Finalize tags
        logger.info("   Step 5/5: Finalizing tags...")
        documents = self._finalize_tags(documents)
        self.tag_collection.deduplicate()
        
        logger.info(f"✅ Tagging complete!")
        logger.info(f"   Total unique tags: {self.tag_collection.total_count()}")
        
        return documents, self.tag_collection
    
    def _ensure_base_tags(
        self,
        documents: List[NormalizedDocument],
        source_type: str
    ) -> List[NormalizedDocument]:
        """
        Ensure all documents have base tags.
        
        Base tags include:
        - source:*
        - file_type:*
        - language:* (if available)
        - has_created_date / has_updated_date
        """
        for doc in documents:
            # Ensure source tag exists
            if not any(tag.startswith('source:') for tag in doc.tags):
                doc.tags.append(f"source:{source_type}")
            
            # Ensure file_type tag exists
            if not any(tag.startswith('file_type:') for tag in doc.tags):
                file_type = doc.metadata.get('file_type', 'unknown')
                doc.tags.append(f"file_type:{file_type}")
            
            # Add language tag if available
            if 'language' in doc.metadata:
                language = doc.metadata['language']
                if not any(tag.startswith('language:') for tag in doc.tags):
                    doc.tags.append(f"language:{language}")
            
            # Add timestamp presence tags
            if 'created_at' in doc.metadata:
                doc.tags.append("has_created_date:true")
            if 'updated_at' in doc.metadata:
                doc.tags.append("has_updated_date:true")
        
        return documents
    
    def _apply_contextual_tags(
        self,
        documents: List[NormalizedDocument],
        analysis: Dict,
        source_type: str
    ) -> List[NormalizedDocument]:
        """
        Apply contextual tags based on corpus analysis.
        
        Args:
            documents: Documents to tag
            analysis: Corpus analysis results (entities, topics, etc.)
            source_type: Source type for prefix mapping
        """
        # Get source-specific prefixes
        prefixes = self.SOURCE_ENTITY_PREFIXES.get(source_type, {
            'PERSON': 'person',
            'ORG': 'organization',
            'NOUN_PHRASE': 'topic'
        })
        
        # Extract entities from analysis
        entities_by_type = analysis.get('entities_by_type', {})
        common_topics = analysis.get('common_topics', [])
        
        # Apply tags to each document
        for doc in documents:
            doc_text = doc.content_md.lower()
            contextual_tags = []
            
            # Add entity-based tags
            for entity_type, entities in entities_by_type.items():
                prefix = prefixes.get(entity_type, 'entity')
                
                # Take top N entities per type
                for entity, count in entities[:30]:
                    if entity.lower() in doc_text:
                        tag = f"{prefix}:{self._normalize_tag(entity)}"
                        contextual_tags.append(tag)
            
            # Add topic tags
            for topic, count in common_topics[:20]:
                if topic.lower() in doc_text:
                    tag = f"topic:{self._normalize_tag(topic)}"
                    contextual_tags.append(tag)
            
            # Limit contextual tags per document
            contextual_tags = contextual_tags[:self.config.max_contextual_tags]
            
            # Enrich existing tags (don't overwrite)
            doc.tags.extend(contextual_tags)
            doc.tags = list(set(doc.tags))  # Deduplicate
            
            # Store contextual tag count in metadata
            doc.metadata['contextual_tag_count'] = len(contextual_tags)
        
        return documents
    
    def _apply_user_tags(
        self,
        documents: List[NormalizedDocument],
        user_tags: List[str]
    ) -> List[NormalizedDocument]:
        """
        Apply user-defined tags to all documents.
        
        Args:
            documents: Documents to tag
            user_tags: List of user-defined tags
        """
        for doc in documents:
            # Add user tags
            doc.tags.extend(user_tags)
            doc.tags = list(set(doc.tags))  # Deduplicate
            
            # Store in metadata
            doc.metadata['has_user_tags'] = True
            doc.metadata['user_tag_count'] = len([t for t in doc.tags if t in user_tags])
        
        return documents
    
    def _finalize_tags(
        self,
        documents: List[NormalizedDocument]
    ) -> List[NormalizedDocument]:
        """
        Final tag processing.
        
        - Sort tags
        - Limit total tags per document
        - Add tag metadata
        """
        for doc in documents:
            # Sort tags for consistency
            doc.tags = sorted(set(doc.tags))
            
            # Limit total tags
            if len(doc.tags) > self.config.max_tags_per_document:
                logger.warning(f"Document {doc.document_id} has {len(doc.tags)} tags, limiting to {self.config.max_tags_per_document}")
                doc.tags = doc.tags[:self.config.max_tags_per_document]
            
            # Add tag metadata
            doc.metadata['tag_count'] = len(doc.tags)
            doc.metadata['tag_types'] = self._count_tag_types(doc.tags)
        
        return documents
    
    def _count_tag_types(self, tags: List[str]) -> Dict[str, int]:
        """Count tags by type."""
        default_count = len([t for t in tags if any(t.startswith(p) for p in self.DEFAULT_TAG_PREFIXES)])
        user_count = len([t for t in tags if t in self.config.user_tags])
        contextual_count = len(tags) - default_count - user_count
        
        return {
            'default': default_count,
            'contextual': max(0, contextual_count),
            'user_defined': user_count
        }
    
    def _collect_tags(self, documents: List[NormalizedDocument], tag_type: TagType):
        """
        Collect tags from documents by type.
        
        Args:
            documents: Documents to collect tags from
            tag_type: Type of tags to collect
        """
        all_tags = []
        for doc in documents:
            all_tags.extend(doc.tags)
        
        unique_tags = list(set(all_tags))
        
        if tag_type == TagType.DEFAULT:
            # Only collect base tags
            self.tag_collection.default_tags = [
                t for t in unique_tags 
                if any(t.startswith(p) for p in self.DEFAULT_TAG_PREFIXES)
            ]
        elif tag_type == TagType.CONTEXTUAL:
            # Collect contextual tags (not base tags, not user tags)
            self.tag_collection.contextual_tags = [
                t for t in unique_tags 
                if not any(t.startswith(p) for p in self.DEFAULT_TAG_PREFIXES)
                and t not in self.config.user_tags
            ]
    
    async def _run_corpus_analysis(
        self,
        documents: List[NormalizedDocument],
        source_type: str
    ) -> Dict:
        """
        Run corpus analysis on documents.
        
        Args:
            documents: Documents to analyze
            source_type: Source type for analysis
        
        Returns:
            Dictionary with analysis results compatible with _apply_contextual_tags
        """
        if not CORPUS_ANALYSIS_AVAILABLE:
            logger.warning("CorpusAnalyzer not available")
            return {}
        
        try:
            # Create analyzer
            from ingestion.analysis import CorpusAnalysisConfig
            
            analysis_config = CorpusAnalysisConfig(
                sample_size=self.config.preprocessing_sample_size,
                min_entity_frequency=self.config.min_entity_frequency,
                extract_relationships=self.config.enable_relationships,
                build_knowledge_graph=self.config.enable_knowledge_graph,
                max_contextual_tags=self.config.max_contextual_tags
            )
            
            analyzer = CorpusAnalyzer(analysis_config)
            
            # Run analysis
            result = await analyzer.analyze(documents)
            
            # Convert to format expected by _apply_contextual_tags
            return {
                'entities_by_type': result.entities_by_type,
                'common_topics': result.common_topics,
                'relationships': result.relationships,
                'knowledge_graph': result.knowledge_graph,
                'total_entities': result.total_entities,
                'documents_analyzed': result.documents_analyzed
            }
        
        except Exception as e:
            logger.error(f"Error running corpus analysis: {e}")
            return {}
    
    def _normalize_tag(self, text: str) -> str:
        """
        Normalize text to tag format.
        
        Args:
            text: Text to normalize
        
        Returns:
            Normalized tag string (lowercase, hyphens, no spaces)
        """
        return text.lower().replace(' ', '-').replace('_', '-').strip().strip('-')
    
    def get_tag_collection(self) -> TagCollection:
        """
        Get complete tag collection.
        
        Returns:
            TagCollection with all tags
        """
        return self.tag_collection
    
    def get_tag_metadata(self) -> Dict:
        """
        Get complete tag metadata for MCP storage.
        
        Returns:
            Dictionary with tag collection and metadata
        """
        return {
            "tag_collection": self.tag_collection.to_dict(),
            "config": {
                "enable_user_tags": self.config.enable_user_tags,
                "enable_preprocessing": self.config.enable_preprocessing,
                "max_tags_per_document": self.config.max_tags_per_document
            }
        }

