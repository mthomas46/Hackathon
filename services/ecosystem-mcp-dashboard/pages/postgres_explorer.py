"""PostgreSQL explorer page."""

import streamlit as st
import httpx
import pandas as pd
from datetime import datetime

def show(api_base_url: str):
    """Show PostgreSQL explorer page."""
    st.title("🗄️ PostgreSQL Explorer")
    
    st.markdown("""
    Browse database tables, execute queries, and monitor database activity.
    """)
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Server Info",
        "📋 Tables",
        "💻 Query Editor",
        "👥 Activity",
        "🔒 Locks"
    ])
    
    with tab1:
        show_server_info(api_base_url)
    
    with tab2:
        show_tables(api_base_url)
    
    with tab3:
        show_query_editor(api_base_url)
    
    with tab4:
        show_activity(api_base_url)
    
    with tab5:
        show_locks(api_base_url)


def show_server_info(api_base_url: str):
    """Display PostgreSQL server information."""
    st.subheader("📊 PostgreSQL Server Information")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Refresh Info", use_container_width=True):
            st.rerun()
    
    try:
        response = httpx.get(f"{api_base_url}/api/v1/postgres/info", timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            
            # Server info
            st.markdown("### Server")
            server = data.get("server", {})
            st.info(f"**Version:** {server.get('version', 'unknown')}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Database", server.get("database", "unknown"))
            with col2:
                st.metric("Size", server.get("size", "unknown"))
            
            # Connections
            st.markdown("### Connections")
            connections = data.get("connections", {})
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Active Connections", connections.get("active", 0))
            with col2:
                oldest = connections.get("oldest")
                if oldest:
                    st.metric("Oldest Connection", oldest)
                else:
                    st.metric("Oldest Connection", "N/A")
            
            # Statistics
            st.markdown("### Database Statistics")
            stats = data.get("stats", {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Active Backends", stats.get("active_backends", 0))
            with col2:
                st.metric("Transactions Committed", f"{stats.get('transactions_committed', 0):,}")
            with col3:
                st.metric("Transactions Rolled Back", f"{stats.get('transactions_rolled_back', 0):,}")
            
            # Cache performance
            st.markdown("### Cache Performance")
            col1, col2, col3 = st.columns(3)
            
            cache_hit_ratio = stats.get("cache_hit_ratio", 0)
            
            with col1:
                st.metric("Cache Hit Ratio", f"{cache_hit_ratio:.2f}%")
            with col2:
                st.metric("Blocks Read", f"{stats.get('blocks_read', 0):,}")
            with col3:
                st.metric("Blocks Hit", f"{stats.get('blocks_hit', 0):,}")
            
            # Tuple statistics
            st.markdown("### Tuple Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Returned", f"{stats.get('tuples_returned', 0):,}")
            with col2:
                st.metric("Fetched", f"{stats.get('tuples_fetched', 0):,}")
            with col3:
                st.metric("Inserted", f"{stats.get('tuples_inserted', 0):,}")
            with col4:
                st.metric("Updated", f"{stats.get('tuples_updated', 0):,}")
        
        else:
            st.error(f"Failed to fetch PostgreSQL info: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def show_tables(api_base_url: str):
    """Display PostgreSQL tables browser."""
    st.subheader("📋 Database Tables")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Refresh Tables", use_container_width=True):
            st.rerun()
    
    try:
        response = httpx.get(f"{api_base_url}/api/v1/postgres/tables", timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            tables = data.get("tables", [])
            
            st.info(f"Found {data.get('total_tables', 0)} tables")
            
            if tables:
                # Create DataFrame for better display
                df = pd.DataFrame(tables)
                
                # Display summary table
                st.dataframe(
                    df[["name", "schema", "row_count", "size", "dead_rows"]].rename(columns={
                        "name": "Table",
                        "schema": "Schema",
                        "row_count": "Rows",
                        "size": "Size",
                        "dead_rows": "Dead Rows"
                    }),
                    use_container_width=True
                )
                
                # Table details expander
                st.markdown("---")
                st.markdown("### Table Details")
                
                selected_table = st.selectbox(
                    "Select table to view details",
                    options=[t["name"] for t in tables]
                )
                
                if selected_table and st.button(f"📊 Load Details for '{selected_table}'"):
                    with st.spinner(f"Loading details for {selected_table}..."):
                        try:
                            details_response = httpx.get(
                                f"{api_base_url}/api/v1/postgres/table/{selected_table}",
                                timeout=10.0
                            )
                            
                            if details_response.status_code == 200:
                                details = details_response.json()
                                
                                # Row count
                                st.metric("Total Rows", f"{details.get('row_count', 0):,}")
                                
                                # Columns
                                st.markdown("#### Columns")
                                columns = details.get("columns", [])
                                if columns:
                                    cols_df = pd.DataFrame(columns)
                                    st.dataframe(
                                        cols_df[["name", "type", "nullable", "default"]].rename(columns={
                                            "name": "Column",
                                            "type": "Type",
                                            "nullable": "Nullable",
                                            "default": "Default"
                                        }),
                                        use_container_width=True
                                    )
                                
                                # Indexes
                                st.markdown("#### Indexes")
                                indexes = details.get("indexes", [])
                                if indexes:
                                    for idx in indexes:
                                        with st.expander(f"🔑 {idx.get('name', 'unknown')}"):
                                            st.code(idx.get("definition", ""), language="sql")
                                else:
                                    st.info("No indexes found")
                                
                                # Sample data
                                st.markdown("#### Sample Data (First 10 Rows)")
                                sample_data = details.get("sample_data", [])
                                if sample_data:
                                    sample_df = pd.DataFrame(sample_data)
                                    st.dataframe(sample_df, use_container_width=True)
                                else:
                                    st.info("No sample data available")
                            
                            else:
                                st.error(f"Failed to load table details: {details_response.status_code}")
                        
                        except Exception as e:
                            st.error(f"Error loading details: {str(e)}")
            else:
                st.info("No tables found")
        
        else:
            st.error(f"Failed to fetch tables: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def show_query_editor(api_base_url: str):
    """Display SQL query editor."""
    st.subheader("💻 SQL Query Editor")
    
    st.warning("⚠️ **Safety:** Only SELECT and WITH queries are allowed. Destructive operations (DELETE, UPDATE, DROP, etc.) are blocked.")
    
    # Query input
    query = st.text_area(
        "SQL Query",
        height=150,
        placeholder="SELECT * FROM your_table LIMIT 10;",
        help="Enter a SELECT query to execute"
    )
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        limit = st.number_input("Row Limit", min_value=1, max_value=1000, value=100)
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        execute_button = st.button("▶️ Execute Query", use_container_width=False, type="primary")
    
    # Execute query
    if execute_button and query.strip():
        with st.spinner("Executing query..."):
            try:
                response = httpx.post(
                    f"{api_base_url}/api/v1/postgres/query",
                    json={"query": query, "limit": limit},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    rows = data.get("rows", [])
                    row_count = data.get("row_count", 0)
                    
                    st.success(f"✅ Query executed successfully! Returned {row_count} rows.")
                    
                    if rows:
                        # Display results
                        st.markdown("### Results")
                        df = pd.DataFrame(rows)
                        st.dataframe(df, use_container_width=True)
                        
                        # Download button
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download as CSV",
                            data=csv,
                            file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("Query returned no results.")
                
                elif response.status_code == 400:
                    error_detail = response.json().get("detail", "Unknown error")
                    st.error(f"❌ Query blocked: {error_detail}")
                
                else:
                    st.error(f"❌ Query failed: {response.status_code} - {response.text}")
            
            except httpx.ConnectError:
                st.error(f"❌ Cannot connect to API at {api_base_url}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Example queries
    with st.expander("📚 Example Queries"):
        st.markdown("""
        **Count documents:**
        ```sql
        SELECT COUNT(*) FROM documents;
        ```
        
        **List recent documents:**
        ```sql
        SELECT id, file_path, file_type, created_at 
        FROM documents 
        ORDER BY created_at DESC 
        LIMIT 10;
        ```
        
        **Group by file type:**
        ```sql
        SELECT file_type, COUNT(*) as count 
        FROM documents 
        GROUP BY file_type 
        ORDER BY count DESC;
        ```
        
        **Find large documents:**
        ```sql
        SELECT file_path, LENGTH(content) as size 
        FROM documents 
        ORDER BY size DESC 
        LIMIT 10;
        ```
        """)


def show_activity(api_base_url: str):
    """Display active database connections."""
    st.subheader("👥 Active Connections")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Refresh Activity", use_container_width=True):
            st.rerun()
    
    try:
        response = httpx.get(f"{api_base_url}/api/v1/postgres/activity", timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            connections = data.get("connections", [])
            
            st.info(f"Found {data.get('total_connections', 0)} active connections")
            
            if connections:
                for conn in connections:
                    pid = conn.get("pid")
                    user = conn.get("user", "unknown")
                    state = conn.get("state", "unknown")
                    duration = conn.get("duration_seconds")
                    query = conn.get("query", "")
                    
                    # State indicator
                    state_icon = "🟢" if state == "active" else "🟡" if state == "idle" else "⚪"
                    
                    with st.expander(f"{state_icon} PID {pid} - {user} ({state})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**User:** {user}")
                            st.markdown(f"**State:** {state}")
                            st.markdown(f"**Application:** {conn.get('application', 'unknown')}")
                        
                        with col2:
                            st.markdown(f"**PID:** {pid}")
                            if duration is not None:
                                st.markdown(f"**Duration:** {duration:.2f}s")
                            client_addr = conn.get("client_addr")
                            if client_addr:
                                st.markdown(f"**Client:** {client_addr}")
                        
                        if query and query.strip():
                            st.markdown("**Query:**")
                            st.code(query, language="sql")
                        else:
                            st.info("No active query")
            else:
                st.info("No active connections (excluding this one)")
        
        else:
            st.error(f"Failed to fetch activity: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def show_locks(api_base_url: str):
    """Display database locks."""
    st.subheader("🔒 Database Locks")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Refresh Locks", use_container_width=True):
            st.rerun()
    
    try:
        response = httpx.get(f"{api_base_url}/api/v1/postgres/locks", timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            locks = data.get("locks", [])
            blocked = data.get("blocked_queries", [])
            
            # Blocked queries (high priority)
            if blocked:
                st.error(f"⚠️ {len(blocked)} blocked queries detected!")
                
                for block in blocked:
                    with st.expander(f"🚫 Blocked PID {block.get('blocked_pid')} by PID {block.get('blocking_pid')}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Blocked Query:**")
                            st.markdown(f"PID: {block.get('blocked_pid')}")
                            st.markdown(f"User: {block.get('blocked_user')}")
                            blocked_query = block.get("blocked_query", "")
                            if blocked_query:
                                st.code(blocked_query, language="sql")
                        
                        with col2:
                            st.markdown("**Blocking Query:**")
                            st.markdown(f"PID: {block.get('blocking_pid')}")
                            st.markdown(f"User: {block.get('blocking_user')}")
                            blocking_query = block.get("blocking_query", "")
                            if blocking_query:
                                st.code(blocking_query, language="sql")
            else:
                st.success("✅ No blocked queries")
            
            # All locks
            st.markdown("---")
            st.markdown(f"### All Locks ({data.get('total_locks', 0)})")
            
            if locks:
                # Create DataFrame
                locks_df = pd.DataFrame(locks)
                
                # Display table
                display_cols = ["type", "relation", "mode", "granted", "pid", "user", "state"]
                available_cols = [col for col in display_cols if col in locks_df.columns]
                
                st.dataframe(
                    locks_df[available_cols].rename(columns={
                        "type": "Type",
                        "relation": "Relation",
                        "mode": "Mode",
                        "granted": "Granted",
                        "pid": "PID",
                        "user": "User",
                        "state": "State"
                    }),
                    use_container_width=True
                )
            else:
                st.info("No locks found")
        
        else:
            st.error(f"Failed to fetch locks: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

