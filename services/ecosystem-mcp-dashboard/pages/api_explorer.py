"""API Explorer page - Discover and test API endpoints."""

import streamlit as st
import httpx
import json
from typing import Dict, Any, List

def show(api_base_url: str):
    """Show API explorer page."""
    st.title("🔌 API Explorer")
    
    st.markdown("""
    Discover and test API endpoints from all containers using OpenAPI/Swagger specifications.
    """)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📚 Endpoints", "🧪 API Tester", "📖 Documentation"])
    
    with tab1:
        show_endpoints(api_base_url)
    
    with tab2:
        show_api_tester(api_base_url)
    
    with tab3:
        show_documentation(api_base_url)


def show_endpoints(api_base_url: str):
    """Display discovered API endpoints."""
    st.subheader("📚 Available API Endpoints")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Fetch OpenAPI spec
    try:
        response = httpx.get(f"{api_base_url}/openapi.json", timeout=10.0)
        
        if response.status_code == 200:
            openapi_spec = response.json()
            
            # Display API info
            info = openapi_spec.get("info", {})
            st.markdown(f"### {info.get('title', 'API')}")
            st.markdown(f"**Version:** {info.get('version', 'unknown')}")
            if info.get('description'):
                st.markdown(f"**Description:** {info.get('description')}")
            
            st.markdown("---")
            
            # Get paths
            paths = openapi_spec.get("paths", {})
            
            if not paths:
                st.info("No endpoints found in OpenAPI specification.")
                return
            
            # Group endpoints by tag
            endpoints_by_tag = {}
            
            for path, path_data in paths.items():
                for method, method_data in path_data.items():
                    if method in ['get', 'post', 'put', 'delete', 'patch']:
                        tags = method_data.get('tags', ['Untagged'])
                        
                        for tag in tags:
                            if tag not in endpoints_by_tag:
                                endpoints_by_tag[tag] = []
                            
                            endpoints_by_tag[tag].append({
                                'path': path,
                                'method': method.upper(),
                                'summary': method_data.get('summary', ''),
                                'description': method_data.get('description', ''),
                                'parameters': method_data.get('parameters', []),
                                'request_body': method_data.get('requestBody', {}),
                                'responses': method_data.get('responses', {})
                            })
            
            # Display endpoints by tag
            st.markdown(f"**Total Tags:** {len(endpoints_by_tag)}")
            st.markdown(f"**Total Endpoints:** {sum(len(eps) for eps in endpoints_by_tag.values())}")
            
            # Filter
            selected_tag = st.selectbox(
                "Filter by tag",
                ["All"] + sorted(endpoints_by_tag.keys())
            )
            
            # Display endpoints
            tags_to_show = [selected_tag] if selected_tag != "All" else sorted(endpoints_by_tag.keys())
            
            for tag in tags_to_show:
                if tag not in endpoints_by_tag:
                    continue
                
                with st.expander(f"📂 {tag} ({len(endpoints_by_tag[tag])} endpoints)", expanded=(selected_tag == tag)):
                    for endpoint in sorted(endpoints_by_tag[tag], key=lambda x: x['path']):
                        # Method color coding
                        method_color = {
                            'GET': '🟢',
                            'POST': '🔵',
                            'PUT': '🟠',
                            'DELETE': '🔴',
                            'PATCH': '🟡'
                        }.get(endpoint['method'], '⚪')
                        
                        st.markdown(f"#### {method_color} `{endpoint['method']}` {endpoint['path']}")
                        
                        if endpoint['summary']:
                            st.markdown(f"**Summary:** {endpoint['summary']}")
                        
                        if endpoint['description']:
                            st.markdown(f"**Description:** {endpoint['description']}")
                        
                        # Parameters
                        if endpoint['parameters']:
                            st.markdown("**Parameters:**")
                            param_data = []
                            for param in endpoint['parameters']:
                                param_data.append({
                                    'Name': param.get('name', ''),
                                    'In': param.get('in', ''),
                                    'Type': param.get('schema', {}).get('type', 'unknown'),
                                    'Required': '✅' if param.get('required') else '❌',
                                    'Description': param.get('description', '')
                                })
                            
                            import pandas as pd
                            df = pd.DataFrame(param_data)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        # Request body
                        if endpoint['request_body']:
                            st.markdown("**Request Body:**")
                            content = endpoint['request_body'].get('content', {})
                            for content_type, schema_data in content.items():
                                st.markdown(f"Content-Type: `{content_type}`")
                                schema = schema_data.get('schema', {})
                                if schema:
                                    st.json(schema)
                        
                        # Responses
                        if endpoint['responses']:
                            st.markdown("**📤 Responses:**")
                            for status_code, response_data in endpoint['responses'].items():
                                st.markdown(f"- **{status_code}:** {response_data.get('description', '')}")
                                content = response_data.get('content', {})
                                if content:
                                    for content_type, schema_data in content.items():
                                        st.markdown(f"  Content-Type: `{content_type}`")
                                        schema = schema_data.get('schema', {})
                                        if schema:
                                            with st.container():
                                                st.json(schema)
                        
                        st.markdown("---")
        
        else:
            st.error(f"Failed to fetch OpenAPI spec: {response.status_code}")
            st.info("Try accessing the API docs directly:")
            st.markdown(f"[OpenAPI Docs]({api_base_url}/docs)")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def show_api_tester(api_base_url: str):
    """Interactive API endpoint tester."""
    st.subheader("🧪 API Tester")
    
    st.markdown("Test API endpoints interactively.")
    
    # Manual endpoint input
    col1, col2 = st.columns([1, 3])
    
    with col1:
        method = st.selectbox(
            "Method",
            ["GET", "POST", "PUT", "DELETE", "PATCH"],
            key="test_method"
        )
    
    with col2:
        endpoint = st.text_input(
            "Endpoint",
            placeholder="/api/v1/health",
            key="test_endpoint"
        )
    
    # Request configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Headers**")
        headers_text = st.text_area(
            "Headers (JSON)",
            value='{\n  "Content-Type": "application/json"\n}',
            height=100,
            key="test_headers"
        )
    
    with col2:
        st.markdown("**Body**")
        body_text = st.text_area(
            "Request Body (JSON)",
            value='{}',
            height=100,
            key="test_body"
        )
    
    if st.button("▶️ Send Request", type="primary", use_container_width=True):
        if not endpoint:
            st.warning("Please enter an endpoint.")
            return
        
        # Build full URL
        if endpoint.startswith('/'):
            full_url = f"{api_base_url}{endpoint}"
        else:
            full_url = f"{api_base_url}/{endpoint}"
        
        try:
            # Parse headers and body
            headers = json.loads(headers_text) if headers_text else {}
            body = json.loads(body_text) if body_text and method in ['POST', 'PUT', 'PATCH'] else None
            
            with st.spinner("Sending request..."):
                # Make request
                if method == 'GET':
                    response = httpx.get(full_url, headers=headers, timeout=10.0)
                elif method == 'POST':
                    response = httpx.post(full_url, headers=headers, json=body, timeout=10.0)
                elif method == 'PUT':
                    response = httpx.put(full_url, headers=headers, json=body, timeout=10.0)
                elif method == 'DELETE':
                    response = httpx.delete(full_url, headers=headers, timeout=10.0)
                elif method == 'PATCH':
                    response = httpx.patch(full_url, headers=headers, json=body, timeout=10.0)
                
                # Display response
                st.markdown("### 📤 Response")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    status_color = "🟢" if response.status_code < 300 else "🟠" if response.status_code < 400 else "🔴"
                    st.metric("Status Code", f"{status_color} {response.status_code}")
                
                with col2:
                    st.metric("Response Time", f"{response.elapsed.total_seconds():.2f}s")
                
                with col3:
                    st.metric("Size", f"{len(response.content)} bytes")
                
                # Response headers
                with st.expander("📋 Response Headers"):
                    st.json(dict(response.headers))
                
                # Response body
                st.markdown("**Response Body:**")
                try:
                    response_json = response.json()
                    st.json(response_json)
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Response",
                        data=json.dumps(response_json, indent=2),
                        file_name="api_response.json",
                        mime="application/json"
                    )
                except:
                    st.code(response.text, language="text")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Response",
                        data=response.text,
                        file_name="api_response.txt",
                        mime="text/plain"
                    )
        
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {str(e)}")
        except httpx.ConnectError:
            st.error(f"❌ Cannot connect to {full_url}")
        except Exception as e:
            st.error(f"Error: {str(e)}")


def show_documentation(api_base_url: str):
    """Show API documentation links."""
    st.subheader("📖 API Documentation")
    
    st.markdown("""
    Access interactive API documentation for the Ecosystem MCP service.
    """)
    
    # Documentation links
    st.markdown("### 📚 Available Documentation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Swagger UI")
        st.markdown(f"Interactive API explorer with Swagger UI")
        st.link_button(
            "🔗 Open Swagger UI",
            f"{api_base_url}/docs",
            use_container_width=True
        )
    
    with col2:
        st.markdown("#### ReDoc")
        st.markdown(f"Clean API documentation with ReDoc")
        st.link_button(
            "🔗 Open ReDoc",
            f"{api_base_url}/redoc",
            use_container_width=True
        )
    
    st.markdown("---")
    
    # OpenAPI spec download
    st.markdown("### 📥 Download Specifications")
    
    try:
        response = httpx.get(f"{api_base_url}/openapi.json", timeout=10.0)
        
        if response.status_code == 200:
            openapi_spec = response.json()
            
            st.download_button(
                label="📥 Download OpenAPI Spec (JSON)",
                data=json.dumps(openapi_spec, indent=2),
                file_name="openapi.json",
                mime="application/json",
                use_container_width=True
            )
            
            # Show spec info
            info = openapi_spec.get("info", {})
            st.info(f"**API:** {info.get('title', 'Unknown')} v{info.get('version', 'unknown')}")
            
            # Stats
            paths = openapi_spec.get("paths", {})
            total_endpoints = sum(
                1 for path_data in paths.values()
                for method in path_data.keys()
                if method in ['get', 'post', 'put', 'delete', 'patch']
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Endpoints", total_endpoints)
            with col2:
                st.metric("Paths", len(paths))
            with col3:
                schemas = openapi_spec.get("components", {}).get("schemas", {})
                st.metric("Schemas", len(schemas))
        
        else:
            st.warning(f"Could not fetch OpenAPI spec: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    
    # Quick links
    st.markdown("### 🔗 Quick Links")
    
    quick_links = {
        "Health Check": "/health",
        "Diagnostics": "/api/v1/diagnostics/health",
        "Configuration": "/api/v1/config/current",
        "Cache Stats": "/api/v1/cache/stats",
        "Containers": "/api/v1/containers",
        "Redis Info": "/api/v1/redis/info",
        "PostgreSQL Info": "/api/v1/postgres/info"
    }
    
    for name, path in quick_links.items():
        col1, col2 = st.columns([2, 1])
        with col1:
            st.text(f"{name}: {path}")
        with col2:
            if st.button(f"Test", key=f"test_{name}", use_container_width=True):
                try:
                    response = httpx.get(f"{api_base_url}{path}", timeout=5.0)
                    if response.status_code == 200:
                        st.success(f"✅ {response.status_code}")
                    else:
                        st.error(f"❌ {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Error")

