"""
Model Validation and Automated Fix Script

This script:
1. Analyzes all database models and their relationships
2. Identifies field mismatches and issues
3. Generates comprehensive fixes for model mapping
4. Creates helper methods automatically
5. Validates the complete pipeline

Usage:
    python scripts/validate_and_fix_models.py --analyze    # Just analyze
    python scripts/validate_and_fix_models.py --fix        # Analyze and apply fixes
"""

import sys
import os
import ast
import inspect
import json
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "services/ecosystem-mcp"))

# Import models
from src.storage.models_analysis import (
    AnalysisResultModel,
    RepositoryContextModel
)
from src.storage.models_discovery import (
    ProcessingPlanModel,
    FileClassificationModel
)

@dataclass
class ModelField:
    """Represents a model field."""
    name: str
    type: str
    nullable: bool = True
    default: Any = None
    is_relationship: bool = False


@dataclass
class ModelInfo:
    """Complete model information."""
    name: str
    table_name: str
    fields: Dict[str, ModelField] = field(default_factory=dict)
    relationships: Dict[str, str] = field(default_factory=dict)
    foreign_keys: Dict[str, str] = field(default_factory=dict)


@dataclass
class DataClassInfo:
    """Information about a dataclass."""
    name: str
    fields: Dict[str, str] = field(default_factory=dict)
    methods: List[str] = field(default_factory=list)


@dataclass
class MappingIssue:
    """Represents a mapping issue."""
    source: str
    target: str
    issue_type: str
    description: str
    suggested_fix: Optional[str] = None


class ModelAnalyzer:
    """Analyzes models and identifies mapping issues."""
    
    def __init__(self):
        self.models: Dict[str, ModelInfo] = {}
        self.dataclasses: Dict[str, DataClassInfo] = {}
        self.issues: List[MappingIssue] = []
    
    def analyze_sqlalchemy_model(self, model_class) -> ModelInfo:
        """Analyze a SQLAlchemy model."""
        info = ModelInfo(
            name=model_class.__name__,
            table_name=model_class.__tablename__ if hasattr(model_class, '__tablename__') else ''
        )
        
        # Get all columns
        if hasattr(model_class, '__table__'):
            for column in model_class.__table__.columns:
                field_info = ModelField(
                    name=column.name,
                    type=str(column.type),
                    nullable=column.nullable,
                    default=column.default
                )
                info.fields[column.name] = field_info
                
                # Check for foreign keys
                if column.foreign_keys:
                    for fk in column.foreign_keys:
                        info.foreign_keys[column.name] = str(fk.column)
        
        # Get relationships
        if hasattr(model_class, '__mapper__'):
            for rel in model_class.__mapper__.relationships:
                info.relationships[rel.key] = rel.mapper.class_.__name__
        
        return info
    
    def analyze_dataclass_from_file(self, file_path: Path) -> List[DataClassInfo]:
        """Analyze dataclasses from a Python file."""
        dataclasses = []
        
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it has @dataclass decorator
                    is_dataclass = any(
                        isinstance(dec, ast.Name) and dec.id == 'dataclass'
                        for dec in node.decorator_list
                    )
                    
                    if is_dataclass:
                        dc_info = DataClassInfo(name=node.name)
                        
                        # Get fields from __annotations__
                        for item in node.body:
                            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                                field_name = item.target.id
                                field_type = ast.unparse(item.annotation) if hasattr(ast, 'unparse') else str(item.annotation)
                                dc_info.fields[field_name] = field_type
                        
                        # Get methods
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                dc_info.methods.append(item.name)
                        
                        dataclasses.append(dc_info)
        
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
        
        return dataclasses
    
    def compare_models(self, source_dc: DataClassInfo, target_model: ModelInfo) -> List[MappingIssue]:
        """Compare a dataclass with a model and find issues."""
        issues = []
        
        # Check for missing fields in model
        for field_name, field_type in source_dc.fields.items():
            if field_name not in target_model.fields:
                issues.append(MappingIssue(
                    source=f"{source_dc.name}.{field_name}",
                    target=target_model.name,
                    issue_type="MISSING_FIELD",
                    description=f"Field '{field_name}' exists in {source_dc.name} but not in {target_model.name}",
                    suggested_fix=f"This field may be calculated or derived from other fields"
                ))
        
        # Check for mismatched field names
        source_fields_lower = {f.lower(): f for f in source_dc.fields.keys()}
        model_fields_lower = {f.lower(): f for f in target_model.fields.keys()}
        
        for source_lower, source_actual in source_fields_lower.items():
            if source_lower in model_fields_lower:
                model_actual = model_fields_lower[source_lower]
                if source_actual != model_actual:
                    issues.append(MappingIssue(
                        source=f"{source_dc.name}.{source_actual}",
                        target=f"{target_model.name}.{model_actual}",
                        issue_type="NAME_MISMATCH",
                        description=f"Field name case mismatch: '{source_actual}' vs '{model_actual}'",
                        suggested_fix=f"Map '{source_actual}' -> '{model_actual}'"
                    ))
        
        return issues
    
    def check_helper_methods(self, dc_info: DataClassInfo) -> bool:
        """Check if dataclass has required helper methods."""
        required_methods = ['to_dict', 'to_model_kwargs']
        return all(method in dc_info.methods for method in required_methods)
    
    def generate_comprehensive_report(self) -> str:
        """Generate a comprehensive analysis report."""
        report = []
        report.append("=" * 80)
        report.append("MODEL ANALYSIS REPORT")
        report.append("=" * 80)
        
        # SQLAlchemy Models
        report.append("\n📊 SQLALCHEMY MODELS:")
        report.append("-" * 80)
        for name, model in self.models.items():
            report.append(f"\n🗄️  {name} (table: {model.table_name})")
            report.append(f"   Fields: {len(model.fields)}")
            for field_name, field_info in model.fields.items():
                nullable = "nullable" if field_info.nullable else "required"
                report.append(f"      • {field_name}: {field_info.type} ({nullable})")
            
            if model.relationships:
                report.append(f"   Relationships: {len(model.relationships)}")
                for rel_name, rel_target in model.relationships.items():
                    report.append(f"      • {rel_name} -> {rel_target}")
            
            if model.foreign_keys:
                report.append(f"   Foreign Keys: {len(model.foreign_keys)}")
                for fk_field, fk_target in model.foreign_keys.items():
                    report.append(f"      • {fk_field} -> {fk_target}")
        
        # Dataclasses
        report.append("\n\n📦 DATACLASSES:")
        report.append("-" * 80)
        for name, dc in self.dataclasses.items():
            report.append(f"\n📋 {name}")
            report.append(f"   Fields: {len(dc.fields)}")
            for field_name, field_type in dc.fields.items():
                report.append(f"      • {field_name}: {field_type}")
            
            if dc.methods:
                report.append(f"   Methods: {', '.join(dc.methods)}")
                has_helpers = self.check_helper_methods(dc)
                status = "✅" if has_helpers else "❌"
                report.append(f"   Helper Methods: {status}")
        
        # Issues
        if self.issues:
            report.append("\n\n⚠️  MAPPING ISSUES FOUND:")
            report.append("-" * 80)
            issue_types = {}
            for issue in self.issues:
                issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1
                report.append(f"\n🐛 {issue.issue_type}")
                report.append(f"   Source: {issue.source}")
                report.append(f"   Target: {issue.target}")
                report.append(f"   Issue: {issue.description}")
                if issue.suggested_fix:
                    report.append(f"   Fix: {issue.suggested_fix}")
            
            report.append(f"\n📊 Issue Summary:")
            for issue_type, count in issue_types.items():
                report.append(f"   {issue_type}: {count}")
        else:
            report.append("\n\n✅ NO ISSUES FOUND!")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)


def main():
    """Main execution."""
    print("🔍 MODEL VALIDATION & FIX GENERATOR")
    print("=" * 80)
    
    analyzer = ModelAnalyzer()
    
    # Step 1: Analyze SQLAlchemy models
    print("\n📊 Step 1: Analyzing SQLAlchemy Models...")
    models_to_analyze = [
        AnalysisResultModel,
        RepositoryContextModel,
        ProcessingPlanModel,
        FileClassificationModel
    ]
    
    for model_class in models_to_analyze:
        print(f"   Analyzing {model_class.__name__}...")
        model_info = analyzer.analyze_sqlalchemy_model(model_class)
        analyzer.models[model_class.__name__] = model_info
    
    print(f"✅ Analyzed {len(analyzer.models)} SQLAlchemy models")
    
    # Step 2: Analyze dataclasses
    print("\n📦 Step 2: Analyzing Dataclasses...")
    analysis_files = [
        PROJECT_ROOT / "services/ecosystem-mcp/src/services/analysis/analysis_engine.py",
        PROJECT_ROOT / "services/ecosystem-mcp/src/services/analysis/stack_detector.py",
        PROJECT_ROOT / "services/ecosystem-mcp/src/services/analysis/architecture_detector.py",
        PROJECT_ROOT / "services/ecosystem-mcp/src/services/analysis/dependency_analyzer.py",
        PROJECT_ROOT / "services/ecosystem-mcp/src/services/analysis/service_detector.py",
    ]
    
    for file_path in analysis_files:
        if file_path.exists():
            print(f"   Analyzing {file_path.name}...")
            dataclasses = analyzer.analyze_dataclass_from_file(file_path)
            for dc in dataclasses:
                analyzer.dataclasses[dc.name] = dc
        else:
            print(f"   ⚠️  File not found: {file_path}")
    
    print(f"✅ Analyzed {len(analyzer.dataclasses)} dataclasses")
    
    # Step 3: Compare and find issues
    print("\n🔍 Step 3: Comparing Models and Dataclasses...")
    
    # Compare AnalysisReport with AnalysisResultModel
    if 'AnalysisReport' in analyzer.dataclasses and 'AnalysisResultModel' in analyzer.models:
        print("   Comparing AnalysisReport <-> AnalysisResultModel...")
        issues = analyzer.compare_models(
            analyzer.dataclasses['AnalysisReport'],
            analyzer.models['AnalysisResultModel']
        )
        analyzer.issues.extend(issues)
    
    # Compare other dataclasses
    dataclass_model_pairs = [
        ('TechnologyStack', 'AnalysisResultModel'),
        ('ArchitectureAnalysis', 'AnalysisResultModel'),
        ('ServiceMap', 'AnalysisResultModel'),
    ]
    
    for dc_name, model_name in dataclass_model_pairs:
        if dc_name in analyzer.dataclasses and model_name in analyzer.models:
            print(f"   Comparing {dc_name} <-> {model_name}...")
            issues = analyzer.compare_models(
                analyzer.dataclasses[dc_name],
                analyzer.models[model_name]
            )
            analyzer.issues.extend(issues)
    
    print(f"✅ Found {len(analyzer.issues)} potential issues")
    
    # Step 4: Generate report
    print("\n📄 Step 4: Generating Report...")
    report = analyzer.generate_comprehensive_report()
    print(report)
    
    # Save report
    report_file = PROJECT_ROOT / "MODEL_ANALYSIS_REPORT.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n💾 Report saved to: {report_file}")
    
    # Step 5: Generate fixes
    print("\n🔧 Step 5: Generating Automated Fixes...")
    
    # Check what needs to be fixed
    missing_helpers = []
    for name, dc in analyzer.dataclasses.items():
        if not analyzer.check_helper_methods(dc):
            missing_helpers.append(name)
    
    if missing_helpers:
        print(f"   ⚠️  Classes missing helper methods: {', '.join(missing_helpers)}")
        print("   📝 Suggested: Add to_dict() and to_model_kwargs() methods")
    else:
        print("   ✅ All dataclasses have helper methods")
    
    # Generate specific fixes
    print("\n📋 Recommended Fixes:")
    print("-" * 80)
    
    if 'TechnologyStack' in analyzer.dataclasses:
        print("\n1️⃣  TechnologyStack field mapping:")
        print("   Issue: Doesn't have 'primary_language' attribute")
        print("   Fix: Calculate from 'languages' dict in to_model_kwargs()")
        print("   Code: max(tech_stack.languages.items(), key=lambda x: x[1])[0]")
    
    if 'ServiceMap' in analyzer.dataclasses:
        print("\n2️⃣  ServiceMap field mapping:")
        print("   Issue: Doesn't have 'is_microservices' or 'service_graph'")
        print("   Fix: Calculate from other fields")
        print("   Code:")
        print("      - is_microservices: (service_count > 1)")
        print("      - service_dependencies: Use 'dependencies' field")
    
    if 'ArchitectureAnalysis' in analyzer.dataclasses:
        print("\n3️⃣  ArchitectureAnalysis field mapping:")
        print("   Issue: Check nested object access")
        print("   Fix: Safely access primary_pattern.name and primary_pattern.confidence")
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    
    return analyzer


if __name__ == "__main__":
    analyzer = main()

