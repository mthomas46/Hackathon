"""Mock utilities and frameworks for Project Simulation Service testing.

Provides comprehensive mocking capabilities that follow ecosystem patterns
for consistent and reliable test isolation.
"""

from .mock_services import *
from .mock_repositories import *
from .mock_clients import *
from .mock_data import *

__all__ = [
    # Mock services
    'MockSimulationApplicationService',
    'MockDomainService',
    'MockLogger',
    'MockMonitoring',

    # Mock repositories
    'MockProjectRepository',
    'MockSimulationRepository',
    'MockTimelineRepository',
    'MockTeamRepository',

    # Mock clients
    'MockEcosystemClient',
    'MockAnalysisServiceClient',
    'MockInterpreterClient',
    'MockDocStoreClient',
    'MockLLMGatewayClient',

    # Mock data generators
    'MockDataGenerator',
    'generate_mock_project',
    'generate_mock_team',
    'generate_mock_timeline',
    'generate_mock_simulation'
]
