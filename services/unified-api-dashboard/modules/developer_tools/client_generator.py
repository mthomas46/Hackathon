"""
Client Code Generator

Generates client SDKs for API services in multiple programming languages
based on OpenAPI specifications and service metadata.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from ..discovery.client import DiscoveryClient
from ..api.catalog import APICatalogManager


class Language(Enum):
    """Supported programming languages for client generation."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    CSHARP = "csharp"
    RUST = "rust"


class ClientType(Enum):
    """Types of client SDKs that can be generated."""
    REST = "rest"
    ASYNC = "async"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"


@dataclass
class ClientGenerationConfig:
    """Configuration for client code generation."""
    language: Language
    client_type: ClientType
    package_name: str
    version: str = "1.0.0"
    author: str = "LLM Documentation Ecosystem"
    description: str = "Generated API Client"
    output_dir: str = "./generated_clients"
    include_tests: bool = True
    include_docs: bool = True
    authentication: Dict[str, Any] = None


@dataclass
class GeneratedClient:
    """Represents a generated client SDK."""
    language: Language
    client_type: ClientType
    package_name: str
    version: str
    files: Dict[str, str]  # filename -> content
    dependencies: List[str]
    installation_instructions: str
    usage_examples: Dict[str, str]


class ClientCodeGenerator:
    """
    Enterprise-grade client code generator for API services.

    Generates production-ready client SDKs in multiple languages with:
    - Type safety and validation
    - Comprehensive error handling
    - Authentication support
    - Unit tests and documentation
    - Async/await support where applicable
    """

    def __init__(self, discovery_client: DiscoveryClient, catalog_manager: APICatalogManager):
        self.discovery_client = discovery_client
        self.catalog_manager = catalog_manager
        self.templates = CodeTemplates()

    async def generate_client(
        self,
        service_name: str,
        config: ClientGenerationConfig
    ) -> GeneratedClient:
        """
        Generate a client SDK for a specific service.

        Args:
            service_name: Name of the service to generate client for
            config: Configuration for client generation

        Returns:
            GeneratedClient: Complete client SDK package
        """
        # Get service specification
        service_spec = await self._get_service_specification(service_name)
        if not service_spec:
            raise ValueError(f"Service '{service_name}' not found or no specification available")

        # Generate client based on language and type
        if config.language == Language.PYTHON:
            return await self._generate_python_client(service_spec, config)
        elif config.language == Language.TYPESCRIPT:
            return await self._generate_typescript_client(service_spec, config)
        elif config.language == Language.GO:
            return await self._generate_go_client(service_spec, config)
        elif config.language == Language.JAVA:
            return await self._generate_java_client(service_spec, config)
        else:
            raise ValueError(f"Language {config.language.value} not yet supported")

    async def generate_all_clients(
        self,
        config: ClientGenerationConfig,
        services_filter: Optional[List[str]] = None
    ) -> Dict[str, GeneratedClient]:
        """
        Generate client SDKs for all available services.

        Args:
            config: Base configuration for client generation
            services_filter: Optional list of services to generate clients for

        Returns:
            Dict of service_name -> GeneratedClient
        """
        # Get all available services
        services = await self.discovery_client.get_all_services()

        if services_filter:
            services = {name: spec for name, spec in services.items() if name in services_filter}

        results = {}
        for service_name in services.keys():
            try:
                # Customize config per service
                service_config = ClientGenerationConfig(
                    **config.__dict__,
                    package_name=f"{config.package_name}_{service_name.lower().replace('-', '_')}"
                )

                client = await self.generate_client(service_name, service_config)
                results[service_name] = client

            except Exception as e:
                print(f"Failed to generate client for {service_name}: {e}")
                continue

        return results

    async def validate_generated_client(
        self,
        client: GeneratedClient,
        service_name: str
    ) -> Dict[str, Any]:
        """
        Validate a generated client against the original service specification.

        Args:
            client: Generated client to validate
            service_name: Name of the service the client is for

        Returns:
            Validation results with success status and any issues
        """
        service_spec = await self._get_service_specification(service_name)
        if not service_spec:
            return {"valid": False, "errors": ["Service specification not found"]}

        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "coverage": {}
        }

        # Validate endpoints coverage
        spec_endpoints = self._extract_endpoints_from_spec(service_spec)
        client_endpoints = self._extract_endpoints_from_client(client)

        covered_endpoints = set(spec_endpoints.keys()) & set(client_endpoints.keys())
        missing_endpoints = set(spec_endpoints.keys()) - set(client_endpoints.keys())

        validation_results["coverage"] = {
            "total_endpoints": len(spec_endpoints),
            "covered_endpoints": len(covered_endpoints),
            "missing_endpoints": list(missing_endpoints),
            "coverage_percentage": len(covered_endpoints) / len(spec_endpoints) * 100 if spec_endpoints else 0
        }

        if missing_endpoints:
            validation_results["warnings"].append(
                f"Missing endpoints: {', '.join(missing_endpoints)}"
            )

        # Validate parameter types and schemas
        for endpoint in covered_endpoints:
            spec_params = spec_endpoints[endpoint].get("parameters", [])
            client_params = client_endpoints[endpoint].get("parameters", [])

            if len(spec_params) != len(client_params):
                validation_results["errors"].append(
                    f"Parameter count mismatch for {endpoint}: spec={len(spec_params)}, client={len(client_params)}"
                )

        return validation_results

    async def _get_service_specification(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get OpenAPI specification for a service."""
        try:
            # Try to get from discovery client first
            services = await self.discovery_client.get_all_services()
            if service_name in services:
                return services[service_name].get("openapi_spec")

            # Fallback to catalog manager
            catalog_entry = await self.catalog_manager.get_service_details(service_name)
            return catalog_entry.get("openapi_spec") if catalog_entry else None

        except Exception as e:
            print(f"Error getting specification for {service_name}: {e}")
            return None

    async def _generate_python_client(
        self,
        service_spec: Dict[str, Any],
        config: ClientGenerationConfig
    ) -> GeneratedClient:
        """Generate Python client SDK."""

        files = {}
        dependencies = ["requests", "pydantic", "typing-extensions"]

        if config.client_type == ClientType.ASYNC:
            dependencies.extend(["aiohttp", "asyncio"])

        # Generate main client class
        files["__init__.py"] = self.templates.get_python_init_template(config)
        files[f"{config.package_name.replace('-', '_')}.py"] = \
            self.templates.get_python_client_template(service_spec, config)

        # Generate models
        if "components" in service_spec and "schemas" in service_spec["components"]:
            files["models.py"] = self.templates.get_python_models_template(
                service_spec["components"]["schemas"], config
            )

        # Generate async version if requested
        if config.client_type == ClientType.ASYNC:
            files[f"{config.package_name.replace('-', '_')}_async.py"] = \
                self.templates.get_python_async_client_template(service_spec, config)
            dependencies.extend(["aiohttp", "asyncio"])

        # Generate tests
        if config.include_tests:
            files["test_client.py"] = self.templates.get_python_test_template(service_spec, config)

        # Generate documentation
        if config.include_docs:
            files["README.md"] = self.templates.get_python_readme_template(service_spec, config)
            files["examples.py"] = self.templates.get_python_examples_template(service_spec, config)

        # Generate setup.py
        files["setup.py"] = self.templates.get_python_setup_template(config, dependencies)

        return GeneratedClient(
            language=config.language,
            client_type=config.client_type,
            package_name=config.package_name,
            version=config.version,
            files=files,
            dependencies=dependencies,
            installation_instructions=f"pip install {config.package_name}",
            usage_examples=self._generate_usage_examples(service_spec, config)
        )

    async def _generate_typescript_client(
        self,
        service_spec: Dict[str, Any],
        config: ClientGenerationConfig
    ) -> GeneratedClient:
        """Generate TypeScript client SDK."""

        files = {}
        dependencies = ["axios", "@types/node"]

        # Generate main client class
        files["index.ts"] = self.templates.get_typescript_client_template(service_spec, config)

        # Generate type definitions
        if "components" in service_spec and "schemas" in service_spec["components"]:
            files["types.ts"] = self.templates.get_typescript_types_template(
                service_spec["components"]["schemas"], config
            )

        # Generate tests
        if config.include_tests:
            files["client.test.ts"] = self.templates.get_typescript_test_template(service_spec, config)

        # Generate documentation
        if config.include_docs:
            files["README.md"] = self.templates.get_typescript_readme_template(service_spec, config)

        # Generate package.json
        files["package.json"] = self.templates.get_typescript_package_template(config, dependencies)

        return GeneratedClient(
            language=config.language,
            client_type=config.client_type,
            package_name=config.package_name,
            version=config.version,
            files=files,
            dependencies=dependencies,
            installation_instructions=f"npm install {config.package_name}",
            usage_examples=self._generate_usage_examples(service_spec, config)
        )

    async def _generate_go_client(
        self,
        service_spec: Dict[str, Any],
        config: ClientGenerationConfig
    ) -> GeneratedClient:
        """Generate Go client SDK."""

        files = {}
        dependencies = []

        # Generate main client
        files["client.go"] = self.templates.get_go_client_template(service_spec, config)

        # Generate models
        if "components" in service_spec and "schemas" in service_spec["components"]:
            files["models.go"] = self.templates.get_go_models_template(
                service_spec["components"]["schemas"], config
            )

        # Generate tests
        if config.include_tests:
            files["client_test.go"] = self.templates.get_go_test_template(service_spec, config)

        # Generate go.mod
        files["go.mod"] = self.templates.get_go_mod_template(config)

        return GeneratedClient(
            language=config.language,
            client_type=config.client_type,
            package_name=config.package_name,
            version=config.version,
            files=files,
            dependencies=dependencies,
            installation_instructions=f"go get {config.package_name}",
            usage_examples=self._generate_usage_examples(service_spec, config)
        )

    async def _generate_java_client(
        self,
        service_spec: Dict[str, Any],
        config: ClientGenerationConfig
    ) -> GeneratedClient:
        """Generate Java client SDK."""

        files = {}
        dependencies = ["com.squareup.okhttp3:okhttp", "com.google.code.gson:gson"]

        # Generate main client class
        package_path = config.package_name.replace("-", "").lower()
        files[f"src/main/java/{package_path}/Client.java"] = \
            self.templates.get_java_client_template(service_spec, config)

        # Generate model classes
        if "components" in service_spec and "schemas" in service_spec["components"]:
            models_dir = f"src/main/java/{package_path}/models"
            for name, schema in service_spec["components"]["schemas"].items():
                files[f"{models_dir}/{name}.java"] = \
                    self.templates.get_java_model_template(name, schema, config)

        # Generate tests
        if config.include_tests:
            files[f"src/test/java/{package_path}/ClientTest.java"] = \
                self.templates.get_java_test_template(service_spec, config)

        # Generate pom.xml
        files["pom.xml"] = self.templates.get_java_pom_template(config, dependencies)

        return GeneratedClient(
            language=config.language,
            client_type=config.client_type,
            package_name=config.package_name,
            version=config.version,
            files=files,
            dependencies=dependencies,
            installation_instructions=f"mvn install (for local) or add to pom.xml",
            usage_examples=self._generate_usage_examples(service_spec, config)
        )

    def _extract_endpoints_from_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Extract endpoint information from OpenAPI spec."""
        endpoints = {}

        if "paths" not in spec:
            return endpoints

        for path, methods in spec["paths"].items():
            for method, details in methods.items():
                if isinstance(details, dict):
                    endpoint_key = f"{method.upper()} {path}"
                    endpoints[endpoint_key] = {
                        "parameters": details.get("parameters", []),
                        "responses": details.get("responses", {})
                    }

        return endpoints

    def _extract_endpoints_from_client(self, client: GeneratedClient) -> Dict[str, Any]:
        """Extract endpoint information from generated client."""
        # This is a simplified implementation - in practice, you'd parse the generated code
        endpoints = {}

        # For now, return empty dict - this would need language-specific parsing
        # In a full implementation, you'd parse the generated code files to extract method signatures

        return endpoints

    def _generate_usage_examples(self, service_spec: Dict[str, Any], config: ClientGenerationConfig) -> Dict[str, str]:
        """Generate usage examples for the client."""
        examples = {}

        # Basic usage example
        if config.language == Language.PYTHON:
            examples["basic"] = f"""
from {config.package_name} import Client

# Initialize client
client = Client(base_url="https://api.example.com")

# Make API calls
result = client.some_endpoint(param1="value1", param2="value2")
print(result)
"""

        elif config.language == Language.TYPESCRIPT:
            examples["basic"] = f"""
import {{ Client }} from '{config.package_name}';

const client = new Client({{ baseURL: 'https://api.example.com' }});

// Make API calls
const result = await client.someEndpoint({{ param1: 'value1', param2: 'value2' }});
console.log(result);
"""

        return examples

    async def save_client_to_disk(self, client: GeneratedClient, output_dir: Optional[str] = None) -> str:
        """
        Save generated client files to disk.

        Args:
            client: Generated client to save
            output_dir: Output directory (overrides config)

        Returns:
            Path to the saved client directory
        """
        base_dir = Path(output_dir or client.files.get("output_dir", "./generated_clients"))
        client_dir = base_dir / f"{client.package_name}_{client.language.value}"

        # Create directory structure
        client_dir.mkdir(parents=True, exist_ok=True)

        # Write files
        for filename, content in client.files.items():
            file_path = client_dir / filename

            # Create subdirectories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return str(client_dir)
