"""Data Migration Script

Migrates existing data from the old schema to the new DDD schema.
This script handles the transition from the monolithic approach to domain-driven design.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib


class DataMigrator:
    """Handles data migration from old to new DDD schema."""

    def __init__(self, old_db_path: str, new_db_path: str):
        """Initialize migrator."""
        self.old_db_path = Path(old_db_path)
        self.new_db_path = Path(new_db_path)
        self.migration_stats = {
            "documents_migrated": 0,
            "analyses_migrated": 0,
            "findings_migrated": 0,
            "errors": []
        }

    def migrate_all_data(self) -> Dict[str, Any]:
        """Perform complete data migration."""
        print("🚀 Starting Data Migration")
        print("=" * 50)
        print(f"📁 Source: {self.old_db_path}")
        print(f"🎯 Target: {self.new_db_path}")

        if not self.old_db_path.exists():
            print("⚠️  No existing database found - starting fresh")
            return {
                "status": "completed",
                "message": "No existing data to migrate",
                "stats": self.migration_stats
            }

        try:
            # Connect to both databases
            old_conn = sqlite3.connect(str(self.old_db_path))
            new_conn = sqlite3.connect(str(self.new_db_path))

            old_conn.row_factory = sqlite3.Row
            new_conn.execute("PRAGMA foreign_keys = ON")

            # Perform migrations
            self._migrate_documents(old_conn, new_conn)
            self._migrate_analyses(old_conn, new_conn)
            self._migrate_findings(old_conn, new_conn)
            self._migrate_repositories(old_conn, new_conn)
            self._migrate_settings(old_conn, new_conn)

            # Record migration completion
            self._record_migration_completion(new_conn)

            old_conn.close()
            new_conn.close()

            print("\n✅ Data Migration Completed!")
            print(f"📊 Documents: {self.migration_stats['documents_migrated']}")
            print(f"📊 Analyses: {self.migration_stats['analyses_migrated']}")
            print(f"📊 Findings: {self.migration_stats['findings_migrated']}")
            print(f"❌ Errors: {len(self.migration_stats['errors'])}")

            return {
                "status": "completed",
                "stats": self.migration_stats,
                "migration_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            error_msg = f"Migration failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.migration_stats["errors"].append(error_msg)

            return {
                "status": "failed",
                "error": error_msg,
                "stats": self.migration_stats
            }

    def _migrate_documents(self, old_conn: sqlite3.Connection, new_conn: sqlite3.Connection):
        """Migrate documents from old to new schema."""
        print("📄 Migrating documents...")

        old_cursor = old_conn.cursor()
        new_cursor = new_conn.cursor()

        # Get existing documents
        old_cursor.execute("SELECT * FROM documents")
        old_documents = old_cursor.fetchall()

        migrated_count = 0
        for old_doc in old_documents:
            try:
                # Transform old document to new DDD format
                new_doc = self._transform_document(old_doc)

                # Insert into new schema
                new_cursor.execute("""
                    INSERT INTO documents (
                        id, title, content_text, content_format, content_hash,
                        author_id, author_name, author_email,
                        repository_id, repository_name, repository_url,
                        branch, commit_hash, file_path, tags, categories,
                        version, status, created_at, updated_at,
                        last_analyzed_at, analysis_count, quality_score,
                        metadata, domain_events
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_doc["id"],
                    new_doc["title"],
                    new_doc["content_text"],
                    new_doc["content_format"],
                    new_doc["content_hash"],
                    new_doc["author_id"],
                    new_doc["author_name"],
                    new_doc["author_email"],
                    new_doc["repository_id"],
                    new_doc["repository_name"],
                    new_doc["repository_url"],
                    new_doc["branch"],
                    new_doc["commit_hash"],
                    new_doc["file_path"],
                    new_doc["tags"],
                    new_doc["categories"],
                    new_doc["version"],
                    new_doc["status"],
                    new_doc["created_at"],
                    new_doc["updated_at"],
                    new_doc["last_analyzed_at"],
                    new_doc["analysis_count"],
                    new_doc["quality_score"],
                    new_doc["metadata"],
                    new_doc["domain_events"]
                ))

                migrated_count += 1

            except Exception as e:
                error_msg = f"Failed to migrate document {old_doc['id']}: {str(e)}"
                print(f"⚠️  {error_msg}")
                self.migration_stats["errors"].append(error_msg)

        new_conn.commit()
        self.migration_stats["documents_migrated"] = migrated_count
        print(f"✅ Migrated {migrated_count} documents")

    def _migrate_analyses(self, old_conn: sqlite3.Connection, new_conn: sqlite3.Connection):
        """Migrate analyses from old to new schema."""
        print("🔍 Migrating analyses...")

        old_cursor = old_conn.cursor()
        new_cursor = new_conn.cursor()

        # Try to find analyses table (may not exist in old schema)
        try:
            old_cursor.execute("SELECT * FROM analyses")
            old_analyses = old_cursor.fetchall()
        except sqlite3.OperationalError:
            print("ℹ️  No analyses table in old database")
            old_analyses = []

        migrated_count = 0
        for old_analysis in old_analyses:
            try:
                # Transform old analysis to new format
                new_analysis = self._transform_analysis(old_analysis)

                # Insert into new schema
                new_cursor.execute("""
                    INSERT INTO analyses (
                        id, document_id, analysis_type, status, priority,
                        configuration, results, error_message, started_at, completed_at,
                        duration_seconds, worker_id, correlation_id, created_by,
                        created_at, updated_at, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_analysis["id"],
                    new_analysis["document_id"],
                    new_analysis["analysis_type"],
                    new_analysis["status"],
                    new_analysis["priority"],
                    new_analysis["configuration"],
                    new_analysis["results"],
                    new_analysis["error_message"],
                    new_analysis["started_at"],
                    new_analysis["completed_at"],
                    new_analysis["duration_seconds"],
                    new_analysis["worker_id"],
                    new_analysis["correlation_id"],
                    new_analysis["created_by"],
                    new_analysis["created_at"],
                    new_analysis["updated_at"],
                    new_analysis["metadata"]
                ))

                migrated_count += 1

            except Exception as e:
                error_msg = f"Failed to migrate analysis {old_analysis.get('id', 'unknown')}: {str(e)}"
                print(f"⚠️  {error_msg}")
                self.migration_stats["errors"].append(error_msg)

        new_conn.commit()
        self.migration_stats["analyses_migrated"] = migrated_count
        print(f"✅ Migrated {migrated_count} analyses")

    def _migrate_findings(self, old_conn: sqlite3.Connection, new_conn: sqlite3.Connection):
        """Migrate findings from old to new schema."""
        print("🎯 Migrating findings...")

        old_cursor = old_conn.cursor()
        new_cursor = new_conn.cursor()

        # Try to find findings table
        try:
            old_cursor.execute("SELECT * FROM findings")
            old_findings = old_cursor.fetchall()
        except sqlite3.OperationalError:
            print("ℹ️  No findings table in old database")
            old_findings = []

        migrated_count = 0
        for old_finding in old_findings:
            try:
                # Transform old finding to new format
                new_finding = self._transform_finding(old_finding)

                # Insert into new schema
                new_cursor.execute("""
                    INSERT INTO findings (
                        id, analysis_id, document_id, finding_type, severity,
                        title, description, location, evidence, recommendation,
                        confidence, tags, status, assigned_to, resolved_at,
                        resolved_by, created_at, updated_at, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_finding["id"],
                    new_finding["analysis_id"],
                    new_finding["document_id"],
                    new_finding["finding_type"],
                    new_finding["severity"],
                    new_finding["title"],
                    new_finding["description"],
                    new_finding["location"],
                    new_finding["evidence"],
                    new_finding["recommendation"],
                    new_finding["confidence"],
                    new_finding["tags"],
                    new_finding["status"],
                    new_finding["assigned_to"],
                    new_finding["resolved_at"],
                    new_finding["resolved_by"],
                    new_finding["created_at"],
                    new_finding["updated_at"],
                    new_finding["metadata"]
                ))

                migrated_count += 1

            except Exception as e:
                error_msg = f"Failed to migrate finding {old_finding.get('id', 'unknown')}: {str(e)}"
                print(f"⚠️  {error_msg}")
                self.migration_stats["errors"].append(error_msg)

        new_conn.commit()
        self.migration_stats["findings_migrated"] = migrated_count
        print(f"✅ Migrated {migrated_count} findings")

    def _migrate_repositories(self, old_conn: sqlite3.Connection, new_conn: sqlite3.Connection):
        """Migrate repository information."""
        print("🏗️  Migrating repositories...")

        old_cursor = old_conn.cursor()
        new_cursor = new_conn.cursor()

        # Extract unique repositories from documents
        old_cursor.execute("""
            SELECT DISTINCT repository_id, repository_name, repository_url
            FROM documents
            WHERE repository_id IS NOT NULL
        """)

        repositories = old_cursor.fetchall()
        migrated_count = 0

        for repo in repositories:
            try:
                # Create repository entry
                repo_data = {
                    "id": repo["repository_id"] or f"repo_{hash(repo['repository_url'] or 'unknown') % 10000}",
                    "name": repo["repository_name"] or "Unknown Repository",
                    "url": repo["repository_url"] or "https://github.com/unknown/repo",
                    "repository_type": "github",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "metadata": json.dumps({"migrated": True, "source": "document_extraction"})
                }

                new_cursor.execute("""
                    INSERT OR IGNORE INTO repositories (
                        id, name, url, repository_type, created_at, updated_at, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    repo_data["id"],
                    repo_data["name"],
                    repo_data["url"],
                    repo_data["repository_type"],
                    repo_data["created_at"],
                    repo_data["updated_at"],
                    repo_data["metadata"]
                ))

                migrated_count += 1

            except Exception as e:
                error_msg = f"Failed to migrate repository {repo.get('repository_id', 'unknown')}: {str(e)}"
                print(f"⚠️  {error_msg}")
                self.migration_stats["errors"].append(error_msg)

        new_conn.commit()
        print(f"✅ Migrated {migrated_count} repositories")

    def _migrate_settings(self, old_conn: sqlite3.Connection, new_conn: sqlite3.Connection):
        """Migrate system settings and configuration."""
        print("⚙️  Migrating system settings...")

        # This would migrate any system settings from old to new format
        # For now, just create default settings
        new_cursor = new_conn.cursor()

        default_settings = [
            ("system.version", "1.0.0", "string"),
            ("migration.completed", "true", "boolean"),
            ("migration.timestamp", datetime.now().isoformat(), "string"),
            ("system.initialized", "true", "boolean")
        ]

        for key, value, value_type in default_settings:
            new_cursor.execute("""
                INSERT OR REPLACE INTO system_configuration (
                    config_key, config_value, config_type, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                key,
                json.dumps(value),
                value_type,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

        new_conn.commit()
        print("✅ System settings initialized")

    def _transform_document(self, old_doc) -> Dict[str, Any]:
        """Transform old document format to new DDD format."""
        # Generate content hash if not present
        content = old_doc.get("content_text", "")
        content_hash = hashlib.md5(content.encode()).hexdigest() if content else None

        # Transform tags from old format to JSON
        tags = old_doc.get("tags", "")
        if tags and not tags.startswith("["):
            tags = json.dumps([tag.strip() for tag in tags.split(",") if tag.strip()])
        elif not tags:
            tags = json.dumps([])

        # Create metadata with domain information
        metadata = {
            "migrated": True,
            "original_format": "legacy",
            "migration_date": datetime.now().isoformat(),
            "legacy_fields": {
                "old_id": old_doc.get("id"),
                "old_format": old_doc.get("content_format", "markdown")
            }
        }

        return {
            "id": old_doc["id"],
            "title": old_doc.get("title", "Untitled Document"),
            "content_text": content,
            "content_format": old_doc.get("content_format", "markdown"),
            "content_hash": content_hash,
            "author_id": old_doc.get("author"),
            "author_name": old_doc.get("author"),
            "author_email": None,
            "repository_id": old_doc.get("repository_id"),
            "repository_name": old_doc.get("repository_name"),
            "repository_url": old_doc.get("repository_url"),
            "branch": old_doc.get("branch", "main"),
            "commit_hash": old_doc.get("commit_hash"),
            "file_path": old_doc.get("file_path"),
            "tags": tags,
            "categories": json.dumps([]),
            "version": old_doc.get("version", "1.0.0"),
            "status": "active",
            "created_at": old_doc.get("created_at", datetime.now().isoformat()),
            "updated_at": old_doc.get("updated_at", datetime.now().isoformat()),
            "last_analyzed_at": None,
            "analysis_count": 0,
            "quality_score": old_doc.get("quality_score"),
            "metadata": json.dumps(metadata),
            "domain_events": json.dumps([])
        }

    def _transform_analysis(self, old_analysis) -> Dict[str, Any]:
        """Transform old analysis format to new format."""
        # Generate ID if not present
        analysis_id = old_analysis.get("id") or f"analysis_{hash(str(old_analysis)) % 10000}"

        # Create configuration JSON
        config = {
            "legacy_analysis": True,
            "original_type": old_analysis.get("analysis_type", "unknown")
        }

        # Create results JSON
        results = old_analysis.get("results", {})
        if isinstance(results, str):
            try:
                results = json.loads(results)
            except:
                results = {"legacy_result": results}

        return {
            "id": analysis_id,
            "document_id": old_analysis.get("document_id", "unknown"),
            "analysis_type": old_analysis.get("analysis_type", "general"),
            "status": old_analysis.get("status", "completed"),
            "priority": old_analysis.get("priority", 1),
            "configuration": json.dumps(config),
            "results": json.dumps(results),
            "error_message": old_analysis.get("error_message"),
            "started_at": old_analysis.get("started_at"),
            "completed_at": old_analysis.get("completed_at"),
            "duration_seconds": old_analysis.get("duration_seconds"),
            "worker_id": old_analysis.get("worker_id"),
            "correlation_id": old_analysis.get("correlation_id"),
            "created_by": old_analysis.get("created_by"),
            "created_at": old_analysis.get("created_at", datetime.now().isoformat()),
            "updated_at": old_analysis.get("updated_at", datetime.now().isoformat()),
            "metadata": json.dumps({"migrated": True})
        }

    def _transform_finding(self, old_finding) -> Dict[str, Any]:
        """Transform old finding format to new format."""
        # Generate ID if not present
        finding_id = old_finding.get("id") or f"finding_{hash(str(old_finding)) % 10000}"

        return {
            "id": finding_id,
            "analysis_id": old_finding.get("analysis_id", "unknown"),
            "document_id": old_finding.get("document_id", "unknown"),
            "finding_type": old_finding.get("finding_type", "general"),
            "severity": old_finding.get("severity", "medium"),
            "title": old_finding.get("title", "Legacy Finding"),
            "description": old_finding.get("description"),
            "location": json.dumps(old_finding.get("location", {})),
            "evidence": json.dumps(old_finding.get("evidence", [])),
            "recommendation": old_finding.get("recommendation"),
            "confidence": old_finding.get("confidence", 0.8),
            "tags": json.dumps(old_finding.get("tags", [])),
            "status": old_finding.get("status", "open"),
            "assigned_to": old_finding.get("assigned_to"),
            "resolved_at": old_finding.get("resolved_at"),
            "resolved_by": old_finding.get("resolved_by"),
            "created_at": old_finding.get("created_at", datetime.now().isoformat()),
            "updated_at": old_finding.get("updated_at", datetime.now().isoformat()),
            "metadata": json.dumps({"migrated": True})
        }

    def _record_migration_completion(self, new_conn: sqlite3.Connection):
        """Record migration completion in schema migrations table."""
        cursor = new_conn.cursor()

        migration_data = {
            "migration_id": "002_data_migration",
            "migration_name": "Data Migration from Legacy Schema",
            "executed_at": datetime.now().isoformat(),
            "execution_time_seconds": 0.0,
            "status": "completed",
            "metadata": json.dumps({
                "description": "Migrated existing data to new DDD schema",
                "stats": self.migration_stats,
                "migration_type": "data_migration"
            })
        }

        cursor.execute("""
            INSERT INTO schema_migrations
            (migration_id, migration_name, executed_at, execution_time_seconds, status, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            migration_data["migration_id"],
            migration_data["migration_name"],
            migration_data["executed_at"],
            migration_data["execution_time_seconds"],
            migration_data["status"],
            migration_data["metadata"]
        ))

        new_conn.commit()


def main():
    """Main migration function."""
    import argparse

    parser = argparse.ArgumentParser(description="Data Migration Script")
    parser.add_argument("--old-db", default="../data/analysis.db",
                       help="Path to old database file")
    parser.add_argument("--new-db", default="../data/analysis_ddd.db",
                       help="Path to new DDD database file")

    args = parser.parse_args()

    print("🔄 Data Migration Tool")
    print("=" * 50)

    migrator = DataMigrator(args.old_db, args.new_db)
    result = migrator.migrate_all_data()

    if result["status"] == "completed":
        print("\n🎉 Migration completed successfully!")
        print("📊 Migration Summary:")
        stats = result["stats"]
        print(f"   • Documents migrated: {stats['documents_migrated']}")
        print(f"   • Analyses migrated: {stats['analyses_migrated']}")
        print(f"   • Findings migrated: {stats['findings_migrated']}")
        print(f"   • Errors encountered: {len(stats['errors'])}")

        if stats["errors"]:
            print("\n⚠️  Errors during migration:")
            for error in stats["errors"][:5]:  # Show first 5 errors
                print(f"   • {error}")

        print("\n🚀 Next steps:")
        print("   1. Verify migrated data integrity")
        print("   2. Test application with new database")
        print("   3. Update application configuration")
        print("   4. Remove old database after verification")

    else:
        print(f"\n❌ Migration failed: {result.get('error', 'Unknown error')}")
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
