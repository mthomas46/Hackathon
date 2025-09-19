"""Risk Assessment Form Components.

This module provides form components for assessing project risks,
calculating success probability, and generating mitigation strategies.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np


def render_risk_assessment_form(
    risk_key: str = "risk_config",
    title: str = "⚠️ Risk Assessment",
    project_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Render risk assessment form for project risk evaluation.

    Args:
        risk_key: Key for storing risk configuration in session state
        title: Form title
        project_config: Project configuration for context

    Returns:
        Dictionary containing risk assessment results
    """
    st.markdown(f"### {title}")
    st.markdown("Assess project risks and calculate success probability with mitigation strategies.")

    # Initialize risk configuration
    if risk_key not in st.session_state:
        st.session_state[risk_key] = get_default_risk_config()

    risk_config = st.session_state[risk_key]

    # Risk assessment questionnaire
    st.markdown("#### 📋 Risk Assessment Questionnaire")

    risk_factors = {
        'team_experience': {
            'question': 'How familiar is your team with the required technology stack?',
            'options': ['Very Experienced', 'Somewhat Experienced', 'Limited Experience', 'New Technology'],
            'weights': {'Very Experienced': 0, 'Somewhat Experienced': 1, 'Limited Experience': 2, 'New Technology': 3}
        },
        'requirement_stability': {
            'question': 'How stable are your project requirements?',
            'options': ['Very Stable', 'Mostly Stable', 'Some Changes Expected', 'High Uncertainty'],
            'weights': {'Very Stable': 0, 'Mostly Stable': 1, 'Some Changes Expected': 2, 'High Uncertainty': 3}
        },
        'timeline_realism': {
            'question': 'How realistic is your project timeline?',
            'options': ['Very Realistic', 'Reasonable', 'Aggressive', 'Unrealistic'],
            'weights': {'Very Realistic': 0, 'Reasonable': 1, 'Aggressive': 2, 'Unrealistic': 3}
        },
        'budget_contingency': {
            'question': 'Do you have adequate budget contingency?',
            'options': ['Strong Contingency (>25%)', 'Adequate Contingency (15-25%)', 'Minimal Contingency (5-15%)', 'No Contingency'],
            'weights': {'Strong Contingency (>25%)': 0, 'Adequate Contingency (15-25%)': 1, 'Minimal Contingency (5-15%)': 2, 'No Contingency': 3}
        },
        'stakeholder_alignment': {
            'question': 'How aligned are stakeholders on project goals?',
            'options': ['Fully Aligned', 'Mostly Aligned', 'Some Misalignment', 'Significant Misalignment'],
            'weights': {'Fully Aligned': 0, 'Mostly Aligned': 1, 'Some Misalignment': 2, 'Significant Misalignment': 3}
        },
        'technical_complexity': {
            'question': 'What is the technical complexity level?',
            'options': ['Straightforward', 'Moderate', 'Complex', 'Highly Complex'],
            'weights': {'Straightforward': 0, 'Moderate': 1, 'Complex': 2, 'Highly Complex': 3}
        },
        'team_size_adequacy': {
            'question': 'Is your team size adequate for the project scope?',
            'options': ['Well-sized', 'Slightly Small', 'Too Small', 'Critically Understaffed'],
            'weights': {'Well-sized': 0, 'Slightly Small': 1, 'Too Small': 2, 'Critically Understaffed': 3}
        },
        'vendor_dependencies': {
            'question': 'How dependent is the project on external vendors?',
            'options': ['No Dependencies', 'Minor Dependencies', 'Significant Dependencies', 'Critical Dependencies'],
            'weights': {'No Dependencies': 0, 'Minor Dependencies': 1, 'Significant Dependencies': 2, 'Critical Dependencies': 3}
        }
    }

    # Get project context for default values
    project_complexity = "Medium"
    if project_config:
        project_complexity = project_config.get('complexity_level', 'Medium')

    # Render risk factor questions
    risk_scores = {}
    for factor_key, factor_config in risk_factors.items():
        # Set default based on project complexity
        default_index = get_risk_default_index(factor_key, project_complexity)

        selected_option = st.selectbox(
            factor_config['question'],
            options=factor_config['options'],
            index=default_index,
            key=f"{risk_key}_{factor_key}"
        )

        risk_scores[factor_key] = {
            'option': selected_option,
            'score': factor_config['weights'][selected_option]
        }

    # Calculate risk assessment
    total_score = sum(score['score'] for score in risk_scores.values())
    max_score = sum(max(factor['weights'].values()) for factor in risk_factors.values())
    risk_percentage = (total_score / max_score) * 100

    # Determine risk level and success probability
    if risk_percentage <= 20:
        risk_level = "Low Risk"
        success_probability = 85
        risk_color = "🟢"
    elif risk_percentage <= 40:
        risk_level = "Medium-Low Risk"
        success_probability = 70
        risk_color = "🟡"
    elif risk_percentage <= 60:
        risk_level = "Medium Risk"
        success_probability = 55
        risk_color = "🟡"
    elif risk_percentage <= 80:
        risk_level = "Medium-High Risk"
        success_probability = 35
        risk_color = "🟠"
    else:
        risk_level = "High Risk"
        success_probability = 20
        risk_color = "🔴"

    # Display risk assessment results
    st.markdown("#### 📊 Risk Assessment Results")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Risk Score", ".1f", risk_percentage)

    with col2:
        st.metric("Risk Level", f"{risk_color} {risk_level}")

    with col3:
        st.metric("Success Probability", ".1f", success_probability)

    with col4:
        confidence_level = calculate_confidence_level(risk_scores)
        st.metric("Confidence", ".1f", confidence_level)

    # Risk visualization
    st.markdown("#### 📈 Risk Breakdown")

    # Create risk factor visualization
    risk_factors_df = pd.DataFrame([
        {'Factor': factor_key.replace('_', ' ').title(), 'Score': score['score'], 'Max_Score': 3}
        for factor_key, score in risk_scores.items()
    ])

    try:
        import plotly.express as px

        fig = px.bar(
            risk_factors_df,
            x='Factor',
            y='Score',
            title="Risk Factors Breakdown",
            labels={'Score': 'Risk Score', 'Factor': 'Risk Factor'},
            color='Score',
            color_continuous_scale='Reds'
        )
        fig.add_hline(y=1.5, line_dash="dash", line_color="orange", annotation_text="Medium Risk Threshold")
        st.plotly_chart(fig, use_container_width=True)

    except ImportError:
        st.bar_chart(risk_factors_df.set_index('Factor')['Score'])

    # Mitigation strategies
    st.markdown("#### 🛡️ Recommended Mitigation Strategies")

    mitigation_strategies = generate_mitigation_strategies(risk_scores, risk_percentage)

    for strategy in mitigation_strategies:
        priority_icon = "🔴" if strategy['priority'] == 'High' else "🟡" if strategy['priority'] == 'Medium' else "🟢"
        with st.expander(f"{priority_icon} {strategy['title']} ({strategy['priority']} Priority)", expanded=False):
            st.write(f"**Description:** {strategy['description']}")
            st.write(f"**Implementation:** {strategy['implementation']}")
            st.write(f"**Expected Impact:** {strategy['impact']}")
            st.write(f"**Timeline:** {strategy['timeline']}")

    # Risk monitoring plan
    st.markdown("#### 📊 Risk Monitoring Plan")

    with st.expander("View Monitoring Recommendations", expanded=False):
        monitoring_plan = generate_monitoring_plan(risk_scores, risk_level)

        for item in monitoring_plan:
            st.markdown(f"**{item['frequency']}**: {item['activity']}")
            st.write(f"   {item['rationale']}")

    # Save risk assessment
    risk_config.update({
        'risk_scores': risk_scores,
        'total_score': total_score,
        'max_score': max_score,
        'risk_percentage': risk_percentage,
        'risk_level': risk_level,
        'success_probability': success_probability,
        'confidence_level': confidence_level,
        'mitigation_strategies': mitigation_strategies,
        'monitoring_plan': monitoring_plan,
        'assessment_date': str(pd.Timestamp.now())
    })

    if st.button("💾 Save Risk Assessment", key=f"{risk_key}_save", type="primary"):
        st.session_state[risk_key] = risk_config
        st.success("✅ Risk assessment saved successfully!")

        # Display success probability prominently
        if success_probability >= 70:
            st.success(f"🎉 High success probability ({success_probability:.1f}%) - project appears well-positioned!")
        elif success_probability >= 50:
            st.warning(f"⚠️ Moderate success probability ({success_probability:.1f}%) - consider mitigation strategies above.")
        else:
            st.error(f"🚨 Low success probability ({success_probability:.1f}%) - significant risk mitigation required.")

    return risk_config


def get_risk_default_index(factor_key: str, complexity: str) -> int:
    """Get default index for risk factor based on project complexity."""
    complexity_defaults = {
        "Simple": {
            'team_experience': 0,      # Very Experienced
            'requirement_stability': 0, # Very Stable
            'timeline_realism': 0,     # Very Realistic
            'budget_contingency': 0,   # Strong Contingency
            'stakeholder_alignment': 0, # Fully Aligned
            'technical_complexity': 0,  # Straightforward
            'team_size_adequacy': 0,    # Well-sized
            'vendor_dependencies': 0    # No Dependencies
        },
        "Medium": {
            'team_experience': 1,      # Somewhat Experienced
            'requirement_stability': 1, # Mostly Stable
            'timeline_realism': 1,     # Reasonable
            'budget_contingency': 1,   # Adequate Contingency
            'stakeholder_alignment': 1, # Mostly Aligned
            'technical_complexity': 1,  # Moderate
            'team_size_adequacy': 1,    # Slightly Small
            'vendor_dependencies': 1    # Minor Dependencies
        },
        "Complex": {
            'team_experience': 2,      # Limited Experience
            'requirement_stability': 2, # Some Changes Expected
            'timeline_realism': 2,     # Aggressive
            'budget_contingency': 2,   # Minimal Contingency
            'stakeholder_alignment': 2, # Some Misalignment
            'technical_complexity': 2,  # Complex
            'team_size_adequacy': 2,    # Too Small
            'vendor_dependencies': 2    # Significant Dependencies
        }
    }

    defaults = complexity_defaults.get(complexity, complexity_defaults["Medium"])
    return defaults.get(factor_key, 1)


def calculate_confidence_level(risk_scores: Dict[str, Any]) -> float:
    """Calculate confidence level in the risk assessment."""
    # Count how many factors are at extreme values (0 or 3)
    extreme_count = sum(1 for score in risk_scores.values() if score['score'] in [0, 3])

    # Higher extreme values indicate higher confidence in assessment
    confidence = 50 + (extreme_count / len(risk_scores)) * 30

    return min(confidence, 95)  # Cap at 95%


def generate_mitigation_strategies(risk_scores: Dict[str, Any], risk_percentage: float) -> List[Dict[str, Any]]:
    """Generate mitigation strategies based on risk assessment."""

    strategies = []

    # High-risk team experience
    if risk_scores['team_experience']['score'] >= 2:
        strategies.append({
            'title': 'Team Training & Skill Development',
            'description': 'Address team experience gaps through targeted training and mentoring.',
            'implementation': 'Conduct skills assessment, provide training programs, bring in experienced consultants.',
            'impact': 'Reduce technical risk by 20-30%, improve team confidence and delivery quality.',
            'timeline': '3-6 months',
            'priority': 'High'
        })

    # Unstable requirements
    if risk_scores['requirement_stability']['score'] >= 2:
        strategies.append({
            'title': 'Requirements Stabilization',
            'description': 'Implement agile practices and change management processes.',
            'implementation': 'Adopt agile methodology, create change control board, implement regular requirement reviews.',
            'impact': 'Improve requirement stability by 25-40%, reduce scope creep.',
            'timeline': '1-3 months',
            'priority': 'High'
        })

    # Unrealistic timeline
    if risk_scores['timeline_realism']['score'] >= 2:
        strategies.append({
            'title': 'Timeline Adjustment & Phasing',
            'description': 'Break project into manageable phases with realistic deadlines.',
            'implementation': 'Create detailed project plan, identify critical path, implement milestone reviews.',
            'impact': 'Improve timeline adherence by 30-50%, reduce delivery pressure.',
            'timeline': '1-2 months',
            'priority': 'High'
        })

    # Inadequate budget contingency
    if risk_scores['budget_contingency']['score'] >= 2:
        strategies.append({
            'title': 'Budget Risk Mitigation',
            'description': 'Increase contingency budget and implement cost monitoring.',
            'implementation': 'Add contingency buffer, implement regular budget reviews, create cost control mechanisms.',
            'impact': 'Reduce budget overrun risk by 25-35%, improve financial predictability.',
            'timeline': 'Immediate',
            'priority': 'Medium'
        })

    # Stakeholder misalignment
    if risk_scores['stakeholder_alignment']['score'] >= 2:
        strategies.append({
            'title': 'Stakeholder Alignment',
            'description': 'Improve communication and alignment with stakeholders.',
            'implementation': 'Schedule regular stakeholder meetings, create communication plan, establish clear decision-making processes.',
            'impact': 'Improve stakeholder satisfaction by 30-50%, reduce misalignment risks.',
            'timeline': 'Ongoing',
            'priority': 'Medium'
        })

    # High technical complexity
    if risk_scores['technical_complexity']['score'] >= 2:
        strategies.append({
            'title': 'Technical Complexity Management',
            'description': 'Break down complex technical challenges into manageable components.',
            'implementation': 'Create technical spikes, implement proof-of-concepts, bring in technical experts.',
            'impact': 'Reduce technical risk by 20-40%, improve solution quality.',
            'timeline': '2-4 months',
            'priority': 'High'
        })

    # Inadequate team size
    if risk_scores['team_size_adequacy']['score'] >= 2:
        strategies.append({
            'title': 'Team Augmentation',
            'description': 'Address team size gaps through hiring or contractor support.',
            'implementation': 'Conduct resource planning, initiate hiring process, engage contractors for peak periods.',
            'impact': 'Reduce delivery timeline by 15-25%, improve quality and reduce burnout.',
            'timeline': '1-3 months',
            'priority': 'High'
        })

    # High vendor dependencies
    if risk_scores['vendor_dependencies']['score'] >= 2:
        strategies.append({
            'title': 'Vendor Risk Management',
            'description': 'Mitigate risks associated with external vendor dependencies.',
            'implementation': 'Create vendor assessment process, establish SLAs, develop contingency plans.',
            'impact': 'Reduce vendor-related delays by 30-50%, improve delivery predictability.',
            'timeline': '1-2 months',
            'priority': 'Medium'
        })

    # Sort by priority (High -> Medium -> Low)
    priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
    strategies.sort(key=lambda x: priority_order[x['priority']])

    return strategies[:6]  # Return top 6 strategies


def generate_monitoring_plan(risk_scores: Dict[str, Any], risk_level: str) -> List[Dict[str, Any]]:
    """Generate risk monitoring plan based on assessment."""

    base_plan = [
        {
            'frequency': 'Daily',
            'activity': 'Team velocity and progress tracking',
            'rationale': 'Monitor delivery progress and identify early warning signs'
        },
        {
            'frequency': 'Weekly',
            'activity': 'Risk register review and status updates',
            'rationale': 'Regular assessment of identified risks and mitigation progress'
        },
        {
            'frequency': 'Bi-weekly',
            'activity': 'Stakeholder communication and alignment check',
            'rationale': 'Ensure ongoing stakeholder engagement and requirement stability'
        }
    ]

    # Add risk-specific monitoring based on high-risk factors
    if risk_scores['team_experience']['score'] >= 2:
        base_plan.append({
            'frequency': 'Weekly',
            'activity': 'Technical skill assessment and training progress',
            'rationale': 'Monitor team capability development and technical readiness'
        })

    if risk_scores['budget_contingency']['score'] >= 2:
        base_plan.append({
            'frequency': 'Weekly',
            'activity': 'Budget tracking and burn rate analysis',
            'rationale': 'Monitor spending against budget and identify cost variances early'
        })

    if risk_scores['timeline_realism']['score'] >= 2:
        base_plan.append({
            'frequency': 'Weekly',
            'activity': 'Milestone review and timeline adjustment',
            'rationale': 'Regular assessment of timeline adherence and milestone achievement'
        })

    if risk_scores['vendor_dependencies']['score'] >= 2:
        base_plan.append({
            'frequency': 'Weekly',
            'activity': 'Vendor performance monitoring and SLA compliance',
            'rationale': 'Track external dependency performance and delivery commitments'
        })

    # Add escalation monitoring for high-risk projects
    if risk_level in ['High Risk', 'Medium-High Risk']:
        base_plan.append({
            'frequency': 'Daily',
            'activity': 'Executive risk dashboard review',
            'rationale': 'Ensure executive visibility into high-risk project status'
        })

    return base_plan


def get_default_risk_config() -> Dict[str, Any]:
    """Get default risk configuration."""
    return {
        'assessment_completed': False,
        'last_assessment': None,
        'risk_scores': {},
        'mitigation_strategies': [],
        'monitoring_plan': [],
        'follow_up_required': False
    }
