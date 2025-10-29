"""
Check and install dependencies for Ground Station Core
This script checks what's installed and helps install missing packages
"""

import subprocess
import sys

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False

def install_package(package_name):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except:
        return False

def main():
    print("=" * 60)
    print("Ground Station Core - Dependency Checker")
    print("=" * 60)
    print()
    
    # Core dependencies
    core_deps = [
        ("requests", "requests"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
        ("skyfield", "skyfield"),
    ]
    
    # Optional but recommended
    optional_deps = [
        ("ttkbootstrap", "ttkbootstrap"),
        ("Pillow", "PIL"),
        ("influxdb-client", "influxdb_client"),
        ("pyyaml", "yaml"),
        ("python-dotenv", "dotenv"),
        ("pyserial", "serial"),
    ]
    
    # Check core dependencies
    print("Checking CORE dependencies (required for full functionality):")
    print("-" * 60)
    
    missing_core = []
    for package, import_name in core_deps:
        status = "✓ INSTALLED" if check_package(package, import_name) else "✗ MISSING"
        print(f"  {package:20s} {status}")
        if status == "✗ MISSING":
            missing_core.append(package)
    
    print()
    print("Checking OPTIONAL dependencies (enhances experience):")
    print("-" * 60)
    
    missing_optional = []
    for package, import_name in optional_deps:
        status = "✓ INSTALLED" if check_package(package, import_name) else "✗ MISSING"
        print(f"  {package:20s} {status}")
        if status == "✗ MISSING":
            missing_optional.append(package)
    
    print()
    print("=" * 60)
    
    # Summary
    if not missing_core and not missing_optional:
        print("✓ ALL DEPENDENCIES INSTALLED!")
        print("You're ready to use Ground Station Core.")
        return 0
    
    if missing_core:
        print(f"\n⚠ MISSING {len(missing_core)} CORE DEPENDENCIES")
        print("These are required for satellite tracking and other key features.")
        print("\nMissing core packages:")
        for pkg in missing_core:
            print(f"  - {pkg}")
        
        print("\nInstall command:")
        print(f"  pip install {' '.join(missing_core)}")
        print()
        
        response = input("Would you like to install core dependencies now? (y/n): ")
        if response.lower() == 'y':
            print("\nInstalling core dependencies...")
            for pkg in missing_core:
                print(f"Installing {pkg}...")
                if install_package(pkg):
                    print(f"  ✓ {pkg} installed successfully")
                else:
                    print(f"  ✗ Failed to install {pkg}")
    
    if missing_optional:
        print(f"\n📋 MISSING {len(missing_optional)} OPTIONAL DEPENDENCIES")
        print("The application will work, but with reduced functionality.")
        print("\nMissing optional packages:")
        for pkg in missing_optional:
            print(f"  - {pkg}")
        
        print("\nInstall command:")
        print(f"  pip install {' '.join(missing_optional)}")
        print()
        
        if not missing_core:  # Only ask if core deps are satisfied
            response = input("Would you like to install optional dependencies now? (y/n): ")
            if response.lower() == 'y':
                print("\nInstalling optional dependencies...")
                for pkg in missing_optional:
                    print(f"Installing {pkg}...")
                    if install_package(pkg):
                        print(f"  ✓ {pkg} installed successfully")
                    else:
                        print(f"  ✗ Failed to install {pkg}")
    
    print("\n" + "=" * 60)
    print("Dependency check complete!")
    print("\nNOTE: Some packages like SoapySDR require system-level installation.")
    print("See INSTALL.md for detailed installation instructions.")
    print("=" * 60)
    
    return 1 if missing_core else 0

if __name__ == "__main__":
    sys.exit(main())
