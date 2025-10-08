#!/usr/bin/env python3
"""
Systematic tags testing script.

Tests tags flow through all architectural layers to identify
exactly where tags are being lost.
"""

import asyncio
import httpx
import json
from datetime import datetime


class TagsSystematicTester:
    """Comprehensive tags testing across all layers."""
    
    def __init__(self, base_url: str = "http://localhost:5087"):
        self.base_url = base_url
        self.test_results = []
        
    async def test_layer(self, layer_name: str, endpoint: str, test_tags: list) -> dict:
        """Test a specific architectural layer."""
        doc_id = f"test-{layer_name}-{datetime.now().strftime('%H%M%S')}"
        
        print(f"\n{'='*70}")
        print(f"Testing: {layer_name}")
        print(f"{'='*70}")
        print(f"Tags sent: {test_tags}")
        
        result = {
            "layer": layer_name,
            "doc_id": doc_id,
            "tags_sent": test_tags,
            "success": False,
            "tags_stored": None,
            "error": None
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create document
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    json={
                        "id": doc_id,
                        "content": f"Test content for {layer_name}",
                        "tags": test_tags,
                        "metadata": {}
                    }
                )
                
                if response.status_code != 200:
                    result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
                    print(f"❌ Request failed: {result['error']}")
                    return result
                
                response_data = response.json()
                print(f"✅ Request successful")
                print(f"Response: {json.dumps(response_data, indent=2)[:300]}...")
                
                # Check what was stored
                if "tags_stored" in response_data:
                    result["tags_stored"] = response_data["tags_stored"]
                else:
                    # Query the debug endpoint to check
                    debug_response = await client.get(
                        f"{self.base_url}/api/v1/debug/documents/{doc_id}/tags-debug"
                    )
                    if debug_response.status_code == 200:
                        debug_data = debug_response.json()
                        result["tags_stored"] = debug_data.get("tags_raw")
                
                result["success"] = True
                result["response_data"] = response_data
                
                # Check if tags were actually stored
                tags_stored_parsed = json.loads(result["tags_stored"]) if result["tags_stored"] else []
                if tags_stored_parsed and len(tags_stored_parsed) > 0:
                    print(f"🎉 SUCCESS! Tags stored: {tags_stored_parsed}")
                else:
                    print(f"⚠️  Tags empty in database: {result['tags_stored']}")
                
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ Exception: {e}")
        
        self.test_results.append(result)
        return result
    
    async def run_all_tests(self):
        """Run comprehensive test suite across all layers."""
        test_tags = ["test:systematic", "layer:validation", "priority:high"]
        
        print("\n" + "="*70)
        print("SYSTEMATIC TAGS TESTING - All Architectural Layers")
        print("="*70)
        print(f"Base URL: {self.base_url}")
        print(f"Test Tags: {test_tags}")
        print("="*70)
        
        # Test 1: Direct SQL (bypasses everything)
        await self.test_layer(
            "1_Direct_SQL",
            "/api/v1/debug/documents/direct-sql",
            test_tags
        )
        
        # Test 2: Via queries.py
        await self.test_layer(
            "2_Via_Queries",
            "/api/v1/debug/documents/via-queries",
            test_tags
        )
        
        # Test 3: Via Repository
        await self.test_layer(
            "3_Via_Repository",
            "/api/v1/debug/documents/via-repository",
            test_tags
        )
        
        # Test 4: Via Service
        await self.test_layer(
            "4_Via_Service",
            "/api/v1/debug/documents/via-service",
            test_tags
        )
        
        # Test 5: Complete Flow Test
        await self.test_complete_flow(test_tags)
        
        # Generate summary report
        self.generate_report()
    
    async def test_complete_flow(self, test_tags: list):
        """Test the complete flow through all layers."""
        print(f"\n{'='*70}")
        print("Testing: Complete Flow (All Layers)")
        print(f"{'='*70}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/debug/test-flow",
                    json={
                        "id": f"flow-test-{datetime.now().strftime('%H%M%S')}",
                        "content": "Complete flow test",
                        "tags": test_tags,
                        "metadata": {}
                    }
                )
                
                if response.status_code == 200:
                    flow_data = response.json()
                    print("✅ Complete flow test successful")
                    print(json.dumps(flow_data, indent=2))
                    
                    self.test_results.append({
                        "layer": "5_Complete_Flow",
                        "success": True,
                        "flow_data": flow_data
                    })
                else:
                    print(f"❌ Complete flow test failed: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Complete flow test exception: {e}")
    
    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "="*70)
        print("TEST RESULTS SUMMARY")
        print("="*70)
        
        total_tests = len([r for r in self.test_results if r.get("layer") != "5_Complete_Flow"])
        successful_tests = sum(1 for r in self.test_results if r.get("success") and r.get("layer") != "5_Complete_Flow")
        tests_with_tags = sum(
            1 for r in self.test_results 
            if r.get("success") and r.get("tags_stored") not in [None, "[]", []] and r.get("layer") != "5_Complete_Flow"
        )
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"Successful: {successful_tests}/{total_tests}")
        print(f"Tags Stored: {tests_with_tags}/{total_tests}")
        
        print("\n" + "-"*70)
        print("LAYER-BY-LAYER RESULTS:")
        print("-"*70)
        
        for result in self.test_results:
            if result.get("layer") == "5_Complete_Flow":
                continue
                
            layer = result.get("layer", "Unknown")
            success = "✅" if result.get("success") else "❌"
            
            tags_stored = result.get("tags_stored")
            if tags_stored:
                try:
                    tags_parsed = json.loads(tags_stored) if isinstance(tags_stored, str) else tags_stored
                    has_tags = "🎉 TAGS OK" if tags_parsed and len(tags_parsed) > 0 else "⚠️  EMPTY"
                except:
                    has_tags = "⚠️  PARSE ERROR"
            else:
                has_tags = "❌ NULL"
            
            print(f"{success} {layer:30} | {has_tags:15} | {tags_stored}")
        
        print("\n" + "="*70)
        print("DIAGNOSIS:")
        print("="*70)
        
        if tests_with_tags == 0:
            print("❌ CRITICAL: Tags not stored in ANY layer!")
            print("   → Database schema issue OR serialization bug")
        elif tests_with_tags < total_tests:
            print(f"⚠️  PARTIAL: Tags work in {tests_with_tags} layers, fail in {total_tests - tests_with_tags}")
            print("   → Architectural issue in specific layers")
            
            # Identify which layer breaks
            for i, result in enumerate(self.test_results):
                if result.get("layer") == "5_Complete_Flow":
                    continue
                if result.get("success"):
                    tags_stored = result.get("tags_stored")
                    if tags_stored and tags_stored not in ["[]", None]:
                        print(f"   ✅ {result['layer']} works!")
                    else:
                        print(f"   ❌ {result['layer']} BREAKS tags!")
        else:
            print("🎉 SUCCESS: Tags work in ALL layers!")
            print("   → Issue is in the HANDLER layer (not tested here)")
        
        print("="*70)


async def main():
    """Run systematic tags testing."""
    tester = TagsSystematicTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    print("\n🔬 Systematic Tags Testing Framework")
    print("="*70)
    asyncio.run(main())

