#!/usr/bin/env python3
"""
Quick test script for embeddings functionality
"""

import asyncio
import sys
import os

# Add the project root to the Python path
project_root = '/Users/dongood/SourceCode/hackathon/Hackathon'
sys.path.insert(0, project_root)

# Import dynamically to handle the hyphenated module name
import importlib.util
confluence_hub_path = '/Users/dongood/SourceCode/hackathon/Hackathon/services/confluence-hub'
sys.path.insert(0, confluence_hub_path)

from modules.openai_service import OpenAIService

async def test_embeddings():
    """Test the OpenAI embeddings service directly."""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('/Users/dongood/SourceCode/hackathon/Hackathon/services/confluence-hub/.env')
    
    api_key = os.getenv('OpenAIApiKey')
    if not api_key:
        print("❌ OpenAI API key not found in environment variables")
        return False
        
    print(f"✅ OpenAI API key found: {api_key[:10]}...")
    
    # Test OpenAI service
    service = OpenAIService(api_key)
    
    try:
        await service.initialize()
        print(f"✅ OpenAI service initialized: {service.initialized}")
        
        if service.initialized:
            # Test embedding generation
            test_text = "This is a test document for embeddings generation."
            embedding = await service.generate_embedding(test_text)
            print(f"✅ Generated embedding with {len(embedding)} dimensions")
            print(f"   First 5 values: {embedding[:5]}")
            return True
        else:
            print("❌ OpenAI service failed to initialize")
            return False
            
    except Exception as e:
        print(f"❌ Error testing embeddings: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Embeddings Functionality")
    print("=" * 40)
    
    result = asyncio.run(test_embeddings())
    
    if result:
        print("\n🎉 Embeddings functionality is working correctly!")
    else:
        print("\n❌ Embeddings functionality test failed")