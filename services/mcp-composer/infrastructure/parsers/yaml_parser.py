"""YAML parser for mcp-compose.yaml files."""

import yaml
from typing import Dict, Any, List
from pathlib import Path
import logging

from services.mcp_composer.domain.entities import (
    Composition,
    MCPReference,
    CompositionStrategy,
    ConflictResolution
)


logger = logging.getLogger(__name__)


class MCPComposeYAMLParser:
    """
    Parser for mcp-compose.yaml files.
    
    Supports composition specifications similar to docker-compose.yaml
    but for MCP orchestration.
    """
    
    SUPPORTED_VERSIONS = ["1.0", "1"]
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def parse_file(self, file_path: str) -> Composition:
        """
        Parse an mcp-compose.yaml file.
        
        Args:
            file_path: Path to the YAML file
        
        Returns:
            Composition object
        
        Raises:
            ValueError: If file is invalid
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        return self.parse_dict(data)
    
    def parse_dict(self, data: Dict[str, Any]) -> Composition:
        """
        Parse a dictionary representation of mcp-compose spec.
        
        Args:
            data: Dictionary containing composition spec
        
        Returns:
            Composition object
        """
        self._validate_spec(data)
        
        # Extract basic info
        composition_id = data.get("id", data["name"].lower().replace(" ", "-"))
        name = data["name"]
        description = data.get("description", "")
        version = data.get("version", "1.0.0")
        
        # Parse strategy
        strategy_str = data.get("strategy", "sequential")
        strategy = CompositionStrategy(strategy_str)
        
        # Parse conflict resolution
        conflict_str = data.get("conflict_resolution", "priority")
        conflict_resolution = ConflictResolution(conflict_str)
        
        # Parse MCPs
        mcps = self._parse_mcps(data["mcps"])
        
        # Create composition
        composition = Composition(
            composition_id=composition_id,
            name=name,
            description=description,
            mcps=mcps,
            strategy=strategy,
            conflict_resolution=conflict_resolution,
            version=version,
            merge_responses=data.get("merge_responses", True),
            deduplicate=data.get("deduplicate", True),
            max_response_length=data.get("max_response_length", 10000),
            min_confidence=data.get("min_confidence", 0.5),
            require_sources=data.get("require_sources", True),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )
        
        self.logger.info(f"Parsed composition: {name} with {len(mcps)} MCPs")
        
        return composition
    
    def _validate_spec(self, data: Dict[str, Any]) -> None:
        """Validate the composition spec."""
        # Check version
        spec_version = data.get("spec_version", "1.0")
        if spec_version not in self.SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported spec version: {spec_version}")
        
        # Check required fields
        if "name" not in data:
            raise ValueError("Missing required field: name")
        
        if "mcps" not in data or not data["mcps"]:
            raise ValueError("Must specify at least one MCP")
        
        # Validate strategy
        if "strategy" in data:
            try:
                CompositionStrategy(data["strategy"])
            except ValueError:
                valid_strategies = [s.value for s in CompositionStrategy]
                raise ValueError(f"Invalid strategy. Must be one of: {valid_strategies}")
        
        # Validate conflict resolution
        if "conflict_resolution" in data:
            try:
                ConflictResolution(data["conflict_resolution"])
            except ValueError:
                valid_resolutions = [r.value for r in ConflictResolution]
                raise ValueError(f"Invalid conflict resolution. Must be one of: {valid_resolutions}")
    
    def _parse_mcps(self, mcps_data: List[Dict[str, Any]]) -> List[MCPReference]:
        """Parse MCP references from the spec."""
        mcps = []
        
        for idx, mcp_data in enumerate(mcps_data):
            if "mcp_id" not in mcp_data:
                raise ValueError(f"MCP at index {idx} missing required field: mcp_id")
            
            if "tier" not in mcp_data:
                raise ValueError(f"MCP at index {idx} missing required field: tier")
            
            mcp = MCPReference(
                mcp_id=mcp_data["mcp_id"],
                tier=mcp_data["tier"],
                priority=mcp_data.get("priority", idx + 1),
                weight=mcp_data.get("weight", 1.0),
                fallback=mcp_data.get("fallback", False),
                required=mcp_data.get("required", True),
                timeout_ms=mcp_data.get("timeout_ms", 30000),
                retry_count=mcp_data.get("retry_count", 3),
                metadata=mcp_data.get("metadata", {})
            )
            
            mcps.append(mcp)
        
        return mcps
    
    def generate_yaml(self, composition: Composition) -> str:
        """
        Generate YAML string from a Composition object.
        
        Args:
            composition: Composition to serialize
        
        Returns:
            YAML string
        """
        data = {
            "spec_version": "1.0",
            "name": composition.name,
            "description": composition.description,
            "version": composition.version,
            "strategy": composition.strategy.value,
            "conflict_resolution": composition.conflict_resolution.value,
            "merge_responses": composition.merge_responses,
            "deduplicate": composition.deduplicate,
            "max_response_length": composition.max_response_length,
            "min_confidence": composition.min_confidence,
            "require_sources": composition.require_sources,
            "tags": composition.tags,
            "metadata": composition.metadata,
            "mcps": [
                {
                    "mcp_id": m.mcp_id,
                    "tier": m.tier,
                    "priority": m.priority,
                    "weight": m.weight,
                    "fallback": m.fallback,
                    "required": m.required,
                    "timeout_ms": m.timeout_ms,
                    "retry_count": m.retry_count,
                    "metadata": m.metadata
                }
                for m in composition.mcps
            ]
        }
        
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    
    def save_to_file(self, composition: Composition, file_path: str) -> None:
        """
        Save a Composition to a YAML file.
        
        Args:
            composition: Composition to save
            file_path: Path to save to
        """
        yaml_content = self.generate_yaml(composition)
        
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            f.write(yaml_content)
        
        self.logger.info(f"Saved composition to: {file_path}")


def create_example_composition() -> str:
    """Create an example mcp-compose.yaml file."""
    return """# MCP Composition Example
spec_version: "1.0"

name: "Multi-Tier Knowledge Composition"
description: "Combines ecosystem, team, and project MCPs for comprehensive answers"
version: "1.0.0"

# Composition strategy
strategy: "hierarchical"  # sequential, parallel, hierarchical, weighted, fallback

# Conflict resolution
conflict_resolution: "priority"  # priority, merge, vote, expert, latest, consensus

# Response merging
merge_responses: true
deduplicate: true
max_response_length: 10000
min_confidence: 0.5
require_sources: true

# Tags for categorization
tags:
  - "production"
  - "multi-tier"

# MCPs to compose
mcps:
  - mcp_id: "ecosystem-core"
    tier: "ecosystem"
    priority: 1
    weight: 0.3
    required: true
    timeout_ms: 30000
    retry_count: 3
    metadata:
      description: "Core ecosystem knowledge"
  
  - mcp_id: "team-backend"
    tier: "team"
    priority: 2
    weight: 0.3
    required: false
    timeout_ms: 20000
    retry_count: 2
    metadata:
      description: "Backend team specific knowledge"
  
  - mcp_id: "project-api-gateway"
    tier: "project"
    priority: 3
    weight: 0.4
    required: false
    fallback: false
    timeout_ms: 15000
    metadata:
      description: "API Gateway project knowledge"
  
  - mcp_id: "fallback-general"
    tier: "ecosystem"
    priority: 10
    weight: 0.1
    required: false
    fallback: true
    timeout_ms: 10000
    metadata:
      description: "Fallback general knowledge"

# Additional metadata
metadata:
  author: "MCP System"
  created: "2025-10-06"
  environment: "production"
"""
