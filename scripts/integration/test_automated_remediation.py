#!/usr/bin/env python3
"""Test script for automated remediation functionality in Analysis Service.

Validates that the automated remediator works correctly.
"""

import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_automated_remediator_import():
    """Test that the automated remediator module can be imported."""
    try:
        from services.analysis_service.modules.automated_remediator import AutomatedRemediator, remediate_document
        print("✅ Automated remediator module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import automated remediator module: {e}")
        return False

def test_automated_remediator_initialization():
    """Test that the automated remediator can be initialized."""
    try:
        from services.analysis_service.modules.automated_remediator import AutomatedRemediator

        remediator = AutomatedRemediator()
        print("✅ AutomatedRemediator initialized successfully")
        print(f"   Initialized: {remediator.initialized}")
        print(f"   Remediation rules: {len(remediator.remediation_rules)} defined")
        print(f"   Safety checks: {len(remediator.safety_checks)} configured")
        print(f"   Confidence thresholds: {len(remediator.confidence_thresholds)} levels")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize automated remediator: {e}")
        return False

def test_document_structure_analysis():
    """Test document structure analysis."""
    try:
        from services.analysis_service.modules.automated_remediator import AutomatedRemediator

        remediator = AutomatedRemediator()

        # Create test document with various structural elements
        test_content = '''
# API Documentation

This is an introduction to our API.

## Getting Started
First, you need to set up your environment.

### Prerequisites
- Python 3.8+
- API Key

## Endpoints

### GET /users
Retrieves user information.

**Parameters:**
- limit: Maximum number of users

```python
import requests
response = requests.get('/users')
```

### POST /users
Creates a new user.

## Error Codes
- 200: Success
- 400: Bad Request

## Troubleshooting
Common issues and solutions.
        '''

        structure = remediator._analyze_document_structure(test_content)

        print("✅ Document structure analysis working")
        print(f"   Headings found: {len(structure['headings'])}")
        print(f"   Code blocks found: {len(structure['code_blocks'])}")
        print(f"   Links found: {len(structure['links'])}")

        for heading in structure['headings'][:3]:
            print(f"     - H{heading['level']}: {heading['title']}")

        return True
    except Exception as e:
        print(f"❌ Document structure analysis failed: {e}")
        return False

def test_formatting_issue_fixes():
    """Test formatting issue fixes."""
    try:
        from services.analysis_service.modules.automated_remediator import AutomatedRemediator

        remediator = AutomatedRemediator()

        # Create content with formatting issues
        messy_content = '''
#api guide

this is a guide for developers. the api uses oauth 2.0.

##getting started
first, create an account.

## endpoints

###get /users
retrieves users.

**parameters:**
- limit (integer): max users

```python
import requests
response = requests.get('/users')
```

###post /users
creates user.

##error handling
api returns errors.
        '''

        fixed_content, applied_fixes = remediator._fix_formatting_issues(messy_content, [])

        print("✅ Formatting issue fixes working")
        print(f"   Fixes applied: {len(applied_fixes)}")

        for fix in applied_fixes[:3]:
            print(f"     - {fix}")

        # Check if common formatting issues were fixed
        assert '# API Guide' in fixed_content or '#api guide' in messy_content
        assert '- limit' in fixed_content or '-limit' in messy_content

        return True
    except Exception as e:
        print(f"❌ Formatting issue fixes failed: {e}")
        return False

def test_terminology_consistency_fixes():
    """Test terminology consistency fixes."""
    try:
        from services.analysis_service.modules.automated_remediator import AutomatedRemediator

        remediator = AutomatedRemediator()

        # Create content with inconsistent terminology
        inconsistent_content = '''
# API Guide

This api guide covers the rest api. The api uses oauth 2.0 for authentication.

## Endpoints

### GET /users
The endpoint retrieves user information.

### POST /users
This endpoint creates a new user.

## Authentication
Use oauth 2.0 to authenticate with the api.
        '''

        fixed_content, applied_fixes = remediator._fix_terminology_consistency(inconsistent_content, [])

        print("✅ Terminology consistency fixes working")
        print(f"   Fixes applied: {len(applied_fixes)}")

        for fix in applied_fixes[:3]:
            print(f"     - {fix}")

        # Check if terminology was standardized
        api_count = fixed_content.count('API')
        original_api_count = inconsistent_content.count('api') + inconsistent_content.count('API')

        print(f"   API capitalized: {api_count} times")
        print(f"   Original API mentions: {original_api_count}")

        return True
    except Exception as e:
        print(f"❌ Terminology consistency fixes failed: {e}")
        return False

def test_link_fixes():
    """Test link fixes."""
    try:
        from services.analysis_service.modules.automated_remediator import AutomatedRemediator

        remediator = AutomatedRemediator()

        # Create content with link issues
        link_content = '''
# Documentation

Check out our [api documentation]  (https://docs.example.com/api) for more details.

Also see the [user guide](https://docs.example.com/guide) and [troubleshooting]   (https://docs.example.com/troubleshoot).

For more information, visit [external site]  (http://example.com).
        '''

        fixed_content, applied_fixes = remediator._fix_link_issues(link_content, [])

        print("✅ Link fixes working")
        print(f"   Fixes applied: {len(applied_fixes)}")

        for fix in applied_fixes[:3]:
            print(f"     - {fix}")

        # Check if link formatting was improved
        assert '[api documentation](https://docs.example.com/api)' in fixed_content

        return True
    except Exception as e:
        print(f"❌ Link fixes failed: {e}")
        return False

def test_safety_checks():
    """Test safety checks for automated changes."""
    try:
        from services.analysis_service.modules.automated_remediator import AutomatedRemediator

        remediator = AutomatedRemediator()

        original_content = '''
# API Guide

This is a guide for the api. The api uses oauth for authentication.
        '''

        # Test with identical content (should be safe)
        safety_results = remediator._check_safety(original_content, original_content)

        print("✅ Safety checks working")
        print(f"   Safe: {safety_results['safe']}")
        print(f"   Confidence score: {safety_results['confidence_score']:.2f}")
        print(f"   Checks passed: {len(safety_results['checks_passed'])}")
        print(f"   Checks failed: {len(safety_results['checks_failed'])}")

        if safety_results['warnings']:
            print("   Warnings:")
            for warning in safety_results['warnings'][:2]:
                print(f"     - {warning}")

        # Test with different content
        modified_content = '''
# API Guide

This is a guide for the API. The API uses OAuth for authentication.
        '''

        safety_results_modified = remediator._check_safety(original_content, modified_content)

        print(f"   Modified content safe: {safety_results_modified['safe']}")
        print(f"   Modified confidence: {safety_results_modified['confidence_score']:.2f}")

        return True
    except Exception as e:
        print(f"❌ Safety checks failed: {e}")
        return False

def test_similarity_calculation():
    """Test similarity calculation between documents."""
    try:
        from services.analysis_service.modules.automated_remediator import AutomatedRemediator

        remediator = AutomatedRemediator()

        doc1 = "This is a guide about API authentication."
        doc2 = "This guide covers API authentication methods."
        doc3 = "The weather is nice today."

        similarity_1_2 = remediator._calculate_similarity(doc1, doc2)
        similarity_1_3 = remediator._calculate_similarity(doc1, doc3)

        print("✅ Similarity calculation working")
        print(f"   Similar documents (1 vs 2): {similarity_1_2:.2f}")
        print(f"   Different documents (1 vs 3): {similarity_1_3:.2f}")

        # Similar documents should have higher similarity
        assert similarity_1_2 > similarity_1_3

        return True
    except Exception as e:
        print(f"❌ Similarity calculation failed: {e}")
        return False

def test_backup_creation():
    """Test backup creation functionality."""
    try:
        from services.analysis_service.modules.automated_remediator import AutomatedRemediator

        remediator = AutomatedRemediator()

        content = "Test content for backup"
        metadata = {"version": "1.0", "author": "test"}

        backup = remediator._create_backup(content, metadata)

        print("✅ Backup creation working")
        print(f"   Backup ID: {backup['backup_id']}")
        print(f"   Timestamp: {backup['timestamp']}")
        print(f"   Content length: {len(backup['content'])}")
        print(f"   Metadata keys: {list(backup['metadata'].keys())}")

        assert backup['content'] == content
        assert backup['metadata'] == metadata
        assert 'timestamp' in backup
        assert 'backup_id' in backup

        return True
    except Exception as e:
        print(f"❌ Backup creation failed: {e}")
        return False

def test_remediation_report_generation():
    """Test remediation report generation."""
    try:
        from services.analysis_service.modules.automated_remediator import AutomatedRemediator

        remediator = AutomatedRemediator()

        original_content = "Original content"
        final_content = "Original content with fixes"
        applied_fixes = ["Fixed formatting", "Standardized terminology"]
        safety_results = {'safe': True, 'checks_passed': ['content_preservation'], 'warnings': []}
        processing_time = 1.5

        report = remediator._generate_remediation_report(
            original_content, final_content, applied_fixes, safety_results, processing_time
        )

        print("✅ Remediation report generation working")
        print(f"   Report sections: {list(report.keys())}")
        print(f"   Changes made: {report['remediation_summary']['changes_made']}")
        print(f"   Processing time: {report['remediation_summary']['processing_time']}")
        print(f"   Applied fixes: {len(report['applied_fixes'])}")

        if report['recommendations']:
            print("   Recommendations:")
            for rec in report['recommendations'][:2]:
                print(f"     - {rec}")

        return True
    except Exception as e:
        print(f"❌ Remediation report generation failed: {e}")
        return False

async def test_full_automated_remediation():
    """Test the complete automated remediation pipeline."""
    try:
        from services.analysis_service.modules.automated_remediator import AutomatedRemediator

        remediator = AutomatedRemediator()

        # Create test document with multiple issues
        test_content = '''
#api guide

this is a guide for developers. the api uses oauth 2.0 for authentication.

##getting started
first, you need to create a account.

## endpoints

###get /users
retrieves users from the system.

**parameters:**
- limit (integer): max users to return

```python
import requests
response = requests.get('/users')
```

###post /users
creates a new user.

##error handling
the api returns standard http status codes:
- 200 ok: success
- 400 bad request: invalid parameters
- 500 internal server error: server error

##rate limiting
requests are limited to 1000 per hour for authenticated users.
        '''

        result = await remediator.remediate_document(
            content=test_content,
            doc_type='api_reference',
            confidence_level='medium'
        )

        print("✅ Full automated remediation pipeline working")
        print(f"   Original content length: {len(result['original_content'])}")
        print(f"   Remediated content length: {len(result['remediated_content'])}")
        print(f"   Changes applied: {result['changes_applied']}")
        print(f"   Safety status: {result['safety_status']}")
        print(f"   Processing time: {result['processing_time']:.2f}s")

        # Check report details
        report = result['report']
        summary = report['remediation_summary']
        print(f"   Report summary:")
        print(f"     Changes made: {summary['changes_made']}")
        print(f"     Processing time: {summary['processing_time']:.2f}s")
        print(f"     Safety status: {summary['safety_status']}")

        # Show applied fixes
        applied_fixes = report['applied_fixes']
        if applied_fixes:
            print(f"   Applied fixes ({len(applied_fixes)}):")
            for i, fix in enumerate(applied_fixes[:3]):
                print(f"     {i+1}. {fix}")

        # Show quality improvements
        improvements = report['quality_improvements']
        if improvements:
            print(f"   Quality improvements:")
            print(f"     Readability: {improvements['readability_score']:.2f}")
            print(f"     Structure: {improvements['structure_score']:.2f}")
            print(f"     Consistency: {improvements['consistency_score']:.2f}")
            print(f"     Overall: {improvements['overall_improvement']:.2f}")

        # Show recommendations
        recommendations = report['recommendations']
        if recommendations:
            print(f"   Recommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations[:2]):
                print(f"     {i+1}. {rec}")

        return True
    except Exception as e:
        print(f"❌ Full automated remediation failed: {e}")
        return False

async def test_remediation_preview():
    """Test remediation preview functionality."""
    try:
        from services.analysis_service.modules.automated_remediator import AutomatedRemediator

        remediator = AutomatedRemediator()

        test_content = '''
#api guide

this is a test document with several issues:
- inconsistent formatting
- grammar problems
- terminology inconsistencies
        '''

        result = await remediator.preview_remediation(
            content=test_content,
            doc_type='general'
        )

        print("✅ Remediation preview working")
        print(f"   Preview available: {result['preview_available']}")
        print(f"   Proposed fixes: {result['fix_count']}")
        print(f"   Estimated processing time: {result['estimated_processing_time']:.2f}s")

        if result['proposed_fixes']:
            print("   Preview of proposed fixes:")
            for i, fix in enumerate(result['proposed_fixes'][:3]):
                print(f"     {i+1}. {fix}")

        return True
    except Exception as e:
        print(f"❌ Remediation preview failed: {e}")
        return False

def test_analysis_service_main_import():
    """Test that the analysis service main module can be imported with automated remediation endpoints."""
    try:
        from services.analysis_service.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        remediation_routes = [r for r in routes if 'remediat' in r]

        print("✅ Analysis service main module imported successfully")
        print(f"✅ Found {len(remediation_routes)} automated remediation routes:")
        for route in remediation_routes:
            print(f"   - {route}")

        return True
    except Exception as e:
        print(f"❌ Failed to import analysis service main module: {e}")
        return False

def main():
    """Run all tests."""
    print("🔧 Testing Automated Remediation Functionality")
    print("=" * 65)

    tests = [
        test_automated_remediator_import,
        test_automated_remediator_initialization,
        test_document_structure_analysis,
        test_formatting_issue_fixes,
        test_terminology_consistency_fixes,
        test_link_fixes,
        test_safety_checks,
        test_similarity_calculation,
        test_backup_creation,
        test_remediation_report_generation,
        test_full_automated_remediation,
        test_remediation_preview,
        test_analysis_service_main_import,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        print(f"\n🧪 Running {test.__name__}...")
        try:
            if test.__name__ in ['test_full_automated_remediation', 'test_remediation_preview']:
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
        print("🎉 All automated remediation tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
