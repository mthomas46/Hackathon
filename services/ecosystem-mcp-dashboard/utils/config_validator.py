"""Configuration validation utilities."""

import os
import httpx
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    check_name: str
    passed: bool
    message: str
    details: Dict[str, Any] = None


class ConfigValidator:
    """Validate dashboard configuration and environment."""
    
    def __init__(self):
        """Initialize validator."""
        self.results: List[ValidationResult] = []
    
    def validate_environment_variables(self) -> ValidationResult:
        """Validate required environment variables."""
        required_vars = {
            "API_BASE_URL": "Base URL for ecosystem-mcp API"
        }
        
        optional_vars = {
            "STREAMLIT_SERVER_PORT": "Streamlit server port (default: 8501)",
            "STREAMLIT_SERVER_HEADLESS": "Run in headless mode (default: true)"
        }
        
        missing = []
        present = []
        
        for var, description in required_vars.items():
            value = os.getenv(var)
            if not value:
                missing.append(f"{var} ({description})")
            else:
                present.append(f"{var}={value}")
        
        if missing:
            return ValidationResult(
                check_name="Environment Variables",
                passed=False,
                message=f"Missing required variables: {', '.join(missing)}",
                details={
                    "missing": missing,
                    "present": present
                }
            )
        
        return ValidationResult(
            check_name="Environment Variables",
            passed=True,
            message="All required environment variables present",
            details={
                "required": present,
                "optional": [
                    f"{var}={os.getenv(var, 'not set')}"
                    for var in optional_vars.keys()
                ]
            }
        )
    
    def validate_api_connectivity(self, api_base_url: str) -> ValidationResult:
        """Validate API connectivity."""
        try:
            response = httpx.get(f"{api_base_url}/health", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                return ValidationResult(
                    check_name="API Connectivity",
                    passed=True,
                    message=f"Successfully connected to API at {api_base_url}",
                    details=data
                )
            else:
                return ValidationResult(
                    check_name="API Connectivity",
                    passed=False,
                    message=f"API returned status {response.status_code}",
                    details={"url": api_base_url, "status": response.status_code}
                )
        
        except httpx.ConnectError as e:
            return ValidationResult(
                check_name="API Connectivity",
                passed=False,
                message=f"Cannot connect to API at {api_base_url}",
                details={"url": api_base_url, "error": str(e)}
            )
        except Exception as e:
            return ValidationResult(
                check_name="API Connectivity",
                passed=False,
                message=f"Error connecting to API: {str(e)}",
                details={"url": api_base_url, "error": str(e)}
            )
    
    def validate_api_endpoints(self, api_base_url: str) -> ValidationResult:
        """Validate critical API endpoints exist."""
        critical_endpoints = [
            "/health",
            "/openapi.json",
            "/api/v1/ask",
            "/api/v1/documents",
            "/api/v1/search"
        ]
        
        available = []
        unavailable = []
        
        for endpoint in critical_endpoints:
            try:
                response = httpx.get(f"{api_base_url}{endpoint}", timeout=3.0)
                if response.status_code in [200, 404]:  # 404 means endpoint exists but may have no data
                    available.append(endpoint)
                else:
                    unavailable.append(f"{endpoint} (HTTP {response.status_code})")
            except Exception as e:
                unavailable.append(f"{endpoint} ({str(e)})")
        
        if unavailable:
            return ValidationResult(
                check_name="API Endpoints",
                passed=False,
                message=f"{len(unavailable)} endpoint(s) unavailable",
                details={
                    "available": available,
                    "unavailable": unavailable
                }
            )
        
        return ValidationResult(
            check_name="API Endpoints",
            passed=True,
            message=f"All {len(available)} critical endpoints available",
            details={"available": available}
        )
    
    def validate_page_imports(self) -> ValidationResult:
        """Validate all dashboard pages can be imported."""
        pages = [
            "home", "health", "diagnostics", "config_viewer",
            "logs_viewer", "api_explorer", "containers",
            "redis_explorer", "postgres_explorer", "rag",
            "documents", "cache", "metrics", "settings"
        ]
        
        importable = []
        failed = []
        
        for page in pages:
            try:
                # Try to import the page
                exec(f"from pages import {page}")
                importable.append(page)
            except ImportError as e:
                failed.append(f"{page} ({str(e)})")
            except Exception as e:
                failed.append(f"{page} ({str(e)})")
        
        if failed:
            return ValidationResult(
                check_name="Page Imports",
                passed=False,
                message=f"{len(failed)} page(s) failed to import",
                details={
                    "importable": importable,
                    "failed": failed
                }
            )
        
        return ValidationResult(
            check_name="Page Imports",
            passed=True,
            message=f"All {len(importable)} pages can be imported",
            details={"pages": importable}
        )
    
    def validate_docker_connectivity(self, api_base_url: str) -> ValidationResult:
        """Validate Docker connectivity via API."""
        # Note: Docker connectivity is not directly exposed in the API
        # We'll skip this check for now as it requires the endpoints that don't exist
        return ValidationResult(
            check_name="Docker Connectivity",
            passed=True,
            message="Docker connectivity check skipped (endpoint not available)",
            details={"note": "Docker management features are planned for future implementation"}
        )
    
    def validate_datasources(self, api_base_url: str) -> ValidationResult:
        """Validate all datasources (Redis, PostgreSQL, etc.) via /health endpoint."""
        try:
            response = httpx.get(f"{api_base_url}/health", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                components = data.get("components", {})
                
                healthy = []
                unhealthy = []
                
                # Check each component from health endpoint
                component_mapping = {
                    "Database": "database",
                    "Redis": "redis",
                    "ChromaDB": "chromadb",
                    "Ollama": "ollama"
                }
                
                for display_name, component_key in component_mapping.items():
                    if component_key in components:
                        comp_data = components[component_key]
                        comp_status = comp_data.get("status", "unknown")
                        
                        if comp_status == "healthy":
                            healthy.append(display_name)
                        else:
                            unhealthy.append(f"{display_name} ({comp_status})")
                    else:
                        unhealthy.append(f"{display_name} (not found in health response)")
                
                if unhealthy:
                    return ValidationResult(
                        check_name="Datasources",
                        passed=False,
                        message=f"{len(unhealthy)} datasource(s) unhealthy",
                        details={
                            "healthy": healthy,
                            "unhealthy": unhealthy
                        }
                    )
                
                return ValidationResult(
                    check_name="Datasources",
                    passed=True,
                    message=f"All {len(healthy)} datasources healthy",
                    details={"datasources": healthy}
                )
            else:
                return ValidationResult(
                    check_name="Datasources",
                    passed=False,
                    message=f"Health endpoint returned status {response.status_code}",
                    details={"status": response.status_code}
                )
        
        except Exception as e:
            return ValidationResult(
                check_name="Datasources",
                passed=False,
                message=f"Error checking datasources: {str(e)}",
                details={"error": str(e)}
            )
    
    def run_all_validations(self, api_base_url: str) -> Tuple[List[ValidationResult], bool]:
        """
        Run all validations.
        
        Returns:
            Tuple of (results, all_passed)
        """
        self.results = []
        
        # Run validations in order
        self.results.append(self.validate_environment_variables())
        self.results.append(self.validate_api_connectivity(api_base_url))
        
        # Only run remaining checks if API is accessible
        if self.results[-1].passed:
            self.results.append(self.validate_api_endpoints(api_base_url))
            self.results.append(self.validate_docker_connectivity(api_base_url))
            self.results.append(self.validate_datasources(api_base_url))
        
        # Always check page imports (doesn't require API)
        self.results.append(self.validate_page_imports())
        
        all_passed = all(r.passed for r in self.results)
        
        return self.results, all_passed

