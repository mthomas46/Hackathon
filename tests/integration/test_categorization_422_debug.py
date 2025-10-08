#!/usr/bin/env python3
"""
TDD: Debug "Categorization failed: 422" errors during crawl.
"""

import requests
import json


class TestCategorizationService:
    """Debug 422 errors from categorization service."""
    
    def test_1_categorization_service_health(self):
        """TEST 1: Is categorization service running and healthy?"""
        print("\n" + "=" * 70)
        print("🧪 TEST 1: Categorization Service Health")
        print("=" * 70)
        
        # Typical categorization service ports
        ports_to_check = [5009, 5020, 8000, 8001]
        
        for port in ports_to_check:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    print(f"✅ Categorization service found on port {port}")
                    print(f"   Response: {response.json()}")
                    return port
            except Exception as e:
                print(f"❌ Port {port}: {type(e).__name__}")
        
        print(f"\n⚠️  Categorization service not accessible on common ports")
        return None
    
    def test_2_what_causes_422(self):
        """TEST 2: What request body causes 422?"""
        print("\n" + "=" * 70)
        print("🧪 TEST 2: Identify 422 Cause")
        print("=" * 70)
        
        # Find categorization service
        port = self.test_1_categorization_service_health()
        
        if not port:
            print("⚠️  Cannot test - service not accessible")
            return
        
        # Test various request bodies
        test_cases = [
            ("empty", {}),
            ("null_text", {"text": None}),
            ("empty_text", {"text": ""}),
            ("valid_text", {"text": "This is a test document about the Horus Heresy"}),
            ("no_text_key", {"content": "test"}),
            ("missing_required", {"title": "test"}),
        ]
        
        base_url = f"http://localhost:{port}"
        
        for name, payload in test_cases:
            try:
                response = requests.post(
                    f"{base_url}/api/v1/categorize",
                    json=payload,
                    timeout=5
                )
                
                if response.status_code == 422:
                    print(f"❌ {name}: HTTP 422")
                    try:
                        error = response.json()
                        print(f"   Error: {json.dumps(error, indent=2)[:200]}")
                    except:
                        print(f"   Raw: {response.text[:200]}")
                elif response.status_code == 200:
                    print(f"✅ {name}: HTTP 200")
                else:
                    print(f"⚠️  {name}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {name}: {type(e).__name__} - {e}")
    
    def test_3_check_demo_crawler_payload(self):
        """TEST 3: What payload is the crawler sending?"""
        print("\n" + "=" * 70)
        print("🧪 TEST 3: Demo Crawler Payload Analysis")
        print("=" * 70)
        
        # Check the crawler code to see what it's sending
        try:
            with open("horus_heresy_demo/demo_horus_heresy.py", 'r') as f:
                content = f.read()
            
            # Look for categorization calls
            import re
            
            # Search for categorization-related code
            matches = re.findall(
                r'(categoriz[^(]*\([^)]*\))',
                content,
                re.IGNORECASE
            )
            
            if matches:
                print(f"Found {len(matches)} categorization calls:")
                for i, match in enumerate(matches[:5], 1):
                    print(f"  {i}. {match[:80]}...")
            else:
                print("⚠️  No categorization calls found in demo script")
                
            # Check if there's error handling
            if "Categorization failed" in content:
                print(f"\n✅ Found 'Categorization failed' error message in code")
                # Find the context
                idx = content.find("Categorization failed")
                context = content[max(0, idx-200):min(len(content), idx+200)]
                print(f"\nContext:")
                print(f"  ...{context}...")
            else:
                print(f"\n⚠️  'Categorization failed' message not found in code")
                
        except Exception as e:
            print(f"❌ Error analyzing crawler: {e}")
    
    def test_4_is_categorization_required(self):
        """TEST 4: Is categorization actually required for the demo?"""
        print("\n" + "=" * 70)
        print("🧪 TEST 4: Categorization Requirement Analysis")
        print("=" * 70)
        
        print("Checking if categorization is critical or optional...")
        
        # Check previous successful runs
        import os
        
        prev_reports = [
            "horus_heresy_demo/reports/crawl_report.json",
            "reports/crawl_report.json"
        ]
        
        for report_path in prev_reports:
            if os.path.exists(report_path):
                try:
                    with open(report_path, 'r') as f:
                        data = json.load(f)
                    
                    stats = data.get("statistics", {})
                    print(f"✅ Found previous run: {report_path}")
                    print(f"   Pages crawled: {stats.get('total_pages', 0)}")
                    print(f"   Tags: {stats.get('total_tags', 0)}")
                    
                    # Check if categories exist
                    if "categories" in str(data):
                        print(f"   ✅ Previous run had categories")
                    else:
                        print(f"   ⚠️  Previous run worked without categories")
                    
                except Exception as e:
                    print(f"   Error reading: {e}")
        
        print(f"\n💡 Assessment:")
        print(f"   If previous runs succeeded, categorization may be optional")
        print(f"   422 errors suggest service is running but rejecting payloads")
    
    def run_all_tests(self):
        """Run all diagnostic tests."""
        print("\n" + "╔" + "=" * 68 + "╗")
        print("║" + " " * 68 + "║")
        print("║" + "  TDD: CATEGORIZATION 422 ERROR DIAGNOSIS".center(68) + "║")
        print("║" + " " * 68 + "║")
        print("╚" + "=" * 68 + "╝")
        
        self.test_1_categorization_service_health()
        self.test_2_what_causes_422()
        self.test_3_check_demo_crawler_payload()
        self.test_4_is_categorization_required()
        
        print("\n" + "=" * 70)
        print("🔍 DIAGNOSIS COMPLETE")
        print("=" * 70)
        print("\n💡 Next Steps:")
        print("   1. Check if categorization service needs fixing")
        print("   2. Check if demo crawler payload is correct")
        print("   3. Consider if categorization is optional for demo")
        print("=" * 70)


if __name__ == "__main__":
    tester = TestCategorizationService()
    tester.run_all_tests()

