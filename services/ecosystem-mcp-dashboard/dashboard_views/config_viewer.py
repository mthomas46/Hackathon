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
    
    # Tabs - Added Registry Health tab
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Current Config", 
        "🌍 Environment", 
        "🐳 Docker Info", 
        "💻 System Info",
        "✅ Registry Health"  # NEW: Configuration Registry validation
    ])
    
    with tab1:
        show_current_config(api_base_url)
    
    with tab2:
        show_environment_variables(api_base_url)
    
    with tab3:
        show_docker_config(api_base_url)
    
    with tab4:
        show_system_info(api_base_url)
    
    with tab5:
        show_registry_health(api_base_url)  # NEW: Registry health monitoring


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


def show_registry_health(api_base_url: str):
    """
    Display Configuration Registry health and validation.
    
    ✅ PHASE 4: Observability - Configuration Registry monitoring
    This displays the new validation endpoints from the Configuration Registry System
    """
    st.subheader("✅ Configuration Registry Health")
    
    st.markdown("""
    Monitor configuration health and detect drift between registry and runtime values.
    
    **Key Features:**
    - **Quick Health Check**: Fast configuration status
    - **Drift Detection**: Identify configuration mismatches ⚠️
    - **Comprehensive Validation**: Validate all components
    - **Component-Specific**: Check Redis, Database, ChromaDB, Services
    """)
    
    # Control buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        if st.button("🔄 Refresh", key="registry_refresh", use_container_width=True):
            st.rerun()
    
    with col3:
        auto_refresh = st.checkbox("Auto-refresh", value=False)
    
    # Quick Health Check
    st.markdown("---")
    st.markdown("### 🚀 Quick Health Check")
    
    try:
        response = httpx.get(f"{api_base_url}/api/v1/config/health", timeout=5.0)
        
        if response.status_code == 200:
            health = response.json()
            status = health.get("status", "unknown")
            
            # Display health status with color coding
            if status == "healthy":
                st.success(f"✅ **Status:** HEALTHY")
            elif status == "degraded":
                st.warning(f"⚠️ **Status:** DEGRADED")
            else:
                st.error(f"❌ **Status:** {status.upper()}")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Registry Loaded",
                    "✅ Yes" if health.get("registry_loaded") else "❌ No"
                )
            
            with col2:
                services = health.get("services", [])
                st.metric("Services", len(services))
            
            with col3:
                st.metric("Redis Streams", health.get("redis_streams", 0))
            
            with col4:
                db_configured = health.get("database_configured", False)
                st.metric(
                    "Database",
                    "✅ Configured" if db_configured else "❌ Not Configured"
                )
            
            # Show issues if any
            issues = health.get("issues", [])
            if issues:
                st.warning("**Issues Detected:**")
                for issue in issues:
                    st.markdown(f"- {issue}")
            
            # Services list
            if services:
                with st.expander("📦 Configured Services"):
                    import pandas as pd
                    df = pd.DataFrame(services)
                    st.dataframe(df, use_container_width=True)
        
        else:
            st.error(f"Failed to fetch health: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    # Drift Detection - CRITICAL FEATURE
    st.markdown("---")
    st.markdown("### 🔍 Configuration Drift Detection")
    st.info("**🎯 Critical Feature**: Detects mismatches between registry and runtime configuration")
    
    try:
        response = httpx.get(f"{api_base_url}/api/v1/config/diff", timeout=5.0)
        
        if response.status_code == 200:
            diff_data = response.json()
            total_diff = diff_data.get("total_differences", 0)
            
            # Display drift status
            if total_diff == 0:
                st.success("✅ **No Configuration Drift Detected**")
                st.info("Registry and runtime configurations match perfectly!")
            else:
                st.error(f"⚠️ **{total_diff} Configuration Difference(s) Detected!**")
                
                # Show severity breakdown
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    critical = diff_data.get("critical", 0)
                    if critical > 0:
                        st.metric("Critical", critical, delta=None, delta_color="off")
                        st.markdown("🔴 **Requires immediate action**")
                
                with col2:
                    high = diff_data.get("high", 0)
                    if high > 0:
                        st.metric("High", high, delta=None, delta_color="off")
                
                with col3:
                    medium = diff_data.get("medium", 0)
                    if medium > 0:
                        st.metric("Medium", medium, delta=None, delta_color="off")
                
                with col4:
                    low = diff_data.get("low", 0)
                    if low > 0:
                        st.metric("Low", low, delta=None, delta_color="off")
                
                # Display differences
                differences = diff_data.get("differences", [])
                if differences:
                    st.markdown("#### 📋 Detected Differences:")
                    
                    for i, diff in enumerate(differences, 1):
                        severity = diff.get("severity", "unknown")
                        
                        # Color code based on severity
                        if severity == "critical":
                            emoji = "🔴"
                            color = "red"
                        elif severity == "high":
                            emoji = "🟠"
                            color = "orange"
                        elif severity == "medium":
                            emoji = "🟡"
                            color = "yellow"
                        else:
                            emoji = "🟢"
                            color = "green"
                        
                        with st.expander(f"{emoji} {diff.get('category', 'Unknown')} - {diff.get('field', 'Unknown')} ({severity})"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**Registry Value:**")
                                st.code(diff.get("registry_value", "N/A"))
                            
                            with col2:
                                st.markdown("**Runtime Value:**")
                                st.code(diff.get("runtime_value", "N/A"))
                            
                            st.markdown(f"**Recommendation:**")
                            st.warning(diff.get("recommendation", "No recommendation available"))
                
                # Show overall recommendation
                recommendation = diff_data.get("recommendation", "")
                if recommendation:
                    if "critical" in recommendation.lower():
                        st.error(f"⚠️ **Action Required:** {recommendation}")
                    else:
                        st.info(f"💡 **Recommendation:** {recommendation}")
        
        else:
            st.error(f"Failed to fetch drift data: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    # Comprehensive Validation
    st.markdown("---")
    st.markdown("### 🔬 Comprehensive Validation")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("▶️ Run Full Validation", use_container_width=True):
            with st.spinner("Running validation..."):
                try:
                    response = httpx.get(
                        f"{api_base_url}/api/v1/config/validate",
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        validation = response.json()
                        
                        # Summary metrics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Total Checks", validation.get("total_checks", 0))
                        
                        with col2:
                            passed = validation.get("passed", 0)
                            st.metric("Passed", passed, delta=None, delta_color="normal")
                        
                        with col3:
                            failed = validation.get("failed", 0)
                            st.metric("Failed", failed, delta=None, delta_color="inverse")
                        
                        with col4:
                            critical_failures = validation.get("critical_failures", 0)
                            st.metric("Critical Failures", critical_failures, delta=None, delta_color="off")
                        
                        # Overall status
                        overall_status = validation.get("overall_status", "unknown")
                        if overall_status == "healthy":
                            st.success("✅ **All validations passed!**")
                        elif overall_status == "degraded":
                            st.warning("⚠️ **Some validations failed (non-critical)**")
                        else:
                            st.error("❌ **Critical validations failed!**")
                        
                        # Detailed results
                        results = validation.get("results", [])
                        if results:
                            st.markdown("#### 📊 Validation Results:")
                            
                            # Separate passed and failed
                            passed_results = [r for r in results if r.get("passed")]
                            failed_results = [r for r in results if not r.get("passed")]
                            
                            # Show failed first
                            if failed_results:
                                st.markdown("**❌ Failed Checks:**")
                                for result in failed_results:
                                    severity = result.get("severity", "unknown")
                                    with st.expander(f"❌ {result.get('check_name', 'Unknown')} ({severity})"):
                                        st.error(result.get("message", "No message"))
                                        
                                        if result.get("remediation"):
                                            st.markdown("**💡 How to Fix:**")
                                            st.info(result["remediation"])
                                        
                                        if result.get("details"):
                                            with st.expander("🔍 Details"):
                                                st.json(result["details"])
                            
                            # Show passed in collapsible section
                            if passed_results:
                                with st.expander(f"✅ Passed Checks ({len(passed_results)})"):
                                    for result in passed_results:
                                        st.success(f"✅ {result.get('check_name', 'Unknown')}: {result.get('message', '')}")
                    
                    else:
                        st.error(f"Validation failed: {response.status_code}")
                
                except httpx.ConnectError:
                    st.error(f"❌ Cannot connect to API at {api_base_url}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Component-Specific Validation
    st.markdown("---")
    st.markdown("### 🔧 Component-Specific Validation")
    
    component_tabs = st.tabs(["🔴 Redis", "🗄️ Database", "🎨 ChromaDB", "⚙️ Services"])
    
    # Redis validation
    with component_tabs[0]:
        if st.button("▶️ Validate Redis", key="validate_redis"):
            validate_component(api_base_url, "redis", "Redis")
    
    # Database validation
    with component_tabs[1]:
        if st.button("▶️ Validate Database", key="validate_database"):
            validate_component(api_base_url, "database", "Database")
    
    # ChromaDB validation
    with component_tabs[2]:
        if st.button("▶️ Validate ChromaDB", key="validate_chromadb"):
            validate_component(api_base_url, "chromadb", "ChromaDB")
    
    # Services validation
    with component_tabs[3]:
        if st.button("▶️ Validate Services", key="validate_services"):
            validate_component(api_base_url, "services", "Services")
    
    # Auto-refresh
    if auto_refresh:
        import time
        time.sleep(5)
        st.rerun()


def validate_component(api_base_url: str, component: str, display_name: str):
    """Validate a specific component."""
    with st.spinner(f"Validating {display_name}..."):
        try:
            response = httpx.get(
                f"{api_base_url}/api/v1/config/validate/{component}",
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Summary
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Checks", data.get("total_checks", 0))
                
                with col2:
                    passed = data.get("passed", 0)
                    st.metric("Passed", passed)
                
                with col3:
                    failed = data.get("failed", 0)
                    st.metric("Failed", failed)
                
                # Status
                status = data.get("status", "unknown")
                if status == "healthy":
                    st.success(f"✅ {display_name} configuration is healthy!")
                else:
                    st.warning(f"⚠️ {display_name} has configuration issues")
                
                # Detailed checks
                checks = data.get("checks", [])
                if checks:
                    for check in checks:
                        if check.get("passed"):
                            st.success(f"✅ {check.get('name', 'Unknown')}: {check.get('message', '')}")
                        else:
                            with st.expander(f"❌ {check.get('name', 'Unknown')}"):
                                st.error(check.get("message", "No message"))
                                if check.get("remediation"):
                                    st.info(f"💡 **Fix:** {check['remediation']}")
            
            else:
                st.error(f"Validation failed: {response.status_code}")
        
        except httpx.ConnectError:
            st.error(f"❌ Cannot connect to API at {api_base_url}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

