"""Unit tests for architecture digitizer data models."""

import pytest
from modules.models import (
    ArchitectureComponent,
    ArchitectureConnection,
    NormalizedArchitectureData,
    NormalizeRequest,
    FileNormalizeRequest,
    NormalizeResponse,
    SupportedSystemInfo,
    FileNormalizeResponse,
    SupportedFileFormatsResponse,
    SupportedSystemsResponse,
)


class TestArchitectureComponent:
    """Test suite for ArchitectureComponent model."""

    def test_valid_component_creation(self):
        """Test creating a valid architecture component."""
        component = ArchitectureComponent(
            id="comp1",
            type="service",
            name="User Service",
            description="Handles user operations"
        )

        assert component.id == "comp1"
        assert component.type == "service"
        assert component.name == "User Service"
        assert component.description == "Handles user operations"

    def test_component_without_description(self):
        """Test component creation without description."""
        component = ArchitectureComponent(
            id="comp2",
            type="database",
            name="User DB"
        )

        assert component.id == "comp2"
        assert component.type == "database"
        assert component.name == "User DB"
        assert component.description is None

    def test_valid_component_types(self):
        """Test all valid component types."""
        valid_types = [
            "service", "database", "queue", "ui", "gateway",
            "function", "storage", "other"
        ]

        for comp_type in valid_types:
            component = ArchitectureComponent(
                id=f"test_{comp_type}",
                type=comp_type,
                name=f"Test {comp_type}"
            )
            assert component.type == comp_type

    def test_invalid_component_type(self):
        """Test rejection of invalid component types."""
        with pytest.raises(ValueError, match="Component type must be one of"):
            ArchitectureComponent(
                id="invalid",
                type="invalid_type",
                name="Invalid Component"
            )

    def test_component_type_case_insensitive_validation(self):
        """Test that validation rejects uppercase types."""
        # Component types are validated as lowercase only
        with pytest.raises(ValueError, match="Component type must be one of"):
            ArchitectureComponent(
                id="test",
                type="SERVICE",  # Uppercase should fail
                name="Test Component"
            )


class TestArchitectureConnection:
    """Test suite for ArchitectureConnection model."""

    def test_valid_connection_creation(self):
        """Test creating a valid architecture connection."""
        connection = ArchitectureConnection(
            from_id="comp1",
            to_id="comp2",
            label="REST API"
        )

        assert connection.from_id == "comp1"
        assert connection.to_id == "comp2"
        assert connection.label == "REST API"

    def test_connection_without_label(self):
        """Test connection creation without label."""
        connection = ArchitectureConnection(
            from_id="service1",
            to_id="database1"
        )

        assert connection.from_id == "service1"
        assert connection.to_id == "database1"
        assert connection.label is None


class TestNormalizedArchitectureData:
    """Test suite for NormalizedArchitectureData model."""

    def test_valid_normalized_data_creation(self):
        """Test creating valid normalized architecture data."""
        components = [
            ArchitectureComponent(id="comp1", type="service", name="API Service"),
            ArchitectureComponent(id="comp2", type="database", name="User DB")
        ]

        connections = [
            ArchitectureConnection(from_id="comp1", to_id="comp2", label="connects to")
        ]

        metadata = {"version": "1.0", "source": "miro"}

        data = NormalizedArchitectureData(
            components=components,
            connections=connections,
            metadata=metadata
        )

        assert len(data.components) == 2
        assert len(data.connections) == 1
        assert data.metadata == metadata

    def test_normalized_data_without_metadata(self):
        """Test normalized data creation without metadata."""
        components = [
            ArchitectureComponent(id="comp1", type="service", name="Test Service")
        ]

        data = NormalizedArchitectureData(
            components=components,
            connections=[]
        )

        assert len(data.components) == 1
        assert data.connections == []
        assert data.metadata is None

    def test_empty_components_and_connections(self):
        """Test normalized data with empty component/connection lists."""
        data = NormalizedArchitectureData(
            components=[],
            connections=[]
        )

        assert data.components == []
        assert data.connections == []
        assert data.metadata is None


class TestNormalizeRequest:
    """Test suite for NormalizeRequest model."""

    def test_valid_request_creation(self):
        """Test creating a valid normalize request."""
        request = NormalizeRequest(
            system="miro",
            board_id="board123",
            token="token456"
        )

        assert request.system == "miro"
        assert request.board_id == "board123"
        assert request.token == "token456"

    def test_valid_systems(self):
        """Test all valid systems."""
        valid_systems = ["miro", "figjam", "lucid", "confluence"]

        for system in valid_systems:
            request = NormalizeRequest(
                system=system,
                board_id="board123",
                token="token456"
            )
            assert request.system == system

    def test_invalid_system(self):
        """Test rejection of invalid systems."""
        with pytest.raises(ValueError, match="System must be one of"):
            NormalizeRequest(
                system="invalid_system",
                board_id="board123",
                token="token456"
            )


class TestFileNormalizeRequest:
    """Test suite for FileNormalizeRequest model."""

    def test_valid_file_request_creation(self):
        """Test creating a valid file normalize request."""
        request = FileNormalizeRequest(
            system="miro",
            file_format="json"
        )

        assert request.system == "miro"
        assert request.file_format == "json"

    def test_valid_file_formats(self):
        """Test all valid file formats."""
        valid_formats = ["json", "pdf", "png", "jpg", "jpeg", "svg", "xml", "html"]

        for fmt in valid_formats:
            request = FileNormalizeRequest(
                system="miro",
                file_format=fmt
            )
            assert request.file_format == fmt.lower()

    def test_file_format_case_normalization(self):
        """Test that file format is normalized to lowercase."""
        request = FileNormalizeRequest(
            system="miro",
            file_format="PDF"  # Uppercase
        )
        assert request.file_format == "pdf"

    def test_invalid_file_format(self):
        """Test rejection of invalid file formats."""
        with pytest.raises(ValueError, match="File format must be one of"):
            FileNormalizeRequest(
                system="miro",
                file_format="invalid_format"
            )


class TestResponseModels:
    """Test suite for response models."""

    def test_normalize_response_creation(self):
        """Test creating a normalize response."""
        components = [
            ArchitectureComponent(id="comp1", type="service", name="Test Service")
        ]
        data = NormalizedArchitectureData(components=components, connections=[])

        response = NormalizeResponse(
            success=True,
            system="miro",
            board_id="board123",
            data=data,
            message="Normalization successful"
        )

        assert response.success is True
        assert response.system == "miro"
        assert response.board_id == "board123"
        assert len(response.data.components) == 1
        assert response.message == "Normalization successful"

    def test_supported_system_info_creation(self):
        """Test creating supported system info."""
        info = SupportedSystemInfo(
            name="Miro",
            description="Miro whiteboard platform",
            auth_type="Bearer token",
            supported=True
        )

        assert info.name == "Miro"
        assert info.description == "Miro whiteboard platform"
        assert info.auth_type == "Bearer token"
        assert info.supported is True

    def test_supported_systems_response_creation(self):
        """Test creating supported systems response."""
        systems = [
            SupportedSystemInfo(
                name="Miro",
                description="Miro whiteboard platform",
                auth_type="Bearer token",
                supported=True
            )
        ]

        response = SupportedSystemsResponse(
            success=True,
            systems=systems,
            count=1,
            message="Systems retrieved successfully"
        )

        assert response.success is True
        assert len(response.systems) == 1
        assert response.count == 1
        assert response.message == "Systems retrieved successfully"

    def test_supported_file_formats_response_creation(self):
        """Test creating supported file formats response."""
        formats = [
            {"format": "json", "description": "JSON format"},
            {"format": "pdf", "description": "PDF format"}
        ]

        response = SupportedFileFormatsResponse(
            success=True,
            system="miro",
            supported_formats=formats,
            count=2,
            message="File formats retrieved successfully"
        )

        assert response.success is True
        assert response.system == "miro"
        assert len(response.supported_formats) == 2
        assert response.count == 2
        assert response.message == "File formats retrieved successfully"

    def test_file_normalize_response_creation(self):
        """Test creating file normalize response."""
        components = [
            ArchitectureComponent(id="comp1", type="service", name="Test Service")
        ]
        data = NormalizedArchitectureData(components=components, connections=[])

        response = FileNormalizeResponse(
            success=True,
            system="miro",
            file_format="json",
            filename="diagram.json",
            data=data,
            message="File normalization successful"
        )

        assert response.success is True
        assert response.system == "miro"
        assert response.file_format == "json"
        assert response.filename == "diagram.json"
        assert len(response.data.components) == 1
        assert response.message == "File normalization successful"


class TestModelValidationEdgeCases:
    """Test edge cases and validation boundaries."""

    def test_component_name_edge_cases(self):
        """Test component name edge cases."""
        # Very long name should be accepted (no length validation in model)
        long_name = "A" * 200
        component = ArchitectureComponent(
            id="test",
            type="service",
            name=long_name
        )
        assert component.name == long_name

    def test_empty_strings_in_models(self):
        """Test handling of empty strings where appropriate."""
        # Empty description should be allowed
        component = ArchitectureComponent(
            id="test",
            type="service",
            name="Test",
            description=""
        )
        assert component.description == ""

        # Empty label should be allowed
        connection = ArchitectureConnection(
            from_id="a",
            to_id="b",
            label=""
        )
        assert connection.label == ""

    def test_unicode_support(self):
        """Test unicode support in model fields."""
        component = ArchitectureComponent(
            id="test_üñíçødé",
            type="service",
            name="Tëst Sërvićé 🚀",
            description="Dëscrïptïön wïth ëmöjïs 🎯"
        )

        assert component.id == "test_üñíçødé"
        assert component.name == "Tëst Sërvićé 🚀"
        assert component.description == "Dëscrïptïön wïth ëmöjïs 🎯"

    def test_model_equality(self):
        """Test model equality comparison."""
        comp1 = ArchitectureComponent(
            id="test",
            type="service",
            name="Test Service"
        )

        comp2 = ArchitectureComponent(
            id="test",
            type="service",
            name="Test Service"
        )

        comp3 = ArchitectureComponent(
            id="different",
            type="service",
            name="Test Service"
        )

        assert comp1 == comp2
        assert comp1 != comp3

    def test_model_dict_conversion(self):
        """Test model to dict conversion."""
        component = ArchitectureComponent(
            id="test",
            type="service",
            name="Test Service",
            description="Test description"
        )

        data = component.model_dump()

        assert data["id"] == "test"
        assert data["type"] == "service"
        assert data["name"] == "Test Service"
        assert data["description"] == "Test description"
