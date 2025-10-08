"""Contextual response generation for MCP queries.

This module provides intelligent, context-aware responses based on query intent
and available training documents.
"""

import re
from typing import List, Dict, Any, Tuple


def extract_key_terms(query: str) -> List[str]:
    """Extract key terms from query for suggestions."""
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'about', 'as', 'into', 'through', 'tell',
        'me', 'what', 'when', 'where', 'who', 'which', 'why', 'how', 'is',
        'are', 'was', 'were', 'provide', 'give', 'describe', 'explain'
    }
    
    words = re.findall(r'\b\w+\b', query.lower())
    return [w for w in words if w not in stop_words and len(w) > 3]


def classify_query_intent(query: str) -> str:
    """Classify query intent for contextual responses."""
    query_lower = query.lower()
    
    # Overview/General
    if any(w in query_lower for w in ['overview', 'what is', 'tell me about', 'explain', 'summary']):
        return 'overview'
    
    # Cause/Reason
    if any(w in query_lower for w in ['why', 'cause', 'reason', 'led to', 'resulted']):
        return 'causation'
    
    # Timeline/Chronology
    if any(w in query_lower for w in ['when', 'timeline', 'chronology', 'sequence', 'order']):
        return 'temporal'
    
    # Comparison
    if any(w in query_lower for w in ['compare', 'difference', 'versus', 'vs', 'contrast']):
        return 'comparison'
    
    # Specific detail
    if any(w in query_lower for w in ['who', 'which', 'name', 'list', 'identify']):
        return 'specific'
    
    return 'general'


def extract_main_topic(query: str) -> str:
    """Extract the main topic from query."""
    key_terms = extract_key_terms(query)
    if key_terms:
        return ' '.join(key_terms[:3])  # First 3 key terms
    return "this topic"


def generate_search_suggestions(key_terms: List[str]) -> List[str]:
    """Generate alternative search suggestions."""
    suggestions = []
    
    # Suggest breaking down complex queries
    if len(key_terms) > 2:
        suggestions.append(f"Try searching for just '{key_terms[0]}'")
        suggestions.append(f"Try searching for '{key_terms[0]} {key_terms[1]}'")
    
    # Suggest broader terms
    if key_terms:
        suggestions.append(f"Try broader terms related to '{key_terms[0]}'")
    
    # Suggest more specific query
    suggestions.append("Try adding more specific details to your question")
    
    # Suggest checking spelling
    suggestions.append("Double-check the spelling of key terms")
    
    return suggestions[:4]  # Return top 4


def generate_no_results_response(query: str, doc_store_status: str = "available") -> str:
    """Generate helpful response when no documents found."""
    key_terms = extract_key_terms(query)
    main_topic = extract_main_topic(query)
    suggestions = generate_search_suggestions(key_terms)
    
    if doc_store_status != "available":
        return f"""
Unable to access training documents due to system issues ({doc_store_status}).
Please try again in a moment, or contact support if the issue persists.
"""
    
    response = f"""I couldn't find specific documents matching your query about "{main_topic}".

This could mean:
• The training data doesn't include information on this specific topic
• The query terms might need to be rephrased
• Related information might be under different terminology

Suggested searches:
"""
    
    for suggestion in suggestions:
        response += f"• {suggestion}\n"
    
    response += "\nWould you like to try a more specific or different query?"
    
    return response.strip()


def generate_intent_based_intro(intent: str, topic: str) -> str:
    """Generate contextual introduction based on query intent."""
    intros = {
        'overview': f"Here's an overview based on the training documents about {topic}:",
        'causation': f"Based on the training documents, here's what led to {topic}:",
        'temporal': f"Here's the timeline of events related to {topic}:",
        'comparison': f"Here's a comparison based on the available training documents:",
        'specific': f"Here's specific information about {topic}:",
        'general': f"Based on the training documents, here's what I found:"
    }
    
    return intros.get(intent, intros['general'])


def extract_relevant_snippets(query: str, docs: List[Dict], max_snippets: int = 3) -> List[Dict]:
    """Extract most relevant snippets from documents."""
    import json
    
    key_terms = extract_key_terms(query)
    snippets = []
    
    for doc in docs:
        content = doc.get('content', '')
        
        # Parse metadata if it's a string
        metadata = doc.get('metadata', {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        
        # Split into paragraphs
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            # Count keyword matches
            keyword_count = sum(1 for term in key_terms if term.lower() in para.lower())
            if keyword_count > 0:
                # Trim long paragraphs
                snippet_text = para[:500] + '...' if len(para) > 500 else para
                snippets.append({
                    'doc_id': doc.get('id', 'unknown'),
                    'content': snippet_text,
                    'relevance': keyword_count,
                    'source': metadata.get('source_url', 'unknown')
                })
        
        if len(snippets) >= max_snippets * 3:  # Get extras for sorting
            break
    
    # Sort by relevance and return top snippets
    snippets.sort(key=lambda x: x['relevance'], reverse=True)
    return snippets[:max_snippets]


def generate_synthesis_response(query: str, docs: List[Dict], confidence: float) -> Dict[str, Any]:
    """Synthesize documents into contextual answer."""
    # Classify query intent
    intent = classify_query_intent(query)
    main_topic = extract_main_topic(query)
    
    # Extract relevant snippets
    snippets = extract_relevant_snippets(query, docs, max_snippets=3)
    
    # Generate contextual intro
    intro = generate_intent_based_intro(intent, main_topic)
    
    # Build response
    response = f"{intro}\n\n"
    
    if snippets:
        for i, snippet in enumerate(snippets, 1):
            source = snippet.get('source', 'unknown')
            content = snippet['content']
            
            # Clean up markdown formatting for better readability
            content = content.replace('#', '').strip()
            
            response += f"**Excerpt {i}** (Source: {source}):\n{content}\n\n"
    else:
        # Fallback to first document content
        if docs:
            first_doc = docs[0]
            content = first_doc.get('content', '')[:1000]
            response += f"{content}...\n\n"
    
    # Add metadata
    source_ids = [d.get('id', 'unknown') for d in docs[:3]]
    
    return {
        'answer': response.strip(),
        'sources': source_ids,
        'confidence': confidence,
        'intent': intent,
        'snippets_used': len(snippets)
    }


def generate_contextual_response(query_text: str, docs: List[Dict], doc_store_status: str = "available") -> Dict[str, Any]:
    """
    Generate contextual response based on query and results.
    
    Args:
        query_text: Original query
        docs: List of documents from doc_store
        doc_store_status: Status of doc_store ("available", "error", "unavailable")
    
    Returns:
        Dict with 'answer', 'sources', and 'confidence'
    """
    # Case 1: No documents found
    if not docs or len(docs) == 0:
        return {
            'answer': generate_no_results_response(query_text, doc_store_status),
            'sources': [],
            'confidence': 0.0,
            'intent': classify_query_intent(query_text),
            'snippets_used': 0
        }
    
    # Case 2: Low confidence (only 1-2 docs)
    if len(docs) <= 2:
        confidence = 0.5
    else:
        confidence = 0.85
    
    # Case 3: Generate synthesis
    return generate_synthesis_response(query_text, docs, confidence)

