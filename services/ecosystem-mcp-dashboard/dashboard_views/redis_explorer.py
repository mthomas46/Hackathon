"""Redis explorer page."""

import streamlit as st
import httpx
import json
from datetime import datetime

def show(api_base_url: str):
    """Show Redis explorer page."""
    st.title("🔍 Redis Explorer")
    
    st.markdown("""
    Browse and manage Redis keys, monitor server statistics, and analyze memory usage.
    """)
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Server Info", "🔑 Keys Browser", "💾 Memory Analysis", "📈 Statistics"])
    
    with tab1:
        show_server_info(api_base_url)
    
    with tab2:
        show_keys_browser(api_base_url)
    
    with tab3:
        show_memory_analysis(api_base_url)
    
    with tab4:
        show_statistics(api_base_url)


def show_server_info(api_base_url: str):
    """Display Redis server information."""
    st.subheader("📊 Redis Server Information")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Refresh Info", use_container_width=True):
            st.rerun()
    
    try:
        response = httpx.get(f"{api_base_url}/api/v1/redis/info", timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            
            # Server metrics
            st.markdown("### Server")
            col1, col2, col3, col4 = st.columns(4)
            
            server = data.get("server", {})
            with col1:
                st.metric("Version", server.get("redis_version", "unknown"))
            with col2:
                uptime_days = server.get("uptime_in_days", 0)
                st.metric("Uptime", f"{uptime_days} days")
            with col3:
                st.metric("Mode", server.get("redis_mode", "unknown").title())
            with col4:
                st.metric("OS", server.get("os", "unknown"))
            
            # Memory metrics
            st.markdown("### Memory")
            col1, col2, col3, col4 = st.columns(4)
            
            memory = data.get("memory", {})
            with col1:
                st.metric("Used Memory", memory.get("used_memory_human", "0B"))
            with col2:
                st.metric("Peak Memory", memory.get("used_memory_peak_human", "0B"))
            with col3:
                st.metric("Max Memory", memory.get("maxmemory_human", "unlimited"))
            with col4:
                st.metric("Eviction Policy", memory.get("maxmemory_policy", "noeviction"))
            
            # Client & Connection metrics
            st.markdown("### Connections")
            col1, col2, col3 = st.columns(3)
            
            clients = data.get("clients", {})
            stats = data.get("stats", {})
            
            with col1:
                st.metric("Connected Clients", clients.get("connected_clients", 0))
            with col2:
                st.metric("Blocked Clients", clients.get("blocked_clients", 0))
            with col3:
                st.metric("Total Connections", stats.get("total_connections_received", 0))
            
            # Hit rate
            st.markdown("### Cache Performance")
            col1, col2, col3 = st.columns(3)
            
            hit_rate = data.get("hit_rate", 0)
            
            with col1:
                st.metric("Hit Rate", f"{hit_rate:.2f}%")
            with col2:
                st.metric("Keyspace Hits", f"{stats.get('keyspace_hits', 0):,}")
            with col3:
                st.metric("Keyspace Misses", f"{stats.get('keyspace_misses', 0):,}")
            
            # Keyspace info
            keyspace = data.get("keyspace", {})
            if keyspace:
                st.markdown("### Keyspace")
                for db_name, db_info in keyspace.items():
                    if isinstance(db_info, dict):
                        keys = db_info.get("keys", 0)
                        expires = db_info.get("expires", 0)
                        st.info(f"**{db_name}**: {keys:,} keys ({expires:,} with expiration)")
            
            # Full info expander
            with st.expander("🔍 View Full Server Info (JSON)"):
                st.json(data.get("full_info", {}))
        
        else:
            st.error(f"Failed to fetch Redis info: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def show_keys_browser(api_base_url: str):
    """Display Redis keys browser."""
    st.subheader("🔑 Keys Browser")
    
    # Search controls
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        pattern = st.text_input(
            "Search Pattern",
            value="*",
            help="Use * for wildcard (e.g., cache:*, session:*)"
        )
    
    with col2:
        count = st.number_input("Max Keys", min_value=10, max_value=1000, value=100, step=10)
    
    with col3:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("🔍 Search", use_container_width=True):
            st.session_state.redis_search_trigger = True
    
    # Perform search
    if st.button("🔍 Search Keys", key="search_keys_button") or st.session_state.get("redis_search_trigger"):
        st.session_state.redis_search_trigger = False
        
        try:
            response = httpx.post(
                f"{api_base_url}/api/v1/redis/keys",
                json={"pattern": pattern, "count": count},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                keys = data.get("keys", [])
                
                st.success(f"Found {len(keys)} keys matching pattern '{pattern}'")
                
                if keys:
                    # Display keys in a nice format
                    for key_info in keys:
                        key_name = key_info.get("key", "")
                        key_type = key_info.get("type", "unknown")
                        ttl = key_info.get("ttl", -1)
                        size = key_info.get("size", 0)
                        
                        # TTL display
                        if ttl == -1:
                            ttl_str = "No expiration"
                        elif ttl == -2:
                            ttl_str = "Expired"
                        else:
                            ttl_str = f"{ttl}s"
                        
                        with st.expander(f"🔑 {key_name} ({key_type})"):
                            col_info, col_actions = st.columns([2, 1])
                            
                            with col_info:
                                st.markdown(f"**Type:** {key_type}")
                                st.markdown(f"**TTL:** {ttl_str}")
                                st.markdown(f"**Size:** {size}")
                            
                            with col_actions:
                                if st.button("👁️ View Value", key=f"view_{key_name}"):
                                    st.session_state[f"view_key_{key_name}"] = True
                                
                                if st.button("🗑️ Delete", key=f"delete_{key_name}"):
                                    st.session_state[f"delete_key_{key_name}"] = True
                            
                            # View value
                            if st.session_state.get(f"view_key_{key_name}"):
                                try:
                                    value_response = httpx.get(
                                        f"{api_base_url}/api/v1/redis/key/{key_name}",
                                        timeout=10.0
                                    )
                                    
                                    if value_response.status_code == 200:
                                        value_data = value_response.json()
                                        value = value_data.get("value")
                                        
                                        st.markdown("**Value:**")
                                        if isinstance(value, (dict, list)):
                                            st.json(value)
                                        else:
                                            st.code(str(value))
                                    else:
                                        st.error("Failed to fetch value")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                            
                            # Delete confirmation
                            if st.session_state.get(f"delete_key_{key_name}"):
                                st.warning(f"Are you sure you want to delete '{key_name}'?")
                                col_yes, col_no = st.columns(2)
                                
                                with col_yes:
                                    if st.button("✅ Yes, Delete", key=f"confirm_delete_{key_name}"):
                                        try:
                                            delete_response = httpx.delete(
                                                f"{api_base_url}/api/v1/redis/key/{key_name}",
                                                timeout=10.0
                                            )
                                            
                                            if delete_response.status_code == 200:
                                                st.success("Key deleted successfully")
                                                del st.session_state[f"delete_key_{key_name}"]
                                                st.rerun()
                                            else:
                                                st.error("Failed to delete key")
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
                                
                                with col_no:
                                    if st.button("❌ Cancel", key=f"cancel_delete_{key_name}"):
                                        del st.session_state[f"delete_key_{key_name}"]
                                        st.rerun()
                else:
                    st.info("No keys found matching the pattern.")
            
            else:
                st.error(f"Failed to search keys: {response.status_code}")
        
        except httpx.ConnectError:
            st.error(f"❌ Cannot connect to API at {api_base_url}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Set key form
    st.markdown("---")
    st.subheader("➕ Set New Key")
    
    with st.form("set_key_form"):
        new_key = st.text_input("Key Name", placeholder="my:new:key")
        new_value = st.text_area("Value", placeholder="key value")
        new_ttl = st.number_input("TTL (seconds, 0 = no expiration)", min_value=0, value=0)
        
        submitted = st.form_submit_button("💾 Set Key")
        
        if submitted and new_key and new_value:
            try:
                set_response = httpx.post(
                    f"{api_base_url}/api/v1/redis/key",
                    json={
                        "key": new_key,
                        "value": new_value,
                        "ttl": new_ttl if new_ttl > 0 else None
                    },
                    timeout=10.0
                )
                
                if set_response.status_code == 200:
                    st.success(f"Key '{new_key}' set successfully!")
                else:
                    st.error(f"Failed to set key: {set_response.status_code}")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")


def show_memory_analysis(api_base_url: str):
    """Display Redis memory analysis."""
    st.subheader("💾 Memory Analysis")
    
    if st.button("🔄 Analyze Memory", use_container_width=False):
        with st.spinner("Analyzing memory usage..."):
            try:
                response = httpx.get(f"{api_base_url}/api/v1/redis/memory", timeout=30.0)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Summary metrics
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Memory", data.get("total_memory_human", "0B"))
                    with col2:
                        st.metric("Peak Memory", data.get("peak_memory_human", "0B"))
                    with col3:
                        frag_ratio = data.get("fragmentation_ratio", 0)
                        st.metric("Fragmentation Ratio", f"{frag_ratio:.2f}")
                    
                    st.info(f"Sampled {data.get('sampled_keys', 0):,} keys")
                    
                    # Pattern breakdown
                    patterns = data.get("patterns", [])
                    
                    if patterns:
                        st.markdown("### Memory Usage by Pattern")
                        
                        # Create table
                        import pandas as pd
                        
                        df = pd.DataFrame(patterns)
                        df["memory_mb"] = df["memory_bytes"] / 1024 / 1024
                        df["avg_size_kb"] = df["avg_size_bytes"] / 1024
                        
                        # Display table
                        st.dataframe(
                            df[["pattern", "count", "memory_mb", "avg_size_kb"]].rename(columns={
                                "pattern": "Pattern",
                                "count": "Keys",
                                "memory_mb": "Memory (MB)",
                                "avg_size_kb": "Avg Size (KB)"
                            }),
                            use_container_width=True
                        )
                        
                        # Bar chart
                        st.bar_chart(df.set_index("pattern")["memory_mb"])
                    else:
                        st.info("No patterns found in sampled keys.")
                
                else:
                    st.error(f"Failed to analyze memory: {response.status_code}")
            
            except httpx.ConnectError:
                st.error(f"❌ Cannot connect to API at {api_base_url}")
            except Exception as e:
                st.error(f"Error: {str(e)}")


def show_statistics(api_base_url: str):
    """Display Redis statistics."""
    st.subheader("📈 Real-Time Statistics")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Refresh Stats", use_container_width=True):
            st.rerun()
    
    try:
        response = httpx.get(f"{api_base_url}/api/v1/redis/info", timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get("stats", {})
            
            # Operations
            st.markdown("### Operations")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Commands Processed", f"{stats.get('total_commands_processed', 0):,}")
            with col2:
                st.metric("Ops/sec", stats.get("instantaneous_ops_per_sec", 0))
            with col3:
                st.metric("Rejected Connections", stats.get("rejected_connections", 0))
            
            # Keys
            st.markdown("### Key Statistics")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Expired Keys", f"{stats.get('expired_keys', 0):,}")
            with col2:
                st.metric("Evicted Keys", f"{stats.get('evicted_keys', 0):,}")
            
            # Network
            st.markdown("### Network I/O")
            col1, col2 = st.columns(2)
            
            input_mb = stats.get("total_net_input_bytes", 0) / 1024 / 1024
            output_mb = stats.get("total_net_output_bytes", 0) / 1024 / 1024
            
            with col1:
                st.metric("Total Input", f"{input_mb:.2f} MB")
            with col2:
                st.metric("Total Output", f"{output_mb:.2f} MB")
        
        else:
            st.error(f"Failed to fetch statistics: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

