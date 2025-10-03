"""
Populate External Service Store with Sample Data

This script initializes the external-service-store database and populates it
with realistic external services relevant to a Scala/Elm/CRUD API project.
"""

import asyncio
import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "external-service-store"))

from infrastructure.repositories.sqlite_external_service_repository import SQLiteExternalServiceRepository
from domain.services.external_service_service import ExternalServiceService
from domain.repositories.external_service_repository import (
    ServiceEndpointRepository, ServiceDependencyRepository,
    ServiceDocumentRepository, ServiceUserRepository, ServiceTopicRepository
)
from infrastructure.repositories.sqlite_external_service_repository import (
    SQLiteServiceEndpointRepository, SQLiteServiceDependencyRepository,
    SQLiteServiceDocumentRepository, SQLiteServiceUserRepository,
    SQLiteServiceTopicRepository
)


async def populate_services():
    """Populate the external service store with sample data."""
    
    # Initialize database path
    db_path = Path(__file__).parent / "services" / "external-service-store" / "data" / "external_services.db"
    db_path.parent.mkdir(exist_ok=True)
    
    print(f"📁 Database: {db_path}")
    print(f"🔧 Initializing repositories...")
    
    # Initialize repositories
    service_repo = SQLiteExternalServiceRepository(str(db_path))
    endpoint_repo = SQLiteServiceEndpointRepository(str(db_path))
    dependency_repo = SQLiteServiceDependencyRepository(str(db_path))
    document_repo = SQLiteServiceDocumentRepository(str(db_path))
    user_repo = SQLiteServiceUserRepository(str(db_path))
    topic_repo = SQLiteServiceTopicRepository(str(db_path))
    
    # Initialize service
    service_service = ExternalServiceService(
        service_repo, endpoint_repo, dependency_repo,
        document_repo, user_repo, topic_repo
    )
    
    print(f"✅ Repositories initialized")
    print(f"\n📝 Creating sample services...")
    
    # Sample services relevant to Scala/Elm/CRUD API
    services_to_create = [
        {
            "name": "scala-http4s-api",
            "display_name": "Scala HTTP4s API",
            "description": "Pure functional Scala HTTP framework built on Cats Effect",
            "service_type": "API",
            "version": "0.23.16",
            "technologies": ["Scala", "Cats Effect", "HTTP4s", "Functional Programming"],
            "tags": ["backend", "api", "functional", "scala"]
        },
        {
            "name": "elm-frontend-framework",
            "display_name": "Elm Frontend Framework",
            "description": "Functional frontend framework with strong type system",
            "service_type": "WEB",
            "version": "0.19.1",
            "technologies": ["Elm", "Functional Programming", "Frontend"],
            "tags": ["frontend", "ui", "functional", "elm"]
        },
        {
            "name": "postgres-database",
            "display_name": "PostgreSQL Database",
            "description": "Advanced open-source relational database",
            "service_type": "DATABASE",
            "version": "15.3",
            "technologies": ["PostgreSQL", "SQL", "Database"],
            "tags": ["database", "storage", "sql", "postgres"]
        },
        {
            "name": "circe-json",
            "display_name": "Circe JSON Library",
            "description": "Functional JSON library for Scala",
            "service_type": "LIBRARY",
            "version": "0.14.5",
            "technologies": ["Scala", "JSON", "Cats"],
            "tags": ["json", "serialization", "scala", "circe"]
        },
        {
            "name": "doobie-database-layer",
            "display_name": "Doobie Database Layer",
            "description": "Pure functional JDBC layer for Scala",
            "service_type": "LIBRARY",
            "version": "1.0.0-RC4",
            "technologies": ["Scala", "JDBC", "Cats Effect", "Database"],
            "tags": ["database", "jdbc", "functional", "scala"]
        },
        {
            "name": "flyway-migrations",
            "display_name": "Flyway Database Migrations",
            "description": "Database migration tool",
            "service_type": "TOOL",
            "version": "9.20.0",
            "technologies": ["SQL", "Migrations", "Database"],
            "tags": ["database", "migrations", "versioning"]
        },
        {
            "name": "scalatest-framework",
            "display_name": "ScalaTest Testing Framework",
            "description": "Testing framework for Scala applications",
            "service_type": "TOOL",
            "version": "3.2.16",
            "technologies": ["Scala", "Testing"],
            "tags": ["testing", "scala", "scalatest"]
        },
        {
            "name": "sbt-build-tool",
            "display_name": "SBT Build Tool",
            "description": "Scala Build Tool for compiling and managing Scala projects",
            "service_type": "TOOL",
            "version": "1.9.2",
            "technologies": ["Scala", "Build Tool"],
            "tags": ["build", "scala", "sbt"]
        },
        {
            "name": "tapir-api-endpoints",
            "display_name": "Tapir API Endpoints",
            "description": "Type-safe API endpoints for Scala",
            "service_type": "LIBRARY",
            "version": "1.6.1",
            "technologies": ["Scala", "API", "Type Safety"],
            "tags": ["api", "endpoints", "scala", "tapir"]
        },
        {
            "name": "elm-json-decode",
            "display_name": "Elm JSON Decode",
            "description": "Built-in Elm JSON decoding library",
            "service_type": "LIBRARY",
            "version": "1.1.8",
            "technologies": ["Elm", "JSON"],
            "tags": ["elm", "json", "decoding"]
        },
        {
            "name": "elm-http-client",
            "display_name": "Elm HTTP Client",
            "description": "Built-in Elm HTTP library for making requests",
            "service_type": "LIBRARY",
            "version": "2.0.0",
            "technologies": ["Elm", "HTTP", "Client"],
            "tags": ["elm", "http", "client", "requests"]
        },
        {
            "name": "cats-effect-runtime",
            "display_name": "Cats Effect Runtime",
            "description": "Runtime for Cats Effect IO applications",
            "service_type": "LIBRARY",
            "version": "3.5.0",
            "technologies": ["Scala", "Cats Effect", "Functional Programming"],
            "tags": ["scala", "cats", "effects", "runtime"]
        },
        {
            "name": "swagger-openapi-docs",
            "display_name": "Swagger OpenAPI Documentation",
            "description": "API documentation and testing interface",
            "service_type": "TOOL",
            "version": "3.0.3",
            "technologies": ["OpenAPI", "API Documentation"],
            "tags": ["documentation", "api", "swagger", "openapi"]
        },
        {
            "name": "nginx-reverse-proxy",
            "display_name": "Nginx Reverse Proxy",
            "description": "HTTP and reverse proxy server",
            "service_type": "INFRASTRUCTURE",
            "version": "1.24.0",
            "technologies": ["Nginx", "HTTP", "Proxy"],
            "tags": ["proxy", "http", "nginx", "infrastructure"]
        },
        {
            "name": "docker-containers",
            "display_name": "Docker Containers",
            "description": "Containerization platform for deployment",
            "service_type": "INFRASTRUCTURE",
            "version": "24.0.5",
            "technologies": ["Docker", "Containers"],
            "tags": ["containers", "docker", "deployment"]
        }
    ]
    
    created_count = 0
    for service_data in services_to_create:
        try:
            service = await service_service.create_service(
                name=service_data["name"],
                display_name=service_data["display_name"],
                description=service_data["description"],
                service_type=service_data["service_type"],
                version=service_data["version"]
            )
            
            # Update with additional fields
            service.technologies = service_data.get("technologies", [])
            service.tags = service_data.get("tags", [])
            await service_repo.update(service)
            
            created_count += 1
            print(f"  ✅ Created: {service.display_name}")
        except ValueError as e:
            print(f"  ⚠️  Skipped {service_data['name']}: {e}")
        except Exception as e:
            print(f"  ❌ Error creating {service_data['name']}: {e}")
    
    print(f"\n✅ Created {created_count}/{len(services_to_create)} services")
    print(f"📁 Database location: {db_path}")
    print(f"💾 Database size: {db_path.stat().st_size / 1024:.1f} KB")
    
    return created_count


async def main():
    print("="*80)
    print("  🏗️  POPULATING EXTERNAL SERVICE STORE")
    print("="*80)
    print()
    
    count = await populate_services()
    
    print()
    print("="*80)
    print(f"✅ COMPLETE: {count} services added to external-service-store")
    print("="*80)
    print()
    print("Next step: Re-run the demo to see real Workflow E results!")
    print("  python demo_hyper_realistic_parameterized.py \\")
    print("    --feature \"Scala/Elm CRUD API\" \\")
    print("    --tickets 35 --team 8 \\")
    print("    --tech Scala \"Cats Effect\" Elm CRUD API \\")
    print("    --output scala_elm_crud_demo_v3")


if __name__ == "__main__":
    asyncio.run(main())

