"""Budget Planner Form Components.

This module provides form components for planning and managing project budgets,
including cost estimation, ROI calculation, and financial analysis.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("⚠️ Plotly not available. Some budget visualizations will be limited.")


def render_budget_planner_form(
    budget_key: str = "budget_config",
    title: str = "💰 Budget Planner",
    project_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Render budget planner form for project financial planning.

    Args:
        budget_key: Key for storing budget configuration in session state
        title: Form title
        project_config: Project configuration for context

    Returns:
        Dictionary containing budget configuration
    """
    st.markdown(f"### {title}")
    st.markdown("Plan and manage your project budget with intelligent cost estimation and ROI analysis.")

    # Initialize budget configuration
    if budget_key not in st.session_state:
        st.session_state[budget_key] = get_default_budget_config()

    budget_config = st.session_state[budget_key]

    # Get project context if provided
    project_complexity = "Medium"
    project_duration = 12
    team_size = 5

    if project_config:
        project_complexity = project_config.get('complexity_level', 'Medium')
        project_duration = project_config.get('duration_weeks', 12)
        team_members = project_config.get('team_members', [])
        team_size = len(team_members) if team_members else 5

    # Budget overview
    st.markdown("#### 📊 Budget Overview")

    # Cost estimation
    estimated_costs = estimate_project_costs(
        complexity=project_complexity,
        duration_weeks=project_duration,
        team_size=team_size,
        custom_factors=budget_config.get('custom_factors', {})
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_budget = estimated_costs['total']
        st.metric("Total Budget", f"${total_budget:,.0f}")

    with col2:
        monthly_cost = estimated_costs['monthly_total']
        st.metric("Monthly Cost", f"${monthly_cost:,.0f}")

    with col3:
        contingency = estimated_costs['contingency']
        st.metric("Contingency", f"${contingency:,.0f}")

    with col4:
        risk_factor = estimated_costs['risk_factor']
        st.metric("Risk Factor", f"{risk_factor:.1f}x")

    # Cost breakdown
    st.markdown("#### 📈 Cost Breakdown")

    cost_categories = {
        'Team': estimated_costs['team_cost'],
        'Infrastructure': estimated_costs['infrastructure_cost'],
        'Tools & Software': estimated_costs['tools_cost'],
        'Training': estimated_costs['training_cost'],
        'Contingency': estimated_costs['contingency'],
        'Miscellaneous': estimated_costs['misc_cost']
    }

    # Create pie chart for cost breakdown
    cost_df = pd.DataFrame({
        'Category': list(cost_categories.keys()),
        'Amount': list(cost_categories.values())
    })

    # Filter out zero values
    cost_df = cost_df[cost_df['Amount'] > 0]

    if not cost_df.empty:
        if PLOTLY_AVAILABLE:
            fig = px.pie(
                cost_df,
                values='Amount',
                names='Category',
                title="Budget Allocation"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(cost_df.set_index('Category'))

    # Detailed cost configuration
    st.markdown("#### ⚙️ Cost Configuration")

    with st.expander("Adjust Cost Factors", expanded=False):
        render_cost_adjustment_form(budget_key, estimated_costs)

    # ROI Calculator
    st.markdown("#### 📈 ROI Calculator")

    col_roi1, col_roi2 = st.columns(2)

    with col_roi1:
        expected_revenue = st.number_input(
            "Expected Annual Revenue ($)",
            min_value=0,
            value=budget_config.get('expected_revenue', 500000),
            step=10000,
            key=f"{budget_key}_revenue",
            help="Projected revenue from the project"
        )

        operational_savings = st.number_input(
            "Annual Operational Savings ($)",
            min_value=0,
            value=budget_config.get('operational_savings', 100000),
            step=5000,
            key=f"{budget_key}_savings",
            help="Cost savings from operational improvements"
        )

    with col_roi2:
        project_lifespan = st.slider(
            "Project Lifespan (years)",
            min_value=1,
            max_value=10,
            value=budget_config.get('project_lifespan', 3),
            key=f"{budget_key}_lifespan"
        )

        discount_rate = st.slider(
            "Discount Rate (%)",
            min_value=0.0,
            max_value=20.0,
            value=budget_config.get('discount_rate', 8.0),
            step=0.5,
            key=f"{budget_key}_discount"
        )

    # Calculate ROI
    total_benefits = expected_revenue + operational_savings
    total_costs = total_budget

    # Simple ROI calculation
    if total_costs > 0:
        roi_percentage = ((total_benefits - total_costs) / total_costs) * 100
        npv = calculate_npv(total_benefits, total_costs, project_lifespan, discount_rate)

        col_roi3, col_roi4 = st.columns(2)

        with col_roi3:
            if roi_percentage > 0:
                st.metric("ROI", ".1f", roi_percentage, delta=f"{roi_percentage:.1f}%")
            else:
                st.metric("ROI", ".1f", roi_percentage, delta=f"{roi_percentage:.1f}%")

        with col_roi4:
            if npv > 0:
                st.metric("NPV", f"${npv:,.0f}", delta="Positive")
            else:
                st.metric("NPV", f"${npv:,.0f}", delta="Negative")

    # Budget vs Benefits comparison
    st.markdown("#### 📊 Budget vs Benefits")

    comparison_data = {
        'Category': ['Total Costs', 'Annual Revenue', 'Operational Savings', 'Net Benefit'],
        'Amount': [total_costs, expected_revenue, operational_savings, total_benefits - total_costs]
    }

    comparison_df = pd.DataFrame(comparison_data)

    # Create bar chart
    if PLOTLY_AVAILABLE:
        fig = px.bar(
            comparison_df,
            x='Category',
            y='Amount',
            title="Financial Analysis",
            color='Category',
            color_discrete_sequence=['red', 'green', 'blue', 'purple']
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.bar_chart(comparison_df.set_index('Category')['Amount'])

    # Budget recommendations
    st.markdown("#### 💡 Budget Recommendations")

    recommendations = generate_budget_recommendations(
        estimated_costs, roi_percentage if 'roi_percentage' in locals() else 0,
        project_complexity, project_duration
    )

    for rec in recommendations:
        if rec['type'] == 'warning':
            st.warning(f"⚠️ {rec['message']}")
        elif rec['type'] == 'success':
            st.success(f"✅ {rec['message']}")
        elif rec['type'] == 'info':
            st.info(f"💡 {rec['message']}")

    # Save budget configuration
    budget_config.update({
        'estimated_costs': estimated_costs,
        'total_budget': total_budget,
        'expected_revenue': expected_revenue,
        'operational_savings': operational_savings,
        'project_lifespan': project_lifespan,
        'discount_rate': discount_rate,
        'roi_percentage': roi_percentage if 'roi_percentage' in locals() else 0,
        'npv': npv if 'npv' in locals() else 0,
        'total_benefits': total_benefits,
        'total_costs': total_costs
    })

    if st.button("💾 Save Budget Plan", key=f"{budget_key}_save", type="primary"):
        st.session_state[budget_key] = budget_config
        st.success("✅ Budget plan saved successfully!")

    return budget_config


def render_cost_adjustment_form(budget_key: str, estimated_costs: Dict[str, Any]):
    """Render form for adjusting cost factors."""
    budget_config = st.session_state[budget_key]

    if 'custom_factors' not in budget_config:
        budget_config['custom_factors'] = {}

    custom_factors = budget_config['custom_factors']

    st.markdown("**Adjust cost multipliers to match your project needs:**")

    col1, col2 = st.columns(2)

    with col1:
        team_multiplier = st.slider(
            "Team Cost Multiplier",
            min_value=0.5,
            max_value=2.0,
            value=custom_factors.get('team_multiplier', 1.0),
            step=0.1,
            key=f"{budget_key}_team_mult",
            help="Adjust team costs (1.0 = estimated, higher = more expensive)"
        )
        custom_factors['team_multiplier'] = team_multiplier

        infra_multiplier = st.slider(
            "Infrastructure Multiplier",
            min_value=0.5,
            max_value=2.0,
            value=custom_factors.get('infra_multiplier', 1.0),
            step=0.1,
            key=f"{budget_key}_infra_mult",
            help="Adjust infrastructure costs"
        )
        custom_factors['infra_multiplier'] = infra_multiplier

        tools_multiplier = st.slider(
            "Tools & Software Multiplier",
            min_value=0.5,
            max_value=2.0,
            value=custom_factors.get('tools_multiplier', 1.0),
            step=0.1,
            key=f"{budget_key}_tools_mult",
            help="Adjust tools and software costs"
        )
        custom_factors['tools_multiplier'] = tools_multiplier

    with col2:
        training_multiplier = st.slider(
            "Training Multiplier",
            min_value=0.0,
            max_value=2.0,
            value=custom_factors.get('training_multiplier', 1.0),
            step=0.1,
            key=f"{budget_key}_training_mult",
            help="Adjust training and onboarding costs"
        )
        custom_factors['training_multiplier'] = training_multiplier

        contingency_multiplier = st.slider(
            "Contingency Multiplier",
            min_value=0.5,
            max_value=2.0,
            value=custom_factors.get('contingency_multiplier', 1.0),
            step=0.1,
            key=f"{budget_key}_contingency_mult",
            help="Adjust contingency buffer"
        )
        custom_factors['contingency_multiplier'] = contingency_multiplier

        location_factor = st.selectbox(
            "Location Cost Factor",
            options=["Low Cost", "Medium Cost", "High Cost"],
            index=["Low Cost", "Medium Cost", "High Cost"].index(custom_factors.get('location_factor', 'Medium Cost')),
            key=f"{budget_key}_location"
        )
        custom_factors['location_factor'] = location_factor

    # Apply custom factors
    if st.button("🔄 Apply Adjustments", key=f"{budget_key}_apply_factors"):
        budget_config['custom_factors'] = custom_factors
        st.success("✅ Cost adjustments applied!")
        st.rerun()


def estimate_project_costs(
    complexity: str = "Medium",
    duration_weeks: int = 12,
    team_size: int = 5,
    custom_factors: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Estimate project costs based on parameters."""

    # Base rates per complexity level
    base_rates = {
        "Simple": 8000,   # $8K/week
        "Medium": 12000,  # $12K/week
        "Complex": 20000   # $20K/week
    }

    base_weekly_rate = base_rates.get(complexity, 12000)

    # Calculate team costs
    team_cost = base_weekly_rate * duration_weeks

    # Infrastructure costs (10-20% of team costs)
    infra_multiplier = 0.15
    infrastructure_cost = team_cost * infra_multiplier

    # Tools and software costs (5-10% of team costs)
    tools_multiplier = 0.075
    tools_cost = team_cost * tools_multiplier

    # Training costs (2-5% of team costs)
    training_multiplier = 0.035
    training_cost = team_cost * training_multiplier

    # Miscellaneous costs (5-10% of team costs)
    misc_multiplier = 0.075
    misc_cost = team_cost * misc_multiplier

    # Apply custom factors if provided
    if custom_factors:
        team_cost *= custom_factors.get('team_multiplier', 1.0)
        infrastructure_cost *= custom_factors.get('infra_multiplier', 1.0)
        tools_cost *= custom_factors.get('tools_multiplier', 1.0)
        training_cost *= custom_factors.get('training_multiplier', 1.0)

        # Location factor
        location_factors = {
            "Low Cost": 0.8,
            "Medium Cost": 1.0,
            "High Cost": 1.3
        }
        location_multiplier = location_factors.get(custom_factors.get('location_factor', 'Medium Cost'), 1.0)
        team_cost *= location_multiplier
        infrastructure_cost *= location_multiplier

    # Calculate contingency (15-25% based on complexity)
    contingency_rates = {
        "Simple": 0.15,
        "Medium": 0.20,
        "Complex": 0.25
    }
    contingency_rate = contingency_rates.get(complexity, 0.20)
    contingency = (team_cost + infrastructure_cost + tools_cost + training_cost + misc_cost) * contingency_rate

    # Apply contingency multiplier if provided
    if custom_factors:
        contingency *= custom_factors.get('contingency_multiplier', 1.0)

    # Calculate totals
    subtotal = team_cost + infrastructure_cost + tools_cost + training_cost + misc_cost
    total = subtotal + contingency

    # Calculate risk factor based on complexity and duration
    risk_factors = {
        "Simple": 1.0,
        "Medium": 1.2,
        "Complex": 1.5
    }
    complexity_factor = risk_factors.get(complexity, 1.2)
    duration_factor = min(duration_weeks / 12, 2.0)  # Duration risk factor
    risk_factor = complexity_factor * duration_factor

    # Monthly totals
    monthly_total = total / max(duration_weeks / 4, 1)  # Assume 4 weeks per month

    return {
        'team_cost': round(team_cost, 2),
        'infrastructure_cost': round(infrastructure_cost, 2),
        'tools_cost': round(tools_cost, 2),
        'training_cost': round(training_cost, 2),
        'misc_cost': round(misc_cost, 2),
        'contingency': round(contingency, 2),
        'subtotal': round(subtotal, 2),
        'total': round(total, 2),
        'monthly_total': round(monthly_total, 2),
        'risk_factor': round(risk_factor, 2),
        'complexity': complexity,
        'duration_weeks': duration_weeks,
        'team_size': team_size
    }


def calculate_npv(benefits: float, costs: float, lifespan: int, discount_rate: float) -> float:
    """Calculate Net Present Value."""
    npv = -costs  # Initial investment

    discount_rate_decimal = discount_rate / 100

    for year in range(1, lifespan + 1):
        discounted_benefit = benefits / ((1 + discount_rate_decimal) ** year)
        npv += discounted_benefit

    return round(npv, 2)


def generate_budget_recommendations(
    estimated_costs: Dict[str, Any],
    roi_percentage: float,
    complexity: str,
    duration: int
) -> List[Dict[str, Any]]:
    """Generate budget recommendations based on analysis."""

    recommendations = []

    # ROI recommendations
    if roi_percentage < 0:
        recommendations.append({
            "type": "warning",
            "message": "Negative ROI detected - consider reducing scope or extending timeline"
        })
    elif roi_percentage < 25:
        recommendations.append({
            "type": "info",
            "message": "Low ROI - focus on high-value features and cost optimization"
        })
    else:
        recommendations.append({
            "type": "success",
            "message": "Strong ROI projection - project appears financially viable"
        })

    # Complexity recommendations
    if complexity == "Complex" and duration < 16:
        recommendations.append({
            "type": "warning",
            "message": "Complex project with short timeline - consider extending duration or reducing scope"
        })

    # Contingency recommendations
    contingency_percentage = (estimated_costs['contingency'] / estimated_costs['subtotal']) * 100
    if contingency_percentage < 15:
        recommendations.append({
            "type": "info",
            "message": "Low contingency buffer - consider increasing for risk mitigation"
        })
    elif contingency_percentage > 30:
        recommendations.append({
            "type": "info",
            "message": "High contingency buffer - ensure it's justified by project risks"
        })

    # Cost distribution recommendations
    team_percentage = (estimated_costs['team_cost'] / estimated_costs['total']) * 100
    if team_percentage > 70:
        recommendations.append({
            "type": "info",
            "message": "High team cost percentage - consider optimizing team composition"
        })

    return recommendations


def get_default_budget_config() -> Dict[str, Any]:
    """Get default budget configuration."""
    return {
        'expected_revenue': 500000,
        'operational_savings': 100000,
        'project_lifespan': 3,
        'discount_rate': 8.0,
        'custom_factors': {
            'team_multiplier': 1.0,
            'infra_multiplier': 1.0,
            'tools_multiplier': 1.0,
            'training_multiplier': 1.0,
            'contingency_multiplier': 1.0,
            'location_factor': 'Medium Cost'
        }
    }
