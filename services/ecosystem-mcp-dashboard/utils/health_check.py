"""Health check utilities for the dashboard."""

import httpx
import streamlit as st
from typing import Dict, Any, Optional
import time


class HealthChecker:
    """Check health of backend services."""
    
    def __init__(self, api_base_url: str, timeout: float = 5.0):
        """Initialize health checker.
        
        Args:
            api_base_url: Base URL for the API
            timeout: Request timeout in seconds
        """
        self.api_base_url = api_base_url
        self.timeout = timeout
        self._last_check: Optional[Dict[str, Any]] = None
        self._last_check_time: float = 0
        self._cache_duration: float = 10.0  # Cache for 10 seconds
    
    def check_health(self, use_cache: bool = True) -> Dict[str, Any]:
        """Check API and service health.
        
        Args:
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with health status
        """
        # Return cached result if available and fresh
        if use_cache and self._last_check and (time.time() - self._last_check_time) < self._cache_duration:
            return self._last_check
        
        health_status = {
            "api_reachable": False,
            "api_healthy": False,
            "postgres_healthy": False,
            "redis_healthy": False,
            "chromadb_healthy": False,
            "error": None,
            "components": {}
        }
        
        try:
            response = httpx.get(
                f"{self.api_base_url}/health",
                timeout=self.timeout
            )
            
            health_status["api_reachable"] = True
            
            if response.status_code == 200:
                data = response.json()
                health_status["api_healthy"] = data.get("status") == "healthy"
                
                # Parse component health
                components = data.get("components", {})
                health_status["components"] = components
                
                # Check individual components
                if "database" in components:
                    health_status["postgres_healthy"] = components["database"].get("status") == "healthy"
                
                if "redis" in components:
                    health_status["redis_healthy"] = components["redis"].get("status") == "healthy"
                
                if "chromadb" in components:
                    health_status["chromadb_healthy"] = components["chromadb"].get("status") == "healthy"
            
        except httpx.ConnectError:
            health_status["error"] = "Cannot connect to API"
        except httpx.TimeoutException:
            health_status["error"] = "API request timed out"
        except Exception as e:
            health_status["error"] = f"Unexpected error: {str(e)}"
        
        # Cache the result
        self._last_check = health_status
        self._last_check_time = time.time()
        
        return health_status
    
    def display_health_status(self, health_status: Optional[Dict[str, Any]] = None):
        """Display health status in Streamlit.
        
        Args:
            health_status: Health status dict (will check if None)
        """
        if health_status is None:
            health_status = self.check_health()
        
        # Display overall status
        if not health_status["api_reachable"]:
            st.error("🔴 **API Unreachable** - Cannot connect to backend API")
            if health_status["error"]:
                st.caption(f"Error: {health_status['error']}")
            st.info("💡 Make sure the API is running on the correct port")
            return False
        
        if not health_status["api_healthy"]:
            st.warning("🟡 **API Issues** - Backend API is reachable but not healthy")
            return False
        
        # Show component status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if health_status["postgres_healthy"]:
                st.success("✅ PostgreSQL")
            else:
                st.error("❌ PostgreSQL")
        
        with col2:
            if health_status["redis_healthy"]:
                st.success("✅ Redis")
            else:
                st.error("❌ Redis")
        
        with col3:
            if health_status["chromadb_healthy"]:
                st.success("✅ ChromaDB")
            else:
                st.warning("⚠️  ChromaDB")
        
        # Show warnings for unhealthy components
        unhealthy = []
        if not health_status["postgres_healthy"]:
            unhealthy.append("PostgreSQL")
        if not health_status["redis_healthy"]:
            unhealthy.append("Redis")
        
        if unhealthy:
            st.warning(f"⚠️  Some services are unavailable: {', '.join(unhealthy)}")
            with st.expander("🔧 How to fix"):
                st.markdown("""
                **Start required services:**
                
                1. **Using Docker (Recommended):**
                   ```bash
                   cd /Users/mykalthomas/Documents/work/Hackathon
                   docker compose -f services/ecosystem-mcp/docker-compose.yml up -d postgres redis
                   ```
                
                2. **Using Homebrew:**
                   ```bash
                   brew services start postgresql@14
                   brew services start redis
                   ```
                
                3. **Check if services are running:**
                   ```bash
                   docker ps  # For Docker
                   brew services list  # For Homebrew
                   ```
                """)
            return False
        
        return True
    
    def require_healthy_api(self, show_status: bool = True) -> bool:
        """Check if API is healthy and show error if not.
        
        Args:
            show_status: Whether to display health status
            
        Returns:
            True if healthy, False otherwise
        """
        health_status = self.check_health()
        
        if show_status:
            self.display_health_status(health_status)
        
        return health_status["api_healthy"]

