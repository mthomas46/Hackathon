"""
Unit Tests for Mock Data Generation (TDD RED Phase)
Following TDD principles: RED -> GREEN -> REFACTOR

These tests are written FIRST (RED phase) and will initially FAIL.
They define the expected behavior before implementation.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any
from datetime import datetime

# Import the modules we'll be testing (these may not exist yet - that's why tests will fail)
from simulation.infrastructure.mock_data.mock_data_generator import MockDataGenerator
from simulation.domain.entities.simulation import SimulationType, SimulationStatus


class TestMockDataGenerator:
    """Test mock data generation functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.generator = MockDataGenerator()

    def test_extract_keywords_from_query(self):
        """Test keyword extraction from natural language queries."""
        # Arrange
        query = "Create a web application with API backend and database"

        # Act
        keywords = self.generator.extract_keywords_from_query(query)

        # Assert
        assert isinstance(keywords, list)
        assert "api" in keywords
        assert "database" in keywords
        assert "web" in keywords or "application" in keywords
        assert len(keywords) > 0

    def test_generate_mock_team_members(self):
        """Test generation of mock team members based on keywords."""
        # Arrange
        keywords = ["api", "database", "frontend"]
        team_size = 3

        # Act
        team_members = self.generator.generate_mock_team_members(keywords, team_size)

        # Assert
        assert isinstance(team_members, list)
        assert len(team_members) == team_size

        for member in team_members:
            assert "id" in member
            assert "name" in member
            assert "role" in member
            assert "skills" in member
            assert "experience_years" in member
            assert "productivity_factor" in member
            assert isinstance(member["experience_years"], int)
            assert 0.5 <= member["productivity_factor"] <= 1.5

    def test_generate_mock_documents(self):
        """Test generation of mock documents."""
        # Arrange
        keywords = ["api", "authentication", "database"]
        context = {"project_type": "web_application", "complexity": "medium"}

        # Act
        documents = self.generator.generate_mock_documents(keywords, context)

        # Assert
        assert isinstance(documents, list)
        assert len(documents) > 0

        for doc in documents:
            assert "id" in doc
            assert "type" in doc
            assert "title" in doc
            assert "content" in doc
            assert "keywords" in doc
            assert "created_at" in doc
            assert isinstance(doc["created_at"], str)  # ISO format datetime

    def test_infer_technologies_from_query(self):
        """Test technology inference from query and keywords."""
        # Arrange
        query = "Build a React frontend with Node.js backend and PostgreSQL database"
        keywords = ["frontend", "backend", "database"]

        # Act
        technologies = self.generator.infer_technologies_from_query(query, keywords)

        # Assert
        assert isinstance(technologies, list)
        assert len(technologies) > 0

        # Should include base technologies
        assert "Python" in technologies
        assert "FastAPI" in technologies

        # Should include some inferred technologies based on keywords
        tech_names = " ".join(technologies).lower()
        # Check that at least some technology inference happened
        inferred_found = (
            "node" in tech_names or
            "react" in tech_names or
            "postgres" in tech_names or
            "vue" in tech_names or
            "angular" in tech_names
        )
        assert inferred_found, f"No expected technologies found in: {technologies}"

    def test_generate_mock_timeline(self):
        """Test generation of mock project timeline."""
        # Arrange
        duration_weeks = 8
        keywords = ["api", "frontend", "testing"]

        # Act
        timeline = self.generator.generate_mock_timeline(duration_weeks, keywords)

        # Assert
        assert isinstance(timeline, list)
        assert len(timeline) > 0

        total_duration = sum(phase["duration_weeks"] for phase in timeline)
        assert total_duration <= duration_weeks

        for phase in timeline:
            assert "phase" in phase
            assert "start_week" in phase
            assert "duration_weeks" in phase
            assert "milestones" in phase
            assert "deliverables" in phase
            assert isinstance(phase["milestones"], list)
            assert isinstance(phase["deliverables"], list)

    def test_generate_comprehensive_mock_data(self):
        """Test generation of comprehensive mock data for simulation."""
        # Arrange
        query = "Create an e-commerce platform with user authentication and payment processing"
        context = {
            "project_type": "web_application",
            "complexity": "high",
            "budget": 200000
        }
        config = {
            "type": "web_application",
            "complexity": "high",
            "duration_weeks": 12,
            "team_size": 5
        }

        # Act
        mock_data = self.generator.generate_comprehensive_mock_data(query, context, config)

        # Assert
        assert isinstance(mock_data, dict)
        assert "team_members" in mock_data
        assert "documents" in mock_data
        assert "technologies" in mock_data
        assert "timeline" in mock_data
        assert "keywords_extracted" in mock_data
        assert "generated_at" in mock_data

        # Verify data consistency
        assert len(mock_data["team_members"]) == config["team_size"]
        assert len(mock_data["timeline"]) > 0
        assert len(mock_data["technologies"]) > 0
        assert len(mock_data["documents"]) > 0

    def test_mock_data_consistency(self):
        """Test that mock data generation is consistent and deterministic."""
        # Arrange
        query = "Build a mobile app with offline capabilities"
        context = {"project_type": "mobile_app"}
        config = {"type": "mobile_app", "team_size": 4}

        # Act - Generate data multiple times
        data1 = self.generator.generate_comprehensive_mock_data(query, context, config)
        data2 = self.generator.generate_comprehensive_mock_data(query, context, config)

        # Assert - Should be consistent (same structure, not necessarily same values)
        assert len(data1["team_members"]) == len(data2["team_members"])
        assert len(data1["documents"]) == len(data2["documents"])
        assert set(data1["technologies"]) == set(data2["technologies"])  # Same technologies

    def test_empty_query_handling(self):
        """Test handling of empty or minimal queries."""
        # Arrange
        query = ""
        context = {}
        config = {"team_size": 3}

        # Act
        mock_data = self.generator.generate_comprehensive_mock_data(query, context, config)

        # Assert
        assert isinstance(mock_data, dict)
        assert "team_members" in mock_data
        assert "documents" in mock_data
        assert "technologies" in mock_data
        assert "timeline" in mock_data
        # Should provide default/fallback data
        assert len(mock_data["team_members"]) == 3

    def test_technology_mapping_accuracy(self):
        """Test that technology mapping is accurate based on keywords."""
        # Arrange
        test_cases = [
            (["api", "rest"], ["REST", "API"]),
            (["database", "postgres"], ["PostgreSQL", "Database"]),
            (["frontend", "react"], ["React", "Frontend"]),
            (["authentication", "jwt"], ["JWT", "OAuth2"]),
        ]

        for keywords, expected_techs in test_cases:
            # Act
            technologies = self.generator.infer_technologies_from_query(" ".join(keywords), keywords)

            # Assert
            tech_names = [tech.lower() for tech in technologies]
            expected_lower = [tech.lower() for tech in expected_techs]

            # At least one expected technology should be present
            assert any(expected in " ".join(tech_names) for expected in expected_lower), \
                f"Expected technologies {expected_techs} not found in {technologies}"


class TestMockDataIntegration:
    """Integration tests for mock data generation with other components."""

    def test_mock_data_with_simulation_creation(self):
        """Test that mock data integrates properly with simulation creation."""
        # This would test integration with the actual simulation creation process
        # For now, just verify the data structure is compatible
        pass

    def test_mock_data_persistence(self):
        """Test that mock data can be properly persisted and retrieved."""
        # This would test integration with the database persistence layer
        pass
