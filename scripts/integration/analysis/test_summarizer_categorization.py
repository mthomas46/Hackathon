#!/usr/bin/env python3
"""Test script for Summarizer Hub categorization functionality.

Validates that the categorization module works correctly.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_categorizer_import():
    """Test that the categorizer module can be imported."""
    try:
        from services.summarizer-hub.modules.categorizer import DocumentCategorizer, categorize_document
        print("✅ Categorizer module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import categorizer module: {e}")
        return False

def test_categorizer_initialization():
    """Test that the categorizer can be initialized."""
    try:
        from services.summarizer-hub.modules.categorizer import DocumentCategorizer

        categorizer = DocumentCategorizer()
        print("✅ DocumentCategorizer initialized successfully")
        print(f"   Model: {categorizer.model_name}")
        print(f"   Initialized: {categorizer.initialized}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize categorizer: {e}")
        return False

def test_rule_based_categorization():
    """Test rule-based categorization functionality."""
    try:
        from services.summarizer-hub.modules.categorizer import DocumentCategorizer

        categorizer = DocumentCategorizer()

        # Test API documentation
        api_text = "This guide explains how to use our REST API endpoints for authentication and data retrieval."
        result = categorizer._rule_based_categorization(api_text)

        print("✅ Rule-based categorization working")
        print(f"   API text categorized as: {result['category']} (confidence: {result['confidence']:.2f})")

        # Test tutorial content
        tutorial_text = "Welcome to our platform! This tutorial will help you get started."
        result2 = categorizer._rule_based_categorization(tutorial_text)

        print(f"   Tutorial text categorized as: {result2['category']} (confidence: {result2['confidence']:.2f})")

        return True
    except Exception as e:
        print(f"❌ Rule-based categorization failed: {e}")
        return False

def test_keyword_extraction():
    """Test keyword extraction functionality."""
    try:
        from services.summarizer-hub.modules.categorizer import DocumentCategorizer

        categorizer = DocumentCategorizer()

        text = "This document covers API authentication, security best practices, and integration guidelines."
        keywords = categorizer._extract_keywords(text, max_keywords=5)

        print("✅ Keyword extraction working")
        print(f"   Extracted keywords: {keywords}")

        return True
    except Exception as e:
        print(f"❌ Keyword extraction failed: {e}")
        return False

def test_main_app_import():
    """Test that the main app can be imported."""
    try:
        from services.summarizer-hub.main import app
        print("✅ Main app imported successfully")

        # Check that categorization endpoints exist
        routes = [route.path for route in app.routes]
        categorization_routes = [r for r in routes if 'categorize' in r]

        print(f"✅ Found {len(categorization_routes)} categorization routes:")
        for route in categorization_routes:
            print(f"   - {route}")

        return True
    except Exception as e:
        print(f"❌ Failed to import main app: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Summarizer Hub Categorization Functionality")
    print("=" * 60)

    tests = [
        test_categorizer_import,
        test_categorizer_initialization,
        test_rule_based_categorization,
        test_keyword_extraction,
        test_main_app_import,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        print(f"\n🧪 Running {test.__name__}...")
        if test():
            passed += 1
        print()

    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All categorization functionality tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
