"""Unit tests for architecture digitizer normalizers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from modules.normalizers import (
    BaseNormalizer,
    MiroNormalizer,
    FigJamNormalizer,
    LucidNormalizer,
    ConfluenceNormalizer,
)


class TestBaseNormalizer:
    """Test suite for BaseNormalizer abstract class."""

    def test_abstract_methods(self):
        """Test that BaseNormalizer defines abstract methods."""
        # BaseNormalizer should not be instantiable directly
        with pytest.raises(TypeError):
            BaseNormalizer()

    def test_get_description(self):
        """Test the default description method."""
        description = BaseNormalizer.get_description()
        assert isinstance(description, str)
        assert len(description) > 0

    def test_get_auth_type(self):
        """Test the default auth type method."""
        auth_type = BaseNormalizer.get_auth_type()
        assert isinstance(auth_type, str)
        assert len(auth_type) > 0


class TestMiroNormalizer:
    """Test suite for MiroNormalizer."""

    @pytest.fixture
    def normalizer(self):
        """Create a MiroNormalizer instance."""
        return MiroNormalizer()

    def test_get_description(self):
        """Test MiroNormalizer description."""
        description = MiroNormalizer.get_description()
        assert "miro" in description.lower()

    def test_get_auth_type(self):
        """Test MiroNormalizer auth type."""
        auth_type = MiroNormalizer.get_auth_type()
        assert "bearer" in auth_type.lower()

    @pytest.mark.asyncio
    async def test_successful_normalization(self, normalizer):
        """Test successful Miro board normalization."""
        # Mock Miro API response
        mock_response_data = {
            "data": [
                {
                    "id": "widget1",
                    "type": "sticky_note",
                    "data": {
                        "content": "User Service"
                    }
                },
                {
                    "id": "widget2",
                    "type": "shape",
                    "data": {
                        "content": "Database",
                        "shape": "rectangle"
                    }
                },
                {
                    "id": "widget3",
                    "type": "line",
                    "startWidget": {"id": "widget1"},
                    "endWidget": {"id": "widget2"}
                }
            ]
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None

            mock_context = MagicMock()
            mock_context.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_context

            result = await normalizer.normalize("board123", "token456")

            assert len(result.components) == 2
            assert len(result.connections) == 1
            assert result.components[0].name == "User Service"
            assert result.components[1].name == "Database"
            assert result.connections[0].from_id == "widget1"
            assert result.connections[0].to_id == "widget2"

    @pytest.mark.asyncio
    async def test_invalid_token_error(self, normalizer):
        """Test handling of invalid token error."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 401
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("401")

            # Create a mock that raises HTTPStatusError
            from httpx import HTTPStatusError
            error_response = MagicMock()
            error_response.status_code = 401
            http_error = HTTPStatusError("Unauthorized", request=MagicMock(), response=error_response)

            mock_client.return_value.__aenter__.return_value.get.side_effect = http_error

            with pytest.raises(ValueError, match="Invalid Miro API token"):
                await normalizer.normalize("board123", "invalid_token")

    @pytest.mark.asyncio
    async def test_board_not_found_error(self, normalizer):
        """Test handling of board not found error."""
        with patch('httpx.AsyncClient') as mock_client:
            from httpx import HTTPStatusError
            error_response = MagicMock()
            error_response.status_code = 404
            http_error = HTTPStatusError("Not Found", request=MagicMock(), response=error_response)

            mock_client.return_value.__aenter__.return_value.get.side_effect = http_error

            with pytest.raises(ValueError, match="Miro board board123 not found"):
                await normalizer.normalize("board123", "token456")

    @pytest.mark.asyncio
    async def test_generic_api_error(self, normalizer):
        """Test handling of generic API errors."""
        with patch('httpx.AsyncClient') as mock_client:
            from httpx import HTTPStatusError
            error_response = MagicMock()
            error_response.status_code = 500
            http_error = HTTPStatusError("Internal Server Error", request=MagicMock(), response=error_response)

            mock_client.return_value.__aenter__.return_value.get.side_effect = http_error

            with pytest.raises(ValueError, match="Miro API error: 500"):
                await normalizer.normalize("board123", "token456")

    def test_normalize_miro_data_empty(self, normalizer):
        """Test normalization of empty Miro data."""
        result = normalizer._normalize_miro_data({"data": []})

        assert len(result.components) == 0
        assert len(result.connections) == 0

    def test_normalize_miro_data_various_widgets(self, normalizer):
        """Test normalization of various Miro widget types."""
        data = {
            "data": [
                {
                    "id": "text1",
                    "type": "text",
                    "data": {"content": "Simple Text"}
                },
                {
                    "id": "sticky1",
                    "type": "sticky_note",
                    "data": {"content": "Important Note"}
                },
                {
                    "id": "shape1",
                    "type": "shape",
                    "data": {"content": "Rectangle Shape", "shape": "rectangle"}
                },
                {
                    "id": "shape2",
                    "type": "shape",
                    "data": {"content": "Circle Shape", "shape": "circle"}
                },
                {
                    "id": "unknown1",
                    "type": "unknown_widget",
                    "data": {"content": "Unknown"}
                }
            ]
        }

        result = normalizer._normalize_miro_data(data)

        assert len(result.components) == 4  # text, sticky_note, and 2 shapes
        assert len(result.connections) == 0

        # Check component types are mapped correctly
        component_names = [c.name for c in result.components]
        assert "Simple Text" in component_names
        assert "Important Note" in component_names
        assert "Rectangle Shape" in component_names
        assert "Circle Shape" in component_names

    def test_shape_type_mapping(self, normalizer):
        """Test mapping of Miro shapes to component types."""
        # Test various shape mappings
        test_cases = [
            ("rectangle", "service"),
            ("circle", "service"),
            ("database", "database"),
            ("cylinder", "database"),
            ("queue", "queue"),
            ("cloud", "storage"),
            ("unknown_shape", "service"),  # Default fallback
        ]

        for shape_name, expected_type in test_cases:
            shape_data = {"shape": shape_name, "content": "Test"}
            component_type = normalizer._map_shape_to_component_type(shape_data)
            assert component_type == expected_type


class TestFigJamNormalizer:
    """Test suite for FigJamNormalizer."""

    @pytest.fixture
    def normalizer(self):
        """Create a FigJamNormalizer instance."""
        return FigJamNormalizer()

    def test_get_description(self):
        """Test FigJamNormalizer description."""
        description = FigJamNormalizer.get_description()
        assert "figjam" in description.lower()

    def test_get_auth_type(self):
        """Test FigJamNormalizer auth type."""
        auth_type = FigJamNormalizer.get_auth_type()
        assert "figma" in auth_type.lower()

    @pytest.mark.asyncio
    async def test_figjam_normalization(self, normalizer):
        """Test FigJam board normalization."""
        # Mock FigJam API response (similar to Miro but different structure)
        mock_response_data = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "text",
                    "text": "API Gateway"
                },
                {
                    "id": "node2",
                    "type": "shape",
                    "shape": "rectangle",
                    "text": "User Service"
                }
            ],
            "connections": [
                {
                    "from": "node1",
                    "to": "node2",
                    "label": "connects"
                }
            ]
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await normalizer.normalize("board123", "token456")

            assert len(result.components) >= 1
            assert len(result.connections) >= 1


class TestLucidNormalizer:
    """Test suite for LucidNormalizer."""

    @pytest.fixture
    def normalizer(self):
        """Create a LucidNormalizer instance."""
        return LucidNormalizer()

    def test_get_description(self):
        """Test LucidNormalizer description."""
        description = LucidNormalizer.get_description()
        assert "lucid" in description.lower()

    def test_get_auth_type(self):
        """Test LucidNormalizer auth type."""
        auth_type = LucidNormalizer.get_auth_type()
        assert "bearer" in auth_type.lower()


class TestConfluenceNormalizer:
    """Test suite for ConfluenceNormalizer."""

    @pytest.fixture
    def normalizer(self):
        """Create a ConfluenceNormalizer instance."""
        return ConfluenceNormalizer()

    def test_get_description(self):
        """Test ConfluenceNormalizer description."""
        description = ConfluenceNormalizer.get_description()
        assert "confluence" in description.lower()

    def test_get_auth_type(self):
        """Test ConfluenceNormalizer auth type."""
        auth_type = ConfluenceNormalizer.get_auth_type()
        assert "bearer" in auth_type.lower()


class TestNormalizerErrorHandling:
    """Test error handling across normalizers."""

    @pytest.mark.asyncio
    async def test_network_timeout(self):
        """Test handling of network timeouts."""
        normalizer = MiroNormalizer()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Timeout")

            with pytest.raises(Exception):  # Should propagate network errors
                await normalizer.normalize("board123", "token456")

    @pytest.mark.asyncio
    async def test_malformed_json_response(self):
        """Test handling of malformed JSON responses."""
        normalizer = MiroNormalizer()

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            with pytest.raises(ValueError):  # Should handle JSON parsing errors
                await normalizer.normalize("board123", "token456")

    def test_empty_response_data(self):
        """Test handling of empty response data."""
        normalizer = MiroNormalizer()

        # Test with None data
        result = normalizer._normalize_miro_data(None)
        assert len(result.components) == 0
        assert len(result.connections) == 0

        # Test with missing data key
        result = normalizer._normalize_miro_data({})
        assert len(result.components) == 0
        assert len(result.connections) == 0

    def test_component_name_truncation(self):
        """Test that long component names are truncated."""
        normalizer = MiroNormalizer()

        long_name = "A" * 100
        data = {
            "data": [
                {
                    "id": "widget1",
                    "type": "sticky_note",
                    "data": {"content": long_name}
                }
            ]
        }

        result = normalizer._normalize_miro_data(data)
        assert len(result.components[0].name) <= 50  # Should be truncated


class TestNormalizerIntegration:
    """Integration tests for normalizer functionality."""

    def test_all_normalizers_have_required_methods(self):
        """Test that all normalizers implement required methods."""
        normalizers = [
            MiroNormalizer,
            FigJamNormalizer,
            LucidNormalizer,
            ConfluenceNormalizer
        ]

        for normalizer_class in normalizers:
            # Should be able to instantiate
            instance = normalizer_class()

            # Should have required methods
            assert hasattr(instance, 'normalize')
            assert hasattr(normalizer_class, 'get_description')
            assert hasattr(normalizer_class, 'get_auth_type')

            # Methods should return strings
            desc = normalizer_class.get_description()
            auth = normalizer_class.get_auth_type()
            assert isinstance(desc, str)
            assert isinstance(auth, str)
            assert len(desc) > 0
            assert len(auth) > 0

    def test_normalizer_inheritance(self):
        """Test that all normalizers inherit from BaseNormalizer."""
        normalizers = [
            MiroNormalizer(),
            FigJamNormalizer(),
            LucidNormalizer(),
            ConfluenceNormalizer()
        ]

        for normalizer in normalizers:
            assert isinstance(normalizer, BaseNormalizer)
