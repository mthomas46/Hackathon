#!/usr/bin/env python3
"""
Check for port conflicts in the ecosystem.

Reads MASTER_CONFIGURATION_REGISTRY.md and validates:
1. No duplicate port assignments
2. Ports are within expected ranges
3. Optional: Check if ports are actually in use on system

Usage:
    python check_port_conflicts.py [service_name]
    
    Without service_name: Check entire registry
    With service_name: Check if service's ports conflict
"""

import re
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Path to registry
REGISTRY_PATH = Path(__file__).parent.parent.parent / "docs" / "refactoring" / "MASTER_CONFIGURATION_REGISTRY.md"

# Port ranges
PORT_RANGES = {
    "frontend": (3000, 3999),
    "backend": (5000, 5999),
    "analysis": (6000, 6999),
    "integration": (7000, 7999),
    "infrastructure": (8000, 8999),
    "mcp": (9000, 9999),
}


def parse_port_registry(registry_content: str) -> List[Dict]:
    """Parse port registry table from markdown."""
    ports = []
    in_table = False
    
    for line in registry_content.split('\n'):
        # Look for port registry section
        if '<!-- AI_SECTION: port_registry -->' in line:
            in_table = True
            continue
        if '<!-- /AI_SECTION -->' in line and in_table:
            break
        
        # Parse table rows
        if in_table and '|' in line and not line.strip().startswith('|--'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 7 and parts[1] and not parts[1].startswith('**') and parts[1] != 'Service Name':
                try:
                    service = parts[1]
                    http_port = parts[2] if parts[2] and parts[2] != '-' else None
                    internal_port = parts[3] if parts[3] and parts[3] != '-' else None
                    grpc_port = parts[4] if parts[4] and parts[4] != '-' else None
                    admin_port = parts[5] if parts[5] and parts[5] != '-' else None
                    status = parts[6]
                    
                    ports.append({
                        'service': service,
                        'http_port': int(http_port) if http_port else None,
                        'internal_port': int(internal_port) if internal_port else None,
                        'grpc_port': int(grpc_port) if grpc_port else None,
                        'admin_port': int(admin_port) if admin_port else None,
                        'status': status,
                    })
                except (ValueError, IndexError):
                    continue
    
    return ports


def check_duplicate_ports(ports: List[Dict]) -> List[Tuple[int, List[str]]]:
    """Check for duplicate port assignments."""
    port_map: Dict[int, List[str]] = {}
    
    for entry in ports:
        for port_type in ['http_port', 'internal_port', 'grpc_port', 'admin_port']:
            port = entry.get(port_type)
            if port:
                if port not in port_map:
                    port_map[port] = []
                port_map[port].append(f"{entry['service']} ({port_type.replace('_port', '')})")
    
    # Find conflicts
    conflicts = [(port, services) for port, services in port_map.items() if len(services) > 1]
    return conflicts


def check_port_ranges(ports: List[Dict]) -> List[Tuple[str, int, str]]:
    """Check if ports are in expected ranges."""
    issues = []
    
    for entry in ports:
        service = entry['service']
        http_port = entry.get('http_port')
        
        if not http_port:
            continue
        
        # Determine expected range based on service name/type
        expected_range = None
        for range_name, (min_port, max_port) in PORT_RANGES.items():
            if range_name in service.lower() or (min_port <= http_port <= max_port):
                expected_range = (range_name, min_port, max_port)
                break
        
        # Check if port is in any valid range
        in_valid_range = any(
            min_port <= http_port <= max_port 
            for min_port, max_port in PORT_RANGES.values()
        )
        
        if not in_valid_range:
            issues.append((service, http_port, "Port outside defined ranges"))
    
    return issues


def check_system_ports(ports: List[Dict], check_system: bool = False) -> List[Tuple[str, int]]:
    """Check if ports are actually in use on the system."""
    if not check_system:
        return []
    
    in_use = []
    
    for entry in ports:
        for port_type in ['http_port', 'internal_port', 'grpc_port', 'admin_port']:
            port = entry.get(port_type)
            if port:
                try:
                    # Use lsof to check if port is in use
                    result = subprocess.run(
                        ['lsof', '-i', f':{port}'],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        in_use.append((entry['service'], port))
                except Exception:
                    # lsof might not be available
                    pass
    
    return in_use


def check_service_port(service_name: str, port: int, ports: List[Dict]) -> bool:
    """Check if a specific service's port conflicts."""
    for entry in ports:
        if entry['service'] == service_name:
            continue
        
        for port_type in ['http_port', 'internal_port', 'grpc_port', 'admin_port']:
            if entry.get(port_type) == port:
                print(f"❌ Port {port} conflicts with {entry['service']} ({port_type.replace('_port', '')})")
                return False
    
    print(f"✅ Port {port} is available")
    return True


def main():
    """Main execution."""
    if not REGISTRY_PATH.exists():
        print(f"❌ Registry not found: {REGISTRY_PATH}")
        sys.exit(1)
    
    # Read registry
    registry_content = REGISTRY_PATH.read_text()
    ports = parse_port_registry(registry_content)
    
    print(f"📊 Loaded {len(ports)} services from registry\n")
    
    # If service name and port provided, check specific service
    if len(sys.argv) == 3:
        service_name = sys.argv[1]
        try:
            port = int(sys.argv[2])
            if check_service_port(service_name, port, ports):
                sys.exit(0)
            else:
                sys.exit(1)
        except ValueError:
            print(f"❌ Invalid port number: {sys.argv[2]}")
            sys.exit(1)
    
    # Otherwise check entire registry
    print("🔍 Checking for port conflicts...\n")
    
    # Check duplicates
    duplicates = check_duplicate_ports(ports)
    if duplicates:
        print("❌ DUPLICATE PORTS FOUND:")
        for port, services in duplicates:
            print(f"   Port {port}:")
            for service in services:
                print(f"      - {service}")
        print()
        has_errors = True
    else:
        print("✅ No duplicate ports\n")
        has_errors = False
    
    # Check ranges
    range_issues = check_port_ranges(ports)
    if range_issues:
        print("⚠️  PORTS OUTSIDE EXPECTED RANGES:")
        for service, port, issue in range_issues:
            print(f"   {service}: Port {port} - {issue}")
        print()
    else:
        print("✅ All ports in valid ranges\n")
    
    # Summary
    print("📋 PORT SUMMARY:")
    print(f"   Frontend (3000-3999): {sum(1 for p in ports if p.get('http_port') and 3000 <= p['http_port'] <= 3999)}")
    print(f"   Backend (5000-5999): {sum(1 for p in ports if p.get('http_port') and 5000 <= p['http_port'] <= 5999)}")
    print(f"   Analysis (6000-6999): {sum(1 for p in ports if p.get('http_port') and 6000 <= p['http_port'] <= 6999)}")
    print(f"   Integration (7000-7999): {sum(1 for p in ports if p.get('http_port') and 7000 <= p['http_port'] <= 7999)}")
    print(f"   Infrastructure (8000-8999): {sum(1 for p in ports if p.get('http_port') and 8000 <= p['http_port'] <= 8999)}")
    print(f"   MCP (9000-9999): {sum(1 for p in ports if p.get('http_port') and 9000 <= p['http_port'] <= 9999)}")
    print()
    
    if has_errors:
        print("❌ Port conflicts detected!")
        sys.exit(1)
    else:
        print("✅ All port checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()

