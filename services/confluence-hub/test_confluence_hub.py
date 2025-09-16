#!/usr/bin/env python3
"""
Test script for Confluence Hub Service.

This script provides basic testing functionality for the Confluence Hub service.
Run this after starting the service to validate that it's working correctly.
"""

import asyncio
import json
import sys
from typing import Dict, Any

try:
    import httpx
except ImportError:
    print("httpx is required for testing. Install with: pip install httpx")
    sys.exit(1)

BASE_URL = "http://localhost:5070"


class ConfluenceHubTester:
    """Test client for Confluence Hub service."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def test_health(self) -> bool:
        """Test the health endpoint."""
        print("🔍 Testing health endpoint...")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check passed: {health_data.get('status', 'unknown')}")
                
                # Print dependency health
                if 'dependencies' in health_data:
                    for dep in health_data['dependencies']:
                        status = dep.get('status', 'unknown')
                        name = dep.get('name', 'unknown')
                        emoji = "✅" if status == "healthy" else "❌"
                        print(f"   {emoji} {name}: {status}")
                        if dep.get('error'):
                            print(f"      Error: {dep['error']}")
                
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return False
    
    async def test_convert_page_by_id(self, page_id: str, session_id: str = "test-session") -> bool:
        """Test converting a page by ID."""
        print(f"🔍 Testing page conversion by ID: {page_id}")
        try:
            payload = {
                "page_id": page_id,
                "session_id": session_id,
                "max_depth": 2,
                "include_content": True
            }
            
            response = await self.client.post(
                f"{self.base_url}/convert-page",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', {})
                pages_processed = data.get('pages_processed', 0)
                total_found = data.get('total_pages_found', 0)
                print(f"✅ Page conversion successful: {pages_processed}/{total_found} pages processed")
                return True
            else:
                print(f"❌ Page conversion failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Page conversion error: {str(e)}")
            return False
    
    async def test_convert_page_by_title(self, title: str, space_key: str, session_id: str = "test-session") -> bool:
        """Test converting a page by title."""
        print(f"🔍 Testing page conversion by title: '{title}' in space '{space_key}'")
        try:
            payload = {
                "page_title": title,
                "space_key": space_key,
                "session_id": session_id,
                "max_depth": 1,
                "include_content": True
            }
            
            response = await self.client.post(
                f"{self.base_url}/convert-page",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', {})
                pages_processed = data.get('pages_processed', 0)
                total_found = data.get('total_pages_found', 0)
                print(f"✅ Page conversion successful: {pages_processed}/{total_found} pages processed")
                return True
            else:
                print(f"❌ Page conversion failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Page conversion error: {str(e)}")
            return False
    
    async def test_get_pages(self, session_id: str = None) -> bool:
        """Test getting stored pages."""
        print("🔍 Testing page retrieval...")
        try:
            params = {}
            if session_id:
                params['session_id'] = session_id
                print(f"   Filtering by session: {session_id}")
            
            response = await self.client.get(
                f"{self.base_url}/pages",
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                pages = result.get('pages', [])
                total = result.get('total', 0)
                print(f"✅ Retrieved {len(pages)} pages (total: {total})")
                
                # Show sample page info
                if pages:
                    page = pages[0]
                    print(f"   Sample page: {page.get('title', 'Unknown')} (ID: {page.get('confluence_page_id', 'Unknown')})")
                
                return True
            else:
                print(f"❌ Page retrieval failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Page retrieval error: {str(e)}")
            return False


async def main():
    """Run all tests."""
    print("🚀 Starting Confluence Hub Service Tests")
    print("=" * 50)
    
    # Check if we have command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Usage: python test_confluence_hub.py [page_id] [space_key page_title]")
            print("")
            print("Examples:")
            print("  python test_confluence_hub.py                    # Health check and basic tests")
            print("  python test_confluence_hub.py 123456789          # Test with specific page ID")
            print("  python test_confluence_hub.py SPACE 'Page Title' # Test with page title and space")
            return
    
    tester = ConfluenceHubTester()
    success_count = 0
    total_tests = 0
    
    try:
        # Test 1: Health check
        total_tests += 1
        if await tester.test_health():
            success_count += 1
        
        print()
        
        # Test 2: Get existing pages
        total_tests += 1
        if await tester.test_get_pages():
            success_count += 1
        
        print()
        
        # Test 3: Convert page (if arguments provided)
        if len(sys.argv) >= 2:
            if len(sys.argv) == 2:
                # Page ID provided
                page_id = sys.argv[1]
                total_tests += 1
                if await tester.test_convert_page_by_id(page_id):
                    success_count += 1
            elif len(sys.argv) >= 3:
                # Space key and page title provided
                space_key = sys.argv[1] 
                page_title = sys.argv[2]
                total_tests += 1
                if await tester.test_convert_page_by_title(page_title, space_key):
                    success_count += 1
        else:
            print("ℹ️  To test page conversion, provide:")
            print("   - Page ID: python test_confluence_hub.py 123456789")
            print("   - Or Page Title: python test_confluence_hub.py SPACE 'Page Title'")
        
        print()
        print("=" * 50)
        print(f"🎯 Test Results: {success_count}/{total_tests} tests passed")
        
        if success_count == total_tests:
            print("🎉 All tests passed! Service is working correctly.")
            return 0
        else:
            print("⚠️  Some tests failed. Check the service configuration and logs.")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        return 1
    finally:
        await tester.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)