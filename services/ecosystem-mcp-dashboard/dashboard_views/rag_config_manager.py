"""
RAG Configuration Manager

Dashboard interface for managing optional RAG enhancements:
- View/edit glossary terms
- View/edit exclusion rules
- Adjust signal weights
- Invalidate cache
- Test configuration
"""

import streamlit as st
import httpx
import yaml
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path


def show(api_base_url: str):
    """Show RAG configuration manager page."""
    st.title("⚙️ RAG Configuration Manager")
    
    st.markdown("""
    Manage optional RAG enhancements to improve search accuracy.
    
    **Features:**
    - 📚 **Glossary**: Boost documents mentioning domain terms
    - 🚫 **Exclusions**: Filter out noise (logs, tests, etc.)
    - ⚖️ **Signal Weights**: Control ranking factors
    - ✅ **No config?** System uses standard RAG (no errors)
    """)
    
    # Check if config exists
    config_status = check_config_status()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "📚 Glossary",
        "🚫 Exclusions",
        "⚖️ Signal Weights",
        "🧪 Test & Debug"
    ])
    
    with tab1:
        show_overview(api_base_url, config_status)
    
    with tab2:
        show_glossary_manager(config_status)
    
    with tab3:
        show_exclusions_manager(config_status)
    
    with tab4:
        show_signal_weights_manager(config_status)
    
    with tab5:
        show_test_debug(api_base_url, config_status)


def check_config_status() -> Dict[str, Any]:
    """Check if RAG config exists and is valid."""
    config_dir = Path("../.rag-config")  # Relative to dashboard
    config_file = config_dir / "config.yaml"
    
    if not config_dir.exists():
        return {
            "exists": False,
            "config_file": str(config_file),
            "message": ".rag-config directory not found"
        }
    
    if not config_file.exists():
        return {
            "exists": False,
            "config_file": str(config_file),
            "message": "config.yaml not found"
        }
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        return {
            "exists": True,
            "config_file": str(config_file),
            "config": config,
            "message": "Config loaded successfully"
        }
    except Exception as e:
        return {
            "exists": False,
            "config_file": str(config_file),
            "message": f"Error loading config: {e}"
        }


def show_overview(api_base_url: str, config_status: Dict[str, Any]):
    """Show configuration overview."""
    st.subheader("📊 Configuration Overview")
    
    # Status indicator
    if config_status["exists"]:
        st.success("✅ RAG configuration is ACTIVE")
        config = config_status.get("config", {})
        
        # Feature flags
        col1, col2, col3 = st.columns(3)
        features = config.get("features_enabled", {})
        
        with col1:
            if features.get("glossary"):
                st.metric("📚 Glossary", "✅ Enabled", delta="Active")
            else:
                st.metric("📚 Glossary", "❌ Disabled", delta="Inactive")
        
        with col2:
            if features.get("exclusions"):
                st.metric("🚫 Exclusions", "✅ Enabled", delta="Active")
            else:
                st.metric("🚫 Exclusions", "❌ Disabled", delta="Inactive")
        
        with col3:
            total_features = sum(features.values())
            st.metric("🎯 Active Features", total_features, delta=f"of {len(features)}")
        
        # Quick stats
        st.markdown("### 📈 Quick Stats")
        col1, col2, col3 = st.columns(3)
        
        # Load additional files
        glossary_file = Path(config_status["config_file"]).parent / "glossary.yaml"
        exclusions_file = Path(config_status["config_file"]).parent / "exclusions.yaml"
        
        try:
            with open(glossary_file, 'r') as f:
                glossary_data = yaml.safe_load(f)
                glossary_count = len(glossary_data.get("glossary", {}))
        except:
            glossary_count = 0
        
        try:
            with open(exclusions_file, 'r') as f:
                exclusions_data = yaml.safe_load(f)
                exclusions_count = len(exclusions_data.get("exclusions", []))
        except:
            exclusions_count = 0
        
        with col1:
            st.metric("📚 Glossary Terms", glossary_count)
        
        with col2:
            st.metric("🚫 Exclusion Rules", exclusions_count)
        
        with col3:
            weights = config.get("signal_weights", {})
            weight_sum = sum(weights.values())
            if 0.95 <= weight_sum <= 1.05:
                st.metric("⚖️ Weight Sum", f"{weight_sum:.2f}", delta="Valid")
            else:
                st.metric("⚖️ Weight Sum", f"{weight_sum:.2f}", delta="Invalid", delta_color="inverse")
        
        # Signal weights visualization
        st.markdown("### ⚖️ Signal Weights Distribution")
        weights = config.get("signal_weights", {})
        
        for signal, weight in weights.items():
            progress_bar = st.progress(weight)
            st.caption(f"**{signal.replace('_', ' ').title()}**: {weight:.2f} ({int(weight*100)}%)")
        
        # Cache controls
        st.markdown("### 🔄 Cache Controls")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Invalidate Cache", use_container_width=True, type="secondary"):
                try:
                    response = httpx.post(f"{api_base_url}/admin/invalidate-rag-config-cache", timeout=10.0)
                    if response.status_code == 200:
                        st.success("✅ Cache invalidated! Config will reload on next query.")
                    else:
                        st.error(f"❌ Failed: {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col2:
            st.info("Cache reloads automatically every 5 minutes or when file changes.")
        
    else:
        st.warning("⚠️ No RAG configuration found - using standard behavior")
        st.info(config_status["message"])
        
        st.markdown("""
        ### 🚀 Quick Start
        
        1. **Create `.rag-config/` directory** in project root
        2. **Copy example files** from the repository
        3. **Edit terms and rules** to match your project
        4. **Enable in API**: `{"use_enhancements": true}`
        
        See `.rag-config/README.md` for detailed instructions.
        """)
        
        # Example file structure
        with st.expander("📁 Expected File Structure"):
            st.code("""
.rag-config/
├── config.yaml          # Main configuration
├── glossary.yaml        # Domain terms
├── exclusions.yaml      # Exclusion rules
└── README.md            # Documentation
            """, language="text")


def show_glossary_manager(config_status: Dict[str, Any]):
    """Show glossary term manager."""
    st.subheader("📚 Glossary Term Manager")
    
    if not config_status["exists"]:
        st.warning("⚠️ Config not found. Create `.rag-config/` first.")
        return
    
    glossary_file = Path(config_status["config_file"]).parent / "glossary.yaml"
    
    if not glossary_file.exists():
        st.warning("⚠️ glossary.yaml not found")
        return
    
    try:
        with open(glossary_file, 'r') as f:
            glossary_data = yaml.safe_load(f)
        
        glossary = glossary_data.get("glossary", {})
        
        st.info(f"**Total Terms:** {len(glossary)}")
        
        # Display existing terms
        for term_name, term_data in glossary.items():
            with st.expander(f"📖 {term_name}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Description:** {term_data.get('description', 'N/A')}")
                    st.markdown(f"**Boost Weight:** {term_data.get('boost_weight', 1.0)}")
                
                with col2:
                    synonyms = term_data.get('synonyms', [])
                    if synonyms:
                        st.markdown(f"**Synonyms:** {', '.join(synonyms)}")
                    
                    examples = term_data.get('examples', [])
                    if examples:
                        st.markdown(f"**Examples:** {len(examples)} provided")
        
        # Edit instructions
        st.markdown("### ✏️ To Edit:")
        st.code(f"nano {glossary_file}", language="bash")
        st.markdown("Or edit directly in your IDE, then click 'Invalidate Cache' above.")
        
        # Raw YAML view
        with st.expander("📄 View Raw YAML"):
            with open(glossary_file, 'r') as f:
                st.code(f.read(), language="yaml")
    
    except Exception as e:
        st.error(f"Error loading glossary: {e}")


def show_exclusions_manager(config_status: Dict[str, Any]):
    """Show exclusion rules manager."""
    st.subheader("🚫 Exclusion Rules Manager")
    
    if not config_status["exists"]:
        st.warning("⚠️ Config not found. Create `.rag-config/` first.")
        return
    
    exclusions_file = Path(config_status["config_file"]).parent / "exclusions.yaml"
    
    if not exclusions_file.exists():
        st.warning("⚠️ exclusions.yaml not found")
        return
    
    try:
        with open(exclusions_file, 'r') as f:
            exclusions_data = yaml.safe_load(f)
        
        exclusions = exclusions_data.get("exclusions", [])
        
        st.info(f"**Total Rules:** {len(exclusions)}")
        
        # Display rules by type
        global_rules = [r for r in exclusions if "*" in r.get("applies_to_queries", [])]
        conditional_rules = [r for r in exclusions if "*" not in r.get("applies_to_queries", [])]
        
        st.markdown(f"**Global Rules:** {len(global_rules)} (apply to all queries)")
        st.markdown(f"**Conditional Rules:** {len(conditional_rules)} (apply to specific queries)")
        
        # Display rules
        for i, rule in enumerate(exclusions):
            pattern = rule.get("pattern", "N/A")
            reason = rule.get("reason", "N/A")
            applies_to = rule.get("applies_to_queries", [])
            
            rule_type = "🌍 Global" if "*" in applies_to else "🎯 Conditional"
            
            with st.expander(f"{rule_type} Rule {i+1}: {pattern}", expanded=False):
                st.markdown(f"**Pattern:** `{pattern}`")
                st.markdown(f"**Reason:** {reason}")
                st.markdown(f"**Applies To:** {', '.join(applies_to)}")
        
        # Edit instructions
        st.markdown("### ✏️ To Edit:")
        st.code(f"nano {exclusions_file}", language="bash")
        st.markdown("Or edit directly in your IDE, then click 'Invalidate Cache' above.")
        
        # Raw YAML view
        with st.expander("📄 View Raw YAML"):
            with open(exclusions_file, 'r') as f:
                st.code(f.read(), language="yaml")
    
    except Exception as e:
        st.error(f"Error loading exclusions: {e}")


def show_signal_weights_manager(config_status: Dict[str, Any]):
    """Show signal weights manager."""
    st.subheader("⚖️ Signal Weights Manager")
    
    if not config_status["exists"]:
        st.warning("⚠️ Config not found. Create `.rag-config/` first.")
        return
    
    config = config_status.get("config", {})
    weights = config.get("signal_weights", {})
    
    if not weights:
        st.warning("⚠️ No signal weights found in config")
        return
    
    st.info("Signal weights control how different factors contribute to document ranking.")
    
    # Validate weights
    weight_sum = sum(weights.values())
    
    if 0.95 <= weight_sum <= 1.05:
        st.success(f"✅ Weights sum to {weight_sum:.2f} (valid)")
    else:
        st.error(f"❌ Weights sum to {weight_sum:.2f} (must sum to 1.0)")
    
    # Display weights with visual bars
    st.markdown("### Current Weights")
    
    for signal, weight in weights.items():
        col1, col2, col3 = st.columns([2, 1, 3])
        
        with col1:
            st.markdown(f"**{signal.replace('_', ' ').title()}**")
        
        with col2:
            st.markdown(f"`{weight:.2f}`")
        
        with col3:
            st.progress(weight)
    
    # Tuning guidance
    st.markdown("### 🎯 Tuning Guidance")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **High Semantic (0.6+)**
        - Trust embeddings
        - General queries
        - Broad topics
        """)
    
    with col2:
        st.markdown("""
        **High Glossary (0.3+)**
        - Strong domain vocabulary
        - Technical docs
        - Acronyms/jargon
        """)
    
    with col3:
        st.markdown("""
        **Balanced (0.25 each)**
        - Multi-signal optimization
        - Complex queries
        - Mixed content
        """)
    
    # Edit instructions
    st.markdown("### ✏️ To Edit:")
    config_file = config_status["config_file"]
    st.code(f"nano {config_file}", language="bash")
    st.markdown("**Important:** Weights must sum to 1.0 (±0.05 tolerance)")


def show_test_debug(api_base_url: str, config_status: Dict[str, Any]):
    """Show test and debug tools."""
    st.subheader("🧪 Test & Debug")
    
    # Test query
    st.markdown("### 🔍 Test Enhanced RAG")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        test_question = st.text_input(
            "Test Question",
            value="What is MCP?",
            placeholder="Enter a question to test..."
        )
    
    with col2:
        use_enhancements = st.checkbox("Use Enhancements", value=True)
    
    if st.button("🚀 Run Test Query", type="primary", use_container_width=True):
        if not test_question:
            st.warning("Please enter a question")
        else:
            with st.spinner("Running query..."):
                try:
                    payload = {
                        "question": test_question,
                        "use_enhancements": use_enhancements,
                        "n_results": 5
                    }
                    
                    response = httpx.post(
                        f"{api_base_url}/api/v1/query/enhanced",
                        json=payload,
                        timeout=60.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success("✅ Query completed!")
                        
                        # Display answer
                        st.markdown("### 💬 Answer:")
                        st.markdown(result.get("answer", "No answer"))
                        
                        # Display metadata
                        st.markdown("### 📊 Metadata:")
                        metadata = result.get("metadata", {})
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Mode", result.get("mode", "N/A"))
                        with col2:
                            st.metric("Tier Used", result.get("tier_used", "N/A"))
                        with col3:
                            st.metric("Sources", len(result.get("sources", [])))
                        
                        # Show if enhancements were applied
                        if metadata.get("enhancements_applied"):
                            st.success("✅ Enhancements were applied!")
                            
                            if "glossary_terms_included" in metadata:
                                terms = metadata["glossary_terms_included"]
                                st.info(f"📚 Matched glossary terms: {', '.join(terms)}")
                        else:
                            st.info("ℹ️ Standard RAG was used (no enhancements)")
                        
                        # Display sources
                        with st.expander("📄 View Sources"):
                            for source in result.get("sources", []):
                                st.markdown(f"- {source}")
                        
                        # Full response
                        with st.expander("🔍 Full Response (JSON)"):
                            st.json(result)
                    
                    else:
                        st.error(f"❌ Query failed: {response.status_code}")
                        st.code(response.text)
                
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    # Debug info
    st.markdown("### 🐛 Debug Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Config Status:**")
        if config_status["exists"]:
            st.success("✅ Config loaded")
        else:
            st.warning("⚠️ No config")
    
    with col2:
        st.markdown("**Config File:**")
        st.code(config_status.get("config_file", "N/A"), language="text")
    
    # API endpoint test
    st.markdown("### 🔌 API Endpoint Test")
    
    if st.button("Test Cache Invalidation Endpoint", use_container_width=True):
        try:
            response = httpx.post(
                f"{api_base_url}/admin/invalidate-rag-config-cache",
                timeout=10.0
            )
            
            if response.status_code == 200:
                st.success("✅ Endpoint working!")
                st.json(response.json())
            else:
                st.error(f"❌ Failed: {response.status_code}")
        
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    # Config file contents
    if config_status["exists"]:
        with st.expander("📄 Current Config (config.yaml)"):
            try:
                with open(config_status["config_file"], 'r') as f:
                    st.code(f.read(), language="yaml")
            except Exception as e:
                st.error(f"Error reading config: {e}")

