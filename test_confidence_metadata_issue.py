#!/usr/bin/env python3
"""
Test script to isolate the ConfidenceMetadata issue.
"""

import httpx
import json

API_BASE = "http://localhost:8000"

def test_get_timeline():
    """Test getting the timeline that fails."""
    timeline_id = "d1739d94-638d-43fd-b076-dd48d4f11e07"
    
    print("=" * 80)
    print("Testing Timeline Retrieval")
    print("=" * 80)
    print(f"\nTimeline ID: {timeline_id}")
    
    try:
        response = httpx.get(
            f"{API_BASE}/api/v1/timelines/{timeline_id}",
            timeout=10.0
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS - Timeline retrieved")
            print(f"Name: {data.get('name')}")
            print(f"Confidence Level: {data.get('confidence_level')}")
            print(f"Confidence Metadata: {json.dumps(data.get('confidence_metadata'), indent=2)}")
        else:
            print(f"\n❌ FAILED")
            print(f"Error: {response.text[:500]}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

def check_database_directly():
    """Check what's in the database."""
    import subprocess
    
    print("\n" + "=" * 80)
    print("Database Check")
    print("=" * 80)
    
    cmd = [
        "docker", "exec", "ecosystem-mcp-postgres",
        "psql", "-U", "ecosystem", "-d", "ecosystem_mcp",
        "-c", "SELECT id, name, confidence_level, confidence_metadata FROM timelines WHERE id = 'd1739d94-638d-43fd-b076-dd48d4f11e07';"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)

if __name__ == "__main__":
    check_database_directly()
    test_get_timeline()
