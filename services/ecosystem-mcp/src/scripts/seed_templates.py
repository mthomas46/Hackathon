"""
Seed System Templates

Loads built-in documentation templates from YAML files and seeds them into the database.
Run this script after migrations to populate system templates.

Usage:
    python -m src.scripts.seed_templates
"""

import asyncio
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any

from ..storage.database import get_database
from ..services.templates.template_manager import get_template_manager, TemplateValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


TEMPLATE_FILES = [
    ".rag-config/doc-templates/api-reference/openapi-style.yaml",
    ".rag-config/doc-templates/runbooks/sre-style.yaml",
    ".rag-config/doc-templates/architecture/c4-model.yaml",
]


async def load_template_from_yaml(file_path: str) -> Dict[str, Any]:
    """
    Load template from YAML file.
    
    Args:
        file_path: Path to YAML file
    
    Returns:
        Template dictionary
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Template file not found: {file_path}")
    
    with open(path, 'r') as f:
        template_data = yaml.safe_load(f)
    
    logger.info(f"✅ Loaded template from {file_path}")
    return template_data


async def seed_template(template_data: Dict[str, Any]) -> None:
    """
    Seed a single template into the database.
    
    Args:
        template_data: Template dictionary from YAML
    """
    template_manager = get_template_manager()
    
    try:
        # Check if template already exists
        existing = None
        try:
            existing = await template_manager.load_template(
                template_data["name"],
                template_data["category"]
            )
        except ValueError:
            pass  # Template doesn't exist, we'll create it
        
        if existing:
            logger.info(f"⏭️  Template '{template_data['name']}' already exists, skipping")
            return
        
        # Create template
        template_id = await template_manager.create_template(
            name=template_data["name"],
            category=template_data["category"],
            structure=template_data["structure"],
            description=template_data.get("description"),
            target_framework=template_data.get("target_framework"),
            target_audience=template_data.get("target_audience"),
            render_options=template_data.get("render_options"),
            is_system_template=True,
            is_public=True,
            created_by="system"
        )
        
        logger.info(
            f"✅ Seeded template '{template_data['name']}' "
            f"(category: {template_data['category']}, ID: {template_id})"
        )
        
    except TemplateValidationError as e:
        logger.error(f"❌ Validation error for template '{template_data['name']}': {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to seed template '{template_data['name']}': {e}")
        raise


async def seed_all_templates() -> None:
    """Seed all system templates into the database."""
    
    logger.info("🌱 Starting template seeding...")
    logger.info(f"   Found {len(TEMPLATE_FILES)} template files to process")
    
    success_count = 0
    error_count = 0
    skip_count = 0
    
    for template_file in TEMPLATE_FILES:
        try:
            # Load template from YAML
            template_data = await load_template_from_yaml(template_file)
            
            # Seed template
            await seed_template(template_data)
            success_count += 1
            
        except FileNotFoundError as e:
            logger.error(f"❌ {e}")
            error_count += 1
        except TemplateValidationError as e:
            logger.error(f"❌ Validation failed for {template_file}: {e}")
            error_count += 1
        except Exception as e:
            logger.error(f"❌ Unexpected error for {template_file}: {e}", exc_info=True)
            error_count += 1
    
    logger.info("\n" + "="*60)
    logger.info("🌱 Template seeding complete!")
    logger.info(f"   ✅ Successfully seeded: {success_count}")
    logger.info(f"   ⏭️  Skipped (already exist): {skip_count}")
    logger.info(f"   ❌ Errors: {error_count}")
    logger.info("="*60)
    
    if error_count > 0:
        raise Exception(f"Template seeding completed with {error_count} errors")


async def main():
    """Main entry point."""
    try:
        # Initialize database connection
        db = get_database()
        
        # Seed templates
        await seed_all_templates()
        
        logger.info("\n✅ All system templates are ready!")
        
    except Exception as e:
        logger.error(f"\n❌ Template seeding failed: {e}")
        raise
    finally:
        # Close database connections
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())

