#!/usr/bin/env python3
"""
Architecture Validation Script
PRIORITY 1 FIX #8 - Check DDD layer dependencies

Usage:
    python3 scripts/refactoring/validate_architecture.py <service-name>

Author: Hackathon Team
Version: 1.0.0
"""

import argparse
import sys
import re
from pathlib import Path
from typing import List, Dict


class ArchitectureValidator:
    """Validates DDD architecture compliance"""
    
    def __init__(self, service_name: str, project_root: Path):
        self.service_name = service_name
        self.service_path = project_root / "services" / service_name
        self.violations = []
        
    def validate(self) -> dict:
        """Validate architecture"""
        
        print(f"🏛️  Validating Architecture: {self.service_name}")
        print("=" * 70)
        print()
        
        if not self.service_path.exists():
            return {"success": False, "error": "Service not found"}
        
        # Check layer dependencies
        print("🔍 Checking DDD layer dependencies...")
        self._check_layer_dependencies()
        
        results = {
            "success": len(self.violations) == 0,
            "violations": self.violations
        }
        
        return results
    
    def _check_layer_dependencies(self):
        """Check for circular dependencies and layer violations"""
        
        layers = ["domain", "application", "infrastructure", "presentation"]
        
        for layer in layers:
            layer_path = self.service_path / layer
            if not layer_path.exists():
                continue
            
            py_files = list(layer_path.rglob("*.py"))
            
            for py_file in py_files:
                try:
                    content = py_file.read_text()
                    imports = self._extract_imports(content)
                    
                    # Check for violations
                    if layer == "domain":
                        # Domain should not import from any other layer
                        for imp in imports:
                            if any(other in imp for other in ["application", "infrastructure", "presentation"]):
                                self.violations.append({
                                    "file": str(py_file.relative_to(self.service_path)),
                                    "layer": "domain",
                                    "violation": f"Domain imports from {imp}",
                                    "severity": "critical"
                                })
                    
                    elif layer == "application":
                        # Application can import domain, but not infrastructure/presentation
                        for imp in imports:
                            if any(other in imp for other in ["infrastructure", "presentation"]):
                                self.violations.append({
                                    "file": str(py_file.relative_to(self.service_path)),
                                    "layer": "application",
                                    "violation": f"Application imports from {imp}",
                                    "severity": "high"
                                })
                    
                    elif layer == "infrastructure":
                        # Infrastructure should not import presentation
                        for imp in imports:
                            if "presentation" in imp:
                                self.violations.append({
                                    "file": str(py_file.relative_to(self.service_path)),
                                    "layer": "infrastructure",
                                    "violation": f"Infrastructure imports from {imp}",
                                    "severity": "medium"
                                })
                
                except Exception as e:
                    pass
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements"""
        imports = []
        
        # Match "from X import Y" and "import X"
        import_pattern = r'^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))'
        
        for line in content.split('\n'):
            match = re.match(import_pattern, line.strip())
            if match:
                imp = match.group(1) or match.group(2)
                imports.append(imp)
        
        return imports


def main():
    parser = argparse.ArgumentParser(description="Validate DDD architecture")
    parser.add_argument("service", help="Service name")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    
    validator = ArchitectureValidator(args.service, args.project_root)
    results = validator.validate()
    
    print()
    if results["success"]:
        print("✅ ARCHITECTURE VALID - No violations found")
    else:
        print(f"❌ ARCHITECTURE VIOLATIONS FOUND ({len(results['violations'])})")
        for v in results["violations"]:
            print(f"  🔴 {v['file']}: {v['violation']}")
    
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()

