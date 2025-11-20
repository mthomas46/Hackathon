"""
Unit tests for Template Manager

Tests all core functionality of the template management system including:
- Template creation, validation, loading
- Template rendering
- Template versioning
- Error handling
"""

import pytest
from datetime import datetime
from uuid import uuid4, UUID

from src.services.templates.template_manager import (
    TemplateManager,
    TemplateValidationError,
    get_template_manager
)


class TestTemplateManager:
    """Test suite for TemplateManager service."""
    
    @pytest.fixture
    async def template_manager(self):
        """Get template manager instance."""
        return get_template_manager()
    
    @pytest.fixture
    def valid_template_structure(self):
        """Valid template structure for testing."""
        return {
            "sections": [
                {
                    "name": "Overview",
                    "required": True,
                    "prompt_template": "What is {service_name}?",
                    "documents_needed": 10,
                    "subsections": []
                },
                {
                    "name": "API Endpoints",
                    "required": True,
                    "prompt_template": "List all API endpoints in {service_name}",
                    "documents_needed": 20,
                    "subsections": [
                        {
                            "name": "Authentication",
                            "required": True
                        }
                    ]
                }
            ],
            "metadata": {
                "version": "1.0",
                "author": "system"
            }
        }
    
    @pytest.fixture
    def invalid_template_structure(self):
        """Invalid template structure (missing required fields)."""
        return {
            "sections": [
                {
                    "name": "Overview",
                    # Missing 'required' field
                    "prompt_template": "What is this?"
                }
            ]
        }
    
    # ============================================================================
    # Template Creation Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_create_template_success(self, template_manager, valid_template_structure):
        """Test successful template creation."""
        template_id = await template_manager.create_template(
            name="test_api_template",
            category="api_reference",
            structure=valid_template_structure,
            description="Test API template",
            target_framework="scala_play",
            target_audience="developers",
            is_system_template=False,
            created_by="test_user"
        )
        
        assert template_id is not None
        assert isinstance(template_id, UUID)
    
    @pytest.mark.asyncio
    async def test_create_template_duplicate_name(self, template_manager, valid_template_structure):
        """Test creating template with duplicate name fails."""
        name = f"duplicate_test_{uuid4().hex[:8]}"
        
        # Create first template
        await template_manager.create_template(
            name=name,
            category="api_reference",
            structure=valid_template_structure
        )
        
        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            await template_manager.create_template(
                name=name,
                category="api_reference",
                structure=valid_template_structure
            )
    
    @pytest.mark.asyncio
    async def test_create_template_invalid_structure(self, template_manager, invalid_template_structure):
        """Test creating template with invalid structure fails."""
        with pytest.raises(TemplateValidationError):
            await template_manager.create_template(
                name="invalid_template",
                category="api_reference",
                structure=invalid_template_structure
            )
    
    @pytest.mark.asyncio
    async def test_create_template_invalid_category(self, template_manager, valid_template_structure):
        """Test creating template with invalid category fails."""
        with pytest.raises(ValueError, match="category"):
            await template_manager.create_template(
                name="test_template",
                category="invalid_category",
                structure=valid_template_structure
            )
    
    # ============================================================================
    # Template Validation Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_validate_structure_valid(self, template_manager, valid_template_structure):
        """Test validation passes for valid structure."""
        result = await template_manager.validate_template_structure(valid_template_structure)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_structure_missing_sections(self, template_manager):
        """Test validation fails when sections are missing."""
        structure = {"metadata": {"version": "1.0"}}
        result = await template_manager.validate_template_structure(structure)
        assert result["valid"] is False
        assert any("sections" in error for error in result["errors"])
    
    @pytest.mark.asyncio
    async def test_validate_structure_invalid_section(self, template_manager):
        """Test validation fails for invalid section."""
        structure = {
            "sections": [
                {
                    "name": "Test",
                    "required": "yes",  # Should be boolean
                    "prompt_template": "Test prompt"
                }
            ]
        }
        result = await template_manager.validate_template_structure(structure)
        assert result["valid"] is False
    
    @pytest.mark.asyncio
    async def test_validate_generated_content(self, template_manager, valid_template_structure):
        """Test content validation against template."""
        # Create template
        template_id = await template_manager.create_template(
            name=f"test_validation_{uuid4().hex[:8]}",
            category="api_reference",
            structure=valid_template_structure
        )
        
        template = await template_manager.get_template(template_id)
        
        # Valid content
        content = "# Overview\n\nThis is the overview section.\n\n# API Endpoints\n\nAPI details here."
        result = await template_manager.validate_generated_content(
            template=template,
            section_name="Overview",
            content=content
        )
        
        assert result["valid"] is True
        assert result["adherence_score"] > 0.5
    
    # ============================================================================
    # Template Loading Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_load_template_by_name(self, template_manager, valid_template_structure):
        """Test loading template by name."""
        name = f"load_test_{uuid4().hex[:8]}"
        category = "api_reference"
        
        # Create template
        await template_manager.create_template(
            name=name,
            category=category,
            structure=valid_template_structure
        )
        
        # Load it
        template = await template_manager.load_template(name, category)
        
        assert template is not None
        assert template["name"] == name
        assert template["category"] == category
        assert "structure" in template
    
    @pytest.mark.asyncio
    async def test_load_template_not_found(self, template_manager):
        """Test loading non-existent template raises error."""
        with pytest.raises(ValueError, match="not found"):
            await template_manager.load_template("nonexistent_template", "api_reference")
    
    @pytest.mark.asyncio
    async def test_get_template_by_id(self, template_manager, valid_template_structure):
        """Test getting template by ID."""
        template_id = await template_manager.create_template(
            name=f"get_test_{uuid4().hex[:8]}",
            category="api_reference",
            structure=valid_template_structure
        )
        
        template = await template_manager.get_template(template_id)
        
        assert template is not None
        assert template["id"] == str(template_id)
    
    # ============================================================================
    # Template Update Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_update_template(self, template_manager, valid_template_structure):
        """Test updating template."""
        # Create template
        template_id = await template_manager.create_template(
            name=f"update_test_{uuid4().hex[:8]}",
            category="api_reference",
            structure=valid_template_structure,
            description="Original description"
        )
        
        # Update it
        updated_id = await template_manager.update_template(
            template_id=template_id,
            description="Updated description",
            target_audience="operators"
        )
        
        assert updated_id == template_id
        
        # Verify updates
        template = await template_manager.get_template(template_id)
        assert template["description"] == "Updated description"
        assert template["target_audience"] == "operators"
        assert template["version"] == 2  # Version should increment
    
    # ============================================================================
    # Template Listing Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_list_templates(self, template_manager, valid_template_structure):
        """Test listing all templates."""
        # Create a few templates
        for i in range(3):
            await template_manager.create_template(
                name=f"list_test_{i}_{uuid4().hex[:8]}",
                category="api_reference",
                structure=valid_template_structure
            )
        
        templates = await template_manager.list_templates()
        
        assert len(templates) >= 3
        assert all("id" in t for t in templates)
        assert all("name" in t for t in templates)
    
    @pytest.mark.asyncio
    async def test_list_templates_by_category(self, template_manager, valid_template_structure):
        """Test listing templates filtered by category."""
        category = "runbook"
        
        # Create template in specific category
        await template_manager.create_template(
            name=f"category_test_{uuid4().hex[:8]}",
            category=category,
            structure=valid_template_structure
        )
        
        templates = await template_manager.list_templates(category=category)
        
        assert all(t["category"] == category for t in templates)
    
    # ============================================================================
    # Template Deletion Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_delete_template(self, template_manager, valid_template_structure):
        """Test deleting template."""
        # Create template
        template_id = await template_manager.create_template(
            name=f"delete_test_{uuid4().hex[:8]}",
            category="api_reference",
            structure=valid_template_structure
        )
        
        # Delete it
        result = await template_manager.delete_template(template_id)
        assert result is True
        
        # Verify it's gone
        with pytest.raises(ValueError, match="not found"):
            await template_manager.get_template(template_id)
    
    @pytest.mark.asyncio
    async def test_delete_system_template_fails(self, template_manager, valid_template_structure):
        """Test that system templates cannot be deleted."""
        # Create system template
        template_id = await template_manager.create_template(
            name=f"system_test_{uuid4().hex[:8]}",
            category="api_reference",
            structure=valid_template_structure,
            is_system_template=True
        )
        
        # Try to delete
        with pytest.raises(ValueError, match="system template"):
            await template_manager.delete_template(template_id)
    
    # ============================================================================
    # Template Rendering Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_render_section(self, template_manager, valid_template_structure):
        """Test rendering a section with template."""
        template_id = await template_manager.create_template(
            name=f"render_test_{uuid4().hex[:8]}",
            category="api_reference",
            structure=valid_template_structure
        )
        
        template = await template_manager.get_template(template_id)
        
        content = "This is the overview content."
        rendered = await template_manager.render_section(
            template=template,
            section_name="Overview",
            content=content,
            context={"service_name": "TestService"}
        )
        
        assert rendered is not None
        assert "Overview" in rendered
        assert content in rendered
    
    # ============================================================================
    # Usage Tracking Tests
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_track_template_usage(self, template_manager, valid_template_structure):
        """Test usage tracking increments counter."""
        template_id = await template_manager.create_template(
            name=f"usage_test_{uuid4().hex[:8]}",
            category="api_reference",
            structure=valid_template_structure
        )
        
        # Get initial usage
        template = await template_manager.get_template(template_id)
        initial_usage = template["usage_count"]
        
        # Track usage
        await template_manager.track_template_usage(template_id)
        
        # Verify increment
        template = await template_manager.get_template(template_id)
        assert template["usage_count"] == initial_usage + 1


class TestTemplateValidation:
    """Test suite for template structure validation logic."""
    
    @pytest.mark.asyncio
    async def test_validate_empty_structure(self):
        """Test validation fails for empty structure."""
        manager = get_template_manager()
        result = await manager.validate_template_structure({})
        assert result["valid"] is False
    
    @pytest.mark.asyncio
    async def test_validate_section_requires_name(self):
        """Test section validation requires name."""
        manager = get_template_manager()
        structure = {
            "sections": [
                {
                    "required": True,
                    "prompt_template": "Test"
                }
            ]
        }
        result = await manager.validate_template_structure(structure)
        assert result["valid"] is False
        assert any("name" in error.lower() for error in result["errors"])
    
    @pytest.mark.asyncio
    async def test_validate_subsections(self):
        """Test subsection validation."""
        manager = get_template_manager()
        structure = {
            "sections": [
                {
                    "name": "Parent",
                    "required": True,
                    "prompt_template": "Test",
                    "subsections": [
                        {
                            "name": "Child",
                            "required": False
                        }
                    ]
                }
            ]
        }
        result = await manager.validate_template_structure(structure)
        assert result["valid"] is True


# ============================================================================
# Integration Tests
# ============================================================================

class TestTemplateManagerIntegration:
    """Integration tests for Template Manager with database."""
    
    @pytest.mark.asyncio
    async def test_template_lifecycle(self, valid_template_structure):
        """Test complete template lifecycle: create -> update -> use -> delete."""
        manager = get_template_manager()
        name = f"lifecycle_test_{uuid4().hex[:8]}"
        
        # Create
        template_id = await manager.create_template(
            name=name,
            category="api_reference",
            structure=valid_template_structure,
            description="Lifecycle test"
        )
        assert template_id is not None
        
        # Update
        await manager.update_template(
            template_id=template_id,
            description="Updated description"
        )
        
        # Use (track usage)
        await manager.track_template_usage(template_id)
        
        # Load
        template = await manager.load_template(name, "api_reference")
        assert template["usage_count"] == 1
        
        # Delete
        result = await manager.delete_template(template_id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_concurrent_template_creation(self, valid_template_structure):
        """Test multiple templates can be created concurrently."""
        import asyncio
        
        manager = get_template_manager()
        
        async def create_template(index):
            return await manager.create_template(
                name=f"concurrent_test_{index}_{uuid4().hex[:8]}",
                category="api_reference",
                structure=valid_template_structure
            )
        
        # Create 5 templates concurrently
        results = await asyncio.gather(*[create_template(i) for i in range(5)])
        
        assert len(results) == 5
        assert all(isinstance(r, UUID) for r in results)
        assert len(set(results)) == 5  # All unique


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def valid_template_structure():
    """Shared valid template structure."""
    return {
        "sections": [
            {
                "name": "Overview",
                "required": True,
                "prompt_template": "What is {service_name}?",
                "documents_needed": 10,
                "subsections": []
            },
            {
                "name": "Details",
                "required": False,
                "prompt_template": "Provide details about {service_name}",
                "documents_needed": 15,
                "subsections": []
            }
        ],
        "metadata": {
            "version": "1.0",
            "author": "test"
        }
    }

