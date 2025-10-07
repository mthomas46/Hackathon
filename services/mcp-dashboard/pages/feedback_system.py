"""
Feedback System UI Page.

Provides interface for:
- Submitting feedback
- Viewing feedback statistics
- Analyzing trends
- Improvement tracking
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import random

# Add services directory to path
services_path = Path(__file__).parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

from mcp_retrieval.src.feedback_system import (
    FeedbackSystem,
    FeedbackType,
    Rating,
)


# ============================================================================
# Page Configuration
# ============================================================================

def render():
    """Render the Feedback System page."""
    
    st.title("💬 Feedback System")
    st.markdown("""
    Provide feedback to help improve the MCP system continuously.
    """)
    
    # Initialize session state
    if 'feedback_system' not in st.session_state:
        st.session_state['feedback_system'] = FeedbackSystem()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Submit", "📊 Statistics", "📈 Trends", "💡 Suggestions"])
    
    with tab1:
        render_submit_feedback()
    
    with tab2:
        render_statistics()
    
    with tab3:
        render_trends()
    
    with tab4:
        render_suggestions()


# ============================================================================
# Submit Feedback Section
# ============================================================================

def render_submit_feedback():
    """Render feedback submission form."""
    
    st.header("📝 Submit Feedback")
    
    system = st.session_state['feedback_system']
    
    # Feedback type
    feedback_type_options = {
        "Retrieval Quality": FeedbackType.RETRIEVAL_QUALITY,
        "Pruning Quality": FeedbackType.PRUNING_QUALITY,
        "Approval Decision": FeedbackType.APPROVAL_DECISION,
        "System Performance": FeedbackType.SYSTEM_PERFORMANCE,
        "Feature Request": FeedbackType.FEATURE_REQUEST,
        "Bug Report": FeedbackType.BUG_REPORT,
    }
    
    selected_type = st.selectbox(
        "Feedback Type",
        options=list(feedback_type_options.keys())
    )
    
    # Rating
    rating_value = st.slider(
        "Rating",
        min_value=1,
        max_value=5,
        value=5,
        help="1 = Poor, 5 = Excellent"
    )
    
    # Show star visual
    stars = "⭐" * rating_value + "☆" * (5 - rating_value)
    st.markdown(f"### {stars}")
    
    # Comment
    comment = st.text_area(
        "Comment (Optional)",
        height=150,
        placeholder="Share your thoughts, suggestions, or report issues..."
    )
    
    # User ID (optional)
    col1, col2 = st.columns(2)
    
    with col1:
        user_id = st.text_input(
            "User ID (Optional)",
            placeholder="your_email@example.com"
        )
    
    with col2:
        context_info = st.text_input(
            "Context (Optional)",
            placeholder="e.g., Request ID, Feature"
        )
    
    # Submit button
    if st.button("📤 Submit Feedback", type="primary", use_container_width=True):
        if submit_feedback_action(
            system,
            feedback_type_options[selected_type],
            rating_value,
            comment,
            user_id,
            context_info
        ):
            st.success("✅ Thank you for your feedback!")
            st.balloons()
            st.rerun()


def submit_feedback_action(system, feedback_type, rating_value, comment, user_id, context_info):
    """Submit feedback action."""
    context = {}
    if context_info:
        context["info"] = context_info
    
    system.submit_feedback(
        feedback_type=feedback_type,
        rating=Rating(rating_value),
        comment=comment if comment else None,
        context=context,
        user_id=user_id if user_id else None
    )
    
    return True


# ============================================================================
# Statistics Section
# ============================================================================

def render_statistics():
    """Render feedback statistics."""
    
    st.header("📊 Feedback Statistics")
    
    system = st.session_state['feedback_system']
    stats = system.get_statistics()
    
    if stats.total_feedback == 0:
        st.info("No feedback yet. Submit some feedback to see statistics!")
        return
    
    # Overall metrics
    st.subheader("📈 Overall Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Feedback", stats.total_feedback)
    with col2:
        st.metric("Average Rating", f"{stats.average_rating:.2f}⭐")
    with col3:
        total_5_star = stats.rating_distribution.get(5, 0)
        st.metric("5-Star Reviews", total_5_star)
    with col4:
        total_low = stats.rating_distribution.get(1, 0) + stats.rating_distribution.get(2, 0)
        st.metric("Needs Attention", total_low)
    
    # Rating distribution
    st.subheader("⭐ Rating Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart
        fig_pie = px.pie(
            values=list(stats.rating_distribution.values()),
            names=[f"{k}⭐" for k in stats.rating_distribution.keys()],
            title="Rating Distribution"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Bar chart
        fig_bar = go.Figure(data=[
            go.Bar(
                x=[f"{k}⭐" for k in sorted(stats.rating_distribution.keys())],
                y=[stats.rating_distribution[k] for k in sorted(stats.rating_distribution.keys())],
                marker_color=['#ff4444', '#ff8844', '#ffaa44', '#88ff44', '#44ff44']
            )
        ])
        fig_bar.update_layout(title="Rating Counts", xaxis_title="Rating", yaxis_title="Count")
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Feedback by type
    st.subheader("📋 Feedback by Type")
    
    if stats.by_type:
        type_df = pd.DataFrame([
            {"Type": k.replace('_', ' ').title(), "Count": v}
            for k, v in stats.by_type.items()
        ])
        
        fig_types = px.bar(
            type_df,
            x="Type",
            y="Count",
            title="Feedback Distribution by Type"
        )
        st.plotly_chart(fig_types, use_container_width=True)
    
    # Recent feedback
    st.subheader("🕐 Recent Feedback")
    
    for entry in stats.recent_feedback[:5]:
        with st.expander(
            f"{'⭐' * entry.rating.value} - {entry.feedback_type.value.replace('_', ' ').title()} - {entry.created_at.strftime('%Y-%m-%d %H:%M')}"
        ):
            if entry.comment:
                st.markdown(f"**Comment:** {entry.comment}")
            if entry.user_id:
                st.markdown(f"**User:** {entry.user_id}")
            if entry.context:
                st.json(entry.context)


# ============================================================================
# Trends Section
# ============================================================================

def render_trends():
    """Render feedback trends analysis."""
    
    st.header("📈 Trends & Analysis")
    
    system = st.session_state['feedback_system']
    
    # Time period selector
    period = st.selectbox(
        "Analysis Period",
        options=[7, 14, 30, 90],
        format_func=lambda x: f"Last {x} days"
    )
    
    # Analyze trends
    trends = system.analyze_trends(days=period)
    
    if trends.get("trend") == "no_data":
        st.info("Not enough data for trend analysis")
        return
    
    # Trend metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Feedback Entries", trends["total_entries"])
    with col2:
        st.metric("Average Rating", f"{trends['average_rating']:.2f}⭐")
    with col3:
        trend_icon = "📈" if trends["trend"] == "positive" else "📉" if trends["trend"] == "negative" else "➡️"
        st.metric("Trend", f"{trend_icon} {trends['trend'].title()}")
    
    # Low ratings alert
    if trends["low_ratings_count"] > 0:
        st.warning(f"⚠️ {trends['low_ratings_count']} low-rated feedback entries need attention")
    else:
        st.success("✅ No low-rated feedback in this period")
    
    # Satisfaction gauge
    st.subheader("😊 Satisfaction Level")
    
    satisfaction = (trends["average_rating"] / 5.0) * 100
    
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=satisfaction,
        title={'text': "Overall Satisfaction"},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 40], 'color': "lightcoral"},
                {'range': [40, 70], 'color': "lightyellow"},
                {'range': [70, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    
    st.plotly_chart(fig_gauge, use_container_width=True)


# ============================================================================
# Suggestions Section
# ============================================================================

def render_suggestions():
    """Render improvement suggestions."""
    
    st.header("💡 Improvement Suggestions")
    
    system = st.session_state['feedback_system']
    suggestions = system.get_improvement_suggestions(min_rating=3)
    
    if not suggestions:
        st.success("✅ No critical feedback at the moment!")
        return
    
    st.markdown(f"**{len(suggestions)} feedback entries** with suggestions for improvement:")
    
    # Group by type
    by_type = {}
    for entry in suggestions:
        type_name = entry.feedback_type.value
        if type_name not in by_type:
            by_type[type_name] = []
        by_type[type_name].append(entry)
    
    # Display by type
    for type_name, entries in by_type.items():
        with st.expander(f"📌 {type_name.replace('_', ' ').title()} ({len(entries)} items)"):
            for entry in entries[:10]:  # Show top 10
                st.markdown(f"""
                **{'⭐' * entry.rating.value}** - {entry.created_at.strftime('%Y-%m-%d')}
                
                {entry.comment}
                """)
                if entry.user_id:
                    st.caption(f"From: {entry.user_id}")
                st.divider()


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    render()

