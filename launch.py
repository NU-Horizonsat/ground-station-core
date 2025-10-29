"""
Ground Station Core - Simple Launcher
Automatically checks dependencies and launches the UI
"""

import sys
import os

def check_and_launch():
    """Check dependencies and launch UI"""
    print("Ground Station Core v2.0 Launcher")
    print("=" * 50)
    print()
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required")
        print(f"You are running Python {sys.version}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Try importing the new UI
    try:
        print("\nLaunching Ground Station Core UI...")
        print("-" * 50)
        print()
        
        # Import and run the new UI
        import ui_v2
        ui_v2.main()
        
    except ImportError as e:
        print(f"\n✗ Import Error: {e}")
        print("\nSome required packages are missing.")
        print("\nRunning dependency checker...")
        print("=" * 50)
        print()
        
        try:
            import check_dependencies
            check_dependencies.main()
        except:
            print("\nQuick install command:")
            print("  pip install skyfield matplotlib numpy requests pyyaml python-dotenv")
        
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n✗ Error launching UI: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    check_and_launch()
