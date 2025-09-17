#!/usr/bin/env python3
"""Test script for content quality scoring functionality in Analysis Service.

Validates that the content quality scorer works correctly.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_content_quality_scorer_import():
    """Test that the content quality scorer module can be imported."""
    try:
        from services.analysis_service.modules.content_quality_scorer import ContentQualityScorer, assess_document_quality
        print("✅ Content quality scorer module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import content quality scorer module: {e}")
        return False

def test_content_quality_scorer_initialization():
    """Test that the content quality scorer can be initialized."""
    try:
        from services.analysis_service.modules.content_quality_scorer import ContentQualityScorer

        scorer = ContentQualityScorer()
        print("✅ ContentQualityScorer initialized successfully")
        print(f"   Initialized: {scorer.initialized}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize content quality scorer: {e}")
        return False

def test_readability_metrics():
    """Test readability metrics calculation."""
    try:
        from services.analysis_service.modules.content_quality_scorer import ContentQualityScorer

        scorer = ContentQualityScorer()

        text = "This is a well-written document that provides clear and comprehensive information. It uses appropriate language and maintains good readability throughout."
        result = scorer._calculate_readability_metrics(text)

        print("✅ Readability metrics calculation working")
        print(f"   Sentence count: {result['sentence_count']}")
        print(f"   Word count: {result['word_count']}")
        print(f"   Readability score: {result['readability_score']:.2f}")
        print(f"   Flesch-Kincaid grade: {result['flesch_kincaid_grade']:.1f}")
        print(f"   Readability level: {result['readability_level']}")

        return True
    except Exception as e:
        print(f"❌ Readability metrics calculation failed: {e}")
        return False

def test_content_structure_assessment():
    """Test content structure assessment."""
    try:
        from services.analysis_service.modules.content_quality_scorer import ContentQualityScorer

        scorer = ContentQualityScorer()

        text = "# Introduction\n\nThis guide provides essential information.\n\n## Getting Started\n\nFollow these steps:\n- Step 1: Install requirements\n- Step 2: Configure settings\n\n## Advanced Usage\n\nFor more complex scenarios..."
        sentences = [s.strip() for s in text.split('.') if s.strip()]

        result = scorer._assess_content_structure(text, sentences)

        print("✅ Content structure assessment working")
        print(f"   Structure score: {result['structure_score']:.2f}")
        print(f"   Heading count: {result['heading_count']}")
        print(f"   List count: {result['list_count']}")
        print(f"   Structure level: {result['structure_level']}")

        return True
    except Exception as e:
        print(f"❌ Content structure assessment failed: {e}")
        return False

def test_completeness_assessment():
    """Test content completeness assessment."""
    try:
        from services.analysis_service.modules.content_quality_scorer import ContentQualityScorer

        scorer = ContentQualityScorer()

        text = "Welcome to our API guide. This documentation covers authentication, data retrieval, and error handling. You'll need an API key to get started. Here are some examples of how to use the endpoints."
        doc = {
            "id": "test_doc",
            "title": "API Guide",
            "metadata": {"type": "documentation"}
        }

        result = scorer._assess_content_completeness(text, doc)

        print("✅ Content completeness assessment working")
        print(f"   Completeness score: {result['completeness_score']:.2f}")
        print(f"   Found elements: {result['found_elements']}")
        print(f"   Word count: {result['word_count']}")
        print(f"   Completeness level: {result['completeness_level']}")

        return True
    except Exception as e:
        print(f"❌ Content completeness assessment failed: {e}")
        return False

def test_technical_accuracy_assessment():
    """Test technical accuracy assessment."""
    try:
        from services.analysis_service.modules.content_quality_scorer import ContentQualityScorer

        scorer = ContentQualityScorer()

        text = "This document provides accurate and well-formatted technical information. It follows proper conventions and uses appropriate terminology throughout."
        doc = {"id": "test_doc"}

        result = scorer._assess_technical_accuracy(text, doc)

        print("✅ Technical accuracy assessment working")
        print(f"   Accuracy score: {result['accuracy_score']:.2f}")
        print(f"   Issue count: {result['issue_count']}")
        print(f"   Capitalization ratio: {result['capitalization_ratio']:.2f}")
        print(f"   Accuracy level: {result['accuracy_level']}")

        return True
    except Exception as e:
        print(f"❌ Technical accuracy assessment failed: {e}")
        return False

def test_overall_quality_calculation():
    """Test overall quality score calculation."""
    try:
        from services.analysis_service.modules.content_quality_scorer import ContentQualityScorer

        scorer = ContentQualityScorer()

        # Good scores across all components
        readability_score = 0.8
        structure_score = 0.9
        completeness_score = 0.85
        accuracy_score = 0.9

        result = scorer._calculate_overall_quality_score(
            readability_score, structure_score, completeness_score, accuracy_score
        )

        print("✅ Overall quality calculation working")
        print(f"   Overall score: {result['overall_score']:.2f}")
        print(f"   Grade: {result['grade']}")
        print(f"   Description: {result['description']}")
        print(f"   Component scores: {result['component_scores']}")

        return True
    except Exception as e:
        print(f"❌ Overall quality calculation failed: {e}")
        return False

async def test_full_quality_assessment():
    """Test the complete quality assessment pipeline."""
    try:
        from services.analysis_service.modules.content_quality_scorer import ContentQualityScorer

        scorer = ContentQualityScorer()

        document = {
            "id": "test_doc",
            "title": "Getting Started Guide",
            "content": "# Welcome\n\nThis comprehensive guide helps you get started with our platform. You'll learn about installation, configuration, and basic usage.\n\n## Installation\n\nFirst, install the required dependencies. Then, follow the setup wizard.\n\n## Examples\n\nHere are some code examples to help you understand the concepts.\n\n## Troubleshooting\n\nCommon issues and their solutions are covered here.",
            "metadata": {
                "author": "Test Author",
                "type": "documentation"
            }
        }

        result = await scorer.assess_content_quality(document)

        print("✅ Full quality assessment pipeline working")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Overall score: {result['quality_assessment']['overall_score']:.2f}")
        print(f"   Grade: {result['quality_assessment']['grade']}")
        print(f"   Description: {result['quality_assessment']['description']}")
        print(f"   Processing time: {result['processing_time']:.2f}s")

        if result['recommendations']:
            print(f"   Recommendations ({len(result['recommendations'])}):")
            for rec in result['recommendations'][:3]:  # Show first 3
                print(f"     - {rec}")

        return True
    except Exception as e:
        print(f"❌ Full quality assessment failed: {e}")
        return False

def test_main_app_import():
    """Test that the main app can be imported with quality assessment endpoints."""
    try:
        from services.analysis_service.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        quality_routes = [r for r in routes if 'quality' in r]

        print("✅ Main app imported successfully")
        print(f"✅ Found {len(quality_routes)} quality assessment routes:")
        for route in quality_routes:
            print(f"   - {route}")

        return True
    except Exception as e:
        print(f"❌ Failed to import main app: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Testing Content Quality Scoring Functionality")
    print("=" * 60)

    tests = [
        (test_content_quality_scorer_import, False),
        (test_content_quality_scorer_initialization, False),
        (test_readability_metrics, False),
        (test_content_structure_assessment, False),
        (test_completeness_assessment, False),
        (test_technical_accuracy_assessment, False),
        (test_overall_quality_calculation, False),
        (test_full_quality_assessment, True),  # This is async
        (test_main_app_import, False),
    ]

    passed = 0
    total = len(tests)

    for test_func, is_async in tests:
        print(f"\n🧪 Running {test_func.__name__}...")
        try:
            if is_async:
                result = await test_func()
            else:
                result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        print()

    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All content quality scoring tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
