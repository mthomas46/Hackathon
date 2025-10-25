"""
Path Validator Widget

Validates paths before ingestion and provides user feedback.
"""

import streamlit as st
import httpx
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PathValidator:
    """Validates and resolves paths for ingestion."""
    
    @staticmethod
    def validate_path(
        api_base_url: str,
        path: str,
        resolve_host_path: bool = True,
        timeout: float = 5.0
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Validate a path using the backend path resolver.
        
        Args:
            api_base_url: Base URL of the API
            path: Path to validate
            resolve_host_path: Whether to resolve as host path
            timeout: Request timeout
            
        Returns:
            Tuple of (is_valid, validation_data, error_message)
        """
        try:
            response = httpx.post(
                f"{api_base_url}/api/v1/path/resolve",
                json={
                    "path": path,
                    "resolve_host_path": resolve_host_path
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return True, data, None
            else:
                error_data = response.json()
                error_msg = error_data.get("detail", f"HTTP {response.status_code}")
                return False, None, error_msg
                
        except httpx.ConnectError:
            return False, None, "Cannot connect to API"
        except httpx.TimeoutException:
            return False, None, "Request timed out"
        except Exception as e:
            return False, None, str(e)


def show_path_validator_widget(
    api_base_url: str,
    default_path: str = "",
    key_prefix: str = "path_validator"
) -> Optional[Dict]:
    """
    Show an interactive path validator widget.
    
    Args:
        api_base_url: Base URL of the API
        default_path: Default path to show
        key_prefix: Unique prefix for widget keys
        
    Returns:
        Validation result if path is valid, None otherwise
    """
    st.markdown("### 📂 Path Validation")
    
    # Path input
    path = st.text_input(
        "Path to Validate",
        value=default_path,
        key=f"{key_prefix}_path_input",
        help="Enter a path on your host machine or in the container"
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        resolve_host = st.checkbox(
            "Resolve as Host Path",
            value=True,
            key=f"{key_prefix}_resolve_host",
            help="If checked, will find git root from host path"
        )
    
    with col2:
        validate_btn = st.button(
            "🔍 Validate",
            key=f"{key_prefix}_validate_btn",
            use_container_width=True,
            type="primary"
        )
    
    # Perform validation on button click
    if validate_btn and path:
        with st.spinner("Validating path..."):
            is_valid, validation_data, error_msg = PathValidator.validate_path(
                api_base_url=api_base_url,
                path=path,
                resolve_host_path=resolve_host
            )
            
            if is_valid and validation_data:
                st.success("✅ **Path is valid!**")
                
                # Display validation results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📍 Resolved Information:**")
                    st.markdown(f"- **Resolved Path:** `{validation_data.get('resolved_path', 'N/A')}`")
                    st.markdown(f"- **Git Root:** `{validation_data.get('git_root', 'N/A')}`")
                    st.markdown(f"- **Is Git Repo:** {'✅ Yes' if validation_data.get('is_git_repo') else '❌ No'}")
                
                with col2:
                    st.markdown("**📊 Repository Info:**")
                    if validation_data.get("is_git_repo"):
                        git_info = validation_data.get("git_info", {})
                        st.markdown(f"- **Current Branch:** `{git_info.get('current_branch', 'N/A')}`")
                        st.markdown(f"- **Total Commits:** `{git_info.get('total_commits', 0)}`")
                        st.markdown(f"- **Total Files:** `{git_info.get('total_files', 0)}`")
                    else:
                        st.markdown("Not a git repository")
                
                # Show full validation data in expander
                with st.expander("🔍 Full Validation Data", expanded=False):
                    st.json(validation_data)
                
                return validation_data
            
            else:
                st.error(f"❌ **Path validation failed:** {error_msg}")
                
                # Show helpful suggestions
                st.markdown("**💡 Suggestions:**")
                if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
                    st.markdown("- Double-check the path spelling")
                    st.markdown("- Ensure the path exists on the system")
                    st.markdown("- Try using an absolute path")
                elif "permission" in error_msg.lower():
                    st.markdown("- Check file/directory permissions")
                    st.markdown("- Ensure the service has access to the path")
                elif "git" in error_msg.lower():
                    st.markdown("- Ensure the directory is a git repository")
                    st.markdown("- Try `git init` if you want to initialize it")
                
                return None
    
    elif validate_btn and not path:
        st.warning("⚠️ Please enter a path to validate")
    
    return None


def show_path_suggestions(api_base_url: str, key_prefix: str = "path_suggestions"):
    """
    Show common path suggestions for quick selection.
    
    Args:
        api_base_url: Base URL of the API
        key_prefix: Unique prefix for widget keys
    """
    with st.expander("💡 Common Paths", expanded=False):
        st.markdown("**Quick Select:**")
        
        common_paths = [
            {
                "label": "🏠 Hackathon Project",
                "path": "/Users/mykalthomas/Documents/work/Hackathon",
                "description": "Main project directory"
            },
            {
                "label": "🧠 Ecosystem MCP",
                "path": "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp",
                "description": "Ecosystem MCP service"
            },
            {
                "label": "📊 Dashboard",
                "path": "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-dashboard",
                "description": "Dashboard service"
            },
            {
                "label": "⚡ Embedding Service",
                "path": "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-embedding",
                "description": "Embedding service"
            },
            {
                "label": "📦 Container /app",
                "path": "/app",
                "description": "Mounted workspace in container"
            }
        ]
        
        for i, suggestion in enumerate(common_paths):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"**{suggestion['label']}**")
                st.caption(f"{suggestion['description']}")
                st.code(suggestion['path'], language="bash")
            
            with col2:
                if st.button("📋 Use", key=f"{key_prefix}_use_{i}", use_container_width=True):
                    st.session_state[f"{key_prefix}_selected_path"] = suggestion['path']
                    st.rerun()


def get_path_health_indicator(
    api_base_url: str,
    path: str,
    resolve_host_path: bool = True
) -> str:
    """
    Get a quick health indicator for a path.
    
    Args:
        api_base_url: Base URL of the API
        path: Path to check
        resolve_host_path: Whether to resolve as host path
        
    Returns:
        Health indicator emoji (🟢/🟡/🔴)
    """
    try:
        is_valid, data, error = PathValidator.validate_path(
            api_base_url=api_base_url,
            path=path,
            resolve_host_path=resolve_host_path,
            timeout=2.0
        )
        
        if is_valid:
            if data and data.get("is_git_repo"):
                return "🟢"  # Perfect - valid git repo
            else:
                return "🟡"  # OK - valid but not git
        else:
            return "🔴"  # Invalid path
            
    except Exception:
        return "⚪"  # Unknown


def show_inline_path_validator(
    api_base_url: str,
    path: str,
    resolve_host_path: bool = True,
    key_prefix: str = "inline_validator"
):
    """
    Show a compact inline path validator.
    
    Args:
        api_base_url: Base URL of the API
        path: Path to validate
        resolve_host_path: Whether to resolve as host path
        key_prefix: Unique prefix for widget keys
    """
    if not path:
        return
    
    col1, col2, col3 = st.columns([1, 4, 2])
    
    with col1:
        # Show health indicator
        indicator = get_path_health_indicator(api_base_url, path, resolve_host_path)
        st.markdown(f"### {indicator}")
    
    with col2:
        st.caption("Path Status")
        if indicator == "🟢":
            st.success("Valid Git Repository", icon="✅")
        elif indicator == "🟡":
            st.warning("Valid Path (Not Git)", icon="⚠️")
        elif indicator == "🔴":
            st.error("Invalid Path", icon="❌")
        else:
            st.info("Status Unknown", icon="ℹ️")
    
    with col3:
        if st.button("🔍 Validate", key=f"{key_prefix}_inline_validate", use_container_width=True):
            with st.spinner("Validating..."):
                is_valid, data, error = PathValidator.validate_path(
                    api_base_url=api_base_url,
                    path=path,
                    resolve_host_path=resolve_host_path
                )
                
                if is_valid and data:
                    st.success(f"✅ Valid: `{data.get('resolved_path', path)}`")
                else:
                    st.error(f"❌ {error}")

