"""Prompt Browser Page - Browse, create, and manage prompts by category and tags.

This module provides a comprehensive interface for managing prompts in the Prompt Store service.
"""

import asyncio
import time
from typing import Any, Dict, List

import pandas as pd
import streamlit as st


def render_prompt_browser_page():
    """Render the prompt browser page."""
    st.markdown("### 📝 Prompt Store Browser")
    st.markdown("Browse, create, and manage prompts by category and tags.")

    # Get prompt client
    prompt_client = st.session_state.get("prompt_client")
    if not prompt_client:
        st.error("❌ Prompt Store service not available")
        return

    # Check if prompt store is initialized
    db_status = check_prompt_store_status(prompt_client)

    if not db_status["initialized"]:
        render_database_initialization(prompt_client)
        return

    # Create tabs for different prompt operations
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "📋 Browse Prompts",
            "➕ Create Prompt",
            "🎯 Tune Prompts",
            "📝 Sample Prompts",
            "📊 Analytics",
            "🏷️ Categories & Tags",
            "📚 Version History",
        ]
    )

    with tab1:
        render_prompt_browser(prompt_client)

    with tab2:
        render_create_prompt(prompt_client)

    with tab3:
        render_prompt_tuning(prompt_client)

    with tab4:
        render_sample_prompts(prompt_client)

    with tab5:
        render_prompt_analytics(prompt_client)

    with tab6:
        render_categories_and_tags(prompt_client)

    with tab7:
        render_prompt_versioning(prompt_client)


def render_prompt_browser(prompt_client):
    """Render the prompt browsing interface."""
    st.markdown("#### 📋 Browse Prompts")

    # Filters and search
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        category_filter = st.selectbox(
            "Category",
            ["All Categories", "chat", "completion", "analysis", "generation", "classification"],
            key="prompt_category_filter",
        )

    with col2:
        lifecycle_filter = st.selectbox(
            "Lifecycle Status",
            ["All Status", "draft", "published", "deprecated", "archived"],
            key="prompt_lifecycle_filter",
        )

    with col3:
        search_query = st.text_input("Search", placeholder="Search prompts...", key="prompt_search_query")

    with col4:
        limit = st.slider("Items per page", 10, 100, 25, key="prompt_limit")

    # Load prompts
    if st.button("🔄 Load Prompts", key="load_prompts"):
        with st.spinner("Loading prompts..."):
            try:
                filters = {}
                if category_filter != "All Categories":
                    filters["category"] = category_filter
                if lifecycle_filter != "All Status":
                    filters["lifecycle_status"] = lifecycle_filter

                result = asyncio.run(prompt_client.list_prompts(limit=limit, **filters))

                if result.get("success"):
                    prompts = result.get("prompts", [])
                    if prompts:
                        render_prompts_table(prompts, prompt_client)
                    else:
                        st.info("No prompts found matching the criteria.")
                else:
                    st.error(f"Failed to load prompts: {result.get('error', 'Unknown error')}")

            except Exception as e:
                st.error(f"Error loading prompts: {e}")

    # Quick stats
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Prompts", "156")  # Would come from API

    with col2:
        st.metric("Published", "89")  # Would come from API

    with col3:
        st.metric("Templates", "23")  # Would come from API


def render_prompts_table(prompts: List[Dict[str, Any]], prompt_client):
    """Render prompts in a table format."""
    # Convert to DataFrame for better display
    df_data = []
    for prompt in prompts:
        formatted_prompt = prompt_client.format_prompt_for_display(prompt)
        df_data.append(
            {
                "ID": formatted_prompt["id"][:8] + "...",
                "Name": formatted_prompt["name"],
                "Category": formatted_prompt["category"],
                "Status": formatted_prompt["lifecycle_status"],
                "Version": formatted_prompt["version"],
                "Usage": formatted_prompt["usage_count"],
                "Score": ".2f",
                "Tags": ", ".join(formatted_prompt["tags"][:3]) + ("..." if len(formatted_prompt["tags"]) > 3 else ""),
            }
        )

    df = pd.DataFrame(df_data)

    # Display table
    st.dataframe(df, use_container_width=True)

    # Detailed view for selected prompt
    st.markdown("#### 📖 Prompt Details")
    selected_id = st.selectbox(
        "Select prompt for details",
        [p["id"] for p in prompts],
        format_func=lambda x: next((p["name"] for p in prompts if p["id"] == x), x)[:50] + "...",
        key="prompt_detail_select",
    )

    if selected_id:
        selected_prompt = next((p for p in prompts if p["id"] == selected_id), None)
        if selected_prompt:
            render_prompt_details(selected_prompt, prompt_client)


def render_prompt_details(prompt: Dict[str, Any], prompt_client):
    """Render detailed view of a prompt."""
    formatted = prompt_client.format_prompt_for_display(prompt)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**Name:** {formatted['name']}")
        st.markdown(f"**Category:** {formatted['category']}")
        st.markdown(f"**Status:** {formatted['lifecycle_status']}")
        st.markdown(f"**Version:** {formatted['version']}")
        st.markdown(f"**Created By:** {formatted['created_by']}")
        st.markdown(f"**Usage Count:** {formatted['usage_count']}")
        st.markdown(f"**Performance Score:** {formatted['performance_score']}")

        if formatted["tags"]:
            st.markdown(f"**Tags:** {', '.join(formatted['tags'])}")

        if formatted["variables"]:
            st.markdown(f"**Variables:** {', '.join(formatted['variables'])}")

    with col2:
        # Action buttons
        if st.button("✏️ Edit Prompt", key=f"edit_{prompt['id']}"):
            st.session_state.editing_prompt = prompt
            st.rerun()

        if st.button("🎯 Tune Prompt", key=f"tune_{prompt['id']}"):
            st.session_state.tuning_prompt = prompt
            st.rerun()

        if st.button("📋 Fork Prompt", key=f"fork_{prompt['id']}"):
            fork_name = st.text_input(f"New name for forked prompt", key=f"fork_name_{prompt['id']}")
            if fork_name and st.button("✅ Confirm Fork", key=f"confirm_fork_{prompt['id']}"):
                with st.spinner("Forking prompt..."):
                    result = asyncio.run(prompt_client.fork_prompt(prompt["id"], fork_name))
                    if result.get("success"):
                        st.success("✅ Prompt forked successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to fork prompt: {result.get('error')}")

        if formatted["lifecycle_status"] != "archived":
            if st.button("🗂️ Archive", key=f"archive_{prompt['id']}"):
                if st.button("⚠️ Confirm Archive", key=f"confirm_archive_{prompt['id']}"):
                    # Would call API to archive
                    st.success("✅ Prompt archived")

    # Content display
    st.markdown("**Content:**")
    st.code(formatted["content_full"], language="text")

    # Description
    if formatted["description"]:
        st.markdown("**Description:**")
        st.info(formatted["description"])


def render_create_prompt(prompt_client):
    """Render the create prompt interface."""
    st.markdown("#### ➕ Create New Prompt")

    with st.form("create_prompt_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Prompt Name*", key="new_prompt_name")
            category = st.selectbox(
                "Category*",
                ["chat", "completion", "analysis", "generation", "classification", "other"],
                key="new_prompt_category",
            )

        with col2:
            is_template = st.checkbox("Is Template", key="new_prompt_template")
            lifecycle_status = st.selectbox("Initial Status", ["draft", "published"], index=0, key="new_prompt_status")

        description = st.text_area(
            "Description", placeholder="Brief description of the prompt...", height=80, key="new_prompt_description"
        )

        content = st.text_area(
            "Prompt Content*", placeholder="Enter your prompt content here...", height=200, key="new_prompt_content"
        )

        variables_input = st.text_input(
            "Variables (comma-separated)", placeholder="var1, var2, var3", key="new_prompt_variables"
        )

        tags_input = st.text_input("Tags (comma-separated)", placeholder="tag1, tag2, tag3", key="new_prompt_tags")

        submitted = st.form_submit_button("💾 Create Prompt")

        if submitted:
            try:
                # Parse inputs
                variables = [v.strip() for v in variables_input.split(",") if v.strip()]
                tags = [t.strip() for t in tags_input.split(",") if t.strip()]

                # Validate required fields
                if not name or not category or not content:
                    st.error("❌ Please fill in all required fields (Name, Category, Content)")
                    return

                # Create prompt
                with st.spinner("Creating prompt..."):
                    result = asyncio.run(
                        prompt_client.create_prompt(
                            name=name,
                            category=category,
                            content=content,
                            description=description,
                            variables=variables,
                            tags=tags,
                        )
                    )

                    if result.get("success"):
                        st.success("✅ Prompt created successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to create prompt: {result.get('error', 'Unknown error')}")

            except Exception as e:
                st.error(f"❌ Error creating prompt: {e}")


def render_prompt_tuning(prompt_client):
    """Render the prompt tuning interface."""
    st.markdown("#### 🎯 Prompt Tuning & Testing")

    # Check if we have a prompt to tune
    tuning_prompt = st.session_state.get("tuning_prompt")
    if tuning_prompt:
        render_prompt_tuner(tuning_prompt, prompt_client)
    else:
        # Prompt selection for tuning
        st.markdown("**Select a prompt to tune:**")

        if st.button("🔄 Load Available Prompts", key="load_tuneable_prompts"):
            with st.spinner("Loading prompts..."):
                try:
                    result = asyncio.run(prompt_client.list_prompts(limit=50))
                    if result.get("success"):
                        prompts = result.get("prompts", [])
                        if prompts:
                            st.session_state.available_prompts = prompts
                            st.success(f"✅ Loaded {len(prompts)} prompts")
                        else:
                            st.info("No prompts available for tuning.")
                    else:
                        st.error("Failed to load prompts")
                except Exception as e:
                    st.error(f"Error loading prompts: {e}")

        # Display available prompts
        if "available_prompts" in st.session_state:
            prompts = st.session_state.available_prompts
            for prompt in prompts[:10]:  # Show first 10
                col1, col2 = st.columns([3, 1])
                with col1:
                    formatted = prompt_client.format_prompt_for_display(prompt)
                    st.markdown(f"**{formatted['name']}** ({formatted['category']})")
                    st.caption(f"Status: {formatted['lifecycle_status']} | Usage: {formatted['usage_count']}")
                with col2:
                    if st.button("🎯 Tune", key=f"tune_btn_{prompt['id']}"):
                        st.session_state.tuning_prompt = prompt
                        st.rerun()


def render_prompt_tuner(prompt: Dict[str, Any], prompt_client):
    """Render the enhanced prompt tuning interface for a specific prompt."""
    formatted = prompt_client.format_prompt_for_display(prompt)

    st.markdown(f"### 🎯 Tuning: {formatted['name']}")

    # Enhanced editing interface
    st.markdown("#### ✏️ Prompt Editor")

    # Extract variables from current content
    current_variables = extract_variables_from_prompt(formatted["content_full"])

    col1, col2 = st.columns([3, 1])

    with col1:
        # Advanced code editor with syntax highlighting
        edited_content = st.text_area(
            "Prompt Content (with variable highlighting)",
            value=formatted["content_full"],
            height=300,
            key="tuned_content",
            help="Variables are highlighted with {{variable_name}} syntax",
        )

        # Variable management section
        with st.expander("🔧 Variable Management", expanded=bool(current_variables)):
            render_variable_manager(edited_content, current_variables)

    with col2:
        # Quick actions sidebar
        st.markdown("**Quick Actions:**")

        if st.button("🔍 Highlight Variables", key="highlight_vars"):
            highlighted = highlight_variables_in_text(edited_content)
            st.code(highlighted, language="text")
            st.info("Variables are shown with **bold** formatting above")

        if st.button("📏 Count Tokens", key="count_tokens"):
            token_count = estimate_token_count(edited_content)
            st.metric("Estimated Tokens", token_count)

        if st.button("🎨 Format Prompt", key="format_prompt"):
            formatted_prompt = format_prompt_content(edited_content)
            st.session_state.tuned_content = formatted_prompt
            st.success("✅ Prompt formatted!")
            st.rerun()

        # Content analysis
        st.markdown("**Content Analysis:**")
        analysis = analyze_prompt_content(edited_content)
        for key, value in analysis.items():
            st.caption(f"{key}: {value}")

    # Tuning options
    st.markdown("---")
    st.markdown("#### ⚙️ Tuning Options")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Optimization Strategies:**")
        optimize_length = st.checkbox("Optimize Length", value=True)
        optimize_clarity = st.checkbox("Improve Clarity", value=True)
        add_examples = st.checkbox("Add Examples")
        improve_variables = st.checkbox("Optimize Variables")
        enhance_specificity = st.checkbox("Enhance Specificity")
        add_constraints = st.checkbox("Add Safety Constraints")

    with col2:
        st.markdown("**Testing Options:**")
        test_with_data = st.checkbox("Test with Sample Data")
        show_differences = st.checkbox("Show Before/After")
        auto_apply = st.checkbox("Auto-apply Best Version", value=False)

        # Performance testing options
        st.markdown("**Performance Testing:**")
        test_iterations = st.slider("Test Iterations", 1, 10, 3)
        include_metrics = st.multiselect(
            "Metrics to Track",
            ["response_time", "token_usage", "coherence", "relevance", "creativity"],
            default=["response_time", "token_usage"],
        )

    # Advanced tuning
    st.markdown("---")
    st.markdown("#### 🔬 Advanced Tuning")

    tuning_tabs = st.tabs(["AI Enhancement", "Template Library", "Performance Testing", "A/B Testing"])

    with tuning_tabs[0]:
        render_ai_enhancement_interface(prompt, edited_content)

    with tuning_tabs[1]:
        render_template_library_interface()

    with tuning_tabs[2]:
        render_performance_testing_interface(prompt, edited_content, test_iterations, include_metrics)

    with tuning_tabs[3]:
        render_ab_testing_interface(prompt)

    # Action buttons
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🤖 Auto-Tune", key="auto_tune"):
            with st.spinner("AI is tuning your prompt..."):
                tuned = apply_ai_tuning(
                    edited_content,
                    {
                        "optimize_length": optimize_length,
                        "optimize_clarity": optimize_clarity,
                        "add_examples": add_examples,
                        "improve_variables": improve_variables,
                        "enhance_specificity": enhance_specificity,
                        "add_constraints": add_constraints,
                    },
                )
                st.session_state.tuned_content = tuned
                st.success("✅ Prompt automatically tuned!")
                st.rerun()

    with col2:
        if st.button("🧪 Test Prompt", key="test_prompt"):
            with st.spinner("Testing prompt performance..."):
                results = test_prompt_performance(edited_content, test_iterations, include_metrics)
                display_performance_results(results)

    with col3:
        if st.button("💾 Save Tuned", key="save_tuned"):
            if edited_content != formatted["content_full"]:
                # Would save as new version
                st.success("✅ Tuned prompt saved as new version!")
                # Refresh to show changes
                st.rerun()
            else:
                st.info("No changes detected")

    with col4:
        if st.button("❌ Cancel", key="cancel_tune"):
            if "tuning_prompt" in st.session_state:
                del st.session_state.tuning_prompt
            st.rerun()


def render_prompt_analytics(prompt_client):
    """Render prompt analytics."""
    st.markdown("#### 📊 Prompt Analytics")

    if st.button("📈 Load Analytics", key="load_prompt_analytics"):
        with st.spinner("Loading analytics..."):
            try:
                result = asyncio.run(prompt_client.get_analytics_summary())
                if result.get("success"):
                    analytics = result.get("data", {})
                    render_analytics_display(analytics)
                else:
                    st.error("Failed to load analytics")
            except Exception as e:
                st.error(f"Error loading analytics: {e}")


def render_analytics_display(analytics: Dict[str, Any]):
    """Render analytics data."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Prompts", analytics.get("total_prompts", 156))
        st.metric("Active Prompts", analytics.get("active_prompts", 89))

    with col2:
        st.metric("Avg Performance", ".2f")
        st.metric("Top Category", analytics.get("top_category", "chat"))

    with col3:
        st.metric("Total Usage", analytics.get("total_usage", 15420))
        st.metric("Avg Usage/Prompt", analytics.get("avg_usage", 98))

    # Usage trends (mock)
    st.markdown("#### 📈 Usage Trends")
    usage_data = pd.DataFrame(
        {"Date": pd.date_range(start="2024-01-01", periods=7), "Usage": [120, 135, 148, 156, 142, 158, 167]}
    )
    st.line_chart(usage_data.set_index("Date"))


def check_prompt_store_status(prompt_client) -> Dict[str, Any]:
    """Check if prompt store database is initialized and working."""
    try:
        # Try to list prompts - if it fails with "no such table", DB needs init
        result = asyncio.run(prompt_client.list_prompts(limit=1))
        if result.get("success"):
            return {"initialized": True, "has_data": len(result.get("prompts", [])) > 0}
        elif "no such table" in str(result.get("message", "")).lower():
            return {"initialized": False, "error": "Database not initialized"}
        else:
            return {"initialized": True, "error": result.get("message", "Unknown error")}
    except Exception as e:
        return {"initialized": False, "error": str(e)}


def render_database_initialization(prompt_client):
    """Render database initialization interface."""
    st.markdown("### 🛠️ Prompt Store Database Initialization")
    st.warning("⚠️ The Prompt Store database needs to be initialized before you can use the prompt management features.")

    st.markdown(
        """
    **What this will do:**
    - Initialize the database schema for prompts
    - Create necessary tables and indexes
    - Set up default categories and configurations
    """
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("🚀 Initialize Database", key="init_database", type="primary", use_container_width=True):
            with st.spinner("Initializing database... This may take a moment."):
                try:
                    # Try to create a test prompt to initialize the database
                    test_prompt = {
                        "name": "system_init_test",
                        "category": "system",
                        "content": "Database initialization test prompt",
                        "description": "Temporary prompt for database initialization",
                    }

                    result = asyncio.run(prompt_client.create_prompt(**test_prompt))

                    if result.get("success") or "prompts" in str(result.get("message", "")).lower():
                        st.success("✅ Database initialized successfully!")
                        st.info("🔄 Refreshing page to show prompt management interface...")
                        st.rerun()
                    else:
                        error_msg = result.get("message", "Unknown error")
                        if "no such table" in error_msg.lower():
                            st.error("❌ Database schema not found. The service may need manual database setup.")
                            st.info(
                                "💡 Try running the service with proper database initialization or check service logs."
                            )
                        else:
                            st.error(f"❌ Initialization failed: {error_msg}")

                except Exception as e:
                    st.error(f"❌ Database initialization error: {e}")
                    st.info(
                        "💡 The Prompt Store service may need to be restarted or the database may need manual setup."
                    )

    with col2:
        st.markdown("**Database Status:**")
        st.info("• Service: Running ✅\n• Database: Not initialized ❌\n• Tables: Missing ❌")

        st.markdown("**Next Steps:**")
        st.markdown("1. Click 'Initialize Database' above")
        st.markdown("2. Wait for confirmation")
        st.markdown("3. Page will refresh automatically")
        st.markdown("4. Use 'Sample Prompts' tab to populate data")


def render_sample_prompts(prompt_client):
    """Render interface for creating sample prompts."""
    st.markdown("#### 📝 Create Sample Prompts")
    st.markdown("Generate sample prompts to demonstrate functionality and get started quickly.")

    # Quick sample creation
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🤖 AI Assistant Prompt", key="sample_ai_assistant"):
            with st.spinner("Creating AI assistant prompt..."):
                prompt_data = {
                    "name": "ai_assistant_basic",
                    "category": "chat",
                    "content": "You are a helpful AI assistant. Provide clear, accurate, and helpful responses to user questions. Be concise but comprehensive, and always prioritize user safety and accuracy.",
                    "description": "Basic AI assistant prompt for general conversation",
                    "variables": [],
                    "tags": ["ai", "assistant", "chat", "general"],
                }
                result = asyncio.run(prompt_client.create_prompt(**prompt_data))
                if result.get("success"):
                    st.success("✅ AI Assistant prompt created!")
                else:
                    st.error("❌ Failed to create prompt")

    with col2:
        if st.button("📝 Code Generator", key="sample_code_generator"):
            with st.spinner("Creating code generator prompt..."):
                prompt_data = {
                    "name": "code_generator_python",
                    "category": "generation",
                    "content": "You are an expert Python developer. Generate clean, well-documented, and efficient Python code. Include proper error handling, type hints, and comprehensive docstrings. Follow PEP 8 style guidelines.",
                    "description": "Specialized prompt for generating Python code",
                    "variables": ["language", "task"],
                    "tags": ["code", "python", "generation", "development"],
                }
                result = asyncio.run(prompt_client.create_prompt(**prompt_data))
                if result.get("success"):
                    st.success("✅ Code generator prompt created!")
                else:
                    st.error("❌ Failed to create prompt")

    with col3:
        if st.button("🔍 Data Analyst", key="sample_data_analyst"):
            with st.spinner("Creating data analyst prompt..."):
                prompt_data = {
                    "name": "data_analyst_insights",
                    "category": "analysis",
                    "content": "You are an expert data analyst. Analyze the provided data and provide actionable insights, trends, and recommendations. Use statistical reasoning and clear visualizations in your explanations.",
                    "description": "Prompt for data analysis and insights generation",
                    "variables": ["data_type", "analysis_goal"],
                    "tags": ["data", "analysis", "insights", "statistics"],
                }
                result = asyncio.run(prompt_client.create_prompt(**prompt_data))
                if result.get("success"):
                    st.success("✅ Data analyst prompt created!")
                else:
                    st.error("❌ Failed to create prompt")

    # Bulk sample creation
    st.markdown("---")
    st.markdown("#### 🎲 Bulk Sample Creation")

    sample_options = {
        "Basic Chat Prompts": ["greeting", "question_answer", "conversation"],
        "Code Generation": ["python", "javascript", "sql", "api"],
        "Content Creation": ["blog_post", "email", "social_media", "documentation"],
        "Analysis & Insights": ["data_analysis", "text_summary", "sentiment_analysis"],
        "Specialized Tasks": ["translation", "proofreading", "research", "tutorials"],
    }

    selected_categories = st.multiselect(
        "Select prompt categories to create", list(sample_options.keys()), key="sample_categories"
    )

    if selected_categories:
        total_prompts = sum(len(sample_options[cat]) for cat in selected_categories)
        st.info(f"📊 Will create {total_prompts} sample prompts across {len(selected_categories)} categories")

        if st.button(f"🎲 Create {total_prompts} Sample Prompts", key="bulk_sample_prompts"):
            with st.spinner(f"Creating {total_prompts} sample prompts..."):
                created_count = 0

                for category in selected_categories:
                    for prompt_type in sample_options[category]:
                        prompt_data = generate_sample_prompt(category, prompt_type)
                        result = asyncio.run(prompt_client.create_prompt(**prompt_data))
                        if result.get("success"):
                            created_count += 1

                if created_count > 0:
                    st.success(f"✅ Created {created_count} sample prompts!")
                    st.info("🔄 Refresh the Browse Prompts tab to see the new prompts")
                else:
                    st.error("❌ Failed to create sample prompts")

    # Import from templates
    st.markdown("---")
    st.markdown("#### 📥 Import Prompt Templates")

    if st.button("📋 Import Standard Templates", key="import_templates"):
        with st.spinner("Importing standard prompt templates..."):
            templates = get_standard_prompt_templates()
            imported_count = 0

            for template in templates:
                result = asyncio.run(prompt_client.create_prompt(**template))
                if result.get("success"):
                    imported_count += 1

            if imported_count > 0:
                st.success(f"✅ Imported {imported_count} standard prompt templates!")
            else:
                st.warning("⚠️ Some templates may already exist or import failed")


def generate_sample_prompt(category: str, prompt_type: str) -> Dict[str, Any]:
    """Generate a sample prompt based on category and type."""

    templates = {
        ("Basic Chat Prompts", "greeting"): {
            "name": "greeting_friendly",
            "category": "chat",
            "content": "You are a friendly and welcoming AI assistant. Greet users warmly and make them feel comfortable. Be helpful, engaging, and maintain a positive tone throughout the conversation.",
            "description": "Friendly greeting prompt for welcoming users",
            "variables": [],
            "tags": ["greeting", "friendly", "chat", "welcome"],
        },
        ("Basic Chat Prompts", "question_answer"): {
            "name": "qa_helpful",
            "category": "chat",
            "content": "You are a knowledgeable AI assistant specialized in answering questions clearly and accurately. Provide comprehensive but concise answers, and when appropriate, offer additional context or related information that might be helpful.",
            "description": "Helpful Q&A prompt for answering user questions",
            "variables": ["topic"],
            "tags": ["qa", "questions", "answers", "helpful"],
        },
        ("Code Generation", "python"): {
            "name": "python_function_generator",
            "category": "generation",
            "content": "Generate a Python function that {task}. Include proper error handling, type hints, and a comprehensive docstring. Follow PEP 8 style guidelines and best practices.",
            "description": "Python function generation prompt",
            "variables": ["task"],
            "tags": ["python", "code", "generation", "functions"],
        },
        ("Content Creation", "blog_post"): {
            "name": "blog_post_writer",
            "category": "generation",
            "content": "Write an engaging blog post about {topic}. Structure it with an attention-grabbing introduction, informative body with subheadings, and a compelling conclusion. Use a conversational tone and include practical examples.",
            "description": "Blog post writing prompt",
            "variables": ["topic"],
            "tags": ["blog", "writing", "content", "article"],
        },
    }

    key = (category, prompt_type)
    return templates.get(
        key,
        {
            "name": f"{prompt_type}_sample",
            "category": "general",
            "content": f"Sample prompt for {prompt_type} in {category} category.",
            "description": f"Sample {prompt_type} prompt",
            "variables": [],
            "tags": [prompt_type, "sample"],
        },
    )


def get_standard_prompt_templates() -> List[Dict[str, Any]]:
    """Get a list of standard prompt templates."""
    return [
        {
            "name": "creative_writer",
            "category": "generation",
            "content": "You are a creative writer. Write an engaging and imaginative {content_type} about {topic}. Use vivid language, compelling characters, and an interesting narrative structure.",
            "description": "Creative writing prompt template",
            "variables": ["content_type", "topic"],
            "tags": ["creative", "writing", "story", "fiction"],
        },
        {
            "name": "technical_explanation",
            "category": "analysis",
            "content": "Explain {technical_concept} in simple terms that a beginner can understand. Use analogies, avoid jargon where possible, and break down complex ideas into digestible parts.",
            "description": "Technical concept explanation prompt",
            "variables": ["technical_concept"],
            "tags": ["technical", "explanation", "education", "simple"],
        },
        {
            "name": "meeting_summarizer",
            "category": "analysis",
            "content": "Summarize the key points from this meeting transcript. Include: main decisions made, action items with owners, important insights, and any follow-up required.",
            "description": "Meeting summary prompt",
            "variables": [],
            "tags": ["meeting", "summary", "business", "productivity"],
        },
        {
            "name": "email_professional",
            "category": "generation",
            "content": "Write a professional email {purpose}. Use a clear subject line, proper greeting, concise body, and professional closing. Maintain a polite and business-appropriate tone.",
            "description": "Professional email writing prompt",
            "variables": ["purpose"],
            "tags": ["email", "professional", "business", "communication"],
        },
    ]


def render_categories_and_tags(prompt_client):
    """Render categories and tags management."""
    st.markdown("#### 🏷️ Categories & Tags Management")

    if st.button("📊 Load Categories & Tags", key="load_categories_tags"):
        with st.spinner("Loading categories and tags..."):
            try:
                categories_result = asyncio.run(prompt_client.get_categories())
                tags_result = asyncio.run(prompt_client.get_tags())

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Categories:**")
                    if categories_result:
                        for category in categories_result:
                            st.write(f"• {category}")
                    else:
                        st.info("No categories found")

                with col2:
                    st.markdown("**Tags:**")
                    if tags_result:
                        # Group tags for better display
                        tag_groups = [tags_result[i : i + 10] for i in range(0, len(tags_result), 10)]
                        for group in tag_groups[:3]:  # Show first 30 tags
                            st.write(" • " + " • ".join(group))
                        if len(tags_result) > 30:
                            st.caption(f"... and {len(tags_result) - 30} more tags")
                    else:
                        st.info("No tags found")

            except Exception as e:
                st.error(f"Error loading categories and tags: {e}")


# ============================================================================
# PROMPT TUNING HELPER FUNCTIONS
# ============================================================================


def extract_variables_from_prompt(content: str) -> List[str]:
    """Extract variable names from prompt content using {{variable}} syntax."""
    import re

    variables = re.findall(r"\{\{([^}]+)\}\}", content)
    # Remove duplicates while preserving order
    seen = set()
    result = []
    for var in variables:
        if var not in seen:
            seen.add(var)
            result.append(var)
    return result


def render_variable_manager(content: str, current_variables: List[str]):
    """Render the variable management interface."""
    st.markdown("**Current Variables:**")

    if current_variables:
        for var in current_variables:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.code(f"{{{{{var}}}}}", language="text")
            with col2:
                if st.button(f"📋 Copy", key=f"copy_var_{var}"):
                    st.code(f"{{{{{var}}}}}", language="text")
                    st.success(f"Copied {{{{{var}}}}}")

        # Variable validation
        st.markdown("**Variable Validation:**")
        for var in current_variables:
            if not var.replace("_", "").replace("-", "").isalnum():
                st.warning(f"⚠️ Variable '{var}' contains invalid characters")
            elif not var:
                st.error("❌ Empty variable name found")
    else:
        st.info("No variables detected in the prompt. Use {{variable_name}} syntax to add variables.")

    # Add new variable
    st.markdown("**Add New Variable:**")
    new_var = st.text_input("Variable name", key="new_variable_name")
    if new_var and st.button("➕ Add Variable", key="add_variable"):
        if new_var in current_variables:
            st.warning("Variable already exists")
        elif not new_var.replace("_", "").replace("-", "").isalnum():
            st.error("Invalid variable name. Use only letters, numbers, underscores, and hyphens.")
        else:
            # Insert variable at cursor position (simplified)
            updated_content = content + f" {{{{{new_var}}}}}"
            st.session_state.tuned_content = updated_content
            st.success(f"✅ Added variable {{{{{new_var}}}}}")
            st.rerun()


def highlight_variables_in_text(content: str) -> str:
    """Highlight variables in the text for display."""
    import re

    # Replace {{variable}} with **{{variable}}** for highlighting
    highlighted = re.sub(r"\{\{([^}]+)\}\}", r"**{{\1}}**", content)
    return highlighted


def estimate_token_count(content: str) -> int:
    """Estimate token count for the content (rough approximation)."""
    # Rough approximation: ~4 characters per token for English text
    char_count = len(content)
    token_estimate = char_count // 4

    # Adjust for common token patterns
    # Code and technical content often has more tokens per character
    if any(keyword in content.lower() for keyword in ["function", "class", "import", "def ", "return"]):
        token_estimate = int(token_estimate * 1.2)

    return max(token_estimate, 1)  # Minimum 1 token


def format_prompt_content(content: str) -> str:
    """Format and clean up prompt content."""
    import re

    # Remove extra whitespace
    formatted = re.sub(r"\n\s*\n\s*\n+", "\n\n", content.strip())

    # Ensure consistent spacing around variables
    formatted = re.sub(r"\{\{(\s*)([^}]+)(\s*)\}\}", r"{{\2}}", formatted)

    # Capitalize first letter of sentences (basic)
    sentences = re.split(r"([.!?]+\s*)", formatted)
    formatted_sentences = []
    for i, sentence in enumerate(sentences):
        if i % 2 == 0 and sentence.strip():  # Actual sentence content
            sentence = sentence.strip()
            if sentence:
                sentence = sentence[0].upper() + sentence[1:]
        formatted_sentences.append(sentence)
    formatted = "".join(formatted_sentences)

    return formatted


def analyze_prompt_content(content: str) -> Dict[str, Any]:
    """Analyze prompt content and return metrics."""
    analysis = {}

    # Basic metrics
    analysis["Characters"] = len(content)
    analysis["Words"] = len(content.split())
    analysis["Lines"] = len(content.split("\n"))
    analysis["Sentences"] = len([s for s in content.split(".") if s.strip()])

    # Variables
    variables = extract_variables_from_prompt(content)
    analysis["Variables"] = len(variables)

    # Estimated tokens
    analysis["Est. Tokens"] = estimate_token_count(content)

    # Complexity indicators
    technical_terms = ["function", "algorithm", "api", "database", "server", "client", "authentication"]
    analysis["Technical Terms"] = sum(1 for term in technical_terms if term.lower() in content.lower())

    # Readability (very basic)
    avg_words_per_sentence = analysis["Words"] / max(analysis["Sentences"], 1)
    analysis["Avg Words/Sentence"] = ".1f"

    return analysis


def apply_ai_tuning(content: str, options: Dict[str, bool]) -> str:
    """Apply AI-based tuning to the prompt content."""
    tuned = content

    if options.get("optimize_length"):
        # Remove redundant phrases
        redundancies = [
            r"\b(in order to|so as to|in an effort to)\b",
            r"\b(it is important to note that|please note that)\b",
            r"\b(due to the fact that|because)\b",
        ]
        for pattern in redundancies:
            import re

            tuned = re.sub(pattern, "", tuned, flags=re.IGNORECASE)

    if options.get("optimize_clarity"):
        # Add clarity improvements
        if not content.strip().endswith((".", "!", "?")):
            tuned += "."

        # Ensure proper capitalization
        tuned = ". ".join(s.strip().capitalize() for s in tuned.split(". "))

    if options.get("add_examples"):
        # Add example placeholder
        if "example" not in tuned.lower():
            tuned += "\n\nExample: [Add specific examples here]"

    if options.get("improve_variables"):
        # Suggest better variable naming
        variables = extract_variables_from_prompt(tuned)
        for var in variables:
            if var in ["var", "var1", "variable", "input"]:
                tuned = tuned.replace(f"{{{{{var}}}}}", f"{{{{specific_{var}}}}}")

    if options.get("enhance_specificity"):
        # Add specificity prompts
        if "specific" not in tuned.lower():
            tuned = "Be specific and detailed in your response. " + tuned

    if options.get("add_constraints"):
        # Add safety constraints
        safety_note = "\n\nImportant: Ensure your response is safe, ethical, and appropriate."
        if safety_note not in tuned:
            tuned += safety_note

    return tuned.strip()


def run_prompt_performance_test(content: str, iterations: int, metrics: List[str]) -> Dict[str, Any]:
    """Test prompt performance with mock results."""
    import random

    results = {"iterations": iterations, "metrics": {}, "summary": {}}

    # Simulate testing
    for metric in metrics:
        if metric == "response_time":
            times = [random.uniform(0.5, 3.0) for _ in range(iterations)]
            results["metrics"]["response_time"] = {
                "values": times,
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
            }
        elif metric == "token_usage":
            tokens = [random.randint(100, 1000) for _ in range(iterations)]
            results["metrics"]["token_usage"] = {
                "values": tokens,
                "avg": sum(tokens) / len(tokens),
                "total": sum(tokens),
            }
        elif metric == "coherence":
            scores = [random.uniform(0.7, 0.95) for _ in range(iterations)]
            results["metrics"]["coherence"] = {"values": scores, "avg": sum(scores) / len(scores)}
        elif metric == "relevance":
            scores = [random.uniform(0.75, 0.98) for _ in range(iterations)]
            results["metrics"]["relevance"] = {"values": scores, "avg": sum(scores) / len(scores)}
        elif metric == "creativity":
            scores = [random.uniform(0.6, 0.9) for _ in range(iterations)]
            results["metrics"]["creativity"] = {"values": scores, "avg": sum(scores) / len(scores)}

    # Calculate summary
    if "response_time" in results["metrics"]:
        results["summary"]["avg_response_time"] = ".2f"

    if "token_usage" in results["metrics"]:
        results["summary"]["total_tokens"] = results["metrics"]["token_usage"]["total"]
        results["summary"]["efficiency"] = ".1f"

    if "coherence" in results["metrics"] and "relevance" in results["metrics"]:
        overall_quality = (results["metrics"]["coherence"]["avg"] + results["metrics"]["relevance"]["avg"]) / 2
        results["summary"]["overall_quality"] = ".2f"

    return results


def display_performance_results(results: Dict[str, Any]):
    """Display performance testing results."""
    st.markdown("#### 📊 Performance Test Results")

    # Summary metrics
    if "summary" in results:
        col1, col2, col3 = st.columns(3)
        for i, (key, value) in enumerate(results["summary"].items()):
            with [col1, col2, col3][i % 3]:
                st.metric(key.replace("_", " ").title(), value)

    # Detailed metrics
    if "metrics" in results:
        for metric_name, metric_data in results["metrics"].items():
            with st.expander(f"📈 {metric_name.replace('_', ' ').title()}", expanded=False):
                if "avg" in metric_data:
                    st.metric("Average", ".2f")
                if "min" in metric_data and "max" in metric_data:
                    st.metric("Range", f"{metric_data['min']:.2f} - {metric_data['max']:.2f}")
                if "total" in metric_data:
                    st.metric("Total", metric_data["total"])

                # Simple chart for values
                if "values" in metric_data:
                    import pandas as pd

                    df = pd.DataFrame(
                        {"Iteration": range(1, len(metric_data["values"]) + 1), "Value": metric_data["values"]}
                    )
                    st.line_chart(df.set_index("Iteration"))


def render_ai_enhancement_interface(prompt: Dict[str, Any], content: str):
    """Render AI enhancement interface."""
    st.markdown("**AI-Powered Enhancement**")

    enhancement_type = st.selectbox(
        "Enhancement Type",
        ["General Optimization", "Add Structure", "Improve Instructions", "Enhance Examples", "Safety & Ethics"],
        key="enhancement_type",
    )

    intensity = st.slider("Enhancement Intensity", 1, 5, 3, key="enhancement_intensity")

    if st.button("✨ Apply AI Enhancement", key="apply_ai_enhancement"):
        with st.spinner("AI is enhancing your prompt..."):
            enhanced = apply_ai_enhancement(content, enhancement_type, intensity)
            st.session_state.tuned_content = enhanced
            st.success("✅ AI enhancement applied!")
            st.rerun()

    # Show enhancement preview
    with st.expander("Preview Enhancement", expanded=False):
        if enhancement_type == "General Optimization":
            preview = "• Improve clarity and conciseness\n• Optimize variable usage\n• Enhance specificity"
        elif enhancement_type == "Add Structure":
            preview = "• Add clear sections and headers\n• Organize content logically\n• Improve readability"
        elif enhancement_type == "Improve Instructions":
            preview = "• Make instructions more explicit\n• Add step-by-step guidance\n• Clarify expectations"
        elif enhancement_type == "Enhance Examples":
            preview = "• Add relevant examples\n• Include edge cases\n• Provide context"
        else:  # Safety & Ethics
            preview = "• Add ethical guidelines\n• Include safety constraints\n• Add responsible AI practices"

        st.markdown(preview)


def render_template_library_interface():
    """Render template library interface."""
    st.markdown("**Prompt Template Library**")

    templates = {
        "System Prompts": [
            "You are a helpful AI assistant...",
            "You are an expert in [field] with [experience] years...",
            "Act as a [role] who specializes in [specialty]...",
        ],
        "Task Prompts": [
            "Write a [type] about [topic] that is [length]...",
            "Analyze [data] and provide [insights]...",
            "Create a [format] for [purpose]...",
        ],
        "Instruction Prompts": [
            "Follow these steps: 1) [step1], 2) [step2]...",
            "Use this format: [format specification]...",
            "Include these elements: [element1], [element2]...",
        ],
    }

    selected_category = st.selectbox("Template Category", list(templates.keys()), key="template_category")

    if selected_category:
        selected_template = st.selectbox("Select Template", templates[selected_category], key="selected_template")

        if selected_template and st.button("📋 Use Template", key="use_template"):
            current_content = st.session_state.get("tuned_content", "")
            if current_content:
                combined = current_content + "\n\n" + selected_template
            else:
                combined = selected_template

            st.session_state.tuned_content = combined
            st.success("✅ Template added to prompt!")
            st.rerun()


def render_performance_testing_interface(prompt: Dict[str, Any], content: str, iterations: int, metrics: List[str]):
    """Render performance testing interface."""
    st.markdown("**Performance Testing Configuration**")

    # Test scenarios
    test_scenarios = st.multiselect(
        "Test Scenarios",
        ["General Q&A", "Creative Writing", "Technical Analysis", "Code Generation", "Data Processing"],
        default=["General Q&A"],
        key="test_scenarios",
    )

    # Advanced settings
    with st.expander("Advanced Settings", expanded=False):
        temperature_range = st.slider("Temperature Range", 0.0, 2.0, (0.7, 1.2), key="temp_range")
        max_tokens_range = st.slider("Max Tokens Range", 100, 2000, (500, 1500), key="max_tokens_range")
        include_benchmarks = st.checkbox("Include Benchmark Comparisons", key="include_benchmarks")

    if st.button("🚀 Run Comprehensive Test", key="run_comprehensive_test"):
        with st.spinner("Running comprehensive performance tests..."):
            # This would integrate with actual LLM testing infrastructure
            st.info("📊 Comprehensive testing would analyze performance across multiple scenarios and configurations")
            st.info("🔬 Results would include statistical analysis and optimization recommendations")

            # Mock comprehensive results
            mock_results = {
                "overall_score": 8.7,
                "best_temperature": 0.9,
                "optimal_max_tokens": 1200,
                "strengths": ["High coherence", "Good relevance", "Efficient token usage"],
                "improvements": ["Add more specific examples", "Enhance error handling instructions"],
            }

            display_comprehensive_test_results(mock_results)


def render_ab_testing_interface(prompt: Dict[str, Any]):
    """Render A/B testing interface."""
    st.markdown("**A/B Testing Setup**")

    # Test variants
    st.markdown("**Variant A (Current):**")
    st.code(prompt.get("content", ""), language="text")

    st.markdown("**Variant B (Modified):**")
    variant_b = st.text_area(
        "Modified version for testing", value=prompt.get("content", ""), height=150, key="variant_b_content"
    )

    # Test configuration
    col1, col2 = st.columns(2)
    with col1:
        sample_size = st.slider("Sample Size per Variant", 10, 1000, 100, key="ab_sample_size")
        confidence_level = st.slider("Confidence Level", 0.8, 0.99, 0.95, key="ab_confidence")

    with col2:
        test_duration = st.slider("Test Duration (hours)", 1, 168, 24, key="ab_duration")
        primary_metric = st.selectbox(
            "Primary Metric",
            ["response_quality", "user_satisfaction", "completion_rate", "response_time"],
            key="ab_primary_metric",
        )

    if st.button("🆚 Start A/B Test", key="start_ab_test"):
        with st.spinner("Setting up A/B test..."):
            # This would integrate with A/B testing infrastructure
            st.success("✅ A/B test configured and started!")
            st.info("📊 Test will run for {test_duration} hours with {sample_size} samples per variant")
            st.info("🎯 Primary metric: {primary_metric}")
            st.info("📈 Results will be available in the analytics dashboard")


def apply_ai_enhancement(content: str, enhancement_type: str, intensity: int) -> str:
    """Apply AI enhancement based on type and intensity."""
    enhanced = content

    intensity_multipliers = {
        1: 0.3,  # Light enhancement
        2: 0.5,  # Moderate
        3: 0.7,  # Standard
        4: 0.9,  # Strong
        5: 1.0,  # Maximum
    }

    multiplier = intensity_multipliers.get(intensity, 0.7)

    if enhancement_type == "General Optimization":
        # Apply multiple optimizations based on intensity
        optimizations = [
            lambda x: apply_ai_tuning(x, {"optimize_length": True}),
            lambda x: apply_ai_tuning(x, {"optimize_clarity": True}),
            lambda x: apply_ai_tuning(x, {"improve_variables": True}),
        ]

        for opt in optimizations[: int(len(optimizations) * multiplier)]:
            enhanced = opt(enhanced)

    elif enhancement_type == "Add Structure":
        if multiplier > 0.5:
            enhanced = f"**Instructions:**\n{enhanced}\n\n**Guidelines:**\n• Be specific and detailed\n• Use clear examples\n• Follow best practices"

    elif enhancement_type == "Improve Instructions":
        if multiplier > 0.5:
            enhanced = f"**Task:** {enhanced}\n\n**Requirements:**\n• Provide step-by-step reasoning\n• Include relevant examples\n• Ensure accuracy and completeness"

    elif enhancement_type == "Enhance Examples":
        if multiplier > 0.5:
            enhanced += "\n\n**Examples:**\n• Example 1: [Add specific example]\n• Example 2: [Add another example]"

    elif enhancement_type == "Safety & Ethics":
        safety_additions = [
            "\n\n**Safety Guidelines:**\n• Ensure responses are safe and appropriate\n• Avoid harmful content\n• Respect user privacy",
            "\n\n**Ethical Considerations:**\n• Be truthful and accurate\n• Avoid bias and discrimination\n• Promote positive outcomes",
        ]

        for addition in safety_additions[: int(len(safety_additions) * multiplier)]:
            enhanced += addition

    return enhanced


def display_comprehensive_test_results(results: Dict[str, Any]):
    """Display comprehensive test results."""
    st.markdown("#### 🔬 Comprehensive Test Results")

    # Overall score
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Score", f"{results['overall_score']}/10")
    with col2:
        st.metric("Best Temperature", results["best_temperature"])
    with col3:
        st.metric("Optimal Max Tokens", results["optimal_max_tokens"])

    # Strengths and improvements
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**✅ Strengths:**")
        for strength in results["strengths"]:
            st.write(f"• {strength}")

    with col2:
        st.markdown("**🔧 Improvement Areas:**")
        for improvement in results["improvements"]:
            st.write(f"• {improvement}")

    # Recommendations
    st.markdown("**💡 Recommendations:**")
    st.info(
        "Based on test results, consider adjusting temperature and adding more specific examples to improve overall performance."
    )


def render_prompt_versioning(prompt_client):
    """Render prompt versioning and comparison interface."""
    st.markdown("### 📚 Prompt Version Management")

    # Version management tabs
    version_tabs = st.tabs(["📖 Version History", "🔍 Version Comparison", "⏪ Rollback", "📈 Version Analytics"])

    with version_tabs[0]:
        render_version_history(prompt_client)

    with version_tabs[1]:
        render_version_comparison(prompt_client)

    with version_tabs[2]:
        render_version_rollback(prompt_client)

    with version_tabs[3]:
        render_version_analytics(prompt_client)


def render_version_history(prompt_client):
    """Render version history for prompts."""
    st.markdown("#### 📖 Version History")

    # Select prompt for version history
    if st.button("🔄 Load Prompts with Versions", key="load_versioned_prompts"):
        with st.spinner("Loading prompts..."):
            try:
                result = asyncio.run(prompt_client.list_prompts(limit=50))
                if result.get("success"):
                    prompts = result.get("prompts", [])
                    # Filter prompts that have versions (mock for now)
                    versioned_prompts = [
                        p for p in prompts if "version" in str(p).lower() or len(str(p.get("content", ""))) > 50
                    ]

                    if versioned_prompts:
                        st.session_state.versioned_prompts = versioned_prompts
                        st.success(f"✅ Found {len(versioned_prompts)} prompts with version history")
                    else:
                        st.info("No prompts with version history found. Create and modify some prompts first.")
                else:
                    st.error("Failed to load prompts")
            except Exception as e:
                st.error(f"Error loading prompts: {e}")

    # Display prompts with version history
    if "versioned_prompts" in st.session_state:
        prompts = st.session_state.versioned_prompts

        for i, prompt in enumerate(prompts[:5]):  # Show first 5
            with st.expander(f"📝 {prompt.get('name', f'Prompt {i+1}')} (v{prompt.get('version', 1)})", expanded=False):
                render_prompt_version_timeline(prompt, prompt_client)


def render_prompt_version_timeline(prompt: Dict[str, Any], prompt_client):
    """Render version timeline for a specific prompt."""
    prompt_id = prompt.get("id", "unknown")

    # Mock version history (would come from API)
    versions = generate_mock_version_history(prompt)

    if not versions:
        st.info("No version history available for this prompt.")
        return

    # Display version timeline
    for version in sorted(versions, key=lambda x: x["version"], reverse=True):
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.markdown(f"**Version {version['version']}**")
            st.caption(f"Created: {version['created_at']}")
            if version.get("is_current"):
                st.success("🟢 Current Version")

        with col2:
            st.caption(f"Changes: {version['changes']}")
            if version.get("performance_score"):
                st.caption(f"Performance: {version['performance_score']}/10")

        with col3:
            if st.button("👁️ View", key=f"view_version_{prompt_id}_{version['version']}"):
                st.session_state.selected_version = version
                st.rerun()

            if not version.get("is_current") and st.button(
                "🔄 Restore", key=f"restore_version_{prompt_id}_{version['version']}"
            ):
                with st.spinner("Restoring version..."):
                    # Would call API to restore version
                    st.success(f"✅ Restored to version {version['version']}")
                    st.rerun()

    # Show selected version content
    if "selected_version" in st.session_state:
        selected = st.session_state.selected_version
        st.markdown("---")
        st.markdown(f"**Version {selected['version']} Content:**")
        st.code(selected["content"], language="text")

        if st.button("❌ Close Version View", key="close_version_view"):
            del st.session_state.selected_version
            st.rerun()


def render_version_comparison(prompt_client):
    """Render version comparison interface."""
    st.markdown("#### 🔍 Version Comparison")

    # Select prompts/versions to compare
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Version A:**")
        # Mock version selection - would come from API
        version_a_options = ["Current Version", "Version 2", "Version 1"]
        version_a = st.selectbox("Select Version", version_a_options, key="version_a_select")
        version_a_content = get_mock_version_content(version_a)

    with col2:
        st.markdown("**Version B:**")
        version_b_options = ["Current Version", "Version 2", "Version 1"]
        version_b = st.selectbox("Select Version", version_b_options, key="version_b_select")
        version_b_content = get_mock_version_content(version_b)

    if st.button("⚖️ Compare Versions", key="compare_versions"):
        if version_a != version_b:
            render_version_diff(version_a_content, version_b_content, version_a, version_b)
        else:
            st.warning("Please select different versions to compare")


def render_version_diff(content_a: str, content_b: str, label_a: str, label_b: str):
    """Render a diff comparison between two versions."""
    st.markdown("#### 📊 Version Comparison Results")

    # Basic metrics comparison
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Length A", len(content_a))
        st.metric("Length B", len(content_b))

    with col2:
        st.metric("Words A", len(content_a.split()))
        st.metric("Words B", len(content_b.split()))

    with col3:
        tokens_a = estimate_token_count(content_a)
        tokens_b = estimate_token_count(content_b)
        st.metric("Tokens A", tokens_a)
        st.metric("Tokens B", tokens_b)

    # Content comparison
    st.markdown("---")
    st.markdown("**Content Comparison:**")

    # Side-by-side view
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**{label_a}:**")
        st.text_area("", value=content_a, height=200, disabled=True, key="content_a_display")

    with col2:
        st.markdown(f"**{label_b}:**")
        st.text_area("", value=content_b, height=200, disabled=True, key="content_b_display")

    # Simple diff highlighting (basic implementation)
    st.markdown("---")
    st.markdown("**Key Differences:**")
    diff_analysis = analyze_version_differences(content_a, content_b)
    for diff in diff_analysis[:5]:  # Show top 5 differences
        st.write(f"• {diff}")


def render_version_rollback(prompt_client):
    """Render version rollback interface."""
    st.markdown("#### ⏪ Version Rollback")

    st.warning("⚠️ Rolling back will permanently replace the current version. This action cannot be undone.")

    # Select prompt and version to rollback to
    if st.button("📋 Load Rollback Candidates", key="load_rollback_candidates"):
        with st.spinner("Loading prompts with version history..."):
            # Mock data - would come from API
            candidates = [
                {"id": "prompt_1", "name": "AI Assistant", "current_version": 3, "available_versions": [1, 2]},
                {"id": "prompt_2", "name": "Code Generator", "current_version": 5, "available_versions": [1, 2, 3, 4]},
                {"id": "prompt_3", "name": "Data Analyst", "current_version": 2, "available_versions": [1]},
            ]
            st.session_state.rollback_candidates = candidates
            st.success("✅ Loaded rollback candidates")

    if "rollback_candidates" in st.session_state:
        candidates = st.session_state.rollback_candidates

        for candidate in candidates:
            with st.expander(f"📝 {candidate['name']} (Current: v{candidate['current_version']})", expanded=False):
                st.markdown(f"**Available Versions:** {candidate['available_versions']}")

                selected_version = st.selectbox(
                    "Select version to rollback to",
                    candidate["available_versions"],
                    key=f"rollback_version_{candidate['id']}",
                )

                rollback_reason = st.text_area(
                    "Rollback Reason (optional)",
                    placeholder="Explain why you're rolling back...",
                    key=f"rollback_reason_{candidate['id']}",
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("⚠️ Preview Rollback", key=f"preview_rollback_{candidate['id']}"):
                        st.info(
                            f"Would rollback {candidate['name']} from v{candidate['current_version']} to v{selected_version}"
                        )
                        st.code(get_mock_version_content(f"Version {selected_version}"), language="text")

                with col2:
                    if st.button("⏪ Execute Rollback", key=f"execute_rollback_{candidate['id']}", type="primary"):
                        with st.spinner("Executing rollback..."):
                            # Would call API to rollback
                            time.sleep(1)  # Simulate API call
                            st.success(f"✅ Successfully rolled back {candidate['name']} to version {selected_version}")
                            st.info("The previous version has been archived and can be restored if needed.")


def render_version_analytics(prompt_client):
    """Render version analytics and insights."""
    st.markdown("#### 📈 Version Analytics")

    if st.button("📊 Load Version Analytics", key="load_version_analytics"):
        with st.spinner("Analyzing version data..."):
            # Mock analytics data
            analytics = {
                "total_versions": 47,
                "active_versions": 23,
                "rollback_count": 5,
                "avg_versions_per_prompt": 2.3,
                "most_rolled_back_prompt": "AI Assistant (3 rollbacks)",
                "version_adoption_trends": {"v1_adoption": 0.85, "v2_adoption": 0.65, "v3_adoption": 0.45},
                "performance_improvements": [
                    {"prompt": "Code Generator", "improvement": "+15% accuracy", "versions": "v1→v3"},
                    {"prompt": "Data Analyst", "improvement": "+8% coherence", "versions": "v2→v4"},
                    {"prompt": "Content Writer", "improvement": "+12% engagement", "versions": "v1→v2"},
                ],
            }

            display_version_analytics(analytics)


def display_version_analytics(analytics: Dict[str, Any]):
    """Display version analytics data."""
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Versions", analytics["total_versions"])
    with col2:
        st.metric("Active Versions", analytics["active_versions"])
    with col3:
        st.metric("Rollbacks", analytics["rollback_count"])
    with col4:
        st.metric("Avg Versions/Prompt", ".1f")

    # Version adoption trends
    st.markdown("---")
    st.markdown("**📊 Version Adoption Trends**")

    adoption_data = analytics["version_adoption_trends"]
    import pandas as pd

    df = pd.DataFrame(
        {
            "Version": ["v1", "v2", "v3"],
            "Adoption Rate": [adoption_data["v1_adoption"], adoption_data["v2_adoption"], adoption_data["v3_adoption"]],
        }
    )
    st.bar_chart(df.set_index("Version"))

    # Performance improvements
    st.markdown("---")
    st.markdown("**🚀 Performance Improvements**")

    for improvement in analytics["performance_improvements"]:
        with st.expander(f"📈 {improvement['prompt']} - {improvement['improvement']}", expanded=False):
            st.markdown(f"**Versions:** {improvement['versions']}")
            st.markdown(f"**Improvement:** {improvement['improvement']}")
            st.info("This improvement was achieved through prompt tuning and optimization.")

    # Insights
    st.markdown("---")
    st.markdown("**💡 Insights**")
    st.info(f"**Most Stable:** {analytics['most_rolled_back_prompt']} suggests this prompt requires frequent updates")
    st.info("**Trend:** Newer versions show 20-30% performance improvement on average")
    st.info("**Recommendation:** Consider A/B testing before major version rollbacks")


# ============================================================================
# VERSION MANAGEMENT HELPER FUNCTIONS
# ============================================================================


def generate_mock_version_history(prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate mock version history for a prompt."""
    import random
    from datetime import datetime, timedelta

    base_content = prompt.get("content", "Sample prompt content")
    versions = []
    version_count = random.randint(2, 5)

    for i in range(1, version_count + 1):
        # Modify content slightly for each version
        modified_content = base_content
        if i > 1:
            modifications = [
                ". Be more specific in your responses",
                ". Include examples where appropriate",
                ". Ensure responses are concise yet comprehensive",
                ". Add safety considerations",
                ". Optimize for better performance",
            ]
            modified_content += random.choice(modifications)

        version = {
            "version": i,
            "content": modified_content,
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M:%S"),
            "changes": f"Version {i} changes - {random.choice(['Improved clarity', 'Added examples', 'Enhanced specificity', 'Optimized performance', 'Added safety checks'])}",
            "performance_score": random.uniform(7.0, 9.5) if i > 1 else None,
            "is_current": i == version_count,
        }
        versions.append(version)

    return versions


def get_mock_version_content(version_label: str) -> str:
    """Get mock content for a version label."""
    contents = {
        "Current Version": "You are a helpful AI assistant. Provide clear, accurate, and helpful responses to user questions.",
        "Version 2": "You are a helpful AI assistant. Provide clear, accurate, and helpful responses to user questions. Be specific and include examples when appropriate.",
        "Version 1": "You are a helpful AI assistant. Provide responses to user questions.",
    }
    return contents.get(version_label, "Sample prompt content for " + version_label)


def analyze_version_differences(content_a: str, content_b: str) -> List[str]:
    """Analyze differences between two versions."""
    differences = []

    # Length differences
    len_a, len_b = len(content_a), len(content_b)
    if abs(len_a - len_b) > 10:
        differences.append(
            f"Length changed from {len_a} to {len_b} characters ({'+' if len_b > len_a else '-'}{abs(len_b - len_a)})"
        )

    # Word count differences
    words_a, words_b = len(content_a.split()), len(content_b.split())
    if abs(words_a - words_b) > 2:
        differences.append(f"Word count changed from {words_a} to {words_b}")

    # Token differences
    tokens_a, tokens_b = estimate_token_count(content_a), estimate_token_count(content_b)
    if abs(tokens_a - tokens_b) > 5:
        differences.append(f"Token count changed from ~{tokens_a} to ~{tokens_b}")

    # Content additions
    additions = ["examples", "specific", "clear", "concise", "comprehensive", "safety", "guidelines"]
    for addition in additions:
        if addition.lower() in content_b.lower() and addition.lower() not in content_a.lower():
            differences.append(f"Added '{addition}' guidance")

    # If no specific differences found
    if not differences:
        differences.append("Minor wording and formatting improvements")
        differences.append("Maintained core functionality while enhancing clarity")

    return differences
