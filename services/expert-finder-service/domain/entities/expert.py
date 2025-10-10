"""
Expert entity - Core domain model.

Represents a user in the system who can be matched as an expert
for specific topics, roles, or services.
"""

from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Expert:
    """
    Expert entity representing a user with specific expertise.
    
    This is the core domain entity that represents a user who can be
    identified as an expert or potential collaborator based on their
    skills, experience, and contributions.
    
    Attributes:
        user_id: Unique identifier for the user
        name: Full name of the expert
        role: Primary role (e.g., "Backend Developer", "Data Scientist")
        seniority: Experience level (senior, mid, junior)
        topics: List of topics/technologies the expert knows
        tags: Additional tags for categorization
        services: List of services the expert has contributed to
        created_at: When the user account was created
        email: Optional email address
        team_id: Optional team identifier
        location: Optional location information
        document_count: Number of documents authored (enriched data)
        service_count: Number of services contributed to (enriched data)
    """
    
    # Required fields
    user_id: str
    name: str
    
    # Optional profile fields
    role: Optional[str] = None
    seniority: str = "junior"  # Default to junior if not specified
    
    # Expertise indicators
    topics: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: Optional[str] = None
    email: Optional[str] = None
    team_id: Optional[str] = None
    location: Optional[str] = None
    
    # Enriched data (added by use cases)
    document_count: int = 0
    service_count: int = 0
    
    def has_role(self, role_query: str) -> bool:
        """
        Check if expert's role matches the query.
        
        Args:
            role_query: Role to match against
            
        Returns:
            True if role matches, False otherwise
        """
        if not self.role or not role_query:
            return False
        return role_query.lower() in self.role.lower()
    
    def has_topic(self, topic: str) -> bool:
        """
        Check if expert has a specific topic.
        
        Args:
            topic: Topic to check for
            
        Returns:
            True if expert has the topic, False otherwise
        """
        topic_lower = topic.lower()
        return any(topic_lower in t.lower() for t in self.topics)
    
    def has_any_topics(self, topics: List[str]) -> bool:
        """
        Check if expert has any of the specified topics.
        
        Args:
            topics: List of topics to check for
            
        Returns:
            True if expert has at least one topic, False otherwise
        """
        return any(self.has_topic(topic) for topic in topics)
    
    def topic_match_count(self, topics: List[str]) -> int:
        """
        Count how many topics match.
        
        Args:
            topics: List of topics to match against
            
        Returns:
            Number of matching topics
        """
        return sum(1 for topic in topics if self.has_topic(topic))
    
    def has_service(self, service_name: str) -> bool:
        """
        Check if expert has contributed to a specific service.
        
        Args:
            service_name: Service to check for
            
        Returns:
            True if expert has contributed to the service, False otherwise
        """
        service_lower = service_name.lower()
        return any(service_lower in s.lower() for s in self.services)
    
    def is_senior(self) -> bool:
        """Check if expert has senior seniority."""
        return self.seniority.lower() == "senior"
    
    def is_mid(self) -> bool:
        """Check if expert has mid-level seniority."""
        return self.seniority.lower() == "mid"
    
    def is_sme(self, min_documents: int = 10) -> bool:
        """
        Check if expert qualifies as a Subject Matter Expert (SME).
        
        Args:
            min_documents: Minimum document count required for SME status
            
        Returns:
            True if expert is an SME, False otherwise
        """
        return self.document_count >= min_documents
    
    def __str__(self) -> str:
        """String representation of expert."""
        return f"Expert(user_id={self.user_id}, name={self.name}, role={self.role})"
    
    def __repr__(self) -> str:
        """Detailed representation of expert."""
        return (
            f"Expert(user_id={self.user_id}, name={self.name}, role={self.role}, "
            f"seniority={self.seniority}, topics={len(self.topics)}, "
            f"services={len(self.services)}, documents={self.document_count})"
        )

