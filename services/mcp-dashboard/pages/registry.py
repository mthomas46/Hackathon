"""Registry Browser - Browse and compare MCP package versions."""

import streamlit as st
import pandas as pd
from datetime import datetime


def render():
    """Render the registry browser page."""
    
    st.title("📚 Package Registry")
    st.markdown("Browse packages, compare versions, and view detailed specifications")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📦 All Packages", "🔍 Version Comparison", "📊 Registry Stats"])
    
    with tab1:
        render_package_browser()
    
    with tab2:
        render_version_comparison()
    
    with tab3:
        render_registry_stats()


def render_package_browser():
    """Render the main package browser."""
    
    st.subheader("Browse All Packages")
    
    # Advanced filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search = st.text_input("🔍 Search", placeholder="Package name or description...")
    
    with col2:
        status_filter = st.multiselect(
            "Status",
            ["Published", "Draft", "Deprecated"],
            default=["Published"]
        )
    
    with col3:
        category_filter = st.multiselect(
            "Category",
            ["Knowledge Base", "Documentation", "Support", "Analytics", "Engineering"]
        )
    
    with col4:
        sort_by = st.selectbox(
            "Sort By",
            ["Name", "Downloads", "Stars", "Updated", "Created"]
        )
    
    # Display mode
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("---")
    with col2:
        view_mode = st.radio("View", ["Grid", "List"], horizontal=True, label_visibility="collapsed")
    
    # Mock package data
    packages = [
        {
            "name": "enterprise-support-kb",
            "display_name": "Enterprise Support KB",
            "description": "Comprehensive customer support knowledge base with 50K+ tickets, FAQs, and solutions. Trained on 5 years of support interactions.",
            "author": "acme-corp",
            "version": "2.1.0",
            "versions_count": 12,
            "downloads": 1247,
            "stars": 342,
            "status": "Published",
            "category": "Support",
            "size": "2.3 GB",
            "updated": "2 days ago",
            "tags": ["support", "enterprise", "kb", "faq"]
        },
        {
            "name": "technical-documentation",
            "display_name": "Technical Documentation",
            "description": "Complete technical documentation for software development. Includes API docs, architecture guides, and best practices.",
            "author": "tech-docs",
            "version": "1.5.2",
            "versions_count": 8,
            "downloads": 982,
            "stars": 287,
            "status": "Published",
            "category": "Documentation",
            "size": "1.8 GB",
            "updated": "1 week ago",
            "tags": ["documentation", "technical", "api", "dev"]
        },
        {
            "name": "sales-playbook",
            "display_name": "Sales Playbook",
            "description": "Sales methodologies, strategies, and best practices. Win rates, objection handling, and pitch decks.",
            "author": "sales-team",
            "version": "1.0.3",
            "versions_count": 4,
            "downloads": 756,
            "stars": 198,
            "status": "Published",
            "category": "Sales",
            "size": "890 MB",
            "updated": "3 days ago",
            "tags": ["sales", "playbook", "strategy"]
        },
        {
            "name": "code-review-patterns",
            "display_name": "Code Review Patterns",
            "description": "Best practices and patterns for code reviews. Security checks, style guides, and common issues.",
            "author": "engineering",
            "version": "1.2.0",
            "versions_count": 6,
            "downloads": 543,
            "stars": 134,
            "status": "Published",
            "category": "Engineering",
            "size": "450 MB",
            "updated": "5 days ago",
            "tags": ["code-review", "engineering", "patterns"]
        },
        {
            "name": "product-analytics-v3",
            "display_name": "Product Analytics v3",
            "description": "Product usage analytics and insights. User behavior, feature adoption, and retention metrics.",
            "author": "analytics-team",
            "version": "3.0.1-beta",
            "versions_count": 15,
            "downloads": 654,
            "stars": 156,
            "status": "Published",
            "category": "Analytics",
            "size": "1.2 GB",
            "updated": "1 day ago",
            "tags": ["analytics", "product", "metrics"]
        }
    ]
    
    # Display packages
    if view_mode == "Grid":
        # Grid view - 2 columns
        col1, col2 = st.columns(2)
        for idx, pkg in enumerate(packages):
            with col1 if idx % 2 == 0 else col2:
                render_package_card_detailed(pkg)
    else:
        # List view
        for pkg in packages:
            render_package_list_item(pkg)


def render_package_card_detailed(pkg):
    """Render a detailed package card."""
    
    with st.container():
        # Header with status badge
        status_color = {"Published": "🟢", "Draft": "🟡", "Deprecated": "🔴"}
        st.markdown(f"### {status_color[pkg['status']]} {pkg['display_name']}")
        st.caption(f"by **{pkg['author']}** | v{pkg['version']}")
        
        # Description
        st.markdown(pkg['description'])
        
        # Tags
        tag_html = " ".join([
            f'<span style="background-color: #e0e7ff; color: #3730a3; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; margin-right: 0.25rem;">{tag}</span>'
            for tag in pkg['tags']
        ])
        st.markdown(tag_html, unsafe_allow_html=True)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Downloads", pkg['downloads'])
        with col2:
            st.metric("Stars", pkg['stars'])
        with col3:
            st.metric("Versions", pkg['versions_count'])
        with col4:
            st.metric("Size", pkg['size'])
        
        # Actions
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📥 Download", key=f"dl_detail_{pkg['name']}", use_container_width=True):
                st.success("Download initiated!")
        with col2:
            if st.button("⭐ Star", key=f"star_detail_{pkg['name']}", use_container_width=True):
                st.success("Package starred!")
        with col3:
            if st.button("📊 Versions", key=f"ver_detail_{pkg['name']}", use_container_width=True):
                st.info("View version history →")
        
        st.markdown("---")


def render_package_list_item(pkg):
    """Render a package as a list item."""
    
    with st.container():
        col1, col2 = st.columns([5, 2])
        
        with col1:
            status_color = {"Published": "🟢", "Draft": "🟡", "Deprecated": "🔴"}
            st.markdown(f"**{status_color[pkg['status']]} {pkg['display_name']}** v{pkg['version']}")
            st.caption(f"{pkg['description'][:100]}...")
            st.caption(f"📥 {pkg['downloads']} | ⭐ {pkg['stars']} | 📦 {pkg['versions_count']} versions | Updated {pkg['updated']}")
        
        with col2:
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.button("📥", key=f"dl_list_{pkg['name']}", help="Download")
            with col_b:
                st.button("⭐", key=f"star_list_{pkg['name']}", help="Star")
            with col_c:
                st.button("📊", key=f"ver_list_{pkg['name']}", help="Versions")
        
        st.markdown("---")


def render_version_comparison():
    """Render version comparison interface."""
    
    st.subheader("Version Comparison")
    st.markdown("Compare different versions of a package to understand changes")
    
    # Package selection
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        package = st.selectbox(
            "Select Package",
            ["enterprise-support-kb", "technical-documentation", "sales-playbook"]
        )
    
    with col2:
        versions = ["2.1.0", "2.0.5", "2.0.0", "1.9.2", "1.8.0"]
        version1 = st.selectbox("Version 1", versions, index=0)
        version2 = st.selectbox("Version 2", versions, index=2)
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Compare", use_container_width=True):
            st.session_state['compare_triggered'] = True
    
    # Comparison results
    if st.session_state.get('compare_triggered'):
        st.markdown("---")
        st.subheader(f"Comparing {version1} vs {version2}")
        
        # Side-by-side comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### Version {version1}")
            st.markdown("**📅 Released:** 2 days ago")
            st.markdown("**👤 Author:** acme-corp")
            st.markdown("**💾 Size:** 2.3 GB")
            st.markdown("**📊 Downloads:** 1,247")
            
            st.markdown("**✨ Changes:**")
            st.markdown("""
            - Added 5,000 new support tickets
            - Improved FAQ categorization
            - Enhanced search accuracy by 15%
            - Fixed 12 data quality issues
            - Updated to latest embedding model
            """)
        
        with col2:
            st.markdown(f"### Version {version2}")
            st.markdown("**📅 Released:** 2 months ago")
            st.markdown("**👤 Author:** acme-corp")
            st.markdown("**💾 Size:** 2.1 GB")
            st.markdown("**📊 Downloads:** 892")
            
            st.markdown("**✨ Changes:**")
            st.markdown("""
            - Initial major release
            - 45,000 support tickets
            - Basic FAQ system
            - Standard search
            - Original embedding model
            """)
        
        # Diff summary
        st.markdown("---")
        st.subheader("📊 Diff Summary")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Size Change", "+200 MB", delta="+9.5%")
        with col2:
            st.metric("Documents", "+5,000", delta="+11.1%")
        with col3:
            st.metric("Search Accuracy", "15%", delta="+15%")
        
        # Detailed changelog
        with st.expander("📝 Detailed Changelog"):
            st.markdown("""
            #### Version 2.1.0 (Latest)
            **New Features:**
            - Advanced FAQ categorization using ML
            - Semantic search improvements
            - Multi-language support (5 new languages)
            
            **Improvements:**
            - 15% better search accuracy
            - 20% faster query response
            - Enhanced embedding quality
            
            **Bug Fixes:**
            - Fixed duplicate FAQ entries
            - Corrected date parsing issues
            - Resolved character encoding problems
            
            **Data Updates:**
            - Added 5,000 new tickets (Q4 2024)
            - Updated 2,000 existing tickets
            - Removed 500 obsolete entries
            """)


def render_registry_stats():
    """Render registry statistics."""
    
    st.subheader("Registry Statistics")
    
    # Overall stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Packages", "47", delta="+3 this month")
    
    with col2:
        st.metric("Total Versions", "312", delta="+18")
    
    with col3:
        st.metric("Total Downloads", "15.4K", delta="+12%")
    
    with col4:
        st.metric("Active Authors", "23", delta="+2")
    
    # Category distribution
    st.markdown("---")
    st.subheader("Packages by Category")
    
    category_data = pd.DataFrame({
        "Category": ["Knowledge Base", "Documentation", "Support", "Analytics", "Engineering", "Sales", "Other"],
        "Packages": [12, 8, 7, 6, 5, 4, 5],
        "Downloads": [4200, 3100, 2800, 2200, 1800, 900, 400]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### By Count")
        st.bar_chart(category_data.set_index("Category")["Packages"])
    
    with col2:
        st.markdown("#### By Downloads")
        st.bar_chart(category_data.set_index("Category")["Downloads"])
    
    # Top packages
    st.markdown("---")
    st.subheader("Top Packages")
    
    tab1, tab2, tab3 = st.tabs(["Most Downloaded", "Most Starred", "Most Recent"])
    
    with tab1:
        top_downloads = pd.DataFrame({
            "Package": ["enterprise-support-kb", "technical-documentation", "sales-playbook", "product-analytics", "code-review"],
            "Downloads": [1247, 982, 756, 654, 543],
            "Stars": [342, 287, 198, 156, 134]
        })
        st.dataframe(top_downloads, use_container_width=True, hide_index=True)
    
    with tab2:
        top_stars = pd.DataFrame({
            "Package": ["enterprise-support-kb", "technical-documentation", "sales-playbook", "product-analytics", "customer-insights"],
            "Stars": [342, 287, 198, 156, 98],
            "Downloads": [1247, 982, 756, 654, 432]
        })
        st.dataframe(top_stars, use_container_width=True, hide_index=True)
    
    with tab3:
        recent = pd.DataFrame({
            "Package": ["product-analytics-v3", "enterprise-support-kb", "sales-playbook", "code-review", "tech-docs"],
            "Version": ["3.0.1-beta", "2.1.0", "1.0.3", "1.2.0", "1.5.2"],
            "Updated": ["1 day ago", "2 days ago", "3 days ago", "5 days ago", "1 week ago"]
        })
        st.dataframe(recent, use_container_width=True, hide_index=True)
    
    # Version history chart
    st.markdown("---")
    st.subheader("Version Releases Over Time")
    
    releases_data = pd.DataFrame({
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "Releases": [12, 15, 18, 14, 20, 18]
    })
    st.line_chart(releases_data.set_index("Month"))
