"""
Documentation Generator

Enhanced with proper timeouts, tier selection, and feedback.
"""

import streamlit as st
import httpx
import time
from datetime import datetime
from typing import List, Dict, Any

# Import state manager
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.state_manager import StateManager


def show(api_base_url: str):
    """Display documentation generator page with enhanced feedback."""
    st.title("📖 Documentation Generator")
    st.markdown("Generate comprehensive documentation using multi-pass RAG queries")
    
    # Initialize state manager
    StateManager.initialize()
    
    # Initialize session state (legacy support)
    if "generation_results" not in st.session_state:
        st.session_state.generation_results = {}
    if "generation_metrics" not in st.session_state:
        st.session_state.generation_metrics = []
    if "generating" not in st.session_state:
        st.session_state.generating = False
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚙️ Configure",
        "📊 Generate",
        "📄 Results",
        "🎯 Quality Metrics"
    ])
    
    # ============================================================================
    # Tab 1: Configuration
    # ============================================================================
    with tab1:
        st.header("⚙️ Generation Configuration")
        
        with st.form("doc_config_form"):
            # Directory selection
            st.markdown("### 📁 Source Directory")
            
            # Path type selector
            directory_type = st.radio(
                "Directory Type",
                options=["Container Path", "Host Machine Path"],
                index=1,  # Default to Host Machine Path
                help="""
                - **Container Path**: Path inside Docker container (e.g., /app)
                - **Host Machine Path**: Path on your local machine
                """,
                horizontal=True
            )
            
            if directory_type == "Host Machine Path":
                directory = st.text_input(
                    "Directory Path",
                    value="/Users/mykalthomas/Documents/work/Hackathon",
                    help="Path on your host machine to analyze. Git root will be auto-detected."
                )
                st.info("""
                💡 **Default:** Hackathon project directory
                - Generate documentation for your local codebase
                - Auto-detects git root
                - Works with temporal versioning
                """)
            else:
                directory = st.text_input(
                    "Directory Path",
                    value="/app",
                    help="Path inside the container (e.g., /app)"
                )
                st.info("""
                💡 **Container Path:** `/app` - The mounted workspace directory
                - Contains all your codebase
                - Accessible from the container
                - Already indexed in the database
                """)
            
            st.markdown("---")
            
            # Service selection (CRITICAL FOR FILTERING)
            st.markdown("### 🎯 Service Selection")
            st.warning("⚠️ **IMPORTANT**: Select which service's documents to use for generation")
            
            service_name = st.selectbox(
                "Target Service",
                options=["adminservice", "Hackathon", "All Services (No Filter)"],
                index=0,  # Default to adminservice
                help="""
                **Choose which service to generate documentation for:**
                - **adminservice**: Use only adminservice documents (Scala/Play Framework)
                - **Hackathon**: Use only Hackathon/ecosystem-mcp documents
                - **All Services**: Query across all services (may mix results)
                
                ⚠️ If you recently ingested new documents, make sure to select the correct service!
                """
            )
            
            # Show what's in the database
            st.caption(f"📊 Currently in database: Hackathon (955 docs), adminservice (868 docs)")
            
            # Convert to API format
            service_filter = None if service_name == "All Services (No Filter)" else service_name
            
            if service_filter:
                st.success(f"✅ Will query **{service_filter}** documents only")
            else:
                st.info("ℹ️ Will query across all services")
            
            st.markdown("---")
            
            # Documentation sections
            st.markdown("### 📚 Sections to Generate")
            
            col1, col2 = st.columns(2)
            
            with col1:
                include_overview = st.checkbox("📋 Overview", value=True)
                include_architecture = st.checkbox("🏗️ Architecture", value=True)
                include_api = st.checkbox("🔌 API Reference", value=True)
            
            with col2:
                include_setup = st.checkbox("🚀 Setup Guide", value=False)
                include_examples = st.checkbox("💡 Examples", value=False)
                include_troubleshooting = st.checkbox("🔧 Troubleshooting", value=False)
            
            st.markdown("---")
            
            # Multi-pass settings
            st.markdown("### 🔄 Multi-Pass Configuration")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                num_passes = st.slider(
                    "Passes per Section",
                    min_value=1,
                    max_value=5,
                    value=2,
                    help="More passes = more comprehensive but slower"
                )
            
            with col2:
                queries_per_pass = st.slider(
                    "Queries per Pass",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="Number of questions to ask per pass"
                )
            
            with col3:
                n_results = st.slider(
                    "Documents per Query",
                    min_value=5,
                    max_value=30,
                    value=10,
                    help="Number of documents to retrieve"
                )
            
            st.markdown("---")
            
            # LLM Tier Selection (NEW)
            st.markdown("### 🤖 LLM Tier Selection")
            
            tier = st.selectbox(
                "Preferred LLM Tier",
                options=["desktop", "auto", "docker"],
                index=0,
                help="""
                **desktop**: Use Desktop Ollama (GPU, fastest) - RECOMMENDED
                **auto**: Automatic complexity-based routing
                **docker**: Use Docker Ollama (CPU, always available)
                
                Desktop Ollama is preferred for documentation generation as it's faster and more reliable.
                Will automatically fall back to Docker if Desktop is unavailable.
                """
            )
            
            if tier == "desktop":
                st.success("✅ Will use Desktop Ollama (GPU) with fallback to Docker")
            elif tier == "auto":
                st.info("ℹ️ Will analyze complexity and route automatically")
            else:
                st.warning("⚠️ Will use Docker Ollama (slower, CPU-based)")
            
            st.markdown("---")
            
            # Generation settings
            st.markdown("### ⚙️ Generation Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                response_length = st.select_slider(
                    "Response Length",
                    options=["S", "M", "L", "XL"],
                    value="L",
                    help="S=512, M=1024, L=2048, XL=4096 tokens"
                )
                
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    step=0.1,
                    help="0.0=Focused, 1.0=Creative"
                )
            
            with col2:
                use_cache = st.checkbox("Use Cache", value=True, help="Speed up with caching")
                include_sources = st.checkbox("Include Sources", value=True, help="Add source citations")
            
            # Timeout settings (NEW)
            st.markdown("---")
            st.markdown("### ⏱️ Timeout Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                query_timeout = st.number_input(
                    "Query Timeout (seconds)",
                    min_value=60,
                    max_value=600,
                    value=300,
                    step=30,
                    help="Timeout for each individual query (5min default)"
                )
            
            with col2:
                max_retries = st.number_input(
                    "Max Retries per Query",
                    min_value=0,
                    max_value=5,
                    value=2,
                    help="Number of retries if a query fails"
                )
            
            st.info(f"""
            ⏱️ **Time Estimates:**
            - Per query: ~{query_timeout}s max
            - Total queries: {sum([include_overview, include_architecture, include_api, include_setup, include_examples, include_troubleshooting]) * num_passes * queries_per_pass}
            - Estimated total: ~{sum([include_overview, include_architecture, include_api, include_setup, include_examples, include_troubleshooting]) * num_passes * queries_per_pass * 10 / 60:.1f} minutes
            - With {tier} tier for optimal performance
            """)
            
            # Documentation Run Persistence (NEW)
            st.markdown("---")
            st.markdown("### 💾 Documentation Run Persistence")
            
            persist_run = st.checkbox(
                "Save Generated Documentation",
                value=True,
                help="Persist generated documents to database for future reference"
            )
            
            if persist_run:
                run_name = st.text_input(
                    "Run Name",
                    value=f"Documentation - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    help="Descriptive name for this documentation run"
                )
                
                run_description = st.text_area(
                    "Description (Optional)",
                    value="",
                    help="Brief description of this documentation generation",
                    height=80
                )
                
                st.success("""
                ✅ **Documentation will be saved with:**
                - Run metadata (config, timing, stats)
                - All generated documents with full content
                - Browseable via Documentation Browser
                - Exportable as ZIP archive
                """)
            else:
                run_name = ""
                run_description = ""
                st.info("ℹ️ Documents will be generated but not persisted to database")
            
            # Submit
            submitted = st.form_submit_button("💾 Save Configuration", use_container_width=True)
            
            if submitted:
                # Build sections list
                sections = []
                if include_overview: sections.append("OVERVIEW")
                if include_architecture: sections.append("ARCHITECTURE")
                if include_api: sections.append("API")
                if include_setup: sections.append("SETUP")
                if include_examples: sections.append("EXAMPLES")
                if include_troubleshooting: sections.append("TROUBLESHOOTING")
                
                # Build pass names
                pass_names = []
                for i in range(num_passes):
                    if i == 0:
                        pass_names.append("initial")
                    elif i == 1:
                        pass_names.append("deep_dive")
                    else:
                        pass_names.append(f"pass_{i+1}")
                
                # Save config
                st.session_state.doc_config = {
                    "directory": directory,
                    "service_filter": service_filter,  # Add service filter
                    "sections": sections,
                    "passes": pass_names,
                    "queries_per_pass": queries_per_pass,
                    "n_results": n_results,
                    "response_length": response_length,
                    "temperature": temperature,
                    "use_cache": use_cache,
                    "include_sources": include_sources,
                    "tier": tier,
                    "query_timeout": query_timeout,
                    "max_retries": max_retries,
                    "persist_run": persist_run,
                    "run_name": run_name,
                    "run_description": run_description
                }
                
                if persist_run:
                    st.success(f"✅ Configuration saved! Ready to generate and persist {len(sections)} sections with {tier} tier.")
                    st.info("📋 Switch to the **Generate** tab to start. Documents will be saved to database.")
                else:
                    st.success(f"✅ Configuration saved! Ready to generate {len(sections)} sections with {tier} tier.")
                    st.info("📋 Switch to the **Generate** tab to start.")
    
    # ============================================================================
    # Tab 2: Generate
    # ============================================================================
    with tab2:
        st.header("📊 Generate Documentation")
        
        if "doc_config" not in st.session_state:
            st.warning("⚠️ Please configure documentation settings in the **Configure** tab first.")
            st.stop()
        
        config = st.session_state.doc_config
        
        # ============================================================================
        # PRE-GENERATION VALIDATIONS
        # ============================================================================
        st.markdown("### ✅ Pre-Generation Checks")
        
        validation_passed = True
        
        # Check 1: Service Filter Validation
        service_filter = config.get('service_filter', '')
        if not service_filter or service_filter == 'All services' or service_filter.lower() == 'unknown':
            st.error("❌ **Service Filter Required:** Please specify a valid service name (e.g., 'adminservice')")
            st.info("💡 Go to **Repository Discovery** to see available services")
            validation_passed = False
        else:
            st.success(f"✅ Service filter set to: '{service_filter}'")
        
        st.markdown("---")
        
        # Show configuration summary
        st.markdown("### 📋 Generation Plan")
        
        # Show service filter prominently
        if config.get('service_filter'):
            st.success(f"🎯 **Target Service:** {config['service_filter']}")
        else:
            st.warning("⚠️ **No service filter** - queries will span all services")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Sections", len(config['sections']))
            st.metric("Passes per Section", len(config['passes']))
        
        with col2:
            st.metric("Queries per Pass", config['queries_per_pass'])
            total_queries = len(config['sections']) * len(config['passes']) * config['queries_per_pass']
            st.metric("Total Queries", total_queries)
        
        with col3:
            st.metric("LLM Tier", config['tier'].upper())
            est_time = total_queries * 10 / 60
            st.metric("Est. Time", f"~{est_time:.1f}min")
        
        # Show sections
        st.markdown("**Sections to Generate:**")
        st.write(", ".join(config['sections']))
        
        st.markdown("---")
        
        # Start button
        if not st.session_state.get("generating", False):
            if st.button("🚀 Start Generation", type="primary", use_container_width=True, disabled=not validation_passed):
                if not validation_passed:
                    st.error("❌ Cannot start generation. Please fix validation errors above.")
                    st.stop()
                
                st.session_state.generating = True
                st.session_state.generation_start_time = time.time()
                st.session_state.generation_results = {}
                st.session_state.generation_metrics = []
                
                # Register process with state manager
                generation_id = f"doc_gen_{int(time.time())}"
                StateManager.register_process(
                    process_id=generation_id,
                    process_type="generation",
                    description=f"Documentation generation for {config.get('directory', 'unknown')}",
                    metadata={
                        "sections": config['sections'],
                        "total_queries": len(config['sections']) * len(config['passes']) * config['queries_per_pass'],
                        "tier": config['tier']
                    }
                )
                st.session_state.generation_process_id = generation_id
                
                st.rerun()
        
        # Generation in progress
        if st.session_state.get("generating", False):
            st.info("🔄 Generation in progress...")
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            metrics_placeholder = st.empty()
            
            # Generate documentation section by section
            total_sections = len(config['sections'])
            
            for i, section in enumerate(config['sections']):
                section_start = time.time()
                status_text.markdown(f"### 📝 Generating: **{section}** ({i+1}/{total_sections})")
                
                section_content = []
                pass_count = 0
                
                # Run each pass for this section
                for pass_idx, pass_name in enumerate(config['passes']):
                    pass_start = time.time()
                    
                    # Show current pass
                    metrics_placeholder.info(f"""
                    🔄 **Current Progress:**
                    - Section: {section} ({i+1}/{total_sections})
                    - Pass: {pass_name} ({pass_idx+1}/{len(config['passes'])})
                    - Tier: {config['tier'].upper()}
                    - Timeout: {config['query_timeout']}s per query
                    """)
                    
                    pass_content = generate_pass(
                        api_base_url=api_base_url,
                        section=section,
                        pass_name=pass_name,
                        config=config
                    )
                    
                    if pass_content:
                        section_content.append(pass_content)
                        pass_count += 1
                    
                    pass_time = time.time() - pass_start
                    
                    # Log metrics
                    st.session_state.generation_metrics.append({
                        "section": section,
                        "pass": pass_name,
                        "duration": pass_time,
                        "success": bool(pass_content)
                    })
                
                # Combine pass results with run ID header
                if section_content:
                    content_with_id = f"<!-- Section: {section} | Run ID: {generation_run_id} -->\n\n" + "\n\n".join(section_content)
                    st.session_state.generation_results[section] = content_with_id
                    section_time = time.time() - section_start
                    st.success(f"✅ {section} complete ({pass_count} passes, {section_time:.1f}s)")
                else:
                    st.error(f"❌ {section} failed - no content generated")
                
                # Update progress
                progress_bar.progress((i + 1) / total_sections)
                
                # Update process status
                if "generation_process_id" in st.session_state:
                    progress_percent = ((i + 1) / total_sections) * 100
                    StateManager.update_process_status(
                        st.session_state.generation_process_id,
                        status="running",
                        progress=progress_percent
                    )
            
            # Generation complete
            st.session_state.generating = False
            generation_time = time.time() - st.session_state.generation_start_time
            
            # Mark process as complete
            if "generation_process_id" in st.session_state:
                StateManager.complete_process(
                    st.session_state.generation_process_id,
                    result={"sections": len(st.session_state.generation_results), "duration": generation_time}
                )
            
            # Save generated content to state manager for persistence
            for section, content in st.session_state.generation_results.items():
                StateManager.save_generated_content(
                    key=f"doc_{section}_{int(time.time())}",
                    content=content,
                    metadata={
                        "section": section,
                        "directory": config.get('directory'),
                        "tier": config.get('tier')
                    }
                )
            
            st.success(f"🎉 Documentation generated in {generation_time:.1f} seconds!")
            st.balloons()
            
            # Save metrics
            if st.session_state.generation_metrics:
                total_queries = len(st.session_state.generation_metrics)
                successful = sum(1 for m in st.session_state.generation_metrics if m['success'])
                
                st.info(f"""
                📊 **Generation Summary:**
                - Total queries: {total_queries}
                - Successful: {successful} ({successful/total_queries*100:.1f}%)
                - Failed: {total_queries - successful}
                - Total time: {generation_time:.1f}s
                - Avg per query: {generation_time/total_queries:.1f}s
                - LLM Tier: {config['tier'].upper()}
                """)
            
            # Persist documentation run if enabled
            if config.get('persist_run', False):
                with st.spinner("💾 Saving documentation to database..."):
                    try:
                        # Create documentation run
                        run_response = httpx.post(
                            f"{api_base_url}/api/v1/documentation/runs",
                            json={
                                "name": config.get('run_name', f"Documentation - {datetime.now().strftime('%Y-%m-%d %H:%M')}"),
                                "description": config.get('run_description', ''),
                                "source_directory": config['directory'],
                                "output_format": "markdown",
                                "response_size": config.get('response_length', 'L'),
                                "tier": config.get('tier', 'auto'),
                                "num_passes": len(config['passes']),
                                "questions_per_pass": config['queries_per_pass'],
                                "created_by": "dashboard_user"
                            },
                            timeout=30.0
                        )
                        
                        if run_response.status_code == 200:
                            run_data = run_response.json()
                            run_id = run_data['run_id']
                            
                            # Mark run as started
                            httpx.put(
                                f"{api_base_url}/api/v1/documentation/runs/{run_id}/start",
                                json={"output_directory": "/tmp/docs"},
                                timeout=10.0
                            )
                            
                            # Save each generated document
                            docs_saved = 0
                            for section, content in st.session_state.generation_results.items():
                                doc_response = httpx.post(
                                    f"{api_base_url}/api/v1/documentation/runs/{run_id}/documents",
                                    json={
                                        "title": section,
                                        "filename": f"{section.lower()}.md",
                                        "content": content,
                                        "pass_number": len(config['passes']),
                                        "question": f"Generated documentation for {section}"
                                    },
                                    timeout=30.0
                                )
                                
                                if doc_response.status_code == 200:
                                    docs_saved += 1
                            
                            # Mark run as completed
                            httpx.put(
                                f"{api_base_url}/api/v1/documentation/runs/{run_id}/complete",
                                json={
                                    "status": "completed",
                                    "total_docs": len(st.session_state.generation_results),
                                    "successful_docs": docs_saved,
                                    "failed_docs": len(st.session_state.generation_results) - docs_saved
                                },
                                timeout=10.0
                            )
                            
                            st.success(f"""
                            ✅ **Documentation saved to database!**
                            - Run ID: `{run_id[:8]}...`
                            - Documents saved: {docs_saved}/{len(st.session_state.generation_results)}
                            - Browse in: 📚 Documentation Browser
                            """)
                            
                            # Store run ID for later reference
                            st.session_state['last_doc_run_id'] = run_id
                        else:
                            st.error(f"❌ Failed to create documentation run: HTTP {run_response.status_code}")
                    
                    except Exception as e:
                        st.error(f"❌ Error saving documentation: {str(e)}")
                        st.info("Documents are still available in the Results tab")
            
            st.info("📄 Switch to the **Results** tab to view and download documentation.")
    
    # ============================================================================
    # Tab 3: Results
    # ============================================================================
    with tab3:
        st.header("📄 Generated Documentation")
        
        # Display current generation run ID if available
        if st.session_state.get('current_generation_run_id'):
            gen_run_id = st.session_state['current_generation_run_id']
            st.code(f"🆔 Generation Run ID: {gen_run_id}", language="text")
        
        # Show link to saved run if persisted
        if st.session_state.get('last_doc_run_id'):
            run_id = st.session_state['last_doc_run_id']
            
            # Add option to fetch from database instead of using session state
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.info(f"""
                💾 **Last Saved to Database:** `{run_id}`
                
                📚 **Browse in:** Documentation Browser → Run History
                🔍 **Filter by:** `{run_id[:8]}`
                """)
            
            with col2:
                if st.button("🔄 Refresh", help="Fetch latest from database"):
                    # Fetch documents from database
                    try:
                        response = httpx.get(
                            f"{api_base_url}/api/v1/documentation/runs/{run_id}/documents",
                            params={"limit": 100},
                            timeout=30.0
                        )
                        
                        if response.status_code == 200:
                            documents = response.json()
                            
                            # Update session state with fresh data
                            st.session_state.generation_results = {}
                            for doc in documents:
                                # Fetch full content
                                content_response = httpx.get(
                                    f"{api_base_url}/api/v1/documentation/documents/{doc['id']}",
                                    timeout=30.0
                                )
                                if content_response.status_code == 200:
                                    content_data = content_response.json()
                                    st.session_state.generation_results[doc['title']] = content_data['content']
                            
                            st.success(f"✅ Refreshed! Loaded {len(documents)} document(s)")
                            st.rerun()
                        else:
                            st.error(f"Failed to fetch: HTTP {response.status_code}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                
                if st.button("🗑️ Clear", help="Clear session results"):
                    st.session_state.generation_results = {}
                    if 'last_doc_run_id' in st.session_state:
                        del st.session_state['last_doc_run_id']
                    st.rerun()
            
            st.markdown("---")
        
        if not st.session_state.generation_results:
            st.info("No documentation in session. Configure and generate first, or click Refresh above to load from database.")
            st.stop()
        
        # Display each section
        for section, content in st.session_state.generation_results.items():
            with st.expander(f"📄 {section}", expanded=False):
                st.markdown(content)
                
                # Download button for this section
                st.download_button(
                    label=f"⬇️ Download {section}",
                    data=content,
                    file_name=f"{section.lower()}.md",
                    mime="text/markdown",
                    key=f"download_{section}"
                )
        
        st.markdown("---")
        
        # Download all
        all_content = "\n\n---\n\n".join([
            f"# {section}\n\n{content}"
            for section, content in st.session_state.generation_results.items()
        ])
        
        st.download_button(
            label="⬇️ Download All Documentation",
            data=all_content,
            file_name="complete_documentation.md",
            mime="text/markdown",
            use_container_width=True
        )
        
        # Metrics
        if st.session_state.generation_metrics:
            st.markdown("---")
            st.markdown("### 📊 Generation Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Sections", len(st.session_state.generation_results))
            
            with col2:
                total_queries = len(st.session_state.generation_metrics)
                st.metric("Total Queries", total_queries)
            
            with col3:
                successful = sum(1 for m in st.session_state.generation_metrics if m['success'])
                st.metric("Success Rate", f"{successful/total_queries*100:.1f}%")
            
            with col4:
                total_time = sum(m['duration'] for m in st.session_state.generation_metrics)
                st.metric("Total Time", f"{total_time:.1f}s")
            
            # Detailed metrics
            with st.expander("📈 Detailed Metrics"):
                st.json(st.session_state.generation_metrics)
    
    # ============================================================================
    # Tab 4: Quality Metrics
    # ============================================================================
    with tab4:
        st.header("🎯 Quality Metrics")
        st.markdown("Validate and monitor documentation quality after generation")
        
        # Check if documentation has been generated
        if not st.session_state.generation_results:
            st.info("📭 No documentation generated yet. Generate documentation first in the Generate tab.")
        else:
            st.success(f"📊 {len(st.session_state.generation_results)} section(s) available for validation")
            
            # Quick validation info
            st.markdown("""
            ### 🔍 Quality Validation
            
            Documentation quality is assessed across three dimensions:
            - **Completeness**: Are all required sections present?
            - **Accuracy**: Is the technical content correct?
            - **Confidence**: Overall quality score
            """)
            
            # Link to full quality dashboard
            st.info("""
            💡 **For comprehensive quality analysis:**
            
            Navigate to **🎯 Quality Dashboard** in the sidebar to:
            - Run full validation on saved documentation runs
            - View detailed quality reports
            - Manage review queue
            - Track quality metrics over time
            """)
            
            # Quality targets
            st.markdown("---")
            st.subheader("🎯 Quality Targets")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Completeness Target", "≥ 85%")
                st.caption("All required sections present with sufficient content")
            
            with col2:
                st.metric("Accuracy Target", "≥ 90%")
                st.caption("Technical correctness and valid code examples")
            
            with col3:
                st.metric("Confidence Target", "≥ 85%")
                st.caption("Overall quality score for production readiness")
            
            # Quality tips
            st.markdown("---")
            st.subheader("💡 Tips for High-Quality Documentation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **Improve Completeness:**
                - ✅ Include all key sections (Overview, Architecture, Setup, Examples)
                - ✅ Add code examples for each major feature
                - ✅ Provide step-by-step setup instructions
                - ✅ Include troubleshooting section
                - ✅ Ensure sections have sufficient detail (50+ words)
                """)
            
            with col2:
                st.markdown("""
                **Improve Accuracy:**
                - ✅ Verify all code examples for syntax correctness
                - ✅ Test API endpoints and request/response formats
                - ✅ Validate technical details against source code
                - ✅ Ensure consistent terminology
                - ✅ Avoid vague language (maybe, might, probably)
                """)


def generate_pass(api_base_url: str, section: str, pass_name: str, config: Dict[str, Any]) -> str:
    """
    Generate documentation for a single pass with enhanced error handling and tier support.
    
    Args:
        api_base_url: Base URL for API
        section: Section name (e.g., "OVERVIEW")
        pass_name: Pass name (e.g., "initial", "deep_dive")
        config: Configuration dictionary
    
    Returns:
        Generated content for this pass
    """
    # Generate questions based on section and pass
    questions = generate_questions(section, pass_name, config['queries_per_pass'])
    
    # Map response length to max_tokens
    length_map = {"S": 512, "M": 1024, "L": 2048, "XL": 4096}
    max_tokens = length_map.get(config['response_length'], 2048)
    
    pass_results = []
    query_timeout = config.get('query_timeout', 300)  # Default 5 minutes
    max_retries = config.get('max_retries', 2)
    tier = config.get('tier', 'desktop')  # Default to desktop
    
    for q_idx, question in enumerate(questions):
        retry_count = 0
        success = False
        
        while retry_count <= max_retries and not success:
            try:
                # Show progress
                st.write(f"  ⏳ Query {q_idx+1}/{len(questions)}: {question[:60]}... (attempt {retry_count+1})")
                
                # Call multi-pass RAG API with tier and extended timeout
                query_payload = {
                    "question": question,
                    "mode": "rag",  # Full RAG mode
                    "tier": tier,  # Desktop/auto/docker
                    "n_results": config['n_results'],
                    "temperature": config['temperature'],
                    "max_tokens": max_tokens,
                    "max_retries": max_retries
                }
                
                # Add service filter if configured
                if config.get('service_filter'):
                    query_payload["service_name"] = config['service_filter']
                
                response = httpx.post(
                    f"{api_base_url}/api/v1/query/enhanced",  # Use enhanced endpoint for tier support
                    json=query_payload,
                    timeout=query_timeout  # Configurable timeout (default 5min)
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    tier_used = data.get("tier_used", "unknown")
                    
                    # Add tier info to first response
                    if q_idx == 0 and retry_count == 0:
                        st.success(f"  ✅ Using {tier_used.upper()} tier")
                    
                    if config['include_sources']:
                        sources = data.get("sources", [])
                        if sources:
                            answer += f"\n\n**Sources:** {len(sources)} documents"
                    
                    pass_results.append(answer)
                    st.success(f"  ✅ Query {q_idx+1} complete")
                    success = True
                    
                elif response.status_code == 503:
                    st.warning(f"  ⚠️ Service unavailable (attempt {retry_count+1})")
                    retry_count += 1
                    if retry_count <= max_retries:
                        time.sleep(2 ** retry_count)  # Exponential backoff
                else:
                    st.warning(f"  ⚠️ Query failed (HTTP {response.status_code})")
                    retry_count += 1
                    
            except httpx.TimeoutException:
                st.error(f"  ⏱️ Timeout after {query_timeout}s (attempt {retry_count+1})")
                retry_count += 1
                if retry_count <= max_retries:
                    st.info(f"  🔄 Retrying in {2 ** retry_count}s...")
                    time.sleep(2 ** retry_count)
                    
            except httpx.ConnectError:
                st.error(f"  ❌ Connection error (attempt {retry_count+1})")
                retry_count += 1
                if retry_count <= max_retries:
                    time.sleep(2 ** retry_count)
                    
            except Exception as e:
                st.error(f"  ❌ Error: {str(e)} (attempt {retry_count+1})")
                retry_count += 1
                if retry_count <= max_retries:
                    time.sleep(2 ** retry_count)
        
        if not success:
            st.error(f"  ❌ Query {q_idx+1} failed after {max_retries+1} attempts")
    
    return "\n\n".join(pass_results)


def generate_questions(section: str, pass_name: str, count: int) -> List[str]:
    """
    Generate questions for a section and pass.
    
    Args:
        section: Section name
        pass_name: Pass name
        count: Number of questions to generate
    
    Returns:
        List of questions
    """
    # Question templates by section
    templates = {
        "OVERVIEW": [
            "What is the main purpose and functionality of this codebase?",
            "What are the key components and their relationships?",
            "What technologies and frameworks are used?",
            "What are the main entry points and workflows?",
            "What is the overall architecture pattern?",
        ],
        "ARCHITECTURE": [
            "How is the system architected at a high level?",
            "What are the main services and how do they interact?",
            "What design patterns are employed?",
            "How is data flow managed?",
            "What are the key architectural decisions?",
        ],
        "API": [
            "What are the main API endpoints?",
            "How are requests authenticated and authorized?",
            "What data formats are supported?",
            "What are the key request/response models?",
            "How is error handling implemented?",
        ],
        "SETUP": [
            "What are the prerequisites for running this project?",
            "How do you install and configure dependencies?",
            "What environment variables are required?",
            "How do you start the development server?",
            "What are the deployment steps?",
        ],
        "EXAMPLES": [
            "What are common use cases and examples?",
            "How do you perform basic operations?",
            "What are best practices for using this system?",
            "Are there code samples or tutorials available?",
            "What are typical workflows?",
        ],
        "TROUBLESHOOTING": [
            "What are common issues and their solutions?",
            "How do you debug problems?",
            "What logs are available for troubleshooting?",
            "How do you handle errors?",
            "What are known limitations?",
        ],
    }
    
    # Get questions for this section
    base_questions = templates.get(section, [
        f"What is important to know about {section.lower()}?",
        f"How does {section.lower()} work in this system?",
        f"What are key aspects of {section.lower()}?",
    ])
    
    # Modify for different passes
    if pass_name == "deep_dive":
        base_questions = [
            q.replace("What are", "Explain in detail")
            .replace("How do", "Describe comprehensively how")
            for q in base_questions
        ]
    
    # Return requested count
    return base_questions[:count]
