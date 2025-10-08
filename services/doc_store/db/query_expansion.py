"""Query expansion with domain-specific synonyms.

This module provides query expansion capabilities for improving search recall
by adding domain-specific synonyms and related terms.
"""

from typing import List, Set, Dict
import logging

logger = logging.getLogger(__name__)

# Domain-specific synonym mappings (Warhammer 40K focused)
WARHAMMER_SYNONYMS = {
    'emperor': ['Emperor of Mankind', 'Master of Mankind', 'God-Emperor', 'Imperium'],
    'primarch': ['Primarchs', 'gene-son', 'gene-sons', 'gene-father', 'Primarch'],
    'space marine': ['Astartes', 'Legiones Astartes', 'Space Marines', 'Marine'],
    'heresy': ['Horus Heresy', 'Great Betrayal', 'civil war', 'rebellion'],
    'chaos': ['Chaos Gods', 'Ruinous Powers', 'Dark Gods', 'Warp', 'Chaos'],
    'traitor': ['Traitor Legions', 'Fallen', 'Heretic Astartes', 'rebels'],
    'loyalist': ['Loyalist Legions', 'Faithful', 'loyal'],
    'horus': ['Warmaster', 'Warmaster Horus', 'Horus Lupercal'],
    'legion': ['Legions', 'Space Marine Legion', 'Astartes Legion'],
    'imperium': ['Imperium of Man', 'Imperial', 'Empire'],
    'terra': ['Terra', 'Holy Terra', 'Earth'],
    'warp': ['Immaterium', 'Warp', 'Sea of Souls', 'Empyrean'],
    'corrupted': ['corruption', 'tainted', 'fallen', 'corrupted'],
    'battle': ['war', 'conflict', 'siege', 'campaign', 'battle'],
    'chronology': ['timeline', 'history', 'events', 'chronology', 'sequence'],
}

# Generic synonyms for common query patterns
GENERIC_SYNONYMS = {
    'overview': ['summary', 'introduction', 'about', 'overview'],
    'cause': ['reason', 'led to', 'resulted in', 'why', 'origins'],
    'effect': ['result', 'consequence', 'impact', 'outcome'],
    'compare': ['difference', 'versus', 'vs', 'comparison', 'contrast'],
    'list': ['enumerate', 'show', 'name', 'identify'],
    'explain': ['describe', 'detail', 'elaborate', 'clarify'],
}

# Combine all synonyms
ALL_SYNONYMS = {**WARHAMMER_SYNONYMS, **GENERIC_SYNONYMS}


def expand_query(query: str, max_expansions: int = 5) -> List[str]:
    """
    Expand query with domain-specific synonyms.
    
    Args:
        query: Original search query
        max_expansions: Maximum number of synonym variations to add
        
    Returns:
        List of query variations including original and expanded terms
    """
    expanded = [query]  # Always include original query
    query_lower = query.lower()
    words = query_lower.split()
    
    # Track added expansions to avoid duplicates
    added_expansions: Set[str] = set()
    
    for word in words:
        if word in ALL_SYNONYMS:
            for synonym in ALL_SYNONYMS[word][:max_expansions]:
                if synonym not in added_expansions:
                    # Create variant by replacing original word with synonym
                    expanded.append(synonym)
                    added_expansions.add(synonym)
                    
                    if len(added_expansions) >= max_expansions:
                        break
        
        if len(added_expansions) >= max_expansions:
            break
    
    logger.debug(f"Expanded query '{query}' to {len(expanded)} variations")
    return expanded


def extract_keywords_with_synonyms(query: str) -> List[str]:
    """
    Extract keywords from query and add relevant synonyms.
    
    Args:
        query: Search query
        
    Returns:
        List of unique keywords including original terms and synonyms
    """
    import re
    
    # Common stop words to filter out
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'about', 'as', 'into', 'through', 'during',
        'what', 'when', 'where', 'who', 'which', 'why', 'how', 'tell', 'me',
        'is', 'are', 'was', 'were', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might',
        'provide', 'give', 'describe', 'explain', 'including', 'comprehensive'
    }
    
    # Extract words
    words = re.findall(r'\b\w+\b', query.lower())
    
    # Filter stop words and short words, then deduplicate
    keywords = list(dict.fromkeys([w for w in words if w not in stop_words and len(w) > 2]))
    
    # Add synonyms for keywords
    expanded_keywords = list(keywords)  # Start with original keywords
    
    for keyword in keywords[:3]:  # Only expand top 3 keywords
        if keyword in ALL_SYNONYMS:
            # Add first 2 synonyms for each keyword
            for synonym in ALL_SYNONYMS[keyword][:2]:
                synonym_lower = synonym.lower()
                if synonym_lower not in expanded_keywords:
                    expanded_keywords.append(synonym_lower)
    
    return expanded_keywords


def get_synonym_patterns(keyword: str) -> List[str]:
    """
    Get all synonym patterns for a given keyword.
    
    Args:
        keyword: The keyword to find synonyms for
        
    Returns:
        List of synonyms including the original keyword
    """
    keyword_lower = keyword.lower()
    
    if keyword_lower in ALL_SYNONYMS:
        return [keyword] + ALL_SYNONYMS[keyword_lower]
    
    return [keyword]

