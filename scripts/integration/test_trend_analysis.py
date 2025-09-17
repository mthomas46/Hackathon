#!/usr/bin/env python3
"""Test script for trend analysis functionality in Analysis Service.

Validates that the trend analyzer works correctly.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_trend_analyzer_import():
    """Test that the trend analyzer module can be imported."""
    try:
        from services.analysis_service.modules.trend_analyzer import TrendAnalyzer, analyze_document_trends
        print("✅ Trend analyzer module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import trend analyzer module: {e}")
        return False

def test_trend_analyzer_initialization():
    """Test that the trend analyzer can be initialized."""
    try:
        from services.analysis_service.modules.trend_analyzer import TrendAnalyzer

        analyzer = TrendAnalyzer()
        print("✅ TrendAnalyzer initialized successfully")
        print(f"   Initialized: {analyzer.initialized}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize trend analyzer: {e}")
        return False

def test_extract_historical_data():
    """Test extraction of historical data."""
    try:
        from services.analysis_service.modules.trend_analyzer import TrendAnalyzer

        analyzer = TrendAnalyzer()

        # Create sample analysis results
        base_date = datetime.now()
        sample_results = [
            {
                "document_id": "doc1",
                "timestamp": (base_date - timedelta(days=10)).isoformat(),
                "total_findings": 5,
                "quality_score": 0.75,
                "findings": [{"type": "drift", "severity": "high"}]
            },
            {
                "document_id": "doc1",
                "timestamp": (base_date - timedelta(days=5)).isoformat(),
                "total_findings": 3,
                "quality_score": 0.82,
                "findings": [{"type": "consistency", "severity": "medium"}]
            }
        ]

        df = analyzer._extract_historical_data(sample_results)

        print("✅ Historical data extraction working")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Date range: {df.index.min()} to {df.index.max()}")

        return True
    except Exception as e:
        print(f"❌ Historical data extraction failed: {e}")
        return False

def test_trend_pattern_analysis():
    """Test trend pattern analysis."""
    try:
        from services.analysis_service.modules.trend_analyzer import TrendAnalyzer

        analyzer = TrendAnalyzer()

        # Create sample analysis results with improving trend
        base_date = datetime.now()
        sample_results = [
            {
                "document_id": "doc1",
                "timestamp": (base_date - timedelta(days=30)).isoformat(),
                "quality_score": 0.70,
                "total_findings": 8
            },
            {
                "document_id": "doc1",
                "timestamp": (base_date - timedelta(days=20)).isoformat(),
                "quality_score": 0.75,
                "total_findings": 6
            },
            {
                "document_id": "doc1",
                "timestamp": (base_date - timedelta(days=10)).isoformat(),
                "quality_score": 0.80,
                "total_findings": 4
            },
            {
                "document_id": "doc1",
                "timestamp": base_date.isoformat(),
                "quality_score": 0.85,
                "total_findings": 2
            }
        ]

        df = analyzer._extract_historical_data(sample_results)
        result = analyzer._analyze_trend_patterns(df)

        print("✅ Trend pattern analysis working")
        print(f"   Trend direction: {result['trend_direction']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Data points: {result['data_points']}")
        print(f"   Volatility: {result['volatility']:.3f}")

        return True
    except Exception as e:
        print(f"❌ Trend pattern analysis failed: {e}")
        return False

def test_future_issue_prediction():
    """Test future issue prediction."""
    try:
        from services.analysis_service.modules.trend_analyzer import TrendAnalyzer

        analyzer = TrendAnalyzer()

        # Create sample data
        base_date = datetime.now()
        sample_results = [
            {
                "document_id": "doc1",
                "timestamp": (base_date - timedelta(days=20)).isoformat(),
                "quality_score": 0.75,
                "total_findings": 6,
                "findings": [{"type": "drift"}, {"type": "drift"}]
            },
            {
                "document_id": "doc1",
                "timestamp": (base_date - timedelta(days=10)).isoformat(),
                "quality_score": 0.80,
                "total_findings": 4,
                "findings": [{"type": "drift"}]
            },
            {
                "document_id": "doc1",
                "timestamp": base_date.isoformat(),
                "quality_score": 0.85,
                "total_findings": 2,
                "findings": []
            }
        ]

        df = analyzer._extract_historical_data(sample_results)
        predictions = analyzer._predict_future_issues(df, prediction_days=7)

        print("✅ Future issue prediction working")
        print(f"   Prediction confidence: {predictions['confidence']:.2f}")
        print(f"   Prediction horizon: {predictions['prediction_horizon_days']} days")

        quality_pred = predictions['predictions'].get('quality_score', {})
        if quality_pred:
            print(f"   Quality trend: {quality_pred.get('current_trend', 'unknown')}")
            print(f"   Predicted final value: {quality_pred.get('predicted_values', [-1])[-1]:.2f}")

        return True
    except Exception as e:
        print(f"❌ Future issue prediction failed: {e}")
        return False

def test_risk_area_identification():
    """Test risk area identification."""
    try:
        from services.analysis_service.modules.trend_analyzer import TrendAnalyzer

        analyzer = TrendAnalyzer()

        # Create sample data with declining trend
        base_date = datetime.now()
        sample_results = [
            {
                "document_id": "doc1",
                "timestamp": (base_date - timedelta(days=10)).isoformat(),
                "quality_score": 0.85
            },
            {
                "document_id": "doc1",
                "timestamp": base_date.isoformat(),
                "quality_score": 0.75
            }
        ]

        df = analyzer._extract_historical_data(sample_results)
        predictions = {
            'predictions': {
                'quality_score': {
                    'current_trend': 'declining',
                    'predicted_values': [0.65, 0.60]
                }
            }
        }

        risk_areas = analyzer._identify_risk_areas(df, predictions)

        print("✅ Risk area identification working")
        print(f"   Number of risk areas: {len(risk_areas)}")

        for i, risk in enumerate(risk_areas[:2]):  # Show first 2
            print(f"   Risk {i+1}: {risk['risk_type']} (severity: {risk['severity']})")
            print(f"     Description: {risk['description']}")

        return True
    except Exception as e:
        print(f"❌ Risk area identification failed: {e}")
        return False

async def test_full_trend_analysis():
    """Test the complete trend analysis pipeline."""
    try:
        from services.analysis_service.modules.trend_analyzer import TrendAnalyzer

        analyzer = TrendAnalyzer()

        # Create comprehensive sample data
        base_date = datetime.now()
        sample_results = [
            {
                "document_id": "test_doc",
                "timestamp": (base_date - timedelta(days=30)).isoformat(),
                "total_findings": 8,
                "quality_score": 0.70,
                "findings": [{"type": "drift"}, {"type": "consistency"}]
            },
            {
                "document_id": "test_doc",
                "timestamp": (base_date - timedelta(days=20)).isoformat(),
                "total_findings": 6,
                "quality_score": 0.75,
                "findings": [{"type": "drift"}]
            },
            {
                "document_id": "test_doc",
                "timestamp": (base_date - timedelta(days=10)).isoformat(),
                "total_findings": 4,
                "quality_score": 0.80,
                "findings": [{"type": "consistency"}]
            },
            {
                "document_id": "test_doc",
                "timestamp": base_date.isoformat(),
                "total_findings": 2,
                "quality_score": 0.85,
                "findings": []
            }
        ]

        result = await analyzer.analyze_documentation_trends(
            document_id="test_doc",
            analysis_results=sample_results,
            prediction_days=14,
            include_predictions=True
        )

        print("✅ Full trend analysis pipeline working")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Trend direction: {result['trend_direction']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Data points: {result['data_points']}")
        print(f"   Risk areas: {len(result['risk_areas'])}")
        print(f"   Processing time: {result['processing_time']:.2f}s")

        if result['insights']:
            print(f"   Insights ({len(result['insights'])}):")
            for insight in result['insights'][:2]:  # Show first 2
                print(f"     - {insight}")

        return True
    except Exception as e:
        print(f"❌ Full trend analysis failed: {e}")
        return False

def test_main_app_import():
    """Test that the main app can be imported with trend analysis endpoints."""
    try:
        from services.analysis_service.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        trend_routes = [r for r in routes if 'trends' in r]

        print("✅ Main app imported successfully")
        print(f"✅ Found {len(trend_routes)} trend analysis routes:")
        for route in trend_routes:
            print(f"   - {route}")

        return True
    except Exception as e:
        print(f"❌ Failed to import main app: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Trend Analysis Functionality")
    print("=" * 60)

    tests = [
        test_trend_analyzer_import,
        test_trend_analyzer_initialization,
        test_extract_historical_data,
        test_trend_pattern_analysis,
        test_future_issue_prediction,
        test_risk_area_identification,
        test_full_trend_analysis,
        test_main_app_import,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        print(f"\n🧪 Running {test.__name__}...")
        try:
            if test.__name__ == 'test_full_trend_analysis':
                import asyncio
                result = asyncio.run(test())
            else:
                result = test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        print()

    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All trend analysis tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
