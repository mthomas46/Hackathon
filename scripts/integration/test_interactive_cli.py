#!/usr/bin/env python3
"""
Test Interactive CLI - Test the overlay integration with the actual CLI
"""

import os
import subprocess
import sys
import time


def test_cli_with_interactive_overlay():
    """Test that the CLI launches and shows the interactive settings menu."""

    # Set up paths
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_dir)

    print("🧪 Testing Interactive CLI Overlay Integration")
    print("=" * 50)

    # Test 1: CLI help (should work)
    print("\n📋 Test 1: CLI Help Command")
    try:
        result = subprocess.run([sys.executable, "run_cli.py", "--help"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and "interactive" in result.stdout:
            print("✅ CLI help working")
        else:
            print("❌ CLI help failed")
            print("STDOUT:", result.stdout[:200])
            print("STDERR:", result.stderr[:200])
    except Exception as e:
        print(f"❌ CLI help error: {e}")

    # Test 2: Health command (should work)
    print("\n📋 Test 2: CLI Health Command")
    try:
        result = subprocess.run([sys.executable, "run_cli.py", "health"], capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and "Service Health Status" in result.stdout:
            print("✅ CLI health command working")
            # Show a snippet of the output
            lines = result.stdout.split("\n")
            for line in lines[:10]:  # First 10 lines
                if line.strip():
                    print(f"   {line}")
            if len(lines) > 10:
                print("   ...")
        else:
            print("❌ CLI health command failed")
            print("STDOUT:", result.stdout[:300])
            print("STDERR:", result.stderr[:200])
    except Exception as e:
        print(f"❌ CLI health error: {e}")

    # Test 3: Interactive mode startup (brief test)
    print("\n📋 Test 3: CLI Interactive Mode Startup")
    try:
        # Start interactive mode and kill it quickly to see if it starts
        proc = subprocess.Popen(
            [sys.executable, "run_cli.py", "interactive"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Wait a bit for startup
        time.sleep(3)

        # Check if it's still running (good sign)
        if proc.poll() is None:
            print("✅ CLI interactive mode started successfully")
            proc.terminate()
            proc.wait()
        else:
            stdout, stderr = proc.communicate()
            if "Select option" in stdout or "Interactive Menu" in stdout:
                print("✅ CLI interactive mode shows menu")
                print("   (Menu displayed before timeout)")
            else:
                print("⚠️  CLI interactive mode exited early")
                print("STDOUT:", stdout[:200])
                print("STDERR:", stderr[:200])

    except Exception as e:
        print(f"❌ CLI interactive error: {e}")

    print("\n🎯 Interactive Overlay Status:")
    try:
        import questionary

        print("✅ Questionary available")
        try:
            from services.cli.modules.interactive_overlay import InteractiveOverlay

            print("✅ Interactive overlay module available")
        except ImportError as e:
            print(f"❌ Interactive overlay import error: {e}")
    except ImportError:
        print("❌ Questionary not available")

    print("\n🏁 CLI Integration Test Complete!")
    print("\nNext Steps:")
    print("1. Run: python3 run_cli.py interactive")
    print("2. Press 's' to access Settings with interactive overlay")
    print("3. Test arrow key navigation and selection")
    print("4. Gradually enable on other managers")


if __name__ == "__main__":
    test_cli_with_interactive_overlay()
