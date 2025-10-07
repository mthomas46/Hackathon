"""
MCP Package Manager UI - "Docker for Knowledge Graphs"

Streamlit UI for managing MCP packages:
- Create packages
- Export to .mcp files
- Import packages
- Version management
- Hot-swapping
- Package discovery
"""

import streamlit as st
import sys
from pathlib import Path
import tempfile
import json
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# Add services to path
services_path = Path(__file__).parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

from mcp_package_manager.src.package_manager import (
    PackageManager,
    PackageMetadata,
    ExportConfig,
    ImportConfig,
    CompressionType
)


# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="MCP Package Manager",
    page_icon="📦",
    layout="wide"
)

st.title("📦 MCP Package Manager")
st.markdown("**Docker for Knowledge Graphs** - Package, version, and deploy your MCP knowledge")


# ============================================================================
# Initialize Package Manager
# ============================================================================

@st.cache_resource
def get_package_manager():
    """Initialize package manager."""
    storage_dir = Path(__file__).parent.parent.parent / "data" / "packages"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return PackageManager(storage_dir=str(storage_dir))


manager = get_package_manager()


# ============================================================================
# Dashboard Metrics
# ============================================================================

st.header("📊 Package Dashboard")

col1, col2, col3, col4 = st.columns(4)

all_packages = manager.list_packages()
total_packages = len(all_packages)

# Calculate total knowledge items
total_knowledge = sum(
    len(manager.get_package_knowledge(pkg.package_id))
    for pkg in all_packages
)

# Count versions
total_versions = sum(
    len(manager.list_versions(pkg.package_id))
    for pkg in all_packages
)

# Get unique tags
all_tags = set()
for pkg in all_packages:
    all_tags.update(pkg.metadata.tags)

with col1:
    st.metric("Total Packages", total_packages)

with col2:
    st.metric("Knowledge Items", total_knowledge)

with col3:
    st.metric("Version Snapshots", total_versions)

with col4:
    st.metric("Unique Tags", len(all_tags))


# ============================================================================
# Tabs
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📦 Create Package",
    "📤 Export",
    "📥 Import",
    "🔄 Version Control",
    "⚡ Hot-Swap",
    "🔍 Browse"
])


# ============================================================================
# Tab 1: Create Package
# ============================================================================

with tab1:
    st.subheader("Create New Package")
    
    with st.form("create_package_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            pkg_name = st.text_input("Package Name *", placeholder="my_mcp_package")
            pkg_version = st.text_input("Version *", value="1.0.0", placeholder="1.0.0")
            pkg_author = st.text_input("Author", placeholder="Your Name")
        
        with col2:
            pkg_description = st.text_area("Description", placeholder="Describe your package...")
            tier_type = st.selectbox("Tier Type", ["client", "project", "team", "company", "ecosystem"])
            pkg_tags = st.text_input("Tags (comma-separated)", placeholder="ml, production, api")
        
        st.markdown("### Add Knowledge Items")
        
        knowledge_items = []
        num_items = st.number_input("Number of knowledge items", min_value=0, max_value=20, value=1)
        
        for i in range(num_items):
            with st.expander(f"Knowledge Item {i+1}"):
                content = st.text_area(f"Content {i+1}", key=f"content_{i}")
                relevance = st.slider(f"Relevance {i+1}", 0.0, 1.0, 0.9, key=f"relevance_{i}")
                
                if content:
                    knowledge_items.append({"content": content, "relevance": relevance})
        
        submitted = st.form_submit_button("Create Package", type="primary", use_container_width=True)
        
        if submitted:
            if not pkg_name or not pkg_version:
                st.error("Package name and version are required!")
            else:
                try:
                    # Create metadata
                    tags = [t.strip() for t in pkg_tags.split(",") if t.strip()]
                    
                    metadata = PackageMetadata(
                        name=pkg_name,
                        version=pkg_version,
                        description=pkg_description,
                        author=pkg_author,
                        tier_type=tier_type,
                        tags=tags
                    )
                    
                    # Create package
                    package = manager.create_package(metadata)
                    
                    # Add knowledge
                    for item in knowledge_items:
                        manager.add_knowledge_to_package(
                            package.package_id,
                            content=item["content"],
                            relevance=item["relevance"]
                        )
                    
                    st.success(f"✅ Package created successfully! ID: {package.package_id}")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Error creating package: {str(e)}")


# ============================================================================
# Tab 2: Export
# ============================================================================

with tab2:
    st.subheader("Export Package to .mcp File")
    
    packages_to_export = manager.list_packages()
    
    if not packages_to_export:
        st.info("No packages available. Create a package first!")
    else:
        # Select package
        package_options = {
            f"{pkg.metadata.name} (v{pkg.metadata.version})": pkg
            for pkg in packages_to_export
        }
        
        selected_pkg_name = st.selectbox("Select Package", list(package_options.keys()))
        selected_pkg = package_options[selected_pkg_name]
        
        # Show package info
        with st.expander("Package Details"):
            info = manager.get_package_info(selected_pkg.package_id)
            st.json(info)
        
        # Export configuration
        col1, col2 = st.columns(2)
        
        with col1:
            include_metadata = st.checkbox("Include Metadata", value=True)
            include_knowledge = st.checkbox("Include Knowledge", value=True)
        
        with col2:
            compression = st.selectbox(
                "Compression",
                ["none", "gzip", "zstd"],
                index=1
            )
        
        if st.button("📤 Export Package", type="primary", use_container_width=True):
            try:
                # Create export config
                compression_type = {
                    "none": CompressionType.NONE,
                    "gzip": CompressionType.GZIP,
                    "zstd": CompressionType.ZSTD
                }[compression]
                
                config = ExportConfig(
                    include_metadata=include_metadata,
                    include_knowledge=include_knowledge,
                    compression=compression_type
                )
                
                # Export to temp file
                export_dir = Path(__file__).parent.parent.parent / "data" / "exports"
                export_dir.mkdir(parents=True, exist_ok=True)
                
                filename = f"{selected_pkg.metadata.name}_v{selected_pkg.metadata.version}.mcp"
                export_path = export_dir / filename
                
                result = manager.export_package(
                    selected_pkg.package_id,
                    str(export_path),
                    config
                )
                
                if result.success:
                    st.success(f"✅ Package exported to: {filename}")
                    
                    # Offer download
                    with open(export_path, 'rb') as f:
                        st.download_button(
                            label="⬇️ Download .mcp File",
                            data=f,
                            file_name=filename,
                            mime="application/octet-stream",
                            use_container_width=True
                        )
                else:
                    st.error(f"Export failed: {result.error}")
                    
            except Exception as e:
                st.error(f"Error exporting package: {str(e)}")


# ============================================================================
# Tab 3: Import
# ============================================================================

with tab3:
    st.subheader("Import Package from .mcp File")
    
    # Upload file
    uploaded_file = st.file_uploader("Upload .mcp file", type=['mcp'])
    
    if uploaded_file:
        # Import configuration
        col1, col2 = st.columns(2)
        
        with col1:
            validate_metadata = st.checkbox("Validate Metadata", value=True)
        
        with col2:
            overwrite_existing = st.checkbox("Overwrite if Exists", value=False)
        
        if st.button("📥 Import Package", type="primary", use_container_width=True):
            try:
                # Save uploaded file temporarily
                import_dir = Path(__file__).parent.parent.parent / "data" / "imports"
                import_dir.mkdir(parents=True, exist_ok=True)
                
                temp_path = import_dir / uploaded_file.name
                temp_path.write_bytes(uploaded_file.getvalue())
                
                # Create import config
                config = ImportConfig(
                    validate_metadata=validate_metadata,
                    overwrite_existing=overwrite_existing
                )
                
                # Import
                result = manager.import_package(str(temp_path), config)
                
                if result.success:
                    st.success(f"✅ Package imported successfully! ID: {result.package_id}")
                    
                    # Show imported package info
                    info = manager.get_package_info(result.package_id)
                    st.json(info)
                else:
                    st.error(f"Import failed: {result.error}")
                    
            except Exception as e:
                st.error(f"Error importing package: {str(e)}")


# ============================================================================
# Tab 4: Version Control
# ============================================================================

with tab4:
    st.subheader("Version Control & Snapshots")
    
    packages_for_version = manager.list_packages()
    
    if not packages_for_version:
        st.info("No packages available. Create a package first!")
    else:
        # Select package
        version_pkg_options = {
            f"{pkg.metadata.name} (v{pkg.metadata.version})": pkg
            for pkg in packages_for_version
        }
        
        selected_version_pkg_name = st.selectbox(
            "Select Package",
            list(version_pkg_options.keys()),
            key="version_select"
        )
        selected_version_pkg = version_pkg_options[selected_version_pkg_name]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### Create Snapshot")
            
            snapshot_tag = st.text_input("Snapshot Tag", placeholder="v1.0.0-stable")
            
            if st.button("📸 Create Snapshot", use_container_width=True):
                if snapshot_tag:
                    try:
                        snapshot = manager.create_snapshot(
                            selected_version_pkg.package_id,
                            tag=snapshot_tag
                        )
                        st.success(f"✅ Snapshot created: {snapshot_tag}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please enter a snapshot tag")
        
        with col2:
            st.markdown("### Rollback")
            
            versions = manager.list_versions(selected_version_pkg.package_id)
            
            if versions:
                version_options = {
                    f"{v.tag} (v{v.version})": v
                    for v in versions
                }
                
                selected_rollback = st.selectbox(
                    "Select Version to Rollback",
                    list(version_options.keys())
                )
                
                if st.button("⏮️ Rollback", use_container_width=True):
                    selected_version = version_options[selected_rollback]
                    
                    result = manager.rollback(
                        selected_version_pkg.package_id,
                        selected_version.version
                    )
                    
                    if result.success:
                        st.success(f"✅ Rolled back to {selected_version.tag}")
                    else:
                        st.error(f"Rollback failed: {result.error}")
            else:
                st.info("No snapshots yet. Create one above!")
        
        # List all versions
        st.markdown("### Version History")
        
        versions = manager.list_versions(selected_version_pkg.package_id)
        
        if versions:
            version_data = []
            for v in versions:
                version_data.append({
                    "Tag": v.tag,
                    "Version": v.version,
                    "Created": v.created_at.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            st.dataframe(version_data, use_container_width=True)
        else:
            st.info("No version history yet")


# ============================================================================
# Tab 5: Hot-Swap
# ============================================================================

with tab5:
    st.subheader("Hot-Swap Packages (Zero Downtime)")
    
    packages_for_swap = manager.list_packages()
    
    if len(packages_for_swap) < 2:
        st.info("Need at least 2 packages for hot-swapping. Create more packages first!")
    else:
        st.markdown("### Instant Hot-Swap")
        
        col1, col2 = st.columns(2)
        
        swap_options = {
            f"{pkg.metadata.name} (v{pkg.metadata.version})": pkg
            for pkg in packages_for_swap
        }
        
        with col1:
            st.markdown("**Current Package**")
            current_pkg_name = st.selectbox(
                "Current",
                list(swap_options.keys()),
                key="current_swap"
            )
            current_pkg = swap_options[current_pkg_name]
        
        with col2:
            st.markdown("**New Package**")
            new_pkg_name = st.selectbox(
                "New",
                list(swap_options.keys()),
                key="new_swap"
            )
            new_pkg = swap_options[new_pkg_name]
        
        if st.button("⚡ Instant Hot-Swap", type="primary", use_container_width=True):
            if current_pkg.package_id == new_pkg.package_id:
                st.warning("Current and new packages are the same!")
            else:
                result = manager.hot_swap(current_pkg.package_id, new_pkg.package_id)
                
                if result.success:
                    st.success(f"✅ Hot-swap successful! Downtime: {result.downtime_ms}ms")
                    st.balloons()
                else:
                    st.error(f"Hot-swap failed: {result.error}")
        
        st.markdown("---")
        st.markdown("### Gradual Rollout")
        
        percentage = st.slider("Rollout Percentage", 0, 100, 10, 10)
        
        if st.button("📈 Gradual Rollout", use_container_width=True):
            result = manager.gradual_rollout(
                current_pkg.package_id,
                new_pkg.package_id,
                percentage
            )
            
            if result.success:
                st.success(f"✅ Rollout at {percentage}%")
                
                # Show progress bar
                st.progress(percentage / 100)
            else:
                st.error(f"Rollout failed: {result.error}")


# ============================================================================
# Tab 6: Browse
# ============================================================================

with tab6:
    st.subheader("Browse & Search Packages")
    
    # Search
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_name = st.text_input("Search by name", placeholder="Enter package name...")
    
    with col2:
        search_tags = st.multiselect("Filter by tags", list(all_tags))
    
    # Get filtered packages
    if search_name or search_tags:
        filtered_packages = manager.search_packages(
            name=search_name if search_name else None,
            tags=search_tags if search_tags else None
        )
    else:
        filtered_packages = manager.list_packages()
    
    st.markdown(f"**Found {len(filtered_packages)} packages**")
    
    # Display packages
    if filtered_packages:
        for pkg in filtered_packages:
            with st.expander(f"📦 {pkg.metadata.name} (v{pkg.metadata.version})"):
                info = manager.get_package_info(pkg.package_id)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Description:** {pkg.metadata.description or 'N/A'}")
                    st.markdown(f"**Author:** {pkg.metadata.author or 'N/A'}")
                    st.markdown(f"**Tier Type:** {pkg.metadata.tier_type}")
                    st.markdown(f"**Tags:** {', '.join(pkg.metadata.tags) if pkg.metadata.tags else 'None'}")
                
                with col2:
                    st.metric("Knowledge Items", info["knowledge_count"])
                    st.metric("Status", info["status"])
                
                # Show knowledge items
                knowledge = manager.get_package_knowledge(pkg.package_id)
                
                if knowledge:
                    st.markdown("**Knowledge Items:**")
                    for i, item in enumerate(knowledge[:5]):  # Show first 5
                        st.markdown(f"{i+1}. {item['content'][:100]}... (relevance: {item['relevance']:.2f})")
                    
                    if len(knowledge) > 5:
                        st.markdown(f"*...and {len(knowledge) - 5} more*")
    else:
        st.info("No packages found")


# ============================================================================
# Visualizations
# ============================================================================

st.markdown("---")
st.header("📈 Analytics")

if all_packages:
    col1, col2 = st.columns(2)
    
    with col1:
        # Packages by tier type
        tier_counts = {}
        for pkg in all_packages:
            tier = pkg.metadata.tier_type
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        fig = px.pie(
            values=list(tier_counts.values()),
            names=list(tier_counts.keys()),
            title="Packages by Tier Type"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top tags
        tag_counts = {}
        for pkg in all_packages:
            for tag in pkg.metadata.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        if tag_counts:
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=[t[0] for t in sorted_tags],
                    y=[t[1] for t in sorted_tags]
                )
            ])
            fig.update_layout(title="Top 10 Tags", xaxis_title="Tag", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# Footer
# ============================================================================

st.markdown("---")
st.markdown("💡 **Tip:** MCP packages are portable across systems - like Docker containers for knowledge!")

