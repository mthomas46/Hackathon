"""Create Simulation Page.

This module provides the simulation creation page with guided setup,
configuration management, and validation.
"""

import streamlit as st


def render_create_page():
    """Render the simulation creation page."""
    st.markdown("## ➕ Create New Simulation")
    st.markdown("Create a new project simulation with guided setup and configuration options.")

    # Quick creation options
    st.markdown("### Quick Start Options")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🚀 Quick Web App", key="quick_web", use_container_width=True):
            create_quick_simulation("web_application", "Quick Web Application")

    with col2:
        if st.button("📱 Quick Mobile App", key="quick_mobile", use_container_width=True):
            create_quick_simulation("mobile_app", "Quick Mobile Application")

    with col3:
        if st.button("🔌 Quick API", key="quick_api", use_container_width=True):
            create_quick_simulation("api_service", "Quick API Service")

    st.markdown("---")

    # Advanced creation form
    st.markdown("### Advanced Configuration")

    with st.form("create_simulation_form"):
        st.subheader("Simulation Details")

        # Basic information
        name = st.text_input(
            "Simulation Name *",
            placeholder="e.g., E-commerce Platform Development",
            help="Choose a descriptive name for your simulation"
        )

        description = st.text_area(
            "Description",
            placeholder="Describe the project and its goals...",
            height=80
        )

        col1, col2 = st.columns(2)
        with col1:
            sim_type = st.selectbox(
                "Project Type *",
                options=["web_application", "mobile_app", "api_service", "data_pipeline", "microservices", "ai_ml_project"],
                format_func=lambda x: x.replace("_", " ").title(),
                help="Select the type of project to simulate"
            )

            complexity = st.selectbox(
                "Complexity Level *",
                options=["low", "medium", "high"],
                format_func=lambda x: x.title(),
                help="Choose the complexity level for realistic simulation"
            )

        with col2:
            team_size = st.slider(
                "Team Size",
                min_value=1,
                max_value=20,
                value=5,
                help="Number of team members"
            )

            duration = st.slider(
                "Duration (weeks)",
                min_value=1,
                max_value=52,
                value=8,
                help="Estimated project duration"
            )

        # Advanced options
        with st.expander("Advanced Options"):
            enable_ecosystem = st.checkbox(
                "Enable Ecosystem Integration",
                value=True,
                help="Integrate with ecosystem services"
            )

            output_formats = st.multiselect(
                "Report Formats",
                options=["json", "html", "pdf", "markdown"],
                default=["json", "html"],
                help="Select output formats for reports"
            )

        # Submit button
        submitted = st.form_submit_button("Create Simulation", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("❌ Please provide a simulation name")
            elif not sim_type:
                st.error("❌ Please select a project type")
            else:
                # Create simulation
                simulation_data = {
                    'name': name,
                    'description': description,
                    'type': sim_type,
                    'complexity': complexity,
                    'team_size': team_size,
                    'duration_weeks': duration,
                    'enable_ecosystem': enable_ecosystem,
                    'output_formats': output_formats
                }

                create_simulation(simulation_data)


def create_quick_simulation(sim_type: str, name: str):
    """Create a quick simulation with default settings."""
    simulation_data = {
        'name': name,
        'description': f"Quick {sim_type.replace('_', ' ').title()} simulation",
        'type': sim_type,
        'complexity': 'medium',
        'team_size': 5,
        'duration_weeks': 8,
        'enable_ecosystem': True,
        'output_formats': ['json', 'html']
    }

    create_simulation(simulation_data)


def create_simulation(simulation_data: Dict[str, Any]):
    """Create simulation using the provided data."""
    try:
        # This is a placeholder - in real implementation, this would call the simulation service
        st.success(f"🎉 Simulation '{simulation_data['name']}' created successfully!")
        st.balloons()

        # Display simulation summary
        with st.expander("Simulation Details"):
            st.write(f"**Name:** {simulation_data['name']}")
            st.write(f"**Type:** {simulation_data['type'].replace('_', ' ').title()}")
            st.write(f"**Complexity:** {simulation_data['complexity'].title()}")
            st.write(f"**Team Size:** {simulation_data['team_size']}")
            st.write(f"**Duration:** {simulation_data['duration_weeks']} weeks")
            st.write(f"**Ecosystem Integration:** {'Enabled' if simulation_data['enable_ecosystem'] else 'Disabled'}")

        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start Simulation", key="start_created_sim"):
                st.session_state.current_page = "monitor"
                st.rerun()

        with col2:
            if st.button("📊 View Dashboard", key="view_dashboard"):
                st.session_state.current_page = "overview"
                st.rerun()

    except Exception as e:
        st.error(f"❌ Failed to create simulation: {str(e)}")
