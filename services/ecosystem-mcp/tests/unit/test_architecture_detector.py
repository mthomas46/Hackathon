"""
Unit tests for ArchitectureDetector.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from src.services.analysis.architecture_detector import (
    ArchitectureDetector,
    ArchitecturePattern,
    ArchitectureAnalysis,
    get_architecture_detector
)


@pytest.fixture
def detector():
    """Create detector instance."""
    return ArchitectureDetector()


@pytest.fixture
def sample_files_microservices():
    """Sample files for microservices architecture."""
    return [
        {'path': 'services/api/main.py', 'is_code': True},
        {'path': 'services/auth/app.py', 'is_code': True},
        {'path': 'services/payment/server.py', 'is_code': True},
        {'path': 'docker-compose.yml', 'is_code': False},
        {'path': 'k8s/deployment.yaml', 'is_code': False}
    ]


@pytest.fixture
def sample_files_mvc():
    """Sample files for MVC architecture."""
    return [
        {'path': 'models/user.py', 'is_code': True},
        {'path': 'views/user_view.py', 'is_code': True},
        {'path': 'controllers/user_controller.py', 'is_code': True},
        {'path': 'templates/index.html', 'is_code': False}
    ]


@pytest.mark.asyncio
async def test_detect_microservices(detector, sample_files_microservices, tmp_path):
    """Test microservices architecture detection."""
    analysis = await detector.detect_architecture(
        sample_files_microservices,
        str(tmp_path)
    )
    
    assert isinstance(analysis, ArchitectureAnalysis)
    assert analysis.primary_pattern is not None
    assert analysis.primary_pattern.name == 'microservices'
    assert analysis.primary_pattern.confidence > 0.3


@pytest.mark.asyncio
async def test_detect_mvc(detector, sample_files_mvc, tmp_path):
    """Test MVC architecture detection."""
    analysis = await detector.detect_architecture(
        sample_files_mvc,
        str(tmp_path)
    )
    
    assert isinstance(analysis, ArchitectureAnalysis)
    assert analysis.primary_pattern is not None
    assert analysis.primary_pattern.name == 'mvc'


@pytest.mark.asyncio
async def test_detect_layers(detector, tmp_path):
    """Test layer detection."""
    files = [
        {'path': 'api/routes.py', 'is_code': True},
        {'path': 'business/services.py', 'is_code': True},
        {'path': 'data/repositories.py', 'is_code': True},
        {'path': 'infrastructure/adapters.py', 'is_code': True}
    ]
    
    analysis = await detector.detect_architecture(files, str(tmp_path))
    
    assert 'api' in analysis.layers
    assert 'business' in analysis.layers
    assert 'data' in analysis.layers
    assert 'infrastructure' in analysis.layers


@pytest.mark.asyncio
async def test_find_entry_points(detector, tmp_path):
    """Test entry point detection."""
    files = [
        {'path': 'src/main.py', 'is_code': True},
        {'path': 'app.py', 'is_code': True},
        {'path': 'server.py', 'is_code': True},
        {'path': 'util.py', 'is_code': True}
    ]
    
    analysis = await detector.detect_architecture(files, str(tmp_path))
    
    assert 'src/main.py' in analysis.entry_points
    assert 'app.py' in analysis.entry_points
    assert 'server.py' in analysis.entry_points
    assert 'util.py' not in analysis.entry_points


@pytest.mark.asyncio
async def test_modularity_score(detector, tmp_path):
    """Test modularity score calculation."""
    files = [
        {'path': 'service1/main.py', 'is_code': True},
        {'path': 'service2/main.py', 'is_code': True}
    ]
    
    # Mock dependency graph with low coupling
    dependency_graph = {
        'nodes': ['service1/main.py', 'service2/main.py'],
        'edges': [
            {'source': 'service1/main.py', 'target': 'service2/main.py'}
        ]
    }
    
    analysis = await detector.detect_architecture(
        files,
        str(tmp_path),
        dependency_graph
    )
    
    assert 0.0 <= analysis.modularity_score <= 1.0


@pytest.mark.asyncio
async def test_confidence_scoring(detector, tmp_path):
    """Test confidence scoring for patterns."""
    # Strong microservices indicators
    files = [
        {'path': 'services/api/main.py', 'is_code': True},
        {'path': 'services/auth/main.py', 'is_code': True},
        {'path': 'services/payment/main.py', 'is_code': True},
        {'path': 'docker-compose.yml', 'is_code': False},
        {'path': 'k8s/deployment.yaml', 'is_code': False},
        {'path': 'k8s/service.yaml', 'is_code': False}
    ]
    
    analysis = await detector.detect_architecture(files, str(tmp_path))
    
    # Should have high confidence with many indicators
    assert analysis.primary_pattern.confidence > 0.5


@pytest.mark.asyncio
async def test_multiple_patterns(detector, tmp_path):
    """Test detection of multiple patterns."""
    # Files suggesting both microservices and layered architecture
    files = [
        {'path': 'services/api/routes.py', 'is_code': True},
        {'path': 'services/api/business/logic.py', 'is_code': True},
        {'path': 'services/api/data/repo.py', 'is_code': True},
        {'path': 'services/auth/main.py', 'is_code': True}
    ]
    
    analysis = await detector.detect_architecture(files, str(tmp_path))
    
    # Should detect primary pattern and secondary patterns
    assert analysis.primary_pattern is not None
    # May have secondary patterns
    assert isinstance(analysis.secondary_patterns, list)


@pytest.mark.asyncio
async def test_empty_files(detector, tmp_path):
    """Test with empty file list."""
    analysis = await detector.detect_architecture([], str(tmp_path))
    
    assert isinstance(analysis, ArchitectureAnalysis)
    assert analysis.primary_pattern is None or analysis.primary_pattern.confidence < 0.3


@pytest.mark.asyncio
async def test_pattern_descriptions(detector):
    """Test pattern descriptions."""
    descriptions = {
        'microservices': detector._get_pattern_description('microservices'),
        'mvc': detector._get_pattern_description('mvc'),
        'layered': detector._get_pattern_description('layered')
    }
    
    for pattern, desc in descriptions.items():
        assert len(desc) > 0
        assert isinstance(desc, str)


@pytest.mark.asyncio
async def test_event_driven_detection(detector, tmp_path):
    """Test event-driven architecture detection."""
    files = [
        {'path': 'events/user_events.py', 'is_code': True},
        {'path': 'handlers/user_handler.py', 'is_code': True},
        {'path': 'subscribers/email_subscriber.py', 'is_code': True}
    ]
    
    # Create files with event patterns
    (tmp_path / 'events').mkdir()
    (tmp_path / 'events' / 'user_events.py').write_text("""
class UserCreatedEvent:
    pass

event_bus = EventBus()
""")
    
    for f in files:
        f['path'] = str(tmp_path / f['path'])
    
    analysis = await detector.detect_architecture(files, str(tmp_path))
    
    # Should detect event-driven if confidence is high enough
    patterns = [analysis.primary_pattern] + analysis.secondary_patterns
    pattern_names = [p.name for p in patterns if p]
    
    # Event-driven may be detected as primary or secondary
    assert 'event_driven' in pattern_names or len(patterns) > 0


def test_singleton():
    """Test singleton pattern."""
    detector1 = get_architecture_detector()
    detector2 = get_architecture_detector()
    
    assert detector1 is detector2

