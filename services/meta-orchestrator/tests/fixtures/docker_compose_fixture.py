"""Test fixtures for Docker Compose configurations"""

import pytest
from pathlib import Path


@pytest.fixture
def sample_compose_config():
    """Sample docker-compose configuration for testing"""
    return {
        'version': '3.8',
        'services': {
            'redis': {
                'image': 'redis:7-alpine',
                'ports': ['6379:6379'],
                'environment': ['REDIS_PASSWORD=test'],
                'healthcheck': {
                    'test': ['CMD', 'redis-cli', 'ping'],
                    'interval': '30s',
                    'timeout': '10s',
                    'retries': 3
                }
            },
            'user-store': {
                'build': {
                    'context': '.',
                    'dockerfile': 'services/user-store/Dockerfile'
                },
                'environment': [
                    'PYTHONPATH=/app',
                    'SERVICE_NAME=user-store',
                    'SERVICE_API_PORT=5150',
                    'REDIS_API_HOST=redis',
                    'ENVIRONMENT=development'
                ],
                'ports': ['8106:5150'],
                'depends_on': {
                    'redis': {'condition': 'service_healthy'}
                },
                'healthcheck': {
                    'test': ['CMD', 'curl', '-f', 'http://localhost:5150/health'],
                    'interval': '30s',
                    'timeout': '10s',
                    'retries': 3
                },
                'volumes': [
                    './services/user-store:/app/services/user-store:rw',
                    './services/shared:/app/services/shared:rw'
                ]
            }
        }
    }


@pytest.fixture
def mock_compose_file(tmp_path, sample_compose_config):
    """Create a temporary docker-compose file for testing"""
    import yaml

    compose_file = tmp_path / "docker-compose.test.yml"
    with open(compose_file, 'w') as f:
        yaml.dump(sample_compose_config, f)

    return compose_file
