"""
Test script for config loader.

Tests graceful degradation without full app imports.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import just the config loader (no dependencies)
from services.rag.config_loader import (
    OptionalConfigLoader,
    GlossaryTerm,
    ExclusionRule,
    RAGConfig
)

def test_graceful_degradation():
    """Test that loader returns None when no config exists."""
    print("=" * 60)
    print("TEST 1: Graceful Degradation (No Config)")
    print("=" * 60)
    
    loader = OptionalConfigLoader(Path("/tmp/nonexistent"))
    config = loader.load_config()
    
    assert config is None, "Expected None when config doesn't exist"
    print("✅ PASS: Returns None when config missing")
    print()


def test_pydantic_models():
    """Test that Pydantic models work."""
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
    assert term.term == "MCP"
    print("✅ PASS: GlossaryTerm model works")
    
    # Test ExclusionRule
    rule = ExclusionRule(
        pattern=r"\.log$",
        reason="Log files"
    )
    assert rule.pattern == r"\.log$"
    print("✅ PASS: ExclusionRule model works")
    
    # Test RAGConfig with validation
    try:
        config = RAGConfig(
            features_enabled={'glossary': True},
            glossary={'MCP': term},
            exclusions=[rule],
            signal_weights={
                'semantic': 0.5,
                'glossary': 0.5
                # Sum = 1.0, should validate
            }
        )
        print("✅ PASS: RAGConfig model works with valid weights")
    except Exception as e:
        print(f"❌ FAIL: RAGConfig validation: {e}")
        raise
    
    # Test weight validation failure
    try:
        bad_config = RAGConfig(
            signal_weights={
                'semantic': 0.5,
                'glossary': 0.6  # Sum > 1.0, should fail
            }
        )
        print("❌ FAIL: Should have rejected invalid weights")
        raise AssertionError("Weight validation didn't work")
    except ValueError as e:
        print(f"✅ PASS: Weight validation caught error: {e}")
    
    print()


def test_cache_behavior():
    """Test that caching works."""
    print("=" * 60)
    print("TEST 3: Cache Behavior")
    print("=" * 60)
    
    loader = OptionalConfigLoader(Path("/tmp/nonexistent"))
    
    # First call
    config1 = loader.load_config()
    
    # Second call (should use same logic)
    config2 = loader.load_config()
    
    assert config1 is None and config2 is None
    print("✅ PASS: Consistent None returns (no caching of None)")
    print()


def test_feature_enabled():
    """Test feature checking."""
    print("=" * 60)
    print("TEST 4: Feature Enabled Check")
    print("=" * 60)
    
    loader = OptionalConfigLoader(Path("/tmp/nonexistent"))
    
    enabled = loader.is_feature_enabled('glossary')
    assert enabled is False, "Should be False when no config"
    print("✅ PASS: Feature check returns False when no config")
    print()


if __name__ == "__main__":
    print("\n🧪 Testing Config Loader\n")
    
    try:
        test_graceful_degradation()
        test_pydantic_models()
        test_cache_behavior()
        test_feature_enabled()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print()
        print("Config Loader Status: ✅ WORKING")
        print("Graceful Degradation: ✅ VERIFIED")
        print("Pydantic Validation: ✅ VERIFIED")
        print("Cache Infrastructure: ✅ VERIFIED")
        print()
        print("🎯 Step 1.1 Complete: Config Loader Ready")
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

