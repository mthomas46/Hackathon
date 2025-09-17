#!/usr/bin/env python3
"""Test script for change impact analysis functionality in Analysis Service.

Validates that the change impact analyzer works correctly.
"""

import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_change_impact_analyzer_import():
    """Test that the change impact analyzer module can be imported."""
    try:
        from services.analysis_service.modules.change_impact_analyzer import ChangeImpactAnalyzer, analyze_change_impact
        print("✅ Change impact analyzer module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import change impact analyzer module: {e}")
        return False

def test_change_impact_analyzer_initialization():
    """Test that the change impact analyzer can be initialized."""
    try:
        from services.analysis_service.modules.change_impact_analyzer import ChangeImpactAnalyzer

        analyzer = ChangeImpactAnalyzer()
        print("✅ ChangeImpactAnalyzer initialized successfully")
        print(f"   Initialized: {analyzer.initialized}")
        print(f"   Impact thresholds: {len(analyzer.impact_thresholds)} configured")
        print(f"   Relationship types: {len(analyzer.relationship_types)} defined")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize change impact analyzer: {e}")
        return False

def test_extract_document_features():
    """Test extraction of document features."""
    try:
        from services.analysis_service.modules.change_impact_analyzer import ChangeImpactAnalyzer

        analyzer = ChangeImpactAnalyzer()

        # Create sample document data
        document_data = {
            'document_id': 'test_api_doc',
            'title': 'API Developer Guide',
            'document_type': 'developer_guide',
            'content': '''
            # API Developer Guide

            This guide covers REST API usage, authentication, and best practices.

            ## Authentication
            Use OAuth 2.0 with client credentials...

            ## Endpoints
            - GET /users - List users
            - POST /users - Create user
            - PUT /users/{id} - Update user

            ## Error Handling
            The API returns standard HTTP status codes...
            ''',
            'tags': ['api', 'rest', 'authentication'],
            'last_modified': datetime.now().isoformat()
        }

        features = analyzer._extract_document_features(document_data)

        print("✅ Document features extraction working")
        print(f"   Document ID: {features['document_id']}")
        print(f"   Document type: {features['document_type']}")
        print(f"   Word count: {features['word_count']}")
        print(f"   Character count: {features['character_count']}")
        print(f"   Technical terms: {len(features['technical_terms'])}")
        print(f"   Stakeholder groups: {len(features['stakeholder_groups'])}")
        print(f"   Links: {features['links']}")
        print(f"   API endpoints: {features['api_endpoints']}")

        return True
    except Exception as e:
        print(f"❌ Document features extraction failed: {e}")
        return False

def test_stakeholder_identification():
    """Test stakeholder group identification."""
    try:
        from services.analysis_service.modules.change_impact_analyzer import ChangeImpactAnalyzer

        analyzer = ChangeImpactAnalyzer()

        # Test different document types
        api_doc = {
            'document_id': 'api_doc',
            'document_type': 'api_reference',
            'content': 'API documentation for developers',
            'tags': ['api', 'developers']
        }

        user_doc = {
            'document_id': 'user_doc',
            'document_type': 'user_guide',
            'content': 'User guide for end users',
            'tags': ['guide', 'users']
        }

        security_doc = {
            'document_id': 'security_doc',
            'document_type': 'security',
            'content': 'Security best practices',
            'tags': ['security', 'compliance']
        }

        stakeholders_api = analyzer._identify_stakeholder_groups(api_doc)
        stakeholders_user = analyzer._identify_stakeholder_groups(user_doc)
        stakeholders_security = analyzer._identify_stakeholder_groups(security_doc)

        print("✅ Stakeholder identification working")
        print(f"   API document stakeholders: {stakeholders_api}")
        print(f"   User guide stakeholders: {stakeholders_user}")
        print(f"   Security document stakeholders: {stakeholders_security}")

        # API docs should include developers
        assert 'developers' in stakeholders_api
        # User guides should include end users
        assert 'end_users' in stakeholders_user
        # Security docs should include security compliance
        assert 'security_compliance' in stakeholders_security

        return True
    except Exception as e:
        print(f"❌ Stakeholder identification failed: {e}")
        return False

def test_semantic_similarity_analysis():
    """Test semantic similarity analysis."""
    try:
        from services.analysis_service.modules.change_impact_analyzer import ChangeImpactAnalyzer

        analyzer = ChangeImpactAnalyzer()

        # Create similar documents
        source_doc = {
            'document_id': 'source',
            'content': 'API authentication using OAuth 2.0 with client credentials flow'
        }

        related_docs = [
            {
                'document_id': 'related1',
                'content': 'OAuth 2.0 authentication for API access with client credentials'
            },
            {
                'document_id': 'related2',
                'content': 'User management and profile information retrieval'
            }
        ]

        similarities = analyzer._analyze_semantic_similarity(source_doc, related_docs)

        print("✅ Semantic similarity analysis working")
        print(f"   Documents analyzed: {len(similarities)}")
        print(f"   Similarity scores:")

        for doc_id, similarity_data in similarities.items():
            print(f"     {doc_id}: {similarity_data['similarity_score']:.3f} ({similarity_data['similarity_level']})")

        # Should have high similarity for the first related document
        if similarities:
            first_doc = list(similarities.keys())[0]
            assert similarities[first_doc]['similarity_score'] > 0.5

        return True
    except Exception as e:
        print(f"❌ Semantic similarity analysis failed: {e}")
        return False

def test_relationship_analysis():
    """Test relationship analysis between documents."""
    try:
        from services.analysis_service.modules.change_impact_analyzer import ChangeImpactAnalyzer

        analyzer = ChangeImpactAnalyzer()

        # Create documents with different relationships
        source_doc = {
            'document_id': 'api_guide',
            'document_type': 'developer_guide',
            'content': 'API guide for developers',
            'tags': ['api', 'guide']
        }

        related_docs = [
            {
                'document_id': 'api_reference',
                'document_type': 'api_reference',
                'content': 'API reference documentation',
                'tags': ['api', 'reference']
            },
            {
                'document_id': 'tutorial',
                'document_type': 'tutorial',
                'content': 'Getting started tutorial',
                'tags': ['tutorial', 'getting-started']
            }
        ]

        relationships = analyzer._analyze_relationships(source_doc, related_docs)

        print("✅ Relationship analysis working")
        print(f"   Relationships identified: {len(relationships)}")

        for doc_id, relationship_data in relationships.items():
            print(f"     {doc_id}:")
            print(f"       Relationship: {relationship_data['primary_relationship']}")
            print(f"       Score: {relationship_data['relationship_score']:.3f}")
            print(f"       Factors: {relationship_data['relationship_factors']}")

        return True
    except Exception as e:
        print(f"❌ Relationship analysis failed: {e}")
        return False

def test_change_severity_assessment():
    """Test change severity assessment."""
    try:
        from services.analysis_service.modules.change_impact_analyzer import ChangeImpactAnalyzer

        analyzer = ChangeImpactAnalyzer()

        # Test different change types
        breaking_change = {
            'change_type': 'breaking_change',
            'change_scope': 'entire_document',
            'description': 'Complete API redesign'
        }

        major_change = {
            'change_type': 'major_change',
            'change_scope': 'major_section',
            'description': 'New authentication flow'
        }

        minor_change = {
            'change_type': 'minor_change',
            'change_scope': 'minor_section',
            'description': 'Updated error messages'
        }

        severity_breaking = analyzer._assess_change_severity(breaking_change)
        severity_major = analyzer._assess_change_severity(major_change)
        severity_minor = analyzer._assess_change_severity(minor_change)

        print("✅ Change severity assessment working")
        print(f"   Breaking change severity: {severity_breaking['severity_level']} ({severity_breaking['severity_score']:.2f})")
        print(f"   Major change severity: {severity_major['severity_level']} ({severity_major['severity_score']:.2f})")
        print(f"   Minor change severity: {severity_minor['severity_level']} ({severity_minor['severity_score']:.2f})")

        # Breaking changes should have highest severity
        assert severity_breaking['severity_score'] > severity_major['severity_score']
        assert severity_major['severity_score'] > severity_minor['severity_score']

        return True
    except Exception as e:
        print(f"❌ Change severity assessment failed: {e}")
        return False

def test_overall_impact_calculation():
    """Test overall impact calculation."""
    try:
        from services.analysis_service.modules.change_impact_analyzer import ChangeImpactAnalyzer

        analyzer = ChangeImpactAnalyzer()

        # Create sample data for impact calculation
        document_features = {
            'document_type': 'api_reference',
            'stakeholder_groups': ['developers', 'administrators'],
            'business_criticality': 'high'
        }

        change_description = {
            'change_type': 'major_change',
            'change_scope': 'major_section'
        }

        # Mock relationships
        relationships = {
            'related_doc_1': {
                'relationship_score': 0.8,
                'primary_relationship': 'dependency',
                'impact_multiplier': 0.8
            },
            'related_doc_2': {
                'relationship_score': 0.6,
                'primary_relationship': 'reference_link',
                'impact_multiplier': 0.7
            }
        }

        impact_analysis = analyzer._calculate_change_impact(
            change_description, document_features, relationships
        )

        print("✅ Overall impact calculation working")
        print(f"   Overall impact score: {impact_analysis['overall_impact']['overall_impact_score']:.3f}")
        print(f"   Impact level: {impact_analysis['overall_impact']['impact_level']}")
        print(f"   Affected documents: {impact_analysis['overall_impact']['affected_documents_count']}")
        print(f"   High impact documents: {impact_analysis['overall_impact']['high_impact_documents_count']}")

        return True
    except Exception as e:
        print(f"❌ Overall impact calculation failed: {e}")
        return False

def test_impact_recommendations():
    """Test impact recommendation generation."""
    try:
        from services.analysis_service.modules.change_impact_analyzer import ChangeImpactAnalyzer

        analyzer = ChangeImpactAnalyzer()

        # Test different impact levels
        critical_impact = {
            'overall_impact': {
                'impact_level': 'critical',
                'affected_documents_count': 8,
                'high_impact_documents_count': 5
            },
            'document_impacts': {},
            'change_analysis': {'change_type': 'breaking_change'}
        }

        medium_impact = {
            'overall_impact': {
                'impact_level': 'medium',
                'affected_documents_count': 3,
                'high_impact_documents_count': 1
            },
            'document_impacts': {},
            'change_analysis': {'change_type': 'minor_change'}
        }

        recommendations_critical = analyzer._generate_impact_recommendations(critical_impact)
        recommendations_medium = analyzer._generate_impact_recommendations(medium_impact)

        print("✅ Impact recommendations working")
        print(f"   Critical impact recommendations ({len(recommendations_critical)}):")
        for i, rec in enumerate(recommendations_critical[:3]):
            print(f"     {i+1}. {rec}")

        print(f"   Medium impact recommendations ({len(recommendations_medium)}):")
        for i, rec in enumerate(recommendations_medium[:2]):
            print(f"     {i+1}. {rec}")

        # Critical impact should have immediate action recommendations
        assert any('immediate' in rec.lower() or 'critical' in rec.upper() for rec in recommendations_critical)

        return True
    except Exception as e:
        print(f"❌ Impact recommendations failed: {e}")
        return False

async def test_full_change_impact_analysis():
    """Test the complete change impact analysis pipeline."""
    try:
        from services.analysis_service.modules.change_impact_analyzer import ChangeImpactAnalyzer

        analyzer = ChangeImpactAnalyzer()

        # Create comprehensive test data
        document_data = {
            'document_id': 'api_guide_v2',
            'title': 'API Developer Guide v2.0',
            'document_type': 'developer_guide',
            'content': '''
            # API Developer Guide v2.0

            This updated guide covers the new REST API with enhanced authentication,
            improved endpoints, and better error handling.

            ## Authentication (Updated)
            The API now supports OAuth 2.0 and JWT tokens for enhanced security.

            ## New Endpoints
            - GET /users - Enhanced user listing with filters
            - POST /users - User creation with validation
            - PUT /users/{id} - User updates with optimistic locking
            - DELETE /users/{id} - Soft delete with audit trail

            ## Enhanced Error Handling
            Improved error responses with detailed messages and error codes.
            ''',
            'tags': ['api', 'rest', 'authentication', 'developers'],
            'last_modified': datetime.now().isoformat()
        }

        change_description = {
            'change_type': 'major_change',
            'change_scope': 'major_section',
            'description': 'Updated authentication system and added new endpoints',
            'affected_sections': ['Authentication', 'Endpoints'],
            'breaking_change': False,
            'estimated_impact': 'medium'
        }

        related_documents = [
            {
                'document_id': 'api_reference',
                'document_type': 'api_reference',
                'content': 'API reference with endpoint details',
                'tags': ['api', 'reference']
            },
            {
                'document_id': 'tutorial',
                'document_type': 'tutorial',
                'content': 'Getting started tutorial for API usage',
                'tags': ['tutorial', 'getting-started']
            },
            {
                'document_id': 'security_guide',
                'document_type': 'security',
                'content': 'Security best practices for API usage',
                'tags': ['security', 'api']
            }
        ]

        result = await analyzer.analyze_change_impact(
            document_id="api_guide_v2",
            document_data=document_data,
            change_description=change_description,
            related_documents=related_documents
        )

        print("✅ Full change impact analysis pipeline working")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Overall impact score: {result['impact_analysis']['overall_impact']['overall_impact_score']:.3f}")
        print(f"   Impact level: {result['impact_analysis']['overall_impact']['impact_level']}")
        print(f"   Affected documents: {result['impact_analysis']['overall_impact']['affected_documents_count']}")
        print(f"   High impact documents: {result['impact_analysis']['overall_impact']['high_impact_documents_count']}")
        print(f"   Change severity: {result['impact_analysis']['change_analysis']['severity_level']}")
        print(f"   Stakeholder impact: {result['impact_analysis']['overall_impact']['stakeholder_impact']['impact_level']}")
        print(f"   Related documents analyzed: {len(result['related_documents_analysis'])}")
        print(f"   Recommendations generated: {len(result['recommendations'])}")
        print(f"   Processing time: {result['processing_time']:.2f}s")

        if result['recommendations']:
            print(f"   Key recommendations:")
            for i, rec in enumerate(result['recommendations'][:3]):
                print(f"     {i+1}. {rec}")

        if result['related_documents_analysis']:
            print(f"   Top related documents:")
            for doc_id, analysis in list(result['related_documents_analysis'].items())[:2]:
                if 'relationship' in analysis:
                    relationship = analysis['relationship']
                    print(f"     {doc_id}: {relationship['primary_relationship']} (score: {relationship['relationship_score']:.2f})")

        return True
    except Exception as e:
        print(f"❌ Full change impact analysis failed: {e}")
        return False

def test_main_app_import():
    """Test that the main app can be imported with change impact analysis endpoints."""
    try:
        from services.analysis_service.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        impact_routes = [r for r in routes if 'impact' in r]

        print("✅ Main app imported successfully")
        print(f"✅ Found {len(impact_routes)} change impact analysis routes:")
        for route in impact_routes:
            print(f"   - {route}")

        return True
    except Exception as e:
        print(f"❌ Failed to import main app: {e}")
        return False

def main():
    """Run all tests."""
    print("🔗 Testing Change Impact Analysis Functionality")
    print("=" * 65)

    tests = [
        test_change_impact_analyzer_import,
        test_change_impact_analyzer_initialization,
        test_extract_document_features,
        test_stakeholder_identification,
        test_semantic_similarity_analysis,
        test_relationship_analysis,
        test_change_severity_assessment,
        test_overall_impact_calculation,
        test_impact_recommendations,
        test_full_change_impact_analysis,
        test_main_app_import,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        print(f"\n🧪 Running {test.__name__}...")
        try:
            if test.__name__ == 'test_full_change_impact_analysis':
                import asyncio
                result = asyncio.run(test())
            else:
                result = test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        print()

    print("=" * 65)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All change impact analysis tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
