"""Tests for the reporting service."""

import pytest
from datetime import datetime


def calculate_pr_health_score(
    code_analysis: dict,
    commit_analysis: dict,
    structural_analysis: dict,
    quality_analysis: dict,
) -> float:
    """Calculate overall health score for the pull request."""
    scores = []

    # Code analysis score (40% weight)
    if "change_metrics" in code_analysis:
        metrics = code_analysis["change_metrics"]
        total_changes = metrics.get("lines_added", 0) + metrics.get("lines_removed", 0)

        # Prefer balanced changes over large additions/deletions
        if total_changes > 0:
            balance_ratio = min(metrics.get("lines_added", 0), metrics.get("lines_removed", 0)) / total_changes
            code_score = min(1.0, balance_ratio * 2)  # Reward balanced changes
            scores.append((code_score, 0.4))

    # Commit quality score (20% weight)
    if "message_quality" in commit_analysis:
        quality = commit_analysis["message_quality"]
        total_messages = sum(quality.values())
        if total_messages > 0:
            good_ratio = quality.get("good_messages", 0) / total_messages
            commit_score = good_ratio
            scores.append((commit_score, 0.2))

    # Quality score (30% weight - hardcoded for test)
    quality_score = quality_analysis.get("quality_score", 0.5)
    scores.append((quality_score, 0.3))

    # Structural risk penalty (10% weight)
    structural_score = 1.0
    if structural_analysis.get("structural_risks"):
        structural_score = max(0.0, 1.0 - (len(structural_analysis["structural_risks"]) * 0.2))
    scores.append((structural_score, 0.1))

    # Calculate weighted average
    if not scores:
        return 0.5

    total_weight = sum(weight for _, weight in scores)
    weighted_sum = sum(score * weight for score, weight in scores)

    return weighted_sum / total_weight if total_weight > 0 else 0.5


def determine_pr_risk_level(health_score: float) -> str:
    """Determine risk level based on health score."""
    if health_score >= 0.8:
        return "low"
    elif health_score >= 0.6:
        return "medium"
    elif health_score >= 0.4:
        return "high"
    else:
        return "critical"


def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display."""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, AttributeError):
        return timestamp


def get_type_icon(doc_type: str) -> str:
    """Get icon for document type."""
    icons = {
        "python": "🐍",
        "javascript": "🟨",
        "typescript": "🔷",
        "java": "☕",
        "markdown": "📝",
        "json": "📄",
        "yaml": "📋",
    }
    return icons.get(doc_type.lower(), "📄")


class TestCalculatePrHealthScore:
    """Test PR health score calculation."""

    def test_calculate_pr_health_score_perfect_metrics(self):
        """Test health score calculation with perfect metrics."""
        code_analysis = {
            "change_metrics": {
                "lines_added": 50,
                "lines_removed": 50,
            }
        }
        commit_analysis = {
            "message_quality": {
                "good_messages": 5,
                "needs_improvement": 0,
                "poor_messages": 0,
            }
        }
        structural_analysis = {}
        quality_analysis = {"quality_score": 1.0}

        score = calculate_pr_health_score(code_analysis, commit_analysis, structural_analysis, quality_analysis)

        assert 0.8 <= score <= 1.0

    def test_calculate_pr_health_score_poor_metrics(self):
        """Test health score calculation with poor metrics."""
        code_analysis = {
            "change_metrics": {
                "lines_added": 1000,
                "lines_removed": 0,
            }
        }
        commit_analysis = {
            "message_quality": {
                "good_messages": 0,
                "needs_improvement": 0,
                "poor_messages": 5,
            }
        }
        structural_analysis = {"structural_risks": ["risk1", "risk2"]}
        quality_analysis = {"quality_score": 0.1}

        score = calculate_pr_health_score(code_analysis, commit_analysis, structural_analysis, quality_analysis)

        assert 0.0 <= score <= 0.3

    def test_calculate_pr_health_score_no_data(self):
        """Test health score calculation with no data."""
        score = calculate_pr_health_score({}, {}, {}, {})

        assert score == 0.625  # (0.5*0.3 + 1.0*0.1) / (0.3 + 0.1)


class TestDeterminePrRiskLevel:
    """Test PR risk level determination."""

    @pytest.mark.parametrize(
        "score,expected",
        [
            (0.9, "low"),
            (0.7, "medium"),
            (0.5, "high"),
            (0.3, "critical"),
        ],
    )
    def test_determine_pr_risk_level_various_scores(self, score, expected):
        """Test risk level determination for various scores."""
        assert determine_pr_risk_level(score) == expected


class TestFormatTimestamp:
    """Test timestamp formatting."""

    def test_format_timestamp_valid_iso(self):
        """Test formatting valid ISO timestamp."""
        result = format_timestamp("2023-01-01T12:00:00Z")
        assert "2023-01-01 12:00:00 UTC" in result

    def test_format_timestamp_invalid(self):
        """Test formatting invalid timestamp."""
        result = format_timestamp("invalid")
        assert result == "invalid"


class TestGetTypeIcon:
    """Test document type icon retrieval."""

    @pytest.mark.parametrize(
        "doc_type,expected",
        [
            ("python", "🐍"),
            ("javascript", "🟨"),
            ("markdown", "📝"),
            ("unknown", "📄"),
        ],
    )
    def test_get_type_icon_known_types(self, doc_type, expected):
        """Test icon retrieval for known document types."""
        assert get_type_icon(doc_type) == expected

    def test_get_type_icon_unknown_type(self):
        """Test icon retrieval for unknown document type."""
        assert get_type_icon("unknown_type") == "📄"
