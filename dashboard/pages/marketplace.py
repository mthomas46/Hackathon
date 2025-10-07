"""Marketplace page - Browse and download MCP packages."""

import streamlit as st
import pandas as pd


def render():
    """Render the marketplace page."""
    
    st.title("🏪 MCP Marketplace")
    st.markdown("Discover, download, and share MCP packages")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🔥 Trending", "🔍 Browse", "⭐ My Starred"])
    
    with tab1:
        render_trending()
    
    with tab2:
        render_browse()
    
    with tab3:
        render_starred()


def render_trending():
    """Render trending packages."""
    
    st.subheader("Trending Packages (Last 7 Days)")
    
    # Mock trending packages
    packages = [
        {
            "name": "enterprise-support-kb",
            "description": "Enterprise customer support knowledge base with 50K+ support tickets",
            "author": "acme-corp",
            "downloads": 1247,
            "stars": 342,
            "version": "2.1.0",
            "size": "2.3 GB",
            "tags": ["support", "enterprise", "kb"]
        },
        {
            "name": "technical-documentation",
            "description": "Comprehensive technical documentation for software development",
            "author": "tech-docs",
            "downloads": 982,
            "stars": 287,
            "version": "1.5.2",
            "size": "1.8 GB",
            "tags": ["documentation", "technical", "dev"]
        },
        {
            "name": "sales-playbook",
            "description": "Sales methodologies, strategies, and best practices",
            "author": "sales-team",
            "downloads": 756,
            "stars": 198,
            "version": "1.0.3",
            "size": "890 MB",
            "tags": ["sales", "playbook", "strategy"]
        }
    ]
    
    for pkg in packages:
        render_package_card(pkg)


def render_browse():
    """Render browse packages interface."""
    
    st.subheader("Browse Packages")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search = st.text_input("🔍 Search", placeholder="Search packages...")
    
    with col2:
        category = st.selectbox("Category", ["All", "Knowledge Base", "Documentation", "Support", "Sales", "Analytics"])
    
    with col3:
        sort_by = st.selectbox("Sort By", ["Trending", "Most Downloaded", "Most Starred", "Recently Updated"])
    
    st.markdown("---")
    
    # All packages (mock data)
    all_packages = [
        {
            "name": "product-analytics",
            "description": "Product usage analytics and insights",
            "author": "analytics-team",
            "downloads": 654,
            "stars": 156,
            "version": "3.0.1",
            "size": "1.2 GB",
            "tags": ["analytics", "product", "insights"]
        },
        {
            "name": "code-review-patterns",
            "description": "Best practices and patterns for code reviews",
            "author": "engineering",
            "downloads": 543,
            "stars": 134,
            "version": "1.2.0",
            "size": "450 MB",
            "tags": ["code-review", "engineering", "patterns"]
        },
        {
            "name": "customer-insights",
            "description": "Customer behavior patterns and insights",
            "author": "data-science",
            "downloads": 432,
            "stars": 98,
            "version": "2.0.0",
            "size": "1.5 GB",
            "tags": ["customer", "insights", "data"]
        }
    ]
    
    for pkg in all_packages:
        render_package_card(pkg)


def render_starred():
    """Render starred packages."""
    
    st.subheader("My Starred Packages")
    
    starred = [
        {
            "name": "enterprise-support-kb",
            "description": "Enterprise customer support knowledge base",
            "author": "acme-corp",
            "downloads": 1247,
            "stars": 342,
            "version": "2.1.0",
            "size": "2.3 GB",
            "tags": ["support", "enterprise"]
        }
    ]
    
    if not starred:
        st.info("⭐ You haven't starred any packages yet. Browse the marketplace to discover packages!")
    else:
        for pkg in starred:
            render_package_card(pkg, starred=True)


def render_package_card(pkg, starred=False):
    """Render a package card."""
    
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"### 📦 {pkg['name']}")
            st.markdown(f"*by {pkg['author']}*")
            st.markdown(f"{pkg['description']}")
            
            # Tags
            tag_html = " ".join([f'<span style="background-color: #e0e7ff; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.875rem; margin-right: 0.5rem;">{tag}</span>' for tag in pkg['tags']])
            st.markdown(tag_html, unsafe_allow_html=True)
            
            # Stats
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.caption(f"📥 {pkg['downloads']} downloads")
            with col_b:
                st.caption(f"⭐ {pkg['stars']} stars")
            with col_c:
                st.caption(f"📦 v{pkg['version']}")
            with col_d:
                st.caption(f"💾 {pkg['size']}")
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("📥 Download", key=f"dl_{pkg['name']}", use_container_width=True):
                st.success(f"✅ Downloading {pkg['name']}...")
            
            star_icon = "⭐" if starred else "☆"
            if st.button(f"{star_icon} Star", key=f"star_{pkg['name']}", use_container_width=True):
                st.success("Package starred!" if not starred else "Package unstarred!")
        
        st.markdown("---")
