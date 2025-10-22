"""
Database Schema Validator

Connects to PostgreSQL and compares:
1. What code is trying to insert (from SQLAlchemy models)
2. What columns actually exist in the database
3. Reports ALL mismatches before any code runs

This prevents the "one error at a time" problem by finding everything upfront.
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Set, Tuple
import asyncpg
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class ColumnInfo:
    """Information about a database column."""
    name: str
    data_type: str
    is_nullable: bool
    column_default: str = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_table: str = None


@dataclass
class TableSchema:
    """Complete schema for a database table."""
    table_name: str
    columns: Dict[str, ColumnInfo] = field(default_factory=dict)
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: Dict[str, str] = field(default_factory=dict)
    indexes: List[str] = field(default_factory=list)


@dataclass
class SchemaMismatch:
    """Represents a schema mismatch."""
    severity: str  # 'CRITICAL', 'WARNING', 'INFO'
    table: str
    issue_type: str
    description: str
    suggested_fix: str = None


class DatabaseSchemaValidator:
    """Validates database schema against code expectations."""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.schemas: Dict[str, TableSchema] = {}
        self.mismatches: List[SchemaMismatch] = []
    
    async def connect_and_analyze(self):
        """Connect to database and analyze all schemas."""
        print("🔌 Connecting to PostgreSQL...")
        
        try:
            conn = await asyncpg.connect(self.db_url)
            print("✅ Connected to database")
            
            # Get all tables
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            print(f"\n📊 Found {len(tables)} tables in database")
            
            for table_row in tables:
                table_name = table_row['table_name']
                await self._analyze_table(conn, table_name)
            
            await conn.close()
            print("✅ Analysis complete")
            
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            print(f"   URL: {self.db_url[:30]}...")
            raise
    
    async def _analyze_table(self, conn, table_name: str):
        """Analyze a single table's schema."""
        schema = TableSchema(table_name=table_name)
        
        # Get column information
        columns = await conn.fetch("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = $1
            ORDER BY ordinal_position
        """, table_name)
        
        for col in columns:
            col_info = ColumnInfo(
                name=col['column_name'],
                data_type=col['data_type'],
                is_nullable=(col['is_nullable'] == 'YES'),
                column_default=col['column_default']
            )
            schema.columns[col['column_name']] = col_info
        
        # Get primary keys
        pks = await conn.fetch("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = $1 
                AND tc.constraint_type = 'PRIMARY KEY'
        """, table_name)
        
        schema.primary_keys = [pk['column_name'] for pk in pks]
        for pk in schema.primary_keys:
            if pk in schema.columns:
                schema.columns[pk].is_primary_key = True
        
        # Get foreign keys
        fks = await conn.fetch("""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.table_name = $1 
                AND tc.constraint_type = 'FOREIGN KEY'
        """, table_name)
        
        for fk in fks:
            col_name = fk['column_name']
            foreign_table = fk['foreign_table_name']
            schema.foreign_keys[col_name] = foreign_table
            if col_name in schema.columns:
                schema.columns[col_name].is_foreign_key = True
                schema.columns[col_name].foreign_table = foreign_table
        
        # Get indexes
        indexes = await conn.fetch("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = $1
        """, table_name)
        
        schema.indexes = [idx['indexname'] for idx in indexes]
        
        self.schemas[table_name] = schema
    
    def check_insert_statement(self, table_name: str, columns: List[str]) -> List[SchemaMismatch]:
        """Check if an INSERT statement would succeed."""
        mismatches = []
        
        if table_name not in self.schemas:
            mismatches.append(SchemaMismatch(
                severity='CRITICAL',
                table=table_name,
                issue_type='TABLE_NOT_FOUND',
                description=f"Table '{table_name}' does not exist in database",
                suggested_fix="Create table with migration or check table name"
            ))
            return mismatches
        
        schema = self.schemas[table_name]
        db_columns = set(schema.columns.keys())
        insert_columns = set(columns)
        
        # Check for columns in INSERT that don't exist
        missing_in_db = insert_columns - db_columns
        for col in missing_in_db:
            mismatches.append(SchemaMismatch(
                severity='CRITICAL',
                table=table_name,
                issue_type='COLUMN_NOT_FOUND',
                description=f"Column '{col}' in INSERT does not exist in table",
                suggested_fix=f"Add column to table or remove from INSERT: ALTER TABLE {table_name} ADD COLUMN {col} ..."
            ))
        
        # Check for required columns (NOT NULL, no default) not in INSERT
        for col_name, col_info in schema.columns.items():
            if (not col_info.is_nullable and 
                col_info.column_default is None and
                not col_info.is_primary_key and
                col_name not in insert_columns):
                mismatches.append(SchemaMismatch(
                    severity='WARNING',
                    table=table_name,
                    issue_type='MISSING_REQUIRED_COLUMN',
                    description=f"Required column '{col_name}' (NOT NULL, no default) not in INSERT",
                    suggested_fix=f"Add column to INSERT or make nullable/add default"
                ))
        
        return mismatches
    
    def check_foreign_key(self, table_name: str, column_name: str, referenced_table: str) -> List[SchemaMismatch]:
        """Check if a foreign key reference is valid."""
        mismatches = []
        
        if table_name not in self.schemas:
            return mismatches
        
        schema = self.schemas[table_name]
        
        if column_name not in schema.columns:
            return mismatches
        
        col = schema.columns[column_name]
        
        if col.is_foreign_key:
            if col.foreign_table != referenced_table:
                mismatches.append(SchemaMismatch(
                    severity='CRITICAL',
                    table=table_name,
                    issue_type='FOREIGN_KEY_MISMATCH',
                    description=f"Column '{column_name}' references '{col.foreign_table}' but code expects '{referenced_table}'",
                    suggested_fix=f"Update code to reference correct table or fix FK constraint"
                ))
        elif referenced_table:
            mismatches.append(SchemaMismatch(
                severity='WARNING',
                table=table_name,
                issue_type='MISSING_FOREIGN_KEY',
                description=f"Column '{column_name}' should reference '{referenced_table}' but no FK exists",
                suggested_fix=f"Add FK constraint or remove FK reference in code"
            ))
        
        return mismatches
    
    def generate_report(self) -> str:
        """Generate comprehensive schema report."""
        report = []
        report.append("=" * 80)
        report.append("DATABASE SCHEMA ANALYSIS REPORT")
        report.append("=" * 80)
        
        # Tables overview
        report.append(f"\n📊 TABLES FOUND: {len(self.schemas)}")
        report.append("-" * 80)
        
        for table_name, schema in sorted(self.schemas.items()):
            report.append(f"\n🗄️  {table_name}")
            report.append(f"   Columns: {len(schema.columns)}")
            report.append(f"   Primary Keys: {', '.join(schema.primary_keys) if schema.primary_keys else 'None'}")
            report.append(f"   Foreign Keys: {len(schema.foreign_keys)}")
            report.append(f"   Indexes: {len(schema.indexes)}")
            
            # Show first few columns
            for i, (col_name, col_info) in enumerate(list(schema.columns.items())[:8]):
                nullable = "nullable" if col_info.is_nullable else "NOT NULL"
                pk = " [PK]" if col_info.is_primary_key else ""
                fk = f" [FK -> {col_info.foreign_table}]" if col_info.is_foreign_key else ""
                report.append(f"      • {col_name}: {col_info.data_type} ({nullable}){pk}{fk}")
            
            if len(schema.columns) > 8:
                report.append(f"      ... and {len(schema.columns) - 8} more columns")
        
        return "\n".join(report)


async def validate_known_operations():
    """Validate known INSERT operations from our code."""
    print("\n" + "=" * 80)
    print("🔍 VALIDATING KNOWN OPERATIONS")
    print("=" * 80)
    
    # Database connection
    db_url = "postgresql://ecosystem_user:ecosystem_pass@localhost:5433/ecosystem_db"
    
    validator = DatabaseSchemaValidator(db_url)
    await validator.connect_and_analyze()
    
    # Print full schema report
    print("\n" + validator.generate_report())
    
    # Known operations from our code
    known_operations = [
        {
            'operation': 'Create AnalysisResultModel',
            'table': 'analysis_results',
            'columns': [
                'id', 'plan_id', 'repo_id', 'repo_path',
                'analysis_complete', 'errors',
                'has_dependency_graph', 'total_nodes', 'total_edges',
                'circular_dependencies', 'topological_order',
                'primary_language', 'total_languages', 'total_frameworks', 'total_databases',
                'primary_architecture', 'architecture_confidence', 
                'secondary_architectures', 'detected_layers',
                'total_services', 'is_microservices', 'service_dependencies',
                'total_files', 'modularity_score',
                'dependency_graph', 'technology_stack', 'architecture_analysis', 'service_map',
                'created_at', 'updated_at'
            ]
        },
        {
            'operation': 'Create RepositoryContextModel',
            'table': 'repository_contexts',
            'columns': [
                'repo_id', 'repo_name', 'architecture_type', 
                'service_count', 'endpoint_count', 'has_rest_api'
            ]
        },
        {
            'operation': 'Create DocumentationRunModel',
            'table': 'documentation_runs',
            'columns': [
                'id', 'plan_id', 'repo_id', 'passes_completed', 'total_passes',
                'current_pass', 'config', 'status', 'started_at', 'completed_at',
                'total_artifacts', 'total_words', 'overall_quality_score',
                'output_path', 'output_formats', 'created_at', 'updated_at'
            ]
        },
        {
            'operation': 'Query ProcessingPlanModel',
            'table': 'processing_plans',
            'columns': ['id', 'repo_path', 'status', 'created_at']
        },
        {
            'operation': 'Query FileClassificationModel',
            'table': 'file_classifications',
            'columns': [
                'file_path', 'relative_path', 'size_bytes', 'extension',
                'language', 'is_code', 'is_test', 'is_doc',
                'importance_level', 'importance_score'
            ]
        }
    ]
    
    print("\n" + "=" * 80)
    print("⚠️  SCHEMA VALIDATION RESULTS")
    print("=" * 80)
    
    all_mismatches = []
    
    for op in known_operations:
        print(f"\n🔍 Checking: {op['operation']}")
        print(f"   Table: {op['table']}")
        print(f"   Columns: {len(op['columns'])}")
        
        mismatches = validator.check_insert_statement(op['table'], op['columns'])
        
        if mismatches:
            all_mismatches.extend(mismatches)
            for mismatch in mismatches:
                icon = "🔴" if mismatch.severity == 'CRITICAL' else "🟡" if mismatch.severity == 'WARNING' else "🔵"
                print(f"   {icon} {mismatch.severity}: {mismatch.description}")
                if mismatch.suggested_fix:
                    print(f"      Fix: {mismatch.suggested_fix}")
        else:
            print(f"   ✅ All columns valid")
    
    # Foreign key checks
    print("\n" + "=" * 80)
    print("🔗 FOREIGN KEY VALIDATION")
    print("=" * 80)
    
    fk_checks = [
        ('analysis_results', 'repo_id', 'repository_contexts'),
        ('analysis_results', 'plan_id', 'processing_plans'),
        ('file_classifications', 'plan_id', 'processing_plans'),
    ]
    
    for table, column, ref_table in fk_checks:
        print(f"\n🔍 Checking FK: {table}.{column} -> {ref_table}")
        fk_mismatches = validator.check_foreign_key(table, column, ref_table)
        
        if fk_mismatches:
            all_mismatches.extend(fk_mismatches)
            for mismatch in fk_mismatches:
                print(f"   🔴 {mismatch.description}")
                if mismatch.suggested_fix:
                    print(f"      Fix: {mismatch.suggested_fix}")
        else:
            print(f"   ✅ Foreign key valid")
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 VALIDATION SUMMARY")
    print("=" * 80)
    
    critical = sum(1 for m in all_mismatches if m.severity == 'CRITICAL')
    warnings = sum(1 for m in all_mismatches if m.severity == 'WARNING')
    
    print(f"\n🔴 Critical Issues: {critical}")
    print(f"🟡 Warnings: {warnings}")
    print(f"✅ Operations Checked: {len(known_operations)}")
    print(f"🔗 Foreign Keys Checked: {len(fk_checks)}")
    
    if critical > 0:
        print("\n⚠️  CRITICAL ISSUES MUST BE FIXED BEFORE CODE WILL WORK")
    elif warnings > 0:
        print("\n⚠️  WARNINGS SHOULD BE REVIEWED")
    else:
        print("\n✅ ALL VALIDATIONS PASSED!")
    
    # Save detailed report
    report_file = PROJECT_ROOT / "DATABASE_SCHEMA_VALIDATION_REPORT.md"
    with open(report_file, 'w') as f:
        f.write("# Database Schema Validation Report\n\n")
        f.write(f"**Generated:** {asyncio.get_event_loop().time()}\n\n")
        f.write("## Schema Overview\n\n")
        f.write(validator.generate_report())
        f.write("\n\n## Validation Issues\n\n")
        
        if all_mismatches:
            for i, mismatch in enumerate(all_mismatches, 1):
                f.write(f"### {i}. {mismatch.severity}: {mismatch.issue_type}\n\n")
                f.write(f"- **Table:** `{mismatch.table}`\n")
                f.write(f"- **Issue:** {mismatch.description}\n")
                if mismatch.suggested_fix:
                    f.write(f"- **Fix:** {mismatch.suggested_fix}\n")
                f.write("\n")
        else:
            f.write("✅ No issues found!\n")
    
    print(f"\n💾 Detailed report saved to: {report_file}")
    
    return all_mismatches


async def main():
    """Main entry point."""
    print("=" * 80)
    print("🔍 DATABASE SCHEMA VALIDATOR")
    print("=" * 80)
    print("\nThis tool validates that our code's INSERT/UPDATE operations")
    print("match the actual database schema, preventing runtime errors.\n")
    
    try:
        mismatches = await validate_known_operations()
        
        if any(m.severity == 'CRITICAL' for m in mismatches):
            sys.exit(1)
        else:
            sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

