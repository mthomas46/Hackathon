#!/usr/bin/env python3
"""Test script for sentiment analysis functionality in Analysis Service.

Validates that the sentiment analyzer works correctly.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_sentiment_analyzer_import():
    """Test that the sentiment analyzer module can be imported."""
    try:
        from services.analysis_service.modules.sentiment_analyzer import SentimentAnalyzer, analyze_document_sentiment
        print("✅ Sentiment analyzer module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import sentiment analyzer module: {e}")
        return False

def test_sentiment_analyzer_initialization():
    """Test that the sentiment analyzer can be initialized."""
    try:
        from services.analysis_service.modules.sentiment_analyzer import SentimentAnalyzer

        analyzer = SentimentAnalyzer()
        print("✅ SentimentAnalyzer initialized successfully")
        print(f"   Model: {analyzer.model_name}")
        print(f"   Initialized: {analyzer.initialized}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize sentiment analyzer: {e}")
        return False

def test_textblob_sentiment_analysis():
    """Test TextBlob-based sentiment analysis."""
    try:
        from services.analysis_service.modules.sentiment_analyzer import SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        text = "This is an amazing and wonderful feature that I'm really excited about!"
        result = analyzer._analyze_sentiment_textblob(text)

        print("✅ TextBlob sentiment analysis working")
        print(f"   Text: '{text[:50]}...'")
        print(f"   Sentiment: {result['sentiment']}")
        print(f"   Polarity: {result['polarity']:.2f}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Subjectivity: {result['subjectivity']:.2f}")

        return True
    except Exception as e:
        print(f"❌ TextBlob sentiment analysis failed: {e}")
        return False

def test_readability_metrics():
    """Test readability metrics calculation."""
    try:
        from services.analysis_service.modules.sentiment_analyzer import SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        text = "This is a well-written document. It contains clear and concise information that is easy to understand. The structure is logical and the content flows naturally from one idea to the next."
        result = analyzer._calculate_readability_metrics(text)

        print("✅ Readability metrics calculation working")
        print(f"   Sentence count: {result['sentence_count']}")
        print(f"   Word count: {result['word_count']}")
        print(f"   Readability score: {result['readability_score']:.2f}")
        print(f"   Clarity score: {result['clarity_score']:.2f}")
        print(f"   Flesch-Kincaid grade: {result['flesch_kincaid_grade']:.1f}")

        return True
    except Exception as e:
        print(f"❌ Readability metrics calculation failed: {e}")
        return False

def test_tone_analysis():
    """Test tone analysis functionality."""
    try:
        from services.analysis_service.modules.sentiment_analyzer import SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        text = "Welcome to our comprehensive guide! We're thrilled to help you succeed with our amazing platform. This documentation will provide clear, step-by-step instructions to get you started quickly."
        result = analyzer._analyze_tone_patterns(text)

        print("✅ Tone analysis working")
        print(f"   Primary tone: {result['primary_tone']}")
        print(f"   Positive score: {result['tone_scores']['positive']:.2f}")
        print(f"   Professional score: {result['tone_scores']['professional']:.2f}")
        print(f"   Positive words: {result['tone_indicators']['positive_words']}")
        print(f"   Professional phrases: {result['tone_indicators']['professional_phrases']}")

        return True
    except Exception as e:
        print(f"❌ Tone analysis failed: {e}")
        return False

def test_full_sentiment_analysis():
    """Test the complete sentiment analysis pipeline."""
    try:
        from services.analysis_service.modules.sentiment_analyzer import SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        document = {
            "id": "test_doc",
            "title": "Getting Started Guide",
            "content": "Welcome to our platform! This guide will help you get started with ease. We're excited to have you here and look forward to your success.",
            "metadata": {"author": "Test Author"}
        }

        # Test with initialization mocked to avoid model loading
        with analyzer._initialize_models() as init_success:
            if not init_success:
                print("⚠️  Models not available, but core functionality should still work")

            result = analyzer.analyze_sentiment_and_clarity(
                document=document,
                use_transformer=False,
                include_tone_analysis=True
            )

            print("✅ Full sentiment analysis pipeline working")
            print(f"   Document ID: {result['document_id']}")
            print(f"   Quality score: {result['quality_score']:.2f}")
            print(f"   Sentiment: {result['sentiment_analysis']['sentiment']}")
            print(f"   Processing time: {result['processing_time']:.2f}s")

            if result['recommendations']:
                print(f"   Recommendations: {len(result['recommendations'])} items")
                for rec in result['recommendations'][:2]:  # Show first 2
                    print(f"     - {rec}")

            return True

    except Exception as e:
        print(f"❌ Full sentiment analysis failed: {e}")
        return False

def test_main_app_import():
    """Test that the main app can be imported with sentiment analysis endpoints."""
    try:
        from services.analysis_service.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        sentiment_routes = [r for r in routes if 'sentiment' in r or 'tone' in r]

        print("✅ Main app imported successfully")
        print(f"✅ Found {len(sentiment_routes)} sentiment/tone analysis routes:")
        for route in sentiment_routes:
            print(f"   - {route}")

        return True
    except Exception as e:
        print(f"❌ Failed to import main app: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Sentiment Analysis Functionality")
    print("=" * 60)

    tests = [
        test_sentiment_analyzer_import,
        test_sentiment_analyzer_initialization,
        test_textblob_sentiment_analysis,
        test_readability_metrics,
        test_tone_analysis,
        test_full_sentiment_analysis,
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
        print("🎉 All sentiment analysis tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
