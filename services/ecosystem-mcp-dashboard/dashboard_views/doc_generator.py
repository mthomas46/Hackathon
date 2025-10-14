"""
Documentation Generator Page

Generates comprehensive documentation using multi-pass RAG queries,
similar to the generate_deep_docs.py script.
"""

import streamlit as st
import httpx
from datetime import datetime
import json
import time
from pathlib import Path
from typing import List, Dict, Any


def show(api_base_url: str):
    """Display documentation generator page."""
    
    st.title("📚 Documentation Generator")
    st.markdown("Generate comprehensive documentation using multi-pass RAG queries")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["⚙️ Configure", "🚀 Generate", "📄 View Output"])
    
    # ============================================================================
    # Tab 1: Configure
    # ============================================================================
    with tab1:
        st.header("⚙️ Documentation Configuration")
        
        with st.form("doc_config_form"):
            st.markdown("### Documentation Sections")
            
            # Section selection
            sections = st.multiselect(
                "Select Sections to Generate",
                options=[
                    "OVERVIEW",
                    "ARCHITECTURE",
                    "API",
                    "FEATURES",
                    "DEVELOPMENT",
                    "DEPLOYMENT",
                    "PERFORMANCE",
                    "TROUBLESHOOTING"
                ],
                default=["OVERVIEW", "ARCHITECTURE", "API"],
                help="Choose which documentation sections to generate"
            )
            
            # Multi-pass workflow options
            st.markdown("### Multi-Pass Workflow")
            
            enable_multipass = st.checkbox(
                "Enable Multi-Pass Workflow",
                value=True,
                help="Use multiple passes for deeper, more comprehensive documentation"
            )
            
            if enable_multipass:
                passes = st.multiselect(
                    "Select Passes",
                    options=[
                        "initial",      # Broad overview
                        "deep_dive",    # Technical details
                        "practical",    # Examples and patterns
                        "integration",  # Synthesis
                        "refinement"    # Polish
                    ],
                    default=["initial", "deep_dive", "practical"],
                    help="Each pass adds more depth and detail"
                )
                
                queries_per_pass = st.slider(
                    "Queries per Pass",
                    min_value=3,
                    max_value=20,
                    value=10,
                    help="Number of questions to ask in each pass"
                )
            else:
                passes = ["initial"]
                queries_per_pass = 5
            
            # RAG parameters
            st.markdown("### RAG Parameters")
            
            col1, col2 = st.columns(2)
            with col1:
                n_results = st.slider(
                    "Documents per Query",
                    min_value=3,
                    max_value=20,
                    value=10,
                    help="Number of documents to retrieve for each query"
                )
                
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.1,
                    help="Lower = more focused, Higher = more creative"
                )
            
            with col2:
                response_length = st.selectbox(
                    "Response Length",
                    options=["S", "M", "L", "XL"],
                    index=2,
                    help="S=512, M=1024, L=2048, XL=4096 tokens"
                )
                
                use_cache = st.checkbox(
                    "Use Cache",
                    value=True,
                    help="Cache responses for faster regeneration"
                )
            
            # Output options
            st.markdown("### Output Options")
            
            include_metrics = st.checkbox(
                "Include Generation Metrics",
                value=True,
                help="Save detailed metrics about the generation process"
            )
            
            include_sources = st.checkbox(
                "Include Source References",
                value=True,
                help="Add source document references to the output"
            )
            
            # Save configuration button
            save_config = st.form_submit_button("💾 Save Configuration", use_container_width=True)
            
            if save_config:
                # Store in session state
                st.session_state.doc_config = {
                    "sections": sections,
                    "enable_multipass": enable_multipass,
                    "passes": passes if enable_multipass else ["initial"],
                    "queries_per_pass": queries_per_pass,
                    "n_results": n_results,
                    "temperature": temperature,
                    "response_length": response_length,
                    "use_cache": use_cache,
                    "include_metrics": include_metrics,
                    "include_sources": include_sources
                }
                st.success("✅ Configuration saved!")
        
        # Configuration summary
        if "doc_config" in st.session_state:
            st.markdown("---")
            st.markdown("### 📋 Current Configuration")
            config = st.session_state.doc_config
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Sections", len(config["sections"]))
            with col2:
                st.metric("Passes", len(config["passes"]))
            with col3:
                estimated_queries = len(config["sections"]) * len(config["passes"]) * config["queries_per_pass"]
                st.metric("Estimated Queries", estimated_queries)
            
            st.info(f"📊 Estimated generation time: {estimated_queries * 3} - {estimated_queries * 5} seconds")
    
    # ============================================================================
    # Tab 2: Generate
    # ============================================================================
    with tab2:
        st.header("🚀 Generate Documentation")
        
        # Check if config exists
        if "doc_config" not in st.session_state:
            st.warning("⚠️ Please configure documentation settings in the **Configure** tab first")
            return
        
        config = st.session_state.doc_config
        
        # Display configuration summary
        st.markdown("### 📋 Generation Plan")
        st.markdown(f"**Sections:** {', '.join(config['sections'])}")
        st.markdown(f"**Passes:** {', '.join(config['passes'])}")
        st.markdown(f"**Queries per pass:** {config['queries_per_pass']}")
        st.markdown(f"**Total estimated queries:** {len(config['sections']) * len(config['passes']) * config['queries_per_pass']}")
        
        st.markdown("---")
        
        # Start generation button
        if st.button("🚀 Start Generation", use_container_width=True, type="primary"):
            st.session_state.generating = True
            st.session_state.generation_start_time = time.time()
            st.session_state.generation_results = {}
            st.session_state.generation_metrics = []
        
        # Generation in progress
        if st.session_state.get("generating", False):
            st.info("🔄 Generation in progress...")
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Generate documentation section by section
            total_sections = len(config['sections'])
            for i, section in enumerate(config['sections']):
                status_text.text(f"Generating {section}... ({i+1}/{total_sections})")
                
                section_content = []
                
                # Run each pass for this section
                for pass_name in config['passes']:
                    pass_content = generate_pass(
                        api_base_url=api_base_url,
                        section=section,
                        pass_name=pass_name,
                        config=config
                    )
                    
                    if pass_content:
                        section_content.append(pass_content)
                
                # Combine pass results
                st.session_state.generation_results[section] = "\n\n".join(section_content)
                
                # Update progress
                progress_bar.progress((i + 1) / total_sections)
            
            # Generation complete
            st.session_state.generating = False
            generation_time = time.time() - st.session_state.generation_start_time
            
            st.success(f"✅ Documentation generated in {generation_time:.1f} seconds!")
            
            # Save metrics
            if config['include_metrics']:
                st.session_state.generation_metrics.append({
                    "timestamp": datetime.now().isoformat(),
                    "sections": config['sections'],
                    "passes": config['passes'],
                    "total_time": generation_time,
                    "queries": len(config['sections']) * len(config['passes']) * config['queries_per_pass']
                })
            
            st.info("📄 View generated documentation in the **View Output** tab")
            
            # Download button
            if st.session_state.generation_results:
                all_content = "\n\n---\n\n".join([
                    f"# {section}\n\n{content}"
                    for section, content in st.session_state.generation_results.items()
                ])
                
                st.download_button(
                    label="📥 Download Complete Documentation",
                    data=all_content,
                    file_name=f"documentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
        
        # Generation controls
        if st.session_state.get("generation_results"):
            st.markdown("---")
            st.markdown("### 🎛️ Controls")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Regenerate", use_container_width=True):
                    st.session_state.generating = True
                    st.rerun()
            
            with col2:
                if st.button("💾 Save to Disk", use_container_width=True):
                    # In a real implementation, this would save to a temporary directory
                    st.info("💡 Would save to: /tmp/generated_docs/")
            
            with col3:
                if st.button("🗑️ Clear Results", use_container_width=True):
                    st.session_state.generation_results = {}
                    st.session_state.generation_metrics = []
                    st.rerun()
    
    # ============================================================================
    # Tab 3: View Output
    # ============================================================================
    with tab3:
        st.header("📄 Generated Documentation")
        
        if not st.session_state.get("generation_results"):
            st.info("📭 No documentation generated yet")
            st.markdown("Generate documentation in the **Generate** tab")
            return
        
        # Section selector
        results = st.session_state.generation_results
        selected_section = st.selectbox(
            "Select Section",
            options=list(results.keys()),
            format_func=lambda x: f"📄 {x}"
        )
        
        if selected_section:
            # Display section content
            st.markdown("---")
            st.markdown(f"## {selected_section}")
            st.markdown(results[selected_section])
            
            # Download this section
            st.download_button(
                label=f"📥 Download {selected_section}",
                data=results[selected_section],
                file_name=f"{selected_section.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                key=f"download_{selected_section}"
            )
        
        # Metrics
        if st.session_state.get("generation_metrics"):
            st.markdown("---")
            st.markdown("### 📊 Generation Metrics")
            
            metrics = st.session_state.generation_metrics[-1]  # Latest
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Sections", len(metrics['sections']))
            with col2:
                st.metric("Passes", len(metrics['passes']))
            with col3:
                st.metric("Total Queries", metrics['queries'])
            with col4:
                st.metric("Generation Time", f"{metrics['total_time']:.1f}s")
            
            # Detailed metrics
            with st.expander("📈 Detailed Metrics"):
                st.json(metrics)


def generate_pass(api_base_url: str, section: str, pass_name: str, config: Dict[str, Any]) -> str:
    """
    Generate documentation for a single pass.
    
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
    
    for question in questions:
        try:
            # Call multi-pass RAG API
            response = httpx.post(
                f"{api_base_url}/api/v1/query/multi-pass",
                json={
                    "query": question,
                    "n_results": config['n_results'],
                    "temperature": config['temperature'],
                    "max_tokens": max_tokens,
                    "response_length": config['response_length'],
                    "use_cache": config['use_cache']
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                
                if config['include_sources']:
                    sources = data.get("sources", [])
                    if sources:
                        answer += f"\n\n**Sources:** {len(sources)} documents"
                
                pass_results.append(answer)
            else:
                st.warning(f"⚠️ Query failed for: {question[:50]}...")
                
        except Exception as e:
            st.error(f"❌ Error querying: {e}")
    
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
    # Question templates by section and pass
    templates = {
        "OVERVIEW": {
            "initial": [
                "What is the ecosystem-mcp service and what does it do?",
                "What are the main components of the ecosystem-mcp architecture?",
                "What problems does ecosystem-mcp solve?",
                "How does ecosystem-mcp integrate with other services?",
                "What are the key features of ecosystem-mcp?"
            ],
            "deep_dive": [
                "Explain the internal architecture of ecosystem-mcp in detail",
                "What design patterns are used in ecosystem-mcp?",
                "How does data flow through the ecosystem-mcp system?",
                "What are the performance characteristics of ecosystem-mcp?",
                "How is state managed in ecosystem-mcp?"
            ],
            "practical": [
                "Provide examples of using ecosystem-mcp",
                "What are common use cases for ecosystem-mcp?",
                "Show typical workflows with ecosystem-mcp",
                "What are best practices for using ecosystem-mcp?",
                "Provide code examples for ecosystem-mcp integration"
            ]
        },
        "ARCHITECTURE": {
            "initial": [
                "What is the high-level architecture of ecosystem-mcp?",
                "What are the main components and their responsibilities?",
                "How do components communicate with each other?",
                "What external dependencies does ecosystem-mcp have?",
                "What is the data flow architecture?"
            ],
            "deep_dive": [
                "Explain the detailed implementation of each component",
                "What design patterns are used and why?",
                "How is concurrency handled in the architecture?",
                "What are the scalability considerations?",
                "How is fault tolerance implemented?"
            ],
            "practical": [
                "Provide architecture diagrams and explanations",
                "Show examples of component interactions",
                "Explain deployment architecture options",
                "What are architectural best practices?",
                "How to extend the architecture?"
            ]
        },
        "API": {
            "initial": [
                "What APIs does ecosystem-mcp expose?",
                "What are the main API endpoints?",
                "How is authentication handled?",
                "What data formats are used?",
                "What are the API rate limits?"
            ],
            "deep_dive": [
                "Explain each API endpoint in detail",
                "What are the request and response schemas?",
                "How is error handling implemented?",
                "What validation is performed?",
                "How are versioning and compatibility handled?"
            ],
            "practical": [
                "Provide API usage examples",
                "Show common API workflows",
                "Explain authentication setup",
                "Provide curl examples",
                "Show client library usage"
            ]
        }
    }
    
    # Get templates for this section and pass, or use generic
    section_templates = templates.get(section, templates["OVERVIEW"])
    pass_templates = section_templates.get(pass_name, section_templates.get("initial", []))
    
    # Return up to count questions
    return pass_templates[:count]

