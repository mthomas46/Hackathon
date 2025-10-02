#!/usr/bin/env python3
"""Test script for maintenance forecasting functionality in Analysis Service.

Validates that the maintenance forecaster works correctly.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_maintenance_forecaster_import():
    """Test that the maintenance forecaster module can be imported."""
    try:
        from services.analysis_service.modules.maintenance_forecaster import MaintenanceForecaster, forecast_document_maintenance
        print("✅ Maintenance forecaster module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import maintenance forecaster module: {e}")
        return False

def test_maintenance_forecaster_initialization():
    """Test that the maintenance forecaster can be initialized."""
    try:
        from services.analysis_service.modules.maintenance_forecaster import MaintenanceForecaster

        forecaster = MaintenanceForecaster()
        print("✅ MaintenanceForecaster initialized successfully")
        print(f"   Initialized: {forecaster.initialized}")
        print(f"   Maintenance factors: {len(forecaster.maintenance_factors)} configured")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize maintenance forecaster: {e}")
        return False

def test_maintenance_urgency_calculation():
    """Test maintenance urgency calculations."""
    try:
        from services.analysis_service.modules.maintenance_forecaster import MaintenanceForecaster

        forecaster = MaintenanceForecaster()

        # Test risk score urgency
        high_risk_urgency = forecaster._calculate_maintenance_urgency('risk_score', 0.8, forecaster.maintenance_factors['risk_score'])
        print("✅ Maintenance urgency calculation working")
        print(f"   High risk score (0.8) urgency: {high_risk_urgency['urgency_score']:.2f}")
        print(f"   Predicted days: {high_risk_urgency['predicted_days']}")

        low_risk_urgency = forecaster._calculate_maintenance_urgency('risk_score', 0.2, forecaster.maintenance_factors['risk_score'])
        print(f"   Low risk score (0.2) urgency: {low_risk_urgency['urgency_score']:.2f}")
        print(f"   Predicted days: {low_risk_urgency['predicted_days']}")

        # Test document age urgency
        old_doc_urgency = forecaster._calculate_maintenance_urgency('document_age', 300, forecaster.maintenance_factors['document_age'])
        print(f"   Old document (300 days) urgency: {old_doc_urgency['urgency_score']:.2f}")
        print(f"   Predicted days: {old_doc_urgency['predicted_days']}")

        # Test usage frequency urgency
        high_usage_urgency = forecaster._calculate_maintenance_urgency('usage_frequency', 500, forecaster.maintenance_factors['usage_frequency'])
        print(f"   High usage (500) urgency: {high_usage_urgency['urgency_score']:.2f}")
        print(f"   Predicted days: {high_usage_urgency['predicted_days']}")

        return True
    except Exception as e:
        print(f"❌ Maintenance urgency calculation failed: {e}")
        return False

def test_maintenance_factor_forecasting():
    """Test maintenance factor forecasting."""
    try:
        from services.analysis_service.modules.maintenance_forecaster import MaintenanceForecaster

        forecaster = MaintenanceForecaster()

        # Create sample document data
        document_data = {
            'document_id': 'test_doc',
            'content': 'Sample API documentation...',
            'last_modified': (datetime.now() - timedelta(days=150)).isoformat(),
            'quality_score': 0.7,
            'risk_score': 0.6,
            'usage_frequency': 200,
            'business_criticality': 'high'
        }

        forecast_data = forecaster._forecast_maintenance_schedule(document_data)

        print("✅ Maintenance factor forecasting working")
        print(f"   Overall predicted days: {forecast_data['overall_forecast']['predicted_days']}")
        print(f"   Overall urgency score: {forecast_data['overall_forecast']['urgency_score']:.2f}")
        print(f"   Priority level: {forecast_data['overall_forecast']['priority_level']}")
        print(f"   Confidence: {forecast_data['overall_forecast']['confidence']:.2f}")
        print(f"   Factor forecasts: {len(forecast_data['factor_forecasts'])}")
        print(f"   Urgent factors: {len(forecast_data['urgent_factors'])}")

        return True
    except Exception as e:
        print(f"❌ Maintenance factor forecasting failed: {e}")
        return False

def test_maintenance_schedule_generation():
    """Test maintenance schedule generation."""
    try:
        from services.analysis_service.modules.maintenance_forecaster import MaintenanceForecaster

        forecaster = MaintenanceForecaster()

        # Test critical priority schedule
        critical_schedule = forecaster._generate_maintenance_schedule(30, 'critical', [])
        print("✅ Maintenance schedule generation working")
        print(f"   Critical schedule type: {critical_schedule['maintenance_type']}")
        print(f"   Critical milestones: {len(critical_schedule['milestones'])}")
        for milestone in critical_schedule['milestones'][:2]:
            print(f"     - {milestone['date'][:10]}: {milestone['description']}")

        # Test medium priority schedule
        medium_schedule = forecaster._generate_maintenance_schedule(90, 'medium', [])
        print(f"   Medium schedule type: {medium_schedule['maintenance_type']}")
        print(f"   Medium milestones: {len(medium_schedule['milestones'])}")

        # Test low priority schedule
        low_schedule = forecaster._generate_maintenance_schedule(180, 'low', [])
        print(f"   Low schedule type: {low_schedule['maintenance_type']}")
        print(f"   Low milestones: {len(low_schedule['milestones'])}")

        return True
    except Exception as e:
        print(f"❌ Maintenance schedule generation failed: {e}")
        return False

def test_maintenance_recommendations():
    """Test maintenance recommendation generation."""
    try:
        from services.analysis_service.modules.maintenance_forecaster import MaintenanceForecaster

        forecaster = MaintenanceForecaster()

        # Test critical recommendations
        critical_forecast = {
            'overall_forecast': {'priority_level': 'critical', 'predicted_days': 15},
            'urgent_factors': [{'factor': 'risk_score', 'urgency': 0.9}]
        }
        critical_recs = forecaster._generate_maintenance_recommendations(critical_forecast)

        print("✅ Maintenance recommendations working")
        print(f"   Critical recommendations ({len(critical_recs)}):")
        for rec in critical_recs[:3]:
            print(f"     - {rec}")

        # Test medium recommendations
        medium_forecast = {
            'overall_forecast': {'priority_level': 'medium', 'predicted_days': 75},
            'urgent_factors': []
        }
        medium_recs = forecaster._generate_maintenance_recommendations(medium_forecast)

        print(f"   Medium recommendations ({len(medium_recs)}):")
        for rec in medium_recs[:2]:
            print(f"     - {rec}")

        return True
    except Exception as e:
        print(f"❌ Maintenance recommendations failed: {e}")
        return False

async def test_full_maintenance_forecasting():
    """Test the complete maintenance forecasting pipeline."""
    try:
        from services.analysis_service.modules.maintenance_forecaster import MaintenanceForecaster

        forecaster = MaintenanceForecaster()

        # Create comprehensive sample data
        document_data = {
            'document_id': 'comprehensive_test_doc',
            'document_type': 'api_reference',
            'content': '''
            # Comprehensive API Documentation

            This is a detailed API reference that covers authentication, endpoints,
            error handling, and best practices for our REST API.

            ## Authentication
            Use OAuth 2.0 with client credentials flow.

            ## Endpoints
            - GET /users - List users
            - POST /users - Create user
            - PUT /users/{id} - Update user
            - DELETE /users/{id} - Delete user

            ## Error Codes
            - 400 Bad Request
            - 401 Unauthorized
            - 403 Forbidden
            - 404 Not Found
            - 500 Internal Server Error

            ## Changelog
            - v2.1.0: Added bulk operations
            - v2.0.0: Major API redesign
            - v1.5.0: Enhanced security
            - v1.0.0: Initial release
            ''',
            'last_modified': (datetime.now() - timedelta(days=200)).isoformat(),
            'author': 'api_team',
            'quality_score': 0.7,
            'risk_score': 0.75,
            'usage_frequency': 300,
            'business_criticality': 'high'
        }

        # Create analysis history
        analysis_history = [
            {
                'timestamp': (datetime.now() - timedelta(days=180)).isoformat(),
                'quality_score': 0.75,
                'risk_score': 0.7,
                'total_findings': 8
            },
            {
                'timestamp': (datetime.now() - timedelta(days) - timedelta(days=120)).isoformat(),
                'quality_score': 0.72,
                'risk_score': 0.73,
                'total_findings': 9
            },
            {
                'timestamp': (datetime.now() - timedelta(days=60)).isoformat(),
                'quality_score': 0.7,
                'risk_score': 0.75,
                'total_findings': 10
            }
        ]

        result = await forecaster.forecast_document_maintenance(
            document_id="comprehensive_test_doc",
            document_data=document_data,
            analysis_history=analysis_history
        )

        print("✅ Full maintenance forecasting pipeline working")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Predicted maintenance days: {result['forecast_data']['overall_forecast']['predicted_days']}")
        print(f"   Urgency score: {result['forecast_data']['overall_forecast']['urgency_score']:.2f}")
        print(f"   Priority level: {result['forecast_data']['overall_forecast']['priority_level']}")
        print(f"   Confidence: {result['forecast_data']['overall_forecast']['confidence']:.2f}")
        print(f"   Maintenance type: {result['forecast_data']['maintenance_schedule']['maintenance_type']}")
        print(f"   Recommendations: {len(result['recommendations'])}")
        print(f"   Processing time: {result['processing_time']:.2f}s")

        if result['recommendations']:
            print(f"   Key recommendations:")
            for i, rec in enumerate(result['recommendations'][:3]):
                print(f"     {i+1}. {rec}")

        if result['forecast_data']['maintenance_schedule']['milestones']:
            print(f"   Maintenance milestones:")
            for milestone in result['forecast_data']['maintenance_schedule']['milestones'][:2]:
                print(f"     - {milestone['date'][:10]}: {milestone['description']}")

        return True
    except Exception as e:
        print(f"❌ Full maintenance forecasting failed: {e}")
        return False

def test_main_app_import():
    """Test that the main app can be imported with maintenance forecasting endpoints."""
    try:
        from services.analysis_service.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        maintenance_routes = [r for r in routes if 'maintenance' in r]

        print("✅ Main app imported successfully")
        print(f"✅ Found {len(maintenance_routes)} maintenance forecasting routes:")
        for route in maintenance_routes:
            print(f"   - {route}")

        return True
    except Exception as e:
        print(f"❌ Failed to import main app: {e}")
        return False

def main():
    """Run all tests."""
    print("🔧 Testing Maintenance Forecasting Functionality")
    print("=" * 60)

    tests = [
        test_maintenance_forecaster_import,
        test_maintenance_forecaster_initialization,
        test_maintenance_urgency_calculation,
        test_maintenance_factor_forecasting,
        test_maintenance_schedule_generation,
        test_maintenance_recommendations,
        test_full_maintenance_forecasting,
        test_main_app_import,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        print(f"\n🧪 Running {test.__name__}...")
        try:
            if test.__name__ == 'test_full_maintenance_forecasting':
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
        print("🎉 All maintenance forecasting tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
