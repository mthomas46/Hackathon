#!/usr/bin/env python3
"""
Service Documentation Validator

Validates that a service has comprehensive documentation and standard API endpoints
following the Service Documentation Strategy and API Standardization Strategy.

Usage:
    python validate_service_documentation.py <service-name>

Example:
    python validate_service_documentation.py doc-store
"""

import os
import sys
import json
import re
import httpx
from pathlib import Path
from typing import Dict, List, Tuple


def check_readme_exists(service_path: Path) -> Tuple[bool, List[str]]:
    """Check if README.md exists"""
    issues = []
    readme_path = service_path / "README.md"
    
    if not readme_path.exists():
        issues.append("README.md not found")
        return False, issues
    
    content = readme_path.read_text()
    
    if len(content) < 500:
        issues.append("README.md is too short (< 500 characters)")
    
    return True, issues


def check_readme_sections(service_path: Path) -> Tuple[Dict[str, bool], List[str]]:
    """Check if README has all required sections"""
    issues = []
    sections = {
        "overview": False,
        "architecture": False,
        "dependencies": False,
        "endpoints": False,
        "relationships": False,
        "quick_start": False,
        "integration": False
    }
    
    readme_path = service_path / "README.md"
    if not readme_path.exists():
        issues.append("README.md not found")
        return sections, issues
    
    content = readme_path.read_text().lower()
    
    # Check for required sections
    if "overview" in content or "capabilities" in content:
        sections["overview"] = True
    else:
        issues.append("Missing Overview/Capabilities section")
    
    if "architecture" in content:
        sections["architecture"] = True
    else:
        issues.append("Missing Architecture section")
    
    if "dependencies" in content or "libraries" in content:
        sections["dependencies"] = True
    else:
        issues.append("Missing Dependencies section")
    
    if "endpoints" in content or "api" in content:
        sections["endpoints"] = True
    else:
        issues.append("Missing Endpoints/API section")
    
    if "relationships" in content or "provider" in content or "consumer" in content:
        sections["relationships"] = True
    else:
        issues.append("Missing Service Relationships section")
    
    if "quick start" in content or "installation" in content:
        sections["quick_start"] = True
    else:
        issues.append("Missing Quick Start section")
    
    if "integration" in content or "how to use" in content:
        sections["integration"] = True
    else:
        issues.append("Missing Integration Guide section")
    
    return sections, issues


def check_diagrams(service_path: Path) -> Tuple[int, List[str]]:
    """Check for visual diagrams"""
    issues = []
    diagram_count = 0
    
    readme_path = service_path / "README.md"
    if not readme_path.exists():
        return 0, ["README.md not found"]
    
    content = readme_path.read_text()
    
    # Check for ASCII diagrams
    ascii_diagrams = len(re.findall(r'```\s*\n[│├└─┌┐┘┴┬┤┼]', content))
    
    # Check for Mermaid diagrams
    mermaid_diagrams = len(re.findall(r'```mermaid', content))
    
    # Check for image references
    image_diagrams = len(re.findall(r'!\[.*\]\(.*\)', content))
    
    diagram_count = ascii_diagrams + mermaid_diagrams + image_diagrams
    
    if diagram_count == 0:
        issues.append("No visual diagrams found (ASCII art, Mermaid, or images)")
    elif diagram_count < 2:
        issues.append("Only 1 diagram found (need at least 2: ecosystem + data flow)")
    
    return diagram_count, issues


def check_library_documentation(service_path: Path) -> Tuple[int, List[str]]:
    """Check if major libraries are documented"""
    issues = []
    
    readme_path = service_path / "README.md"
    if not readme_path.exists():
        return 0, ["README.md not found"]
    
    content = readme_path.read_text()
    
    # Check for library documentation table
    has_library_table = "| Library |" in content or "| library |" in content
    
    if not has_library_table:
        issues.append("No library documentation table found")
        return 0, issues
    
    # Count documented libraries
    library_rows = len(re.findall(r'\|[^\|]+\|[^\|]+\|[^\|]+\|', content))
    
    if library_rows < 3:
        issues.append("Fewer than 3 libraries documented")
    
    return library_rows, issues


def check_endpoint_documentation(service_path: Path) -> Tuple[int, List[str]]:
    """Check if endpoints are documented"""
    issues = []
    
    readme_path = service_path / "README.md"
    if not readme_path.exists():
        return 0, ["README.md not found"]
    
    content = readme_path.read_text()
    
    # Check for standard endpoints
    standard_endpoints = ["/health", "/about-me", "/endpoints", "/provider-consumer"]
    missing_standard = []
    
    for endpoint in standard_endpoints:
        if endpoint not in content:
            missing_standard.append(endpoint)
    
    if missing_standard:
        issues.append(f"Missing standard endpoints in docs: {', '.join(missing_standard)}")
    
    # Count documented endpoints
    endpoint_count = len(re.findall(r'/api/v\d+/\w+', content))
    
    if endpoint_count == 0:
        issues.append("No API endpoints documented")
    
    return endpoint_count, issues


def check_relationship_documentation(service_path: Path) -> Tuple[bool, List[str]]:
    """Check if service relationships are documented"""
    issues = []
    
    readme_path = service_path / "README.md"
    if not readme_path.exists():
        return False, ["README.md not found"]
    
    content = readme_path.read_text().lower()
    
    # Check for provider/consumer documentation
    has_providers = "provider" in content
    has_consumers = "consumer" in content
    has_relationships = "relationship" in content
    
    if not (has_providers or has_consumers or has_relationships):
        issues.append("No service relationship documentation found")
        return False, issues
    
    # Check for JSON format
    has_json = "```json" in content.lower()
    
    if not has_json:
        issues.append("No JSON relationship data found")
    
    return True, issues


async def check_standard_endpoints_live(service_name: str, port: int) -> Tuple[Dict[str, bool], List[str]]:
    """Check if standard endpoints are implemented (live service check)"""
    issues = []
    endpoints = {
        "/health": False,
        "/about-me": False,
        "/endpoints": False,
        "/provider-consumer": False
    }
    
    base_url = f"http://localhost:{port}"
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for endpoint in endpoints.keys():
            try:
                response = await client.get(f"{base_url}{endpoint}")
                if response.status_code == 200:
                    endpoints[endpoint] = True
                else:
                    issues.append(f"{endpoint} returned {response.status_code}")
            except Exception as e:
                issues.append(f"{endpoint} not accessible: {str(e)}")
    
    return endpoints, issues


async def check_openapi_spec(service_name: str, port: int) -> Tuple[bool, List[str]]:
    """Check if OpenAPI spec is available"""
    issues = []
    
    base_url = f"http://localhost:{port}"
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Check /docs (Swagger UI)
        try:
            response = await client.get(f"{base_url}/docs")
            if response.status_code != 200:
                issues.append(f"/docs returned {response.status_code}")
        except Exception as e:
            issues.append(f"/docs not accessible: {str(e)}")
        
        # Check /openapi.json
        try:
            response = await client.get(f"{base_url}/openapi.json")
            if response.status_code != 200:
                issues.append(f"/openapi.json returned {response.status_code}")
                return False, issues
            
            # Validate OpenAPI spec
            spec = response.json()
            
            if "openapi" not in spec:
                issues.append("OpenAPI spec missing 'openapi' version field")
            
            if "info" not in spec:
                issues.append("OpenAPI spec missing 'info' section")
            
            if "paths" not in spec or len(spec["paths"]) == 0:
                issues.append("OpenAPI spec has no paths defined")
            
            return True, issues
            
        except Exception as e:
            issues.append(f"/openapi.json error: {str(e)}")
            return False, issues


def get_service_port(service_path: Path) -> int:
    """Get service port from configuration"""
    # Try docker-compose file
    repo_root = service_path.parent.parent
    docker_compose = repo_root / "docker-compose.dev.yml"
    
    if docker_compose.exists():
        import yaml
        with open(docker_compose) as f:
            compose = yaml.safe_load(f)
            service_name = service_path.name
            if "services" in compose and service_name in compose["services"]:
                ports = compose["services"][service_name].get("ports", [])
                if ports:
                    port_mapping = ports[0]
                    if isinstance(port_mapping, str):
                        port = int(port_mapping.split(":")[0])
                        return port
    
    # Default port
    return 5000


def calculate_score(results: Dict) -> int:
    """Calculate documentation compliance score (0-100)"""
    checks = []
    
    # README exists (10 points)
    checks.append((results["readme_exists"], 10))
    
    # README sections (30 points total, ~4.3 per section)
    sections = results["readme_sections"]["sections"]
    for section_present in sections.values():
        checks.append((section_present, 4.3))
    
    # Diagrams (15 points)
    diagram_count = results["diagrams"]["count"]
    checks.append((diagram_count >= 2, 15))
    
    # Library documentation (10 points)
    checks.append((results["library_documentation"]["count"] >= 3, 10))
    
    # Endpoint documentation (10 points)
    checks.append((results["endpoint_documentation"]["count"] > 0, 10))
    
    # Relationship documentation (10 points)
    checks.append((results["relationship_documentation"]["documented"], 10))
    
    # Live endpoint checks (15 points total, 3.75 per endpoint)
    if results.get("live_endpoints"):
        for endpoint_working in results["live_endpoints"]["endpoints"].values():
            checks.append((endpoint_working, 3.75))
    
    # OpenAPI spec (10 points)
    if results.get("openapi_spec"):
        checks.append((results["openapi_spec"]["available"], 10))
    
    score = sum(points for passed, points in checks if passed)
    return int(min(score, 100))


def generate_report(service_name: str, results: Dict) -> Dict:
    """Generate validation report"""
    score = calculate_score(results)
    
    status = "PASS" if score >= 80 else "FAIL"
    
    # Collect all issues
    all_issues = []
    for check, data in results.items():
        if isinstance(data, dict) and "issues" in data:
            all_issues.extend(data["issues"])
    
    recommendations = []
    
    if not results["readme_exists"]:
        recommendations.append("Generate README using: python scripts/refactoring/generate_service_readme.py")
    
    if results["diagrams"]["count"] < 2:
        recommendations.append("Add visual diagrams (ecosystem architecture, data flow, workflows)")
    
    if results["library_documentation"]["count"] < 3:
        recommendations.append("Document major libraries used in the service")
    
    if not results["relationship_documentation"]["documented"]:
        recommendations.append("Document service relationships (providers/consumers)")
    
    if results.get("live_endpoints"):
        missing_endpoints = [
            ep for ep, working in results["live_endpoints"]["endpoints"].items() 
            if not working
        ]
        if missing_endpoints:
            recommendations.append(f"Implement missing standard endpoints: {', '.join(missing_endpoints)}")
    
    if results.get("openapi_spec") and not results["openapi_spec"]["available"]:
        recommendations.append("Add OpenAPI/Swagger documentation")
    
    return {
        "service": service_name,
        "score": score,
        "status": status,
        "checks": results,
        "all_issues": all_issues,
        "recommendations": recommendations
    }


def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python validate_service_documentation.py <service-name>")
        print("Example: python validate_service_documentation.py doc-store")
        sys.exit(1)
    
    service_name = sys.argv[1]
    
    # Determine service path
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    service_path = repo_root / "services" / service_name
    
    if not service_path.exists():
        print(f"✗ Service not found: {service_path}")
        sys.exit(1)
    
    print(f"\n🔍 Validating documentation for '{service_name}'")
    print(f"   Path: {service_path}\n")
    
    # Run checks
    results = {}
    
    print("Running documentation checks...")
    
    # Check 1: README exists
    readme_exists, issues = check_readme_exists(service_path)
    results["readme_exists"] = readme_exists
    results["readme_issues"] = issues
    print(f"  {'✓' if readme_exists else '✗'} README.md exists")
    
    # Check 2: README sections
    sections, issues = check_readme_sections(service_path)
    results["readme_sections"] = {"sections": sections, "issues": issues}
    sections_count = sum(sections.values())
    print(f"  {'✓' if sections_count >= 6 else '✗'} README sections ({sections_count}/7)")
    
    # Check 3: Diagrams
    diagram_count, issues = check_diagrams(service_path)
    results["diagrams"] = {"count": diagram_count, "issues": issues}
    print(f"  {'✓' if diagram_count >= 2 else '✗'} Visual diagrams ({diagram_count} found)")
    
    # Check 4: Library documentation
    lib_count, issues = check_library_documentation(service_path)
    results["library_documentation"] = {"count": lib_count, "issues": issues}
    print(f"  {'✓' if lib_count >= 3 else '✗'} Library documentation ({lib_count} libraries)")
    
    # Check 5: Endpoint documentation
    endpoint_count, issues = check_endpoint_documentation(service_path)
    results["endpoint_documentation"] = {"count": endpoint_count, "issues": issues}
    print(f"  {'✓' if endpoint_count > 0 else '✗'} Endpoint documentation ({endpoint_count} endpoints)")
    
    # Check 6: Relationship documentation
    documented, issues = check_relationship_documentation(service_path)
    results["relationship_documentation"] = {"documented": documented, "issues": issues}
    print(f"  {'✓' if documented else '✗'} Service relationships documented")
    
    # Live checks (optional)
    port = get_service_port(service_path)
    print(f"\nRunning live API checks (port {port})...")
    
    import asyncio
    
    # Check 7: Standard endpoints (live)
    try:
        endpoints, issues = asyncio.run(check_standard_endpoints_live(service_name, port))
        results["live_endpoints"] = {"endpoints": endpoints, "issues": issues}
        working_count = sum(endpoints.values())
        print(f"  {'✓' if working_count == 4 else '✗'} Standard endpoints ({working_count}/4 working)")
    except Exception as e:
        print(f"  ⚠ Could not check live endpoints: {e}")
        results["live_endpoints"] = None
    
    # Check 8: OpenAPI spec (live)
    try:
        available, issues = asyncio.run(check_openapi_spec(service_name, port))
        results["openapi_spec"] = {"available": available, "issues": issues}
        print(f"  {'✓' if available else '✗'} OpenAPI/Swagger available")
    except Exception as e:
        print(f"  ⚠ Could not check OpenAPI spec: {e}")
        results["openapi_spec"] = None
    
    # Generate report
    report = generate_report(service_name, results)
    
    # Save report
    report_path = repo_root / "reports" / f"{service_name}_documentation_validation.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"\n📊 Documentation Validation Results")
    print(f"   Score: {report['score']}/100")
    print(f"   Status: {report['status']}")
    print(f"   Report: {report_path}")
    
    if report['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"   - {rec}")
    
    print(f"\n📚 Reference:")
    print(f"   - Service Documentation Strategy: docs/refactoring/SERVICE_DOCUMENTATION_STRATEGY.md")
    print(f"   - API Standardization Strategy: docs/refactoring/API_STANDARDIZATION_STRATEGY.md")
    
    # Exit with error if failed
    if report['status'] == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()

