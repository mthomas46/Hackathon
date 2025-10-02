"""Wizard Application Service.

Handles the business logic for the simulation setup wizard,
coordinating between domain services and managing wizard state.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ...domain.services.simulation_service import SimulationService
from ...domain.models.value_objects import ProjectType, RiskLevel

logger = logging.getLogger(__name__)


class WizardService:
    """Application service for simulation wizard business logic."""

    def __init__(self, simulation_service: SimulationService):
        self.simulation_service = simulation_service

    def initialize_wizard_data(self) -> Dict[str, Any]:
        """Initialize default wizard data structure."""
        return {
            "step": 1,
            "total_steps": 7,
            "project_info": {
                "name": "",
                "description": "",
                "type": None,
                "priority": "medium"
            },
            "team_config": {
                "size": 5,
                "experience_level": "intermediate",
                "distribution": {}
            },
            "timeline_config": {
                "start_date": datetime.now().date(),
                "duration_weeks": 12,
                "milestones": []
            },
            "budget_config": {
                "total_budget": 100000,
                "currency": "USD",
                "allocation": {}
            },
            "risk_assessment": {
                "complexity": "medium",
                "external_dependencies": 3,
                "risk_level": RiskLevel.MEDIUM,
                "mitigation_strategies": []
            },
            "advanced_config": {
                "simulation_scenarios": 3,
                "monte_carlo_iterations": 1000,
                "confidence_interval": 0.95
            },
            "validation_errors": {},
            "progress": {},
        }

    def get_project_type_options(self) -> List[Dict[str, Any]]:
        """Get available project type options with metadata."""
        return [
            {
                "id": ProjectType.WEB_APPLICATION,
                "name": "Web Application",
                "description": "Modern web application development",
                "complexity": "medium",
                "estimated_duration": 12,
                "team_size": "5-10",
                "risk_level": "medium"
            },
            {
                "id": ProjectType.MOBILE_APP,
                "name": "Mobile Application",
                "description": "iOS/Android mobile app development",
                "complexity": "high",
                "estimated_duration": 16,
                "team_size": "8-15",
                "risk_level": "high"
            },
            {
                "id": ProjectType.API_SERVICE,
                "name": "API/Microservice",
                "description": "Backend API or microservice development",
                "complexity": "medium",
                "estimated_duration": 10,
                "team_size": "3-8",
                "risk_level": "low"
            },
            {
                "id": ProjectType.DATA_ANALYTICS,
                "name": "Data Analytics Platform",
                "description": "Big data and analytics solution",
                "complexity": "high",
                "estimated_duration": 20,
                "team_size": "10-20",
                "risk_level": "high"
            },
            {
                "id": ProjectType.DEVOPS_INFRASTRUCTURE,
                "name": "DevOps/Infrastructure",
                "description": "Cloud infrastructure and DevOps setup",
                "complexity": "medium",
                "estimated_duration": 8,
                "team_size": "3-6",
                "risk_level": "medium"
            }
        ]

    def validate_wizard_step(self, step: int, data: Dict[str, Any]) -> Dict[str, str]:
        """Validate data for a specific wizard step."""
        errors = {}

        if step == 1:  # Project basics
            if not data.get("project_info", {}).get("name", "").strip():
                errors["name"] = "Project name is required"
            if not data.get("project_info", {}).get("type"):
                errors["type"] = "Project type must be selected"

        elif step == 2:  # Team configuration
            team_size = data.get("team_config", {}).get("size", 0)
            if team_size < 1:
                errors["team_size"] = "Team size must be at least 1"
            if team_size > 50:
                errors["team_size"] = "Team size cannot exceed 50"

        elif step == 3:  # Timeline
            duration = data.get("timeline_config", {}).get("duration_weeks", 0)
            if duration < 1:
                errors["duration"] = "Duration must be at least 1 week"
            if duration > 104:  # 2 years
                errors["duration"] = "Duration cannot exceed 2 years"

        elif step == 4:  # Budget
            budget = data.get("budget_config", {}).get("total_budget", 0)
            if budget <= 0:
                errors["budget"] = "Budget must be greater than 0"
            if budget > 10000000:  # $10M
                errors["budget"] = "Budget cannot exceed $10,000,000"

        return errors

    def calculate_wizard_progress(self, data: Dict[str, Any]) -> float:
        """Calculate overall wizard completion progress."""
        total_fields = 0
        completed_fields = 0

        # Project info (3 fields)
        project_info = data.get("project_info", {})
        total_fields += 3
        if project_info.get("name"): completed_fields += 1
        if project_info.get("description"): completed_fields += 1
        if project_info.get("type"): completed_fields += 1

        # Team config (2 fields)
        team_config = data.get("team_config", {})
        total_fields += 2
        if team_config.get("size"): completed_fields += 1
        if team_config.get("experience_level"): completed_fields += 1

        # Timeline (2 fields)
        timeline_config = data.get("timeline_config", {})
        total_fields += 2
        if timeline_config.get("start_date"): completed_fields += 1
        if timeline_config.get("duration_weeks"): completed_fields += 1

        # Budget (2 fields)
        budget_config = data.get("budget_config", {})
        total_fields += 2
        if budget_config.get("total_budget"): completed_fields += 1
        if budget_config.get("currency"): completed_fields += 1

        # Risk assessment (2 fields)
        risk_config = data.get("risk_assessment", {})
        total_fields += 2
        if risk_config.get("complexity"): completed_fields += 1
        if risk_config.get("external_dependencies") is not None: completed_fields += 1

        return (completed_fields / total_fields) * 100 if total_fields > 0 else 0

    def generate_simulation_from_wizard(self, wizard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate simulation configuration from wizard data."""
        try:
            # Extract and structure data for simulation creation
            simulation_config = {
                "name": wizard_data["project_info"]["name"],
                "description": wizard_data["project_info"]["description"],
                "simulation_type": "project_simulation",
                "parameters": {
                    "project_type": wizard_data["project_info"]["type"],
                    "team_size": wizard_data["team_config"]["size"],
                    "timeline_weeks": wizard_data["timeline_config"]["duration_weeks"],
                    "budget": wizard_data["budget_config"]["total_budget"],
                    "risk_level": wizard_data["risk_assessment"]["risk_level"].value,
                    "complexity": wizard_data["risk_assessment"]["complexity"],
                    "scenarios": wizard_data["advanced_config"]["simulation_scenarios"],
                    "iterations": wizard_data["advanced_config"]["monte_carlo_iterations"]
                },
                "metadata": {
                    "created_from_wizard": True,
                    "wizard_version": "1.0",
                    "completion_percentage": self.calculate_wizard_progress(wizard_data)
                }
            }

            return simulation_config

        except Exception as e:
            logger.error(f"Failed to generate simulation from wizard: {e}")
            raise ValueError(f"Invalid wizard data: {str(e)}")

    def get_wizard_templates(self) -> List[Dict[str, Any]]:
        """Get available wizard templates for quick setup."""
        return [
            {
                "id": "startup_mvp",
                "name": "Startup MVP",
                "description": "Quick MVP development for startups",
                "estimated_duration": 8,
                "team_size": 4,
                "budget_range": "50000-150000"
            },
            {
                "id": "enterprise_solution",
                "name": "Enterprise Solution",
                "description": "Large-scale enterprise application",
                "estimated_duration": 24,
                "team_size": 15,
                "budget_range": "500000-2000000"
            },
            {
                "id": "api_microservice",
                "name": "API/Microservice",
                "description": "Backend API or microservice",
                "estimated_duration": 10,
                "team_size": 6,
                "budget_range": "100000-300000"
            }
        ]

    def apply_wizard_template(self, template_id: str, wizard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a wizard template to populate default values."""
        templates = self.get_wizard_templates()
        template = next((t for t in templates if t["id"] == template_id), None)

        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Apply template defaults
        wizard_data["timeline_config"]["duration_weeks"] = template["estimated_duration"]
        wizard_data["team_config"]["size"] = template["team_size"]

        # Parse budget range and set middle value
        budget_range = template["budget_range"]
        if "-" in budget_range:
            min_budget, max_budget = budget_range.split("-")
            avg_budget = (int(min_budget) + int(max_budget)) // 2
            wizard_data["budget_config"]["total_budget"] = avg_budget

        return wizard_data
