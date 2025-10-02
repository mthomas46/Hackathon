"""Guided Setup Wizard Page.

Streamlit UI component for the simulation setup wizard.
Business logic is handled by the WizardService application service.
"""

from typing import Any, Dict, List, Optional

import streamlit as st

# Import application service
from ..application.services.wizard_service import WizardService
from ..domain.services.simulation_service import SimulationService
from ..infrastructure.repositories.simulation_repository import SimulationRepository

# Initialize services
_simulation_service = SimulationService(SimulationRepository())
_wizard_service = WizardService(_simulation_service)


def render_wizard_page():
    """Render the guided setup wizard page."""
    st.markdown("## 🧙‍♂️ Guided Simulation Setup Wizard")
    st.markdown("Create comprehensive project simulations with our step-by-step guided wizard.")

    # Initialize wizard session state
    _initialize_wizard_state()

    # Check if wizard is already in progress
    if "wizard_active" not in st.session_state:
        _render_wizard_start()
    else:
        _render_wizard_steps()

    # Wizard navigation
    _render_wizard_navigation()


def _initialize_wizard_state():
    """Initialize session state for the wizard."""
    if "wizard_data" not in st.session_state:
        st.session_state.wizard_data = _wizard_service.initialize_wizard_data()

    if "wizard_templates" not in st.session_state:
        st.session_state.wizard_templates = _wizard_service.get_wizard_templates()


def _render_wizard_start():
    """Render the wizard start screen with options."""
    st.markdown("### 🚀 Choose Your Setup Method")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📝 Start from Scratch", use_container_width=True):
            st.session_state.wizard_active = True
            st.session_state.wizard_data["step"] = 1
            st.rerun()

    with col2:
        if st.button("📋 Use Template", use_container_width=True):
            _render_template_selection()

    with col3:
        if st.button("📊 Quick Setup", use_container_width=True):
            _apply_quick_setup()
            st.success("Quick setup applied! Redirecting to simulation...")
            st.rerun()


def _render_template_selection():
    """Render template selection interface."""
    st.markdown("### 📋 Choose a Template")

    templates = st.session_state.wizard_templates
    template_options = [t["name"] for t in templates]
    selected_template = st.selectbox("Select a template:", template_options)

    if st.button("Apply Template"):
        template_id = next(t["id"] for t in templates if t["name"] == selected_template)
        st.session_state.wizard_data = _wizard_service.apply_wizard_template(
            template_id, st.session_state.wizard_data
        )
        st.session_state.wizard_active = True
        st.success(f"Template '{selected_template}' applied!")
        st.rerun()


def _apply_quick_setup():
    """Apply quick setup defaults."""
    st.session_state.wizard_data = _wizard_service.initialize_wizard_data()
    # Apply some reasonable defaults
    st.session_state.wizard_data["project_info"].update({
        "name": "Quick Simulation",
        "description": "Quick simulation setup",
        "type": "web_application"
    })
    st.session_state.wizard_active = True


def _render_wizard_steps():
    """Render the current wizard step."""
    wizard_data = st.session_state.wizard_data
    current_step = wizard_data["step"]

    # Progress indicator
    progress = _wizard_service.calculate_wizard_progress(wizard_data)
    st.progress(progress / 100)
    st.markdown(f"**Step {current_step} of {wizard_data['total_steps']}** - {progress:.1f}% Complete")

    # Render current step
    if current_step == 1:
        _render_step_1_project_basics()
    elif current_step == 2:
        _render_step_2_team_config()
    elif current_step == 3:
        _render_step_3_timeline()
    elif current_step == 4:
        _render_step_4_budget()
    elif current_step == 5:
        _render_step_5_risk_assessment()
    elif current_step == 6:
        _render_step_6_advanced_config()
    elif current_step == 7:
        _render_step_7_review_and_create()


def _render_step_1_project_basics():
    """Render project basics step."""
    st.markdown("### 📋 Project Basics")

    wizard_data = st.session_state.wizard_data

    # Project name
    name = st.text_input(
        "Project Name",
        value=wizard_data["project_info"].get("name", ""),
        help="Enter a descriptive name for your project"
    )

    # Project description
    description = st.text_area(
        "Project Description",
        value=wizard_data["project_info"].get("description", ""),
        help="Describe what this project aims to achieve"
    )

    # Project type
    project_types = _wizard_service.get_project_type_options()
    type_options = [pt["name"] for pt in project_types]
    current_type = wizard_data["project_info"].get("type")
    if current_type:
        current_index = next((i for i, pt in enumerate(project_types) if pt["id"] == current_type), 0)
    else:
        current_index = 0

    selected_type_name = st.selectbox("Project Type", type_options, index=current_index)

    # Find selected type
    selected_type = next((pt for pt in project_types if pt["name"] == selected_type_name), None)
    if selected_type:
        st.info(f"**{selected_type['name']}**: {selected_type['description']}")

    # Update wizard data
    wizard_data["project_info"]["name"] = name
    wizard_data["project_info"]["description"] = description
    if selected_type:
        wizard_data["project_info"]["type"] = selected_type["id"]


def _render_step_2_team_config():
    """Render team configuration step."""
    st.markdown("### 👥 Team Configuration")

    wizard_data = st.session_state.wizard_data
    team_config = wizard_data["team_config"]

    col1, col2 = st.columns(2)

    with col1:
        team_size = st.slider(
            "Team Size",
            min_value=1,
            max_value=50,
            value=team_config.get("size", 5),
            help="Number of team members"
        )

    with col2:
        experience_levels = ["beginner", "intermediate", "expert"]
        experience = st.selectbox(
            "Experience Level",
            experience_levels,
            index=experience_levels.index(team_config.get("experience_level", "intermediate"))
        )

    # Update wizard data
    team_config["size"] = team_size
    team_config["experience_level"] = experience


def _render_step_3_timeline():
    """Render timeline configuration step."""
    st.markdown("### 📅 Timeline Configuration")

    wizard_data = st.session_state.wizard_data
    timeline_config = wizard_data["timeline_config"]

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            value=timeline_config.get("start_date"),
            help="When will the project start?"
        )

    with col2:
        duration = st.slider(
            "Duration (weeks)",
            min_value=1,
            max_value=104,
            value=timeline_config.get("duration_weeks", 12),
            help="How long will the project take?"
        )

    # Update wizard data
    timeline_config["start_date"] = start_date
    timeline_config["duration_weeks"] = duration


def _render_step_4_budget():
    """Render budget configuration step."""
    st.markdown("### 💰 Budget Configuration")

    wizard_data = st.session_state.wizard_data
    budget_config = wizard_data["budget_config"]

    col1, col2 = st.columns(2)

    with col1:
        budget = st.number_input(
            "Total Budget",
            min_value=0,
            value=budget_config.get("total_budget", 100000),
            step=1000,
            help="Total project budget"
        )

    with col2:
        currencies = ["USD", "EUR", "GBP", "CAD", "AUD"]
        currency = st.selectbox(
            "Currency",
            currencies,
            index=currencies.index(budget_config.get("currency", "USD"))
        )

    # Update wizard data
    budget_config["total_budget"] = budget
    budget_config["currency"] = currency


def _render_step_5_risk_assessment():
    """Render risk assessment step."""
    st.markdown("### ⚠️ Risk Assessment")

    wizard_data = st.session_state.wizard_data
    risk_config = wizard_data["risk_assessment"]

    col1, col2 = st.columns(2)

    with col1:
        complexities = ["low", "medium", "high"]
        complexity = st.selectbox(
            "Project Complexity",
            complexities,
            index=complexities.index(risk_config.get("complexity", "medium"))
        )

    with col2:
        dependencies = st.slider(
            "External Dependencies",
            min_value=0,
            max_value=10,
            value=risk_config.get("external_dependencies", 3),
            help="Number of external dependencies"
        )

    # Update wizard data
    risk_config["complexity"] = complexity
    risk_config["external_dependencies"] = dependencies
    # Auto-calculate risk level
    risk_config["risk_level"] = "high" if complexity == "high" or dependencies > 7 else "medium" if complexity == "medium" or dependencies > 3 else "low"


def _render_step_6_advanced_config():
    """Render advanced configuration step."""
    st.markdown("### ⚙️ Advanced Configuration")

    wizard_data = st.session_state.wizard_data
    advanced_config = wizard_data["advanced_config"]

    col1, col2, col3 = st.columns(3)

    with col1:
        scenarios = st.slider(
            "Simulation Scenarios",
            min_value=1,
            max_value=10,
            value=advanced_config.get("simulation_scenarios", 3),
            help="Number of simulation scenarios to run"
        )

    with col2:
        iterations = st.slider(
            "Monte Carlo Iterations",
            min_value=100,
            max_value=10000,
            value=advanced_config.get("monte_carlo_iterations", 1000),
            step=100,
            help="Number of Monte Carlo iterations"
        )

    with col3:
        confidence = st.slider(
            "Confidence Interval",
            min_value=0.80,
            max_value=0.99,
            value=advanced_config.get("confidence_interval", 0.95),
            step=0.01,
            help="Statistical confidence interval"
        )

    # Update wizard data
    advanced_config["simulation_scenarios"] = scenarios
    advanced_config["monte_carlo_iterations"] = iterations
    advanced_config["confidence_interval"] = confidence


def _render_step_7_review_and_create():
    """Render review and creation step."""
    st.markdown("### ✅ Review & Create Simulation")

    wizard_data = st.session_state.wizard_data

    # Display summary
    with st.expander("📋 Project Summary", expanded=True):
        st.json(wizard_data)

    # Validation
    errors = _wizard_service.validate_wizard_step(7, wizard_data)
    if errors:
        st.error("Please fix the following errors:")
        for field, error in errors.items():
            st.error(f"• {field}: {error}")
    else:
        st.success("All validations passed!")

        if st.button("🚀 Create Simulation", type="primary", use_container_width=True):
            try:
                # Generate simulation config
                simulation_config = _wizard_service.generate_simulation_from_wizard(wizard_data)

                # Here you would call the simulation creation API
                st.success("Simulation created successfully!")
                st.json(simulation_config)

                # Reset wizard
                if st.button("Create Another Simulation"):
                    for key in list(st.session_state.keys()):
                        if key.startswith("wizard"):
                            del st.session_state[key]
                    st.rerun()

            except Exception as e:
                st.error(f"Failed to create simulation: {str(e)}")


def _render_wizard_navigation():
    """Render wizard navigation controls."""
    if "wizard_active" not in st.session_state:
        return

    wizard_data = st.session_state.wizard_data
    current_step = wizard_data["step"]
    total_steps = wizard_data["total_steps"]

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if current_step > 1:
            if st.button("⬅️ Previous", key="prev_step"):
                wizard_data["step"] -= 1
                st.rerun()

    with col2:
        st.markdown(f"**Step {current_step} of {total_steps}**")

    with col3:
        if current_step < total_steps:
            # Validate current step before allowing next
            errors = _wizard_service.validate_wizard_step(current_step, wizard_data)
            if errors:
                st.button("Next ➡️", disabled=True, help="Please fix validation errors first")
            else:
                if st.button("Next ➡️", key="next_step"):
                    wizard_data["step"] += 1
                    st.rerun()
        else:
            st.button("✅ Complete", disabled=True, help="Use the Create Simulation button above")

