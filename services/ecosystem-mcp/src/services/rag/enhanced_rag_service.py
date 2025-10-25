"""
Enhanced RAG Service with optional multi-signal ranking.

Extends RAGService with optional enhancements while maintaining
backward compatibility. If no config exists, behaves exactly like RAGService.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .rag_service import RAGService
from .config_loader import get_rag_config, OptionalConfigLoader
from ...storage import get_database
from ...storage.repositories import DocumentRepository

logger = logging.getLogger(__name__)


class EnhancedRAGService(RAGService):
    """
    Enhanced RAG service with optional multi-signal ranking.
    
    If no config exists, behaves exactly like RAGService (backward compatible).
    If config exists, applies optional enhancements.
    
    Critical Features:
    - Context-aware exclusions (skip for temporal/gap analysis)
    - Multi-signal ranking (semantic + glossary + quality + recency)
    - Token-rich context building (glossary definitions)
    - Graceful degradation (always works without config)
    """
    
    def __init__(self):
        """Initialize enhanced RAG service."""
        super().__init__()
        
        # Load optional config
        self.config_loader = OptionalConfigLoader()
        self.config = self.config_loader.load_config()
        
        if self.config is None:
            logger.info("EnhancedRAGService: No config found, using standard behavior")
        else:
            logger.info(
                f"EnhancedRAGService: Config loaded with "
                f"{len(self.config.glossary)} glossary terms, "
                f"{len(self.config.exclusions)} exclusion rules"
            )
        
        # Pre-compile exclusion patterns for performance
        self._compiled_exclusions = self._compile_exclusion_patterns()
    
    def _compile_exclusion_patterns(self) -> List[tuple]:
        """Pre-compile exclusion regex patterns for fast filtering."""
        if self.config is None or not self.config.exclusions:
            return []
        
        compiled = []
        for rule in self.config.exclusions:
            try:
                pattern = re.compile(rule.pattern)
                compiled.append((pattern, rule))
            except re.error as e:
                logger.warning(f"Invalid exclusion pattern '{rule.pattern}': {e}")
        
        return compiled
    
    async def ask(
        self,
        question: str,
        n_results: int = 10,
        context: Optional[List[Dict[str, Any]]] = None,
        prefer_recent: bool = True,
        temperature: float = 0.7,
        response_length: int = 1000
    ) -> Dict[str, Any]:
        """
        Answer question with optional enhancements.
        
        Enhancement flow:
        1. Standard retrieval (base RAGService)
        2. Apply optional filters (if config exists)
        3. Apply optional multi-signal ranking (if config exists)
        4. Build enhanced context (if config exists)
        5. Generate answer (always)
        
        Args:
            question: User's question
            n_results: Number of documents to retrieve
            context: Previous conversation context (also used for feature flags!)
            prefer_recent: Whether to boost recent documents
            temperature: LLM temperature
            response_length: Maximum tokens in response
        
        Returns:
            Dict with answer, sources, and metadata
        """
        logger.info(f"Enhanced RAG query: {question[:100]}...")
        
        # Extract context flags if provided
        context_flags = self._extract_context_flags(context)
        
        # Step 0: Check for matching query template (Phase 3)
        matched_template = None
        if self.config and self.config.features_enabled.get('templates'):
            matched_template = self._match_query_template(question)
            if matched_template:
                template_name, template = matched_template
                logger.info(f"✅ Matched template: {template_name}")
                # Override parameters based on template
                n_results = template.documents_needed
                prefer_recent = template.prefer_recent
        
        # Step 1: Standard retrieval (delegates to parent)
        documents = await self._retrieve_with_scoring(
            question,
            n_results=n_results * 2,  # Get extra for filtering
            prefer_recent=prefer_recent
        )
        
        if not documents:
            return {
                "answer": "I don't have enough information to answer that question.",
                "sources": [],
                "confidence": 0.0,
                "metadata": {"reason": "no_relevant_documents"}
            }
        
        # Step 2: Apply optional pre-filtering (context-aware!)
        if self.config and self.config.features_enabled.get('exclusions'):
            documents = await self._apply_exclusion_filters(
                documents, question, context_flags
            )
            logger.info(f"After exclusions: {len(documents)} documents")
        
        # Step 3: Apply optional multi-signal ranking
        if self.config and self._has_any_signal_enhancement():
            documents = await self._apply_multi_signal_ranking(
                documents, question
            )
            logger.info("Applied multi-signal ranking")
        
        # Trim to requested size
        documents = documents[:n_results]
        
        # Step 4: Build context (optionally enhanced)
        if self.config and self.config.features_enabled.get('glossary'):
            context_text = await self._build_enhanced_context(documents, question)
        else:
            context_text = self._build_context(documents)
        
        # Step 5: Generate answer (standard)
        answer = await self._generate_answer(
            question=question,
            context=context_text,
            conversation_history=context,
            temperature=temperature,
            retrieved_documents=documents,
            max_tokens=response_length
        )
        
        # Step 6: Format response with enhancement metadata
        import uuid
        query_id = str(uuid.uuid4())  # Phase 3: Feedback tracking
        
        sources = self._format_sources(documents)
        confidence = self._calculate_confidence(documents, answer)
        
        # Extract matched template name if any (Phase 3)
        matched_template_name = None
        if matched_template:
            matched_template_name = matched_template[0]
        
        result = {
            "query_id": query_id,  # Phase 3: For feedback tracking
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "metadata": {
                "documents_used": len(documents),
                "temperature": temperature,
                "prefer_recent": prefer_recent,
                "top_score": documents[0]["adjusted_score"] if documents else 0.0,
                "enhancements_applied": self._get_applied_enhancements(),
                "matched_template": matched_template_name,  # Phase 3
                "context_flags": context_flags,
                "feedback_endpoint": "/api/v1/feedback"  # Phase 3: Future implementation
            }
        }
        
        return result
    
    def _match_query_template(
        self,
        question: str
    ) -> Optional[Tuple[str, Any]]:
        """
        Match question against query templates using regex patterns.
        
        Phase 3 feature: Pre-optimized query structures.
        
        Args:
            question: User's question
        
        Returns:
            Tuple of (template_name, template) if matched, None otherwise
        """
        if not self.config or not self.config.templates:
            return None
        
        import re
        question_lower = question.lower()
        
        # Try to match each template's patterns
        for template_name, template in self.config.templates.items():
            for pattern in template.patterns:
                try:
                    if re.search(pattern, question_lower, re.IGNORECASE):
                        logger.debug(f"Question matched template '{template_name}' with pattern: {pattern}")
                        return (template_name, template)
                except re.error as e:
                    logger.warning(f"Invalid regex pattern in template '{template_name}': {pattern} - {e}")
                    continue
        
        return None
    
    def _extract_context_flags(
        self,
        context: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, bool]:
        """
        Extract context flags from conversation context.
        
        Context flags tell us to skip certain enhancements:
        - temporal: True → Skip exclusions (need historical docs)
        - gap_analysis: True → Skip exclusions (need all docs to find gaps)
        - doc_generation: True → Modify exclusions (need test examples)
        
        Args:
            context: Conversation context
        
        Returns:
            Dict of boolean flags
        """
        if not context:
            return {}
        
        flags = {}
        
        # Check if any context entry has special flags
        for entry in context:
            if isinstance(entry, dict):
                if entry.get('temporal'):
                    flags['temporal'] = True
                if entry.get('gap_analysis'):
                    flags['gap_analysis'] = True
                if entry.get('doc_generation'):
                    flags['doc_generation'] = True
        
        return flags
    
    async def _apply_exclusion_filters(
        self,
        documents: List[Dict[str, Any]],
        question: str,
        context_flags: Dict[str, bool]
    ) -> List[Dict[str, Any]]:
        """
        Apply exclusion rules to filter out unwanted documents.
        
        CRITICAL: Context-aware filtering!
        - temporal=True → Skip exclusions (need historical docs)
        - gap_analysis=True → Skip exclusions (need all docs)
        - doc_generation=True → Modify exclusions (keep test files)
        
        Fast O(n) filtering using pre-compiled patterns.
        
        Args:
            documents: Documents to filter
            question: User's question
            context_flags: Context flags from conversation
        
        Returns:
            Filtered documents
        """
        if not self._compiled_exclusions:
            return documents
        
        # CRITICAL: Skip exclusions for temporal queries
        if context_flags.get('temporal'):
            logger.info("⏰ Temporal query: Skipping exclusions (need historical docs)")
            return documents
        
        # CRITICAL: Skip exclusions for gap analysis
        if context_flags.get('gap_analysis'):
            logger.info("📊 Gap analysis: Skipping exclusions (need all docs)")
            return documents
        
        # CRITICAL: Modify exclusions for doc generation
        if context_flags.get('doc_generation'):
            logger.info("📝 Doc generation: Keeping test files for examples")
            # Filter out test-related exclusion rules
            effective_exclusions = [
                (pattern, rule) for pattern, rule in self._compiled_exclusions
                if 'test' not in rule.pattern.lower()
            ]
        else:
            effective_exclusions = self._compiled_exclusions
        
        filtered = []
        excluded_count = 0
        
        for doc in documents:
            doc_path = doc.get('path', doc.get('file_path', ''))
            excluded = False
            
            for pattern, rule in effective_exclusions:
                # Check if rule applies to this query type
                if '*' not in rule.applies_to_queries:
                    # TODO: Implement query classification
                    pass
                
                if pattern.search(doc_path):
                    excluded = True
                    excluded_count += 1
                    logger.debug(
                        f"Excluded {doc_path}: {rule.reason}"
                    )
                    break
            
            if not excluded:
                filtered.append(doc)
        
        if excluded_count > 0:
            logger.info(f"Excluded {excluded_count} documents using config rules")
        
        return filtered
    
    async def _apply_multi_signal_ranking(
        self,
        documents: List[Dict[str, Any]],
        question: str
    ) -> List[Dict[str, Any]]:
        """
        Apply multi-signal ranking to documents.
        
        Combines:
        - Semantic similarity (already in adjusted_score)
        - Glossary relevance (if enabled)
        - Content quality (from metadata)
        - Recency (already in adjusted_score)
        - User feedback (future)
        
        Uses normalized additive scoring to prevent over-boosting.
        
        Args:
            documents: Documents to rank
            question: User's question
        
        Returns:
            Re-ranked documents
        """
        # Extract base semantic scores
        semantic_scores = [doc.get('adjusted_score', 0.5) for doc in documents]
        
        # Normalize to [0, 1]
        semantic_normalized = self._normalize_scores(semantic_scores)
        
        # Compute optional signals
        glossary_scores = await self._compute_glossary_scores(documents, question)
        quality_scores = self._compute_quality_scores(documents)
        priority_scores = self._compute_priority_scores(documents)  # Phase 3
        
        # Get signal weights
        weights = self.config.signal_weights if self.config else {
            'semantic': 0.55,  # Higher weight when no other signals
            'glossary': 0.15,
            'priority': 0.0,  # Disabled without config
            'content_quality': 0.15,
            'recency': 0.15
        }
        
        # Combine signals using weighted sum
        for idx, doc in enumerate(documents):
            # Compute base score from weighted signals
            base_score = (
                semantic_normalized[idx] * weights['semantic'] +
                glossary_scores[idx] * weights.get('glossary', 0) +
                quality_scores[idx] * weights.get('content_quality', 0)
                # Note: recency already in adjusted_score from parent
            )
            
            # Apply priority as a multiplier (not weighted sum)
            # Priority acts as a document-level boost
            priority_weight = weights.get('priority', 0.0)
            if priority_weight > 0:
                # Priority scores are 0.5-2.0, apply weighted influence
                priority_adjustment = (priority_scores[idx] - 1.0) * priority_weight
                final_score = base_score * (1.0 + priority_adjustment)
            else:
                final_score = base_score
            
            doc['final_score'] = final_score
            doc['signal_breakdown'] = {
                'semantic': semantic_normalized[idx],
                'glossary': glossary_scores[idx],
                'quality': quality_scores[idx],
                'priority': priority_scores[idx]
            }
        
        # Re-sort by final score
        documents.sort(key=lambda x: x['final_score'], reverse=True)
        
        return documents
    
    async def _compute_glossary_scores(
        self,
        documents: List[Dict[str, Any]],
        question: str
    ) -> List[float]:
        """
        Compute glossary relevance scores.
        
        Returns normalized scores [0, 1] for each document.
        
        Args:
            documents: Documents to score
            question: User's question
        
        Returns:
            List of normalized scores
        """
        if not self.config or not self.config.glossary:
            return [0.0] * len(documents)
        
        # Find relevant glossary terms in question
        question_lower = question.lower()
        relevant_terms = []
        
        for term_name, term_config in self.config.glossary.items():
            # Check if term or any synonym appears in question
            if term_name.lower() in question_lower:
                relevant_terms.append((term_name, term_config))
                continue
            
            for synonym in term_config.synonyms:
                if synonym.lower() in question_lower:
                    relevant_terms.append((term_name, term_config))
                    break
        
        if not relevant_terms:
            return [0.0] * len(documents)
        
        # Score documents based on term mentions
        scores = []
        for doc in documents:
            content = (doc.get('content') or '').lower()
            score = 0.0
            
            for term_name, term_config in relevant_terms:
                # Check term mentions
                if term_name.lower() in content:
                    score += term_config.boost_weight
                
                # Check synonym mentions
                for synonym in term_config.synonyms:
                    if synonym.lower() in content:
                        score += term_config.boost_weight * 0.8  # Slightly lower for synonyms
            
            scores.append(score)
        
        # Normalize to [0, 1]
        return self._normalize_scores(scores)
    
    def _compute_quality_scores(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[float]:
        """
        Compute content quality scores from metadata.
        
        Uses:
        - Document length (from metadata or content)
        - Update frequency (from metadata if available)
        - Cross-references (from metadata if available)
        
        Args:
            documents: Documents to score
        
        Returns:
            List of normalized scores
        """
        scores = []
        
        for doc in documents:
            metadata = doc.get('metadata', {})
            
            # Length signal
            content = doc.get('content') or ''
            length = len(content)
            if length < 200:
                length_score = 0.3  # Probably a stub
            elif length > 2000:
                length_score = 1.0  # Comprehensive
            else:
                length_score = 0.5 + (length - 200) / 3600  # Linear 200-2000
            
            # Update frequency signal (from metadata if available)
            update_count = metadata.get('update_count_90d', 0)
            update_score = min(1.0, update_count / 10)
            
            # Cross-references signal (from metadata if available)
            reference_count = metadata.get('reference_count', 0)
            reference_score = min(1.0, reference_count / 5)
            
            # Combine quality signals
            quality = (
                length_score * 0.4 +
                update_score * 0.3 +
                reference_score * 0.3
            )
            
            scores.append(quality)
        
        return self._normalize_scores(scores)
    
    def _compute_priority_scores(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[float]:
        """
        Compute priority scores based on file path patterns.
        
        Phase 3 feature: User-defined document priorities.
        
        Uses priority rules to boost documents based on path:
        - Critical (2.0): README.md, core docs
        - High (1.5): Architecture, API docs
        - Medium (1.0): Standard docs
        - Low (0.5): Examples, samples
        
        Args:
            documents: Documents to score
        
        Returns:
            List of priority scores (0.5-2.0)
        """
        if not self.config or not self.config.priorities:
            return [1.0] * len(documents)  # Neutral priority
        
        import re
        scores = []
        
        for doc in documents:
            file_path = doc.get('metadata', {}).get('file_path', '')
            
            # Try to match against priority rules (first match wins)
            matched_priority = 1.0  # Default to medium priority
            
            # Check each priority level in order (critical, high, medium, low)
            for priority_name, priority_rule in self.config.priorities.items():
                for pattern in priority_rule.patterns:
                    try:
                        if re.search(pattern, file_path, re.IGNORECASE):
                            matched_priority = priority_rule.level
                            logger.debug(f"Matched priority '{priority_name}' ({priority_rule.level}) for {file_path}")
                            break
                    except re.error as e:
                        logger.warning(f"Invalid priority pattern '{pattern}': {e}")
                        continue
                
                if matched_priority != 1.0:  # Found a match, stop checking
                    break
            
            scores.append(matched_priority)
        
        return scores  # Don't normalize, these are multipliers

    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """
        Normalize scores to [0, 1] using min-max scaling.
        
        Prevents one signal from dominating.
        
        Args:
            scores: Raw scores
        
        Returns:
            Normalized scores
        """
        if not scores:
            return []
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [0.5] * len(scores)  # All equal
        
        return [
            (score - min_score) / (max_score - min_score)
            for score in scores
        ]
    
    async def _build_enhanced_context(
        self,
        documents: List[Dict[str, Any]],
        question: str
    ) -> str:
        """
        Build token-rich context with glossary definitions.
        
        Since Ollama has large context window, include everything useful!
        
        Args:
            documents: Retrieved documents
            question: User's question
        
        Returns:
            Enhanced context string
        """
        parts = []
        
        # Add glossary section if relevant terms found
        if self.config and self.config.glossary:
            glossary_section = self._build_glossary_section(question)
            if glossary_section:
                parts.append(glossary_section)
        
        # Add standard document context
        parts.append(self._build_context(documents))
        
        # Add ranking explanations (helps LLM understand why these docs)
        if documents and 'signal_breakdown' in documents[0]:
            parts.append(self._build_ranking_explanation(documents))
        
        return "\n\n".join(parts)
    
    def _build_glossary_section(self, question: str) -> Optional[str]:
        """
        Build glossary section with relevant terms.
        
        Args:
            question: User's question
        
        Returns:
            Glossary markdown or None
        """
        if not self.config or not self.config.glossary:
            return None
        
        question_lower = question.lower()
        relevant_terms = []
        
        for term_name, term_config in self.config.glossary.items():
            if term_name.lower() in question_lower:
                relevant_terms.append(term_config)
                continue
            
            for synonym in term_config.synonyms:
                if synonym.lower() in question_lower:
                    relevant_terms.append(term_config)
                    break
        
        if not relevant_terms:
            return None
        
        lines = ["## 📚 Domain Glossary", ""]
        for term in relevant_terms[:5]:  # Max 5 terms
            lines.append(f"**{term.term}:** {term.description}")
            if term.synonyms:
                lines.append(f"*Also known as:* {', '.join(term.synonyms)}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _build_ranking_explanation(self, documents: List[Dict[str, Any]]) -> str:
        """
        Build explanation of why documents were selected.
        
        Args:
            documents: Ranked documents
        
        Returns:
            Explanation markdown
        """
        lines = ["## 🎯 Why These Documents", ""]
        
        for idx, doc in enumerate(documents[:5], 1):  # Top 5
            if 'signal_breakdown' not in doc:
                continue
            
            signals = doc['signal_breakdown']
            top_signal = max(signals.items(), key=lambda x: x[1])
            
            lines.append(
                f"{idx}. **{doc.get('path', 'Unknown')}** - "
                f"Selected primarily for {top_signal[0]} ({top_signal[1]:.2f})"
            )
        
        return "\n".join(lines)
    
    def _has_any_signal_enhancement(self) -> bool:
        """Check if any signal enhancement is enabled."""
        if not self.config:
            return False
        
        return any([
            self.config.features_enabled.get('glossary'),
            self.config.features_enabled.get('priorities'),
            self.config.features_enabled.get('feedback')
        ])
    
    def _get_applied_enhancements(self) -> List[str]:
        """Get list of enhancements that were applied."""
        if not self.config:
            return []
        
        enhancements = []
        
        if self.config.features_enabled.get('exclusions') and self._compiled_exclusions:
            enhancements.append(f"exclusions ({len(self.config.exclusions)} rules)")
        
        if self.config.features_enabled.get('glossary') and self.config.glossary:
            enhancements.append(f"glossary ({len(self.config.glossary)} terms)")
        
        if self._has_any_signal_enhancement():
            enhancements.append("multi-signal ranking")
        
        return enhancements


# Global enhanced RAG service instance
_enhanced_rag_service: Optional[EnhancedRAGService] = None


def get_enhanced_rag_service() -> EnhancedRAGService:
    """Get global enhanced RAG service instance."""
    global _enhanced_rag_service
    if _enhanced_rag_service is None:
        _enhanced_rag_service = EnhancedRAGService()
    return _enhanced_rag_service

