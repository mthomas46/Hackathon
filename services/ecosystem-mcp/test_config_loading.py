"""
Test that config loader can read the example config files.
"""

import sys
from pathlib import Path
import importlib.util

print("\n" + "=" * 70)
print("🧪 CONFIG LOADING TEST")
print("=" * 70 + "\n")

# Load config_loader module
config_loader_path = Path(__file__).parent / "src" / "services" / "rag" / "config_loader.py"
spec = importlib.util.spec_from_file_location("config_loader", config_loader_path)
config_loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_loader)

# Set config directory to repo root (go up 2 levels from test file)
repo_root = Path(__file__).parent.parent.parent
loader = config_loader.OptionalConfigLoader(repo_root)

print(f"Looking for config in: {repo_root / '.rag-config'}")
print()

# Try to load config
config = loader.load_config()

if config is None:
    print("❌ Config not loaded!")
    print("   Check that .rag-config/ directory exists in repo root")
    sys.exit(1)

print("✅ Config loaded successfully!")
print()

# Verify structure
print("📊 Config Structure:")
print(f"  Features enabled: {list(config.features_enabled.keys())}")
print(f"  Glossary terms: {len(config.glossary)}")
print(f"  Exclusion rules: {len(config.exclusions)}")
print(f"  Signal weights sum: {sum(config.signal_weights.values()):.2f}")
print()

# Check glossary
print("📚 Glossary Terms:")
for term_name, term in list(config.glossary.items())[:3]:
    print(f"  • {term_name}: {term.description[:50]}...")
    if len(config.glossary) > 3:
        remaining = len(config.glossary) - 3
        print(f"  ... and {remaining} more")
        break
print()

# Check exclusions
print("🚫 Exclusion Rules:")
for rule in list(config.exclusions)[:3]:
    print(f"  • {rule.pattern}: {rule.reason}")
if len(config.exclusions) > 3:
    remaining = len(config.exclusions) - 3
    print(f"  ... and {remaining} more")
print()

# Check signal weights
print("⚖️  Signal Weights:")
for signal, weight in config.signal_weights.items():
    bar = "█" * int(weight * 40)
    print(f"  {signal:20} {weight:.2f} {bar}")
print()

# Verify weights sum to 1.0
weight_sum = sum(config.signal_weights.values())
if 0.95 <= weight_sum <= 1.05:
    print(f"✅ Weights sum to {weight_sum:.2f} (valid)")
else:
    print(f"❌ Weights sum to {weight_sum:.2f} (should be 1.0)")
    sys.exit(1)

print()
print("=" * 70)
print("✅ CONFIG FILES WORKING!")
print("=" * 70)
print()
print("📦 Config Summary:")
print(f"  • Features: {sum(config.features_enabled.values())} enabled")
print(f"  • Glossary: {len(config.glossary)} terms")
print(f"  • Exclusions: {len(config.exclusions)} rules")
print(f"  • Templates: {len(config.templates)} (Phase 3)")
print()
print("🎯 Ready for use with: {\"use_enhancements\": true}")
print()

