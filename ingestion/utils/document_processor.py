"""
Document post-processing for human-readable output.

Handles:
- Text cleanup (spacing, formatting)
- Deduplication of similar content
- Content summarization
- Section organization
- Hierarchical topic-based organization (NEW!)
"""
import re
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ProcessedSection:
    """A cleaned and organized document section."""
    title: str
    content: str
    sources: List[str]
    relevance_score: float
    topic_hierarchy: Optional[Dict[str, List[str]]] = None  # NEW: main, sub, related topics


class DocumentProcessor:
    """Post-process raw crawled data into human-readable documents."""
    
    def __init__(self):
        self.seen_content_hashes = set()
    
    def clean_wiki_text(self, text: str) -> str:
        """
        Clean raw wiki/HTML text for better readability.
        
        Fixes:
        - Missing spaces between words
        - Excess whitespace
        - Wiki markup artifacts
        - HTML entities
        """
        if not text:
            return ""
        
        # Fix common wiki formatting issues
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space before caps
        text = re.sub(r'\s+', ' ', text)  # Collapse whitespace
        text = re.sub(r'\*\*\*+', '**', text)  # Fix excessive bold
        text = re.sub(r'===+', '==', text)  # Fix excessive headers
        
        # Remove wiki table artifacts
        text = re.sub(r'\{[^}]*\}', '', text)  # Remove template calls
        text = re.sub(r'\[\[File:.*?\]\]', '', text, flags=re.IGNORECASE)  # Remove file refs
        text = re.sub(r'\[\[Category:.*?\]\]', '', text, flags=re.IGNORECASE)  # Remove categories
        
        # Clean up links but keep text
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)  # [[link|text]] -> text
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)  # [[link]] -> link
        
        # Remove HTML comments and tags
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s*([a-zA-Z])', r'\1 \2', text)
        
        # Final cleanup
        text = text.strip()
        text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
        
        return text
    
    def get_content_hash(self, text: str) -> str:
        """
        Get a simple hash for deduplication.
        
        Uses first 100 chars of normalized text.
        """
        normalized = re.sub(r'\s+', '', text.lower())[:100]
        return normalized
    
    def deduplicate_sections(
        self,
        sections: List[Tuple[str, str, str, float]]
    ) -> List[Tuple[str, str, str, float]]:
        """
        Remove duplicate or highly similar sections.
        
        Args:
            sections: List of (title, content, source, score) tuples
        
        Returns:
            Deduplicated list
        """
        seen_hashes: Set[str] = set()
        seen_titles: Set[str] = set()
        unique_sections = []
        
        for title, content, source, score in sections:
            # Normalize title for comparison
            normalized_title = title.lower().strip()
            
            # Get content hash
            content_hash = self.get_content_hash(content)
            
            # Skip if we've seen this title or very similar content
            if normalized_title in seen_titles:
                continue
            
            if content_hash in seen_hashes:
                continue
            
            # Keep this section
            seen_titles.add(normalized_title)
            seen_hashes.add(content_hash)
            unique_sections.append((title, content, source, score))
        
        return unique_sections
    
    def extract_key_info(self, text: str, max_length: int = 500) -> str:
        """
        Extract key information from text, focusing on first few sentences.
        
        Args:
            text: Raw text
            max_length: Maximum length of extracted text
        
        Returns:
            Key excerpt
        """
        # Clean the text first
        text = self.clean_wiki_text(text)
        
        if not text:
            return ""
        
        # Split into sentences (rough)
        sentences = re.split(r'[.!?]+\s+', text)
        
        # Take first few sentences up to max_length
        result = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if current_length + len(sentence) > max_length:
                break
            
            result.append(sentence)
            current_length += len(sentence)
        
        excerpt = '. '.join(result)
        if excerpt and not excerpt.endswith('.'):
            excerpt += '.'
        
        return excerpt
    
    def organize_by_topic(
        self,
        sections: List[Tuple[str, str, str, float]]
    ) -> Dict[str, List[Tuple[str, str, str, float]]]:
        """
        Group sections by common topics/themes.
        
        Args:
            sections: List of (title, content, source, score) tuples
        
        Returns:
            Dict mapping topic to sections
        """
        topics: Dict[str, List[Tuple[str, str, str, float]]] = {}
        
        for section in sections:
            title, content, source, score = section
            
            # Extract main topic from title (first significant word)
            words = title.split()
            main_topic = words[0] if words else "General"
            
            # Normalize topic
            main_topic = main_topic.strip(':').title()
            
            if main_topic not in topics:
                topics[main_topic] = []
            
            topics[main_topic].append(section)
        
        return topics
    
    def synthesize_content(
        self,
        sections: List[Tuple[str, str, str, float]],
        topic: str
    ) -> str:
        """
        Synthesize multiple sections into coherent content.
        
        Args:
            sections: List of (title, content, source, score) tuples
            topic: Topic name
        
        Returns:
            Synthesized content block
        """
        if not sections:
            return ""
        
        # Extract key information from each section
        excerpts = []
        sources = []
        
        for title, content, source, score in sections[:5]:  # Top 5 only
            # Extract key info
            excerpt = self.extract_key_info(content, max_length=300)
            if excerpt:
                excerpts.append(excerpt)
                sources.append(source)
        
        if not excerpts:
            return ""
        
        # Build synthesized content
        content_parts = []
        
        # Add overview
        content_parts.append(f"### {topic}\n")
        
        # Add synthesized information
        for i, excerpt in enumerate(excerpts, 1):
            content_parts.append(f"{excerpt}\n")
            if i < len(excerpts):
                content_parts.append("")  # Blank line between excerpts
        
        # Add sources
        if sources:
            content_parts.append("\n**Sources:**")
            for source in sources[:3]:  # Top 3 sources
                content_parts.append(f"- {source}")
        
        return '\n'.join(content_parts)
    
    def organize_by_hierarchical_topics(
        self,
        sections: List[Tuple[str, str, str, float]],
        hierarchical_tags: Optional[List[str]] = None
    ) -> Dict[str, List[Tuple[str, str, str, float]]]:
        """
        Organize sections using hierarchical topic structure (NEW!).
        
        Uses AI-extracted hierarchical tags to intelligently group content:
        - Main topics get top priority
        - Sub-topics are grouped under main topics
        - Related topics create connections
        
        Args:
            sections: List of (title, content, source, score) tuples
            hierarchical_tags: List of hierarchical tags (e.g., 'topic:main:imperial-palace')
        
        Returns:
            Dict with 'main', 'sub', 'related' keys, each containing organized sections
        """
        if not hierarchical_tags:
            # Fallback to simple topic organization
            return {'main': sections, 'sub': [], 'related': []}
        
        # Extract and categorize hierarchical topics
        main_topics = []
        sub_topics = []
        related_topics = []
        
        for tag in hierarchical_tags:
            if ':main:' in tag:
                topic = tag.replace('topic:main:', '').replace('-', ' ').title()
                main_topics.append(topic)
            elif ':sub:' in tag:
                topic = tag.replace('topic:sub:', '').replace('topic:main:', '').replace('-', ' ').title()
                sub_topics.append(topic)
            elif ':related:' in tag or ':tangential:' in tag:
                topic = tag.replace('topic:related:', '').replace('topic:tangential:', '').replace('-', ' ').title()
                related_topics.append(topic)
        
        # Organize sections by hierarchy
        organized = {
            'main': [],
            'sub': [],
            'related': []
        }
        
        for section in sections:
            title, content, source, score = section
            combined_text = (title + ' ' + content).lower()
            
            # Check which hierarchy level this section belongs to
            main_matches = sum(1 for t in main_topics if t.lower() in combined_text)
            sub_matches = sum(1 for t in sub_topics if t.lower() in combined_text)
            related_matches = sum(1 for t in related_topics if t.lower() in combined_text)
            
            # Assign to the hierarchy level with most matches
            if main_matches > 0 and main_matches >= sub_matches and main_matches >= related_matches:
                organized['main'].append(section)
            elif sub_matches > 0 and sub_matches >= related_matches:
                organized['sub'].append(section)
            elif related_matches > 0:
                organized['related'].append(section)
            else:
                # No clear match, default to main
                organized['main'].append(section)
        
        return organized
    
    def create_hierarchical_document_structure(
        self,
        main_sections: List[Tuple[str, str, str, float]],
        sub_sections: List[Tuple[str, str, str, float]],
        related_sections: List[Tuple[str, str, str, float]]
    ) -> str:
        """
        Create a well-structured document using hierarchical sections (NEW!).
        
        Args:
            main_sections: Primary topic sections (highest priority)
            sub_sections: Supporting detail sections
            related_sections: Contextual/tangential sections
        
        Returns:
            Formatted markdown document structure
        """
        document_parts = []
        
        # Main Topics Section
        if main_sections:
            document_parts.append("## Primary Topics\n")
            document_parts.append("*Core subjects covered in depth:*\n\n")
            
            for title, content, source, score in main_sections[:5]:  # Top 5
                excerpt = self.extract_key_info(content, max_length=400)
                document_parts.append(f"### {title}\n")
                document_parts.append(f"{excerpt}\n")
                document_parts.append(f"*Source: {source}*\n\n")
        
        # Sub-Topics Section
        if sub_sections:
            document_parts.append("## Supporting Details\n")
            document_parts.append("*Additional information and specifics:*\n\n")
            
            for title, content, source, score in sub_sections[:8]:  # Top 8
                excerpt = self.extract_key_info(content, max_length=200)
                document_parts.append(f"### {title}\n")
                document_parts.append(f"{excerpt}\n\n")
        
        # Related Topics Section
        if related_sections:
            document_parts.append("## Related Context\n")
            document_parts.append("*Broader connections and background:*\n\n")
            
            for title, content, source, score in related_sections[:3]:  # Top 3
                excerpt = self.extract_key_info(content, max_length=150)
                document_parts.append(f"### {title}\n")
                document_parts.append(f"{excerpt}\n\n")
        
        return ''.join(document_parts)

