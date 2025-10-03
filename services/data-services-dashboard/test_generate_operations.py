#!/usr/bin/env python3
"""
Test Script: Generate Sample Datastore Operations

This script generates sample datastore operations to populate the dashboard
with realistic data for testing and demonstration purposes.

Usage:
    python3 services/data-services-dashboard/test_generate_operations.py
    python3 services/data-services-dashboard/test_generate_operations.py --count 50
"""

import httpx
import random
import time
import argparse
from datetime import datetime

# Service configurations
SERVICES = {
    "doc_store": {
        "port": 5087,
        "endpoints": [
            ("POST", "/api/v1/documents", {"id": "test_{}", "content": "Test document", "metadata": {}}),
            ("GET", "/api/v1/documents/test_123", None),
            ("GET", "/api/v1/search", None),
            ("GET", "/health", None),
        ]
    },
    "prompt_store": {
        "port": 5110,
        "endpoints": [
            ("GET", "/health", None),
            ("GET", "/api/v1/prompts", None),
        ]
    },
    "external-service-store": {
        "port": 5140,
        "endpoints": [
            ("GET", "/health", None),
            ("GET", "/api/v1/services", None),
        ]
    },
    "memory-agent": {
        "port": 5090,
        "endpoints": [
            ("GET", "/health", None),
            ("GET", "/api/v1/memories", None),
        ]
    }
}

WORKFLOW_IDS = [
    "workflow_alpha_001",
    "workflow_beta_002",
    "workflow_gamma_003",
    "workflow_delta_004",
    "workflow_epsilon_005"
]

def make_request(service_name: str, port: int, method: str, endpoint: str, 
                 json_data: dict = None, workflow_id: str = None):
    """Make a request to a datastore service."""
    url = f"http://localhost:{port}{endpoint}"
    
    headers = {}
    if workflow_id:
        headers["X-Workflow-ID"] = workflow_id
    
    try:
        if method == "POST":
            response = httpx.post(url, json=json_data, headers=headers, timeout=5.0)
        elif method == "GET":
            response = httpx.get(url, headers=headers, timeout=5.0)
        elif method == "PUT":
            response = httpx.put(url, json=json_data, headers=headers, timeout=5.0)
        else:
            return None
        
        return {
            "service": service_name,
            "method": method,
            "endpoint": endpoint,
            "status": response.status_code,
            "success": response.status_code < 400
        }
    except httpx.RequestError as e:
        return {
            "service": service_name,
            "method": method,
            "endpoint": endpoint,
            "status": "error",
            "success": False,
            "error": str(e)
        }

def generate_operations(count: int = 20, delay: float = 0.5):
    """Generate sample operations."""
    print(f"╔══════════════════════════════════════════════════════════════════╗")
    print(f"║                                                                  ║")
    print(f"║     Generating {count} Sample Datastore Operations                 ║")
    print(f"║                                                                  ║")
    print(f"╚══════════════════════════════════════════════════════════════════╝")
    print()
    
    results = {
        "total": 0,
        "successful": 0,
        "failed": 0,
        "by_service": {}
    }
    
    for i in range(count):
        # Randomly select a service
        service_name = random.choice(list(SERVICES.keys()))
        service_config = SERVICES[service_name]
        
        # Randomly select an endpoint
        method, endpoint, json_template = random.choice(service_config["endpoints"])
        
        # Prepare JSON data if needed
        json_data = None
        if json_template:
            json_data = json_template.copy()
            if "id" in json_data:
                json_data["id"] = json_data["id"].format(i)
        
        # Random workflow ID
        workflow_id = random.choice(WORKFLOW_IDS) if random.random() > 0.3 else None
        
        # Make request
        result = make_request(
            service_name,
            service_config["port"],
            method,
            endpoint,
            json_data,
            workflow_id
        )
        
        # Track results
        results["total"] += 1
        if result["success"]:
            results["successful"] += 1
            status_icon = "✅"
        else:
            results["failed"] += 1
            status_icon = "❌"
        
        if service_name not in results["by_service"]:
            results["by_service"][service_name] = {"success": 0, "failed": 0}
        
        if result["success"]:
            results["by_service"][service_name]["success"] += 1
        else:
            results["by_service"][service_name]["failed"] += 1
        
        # Display progress
        print(f"[{i+1}/{count}] {status_icon} {service_name:25} {method:6} {endpoint:40} → {result['status']}")
        
        # Delay between requests
        if delay > 0 and i < count - 1:
            time.sleep(delay)
    
    # Display summary
    print()
    print(f"╔══════════════════════════════════════════════════════════════════╗")
    print(f"║                         Summary                                  ║")
    print(f"╚══════════════════════════════════════════════════════════════════╝")
    print()
    print(f"Total Operations:       {results['total']}")
    print(f"Successful:             {results['successful']} ({results['successful']/results['total']*100:.1f}%)")
    print(f"Failed:                 {results['failed']} ({results['failed']/results['total']*100:.1f}%)")
    print()
    print("Operations by Service:")
    for service, counts in results["by_service"].items():
        total = counts["success"] + counts["failed"]
        print(f"  {service:25} {total:3} ops ({counts['success']} success, {counts['failed']} failed)")
    print()
    print("✅ Operations logged to log-collector")
    print("📊 View in dashboard: http://localhost:8501")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate sample datastore operations")
    parser.add_argument("--count", type=int, default=20, help="Number of operations to generate")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between operations (seconds)")
    parser.add_argument("--workflow", type=str, help="Use specific workflow ID for all operations")
    
    args = parser.parse_args()
    
    # Override workflow IDs if specified
    if args.workflow:
        global WORKFLOW_IDS
        WORKFLOW_IDS = [args.workflow]
    
    generate_operations(count=args.count, delay=args.delay)

if __name__ == "__main__":
    main()

