"""Team Builder Form Components.

This module provides form components for building and configuring project teams,
including role assignment, skill selection, and team optimization.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import pandas as pd


def render_team_builder_form(
    team_key: str = "team_config",
    title: str = "👥 Team Builder",
    max_team_size: int = 15
) -> Dict[str, Any]:
    """Render team builder form for configuring project teams.

    Args:
        team_key: Key for storing team configuration in session state
        title: Form title
        max_team_size: Maximum team size allowed

    Returns:
        Dictionary containing team configuration
    """
    st.markdown(f"### {title}")
    st.markdown("Configure your project team with roles, skills, and expertise levels.")

    # Initialize team configuration
    if team_key not in st.session_state:
        st.session_state[team_key] = {
            'team_members': [],
            'team_size': 0,
            'total_cost': 0,
            'average_expertise': 0,
            'role_distribution': {},
            'skill_coverage': {}
        }

    team_config = st.session_state[team_key]

    # Team overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Team Size", len(team_config['team_members']))

    with col2:
        st.metric("Monthly Cost", f"${team_config.get('total_cost', 0):,.0f}")

    with col3:
        st.metric("Avg Expertise", ".1f", team_config.get('average_expertise', 0))

    with col4:
        st.metric("Role Diversity", len(team_config.get('role_distribution', {})))

    # Add team member
    st.markdown("#### ➕ Add Team Member")

    with st.expander("Add New Team Member", expanded=False):
        render_add_team_member_form(team_key, max_team_size)

    # Display current team
    if team_config['team_members']:
        st.markdown("#### 👥 Current Team")

        # Team member management
        for i, member in enumerate(team_config['team_members']):
            render_team_member_card(i, member, team_key)

        # Team analysis
        st.markdown("#### 📊 Team Analysis")
        render_team_analysis(team_config)

    else:
        st.info("👋 No team members added yet. Click 'Add New Team Member' to get started!")

    # Quick team templates
    st.markdown("#### 🏗️ Quick Team Templates")

    col_temp1, col_temp2, col_temp3 = st.columns(3)

    with col_temp1:
        if st.button("🚀 Startup Team", key="template_startup"):
            apply_team_template(team_key, "startup")

    with col_temp2:
        if st.button("🏢 Enterprise Team", key="template_enterprise"):
            apply_team_template(team_key, "enterprise")

    with col_temp3:
        if st.button("🔬 R&D Team", key="template_rnd"):
            apply_team_template(team_key, "rnd")

    return team_config


def render_add_team_member_form(team_key: str, max_team_size: int):
    """Render form for adding a new team member."""
    team_config = st.session_state[team_key]

    if len(team_config['team_members']) >= max_team_size:
        st.warning(f"Maximum team size ({max_team_size}) reached!")
        return

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input(
            "Full Name *",
            key=f"{team_key}_new_name",
            placeholder="e.g., John Doe"
        )

        role = st.selectbox(
            "Role *",
            options=[
                "Product Manager", "Technical Lead", "Senior Developer",
                "Developer", "QA Engineer", "DevOps Engineer",
                "UI/UX Designer", "Data Scientist", "Business Analyst",
                "Scrum Master", "Architect", "Security Engineer"
            ],
            key=f"{team_key}_new_role"
        )

        expertise_level = st.selectbox(
            "Expertise Level",
            options=["Junior", "Intermediate", "Senior", "Expert", "Lead"],
            index=1,  # Default to Intermediate
            key=f"{team_key}_new_expertise"
        )

    with col2:
        hourly_rate = st.number_input(
            "Hourly Rate ($)",
            min_value=25,
            max_value=200,
            value=65,
            step=5,
            key=f"{team_key}_new_rate"
        )

        availability = st.slider(
            "Availability (%)",
            min_value=50,
            max_value=100,
            value=100,
            key=f"{team_key}_new_availability"
        )

        # Skills selection
        st.markdown("**Key Skills**")
        available_skills = [
            "Python", "JavaScript", "Java", "C++", "Go", "Rust",
            "React", "Angular", "Vue.js", "Node.js", "Django", "Flask",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
            "SQL", "NoSQL", "Data Science", "Machine Learning",
            "UI/UX Design", "Testing", "DevOps", "Security"
        ]

        selected_skills = st.multiselect(
            "Select relevant skills",
            options=available_skills,
            key=f"{team_key}_new_skills",
            max_selections=8
        )

    # Add member button
    if st.button("➕ Add Team Member", key=f"{team_key}_add_member", type="primary"):
        if not name.strip():
            st.error("❌ Please enter a name for the team member.")
            return

        if not role:
            st.error("❌ Please select a role for the team member.")
            return

        # Create new team member
        new_member = {
            'id': f"member_{len(team_config['team_members']) + 1}",
            'name': name.strip(),
            'role': role,
            'expertise_level': expertise_level,
            'hourly_rate': hourly_rate,
            'availability': availability,
            'skills': selected_skills,
            'monthly_cost': calculate_monthly_cost(hourly_rate, availability),
            'productivity_multiplier': get_productivity_multiplier(expertise_level),
            'added_at': str(pd.Timestamp.now())
        }

        # Add to team
        team_config['team_members'].append(new_member)

        # Update team statistics
        update_team_statistics(team_config)

        st.success(f"✅ Added {name} as {role} to the team!")

        # Clear form
        st.rerun()


def render_team_member_card(index: int, member: Dict[str, Any], team_key: str):
    """Render a card for a team member."""
    with st.expander(f"👤 {member['name']} - {member['role']}", expanded=False):
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.write(f"**Expertise:** {member['expertise_level']}")
            st.write(f"**Hourly Rate:** ${member['hourly_rate']}")
            st.write(f"**Monthly Cost:** ${member['monthly_cost']:,.0f}")

        with col2:
            st.write(f"**Availability:** {member['availability']}%")
            st.write(f"**Productivity:** {member['productivity_multiplier']:.2f}x")

            if member['skills']:
                st.write("**Skills:**")
                skills_text = ", ".join(member['skills'][:5])  # Show first 5 skills
                if len(member['skills']) > 5:
                    skills_text += f" +{len(member['skills']) - 5} more"
                st.write(skills_text)

        with col3:
            # Edit and Remove buttons
            if st.button("✏️ Edit", key=f"{team_key}_edit_{index}"):
                st.session_state[f"{team_key}_editing"] = index
                st.rerun()

            if st.button("🗑️ Remove", key=f"{team_key}_remove_{index}", type="secondary"):
                if st.checkbox("Confirm removal", key=f"{team_key}_confirm_remove_{index}"):
                    team_config = st.session_state[team_key]
                    team_config['team_members'].pop(index)
                    update_team_statistics(team_config)
                    st.success("✅ Team member removed!")
                    st.rerun()

        # Edit form (shown when editing)
        if st.session_state.get(f"{team_key}_editing") == index:
            render_edit_team_member_form(index, member, team_key)


def render_edit_team_member_form(index: int, member: Dict[str, Any], team_key: str):
    """Render form for editing a team member."""
    st.markdown("---")
    st.markdown("**Edit Team Member**")

    col1, col2 = st.columns(2)

    with col1:
        new_name = st.text_input(
            "Name",
            value=member['name'],
            key=f"{team_key}_edit_name_{index}"
        )

        new_role = st.selectbox(
            "Role",
            options=[
                "Product Manager", "Technical Lead", "Senior Developer",
                "Developer", "QA Engineer", "DevOps Engineer",
                "UI/UX Designer", "Data Scientist", "Business Analyst",
                "Scrum Master", "Architect", "Security Engineer"
            ],
            index=[
                "Product Manager", "Technical Lead", "Senior Developer",
                "Developer", "QA Engineer", "DevOps Engineer",
                "UI/UX Designer", "Data Scientist", "Business Analyst",
                "Scrum Master", "Architect", "Security Engineer"
            ].index(member['role']),
            key=f"{team_key}_edit_role_{index}"
        )

    with col2:
        new_rate = st.number_input(
            "Hourly Rate ($)",
            min_value=25,
            max_value=200,
            value=member['hourly_rate'],
            step=5,
            key=f"{team_key}_edit_rate_{index}"
        )

        new_availability = st.slider(
            "Availability (%)",
            min_value=50,
            max_value=100,
            value=member['availability'],
            key=f"{team_key}_edit_availability_{index}"
        )

    # Save changes
    col_save, col_cancel = st.columns(2)

    with col_save:
        if st.button("💾 Save Changes", key=f"{team_key}_save_edit_{index}", type="primary"):
            team_config = st.session_state[team_key]

            # Update member
            team_config['team_members'][index].update({
                'name': new_name,
                'role': new_role,
                'hourly_rate': new_rate,
                'availability': new_availability,
                'monthly_cost': calculate_monthly_cost(new_rate, new_availability)
            })

            # Update team statistics
            update_team_statistics(team_config)

            # Clear editing state
            if f"{team_key}_editing" in st.session_state:
                del st.session_state[f"{team_key}_editing"]

            st.success("✅ Team member updated!")
            st.rerun()

    with col_cancel:
        if st.button("❌ Cancel", key=f"{team_key}_cancel_edit_{index}"):
            if f"{team_key}_editing" in st.session_state:
                del st.session_state[f"{team_key}_editing"]
            st.rerun()


def render_team_analysis(team_config: Dict[str, Any]):
    """Render team analysis and insights."""
    team_members = team_config['team_members']

    if not team_members:
        return

    # Role distribution
    roles = [member['role'] for member in team_members]
    role_counts = pd.Series(roles).value_counts()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Role Distribution**")
        if len(role_counts) > 0:
            # Create a simple bar chart for roles
            role_df = pd.DataFrame({
                'Role': role_counts.index,
                'Count': role_counts.values
            })
            st.bar_chart(role_df.set_index('Role'))

    with col2:
        st.markdown("**Expertise Distribution**")
        expertise_levels = [member['expertise_level'] for member in team_members]
        expertise_counts = pd.Series(expertise_levels).value_counts()

        if len(expertise_counts) > 0:
            expertise_df = pd.DataFrame({
                'Level': expertise_counts.index,
                'Count': expertise_counts.values
            })
            st.bar_chart(expertise_df.set_index('Level'))

    # Team insights
    st.markdown("**💡 Team Insights**")

    insights = []

    # Check for role balance
    technical_roles = ['Technical Lead', 'Senior Developer', 'Developer', 'DevOps Engineer', 'Data Scientist', 'Architect', 'Security Engineer']
    business_roles = ['Product Manager', 'Business Analyst', 'Scrum Master']

    technical_count = sum(1 for member in team_members if member['role'] in technical_roles)
    business_count = sum(1 for member in team_members if member['role'] in business_roles)

    if technical_count == 0:
        insights.append({"type": "warning", "message": "⚠️ No technical roles in the team"})
    elif business_count == 0:
        insights.append({"type": "warning", "message": "⚠️ No business roles in the team"})

    # Check for cost efficiency
    avg_hourly_rate = sum(member['hourly_rate'] for member in team_members) / len(team_members)
    if avg_hourly_rate > 100:
        insights.append({"type": "info", "message": "💰 High-cost team - consider optimizing for budget"})
    elif avg_hourly_rate < 50:
        insights.append({"type": "info", "message": "💰 Cost-effective team composition"})

    # Check for expertise balance
    expert_count = sum(1 for member in team_members if member['expertise_level'] in ['Expert', 'Lead'])
    if expert_count == 0:
        insights.append({"type": "warning", "message": "⚠️ No senior expertise in the team"})
    elif expert_count > len(team_members) / 2:
        insights.append({"type": "info", "message": "✅ Strong senior leadership presence"})

    # Display insights
    for insight in insights:
        if insight['type'] == 'warning':
            st.warning(insight['message'])
        elif insight['type'] == 'success':
            st.success(insight['message'])
        else:
            st.info(insight['message'])


def apply_team_template(team_key: str, template_name: str):
    """Apply a team template."""
    team_config = st.session_state[team_key]

    templates = {
        "startup": [
            {"name": "Sarah Chen", "role": "Product Manager", "expertise_level": "Senior", "hourly_rate": 75, "skills": ["Product Strategy", "Agile"]},
            {"name": "Marcus Rodriguez", "role": "Technical Lead", "expertise_level": "Expert", "hourly_rate": 85, "skills": ["Python", "Architecture"]},
            {"name": "Emily Johnson", "role": "Senior Developer", "expertise_level": "Senior", "hourly_rate": 65, "skills": ["Python", "React", "AWS"]},
            {"name": "David Kim", "role": "Developer", "expertise_level": "Intermediate", "hourly_rate": 55, "skills": ["JavaScript", "Node.js"]},
            {"name": "James Park", "role": "QA Engineer", "expertise_level": "Intermediate", "hourly_rate": 50, "skills": ["Testing", "Automation"]}
        ],
        "enterprise": [
            {"name": "Dr. Enterprise Lead", "role": "Architect", "expertise_level": "Expert", "hourly_rate": 120, "skills": ["Enterprise Architecture", "Strategy"]},
            {"name": "Senior Tech Lead", "role": "Technical Lead", "expertise_level": "Expert", "hourly_rate": 95, "skills": ["System Design", "Leadership"]},
            {"name": "Enterprise Developer 1", "role": "Senior Developer", "expertise_level": "Senior", "hourly_rate": 75, "skills": ["Java", "Spring", "Microservices"]},
            {"name": "Enterprise Developer 2", "role": "Senior Developer", "expertise_level": "Senior", "hourly_rate": 75, "skills": ["Python", ".NET", "Azure"]},
            {"name": "Enterprise Developer 3", "role": "Developer", "expertise_level": "Intermediate", "hourly_rate": 60, "skills": ["React", "SQL", "Docker"]},
            {"name": "Enterprise QA", "role": "QA Engineer", "expertise_level": "Senior", "hourly_rate": 65, "skills": ["Test Automation", "Performance Testing"]},
            {"name": "Enterprise DevOps", "role": "DevOps Engineer", "expertise_level": "Senior", "hourly_rate": 80, "skills": ["Kubernetes", "CI/CD", "Terraform"]}
        ],
        "rnd": [
            {"name": "Research Lead", "role": "Architect", "expertise_level": "Expert", "hourly_rate": 110, "skills": ["Research", "Innovation", "Strategy"]},
            {"name": "Data Scientist 1", "role": "Data Scientist", "expertise_level": "Expert", "hourly_rate": 90, "skills": ["Machine Learning", "Python", "Statistics"]},
            {"name": "Data Scientist 2", "role": "Data Scientist", "expertise_level": "Senior", "hourly_rate": 75, "skills": ["Deep Learning", "TensorFlow", "Research"]},
            {"name": "ML Engineer", "role": "Data Scientist", "expertise_level": "Senior", "hourly_rate": 80, "skills": ["MLOps", "Model Deployment", "Python"]},
            {"name": "Research Assistant", "role": "Developer", "expertise_level": "Intermediate", "hourly_rate": 55, "skills": ["Python", "Data Analysis", "Research"]}
        ]
    }

    if template_name in templates:
        template_members = templates[template_name]

        # Convert template to full member objects
        team_config['team_members'] = []
        for i, member_data in enumerate(template_members):
            member = {
                'id': f"template_{template_name}_{i+1}",
                'name': member_data['name'],
                'role': member_data['role'],
                'expertise_level': member_data['expertise_level'],
                'hourly_rate': member_data['hourly_rate'],
                'availability': 100,
                'skills': member_data['skills'],
                'monthly_cost': calculate_monthly_cost(member_data['hourly_rate'], 100),
                'productivity_multiplier': get_productivity_multiplier(member_data['expertise_level']),
                'added_at': str(pd.Timestamp.now())
            }
            team_config['team_members'].append(member)

        # Update team statistics
        update_team_statistics(team_config)

        st.success(f"✅ Applied {template_name.title()} team template with {len(template_members)} members!")


def calculate_monthly_cost(hourly_rate: float, availability: float) -> float:
    """Calculate monthly cost for a team member."""
    # Assume 40 hours/week * 4 weeks/month * availability percentage
    monthly_hours = 40 * 4 * (availability / 100)
    return round(hourly_rate * monthly_hours, 2)


def get_productivity_multiplier(expertise_level: str) -> float:
    """Get productivity multiplier based on expertise level."""
    multipliers = {
        "Junior": 0.7,
        "Intermediate": 1.0,
        "Senior": 1.2,
        "Expert": 1.4,
        "Lead": 1.6
    }
    return multipliers.get(expertise_level, 1.0)


def update_team_statistics(team_config: Dict[str, Any]):
    """Update team statistics after changes."""
    team_members = team_config['team_members']

    # Calculate totals
    total_cost = sum(member['monthly_cost'] for member in team_members)
    team_config['total_cost'] = total_cost

    # Calculate average expertise
    if team_members:
        total_expertise = sum(get_productivity_multiplier(member['expertise_level']) for member in team_members)
        team_config['average_expertise'] = round(total_expertise / len(team_members), 2)
    else:
        team_config['average_expertise'] = 0

    # Role distribution
    roles = [member['role'] for member in team_members]
    role_distribution = {}
    for role in set(roles):
        role_distribution[role] = roles.count(role)
    team_config['role_distribution'] = role_distribution

    # Skill coverage
    all_skills = []
    for member in team_members:
        all_skills.extend(member['skills'])
    skill_coverage = {}
    for skill in set(all_skills):
        skill_coverage[skill] = all_skills.count(skill)
    team_config['skill_coverage'] = skill_coverage
