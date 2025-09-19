"""Guided Setup Wizard Page.

This module provides a comprehensive, user-friendly multi-step wizard
for creating and configuring project simulations with all required inputs.
"""

import streamlit as st
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import json
import uuid

from services.clients.simulation_client import SimulationClient
from infrastructure.config.config import get_config


def render_wizard_page():
    """Render the comprehensive guided setup wizard page."""
    st.markdown("## 🧙‍♂️ Guided Simulation Setup Wizard")
    st.markdown("Create comprehensive project simulations with our step-by-step guided wizard.")

    # Initialize wizard session state
    initialize_wizard_state()

    # Check if wizard is already in progress
    if 'wizard_active' not in st.session_state:
        render_wizard_start()
    else:
        render_wizard_steps()

    # Wizard navigation
    render_wizard_navigation()


def initialize_wizard_state():
    """Initialize session state for the wizard."""
    if 'wizard_data' not in st.session_state:
        st.session_state.wizard_data = {
            'step': 1,
            'total_steps': 7,
            'project_info': {},
            'team_config': {},
            'timeline_config': {},
            'budget_config': {},
            'risk_assessment': {},
            'advanced_config': {},
            'validation_errors': {},
            'progress': {}
        }

    if 'wizard_templates' not in st.session_state:
        st.session_state.wizard_templates = load_wizard_templates()


def render_wizard_start():
    """Render the wizard start screen with options."""
    st.markdown("### 🚀 Choose Your Setup Method")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🏃‍♂️ Quick Start")
        st.markdown("Get started quickly with pre-configured templates for common scenarios.")

        if st.button("🚀 Quick Start", key="quick_start", type="primary", use_container_width=True):
            st.session_state.wizard_active = True
            st.session_state.wizard_data['setup_method'] = 'quick'
            st.session_state.wizard_data['step'] = 1
            st.rerun()

        st.markdown("**Perfect for:**")
        st.markdown("- First-time users")
        st.markdown("- Standard projects")
        st.markdown("- Rapid prototyping")

    with col2:
        st.markdown("#### 🧙‍♂️ Guided Setup")
        st.markdown("Step through our comprehensive wizard with detailed configuration options.")

        if st.button("🧙‍♂️ Guided Setup", key="guided_setup", type="primary", use_container_width=True):
            st.session_state.wizard_active = True
            st.session_state.wizard_data['setup_method'] = 'guided'
            st.session_state.wizard_data['step'] = 1
            st.rerun()

        st.markdown("**Perfect for:**")
        st.markdown("- Complex projects")
        st.markdown("- Custom requirements")
        st.markdown("- Advanced users")

    with col3:
        st.markdown("#### 📤 Import Configuration")
        st.markdown("Upload an existing YAML configuration file to get started.")

        uploaded_file = st.file_uploader("Upload YAML config", type=['yaml', 'yml'], key="config_upload")

        if uploaded_file is not None and st.button("📤 Import & Continue", key="import_config"):
            config_data = load_config_from_file(uploaded_file)
            if config_data:
                st.session_state.wizard_active = True
                st.session_state.wizard_data['setup_method'] = 'import'
                st.session_state.wizard_data['imported_config'] = config_data
                st.session_state.wizard_data['step'] = 2  # Skip to team config
                st.success("✅ Configuration imported successfully!")
                st.rerun()

        st.markdown("**Perfect for:**")
        st.markdown("- Existing configurations")
        st.markdown("- Batch setups")
        st.markdown("- Configuration reuse")

    # Recent projects
    st.markdown("---")
    st.markdown("### 🕐 Recent Projects")

    recent_projects = get_recent_projects()

    if recent_projects:
        for project in recent_projects[:3]:
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.write(f"**{project['name']}**")

            with col2:
                st.write(f"*{project['type']} • {project['complexity']}*")

            with col3:
                if st.button("🔄 Reuse", key=f"reuse_{project['id']}"):
                    reuse_project_config(project)
                    st.session_state.wizard_active = True
                    st.session_state.wizard_data['setup_method'] = 'reuse'
                    st.rerun()
    else:
        st.info("No recent projects found. Start your first simulation above!")


def render_wizard_steps():
    """Render the multi-step wizard interface."""
    wizard_data = st.session_state.wizard_data

    # Progress bar
    progress = (wizard_data['step'] - 1) / wizard_data['total_steps']
    st.progress(progress)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.markdown(f"**Step {wizard_data['step']} of {wizard_data['total_steps']}**")

    with col2:
        step_names = [
            "Project Basics",
            "Team Setup",
            "Timeline Design",
            "Budget Planning",
            "Risk Assessment",
            "Advanced Config",
            "Review & Launch"
        ]
        st.markdown(f"**{step_names[wizard_data['step'] - 1]}**")

    with col3:
        st.markdown(f"**{int(progress * 100)}% Complete**")

    # Render current step
    if wizard_data['step'] == 1:
        render_step_1_project_basics()
    elif wizard_data['step'] == 2:
        render_step_2_team_setup()
    elif wizard_data['step'] == 3:
        render_step_3_timeline_design()
    elif wizard_data['step'] == 4:
        render_step_4_budget_planning()
    elif wizard_data['step'] == 5:
        render_step_5_risk_assessment()
    elif wizard_data['step'] == 6:
        render_step_6_advanced_config()
    elif wizard_data['step'] == 7:
        render_step_7_review_launch()

    # Validation errors
    if wizard_data.get('validation_errors'):
        st.error("⚠️ Please fix the following issues before continuing:")
        for field, errors in wizard_data['validation_errors'].items():
            for error in errors:
                st.error(f"• {field}: {error}")


def render_step_1_project_basics():
    """Render Step 1: Project Basics."""
    st.markdown("### 🎯 Step 1: Project Basics")
    st.markdown("Let's start with the fundamental information about your project.")

    wizard_data = st.session_state.wizard_data

    # Project information
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📝 Basic Information")

        project_name = st.text_input(
            "Project Name *",
            value=wizard_data['project_info'].get('name', ''),
            placeholder="e.g., AI-Powered E-commerce Platform",
            key="project_name"
        )

        project_description = st.text_area(
            "Project Description",
            value=wizard_data['project_info'].get('description', ''),
            placeholder="Describe your project in detail...",
            height=100,
            key="project_description"
        )

        # Enhanced project type selection with detailed descriptions
        project_type_options = [
            {
                "name": "Web Application",
                "description": "Traditional web application with frontend and backend",
                "technologies": "React/Vue/Angular + Python/Node.js + PostgreSQL",
                "complexity": "Medium",
                "duration": "8-16 weeks",
                "team_size": "4-8 developers"
            },
            {
                "name": "API Service",
                "description": "RESTful API service with comprehensive documentation",
                "technologies": "FastAPI/Express + PostgreSQL/Redis + Docker",
                "complexity": "Medium",
                "duration": "6-12 weeks",
                "team_size": "3-6 developers"
            },
            {
                "name": "Mobile Application",
                "description": "Cross-platform mobile app with native performance",
                "technologies": "React Native/Flutter + Firebase + iOS/Android",
                "complexity": "Medium-High",
                "duration": "10-20 weeks",
                "team_size": "4-10 developers"
            },
            {
                "name": "Microservices",
                "description": "Distributed system with multiple independent services",
                "technologies": "Kubernetes + Docker + Service Mesh + CI/CD",
                "complexity": "High",
                "duration": "16-32 weeks",
                "team_size": "8-15 developers"
            },
            {
                "name": "Data Pipeline",
                "description": "ETL/ELT pipeline for data processing and analytics",
                "technologies": "Apache Airflow + Spark + Snowflake/Redshift",
                "complexity": "Medium-High",
                "duration": "12-24 weeks",
                "team_size": "5-12 developers"
            },
            {
                "name": "Machine Learning",
                "description": "ML/AI solution with model training and deployment",
                "technologies": "Python + TensorFlow/PyTorch + MLflow + Kubernetes",
                "complexity": "High",
                "duration": "14-28 weeks",
                "team_size": "6-14 developers"
            }
        ]

        project_type_names = [opt["name"] for opt in project_type_options]
        selected_type_index = get_project_type_index(wizard_data['project_info'].get('type'))

        project_type = st.selectbox(
            "Project Type *",
            options=project_type_names,
            index=selected_type_index,
            key="project_type"
        )

        # Show detailed information for selected project type
        selected_type_info = next((opt for opt in project_type_options if opt["name"] == project_type), project_type_options[0])

        with st.expander(f"📋 {project_type} Details", expanded=False):
            col_a, col_b = st.columns(2)

            with col_a:
                st.write(f"**Description:** {selected_type_info['description']}")
                st.write(f"**Technologies:** {selected_type_info['technologies']}")
                st.write(f"**Complexity:** {selected_type_info['complexity']}")

            with col_b:
                st.write(f"**Typical Duration:** {selected_type_info['duration']}")
                st.write(f"**Recommended Team:** {selected_type_info['team_size']}")

                # Show technology recommendations
                tech_stack = selected_type_info['technologies'].split(' + ')
                st.write("**Technology Stack:**")
                for tech in tech_stack:
                    st.write(f"• {tech.strip()}")

        # Project type recommendations
        st.markdown("#### 💡 Recommendations")

        recommendations = get_project_type_recommendations(project_type)
        for rec in recommendations:
            if rec['type'] == 'success':
                st.success(f"✅ {rec['message']}")
            elif rec['type'] == 'warning':
                st.warning(f"⚠️ {rec['message']}")
            elif rec['type'] == 'info':
                st.info(f"💡 {rec['message']}")

    with col2:
        st.markdown("#### 🎯 Project Scope")

        # Enhanced complexity selection with detailed information
        complexity_options = [
            {
                "name": "Simple",
                "description": "Straightforward implementation with well-understood requirements",
                "duration": "4-8 weeks",
                "team": "2-4 people",
                "risk": "Low",
                "technologies": "Standard, well-established tech stack",
                "requirements": "Clear, stable requirements with minimal changes"
            },
            {
                "name": "Medium",
                "description": "Moderate complexity with some technical challenges",
                "duration": "8-16 weeks",
                "team": "4-8 people",
                "risk": "Medium",
                "technologies": "Mix of familiar and some new technologies",
                "requirements": "Mostly stable with some evolving requirements"
            },
            {
                "name": "Complex",
                "description": "High complexity with advanced technical requirements",
                "duration": "16-32 weeks",
                "team": "8-15 people",
                "risk": "High",
                "technologies": "Advanced, cutting-edge technologies and architectures",
                "requirements": "Complex, evolving requirements with technical unknowns"
            }
        ]

        complexity_names = [opt["name"] for opt in complexity_options]
        selected_complexity_index = get_complexity_index(wizard_data['project_info'].get('complexity'))

        complexity = st.selectbox(
            "Complexity Level *",
            options=complexity_names,
            index=selected_complexity_index,
            key="complexity"
        )

        # Show detailed complexity information
        selected_complexity = next((opt for opt in complexity_options if opt["name"] == complexity), complexity_options[1])

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Typical Duration", selected_complexity["duration"])
        with col_b:
            st.metric("Team Size", selected_complexity["team"])
        with col_c:
            risk_color = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}[selected_complexity["risk"]]
            st.metric("Risk Level", f"{risk_color} {selected_complexity['risk']}")

        with st.expander(f"📋 {complexity} Project Details", expanded=False):
            st.write(f"**Description:** {selected_complexity['description']}")
            st.write(f"**Technology Approach:** {selected_complexity['technologies']}")
            st.write(f"**Requirements Profile:** {selected_complexity['requirements']}")

            # Complexity assessment questionnaire
            st.markdown("---")
            st.markdown("#### 🧠 Quick Complexity Assessment")

            assessment_score = 0
            total_questions = 5

            # Question 1: Technology familiarity
            tech_familiarity = st.selectbox(
                "How familiar is your team with the required technology stack?",
                ["Very Familiar", "Somewhat Familiar", "Limited Experience", "New Technology"],
                key="tech_familiarity"
            )
            assessment_score += {"Very Familiar": 0, "Somewhat Familiar": 1, "Limited Experience": 2, "New Technology": 3}[tech_familiarity]

            # Question 2: Requirements stability
            req_stability = st.selectbox(
                "How stable are your project requirements?",
                ["Very Stable", "Mostly Stable", "Some Changes Expected", "High Uncertainty"],
                key="req_stability"
            )
            assessment_score += {"Very Stable": 0, "Mostly Stable": 1, "Some Changes Expected": 2, "High Uncertainty": 3}[req_stability]

            # Question 3: Timeline pressure
            timeline_pressure = st.selectbox(
                "What is your timeline flexibility?",
                ["Flexible Timeline", "Moderate Pressure", "Tight Deadline", "Fixed Deadline"],
                key="timeline_pressure"
            )
            assessment_score += {"Flexible Timeline": 0, "Moderate Pressure": 1, "Tight Deadline": 2, "Fixed Deadline": 3}[timeline_pressure]

            # Question 4: Team experience
            team_experience = st.selectbox(
                "What is your team's overall experience level?",
                ["Expert Team", "Experienced Team", "Mixed Experience", "Junior Team"],
                key="team_experience"
            )
            assessment_score += {"Expert Team": 0, "Experienced Team": 1, "Mixed Experience": 2, "Junior Team": 3}[team_experience]

            # Question 5: Project scope
            project_scope = st.selectbox(
                "What is the scope of your project?",
                ["Well-defined Scope", "Moderate Scope", "Broad Scope", "Undefined Scope"],
                key="project_scope"
            )
            assessment_score += {"Well-defined Scope": 0, "Moderate Scope": 1, "Broad Scope": 2, "Undefined Scope": 3}[project_scope]

            # Calculate recommended complexity
            recommended_complexity = "Simple" if assessment_score <= 3 else "Medium" if assessment_score <= 7 else "Complex"
            assessment_percentage = (assessment_score / (total_questions * 3)) * 100

            st.markdown("#### 📊 Assessment Results")
            col_x, col_y = st.columns(2)

            with col_x:
                if recommended_complexity == complexity:
                    st.success(f"✅ Assessment matches your selection: {complexity}")
                else:
                    st.warning(f"⚠️ Assessment suggests: {recommended_complexity} (you selected: {complexity})")

            with col_y:
                st.metric("Complexity Score", ".1f", assessment_percentage)

        # Auto-adjust duration based on complexity and project type
        default_duration = get_recommended_duration(complexity, project_type)

        duration_weeks = st.slider(
            "Duration (weeks)",
            min_value=2,
            max_value=52,
            value=wizard_data['project_info'].get('duration_weeks', default_duration),
            help=f"Recommended: {default_duration} weeks for {complexity.lower()} {project_type.lower()}",
            key="duration_weeks"
        )

        # Budget estimation based on complexity, duration, and project type
        estimated_budget = estimate_project_budget(complexity, duration_weeks, project_type)

        budget_ranges = [
            "Under $50K",
            "$50K - $100K",
            "$100K - $250K",
            "$250K - $500K",
            "$500K - $1M",
            "Over $1M"
        ]

        # Auto-select appropriate budget range
        auto_budget_index = get_budget_range_from_estimate(estimated_budget)

        budget_range = st.selectbox(
            "Budget Range",
            options=budget_ranges,
            index=auto_budget_index,
            help=f"Estimated budget: ${estimated_budget:,.0f}",
            key="budget_range"
        )

        st.success(f"💰 **Estimated Budget:** ${estimated_budget:,.0f} for {duration_weeks} weeks")

    # Quick setup for quick start method
    if wizard_data.get('setup_method') == 'quick':
        st.markdown("---")
        st.markdown("#### 🚀 Quick Setup Options")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🏪 E-commerce Platform", key="template_ecommerce"):
                apply_template('ecommerce')

        with col2:
            if st.button("📱 Mobile App", key="template_mobile"):
                apply_template('mobile_app')

        with col3:
            if st.button("🔧 API Service", key="template_api"):
                apply_template('api_service')

    # Save step data
    if st.button("Continue to Team Setup →", key="step1_continue", type="primary"):
        if validate_step_1():
            save_step_1_data(project_name, project_description, project_type, complexity, duration_weeks, budget_range)
            wizard_data['step'] = 2
            st.rerun()


def render_step_2_team_setup():
    """Render Step 2: Team Setup."""
    st.markdown("### 👥 Step 2: Team Setup")
    st.markdown("Configure your project team with roles, skills, and expertise levels.")

    wizard_data = st.session_state.wizard_data

    # Team size recommendation
    project_complexity = wizard_data['project_info'].get('complexity', 'Medium')
    recommended_team_size = get_recommended_team_size(project_complexity)

    st.info(f"**Recommended team size for {project_complexity.lower()} complexity:** {recommended_team_size} members")

    # Team composition
    st.markdown("#### 👥 Team Composition")

    if 'team_members' not in wizard_data['team_config']:
        wizard_data['team_config']['team_members'] = []

    team_members = wizard_data['team_config']['team_members']

    # Add team member
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("**Add Team Members**")

    with col2:
        if st.button("➕ Add Member", key="add_team_member"):
            team_members.append({
                'id': str(uuid.uuid4()),
                'name': '',
                'role': 'developer',
                'expertise_level': 'intermediate',
                'skills': [],
                'cost_per_hour': 50.0
            })
            st.rerun()

    # Display current team members
    for i, member in enumerate(team_members):
        render_team_member_form(i, member)

    # Team analysis
    if team_members:
        st.markdown("#### 📊 Team Analysis")

        col1, col2, col3 = st.columns(3)

        with col1:
            total_cost = sum(m.get('cost_per_hour', 50) * 40 * 4 for m in team_members)  # Monthly estimate
            st.metric("Monthly Cost", f"${total_cost:,.0f}")

        with col2:
            roles = [m.get('role', 'developer') for m in team_members]
            unique_roles = len(set(roles))
            st.metric("Role Diversity", unique_roles)

        with col3:
            avg_expertise = sum(get_expertise_score(m.get('expertise_level', 'intermediate')) for m in team_members) / len(team_members)
            st.metric("Avg Expertise", ".2f", avg_expertise)

        # Team recommendations
        recommendations = get_team_recommendations(team_members, project_complexity)
        if recommendations:
            st.markdown("#### 💡 Recommendations")
            for rec in recommendations:
                st.info(f"💡 {rec}")

    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("← Back to Project Basics", key="step2_back"):
            wizard_data['step'] = 1
            st.rerun()

    with col3:
        if st.button("Continue to Timeline →", key="step2_continue", type="primary"):
            if validate_step_2():
                wizard_data['step'] = 3
                st.rerun()


def render_step_3_timeline_design():
    """Render Step 3: Timeline Design."""
    st.markdown("### 📅 Step 3: Timeline Design")
    st.markdown("Design your project timeline with phases, milestones, and dependencies.")

    wizard_data = st.session_state.wizard_data

    # Timeline overview
    project_duration = wizard_data['project_info'].get('duration_weeks', 12)
    st.info(f"**Project Duration:** {project_duration} weeks")

    # Phase management
    st.markdown("#### 📊 Project Phases")

    if 'phases' not in wizard_data['timeline_config']:
        wizard_data['timeline_config']['phases'] = []

    phases = wizard_data['timeline_config']['phases']

    # Add phase
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("**Project Phases**")

    with col2:
        if st.button("➕ Add Phase", key="add_phase"):
            phases.append({
                'id': str(uuid.uuid4()),
                'name': '',
                'description': '',
                'duration_days': 7,
                'start_day': 1,
                'dependencies': [],
                'deliverables': []
            })
            st.rerun()

    # Display phases
    for i, phase in enumerate(phases):
        render_phase_form(i, phase)

    # Timeline visualization
    if phases:
        st.markdown("#### 📈 Timeline Visualization")
        render_timeline_visualization(phases, project_duration)

        # Timeline analysis
        st.markdown("#### 📊 Timeline Analysis")

        col1, col2, col3 = st.columns(3)

        with col1:
            total_days = sum(p.get('duration_days', 7) for p in phases)
            st.metric("Total Duration", f"{total_days} days")

        with col2:
            critical_path = calculate_critical_path(phases)
            st.metric("Critical Path", f"{critical_path} days")

        with col3:
            resource_conflicts = detect_resource_conflicts(phases)
            if resource_conflicts > 0:
                st.metric("Resource Conflicts", resource_conflicts, delta=f"-{resource_conflicts}")
            else:
                st.metric("Resource Conflicts", "None")

    # Quick templates
    st.markdown("#### 🏗️ Phase Templates")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Standard SDLC", key="template_sdlc"):
            apply_timeline_template('sdlc')

    with col2:
        if st.button("🚀 Agile Sprints", key="template_agile"):
            apply_timeline_template('agile')

    with col3:
        if st.button("⚡ MVP Approach", key="template_mvp"):
            apply_timeline_template('mvp')

    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("← Back to Team Setup", key="step3_back"):
            wizard_data['step'] = 2
            st.rerun()

    with col3:
        if st.button("Continue to Budget →", key="step3_continue", type="primary"):
            if validate_step_3():
                wizard_data['step'] = 4
                st.rerun()


def render_step_4_budget_planning():
    """Render Step 4: Budget Planning."""
    st.markdown("### 💰 Step 4: Budget Planning")
    st.markdown("Plan your project budget with cost estimation and ROI analysis.")

    wizard_data = st.session_state.wizard_data

    # Budget overview
    col1, col2, col3 = st.columns(3)

    with col1:
        team_cost = calculate_team_cost(wizard_data['team_config'].get('team_members', []))
        st.metric("Team Cost", f"${team_cost:,.0f}/month")

    with col2:
        infrastructure_cost = estimate_infrastructure_cost(wizard_data['project_info'])
        st.metric("Infrastructure", f"${infrastructure_cost:,.0f}/month")

    with col3:
        total_monthly = team_cost + infrastructure_cost
        st.metric("Total Monthly", f"${total_monthly:,.0f}")

    # Cost breakdown
    st.markdown("#### 📊 Cost Breakdown")

    # Team costs
    if wizard_data['team_config'].get('team_members'):
        st.markdown("**👥 Team Costs**")

        team_data = []
        for member in wizard_data['team_config']['team_members']:
            monthly_cost = member.get('cost_per_hour', 50) * 40 * 4  # 40 hours/week * 4 weeks
            team_data.append({
                'Member': member.get('name', 'Unnamed'),
                'Role': member.get('role', 'developer').title(),
                'Monthly Cost': monthly_cost
            })

        if team_data:
            import pandas as pd
            df = pd.DataFrame(team_data)
            st.dataframe(df, use_container_width=True)

    # Infrastructure costs
    st.markdown("**🖥️ Infrastructure Costs**")

    infra_costs = {
        'Cloud Hosting': infrastructure_cost * 0.4,
        'Development Tools': infrastructure_cost * 0.2,
        'Third-party Services': infrastructure_cost * 0.25,
        'Monitoring & Security': infrastructure_cost * 0.15
    }

    for category, cost in infra_costs.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"• {category}")
        with col2:
            st.write(f"${cost:,.0f}")

    # ROI Calculator
    st.markdown("#### 📈 ROI Calculator")

    col1, col2 = st.columns(2)

    with col1:
        project_benefits = st.number_input(
            "Expected Annual Benefits ($)",
            min_value=0,
            value=100000,
            step=10000,
            key="project_benefits"
        )

        project_duration_years = st.slider(
            "Project Duration (years)",
            min_value=1,
            max_value=5,
            value=2,
            key="project_duration_years"
        )

    with col2:
        total_investment = total_monthly * 12 * project_duration_years
        roi_percentage = ((project_benefits - total_investment) / total_investment) * 100 if total_investment > 0 else 0

        st.metric("Total Investment", f"${total_investment:,.0f}")
        st.metric("ROI", ".1f", roi_percentage)

        if roi_percentage > 0:
            st.success(f"✅ Positive ROI: {roi_percentage:.1f}%")
        else:
            st.warning(f"⚠️ Negative ROI: {roi_percentage:.1f}%")

    # Budget recommendations
    st.markdown("#### 💡 Budget Recommendations")

    recommendations = get_budget_recommendations(total_monthly, wizard_data['project_info'])
    for rec in recommendations:
        if rec['type'] == 'warning':
            st.warning(f"⚠️ {rec['message']}")
        elif rec['type'] == 'success':
            st.success(f"✅ {rec['message']}")
        else:
            st.info(f"💡 {rec['message']}")

    # Save budget data
    wizard_data['budget_config'].update({
        'monthly_cost': total_monthly,
        'annual_benefits': project_benefits,
        'total_investment': total_investment,
        'roi_percentage': roi_percentage
    })

    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("← Back to Timeline", key="step4_back"):
            wizard_data['step'] = 3
            st.rerun()

    with col3:
        if st.button("Continue to Risk Assessment →", key="step4_continue", type="primary"):
            wizard_data['step'] = 5
            st.rerun()


def render_step_5_risk_assessment():
    """Render Step 5: Risk Assessment."""
    st.markdown("### ⚠️ Step 5: Risk Assessment")
    st.markdown("Identify potential risks and assess project success probability.")

    wizard_data = st.session_state.wizard_data

    # Risk questionnaire
    st.markdown("#### 📋 Risk Assessment Questionnaire")

    risk_factors = {
        'team_experience': {
            'question': 'How experienced is your team with this technology stack?',
            'options': ['Very Experienced', 'Somewhat Experienced', 'Limited Experience', 'New Technology']
        },
        'requirement_stability': {
            'question': 'How stable are the project requirements?',
            'options': ['Very Stable', 'Mostly Stable', 'Some Changes Expected', 'High Uncertainty']
        },
        'timeline_realism': {
            'question': 'How realistic is the project timeline?',
            'options': ['Very Realistic', 'Reasonable', 'Aggressive', 'Unrealistic']
        },
        'budget_contingency': {
            'question': 'Do you have budget contingency for unexpected issues?',
            'options': ['Yes, >20% contingency', 'Yes, 10-20% contingency', 'Minimal contingency', 'No contingency']
        },
        'stakeholder_alignment': {
            'question': 'How aligned are stakeholders on project goals?',
            'options': ['Fully Aligned', 'Mostly Aligned', 'Some Misalignment', 'Significant Misalignment']
        }
    }

    risk_scores = {}
    for factor, config in risk_factors.items():
        score = st.selectbox(
            config['question'],
            options=config['options'],
            index=get_risk_score_index(wizard_data['risk_assessment'].get(factor)),
            key=f"risk_{factor}"
        )
        risk_scores[factor] = score

    # Calculate risk score
    risk_score = calculate_risk_score(risk_scores)
    success_probability = calculate_success_probability(risk_score)

    # Risk assessment results
    st.markdown("#### 📊 Risk Assessment Results")

    col1, col2, col3 = st.columns(3)

    with col1:
        risk_color = "🟢" if risk_score < 30 else "🟡" if risk_score < 60 else "🔴"
        st.metric("Risk Score", ".1f", risk_score)

    with col2:
        success_color = "🟢" if success_probability > 70 else "🟡" if success_probability > 50 else "🔴"
        st.metric("Success Probability", ".1f", success_probability)

    with col3:
        risk_level = "Low" if risk_score < 30 else "Medium" if risk_score < 60 else "High"
        st.metric("Risk Level", risk_level)

    # Risk mitigation strategies
    st.markdown("#### 🛡️ Risk Mitigation Strategies")

    mitigation_strategies = get_mitigation_strategies(risk_scores, risk_score)

    for strategy in mitigation_strategies:
        priority_icon = "🔴" if strategy['priority'] == 'High' else "🟡" if strategy['priority'] == 'Medium' else "🟢"
        with st.expander(f"{priority_icon} {strategy['title']} ({strategy['priority']} Priority)"):
            st.write(f"**Description:** {strategy['description']}")
            st.write(f"**Implementation:** {strategy['implementation']}")
            st.write(f"**Expected Impact:** {strategy['impact']}")

    # Save risk assessment
    wizard_data['risk_assessment'].update({
        'risk_scores': risk_scores,
        'risk_score': risk_score,
        'success_probability': success_probability,
        'risk_level': risk_level,
        'mitigation_strategies': mitigation_strategies
    })

    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("← Back to Budget", key="step5_back"):
            wizard_data['step'] = 4
            st.rerun()

    with col3:
        if st.button("Continue to Advanced Config →", key="step5_continue", type="primary"):
            wizard_data['step'] = 6
            st.rerun()


def render_step_6_advanced_config():
    """Render Step 6: Advanced Configuration."""
    st.markdown("### ⚙️ Step 6: Advanced Configuration")
    st.markdown("Configure advanced simulation settings and ecosystem integrations.")

    wizard_data = st.session_state.wizard_data

    # Simulation settings
    st.markdown("#### 🎮 Simulation Settings")

    col1, col2 = st.columns(2)

    with col1:
        simulation_type = st.selectbox(
            "Simulation Type",
            options=["Full Project", "Phase Focus", "Team Dynamics", "Document Generation", "Workflow Execution", "Performance Test"],
            index=get_simulation_type_index(wizard_data['advanced_config'].get('simulation_type')),
            key="simulation_type"
        )

        max_execution_time = st.slider(
            "Max Execution Time (minutes)",
            min_value=30,
            max_value=480,
            value=wizard_data['advanced_config'].get('max_execution_time', 120),
            key="max_execution_time"
        )

    with col2:
        real_time_progress = st.checkbox(
            "Real-time Progress Updates",
            value=wizard_data['advanced_config'].get('real_time_progress', True),
            key="real_time_progress"
        )

        websocket_enabled = st.checkbox(
            "WebSocket Communication",
            value=wizard_data['advanced_config'].get('websocket_enabled', True),
            key="websocket_enabled"
        )

        capture_metrics = st.checkbox(
            "Capture Performance Metrics",
            value=wizard_data['advanced_config'].get('capture_metrics', True),
            key="capture_metrics"
        )

    # Content generation settings
    st.markdown("#### 📝 Content Generation")

    col1, col2, col3 = st.columns(3)

    with col1:
        include_document_generation = st.checkbox(
            "Document Generation",
            value=wizard_data['advanced_config'].get('include_document_generation', True),
            key="include_document_generation"
        )

    with col2:
        include_workflow_execution = st.checkbox(
            "Workflow Execution",
            value=wizard_data['advanced_config'].get('include_workflow_execution', True),
            key="include_workflow_execution"
        )

    with col3:
        include_team_dynamics = st.checkbox(
            "Team Dynamics",
            value=wizard_data['advanced_config'].get('include_team_dynamics', True),
            key="include_team_dynamics"
        )

    # Ecosystem integration
    st.markdown("#### 🌐 Ecosystem Integration")

    ecosystem_services = {
        'enable_ecosystem_integration': {
            'label': 'Enable Ecosystem Integration',
            'description': 'Connect with other LLM Documentation Ecosystem services'
        },
        'enable_analysis': {
            'label': 'Analysis Service',
            'description': 'Document analysis and quality assessment'
        },
        'enable_orchestration': {
            'label': 'Workflow Orchestration',
            'description': 'Advanced workflow management and orchestration'
        },
        'enable_notification': {
            'label': 'Notification Service',
            'description': 'Automated notifications and alerts'
        },
        'enable_audit': {
            'label': 'Audit Integration',
            'description': 'Comprehensive audit trail and compliance'
        }
    }

    for service_key, service_config in ecosystem_services.items():
        enabled = st.checkbox(
            service_config['label'],
            value=wizard_data['advanced_config'].get(service_key, False),
            key=service_key
        )
        if enabled:
            st.caption(service_config['description'])

    # Performance settings
    st.markdown("#### ⚡ Performance Settings")

    col1, col2 = st.columns(2)

    with col1:
        generate_realistic_delays = st.checkbox(
            "Realistic Delays",
            value=wizard_data['advanced_config'].get('generate_realistic_delays', True),
            key="generate_realistic_delays"
        )

        enable_performance_monitoring = st.checkbox(
            "Performance Monitoring",
            value=wizard_data['advanced_config'].get('enable_performance_monitoring', True),
            key="enable_performance_monitoring"
        )

    with col2:
        delay_multiplier = st.slider(
            "Delay Multiplier",
            min_value=0.1,
            max_value=5.0,
            value=wizard_data['advanced_config'].get('delay_multiplier', 1.0),
            key="delay_multiplier"
        )

        resource_intensity = st.selectbox(
            "Resource Intensity",
            options=["Low", "Medium", "High", "Very High"],
            index=get_resource_intensity_index(wizard_data['advanced_config'].get('resource_intensity')),
            key="resource_intensity"
        )

    # Save advanced config
    wizard_data['advanced_config'].update({
        'simulation_type': simulation_type,
        'max_execution_time': max_execution_time,
        'real_time_progress': real_time_progress,
        'websocket_enabled': websocket_enabled,
        'capture_metrics': capture_metrics,
        'include_document_generation': include_document_generation,
        'include_workflow_execution': include_workflow_execution,
        'include_team_dynamics': include_team_dynamics,
        'generate_realistic_delays': generate_realistic_delays,
        'enable_performance_monitoring': enable_performance_monitoring,
        'delay_multiplier': delay_multiplier,
        'resource_intensity': resource_intensity
    })

    # Add ecosystem settings
    for service_key in ecosystem_services.keys():
        wizard_data['advanced_config'][service_key] = st.session_state.get(service_key, False)

    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("← Back to Risk Assessment", key="step6_back"):
            wizard_data['step'] = 5
            st.rerun()

    with col3:
        if st.button("Review & Launch →", key="step6_continue", type="primary"):
            if validate_step_6():
                wizard_data['step'] = 7
                st.rerun()


def render_step_7_review_launch():
    """Render Step 7: Review & Launch."""
    st.markdown("### 🎯 Step 7: Review & Launch")
    st.markdown("Review your simulation configuration and launch the simulation.")

    wizard_data = st.session_state.wizard_data

    # Configuration summary
    st.markdown("#### 📋 Configuration Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🎯 Project Basics**")
        st.write(f"**Name:** {wizard_data['project_info'].get('name', 'Not specified')}")
        st.write(f"**Type:** {wizard_data['project_info'].get('type', 'Not specified')}")
        st.write(f"**Complexity:** {wizard_data['project_info'].get('complexity', 'Not specified')}")
        st.write(f"**Duration:** {wizard_data['project_info'].get('duration_weeks', 0)} weeks")

    with col2:
        st.markdown("**👥 Team Setup**")
        team_members = wizard_data['team_config'].get('team_members', [])
        st.write(f"**Team Size:** {len(team_members)} members")
        if team_members:
            roles = [m.get('role', 'developer') for m in team_members]
            st.write(f"**Roles:** {', '.join(set(roles))}")

    # Timeline summary
    st.markdown("**📅 Timeline**")
    phases = wizard_data['timeline_config'].get('phases', [])
    if phases:
        st.write(f"**Phases:** {len(phases)}")
        total_duration = sum(p.get('duration_days', 0) for p in phases)
        st.write(f"**Total Duration:** {total_duration} days")
    else:
        st.write("No phases defined")

    # Budget summary
    st.markdown("**💰 Budget**")
    monthly_cost = wizard_data['budget_config'].get('monthly_cost', 0)
    roi = wizard_data['budget_config'].get('roi_percentage', 0)
    st.write(f"**Monthly Cost:** ${monthly_cost:,.0f}")
    st.write(f"**Expected ROI:** {roi:.1f}%")

    # Risk summary
    st.markdown("**⚠️ Risk Assessment**")
    risk_score = wizard_data['risk_assessment'].get('risk_score', 0)
    success_prob = wizard_data['risk_assessment'].get('success_probability', 0)
    risk_level = wizard_data['risk_assessment'].get('risk_level', 'Unknown')
    st.write(f"**Risk Level:** {risk_level}")
    st.write(f"**Success Probability:** {success_prob:.1f}%")

    # Advanced config summary
    st.markdown("**⚙️ Advanced Configuration**")
    sim_type = wizard_data['advanced_config'].get('simulation_type', 'Full Project')
    max_time = wizard_data['advanced_config'].get('max_execution_time', 120)
    st.write(f"**Simulation Type:** {sim_type}")
    st.write(f"**Max Execution Time:** {max_time} minutes")

    # Validation status
    st.markdown("#### ✅ Validation Status")

    validation_status = validate_complete_configuration(wizard_data)

    for check, status in validation_status.items():
        if status['valid']:
            st.success(f"✅ {check}")
        else:
            st.error(f"❌ {check}: {status['message']}")

    # Launch options
    st.markdown("#### 🚀 Launch Options")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Save Configuration", key="save_config"):
            config_path = save_configuration(wizard_data)
            if config_path:
                st.success(f"✅ Configuration saved to: {config_path}")

    with col2:
        if st.button("📤 Export YAML", key="export_yaml"):
            yaml_content = export_as_yaml(wizard_data)
            st.download_button(
                label="📥 Download YAML",
                data=yaml_content,
                file_name="simulation_config.yaml",
                mime="text/yaml",
                key="download_yaml"
            )

    with col3:
        if all(status['valid'] for status in validation_status.values()):
            if st.button("🚀 Launch Simulation", key="launch_simulation", type="primary"):
                simulation_id = launch_simulation(wizard_data)
                if simulation_id:
                    st.success(f"🎉 Simulation launched successfully!")
                    st.info(f"**Simulation ID:** {simulation_id}")
                    st.balloons()

                    # Reset wizard
                    if st.button("🔄 Start New Simulation", key="start_new"):
                        reset_wizard()
                        st.rerun()
        else:
            st.warning("⚠️ Please fix validation errors before launching.")

    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("← Back to Advanced Config", key="step7_back"):
            wizard_data['step'] = 6
            st.rerun()


def render_wizard_navigation():
    """Render wizard navigation controls."""
    if 'wizard_active' not in st.session_state:
        return

    wizard_data = st.session_state.wizard_data

    st.markdown("---")
    st.markdown("### 🧭 Wizard Navigation")

    # Step indicators
    cols = st.columns(wizard_data['total_steps'])

    step_names = [
        "Basics", "Team", "Timeline", "Budget", "Risk", "Advanced", "Launch"
    ]

    for i in range(wizard_data['total_steps']):
        with cols[i]:
            step_num = i + 1
            if step_num < wizard_data['step']:
                st.button(f"✅ {step_num}", key=f"nav_step_{step_num}", disabled=True)
            elif step_num == wizard_data['step']:
                st.button(f"🔵 {step_num}", key=f"nav_current_{step_num}", disabled=True)
            else:
                if st.button(f"⬜ {step_num}", key=f"nav_step_{step_num}"):
                    wizard_data['step'] = step_num
                    st.rerun()

            st.caption(step_names[i])

    # Quick actions
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Reset Wizard", key="reset_wizard"):
            if st.checkbox("Confirm reset", key="confirm_reset"):
                reset_wizard()
                st.rerun()

    with col2:
        if st.button("💾 Save Progress", key="save_progress"):
            save_wizard_progress()
            st.success("✅ Progress saved!")

    with col3:
        if st.button("❌ Exit Wizard", key="exit_wizard"):
            st.session_state.pop('wizard_active', None)
            st.rerun()


# Helper Functions

def load_wizard_templates() -> Dict[str, Any]:
    """Load predefined wizard templates."""
    return {
        'ecommerce': {
            'name': 'E-commerce Platform',
            'type': 'web_application',
            'complexity': 'complex',
            'duration_weeks': 16,
            'description': 'AI-powered e-commerce platform with microservices'
        },
        'mobile_app': {
            'name': 'Mobile Application',
            'type': 'mobile_application',
            'complexity': 'medium',
            'duration_weeks': 10,
            'description': 'Cross-platform mobile application'
        },
        'api_service': {
            'name': 'API Service',
            'type': 'api_service',
            'complexity': 'medium',
            'duration_weeks': 8,
            'description': 'RESTful API service with documentation'
        }
    }


def get_recent_projects() -> List[Dict[str, Any]]:
    """Get list of recent projects."""
    # Mock data - in production, this would come from a database
    return [
        {
            'id': 'proj_001',
            'name': 'AI-Powered E-commerce Platform',
            'type': 'Web Application',
            'complexity': 'Complex',
            'created_at': datetime.now() - timedelta(days=5)
        },
        {
            'id': 'proj_002',
            'name': 'Mobile App Development',
            'type': 'Mobile Application',
            'complexity': 'Medium',
            'created_at': datetime.now() - timedelta(days=12)
        }
    ]


def reset_wizard():
    """Reset the wizard to initial state."""
    keys_to_remove = [k for k in st.session_state.keys() if k.startswith('wizard_')]
    for key in keys_to_remove:
        del st.session_state[key]


def save_wizard_progress():
    """Save current wizard progress."""
    # In production, this would save to a database
    pass


# Step validation functions
def validate_step_1() -> bool:
    """Validate step 1 data."""
    wizard_data = st.session_state.wizard_data
    errors = {}

    if not wizard_data['project_info'].get('name', '').strip():
        errors['Project Name'] = ['Project name is required']

    if not wizard_data['project_info'].get('type'):
        errors['Project Type'] = ['Project type must be selected']

    if not wizard_data['project_info'].get('complexity'):
        errors['Complexity'] = ['Complexity level must be selected']

    wizard_data['validation_errors'] = errors
    return len(errors) == 0


def validate_step_2() -> bool:
    """Validate step 2 data."""
    wizard_data = st.session_state.wizard_data
    errors = {}

    team_members = wizard_data['team_config'].get('team_members', [])
    if not team_members:
        errors['Team Members'] = ['At least one team member is required']

    for i, member in enumerate(team_members):
        if not member.get('name', '').strip():
            errors[f'Team Member {i+1}'] = ['Name is required']
        if not member.get('role'):
            errors[f'Team Member {i+1}'] = ['Role must be selected']

    wizard_data['validation_errors'] = errors
    return len(errors) == 0


def validate_step_3() -> bool:
    """Validate step 3 data."""
    wizard_data = st.session_state.wizard_data
    errors = {}

    phases = wizard_data['timeline_config'].get('phases', [])
    if not phases:
        errors['Project Phases'] = ['At least one project phase is required']

    for i, phase in enumerate(phases):
        if not phase.get('name', '').strip():
            errors[f'Phase {i+1}'] = ['Phase name is required']

    wizard_data['validation_errors'] = errors
    return len(errors) == 0


def validate_step_6() -> bool:
    """Validate step 6 data."""
    # Advanced config validation - most fields are optional
    return True


def validate_complete_configuration(wizard_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the complete configuration."""
    validation_status = {
        'project_basics': {'valid': True, 'message': 'Project information complete'},
        'team_setup': {'valid': True, 'message': 'Team configuration complete'},
        'timeline': {'valid': True, 'message': 'Timeline configuration complete'},
        'budget': {'valid': True, 'message': 'Budget planning complete'},
        'risk_assessment': {'valid': True, 'message': 'Risk assessment complete'},
        'advanced_config': {'valid': True, 'message': 'Advanced configuration complete'}
    }

    # Check project basics
    if not wizard_data['project_info'].get('name'):
        validation_status['project_basics'] = {'valid': False, 'message': 'Project name is required'}

    # Check team setup
    if not wizard_data['team_config'].get('team_members'):
        validation_status['team_setup'] = {'valid': False, 'message': 'At least one team member required'}

    # Check timeline
    if not wizard_data['timeline_config'].get('phases'):
        validation_status['timeline'] = {'valid': False, 'message': 'At least one project phase required'}

    return validation_status


def save_configuration(wizard_data: Dict[str, Any]) -> Optional[str]:
    """Save configuration to file."""
    try:
        # In production, this would save to a proper location
        config_path = f"/tmp/simulation_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        # Save logic would go here
        return config_path
    except Exception as e:
        st.error(f"Failed to save configuration: {str(e)}")
        return None


def export_as_yaml(wizard_data: Dict[str, Any]) -> str:
    """Export configuration as YAML."""
    try:
        # Convert wizard data to YAML format
        yaml_content = "# Generated Simulation Configuration\n"
        yaml_content += f"project_name: \"{wizard_data['project_info'].get('name', '')}\"\n"
        yaml_content += f"project_type: \"{wizard_data['project_info'].get('type', '').lower()}\"\n"
        yaml_content += f"complexity_level: \"{wizard_data['project_info'].get('complexity', '').lower()}\"\n"
        # Add more YAML conversion logic as needed
        return yaml_content
    except Exception as e:
        return "# Error generating YAML configuration"


def launch_simulation(wizard_data: Dict[str, Any]) -> Optional[str]:
    """Launch the simulation with the configured settings."""
    try:
        # Convert wizard data to simulation request format
        simulation_request = {
            'name': wizard_data['project_info'].get('name', 'Unnamed Project'),
            'description': wizard_data['project_info'].get('description', ''),
            'type': wizard_data['project_info'].get('type', 'web_application').lower().replace(' ', '_'),
            'complexity': wizard_data['project_info'].get('complexity', 'medium').lower(),
            'duration_weeks': wizard_data['project_info'].get('duration_weeks', 12),
            'team_members': wizard_data['team_config'].get('team_members', []),
            'phases': wizard_data['timeline_config'].get('phases', [])
        }

        # In production, this would call the simulation service API
        # For now, return a mock simulation ID
        simulation_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return simulation_id

    except Exception as e:
        st.error(f"Failed to launch simulation: {str(e)}")
        return None


# Utility functions
def get_project_type_index(project_type: Optional[str]) -> int:
    """Get index for project type selection."""
    types = ["Web Application", "API Service", "Mobile Application", "Microservices", "Data Pipeline", "Machine Learning"]
    try:
        return types.index(project_type) if project_type else 0
    except ValueError:
        return 0


def get_complexity_index(complexity: Optional[str]) -> int:
    """Get index for complexity selection."""
    complexities = ["Simple", "Medium", "Complex"]
    try:
        return complexities.index(complexity) if complexity else 1
    except ValueError:
        return 1


def get_budget_index(budget_range: Optional[str]) -> int:
    """Get index for budget range selection."""
    ranges = ["Under $50K", "$50K - $100K", "$100K - $250K", "$250K - $500K", "$500K - $1M", "Over $1M"]
    try:
        return ranges.index(budget_range) if budget_range else 2
    except ValueError:
        return 2


def save_step_1_data(name: str, description: str, project_type: str, complexity: str, duration: int, budget_range: str):
    """Save step 1 data to wizard state."""
    wizard_data = st.session_state.wizard_data
    wizard_data['project_info'] = {
        'name': name,
        'description': description,
        'type': project_type,
        'complexity': complexity,
        'duration_weeks': duration,
        'budget_range': budget_range
    }


# Additional utility functions would be implemented here for the remaining steps
def render_team_member_form(i: int, member: Dict[str, Any]):
    """Render form for team member configuration."""
    # Implementation would include form fields for team member details
    pass


def get_recommended_team_size(complexity: str) -> int:
    """Get recommended team size based on complexity."""
    recommendations = {"Simple": 3, "Medium": 5, "Complex": 8}
    return recommendations.get(complexity, 5)


def get_team_recommendations(team_members: List[Dict[str, Any]], complexity: str) -> List[str]:
    """Get team configuration recommendations."""
    # Implementation would analyze team composition and provide recommendations
    return []


def render_phase_form(i: int, phase: Dict[str, Any]):
    """Render form for phase configuration."""
    # Implementation would include form fields for phase details
    pass


def render_timeline_visualization(phases: List[Dict[str, Any]], duration: int):
    """Render timeline visualization."""
    # Implementation would create a visual timeline chart
    pass


def calculate_critical_path(phases: List[Dict[str, Any]]) -> int:
    """Calculate critical path duration."""
    # Implementation would calculate the longest path through phases
    return sum(p.get('duration_days', 7) for p in phases)


def detect_resource_conflicts(phases: List[Dict[str, Any]]) -> int:
    """Detect resource conflicts in timeline."""
    # Implementation would analyze phase overlaps and resource usage
    return 0


def calculate_team_cost(team_members: List[Dict[str, Any]]) -> float:
    """Calculate total team cost."""
    return sum(m.get('cost_per_hour', 50) * 40 * 4 for m in team_members)


def estimate_infrastructure_cost(project_info: Dict[str, Any]) -> float:
    """Estimate infrastructure costs."""
    # Implementation would calculate infrastructure costs based on project type and complexity
    return 2000.0


def get_budget_recommendations(monthly_cost: float, project_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get budget planning recommendations."""
    # Implementation would provide budget recommendations
    return []


def get_risk_score_index(score: Optional[str]) -> int:
    """Get index for risk score selection."""
    options = ["Very Experienced", "Somewhat Experienced", "Limited Experience", "New Technology"]
    try:
        return options.index(score) if score else 1
    except ValueError:
        return 1


def calculate_risk_score(risk_scores: Dict[str, Any]) -> float:
    """Calculate overall risk score."""
    # Implementation would calculate risk score from individual factors
    return 35.0


def calculate_success_probability(risk_score: float) -> float:
    """Calculate success probability."""
    return max(0, 100 - risk_score)


def get_mitigation_strategies(risk_scores: Dict[str, Any], risk_score: float) -> List[Dict[str, Any]]:
    """Get risk mitigation strategies."""
    # Implementation would provide risk mitigation recommendations
    return []


def get_simulation_type_index(sim_type: Optional[str]) -> int:
    """Get index for simulation type selection."""
    types = ["Full Project", "Phase Focus", "Team Dynamics", "Document Generation", "Workflow Execution", "Performance Test"]
    try:
        return types.index(sim_type) if sim_type else 0
    except ValueError:
        return 0


def get_resource_intensity_index(intensity: Optional[str]) -> int:
    """Get index for resource intensity selection."""
    intensities = ["Low", "Medium", "High", "Very High"]
    try:
        return intensities.index(intensity) if intensity else 1
    except ValueError:
        return 1


def load_config_from_file(uploaded_file) -> Optional[Dict[str, Any]]:
    """Load configuration from uploaded file."""
    # Implementation would parse YAML file
    return {}


def reuse_project_config(project: Dict[str, Any]):
    """Reuse configuration from previous project."""
    # Implementation would load project configuration
    pass


def apply_template(template_name: str):
    """Apply predefined template."""
    # Implementation would apply template configuration
    pass


def apply_timeline_template(template_name: str):
    """Apply timeline template."""
    # Implementation would apply timeline template
    pass


def get_expertise_score(expertise_level: str) -> float:
    """Get numerical score for expertise level."""
    scores = {"junior": 1.0, "intermediate": 2.0, "senior": 3.0, "expert": 4.0, "lead": 5.0}
    return scores.get(expertise_level.lower(), 2.0)


# New helper functions for enhanced wizard

def get_project_type_recommendations(project_type: str) -> List[Dict[str, Any]]:
    """Get recommendations based on selected project type."""
    recommendations = []

    if project_type == "Web Application":
        recommendations = [
            {"type": "success", "message": "Great choice for traditional web development with proven technologies"},
            {"type": "info", "message": "Consider using modern frontend frameworks like React or Vue.js"},
            {"type": "info", "message": "PostgreSQL or MySQL are excellent database choices for web apps"}
        ]
    elif project_type == "API Service":
        recommendations = [
            {"type": "success", "message": "Perfect for microservices architecture and API-first development"},
            {"type": "info", "message": "FastAPI or Express.js provide excellent API development frameworks"},
            {"type": "info", "message": "Consider implementing comprehensive API documentation with OpenAPI/Swagger"}
        ]
    elif project_type == "Mobile Application":
        recommendations = [
            {"type": "warning", "message": "Mobile development requires specialized skills and testing across platforms"},
            {"type": "info", "message": "React Native or Flutter enable cross-platform development"},
            {"type": "info", "message": "Plan for additional QA time due to device fragmentation"}
        ]
    elif project_type == "Microservices":
        recommendations = [
            {"type": "warning", "message": "High complexity - requires DevOps expertise and infrastructure investment"},
            {"type": "info", "message": "Kubernetes provides excellent orchestration for microservices"},
            {"type": "info", "message": "Implement service mesh (Istio/Linkerd) for advanced service communication"}
        ]
    elif project_type == "Data Pipeline":
        recommendations = [
            {"type": "info", "message": "Apache Airflow is excellent for orchestrating complex data workflows"},
            {"type": "info", "message": "Consider cloud data warehouses like Snowflake or BigQuery for scalability"},
            {"type": "warning", "message": "Data pipelines require careful monitoring and error handling"}
        ]
    elif project_type == "Machine Learning":
        recommendations = [
            {"type": "warning", "message": "ML projects require specialized data science and MLOps expertise"},
            {"type": "info", "message": "Implement MLflow for experiment tracking and model management"},
            {"type": "info", "message": "Plan for GPU resources and model serving infrastructure"}
        ]

    return recommendations


def get_recommended_duration(complexity: str, project_type: str) -> int:
    """Get recommended duration based on complexity and project type."""
    base_durations = {
        ("Simple", "Web Application"): 6,
        ("Simple", "API Service"): 4,
        ("Simple", "Mobile Application"): 8,
        ("Simple", "Microservices"): 10,
        ("Simple", "Data Pipeline"): 6,
        ("Simple", "Machine Learning"): 8,
        ("Medium", "Web Application"): 12,
        ("Medium", "API Service"): 8,
        ("Medium", "Mobile Application"): 14,
        ("Medium", "Microservices"): 18,
        ("Medium", "Data Pipeline"): 16,
        ("Medium", "Machine Learning"): 20,
        ("Complex", "Web Application"): 20,
        ("Complex", "API Service"): 14,
        ("Complex", "Mobile Application"): 24,
        ("Complex", "Microservices"): 28,
        ("Complex", "Data Pipeline"): 24,
        ("Complex", "Machine Learning"): 32
    }

    return base_durations.get((complexity, project_type), 12)


def estimate_project_budget(complexity: str, duration_weeks: int, project_type: str) -> float:
    """Estimate project budget based on complexity, duration, and project type."""
    # Base rates per week by complexity
    base_rates = {
        "Simple": 8000,  # $8K/week for simple projects
        "Medium": 12000, # $12K/week for medium projects
        "Complex": 20000  # $20K/week for complex projects
    }

    # Multipliers by project type
    type_multipliers = {
        "Web Application": 1.0,
        "API Service": 0.8,
        "Mobile Application": 1.2,
        "Microservices": 1.5,
        "Data Pipeline": 1.3,
        "Machine Learning": 1.8
    }

    base_rate = base_rates.get(complexity, 12000)
    type_multiplier = type_multipliers.get(project_type, 1.0)

    # Calculate base cost
    base_cost = base_rate * duration_weeks * type_multiplier

    # Add contingency (15-25% based on complexity)
    contingency_rates = {"Simple": 0.15, "Medium": 0.20, "Complex": 0.25}
    contingency = base_cost * contingency_rates.get(complexity, 0.20)

    # Add infrastructure costs (10-20% based on project type)
    infra_multipliers = {
        "Web Application": 0.10,
        "API Service": 0.08,
        "Mobile Application": 0.12,
        "Microservices": 0.18,
        "Data Pipeline": 0.15,
        "Machine Learning": 0.20
    }
    infrastructure = base_cost * infra_multipliers.get(project_type, 0.12)

    total_cost = base_cost + contingency + infrastructure

    return round(total_cost, -2)  # Round to nearest hundred


def get_budget_range_from_estimate(estimated_budget: float) -> int:
    """Get budget range index from estimated budget."""
    if estimated_budget < 50000:
        return 0  # Under $50K
    elif estimated_budget < 100000:
        return 1  # $50K - $100K
    elif estimated_budget < 250000:
        return 2  # $100K - $250K
    elif estimated_budget < 500000:
        return 3  # $250K - $500K
    elif estimated_budget < 1000000:
        return 4  # $500K - $1M
    else:
        return 5  # Over $1M
