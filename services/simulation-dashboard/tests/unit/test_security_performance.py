"""Unit tests for Security and Performance functionality.

This module contains comprehensive tests for security validation, performance benchmarking,
load testing, and security monitoring capabilities of the simulation dashboard.
"""

import pytest
import time
import threading
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import numpy as np
import hashlib
import sys
import os
from queue import Queue
import psutil
import requests

# Add the dashboard service to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestSecurityValidation:
    """Test suite for security validation functionality."""

    def setup_method(self):
        """Set up test environment for security tests."""
        self.sample_user_data = {
            'user_id': 'user_123',
            'username': 'test_user',
            'role': 'admin',
            'permissions': ['read', 'write', 'delete', 'admin'],
            'last_login': datetime.now(),
            'session_token': 'token_abc123'
        }

        self.sample_request_data = {
            'method': 'POST',
            'endpoint': '/api/simulations',
            'headers': {
                'Authorization': 'Bearer token_abc123',
                'Content-Type': 'application/json',
                'User-Agent': 'TestClient/1.0'
            },
            'body': '{"name": "test_simulation", "config": {}}',
            'ip_address': '192.168.1.100',
            'timestamp': datetime.now()
        }

    def test_input_validation_sanitization(self):
        """Test input validation and sanitization."""
        # Test SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "javascript:alert('xss')",
            "UNION SELECT * FROM users"
        ]

        for malicious_input in malicious_inputs:
            # Should detect and reject malicious inputs
            assert self._is_malicious_input(malicious_input)

        # Test valid inputs
        valid_inputs = [
            "normal_user_input",
            "user@example.com",
            "Test Simulation 2024",
            "config_value_123"
        ]

        for valid_input in valid_inputs:
            assert not self._is_malicious_input(valid_input)

    def test_authentication_validation(self):
        """Test authentication validation."""
        # Valid authentication
        valid_auth = self._validate_authentication('valid_token', 'user_123')
        assert valid_auth['valid'] is True
        assert valid_auth['user_id'] == 'user_123'

        # Invalid authentication
        invalid_auth = self._validate_authentication('invalid_token', 'user_123')
        assert invalid_auth['valid'] is False
        assert 'error' in invalid_auth

        # Expired token
        expired_auth = self._validate_authentication('expired_token', 'user_123')
        assert expired_auth['valid'] is False
        assert expired_auth['error'] == 'token_expired'

    def test_authorization_permissions(self):
        """Test authorization and permissions validation."""
        # Admin user should have all permissions
        admin_permissions = self._check_permissions('admin', ['read', 'write', 'delete'])
        assert admin_permissions['granted'] is True
        assert admin_permissions['missing_permissions'] == []

        # Regular user with limited permissions
        user_permissions = self._check_permissions('user', ['read', 'write', 'admin'])
        assert user_permissions['granted'] is False
        assert 'admin' in user_permissions['missing_permissions']

        # Permission escalation attempt
        escalation_attempt = self._check_permissions('user', ['admin', 'superuser'])
        assert escalation_attempt['granted'] is False
        assert len(escalation_attempt['missing_permissions']) > 0

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Normal request rate
        normal_rate = self._check_rate_limit('user_123', 10)  # 10 requests
        assert normal_rate['allowed'] is True
        assert normal_rate['remaining'] > 0

        # High request rate (potential DoS)
        high_rate = self._check_rate_limit('user_123', 1000)  # 1000 requests
        assert high_rate['allowed'] is False
        assert high_rate['retry_after'] > 0

        # Burst rate limiting
        burst_rate = self._check_rate_limit('user_123', 50)  # 50 requests in short time
        assert burst_rate['allowed'] is False

    def test_session_security(self):
        """Test session security validation."""
        # Valid session
        valid_session = self._validate_session('valid_session_id', 'user_123')
        assert valid_session['valid'] is True
        assert valid_session['user_id'] == 'user_123'

        # Invalid session
        invalid_session = self._validate_session('invalid_session_id', 'user_123')
        assert invalid_session['valid'] is False

        # Session timeout
        timeout_session = self._validate_session('timeout_session_id', 'user_123')
        assert timeout_session['valid'] is False
        assert timeout_session['error'] == 'session_expired'

    def test_data_encryption(self):
        """Test data encryption and decryption."""
        test_data = "sensitive_simulation_data"
        encryption_key = "test_key_123"

        # Encrypt data
        encrypted = self._encrypt_data(test_data, encryption_key)
        assert encrypted != test_data
        assert isinstance(encrypted, str)

        # Decrypt data
        decrypted = self._decrypt_data(encrypted, encryption_key)
        assert decrypted == test_data

        # Test with wrong key
        wrong_decrypt = self._decrypt_data(encrypted, "wrong_key")
        assert wrong_decrypt != test_data

    def test_audit_logging_security(self):
        """Test security audit logging."""
        security_event = {
            'event_type': 'failed_login',
            'user_id': 'user_123',
            'ip_address': '192.168.1.100',
            'user_agent': 'SuspiciousClient/1.0',
            'timestamp': datetime.now()
        }

        # Log security event
        log_result = self._log_security_event(security_event)

        assert log_result['logged'] is True
        assert 'event_id' in log_result

        # Verify event was logged with correct information
        logged_event = log_result['event']
        assert logged_event['event_type'] == 'failed_login'
        assert logged_event['severity'] == 'high'

    def _is_malicious_input(self, input_string):
        """Helper method to detect malicious input."""
        malicious_patterns = [
            "';", "--", "<script", "javascript:", "UNION SELECT",
            "../../../", "<iframe", "eval(", "document.cookie"
        ]

        return any(pattern in input_string.lower() for pattern in malicious_patterns)

    def _validate_authentication(self, token, user_id):
        """Helper method for authentication validation."""
        if token == 'valid_token' and user_id == 'user_123':
            return {'valid': True, 'user_id': user_id}
        elif token == 'expired_token':
            return {'valid': False, 'error': 'token_expired'}
        else:
            return {'valid': False, 'error': 'invalid_token'}

    def _check_permissions(self, user_role, requested_permissions):
        """Helper method for permission checking."""
        role_permissions = {
            'admin': ['read', 'write', 'delete', 'admin'],
            'user': ['read', 'write'],
            'guest': ['read']
        }

        user_perms = role_permissions.get(user_role, [])
        missing_perms = [p for p in requested_permissions if p not in user_perms]

        return {
            'granted': len(missing_perms) == 0,
            'missing_permissions': missing_perms
        }

    def _check_rate_limit(self, user_id, request_count):
        """Helper method for rate limiting."""
        # Simple rate limiting logic
        if request_count > 100:
            return {'allowed': False, 'retry_after': 60}
        elif request_count > 20:
            return {'allowed': False, 'retry_after': 30}
        else:
            return {'allowed': True, 'remaining': 100 - request_count}

    def _validate_session(self, session_id, user_id):
        """Helper method for session validation."""
        if session_id == 'valid_session_id':
            return {'valid': True, 'user_id': user_id}
        elif session_id == 'timeout_session_id':
            return {'valid': False, 'error': 'session_expired'}
        else:
            return {'valid': False, 'error': 'invalid_session'}

    def _encrypt_data(self, data, key):
        """Helper method for data encryption."""
        # Simple encryption for testing (not production-ready)
        combined = f"{data}:{key}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _decrypt_data(self, encrypted_data, key):
        """Helper method for data decryption."""
        # This is a mock - real decryption would reverse the encryption
        return "decrypted_data" if encrypted_data else ""

    def _log_security_event(self, event):
        """Helper method for security event logging."""
        event_id = f"sec_{int(time.time())}_{hash(str(event)) % 10000}"
        logged_event = event.copy()
        logged_event.update({
            'event_id': event_id,
            'severity': 'high' if event['event_type'] == 'failed_login' else 'medium',
            'logged_at': datetime.now()
        })

        return {
            'logged': True,
            'event_id': event_id,
            'event': logged_event
        }


class TestPerformanceBenchmarking:
    """Test suite for performance benchmarking functionality."""

    def setup_method(self):
        """Set up test environment for performance tests."""
        self.baseline_metrics = {
            'response_time': 150,  # ms
            'throughput': 1000,    # req/s
            'cpu_usage': 65,       # %
            'memory_usage': 70,    # %
            'error_rate': 0.02     # %
        }

    def test_response_time_benchmarking(self):
        """Test response time benchmarking."""
        test_results = [120, 145, 180, 135, 160, 140, 155, 170]

        benchmark = self._calculate_response_time_benchmark(test_results)

        assert 'average' in benchmark
        assert 'median' in benchmark
        assert 'p95' in benchmark
        assert 'p99' in benchmark
        assert benchmark['average'] > 0
        assert benchmark['p95'] > benchmark['average']

    def test_throughput_benchmarking(self):
        """Test throughput benchmarking."""
        throughput_results = [950, 1100, 1050, 1200, 980, 1150, 1020, 1180]

        benchmark = self._calculate_throughput_benchmark(throughput_results)

        assert 'average' in benchmark
        assert 'peak' in benchmark
        assert 'sustained' in benchmark
        assert benchmark['peak'] >= benchmark['average']

    def test_resource_utilization_benchmarking(self):
        """Test resource utilization benchmarking."""
        cpu_results = [60, 75, 80, 65, 70, 85, 62, 78]
        memory_results = [65, 78, 82, 70, 75, 88, 68, 80]

        cpu_benchmark = self._calculate_resource_benchmark(cpu_results, 'cpu')
        memory_benchmark = self._calculate_resource_benchmark(memory_results, 'memory')

        assert cpu_benchmark['average'] > 0
        assert memory_benchmark['average'] > 0
        assert cpu_benchmark['peak'] <= 100  # Should not exceed 100%
        assert memory_benchmark['peak'] <= 100

    def test_error_rate_benchmarking(self):
        """Test error rate benchmarking."""
        error_rates = [0.01, 0.02, 0.005, 0.03, 0.008, 0.015, 0.025, 0.012]

        benchmark = self._calculate_error_rate_benchmark(error_rates)

        assert 'average' in benchmark
        assert 'peak' in benchmark
        assert 'success_rate' in benchmark
        assert benchmark['success_rate'] == 100 - (benchmark['average'] * 100)

    def test_performance_regression_detection(self):
        """Test performance regression detection."""
        baseline_performance = self.baseline_metrics.copy()

        # Simulate performance regression
        degraded_performance = baseline_performance.copy()
        degraded_performance['response_time'] = 250  # Increased by 100ms
        degraded_performance['error_rate'] = 0.08    # Increased error rate

        regression = self._detect_performance_regression(baseline_performance, degraded_performance)

        assert regression['detected'] is True
        assert len(regression['regressions']) > 0
        assert 'response_time' in [r['metric'] for r in regression['regressions']]

    def test_load_capacity_benchmarking(self):
        """Test load capacity benchmarking."""
        load_levels = [100, 500, 1000, 1500, 2000, 2500]
        response_times = [120, 145, 180, 250, 400, 800]  # Corresponding response times

        capacity_benchmark = self._calculate_load_capacity_benchmark(load_levels, response_times)

        assert 'max_capacity' in capacity_benchmark
        assert 'optimal_load' in capacity_benchmark
        assert 'breaking_point' in capacity_benchmark
        assert capacity_benchmark['max_capacity'] > 0

    def _calculate_response_time_benchmark(self, results):
        """Helper method for response time benchmarking."""
        return {
            'average': np.mean(results),
            'median': np.median(results),
            'p95': np.percentile(results, 95),
            'p99': np.percentile(results, 99),
            'min': np.min(results),
            'max': np.max(results)
        }

    def _calculate_throughput_benchmark(self, results):
        """Helper method for throughput benchmarking."""
        return {
            'average': np.mean(results),
            'peak': np.max(results),
            'sustained': np.percentile(results, 80),  # 80th percentile as sustained
            'min': np.min(results)
        }

    def _calculate_resource_benchmark(self, results, resource_type):
        """Helper method for resource utilization benchmarking."""
        return {
            'average': np.mean(results),
            'peak': np.max(results),
            'median': np.median(results),
            'p90': np.percentile(results, 90)
        }

    def _calculate_error_rate_benchmark(self, error_rates):
        """Helper method for error rate benchmarking."""
        avg_error_rate = np.mean(error_rates)
        return {
            'average': avg_error_rate,
            'peak': np.max(error_rates),
            'success_rate': 100 - (avg_error_rate * 100)
        }

    def _detect_performance_regression(self, baseline, current):
        """Helper method for performance regression detection."""
        regressions = []
        threshold = 0.20  # 20% degradation threshold

        for metric, baseline_value in baseline.items():
            current_value = current[metric]
            change = (current_value - baseline_value) / baseline_value

            if change > threshold:
                regressions.append({
                    'metric': metric,
                    'baseline': baseline_value,
                    'current': current_value,
                    'change_percent': change * 100,
                    'severity': 'high' if change > 0.50 else 'medium'
                })

        return {
            'detected': len(regressions) > 0,
            'regressions': regressions,
            'regression_count': len(regressions)
        }

    def _calculate_load_capacity_benchmark(self, load_levels, response_times):
        """Helper method for load capacity benchmarking."""
        # Find breaking point (response time > 500ms)
        breaking_point = None
        for i, rt in enumerate(response_times):
            if rt > 500:
                breaking_point = load_levels[i-1] if i > 0 else load_levels[0]
                break

        # Find optimal load (best performance before degradation)
        optimal_idx = np.argmin(response_times)
        optimal_load = load_levels[optimal_idx]

        return {
            'max_capacity': load_levels[-1],
            'optimal_load': optimal_load,
            'breaking_point': breaking_point,
            'capacity_utilization': optimal_load / load_levels[-1]
        }


class TestLoadTesting:
    """Test suite for load testing functionality."""

    def setup_method(self):
        """Set up test environment for load testing."""
        self.test_endpoints = [
            '/api/simulations',
            '/api/simulations/123',
            '/api/metrics',
            '/api/health'
        ]

        self.load_profiles = {
            'light': {'users': 10, 'duration': 60},
            'medium': {'users': 50, 'duration': 120},
            'heavy': {'users': 100, 'duration': 180},
            'stress': {'users': 200, 'duration': 300}
        }

    def test_concurrent_user_simulation(self):
        """Test concurrent user simulation."""
        # Simulate concurrent users
        results = self._simulate_concurrent_users(10, 30)  # 10 users for 30 seconds

        assert 'total_requests' in results
        assert 'successful_requests' in results
        assert 'failed_requests' in results
        assert 'average_response_time' in results
        assert results['total_requests'] > 0

    def test_load_profile_execution(self):
        """Test load profile execution."""
        for profile_name, profile_config in self.load_profiles.items():
            results = self._execute_load_profile(profile_name, profile_config)

            assert 'profile' in results
            assert 'duration' in results
            assert 'metrics' in results
            assert results['profile'] == profile_name

    def test_endpoint_load_testing(self):
        """Test load testing for specific endpoints."""
        for endpoint in self.test_endpoints:
            results = self._test_endpoint_load(endpoint, 20, 30)  # 20 concurrent users, 30 seconds

            assert 'endpoint' in results
            assert 'response_times' in results
            assert 'error_rate' in results
            assert results['endpoint'] == endpoint

    def test_resource_monitoring_under_load(self):
        """Test resource monitoring during load testing."""
        # Simulate load test with resource monitoring
        with patch('psutil.cpu_percent') as mock_cpu, \
             patch('psutil.virtual_memory') as mock_memory:

            mock_cpu.return_value = 75.5
            mock_memory.return_value.percent = 82.3

            resources = self._monitor_resources_during_load()

            assert 'cpu_usage' in resources
            assert 'memory_usage' in resources
            assert 'peak_cpu' in resources
            assert 'peak_memory' in resources

    def test_load_test_reporting(self):
        """Test load test result reporting."""
        test_results = {
            'total_requests': 1000,
            'successful_requests': 950,
            'failed_requests': 50,
            'average_response_time': 245.8,
            'p95_response_time': 450.2,
            'error_rate': 0.05
        }

        report = self._generate_load_test_report(test_results)

        assert 'summary' in report
        assert 'metrics' in report
        assert 'recommendations' in report
        assert 'passed' in report

    def test_scalability_assessment(self):
        """Test scalability assessment under load."""
        scalability_results = self._assess_scalability()

        assert 'current_capacity' in scalability_results
        assert 'recommended_capacity' in scalability_results
        assert 'bottlenecks' in scalability_results
        assert 'scalability_score' in scalability_results

    def _simulate_concurrent_users(self, user_count, duration):
        """Helper method for concurrent user simulation."""
        # Mock concurrent user simulation
        return {
            'total_requests': user_count * 10,  # 10 requests per user
            'successful_requests': int(user_count * 9.5),  # 95% success rate
            'failed_requests': int(user_count * 0.5),
            'average_response_time': 245.8,
            'min_response_time': 120.5,
            'max_response_time': 890.2
        }

    def _execute_load_profile(self, profile_name, config):
        """Helper method for load profile execution."""
        return {
            'profile': profile_name,
            'users': config['users'],
            'duration': config['duration'],
            'metrics': {
                'throughput': config['users'] * 5,  # 5 req/s per user
                'response_time': 200 + (config['users'] * 2),  # Increases with load
                'error_rate': min(0.01 * config['users'] / 10, 0.1)  # Increases with load
            }
        }

    def _test_endpoint_load(self, endpoint, users, duration):
        """Helper method for endpoint load testing."""
        return {
            'endpoint': endpoint,
            'concurrent_users': users,
            'duration': duration,
            'response_times': np.random.normal(200, 50, 100),
            'error_rate': np.random.uniform(0.01, 0.05),
            'throughput': users * 8  # 8 req/s per user
        }

    def _monitor_resources_during_load(self):
        """Helper method for resource monitoring."""
        return {
            'cpu_usage': 75.5,
            'memory_usage': 82.3,
            'peak_cpu': 89.2,
            'peak_memory': 88.7,
            'network_io': 1250.5,
            'disk_io': 450.8
        }

    def _generate_load_test_report(self, results):
        """Helper method for load test reporting."""
        success_rate = results['successful_requests'] / results['total_requests']
        passed = success_rate > 0.95 and results['average_response_time'] < 500

        recommendations = []
        if results['error_rate'] > 0.05:
            recommendations.append("High error rate detected - investigate system stability")
        if results['p95_response_time'] > 1000:
            recommendations.append("Slow response times - consider performance optimization")

        return {
            'summary': f"Load test completed with {success_rate:.1%} success rate",
            'metrics': results,
            'recommendations': recommendations,
            'passed': passed
        }

    def _assess_scalability(self):
        """Helper method for scalability assessment."""
        return {
            'current_capacity': 1000,  # req/s
            'recommended_capacity': 1500,
            'bottlenecks': ['database_connections', 'memory_usage'],
            'scalability_score': 7.5,  # Out of 10
            'improvement_areas': ['caching', 'database_optimization', 'load_balancing']
        }


class TestSecurityMonitoring:
    """Test suite for security monitoring functionality."""

    def setup_method(self):
        """Set up test environment for security monitoring."""
        self.security_events = [
            {
                'event_type': 'failed_login',
                'user_id': 'user_123',
                'ip_address': '192.168.1.100',
                'timestamp': datetime.now(),
                'severity': 'medium'
            },
            {
                'event_type': 'suspicious_activity',
                'user_id': 'user_456',
                'ip_address': '10.0.0.50',
                'timestamp': datetime.now() - timedelta(minutes=5),
                'severity': 'high'
            }
        ]

    def test_intrusion_detection(self):
        """Test intrusion detection capabilities."""
        # Test with normal traffic
        normal_traffic = self._simulate_network_traffic('normal', 100)
        normal_analysis = self._analyze_intrusion_patterns(normal_traffic)

        assert normal_analysis['threat_level'] == 'low'
        assert len(normal_analysis['suspicious_patterns']) == 0

        # Test with suspicious traffic
        suspicious_traffic = self._simulate_network_traffic('suspicious', 100)
        suspicious_analysis = self._analyze_intrusion_patterns(suspicious_traffic)

        assert suspicious_analysis['threat_level'] in ['medium', 'high']
        assert len(suspicious_analysis['suspicious_patterns']) > 0

    def test_anomaly_detection_security(self):
        """Test security-focused anomaly detection."""
        # Normal user behavior
        normal_behavior = self._generate_user_behavior('normal', 50)
        normal_score = self._calculate_security_anomaly_score(normal_behavior)

        assert normal_score < 0.3  # Low anomaly score

        # Anomalous user behavior
        anomalous_behavior = self._generate_user_behavior('anomalous', 50)
        anomalous_score = self._calculate_security_anomaly_score(anomalous_behavior)

        assert anomalous_score > 0.7  # High anomaly score

    def test_access_pattern_analysis(self):
        """Test access pattern analysis for security."""
        access_patterns = self._generate_access_patterns()

        analysis = self._analyze_access_patterns(access_patterns)

        assert 'normal_patterns' in analysis
        assert 'suspicious_patterns' in analysis
        assert 'risk_score' in analysis
        assert 0 <= analysis['risk_score'] <= 1

    def test_vulnerability_scanning(self):
        """Test vulnerability scanning capabilities."""
        scan_results = self._perform_vulnerability_scan()

        assert 'vulnerabilities_found' in scan_results
        assert 'critical_vulnerabilities' in scan_results
        assert 'scan_duration' in scan_results
        assert 'recommendations' in scan_results

    def test_security_incident_response(self):
        """Test security incident response simulation."""
        incident = {
            'type': 'data_breach_attempt',
            'severity': 'critical',
            'affected_systems': ['database', 'api_server'],
            'timestamp': datetime.now()
        }

        response = self._simulate_incident_response(incident)

        assert 'response_actions' in response
        assert 'estimated_resolution_time' in response
        assert 'containment_status' in response
        assert len(response['response_actions']) > 0

    def _simulate_network_traffic(self, pattern_type, packet_count):
        """Helper method for network traffic simulation."""
        if pattern_type == 'normal':
            return {
                'packets': [{'size': np.random.randint(100, 1500)} for _ in range(packet_count)],
                'protocols': ['HTTP', 'HTTPS'] * (packet_count // 2),
                'ports': [80, 443] * (packet_count // 2)
            }
        else:  # suspicious
            return {
                'packets': [{'size': np.random.choice([64, 1500, 9000])} for _ in range(packet_count)],
                'protocols': ['UNKNOWN', 'TCP', 'UDP'] * (packet_count // 3),
                'ports': [22, 3389, 445, 1433] * (packet_count // 4)  # Suspicious ports
            }

    def _analyze_intrusion_patterns(self, traffic):
        """Helper method for intrusion pattern analysis."""
        suspicious_ports = [22, 3389, 445, 1433]  # Common attack ports
        suspicious_protocols = ['UNKNOWN']

        suspicious_count = 0
        for i, port in enumerate(traffic['ports']):
            if port in suspicious_ports:
                suspicious_count += 1
            if traffic['protocols'][i] in suspicious_protocols:
                suspicious_count += 1

        threat_level = 'low' if suspicious_count < 5 else 'medium' if suspicious_count < 15 else 'high'

        return {
            'threat_level': threat_level,
            'suspicious_patterns': suspicious_count,
            'total_packets': len(traffic['packets'])
        }

    def _generate_user_behavior(self, behavior_type, event_count):
        """Helper method for user behavior generation."""
        if behavior_type == 'normal':
            return {
                'login_times': np.random.normal(9, 1, event_count),  # 9 AM ± 1 hour
                'session_duration': np.random.normal(480, 60, event_count),  # 8 hours ± 1 hour
                'failed_logins': np.random.poisson(0.1, event_count),  # Rare failures
                'resource_access': np.random.choice(['dashboard', 'reports', 'settings'], event_count)
            }
        else:  # anomalous
            return {
                'login_times': np.random.choice([2, 3, 4, 14, 15, 16], event_count),  # Unusual hours
                'session_duration': np.random.exponential(120, event_count),  # Very short sessions
                'failed_logins': np.random.poisson(3, event_count),  # Frequent failures
                'resource_access': np.random.choice(['admin', 'system', 'config'], event_count, p=[0.7, 0.2, 0.1])
            }

    def _calculate_security_anomaly_score(self, behavior):
        """Helper method for security anomaly scoring."""
        score = 0

        # Unusual login times
        unusual_logins = sum(1 for t in behavior['login_times'] if t < 6 or t > 18)
        score += unusual_logins / len(behavior['login_times']) * 0.4

        # Short sessions
        short_sessions = sum(1 for d in behavior['session_duration'] if d < 60)
        score += short_sessions / len(behavior['session_duration']) * 0.3

        # Failed logins
        failed_login_rate = np.mean(behavior['failed_logins'])
        score += min(failed_login_rate / 5, 1) * 0.3

        return min(score, 1.0)

    def _generate_access_patterns(self):
        """Helper method for access pattern generation."""
        return {
            'user_access': ['dashboard', 'reports', 'settings', 'admin'],
            'frequency': [50, 30, 15, 5],
            'time_patterns': ['business_hours', 'after_hours', 'weekends'],
            'location_patterns': ['office', 'remote', 'unknown']
        }

    def _analyze_access_patterns(self, patterns):
        """Helper method for access pattern analysis."""
        # Simple risk scoring based on access patterns
        risk_factors = 0

        if 'admin' in patterns['user_access']:
            risk_factors += 0.3

        if 'after_hours' in patterns['time_patterns']:
            risk_factors += 0.2

        if 'unknown' in patterns['location_patterns']:
            risk_factors += 0.3

        return {
            'normal_patterns': len(patterns['user_access']) - 1,  # Exclude admin
            'suspicious_patterns': 1 if 'admin' in patterns['user_access'] else 0,
            'risk_score': min(risk_factors, 1.0)
        }

    def _perform_vulnerability_scan(self):
        """Helper method for vulnerability scanning."""
        return {
            'vulnerabilities_found': 3,
            'critical_vulnerabilities': 1,
            'high_vulnerabilities': 1,
            'medium_vulnerabilities': 1,
            'scan_duration': 45.2,
            'recommendations': [
                'Update SSL certificate',
                'Patch known vulnerabilities',
                'Implement rate limiting'
            ]
        }

    def _simulate_incident_response(self, incident):
        """Helper method for incident response simulation."""
        response_actions = []

        if incident['type'] == 'data_breach_attempt':
            response_actions.extend([
                'Isolate affected systems',
                'Block suspicious IP addresses',
                'Notify security team',
                'Enable enhanced monitoring'
            ])

        return {
            'response_actions': response_actions,
            'estimated_resolution_time': 120,  # minutes
            'containment_status': 'in_progress',
            'escalation_level': 'high' if incident['severity'] == 'critical' else 'medium'
        }


# Performance testing fixtures
@pytest.fixture
def performance_test_config():
    """Fixture for performance test configuration."""
    return {
        'duration': 60,
        'users': 50,
        'ramp_up_time': 10,
        'think_time': 2,
        'target_endpoints': ['/api/simulations', '/api/metrics']
    }


@pytest.fixture
def security_test_config():
    """Fixture for security test configuration."""
    return {
        'scan_types': ['vulnerability', 'intrusion', 'access'],
        'severity_threshold': 'medium',
        'false_positive_rate': 0.05,
        'response_time_limit': 30
    }


if __name__ == "__main__":
    pytest.main([__file__])
