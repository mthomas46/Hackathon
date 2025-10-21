"""
Quality Dashboard

Comprehensive UI for documentation quality metrics, review queue management,
and quality report visualization.
"""

import streamlit as st
import requests
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def show(api_base_url: str):
    """Display the Quality Dashboard."""
    st.title("📊 Quality Dashboard")
    st.markdown("Monitor documentation quality, manage reviews, and track quality metrics.")
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Overview",
        "📋 Review Queue",
        "📊 Quality Reports",
        "🎯 Validation"
    ])
    
    with tab1:
        show_quality_overview(api_base_url)
    
    with tab2:
        show_review_queue(api_base_url)
    
    with tab3:
        show_quality_reports(api_base_url)
    
    with tab4:
        show_validation_interface(api_base_url)


def show_quality_overview(api_base_url: str):
    """Show quality metrics overview."""
    st.header("📈 Quality Metrics Overview")
    
    # Get list of documentation runs
    try:
        response = requests.get(
            f"{api_base_url}/api/v1/documentation/runs",
            timeout=10
        )
        response.raise_for_status()
        runs = response.json()
        
        if not runs:
            st.info("📭 No documentation runs found. Generate documentation first.")
            return
        
        # Select run
        run_options = {
            f"{run['id'][:8]}... - {run.get('status', 'unknown')} ({run.get('created_at', 'unknown')[:10]})": run['id']
            for run in runs[-10:]  # Last 10 runs
        }
        
        selected_run_key = st.selectbox(
            "Select Documentation Run",
            options=list(run_options.keys()),
            key="quality_overview_run_select"
        )
        
        if not selected_run_key:
            return
        
        run_id = run_options[selected_run_key]
        
        # Fetch quality metrics
        metrics_response = requests.get(
            f"{api_base_url}/api/v1/quality/metrics/{run_id}",
            timeout=10
        )
        
        if metrics_response.status_code == 404:
            st.warning("⚠️ No quality metrics found for this run. Run validation first.")
            
            # Add validation button
            if st.button("🔍 Run Quality Validation", key="run_validation_overview"):
                with st.spinner("Running quality validation..."):
                    validate_response = requests.post(
                        f"{api_base_url}/api/v1/quality/validate-run",
                        json={"run_id": run_id},
                        timeout=300
                    )
                    
                    if validate_response.status_code == 200:
                        result = validate_response.json()
                        st.success(f"✅ Validation complete! {result['validated_artifacts']}/{result['total_artifacts']} artifacts validated")
                        st.rerun()
                    else:
                        st.error(f"❌ Validation failed: {validate_response.text}")
            return
        
        metrics_response.raise_for_status()
        metrics = metrics_response.json()
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            completeness = metrics.get('average_completeness', 0)
            delta_color = "normal" if completeness >= 0.85 else "inverse"
            st.metric(
                "Avg Completeness",
                f"{completeness:.1%}",
                delta=f"{(completeness - 0.85):.1%} vs target",
                delta_color=delta_color
            )
        
        with col2:
            accuracy = metrics.get('average_accuracy', 0)
            delta_color = "normal" if accuracy >= 0.90 else "inverse"
            st.metric(
                "Avg Accuracy",
                f"{accuracy:.1%}",
                delta=f"{(accuracy - 0.90):.1%} vs target",
                delta_color=delta_color
            )
        
        with col3:
            confidence = metrics.get('average_confidence', 0)
            delta_color = "normal" if confidence >= 0.85 else "inverse"
            st.metric(
                "Avg Confidence",
                f"{confidence:.1%}",
                delta=f"{(confidence - 0.85):.1%} vs target",
                delta_color=delta_color
            )
        
        with col4:
            requiring_review = metrics.get('requiring_review', 0)
            total = metrics.get('total_artifacts', 1)
            review_rate = requiring_review / total if total > 0 else 0
            delta_color = "inverse" if review_rate > 0.1 else "normal"
            st.metric(
                "Requiring Review",
                f"{requiring_review}/{total}",
                delta=f"{review_rate:.1%} rate",
                delta_color=delta_color
            )
        
        # Priority breakdown
        st.subheader("📊 Priority Breakdown")
        
        by_priority = metrics.get('by_priority', {})
        if by_priority:
            # Create pie chart
            fig = go.Figure(data=[go.Pie(
                labels=list(by_priority.keys()),
                values=list(by_priority.values()),
                hole=0.4,
                marker=dict(colors=['#ff4444', '#ffbb33', '#00c851', '#33b5e5'])
            )])
            fig.update_layout(
                title="Artifacts by Priority",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No priority data available")
        
        # Quality distribution
        st.subheader("📈 Quality Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Completeness gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=completeness * 100,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Completeness"},
                delta={'reference': 85},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 60], 'color': "lightgray"},
                        {'range': [60, 85], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 85
                    }
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Accuracy gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=accuracy * 100,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Accuracy"},
                delta={'reference': 90},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 60], 'color': "lightgray"},
                        {'range': [60, 90], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
        
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching quality metrics: {e}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")


def show_review_queue(api_base_url: str):
    """Show review queue management interface."""
    st.header("📋 Review Queue Management")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "pending", "in_review", "approved", "rejected", "needs_revision"],
            key="review_queue_status_filter"
        )
    
    with col2:
        priority_filter = st.selectbox(
            "Filter by Priority",
            ["All", "critical", "high", "medium", "low"],
            key="review_queue_priority_filter"
        )
    
    with col3:
        limit = st.number_input(
            "Max Items",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            key="review_queue_limit"
        )
    
    # Build query params
    params = {"limit": limit}
    if status_filter != "All":
        params["status"] = status_filter
    if priority_filter != "All":
        params["priority"] = priority_filter
    
    try:
        # Fetch review queue
        response = requests.get(
            f"{api_base_url}/api/v1/quality/review/queue",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        queue = response.json()
        
        if not queue:
            st.info("📭 No review items found matching the filters.")
            return
        
        st.success(f"📊 Found {len(queue)} review item(s)")
        
        # Display queue
        for item in queue:
            with st.expander(
                f"{'🔴' if item['priority'] == 'critical' else '🟡' if item['priority'] == 'high' else '🟢'} "
                f"{item['artifact_title']} - {item['status'].upper()}",
                expanded=False
            ):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Confidence Score", f"{item['confidence_score']:.1%}")
                    st.caption(f"Priority: **{item['priority'].upper()}**")
                
                with col2:
                    st.metric("Status", item['status'].upper())
                    st.caption(f"Created: {item['created_at'][:10]}")
                
                with col3:
                    st.metric("Issues", len(item.get('issues', [])))
                    st.caption(f"ID: {item['review_id'][:8]}...")
                
                # Issues
                if item.get('issues'):
                    st.subheader("⚠️ Issues")
                    for issue in item['issues']:
                        st.markdown(f"- {issue}")
                
                # Recommendations
                if item.get('recommendations'):
                    st.subheader("💡 Recommendations")
                    for rec in item['recommendations']:
                        st.markdown(f"- {rec}")
                
                # Actions
                st.subheader("🎯 Actions")
                
                action_col1, action_col2, action_col3 = st.columns(3)
                
                with action_col1:
                    if item['status'] == 'pending':
                        reviewer_email = st.text_input(
                            "Assign to",
                            placeholder="reviewer@example.com",
                            key=f"assign_{item['review_id']}"
                        )
                        
                        if st.button("👤 Assign Review", key=f"btn_assign_{item['review_id']}"):
                            if reviewer_email:
                                assign_response = requests.post(
                                    f"{api_base_url}/api/v1/quality/review/{item['review_id']}/assign",
                                    json={"reviewer": reviewer_email},
                                    timeout=10
                                )
                                
                                if assign_response.status_code == 200:
                                    st.success(f"✅ Assigned to {reviewer_email}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Assignment failed: {assign_response.text}")
                            else:
                                st.warning("⚠️ Enter reviewer email")
                
                with action_col2:
                    if item['status'] in ['in_review', 'needs_revision']:
                        complete_status = st.selectbox(
                            "Complete as",
                            ["approved", "rejected", "needs_revision"],
                            key=f"complete_status_{item['review_id']}"
                        )
                        
                        reviewer_notes = st.text_area(
                            "Notes",
                            placeholder="Optional reviewer notes",
                            key=f"notes_{item['review_id']}"
                        )
                        
                        if st.button("✅ Complete Review", key=f"btn_complete_{item['review_id']}"):
                            complete_response = requests.post(
                                f"{api_base_url}/api/v1/quality/review/{item['review_id']}/complete",
                                json={
                                    "status": complete_status,
                                    "reviewer_notes": reviewer_notes
                                },
                                timeout=10
                            )
                            
                            if complete_response.status_code == 200:
                                st.success(f"✅ Review completed as {complete_status}")
                                st.rerun()
                            else:
                                st.error(f"❌ Completion failed: {complete_response.text}")
                
                with action_col3:
                    if st.button("🔗 View Artifact", key=f"btn_view_{item['review_id']}"):
                        st.info(f"Artifact ID: {item['artifact_id']}")
                        st.caption("Navigate to Documentation Browser to view full artifact")
        
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching review queue: {e}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")


def show_quality_reports(api_base_url: str):
    """Show quality reports interface."""
    st.header("📊 Quality Reports")
    
    # Get list of documentation runs
    try:
        response = requests.get(
            f"{api_base_url}/api/v1/documentation/runs",
            timeout=10
        )
        response.raise_for_status()
        runs = response.json()
        
        if not runs:
            st.info("📭 No documentation runs found.")
            return
        
        # Select run
        run_options = {
            f"{run['id'][:8]}... - {run.get('status', 'unknown')} ({run.get('created_at', 'unknown')[:10]})": run['id']
            for run in runs[-10:]
        }
        
        selected_run_key = st.selectbox(
            "Select Documentation Run",
            options=list(run_options.keys()),
            key="quality_report_run_select"
        )
        
        if not selected_run_key:
            return
        
        run_id = run_options[selected_run_key]
        
        # Fetch quality report
        report_response = requests.get(
            f"{api_base_url}/api/v1/quality/report/{run_id}",
            timeout=10
        )
        
        if report_response.status_code == 404:
            st.warning("⚠️ No quality report found for this run.")
            return
        
        report_response.raise_for_status()
        report = report_response.json()
        
        # Summary metrics
        st.subheader("📊 Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Artifacts", report['total_artifacts'])
        
        with col2:
            st.metric("Avg Completeness", f"{report['average_completeness']:.1%}")
        
        with col3:
            st.metric("Avg Accuracy", f"{report['average_accuracy']:.1%}")
        
        with col4:
            st.metric("Avg Confidence", f"{report['average_confidence']:.1%}")
        
        # Issues breakdown
        st.subheader("⚠️ Issues Breakdown")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Issues", report['total_issues'])
            st.metric("Critical Issues", report['critical_issues'])
        
        with col2:
            st.metric("Requiring Review", report['artifacts_requiring_review'])
            review_rate = report['artifacts_requiring_review'] / report['total_artifacts'] if report['total_artifacts'] > 0 else 0
            st.metric("Review Rate", f"{review_rate:.1%}")
        
        # Priority breakdown
        if report.get('review_priority_breakdown'):
            st.subheader("📊 Priority Breakdown")
            
            priority_df = pd.DataFrame([
                {"Priority": k.capitalize(), "Count": v}
                for k, v in report['review_priority_breakdown'].items()
            ])
            
            fig = px.bar(
                priority_df,
                x="Priority",
                y="Count",
                title="Artifacts by Priority",
                color="Priority",
                color_discrete_map={
                    "Critical": "#ff4444",
                    "High": "#ffbb33",
                    "Medium": "#00c851",
                    "Low": "#33b5e5"
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Top recommendations
        if report.get('top_recommendations'):
            st.subheader("💡 Top Recommendations")
            
            for i, rec in enumerate(report['top_recommendations'][:10], 1):
                st.markdown(f"{i}. {rec}")
        
        # Generated timestamp
        st.caption(f"Report generated at: {report['generated_at']}")
        
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching quality report: {e}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")


def show_validation_interface(api_base_url: str):
    """Show validation interface for manual validation."""
    st.header("🎯 Manual Validation")
    
    st.markdown("""
    Run quality validation on documentation artifacts manually.
    Validation checks:
    - **Completeness**: Section coverage, placeholders, links
    - **Accuracy**: Code syntax, API docs, type consistency
    - **Confidence**: Overall quality score and review requirements
    """)
    
    # Validate single artifact
    with st.expander("🔍 Validate Single Artifact", expanded=False):
        artifact_id = st.text_input(
            "Artifact ID",
            placeholder="Enter artifact UUID",
            key="validate_single_artifact_id"
        )
        
        source_quality = st.slider(
            "Source Quality (optional)",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05,
            help="Quality score of the source code (e.g., test coverage, documentation)",
            key="validate_single_source_quality"
        )
        
        if st.button("🔍 Run Validation", key="btn_validate_single"):
            if not artifact_id:
                st.warning("⚠️ Enter artifact ID")
            else:
                with st.spinner("Running validation..."):
                    try:
                        response = requests.post(
                            f"{api_base_url}/api/v1/quality/validate",
                            json={
                                "artifact_id": artifact_id,
                                "source_quality": source_quality
                            },
                            timeout=60
                        )
                        response.raise_for_status()
                        result = response.json()
                        
                        st.success("✅ Validation complete!")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Completeness", f"{result['completeness_score']:.1%}")
                        
                        with col2:
                            st.metric("Accuracy", f"{result['accuracy_score']:.1%}")
                        
                        with col3:
                            st.metric("Confidence", f"{result['overall_confidence']:.1%}")
                        
                        st.info(f"**Requires Review:** {'Yes' if result['requires_review'] else 'No'}")
                        st.caption(f"**Priority:** {result['review_priority'].upper()}")
                        
                        if result.get('recommendations'):
                            st.subheader("💡 Recommendations")
                            for rec in result['recommendations'][:5]:
                                st.markdown(f"- {rec}")
                        
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Validation failed: {e}")
    
    # Validate entire run
    with st.expander("📚 Validate Entire Run", expanded=True):
        try:
            # Get documentation runs
            runs_response = requests.get(
                f"{api_base_url}/api/v1/documentation/runs",
                timeout=10
            )
            runs_response.raise_for_status()
            runs = runs_response.json()
            
            if not runs:
                st.info("📭 No documentation runs found.")
            else:
                run_options = {
                    f"{run['id'][:8]}... - {run.get('status', 'unknown')} ({run.get('created_at', 'unknown')[:10]})": run['id']
                    for run in runs[-10:]
                }
                
                selected_run_key = st.selectbox(
                    "Select Documentation Run",
                    options=list(run_options.keys()),
                    key="validate_run_select"
                )
                
                if selected_run_key:
                    run_id = run_options[selected_run_key]
                    
                    if st.button("🔍 Run Full Validation", key="btn_validate_run"):
                        with st.spinner("Running full validation (this may take a while)..."):
                            try:
                                response = requests.post(
                                    f"{api_base_url}/api/v1/quality/validate-run",
                                    json={"run_id": run_id},
                                    timeout=300
                                )
                                response.raise_for_status()
                                result = response.json()
                                
                                st.success(f"✅ Validation complete!")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.metric("Validated", f"{result['validated_artifacts']}/{result['total_artifacts']}")
                                
                                with col2:
                                    st.metric("Avg Completeness", f"{result['average_completeness']:.1%}")
                                
                                with col3:
                                    st.metric("Avg Accuracy", f"{result['average_accuracy']:.1%}")
                                
                                with col4:
                                    st.metric("Requiring Review", result['artifacts_requiring_review'])
                                
                                st.info(f"📊 Quality report generated! View in the Quality Reports tab.")
                                
                            except requests.exceptions.RequestException as e:
                                st.error(f"❌ Validation failed: {e}")
        
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Error loading runs: {e}")

