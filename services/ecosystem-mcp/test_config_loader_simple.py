"""
Simple test for config loader (no app imports).
"""

import sys
from pathlib import Path

# Direct import of the module file
config_loader_path = Path(__file__).parent / "src" / "services" / "rag" / "config_loader.py"

# Load as module
import importlib.util
spec = importlib.util.spec_from_file_location("config_loader", config_loader_path)
config_loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_loader)

# Now use the module
OptionalConfigLoader = config_loader.OptionalConfigLoader
GlossaryTerm = config_loader.GlossaryTerm
ExclusionRule = config_loader.ExclusionRule
RAGConfig = config_loader.RAGConfig

print("\n🧪 Testing Config Loader (Isolated)\n")
print("=" * 60)
print("TEST 1: Graceful Degradation")
print("=" * 60)

loader = OptionalConfigLoader(Path("/tmp/nonexistent"))
config = loader.load_config()

if config is None:
    print("✅ PASS: Returns None when no config exists")
else:
    print("❌ FAIL: Should return None")
    sys.exit(1)

print()
print("=" * 60)
print("TEST 2: Pydantic Models")
print("=" * 60)

# Test GlossaryTerm
term = GlossaryTerm(
    term="MCP",
    description="Model Context Protocol",
    synonyms=["protocol"],
    boost_weight=1.5
)
print(f"✅ PASS: GlossaryTerm created: {term.term}")

# Test ExclusionRule
rule = ExclusionRule(
    pattern=r"\.log$",
    reason="Log files"
)
print(f"✅ PASS: ExclusionRule created: {rule.pattern}")

# Test RAGConfig
config_obj = RAGConfig(
    features_enabled={'glossary': True},
    glossary={'MCP': term},
    exclusions=[rule]
)
print(f"✅ PASS: RAGConfig created with {len(config_obj.glossary)} terms")

# Test weight validation
print()
print("Testing weight validation...")
try:
    bad_config = RAGConfig(
        signal_weights={
            'semantic': 0.5,
            'glossary': 0.6  # Sum > 1.0
        }
    )
    print("❌ FAIL: Should reject invalid weights")
    sys.exit(1)
except ValueError as e:
    print(f"✅ PASS: Rejected invalid weights: {str(e)[:50]}...")

print()
print("=" * 60)
print("TEST 3: Feature Check")
print("=" * 60)

enabled = loader.is_feature_enabled('glossary')
if enabled is False:
    print("✅ PASS: Feature check returns False when no config")
else:
    print("❌ FAIL: Should be False")
    sys.exit(1)

print()
print("=" * 60)
print("✅ ALL TESTS PASSED")
print("=" * 60)
print()
print("📦 Config Loader Status:")
print("   • File created: config_loader.py")
print("   • Graceful degradation: ✅ VERIFIED")
print("   • Pydantic validation: ✅ VERIFIED")
print("   • Smart caching: ✅ IMPLEMENTED")
print("   • Feature checking: ✅ VERIFIED")
print()
print("🎯 Step 1.1 COMPLETE")
print()

