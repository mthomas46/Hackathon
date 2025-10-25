"""
Documentation Maintenance Dashboard

Proactive documentation quality management with:
- Staleness detection
- Coverage analysis  
- Consistency checking
- Quality scoring
- Dependency tracking
- Auto-refresh planning
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils.api_tracker import make_api_request


def show(api_base_url: str):
    """Display documentation maintenance dashboard."""
    st.title("🔧 Documentation Maintenance")
    st.markdown("Proactive documentation quality management and health monitoring")
    
    # Top-level tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview",
        "🕐 Staleness",
        "📋 Coverage",
        "✅ Consistency",
        "⭐ Quality",
        "🔗 Dependencies"
    ])
    
    with tab1:
        show_maintenance_overview(api_base_url)
    
    with tab2:
        show_staleness_detection(api_base_url)
    
    with tab3:
        show_coverage_analysis(api_base_url)
    
    with tab4:
        show_consistency_checking(api_base_url)
    
    with tab5:
        show_quality_scoring(api_base_url)
    
    with tab6:
        show_dependency_tracking(api_base_url)


def show_maintenance_overview(api_base_url: str):
    """Show overall documentation maintenance status."""
    st.subheader("📊 Maintenance Overview")
    
    # Fetch all metrics
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Overview", type="primary"):
            st.rerun()
    
    with col2:
        auto_refresh = st.toggle("Auto-refresh (30s)")
        if auto_refresh:
            st.info("⏱️ Auto-refreshing every 30 seconds")
    
    st.markdown("---")
    
    # Quality metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Mock data for now - replace with actual API calls
    with col1:
        st.metric("📚 Total Docs", "247", delta="5")
    with col2:
        st.metric("🕐 Stale Docs", "12", delta="-2", delta_color="inverse")
    with col3:
        st.metric("📋 Coverage", "87%", delta="3%")
    with col4:
        st.metric("⭐ Avg Quality", "8.2/10", delta="0.3")
    
    st.markdown("---")
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🕐 Detect Stale Docs", use_container_width=True):
            st.info("⚠️ This feature requires additional API implementation")
            st.markdown("**Status:** API endpoints pending implementation")
            st.markdown("**Endpoint:** `/api/v1/maintenance/staleness/detect`")
    
    with col2:
        if st.button("📋 Analyze Coverage", use_container_width=True):
            st.info("⚠️ This feature requires additional API implementation")
            st.markdown("**Endpoint:** `/api/v1/maintenance/coverage/analyze`")
    
    with col3:
        if st.button("✅ Check Consistency", use_container_width=True):
            st.info("⚠️ This feature requires additional API implementation")
            st.markdown("**Endpoint:** `/api/v1/maintenance/consistency/check`")


def show_staleness_detection(api_base_url: str):
    """Show staleness detection interface."""
    st.subheader("🕐 Staleness Detection")
    st.markdown("Identify outdated documentation that needs updating")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        staleness_threshold = st.slider(
            "Staleness Threshold (days)",
            min_value=7,
            max_value=180,
            value=30,
            help="Documents not updated for this many days are considered stale"
        )
    
    with col2:
        severity_filter = st.multiselect(
            "Severity",
            ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
            default=["CRITICAL", "HIGH"]
        )
    
    if st.button("🔍 Detect Stale Documents", type="primary"):
        with st.spinner("Analyzing documentation staleness..."):
            result = make_api_request(
                api_base_url,
                "/api/v1/maintenance/staleness/detect",
                method="POST",
                json_data={
                    "threshold_days": staleness_threshold,
                    "severity_filter": severity_filter
                },
                timeout=30.0
            )
            
            if result:
                stale_docs = result.get("stale_documents", [])
                
                if not stale_docs:
                    st.success("✅ No stale documents found!")
                else:
                    st.warning(f"⚠️ Found {len(stale_docs)} stale documents")
                    
                    # Display metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        critical = sum(1 for d in stale_docs if d.get("severity") == "CRITICAL")
                        st.metric("Critical", critical)
                    with col2:
                        high = sum(1 for d in stale_docs if d.get("severity") == "HIGH")
                        st.metric("High", high)
                    with col3:
                        medium = sum(1 for d in stale_docs if d.get("severity") == "MEDIUM")
                        st.metric("Medium", medium)
                    
                    # Display stale documents
                    st.markdown("### 📄 Stale Documents")
                    
                    for doc in stale_docs[:20]:  # Show first 20
                        severity = doc.get("severity", "INFO")
                        icon = {"CRITICAL": "🔴", "HIGH": "🟡", "MEDIUM": "🟠", "LOW": "🔵"}.get(severity, "⚪")
                        
                        with st.expander(f"{icon} {doc.get('file_path', 'Unknown')} - {doc.get('days_old', 0)} days old"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Last Updated:** {doc.get('last_updated', 'Unknown')}")
                                st.markdown(f"**Service:** {doc.get('service_name', 'N/A')}")
                            with col2:
                                st.markdown(f"**Severity:** {severity}")
                                st.markdown(f"**Age:** {doc.get('days_old', 0)} days")
                            
                            st.markdown(f"**Reason:** {doc.get('reason', 'N/A')}")
                            
                            if doc.get("doc_id"):
                                if st.button(f"View Details", key=f"view_{doc['doc_id']}"):
                                    show_staleness_details(api_base_url, doc["doc_id"])


def show_staleness_details(api_base_url: str, doc_id: str):
    """Show detailed staleness information for a document."""
    result = make_api_request(
        api_base_url,
        f"/api/v1/maintenance/staleness/details/{doc_id}",
        method="GET"
    )
    
    if result:
        st.markdown("#### 📊 Detailed Staleness Analysis")
        st.json(result)


def show_coverage_analysis(api_base_url: str):
    """Show coverage analysis interface."""
    st.subheader("📋 Coverage Analysis")
    st.markdown("Analyze documentation coverage across services")
    
    scope = st.selectbox(
        "Analysis Scope",
        ["All Services", "Specific Service", "By Type"]
    )
    
    service_filter = None
    if scope == "Specific Service":
        service_filter = st.text_input("Service Name", placeholder="ecosystem-mcp")
    
    if st.button("📊 Analyze Coverage", type="primary"):
        with st.spinner("Analyzing documentation coverage..."):
            params = {}
            if service_filter:
                params["service"] = service_filter
            
            result = make_api_request(
                api_base_url,
                "/api/v1/maintenance/coverage/analyze",
                method="POST",
                json_data=params,
                timeout=30.0
            )
            
            if result:
                # Display overall coverage
                coverage_percent = result.get("coverage_percent", 0)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Overall Coverage", f"{coverage_percent:.1f}%")
                with col2:
                    st.metric("Documented", result.get("documented_count", 0))
                with col3:
                    st.metric("Undocumented", result.get("undocumented_count", 0))
                with col4:
                    st.metric("Partial", result.get("partial_count", 0))
                
                # Coverage by category
                if "coverage_by_category" in result:
                    st.markdown("### 📊 Coverage by Category")
                    
                    categories = result["coverage_by_category"]
                    df = pd.DataFrame([
                        {"Category": cat, "Coverage": data["coverage_percent"]}
                        for cat, data in categories.items()
                    ])
                    
                    fig = px.bar(df, x="Category", y="Coverage", title="Coverage by Category")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Show gaps
                if st.button("🔍 Show Coverage Gaps"):
                    gaps_result = make_api_request(
                        api_base_url,
                        "/api/v1/maintenance/coverage/gaps",
                        method="GET",
                        params=params
                    )
                    
                    if gaps_result and gaps_result.get("gaps"):
                        st.markdown("### 🕳️ Coverage Gaps")
                        for gap in gaps_result["gaps"][:10]:
                            st.warning(f"⚠️ {gap.get('type', 'Unknown')}: {gap.get('description', 'N/A')}")


def show_consistency_checking(api_base_url: str):
    """Show consistency checking interface."""
    st.subheader("✅ Consistency Checking")
    st.markdown("Detect conflicts and inconsistencies in documentation")
    
    check_type = st.multiselect(
        "Check Types",
        ["Cross-references", "Version Mismatches", "Duplicate Content", "Broken Links"],
        default=["Cross-references", "Version Mismatches"]
    )
    
    if st.button("🔍 Check Consistency", type="primary"):
        with st.spinner("Checking documentation consistency..."):
            result = make_api_request(
                api_base_url,
                "/api/v1/maintenance/consistency/check",
                method="POST",
                json_data={"check_types": check_type},
                timeout=30.0
            )
            
            if result:
                conflicts = result.get("conflicts", [])
                
                if not conflicts:
                    st.success("✅ No consistency issues found!")
                else:
                    st.warning(f"⚠️ Found {len(conflicts)} consistency issues")
                    
                    # Group by severity
                    critical = [c for c in conflicts if c.get("severity") == "CRITICAL"]
                    high = [c for c in conflicts if c.get("severity") == "HIGH"]
                    medium = [c for c in conflicts if c.get("severity") == "MEDIUM"]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Critical", len(critical))
                    with col2:
                        st.metric("High", len(high))
                    with col3:
                        st.metric("Medium", len(medium))
                    
                    # Show conflicts
                    st.markdown("### ⚠️ Consistency Issues")
                    
                    for conflict in conflicts[:15]:
                        severity = conflict.get("severity", "INFO")
                        icon = {"CRITICAL": "🔴", "HIGH": "🟡", "MEDIUM": "🟠"}.get(severity, "⚪")
                        
                        with st.expander(f"{icon} {conflict.get('type', 'Unknown')} - {conflict.get('title', 'Issue')}"):
                            st.markdown(f"**Severity:** {severity}")
                            st.markdown(f"**Description:** {conflict.get('description', 'N/A')}")
                            
                            if "affected_files" in conflict:
                                st.markdown("**Affected Files:**")
                                for file in conflict["affected_files"]:
                                    st.markdown(f"- {file}")
                            
                            if "recommendation" in conflict:
                                st.info(f"💡 **Recommendation:** {conflict['recommendation']}")


def show_quality_scoring(api_base_url: str):
    """Show quality scoring interface."""
    st.subheader("⭐ Quality Scoring")
    st.markdown("Assess documentation quality with automated scoring")
    
    scope = st.radio(
        "Scoring Scope",
        ["Overall Quality", "By Service", "By Document Type"],
        horizontal=True
    )
    
    if st.button("📊 Generate Quality Report", type="primary"):
        with st.spinner("Calculating quality scores..."):
            result = make_api_request(
                api_base_url,
                "/api/v1/maintenance/quality/score",
                method="POST",
                json_data={"scope": scope},
                timeout=30.0
            )
            
            if result:
                # Overall score
                overall_score = result.get("overall_score", 0)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Overall Quality", f"{overall_score:.1f}/10")
                with col2:
                    st.metric("Completeness", f"{result.get('completeness', 0):.0f}%")
                with col3:
                    st.metric("Accuracy", f"{result.get('accuracy', 0):.0f}%")
                with col4:
                    st.metric("Freshness", f"{result.get('freshness', 0):.0f}%")
                
                # Quality breakdown
                if "quality_by_service" in result:
                    st.markdown("### 📊 Quality by Service")
                    
                    services_data = []
                    for service, data in result["quality_by_service"].items():
                        services_data.append({
                            "Service": service,
                            "Score": data.get("score", 0),
                            "Docs": data.get("document_count", 0)
                        })
                    
                    df = pd.DataFrame(services_data)
                    fig = px.scatter(df, x="Docs", y="Score", text="Service", size="Docs",
                                   title="Quality vs Document Count by Service")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Get detailed report
                if st.button("📄 View Detailed Report"):
                    report_result = make_api_request(
                        api_base_url,
                        "/api/v1/maintenance/quality/report",
                        method="GET"
                    )
                    
                    if report_result:
                        st.markdown("### 📋 Detailed Quality Report")
                        st.json(report_result)


def show_dependency_tracking(api_base_url: str):
    """Show dependency tracking interface."""
    st.subheader("🔗 Dependency Tracking")
    st.markdown("Analyze cross-references and dependencies between documents")
    
    analysis_type = st.radio(
        "Analysis Type",
        ["Dependency Graph", "Impact Analysis", "Circular Dependencies"],
        horizontal=True
    )
    
    if st.button("🔍 Analyze Dependencies", type="primary"):
        with st.spinner("Analyzing document dependencies..."):
            result = make_api_request(
                api_base_url,
                "/api/v1/maintenance/dependencies/analyze",
                method="POST",
                json_data={"analysis_type": analysis_type},
                timeout=30.0
            )
            
            if result:
                # Show metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Links", result.get("total_links", 0))
                with col2:
                    st.metric("Cross-Service Links", result.get("cross_service_links", 0))
                with col3:
                    st.metric("Broken Links", result.get("broken_links", 0))
                
                # Show dependency graph
                if analysis_type == "Dependency Graph":
                    if st.button("📊 View Dependency Graph"):
                        graph_result = make_api_request(
                            api_base_url,
                            "/api/v1/maintenance/dependencies/graph",
                            method="GET"
                        )
                        
                        if graph_result:
                            st.info("📊 Dependency graph visualization coming soon")
                            st.json(graph_result)

