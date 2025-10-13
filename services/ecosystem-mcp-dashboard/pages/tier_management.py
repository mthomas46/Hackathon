"""
LLM Tier Management Page.

Provides tools to:
- Monitor tier availability
- Test connections
- Reestablish connections
- Configure tier settings
"""

import streamlit as st
import httpx
import os
from datetime import datetime


def show(api_base_url: str):
    """Show tier management page."""
    st.title("🔌 LLM Tier Management")
    
    st.markdown("""
    Monitor and manage the **3-tier LLM hierarchy** (Cursor IDE → Desktop Ollama → Docker Ollama).
    
    Test connections, view status, and enable higher tiers for better performance.
    """)
    
    # Fetch current tier status
    st.markdown("---")
    st.subheader("📊 Current Tier Status")
    
    try:
        tier_response = httpx.get(f"{api_base_url}/api/v1/query/tier-status", timeout=5.0)
        
        if tier_response.status_code == 200:
            tier_data = tier_response.json()
            tiers = tier_data.get("tiers", {})
            recommendation = tier_data.get("recommendation", "auto")
            
            # Display tier cards
            col1, col2, col3 = st.columns(3)
            
            with col1:
                cursor_tier = tiers.get("cursor", {})
                is_available = cursor_tier.get("available", False)
                
                if is_available:
                    st.success("### ✅ Tier 1: Cursor IDE")
                else:
                    st.error("### ❌ Tier 1: Cursor IDE")
                
                st.markdown(f"**Status:** {'Available' if is_available else 'Unavailable'}")
                st.markdown(f"**Model:** {cursor_tier.get('model', 'Unknown')}")
                st.markdown(f"**Use Case:** {cursor_tier.get('use_case', 'N/A')}")
                
                if not is_available:
                    st.caption("⚠️ Cursor IDE or MCP server not running")
            
            with col2:
                desktop_tier = tiers.get("desktop", {})
                is_available = desktop_tier.get("available", False)
                
                if is_available:
                    st.success("### ✅ Tier 2: Desktop Ollama")
                else:
                    st.warning("### ⚠️ Tier 2: Desktop Ollama")
                
                st.markdown(f"**Status:** {'Available' if is_available else 'Unavailable'}")
                st.markdown(f"**Model:** {desktop_tier.get('model', 'Unknown')}")
                st.markdown(f"**Use Case:** {desktop_tier.get('use_case', 'N/A')}")
                
                if not is_available:
                    st.caption("⚠️ Ollama not running on host:11435")
            
            with col3:
                docker_tier = tiers.get("docker", {})
                is_available = docker_tier.get("available", False)
                
                if is_available:
                    st.success("### ✅ Tier 3: Docker Ollama")
                else:
                    st.error("### ❌ Tier 3: Docker Ollama")
                
                st.markdown(f"**Status:** {'Available' if is_available else 'Unavailable'}")
                st.markdown(f"**Model:** {docker_tier.get('model', 'Unknown')}")
                st.markdown(f"**Use Case:** {docker_tier.get('use_case', 'N/A')}")
                
                if is_available:
                    st.caption("✅ Always available as fallback")
            
            st.info(f"💡 **Current Recommendation:** Use **{recommendation.upper()}** tier")
            
            # Refresh button
            col_refresh, col_space = st.columns([1, 3])
            with col_refresh:
                if st.button("🔄 Refresh Status", use_container_width=True):
                    st.rerun()
        
        else:
            st.error(f"Failed to fetch tier status: HTTP {tier_response.status_code}")
    
    except Exception as e:
        st.error(f"Error fetching tier status: {str(e)}")
    
    # Connection testing
    st.markdown("---")
    st.subheader("🔬 Connection Testing")
    
    test_col1, test_col2, test_col3 = st.columns(3)
    
    with test_col1:
        st.markdown("**Test Cursor IDE**")
        cursor_url = st.text_input(
            "Cursor MCP URL",
            value="http://host.docker.internal:3000",
            key="cursor_url"
        )
        if st.button("🧪 Test Cursor Connection", use_container_width=True):
            with st.spinner("Testing..."):
                try:
                    test_response = httpx.get(f"{cursor_url}/health", timeout=5.0)
                    if test_response.status_code == 200:
                        st.success("✅ Cursor IDE is reachable!")
                    else:
                        st.error(f"❌ Cursor returned: {test_response.status_code}")
                except httpx.TimeoutException:
                    st.error("❌ Connection timeout")
                except httpx.ConnectError:
                    st.error("❌ Cannot connect to Cursor IDE")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    with test_col2:
        st.markdown("**Test Desktop Ollama**")
        desktop_url = st.text_input(
            "Desktop Ollama URL",
            value="http://host.docker.internal:11435",
            key="desktop_url"
        )
        if st.button("🧪 Test Desktop Connection", use_container_width=True):
            with st.spinner("Testing..."):
                try:
                    test_response = httpx.get(f"{desktop_url}/api/version", timeout=5.0)
                    if test_response.status_code == 200:
                        version_data = test_response.json()
                        st.success(f"✅ Desktop Ollama is reachable!")
                        st.caption(f"Version: {version_data.get('version', 'unknown')}")
                    else:
                        st.error(f"❌ Desktop returned: {test_response.status_code}")
                except httpx.TimeoutException:
                    st.error("❌ Connection timeout")
                except httpx.ConnectError:
                    st.error("❌ Cannot connect to Desktop Ollama")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    with test_col3:
        st.markdown("**Test Docker Ollama**")
        docker_url = st.text_input(
            "Docker Ollama URL",
            value="http://ollama:11434",
            key="docker_url"
        )
        if st.button("🧪 Test Docker Connection", use_container_width=True):
            with st.spinner("Testing..."):
                try:
                    test_response = httpx.get(f"{docker_url}/api/version", timeout=5.0)
                    if test_response.status_code == 200:
                        version_data = test_response.json()
                        st.success(f"✅ Docker Ollama is reachable!")
                        st.caption(f"Version: {version_data.get('version', 'unknown')}")
                    else:
                        st.error(f"❌ Docker returned: {test_response.status_code}")
                except httpx.TimeoutException:
                    st.error("❌ Connection timeout")
                except httpx.ConnectError:
                    st.error("❌ Cannot connect to Docker Ollama")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Setup instructions
    st.markdown("---")
    st.subheader("🚀 Enable Higher Tiers")
    
    tab1, tab2, tab3 = st.tabs(["🥈 Desktop Ollama (GPU)", "🥇 Cursor IDE (Premium)", "📋 Current Setup"])
    
    with tab1:
        st.markdown("""
        ### Enable Desktop Ollama for GPU Performance
        
        **Benefits:**
        - 🚀 Faster inference with GPU acceleration
        - 🎯 Better performance for heavy workloads
        - 💪 Larger models (llama3:70b, etc.)
        
        **Setup Steps:**
        
        1. **Install Ollama** on your host machine:
           ```bash
           # macOS
           brew install ollama
           
           # Linux
           curl -fsSL https://ollama.ai/install.sh | sh
           
           # Windows
           # Download from https://ollama.ai/download
           ```
        
        2. **Start Ollama** with custom port:
           ```bash
           OLLAMA_HOST=0.0.0.0:11435 ollama serve
           ```
        
        3. **Pull a model**:
           ```bash
           ollama pull llama3:latest
           # or
           ollama pull llama3:70b  # If you have enough VRAM
           ```
        
        4. **Verify accessibility**:
           ```bash
           curl http://localhost:11435/api/version
           ```
        
        5. **Test connection** using the button above
        
        Once Desktop Ollama is running, the system will automatically detect it and use it for heavy workloads!
        """)
        
        with st.expander("🔧 Advanced Configuration"):
            st.markdown("""
            **Custom Model:**
            You can change which model Desktop Ollama uses by updating the environment variable:
            ```
            OLLAMA_DESKTOP_MODEL=llama3:70b
            ```
            
            **GPU Selection:**
            ```bash
            # Use specific GPU
            CUDA_VISIBLE_DEVICES=0 OLLAMA_HOST=0.0.0.0:11435 ollama serve
            ```
            """)
    
    with tab2:
        st.markdown("""
        ### Enable Cursor IDE for Premium Models
        
        **Benefits:**
        - 🎯 Access to Claude 4.5 Sonnet
        - 🧠 Best quality for extreme complexity
        - 💎 Premium model capabilities
        
        **Setup Steps:**
        
        1. **Install Cursor IDE**:
           - Download from https://cursor.sh
        
        2. **Setup Cursor MCP Server**:
           - Requires Cursor IDE running
           - MCP server must be accessible on port 3000
           - (Configuration depends on your Cursor setup)
        
        3. **Verify Cursor is running**:
           ```bash
           curl http://localhost:3000/health
           ```
        
        4. **Test connection** using the button above
        
        **Note:** Cursor integration requires additional MCP server setup beyond just running Cursor IDE.
        """)
    
    with tab3:
        st.markdown("""
        ### Current Setup
        
        Your system is currently using **Docker Ollama (Tier 3)** which provides:
        
        ✅ **Advantages:**
        - Always available (no external dependencies)
        - Works out of the box
        - Sufficient for most queries
        - Good for development and testing
        
        📊 **When to Enable Higher Tiers:**
        - **Desktop Ollama:** When you need faster inference or larger models
        - **Cursor IDE:** When you need premium Claude 4.5 capabilities
        
        💡 **For Most Users:**
        The current Docker Ollama setup is sufficient for:
        - RAG queries
        - Multi-pass analysis
        - Document processing
        - Standard LLM operations
        """)
    
    # Monitoring
    st.markdown("---")
    st.subheader("📈 Usage Monitoring")
    
    st.info("""
    **Tier Usage Statistics** (Coming Soon)
    
    Future features:
    - Query count per tier
    - Performance metrics
    - Cost tracking
    - Automatic tier optimization
    """)
    
    # Help section
    st.markdown("---")
    with st.expander("❓ Troubleshooting"):
        st.markdown("""
        ### Common Issues
        
        **Desktop Ollama not connecting:**
        - Ensure Ollama is running: `ps aux | grep ollama`
        - Check the port: `lsof -i :11435`
        - Verify host access: `curl http://localhost:11435/api/version`
        - Check firewall settings
        
        **Cursor IDE not connecting:**
        - Ensure Cursor IDE is running
        - Verify MCP server is started on port 3000
        - Check that MCP integration is configured
        
        **Still having issues?**
        - Check API logs: View "📋 Logs Viewer" page
        - Verify network connectivity
        - Ensure `host.docker.internal` resolves correctly
        """)


if __name__ == "__main__":
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    show(api_base_url)

