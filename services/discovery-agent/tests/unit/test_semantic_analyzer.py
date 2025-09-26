"""Comprehensive unit tests for SemanticToolAnalyzer.

Tests all methods including the newly refactored semantic analysis logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add project root to path for imports
current_dir = Path(__file__).parent  # tests/unit
tests_dir = current_dir.parent       # tests
service_dir = tests_dir.parent       # discovery-agent
services_dir = service_dir.parent    # services
project_root = services_dir.parent   # project root

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(services_dir))

from domain.services.semantic_analyzer import SemanticToolAnalyzer


class TestSemanticToolAnalyzer:
    """Test suite for SemanticToolAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create a SemanticToolAnalyzer instance."""
        return SemanticToolAnalyzer()

    def test_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.interpreter_url == "http://localhost:5120"
        assert analyzer.service_client is not None
        assert len(analyzer.semantic_categories) > 0
        assert "content_generation" in analyzer.semantic_categories
        assert "content_analysis" in analyzer.semantic_categories

    def test_semantic_categories_structure(self, analyzer):
        """Test that semantic categories have proper structure."""
        for category_name, category_data in analyzer.semantic_categories.items():
            assert "keywords" in category_data
            assert "capabilities" in category_data
            assert "use_cases" in category_data
            assert isinstance(category_data["keywords"], list)
            assert isinstance(category_data["capabilities"], list)
            assert isinstance(category_data["use_cases"], list)

    @pytest.mark.asyncio
    async def test_analyze_tool_semantics_llm_success(self, analyzer):
        """Test semantic analysis with successful LLM response."""
        tool = {
            "name": "test_tool",
            "description": "A test tool",
            "method": "GET",
            "path": "/api/test"
        }

        mock_llm_response = {
            "success": True,
            "analysis": '{"semantic_categories": ["analysis"], "primary_category": "analysis", "capabilities": ["data_analysis"], "use_cases": ["validation"], "description": "Tool for analysis"}'
        }

        with patch.object(analyzer, '_perform_llm_semantic_analysis', return_value=mock_llm_response):
            with patch.object(analyzer, '_parse_llm_semantic_response') as mock_parse:
                mock_parse.return_value = {
                    "semantic_categories": ["analysis"],
                    "primary_category": "analysis",
                    "capabilities_identified": ["data_analysis"],
                    "use_cases_identified": ["validation"],
                    "semantic_description": "Tool for analysis"
                }

                result = await analyzer.analyze_tool_semantics(tool)

                assert result["tool_name"] == "test_tool"
                assert result["primary_category"] == "analysis"
                assert "data_analysis" in result["capabilities_identified"]
                assert result["llm_analysis"] is not None

    @pytest.mark.asyncio
    async def test_analyze_tool_semantics_llm_failure_fallback(self, analyzer):
        """Test semantic analysis with LLM failure, falling back to rule-based."""
        tool = {
            "name": "test_tool",
            "description": "A test tool",
            "method": "GET",
            "path": "/api/test"
        }

        mock_llm_response = {"success": False}

        with patch.object(analyzer, '_perform_llm_semantic_analysis', return_value=mock_llm_response):
            with patch.object(analyzer, '_rule_based_semantic_analysis') as mock_rule_based:
                mock_rule_based.return_value = {
                    "semantic_categories": ["utility"],
                    "primary_category": "utility",
                    "capabilities_identified": ["basic"],
                    "use_cases_identified": ["general"],
                    "semantic_description": "Basic tool"
                }

                result = await analyzer.analyze_tool_semantics(tool)

                assert result["tool_name"] == "test_tool"
                assert result["llm_analysis"] == mock_llm_response["analysis"]
                mock_rule_based.assert_called_once_with(tool)

    def test_rule_based_semantic_analysis(self, analyzer):
        """Test rule-based semantic analysis."""
        tool = {
            "name": "analyze_data_tool",
            "description": "Tool for analyzing data",
            "path": "/api/analyze",
            "category": "analysis"
        }

        with patch.object(analyzer, '_prepare_tool_text_for_analysis', return_value="analyze data tool analyze"):
            with patch.object(analyzer, '_score_semantic_categories') as mock_score:
                mock_score.return_value = [
                    {"category": "content_analysis", "score": 8, "capabilities": ["analysis"], "use_cases": ["validation"]}
                ]
                with patch.object(analyzer, '_determine_primary_category', return_value="content_analysis"):
                    with patch.object(analyzer, '_collect_capabilities_and_use_cases', return_value=(["analysis"], ["validation"])):
                        with patch.object(analyzer, '_build_semantic_analysis_result') as mock_build:
                            mock_build.return_value = {"test": "result"}

                            result = analyzer._rule_based_semantic_analysis(tool)

                            assert result == {"test": "result"}
                            mock_build.assert_called_once()

    def test_process_semantic_matches(self, analyzer):
        """Test semantic match processing."""
        semantic_matches = [
            {"category": "analysis", "score": 8, "capabilities": ["data_analysis"], "use_cases": ["validation"]}
        ]

        with patch.object(analyzer, '_determine_primary_category', return_value="analysis"):
            with patch.object(analyzer, '_collect_capabilities_and_use_cases', return_value=(["data_analysis"], ["validation"])):

                result = analyzer._process_semantic_matches(semantic_matches)

                assert result["primary_category"] == "analysis"
                assert result["capabilities"] == ["data_analysis"]
                assert result["use_cases"] == ["validation"]

    def test_prepare_tool_text_for_analysis(self, analyzer):
        """Test tool text preparation for analysis."""
        tool = {
            "name": "TestTool",
            "description": "A TEST tool",
            "path": "/api/TEST",
            "category": "TEST"
        }

        result = analyzer._prepare_tool_text_for_analysis(tool)
        assert result == "testtool a test tool /api/test test"

    def test_score_semantic_categories(self, analyzer):
        """Test semantic category scoring."""
        combined_text = "analyze data tool for processing"

        with patch.object(analyzer, '_calculate_category_score') as mock_calc:
            mock_calc.side_effect = [5, 0, 8]  # content_analysis gets highest score
            with patch.object(analyzer, '_is_category_relevant', side_effect=[True, False, True]):
                with patch.object(analyzer, '_create_semantic_match') as mock_create:
                    mock_create.side_effect = [
                        {"category": "content_analysis", "score": 5, "capabilities": [], "use_cases": []},
                        {"category": "content_generation", "score": 8, "capabilities": [], "use_cases": []}
                    ]

                    result = analyzer._score_semantic_categories(combined_text)

                    assert len(result) == 2
                    mock_calc.assert_called()

    def test_is_category_relevant(self, analyzer):
        """Test category relevance determination."""
        assert analyzer._is_category_relevant(3) == True
        assert analyzer._is_category_relevant(1) == False
        assert analyzer._is_category_relevant(2) == True

    def test_create_semantic_match(self, analyzer):
        """Test semantic match creation."""
        category_data = {
            "capabilities": ["analysis", "processing"],
            "use_cases": ["validation", "reporting"]
        }

        result = analyzer._create_semantic_match("content_analysis", 8, category_data)

        assert result["category"] == "content_analysis"
        assert result["score"] == 8
        assert result["capabilities"] == ["analysis", "processing"]
        assert result["use_cases"] == ["validation", "reporting"]

    def test_calculate_category_score(self, analyzer):
        """Test category score calculation."""
        category_data = {"keywords": ["analyze", "process"]}
        combined_text = "analyze this data for processing"

        with patch.object(analyzer, '_calculate_keyword_score', return_value=4):
            with patch.object(analyzer, '_calculate_category_name_score', return_value=3):

                score = analyzer._calculate_category_score("content_analysis", category_data, combined_text)

                assert score == 7

    def test_calculate_keyword_score(self, analyzer):
        """Test keyword score calculation."""
        keywords = ["analyze", "process", "data"]
        combined_text = "analyze this data for processing"

        score = analyzer._calculate_keyword_score(keywords, combined_text)
        assert score == 6  # 2 points per keyword match

    def test_calculate_category_name_score(self, analyzer):
        """Test category name score calculation."""
        # Test positive match
        score = analyzer._calculate_category_name_score("content_analysis", "content analysis tool")
        assert score == 3

        # Test no match
        score = analyzer._calculate_category_name_score("content_analysis", "storage tool")
        assert score == 0

    def test_determine_primary_category(self, analyzer):
        """Test primary category determination."""
        semantic_matches = [
            {"category": "analysis", "score": 5},
            {"category": "storage", "score": 8},
            {"category": "processing", "score": 3}
        ]

        # Should return highest scoring category
        primary = analyzer._determine_primary_category(semantic_matches)
        assert primary == "storage"

    def test_determine_primary_category_empty(self, analyzer):
        """Test primary category determination with empty matches."""
        primary = analyzer._determine_primary_category([])
        assert primary == "utility"

    def test_collect_capabilities_and_use_cases(self, analyzer):
        """Test capability and use case collection."""
        semantic_matches = [
            {"capabilities": ["analysis", "processing"], "use_cases": ["validation", "reporting"]},
            {"capabilities": ["storage"], "use_cases": ["archival"]}
        ]

        with patch.object(analyzer, '_get_top_semantic_matches', return_value=semantic_matches):
            with patch.object(analyzer, '_deduplicate_list') as mock_dedup:
                mock_dedup.side_effect = [
                    ["analysis", "processing", "storage"],
                    ["validation", "reporting", "archival"]
                ]

                capabilities, use_cases = analyzer._collect_capabilities_and_use_cases(semantic_matches)

                assert capabilities == ["analysis", "processing", "storage"]
                assert use_cases == ["validation", "reporting", "archival"]

    def test_get_top_semantic_matches(self, analyzer):
        """Test getting top semantic matches."""
        semantic_matches = [
            {"score": 5},
            {"score": 8},
            {"score": 3},
            {"score": 9}
        ]

        result = analyzer._get_top_semantic_matches(semantic_matches, limit=2)
        assert len(result) == 2
        assert result[0]["score"] == 5  # Original order preserved
        assert result[1]["score"] == 8

    def test_deduplicate_list(self, analyzer):
        """Test list deduplication."""
        items = ["analysis", "processing", "analysis", "storage", "processing"]
        result = analyzer._deduplicate_list(items)
        assert result == ["analysis", "processing", "storage"]

    def test_build_semantic_analysis_result(self, analyzer):
        """Test semantic analysis result building."""
        tool = {"name": "test_tool"}
        semantic_matches = [
            {"category": "analysis"},
            {"category": "processing"}
        ]
        primary_category = "analysis"
        capabilities = ["data_analysis"]
        use_cases = ["validation"]

        result = analyzer._build_semantic_analysis_result(
            tool, semantic_matches, primary_category, capabilities, use_cases
        )

        assert result["tool_name"] == "test_tool"
        assert result["semantic_categories"] == ["analysis", "processing"]
        assert result["primary_category"] == "analysis"
        assert result["capabilities_identified"] == ["data_analysis"]
        assert result["use_cases_identified"] == ["validation"]

    def test_calculate_semantic_confidence(self, analyzer):
        """Test semantic confidence calculation."""
        analysis_result = {
            "llm_analysis": "comprehensive analysis",
            "semantic_categories": ["analysis", "processing"],
            "primary_category": "analysis"
        }

        confidence = analyzer._calculate_semantic_confidence(analysis_result)
        # Confidence calculation depends on LLM availability and category count
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_perform_llm_semantic_analysis_success(self, analyzer):
        """Test successful LLM semantic analysis."""
        tool = {"name": "test_tool", "description": "test", "method": "GET", "path": "/test"}

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "analysis successful"})

        with patch.object(analyzer.service_client, 'session') as mock_session:
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            result = await analyzer._perform_llm_semantic_analysis(tool)

            assert result["success"] == True
            assert "analysis successful" in result["analysis"]

    @pytest.mark.asyncio
    async def test_perform_llm_semantic_analysis_failure(self, analyzer):
        """Test failed LLM semantic analysis."""
        tool = {"name": "test_tool"}

        with patch.object(analyzer.service_client, 'session') as mock_session:
            mock_session.return_value.__aenter__.return_value.post.side_effect = Exception("LLM error")

            result = await analyzer._perform_llm_semantic_analysis(tool)

            assert result["success"] == False
            assert "LLM error" in result["analysis"]

    def test_parse_llm_semantic_response_valid_json(self, analyzer):
        """Test parsing valid LLM response."""
        llm_response = '{"semantic_categories": ["analysis"], "primary_category": "analysis", "capabilities": ["data_analysis"], "use_cases": ["validation"], "description": "Analysis tool"}'

        result = analyzer._parse_llm_semantic_response(llm_response)

        assert result["semantic_categories"] == ["analysis"]
        assert result["primary_category"] == "analysis"
        assert result["capabilities_identified"] == ["data_analysis"]
        assert result["use_cases_identified"] == ["validation"]
        assert result["semantic_description"] == "Analysis tool"

    def test_parse_llm_semantic_response_invalid_json(self, analyzer):
        """Test parsing invalid LLM response."""
        llm_response = "invalid json"

        result = analyzer._parse_llm_semantic_response(llm_response)

        # Should return default values
        assert result["semantic_categories"] == []
        assert result["primary_category"] == ""
        assert result["capabilities_identified"] == []
        assert result["use_cases_identified"] == []
        assert "could not be parsed" in result["semantic_description"]

    @pytest.mark.asyncio
    async def test_analyze_tool_relationships(self, analyzer):
        """Test tool relationship analysis."""
        tools = [
            {"name": "analyze_tool", "categories": ["analysis"]},
            {"name": "store_tool", "categories": ["storage"]},
            {"name": "process_tool", "categories": ["processing", "analysis"]}
        ]

        result = await analyzer.analyze_tool_relationships(tools)

        assert "analyze_tool" in result
        assert "relationships" in result["analyze_tool"]
        assert isinstance(result["analyze_tool"]["relationships"], dict)
