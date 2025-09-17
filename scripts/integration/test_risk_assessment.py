#!/usr/bin/env python3
"""Test script for risk assessment functionality in Analysis Service.

Validates that the risk assessor works correctly.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_risk_assessor_import():
    """Test that the risk assessor module can be imported."""
    try:
        from services.analysis_service.modules.risk_assessor import RiskAssessor, assess_document_risk
        print("✅ Risk assessor module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import risk assessor module: {e}")
        return False

def test_risk_assessor_initialization():
    """Test that the risk assessor can be initialized."""
    try:
        from services.analysis_service.modules.risk_assessor import RiskAssessor

        assessor = RiskAssessor()
        print("✅ RiskAssessor initialized successfully")
        print(f"   Initialized: {assessor.initialized}")
        print(f"   Risk factors: {len(assessor.risk_factors)} configured")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize risk assessor: {e}")
        return False

def test_risk_factor_calculation():
    """Test risk factor score calculations."""
    try:
        from services.analysis_service.modules.risk_assessor import RiskAssessor

        assessor = RiskAssessor()

        # Test linear increase (higher values = higher risk)
        age_score = assessor._calculate_risk_factor_score('document_age', 200, assessor.risk_factors['document_age'])
        print("✅ Risk factor calculation working")
        print(f"   Document age (200 days): {age_score:.2f} (should be > 0.5)")

        # Test inverse linear (lower values = higher risk)
        quality_score = assessor._calculate_risk_factor_score('quality_score', 0.6, assessor.risk_factors['quality_score'])
        print(f"   Quality score (0.6): {quality_score:.2f} (should be moderate risk)")

        # Test categorical
        impact_score = assessor._calculate_risk_factor_score('stakeholder_impact', 'critical', assessor.risk_factors['stakeholder_impact'])
        print(f"   Stakeholder impact (critical): {impact_score:.2f} (should be > 0.5)")

        return True
    except Exception as e:
        print(f"❌ Risk factor calculation failed: {e}")
        return False

def test_individual_risk_assessment():
    """Test individual risk factor assessment."""
    try:
        from services.analysis_service.modules.risk_assessor import RiskAssessor

        assessor = RiskAssessor()

        # Create sample document data
        document_data = {
            'document_id': 'test_doc',
            'document_type': 'api_reference',
            'content': 'API documentation with technical content...',
            'last_modified': (datetime.now() - timedelta(days=120)).isoformat(),
            'quality_score': 0.7,
            'complexity_score': 0.8,
            'stakeholder_impact': 'high',
            'usage_frequency': 200
        }

        risk_scores = assessor._assess_individual_risks(document_data)

        print("✅ Individual risk assessment working")
        print(f"   Risk factors assessed: {len(risk_scores)}")

        # Show a few key factors
        for factor in ['document_age', 'quality_score', 'complexity_score', 'stakeholder_impact']:
            if factor in risk_scores:
                score_data = risk_scores[factor]
                print(".2f"
                      f"(weight: {score_data['weight']:.2f})")

        return True
    except Exception as e:
        print(f"❌ Individual risk assessment failed: {e}")
        return False

def test_overall_risk_calculation():
    """Test overall risk score calculation."""
    try:
        from services.analysis_service.modules.risk_assessor import RiskAssessor

        assessor = RiskAssessor()

        # Create mock risk scores
        risk_scores = {
            'document_age': {'risk_score': 0.8, 'weight': 0.15},
            'quality_score': {'risk_score': 0.6, 'weight': 0.18},
            'complexity_score': {'risk_score': 0.7, 'weight': 0.20},
            'stakeholder_impact': {'risk_score': 0.9, 'weight': 0.12},
            'change_frequency': {'risk_score': 0.4, 'weight': 0.10},
            'finding_density': {'risk_score': 0.5, 'weight': 0.08},
            'trend_decline': {'risk_score': 0.3, 'weight': 0.10},
            'usage_frequency': {'risk_score': 0.2, 'weight': 0.05}
        }

        overall_risk = assessor._calculate_overall_risk_score(risk_scores)

        print("✅ Overall risk calculation working")
        print(f"   Overall risk score: {overall_risk['overall_score']:.3f}")
        print(f"   Risk level: {overall_risk['risk_level']}")
        print(f"   Weighted sum: {overall_risk['weighted_sum']:.3f}")
        print(f"   Total weight: {overall_risk['total_weight']:.3f}")

        return True
    except Exception as e:
        print(f"❌ Overall risk calculation failed: {e}")
        return False

def test_risk_recommendations():
    """Test risk recommendation generation."""
    try:
        from services.analysis_service.modules.risk_assessor import RiskAssessor

        assessor = RiskAssessor()

        # Test high-risk scenario
        high_risk_scores = {
            'document_age': {'risk_score': 0.9, 'value': 300},
            'quality_score': {'risk_score': 0.8, 'value': 0.5}
        }
        high_risk_overall = {'risk_level': 'high'}

        recommendations = assessor._generate_risk_recommendations(high_risk_scores, high_risk_overall)

        print("✅ Risk recommendations working")
        print(f"   Recommendations for high-risk scenario ({len(recommendations)}):")
        for i, rec in enumerate(recommendations[:3]):
            print(f"     {i+1}. {rec}")

        # Test low-risk scenario
        low_risk_scores = {
            'document_age': {'risk_score': 0.2, 'value': 30},
            'quality_score': {'risk_score': 0.1, 'value': 0.9}
        }
        low_risk_overall = {'risk_level': 'low'}

        low_recommendations = assessor._generate_risk_recommendations(low_risk_scores, low_risk_overall)

        print(f"   Recommendations for low-risk scenario ({len(low_recommendations)}):")
        for i, rec in enumerate(low_recommendations[:2]):
            print(f"     {i+1}. {rec}")

        return True
    except Exception as e:
        print(f"❌ Risk recommendations failed: {e}")
        return False

def test_risk_drivers_identification():
    """Test identification of risk drivers."""
    try:
        from services.analysis_service.modules.risk_assessor import RiskAssessor

        assessor = RiskAssessor()

        risk_scores = {
            'document_age': {'risk_score': 0.9, 'weight': 0.15, 'description': 'Document age'},
            'quality_score': {'risk_score': 0.8, 'weight': 0.18, 'description': 'Quality score'},
            'complexity_score': {'risk_score': 0.7, 'weight': 0.20, 'description': 'Complexity'},
            'stakeholder_impact': {'risk_score': 0.6, 'weight': 0.12, 'description': 'Stakeholder impact'},
            'change_frequency': {'risk_score': 0.4, 'weight': 0.10, 'description': 'Change frequency'},
            'finding_density': {'risk_score': 0.5, 'weight': 0.08, 'description': 'Finding density'},
            'trend_decline': {'risk_score': 0.3, 'weight': 0.10, 'description': 'Trend decline'},
            'usage_frequency': {'risk_score': 0.2, 'weight': 0.05, 'description': 'Usage frequency'}
        }

        risk_drivers = assessor._identify_risk_drivers(risk_scores)

        print("✅ Risk drivers identification working")
        print(f"   Top risk drivers ({len(risk_drivers)}):")
        for i, driver in enumerate(risk_drivers[:3]):
            print(".3f"
                  f"(score: {driver['risk_score']:.2f}, weight: {driver['weight']:.2f})")

        return True
    except Exception as e:
        print(f"❌ Risk drivers identification failed: {e}")
        return False

async def test_full_risk_assessment():
    """Test the complete risk assessment pipeline."""
    try:
        from services.analysis_service.modules.risk_assessor import RiskAssessor

        assessor = RiskAssessor()

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

            ## Rate Limits
            - 1000 requests/hour for authenticated users
            - 100 requests/hour for anonymous users

            ## Changelog
            - v2.1.0: Added bulk operations
            - v2.0.0: Major API redesign
            - v1.5.0: Enhanced security
            - v1.0.0: Initial release
            ''',
            'last_modified': (datetime.now() - timedelta(days=90)).isoformat(),
            'author': 'api_team',
            'quality_score': 0.75,
            'complexity_score': 0.7,
            'usage_frequency': 300,
            'stakeholder_impact': 'high'
        }

        # Create analysis history
        analysis_history = [
            {
                'timestamp': (datetime.now() - timedelta(days=60)).isoformat(),
                'quality_score': 0.8,
                'total_findings': 4,
                'critical_findings': 0,
                'high_findings': 2
            },
            {
                'timestamp': (datetime.now() - timedelta(days=30)).isoformat(),
                'quality_score': 0.78,
                'total_findings': 6,
                'critical_findings': 1,
                'high_findings': 2
            },
            {
                'timestamp': (datetime.now() - timedelta(days=7)).isoformat(),
                'quality_score': 0.75,
                'total_findings': 8,
                'critical_findings': 2,
                'high_findings': 3
            }
        ]

        result = await assessor.assess_document_risk(
            document_id="comprehensive_test_doc",
            document_data=document_data,
            analysis_history=analysis_history
        )

        print("✅ Full risk assessment pipeline working")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Overall risk score: {result['overall_risk']['overall_score']:.3f}")
        print(f"   Risk level: {result['overall_risk']['risk_level']}")
        print(f"   Risk drivers: {len(result['risk_drivers'])}")
        print(f"   Recommendations: {len(result['recommendations'])}")
        print(f"   Processing time: {result['processing_time']:.2f}s")

        if result['risk_drivers']:
            print(f"   Top risk drivers:")
            for i, driver in enumerate(result['risk_drivers'][:2]):
                print(".3f")

        if result['recommendations']:
            print(f"   Key recommendations:")
            for i, rec in enumerate(result['recommendations'][:2]):
                print(f"     {i+1}. {rec}")

        return True
    except Exception as e:
        print(f"❌ Full risk assessment failed: {e}")
        return False

def test_main_app_import():
    """Test that the main app can be imported with risk assessment endpoints."""
    try:
        from services.analysis_service.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        risk_routes = [r for r in routes if 'risk' in r]

        print("✅ Main app imported successfully")
        print(f"✅ Found {len(risk_routes)} risk assessment routes:")
        for route in risk_routes:
            print(f"   - {route}")

        return True
    except Exception as e:
        print(f"❌ Failed to import main app: {e}")
        return False

def main():
    """Run all tests."""
    print("🛡️  Testing Risk Assessment Functionality")
    print("=" * 60)

    tests = [
        test_risk_assessor_import,
        test_risk_assessor_initialization,
        test_risk_factor_calculation,
        test_individual_risk_assessment,
        test_overall_risk_calculation,
        test_risk_recommendations,
        test_risk_drivers_identification,
        test_full_risk_assessment,
        test_main_app_import,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        print(f"\n🧪 Running {test.__name__}...")
        try:
            if test.__name__ == 'test_full_risk_assessment':
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
        print("🎉 All risk assessment tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
