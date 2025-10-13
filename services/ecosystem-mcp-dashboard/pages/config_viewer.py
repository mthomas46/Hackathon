"""Configuration viewer page."""

import streamlit as st
import httpx
import json
from datetime import datetime

def show(api_base_url: str):
    """Show configuration viewer page."""
    st.title("⚙️ Configuration Viewer")
    
    st.markdown("""
    View currently loaded configuration for all services and containers.
    """)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Current Config", "🌍 Environment", "🐳 Docker Info", "💻 System Info"])
    
    with tab1:
        show_current_config(api_base_url)
    
    with tab2:
        show_environment_variables(api_base_url)
    
    with tab3:
        show_docker_config(api_base_url)
    
    with tab4:
        show_system_info(api_base_url)


def show_current_config(api_base_url: str):
    """Display current configuration."""
    st.subheader("📝 Current Configuration")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    try:
        response = httpx.get(f"{api_base_url}/api/v1/config/current", timeout=10.0)
        
        if response.status_code == 200:
            config = response.json()
            
            st.info(f"**Configuration loaded at:** {config.get('timestamp', 'unknown')}")
            st.info(f"**Environment:** {config.get('environment', 'unknown')}")
            
            # Database config
            st.markdown("### 🗄️ Database (PostgreSQL)")
            database = config.get("database", {})
            with st.expander("Database Configuration", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**URL:** `{database.get('url', 'N/A')}`")
                    st.markdown(f"**Pool Size:** {database.get('pool_size', 'N/A')}")
                    st.markdown(f"**Max Overflow:** {database.get('max_overflow', 'N/A')}")
                with col2:
                    st.markdown(f"**Pool Pre-Ping:** {database.get('pool_pre_ping', 'N/A')}")
                    st.markdown(f"**Echo SQL:** {database.get('echo', 'N/A')}")
            
            # Redis config
            st.markdown("### 🔴 Redis")
            redis = config.get("redis", {})
            with st.expander("Redis Configuration", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**URL:** `{redis.get('url', 'N/A')}`")
                    st.markdown(f"**Max Connections:** {redis.get('max_connections', 'N/A')}")
                with col2:
                    st.markdown(f"**Socket Timeout:** {redis.get('socket_timeout', 'N/A')}s")
                    st.markdown(f"**Connect Timeout:** {redis.get('socket_connect_timeout', 'N/A')}s")
            
            # ChromaDB config
            st.markdown("### 🎨 ChromaDB")
            chromadb = config.get("chromadb", {})
            with st.expander("ChromaDB Configuration", expanded=True):
                st.markdown(f"**Storage Path:** `{chromadb.get('path', 'N/A')}`")
                st.markdown(f"**Collection Name:** `{chromadb.get('collection_name', 'N/A')}`")
            
            # Ollama config
            st.markdown("### 🦙 Ollama")
            ollama = config.get("ollama", {})
            with st.expander("Ollama Configuration", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Base URL:** `{ollama.get('base_url', 'N/A')}`")
                    st.markdown(f"**Model:** `{ollama.get('model', 'N/A')}`")
                with col2:
                    st.markdown(f"**Embedding Model:** `{ollama.get('embedding_model', 'N/A')}`")
                    st.markdown(f"**Timeout:** {ollama.get('timeout', 'N/A')}s")
            
            # LLM Strategy
            st.markdown("### 🧠 LLM Strategy")
            llm = config.get("llm_strategy", {})
            cursor = config.get("cursor", {})
            with st.expander("LLM Configuration", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Model Strategy:** {llm.get('model_strategy', 'N/A')}")
                    st.markdown(f"**Fallback Enabled:** {llm.get('fallback_enabled', 'N/A')}")
                with col2:
                    st.markdown(f"**Cursor Enabled:** {cursor.get('enabled', 'N/A')}")
                    st.markdown(f"**Cursor Model:** {cursor.get('model', 'N/A')}")
            
            # Ingestion config
            st.markdown("### 📥 Ingestion")
            ingestion = config.get("ingestion", {})
            with st.expander("Ingestion Configuration"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Batch Size", ingestion.get("batch_size", 0))
                with col2:
                    st.metric("Parallel Workers", ingestion.get("parallel_workers", 0))
                with col3:
                    st.metric("Max File Size (MB)", ingestion.get("max_file_size_mb", 0))
            
            # Rate limiting
            st.markdown("### 🚦 Rate Limiting")
            rate = config.get("rate_limiting", {})
            with st.expander("Rate Limiting Configuration"):
                enabled = rate.get("enabled", False)
                if enabled:
                    st.success("✅ Rate limiting is ENABLED")
                else:
                    st.warning("⚠️ Rate limiting is DISABLED")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**RAG:** {rate.get('rag_rate_limit', 'N/A')}")
                with col2:
                    st.markdown(f"**Search:** {rate.get('search_rate_limit', 'N/A')}")
                with col3:
                    st.markdown(f"**Query:** {rate.get('query_rate_limit', 'N/A')}")
            
            # Caching
            st.markdown("### ⚡ Caching")
            cache = config.get("caching", {})
            with st.expander("Caching Configuration"):
                enabled = cache.get("enable_cache", False)
                if enabled:
                    st.success("✅ Caching is ENABLED")
                else:
                    st.warning("⚠️ Caching is DISABLED")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Cache TTL", f"{cache.get('cache_ttl', 0)}s")
                with col2:
                    st.metric("Embedding Cache TTL", f"{cache.get('embedding_cache_ttl', 0)}s")
                with col3:
                    st.metric("Search Cache TTL", f"{cache.get('search_cache_ttl', 0)}s")
            
            # Performance
            st.markdown("### ⚡ Performance")
            perf = config.get("performance", {})
            with st.expander("Performance Configuration"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("HTTP Timeout", f"{perf.get('httpx_timeout', 0)}s")
                with col2:
                    st.metric("Max Connections", perf.get("httpx_max_connections", 0))
                with col3:
                    st.metric("Keepalive Connections", perf.get("httpx_max_keepalive_connections", 0))
            
            # Full JSON
            with st.expander("📄 View Full Configuration (JSON)"):
                st.json(config)
        
        else:
            st.error(f"Failed to fetch configuration: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def show_environment_variables(api_base_url: str):
    """Display environment variables."""
    st.subheader("🌍 Environment Variables")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search = st.text_input("🔍 Search variables", placeholder="Enter keyword...")
    
    with col2:
        if st.button("🔄 Refresh", key="env_refresh", use_container_width=True):
            st.rerun()
    
    try:
        response = httpx.get(f"{api_base_url}/api/v1/config/environment", timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            variables = data.get("variables", {})
            
            st.info(f"**Total Variables:** {data.get('total_variables', 0)}")
            st.warning("⚠️ **Note:** Sensitive values are masked for security")
            
            # Filter variables
            if search:
                filtered_vars = {k: v for k, v in variables.items() if search.lower() in k.lower()}
            else:
                filtered_vars = variables
            
            if filtered_vars:
                st.markdown(f"**Showing {len(filtered_vars)} variables**")
                
                # Display in table format
                import pandas as pd
                df = pd.DataFrame([
                    {"Variable": k, "Value": v}
                    for k, v in sorted(filtered_vars.items())
                ])
                
                st.dataframe(df, use_container_width=True, height=400)
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"environment_variables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No variables match the search criteria.")
        
        else:
            st.error(f"Failed to fetch environment variables: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def show_docker_config(api_base_url: str):
    """Display Docker configuration."""
    st.subheader("🐳 Docker Container Information")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Refresh", key="docker_refresh", use_container_width=True):
            st.rerun()
    
    try:
        response = httpx.get(f"{api_base_url}/api/v1/config/docker", timeout=10.0)
        
        if response.status_code == 200:
            config = response.json()
            
            # Container info
            st.markdown("### 📦 Container Details")
            container = config.get("container", {})
            with st.expander("Container Information", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Hostname:** `{container.get('hostname', 'unknown')}`")
                    st.markdown(f"**User:** `{container.get('user', 'unknown')}`")
                with col2:
                    st.markdown(f"**Home:** `{container.get('home', 'unknown')}`")
                    st.markdown(f"**Working Directory:** `{container.get('pwd', 'unknown')}`")
            
            # Resource limits
            st.markdown("### 💾 Resource Limits")
            resources = config.get("resources", {})
            if "error" not in resources and resources:
                with st.expander("Resource Limits", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        memory_mb = resources.get("memory_limit_mb")
                        if memory_mb:
                            st.metric("Memory Limit", f"{memory_mb:.2f} MB")
                    with col2:
                        cpu_limit = resources.get("cpu_limit")
                        if cpu_limit:
                            st.metric("CPU Limit", f"{cpu_limit:.2f} cores")
            else:
                st.info("Resource limits not available (may not be in Docker)")
            
            # Networking
            st.markdown("### 🌐 Networking")
            networking = config.get("networking", {})
            if "error" not in networking and networking:
                with st.expander("Network Information", expanded=True):
                    st.markdown(f"**Hostname:** `{networking.get('hostname', 'unknown')}`")
                    st.markdown(f"**IP Address:** `{networking.get('ip_address', 'unknown')}`")
            
            # Volumes
            st.markdown("### 💽 Volume Mounts")
            volumes = config.get("volumes", {})
            if "error" not in volumes and "mounts" in volumes:
                mounts = volumes.get("mounts", [])
                if mounts:
                    import pandas as pd
                    df = pd.DataFrame(mounts)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No volume mounts found")
            
            # Full JSON
            with st.expander("📄 View Full Docker Config (JSON)"):
                st.json(config)
        
        else:
            st.error(f"Failed to fetch Docker config: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def show_system_info(api_base_url: str):
    """Display system information."""
    st.subheader("💻 System Information")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Refresh", key="system_refresh", use_container_width=True):
            st.rerun()
    
    try:
        response = httpx.get(f"{api_base_url}/api/v1/config/system", timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            
            st.info(f"**Last Updated:** {data.get('timestamp', 'unknown')}")
            
            # CPU info
            st.markdown("### 🖥️ CPU")
            cpu = data.get("cpu", {})
            with st.expander("CPU Information", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total CPUs", cpu.get("count", 0))
                with col2:
                    st.metric("Physical CPUs", cpu.get("physical_count", 0))
                with col3:
                    st.metric("Usage", f"{cpu.get('percent', 0):.1f}%")
                
                # Per-CPU usage
                per_cpu = cpu.get("per_cpu", [])
                if per_cpu:
                    st.markdown("**Per-CPU Usage:**")
                    cols = st.columns(min(len(per_cpu), 8))
                    for i, usage in enumerate(per_cpu[:8]):
                        with cols[i]:
                            st.metric(f"CPU {i}", f"{usage:.1f}%")
            
            # Memory info
            st.markdown("### 💾 Memory")
            memory = data.get("memory", {})
            with st.expander("Memory Information", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_gb = memory.get("total_gb", 0)
                    st.metric("Total Memory", f"{total_gb:.2f} GB")
                with col2:
                    available_mb = memory.get("available_mb", 0)
                    st.metric("Available", f"{available_mb:.2f} MB")
                with col3:
                    used_percent = memory.get("used_percent", 0)
                    st.metric("Usage", f"{used_percent:.1f}%")
                
                used_mb = memory.get("used_mb", 0)
                st.metric("Used Memory", f"{used_mb:.2f} MB")
            
            # Disk info
            st.markdown("### 💽 Disk")
            disk = data.get("disk", {})
            with st.expander("Disk Information", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_gb = disk.get("total_gb", 0)
                    st.metric("Total Space", f"{total_gb:.2f} GB")
                with col2:
                    used_gb = disk.get("used_gb", 0)
                    st.metric("Used Space", f"{used_gb:.2f} GB")
                with col3:
                    free_gb = disk.get("free_gb", 0)
                    st.metric("Free Space", f"{free_gb:.2f} GB")
                
                percent = disk.get("percent", 0)
                st.metric("Usage", f"{percent:.1f}%")
            
            # Platform info
            st.markdown("### 🖥️ Platform")
            platform = data.get("platform", {})
            with st.expander("Platform Information", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**System:** {platform.get('system', 'unknown')}")
                    st.markdown(f"**Release:** {platform.get('release', 'unknown')}")
                    st.markdown(f"**Machine:** {platform.get('machine', 'unknown')}")
                with col2:
                    st.markdown(f"**Processor:** {platform.get('processor', 'unknown')}")
                    st.markdown(f"**Python Version:** {platform.get('python_version', 'unknown')}")
            
            # Full JSON
            with st.expander("📄 View Full System Info (JSON)"):
                st.json(data)
        
        else:
            st.error(f"Failed to fetch system info: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

