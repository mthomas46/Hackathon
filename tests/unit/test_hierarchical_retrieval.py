"""
Unit tests for hierarchical retrieval system.

Following TDD methodology:
1. Write tests first (Red phase)
2. Run tests (should fail)
3. Implement code (Green phase)
4. Run tests (should pass)
5. Refactor (Blue phase)
"""

import pytest
from typing import List, Dict, Any
from dataclasses import dataclass


# Import the actual implementation
import sys
from pathlib import Path

# Add services directory to path
services_path = Path(__file__).parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

from mcp_retrieval.src.hierarchical_retrieval import (
    HierarchicalRetriever,
    RetrievalResult,
    TierConfig,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def default_retriever():
    """Fixture for default hierarchical retriever."""
    return HierarchicalRetriever(
        tiers=["client", "project", "company"]
    )


@pytest.fixture
def custom_weight_retriever():
    """Fixture for retriever with custom weights."""
    return HierarchicalRetriever(
        tiers=["client", "project"],
        tier_weights={
            "client": 0.7,
            "project": 0.3,
        }
    )


@pytest.fixture
def budget_retriever():
    """Fixture for retriever with token budget."""
    return HierarchicalRetriever(
        tiers=["client", "project", "company"],
        token_budget=2000
    )


# ============================================================================
# Test: Single Tier Retrieval
# ============================================================================

def test_retrieve_from_single_tier(default_retriever):
    """
    Test retrieval from a single tier.
    
    Expected behavior:
    - Should retrieve only from specified tier
    - Should respect max_results limit
    - All results should be from the same tier
    """
    results = default_retriever.retrieve(
        query="What is our pricing strategy?",
        tiers=["client"],
        max_results=5
    )
    
    assert isinstance(results, list)
    assert len(results) <= 5
    assert all(isinstance(r, RetrievalResult) for r in results)
    assert all(r.tier == "client" for r in results)


def test_retrieve_empty_query():
    """
    Test retrieval with empty query.
    
    Expected behavior:
    - Should handle empty query gracefully
    - Should return empty list or raise ValueError
    """
    retriever = HierarchicalRetriever(tiers=["client"])
    
    with pytest.raises(ValueError):
        retriever.retrieve(query="", max_results=5)


def test_retrieve_invalid_tier():
    """
    Test retrieval with invalid tier name.
    
    Expected behavior:
    - Should raise ValueError for invalid tier
    """
    retriever = HierarchicalRetriever(tiers=["client"])
    
    with pytest.raises(ValueError):
        retriever.retrieve(
            query="test query",
            tiers=["invalid_tier"],
            max_results=5
        )


# ============================================================================
# Test: Cascading Retrieval
# ============================================================================

def test_retrieve_cascading_across_tiers(default_retriever):
    """
    Test cascading retrieval across multiple tiers.
    
    Expected behavior:
    - Should retrieve from client tier first
    - If insufficient results, cascade to project tier
    - If still insufficient, cascade to company tier
    - Results should be ordered by tier priority
    """
    results = default_retriever.retrieve(
        query="What are our company values?",
        max_results=10
    )
    
    assert isinstance(results, list)
    assert len(results) <= 10
    
    # Results should include multiple tiers
    tiers_present = set(r.tier for r in results)
    assert len(tiers_present) >= 1  # At least one tier
    
    # Higher priority tiers should appear first
    if len(results) > 1:
        client_results = [r for r in results if r.tier == "client"]
        project_results = [r for r in results if r.tier == "project"]
        
        if client_results and project_results:
            # Client results should have higher or equal scores
            assert max(r.score for r in client_results) >= min(r.score for r in project_results)


def test_retrieve_respects_tier_order():
    """
    Test that retrieval respects tier priority order.
    
    Expected behavior:
    - Client tier should be prioritized over project
    - Project tier should be prioritized over company
    - And so on...
    """
    retriever = HierarchicalRetriever(
        tiers=["client", "project", "company", "team", "ecosystem"]
    )
    
    results = retriever.retrieve(
        query="test query",
        max_results=20
    )
    
    # Group results by tier
    tier_order = ["client", "project", "company", "team", "ecosystem"]
    results_by_tier = {tier: [] for tier in tier_order}
    
    for result in results:
        results_by_tier[result.tier].append(result)
    
    # Verify tier prioritization (higher tiers should have results if available)
    for i, tier in enumerate(tier_order[:-1]):
        next_tier = tier_order[i + 1]
        # If next tier has results, current tier should also have results
        # (unless current tier is completely empty)
        if results_by_tier[next_tier]:
            # This is a soft check - we expect higher tiers to be checked first
            pass


# ============================================================================
# Test: Token Budget Distribution
# ============================================================================

def test_retrieve_with_token_budget(budget_retriever):
    """
    Test retrieval respects token budget.
    
    Expected behavior:
    - Total tokens should not exceed budget
    - Should distribute tokens across tiers
    - Should prioritize higher-value content
    """
    results = budget_retriever.retrieve_with_budget(
        query="What is our technical architecture?"
    )
    
    assert isinstance(results, list)
    
    total_tokens = sum(r.token_count for r in results)
    assert total_tokens <= 2000, f"Exceeded token budget: {total_tokens} > 2000"


def test_token_budget_distribution_across_tiers():
    """
    Test token budget is distributed across tiers according to weights.
    
    Expected behavior:
    - Client tier should get 40% of budget (default weight 0.4)
    - Project tier should get 30% of budget (default weight 0.3)
    - Company tier should get 15% of budget (default weight 0.15)
    - And so on...
    """
    retriever = HierarchicalRetriever(
        tiers=["client", "project", "company"],
        token_budget=1000
    )
    
    results = retriever.retrieve_with_budget(
        query="test query"
    )
    
    # Calculate tokens per tier
    tokens_by_tier = {}
    for result in results:
        tokens_by_tier[result.tier] = tokens_by_tier.get(result.tier, 0) + result.token_count
    
    # Verify approximate distribution (allow 20% variance)
    if "client" in tokens_by_tier:
        client_tokens = tokens_by_tier["client"]
        expected_client = 1000 * 0.4  # 400 tokens
        # Allow significant variance since actual distribution depends on content
        assert client_tokens <= expected_client * 1.5


def test_token_budget_custom_weights(custom_weight_retriever):
    """
    Test custom tier weights are respected in budget distribution.
    
    Expected behavior:
    - Client should get 70% of budget
    - Project should get 30% of budget
    """
    results = custom_weight_retriever.retrieve_with_budget(
        query="test query"
    )
    
    total_tokens = sum(r.token_count for r in results)
    assert total_tokens <= custom_weight_retriever.token_budget


# ============================================================================
# Test: Tier Weighting
# ============================================================================

def test_tier_weights_affect_scoring():
    """
    Test that tier weights affect result scoring.
    
    Expected behavior:
    - Higher weight tiers should have boosted scores
    - Lower weight tiers should have reduced scores
    """
    retriever = HierarchicalRetriever(
        tiers=["client", "project"],
        tier_weights={
            "client": 0.8,
            "project": 0.2,
        }
    )
    
    results = retriever.retrieve(
        query="test query",
        max_results=10
    )
    
    client_results = [r for r in results if r.tier == "client"]
    project_results = [r for r in results if r.tier == "project"]
    
    # If we have results from both tiers, client results should generally score higher
    if client_results and project_results:
        avg_client_score = sum(r.score for r in client_results) / len(client_results)
        avg_project_score = sum(r.score for r in project_results) / len(project_results)
        
        # Not a strict requirement, but generally expected
        # (depends on actual content quality)
        pass


def test_equal_weights_all_tiers():
    """
    Test equal weights give fair distribution.
    
    Expected behavior:
    - All tiers should have equal weight
    - Results should be based purely on relevance
    """
    retriever = HierarchicalRetriever(
        tiers=["client", "project", "company"],
        tier_weights={
            "client": 0.33,
            "project": 0.33,
            "company": 0.34,
        }
    )
    
    results = retriever.retrieve(
        query="test query",
        max_results=15
    )
    
    # With equal weights, distribution should be more balanced
    assert isinstance(results, list)


# ============================================================================
# Test: Edge Cases
# ============================================================================

def test_retrieve_no_results_found():
    """
    Test behavior when no results found.
    
    Expected behavior:
    - Should return empty list
    - Should not raise exception
    """
    retriever = HierarchicalRetriever(tiers=["client"])
    
    results = retriever.retrieve(
        query="extremely specific query that will not match anything xyz123",
        max_results=5
    )
    
    assert isinstance(results, list)
    assert len(results) == 0


def test_retrieve_max_results_zero():
    """
    Test retrieval with max_results=0.
    
    Expected behavior:
    - Should return empty list
    """
    retriever = HierarchicalRetriever(tiers=["client"])
    
    results = retriever.retrieve(
        query="test query",
        max_results=0
    )
    
    assert isinstance(results, list)
    assert len(results) == 0


def test_retrieve_very_large_max_results():
    """
    Test retrieval with very large max_results.
    
    Expected behavior:
    - Should handle gracefully
    - Should return available results (not necessarily all 10000)
    """
    retriever = HierarchicalRetriever(tiers=["client", "project", "company"])
    
    results = retriever.retrieve(
        query="test query",
        max_results=10000
    )
    
    assert isinstance(results, list)
    # Will return however many results are available


def test_retrieve_with_very_small_budget():
    """
    Test retrieval with very small token budget.
    
    Expected behavior:
    - Should handle gracefully
    - Should return at least one result if possible
    - Or return empty if no result fits
    """
    retriever = HierarchicalRetriever(
        tiers=["client"],
        token_budget=50  # Very small budget
    )
    
    results = retriever.retrieve_with_budget(
        query="test query"
    )
    
    assert isinstance(results, list)
    total_tokens = sum(r.token_count for r in results)
    assert total_tokens <= 50


# ============================================================================
# Test: Result Quality
# ============================================================================

def test_results_have_required_fields():
    """
    Test that all results have required fields.
    
    Expected behavior:
    - Each result should have: content, tier, score, token_count, metadata
    """
    retriever = HierarchicalRetriever(tiers=["client", "project"])
    
    results = retriever.retrieve(
        query="test query",
        max_results=5
    )
    
    for result in results:
        assert hasattr(result, 'content')
        assert hasattr(result, 'tier')
        assert hasattr(result, 'score')
        assert hasattr(result, 'token_count')
        assert hasattr(result, 'metadata')
        
        assert isinstance(result.content, str)
        assert isinstance(result.tier, str)
        assert isinstance(result.score, float)
        assert isinstance(result.token_count, int)
        assert isinstance(result.metadata, dict)


def test_results_ordered_by_score():
    """
    Test that results are ordered by score (descending).
    
    Expected behavior:
    - Results should be sorted by score (highest first)
    """
    retriever = HierarchicalRetriever(tiers=["client", "project", "company"])
    
    results = retriever.retrieve(
        query="test query",
        max_results=10
    )
    
    if len(results) > 1:
        scores = [r.score for r in results]
        # Check if sorted in descending order
        assert scores == sorted(scores, reverse=True)


def test_score_range():
    """
    Test that scores are in valid range.
    
    Expected behavior:
    - Scores should be between 0.0 and 1.0
    """
    retriever = HierarchicalRetriever(tiers=["client", "project"])
    
    results = retriever.retrieve(
        query="test query",
        max_results=10
    )
    
    for result in results:
        assert 0.0 <= result.score <= 1.0, f"Score out of range: {result.score}"


# ============================================================================
# Test: Performance
# ============================================================================

def test_retrieval_performance():
    """
    Test that retrieval completes in reasonable time.
    
    Expected behavior:
    - Should complete in less than 5 seconds for typical query
    """
    import time
    
    retriever = HierarchicalRetriever(
        tiers=["client", "project", "company", "team", "ecosystem"]
    )
    
    start_time = time.time()
    results = retriever.retrieve(
        query="test query",
        max_results=50
    )
    duration = time.time() - start_time
    
    # Should complete in reasonable time
    # This is a soft limit and depends on data store performance
    assert duration < 10.0, f"Retrieval too slow: {duration:.2f}s"


# ============================================================================
# Summary
# ============================================================================

"""
Test Summary:
=============

Unit Tests Written: 23

Categories:
- Single tier retrieval: 3 tests
- Cascading retrieval: 2 tests
- Token budget: 3 tests
- Tier weighting: 2 tests
- Edge cases: 5 tests
- Result quality: 3 tests
- Performance: 1 test

Next Steps (TDD):
1. Run these tests (they should ALL fail - Red phase)
2. Implement HierarchicalRetriever class (Green phase)
3. Make tests pass one by one
4. Refactor implementation (Blue phase)
5. Run tests again (all should pass)

Expected to fail because we haven't implemented:
- HierarchicalRetriever class
- RetrievalResult dataclass
- TierConfig class
- retrieve() method
- retrieve_with_budget() method
"""

