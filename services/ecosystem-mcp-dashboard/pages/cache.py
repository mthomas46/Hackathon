"""Cache performance monitoring page."""

import streamlit as st
import httpx
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

def show(api_base_url: str):
    """Show cache performance page."""
    st.title("⚡ Cache Performance")
    
    # Refresh controls
    col1, col2 = st.columns([1, 5])
    
    with col1:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (30s)")
    
    try:
        # Fetch cache stats
        response = httpx.get(
            f"{api_base_url}/api/v1/cache/stats",
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract overall data (may be nested or top-level)
            overall = data.get("overall", data)
            
            # Overall metrics
            st.subheader("📊 Cache Overview")
            
            col1, col2, col3, col4 = st.columns(4)
            
            total_hits = overall.get("total_hits", 0)
            total_misses = overall.get("total_misses", 0)
            total_requests = overall.get("total_requests", total_hits + total_misses)
            hit_rate = overall.get("hit_rate", (total_hits / total_requests * 100) if total_requests > 0 else 0)
            
            with col1:
                st.metric("Total Hits", f"{total_hits:,}")
            
            with col2:
                st.metric("Total Misses", f"{total_misses:,}")
            
            with col3:
                st.metric("Hit Rate", f"{hit_rate:.1f}%")
            
            with col4:
                cached_keys = overall.get("cached_keys", 0)
                st.metric("Cached Keys", f"{cached_keys:,}")
            
            # Show status message if available
            cache_status = overall.get("status", "")
            if cache_status:
                st.info(f"ℹ️ {cache_status}")
            
            # Cache hit rate visualization
            st.markdown("---")
            st.subheader("📈 Cache Hit Rate")
            
            if total_requests > 0:
                fig = go.Figure(data=[go.Pie(
                    labels=['Hits', 'Misses'],
                    values=[total_hits, total_misses],
                    marker=dict(colors=['#00c851', '#ff4444']),
                    hole=.4
                )])
                
                fig.update_layout(
                    title="Cache Performance",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 No cache requests yet. Start using the API to see cache statistics!")
            
            # Per-prefix/endpoint stats
            st.markdown("---")
            st.subheader("🏷️ Cache by Endpoint")
            
            # Try both field names for compatibility
            cache_stats = data.get("by_endpoint", data.get("cache_stats", {}))
            
            if cache_stats:
                # Create table data
                table_data = []
                for prefix, stats in cache_stats.items():
                    hits = stats.get("hits", 0)
                    misses = stats.get("misses", 0)
                    total = stats.get("total", hits + misses)
                    rate = stats.get("hit_rate", (hits / total * 100) if total > 0 else 0)
                    status_msg = stats.get("status", "")
                    
                    row = {
                        "Endpoint": prefix,
                        "Hits": hits,
                        "Misses": misses,
                        "Total": total,
                        "Hit Rate": f"{rate:.1f}%"
                    }
                    
                    if status_msg:
                        row["Status"] = status_msg
                    
                    table_data.append(row)
                
                # Display as table
                st.dataframe(
                    table_data,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Bar chart
                if table_data:
                    fig = go.Figure()
                    
                    endpoints = [d["Endpoint"] for d in table_data]
                    hits = [d["Hits"] for d in table_data]
                    misses = [d["Misses"] for d in table_data]
                    
                    fig.add_trace(go.Bar(
                        name='Hits',
                        x=endpoints,
                        y=hits,
                        marker_color='#00c851'
                    ))
                    
                    fig.add_trace(go.Bar(
                        name='Misses',
                        x=endpoints,
                        y=misses,
                        marker_color='#ff4444'
                    ))
                    
                    fig.update_layout(
                        title="Cache Operations by Endpoint",
                        xaxis_title="Endpoint",
                        yaxis_title="Count",
                        barmode='group',
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No detailed cache statistics available")
            
            # Cache configuration
            st.markdown("---")
            st.subheader("⚙️ Cache Configuration")
            
            config = data.get("config", {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Default TTL", f"{config.get('default_ttl', 'N/A')}s")
                st.metric("Max Keys", config.get('max_keys', 'N/A'))
            
            with col2:
                st.metric("Eviction Policy", config.get('eviction_policy', 'N/A'))
                st.metric("Compression", "✅" if config.get('compression') else "❌")
            
            # Cache management
            st.markdown("---")
            st.subheader("🛠️ Cache Management")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🗑️ Clear All Cache", use_container_width=True):
                    with st.spinner("Clearing cache..."):
                        try:
                            clear_response = httpx.post(
                                f"{api_base_url}/api/v1/admin/clear-cache",
                                timeout=10.0
                            )
                            
                            if clear_response.status_code == 200:
                                st.success("✅ Cache cleared!")
                                st.rerun()
                            else:
                                st.error(f"Failed: {clear_response.status_code}")
                        
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            
            with col2:
                if st.button("💾 Export Stats", use_container_width=True):
                    st.download_button(
                        "📥 Download JSON",
                        data=response.text,
                        file_name=f"cache_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            
            with col3:
                if st.button("📊 Analyze", use_container_width=True):
                    st.info("Cache analysis coming soon...")
            
            # Full stats
            with st.expander("🔍 Raw Cache Stats"):
                st.json(data)
        
        else:
            st.error(f"Failed to fetch cache stats: {response.status_code}")
            st.code(response.text)
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to service at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

