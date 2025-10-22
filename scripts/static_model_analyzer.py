"""
Static Model Analyzer - No imports required

Analyzes Python files statically to find all model/dataclass mismatches
and generates comprehensive fixes.
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class FieldInfo:
    name: str
    type_hint: str
    is_optional: bool = False
    default_value: str = None


@dataclass
class ClassInfo:
    name: str
    file_path: Path
    is_dataclass: bool = False
    is_sqlalchemy: bool = False
    fields: List[FieldInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)


class StaticAnalyzer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.classes: Dict[str, ClassInfo] = {}
        self.issues: List[Dict] = []
    
    def analyze_file(self, file_path: Path) -> List[ClassInfo]:
        """Parse a Python file and extract class information."""
        classes = []
        
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = self._extract_class_info(node, file_path)
                    if class_info:
                        classes.append(class_info)
        
        except Exception as e:
            print(f"⚠️  Error parsing {file_path}: {e}")
        
        return classes
    
    def _extract_class_info(self, node: ast.ClassDef, file_path: Path) -> ClassInfo:
        """Extract information from a class definition."""
        class_info = ClassInfo(name=node.name, file_path=file_path)
        
        # Check decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == 'dataclass':
                class_info.is_dataclass = True
        
        # Check if inherits from Base (SQLAlchemy)
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == 'Base':
                class_info.is_sqlalchemy = True
        
        # Extract fields from annotations
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_name = item.target.id
                try:
                    type_hint = ast.unparse(item.annotation) if hasattr(ast, 'unparse') else self._ast_to_str(item.annotation)
                except:
                    type_hint = "Unknown"
                
                is_optional = 'Optional' in type_hint or 'None' in type_hint
                default_val = None
                if item.value:
                    try:
                        default_val = ast.unparse(item.value) if hasattr(ast, 'unparse') else self._ast_to_str(item.value)
                    except:
                        default_val = "..."
                
                class_info.fields.append(FieldInfo(
                    name=field_name,
                    type_hint=type_hint,
                    is_optional=is_optional,
                    default_value=default_val
                ))
            
            # Extract methods
            elif isinstance(item, ast.FunctionDef):
                class_info.methods.append(item.name)
            
            # Look for SQLAlchemy relationships
            elif isinstance(item, ast.Assign):
                if isinstance(item.value, ast.Call):
                    if isinstance(item.value.func, ast.Name) and item.value.func.id == 'relationship':
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                class_info.relationships.append(target.id)
        
        return class_info
    
    def _ast_to_str(self, node):
        """Convert AST node to string (fallback for older Python)."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._ast_to_str(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._ast_to_str(node.value)}[...]"
        return "Unknown"
    
    def find_mapping_issues(self):
        """Find all model mapping issues."""
        print("\n🔍 Analyzing Model Mappings...\n")
        
        # Get specific classes
        analysis_report = self.classes.get('AnalysisReport')
        analysis_result_model = self.classes.get('AnalysisResultModel')
        tech_stack = self.classes.get('TechnologyStack')
        service_map = self.classes.get('ServiceMap')
        arch_analysis = self.classes.get('ArchitectureAnalysis')
        processing_plan = self.classes.get('ProcessingPlanModel')
        
        # Issue 1: AnalysisReport -> AnalysisResultModel mapping
        if analysis_report and analysis_result_model:
            print("📊 Checking: AnalysisReport -> AnalysisResultModel")
            self._check_mapping(analysis_report, analysis_result_model, 
                              "AnalysisReport", "AnalysisResultModel")
        
        # Issue 2: TechnologyStack fields
        if tech_stack:
            print("📊 Checking: TechnologyStack fields")
            tech_fields = {f.name for f in tech_stack.fields}
            if 'primary_language' not in tech_fields:
                self.issues.append({
                    'class': 'TechnologyStack',
                    'issue': 'Missing primary_language field',
                    'fix': 'Calculate from languages dict: max(tech_stack.languages.items(), key=lambda x: x[1])[0]',
                    'location': 'to_model_kwargs() method'
                })
        
        # Issue 3: ServiceMap fields
        if service_map:
            print("📊 Checking: ServiceMap fields")
            svc_fields = {f.name for f in service_map.fields}
            if 'is_microservices' not in svc_fields:
                self.issues.append({
                    'class': 'ServiceMap',
                    'issue': 'Missing is_microservices field',
                    'fix': 'Calculate from service_count: (svc_map.service_count > 1)',
                    'location': 'to_model_kwargs() method'
                })
            if 'service_graph' not in svc_fields and 'dependencies' in svc_fields:
                self.issues.append({
                    'class': 'ServiceMap',
                    'issue': 'Field name mismatch: service_graph vs dependencies',
                    'fix': 'Use svc_map.dependencies instead of svc_map.service_graph',
                    'location': 'to_model_kwargs() method'
                })
        
        # Issue 4: ProcessingPlanModel relationships
        if processing_plan:
            print("📊 Checking: ProcessingPlanModel relationships")
            if 'files' not in processing_plan.relationships and 'file_classifications' in processing_plan.relationships:
                self.issues.append({
                    'class': 'ProcessingPlanModel',
                    'issue': 'No direct files attribute, use file_classifications relationship',
                    'fix': 'Access via plan.file_classifications instead of plan.files',
                    'location': 'Query with selectinload(ProcessingPlanModel.file_classifications)'
                })
    
    def _check_mapping(self, source: ClassInfo, target: ClassInfo, source_name: str, target_name: str):
        """Check mapping between two classes."""
        source_fields = {f.name for f in source.fields}
        target_fields = {f.name for f in target.fields}
        
        # Check for missing helper methods in source
        if 'to_model_kwargs' not in source.methods:
            self.issues.append({
                'class': source_name,
                'issue': 'Missing to_model_kwargs() helper method',
                'fix': 'Add method to convert dataclass fields to model constructor kwargs',
                'location': f'{source.file_path.name}'
            })
        
        # Check for field mismatches
        for field in source_fields:
            if field not in target_fields:
                # This might be a calculated field
                self.issues.append({
                    'class': f'{source_name} -> {target_name}',
                    'issue': f'Field "{field}" in source not in target',
                    'fix': f'May need to calculate or map differently',
                    'location': 'to_model_kwargs() method'
                })
    
    def generate_fix_code(self) -> str:
        """Generate Python code to fix all issues."""
        fixes = []
        
        fixes.append("# AUTO-GENERATED FIXES FOR MODEL MAPPING ISSUES")
        fixes.append("# " + "=" * 70)
        fixes.append("")
        
        for i, issue in enumerate(self.issues, 1):
            fixes.append(f"# Fix #{i}: {issue['class']}")
            fixes.append(f"# Issue: {issue['issue']}")
            fixes.append(f"# Location: {issue['location']}")
            fixes.append(f"# Suggested Fix: {issue['fix']}")
            fixes.append("")
        
        return "\n".join(fixes)


def main():
    print("=" * 80)
    print("🔍 STATIC MODEL ANALYZER")
    print("=" * 80)
    
    project_root = Path(__file__).parent.parent
    analyzer = StaticAnalyzer(project_root)
    
    # Files to analyze
    files_to_analyze = [
        # Storage models
        project_root / "services/ecosystem-mcp/src/storage/models_analysis.py",
        project_root / "services/ecosystem-mcp/src/storage/models_discovery.py",
        
        # Analysis dataclasses
        project_root / "services/ecosystem-mcp/src/services/analysis/analysis_engine.py",
        project_root / "services/ecosystem-mcp/src/services/analysis/stack_detector.py",
        project_root / "services/ecosystem-mcp/src/services/analysis/service_detector.py",
        project_root / "services/ecosystem-mcp/src/services/analysis/architecture_detector.py",
        project_root / "services/ecosystem-mcp/src/services/analysis/dependency_analyzer.py",
    ]
    
    print("\n📂 Analyzing Files...")
    for file_path in files_to_analyze:
        if file_path.exists():
            print(f"   • {file_path.name}")
            classes = analyzer.analyze_file(file_path)
            for cls in classes:
                analyzer.classes[cls.name] = cls
        else:
            print(f"   ⚠️  Not found: {file_path.name}")
    
    print(f"\n✅ Found {len(analyzer.classes)} classes")
    
    # Display all classes
    print("\n" + "=" * 80)
    print("📊 DISCOVERED CLASSES")
    print("=" * 80)
    
    for name, cls in sorted(analyzer.classes.items()):
        icon = "📦" if cls.is_dataclass else "🗄️ " if cls.is_sqlalchemy else "📄"
        type_str = "Dataclass" if cls.is_dataclass else "SQLAlchemy Model" if cls.is_sqlalchemy else "Class"
        print(f"\n{icon} {name} ({type_str})")
        print(f"   File: {cls.file_path.name}")
        print(f"   Fields: {len(cls.fields)}")
        for field in cls.fields[:5]:  # Show first 5 fields
            opt = " (optional)" if field.is_optional else ""
            print(f"      • {field.name}: {field.type_hint}{opt}")
        if len(cls.fields) > 5:
            print(f"      ... and {len(cls.fields) - 5} more")
        
        if cls.methods:
            key_methods = [m for m in cls.methods if m in ['to_dict', 'to_model_kwargs', '__init__']]
            if key_methods:
                print(f"   Key Methods: {', '.join(key_methods)}")
        
        if cls.relationships:
            print(f"   Relationships: {', '.join(cls.relationships)}")
    
    # Find issues
    analyzer.find_mapping_issues()
    
    # Display issues
    print("\n" + "=" * 80)
    print("⚠️  ISSUES FOUND")
    print("=" * 80)
    
    if analyzer.issues:
        for i, issue in enumerate(analyzer.issues, 1):
            print(f"\n{i}. {issue['class']}")
            print(f"   Issue: {issue['issue']}")
            print(f"   Fix: {issue['fix']}")
            print(f"   Location: {issue['location']}")
    else:
        print("\n✅ No issues found!")
    
    # Generate fixes
    fix_code = analyzer.generate_fix_code()
    fix_file = project_root / "MODEL_MAPPING_FIXES.txt"
    with open(fix_file, 'w') as f:
        f.write(fix_code)
    
    print(f"\n💾 Fixes saved to: {fix_file}")
    
    # Generate summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Classes analyzed: {len(analyzer.classes)}")
    print(f"SQLAlchemy models: {sum(1 for c in analyzer.classes.values() if c.is_sqlalchemy)}")
    print(f"Dataclasses: {sum(1 for c in analyzer.classes.values() if c.is_dataclass)}")
    print(f"Issues found: {len(analyzer.issues)}")
    
    return analyzer


if __name__ == "__main__":
    analyzer = main()

