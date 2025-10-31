"""
Document Value Scoring System

Assigns a quality/value score (0-100) to each document based on:
- Content length and depth
- Technical density
- Glossary term matches
- System/architecture references
- Structural quality (headers, lists, code blocks)
- Category-based importance

Higher scores = higher value documents for RAG.
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentScore:
    """Complete scoring breakdown for a document."""
    total_score: float  # 0-100
    breakdown: Dict[str, float]
    matched_terms: List[str]
    matched_systems: List[str]
    quality_grade: str  # S, A, B, C, D
    reasoning: str


class DocumentScorer:
    """
    Scores documents based on multiple quality signals.
    
    Scoring factors:
    1. Content depth (20 points): Length, detail level
    2. Technical density (15 points): Code, technical terms
    3. Glossary matches (20 points): User-provided terms
    4. System references (15 points): Architecture, components
    5. Structural quality (15 points): Headers, organization
    6. Category importance (15 points): Docs > Code > Tests
    
    Total: 100 points
    """
    
    # Default glossary terms (can be extended by user)
    DEFAULT_GLOSSARY = {
        # Core systems
        "chromadb", "postgresql", "redis", "docker", "fastapi",
        "ollama", "llama", "embedding", "vector database",
        
        # Architecture patterns
        "microservice", "api gateway", "message queue", "worker",
        "stream processing", "event-driven", "async", "temporal",
        
        # RAG concepts
        "retrieval augmented generation", "semantic search",
        "similarity search", "context window", "prompt engineering",
        
        # Data concepts
        "ingestion", "normalization", "deduplication", "versioning",
        "snapshot", "enrichment", "metadata", "indexing"
    }
    
    # System/component terms
    DEFAULT_SYSTEMS = {
        "ecosystem-mcp", "ingestion worker", "job processor",
        "query engine", "embedding service", "dashboard",
        "temporal rag", "multi-pass query", "context-aware",
        "document cleanup", "intelligent filtering"
    }
    
    # Technical indicators (regex patterns)
    TECHNICAL_PATTERNS = [
        r'\bclass\s+\w+',  # Class definitions
        r'\bdef\s+\w+',  # Function definitions
        r'\bimport\s+',  # Imports
        r'\bfrom\s+\w+\s+import',  # From imports
        r'```\w*\n',  # Code blocks
        r'\b(?:GET|POST|PUT|DELETE|PATCH)\s+/',  # API endpoints
        r'\b(?:SELECT|INSERT|UPDATE|DELETE)\b',  # SQL
        r'\b(?:async|await)\b',  # Async code
    ]
    
    def __init__(
        self,
        custom_glossary: Optional[Set[str]] = None,
        custom_systems: Optional[Set[str]] = None
    ):
        """
        Initialize scorer with optional custom terms.
        
        Args:
            custom_glossary: Additional glossary terms to match
            custom_systems: Additional system names to match
        """
        # Combine default + custom terms
        self.glossary = self.DEFAULT_GLOSSARY.copy()
        if custom_glossary:
            self.glossary.update(term.lower() for term in custom_glossary)
        
        self.systems = self.DEFAULT_SYSTEMS.copy()
        if custom_systems:
            self.systems.update(system.lower() for system in custom_systems)
        
        # Compile technical patterns
        self.technical_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.TECHNICAL_PATTERNS
        ]
        
        logger.info(
            f"📊 DocumentScorer initialized: "
            f"{len(self.glossary)} glossary terms, "
            f"{len(self.systems)} systems"
        )
    
    def score_document(
        self,
        content: str,
        file_path: str,
        category: Optional[str] = None
    ) -> DocumentScore:
        """
        Score a document comprehensively.
        
        Args:
            content: Document content (normalized markdown)
            file_path: File path for context
            category: Document category (documentation, source_code, etc.)
        
        Returns:
            Complete DocumentScore with breakdown
        """
        # Calculate individual scores
        depth_score = self._score_content_depth(content)
        technical_score = self._score_technical_density(content)
        glossary_score, glossary_matches = self._score_glossary_matches(content)
        system_score, system_matches = self._score_system_references(content)
        structure_score = self._score_structural_quality(content)
        category_score = self._score_category_importance(file_path, category)
        
        # Build breakdown
        breakdown = {
            "content_depth": depth_score,
            "technical_density": technical_score,
            "glossary_matches": glossary_score,
            "system_references": system_score,
            "structural_quality": structure_score,
            "category_importance": category_score
        }
        
        # Total score (weighted sum)
        total = sum(breakdown.values())
        
        # Determine grade
        grade = self._score_to_grade(total)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(breakdown, glossary_matches, system_matches)
        
        return DocumentScore(
            total_score=round(total, 2),
            breakdown=breakdown,
            matched_terms=glossary_matches,
            matched_systems=system_matches,
            quality_grade=grade,
            reasoning=reasoning
        )
    
    def _score_content_depth(self, content: str) -> float:
        """
        Score based on content length and apparent depth.
        
        Max: 20 points
        
        Factors:
        - Word count (0-10): More words = more detail
        - Paragraph depth (0-5): Longer paragraphs = more explanation
        - Unique words (0-5): Vocabulary richness
        """
        words = content.split()
        word_count = len(words)
        
        # Word count score (0-10)
        # 0 words = 0, 100 words = 3, 500 words = 7, 1000+ words = 10
        if word_count == 0:
            word_score = 0
        elif word_count < 100:
            word_score = word_count / 10
        elif word_count < 500:
            word_score = 3 + (word_count - 100) / 100
        elif word_count < 1000:
            word_score = 7 + (word_count - 500) / 166
        else:
            word_score = 10
        
        # Paragraph depth (0-5)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if not paragraphs:
            paragraph_score = 0
        else:
            avg_paragraph_len = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
            # 20 words/paragraph = 2, 40+ words/paragraph = 5
            paragraph_score = min(5, avg_paragraph_len / 8)
        
        # Vocabulary richness (0-5)
        if not words:
            vocab_score = 0
        else:
            unique_ratio = len(set(w.lower() for w in words)) / len(words)
            vocab_score = unique_ratio * 5
        
        return round(word_score + paragraph_score + vocab_score, 2)
    
    def _score_technical_density(self, content: str) -> float:
        """
        Score based on technical content density.
        
        Max: 15 points
        
        Factors:
        - Code blocks (0-7): Presence of code examples
        - Technical patterns (0-5): Technical syntax
        - Technical terms (0-3): Domain-specific vocabulary
        """
        # Code blocks (0-7)
        code_blocks = content.count('```')
        code_score = min(7, code_blocks * 1.5)
        
        # Technical patterns (0-5)
        pattern_matches = sum(
            len(pattern.findall(content))
            for pattern in self.technical_patterns
        )
        pattern_score = min(5, pattern_matches / 5)
        
        # Technical terms (0-3)
        technical_terms = [
            'architecture', 'infrastructure', 'deployment', 'configuration',
            'implementation', 'algorithm', 'optimization', 'scalability',
            'performance', 'security', 'authentication', 'authorization'
        ]
        content_lower = content.lower()
        term_count = sum(1 for term in technical_terms if term in content_lower)
        term_score = min(3, term_count / 3)
        
        return round(code_score + pattern_score + term_score, 2)
    
    def _score_glossary_matches(self, content: str) -> Tuple[float, List[str]]:
        """
        Score based on glossary term matches.
        
        Max: 20 points
        
        More matches = higher value for RAG queries.
        """
        content_lower = content.lower()
        
        # Find all matching terms
        matches = []
        for term in self.glossary:
            # Use word boundaries for better matching
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, content_lower):
                matches.append(term)
        
        # Score: 0 matches = 0, 5 matches = 10, 10+ matches = 20
        if not matches:
            score = 0
        elif len(matches) < 5:
            score = len(matches) * 2
        elif len(matches) < 10:
            score = 10 + (len(matches) - 5)
        else:
            score = 20
        
        return round(score, 2), matches
    
    def _score_system_references(self, content: str) -> Tuple[float, List[str]]:
        """
        Score based on system/component references.
        
        Max: 15 points
        
        Documents that reference actual systems are more valuable.
        """
        content_lower = content.lower()
        
        # Find matching systems
        matches = []
        for system in self.systems:
            if system in content_lower:
                matches.append(system)
        
        # Score: 0 = 0, 2 = 7, 4+ = 15
        if not matches:
            score = 0
        elif len(matches) == 1:
            score = 5
        elif len(matches) == 2:
            score = 10
        else:
            score = 15
        
        return round(score, 2), matches
    
    def _score_structural_quality(self, content: str) -> float:
        """
        Score based on document structure.
        
        Max: 15 points
        
        Factors:
        - Headers (0-7): Well-organized with sections
        - Lists (0-4): Structured information
        - Links/references (0-4): Connected to other resources
        """
        # Headers (0-7)
        header_count = len(re.findall(r'^#{1,6}\s+.+$', content, re.MULTILINE))
        header_score = min(7, header_count)
        
        # Lists (0-4)
        list_items = len(re.findall(r'^[\*\-\+]\s+', content, re.MULTILINE))
        list_score = min(4, list_items / 5)
        
        # Links/references (0-4)
        links = len(re.findall(r'\[.+?\]\(.+?\)', content))
        link_score = min(4, links / 3)
        
        return round(header_score + list_score + link_score, 2)
    
    def _score_category_importance(
        self,
        file_path: str,
        category: Optional[str] = None
    ) -> float:
        """
        Score based on file category/type.
        
        Max: 15 points
        
        Priority:
        - Architecture docs: 15
        - README, documentation: 12-13
        - API/design docs: 10-11
        - Source code: 7-8
        - Tests: 4-5
        - Configs: 2-3
        - Other: 5
        """
        path_lower = file_path.lower()
        
        # Architecture documentation (highest value)
        if 'architecture' in path_lower or 'design' in path_lower:
            return 15.0
        
        # README and main documentation
        if 'readme' in path_lower:
            return 13.0
        if '/docs/' in path_lower or path_lower.endswith('.md'):
            return 12.0
        
        # API documentation
        if 'api' in path_lower or 'openapi' in path_lower or 'swagger' in path_lower:
            return 11.0
        
        # Source code (by category)
        if category == "documentation":
            return 12.0
        elif category == "source_code":
            # Service/core code
            if '/services/' in path_lower or '/src/' in path_lower:
                return 8.0
            return 7.0
        elif category == "test":
            return 5.0
        elif category == "configuration":
            return 3.0
        
        # Default for unknown
        return 5.0
    
    def _score_to_grade(self, score: float) -> str:
        """
        Convert numeric score to letter grade.
        
        S: 90-100 (Exceptional)
        A: 75-89  (High value)
        B: 60-74  (Good value)
        C: 40-59  (Medium value)
        D: 20-39  (Low value)
        F: 0-19   (Minimal value)
        """
        if score >= 90:
            return "S"
        elif score >= 75:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 40:
            return "C"
        elif score >= 20:
            return "D"
        else:
            return "F"
    
    def _generate_reasoning(
        self,
        breakdown: Dict[str, float],
        glossary_matches: List[str],
        system_matches: List[str]
    ) -> str:
        """Generate human-readable reasoning for the score."""
        reasons = []
        
        # Content depth
        if breakdown["content_depth"] >= 15:
            reasons.append("comprehensive content")
        elif breakdown["content_depth"] >= 10:
            reasons.append("detailed content")
        elif breakdown["content_depth"] < 5:
            reasons.append("brief content")
        
        # Technical density
        if breakdown["technical_density"] >= 10:
            reasons.append("highly technical")
        elif breakdown["technical_density"] >= 5:
            reasons.append("technical")
        
        # Glossary matches
        if glossary_matches:
            if len(glossary_matches) >= 10:
                reasons.append(f"extensive domain coverage ({len(glossary_matches)} terms)")
            elif len(glossary_matches) >= 5:
                reasons.append(f"good domain coverage ({len(glossary_matches)} terms)")
            else:
                reasons.append(f"{len(glossary_matches)} domain terms")
        
        # System references
        if system_matches:
            reasons.append(f"references {len(system_matches)} systems")
        
        # Structure
        if breakdown["structural_quality"] >= 10:
            reasons.append("well-structured")
        
        # Category
        if breakdown["category_importance"] >= 12:
            reasons.append("critical documentation")
        elif breakdown["category_importance"] >= 8:
            reasons.append("core content")
        
        return ", ".join(reasons) if reasons else "basic content"


# ============================================================
# Global Scorer Instance
# ============================================================

_scorer_instance: Optional[DocumentScorer] = None


def get_document_scorer(
    custom_glossary: Optional[Set[str]] = None,
    custom_systems: Optional[Set[str]] = None
) -> DocumentScorer:
    """
    Get or create global document scorer instance.
    
    Args:
        custom_glossary: Additional glossary terms
        custom_systems: Additional system names
    
    Returns:
        DocumentScorer instance
    """
    global _scorer_instance
    
    if _scorer_instance is None or custom_glossary or custom_systems:
        _scorer_instance = DocumentScorer(
            custom_glossary=custom_glossary,
            custom_systems=custom_systems
        )
    
    return _scorer_instance


# ============================================================
# Convenience Functions
# ============================================================

def score_document(
    content: str,
    file_path: str,
    category: Optional[str] = None
) -> DocumentScore:
    """
    Score a document using the global scorer.
    
    Args:
        content: Document content
        file_path: File path
        category: Document category
    
    Returns:
        DocumentScore with breakdown
    """
    scorer = get_document_scorer()
    return scorer.score_document(content, file_path, category)


def load_custom_glossary(glossary_file: Path) -> Set[str]:
    """
    Load custom glossary terms from a file.
    
    Format: One term per line, case-insensitive.
    Lines starting with # are comments.
    
    Args:
        glossary_file: Path to glossary file
    
    Returns:
        Set of glossary terms
    """
    terms = set()
    
    try:
        with open(glossary_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    terms.add(line.lower())
        
        logger.info(f"📖 Loaded {len(terms)} custom glossary terms from {glossary_file}")
    
    except Exception as e:
        logger.error(f"Failed to load glossary from {glossary_file}: {e}")
    
    return terms

