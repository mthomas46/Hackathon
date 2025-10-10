"""
Unit tests for Expert entity.
"""

import pytest
from domain.entities.expert import Expert


class TestExpertEntity:
    """Tests for Expert entity."""
    
    def test_expert_creation(self):
        """Test creating an expert instance."""
        expert = Expert(
            user_id="user123",
            name="Alice Smith",
            role="Backend Developer",
            seniority="senior",
            topics=["Python", "FastAPI"],
            tags=["backend"],
            services=["user-store"]
        )
        
        assert expert.user_id == "user123"
        assert expert.name == "Alice Smith"
        assert expert.role == "Backend Developer"
        assert expert.seniority == "senior"
        assert len(expert.topics) == 2
        assert expert.document_count == 0  # Default
    
    def test_has_role(self):
        """Test role matching."""
        expert = Expert(user_id="1", name="Alice", role="Backend Developer")
        
        assert expert.has_role("Backend")
        assert expert.has_role("Developer")
        assert not expert.has_role("Frontend")
    
    def test_has_topic(self):
        """Test topic matching."""
        expert = Expert(
            user_id="1",
            name="Alice",
            topics=["Python", "FastAPI", "Docker"]
        )
        
        assert expert.has_topic("Python")
        assert expert.has_topic("python")  # Case insensitive
        assert expert.has_topic("Fast")  # Substring match
        assert not expert.has_topic("JavaScript")
    
    def test_topic_match_count(self):
        """Test counting topic matches."""
        expert = Expert(
            user_id="1",
            name="Alice",
            topics=["Python", "FastAPI", "Docker"]
        )
        
        assert expert.topic_match_count(["Python", "Docker"]) == 2
        assert expert.topic_match_count(["Python", "JavaScript"]) == 1
        assert expert.topic_match_count(["JavaScript", "Ruby"]) == 0
    
    def test_is_senior(self):
        """Test seniority checks."""
        senior = Expert(user_id="1", name="Alice", seniority="senior")
        mid = Expert(user_id="2", name="Bob", seniority="mid")
        junior = Expert(user_id="3", name="Carol", seniority="junior")
        
        assert senior.is_senior()
        assert not mid.is_senior()
        assert not junior.is_senior()
    
    def test_is_sme(self):
        """Test SME identification."""
        expert = Expert(user_id="1", name="Alice", document_count=15)
        
        assert expert.is_sme(min_documents=10)
        assert not expert.is_sme(min_documents=20)
    
    def test_defaults(self):
        """Test default values."""
        expert = Expert(user_id="1", name="Alice")
        
        assert expert.seniority == "junior"
        assert expert.topics == []
        assert expert.tags == []
        assert expert.services == []
        assert expert.document_count == 0

