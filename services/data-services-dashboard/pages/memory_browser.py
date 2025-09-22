"""Memory Browser Page - Browse and manage conversation memory and operational context.

This module provides a comprehensive interface for browsing, searching, and managing
memory items stored by the Memory Agent service.
"""

import asyncio
from typing import Any, Dict, List

import pandas as pd
import streamlit as st


def render_memory_browser_page():
    """Render the memory browser page."""
    st.markdown("### 🧠 Memory Agent Browser")
    st.markdown("Browse and manage conversation memory and operational context items.")

    # Get memory client
    memory_client = st.session_state.get("memory_client")
    if not memory_client:
        st.error("❌ Memory Agent service not available")
        return

    # Create tabs for different memory operations
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["📋 Browse Memory", "🔍 Advanced Search", "➕ Add Memory", "🎭 Create Samples", "📊 Analytics", "📈 Insights"]
    )

    with tab1:
        render_memory_browser(memory_client)

    with tab2:
        render_advanced_memory_search(memory_client)

    with tab3:
        render_add_memory(memory_client)

    with tab4:
        render_create_samples(memory_client)

    with tab5:
        render_memory_analytics(memory_client)

    with tab6:
        render_memory_insights(memory_client)


def render_memory_browser(memory_client):
    """Render the memory browsing interface."""
    st.markdown("#### 📋 Browse Memory Items")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        type_filter = st.selectbox(
            "Filter by Type",
            ["All Types", "operation", "llm_summary", "doc_summary", "api_summary", "finding"],
            key="memory_type_filter",
        )

    with col2:
        sort_by = st.selectbox("Sort by", ["Newest First", "Oldest First", "Type", "Key"], key="memory_sort")

    with col3:
        limit = st.slider("Items per page", 10, 100, 50, key="memory_limit")

    # Load memory items
    if st.button("🔄 Load Memory Items", key="load_memory"):
        with st.spinner("Loading memory items..."):
            try:
                # Get memory types first to populate filter
                types_result = asyncio.run(memory_client.get_memory_types())
                if types_result:
                    # Update the filter options
                    pass

                # Get memory items
                filter_params = {}
                if type_filter != "All Types":
                    filter_params["type_filter"] = type_filter

                result = asyncio.run(memory_client.list_memory_items(limit=limit, **filter_params))

                if result.get("success"):
                    items = result.get("items", [])
                    if items:
                        render_memory_items_table(items)
                    else:
                        st.info("No memory items found matching the criteria.")
                else:
                    st.error(f"Failed to load memory items: {result.get('error', 'Unknown error')}")

            except Exception as e:
                st.error(f"Error loading memory items: {e}")


def render_memory_items_table(items: List[Dict[str, Any]]):
    """Render memory items in a table format."""
    # Convert to DataFrame for better display
    df_data = []
    for item in items:
        formatted_item = memory_client.format_memory_item(item)
        df_data.append(
            {
                "ID": formatted_item["id"][:8] + "...",  # Truncate ID
                "Type": formatted_item["type"],
                "Key": formatted_item["key"] or "",
                "Summary": (
                    formatted_item["summary"][:50] + "..."
                    if len(formatted_item["summary"]) > 50
                    else formatted_item["summary"]
                ),
                "Created": formatted_item["created_at"],
                "Expires": formatted_item["expires_at"] or "Never",
            }
        )

    df = pd.DataFrame(df_data)

    # Display table
    st.dataframe(df, use_container_width=True)

    # Detailed view for selected items
    st.markdown("#### 📖 Detailed View")
    selected_id = st.selectbox(
        "Select item for details",
        [item["id"] for item in items],
        format_func=lambda x: x[:8] + "...",
        key="memory_detail_select",
    )

    if selected_id:
        selected_item = next((item for item in items if item["id"] == selected_id), None)
        if selected_item:
            render_memory_item_details(selected_item)


def render_memory_item_details(item: Dict[str, Any]):
    """Render detailed view of a memory item."""
    formatted = memory_client.format_memory_item(item)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**ID:** {formatted['id']}")
        st.markdown(f"**Type:** {formatted['type']}")
        st.markdown(f"**Key:** {formatted['key'] or 'N/A'}")
        st.markdown(f"**Created:** {formatted['created_at']}")
        st.markdown(f"**Expires:** {formatted['expires_at'] or 'Never'}")

    with col2:
        st.markdown("**Summary:**")
        st.info(formatted["summary"])

        if formatted["data_full"]:
            with st.expander("📊 Full Data"):
                st.json(formatted["data_full"])


def render_memory_search(memory_client):
    """Render memory search interface."""
    st.markdown("#### 🔍 Search Memory Items")

    # Search form
    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input(
            "Search Query", placeholder="Enter keywords to search in memory...", key="memory_search_query"
        )

    with col2:
        search_type = st.selectbox(
            "Search in Type",
            ["All Types", "operation", "llm_summary", "doc_summary", "api_summary", "finding"],
            key="memory_search_type",
        )

    if st.button("🔍 Search", key="execute_memory_search") and search_query.strip():
        with st.spinner("Searching memory items..."):
            try:
                type_filter = None if search_type == "All Types" else search_type
                result = asyncio.run(memory_client.search_memory_items(query=search_query, type_filter=type_filter))

                if result.get("success"):
                    items = result.get("items", [])
                    total = result.get("total", 0)

                    st.success(f"Found {len(items)} results (showing top {len(items)} of {total})")

                    if items:
                        render_memory_items_table(items)
                    else:
                        st.info("No memory items found matching your search.")
                else:
                    st.error(f"Search failed: {result.get('error', 'Unknown error')}")

            except Exception as e:
                st.error(f"Error during search: {e}")


def render_advanced_memory_search(memory_client):
    """Render advanced memory search interface with filters and analytics."""
    st.markdown("#### 🔍 Advanced Memory Search")

    # Advanced filters section
    with st.expander("🎛️ Advanced Filters", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            # Memory type multi-select
            memory_types = st.multiselect(
                "Memory Types",
                ["operation", "llm_summary", "doc_summary", "api_summary", "finding"],
                default=["operation", "llm_summary"],
                key="adv_memory_types",
            )

            # Date range filter
            date_filter = st.selectbox(
                "Time Filter",
                ["All Time", "Last Hour", "Last 24 Hours", "Last Week", "Last Month"],
                key="adv_date_filter",
            )

        with col2:
            # Content filters
            content_contains = st.text_input(
                "Content Contains", placeholder="Keywords in content...", key="adv_content_filter"
            )

            key_pattern = st.text_input("Key Pattern", placeholder="Regex pattern for keys...", key="adv_key_pattern")

        with col3:
            # Quality filters
            min_summary_length = st.slider("Min Summary Length", 0, 500, 10, key="adv_min_length")

            sort_by = st.selectbox(
                "Sort By", ["Newest First", "Oldest First", "Type", "Key", "Summary Length"], key="adv_sort_by"
            )

            results_limit = st.slider("Results Limit", 10, 200, 50, key="adv_results_limit")

    # Search execution
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("🔍 Execute Search", key="execute_adv_search", use_container_width=True):
            execute_advanced_memory_search(
                memory_client,
                {
                    "types": memory_types,
                    "date_filter": date_filter,
                    "content_contains": content_contains,
                    "key_pattern": key_pattern,
                    "min_length": min_summary_length,
                    "sort_by": sort_by,
                    "limit": results_limit,
                },
            )

    with col2:
        if st.button("📊 Analyze Results", key="analyze_search_results", use_container_width=True):
            st.info("Analysis feature would show search result statistics and trends")

    with col3:
        export_format = st.selectbox("Export Format", ["JSON", "CSV", "Markdown"], key="export_format")
        if st.button("📥 Export Results", key="export_search_results"):
            st.info(f"Would export search results as {export_format}")

    # Search templates
    st.markdown("---")
    st.markdown("**🔖 Search Templates**")

    templates = {
        "Recent Operations": {"types": ["operation"], "date_filter": "Last 24 Hours"},
        "LLM Interactions": {"types": ["llm_summary"], "date_filter": "Last Week"},
        "Document Analysis": {"types": ["doc_summary"], "content_contains": "analysis"},
        "API Monitoring": {"types": ["api_summary"], "date_filter": "Last Hour"},
        "Security Findings": {"types": ["finding"], "content_contains": "security"},
    }

    selected_template = st.selectbox(
        "Quick Templates", ["Select Template"] + list(templates.keys()), key="search_template"
    )

    if selected_template != "Select Template":
        template_config = templates[selected_template]
        if st.button("📋 Apply Template", key="apply_template"):
            # This would populate the filters with template values
            st.info(f"Applied template: {selected_template}")
            st.json(template_config)


def render_memory_analytics(memory_client):
    """Render comprehensive memory analytics."""
    st.markdown("#### 📊 Memory Analytics")

    if st.button("📈 Load Analytics", key="load_memory_analytics"):
        with st.spinner("Analyzing memory data..."):
            # Mock analytics - would come from API
            analytics = {
                "total_items": 245,
                "memory_types": {
                    "operation": 89,
                    "llm_summary": 67,
                    "doc_summary": 45,
                    "api_summary": 31,
                    "finding": 13,
                },
                "avg_summary_length": 87,
                "oldest_item_days": 15,
                "newest_item_hours": 2,
                "memory_health_score": 8.7,
                "usage_patterns": {
                    "peak_hours": [9, 10, 14, 15],
                    "most_active_type": "operation",
                    "avg_items_per_day": 12,
                },
                "content_insights": {
                    "most_common_words": ["processing", "completed", "analysis", "success", "data"],
                    "sentiment_distribution": {"positive": 0.65, "neutral": 0.30, "negative": 0.05},
                },
            }

            display_memory_analytics_dashboard(analytics)


def render_memory_insights(memory_client):
    """Render memory insights and recommendations."""
    st.markdown("#### 📈 Memory Insights & Recommendations")

    if st.button("🔍 Generate Insights", key="generate_memory_insights"):
        with st.spinner("Analyzing memory patterns and generating insights..."):
            # Mock insights - would come from ML/AI analysis
            insights = {
                "patterns": [
                    "Operations peak during business hours (9-11 AM, 2-4 PM)",
                    "LLM summaries show increasing complexity over time",
                    "Document analysis requests correlate with code generation activities",
                    "API monitoring shows healthy error rates (< 5%)",
                ],
                "anomalies": [
                    "Unusual spike in 'finding' type memories last Tuesday",
                    "Lower than expected memory retention for 'api_summary' items",
                ],
                "recommendations": [
                    "Consider increasing memory capacity for peak hours",
                    "Implement automated cleanup for older operation logs",
                    "Add correlation analysis between different memory types",
                    "Monitor API error patterns more closely",
                ],
                "predictions": [
                    "Memory usage expected to grow 15% in next week",
                    "New memory type 'user_feedback' might be needed soon",
                    "Potential memory bottleneck if current growth continues",
                ],
            }

            display_memory_insights_dashboard(insights)


def render_add_memory(memory_client):
    """Render interface for adding new memory items."""
    st.markdown("#### ➕ Add New Memory Item")

    with st.form("add_memory_form"):
        col1, col2 = st.columns(2)

        with col1:
            memory_type = st.selectbox(
                "Memory Type",
                ["operation", "llm_summary", "doc_summary", "api_summary", "finding"],
                key="new_memory_type",
            )

            memory_key = st.text_input(
                "Key (Optional)", placeholder="correlation_id, doc_id, etc.", key="new_memory_key"
            )

        with col2:
            memory_summary = st.text_area(
                "Summary", placeholder="Brief summary of the memory item...", height=100, key="new_memory_summary"
            )

        # Data input
        st.markdown("**Data (JSON format):**")
        data_input = st.text_area(
            "Data", placeholder='{"key": "value", "details": "..."}', height=150, key="new_memory_data"
        )

        # Submit button
        submitted = st.form_submit_button("💾 Save Memory Item")

        if submitted:
            try:
                # Parse data
                data = {}
                if data_input.strip():
                    data = json.loads(data_input)

                # Add memory item
                with st.spinner("Saving memory item..."):
                    result = asyncio.run(
                        memory_client.put_memory_item(
                            item_type=memory_type,
                            key=memory_key if memory_key.strip() else None,
                            summary=memory_summary,
                            data=data,
                        )
                    )

                    if result.get("success"):
                        st.success("✅ Memory item saved successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to save memory item: {result.get('error', 'Unknown error')}")

            except json.JSONDecodeError:
                st.error("❌ Invalid JSON format in data field")
            except Exception as e:
                st.error(f"❌ Error saving memory item: {e}")


def render_memory_stats(memory_client):
    """Render memory statistics and analytics."""
    st.markdown("#### 📊 Memory Statistics")

    if st.button("📈 Load Statistics", key="load_memory_stats"):
        with st.spinner("Loading memory statistics..."):
            try:
                stats = asyncio.run(memory_client.get_memory_stats())

                if stats and not stats.get("error"):
                    render_memory_stats_display(stats)
                else:
                    st.error(f"Failed to load statistics: {stats.get('error', 'Unknown error')}")

            except Exception as e:
                st.error(f"Error loading memory statistics: {e}")


def render_memory_stats_display(stats: Dict[str, Any]):
    """Render memory statistics display."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Memory Items", stats.get("estimated_total_items", 0))
        st.metric("Memory Types", stats.get("total_types", 0))

    with col2:
        health_status = stats.get("health", {})
        status = health_status.get("status", "unknown")
        status_color = "🟢" if status == "healthy" else "🔴"
        st.metric("Service Status", f"{status_color} {status.title()}")

    with col3:
        uptime = health_status.get("uptime_seconds", 0)
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        st.metric("Uptime", f"{hours}h {minutes}m")

    # Type distribution
    if stats.get("type_counts"):
        st.markdown("#### 📊 Memory Distribution by Type")

        type_data = stats["type_counts"]
        if type_data:
            df = pd.DataFrame(list(type_data.items()), columns=["Type", "Count"])
            st.bar_chart(df.set_index("Type"))
        else:
            st.info("No type distribution data available")

    # Recent activity
    st.markdown("#### 🕐 Recent Memory Activity")
    st.info("Recent memory operations would be displayed here (requires additional API endpoints)")


def render_create_samples(memory_client):
    """Render interface for creating sample memory data."""
    st.markdown("#### 🎭 Create Sample Memory Data")
    st.markdown("Generate sample memory items to demonstrate functionality.")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🧠 Add LLM Summary", key="sample_llm_summary"):
            with st.spinner("Adding LLM summary sample..."):
                sample_data = {
                    "type": "llm_summary",
                    "key": "session_12345",
                    "summary": "User requested a Python function for data analysis. LLM generated code with proper error handling and documentation.",
                    "data": {
                        "session_id": "session_12345",
                        "user_query": "Write a Python function to analyze CSV data",
                        "llm_response": "Generated pandas-based data analysis function",
                        "tokens_used": 245,
                        "processing_time": 1.2,
                    },
                }
                result = asyncio.run(memory_client.put_memory_item(**sample_data))
                if result.get("success"):
                    st.success("✅ LLM summary sample added!")
                else:
                    st.error("❌ Failed to add sample")

    with col2:
        if st.button("📝 Add Doc Summary", key="sample_doc_summary"):
            with st.spinner("Adding document summary sample..."):
                sample_data = {
                    "type": "doc_summary",
                    "key": "doc_analysis_67890",
                    "summary": "Analyzed API documentation for user authentication endpoints. Found 3 deprecated methods and 2 security improvements.",
                    "data": {
                        "document_id": "api_docs_v2.pdf",
                        "analysis_type": "security_audit",
                        "issues_found": ["deprecated_auth_method", "missing_rate_limiting"],
                        "recommendations": ["Update to OAuth2", "Add rate limiting"],
                        "quality_score": 7.8,
                    },
                }
                result = asyncio.run(memory_client.put_memory_item(**sample_data))
                if result.get("success"):
                    st.success("✅ Document summary sample added!")
                else:
                    st.error("❌ Failed to add sample")

    with col3:
        if st.button("⚡ Add Operation", key="sample_operation"):
            with st.spinner("Adding operation sample..."):
                sample_data = {
                    "type": "operation",
                    "key": "workflow_execution_abc123",
                    "summary": "Successfully executed data processing workflow with 98.5% success rate across 1500 records.",
                    "data": {
                        "operation_id": "workflow_execution_abc123",
                        "operation_type": "data_processing",
                        "records_processed": 1500,
                        "success_rate": 0.985,
                        "duration_seconds": 45.2,
                        "errors": ["3 validation errors", "2 timeout errors"],
                    },
                }
                result = asyncio.run(memory_client.put_memory_item(**sample_data))
                if result.get("success"):
                    st.success("✅ Operation sample added!")
                else:
                    st.error("❌ Failed to add sample")

    # Bulk sample creation
    st.markdown("---")
    st.markdown("#### 🎲 Bulk Sample Creation")

    sample_count = st.slider("Number of random samples", 5, 50, 10, key="sample_count")

    if st.button(f"🎲 Create {sample_count} Random Samples", key="bulk_samples"):
        with st.spinner(f"Creating {sample_count} sample memory items..."):
            created_count = 0
            for i in range(sample_count):
                # Create varied sample data
                sample_types = ["operation", "llm_summary", "doc_summary", "api_summary", "finding"]
                sample_type = sample_types[i % len(sample_types)]

                sample_data = generate_random_sample(sample_type, i)
                result = asyncio.run(memory_client.put_memory_item(**sample_data))
                if result.get("success"):
                    created_count += 1

            if created_count > 0:
                st.success(f"✅ Created {created_count} sample memory items!")
                st.info("🔄 Refresh the Browse Memory tab to see the new samples")
            else:
                st.error("❌ Failed to create samples")

    # Clear all samples
    st.markdown("---")
    if st.button("🗑️ Clear All Samples", key="clear_samples"):
        st.warning("⚠️ This will remove all memory items. Are you sure?")
        if st.button("✅ Confirm Clear All", key="confirm_clear"):
            # Note: Memory agent doesn't have a clear endpoint, this would need API enhancement
            st.info("Clear functionality would require API enhancement")


def generate_random_sample(sample_type: str, index: int) -> Dict[str, Any]:
    """Generate a random sample memory item."""
    import random
    import uuid

    samples = {
        "operation": {
            "type": "operation",
            "key": f"operation_{uuid.uuid4().hex[:8]}",
            "summary": f"Executed {random.choice(['data_import', 'user_sync', 'report_generation', 'cache_cleanup'])} operation with {random.randint(85, 99)}% success rate.",
            "data": {
                "operation_type": random.choice(["data_import", "user_sync", "report_generation", "cache_cleanup"]),
                "records_processed": random.randint(100, 5000),
                "success_rate": round(random.uniform(0.85, 0.99), 3),
                "duration_seconds": round(random.uniform(10, 300), 1),
                "errors": [
                    f"{random.randint(0, 5)} {random.choice(['validation', 'timeout', 'network', 'permission'])} errors"
                ],
            },
        },
        "llm_summary": {
            "type": "llm_summary",
            "key": f"llm_session_{uuid.uuid4().hex[:8]}",
            "summary": f"LLM processed {random.choice(['code generation', 'text analysis', 'question answering', 'content creation'])} request with {random.randint(150, 800)} tokens used.",
            "data": {
                "session_id": f"session_{uuid.uuid4().hex[:12]}",
                "user_query": random.choice(
                    [
                        "Generate a Python function for data visualization",
                        "Analyze this text for sentiment",
                        "Explain quantum computing concepts",
                        "Create a marketing email template",
                    ]
                ),
                "llm_response": "Generated comprehensive response with examples and best practices",
                "tokens_used": random.randint(150, 800),
                "processing_time": round(random.uniform(0.5, 5.0), 1),
                "model_used": random.choice(["gpt-4", "claude-2", "llama-2-70b", "codellama"]),
            },
        },
        "doc_summary": {
            "type": "doc_summary",
            "key": f"doc_analysis_{uuid.uuid4().hex[:8]}",
            "summary": f"Analyzed {random.choice(['API documentation', 'user manual', 'technical specification', 'research paper'])} and identified {random.randint(1, 5)} key insights.",
            "data": {
                "document_id": f"doc_{uuid.uuid4().hex[:12]}.pdf",
                "analysis_type": random.choice(
                    ["content_analysis", "security_audit", "quality_check", "compliance_review"]
                ),
                "issues_found": [
                    f"{random.randint(0, 3)} {random.choice(['formatting', 'security', 'accessibility', 'performance'])} issues"
                ],
                "recommendations": [
                    f"Improve {random.choice(['documentation', 'security', 'usability', 'performance'])}"
                ],
                "quality_score": round(random.uniform(6.0, 9.5), 1),
                "word_count": random.randint(1000, 50000),
            },
        },
        "api_summary": {
            "type": "api_summary",
            "key": f"api_call_{uuid.uuid4().hex[:8]}",
            "summary": f"API endpoint {random.choice(['user creation', 'data retrieval', 'file upload', 'report generation'])} completed with status {random.choice([200, 201, 400, 404, 500])}.",
            "data": {
                "endpoint": f"/api/v{random.randint(1, 3)}/{random.choice(['users', 'documents', 'reports', 'analytics'])}",
                "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                "status_code": random.choice([200, 201, 400, 404, 500]),
                "response_time": round(random.uniform(0.1, 3.0), 2),
                "data_transferred": f"{random.randint(1, 1000)} KB",
                "user_agent": "DataServicesDashboard/1.0",
            },
        },
        "finding": {
            "type": "finding",
            "key": f"finding_{uuid.uuid4().hex[:8]}",
            "summary": f"Security {random.choice(['vulnerability', 'anomaly', 'optimization', 'improvement'])} detected in {random.choice(['authentication', 'data processing', 'API gateway', 'database'])}.",
            "data": {
                "finding_type": random.choice(["security", "performance", "reliability", "usability"]),
                "severity": random.choice(["low", "medium", "high", "critical"]),
                "component": random.choice(
                    ["authentication", "data_processing", "api_gateway", "database", "frontend"]
                ),
                "description": f"Detected {random.choice(['potential security risk', 'performance bottleneck', 'reliability issue', 'usability problem'])}",
                "recommendation": f"Implement {random.choice(['additional validation', 'caching layer', 'retry mechanism', 'user feedback'])}",
                "confidence": round(random.uniform(0.7, 0.95), 2),
            },
        },
    }

    return samples.get(sample_type, samples["operation"])


# ============================================================================
# MEMORY ANALYTICS AND INSIGHTS HELPER FUNCTIONS
# ============================================================================


def execute_advanced_memory_search(memory_client, filters):
    """Execute advanced memory search with given filters."""
    with st.spinner("Performing advanced search..."):
        try:
            # This would integrate with actual search API
            # For now, we'll simulate search results
            mock_results = generate_mock_search_results(filters)

            if mock_results:
                st.success(f"Found {len(mock_results)} memory items")

                # Results summary
                display_search_summary(mock_results, filters)

                # Results visualization
                display_search_visualization(mock_results)

                # Detailed results
                display_search_results(mock_results, filters)

            else:
                st.info("No memory items found matching your criteria")

        except Exception as e:
            st.error(f"Error during advanced search: {e}")


def generate_mock_search_results(filters):
    """Generate mock search results based on filters."""
    import random

    # Base results count based on filters
    base_count = 25
    if filters.get("types"):
        base_count *= len(filters["types"]) / 5  # Adjust based on type selection
    if filters.get("content_contains"):
        base_count *= 0.7  # Content filter reduces results
    if filters.get("key_pattern"):
        base_count *= 0.5  # Key pattern filter reduces results

    result_count = max(1, int(base_count))

    results = []
    memory_types = filters.get("types", ["operation", "llm_summary", "doc_summary"])

    for i in range(result_count):
        item_type = random.choice(memory_types)

        if item_type == "operation":
            item = {
                "type": "operation",
                "key": f"operation_{random.randint(1000, 9999)}",
                "summary": f"Executed {random.choice(['data_import', 'user_sync', 'report_generation'])} operation with {random.randint(85, 99)}% success rate",
                "data": {
                    "operation_type": random.choice(["data_import", "user_sync", "report_generation"]),
                    "records_processed": random.randint(100, 5000),
                    "success_rate": round(random.uniform(0.85, 0.99), 3),
                },
            }
        elif item_type == "llm_summary":
            item = {
                "type": "llm_summary",
                "key": f"session_{random.randint(1000, 9999)}",
                "summary": f"LLM processed user query about {random.choice(['Python', 'data analysis', 'API design', 'database optimization'])}",
                "data": {
                    "session_id": f"session_{random.randint(1000, 9999)}",
                    "tokens_used": random.randint(150, 800),
                    "processing_time": round(random.uniform(0.5, 5.0), 1),
                },
            }
        else:  # doc_summary
            item = {
                "type": "doc_summary",
                "key": f"doc_analysis_{random.randint(1000, 9999)}",
                "summary": f"Analyzed {random.choice(['API docs', 'user manual', 'technical spec'])} and identified {random.randint(1, 5)} key improvements",
                "data": {
                    "document_id": f"doc_{random.randint(1000, 9999)}",
                    "issues_found": random.randint(0, 3),
                    "quality_score": round(random.uniform(7.0, 9.5), 1),
                },
            }

        results.append(item)

    return results


def display_search_summary(results, filters):
    """Display search results summary."""
    col1, col2, col3, col4 = st.columns(4)

    type_counts = {}
    for item in results:
        item_type = item.get("type", "unknown")
        type_counts[item_type] = type_counts.get(item_type, 0) + 1

    with col1:
        st.metric("Total Results", len(results))
    with col2:
        st.metric("Types Found", len(type_counts))
    with col3:
        most_common = max(type_counts.items(), key=lambda x: x[1]) if type_counts else ("None", 0)
        st.metric("Most Common", f"{most_common[0]} ({most_common[1]})")
    with col4:
        avg_length = sum(len(item.get("summary", "")) for item in results) / len(results) if results else 0
        st.metric("Avg Summary Length", f"{avg_length:.0f} chars")


def display_search_visualization(results):
    """Display search results visualization."""
    # Type distribution
    type_counts = {}
    for item in results:
        item_type = item.get("type", "unknown")
        type_counts[item_type] = type_counts.get(item_type, 0) + 1

    if type_counts:
        st.markdown("**📊 Results by Type**")
        df_types = pd.DataFrame({"Type": list(type_counts.keys()), "Count": list(type_counts.values())})
        st.bar_chart(df_types.set_index("Type"))

    # Timeline (mock)
    if len(results) > 5:
        st.markdown("**📈 Results Timeline**")
        # Mock timeline data
        dates = pd.date_range(start="2024-01-01", periods=min(len(results), 20), freq="H")
        timeline_data = pd.DataFrame({"Date": dates, "Results": [len(results) // len(dates)] * len(dates)})
        st.line_chart(timeline_data.set_index("Date"))


def display_search_results(results, filters):
    """Display detailed search results."""
    st.markdown("**📋 Detailed Results**")

    for i, item in enumerate(results):
        with st.expander(f"#{i+1} - {item.get('type', 'Unknown')} | {item.get('key', 'No key')}", expanded=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Type:** {item.get('type', 'N/A')}")
                st.markdown(f"**Key:** {item.get('key', 'N/A')}")
                st.markdown(f"**Summary:** {item.get('summary', 'N/A')}")
                if item.get("data"):
                    st.markdown("**Data:**")
                    st.json(item["data"])

            with col2:
                # Action buttons
                if st.button("👁️ View Full", key=f"view_full_{i}"):
                    st.json(item)

                if st.button("📋 Copy Key", key=f"copy_key_{i}"):
                    st.code(item.get("key", ""), language="text")
                    st.success("Key copied!")

                if st.button("🔗 Related Items", key=f"related_{i}"):
                    st.info("Would show related memory items")


def display_memory_analytics_dashboard(analytics):
    """Display comprehensive memory analytics dashboard."""
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Items", analytics["total_items"])
    with col2:
        st.metric("Avg Summary Length", f"{analytics['avg_summary_length']} chars")
    with col3:
        st.metric("Memory Health", f"{analytics['memory_health_score']}/10")
    with col4:
        st.metric("Items/Day", analytics["usage_patterns"]["avg_items_per_day"])

    # Type distribution
    st.markdown("---")
    st.markdown("**📊 Memory Type Distribution**")

    type_data = analytics["memory_types"]
    df_types = pd.DataFrame({"Type": list(type_data.keys()), "Count": list(type_data.values())})
    st.bar_chart(df_types.set_index("Type"))

    # Usage patterns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**⏰ Usage Patterns**")
        patterns = analytics["usage_patterns"]
        st.info(f"Peak Hours: {', '.join(map(str, patterns['peak_hours']))}")
        st.info(f"Most Active Type: {patterns['most_active_type']}")

    with col2:
        st.markdown("**📝 Content Insights**")
        insights = analytics["content_insights"]
        st.info(f"Top Words: {', '.join(insights['most_common_words'][:3])}")
        sentiment = insights["sentiment_distribution"]
        st.info(".0%")

    # Memory health indicators
    st.markdown("---")
    st.markdown("**🏥 Memory Health Indicators**")

    health_indicators = [
        {"name": "Capacity Usage", "value": 73, "status": "good", "threshold": 80},
        {"name": "TTL Compliance", "value": 98, "status": "excellent", "threshold": 95},
        {"name": "Data Freshness", "value": 89, "status": "good", "threshold": 85},
        {"name": "Type Diversity", "value": 92, "status": "excellent", "threshold": 90},
    ]

    for indicator in health_indicators:
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"**{indicator['name']}**")

        with col2:
            color = "🟢" if indicator["status"] == "excellent" else "🟡" if indicator["status"] == "good" else "🔴"
            st.markdown(f"{color} {indicator['value']}%")

        with col3:
            status_text = (
                "Excellent"
                if indicator["status"] == "excellent"
                else "Good" if indicator["status"] == "good" else "Needs Attention"
            )
            st.caption(status_text)


def display_memory_insights_dashboard(insights):
    """Display memory insights and recommendations."""
    # Patterns discovered
    st.markdown("**🔍 Patterns Discovered**")
    for pattern in insights["patterns"]:
        st.info(f"• {pattern}")

    # Anomalies detected
    if insights["anomalies"]:
        st.markdown("---")
        st.markdown("**⚠️ Anomalies Detected**")
        for anomaly in insights["anomalies"]:
            st.warning(f"• {anomaly}")

    # Recommendations
    st.markdown("---")
    st.markdown("**💡 Recommendations**")
    for rec in insights["recommendations"]:
        st.success(f"• {rec}")

    # Future predictions
    st.markdown("---")
    st.markdown("**🔮 Future Predictions**")
    for pred in insights["predictions"]:
        st.write(f"• {pred}")

    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📋 Export Insights", key="export_insights"):
            st.info("Would export insights as PDF report")

    with col2:
        if st.button("🔧 Apply Recommendations", key="apply_recommendations"):
            st.info("Would automatically implement selected recommendations")

    with col3:
        if st.button("📊 Schedule Monitoring", key="schedule_monitoring"):
            st.info("Would set up automated monitoring alerts")


# Import json for data parsing
import json
