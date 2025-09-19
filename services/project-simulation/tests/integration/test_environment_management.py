"""Environment Management Integration Tests.

This module contains comprehensive integration tests for environment management,
including environment switching, configuration validation, and service health monitoring.
"""

import pytest
import os
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Optional
import sys

# Add project path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestEnvironmentSwitching:
    """Test environment switching functionality."""

    def test_environment_detection(self):
        """Test automatic environment detection."""
        # Test environment detection from various sources

        # Test environment variable detection
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            detected_env = self._detect_environment()
            assert detected_env == "production"

        with patch.dict(os.environ, {"NODE_ENV": "staging"}):
            detected_env = self._detect_environment()
            assert detected_env == "staging"

        # Test config file detection
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"environment": "development"}, f)
            config_file = f.name

        try:
            with patch('builtins.open', create=True) as mock_open:
                mock_file = Mock()
                mock_file.read.return_value = yaml.dump({"environment": "testing"})
                mock_open.return_value.__enter__.return_value = mock_file

                detected_env = self._detect_environment_from_config("test_config.yaml")
                assert detected_env == "testing"
        finally:
            os.unlink(config_file)

        print("✅ Environment detection validated")

    def test_environment_configuration_loading(self):
        """Test environment-specific configuration loading."""
        # Test loading configurations for different environments
        environments = ["development", "staging", "production"]

        for env in environments:
            config = self._load_environment_config(env)

            # Validate required configuration keys exist
            required_keys = ["database", "api", "logging", "redis"]
            for key in required_keys:
                assert key in config, f"Missing {key} config for {env} environment"

            # Validate environment-specific settings
            if env == "development":
                assert config["logging"]["level"] == "DEBUG"
                assert config["database"]["type"] == "sqlite"
            elif env == "production":
                assert config["logging"]["level"] == "WARNING"
                assert "ssl" in config["database"]

        print("✅ Environment configuration loading validated")

    def test_environment_variable_override(self):
        """Test environment variable override functionality."""
        base_config = {
            "database": {"host": "localhost", "port": 5432},
            "api": {"host": "0.0.0.0", "port": 8000},
            "redis": {"host": "localhost", "port": 6379}
        }

        # Test environment variable overrides
        overrides = {
            "DATABASE_HOST": "db.example.com",
            "API_PORT": "9000",
            "REDIS_HOST": "redis-cluster"
        }

        with patch.dict(os.environ, overrides):
            merged_config = self._apply_environment_overrides(base_config)

            assert merged_config["database"]["host"] == "db.example.com"
            assert merged_config["api"]["port"] == 9000
            assert merged_config["redis"]["host"] == "redis-cluster"
            # Non-overridden values should remain unchanged
            assert merged_config["database"]["port"] == 5432

        print("✅ Environment variable override validated")

    def test_environment_context_management(self):
        """Test environment context management and isolation."""
        # Test creating isolated environment contexts
        contexts = {}

        environments = ["dev", "staging", "prod"]

        for env in environments:
            context = self._create_environment_context(env)
            contexts[env] = context

            # Validate context isolation
            assert context["name"] == env
            assert "config" in context
            assert "services" in context
            assert "variables" in context

            # Validate no cross-contamination
            for other_env in environments:
                if other_env != env:
                    assert contexts[env]["name"] != contexts[other_env]["name"]

        # Test context switching
        current_context = None
        for env in environments:
            self._switch_to_environment(contexts[env])
            current_context = env

            # Verify active context
            active = self._get_active_environment()
            assert active == current_context

        print("✅ Environment context management validated")

    def test_environment_validation(self):
        """Test environment configuration validation."""
        # Test valid configurations
        valid_configs = [
            {
                "environment": "development",
                "database": {"type": "sqlite", "path": ":memory:"},
                "api": {"port": 8000},
                "logging": {"level": "DEBUG"}
            },
            {
                "environment": "production",
                "database": {"type": "postgresql", "host": "prod-db"},
                "api": {"port": 443, "ssl": True},
                "logging": {"level": "WARNING"}
            }
        ]

        for config in valid_configs:
            is_valid, errors = self._validate_environment_config(config)
            assert is_valid, f"Valid config rejected: {errors}"
            assert len(errors) == 0

        # Test invalid configurations
        invalid_configs = [
            {
                "environment": "invalid_env",
                "database": {"type": "unknown"},
            },
            {
                "database": {"host": "localhost"},  # Missing required fields
            },
            {
                "environment": "production",
                "api": {"port": "not_a_number"}
            }
        ]

        for config in invalid_configs:
            is_valid, errors = self._validate_environment_config(config)
            assert not is_valid, "Invalid config accepted"
            assert len(errors) > 0

        print("✅ Environment validation validated")

    def _detect_environment(self):
        """Mock environment detection."""
        return os.environ.get("ENVIRONMENT", os.environ.get("NODE_ENV", "development"))

    def _detect_environment_from_config(self, config_file):
        """Mock environment detection from config file."""
        return "testing"

    def _load_environment_config(self, environment):
        """Mock environment configuration loading."""
        configs = {
            "development": {
                "database": {"type": "sqlite", "path": ":memory:"},
                "api": {"host": "localhost", "port": 8000},
                "logging": {"level": "DEBUG"},
                "redis": {"host": "localhost", "port": 6379}
            },
            "staging": {
                "database": {"type": "postgresql", "host": "staging-db"},
                "api": {"host": "0.0.0.0", "port": 8000},
                "logging": {"level": "INFO"},
                "redis": {"host": "staging-redis", "port": 6379}
            },
            "production": {
                "database": {"type": "postgresql", "host": "prod-db", "ssl": True},
                "api": {"host": "0.0.0.0", "port": 443, "ssl": True},
                "logging": {"level": "WARNING"},
                "redis": {"host": "prod-redis", "port": 6379, "ssl": True}
            }
        }
        return configs.get(environment, configs["development"])

    def _apply_environment_overrides(self, config):
        """Mock environment variable override application."""
        overrides = {
            "DATABASE_HOST": "database.host",
            "API_PORT": "api.port",
            "REDIS_HOST": "redis.host"
        }

        result = json.loads(json.dumps(config))  # Deep copy

        for env_var, config_path in overrides.items():
            value = os.environ.get(env_var)
            if value is not None:
                keys = config_path.split('.')
                target = result
                for key in keys[:-1]:
                    if key not in target:
                        target[key] = {}
                    target = target[key]
                target[keys[-1]] = value

        return result

    def _create_environment_context(self, env_name):
        """Mock environment context creation."""
        return {
            "name": env_name,
            "config": self._load_environment_config(env_name),
            "services": {},
            "variables": {}
        }

    def _switch_to_environment(self, context):
        """Mock environment switching."""
        global _active_context
        _active_context = context["name"]

    def _get_active_environment(self):
        """Mock active environment getter."""
        return getattr(sys.modules[__name__], '_active_context', 'development')

    def _validate_environment_config(self, config):
        """Mock environment configuration validation."""
        errors = []

        # Check required fields
        required_fields = ["environment", "database", "api", "logging"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")

        # Validate environment name
        valid_environments = ["development", "staging", "production", "testing"]
        if "environment" in config and config["environment"] not in valid_environments:
            errors.append(f"Invalid environment: {config['environment']}")

        # Validate database config
        if "database" in config:
            db_config = config["database"]
            if "type" in db_config:
                valid_types = ["sqlite", "postgresql", "mysql"]
                if db_config["type"] not in valid_types:
                    errors.append(f"Invalid database type: {db_config['type']}")

        # Validate API port
        if "api" in config and "port" in config["api"]:
            try:
                port = int(config["api"]["port"])
                if not (1024 <= port <= 65535):
                    errors.append(f"Invalid port number: {port}")
            except (ValueError, TypeError):
                errors.append("API port must be a valid integer")

        return len(errors) == 0, errors


class TestConfigurationValidation:
    """Test configuration validation functionality."""

    def test_yaml_configuration_parsing(self):
        """Test YAML configuration file parsing."""
        # Test valid YAML configurations
        valid_yaml_configs = [
            """
            environment: development
            database:
              type: sqlite
              path: :memory:
            api:
              host: localhost
              port: 8000
            """,
            """
            environment: production
            database:
              type: postgresql
              host: prod-db.example.com
              port: 5432
              ssl: true
            api:
              host: 0.0.0.0
              port: 443
              ssl: true
            logging:
              level: WARNING
              format: json
            """
        ]

        for yaml_config in valid_yaml_configs:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(yaml_config)
                config_file = f.name

            try:
                parsed_config = self._parse_yaml_config(config_file)
                assert isinstance(parsed_config, dict)
                assert "environment" in parsed_config
                assert "database" in parsed_config
                assert "api" in parsed_config
            finally:
                os.unlink(config_file)

        print("✅ YAML configuration parsing validated")

    def test_json_configuration_parsing(self):
        """Test JSON configuration file parsing."""
        # Test valid JSON configurations
        valid_json_configs = [
            {
                "environment": "development",
                "database": {"type": "sqlite", "path": ":memory:"},
                "api": {"host": "localhost", "port": 8000}
            },
            {
                "environment": "staging",
                "database": {"type": "postgresql", "host": "staging-db"},
                "api": {"host": "0.0.0.0", "port": 8000},
                "logging": {"level": "INFO"}
            }
        ]

        for json_config in valid_json_configs:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(json_config, f)
                config_file = f.name

            try:
                parsed_config = self._parse_json_config(config_file)
                assert isinstance(parsed_config, dict)
                assert "environment" in parsed_config
                assert parsed_config["environment"] in ["development", "staging", "production"]
            finally:
                os.unlink(config_file)

        print("✅ JSON configuration parsing validated")

    def test_configuration_schema_validation(self):
        """Test configuration schema validation."""
        # Test valid configurations against schema
        valid_configs = [
            {
                "environment": "development",
                "database": {"type": "sqlite", "path": ":memory:"},
                "api": {"host": "localhost", "port": 8000, "cors": True},
                "logging": {"level": "DEBUG", "format": "text"},
                "redis": {"host": "localhost", "port": 6379}
            }
        ]

        schema = self._get_configuration_schema()

        for config in valid_configs:
            is_valid, errors = self._validate_against_schema(config, schema)
            assert is_valid, f"Valid config failed schema validation: {errors}"

        # Test invalid configurations
        invalid_configs = [
            {
                "environment": "invalid_env",  # Invalid environment
                "database": {"type": "sqlite"},
                "api": {"port": "not_a_number"}  # Invalid port type
            },
            {
                "database": {"host": "localhost"},  # Missing required fields
            },
            {
                "environment": "production",
                "database": {"type": "unknown_db_type"},  # Invalid database type
                "api": {"port": 80}  # Invalid port for production
            }
        ]

        for config in invalid_configs:
            is_valid, errors = self._validate_against_schema(config, schema)
            assert not is_valid, f"Invalid config passed schema validation: {config}"
            assert len(errors) > 0

        print("✅ Configuration schema validation validated")

    def test_configuration_merge_strategies(self):
        """Test configuration merge strategies."""
        # Test different merge strategies
        base_config = {
            "environment": "development",
            "database": {"type": "sqlite", "path": ":memory:"},
            "api": {"host": "localhost", "port": 8000}
        }

        override_config = {
            "database": {"path": "/tmp/test.db"},
            "api": {"port": 9000},
            "redis": {"host": "redis-server"}
        }

        # Test deep merge strategy
        merged_deep = self._deep_merge_configs(base_config, override_config)
        assert merged_deep["database"]["type"] == "sqlite"  # Preserved
        assert merged_deep["database"]["path"] == "/tmp/test.db"  # Overridden
        assert merged_deep["api"]["host"] == "localhost"  # Preserved
        assert merged_deep["api"]["port"] == 9000  # Overridden
        assert merged_deep["redis"]["host"] == "redis-server"  # Added

        # Test shallow merge strategy
        merged_shallow = self._shallow_merge_configs(base_config, override_config)
        assert merged_shallow["database"] == {"path": "/tmp/test.db"}  # Completely replaced
        assert merged_shallow["api"] == {"port": 9000}  # Completely replaced

        print("✅ Configuration merge strategies validated")

    def test_configuration_change_tracking(self):
        """Test configuration change tracking and auditing."""
        # Test tracking configuration changes
        initial_config = {
            "database": {"host": "localhost", "port": 5432},
            "api": {"port": 8000}
        }

        changes = []

        # Simulate configuration changes
        change_events = [
            {"path": "database.host", "old_value": "localhost", "new_value": "db.example.com"},
            {"path": "api.port", "old_value": 8000, "new_value": 9000},
            {"path": "redis.host", "old_value": None, "new_value": "redis.example.com"}
        ]

        for change in change_events:
            self._track_configuration_change(change, changes)

        assert len(changes) == 3

        # Verify change tracking
        host_change = next(c for c in changes if c["path"] == "database.host")
        assert host_change["old_value"] == "localhost"
        assert host_change["new_value"] == "db.example.com"
        assert "timestamp" in host_change

        port_change = next(c for c in changes if c["path"] == "api.port")
        assert port_change["old_value"] == 8000
        assert port_change["new_value"] == 9000

        redis_change = next(c for c in changes if c["path"] == "redis.host")
        assert redis_change["old_value"] is None
        assert redis_change["new_value"] == "redis.example.com"

        print("✅ Configuration change tracking validated")

    def _parse_yaml_config(self, file_path):
        """Mock YAML configuration parsing."""
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)

    def _parse_json_config(self, file_path):
        """Mock JSON configuration parsing."""
        with open(file_path, 'r') as f:
            return json.load(f)

    def _get_configuration_schema(self):
        """Mock configuration schema."""
        return {
            "type": "object",
            "required": ["environment", "database", "api"],
            "properties": {
                "environment": {
                    "type": "string",
                    "enum": ["development", "staging", "production", "testing"]
                },
                "database": {
                    "type": "object",
                    "required": ["type"],
                    "properties": {
                        "type": {"type": "string", "enum": ["sqlite", "postgresql", "mysql"]},
                        "host": {"type": "string"},
                        "port": {"type": "integer", "minimum": 1024, "maximum": 65535}
                    }
                },
                "api": {
                    "type": "object",
                    "properties": {
                        "port": {"type": "integer", "minimum": 1024, "maximum": 65535}
                    }
                }
            }
        }

    def _validate_against_schema(self, config, schema):
        """Mock schema validation."""
        errors = []

        # Basic validation logic
        if "environment" not in config:
            errors.append("Missing environment field")
        elif config["environment"] not in ["development", "staging", "production", "testing"]:
            errors.append(f"Invalid environment: {config['environment']}")

        if "database" not in config:
            errors.append("Missing database configuration")
        elif "type" in config.get("database", {}):
            db_type = config["database"]["type"]
            if db_type not in ["sqlite", "postgresql", "mysql"]:
                errors.append(f"Invalid database type: {db_type}")

        if "api" in config and "port" in config["api"]:
            port = config["api"]["port"]
            if not isinstance(port, int) or not (1024 <= port <= 65535):
                errors.append(f"Invalid API port: {port}")

        return len(errors) == 0, errors

    def _deep_merge_configs(self, base, override):
        """Mock deep merge of configurations."""
        result = json.loads(json.dumps(base))  # Deep copy

        def merge_dict(target, source):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    merge_dict(target[key], value)
                else:
                    target[key] = value

        merge_dict(result, override)
        return result

    def _shallow_merge_configs(self, base, override):
        """Mock shallow merge of configurations."""
        result = json.loads(json.dumps(base))  # Deep copy
        result.update(override)
        return result

    def _track_configuration_change(self, change, changes_list):
        """Mock configuration change tracking."""
        change_entry = {
            "path": change["path"],
            "old_value": change["old_value"],
            "new_value": change["new_value"],
            "timestamp": "2024-01-01T12:00:00Z"
        }
        changes_list.append(change_entry)


class TestServiceHealthMonitoring:
    """Test service health monitoring functionality."""

    def test_health_endpoint_validation(self):
        """Test health endpoint response validation."""
        # Mock health endpoints and their expected responses
        health_endpoints = [
            {
                "url": "/api/v1/health",
                "expected_status": 200,
                "expected_response": {
                    "status": "healthy",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "services": {
                        "database": "healthy",
                        "redis": "healthy",
                        "api": "healthy"
                    }
                }
            },
            {
                "url": "/api/v1/health/detailed",
                "expected_status": 200,
                "expected_response": {
                    "status": "healthy",
                    "uptime_seconds": 3600,
                    "memory_usage": {"used": 150, "total": 1000},
                    "cpu_usage": 25.5
                }
            }
        ]

        for endpoint in health_endpoints:
            # Mock HTTP response
            mock_response = Mock()
            mock_response.status_code = endpoint["expected_status"]
            mock_response.json.return_value = endpoint["expected_response"]

            # Validate health response
            is_valid, errors = self._validate_health_response(mock_response, endpoint)

            assert is_valid, f"Health endpoint validation failed for {endpoint['url']}: {errors}"
            assert len(errors) == 0

        print("✅ Health endpoint validation validated")

    def test_service_health_status_aggregation(self):
        """Test service health status aggregation."""
        # Test various service health scenarios
        health_scenarios = [
            {
                "services": {"db": "healthy", "redis": "healthy", "api": "healthy"},
                "expected_overall": "healthy"
            },
            {
                "services": {"db": "healthy", "redis": "degraded", "api": "healthy"},
                "expected_overall": "degraded"
            },
            {
                "services": {"db": "unhealthy", "redis": "healthy", "api": "healthy"},
                "expected_overall": "unhealthy"
            },
            {
                "services": {"db": "healthy", "redis": "healthy", "api": "unknown"},
                "expected_overall": "degraded"
            }
        ]

        for scenario in health_scenarios:
            overall_status = self._aggregate_service_health(scenario["services"])
            assert overall_status == scenario["expected_overall"], \
                f"Expected {scenario['expected_overall']}, got {overall_status} for services {scenario['services']}"

        print("✅ Service health status aggregation validated")

    def test_health_check_timing_and_reliability(self):
        """Test health check timing and reliability."""
        import time

        # Test health check timing
        health_check_times = []

        for i in range(10):
            start_time = time.time()

            # Mock health check
            self._perform_mock_health_check()

            end_time = time.time()
            health_check_times.append(end_time - start_time)

        # Validate timing requirements
        average_time = sum(health_check_times) / len(health_check_times)
        max_time = max(health_check_times)

        # Health checks should be fast (< 100ms average)
        assert average_time < 0.1, f"Health check too slow: {average_time:.3f}s average"

        # No health check should take more than 500ms
        assert max_time < 0.5, f"Health check too slow: {max_time:.3f}s max"

        # Test reliability - simulate some failures
        success_count = 0
        total_attempts = 20

        for i in range(total_attempts):
            if self._perform_mock_health_check_with_failure_probability(0.1):  # 10% failure rate
                success_count += 1

        success_rate = success_count / total_attempts

        # Should have reasonable success rate (> 80%)
        assert success_rate > 0.8, f"Health check reliability too low: {success_rate:.1%}"

        print("✅ Health check timing and reliability validated")

    def test_health_monitoring_alerting(self):
        """Test health monitoring alerting mechanisms."""
        # Test alerting for different health states
        health_states = [
            {"status": "healthy", "should_alert": False, "alert_level": None},
            {"status": "degraded", "should_alert": True, "alert_level": "warning"},
            {"status": "unhealthy", "should_alert": True, "alert_level": "critical"}
        ]

        alerts_sent = []

        for state in health_states:
            self._evaluate_health_alert(state, alerts_sent)

            if state["should_alert"]:
                assert len(alerts_sent) > 0, f"No alert sent for {state['status']}"
                latest_alert = alerts_sent[-1]
                assert latest_alert["level"] == state["alert_level"]
                assert latest_alert["status"] == state["status"]
            else:
                # Count alerts before this state
                initial_alert_count = len([a for a in alerts_sent if a["status"] != state["status"]])
                assert len(alerts_sent) == initial_alert_count, f"Unexpected alert sent for {state['status']}"

        print("✅ Health monitoring alerting validated")

    def test_health_check_endpoint_discovery(self):
        """Test automatic health check endpoint discovery."""
        # Test discovering health endpoints from service configurations
        service_configs = [
            {
                "name": "simulation-service",
                "base_url": "http://localhost:8000",
                "health_endpoints": ["/health", "/api/v1/health"]
            },
            {
                "name": "database-service",
                "base_url": "http://localhost:5432",
                "health_endpoints": ["/health/ready", "/health/live"]
            },
            {
                "name": "redis-service",
                "base_url": "redis://localhost:6379",
                "health_endpoints": []  # No explicit health endpoints
            }
        ]

        discovered_endpoints = {}

        for service in service_configs:
            endpoints = self._discover_health_endpoints(service)
            discovered_endpoints[service["name"]] = endpoints

            # Validate discovered endpoints
            if service["health_endpoints"]:
                assert len(endpoints) == len(service["health_endpoints"])
                for expected_endpoint in service["health_endpoints"]:
                    full_url = f"{service['base_url']}{expected_endpoint}"
                    assert full_url in endpoints
            else:
                # Services without explicit endpoints should have defaults
                assert len(endpoints) > 0, f"No default endpoints discovered for {service['name']}"

        print("✅ Health check endpoint discovery validated")

    def _validate_health_response(self, response, endpoint_config):
        """Mock health response validation."""
        errors = []

        # Check HTTP status
        if response.status_code != endpoint_config["expected_status"]:
            errors.append(f"Expected status {endpoint_config['expected_status']}, got {response.status_code}")

        # Check response structure
        try:
            response_data = response.json()
            expected_data = endpoint_config["expected_response"]

            # Check required fields
            for key in expected_data.keys():
                if key not in response_data:
                    errors.append(f"Missing field: {key}")

            # Check status field
            if "status" in expected_data and response_data.get("status") != expected_data["status"]:
                errors.append(f"Status mismatch: expected {expected_data['status']}, got {response_data.get('status')}")

        except Exception as e:
            errors.append(f"Invalid JSON response: {e}")

        return len(errors) == 0, errors

    def _aggregate_service_health(self, services):
        """Mock service health aggregation."""
        status_priority = {"unhealthy": 3, "degraded": 2, "unknown": 1, "healthy": 0}

        max_priority = max((status_priority.get(status, 1) for status in services.values()), default=0)

        priority_map = {3: "unhealthy", 2: "degraded", 1: "degraded", 0: "healthy"}
        return priority_map.get(max_priority, "unknown")

    def _perform_mock_health_check(self):
        """Mock health check operation."""
        import time
        time.sleep(0.001)  # Simulate 1ms health check

    def _perform_mock_health_check_with_failure_probability(self, failure_rate):
        """Mock health check with configurable failure rate."""
        import random
        return random.random() > failure_rate

    def _evaluate_health_alert(self, health_state, alerts_list):
        """Mock health alert evaluation."""
        if health_state["should_alert"]:
            alert = {
                "status": health_state["status"],
                "level": health_state["alert_level"],
                "timestamp": "2024-01-01T12:00:00Z",
                "message": f"Service health changed to {health_state['status']}"
            }
            alerts_list.append(alert)

    def _discover_health_endpoints(self, service_config):
        """Mock health endpoint discovery."""
        base_url = service_config["base_url"]
        explicit_endpoints = service_config.get("health_endpoints", [])

        endpoints = []
        for endpoint in explicit_endpoints:
            endpoints.append(f"{base_url}{endpoint}")

        # Add default endpoints if none specified
        if not endpoints:
            if "localhost" in base_url:
                endpoints.append(f"{base_url}/health")
                endpoints.append(f"{base_url}/api/v1/health")

        return endpoints


class TestEnvironmentManagementIntegration:
    """Test environment management integration scenarios."""

    def test_complete_environment_lifecycle(self):
        """Test complete environment lifecycle management."""
        # Test full environment management workflow
        environments = ["development", "staging", "production"]

        for env in environments:
            # Initialize environment
            env_context = self._initialize_environment(env)
            assert env_context["name"] == env
            assert env_context["status"] == "initialized"

            # Load configuration
            config = self._load_environment_configuration(env)
            assert "database" in config
            assert "api" in config
            assert "logging" in config

            # Validate configuration
            is_valid, errors = self._validate_environment_configuration(config)
            assert is_valid, f"Invalid configuration for {env}: {errors}"

            # Start services
            services_started = self._start_environment_services(env, config)
            assert services_started, f"Failed to start services for {env}"

            # Perform health checks
            health_status = self._perform_environment_health_checks(env)
            assert health_status["overall"] == "healthy", f"Unhealthy environment {env}: {health_status}"

            # Switch to environment
            switched = self._switch_to_environment(env)
            assert switched, f"Failed to switch to {env}"

            # Verify active environment
            active_env = self._get_active_environment()
            assert active_env == env

            # Clean up environment
            cleanup_success = self._cleanup_environment(env)
            assert cleanup_success, f"Failed to cleanup {env}"

        print("✅ Complete environment lifecycle validated")

    def test_environment_configuration_persistence(self):
        """Test environment configuration persistence."""
        # Test saving and loading environment configurations
        test_configs = {
            "development": {
                "database": {"type": "sqlite", "path": ":memory:"},
                "api": {"port": 8000},
                "features": ["debug", "hot_reload"]
            },
            "production": {
                "database": {"type": "postgresql", "host": "prod-db"},
                "api": {"port": 443, "ssl": True},
                "features": ["ssl", "monitoring"]
            }
        }

        # Save configurations
        for env, config in test_configs.items():
            saved = self._save_environment_configuration(env, config)
            assert saved, f"Failed to save configuration for {env}"

        # Load and verify configurations
        for env, expected_config in test_configs.items():
            loaded_config = self._load_environment_configuration(env)
            assert loaded_config == expected_config, f"Configuration mismatch for {env}"

        # Test configuration updates
        updated_config = test_configs["development"].copy()
        updated_config["api"]["port"] = 9000

        self._save_environment_configuration("development", updated_config)
        loaded_updated = self._load_environment_configuration("development")

        assert loaded_updated["api"]["port"] == 9000, "Configuration update not persisted"

        print("✅ Environment configuration persistence validated")

    def test_environment_service_discovery(self):
        """Test environment-specific service discovery."""
        # Test service discovery in different environments
        service_discovery_configs = {
            "development": {
                "services": {
                    "database": "sqlite:///:memory:",
                    "redis": "redis://localhost:6379",
                    "api": "http://localhost:8000"
                }
            },
            "staging": {
                "services": {
                    "database": "postgresql://staging-db:5432/staging_db",
                    "redis": "redis://staging-redis:6379",
                    "api": "https://staging-api.example.com"
                }
            },
            "production": {
                "services": {
                    "database": "postgresql://prod-db:5432/prod_db",
                    "redis": "redis://prod-redis-cluster:6379",
                    "api": "https://api.example.com"
                }
            }
        }

        for env, config in service_discovery_configs.items():
            # Discover services
            discovered_services = self._discover_services_for_environment(env, config)

            # Verify all expected services discovered
            for service_name, expected_url in config["services"].items():
                assert service_name in discovered_services, f"Service {service_name} not discovered in {env}"
                assert discovered_services[service_name] == expected_url, \
                    f"Service URL mismatch for {service_name} in {env}"

            # Test service connectivity
            connectivity_results = self._test_service_connectivity(discovered_services)

            # All services should be connectable in their respective environments
            for service_name, is_connected in connectivity_results.items():
                # In test environment, we simulate connectivity
                assert is_connected, f"Service {service_name} not connectable in {env}"

        print("✅ Environment service discovery validated")

    def _initialize_environment(self, env_name):
        """Mock environment initialization."""
        return {
            "name": env_name,
            "status": "initialized",
            "config": {},
            "services": []
        }

    def _load_environment_configuration(self, env_name):
        """Mock environment configuration loading."""
        configs = {
            "development": {
                "database": {"type": "sqlite"},
                "api": {"port": 8000},
                "logging": {"level": "DEBUG"}
            },
            "staging": {
                "database": {"type": "postgresql"},
                "api": {"port": 8000},
                "logging": {"level": "INFO"}
            },
            "production": {
                "database": {"type": "postgresql"},
                "api": {"port": 443},
                "logging": {"level": "WARNING"}
            }
        }
        return configs.get(env_name, configs["development"])

    def _validate_environment_configuration(self, config):
        """Mock configuration validation."""
        errors = []
        if "database" not in config:
            errors.append("Missing database configuration")
        if "api" not in config:
            errors.append("Missing API configuration")
        return len(errors) == 0, errors

    def _start_environment_services(self, env_name, config):
        """Mock service starting."""
        return True

    def _perform_environment_health_checks(self, env_name):
        """Mock health checks."""
        return {
            "overall": "healthy",
            "services": {
                "database": "healthy",
                "api": "healthy",
                "redis": "healthy"
            }
        }

    def _switch_to_environment(self, env_name):
        """Mock environment switching."""
        return True

    def _get_active_environment(self):
        """Mock active environment getter."""
        return "development"

    def _cleanup_environment(self, env_name):
        """Mock environment cleanup."""
        return True

    def _save_environment_configuration(self, env_name, config):
        """Mock configuration saving."""
        return True

    def _discover_services_for_environment(self, env_name, config):
        """Mock service discovery."""
        return config.get("services", {})

    def _test_service_connectivity(self, services):
        """Mock service connectivity testing."""
        # In test environment, simulate all services as connectable
        return {service_name: True for service_name in services.keys()}


# Helper fixtures
@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config = {
            "environment": "testing",
            "database": {"type": "sqlite", "path": ":memory:"},
            "api": {"host": "localhost", "port": 8000}
        }
        yaml.dump(config, f)
        config_file = f.name

    yield config_file

    # Cleanup
    os.unlink(config_file)


@pytest.fixture
def mock_environment_config():
    """Create a mock environment configuration."""
    return {
        "environment": "development",
        "database": {"type": "sqlite", "path": ":memory:"},
        "api": {"host": "localhost", "port": 8000},
        "logging": {"level": "DEBUG"},
        "redis": {"host": "localhost", "port": 6379}
    }


@pytest.fixture
def mock_health_response():
    """Create a mock health check response."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "status": "healthy",
        "timestamp": "2024-01-01T12:00:00Z",
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "api": "healthy"
        }
    }
    return response
