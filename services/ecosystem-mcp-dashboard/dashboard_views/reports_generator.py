"""
Report Generation UI

Generate and export various types of reports including:
- Progression reports (timeline analysis)
- Gap analysis reports  
- Drift detection reports
- Architecture reports
- Service analysis reports
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional

from utils.api_tracker import make_api_request


def show(api_base_url: str):
    """Display report generation interface."""
    st.title("📑 Report Generation")
    st.markdown("Generate comprehensive reports and analysis documents")
    
    # Report type selector
    report_type = st.radio(
        "Report Type",
        [
            "📊 Analysis Report",
            "🏗️ Architecture Report",
            "🔧 Service Analysis",
            "📈 Stack Analysis",
            "🌳 Context Report"
        ],
        horizontal=False
    )
    
    st.markdown("---")
    
    if report_type == "📊 Analysis Report":
        show_analysis_report_generator(api_base_url)
    elif report_type == "🏗️ Architecture Report":
        show_architecture_report_generator(api_base_url)
    elif report_type == "🔧 Service Analysis":
        show_service_analysis_generator(api_base_url)
    elif report_type == "📈 Stack Analysis":
        show_stack_analysis_generator(api_base_url)
    elif report_type == "🌳 Context Report":
        show_context_report_generator(api_base_url)


def show_analysis_report_generator(api_base_url: str):
    """Generate comprehensive analysis reports."""
    st.subheader("📊 Analysis Report Generator")
    st.markdown("Generate comprehensive analysis reports from processing plans")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        plan_id = st.text_input(
            "Plan ID",
            placeholder="Enter plan ID from Discovery & Orchestration",
            help="The processing plan to analyze"
        )
    
    with col2:
        export_format = st.selectbox(
            "Export Format",
            ["Markdown", "HTML", "JSON", "PDF"],
            help="Format for the generated report"
        )
    
    # Report options
    st.markdown("### 🔧 Report Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        include_summary = st.checkbox("Executive Summary", value=True)
        include_details = st.checkbox("Detailed Analysis", value=True)
    
    with col2:
        include_metrics = st.checkbox("Metrics & Statistics", value=True)
        include_charts = st.checkbox("Charts & Visualizations", value=True)
    
    with col3:
        include_recommendations = st.checkbox("Recommendations", value=True)
        include_citations = st.checkbox("Source Citations", value=True)
    
    if st.button("📊 Generate Report", type="primary", disabled=not plan_id):
        with st.spinner("Generating analysis report..."):
            result = make_api_request(
                api_base_url,
                f"/api/v1/analysis/reports/{plan_id}",
                method="GET",
                params={
                    "format": export_format.lower(),
                    "include_summary": include_summary,
                    "include_details": include_details,
                    "include_metrics": include_metrics,
                    "include_charts": include_charts,
                    "include_recommendations": include_recommendations,
                    "include_citations": include_citations
                },
                timeout=60.0
            )
            
            if result:
                st.success("✅ Report generated successfully!")
                
                # Display report metadata
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Report Size", f"{result.get('size_kb', 0):.1f} KB")
                with col2:
                    st.metric("Sections", result.get('section_count', 0))
                with col3:
                    st.metric("Pages", result.get('page_count', 0))
                
                # Display report content
                st.markdown("### 📄 Report Preview")
                
                if export_format == "Markdown":
                    report_content = result.get('content', '')
                    st.markdown(report_content)
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Markdown",
                        data=report_content,
                        file_name=f"analysis_report_{plan_id[:8]}_{datetime.now().strftime('%Y%m%d')}.md",
                        mime="text/markdown"
                    )
                
                elif export_format == "JSON":
                    st.json(result.get('content', {}))
                    
                    import json
                    st.download_button(
                        label="📥 Download JSON",
                        data=json.dumps(result.get('content', {}), indent=2),
                        file_name=f"analysis_report_{plan_id[:8]}_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
                
                elif export_format == "HTML":
                    html_content = result.get('content', '')
                    st.components.v1.html(html_content, height=600, scrolling=True)
                    
                    st.download_button(
                        label="📥 Download HTML",
                        data=html_content,
                        file_name=f"analysis_report_{plan_id[:8]}_{datetime.now().strftime('%Y%m%d')}.html",
                        mime="text/html"
                    )
                
                else:  # PDF
                    st.info("📄 PDF report generated. Use download button to save.")
                    
                    if 'content' in result:
                        st.download_button(
                            label="📥 Download PDF",
                            data=result['content'],
                            file_name=f"analysis_report_{plan_id[:8]}_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )


def show_architecture_report_generator(api_base_url: str):
    """Generate architecture analysis reports."""
    st.subheader("🏗️ Architecture Report Generator")
    st.markdown("Analyze and document system architecture from processing plans")
    
    plan_id = st.text_input(
        "Plan ID",
        placeholder="Enter plan ID",
        help="The processing plan to analyze for architecture"
    )
    
    # Architecture analysis options
    st.markdown("### 🔧 Analysis Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        analyze_dependencies = st.checkbox("Analyze Dependencies", value=True)
        analyze_layers = st.checkbox("Identify Architectural Layers", value=True)
        analyze_patterns = st.checkbox("Detect Design Patterns", value=True)
    
    with col2:
        include_diagram = st.checkbox("Generate Architecture Diagram", value=True)
        include_dataflow = st.checkbox("Data Flow Analysis", value=True)
        include_evolution = st.checkbox("Evolution Analysis", value=False)
    
    if st.button("🏗️ Generate Architecture Report", type="primary", disabled=not plan_id):
        with st.spinner("Analyzing architecture..."):
            result = make_api_request(
                api_base_url,
                f"/api/v1/analysis/architecture/{plan_id}",
                method="GET",
                params={
                    "analyze_dependencies": analyze_dependencies,
                    "analyze_layers": analyze_layers,
                    "analyze_patterns": analyze_patterns,
                    "include_diagram": include_diagram,
                    "include_dataflow": include_dataflow,
                    "include_evolution": include_evolution
                },
                timeout=60.0
            )
            
            if result:
                st.success("✅ Architecture report generated!")
                
                # Display architecture overview
                if "overview" in result:
                    st.markdown("### 🏛️ Architecture Overview")
                    overview = result["overview"]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Layers", overview.get("layer_count", 0))
                    with col2:
                        st.metric("Components", overview.get("component_count", 0))
                    with col3:
                        st.metric("Dependencies", overview.get("dependency_count", 0))
                    with col4:
                        st.metric("Patterns", overview.get("pattern_count", 0))
                
                # Display layers
                if "layers" in result:
                    st.markdown("### 📊 Architectural Layers")
                    
                    for layer in result["layers"]:
                        with st.expander(f"🏗️ {layer.get('name', 'Unknown Layer')}"):
                            st.markdown(f"**Description:** {layer.get('description', 'N/A')}")
                            st.markdown(f"**Components:** {layer.get('component_count', 0)}")
                            
                            if "components" in layer:
                                st.markdown("**Component List:**")
                                for comp in layer["components"][:10]:
                                    st.markdown(f"- {comp}")
                
                # Display patterns detected
                if "patterns" in result:
                    st.markdown("### 🎨 Design Patterns Detected")
                    
                    for pattern in result["patterns"]:
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**{pattern.get('name', 'Unknown')}**")
                            st.caption(pattern.get('description', ''))
                        
                        with col2:
                            st.metric("Instances", pattern.get('count', 0))


def show_service_analysis_generator(api_base_url: str):
    """Generate service analysis reports."""
    st.subheader("🔧 Service Analysis Generator")
    st.markdown("Analyze individual services within a processing plan")
    
    plan_id = st.text_input(
        "Plan ID",
        placeholder="Enter plan ID",
        help="The processing plan containing services to analyze"
    )
    
    if st.button("🔍 Load Services", disabled=not plan_id):
        with st.spinner("Loading services..."):
            result = make_api_request(
                api_base_url,
                f"/api/v1/analysis/services/{plan_id}",
                method="GET",
                timeout=30.0
            )
            
            if result and "services" in result:
                st.session_state.services = result["services"]
                st.success(f"✅ Found {len(result['services'])} service(s)")
    
    # Service selector
    if "services" in st.session_state and st.session_state.services:
        services = st.session_state.services
        service_names = [s.get("name", "Unknown") for s in services]
        
        selected_service = st.selectbox(
            "Select Service",
            service_names
        )
        
        if selected_service:
            # Find selected service data
            service_data = next((s for s in services if s.get("name") == selected_service), None)
            
            if service_data:
                st.markdown(f"### 📦 {selected_service}")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Files", service_data.get("file_count", 0))
                with col2:
                    st.metric("Size", f"{service_data.get('size_mb', 0):.1f} MB")
                with col3:
                    st.metric("Type", service_data.get("type", "Unknown"))
                with col4:
                    st.metric("Dependencies", service_data.get("dependency_count", 0))
                
                # Service details
                if "details" in service_data:
                    st.markdown("### 📋 Details")
                    st.json(service_data["details"])


def show_stack_analysis_generator(api_base_url: str):
    """Generate technology stack analysis reports."""
    st.subheader("📈 Stack Analysis Generator")
    st.markdown("Analyze technology stack and dependencies")
    
    plan_id = st.text_input(
        "Plan ID",
        placeholder="Enter plan ID",
        help="The processing plan to analyze for technology stack"
    )
    
    if st.button("📈 Analyze Stack", type="primary", disabled=not plan_id):
        with st.spinner("Analyzing technology stack..."):
            result = make_api_request(
                api_base_url,
                f"/api/v1/analysis/stack/{plan_id}",
                method="GET",
                timeout=30.0
            )
            
            if result:
                st.success("✅ Stack analysis complete!")
                
                # Technology summary
                if "technologies" in result:
                    st.markdown("### 💻 Technologies Detected")
                    
                    tech_data = []
                    for tech in result["technologies"]:
                        tech_data.append({
                            "Technology": tech.get("name", "Unknown"),
                            "Version": tech.get("version", "N/A"),
                            "Files": tech.get("file_count", 0),
                            "Category": tech.get("category", "Other")
                        })
                    
                    df = pd.DataFrame(tech_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Dependency graph
                if "dependencies" in result:
                    st.markdown("### 🔗 Dependency Analysis")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    deps = result["dependencies"]
                    with col1:
                        st.metric("Total Dependencies", deps.get("total", 0))
                    with col2:
                        st.metric("Direct", deps.get("direct", 0))
                    with col3:
                        st.metric("Transitive", deps.get("transitive", 0))


def show_context_report_generator(api_base_url: str):
    """Generate hierarchical context reports."""
    st.subheader("🌳 Context Report Generator")
    st.markdown("Generate hierarchical context and repository structure reports")
    
    # Get available contexts
    result = make_api_request(
        api_base_url,
        "/api/v1/analysis/contexts",
        method="GET",
        timeout=10.0,
        show_error=False
    )
    
    if result and "contexts" in result:
        contexts = result["contexts"]
        
        if contexts:
            context_ids = [c.get("repo_id", "Unknown") for c in contexts]
            
            selected_context = st.selectbox(
                "Select Repository Context",
                context_ids,
                format_func=lambda x: x if len(x) < 50 else x[:47] + "..."
            )
            
            if selected_context and st.button("🌳 Generate Context Report", type="primary"):
                with st.spinner("Generating context report..."):
                    context_result = make_api_request(
                        api_base_url,
                        f"/api/v1/analysis/contexts/{selected_context}",
                        method="GET",
                        timeout=30.0
                    )
                    
                    if context_result:
                        st.success("✅ Context report generated!")
                        
                        # Display context hierarchy
                        st.markdown("### 🌲 Context Hierarchy")
                        st.json(context_result)
        else:
            st.info("📭 No repository contexts available. Run discovery scans to create contexts.")
    else:
        st.info("📭 Unable to fetch contexts. Make sure the API is running.")

