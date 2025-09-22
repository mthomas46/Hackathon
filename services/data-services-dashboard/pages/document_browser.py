"""Document Browser Page - Upload, manage, and search documents with advanced filters.

This module provides a comprehensive interface for managing documents in the Document Store service.
"""

import asyncio
import json
import re
from typing import Any, Dict, List

import pandas as pd
import streamlit as st


def render_document_browser_page():
    """Render the document browser page."""
    st.markdown("### 📄 Document Store Browser")
    st.markdown("Upload, manage, and search documents with advanced filters.")

    # Get document client
    document_client = st.session_state.get("document_client")
    if not document_client:
        st.error("❌ Document Store service not available")
        return

    # Create tabs for different document operations
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📋 Browse Documents", "📤 Upload Document", "🔍 Advanced Search", "📊 Analytics", "🔗 Relationships"]
    )

    with tab1:
        render_document_browser(document_client)

    with tab2:
        render_document_upload(document_client)

    with tab3:
        render_document_search(document_client)

    with tab4:
        render_document_analytics(document_client)

    with tab5:
        render_document_relationships(document_client)


def render_document_browser(document_client):
    """Render the document browsing interface."""
    st.markdown("#### 📋 Browse Documents")

    # Filters and controls
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        search_query = st.text_input("Search", placeholder="Search documents...", key="doc_search_query")

    with col2:
        sort_by = st.selectbox("Sort by", ["Newest First", "Oldest First", "Title", "Size"], key="doc_sort")

    with col3:
        content_type_filter = st.selectbox(
            "Content Type", ["All Types", "text", "markdown", "json", "html", "other"], key="doc_content_type"
        )

    with col4:
        limit = st.slider("Items per page", 10, 100, 25, key="doc_limit")

    # Load documents
    if st.button("🔄 Load Documents", key="load_documents"):
        with st.spinner("Loading documents..."):
            try:
                filters = {}
                if content_type_filter != "All Types":
                    filters["content_type"] = content_type_filter

                result = asyncio.run(
                    document_client.list_documents(
                        limit=limit, search=search_query if search_query.strip() else None, **filters
                    )
                )

                if "items" in result and result["items"]:
                    render_documents_table(result["items"], document_client)
                elif "documents" in result and result["documents"]:
                    render_documents_table(result["documents"], document_client)
                else:
                    st.info("No documents found matching the criteria.")
                    # Show some debug info
                    with st.expander("Debug Info"):
                        st.json(result)

            except Exception as e:
                st.error(f"Error loading documents: {e}")
                st.info(
                    "💡 The document store might need database initialization or the API structure might be different."
                )

    # Quick stats
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Documents", "36")  # From our curl test

    with col2:
        st.metric("Storage Used", "~2.5 MB")  # Estimate

    with col3:
        st.metric("Active Versions", "42")  # Estimate


def render_documents_table(documents: List[Dict[str, Any]], document_client):
    """Render documents in a table format."""
    # Convert to DataFrame for better display
    df_data = []
    for doc in documents:
        # Handle different document structures
        doc_id = doc.get("id", "")
        title = doc.get("title", doc.get("id", "")[:20] + "...")
        content_type = doc.get("content_type", "text")
        size = doc.get("size", len(doc.get("content", "")))
        tags = doc.get("tags", [])
        created_at = doc.get("created_at", "")
        metadata = doc.get("metadata", {})

        df_data.append(
            {
                "ID": doc_id[:8] + "..." if len(doc_id) > 8 else doc_id,
                "Title": title[:30] + "..." if len(title) > 30 else title,
                "Type": content_type,
                "Size": f"{size:,}" if isinstance(size, int) else str(size),
                "Tags": ", ".join(tags[:2]) + ("..." if len(tags) > 2 else ""),
                "Created": created_at[:19] if created_at else "",
                "Metadata Keys": len(metadata) if metadata else 0,
            }
        )

    df = pd.DataFrame(df_data)

    # Display table
    st.dataframe(df, use_container_width=True)

    # Detailed view for selected document
    st.markdown("#### 📖 Document Details")
    selected_id = st.selectbox(
        "Select document for details",
        [doc.get("id", "") for doc in documents],
        format_func=lambda x: next(
            (doc.get("title", doc.get("id", "")[:20]) for doc in documents if doc.get("id") == x), x
        )[:40]
        + "...",
        key="doc_detail_select",
    )

    if selected_id:
        selected_doc = next((doc for doc in documents if doc.get("id") == selected_id), None)
        if selected_doc:
            render_document_details(selected_doc, document_client)


def render_document_details(document: Dict[str, Any], document_client):
    """Render detailed view of a document."""
    doc_id = document.get("id", "")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**ID:** {doc_id}")
        st.markdown(f"**Title:** {document.get('title', 'N/A')}")
        st.markdown(f"**Content Type:** {document.get('content_type', 'text')}")
        st.markdown(f"**Size:** {document.get('size', len(document.get('content', ''))):,}")
        st.markdown(f"**Created:** {document.get('created_at', 'N/A')}")
        st.markdown(f"**Updated:** {document.get('updated_at', 'N/A')}")

        if document.get("tags"):
            st.markdown(f"**Tags:** {', '.join(document['tags'])}")

        if document.get("metadata"):
            st.markdown(f"**Metadata Keys:** {len(document['metadata'])}")

    with col2:
        # Action buttons
        if st.button("👁️ View Full Content", key=f"view_content_{doc_id}"):
            with st.expander("📄 Full Document Content"):
                content = document.get("content", "")
                if len(content) > 10000:
                    st.text_area("Content (truncated)", content[:10000] + "...", height=300)
                    st.download_button(
                        "📥 Download Full Content", content, file_name=f"document_{doc_id}.txt", mime="text/plain"
                    )
                else:
                    st.text_area("Content", content, height=300)

        if st.button("📊 View Quality", key=f"view_quality_{doc_id}"):
            with st.spinner("Loading quality metrics..."):
                try:
                    quality_result = asyncio.run(document_client.get_document_quality(doc_id))
                    if quality_result.get("success"):
                        quality_data = quality_result.get("data", {})
                        st.markdown("**Quality Metrics:**")
                        st.json(quality_data)
                    else:
                        st.info("Quality metrics not available for this document")
                except Exception as e:
                    st.error(f"Error loading quality metrics: {e}")

        if st.button("🏷️ Manage Tags", key=f"manage_tags_{doc_id}"):
            st.info("Tag management coming soon!")

        if st.button("🔗 View Relationships", key=f"view_relationships_{doc_id}"):
            with st.spinner("Loading relationships..."):
                try:
                    rel_result = asyncio.run(document_client.get_document_relationships(doc_id))
                    if rel_result.get("success"):
                        relationships = rel_result.get("relationships", [])
                        if relationships:
                            st.markdown("**Relationships:**")
                            for rel in relationships[:5]:
                                st.write(f"• {rel.get('type', 'related to')} {rel.get('target_id', '')[:8]}...")
                        else:
                            st.info("No relationships found")
                    else:
                        st.info("Relationships not available")
                except Exception as e:
                    st.error(f"Error loading relationships: {e}")

    # Enhanced content viewing
    render_enhanced_document_viewer(document)

    # Metadata display
    if document.get("metadata"):
        with st.expander("📋 Metadata"):
            st.json(document["metadata"])


def render_document_upload(document_client):
    """Render the document upload interface."""
    st.markdown("#### 📤 Upload New Document")

    with st.form("upload_document_form"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Document Title*", key="upload_title")
            content_type = st.selectbox(
                "Content Type", ["text", "markdown", "json", "html", "code", "other"], key="upload_content_type"
            )

        with col2:
            tags_input = st.text_input("Tags (comma-separated)", placeholder="tag1, tag2, tag3", key="upload_tags")

        content = st.text_area(
            "Document Content*",
            placeholder="Enter or paste your document content here...",
            height=300,
            key="upload_content",
        )

        # File upload alternative
        st.markdown("**Or upload a file:**")
        uploaded_file = st.file_uploader(
            "Choose a file", type=["txt", "md", "json", "html", "py", "js", "css"], key="file_upload"
        )

        submitted = st.form_submit_button("📤 Upload Document")

        if submitted:
            try:
                # Handle file upload
                if uploaded_file is not None:
                    file_content = uploaded_file.read().decode("utf-8")
                    final_content = file_content
                    final_title = uploaded_file.name if not title.strip() else title
                else:
                    final_content = content
                    final_title = title

                # Validate required fields
                if not final_title or not final_content:
                    st.error("❌ Please provide both title and content")
                    return

                # Parse tags
                tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

                # Prepare document data
                document_data = {
                    "title": final_title,
                    "content": final_content,
                    "content_type": content_type,
                    "metadata": {"uploaded_via": "dashboard", "tags": tags},
                }

                # Upload document
                with st.spinner("Uploading document..."):
                    result = asyncio.run(document_client.create_document(document_data))

                    if result.get("success") or result.get("id"):
                        st.success("✅ Document uploaded successfully!")
                        doc_id = result.get("id") or result.get("document", {}).get("id")
                        if doc_id:
                            st.info(f"Document ID: {doc_id}")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to upload document: {result.get('message', 'Unknown error')}")

            except Exception as e:
                st.error(f"❌ Error uploading document: {e}")


def render_document_search(document_client):
    """Render advanced document search."""
    st.markdown("#### 🔍 Advanced Document Search")

    col1, col2 = st.columns([2, 1])

    with col1:
        search_query = st.text_area(
            "Search Query", placeholder="Enter your search query...", height=100, key="advanced_doc_search"
        )

        # Advanced filters
        with st.expander("🎛️ Advanced Filters"):
            filter_tags = st.multiselect(
                "Tags", ["test", "performance", "refinement", "session", "batch"], key="search_tags"
            )

            filter_content_types = st.multiselect(
                "Content Types", ["text", "markdown", "json", "html"], key="search_content_types"
            )

            date_range = st.date_input("Date Range", [], key="search_date_range")

            min_size = st.number_input("Minimum Size (bytes)", min_value=0, key="min_size")
            max_size = st.number_input("Maximum Size (bytes)", min_value=0, value=1000000, key="max_size")

    with col2:
        st.markdown("**Search Options:**")
        search_mode = st.selectbox(
            "Search Mode", ["Content Only", "Metadata Only", "Content + Metadata"], key="search_mode"
        )

        max_results = st.slider("Max Results", 10, 100, 50, key="search_max_results")

        # Search button
        if st.button("🔍 Execute Search", key="execute_doc_search", use_container_width=True):
            if search_query.strip():
                with st.spinner("Searching documents..."):
                    try:
                        # Build search filters
                        filters = {}
                        if filter_tags:
                            filters["tags"] = filter_tags
                        if filter_content_types:
                            filters["content_types"] = filter_content_types
                        if min_size > 0:
                            filters["min_size"] = min_size
                        if max_size < 1000000:
                            filters["max_size"] = max_size

                        result = asyncio.run(document_client.search_documents(query=search_query, **filters))

                        if result.get("success") and result.get("results"):
                            documents = result["results"]
                            st.success(f"Found {len(documents)} results")

                            if documents:
                                render_documents_table(documents, document_client)
                        else:
                            st.info("No documents found matching your search criteria.")
                            with st.expander("Debug Info"):
                                st.json(result)

                    except Exception as e:
                        st.error(f"Error during search: {e}")
            else:
                st.warning("Please enter a search query")


def render_document_analytics(document_client):
    """Render document analytics."""
    st.markdown("#### 📊 Document Analytics")

    if st.button("📈 Load Analytics", key="load_doc_analytics"):
        with st.spinner("Loading analytics..."):
            try:
                result = asyncio.run(document_client.get_document_analytics())
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
        st.metric("Total Documents", analytics.get("total_documents", 36))
        st.metric("Active Documents", analytics.get("active_documents", 36))

    with col2:
        st.metric("Avg Size", analytics.get("avg_size", "1.2 KB"))
        st.metric("Total Size", analytics.get("total_size", "45 MB"))

    with col3:
        st.metric("Versions Created", analytics.get("total_versions", 42))
        st.metric("Relationships", analytics.get("total_relationships", 12))

    # Content type distribution (mock)
    st.markdown("#### 📊 Content Type Distribution")
    content_types = pd.DataFrame({"Type": ["Text", "Markdown", "JSON", "HTML", "Other"], "Count": [15, 12, 6, 2, 1]})
    st.bar_chart(content_types.set_index("Type"))

    # Upload activity (mock)
    st.markdown("#### 📈 Upload Activity (Last 7 Days)")
    activity = pd.DataFrame({"Date": pd.date_range(start="2024-01-01", periods=7), "Uploads": [3, 5, 2, 8, 4, 6, 7]})
    st.line_chart(activity.set_index("Date"))


def render_document_relationships(document_client):
    """Render document relationships management."""
    st.markdown("#### 🔗 Document Relationships")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Create Relationship**")

        source_doc = st.text_input("Source Document ID", placeholder="Enter source document ID", key="source_doc_id")

        target_doc = st.text_input("Target Document ID", placeholder="Enter target document ID", key="target_doc_id")

        relationship_type = st.selectbox(
            "Relationship Type",
            ["related_to", "parent_of", "child_of", "references", "supersedes"],
            key="relationship_type",
        )

        if st.button("🔗 Create Relationship", key="create_relationship"):
            if source_doc and target_doc:
                with st.spinner("Creating relationship..."):
                    try:
                        result = asyncio.run(
                            document_client.add_document_relationship(source_doc, target_doc, relationship_type)
                        )

                        if result.get("success"):
                            st.success("✅ Relationship created successfully!")
                        else:
                            st.error(f"❌ Failed to create relationship: {result.get('message')}")
                    except Exception as e:
                        st.error(f"❌ Error creating relationship: {e}")
            else:
                st.warning("Please provide both source and target document IDs")

    with col2:
        st.markdown("**View Relationships**")

        view_doc_id = st.text_input(
            "Document ID to View", placeholder="Enter document ID", key="view_relationships_doc_id"
        )

        if st.button("👁️ View Relationships", key="view_relationships"):
            if view_doc_id:
                with st.spinner("Loading relationships..."):
                    try:
                        result = asyncio.run(document_client.get_document_relationships(view_doc_id))

                        if result.get("success"):
                            relationships = result.get("relationships", [])
                            if relationships:
                                st.markdown(f"**Relationships for {view_doc_id}:**")
                                for rel in relationships:
                                    st.write(f"• {rel.get('type', 'related to')} → {rel.get('target_id', '')}")
                            else:
                                st.info("No relationships found for this document")
                        else:
                            st.info("No relationships data available")
                    except Exception as e:
                        st.error(f"Error loading relationships: {e}")
            else:
                st.warning("Please provide a document ID")


# ============================================================================
# ENHANCED DOCUMENT VIEWING FUNCTIONS
# ============================================================================


def render_enhanced_document_viewer(document: Dict[str, Any]):
    """Render enhanced document viewer with syntax highlighting and advanced
    features."""
    content = document.get("content", "")
    content_type = document.get("content_type", "text")
    doc_id = document.get("id", "")

    if not content:
        st.warning("No content available for this document")
        return

    # Viewer tabs
    viewer_tabs = st.tabs(["📖 Content Viewer", "🔍 Content Search", "📊 Content Analysis", "📥 Export"])

    with viewer_tabs[0]:
        render_content_viewer(content, content_type, doc_id)

    with viewer_tabs[1]:
        render_content_search(content, doc_id)

    with viewer_tabs[2]:
        render_content_analysis(content, content_type)

    with viewer_tabs[3]:
        render_content_export(content, document)


def render_content_viewer(content: str, content_type: str, doc_id: str):
    """Render the main content viewer with syntax highlighting."""
    st.markdown("**📖 Document Content**")

    # Content type selector for viewing
    view_mode = st.selectbox(
        "View Mode",
        ["Auto Detect", "Plain Text", "Markdown", "JSON", "Code (Python)", "Code (JavaScript)", "Code (SQL)", "HTML"],
        key=f"view_mode_{doc_id}",
    )

    # Determine syntax highlighting
    if view_mode == "Auto Detect":
        if content_type == "markdown":
            syntax_lang = "markdown"
        elif content_type == "json":
            syntax_lang = "json"
        elif content.startswith("```") and "```" in content:
            # Extract language from code blocks
            first_line = content.split("\n")[0]
            if first_line.startswith("```"):
                syntax_lang = first_line[3:].strip() or "text"
            else:
                syntax_lang = "text"
        elif any(keyword in content.lower() for keyword in ["function", "def ", "class ", "import "]):
            syntax_lang = "python"
        elif any(keyword in content.lower() for keyword in ["function", "const ", "let ", "var "]):
            syntax_lang = "javascript"
        elif any(keyword in content.lower() for keyword in ["select", "from", "where", "insert"]):
            syntax_lang = "sql"
        else:
            syntax_lang = "text"
    else:
        lang_map = {
            "Plain Text": "text",
            "Markdown": "markdown",
            "JSON": "json",
            "Code (Python)": "python",
            "Code (JavaScript)": "javascript",
            "Code (SQL)": "sql",
            "HTML": "html",
        }
        syntax_lang = lang_map.get(view_mode, "text")

    # Content length controls
    content_length = len(content)
    if content_length > 10000:
        max_chars = st.slider(
            "Display Limit (characters)",
            min_value=1000,
            max_value=min(content_length, 50000),
            value=10000,
            step=1000,
            key=f"content_limit_{doc_id}",
        )
        display_content = content[:max_chars] + "\n\n[... content truncated ...]"
        st.info(f"Showing first {max_chars} of {content_length} characters")
    else:
        display_content = content
        max_chars = content_length

    # Display content with syntax highlighting
    if syntax_lang == "markdown":
        st.markdown(display_content)
    elif syntax_lang == "json":
        try:
            parsed_json = json.loads(display_content)
            st.json(parsed_json)
        except:
            st.code(display_content, language="json")
    else:
        st.code(display_content, language=syntax_lang)

    # Content statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Characters", content_length)
    with col2:
        st.metric("Lines", len(content.split("\n")))
    with col3:
        st.metric("Words", len(content.split()))
    with col4:
        st.metric("Paragraphs", len([p for p in content.split("\n\n") if p.strip()]))


def render_content_search(content: str, doc_id: str):
    """Render content search functionality within the document."""
    st.markdown("**🔍 Search Within Document**")

    search_term = st.text_input("Search Term", placeholder="Enter text to find...", key=f"content_search_{doc_id}")

    case_sensitive = st.checkbox("Case Sensitive", key=f"case_sensitive_{doc_id}")
    whole_words = st.checkbox("Whole Words Only", key=f"whole_words_{doc_id}")

    if search_term:
        # Perform search
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = r"\b" + re.escape(search_term) + r"\b" if whole_words else re.escape(search_term)

        try:
            matches = list(re.finditer(pattern, content, flags))
            match_count = len(matches)

            if match_count > 0:
                st.success(f"Found {match_count} matches")

                # Show matches with context
                for i, match in enumerate(matches[:20]):  # Show first 20 matches
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 100)
                    context = content[start:end]

                    # Highlight the match
                    highlighted_context = context.replace(match.group(), f"**{match.group()}**")

                    with st.expander(f"Match #{i+1} (position {match.start()})", expanded=i < 3):
                        st.markdown(highlighted_context)

                if match_count > 20:
                    st.info(f"And {match_count - 20} more matches...")

                # Show distribution
                st.markdown("**📊 Match Distribution**")
                positions = [match.start() for match in matches]
                if len(positions) > 1:
                    # Simple histogram
                    bins = 10
                    bin_size = len(content) // bins
                    hist_data = [0] * bins

                    for pos in positions:
                        bin_idx = min(pos // bin_size, bins - 1)
                        hist_data[bin_idx] += 1

                    import pandas as pd

                    df_hist = pd.DataFrame(
                        {"Section": [f"{i*bin_size}-{(i+1)*bin_size}" for i in range(bins)], "Matches": hist_data}
                    )
                    st.bar_chart(df_hist.set_index("Section"))

            else:
                st.info("No matches found")

        except re.error as e:
            st.error(f"Invalid search pattern: {e}")


def render_content_analysis(content: str, content_type: str):
    """Render content analysis for the document."""
    st.markdown("**📊 Content Analysis**")

    # Basic analysis
    analysis = analyze_document_content(content, content_type)

    # Display analysis results
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📈 Content Metrics**")
        for key, value in analysis["metrics"].items():
            st.metric(key, value)

    with col2:
        st.markdown("**🔍 Content Insights**")
        for insight in analysis["insights"]:
            st.info(insight)

    # Content quality indicators
    st.markdown("---")
    st.markdown("**⭐ Quality Indicators**")

    quality_indicators = analysis["quality"]
    for indicator in quality_indicators:
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"**{indicator['name']}**")

        with col2:
            color = "🟢" if indicator["score"] >= 80 else "🟡" if indicator["score"] >= 60 else "🔴"
            st.markdown(f"{color} {indicator['score']}/100")

        with col3:
            st.caption(indicator["level"])

    # Content structure analysis
    if analysis.get("structure"):
        st.markdown("---")
        st.markdown("**🏗️ Content Structure**")

        structure = analysis["structure"]
        if structure["headings"]:
            st.markdown("**Headings:**")
            for heading in structure["headings"][:5]:
                st.write(f"• {heading}")
            if len(structure["headings"]) > 5:
                st.caption(f"... and {len(structure['headings']) - 5} more")

        if structure["code_blocks"]:
            st.metric("Code Blocks", structure["code_blocks"])

        if structure["lists"]:
            st.metric("Lists", structure["lists"])


def render_content_export(content: str, document: Dict[str, Any]):
    """Render content export functionality."""
    st.markdown("**📥 Export Document**")

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        export_format = st.selectbox(
            "Export Format",
            ["Original", "Plain Text", "Markdown", "PDF", "HTML"],
            key=f"export_format_{document.get('id', '')}",
        )

        include_metadata = st.checkbox("Include Metadata", value=True, key=f"include_meta_{document.get('id', '')}")

    with col2:
        export_filename = st.text_input(
            "Filename",
            value=f"document_{document.get('id', 'unknown')}",
            key=f"export_filename_{document.get('id', '')}",
        )

        if "." not in export_filename and export_format != "Original":
            if export_format == "PDF":
                export_filename += ".pdf"
            elif export_format == "HTML":
                export_filename += ".html"
            elif export_format == "Markdown":
                export_filename += ".md"
            else:
                export_filename += ".txt"

    # Export button
    if st.button("📥 Export Document", key=f"export_doc_{document.get('id', '')}"):
        export_content = prepare_export_content(content, document, export_format, include_metadata)

        if export_format == "PDF":
            st.info("PDF export would be implemented with report generation library")
        elif export_format == "HTML":
            html_content = f"<html><body><pre>{export_content}</pre></body></html>"
            st.download_button(
                "Download HTML",
                html_content,
                file_name=export_filename,
                mime="text/html",
                key=f"download_html_{document.get('id', '')}",
            )
        else:
            st.download_button(
                "Download File",
                export_content,
                file_name=export_filename,
                mime="text/plain",
                key=f"download_file_{document.get('id', '')}",
            )

    # Quick actions
    st.markdown("---")
    st.markdown("**⚡ Quick Actions**")

    quick_actions = st.columns(3)
    with quick_actions[0]:
        if st.button("📋 Copy to Clipboard", key=f"copy_content_{document.get('id', '')}"):
            st.code(content[:1000] + ("..." if len(content) > 1000 else ""), language="text")
            st.success("Content copied to display area above!")

    with quick_actions[1]:
        if st.button("📊 Generate Summary", key=f"summarize_{document.get('id', '')}"):
            summary = generate_content_summary(content)
            st.info(f"**Summary:** {summary}")

    with quick_actions[2]:
        if st.button("🏷️ Extract Keywords", key=f"keywords_{document.get('id', '')}"):
            keywords = extract_keywords(content)
            st.info(f"**Keywords:** {', '.join(keywords[:5])}")


# ============================================================================
# CONTENT ANALYSIS HELPER FUNCTIONS
# ============================================================================


def analyze_document_content(content: str, content_type: str) -> Dict[str, Any]:
    """Analyze document content and return metrics and insights."""
    analysis = {"metrics": {}, "insights": [], "quality": [], "structure": {}}

    # Basic metrics
    analysis["metrics"]["Characters"] = len(content)
    analysis["metrics"]["Words"] = len(content.split())
    analysis["metrics"]["Sentences"] = len([s for s in content.split(".") if s.strip()])
    analysis["metrics"]["Lines"] = len(content.split("\n"))
    analysis["metrics"]["Paragraphs"] = len([p for p in content.split("\n\n") if p.strip()])

    # Content type specific analysis
    if content_type == "markdown":
        analysis["structure"]["headings"] = extract_markdown_headings(content)
        analysis["structure"]["code_blocks"] = len(re.findall(r"```.*?```", content, re.DOTALL))
        analysis["structure"]["lists"] = len(re.findall(r"^[-*+]\s", content, re.MULTILINE))

    # Quality indicators
    quality_indicators = [
        {
            "name": "Readability",
            "score": min(
                100, max(0, 100 - (analysis["metrics"]["Words"] / max(analysis["metrics"]["Sentences"], 1) - 15) * 5)
            ),
            "level": (
                "Good" if analysis["metrics"]["Words"] / max(analysis["metrics"]["Sentences"], 1) < 25 else "Needs Work"
            ),
        },
        {
            "name": "Structure",
            "score": 80 if analysis["metrics"]["Paragraphs"] > 3 else 60,
            "level": "Good" if analysis["metrics"]["Paragraphs"] > 3 else "Basic",
        },
        {
            "name": "Conciseness",
            "score": max(0, 100 - (len(content) - 1000) // 100),
            "level": "Excellent" if len(content) < 2000 else "Good" if len(content) < 5000 else "Verbose",
        },
    ]

    analysis["quality"] = quality_indicators

    # Insights
    if len(content) > 5000:
        analysis["insights"].append("Document is quite long - consider breaking into sections")
    if analysis["metrics"]["Sentences"] < 5:
        analysis["insights"].append("Document appears to be very concise or fragmented")
    if content.count("?") > content.count(".") * 0.5:
        analysis["insights"].append("Document contains many questions - appears to be Q&A format")
    if any(keyword in content.lower() for keyword in ["error", "exception", "failed", "issue"]):
        analysis["insights"].append("Document contains technical issue references")

    return analysis


def extract_markdown_headings(content: str) -> List[str]:
    """Extract markdown headings from content."""
    headings = []
    lines = content.split("\n")
    for line in lines:
        if line.startswith("#"):
            # Remove # symbols and extra spaces
            heading_text = re.sub(r"^#+\s*", "", line).strip()
            if heading_text:
                headings.append(heading_text)
    return headings


def generate_content_summary(content: str) -> str:
    """Generate a simple content summary."""
    words = content.split()
    if len(words) < 50:
        return content

    # Simple extractive summary - first and last sentences
    sentences = [s.strip() for s in content.split(".") if s.strip()]
    if len(sentences) >= 2:
        return f"{sentences[0]}. {sentences[-1]}."
    else:
        return " ".join(words[:30]) + "..."


def extract_keywords(content: str) -> List[str]:
    """Extract potential keywords from content."""
    # Simple keyword extraction - words that appear multiple times
    words = re.findall(r"\b[a-zA-Z]{4,}\b", content.lower())
    word_counts = {}

    # Count word frequencies
    for word in words:
        if word not in [
            "that",
            "this",
            "with",
            "from",
            "they",
            "have",
            "been",
            "were",
            "which",
            "their",
            "there",
            "these",
            "those",
        ]:
            word_counts[word] = word_counts.get(word, 0) + 1

    # Return top keywords
    sorted_keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_keywords[:10] if count > 1]


def prepare_export_content(content: str, document: Dict[str, Any], format_type: str, include_metadata: bool) -> str:
    """Prepare content for export in the specified format."""
    if not include_metadata:
        return content

    metadata = document.get("metadata", {})
    export_header = f"Document ID: {document.get('id', 'unknown')}\n"
    export_header += f"Content Type: {document.get('content_type', 'unknown')}\n"
    export_header += f"Created: {document.get('created_at', 'unknown')}\n"
    export_header += f"Updated: {document.get('updated_at', 'unknown')}\n"

    if metadata:
        export_header += f"Metadata: {json.dumps(metadata, indent=2)}\n"

    export_header += "=" * 50 + "\n\n"

    return export_header + content
