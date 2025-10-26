"""
API Discovery & Interactive Testing Page

Browse all available API endpoints and test them interactively.
"""

import streamlit as st
import httpx
import json
from datetime import datetime
from typing import Dict, List, Optional

def show(api_base_url: str):
    """Display API discovery and testing page."""
    st.title("🔌 API Discovery & Testing")
    st.markdown("Explore and test all available API endpoints interactively")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📋 Browse Endpoints", "🧪 Test Endpoint", "📊 Request History"])
    
    # ============================================================================
    # Tab 1: Browse Endpoints
    # ============================================================================
    with tab1:
        st.header("📋 Available Endpoints")
        
        # Fetch endpoints from /endpoints
        try:
            response = httpx.get(f"{api_base_url}/endpoints", timeout=10.0)
            
            if response.status_code == 200:
                endpoints = response.json()
                
                # Group by tags
                endpoints_by_tag = {}
                for endpoint in endpoints:
                    tags = endpoint.get('tags', ['Other'])
                    for tag in tags:
                        if tag not in endpoints_by_tag:
                            endpoints_by_tag[tag] = []
                        endpoints_by_tag[tag].append(endpoint)
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Endpoints", len(endpoints))
                with col2:
                    st.metric("Categories", len(endpoints_by_tag))
                with col3:
                    st.metric("API Version", "v1")
                
                # Search box
                st.markdown("---")
                search_query = st.text_input("🔍 Search Endpoints", placeholder="e.g., query, ingest, health")
                
                # Filter endpoints
                filtered_endpoints = endpoints
                if search_query:
                    search_lower = search_query.lower()
                    filtered_endpoints = [
                        e for e in endpoints
                        if search_lower in e.get('path', '').lower() or
                           search_lower in e.get('description', '').lower() or
                           any(search_lower in tag.lower() for tag in e.get('tags', []))
                    ]
                
                # Group filtered endpoints
                filtered_by_tag = {}
                for endpoint in filtered_endpoints:
                    tags = endpoint.get('tags', ['Other'])
                    for tag in tags:
                        if tag not in filtered_by_tag:
                            filtered_by_tag[tag] = []
                        filtered_by_tag[tag].append(endpoint)
                
                # Display by category
                for tag in sorted(filtered_by_tag.keys()):
                    with st.expander(f"**{tag}** ({len(filtered_by_tag[tag])} endpoints)", expanded=(search_query != "")):
                        for endpoint in sorted(filtered_by_tag[tag], key=lambda x: x.get('path', '')):
                            method = endpoint.get('method', 'GET')
                            path = endpoint.get('path', '')
                            description = endpoint.get('description', 'No description')
                            
                            # Method color coding
                            method_colors = {
                                'GET': '🟢',
                                'POST': '🔵',
                                'PUT': '🟡',
                                'DELETE': '🔴',
                                'PATCH': '🟠'
                            }
                            method_icon = method_colors.get(method, '⚪')
                            
                            st.markdown(f"{method_icon} **{method}** `{path}`")
                            st.caption(description)
                            
                            if st.button(f"Test {method} {path[:30]}...", key=f"test_{method}_{path}", use_container_width=True):
                                st.session_state['test_endpoint'] = {
                                    'method': method,
                                    'path': path,
                                    'description': description
                                }
                                st.rerun()
                            
                            st.markdown("---")
            
            else:
                st.error(f"❌ Failed to fetch endpoints: HTTP {response.status_code}")
        
        except Exception as e:
            st.error(f"❌ Error fetching endpoints: {str(e)}")
            st.info("💡 Make sure the API server is running at the configured base URL")
    
    # ============================================================================
    # Tab 2: Test Endpoint
    # ============================================================================
    with tab2:
        st.header("🧪 Test Endpoint")
        
        # Check if endpoint selected from tab 1
        if 'test_endpoint' in st.session_state:
            test_info = st.session_state['test_endpoint']
            st.success(f"Testing: **{test_info['method']}** `{test_info['path']}`")
            st.caption(test_info['description'])
            st.markdown("---")
        
        with st.form("test_endpoint_form"):
            # Method selection
            method = st.selectbox(
                "HTTP Method",
                options=["GET", "POST", "PUT", "DELETE", "PATCH"],
                index=0 if 'test_endpoint' not in st.session_state else 
                      ["GET", "POST", "PUT", "DELETE", "PATCH"].index(st.session_state.get('test_endpoint', {}).get('method', 'GET'))
            )
            
            # Path
            path = st.text_input(
                "Endpoint Path",
                value=st.session_state.get('test_endpoint', {}).get('path', '/health'),
                help="e.g., /api/v1/query, /health, /endpoints"
            )
            
            # Query parameters
            st.markdown("### Query Parameters")
            col1, col2 = st.columns(2)
            with col1:
                param_key1 = st.text_input("Key 1", key="param_key1")
                param_key2 = st.text_input("Key 2", key="param_key2")
            with col2:
                param_val1 = st.text_input("Value 1", key="param_val1")
                param_val2 = st.text_input("Value 2", key="param_val2")
            
            # Request body (for POST/PUT/PATCH)
            if method in ["POST", "PUT", "PATCH"]:
                st.markdown("### Request Body (JSON)")
                body_text = st.text_area(
                    "JSON Body",
                    value='{\n  "example": "value"\n}',
                    height=200,
                    help="Enter JSON request body"
                )
            
            # Headers
            st.markdown("### Headers")
            with st.expander("Add Custom Headers", expanded=False):
                header_key1 = st.text_input("Header Key", key="header_key1")
                header_val1 = st.text_input("Header Value", key="header_val1")
            
            # Timeout
            timeout = st.slider("Timeout (seconds)", min_value=5, max_value=300, value=30)
            
            # Submit
            submitted = st.form_submit_button("🚀 Send Request", use_container_width=True, type="primary")
        
        if submitted:
            # Build URL
            url = f"{api_base_url}{path}"
            
            # Build query parameters
            params = {}
            if param_key1:
                params[param_key1] = param_val1
            if param_key2:
                params[param_key2] = param_val2
            
            # Build headers
            headers = {}
            if method in ["POST", "PUT", "PATCH"]:
                headers["Content-Type"] = "application/json"
            if header_key1:
                headers[header_key1] = header_val1
            
            # Parse body
            body_json = None
            if method in ["POST", "PUT", "PATCH"]:
                try:
                    body_json = json.loads(body_text)
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON: {str(e)}")
                    st.stop()
            
            # Make request
            with st.spinner("Sending request..."):
                start_time = datetime.now()
                
                try:
                    if method == "GET":
                        response = httpx.get(url, params=params, headers=headers, timeout=timeout)
                    elif method == "POST":
                        response = httpx.post(url, params=params, json=body_json, headers=headers, timeout=timeout)
                    elif method == "PUT":
                        response = httpx.put(url, params=params, json=body_json, headers=headers, timeout=timeout)
                    elif method == "DELETE":
                        response = httpx.delete(url, params=params, headers=headers, timeout=timeout)
                    elif method == "PATCH":
                        response = httpx.patch(url, params=params, json=body_json, headers=headers, timeout=timeout)
                    
                    elapsed = (datetime.now() - start_time).total_seconds()
                    
                    # Display response
                    st.markdown("---")
                    st.subheader("📬 Response")
                    
                    # Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        status_emoji = "✅" if 200 <= response.status_code < 300 else "❌"
                        st.metric("Status Code", f"{status_emoji} {response.status_code}")
                    with col2:
                        st.metric("Response Time", f"{elapsed:.2f}s")
                    with col3:
                        content_length = len(response.content)
                        st.metric("Size", f"{content_length:,} bytes")
                    
                    # Response headers
                    with st.expander("📋 Response Headers", expanded=False):
                        st.json(dict(response.headers))
                    
                    # Response body
                    st.markdown("### Response Body")
                    try:
                        response_json = response.json()
                        st.json(response_json)
                        
                        # Download button
                        st.download_button(
                            "💾 Download Response",
                            data=json.dumps(response_json, indent=2),
                            file_name=f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    except:
                        st.code(response.text)
                        
                        # Download button for text
                        st.download_button(
                            "💾 Download Response",
                            data=response.text,
                            file_name=f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    
                    # Save to history
                    if 'request_history' not in st.session_state:
                        st.session_state.request_history = []
                    
                    st.session_state.request_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'method': method,
                        'url': url,
                        'status_code': response.status_code,
                        'elapsed': elapsed,
                        'params': params,
                        'body': body_json,
                        'response_size': content_length
                    })
                    
                    # Keep only last 50 requests
                    if len(st.session_state.request_history) > 50:
                        st.session_state.request_history = st.session_state.request_history[-50:]
                
                except httpx.TimeoutException:
                    st.error(f"⏱️ Request timed out after {timeout}s")
                except httpx.ConnectError:
                    st.error(f"❌ Cannot connect to {url}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # ============================================================================
    # Tab 3: Request History
    # ============================================================================
    with tab3:
        st.header("📊 Request History")
        
        if 'request_history' in st.session_state and st.session_state.request_history:
            history = st.session_state.request_history[::-1]  # Reverse for newest first
            
            # Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Requests", len(history))
            with col2:
                successful = sum(1 for r in history if 200 <= r['status_code'] < 300)
                st.metric("Successful", successful)
            with col3:
                avg_time = sum(r['elapsed'] for r in history) / len(history)
                st.metric("Avg Response Time", f"{avg_time:.2f}s")
            
            st.markdown("---")
            
            # Display history
            for i, req in enumerate(history[:20]):  # Show last 20
                with st.expander(
                    f"{req['method']} {req['url'][:50]}... - "
                    f"{'✅' if 200 <= req['status_code'] < 300 else '❌'} {req['status_code']} "
                    f"({req['elapsed']:.2f}s)",
                    expanded=False
                ):
                    st.markdown(f"**Timestamp:** {req['timestamp']}")
                    st.markdown(f"**Method:** {req['method']}")
                    st.markdown(f"**URL:** `{req['url']}`")
                    st.markdown(f"**Status Code:** {req['status_code']}")
                    st.markdown(f"**Response Time:** {req['elapsed']:.2f}s")
                    st.markdown(f"**Response Size:** {req['response_size']:,} bytes")
                    
                    if req['params']:
                        st.markdown("**Query Parameters:**")
                        st.json(req['params'])
                    
                    if req['body']:
                        st.markdown("**Request Body:**")
                        st.json(req['body'])
                    
                    if st.button("🔄 Repeat Request", key=f"repeat_{i}"):
                        st.session_state['test_endpoint'] = {
                            'method': req['method'],
                            'path': req['url'].replace(api_base_url, ''),
                            'description': 'Repeated from history'
                        }
                        st.rerun()
            
            # Clear history
            st.markdown("---")
            if st.button("🗑️ Clear History", type="secondary"):
                st.session_state.request_history = []
                st.rerun()
        
        else:
            st.info("No request history yet. Test some endpoints to see them here!")
    
    # Help section
    st.markdown("---")
    with st.expander("❓ **How to Use API Discovery**"):
        st.markdown("""
        ### API Discovery Workflow
        
        1. **Browse Endpoints (Tab 1)**
           - View all available API endpoints grouped by category
           - Search for specific endpoints
           - Click "Test" to try an endpoint
        
        2. **Test Endpoint (Tab 2)**
           - Configure HTTP method, path, parameters
           - Add request body for POST/PUT/PATCH
           - Send request and view response
           - Download response for analysis
        
        3. **Request History (Tab 3)**
           - View all requests you've made
           - See success rates and response times
           - Repeat previous requests
        
        ### Common Endpoints
        
        - `/health` - Check service health
        - `/endpoints` - List all endpoints
        - `/api/v1/query` - Query documents
        - `/api/v1/admin/stats` - Get service statistics
        - `/api/v1/admin/ingest` - Start ingestion job
        
        ### Tips
        
        - Use search in Tab 1 to quickly find endpoints
        - Check response headers for additional info
        - Download responses for further analysis
        - Review request history to debug issues
        """)

