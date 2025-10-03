"""
Tests for Sampling Engine
=========================

Unit tests for intelligent document sampling strategies.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
import sys
from pathlib import Path
from dataclasses import dataclass

# Add service root to path
service_root = str(Path(__file__).parent.parent)
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from domain.services.sampling_engine import (
    SamplingEngine,
    SamplingStrategy,
    SamplingConfig,
    SamplingResult
)


@dataclass
class MockDocument:
    """Mock document for testing."""
    id: str
    title: str
    content: str
    status: str
    labels: list
    updated: datetime
    importance: float = 0.5


@pytest.fixture
def mock_log_client():
    """Create mock log collector client."""
    client = Mock()
    client.log_business_event = AsyncMock()
    return client


@pytest.fixture
def sampling_engine(mock_log_client):
    """Create sampling engine with mock log client."""
    return SamplingEngine(log_client=mock_log_client)


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    base_date = datetime.now() - timedelta(days=100)
    
    documents = []
    for i in range(100):
        doc = MockDocument(
            id=f"doc-{i}",
            title=f"Document {i}",
            content=f"Content for document {i}",
            status=["todo", "in_progress", "done"][i % 3],
            labels=[f"label-{i % 5}", "test"],
            updated=base_date + timedelta(days=i),
            importance=i / 100.0  # 0.0 to 0.99
        )
        documents.append(doc)
    
    return documents


class TestSamplingEngine:
    """Test suite for Sampling Engine."""
    
    @pytest.mark.asyncio
    async def test_random_sampling(self, sampling_engine, sample_documents):
        """Test random sampling strategy."""
        config = SamplingConfig(
            strategy=SamplingStrategy.RANDOM,
            target_count=30
        )
        
        result = await sampling_engine.sample(sample_documents, config)
        
        assert isinstance(result, SamplingResult)
        assert result.sampled_count == 30
        assert result.original_count == 100
        assert result.reduction_percentage == 70.0
        assert result.strategy_used == SamplingStrategy.RANDOM
    
    @pytest.mark.asyncio
    async def test_random_sampling_with_percentage(self, sampling_engine, sample_documents):
        """Test random sampling with percentage target."""
        config = SamplingConfig(
            strategy=SamplingStrategy.RANDOM,
            target_percentage=0.2
        )
        
        result = await sampling_engine.sample(sample_documents, config)
        
        assert result.sampled_count == 20
        assert result.reduction_percentage == 80.0
    
    @pytest.mark.asyncio
    async def test_stratified_sampling(self, sampling_engine, sample_documents):
        """Test stratified sampling maintains representation."""
        config = SamplingConfig(
            strategy=SamplingStrategy.STRATIFIED,
            target_count=30,
            min_samples_per_strata=2
        )
        
        def strata_extractor(doc):
            return doc.status
        
        result = await sampling_engine.sample(
            sample_documents,
            config,
            strata_extractor=strata_extractor
        )
        
        assert isinstance(result, SamplingResult)
        assert result.sampled_count <= 30
        assert result.strategy_used == SamplingStrategy.STRATIFIED
        
        # Check that all strata are represented
        sampled_strata = {doc.status for doc in result.sampled_items}
        assert len(sampled_strata) == 3  # todo, in_progress, done
        
        # Check metadata
        assert "strata_count" in result.metadata
        assert result.metadata["strata_count"] == 3
    
    @pytest.mark.asyncio
    async def test_importance_based_sampling(self, sampling_engine, sample_documents):
        """Test importance-based sampling selects high-value items."""
        config = SamplingConfig(
            strategy=SamplingStrategy.IMPORTANCE_BASED,
            target_count=20
        )
        
        def importance_scorer(doc):
            return doc.importance
        
        result = await sampling_engine.sample(
            sample_documents,
            config,
            importance_scorer=importance_scorer
        )
        
        assert result.sampled_count == 20
        assert result.strategy_used == SamplingStrategy.IMPORTANCE_BASED
        
        # Verify high importance items were selected
        avg_importance = sum(doc.importance for doc in result.sampled_items) / len(result.sampled_items)
        assert avg_importance > 0.75  # Should be in top 20%
        
        # Check metadata
        assert "avg_importance_score" in result.metadata
    
    @pytest.mark.asyncio
    async def test_temporal_sampling(self, sampling_engine, sample_documents):
        """Test temporal sampling favors recent items."""
        config = SamplingConfig(
            strategy=SamplingStrategy.TEMPORAL,
            target_count=20,
            recency_weight=0.8
        )
        
        result = await sampling_engine.sample(sample_documents, config)
        
        assert result.sampled_count == 20
        assert result.strategy_used == SamplingStrategy.TEMPORAL
        
        # Verify recent items are prioritized
        avg_age = sum(
            (datetime.now() - doc.updated).days
            for doc in result.sampled_items
        ) / len(result.sampled_items)
        
        # Average age should be less than overall average (50 days)
        assert avg_age < 40
    
    @pytest.mark.asyncio
    async def test_diversity_based_sampling(self, sampling_engine, sample_documents):
        """Test diversity-based sampling maximizes variety."""
        config = SamplingConfig(
            strategy=SamplingStrategy.DIVERSITY_BASED,
            target_count=20
        )
        
        result = await sampling_engine.sample(sample_documents, config)
        
        assert result.sampled_count == 20
        assert result.strategy_used == SamplingStrategy.DIVERSITY_BASED
        
        # Check for label diversity
        all_labels = set()
        for doc in result.sampled_items:
            all_labels.update(doc.labels)
        
        # Should have good label coverage (at least 4 out of 5 label types)
        assert len(all_labels) >= 4
        
        # Check metadata
        assert "unique_features" in result.metadata
    
    @pytest.mark.asyncio
    async def test_deduplication(self, sampling_engine):
        """Test that duplicates are removed."""
        # Create documents with duplicates
        documents = [
            MockDocument(f"doc-{i}", f"Title {i % 5}", "content", "todo", [], datetime.now(), 0.5)
            for i in range(20)
        ]
        
        config = SamplingConfig(
            strategy=SamplingStrategy.RANDOM,
            target_count=10
        )
        
        def key_extractor(doc):
            return doc.title
        
        result = await sampling_engine.sample(
            documents,
            config,
            key_extractor=key_extractor
        )
        
        # Should have only 5 unique titles
        unique_titles = {doc.title for doc in result.sampled_items}
        assert len(unique_titles) <= 5
    
    @pytest.mark.asyncio
    async def test_empty_items(self, sampling_engine):
        """Test sampling with empty item list."""
        config = SamplingConfig(strategy=SamplingStrategy.RANDOM, target_count=10)
        
        result = await sampling_engine.sample([], config)
        
        assert result.original_count == 0
        assert result.sampled_count == 0
        assert result.reduction_percentage == 0.0
    
    @pytest.mark.asyncio
    async def test_target_count_exceeds_items(self, sampling_engine, sample_documents):
        """Test when target count exceeds available items."""
        small_sample = sample_documents[:10]
        
        config = SamplingConfig(
            strategy=SamplingStrategy.RANDOM,
            target_count=20
        )
        
        result = await sampling_engine.sample(small_sample, config)
        
        # Should return all items
        assert result.sampled_count == 10
        assert result.reduction_percentage == 0.0
    
    @pytest.mark.asyncio
    async def test_stratified_sampling_min_samples(self, sampling_engine):
        """Test stratified sampling respects minimum samples per strata."""
        # Create documents with uneven distribution
        documents = [
            MockDocument(f"doc-{i}", f"Title {i}", "content", "common" if i < 90 else "rare", [], datetime.now(), 0.5)
            for i in range(100)
        ]
        
        config = SamplingConfig(
            strategy=SamplingStrategy.STRATIFIED,
            target_count=15,
            min_samples_per_strata=3
        )
        
        def strata_extractor(doc):
            return doc.status
        
        result = await sampling_engine.sample(
            documents,
            config,
            strata_extractor=strata_extractor
        )
        
        # Count samples from rare stratum
        rare_samples = sum(1 for doc in result.sampled_items if doc.status == "rare")
        
        # Should have at least min_samples_per_strata from rare stratum
        assert rare_samples >= config.min_samples_per_strata
    
    @pytest.mark.asyncio
    async def test_missing_required_extractor(self, sampling_engine, sample_documents):
        """Test that missing required extractor raises error."""
        config = SamplingConfig(
            strategy=SamplingStrategy.STRATIFIED,
            target_count=30
        )
        
        # Should raise ValueError for missing strata_extractor
        with pytest.raises(ValueError, match="strata_extractor required"):
            await sampling_engine.sample(sample_documents, config)
    
    @pytest.mark.asyncio
    async def test_missing_importance_scorer(self, sampling_engine, sample_documents):
        """Test that missing importance scorer raises error."""
        config = SamplingConfig(
            strategy=SamplingStrategy.IMPORTANCE_BASED,
            target_count=30
        )
        
        # Should raise ValueError for missing importance_scorer
        with pytest.raises(ValueError, match="importance_scorer required"):
            await sampling_engine.sample(sample_documents, config)
    
    @pytest.mark.asyncio
    async def test_recommend_strategy_small_dataset(self, sampling_engine):
        """Test strategy recommendation for small dataset."""
        small_docs = [
            MockDocument(f"doc-{i}", f"Title {i}", "content", "todo", [], datetime.now(), 0.5)
            for i in range(10)
        ]
        
        strategy = await sampling_engine.recommend_strategy(small_docs)
        
        assert strategy == SamplingStrategy.RANDOM
    
    @pytest.mark.asyncio
    async def test_recommend_strategy_with_strata(self, sampling_engine, sample_documents):
        """Test strategy recommendation with stratified data."""
        strategy = await sampling_engine.recommend_strategy(sample_documents)
        
        # Should recommend stratified since documents have status
        assert strategy == SamplingStrategy.STRATIFIED
    
    @pytest.mark.asyncio
    async def test_recommend_strategy_temporal(self, sampling_engine):
        """Test strategy recommendation for temporal data."""
        # Create simple objects without status attribute to avoid stratified recommendation
        @dataclass
        class TemporalDoc:
            id: str
            title: str
            updated: datetime
        
        docs = [
            TemporalDoc(f"doc-{i}", f"Title {i}", datetime.now() - timedelta(days=i))
            for i in range(50)
        ]
        
        strategy = await sampling_engine.recommend_strategy(docs, target_reduction=0.5)
        
        # Should recommend temporal since documents have timestamps
        assert strategy == SamplingStrategy.TEMPORAL
    
    @pytest.mark.asyncio
    async def test_recommend_strategy_diversity(self, sampling_engine):
        """Test strategy recommendation for diverse data."""
        # Create simple objects without status or timestamp to test diversity
        @dataclass
        class DiverseDoc:
            id: str
            title: str
            labels: list
        
        docs = [
            DiverseDoc(f"doc-{i}", f"Document {i}", [f"label-{i % 10}"])
            for i in range(50)
        ]
        
        strategy = await sampling_engine.recommend_strategy(docs)
        
        # Should recommend diversity since documents have rich labels
        assert strategy == SamplingStrategy.DIVERSITY_BASED
    
    @pytest.mark.asyncio
    async def test_logging_integration(self, sampling_engine, sample_documents, mock_log_client):
        """Test that sampling operations are logged."""
        config = SamplingConfig(
            strategy=SamplingStrategy.RANDOM,
            target_count=30
        )
        
        await sampling_engine.sample(sample_documents, config)
        
        # Should log business event
        mock_log_client.log_business_event.assert_called_once()
        call_args = mock_log_client.log_business_event.call_args[0]
        assert call_args[0] == "sampling_completed"
    
    def test_deduplicate_default_key(self, sampling_engine):
        """Test deduplication with default key extractor."""
        items = ["item1", "item2", "item1", "item3", "item2"]
        
        deduplicated = sampling_engine._deduplicate(items)
        
        assert len(deduplicated) == 3
        assert set(deduplicated) == {"item1", "item2", "item3"}
    
    def test_deduplicate_custom_key(self, sampling_engine):
        """Test deduplication with custom key extractor."""
        items = [
            MockDocument("1", "Title A", "content", "todo", [], datetime.now(), 0.5),
            MockDocument("2", "Title B", "content", "todo", [], datetime.now(), 0.5),
            MockDocument("3", "Title A", "content", "todo", [], datetime.now(), 0.5),
        ]
        
        deduplicated = sampling_engine._deduplicate(items, key_extractor=lambda x: x.title)
        
        assert len(deduplicated) == 2
    
    def test_calculate_target_count_from_count(self, sampling_engine):
        """Test target count calculation from explicit count."""
        config = SamplingConfig(strategy=SamplingStrategy.RANDOM, target_count=25)
        
        target = sampling_engine._calculate_target_count(100, config)
        
        assert target == 25
    
    def test_calculate_target_count_from_percentage(self, sampling_engine):
        """Test target count calculation from percentage."""
        config = SamplingConfig(strategy=SamplingStrategy.RANDOM, target_percentage=0.3)
        
        target = sampling_engine._calculate_target_count(100, config)
        
        assert target == 30
    
    def test_calculate_target_count_default(self, sampling_engine):
        """Test target count calculation with default (30%)."""
        config = SamplingConfig(strategy=SamplingStrategy.RANDOM)
        
        target = sampling_engine._calculate_target_count(100, config)
        
        assert target == 30
    
    @pytest.mark.asyncio
    async def test_reduction_percentage_calculation(self, sampling_engine, sample_documents):
        """Test that reduction percentage is calculated correctly."""
        config = SamplingConfig(strategy=SamplingStrategy.RANDOM, target_count=25)
        
        result = await sampling_engine.sample(sample_documents, config)
        
        # 100 -> 25 = 75% reduction
        assert result.reduction_percentage == 75.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

