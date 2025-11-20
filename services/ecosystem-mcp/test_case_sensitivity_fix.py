"""
Test case sensitivity fix for service_name
"""
import asyncio
import json
from src.services.documentation.adaptive_orchestrator import get_adaptive_orchestrator

async def test_service_name_case_insensitive():
    """Test that service_name matching is case-insensitive"""
    print("\n🧪 Testing Case-Insensitive Service Name Matching\n")
    print("="*70)
    
    orchestrator = get_adaptive_orchestrator()
    
    # Test 1: Try with lowercase 'adminservice'
    print("\n📝 Test 1: Querying with lowercase 'adminservice'...")
    try:
        result = await orchestrator.generate_adaptive_documentation(
            service_name="adminservice",  # lowercase
            template_name="api_reference_openapi_style",
            category="api_reference",
            config={
                "include_citations": True,
                "transparency_mode": "verbose"
            }
        )
        
        print("✅ SUCCESS!")
        print(f"   Run ID: {result['run_id']}")
        print(f"   Service Name: {result['service_name']}")
        print(f"   Content Length: {len(result['content'])} chars")
        print(f"   Sections: {result['metadata']['sections_generated']}")
        print(f"   Citations: {result['metadata']['citations_added']}")
        print(f"   Frameworks: {result['metadata']['frameworks_detected']}")
        
        # Check for "ecosystem-mcp" in content
        if "ecosystem-mcp" in result['content'].lower():
            print("⚠️  WARNING: 'ecosystem-mcp' found in content!")
            # Find and show context
            content = result['content']
            idx = content.lower().find("ecosystem-mcp")
            if idx >= 0:
                context = content[max(0, idx-100):min(len(content), idx+100)]
                print(f"   Context: ...{context}...")
        else:
            print("✅ No 'ecosystem-mcp' references found in content")
        
        # Check if adminService is mentioned
        if "adminService" in result['content'] or "adminservice" in result['content'].lower():
            print("✅ Content correctly references adminService")
        
        return result
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_service_name_case_insensitive())
    
    if result:
        print("\n" + "="*70)
        print("🎉 TEST PASSED: Case-insensitive matching works!")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ TEST FAILED")
        print("="*70)
