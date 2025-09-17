#!/usr/bin/env python3
"""Test script for peer review enhancement functionality in Summarizer Hub.

Validates that the peer review enhancer works correctly.
"""

import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_peer_review_enhancer_import():
    """Test that the peer review enhancer module can be imported."""
    try:
        from services.summarizer_hub.modules.peer_review_enhancer import PeerReviewEnhancer, review_documentation
        print("✅ Peer review enhancer module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import peer review enhancer module: {e}")
        return False

def test_peer_review_enhancer_initialization():
    """Test that the peer review enhancer can be initialized."""
    try:
        from services.summarizer_hub.modules.peer_review_enhancer import PeerReviewEnhancer

        enhancer = PeerReviewEnhancer()
        print("✅ PeerReviewEnhancer initialized successfully")
        print(f"   Initialized: {enhancer.initialized}")
        print(f"   Quality criteria: {len(enhancer.quality_criteria)} defined")
        print(f"   Best practices: {len(enhancer.best_practices)} categories")
        print(f"   Review categories: {len(enhancer.review_categories)} types")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize peer review enhancer: {e}")
        return False

def test_document_feature_extraction():
    """Test extraction of document features."""
    try:
        from services.summarizer_hub.modules.peer_review_enhancer import PeerReviewEnhancer

        enhancer = PeerReviewEnhancer()

        # Create sample document data
        document_data = {
            'document_id': 'test_api_doc',
            'title': 'API Developer Guide',
            'document_type': 'api_reference',
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

        features = enhancer._extract_document_features(document_data)

        print("✅ Document feature extraction working")
        print(f"   Document ID: {features['document_id']}")
        print(f"   Document type: {features['document_type']}")
        print(f"   Word count: {features['word_count']}")
        print(f"   Character count: {features['character_count']}")
        print(f"   Code blocks: {features['code_blocks']}")
        print(f"   Links: {features['links']}")
        print(f"   Headings: {features['headings']}")
        print(f"   API endpoints: {features['api_endpoints']}")
        print(f"   Technical terms: {len(features['technical_terms'])}")
        print(f"   Stakeholder groups: {len(features['stakeholder_groups'])}")

        return True
    except Exception as e:
        print(f"❌ Document feature extraction failed: {e}")
        return False

def test_stakeholder_identification():
    """Test stakeholder group identification."""
    try:
        from services.summarizer_hub.modules.peer_review_enhancer import PeerReviewEnhancer

        enhancer = PeerReviewEnhancer()

        # Test different document types
        api_doc = {
            'document_id': 'api_doc',
            'document_type': 'api_reference',
            'content': 'API documentation for developers with endpoints and authentication'
        }

        user_doc = {
            'document_id': 'user_doc',
            'document_type': 'user_guide',
            'content': 'User guide for end users to get started with the platform'
        }

        security_doc = {
            'document_id': 'security_doc',
            'document_type': 'security',
            'content': 'Security best practices and compliance guidelines'
        }

        stakeholders_api = enhancer._identify_stakeholder_groups(api_doc)
        stakeholders_user = enhancer._identify_stakeholder_groups(user_doc)
        stakeholders_security = enhancer._identify_stakeholder_groups(security_doc)

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

def test_content_completeness_analysis():
    """Test content completeness analysis."""
    try:
        from services.summarizer_hub.modules.peer_review_enhancer import PeerReviewEnhancer

        enhancer = PeerReviewEnhancer()

        # Test API reference completeness
        api_content = '''
        # API Reference

        ## Authentication
        Use OAuth 2.0...

        ## Endpoints
        - GET /users
        - POST /users

        ## Error Handling
        The API returns standard HTTP status codes...
        '''

        completeness = enhancer._analyze_content_completeness(api_content, 'api_reference')

        print("✅ Content completeness analysis working")
        print(f"   Completeness score: {completeness['score']:.2f}")
        print(f"   Issues found: {len(completeness['issues'])}")
        print(f"   Suggestions provided: {len(completeness['suggestions'])}")

        if completeness['issues']:
            print("   Issues:")
            for issue in completeness['issues'][:2]:
                print(f"     - {issue}")

        if completeness['suggestions']:
            print("   Suggestions:")
            for suggestion in completeness['suggestions'][:2]:
                print(f"     - {suggestion}")

        return True
    except Exception as e:
        print(f"❌ Content completeness analysis failed: {e}")
        return False

def test_technical_accuracy_analysis():
    """Test technical accuracy analysis."""
    try:
        from services.summarizer_hub.modules.peer_review_enhancer import PeerReviewEnhancer

        enhancer = PeerReviewEnhancer()

        # Test technical accuracy
        technical_content = '''
        # API Guide

        ## Authentication
        Use OAuth 2.0 for authentication. Send POST request to /oauth/token.

        ## Endpoints
        - GET /users - List users
        - POST /users - Create user

        ## Rate Limiting
        API requests are limited to 1000 per hour for authenticated users.
        '''

        accuracy = enhancer._analyze_technical_accuracy(technical_content)

        print("✅ Technical accuracy analysis working")
        print(f"   Accuracy score: {accuracy['score']:.2f}")
        print(f"   Issues found: {len(accuracy['issues'])}")
        print(f"   Suggestions provided: {len(accuracy['suggestions'])}")

        if accuracy['issues']:
            print("   Issues:")
            for issue in accuracy['issues'][:2]:
                print(f"     - {issue}")

        if accuracy['suggestions']:
            print("   Suggestions:")
            for suggestion in accuracy['suggestions'][:2]:
                print(f"     - {suggestion}")

        return True
    except Exception as e:
        print(f"❌ Technical accuracy analysis failed: {e}")
        return False

def test_clarity_readability_analysis():
    """Test clarity and readability analysis."""
    try:
        from services.summarizer_hub.modules.peer_review_enhancer import PeerReviewEnhancer

        enhancer = PeerReviewEnhancer()

        # Test readability
        readable_content = '''
        # Getting Started Guide

        Welcome to our platform! This guide will help you get started quickly and easily.

        ## Step 1: Create Your Account
        First, you'll need to create an account. Click the "Sign Up" button on the homepage.

        ## Step 2: Verify Your Email
        After signing up, check your email for a verification link and click it.

        ## Step 3: Log In
        Once verified, return to the platform and log in with your credentials.
        '''

        clarity = enhancer._analyze_clarity_and_readability(readable_content)

        print("✅ Clarity and readability analysis working")
        print(f"   Clarity score: {clarity['score']:.2f}")
        print(f"   Issues found: {len(clarity['issues'])}")
        print(f"   Suggestions provided: {len(clarity['suggestions'])}")

        if clarity['issues']:
            print("   Issues:")
            for issue in clarity['issues'][:2]:
                print(f"     - {issue}")

        if clarity['suggestions']:
            print("   Suggestions:")
            for suggestion in clarity['suggestions'][:2]:
                print(f"     - {suggestion}")

        return True
    except Exception as e:
        print(f"❌ Clarity and readability analysis failed: {e}")
        return False

def test_structure_organization_analysis():
    """Test structure and organization analysis."""
    try:
        from services.summarizer_hub.modules.peer_review_enhancer import PeerReviewEnhancer

        enhancer = PeerReviewEnhancer()

        # Test document structure
        structured_content = '''
        # User Guide

        ## Introduction
        Welcome to our platform!

        ## Getting Started
        Here's how to get started...

        ### Prerequisites
        Before you begin...

        ### Installation
        Install the software...

        ## Basic Usage
        Learn the basic features...

        ## Advanced Features
        Explore advanced capabilities...

        ## Troubleshooting
        Common issues and solutions...

        ## Next Steps
        What's next after getting started...
        '''

        structure = enhancer._analyze_structure_and_organization(structured_content)

        print("✅ Structure and organization analysis working")
        print(f"   Structure score: {structure['score']:.2f}")
        print(f"   Issues found: {len(structure['issues'])}")
        print(f"   Suggestions provided: {len(structure['suggestions'])}")

        if structure['issues']:
            print("   Issues:")
            for issue in structure['issues'][:2]:
                print(f"     - {issue}")

        if structure['suggestions']:
            print("   Suggestions:")
            for suggestion in structure['suggestions'][:2]:
                print(f"     - {suggestion}")

        return True
    except Exception as e:
        print(f"❌ Structure and organization analysis failed: {e}")
        return False

def test_overall_review_score_calculation():
    """Test overall review score calculation."""
    try:
        from services.summarizer_hub.modules.peer_review_enhancer import PeerReviewEnhancer

        enhancer = PeerReviewEnhancer()

        # Mock criteria scores
        criteria_scores = {
            'completeness': 0.8,
            'accuracy': 0.9,
            'clarity': 0.7,
            'structure': 0.85,
            'compliance': 0.9,
            'engagement': 0.75
        }

        overall_score = enhancer._generate_overall_review_score(criteria_scores)

        print("✅ Overall review score calculation working")
        print(f"   Overall score: {overall_score['overall_score']:.2f}")
        print(f"   Grade: {overall_score['grade']}")
        print(f"   Description: {overall_score['description']}")

        # Calculate expected score manually
        expected_score = (
            0.8 * 0.25 +  # completeness
            0.9 * 0.20 +  # accuracy
            0.7 * 0.18 +  # clarity
            0.85 * 0.15 + # structure
            0.9 * 0.12 +  # compliance
            0.75 * 0.10   # engagement
        )

        print(f"   Expected score: {expected_score:.2f}")
        assert abs(overall_score['overall_score'] - expected_score) < 0.01

        return True
    except Exception as e:
        print(f"❌ Overall review score calculation failed: {e}")
        return False

def test_review_feedback_generation():
    """Test review feedback generation."""
    try:
        from services.summarizer_hub.modules.peer_review_enhancer import PeerReviewEnhancer

        enhancer = PeerReviewEnhancer()

        # Mock criteria analyses and overall assessment
        criteria_analyses = {
            'completeness': {
                'score': 0.8,
                'issues': ['Missing troubleshooting section'],
                'suggestions': ['Consider adding a troubleshooting section']
            },
            'accuracy': {
                'score': 0.9,
                'issues': [],
                'suggestions': ['Consider adding version information']
            }
        }

        overall_assessment = {
            'overall_score': 0.82,
            'grade': 'B',
            'description': 'Good documentation quality'
        }

        feedback = enhancer._generate_review_feedback(criteria_analyses, overall_assessment)

        print("✅ Review feedback generation working")
        print(f"   Feedback items generated: {len(feedback)}")

        for i, item in enumerate(feedback[:3]):
            print(f"   {i+1}. [{item['priority']}] {item['title']}")
            print(f"      {item['message'][:100]}...")

        # Should have overall assessment feedback
        assert any(item['type'] == 'overall_assessment' for item in feedback)
        # Should have issue feedback
        assert any(item['type'] == 'issue' for item in feedback)
        # Should have suggestion feedback
        assert any(item['type'] == 'suggestion' for item in feedback)

        return True
    except Exception as e:
        print(f"❌ Review feedback generation failed: {e}")
        return False

async def test_full_peer_review_analysis():
    """Test the complete peer review analysis pipeline."""
    try:
        from services.summarizer_hub.modules.peer_review_enhancer import PeerReviewEnhancer

        enhancer = PeerReviewEnhancer()

        # Create comprehensive test document
        test_content = '''
        # API Developer Guide

        This comprehensive guide covers the REST API for our platform.

        ## Authentication
        The API uses OAuth 2.0 for authentication. You need to obtain an access token
        by sending a POST request to /oauth/token with your client credentials.

        ## Core Endpoints

        ### GET /users
        Retrieves a paginated list of users.

        **Parameters:**
        - limit (integer): Maximum number of users to return (default: 100)
        - offset (integer): Number of users to skip (default: 0)

        ### POST /users
        Creates a new user account.

        **Request Body:**
        ```json
        {
          "name": "Jane Smith",
          "email": "jane@example.com",
          "role": "user"
        }
        ```

        ## Error Handling
        The API returns standard HTTP status codes:
        - 200 OK: Success
        - 400 Bad Request: Invalid request
        - 401 Unauthorized: Authentication required
        - 500 Internal Server Error: Server error

        ## Rate Limiting
        API requests are limited to 1000 per hour for authenticated users.
        '''

        result = await enhancer.review_documentation(
            content=test_content,
            doc_type='api_reference',
            title='API Developer Guide v1.0'
        )

        print("✅ Full peer review analysis pipeline working")
        print(f"   Document title: {result['document_title']}")
        print(f"   Document type: {result['document_type']}")
        print(f"   Overall score: {result['overall_assessment']['overall_score']:.2f}")
        print(f"   Grade: {result['overall_assessment']['grade']}")
        print(f"   Description: {result['overall_assessment']['description']}")
        print(f"   Processing time: {result['processing_time']:.2f}s")

        # Check criteria scores
        criteria_scores = result['criteria_scores']
        print(f"   Criteria scores:")
        for criterion, score in criteria_scores.items():
            print(f"     {criterion}: {score:.2f}")

        # Check feedback
        feedback = result['feedback']
        print(f"   Feedback generated: {len(feedback)} items")

        # Check review summary
        summary = result['review_summary']
        print(f"   Review summary:")
        print(f"     Grade: {summary['grade']}")
        print(f"     Issues found: {summary['issues_found']}")
        print(f"     Suggestions provided: {summary['suggestions_provided']}")
        print(f"     Improvement roadmap: {summary['improvement_roadmap']}")

        # Show some feedback items
        print(f"   Sample feedback:")
        for i, item in enumerate(feedback[:3]):
            print(f"     {i+1}. [{item['priority']}] {item['title']}")

        return True
    except Exception as e:
        print(f"❌ Full peer review analysis failed: {e}")
        return False

async def test_document_version_comparison():
    """Test document version comparison."""
    try:
        from services.summarizer_hub.modules.peer_review_enhancer import PeerReviewEnhancer

        enhancer = PeerReviewEnhancer()

        # Old version (less comprehensive)
        old_content = '''
        # API Guide

        ## Authentication
        Use OAuth 2.0...

        ## Endpoints
        - GET /users
        - POST /users
        '''

        # New version (more comprehensive)
        new_content = '''
        # API Developer Guide v2.0

        This comprehensive guide covers the REST API for our platform.

        ## Authentication
        The API uses OAuth 2.0 for authentication. You need to obtain an access token
        by sending a POST request to /oauth/token with your client credentials.

        ## Core Endpoints

        ### GET /users
        Retrieves a paginated list of users.

        **Parameters:**
        - limit (integer): Maximum number of users to return (default: 100)
        - offset (integer): Number of users to skip (default: 0)

        ### POST /users
        Creates a new user account.

        **Request Body:**
        ```json
        {
          "name": "Jane Smith",
          "email": "jane@example.com",
          "role": "user"
        }
        ```

        ## Error Handling
        The API returns standard HTTP status codes...

        ## Rate Limiting
        API requests are limited to 1000 per hour...
        '''

        result = await enhancer.compare_document_versions(
            old_content=old_content,
            new_content=new_content,
            doc_type='api_reference'
        )

        print("✅ Document version comparison working")
        print(f"   Old version score: {result['comparison']['old_version']['score']:.2f}")
        print(f"   Old version grade: {result['comparison']['old_version']['grade']}")
        print(f"   New version score: {result['comparison']['new_version']['score']:.2f}")
        print(f"   New version grade: {result['comparison']['new_version']['grade']}")
        print(f"   Score improvement: {result['comparison']['improvement']['score_change']:.2f}")
        print(f"   Grade change: {result['comparison']['improvement']['grade_change']}")
        print(f"   Processing time: {result['processing_time']:.2f}s")

        # Show improvements
        improvements = result['comparison'].get('improvements', [])
        if improvements:
            print(f"   Improvements identified: {len(improvements)}")
            for i, improvement in enumerate(improvements[:2]):
                print(f"     {i+1}. {improvement}")

        # Show regressions (if any)
        regressions = result['comparison'].get('regressions', [])
        if regressions:
            print(f"   Regressions identified: {len(regressions)}")
            for i, regression in enumerate(regressions[:2]):
                print(f"     {i+1}. {regression}")

        return True
    except Exception as e:
        print(f"❌ Document version comparison failed: {e}")
        return False

def test_summarizer_hub_main_import():
    """Test that the summarizer hub main module can be imported with peer review endpoints."""
    try:
        from services.summarizer_hub.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        review_routes = [r for r in routes if 'review' in r]

        print("✅ Summarizer hub main module imported successfully")
        print(f"✅ Found {len(review_routes)} peer review routes:")
        for route in review_routes:
            print(f"   - {route}")

        return True
    except Exception as e:
        print(f"❌ Failed to import summarizer hub main module: {e}")
        return False

def main():
    """Run all tests."""
    print("🤖 Testing Peer Review Enhancement Functionality")
    print("=" * 65)

    tests = [
        test_peer_review_enhancer_import,
        test_peer_review_enhancer_initialization,
        test_document_feature_extraction,
        test_stakeholder_identification,
        test_content_completeness_analysis,
        test_technical_accuracy_analysis,
        test_clarity_readability_analysis,
        test_structure_organization_analysis,
        test_overall_review_score_calculation,
        test_review_feedback_generation,
        test_full_peer_review_analysis,
        test_document_version_comparison,
        test_summarizer_hub_main_import,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        print(f"\n🧪 Running {test.__name__}...")
        try:
            if test.__name__ in ['test_full_peer_review_analysis', 'test_document_version_comparison']:
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
        print("🎉 All peer review enhancement tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
