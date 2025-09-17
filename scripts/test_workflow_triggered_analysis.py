#!/usr/bin/env python3
"""Test script for workflow-triggered analysis functionality in Analysis Service.

Validates that the workflow trigger works correctly.
"""

import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

def test_workflow_trigger_import():
    """Test that the workflow trigger module can be imported."""
    try:
        from services.analysis_service.modules.workflow_trigger import WorkflowTrigger, process_workflow_event
        print("✅ Workflow trigger module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import workflow trigger module: {e}")
        return False

def test_workflow_trigger_initialization():
    """Test that the workflow trigger can be initialized."""
    try:
        from services.analysis_service.modules.workflow_trigger import WorkflowTrigger

        trigger = WorkflowTrigger()
        print("✅ WorkflowTrigger initialized successfully")
        print(f"   Initialized: {trigger.initialized}")
        print(f"   Event handlers: {len(trigger.event_handlers)} configured")
        print(f"   Trigger rules: {len(trigger.trigger_rules)} defined")
        print(f"   Analysis queues: {len(trigger.analysis_queues)} created")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize workflow trigger: {e}")
        return False

def test_event_context_analysis():
    """Test event context analysis."""
    try:
        from services.analysis_service.modules.workflow_trigger import WorkflowTrigger

        trigger = WorkflowTrigger()

        # Test pull request event
        pr_event = {
            'event_type': 'pull_request',
            'action': 'opened',
            'repository': 'my-org/docs-repo',
            'branch': 'feature/add-api-docs',
            'base_branch': 'main',
            'files_changed': ['docs/api.md', 'docs/examples.py'],
            'lines_changed': 150,
            'title': 'Add comprehensive API documentation'
        }

        pr_context = trigger._analyze_event_context(pr_event)

        print("✅ Pull request event context analysis working")
        print(f"   Event type: {pr_context['event_type']}")
        print(f"   Priority: {pr_context['priority']}")
        print(f"   Analysis types: {pr_context['analysis_types']}")
        print(f"   Documentation changes: {pr_context['file_changes']['has_documentation_changes']}")
        print(f"   Code changes: {pr_context['file_changes']['has_code_changes']}")
        print(f"   Urgency level: {pr_context['urgency_level']}")

        # Test push event
        push_event = {
            'event_type': 'push',
            'action': 'push',
            'repository': 'my-org/docs-repo',
            'branch': 'main',
            'files_changed': ['docs/getting-started.md'],
            'lines_changed': 25
        }

        push_context = trigger._analyze_event_context(push_event)

        print("✅ Push event context analysis working")
        print(f"   Event type: {push_context['event_type']}")
        print(f"   Priority: {push_context['priority']}")
        print(f"   Analysis types: {push_context['analysis_types']}")

        return True
    except Exception as e:
        print(f"❌ Event context analysis failed: {e}")
        return False

def test_file_changes_analysis():
    """Test file changes analysis."""
    try:
        from services.analysis_service.modules.workflow_trigger import WorkflowTrigger

        trigger = WorkflowTrigger()

        # Test mixed file changes
        event_data = {
            'files_changed': [
                'docs/api/reference.md',
                'docs/user-guide/tutorial.md',
                'src/main.py',
                'tests/test_api.py',
                'README.md',
                'docker-compose.yml'
            ]
        }

        file_analysis = trigger._analyze_file_changes(event_data)

        print("✅ File changes analysis working")
        print(f"   Total files: {file_analysis['total_files']}")
        print(f"   Documentation files: {len(file_analysis['documentation_files'])}")
        print(f"   Code files: {len(file_analysis['code_files'])}")
        print(f"   Config files: {len(file_analysis['config_files'])}")
        print(f"   Has documentation changes: {file_analysis['has_documentation_changes']}")
        print(f"   Has code changes: {file_analysis['has_code_changes']}")
        print(f"   Has config changes: {file_analysis['has_config_changes']}")

        # Verify categorization
        assert 'docs/api/reference.md' in file_analysis['documentation_files']
        assert 'src/main.py' in file_analysis['code_files']
        assert 'docker-compose.yml' in file_analysis['config_files']

        return True
    except Exception as e:
        print(f"❌ File changes analysis failed: {e}")
        return False

def test_branch_context_analysis():
    """Test branch context analysis."""
    try:
        from services.analysis_service.modules.workflow_trigger import WorkflowTrigger

        trigger = WorkflowTrigger()

        # Test different branch types
        branches = [
            ('main', 'main'),
            ('master', 'main'),
            ('develop', 'main'),
            ('feature/add-api', 'feature'),
            ('feat/new-ui', 'feature'),
            ('hotfix/security-patch', 'hotfix'),
            ('fix/typo', 'hotfix'),
            ('release/v2.1.0', 'release')
        ]

        print("✅ Branch context analysis working")

        for branch_name, expected_type in branches:
            event_data = {'branch': branch_name}
            branch_context = trigger._analyze_branch_context(event_data)

            print(f"   Branch '{branch_name}' → Type: {branch_context['branch_type']}")

            if expected_type == 'main':
                assert branch_context['is_main_branch'] is True
            elif expected_type == 'feature':
                assert branch_context['is_feature_branch'] is True
            elif expected_type == 'hotfix':
                assert branch_context['is_hotfix_branch'] is True
            elif expected_type == 'release':
                assert branch_context['is_release_branch'] is True

        return True
    except Exception as e:
        print(f"❌ Branch context analysis failed: {e}")
        return False

def test_change_size_assessment():
    """Test change size assessment."""
    try:
        from services.analysis_service.modules.workflow_trigger import WorkflowTrigger

        trigger = WorkflowTrigger()

        # Test different change sizes
        test_cases = [
            (5, 'small'),
            (50, 'small'),
            (150, 'medium'),
            (500, 'medium'),
            (1500, 'large'),
            (5000, 'large')
        ]

        print("✅ Change size assessment working")

        for lines_changed, expected_size in test_cases:
            event_data = {'lines_changed': lines_changed}
            assessed_size = trigger._assess_change_size(event_data)

            print(f"   {lines_changed} lines → {assessed_size}")
            assert assessed_size == expected_size

        return True
    except Exception as e:
        print(f"❌ Change size assessment failed: {e}")
        return False

def test_urgency_determination():
    """Test urgency determination."""
    try:
        from services.analysis_service.modules.workflow_trigger import WorkflowTrigger

        trigger = WorkflowTrigger()

        # Test different urgency scenarios
        test_cases = [
            ({'event_type': 'pull_request', 'branch': 'main'}, 'high'),
            ({'event_type': 'pull_request', 'branch': 'feature/test'}, 'medium'),
            ({'event_type': 'push', 'branch': 'main'}, 'high'),
            ({'event_type': 'push', 'branch': 'develop'}, 'medium'),
            ({'event_type': 'release', 'branch': 'main'}, 'high'),
            ({'event_type': 'issue', 'branch': 'main'}, 'low')
        ]

        print("✅ Urgency determination working")

        for event_data, expected_urgency in test_cases:
            urgency = trigger._determine_urgency(event_data)

            print(f"   {event_data['event_type']} on {event_data['branch']} → {urgency}")
            assert urgency == expected_urgency

        return True
    except Exception as e:
        print(f"❌ Urgency determination failed: {e}")
        return False

def test_analysis_plan_creation():
    """Test analysis plan creation."""
    try:
        from services.analysis_service.modules.workflow_trigger import WorkflowTrigger

        trigger = WorkflowTrigger()

        # Test PR event context
        pr_context = {
            'event_type': 'pull_request',
            'event_action': 'opened',
            'priority': 'high',
            'analysis_types': ['quality_check', 'consistency_check'],
            'urgency_level': 'medium',
            'size_assessment': 'medium',
            'file_changes': {'has_documentation_changes': True},
            'async_processing': True
        }

        plan = trigger._create_analysis_plan(pr_context)

        print("✅ Analysis plan creation working")
        print(f"   Analysis types: {plan['analysis_types']}")
        print(f"   Priority: {plan['priority']}")
        print(f"   Processing mode: {plan['processing_mode']}")
        print(f"   Time window: {plan['time_window']}")
        print(f"   Quality checks: {len(plan['quality_checks'])}")
        print(f"   Consistency checks: {len(plan['consistency_checks'])}")

        assert plan['priority'] == 'high'
        assert len(plan['quality_checks']) > 0
        assert len(plan['consistency_checks']) > 0

        return True
    except Exception as e:
        print(f"❌ Analysis plan creation failed: {e}")
        return False

def test_processing_time_estimation():
    """Test processing time estimation."""
    try:
        from services.analysis_service.modules.workflow_trigger import WorkflowTrigger

        trigger = WorkflowTrigger()

        # Test different plan complexities
        simple_plan = {
            'quality_checks': ['completeness_check'],
            'consistency_checks': ['terminology_check'],
            'impact_analysis': [],
            'peer_review': [],
            'automated_remediation': []
        }

        complex_plan = {
            'quality_checks': ['completeness_check', 'accuracy_check', 'clarity_check'],
            'consistency_checks': ['terminology_check', 'formatting_check'],
            'impact_analysis': ['dependency_analysis', 'stakeholder_analysis'],
            'peer_review': ['automated_review', 'quality_scoring'],
            'automated_remediation': ['formatting_fixes', 'terminology_fixes']
        }

        simple_time = trigger._estimate_processing_time(simple_plan)
        complex_time = trigger._estimate_processing_time(complex_plan)

        print("✅ Processing time estimation working")
        print(f"   Simple plan: {simple_time:.1f}s")
        print(f"   Complex plan: {complex_time:.1f}s")

        # Complex plan should take longer
        assert complex_time > simple_time

        return True
    except Exception as e:
        print(f"❌ Processing time estimation failed: {e}")
        return False

async def test_workflow_event_processing():
    """Test workflow event processing."""
    try:
        from services.analysis_service.modules.workflow_trigger import WorkflowTrigger

        trigger = WorkflowTrigger()

        # Test PR event processing
        pr_event = {
            'event_type': 'pull_request',
            'action': 'opened',
            'repository': 'my-org/docs-repo',
            'branch': 'feature/add-api-docs',
            'base_branch': 'main',
            'files_changed': ['docs/api.md', 'docs/examples.py'],
            'lines_changed': 150,
            'title': 'Add comprehensive API documentation'
        }

        result = await trigger.process_workflow_event(pr_event)

        print("✅ Workflow event processing working")
        print(f"   Workflow ID: {result['workflow_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Priority: {result['priority']}")
        print(f"   Analysis types: {len(result['analysis_types'])}")
        print(f"   Estimated processing time: {result['estimated_processing_time']:.1f}s")
        print(f"   Processing time: {result['processing_time']:.2f}s")

        # Verify workflow was stored
        workflow_id = result['workflow_id']
        workflow_record = trigger.get_workflow_status(workflow_id)

        print(f"   Workflow stored: {workflow_record is not None}")
        if workflow_record:
            print(f"   Workflow status: {workflow_record['status']}")
            print(f"   Analysis plan created: {'analysis_plan' in workflow_record}")

        return True
    except Exception as e:
        print(f"❌ Workflow event processing failed: {e}")
        return False

def test_queue_management():
    """Test queue management functionality."""
    try:
        from services.analysis_service.modules.workflow_trigger import WorkflowTrigger

        trigger = WorkflowTrigger()

        # Test initial queue status
        initial_status = trigger.get_queue_status()

        print("✅ Queue management working")
        print(f"   Initial queue status: {initial_status}")

        # All queues should start empty
        for priority, count in initial_status.items():
            assert count == 0

        return True
    except Exception as e:
        print(f"❌ Queue management failed: {e}")
        return False

def test_webhook_configuration():
    """Test webhook configuration."""
    try:
        from services.analysis_service.modules.workflow_trigger import WorkflowTrigger

        trigger = WorkflowTrigger()

        # Test webhook secret configuration
        secret = "test-webhook-secret-12345"
        trigger.configure_webhook_secret(secret)

        print("✅ Webhook configuration working")
        print(f"   Secret configured: {trigger.webhook_secret == secret}")

        return True
    except Exception as e:
        print(f"❌ Webhook configuration failed: {e}")
        return False

async def test_workflow_status_tracking():
    """Test workflow status tracking."""
    try:
        from services.analysis_service.modules.workflow_trigger import WorkflowTrigger

        trigger = WorkflowTrigger()

        # Process an event
        event = {
            'event_type': 'pull_request',
            'action': 'opened',
            'files_changed': ['docs/api.md'],
            'lines_changed': 50
        }

        result = await trigger.process_workflow_event(event)
        workflow_id = result['workflow_id']

        # Check status
        status = trigger.get_workflow_status(workflow_id)

        print("✅ Workflow status tracking working")
        print(f"   Workflow ID: {workflow_id}")
        print(f"   Status: {status['status']}")
        print(f"   Created at: {status['created_at']}")
        print(f"   Processed at: {status.get('processed_at', 'Not processed yet')}")
        print(f"   Completed at: {status.get('completed_at', 'Not completed yet')}")

        # Check event history
        history = trigger.get_event_history(limit=5)

        print(f"   Event history entries: {len(history)}")
        if history:
            latest_event = history[0]
            print(f"   Latest event type: {latest_event['event_type']}")
            print(f"   Latest event action: {latest_event['event_action']}")

        return True
    except Exception as e:
        print(f"❌ Workflow status tracking failed: {e}")
        return False

def test_analysis_service_main_import():
    """Test that the analysis service main module can be imported with workflow endpoints."""
    try:
        from services.analysis_service.main import app
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        workflow_routes = [r for r in routes if 'workflow' in r]

        print("✅ Analysis service main module imported successfully")
        print(f"✅ Found {len(workflow_routes)} workflow routes:")
        for route in workflow_routes:
            print(f"   - {route}")

        return True
    except Exception as e:
        print(f"❌ Failed to import analysis service main module: {e}")
        return False

def main():
    """Run all tests."""
    print("🔄 Testing Workflow-Triggered Analysis Functionality")
    print("=" * 65)

    tests = [
        test_workflow_trigger_import,
        test_workflow_trigger_initialization,
        test_event_context_analysis,
        test_file_changes_analysis,
        test_branch_context_analysis,
        test_change_size_assessment,
        test_urgency_determination,
        test_analysis_plan_creation,
        test_processing_time_estimation,
        test_workflow_event_processing,
        test_queue_management,
        test_webhook_configuration,
        test_workflow_status_tracking,
        test_analysis_service_main_import,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        print(f"\n🧪 Running {test.__name__}...")
        try:
            if test.__name__ in ['test_workflow_event_processing', 'test_workflow_status_tracking']:
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
        print("🎉 All workflow-triggered analysis tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
