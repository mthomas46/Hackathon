#!/usr/bin/env python3
"""
Comprehensive Dashboard Frontend Audit
Checks all dashboard pages for proper backend integration
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Dashboard views directory
DASHBOARD_DIR = Path("/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-dashboard/dashboard_views")

# Known backend endpoints
BACKEND_ENDPOINTS = {
    "GET": [
        "/health",
        "/api/v1/diagnostics/health",
        "/api/v1/admin/stats",
        "/api/v1/cache/stats",
        "/api/v1/config/current",
        "/api/v1/config/health",
        "/api/v1/containers",
        "/api/v1/redis/info",
        "/api/v1/postgres/info",
        "/api/v1/documents",
        "/api/v1/contexts",
        "/api/v1/workers/health",
        "/api/v1/admin/queue-status",
    ],
    "POST": [
        "/api/v1/query",
        "/api/v1/query/enhanced",
        "/api/v1/query/multi-pass",
        "/api/v1/query/context-aware",
        "/api/v1/admin/ingest",
        "/api/v1/admin/clear-cache",
    ],
}

def extract_api_calls(file_path: Path) -> List[Tuple[str, str]]:
    """Extract API endpoint calls from a Python file."""
    api_calls = []
    
    try:
        content = file_path.read_text()
        
        # Pattern 1: httpx.get/post/put/delete
        httpx_pattern = r'httpx\.(get|post|put|delete)\s*\(\s*f?"([^"]+)"'
        for match in re.finditer(httpx_pattern, content):
            method = match.group(1).upper()
            endpoint = match.group(2)
            # Clean up f-string format
            endpoint = re.sub(r'\{[^}]+\}', '{param}', endpoint)
            endpoint = endpoint.replace('{api_base_url}', '').replace('{API_BASE}', '')
            api_calls.append((method, endpoint))
        
        # Pattern 2: requests.get/post/put/delete
        requests_pattern = r'requests\.(get|post|put|delete)\s*\(\s*f?"([^"]+)"'
        for match in re.finditer(requests_pattern, content):
            method = match.group(1).upper()
            endpoint = match.group(2)
            endpoint = re.sub(r'\{[^}]+\}', '{param}', endpoint)
            endpoint = endpoint.replace('{api_base_url}', '').replace('{API_BASE}', '')
            api_calls.append((method, endpoint))
        
        # Pattern 3: make_api_request calls
        api_request_pattern = r'make_api_request\([^,]+,\s*"([^"]+)"[^)]*method="(\w+)"'
        for match in re.finditer(api_request_pattern, content):
            endpoint = match.group(1)
            method = match.group(2).upper()
            api_calls.append((method, endpoint))
        
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return api_calls

def check_endpoint_exists(method: str, endpoint: str) -> bool:
    """Check if endpoint exists in backend."""
    # Normalize endpoint
    endpoint = endpoint.strip()
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint
    
    # Check exact match
    if endpoint in BACKEND_ENDPOINTS.get(method, []):
        return True
    
    # Check pattern match (for parameterized endpoints)
    for known_endpoint in BACKEND_ENDPOINTS.get(method, []):
        # Replace {param} with regex pattern
        pattern = known_endpoint.replace('{param}', r'[^/]+')
        if re.match(f'^{pattern}$', endpoint):
            return True
    
    return False

def audit_dashboard():
    """Run comprehensive audit of all dashboard views."""
    print("**Date:** October 29, 2025")
    print("**Status:** Dashboard Frontend Audit")
    print("**Scope:** All dashboard views\n")
    print("# Dashboard Frontend Audit Report\n")
    print("## 📊 Comprehensive Integration Check\n")
    
    total_files = 0
    total_endpoints = 0
    valid_endpoints = 0
    invalid_endpoints = []
    
    print("## 🔍 Per-File Analysis\n")
    
    for file_path in sorted(DASHBOARD_DIR.glob("*.py")):
        if file_path.name.startswith("__"):
            continue
        
        total_files += 1
        api_calls = extract_api_calls(file_path)
        
        if api_calls:
            print(f"### {file_path.name}\n")
            print("| Method | Endpoint | Status |")
            print("|--------|----------|--------|")
            
            for method, endpoint in api_calls:
                total_endpoints += 1
                exists = check_endpoint_exists(method, endpoint)
                
                if exists:
                    valid_endpoints += 1
                    status = "✅ Valid"
                else:
                    invalid_endpoints.append((file_path.name, method, endpoint))
                    status = "❌ Unknown"
                
                # Truncate long endpoints
                display_endpoint = endpoint if len(endpoint) < 50 else endpoint[:47] + "..."
                print(f"| {method} | `{display_endpoint}` | {status} |")
            
            print()
    
    # Summary
    print("## 📊 Summary\n")
    print(f"- **Files Scanned**: {total_files}")
    print(f"- **API Calls Found**: {total_endpoints}")
    print(f"- **Valid Endpoints**: {valid_endpoints}")
    print(f"- **Unknown Endpoints**: {len(invalid_endpoints)}\n")
    
    if invalid_endpoints:
        print("## ⚠️ Unknown Endpoints\n")
        print("| File | Method | Endpoint |")
        print("|------|--------|----------|")
        for filename, method, endpoint in invalid_endpoints:
            display_endpoint = endpoint if len(endpoint) < 50 else endpoint[:47] + "..."
            print(f"| {filename} | {method} | `{display_endpoint}` |")
        print()
    
    # Success rate
    success_rate = (valid_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0
    print(f"## 🎯 Integration Health\n")
    print(f"**Success Rate**: {success_rate:.1f}%\n")
    
    if success_rate == 100:
        print("### ✅ ALL ENDPOINTS VALID!\n")
        print("All dashboard views are properly integrated with backend endpoints.")
    elif success_rate >= 90:
        print("### 🟢 EXCELLENT INTEGRATION\n")
        print("Most endpoints are valid. Minor cleanup needed.")
    elif success_rate >= 75:
        print("### 🟡 GOOD INTEGRATION\n")
        print("Good integration but some endpoints need attention.")
    else:
        print("### 🔴 NEEDS ATTENTION\n")
        print("Several endpoints require investigation.")

if __name__ == "__main__":
    audit_dashboard()

