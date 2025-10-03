"""
Tests for Software Development Domain Model
==========================================

Unit tests for ticket templates, complexity estimation, and domain knowledge.
"""

import pytest
import sys
from pathlib import Path

# Add service root to path
service_root = str(Path(__file__).parent.parent)
if service_root not in sys.path:
    sys.path.insert(0, service_root)

# Import from the correct module path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.models.software_development import (
    SoftwareDevelopmentDomain,
    TicketType,
    ComplexityLevel,
    TechnologyCategory,
    Priority
)


@pytest.fixture
def domain():
    """Create software development domain instance."""
    return SoftwareDevelopmentDomain()


class TestSoftwareDevelopmentDomain:
    """Test suite for Software Development Domain Model."""
    
    def test_initialization(self, domain):
        """Test domain initializes with all templates and patterns."""
        assert domain is not None
        assert len(domain.ticket_templates) > 0
        assert len(domain.complexity_factors) > 0
        assert len(domain.technology_stacks) > 0
        assert len(domain.best_practices) > 0
    
    def test_all_ticket_types_have_templates(self, domain):
        """Test that all major ticket types have templates."""
        expected_types = [
            TicketType.USER_STORY,
            TicketType.BUG,
            TicketType.SPIKE,
            TicketType.TASK,
            TicketType.REFACTORING
        ]
        
        for ticket_type in expected_types:
            template = domain.get_template(ticket_type)
            assert template is not None
            assert template.type == ticket_type
            assert template.title_pattern
            assert template.description_template
            assert len(template.required_fields) > 0
    
    def test_user_story_template(self, domain):
        """Test user story template structure."""
        template = domain.get_template(TicketType.USER_STORY)
        
        assert template is not None
        assert "As a" in template.title_pattern
        assert "user_type" in template.required_fields
        assert "action" in template.required_fields
        assert "benefit" in template.required_fields
        assert len(template.acceptance_criteria_template) > 0
        assert len(template.common_subtasks) > 0
        assert len(template.examples) > 0
    
    def test_bug_template(self, domain):
        """Test bug template structure."""
        template = domain.get_template(TicketType.BUG)
        
        assert template is not None
        assert "Steps to Reproduce" in template.description_template
        assert "Expected Behavior" in template.description_template
        assert "Actual Behavior" in template.description_template
        assert "steps_to_reproduce" in template.required_fields
        assert template.typical_complexity == ComplexityLevel.SIMPLE
    
    def test_spike_template(self, domain):
        """Test spike/research template structure."""
        template = domain.get_template(TicketType.SPIKE)
        
        assert template is not None
        assert "Research" in template.title_pattern
        assert "research_goal" in template.required_fields
        assert "time_box" in template.required_fields
        assert "deliverables" in template.required_fields
    
    def test_task_template(self, domain):
        """Test task template structure."""
        template = domain.get_template(TicketType.TASK)
        
        assert template is not None
        assert "definition_of_done" in template.required_fields
        assert template.typical_complexity == ComplexityLevel.SIMPLE
    
    def test_refactoring_template(self, domain):
        """Test refactoring template structure."""
        template = domain.get_template(TicketType.REFACTORING)
        
        assert template is not None
        assert "Refactor" in template.title_pattern
        assert "current_state" in template.required_fields
        assert "problems" in template.required_fields
        assert "testing_strategy" in template.required_fields
        assert template.typical_complexity == ComplexityLevel.COMPLEX
    
    def test_complexity_factors_categories(self, domain):
        """Test complexity factors are categorized."""
        categories = {f.category for f in domain.complexity_factors}
        
        # Should have all major categories
        assert "technical" in categories
        assert "domain" in categories
        assert "team" in categories
        assert "external" in categories
    
    def test_find_complexity_factors_by_category(self, domain):
        """Test finding complexity factors by category."""
        technical_factors = domain.find_complexity_factors("technical")
        
        assert len(technical_factors) > 0
        assert all(f.category == "technical" for f in technical_factors)
    
    def test_find_all_complexity_factors(self, domain):
        """Test finding all complexity factors."""
        all_factors = domain.find_complexity_factors()
        
        assert len(all_factors) == len(domain.complexity_factors)
    
    def test_complexity_factors_have_impact(self, domain):
        """Test all complexity factors have impact rating."""
        for factor in domain.complexity_factors:
            assert factor.impact in ["low", "medium", "high"]
            assert factor.description
            assert factor.name
    
    def test_technology_stacks_by_category(self, domain):
        """Test technology stacks are categorized."""
        categories = {stack.category for stack in domain.technology_stacks.values()}
        
        # Should have multiple categories
        assert len(categories) >= 3
        assert TechnologyCategory.FRONTEND in categories or TechnologyCategory.BACKEND in categories
    
    def test_get_technology_stack(self, domain):
        """Test getting technology stack information."""
        react_stack = domain.get_technology_stack("react")
        
        assert react_stack is not None
        assert react_stack.name == "React"
        assert react_stack.category == TechnologyCategory.FRONTEND
        assert len(react_stack.common_tasks) > 0
        assert len(react_stack.typical_patterns) > 0
        assert react_stack.learning_curve in ["low", "medium", "high"]
        assert react_stack.maturity in ["experimental", "stable", "mature"]
    
    def test_get_technology_stack_case_insensitive(self, domain):
        """Test technology stack lookup is case-insensitive."""
        stack1 = domain.get_technology_stack("REACT")
        stack2 = domain.get_technology_stack("React")
        stack3 = domain.get_technology_stack("react")
        
        assert stack1 is not None
        assert stack1 == stack2 == stack3
    
    def test_fastapi_technology_stack(self, domain):
        """Test FastAPI technology stack details."""
        fastapi_stack = domain.get_technology_stack("fastapi")
        
        assert fastapi_stack is not None
        assert fastapi_stack.category == TechnologyCategory.BACKEND
        assert fastapi_stack.learning_curve == "low"
        assert "Dependency Injection" in fastapi_stack.typical_patterns
    
    def test_best_practices_categories(self, domain):
        """Test best practices cover multiple categories."""
        categories = {bp.category for bp in domain.best_practices}
        
        # Should have practices in multiple areas
        assert len(categories) >= 3
    
    def test_best_practices_structure(self, domain):
        """Test best practices have complete information."""
        for practice in domain.best_practices:
            assert practice.name
            assert practice.category
            assert practice.description
            assert practice.when_to_use
            assert len(practice.benefits) > 0
            assert len(practice.considerations) > 0
            assert len(practice.examples) > 0
    
    def test_estimate_complexity_trivial(self, domain):
        """Test complexity estimation for trivial task."""
        result = domain.estimate_complexity(
            description="Update button color to blue",
            technologies=["react"],
            is_new_feature=False
        )
        
        assert result["complexity_level"] in [ComplexityLevel.TRIVIAL.value, ComplexityLevel.SIMPLE.value]
        assert result["estimated_hours"] <= 8
        assert isinstance(result["complexity_score"], int)
        assert isinstance(result["identified_factors"], list)
    
    def test_estimate_complexity_simple(self, domain):
        """Test complexity estimation for simple task."""
        result = domain.estimate_complexity(
            description="Add validation to email input field",
            technologies=["react"],
            is_new_feature=True
        )
        
        assert result["complexity_level"] in [ComplexityLevel.TRIVIAL.value, ComplexityLevel.SIMPLE.value, ComplexityLevel.MODERATE.value]
        assert result["estimated_hours"] > 0
    
    def test_estimate_complexity_with_integration(self, domain):
        """Test complexity estimation with integration work."""
        result = domain.estimate_complexity(
            description="Integrate payment gateway with checkout system",
            technologies=["fastapi", "stripe"],
            is_new_feature=True
        )
        
        assert result["complexity_score"] >= 2  # Should detect integration
        assert "Multiple System Integration" in result["identified_factors"]
    
    def test_estimate_complexity_with_migration(self, domain):
        """Test complexity estimation with migration work."""
        result = domain.estimate_complexity(
            description="Migrate user database from MySQL to PostgreSQL",
            technologies=["postgresql", "python"],
            is_new_feature=False
        )
        
        assert result["complexity_score"] >= 3  # Should detect migration
        assert any("Migration" in factor or "Integration" in factor for factor in result["identified_factors"])
    
    def test_estimate_complexity_with_performance(self, domain):
        """Test complexity estimation with performance requirements."""
        result = domain.estimate_complexity(
            description="Optimize API endpoint to handle 10k requests per second",
            technologies=["fastapi"],
            is_new_feature=False
        )
        
        assert result["complexity_score"] >= 2
        assert "Performance Requirements" in result["identified_factors"]
    
    def test_estimate_complexity_with_security(self, domain):
        """Test complexity estimation with security requirements."""
        result = domain.estimate_complexity(
            description="Implement OAuth2 authentication with GDPR compliance",
            technologies=["fastapi"],
            is_new_feature=True
        )
        
        assert result["complexity_score"] >= 1
        assert "Regulatory Compliance" in result["identified_factors"]
    
    def test_estimate_complexity_with_new_technology(self, domain):
        """Test complexity estimation with unfamiliar technology."""
        result = domain.estimate_complexity(
            description="Build real-time dashboard",
            technologies=["graphql", "websockets", "redis"],
            is_new_feature=True
        )
        
        # Should detect new/unfamiliar technologies
        assert result["complexity_score"] >= 2
        assert "New Technology" in result["identified_factors"]
    
    def test_estimate_complexity_very_complex(self, domain):
        """Test complexity estimation for very complex task."""
        result = domain.estimate_complexity(
            description="Migrate authentication system to OAuth2, integrate with Active Directory, optimize performance for 100k users, ensure GDPR compliance",
            technologies=["oauth2", "ldap", "redis", "postgresql"],
            is_new_feature=False
        )
        
        # Should be very complex with multiple factors
        assert result["complexity_score"] >= 5
        assert result["complexity_level"] in [ComplexityLevel.COMPLEX.value, ComplexityLevel.VERY_COMPLEX.value]
        assert len(result["identified_factors"]) >= 3
    
    def test_ticket_template_hours_range(self, domain):
        """Test all ticket templates have valid hour ranges."""
        for template in domain.ticket_templates.values():
            min_hours, max_hours = template.estimated_hours_range
            assert min_hours > 0
            assert max_hours >= min_hours
            assert max_hours <= 200  # Reasonable upper bound
    
    def test_complexity_factors_have_mitigation(self, domain):
        """Test high-impact complexity factors have mitigation strategies."""
        high_impact_factors = [f for f in domain.complexity_factors if f.impact == "high"]
        
        assert len(high_impact_factors) > 0
        for factor in high_impact_factors:
            # High-impact factors should have mitigation strategies
            assert factor.mitigation is not None
            assert len(factor.mitigation) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

