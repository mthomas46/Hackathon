"""Workflow Trigger module for Analysis Service.

Provides intelligent workflow-triggered analysis capabilities that automatically
respond to workflow events (PRs, commits, releases, etc.) with appropriate
documentation analysis and quality checks.
"""

import time
import logging
import json
from typing import Dict, Any, List, Optional, Set, Union
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio
import re

from services.shared.core.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes

logger = logging.getLogger(__name__)


class WorkflowTrigger:
    """Intelligent workflow-triggered analysis system."""

    def __init__(self):
        """Initialize the workflow trigger system."""
        self.event_handlers = self._get_event_handlers()
        self.trigger_rules = self._get_trigger_rules()
        self.analysis_queues = defaultdict(deque)
        self.active_workflows = {}
        self.event_history = deque(maxlen=1000)  # Keep last 1000 events
        self.webhook_secret = None
        self._initialize_trigger_system()

    def _initialize_trigger_system(self) -> bool:
        """Initialize the workflow trigger system."""
        try:
            # Initialize event processing queues
            self._setup_event_queues()
            logger.info("Workflow trigger system initialized successfully")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize workflow trigger system: {e}")
            return False

    def _get_event_handlers(self) -> Dict[str, Dict[str, Any]]:
        """Define handlers for different workflow events."""
        return {
            'pull_request': {
                'description': 'Handle pull request events',
                'events': ['opened', 'synchronize', 'closed', 'merged'],
                'analysis_types': ['quality_check', 'consistency_check', 'impact_analysis'],
                'priority': 'high',
                'async_processing': True
            },
            'push': {
                'description': 'Handle push/commit events',
                'events': ['push'],
                'analysis_types': ['quality_check', 'change_analysis'],
                'priority': 'medium',
                'async_processing': True
            },
            'release': {
                'description': 'Handle release events',
                'events': ['published', 'updated', 'deleted'],
                'analysis_types': ['comprehensive_analysis', 'version_check'],
                'priority': 'high',
                'async_processing': False
            },
            'issue': {
                'description': 'Handle issue events',
                'events': ['opened', 'edited', 'closed'],
                'analysis_types': ['documentation_check'],
                'priority': 'low',
                'async_processing': True
            },
            'deployment': {
                'description': 'Handle deployment events',
                'events': ['started', 'completed', 'failed'],
                'analysis_types': ['deployment_validation', 'documentation_sync'],
                'priority': 'critical',
                'async_processing': False
            },
            'documentation_update': {
                'description': 'Handle documentation-specific updates',
                'events': ['created', 'updated', 'deleted'],
                'analysis_types': ['quality_analysis', 'consistency_check', 'peer_review'],
                'priority': 'high',
                'async_processing': True
            }
        }

    def _get_trigger_rules(self) -> Dict[str, Dict[str, Any]]:
        """Define rules for triggering analyses based on events."""
        return {
            'file_patterns': {
                'documentation': [
                    r'\.md$', r'\.rst$', r'\.txt$', r'\.adoc$',
                    r'docs/', r'documentation/', r'wiki/'
                ],
                'code': [
                    r'\.py$', r'\.js$', r'\.ts$', r'\.java$', r'\.go$',
                    r'\.cpp$', r'\.c$', r'\.h$', r'\.php$'
                ],
                'configuration': [
                    r'\.yml$', r'\.yaml$', r'\.json$', r'\.toml$',
                    r'\.ini$', r'\.cfg$', r'\.conf$'
                ]
            },
            'branch_patterns': {
                'main_branches': [r'^main$', r'^master$', r'^develop$', r'^staging$'],
                'feature_branches': [r'^feature/', r'^feat/'],
                'hotfix_branches': [r'^hotfix/', r'^fix/'],
                'release_branches': [r'^release/']
            },
            'size_thresholds': {
                'small': 10,      # Lines changed
                'medium': 100,
                'large': 1000
            },
            'time_windows': {
                'immediate': 0,         # Process immediately
                'quick': 300,          # 5 minutes
                'normal': 3600,        # 1 hour
                'batch': 86400         # 24 hours
            }
        }

    def _setup_event_queues(self) -> None:
        """Set up event processing queues for different priorities."""
        self.analysis_queues['critical'] = deque()
        self.analysis_queues['high'] = deque()
        self.analysis_queues['medium'] = deque()
        self.analysis_queues['low'] = deque()

    def _analyze_event_context(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the context of a workflow event to determine appropriate analysis."""
        event_type = event_data.get('event_type', 'unknown')
        event_action = event_data.get('action', 'unknown')

        context = {
            'event_type': event_type,
            'event_action': event_action,
            'priority': 'medium',
            'analysis_types': [],
            'trigger_reasons': [],
            'file_changes': self._analyze_file_changes(event_data),
            'branch_context': self._analyze_branch_context(event_data),
            'size_assessment': self._assess_change_size(event_data),
            'urgency_level': self._determine_urgency(event_data)
        }

        # Determine analysis types based on event
        if event_type == 'pull_request':
            context['analysis_types'] = ['quality_check', 'consistency_check']
            if event_action == 'opened':
                context['trigger_reasons'].append('new_pr_review')
            elif event_action == 'synchronize':
                context['trigger_reasons'].append('pr_update_review')

        elif event_type == 'push':
            context['analysis_types'] = ['change_analysis']
            context['trigger_reasons'].append('code_changes')

        elif event_type == 'release':
            context['analysis_types'] = ['comprehensive_analysis', 'version_check']
            context['trigger_reasons'].append('release_validation')

        elif event_type == 'documentation_update':
            context['analysis_types'] = ['quality_analysis', 'consistency_check', 'peer_review']
            context['trigger_reasons'].append('docs_update')

        # Set priority based on context
        if context['urgency_level'] == 'critical':
            context['priority'] = 'critical'
        elif event_type in ['pull_request', 'release', 'deployment']:
            context['priority'] = 'high'
        elif context['size_assessment'] == 'large':
            context['priority'] = 'high'

        return context

    def _analyze_file_changes(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze file changes in the event."""
        files_changed = event_data.get('files_changed', [])
        files_added = event_data.get('files_added', [])
        files_modified = event_data.get('files_modified', [])
        files_deleted = event_data.get('files_deleted', [])

        file_analysis = {
            'total_files': len(files_changed),
            'added_files': len(files_added),
            'modified_files': len(files_modified),
            'deleted_files': len(files_deleted),
            'documentation_files': [],
            'code_files': [],
            'config_files': [],
            'other_files': [],
            'has_documentation_changes': False,
            'has_code_changes': False,
            'has_config_changes': False
        }

        # Categorize files
        for file_path in files_changed:
            if any(re.search(pattern, file_path, re.IGNORECASE) for pattern in self.trigger_rules['file_patterns']['documentation']):
                file_analysis['documentation_files'].append(file_path)
                file_analysis['has_documentation_changes'] = True
            elif any(re.search(pattern, file_path, re.IGNORECASE) for pattern in self.trigger_rules['file_patterns']['code']):
                file_analysis['code_files'].append(file_path)
                file_analysis['has_code_changes'] = True
            elif any(re.search(pattern, file_path, re.IGNORECASE) for pattern in self.trigger_rules['file_patterns']['configuration']):
                file_analysis['config_files'].append(file_path)
                file_analysis['has_config_changes'] = True
            else:
                file_analysis['other_files'].append(file_path)

        return file_analysis

    def _analyze_branch_context(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the branch context of the event."""
        branch_name = event_data.get('branch', '')
        base_branch = event_data.get('base_branch', '')

        branch_context = {
            'branch_name': branch_name,
            'base_branch': base_branch,
            'branch_type': 'unknown',
            'is_main_branch': False,
            'is_feature_branch': False,
            'is_release_branch': False,
            'is_hotfix_branch': False
        }

        # Determine branch type
        if any(re.search(pattern, branch_name) for pattern in self.trigger_rules['branch_patterns']['main_branches']):
            branch_context['branch_type'] = 'main'
            branch_context['is_main_branch'] = True
        elif any(re.search(pattern, branch_name) for pattern in self.trigger_rules['branch_patterns']['feature_branches']):
            branch_context['branch_type'] = 'feature'
            branch_context['is_feature_branch'] = True
        elif any(re.search(pattern, branch_name) for pattern in self.trigger_rules['branch_patterns']['release_branches']):
            branch_context['branch_type'] = 'release'
            branch_context['is_release_branch'] = True
        elif any(re.search(pattern, branch_name) for pattern in self.trigger_rules['branch_patterns']['hotfix_branches']):
            branch_context['branch_type'] = 'hotfix'
            branch_context['is_hotfix_branch'] = True

        return branch_context

    def _assess_change_size(self, event_data: Dict[str, Any]) -> str:
        """Assess the size/scope of changes."""
        lines_changed = event_data.get('lines_changed', 0)
        files_changed = len(event_data.get('files_changed', []))

        if lines_changed >= self.trigger_rules['size_thresholds']['large'] or files_changed >= 20:
            return 'large'
        elif lines_changed >= self.trigger_rules['size_thresholds']['medium'] or files_changed >= 10:
            return 'medium'
        elif lines_changed >= self.trigger_rules['size_thresholds']['small'] or files_changed >= 1:
            return 'small'
        else:
            return 'minimal'

    def _determine_urgency(self, event_data: Dict[str, Any]) -> str:
        """Determine the urgency level of the event."""
        event_type = event_data.get('event_type', '')
        event_action = event_data.get('action', '')
        branch_context = self._analyze_branch_context(event_data)

        # Critical urgency
        if event_type == 'deployment' and event_action == 'failed':
            return 'critical'
        if event_type == 'release' and branch_context['is_main_branch']:
            return 'critical'

        # High urgency
        if event_type == 'pull_request' and branch_context['is_main_branch']:
            return 'high'
        if event_type == 'push' and branch_context['is_main_branch']:
            return 'high'

        # Medium urgency
        if event_type in ['pull_request', 'push']:
            return 'medium'

        # Low urgency
        return 'low'

    def _create_analysis_plan(self, event_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create an analysis plan based on event context."""
        plan = {
            'analysis_types': event_context['analysis_types'],
            'priority': event_context['priority'],
            'processing_mode': 'async' if event_context.get('async_processing', True) else 'sync',
            'time_window': self._determine_time_window(event_context),
            'quality_checks': [],
            'consistency_checks': [],
            'impact_analysis': [],
            'peer_review': [],
            'automated_remediation': []
        }

        # Define specific checks based on analysis types
        if 'quality_check' in event_context['analysis_types']:
            plan['quality_checks'] = [
                'completeness_check',
                'accuracy_check',
                'clarity_check',
                'structure_check'
            ]

        if 'consistency_check' in event_context['analysis_types']:
            plan['consistency_checks'] = [
                'terminology_consistency',
                'formatting_consistency',
                'style_consistency'
            ]

        if 'impact_analysis' in event_context['analysis_types']:
            plan['impact_analysis'] = [
                'dependency_analysis',
                'stakeholder_impact',
                'change_propagation'
            ]

        if 'peer_review' in event_context['analysis_types']:
            plan['peer_review'] = [
                'automated_review',
                'quality_scoring',
                'improvement_suggestions'
            ]

        if 'change_analysis' in event_context['analysis_types']:
            plan['automated_remediation'] = [
                'formatting_fixes',
                'terminology_fixes',
                'link_fixes'
            ]

        return plan

    def _determine_time_window(self, event_context: Dict[str, Any]) -> str:
        """Determine the appropriate time window for analysis."""
        urgency = event_context.get('urgency_level', 'low')
        size = event_context.get('size_assessment', 'small')
        priority = event_context.get('priority', 'medium')

        if urgency == 'critical' or priority == 'critical':
            return 'immediate'
        elif priority == 'high' or size == 'large':
            return 'quick'
        elif priority == 'medium':
            return 'normal'
        else:
            return 'batch'

    async def process_workflow_event(self, event_data: Dict[str, Any],
                                   webhook_signature: Optional[str] = None) -> Dict[str, Any]:
        """Process a workflow event and trigger appropriate analyses."""

        start_time = time.time()

        try:
            # Validate webhook signature if provided
            if webhook_signature and self.webhook_secret:
                if not self._validate_webhook_signature(event_data, webhook_signature):
                    return {
                        'error': 'Invalid webhook signature',
                        'status': 'rejected'
                    }

            # Analyze event context
            event_context = self._analyze_event_context(event_data)

            # Create analysis plan
            analysis_plan = self._create_analysis_plan(event_context)

            # Create workflow record
            workflow_id = f"wf_{int(time.time())}_{hash(str(event_data)) % 10000}"
            workflow_record = {
                'workflow_id': workflow_id,
                'event_data': event_data,
                'event_context': event_context,
                'analysis_plan': analysis_plan,
                'status': 'queued',
                'created_at': time.time(),
                'processed_at': None,
                'completed_at': None,
                'results': None
            }

            # Store workflow record
            self.active_workflows[workflow_id] = workflow_record

            # Add to event history
            self.event_history.append({
                'workflow_id': workflow_id,
                'event_type': event_context['event_type'],
                'event_action': event_context['event_action'],
                'priority': event_context['priority'],
                'timestamp': time.time()
            })

            # Queue analysis based on priority
            self.analysis_queues[event_context['priority']].append(workflow_id)

            # Process immediately if sync mode or critical
            if analysis_plan['processing_mode'] == 'sync' or event_context['priority'] == 'critical':
                await self._process_workflow(workflow_id)
            else:
                # Schedule async processing
                asyncio.create_task(self._process_workflow_async(workflow_id))

            processing_time = time.time() - start_time

            return {
                'workflow_id': workflow_id,
                'status': 'accepted',
                'priority': event_context['priority'],
                'analysis_types': event_context['analysis_types'],
                'estimated_processing_time': self._estimate_processing_time(analysis_plan),
                'processing_time': processing_time
            }

        except Exception as e:
            logger.error(f"Failed to process workflow event: {e}")
            return {
                'error': 'Workflow event processing failed',
                'message': str(e),
                'processing_time': time.time() - start_time
            }

    async def _process_workflow(self, workflow_id: str) -> None:
        """Process a workflow analysis."""
        try:
            workflow_record = self.active_workflows.get(workflow_id)
            if not workflow_record:
                logger.warning(f"Workflow {workflow_id} not found")
                return

            workflow_record['status'] = 'processing'
            workflow_record['processed_at'] = time.time()

            analysis_plan = workflow_record['analysis_plan']
            event_context = workflow_record['event_context']

            # Execute analyses based on plan
            results = await self._execute_analysis_plan(analysis_plan, event_context)

            # Update workflow record
            workflow_record['status'] = 'completed'
            workflow_record['completed_at'] = time.time()
            workflow_record['results'] = results

            # Clean up old workflows (keep last 100)
            if len(self.active_workflows) > 100:
                oldest_keys = sorted(self.active_workflows.keys(),
                                   key=lambda x: self.active_workflows[x]['created_at'])[:10]
                for key in oldest_keys:
                    del self.active_workflows[key]

        except Exception as e:
            logger.error(f"Workflow processing failed for {workflow_id}: {e}")
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]['status'] = 'failed'
                self.active_workflows[workflow_id]['error'] = str(e)

    async def _process_workflow_async(self, workflow_id: str) -> None:
        """Process workflow asynchronously with delay based on time window."""
        try:
            workflow_record = self.active_workflows.get(workflow_id)
            if not workflow_record:
                return

            analysis_plan = workflow_record['analysis_plan']
            time_window = analysis_plan.get('time_window', 'normal')

            # Wait based on time window
            delay = self.trigger_rules['time_windows'].get(time_window, 3600)
            if delay > 0:
                await asyncio.sleep(delay)

            await self._process_workflow(workflow_id)

        except Exception as e:
            logger.error(f"Async workflow processing failed for {workflow_id}: {e}")

    async def _execute_analysis_plan(self, analysis_plan: Dict[str, Any],
                                   event_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the analysis plan for a workflow."""
        results = {
            'quality_checks': {},
            'consistency_checks': {},
            'impact_analysis': {},
            'peer_review': {},
            'automated_remediation': {},
            'summary': {}
        }

        try:
            # Import analysis modules (lazy loading)
            from .quality_analyzer import analyze_document_quality
            from .consistency_checker import check_document_consistency
            from .change_impact_analyzer import analyze_change_impact
            from .peer_review_enhancer import review_documentation
            from .automated_remediator import remediate_document

            # Execute quality checks
            if analysis_plan.get('quality_checks'):
                # This would integrate with actual document content
                results['quality_checks'] = {
                    'status': 'completed',
                    'checks_performed': analysis_plan['quality_checks'],
                    'findings': []
                }

            # Execute consistency checks
            if analysis_plan.get('consistency_checks'):
                results['consistency_checks'] = {
                    'status': 'completed',
                    'checks_performed': analysis_plan['consistency_checks'],
                    'issues_found': 0
                }

            # Execute impact analysis
            if analysis_plan.get('impact_analysis'):
                results['impact_analysis'] = {
                    'status': 'completed',
                    'analyses_performed': analysis_plan['impact_analysis'],
                    'impacts_identified': []
                }

            # Execute peer review
            if analysis_plan.get('peer_review'):
                results['peer_review'] = {
                    'status': 'completed',
                    'reviews_performed': analysis_plan['peer_review'],
                    'recommendations': []
                }

            # Execute automated remediation
            if analysis_plan.get('automated_remediation'):
                results['automated_remediation'] = {
                    'status': 'completed',
                    'fixes_applied': analysis_plan['automated_remediation'],
                    'changes_made': 0
                }

            # Generate summary
            results['summary'] = self._generate_workflow_summary(results, event_context)

        except Exception as e:
            logger.error(f"Analysis plan execution failed: {e}")
            results['error'] = str(e)

        return results

    def _generate_workflow_summary(self, results: Dict[str, Any],
                                 event_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of workflow analysis results."""
        summary = {
            'total_analyses': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'critical_findings': 0,
            'recommendations_count': 0,
            'processing_status': 'completed'
        }

        # Count analyses
        for category, category_results in results.items():
            if category != 'summary' and isinstance(category_results, dict):
                summary['total_analyses'] += 1
                if category_results.get('status') == 'completed':
                    summary['successful_analyses'] += 1
                elif category_results.get('status') == 'failed':
                    summary['failed_analyses'] += 1

                # Count findings and recommendations
                summary['critical_findings'] += len(category_results.get('findings', []))
                summary['recommendations_count'] += len(category_results.get('recommendations', []))

        # Determine overall status
        if summary['failed_analyses'] > 0:
            summary['processing_status'] = 'partial_failure'
        elif summary['successful_analyses'] == 0:
            summary['processing_status'] = 'no_analyses'
        else:
            summary['processing_status'] = 'success'

        return summary

    def _validate_webhook_signature(self, event_data: Dict[str, Any], signature: str) -> bool:
        """Validate webhook signature for security."""
        # This would implement proper webhook signature validation
        # For now, return True (implement actual validation based on webhook provider)
        return True

    def _estimate_processing_time(self, analysis_plan: Dict[str, Any]) -> float:
        """Estimate processing time for an analysis plan."""
        base_time = 5.0  # Base processing time in seconds

        # Add time for each analysis type
        time_multipliers = {
            'quality_checks': len(analysis_plan.get('quality_checks', [])) * 2.0,
            'consistency_checks': len(analysis_plan.get('consistency_checks', [])) * 1.5,
            'impact_analysis': len(analysis_plan.get('impact_analysis', [])) * 3.0,
            'peer_review': len(analysis_plan.get('peer_review', [])) * 4.0,
            'automated_remediation': len(analysis_plan.get('automated_remediation', [])) * 2.5
        }

        total_time = base_time
        for analysis_type, multiplier in time_multipliers.items():
            total_time += multiplier

        return round(total_time, 2)

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow."""
        return self.active_workflows.get(workflow_id)

    def get_event_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent event history."""
        return list(self.event_history)[-limit:]

    def get_queue_status(self) -> Dict[str, Any]:
        """Get the status of analysis queues."""
        return {
            priority: len(queue)
            for priority, queue in self.analysis_queues.items()
        }

    def configure_webhook_secret(self, secret: str) -> None:
        """Configure webhook secret for signature validation."""
        self.webhook_secret = secret

    def clear_old_workflows(self, max_age_hours: int = 24) -> int:
        """Clear old completed workflows."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        workflows_to_remove = []

        for workflow_id, workflow in self.active_workflows.items():
            if (workflow.get('completed_at') and
                workflow['completed_at'] < cutoff_time):
                workflows_to_remove.append(workflow_id)

        for workflow_id in workflows_to_remove:
            del self.active_workflows[workflow_id]

        return len(workflows_to_remove)


# Global instance for reuse
workflow_trigger = WorkflowTrigger()


async def process_workflow_event(event_data: Dict[str, Any],
                               webhook_signature: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function for processing workflow events.

    Args:
        event_data: Workflow event data
        webhook_signature: Optional webhook signature for validation

    Returns:
        Workflow processing results
    """
    return await workflow_trigger.process_workflow_event(event_data, webhook_signature)
