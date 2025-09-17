#!/usr/bin/env python3
"""Test script for quality degradation detection functionality in Analysis Service.

Validates that the quality degradation detector works correctly.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_quality_degradation_detector_import():
    """Test that the quality degradation detector module can be imported."""
    try:
        from services.analysis_service.modules.quality_degradation_detector import QualityDegradationDetector, detect_document_degradation
        print("✅ Quality degradation detector module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import quality degradation detector module: {e}")
        return False

def test_quality_degradation_detector_initialization():
    """Test that the quality degradation detector can be initialized."""
    try:
        from services.analysis_service.modules.quality_degradation_detector import QualityDegradationDetector

        detector = QualityDegradationDetector()
        print("✅ QualityDegradationDetector initialized successfully")
        print(f"   Initialized: {detector.initialized}")
        print(f"   Detection thresholds: {len(detector.degradation_thresholds)} configured")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize quality degradation detector: {e}")
        return False

def test_extract_quality_metrics():
    """Test extraction of quality metrics from analysis history."""
    try:
        from services.analysis_service.modules.quality_degradation_detector import QualityDegradationDetector

        detector = QualityDegradationDetector()

        # Create sample analysis history
        base_date = datetime.now()
        analysis_history = [
            {
                'timestamp': (base_date - timedelta(days=60)).isoformat(),
                'quality_score': 0.85,
                'total_findings': 3,
                'sentiment_score': 0.8,
                'readability_score': 0.88
            },
            {
                'timestamp': (base_date - timedelta(days=30)).isoformat(),
                'quality_score': 0.78,
                'total_findings': 7,
                'sentiment_score': 0.75,
                'readability_score': 0.82
            },
            {
                'timestamp': base_date.isoformat(),
                'quality_score': 0.72,
                'total_findings': 10,
                'sentiment_score': 0.7,
                'readability_score': 0.78
            }
        ]

        metrics_df = detector._extract_quality_metrics(analysis_history)

        print("✅ Quality metrics extraction working")
        print(f"   DataFrame shape: {metrics_df.shape}")
        print(f"   Columns: {list(metrics_df.columns)}")
        print(f"   Quality scores: {list(metrics_df['quality_score'])}")
        print(f"   Finding counts: {list(metrics_df['total_findings'])}")

        return True
    except Exception as e:
        print(f"❌ Quality metrics extraction failed: {e}")
        return False

def test_trend_analysis_calculation():
    """Test trend analysis calculation."""
    try:
        from services.analysis_service.modules.quality_degradation_detector import QualityDegradationDetector

        detector = QualityDegradationDetector()

        # Create sample quality scores with degrading trend
        base_date = datetime.now()
        analysis_history = [
            {
                'timestamp': (base_date - timedelta(days=60)).isoformat(),
                'quality_score': 0.85
            },
            {
                'timestamp': (base_date - timedelta(days=45)).isoformat(),
                'quality_score': 0.82
            },
            {
                'timestamp': (base_date - timedelta(days=30)).isoformat(),
                'quality_score': 0.78
            },
            {
                'timestamp': (base_date - timedelta(days=15)).isoformat(),
                'quality_score': 0.74
            },
            {
                'timestamp': base_date.isoformat(),
                'quality_score': 0.70
            }
        ]

        metrics_df = detector._extract_quality_metrics(analysis_history)
        quality_scores = metrics_df['quality_score']
        trend_analysis = detector._calculate_trend_analysis(quality_scores)

        print("✅ Trend analysis calculation working")
        print(f"   Slope: {trend_analysis['slope']:.4f}")
        print(f"   R-squared: {trend_analysis['r_squared']:.3f}")
        print(f"   Trend direction: {trend_analysis['trend_direction']}")
        print(f"   Confidence: {trend_analysis['confidence']:.2f}")

        return True
    except Exception as e:
        print(f"❌ Trend analysis calculation failed: {e}")
        return False

def test_volatility_analysis():
    """Test volatility analysis calculation."""
    try:
        from services.analysis_service.modules.quality_degradation_detector import QualityDegradationDetector

        detector = QualityDegradationDetector()

        # Create sample data with increasing volatility
        base_date = datetime.now()
        analysis_history = [
            {
                'timestamp': (base_date - timedelta(days=60)).isoformat(),
                'quality_score': 0.85
            },
            {
                'timestamp': (base_date - timedelta(days=50)).isoformat(),
                'quality_score': 0.84
            },
            {
                'timestamp': (base_date - timedelta(days=40)).isoformat(),
                'quality_score': 0.86
            },
            {
                'timestamp': (base_date - timedelta(days=30)).isoformat(),
                'quality_score': 0.78
            },
            {
                'timestamp': (base_date - timedelta(days=20)).isoformat(),
                'quality_score': 0.82
            },
            {
                'timestamp': (base_date - timedelta(days=10)).isoformat(),
                'quality_score': 0.70
            },
            {
                'timestamp': base_date.isoformat(),
                'quality_score': 0.75
            }
        ]

        metrics_df = detector._extract_quality_metrics(analysis_history)
        quality_scores = metrics_df['quality_score']
        volatility_analysis = detector._calculate_volatility_analysis(quality_scores)

        print("✅ Volatility analysis working")
        print(f"   Current volatility: {volatility_analysis['current_volatility']:.4f}")
        print(f"   Baseline volatility: {volatility_analysis['baseline_volatility']:.4f}")
        print(f"   Volatility change: {volatility_analysis['volatility_change']:.4f}")
        print(f"   Volatility ratio: {volatility_analysis['volatility_ratio']:.2f}")

        return True
    except Exception as e:
        print(f"❌ Volatility analysis failed: {e}")
        return False

def test_degradation_events_detection():
    """Test degradation events detection."""
    try:
        from services.analysis_service.modules.quality_degradation_detector import QualityDegradationDetector

        detector = QualityDegradationDetector()

        # Create sample data with a sharp degradation event
        base_date = datetime.now()
        analysis_history = [
            {
                'timestamp': (base_date - timedelta(days=60)).isoformat(),
                'quality_score': 0.85
            },
            {
                'timestamp': (base_date - timedelta(days=45)).isoformat(),
                'quality_score': 0.83
            },
            {
                'timestamp': (base_date - timedelta(days=30)).isoformat(),
                'quality_score': 0.81
            },
            {
                'timestamp': (base_date - timedelta(days=15)).isoformat(),
                'quality_score': 0.60  # Sharp degradation
            },
            {
                'timestamp': base_date.isoformat(),
                'quality_score': 0.58
            }
        ]

        metrics_df = detector._extract_quality_metrics(analysis_history)
        quality_scores = metrics_df['quality_score']
        degradation_events = detector._detect_degradation_events(quality_scores, threshold=-0.15)

        print("✅ Degradation events detection working")
        print(f"   Degradation events detected: {len(degradation_events)}")

        for i, event in enumerate(degradation_events):
            print(f"   Event {i+1}:")
            print(f"     Score change: {event['score_change']:.2f}")
            print(f"     Percent change: {event['percent_change']:.1%}")
            print(f"     Severity: {event['severity']}")

        return True
    except Exception as e:
        print(f"❌ Degradation events detection failed: {e}")
        return False

def test_degradation_severity_assessment():
    """Test degradation severity assessment."""
    try:
        from services.analysis_service.modules.quality_degradation_detector import QualityDegradationDetector

        detector = QualityDegradationDetector()

        # Create mock analysis results
        trend_analysis = {
            'slope': -0.005,
            'confidence': 0.85,
            'trend_direction': 'degrading'
        }

        volatility_analysis = {
            'current_volatility': 0.08,
            'baseline_volatility': 0.04,
            'volatility_ratio': 2.0
        }

        degradation_events = [
            {
                'score_change': -0.2,
                'percent_change': -0.25,
                'severity': 'critical'
            }
        ]

        finding_trend = {
            'slope': 0.3,
            'trend_direction': 'increasing'
        }

        severity_assessment = detector._assess_degradation_severity(
            trend_analysis, volatility_analysis, degradation_events, finding_trend
        )

        print("✅ Degradation severity assessment working")
        print(f"   Overall severity: {severity_assessment['overall_severity']}")
        print(f"   Severity score: {severity_assessment['severity_score']:.2f}")
        print(f"   Requires attention: {severity_assessment['requires_attention']}")
        print(f"   Severity factors: {len(severity_assessment['severity_factors'])}")

        for factor in severity_assessment['severity_factors']:
            print(f"     - {factor['factor']}: {factor['severity']} severity")

        return True
    except Exception as e:
        print(f"❌ Degradation severity assessment failed: {e}")
        return False

def test_alert_generation():
    """Test alert generation for degradation."""
    try:
        from services.analysis_service.modules.quality_degradation_detector import QualityDegradationDetector

        detector = QualityDegradationDetector()

        # Test critical severity alert
        severity_assessment = {
            'overall_severity': 'critical',
            'severity_score': 0.85,
            'severity_factors': [
                {'factor': 'trend_slope', 'severity': 'critical', 'description': 'Steep negative trend'}
            ]
        }

        trend_analysis = {'slope': -0.01, 'confidence': 0.9}

        alerts = detector._generate_degradation_alerts(severity_assessment, trend_analysis)

        print("✅ Alert generation working")
        print(f"   Alerts generated: {len(alerts)}")

        for i, alert in enumerate(alerts):
            print(f"   Alert {i+1}:")
            print(f"     Type: {alert['alert_type']}")
            print(f"     Severity: {alert['severity']}")
            print(f"     Priority: {alert['priority']}")
            print(f"     Message: {alert['message']}")

        return True
    except Exception as e:
        print(f"❌ Alert generation failed: {e}")
        return False

async def test_full_quality_degradation_detection():
    """Test the complete quality degradation detection pipeline."""
    try:
        from services.analysis_service.modules.quality_degradation_detector import QualityDegradationDetector

        detector = QualityDegradationDetector()

        # Create comprehensive analysis history showing degradation
        base_date = datetime.now()
        analysis_history = [
            {
                'timestamp': (base_date - timedelta(days=90)).isoformat(),
                'quality_score': 0.88,
                'total_findings': 2,
                'sentiment_score': 0.85,
                'readability_score': 0.90
            },
            {
                'timestamp': (base_date - timedelta(days=75)).isoformat(),
                'quality_score': 0.86,
                'total_findings': 3,
                'sentiment_score': 0.83,
                'readability_score': 0.88
            },
            {
                'timestamp': (base_date - timedelta(days=60)).isoformat(),
                'quality_score': 0.84,
                'total_findings': 4,
                'sentiment_score': 0.81,
                'readability_score': 0.86
            },
            {
                'timestamp': (base_date - timedelta(days=45)).isoformat(),
                'quality_score': 0.81,
                'total_findings': 6,
                'sentiment_score': 0.79,
                'readability_score': 0.84
            },
            {
                'timestamp': (base_date - timedelta(days=30)).isoformat(),
                'quality_score': 0.78,
                'total_findings': 8,
                'sentiment_score': 0.76,
                'readability_score': 0.81
            },
            {
                'timestamp': (base_date - timedelta(days=15)).isoformat(),
                'quality_score': 0.74,
                'total_findings': 9,
                'sentiment_score': 0.73,
                'readability_score': 0.78
            },
            {
                'timestamp': base_date.isoformat(),
                'quality_score': 0.70,
                'total_findings': 12,
                'sentiment_score': 0.70,
                'readability_score': 0.75
            }
        ]

        result = await detector.detect_quality_degradation(
            document_id="degrading_document",
            analysis_history=analysis_history,
            baseline_period_days=60,
            alert_threshold=0.05
        )

        print("✅ Full quality degradation detection pipeline working")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Degradation detected: {result['degradation_detected']}")
        print(f"   Overall severity: {result['severity_assessment']['overall_severity']}")
        print(f"   Severity score: {result['severity_assessment']['severity_score']:.2f}")
        print(f"   Trend direction: {result['trend_analysis']['trend_direction']}")
        print(f"   Confidence: {result['trend_analysis']['confidence']:.2f}")
        print(f"   Data points: {result['data_points']}")
        print(f"   Alerts generated: {len(result['alerts'])}")
        print(f"   Processing time: {result['processing_time']:.2f}s")

        if result['alerts']:
            print(f"   Alert details:")
            for alert in result['alerts']:
                print(f"     - {alert['severity'].upper()} PRIORITY: {alert['message']}")

        if result['recommendations']:
            print(f"   Key recommendations:")
            for i, rec in enumerate(result['recommendations'][:3]):
                print(f"     {i+1}. {rec}")

        return True
    except Exception as e:
        print(f"❌ Full quality degradation detection failed: {e}")
        return False

def test_main_app_import():
    """Test that the main app can be imported with quality degradation detection endpoints."""
    try:
        from services.analysis_service.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        degradation_routes = [r for r in routes if 'degradation' in r]

        print("✅ Main app imported successfully")
        print(f"✅ Found {len(degradation_routes)} quality degradation detection routes:")
        for route in degradation_routes:
            print(f"   - {route}")

        return True
    except Exception as e:
        print(f"❌ Failed to import main app: {e}")
        return False

def main():
    """Run all tests."""
    print("📉 Testing Quality Degradation Detection Functionality")
    print("=" * 70)

    tests = [
        test_quality_degradation_detector_import,
        test_quality_degradation_detector_initialization,
        test_extract_quality_metrics,
        test_trend_analysis_calculation,
        test_volatility_analysis,
        test_degradation_events_detection,
        test_degradation_severity_assessment,
        test_alert_generation,
        test_full_quality_degradation_detection,
        test_main_app_import,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        print(f"\n🧪 Running {test.__name__}...")
        try:
            if test.__name__ == 'test_full_quality_degradation_detection':
                import asyncio
                result = asyncio.run(test())
            else:
                result = test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        print()

    print("=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All quality degradation detection tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
