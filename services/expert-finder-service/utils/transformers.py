"""
Data transformation utilities for expert-finder-service.

Provides functions to transform data between different formats,
particularly converting external service responses to internal models.
"""

from typing import List, Dict, Any


def user_dict_to_expert(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform user-store data format to expert format.
    
    Standardizes the data structure from external user-store service
    to the internal expert representation used throughout the service.
    
    Args:
        user_data: Raw user data from user-store service
        
    Returns:
        Transformed expert data with standardized field names
        
    Examples:
        >>> user_data = {
        ...     "id": "user123",
        ...     "name": "Alice Smith",
        ...     "role": "Backend Developer",
        ...     "seniority": "senior",
        ...     "topics": ["Python", "FastAPI"],
        ...     "tags": ["backend"],
        ...     "subscribed_services": ["user-store"],
        ...     "created_at": "2024-01-01T00:00:00Z"
        ... }
        >>> expert = user_dict_to_expert(user_data)
        >>> expert["user_id"]
        'user123'
        >>> expert["services"]
        ['user-store']
    """
    return {
        "user_id": user_data.get("id"),
        "name": user_data.get("name", "Unknown"),
        "role": user_data.get("role"),
        "seniority": user_data.get("seniority", "junior"),
        "topics": user_data.get("topics", []),
        "tags": user_data.get("tags", []),
        "services": user_data.get("subscribed_services", []),
        "created_at": user_data.get("created_at"),
        # Additional fields that might be present
        "email": user_data.get("email"),
        "team_id": user_data.get("team_id"),
        "location": user_data.get("location"),
    }


def enrich_with_documents(expert: Dict[str, Any], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Enrich expert data with document information.
    
    Adds document count and list of recent documents to expert data.
    Used to enhance expert profiles with their contributions.
    
    Args:
        expert: Expert data to enrich
        documents: List of documents authored by the expert
        
    Returns:
        Enriched expert data with document_count and recent_documents fields
        
    Examples:
        >>> expert = {"user_id": "user123", "name": "Alice"}
        >>> documents = [
        ...     {"id": "doc1", "title": "Python Guide", "created_at": "2024-01-02"},
        ...     {"id": "doc2", "title": "FastAPI Tips", "created_at": "2024-01-01"}
        ... ]
        >>> enriched = enrich_with_documents(expert, documents)
        >>> enriched["document_count"]
        2
        >>> len(enriched["recent_documents"])
        2
        >>> enriched["recent_documents"][0]["title"]
        'Python Guide'
    """
    # Create a copy to avoid mutating the original
    enriched = expert.copy()
    
    # Add document count
    enriched["document_count"] = len(documents)
    
    # Add recent documents (sorted by creation date, most recent first)
    enriched["recent_documents"] = sorted(
        documents,
        key=lambda d: d.get("created_at", ""),
        reverse=True
    )[:5]  # Keep only 5 most recent
    
    return enriched


def enrich_with_services(expert: Dict[str, Any], service_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Enrich expert data with service contribution information.
    
    Adds service count and contribution roles to expert data.
    
    Args:
        expert: Expert data to enrich
        service_data: List of services the expert has contributed to
        
    Returns:
        Enriched expert data with service_count and service_contributions fields
        
    Examples:
        >>> expert = {"user_id": "user123", "name": "Alice"}
        >>> services = [
        ...     {"service_name": "user-store", "role": "maintainer"},
        ...     {"service_name": "doc-store", "role": "contributor"}
        ... ]
        >>> enriched = enrich_with_services(expert, services)
        >>> enriched["service_count"]
        2
    """
    enriched = expert.copy()
    
    # Add service count
    enriched["service_count"] = len(service_data)
    
    # Add service contributions with roles
    enriched["service_contributions"] = [
        {
            "service": s.get("service_name"),
            "role": s.get("role", "contributor")
        }
        for s in service_data
    ]
    
    return enriched


def normalize_query(query_text: str) -> str:
    """
    Normalize query text for consistent matching.
    
    Converts to lowercase, removes extra whitespace, and standardizes formatting.
    
    Args:
        query_text: Raw query text
        
    Returns:
        Normalized query text
        
    Examples:
        >>> normalize_query("  Python   Developer  ")
        'python developer'
        >>> normalize_query("BACKEND-DEV")
        'backend-dev'
    """
    # Convert to lowercase
    normalized = query_text.lower()
    
    # Remove extra whitespace
    normalized = " ".join(normalized.split())
    
    return normalized


def extract_keywords(text: str) -> List[str]:
    """
    Extract keywords from text for matching.
    
    Splits text into individual words and filters out common stop words.
    
    Args:
        text: Text to extract keywords from
        
    Returns:
        List of keywords
        
    Examples:
        >>> extract_keywords("Python backend developer with FastAPI")
        ['python', 'backend', 'developer', 'fastapi']
    """
    # Common stop words to filter out
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    
    # Split and normalize
    words = normalize_query(text).split()
    
    # Filter out stop words
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return keywords

