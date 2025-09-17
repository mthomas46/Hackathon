"""Prompt Manager for configurable LLM prompts.

Provides centralized management of prompts used across all LLM-powered services.
Supports templating, versioning, and easy customization.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from string import Template


@dataclass
class PromptTemplate:
    """Represents a configurable prompt template."""
    name: str
    category: str
    content: str
    variables: List[str]
    version: str = "1.0.0"
    description: str = ""


class PromptManager:
    """Centralized prompt management system."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize prompt manager.

        Args:
            config_path: Path to prompts configuration file
        """
        if config_path is None:
            # Default path relative to this file
            current_dir = Path(__file__).parent
            config_path = current_dir / "prompts.yaml"

        self.config_path = Path(config_path)
        self._prompts: Dict[str, PromptTemplate] = {}
        self._load_prompts()

    def _load_prompts(self):
        """Load prompts from configuration file."""
        if not self.config_path.exists():
            print(f"Warning: Prompts config not found at {self.config_path}")
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            for category, prompts in config.items():
                if not isinstance(prompts, dict):
                    continue

                for prompt_name, prompt_data in prompts.items():
                    if isinstance(prompt_data, str):
                        # Simple prompt without metadata
                        template = PromptTemplate(
                            name=prompt_name,
                            category=category,
                            content=prompt_data,
                            variables=self._extract_variables(prompt_data)
                        )
                    elif isinstance(prompt_data, dict):
                        # Prompt with metadata
                        template = PromptTemplate(
                            name=prompt_name,
                            category=category,
                            content=prompt_data.get('content', ''),
                            variables=self._extract_variables(prompt_data.get('content', '')),
                            version=prompt_data.get('version', '1.0.0'),
                            description=prompt_data.get('description', '')
                        )

                    self._prompts[f"{category}.{prompt_name}"] = template

        except Exception as e:
            print(f"Error loading prompts: {e}")

    def _extract_variables(self, content: str) -> List[str]:
        """Extract template variables from prompt content."""
        from .utilities import extract_variables
        return extract_variables(content)

    def get_prompt(self, key: str, **variables) -> str:
        """Get a prompt by key and fill in variables.

        Args:
            key: Prompt key in format "category.name"
            **variables: Variables to substitute in the prompt

        Returns:
            Filled prompt string

        Raises:
            KeyError: If prompt key not found
            ValueError: If required variables are missing
        """
        if key not in self._prompts:
            raise KeyError(f"Prompt '{key}' not found. Available prompts: {list(self._prompts.keys())}")

        template = self._prompts[key]

        # Check if all required variables are provided
        missing_vars = set(template.variables) - set(variables.keys())
        if missing_vars:
            raise ValueError(f"Missing required variables for prompt '{key}': {missing_vars}")

        # Fill in the template
        try:
            filled_prompt = template.content.format(**variables)
            return filled_prompt
        except KeyError as e:
            raise ValueError(f"Missing variable in prompt '{key}': {e}")

    def get_prompt_template(self, key: str) -> PromptTemplate:
        """Get the prompt template object."""
        if key not in self._prompts:
            raise KeyError(f"Prompt '{key}' not found")
        return self._prompts[key]

    def list_prompts(self, category: Optional[str] = None) -> Dict[str, PromptTemplate]:
        """List available prompts, optionally filtered by category."""
        if category:
            return {k: v for k, v in self._prompts.items() if v.category == category}
        return self._prompts.copy()

    def reload_prompts(self):
        """Reload prompts from configuration file."""
        self._prompts.clear()
        self._load_prompts()

    def validate_prompts(self) -> List[str]:
        """Validate all prompts for syntax and completeness."""
        errors = []

        for key, template in self._prompts.items():
            # Check for unmatched braces
            if '{' in template.content and '}' not in template.content:
                errors.append(f"Prompt '{key}': Unmatched opening brace")
            if '}' in template.content and '{' not in template.content:
                errors.append(f"Prompt '{key}': Unmatched closing brace")

            # Check for unused variables in content
            import re
            content_vars = set(re.findall(r'\{([^}]+)\}', template.content))
            declared_vars = set(template.variables)

            unused_vars = declared_vars - content_vars
            if unused_vars:
                errors.append(f"Prompt '{key}': Unused variables: {unused_vars}")

        return errors


# Global prompt manager instance
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager


def get_prompt(key: str, **variables) -> str:
    """Convenience function to get a prompt."""
    return get_prompt_manager().get_prompt(key, **variables)


# Example usage:
if __name__ == "__main__":
    # Initialize prompt manager
    pm = PromptManager()

    # List available prompts
    print("Available prompts:")
    for key, template in pm.list_prompts().items():
        print(f"  {key}: {template.description or 'No description'}")

    # Get a specific prompt
    try:
        prompt = pm.get_prompt("summarization.default", content="Some content to summarize")
        print(f"\nGenerated prompt:\n{prompt}")
    except Exception as e:
        print(f"Error: {e}")
