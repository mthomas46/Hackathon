"""
Simple SQLite Population Script for External Service Store

Directly populates the external-service-store SQLite database with sample services.
"""

import sqlite3
import uuid
import json
from datetime import datetime
from pathlib import Path


def create_database_schema(conn):
    """Create the database schema."""
    print("📐 Creating database schema...")
    
    # Main services table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS external_services (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            description TEXT,
            summary TEXT,
            service_type TEXT NOT NULL,
            status TEXT NOT NULL,
            version TEXT NOT NULL,
            latest_release TEXT,
            release_date TEXT,
            technologies TEXT NOT NULL,
            run_requirements TEXT NOT NULL,
            base_url TEXT,
            port INTEGER,
            health_endpoint TEXT,
            last_confluence_document TEXT,
            last_jira_ticket TEXT,
            last_github_pr TEXT,
            data_contracts TEXT NOT NULL,
            owner TEXT,
            maintainers TEXT NOT NULL,
            tags TEXT NOT NULL,
            metadata TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    print("  ✅ Schema created")


def insert_service(conn, service_data):
    """Insert a service into the database."""
    service_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    conn.execute("""
        INSERT INTO external_services (
            id, name, display_name, description, summary, service_type, status,
            version, latest_release, release_date, technologies, run_requirements,
            base_url, port, health_endpoint, last_confluence_document,
            last_jira_ticket, last_github_pr, data_contracts, owner,
            maintainers, tags, metadata, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        service_id,
        service_data["name"],
        service_data["display_name"],
        service_data["description"],
        service_data.get("summary", ""),
        service_data["service_type"],
        "ACTIVE",
        service_data["version"],
        service_data.get("latest_release"),
        service_data.get("release_date"),
        json.dumps(service_data.get("technologies", [])),
        json.dumps(service_data.get("run_requirements", {})),
        service_data.get("base_url"),
        service_data.get("port"),
        service_data.get("health_endpoint"),
        None,  # last_confluence_document
        None,  # last_jira_ticket
        None,  # last_github_pr
        json.dumps(service_data.get("data_contracts", {})),
        service_data.get("owner"),
        json.dumps(service_data.get("maintainers", [])),
        json.dumps(service_data.get("tags", [])),
        json.dumps(service_data.get("metadata", {})),
        now,
        now
    ))
    
    return service_id


def main():
    # Setup database path
    db_path = Path(__file__).parent / "services" / "external-service-store" / "data" / "external_services.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("  🏗️  POPULATING EXTERNAL SERVICE STORE (Simple Method)")
    print("=" * 80)
    print(f"\n📁 Database: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    
    # Create schema
    create_database_schema(conn)
    
    # Sample services relevant to Scala/Elm/CRUD API
    services_to_create = [
        {
            "name": "scala-http4s-api",
            "display_name": "Scala HTTP4s API",
            "description": "Pure functional Scala HTTP framework built on Cats Effect",
            "service_type": "API",
            "version": "0.23.16",
            "technologies": ["Scala", "Cats Effect", "HTTP4s", "Functional Programming"],
            "tags": ["backend", "api", "functional", "scala", "http4s", "cats"]
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
            "description": "Advanced open-source relational database for CRUD operations",
            "service_type": "DATABASE",
            "version": "15.3",
            "technologies": ["PostgreSQL", "SQL", "Database", "CRUD"],
            "tags": ["database", "storage", "sql", "postgres", "crud"]
        },
        {
            "name": "circe-json",
            "display_name": "Circe JSON Library",
            "description": "Functional JSON library for Scala - essential for REST APIs",
            "service_type": "LIBRARY",
            "version": "0.14.5",
            "technologies": ["Scala", "JSON", "Cats", "API"],
            "tags": ["json", "serialization", "scala", "circe", "api"]
        },
        {
            "name": "doobie-database-layer",
            "display_name": "Doobie Database Layer",
            "description": "Pure functional JDBC layer for Scala - perfect for CRUD operations",
            "service_type": "LIBRARY",
            "version": "1.0.0-RC4",
            "technologies": ["Scala", "JDBC", "Cats Effect", "Database", "CRUD"],
            "tags": ["database", "jdbc", "functional", "scala", "crud"]
        },
        {
            "name": "flyway-migrations",
            "display_name": "Flyway Database Migrations",
            "description": "Database migration tool for managing schema changes",
            "service_type": "TOOL",
            "version": "9.20.0",
            "technologies": ["SQL", "Migrations", "Database"],
            "tags": ["database", "migrations", "versioning", "sql"]
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
            "description": "Type-safe API endpoints for Scala - ideal for CRUD operations",
            "service_type": "LIBRARY",
            "version": "1.6.1",
            "technologies": ["Scala", "API", "Type Safety", "CRUD"],
            "tags": ["api", "endpoints", "scala", "tapir", "crud"]
        },
        {
            "name": "elm-json-decode",
            "display_name": "Elm JSON Decode",
            "description": "Built-in Elm JSON decoding library for API responses",
            "service_type": "LIBRARY",
            "version": "1.1.8",
            "technologies": ["Elm", "JSON", "API"],
            "tags": ["elm", "json", "decoding", "api"]
        },
        {
            "name": "elm-http-client",
            "display_name": "Elm HTTP Client",
            "description": "Built-in Elm HTTP library for making CRUD API requests",
            "service_type": "LIBRARY",
            "version": "2.0.0",
            "technologies": ["Elm", "HTTP", "Client", "API"],
            "tags": ["elm", "http", "client", "requests", "api"]
        },
        {
            "name": "cats-effect-runtime",
            "display_name": "Cats Effect Runtime",
            "description": "Runtime for Cats Effect IO applications - core of HTTP4s",
            "service_type": "LIBRARY",
            "version": "3.5.0",
            "technologies": ["Scala", "Cats Effect", "Functional Programming"],
            "tags": ["scala", "cats", "effects", "runtime"]
        },
        {
            "name": "swagger-openapi-docs",
            "display_name": "Swagger OpenAPI Documentation",
            "description": "API documentation and testing interface for REST APIs",
            "service_type": "TOOL",
            "version": "3.0.3",
            "technologies": ["OpenAPI", "API Documentation", "REST"],
            "tags": ["documentation", "api", "swagger", "openapi", "rest"]
        },
        {
            "name": "nginx-reverse-proxy",
            "display_name": "Nginx Reverse Proxy",
            "description": "HTTP and reverse proxy server for serving APIs",
            "service_type": "INFRASTRUCTURE",
            "version": "1.24.0",
            "technologies": ["Nginx", "HTTP", "Proxy", "API"],
            "tags": ["proxy", "http", "nginx", "infrastructure", "api"]
        },
        {
            "name": "docker-containers",
            "display_name": "Docker Containers",
            "description": "Containerization platform for deployment of Scala and Elm apps",
            "service_type": "INFRASTRUCTURE",
            "version": "24.0.5",
            "technologies": ["Docker", "Containers", "Deployment"],
            "tags": ["containers", "docker", "deployment"]
        }
    ]
    
    print(f"\n📝 Inserting {len(services_to_create)} services...")
    created_count = 0
    
    for service_data in services_to_create:
        try:
            service_id = insert_service(conn, service_data)
            conn.commit()
            created_count += 1
            print(f"  ✅ Created: {service_data['display_name']} (ID: {service_id[:8]}...)")
        except sqlite3.IntegrityError as e:
            print(f"  ⚠️  Skipped {service_data['name']}: Already exists")
        except Exception as e:
            print(f"  ❌ Error creating {service_data['name']}: {e}")
    
    conn.close()
    
    print(f"\n✅ Created {created_count}/{len(services_to_create)} services")
    print(f"📁 Database location: {db_path}")
    print(f"💾 Database size: {db_path.stat().st_size / 1024:.1f} KB")
    
    print("\n" + "=" * 80)
    print(f"✅ COMPLETE: {created_count} services added to external-service-store")
    print("=" * 80)
    print("\nNow the demo should find these services during Workflow E!")
    print("\nNote: The demo still needs service clients to actually query the database.")
    print("But at least now the database exists with data!\n")


if __name__ == "__main__":
    main()

