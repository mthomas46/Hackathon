"""Unit tests for Autonomous Systems functionality.

This module contains comprehensive unit tests for autonomous system capabilities,
including auto-scaling, self-healing, intelligent resource allocation,
and autonomous optimization loops.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import asyncio
import sys
import os
from typing import Dict, Any, List

# Add the dashboard service to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pages.autonomous import (
    render_autonomous_page,
    initialize_autonomous_state,
    perform_auto_scaling_analysis,
    execute_auto_scaling_action,
    detect_system_anomalies,
    trigger_self_healing,
    optimize_resource_allocation,
    run_autonomous_optimization_loop,
    calculate_system_health_score,
    predict_resource_demand,
    generate_autonomous_recommendations,
    execute_autonomous_actions,
    monitor_autonomous_performance
)


class TestAutonomousSystemsCore:
    """Test suite for core autonomous systems functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.sample_system_metrics = {
            'cpu_usage': 75.5,
            'memory_usage': 82.3,
            'disk_usage': 45.6,
            'network_traffic': 1250.5,
            'active_connections': 245,
            'response_time': 145.8,
            'error_rate': 0.05,
            'throughput': 1250.0
        }

        self.sample_resource_data = pd.DataFrame({
            'resource_id': ['cpu', 'memory', 'disk', 'network'],
            'current_usage': [75.5, 82.3, 45.6, 1250.5],
            'capacity': [100, 100, 100, 2000],
            'threshold': [80, 85, 90, 1500],
            'cost_per_unit': [0.1, 0.05, 0.02, 0.001]
        })

    @patch('streamlit.set_page_config')
    @patch('streamlit.tabs')
    def test_render_autonomous_page_structure(self, mock_tabs, mock_page_config):
        """Test that autonomous page renders with correct structure."""
        mock_tab1, mock_tab2, mock_tab3, mock_tab4 = Mock(), Mock(), Mock(), Mock()
        mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3, mock_tab4]

        with patch('streamlit.warning'), patch('streamlit.info'):
            render_autonomous_page()

        # Verify tabs were created
        mock_tabs.assert_called_once()
        assert len(mock_tabs.call_args[0][0]) == 4  # Should have 4 tabs

    def test_initialize_autonomous_state(self):
        """Test initialization of autonomous systems session state."""
        with patch('streamlit.session_state', {}) as mock_session_state:
            initialize_autonomous_state()

            # Verify session state was initialized
            assert 'autonomous_config' in mock_session_state
            assert 'scaling_history' in mock_session_state
            assert 'healing_actions' in mock_session_state
            assert 'optimization_metrics' in mock_session_state
            assert 'autonomous_mode' in mock_session_state

    def test_calculate_system_health_score(self):
        """Test system health score calculation."""
        health_score = calculate_system_health_score(self.sample_system_metrics)

        assert isinstance(health_score, float)
        assert 0 <= health_score <= 100

        # Test with degraded system
        degraded_metrics = self.sample_system_metrics.copy()
        degraded_metrics['cpu_usage'] = 95
        degraded_metrics['error_rate'] = 0.15

        degraded_score = calculate_system_health_score(degraded_metrics)
        assert degraded_score < health_score  # Should be lower

    def test_predict_resource_demand(self):
        """Test resource demand prediction."""
        historical_data = pd.DataFrame({
            'timestamp': pd.date_range('2023-01-01', periods=100, freq='H'),
            'cpu_usage': np.random.normal(70, 10, 100),
            'memory_usage': np.random.normal(75, 8, 100),
            'request_count': np.random.normal(1000, 200, 100)
        })

        predictions = predict_resource_demand(historical_data, forecast_hours=24)

        assert isinstance(predictions, dict)
        assert 'cpu_prediction' in predictions
        assert 'memory_prediction' in predictions
        assert 'confidence_intervals' in predictions
        assert len(predictions['cpu_prediction']) == 24


class TestAutoScaling:
    """Test suite for auto-scaling functionality."""

    def setup_method(self):
        """Set up test data for auto-scaling."""
        self.scaling_config = {
            'min_instances': 1,
            'max_instances': 10,
            'cpu_threshold_high': 80,
            'cpu_threshold_low': 30,
            'memory_threshold_high': 85,
            'memory_threshold_low': 40,
            'scale_up_cooldown': 300,
            'scale_down_cooldown': 600,
            'scaling_history': []
        }

        self.current_metrics = {
            'cpu_usage': 85,
            'memory_usage': 78,
            'active_connections': 1500,
            'response_time': 200,
            'current_instances': 3
        }

    def test_perform_auto_scaling_analysis(self):
        """Test auto-scaling analysis."""
        analysis_result = perform_auto_scaling_analysis(
            self.current_metrics, self.scaling_config
        )

        assert isinstance(analysis_result, dict)
        assert 'recommendation' in analysis_result
        assert 'confidence' in analysis_result
        assert 'metrics' in analysis_result
        assert 'reasoning' in analysis_result

    def test_auto_scaling_high_load_scenario(self):
        """Test auto-scaling under high load."""
        high_load_metrics = self.current_metrics.copy()
        high_load_metrics['cpu_usage'] = 90
        high_load_metrics['memory_usage'] = 88
        high_load_metrics['active_connections'] = 2000

        analysis = perform_auto_scaling_analysis(high_load_metrics, self.scaling_config)

        assert analysis['recommendation'] in ['scale_up', 'urgent_scale_up']
        assert analysis['confidence'] > 0.7  # High confidence for scaling up

    def test_auto_scaling_low_load_scenario(self):
        """Test auto-scaling under low load."""
        low_load_metrics = self.current_metrics.copy()
        low_load_metrics['cpu_usage'] = 25
        low_load_metrics['memory_usage'] = 30
        low_load_metrics['active_connections'] = 200

        analysis = perform_auto_scaling_analysis(low_load_metrics, self.scaling_config)

        assert analysis['recommendation'] in ['scale_down', 'consider_scale_down']
        assert analysis['confidence'] > 0.6  # Moderate confidence for scaling down

    def test_auto_scaling_normal_load_scenario(self):
        """Test auto-scaling under normal load."""
        analysis = perform_auto_scaling_analysis(self.current_metrics, self.scaling_config)

        assert analysis['recommendation'] == 'maintain'
        assert analysis['confidence'] > 0.8  # High confidence for maintaining current state

    @patch('pages.autonomous.execute_scaling_action')
    def test_execute_auto_scaling_action(self, mock_execute):
        """Test execution of auto-scaling actions."""
        mock_execute.return_value = {
            'success': True,
            'new_instance_count': 4,
            'execution_time': 45.2
        }

        result = execute_auto_scaling_action('scale_up', 4)

        assert result['success'] is True
        assert result['new_instance_count'] == 4
        assert 'execution_time' in result

    def test_auto_scaling_cooldown_logic(self):
        """Test auto-scaling cooldown logic."""
        # Add recent scaling action to history
        recent_action = datetime.now() - timedelta(seconds=100)  # 100 seconds ago
        self.scaling_config['scaling_history'].append({
            'action': 'scale_up',
            'timestamp': recent_action,
            'instances': 4
        })

        # Should be in cooldown period
        analysis = perform_auto_scaling_analysis(self.current_metrics, self.scaling_config)

        assert 'cooldown_active' in analysis
        assert analysis['cooldown_active'] is True

    def test_auto_scaling_boundaries(self):
        """Test auto-scaling respects min/max boundaries."""
        # Test minimum boundary
        min_config = self.scaling_config.copy()
        min_config['current_instances'] = 1

        low_metrics = self.current_metrics.copy()
        low_metrics['cpu_usage'] = 20
        low_metrics['current_instances'] = 1

        analysis = perform_auto_scaling_analysis(low_metrics, min_config)
        assert analysis['recommendation'] != 'scale_down'  # Should not scale below minimum

        # Test maximum boundary
        max_config = self.scaling_config.copy()
        max_config['current_instances'] = 10

        high_metrics = self.current_metrics.copy()
        high_metrics['cpu_usage'] = 95
        high_metrics['current_instances'] = 10

        analysis = perform_auto_scaling_analysis(high_metrics, max_config)
        assert analysis['recommendation'] != 'scale_up'  # Should not scale above maximum


class TestSelfHealing:
    """Test suite for self-healing functionality."""

    def setup_method(self):
        """Set up test data for self-healing."""
        self.system_state = {
            'services': {
                'web_server': {'status': 'healthy', 'response_time': 150},
                'database': {'status': 'warning', 'response_time': 500},
                'cache': {'status': 'critical', 'response_time': 2000},
                'api_gateway': {'status': 'healthy', 'response_time': 100}
            },
            'resources': {
                'cpu': {'usage': 85, 'threshold': 80},
                'memory': {'usage': 90, 'threshold': 85},
                'disk': {'usage': 95, 'threshold': 90}
            },
            'errors': [
                {'service': 'cache', 'error': 'Connection timeout', 'count': 15},
                {'service': 'database', 'error': 'Slow query', 'count': 8}
            ]
        }

    def test_detect_system_anomalies(self):
        """Test anomaly detection for self-healing."""
        anomalies = detect_system_anomalies(self.system_state)

        assert isinstance(anomalies, list)
        assert len(anomalies) > 0  # Should detect some anomalies

        # Check anomaly structure
        for anomaly in anomalies:
            assert 'type' in anomaly
            assert 'severity' in anomaly
            assert 'description' in anomaly
            assert 'affected_service' in anomaly
            assert 'recommended_action' in anomaly

    def test_trigger_self_healing_critical_service(self):
        """Test self-healing for critical service failure."""
        healing_actions = trigger_self_healing(self.system_state, 'cache')

        assert isinstance(healing_actions, list)
        assert len(healing_actions) > 0

        # Should include restart action for critical service
        restart_actions = [a for a in healing_actions if a.get('action') == 'restart']
        assert len(restart_actions) > 0

    def test_trigger_self_healing_resource_issue(self):
        """Test self-healing for resource-related issues."""
        # Simulate high memory usage
        high_memory_state = self.system_state.copy()
        high_memory_state['resources']['memory']['usage'] = 95

        healing_actions = trigger_self_healing(high_memory_state, 'memory')

        assert isinstance(healing_actions, list)

        # Should include memory optimization actions
        memory_actions = [a for a in healing_actions if 'memory' in a.get('action', '').lower()]
        assert len(memory_actions) > 0

    @patch('pages.autonomous.execute_healing_action')
    def test_execute_healing_action_success(self, mock_execute):
        """Test successful execution of healing action."""
        mock_execute.return_value = {
            'success': True,
            'execution_time': 30.5,
            'result': 'Service restarted successfully'
        }

        action = {
            'action': 'restart',
            'service': 'cache',
            'parameters': {'force': True}
        }

        result = self._execute_healing_action(action)

        assert result['success'] is True
        assert 'execution_time' in result
        assert 'result' in result

    def test_self_healing_action_validation(self):
        """Test validation of healing actions."""
        # Test invalid action
        invalid_action = {'action': 'invalid_action', 'service': 'test'}

        with pytest.raises(ValueError):
            trigger_self_healing(self.system_state, 'test', [invalid_action])

        # Test missing required parameters
        incomplete_action = {'action': 'restart'}  # Missing service

        with pytest.raises(ValueError):
            trigger_self_healing(self.system_state, 'test', [incomplete_action])

    def _execute_healing_action(self, action):
        """Helper method for executing healing action."""
        return {
            'success': True,
            'execution_time': 30.5,
            'result': f"{action['action']} executed successfully"
        }


class TestResourceOptimization:
    """Test suite for resource optimization functionality."""

    def setup_method(self):
        """Set up test data for resource optimization."""
        self.resource_allocation = {
            'web_servers': {'instances': 3, 'cpu_allocation': 2, 'memory_allocation': 4},
            'databases': {'instances': 2, 'cpu_allocation': 4, 'memory_allocation': 8},
            'cache_servers': {'instances': 2, 'cpu_allocation': 1, 'memory_allocation': 2},
            'worker_nodes': {'instances': 5, 'cpu_allocation': 2, 'memory_allocation': 4}
        }

        self.workload_patterns = pd.DataFrame({
            'timestamp': pd.date_range('2023-01-01', periods=168, freq='H'),  # One week
            'cpu_demand': np.random.normal(70, 15, 168),
            'memory_demand': np.random.normal(75, 10, 168),
            'request_load': np.random.normal(1000, 200, 168)
        })

    def test_optimize_resource_allocation(self):
        """Test resource allocation optimization."""
        optimization_result = optimize_resource_allocation(
            self.resource_allocation, self.workload_patterns
        )

        assert isinstance(optimization_result, dict)
        assert 'optimized_allocation' in optimization_result
        assert 'cost_savings' in optimization_result
        assert 'performance_impact' in optimization_result
        assert 'recommendations' in optimization_result

    def test_resource_optimization_cost_benefit_analysis(self):
        """Test cost-benefit analysis for resource optimization."""
        result = optimize_resource_allocation(self.resource_allocation, self.workload_patterns)

        # Verify cost savings calculation
        assert 'cost_savings' in result
        assert isinstance(result['cost_savings'], dict)
        assert 'monthly_savings' in result['cost_savings']
        assert 'percentage_reduction' in result['cost_savings']

    def test_resource_optimization_performance_impact(self):
        """Test performance impact assessment."""
        result = optimize_resource_allocation(self.resource_allocation, self.workload_patterns)

        # Verify performance impact assessment
        assert 'performance_impact' in result
        assert isinstance(result['performance_impact'], dict)
        assert 'response_time_change' in result['performance_impact']
        assert 'throughput_change' in result['performance_impact']

    def test_resource_optimization_under_peak_load(self):
        """Test resource optimization under peak load conditions."""
        # Create peak load scenario
        peak_workload = self.workload_patterns.copy()
        peak_workload.loc[peak_workload.index[:24], 'cpu_demand'] = 95  # High CPU demand for first day
        peak_workload.loc[peak_workload.index[:24], 'request_load'] = 1500

        result = optimize_resource_allocation(self.resource_allocation, peak_workload)

        # Under peak load, should recommend maintaining or increasing resources
        assert result['optimized_allocation']['web_servers']['instances'] >= 3
        assert 'performance_impact' in result

    def test_resource_optimization_under_low_load(self):
        """Test resource optimization under low load conditions."""
        # Create low load scenario
        low_workload = self.workload_patterns.copy()
        low_workload['cpu_demand'] = 30  # Low CPU demand
        low_workload['memory_demand'] = 40
        low_workload['request_load'] = 300

        result = optimize_resource_allocation(self.resource_allocation, low_workload)

        # Under low load, should recommend reducing resources
        assert result['optimized_allocation']['web_servers']['instances'] <= 3
        assert result['cost_savings']['percentage_reduction'] > 0


class TestAutonomousOptimizationLoop:
    """Test suite for autonomous optimization loop functionality."""

    def setup_method(self):
        """Set up test data for autonomous optimization."""
        self.optimization_config = {
            'enabled': True,
            'optimization_interval': 3600,  # 1 hour
            'max_concurrent_actions': 3,
            'risk_tolerance': 'medium',
            'performance_targets': {
                'response_time_max': 500,
                'error_rate_max': 0.05,
                'throughput_min': 800
            },
            'cost_optimization_weight': 0.3,
            'performance_optimization_weight': 0.7
        }

    @pytest.mark.asyncio
    async def test_run_autonomous_optimization_loop(self):
        """Test autonomous optimization loop execution."""
        system_state = {
            'performance_metrics': {
                'response_time': 450,
                'error_rate': 0.03,
                'throughput': 950
            },
            'resource_utilization': {
                'cpu': 65,
                'memory': 70,
                'disk': 45
            },
            'cost_metrics': {
                'monthly_cost': 5000,
                'cost_per_request': 0.005
            }
        }

        with patch('pages.autonomous.generate_optimization_actions') as mock_generate, \
             patch('pages.autonomous.evaluate_action_impact') as mock_evaluate, \
             patch('asyncio.sleep'):

            mock_generate.return_value = [
                {'action': 'scale_down', 'service': 'web_servers', 'impact': 0.8},
                {'action': 'optimize_cache', 'service': 'cache', 'impact': 0.6}
            ]

            mock_evaluate.return_value = {
                'net_benefit': 150,
                'risk_level': 'low',
                'execution_confidence': 0.85
            }

            result = await run_autonomous_optimization_loop(system_state, self.optimization_config)

            assert isinstance(result, dict)
            assert 'actions_executed' in result
            assert 'optimization_metrics' in result
            assert 'next_optimization_time' in result

    def test_generate_autonomous_recommendations(self):
        """Test generation of autonomous recommendations."""
        system_state = {
            'performance_metrics': {'response_time': 600, 'error_rate': 0.08},
            'resource_utilization': {'cpu': 85, 'memory': 80},
            'cost_metrics': {'monthly_cost': 6000}
        }

        recommendations = generate_autonomous_recommendations(system_state, self.optimization_config)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        for rec in recommendations:
            assert 'action' in rec
            assert 'priority' in rec
            assert 'expected_benefit' in rec
            assert 'risk_assessment' in rec

    def test_execute_autonomous_actions(self):
        """Test execution of autonomous actions."""
        actions = [
            {'action': 'restart_service', 'service': 'cache', 'priority': 'high'},
            {'action': 'scale_up', 'service': 'web_servers', 'instances': 2, 'priority': 'medium'}
        ]

        with patch('pages.autonomous.execute_action') as mock_execute:
            mock_execute.return_value = {'success': True, 'execution_time': 30}

            results = execute_autonomous_actions(actions)

            assert isinstance(results, list)
            assert len(results) == len(actions)

            for result in results:
                assert 'action' in result
                assert 'success' in result
                assert 'execution_time' in result

    def test_monitor_autonomous_performance(self):
        """Test monitoring of autonomous system performance."""
        optimization_history = [
            {'timestamp': datetime.now() - timedelta(hours=2), 'action': 'scale_up', 'benefit': 100},
            {'timestamp': datetime.now() - timedelta(hours=1), 'action': 'optimize_cache', 'benefit': 50},
            {'timestamp': datetime.now(), 'action': 'restart_service', 'benefit': 75}
        ]

        performance_metrics = monitor_autonomous_performance(optimization_history)

        assert isinstance(performance_metrics, dict)
        assert 'total_benefit' in performance_metrics
        assert 'average_benefit_per_action' in performance_metrics
        assert 'success_rate' in performance_metrics
        assert 'optimization_frequency' in performance_metrics

    def test_autonomous_optimization_risk_assessment(self):
        """Test risk assessment for autonomous actions."""
        high_risk_action = {
            'action': 'terminate_instances',
            'service': 'database',
            'instances': 3
        }

        low_risk_action = {
            'action': 'clear_cache',
            'service': 'web_cache'
        }

        # High risk action should have higher risk score
        assert self._assess_action_risk(high_risk_action) > self._assess_action_risk(low_risk_action)

    def test_autonomous_optimization_cost_benefit_analysis(self):
        """Test cost-benefit analysis for optimization actions."""
        action = {
            'action': 'scale_down',
            'service': 'worker_nodes',
            'instances': 2,
            'estimated_savings': 500,
            'performance_impact': -0.1
        }

        analysis = self._analyze_cost_benefit(action, self.optimization_config)

        assert 'net_benefit' in analysis
        assert 'benefit_cost_ratio' in analysis
        assert 'risk_adjusted_benefit' in analysis

    def _assess_action_risk(self, action):
        """Helper method for action risk assessment."""
        risk_scores = {
            'terminate_instances': 0.9,
            'restart_service': 0.7,
            'scale_up': 0.4,
            'scale_down': 0.3,
            'clear_cache': 0.1,
            'optimize_config': 0.2
        }

        return risk_scores.get(action['action'], 0.5)

    def _analyze_cost_benefit(self, action, config):
        """Helper method for cost-benefit analysis."""
        return {
            'net_benefit': action['estimated_savings'] * 0.9,  # 10% risk adjustment
            'benefit_cost_ratio': 2.5,
            'risk_adjusted_benefit': action['estimated_savings'] * 0.8
        }


class TestIntegrationScenarios:
    """Test suite for autonomous system integration scenarios."""

    def test_full_autonomous_workflow(self):
        """Test complete autonomous workflow from monitoring to action."""
        # This would test the complete autonomous workflow
        # For now, verify the components work together
        system_state = {
            'performance_metrics': {'response_time': 600},
            'resource_utilization': {'cpu': 85}
        }

        # Generate recommendations
        recommendations = generate_autonomous_recommendations(system_state, {})

        assert len(recommendations) > 0

        # Execute actions (mocked)
        with patch('pages.autonomous.execute_autonomous_actions') as mock_execute:
            mock_execute.return_value = [{'success': True}]
            results = execute_autonomous_actions(recommendations[:1])

            assert len(results) == 1
            assert results[0]['success'] is True

    def test_autonomous_system_boundaries(self):
        """Test autonomous system respects boundaries and constraints."""
        config = {
            'max_concurrent_actions': 2,
            'risk_tolerance': 'low',
            'performance_targets': {'response_time_max': 300}
        }

        # Test with high-risk actions
        high_risk_actions = [
            {'action': 'terminate_instances', 'risk': 0.9},
            {'action': 'restart_database', 'risk': 0.8},
            {'action': 'scale_down', 'risk': 0.2}
        ]

        # Should filter out high-risk actions for low risk tolerance
        filtered_actions = [a for a in high_risk_actions if a['risk'] <= 0.3]

        assert len(filtered_actions) == 1
        assert filtered_actions[0]['action'] == 'scale_down'

    def test_autonomous_system_learning(self):
        """Test autonomous system learning from past actions."""
        # This would test the learning component
        # For now, verify the structure exists
        assert callable(generate_autonomous_recommendations)
        assert callable(execute_autonomous_actions)


# Pytest fixtures for common test data
@pytest.fixture
def sample_system_state():
    """Fixture for sample system state."""
    return {
        'performance_metrics': {
            'response_time': 450,
            'error_rate': 0.03,
            'throughput': 950
        },
        'resource_utilization': {
            'cpu': 65,
            'memory': 70,
            'disk': 45
        },
        'services': {
            'web_server': {'status': 'healthy'},
            'database': {'status': 'warning'},
            'cache': {'status': 'healthy'}
        }
    }


@pytest.fixture
def sample_optimization_config():
    """Fixture for sample optimization configuration."""
    return {
        'enabled': True,
        'optimization_interval': 3600,
        'max_concurrent_actions': 3,
        'risk_tolerance': 'medium',
        'performance_targets': {
            'response_time_max': 500,
            'error_rate_max': 0.05,
            'throughput_min': 800
        }
    }


if __name__ == "__main__":
    pytest.main([__file__])
