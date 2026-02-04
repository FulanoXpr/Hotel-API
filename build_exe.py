#!/usr/bin/env python3
"""
Build script for Hotel Price Checker.

Verifies and installs dependencies, then builds the .exe file.

Usage:
    python build_exe.py              # Check dependencies and build
    python build_exe.py --check      # Only check dependencies (no build)
    python build_exe.py --install    # Install missing dependencies only
    python build_exe.py --installer  # Build + create Windows installer (requires Inno Setup)
"""

import subprocess
import sys
import shutil
from pathlib import Path

# Required packages for building
BUILD_DEPENDENCIES = [
    "pyinstaller",
]

# Required packages for the application
APP_DEPENDENCIES = [
    "customtkinter",
    "requests",
    "openpyxl",
    "python-dotenv",
    "packaging",
    "Pillow",
]

# Optional cascade dependencies (app works without them)
OPTIONAL_DEPENDENCIES = [
    "google-search-results",  # SerpApi
    "apify-client",           # Apify
    "amadeus",                # Amadeus GDS
]


def check_python_version():
    """Verify Python version is 3.9+."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"[ERROR] Python 3.9+ required. Found: {version.major}.{version.minor}")
        return False
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    # Map package names to import names
    import_map = {
        "python-dotenv": "dotenv",
        "google-search-results": "serpapi",
        "apify-client": "apify_client",
        "Pillow": "PIL",
        "pyinstaller": "PyInstaller",
    }
    import_name = import_map.get(package_name, package_name.replace("-", "_"))

    try:
        __import__(import_name)
        return True
    except ImportError:
        return False


def install_package(package_name: str) -> bool:
    """Install a package using pip."""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def check_dependencies(install_missing: bool = False) -> dict:
    """Check all dependencies and optionally install missing ones."""
    results = {
        "build": {},
        "app": {},
        "optional": {},
    }

    print("\n=== Checking Build Dependencies ===")
    for pkg in BUILD_DEPENDENCIES:
        installed = check_package_installed(pkg)
        if installed:
            print(f"  [OK] {pkg}")
        elif install_missing:
            print(f"  [INSTALLING] {pkg}...", end=" ")
            if install_package(pkg):
                print("OK")
                installed = True
            else:
                print("FAILED")
        else:
            print(f"  [MISSING] {pkg}")
        results["build"][pkg] = installed

    print("\n=== Checking App Dependencies ===")
    for pkg in APP_DEPENDENCIES:
        installed = check_package_installed(pkg)
        if installed:
            print(f"  [OK] {pkg}")
        elif install_missing:
            print(f"  [INSTALLING] {pkg}...", end=" ")
            if install_package(pkg):
                print("OK")
                installed = True
            else:
                print("FAILED")
        else:
            print(f"  [MISSING] {pkg}")
        results["app"][pkg] = installed

    print("\n=== Checking Optional Dependencies (Cascade Pipeline) ===")
    for pkg in OPTIONAL_DEPENDENCIES:
        installed = check_package_installed(pkg)
        if installed:
            print(f"  [OK] {pkg}")
        elif install_missing:
            print(f"  [INSTALLING] {pkg}...", end=" ")
            if install_package(pkg):
                print("OK")
                installed = True
            else:
                print("FAILED")
        else:
            print(f"  [OPTIONAL] {pkg} - not installed")
        results["optional"][pkg] = installed

    return results


def check_required_files() -> bool:
    """Verify required files exist for building."""
    print("\n=== Checking Required Files ===")

    required_files = [
        "hotel_price_app.py",
        "hotel_app.spec",
        "ui/assets/fpr_logo.png",
        ".env.example",
    ]

    base_path = Path(__file__).parent
    all_exist = True

    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"  [OK] {file_path}")
        else:
            print(f"  [MISSING] {file_path}")
            all_exist = False

    return all_exist


def build_exe() -> bool:
    """Build the .exe using PyInstaller."""
    print("\n=== Building Executable ===")

    base_path = Path(__file__).parent
    spec_file = base_path / "hotel_app.spec"

    try:
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", str(spec_file), "--clean", "--noconfirm"],
            cwd=str(base_path),
            capture_output=False,
        )

        if result.returncode == 0:
            dist_path = base_path / "dist" / "HotelPriceChecker"
            exe_path = dist_path / "HotelPriceChecker.exe"

            if exe_path.exists():
                # Calculate folder size
                total_size = sum(f.stat().st_size for f in dist_path.rglob("*") if f.is_file())
                size_mb = total_size / (1024 * 1024)

                print(f"\n[SUCCESS] Build completed!")
                print(f"  Executable: {exe_path}")
                print(f"  Folder size: {size_mb:.1f} MB")
                return True

        print("\n[ERROR] Build failed")
        return False

    except Exception as e:
        print(f"\n[ERROR] Build error: {e}")
        return False


def create_zip_distribution():
    """Create a ZIP file for distribution."""
    print("\n=== Creating ZIP Distribution ===")

    base_path = Path(__file__).parent
    dist_path = base_path / "dist" / "HotelPriceChecker"

    if not dist_path.exists():
        print("  [ERROR] dist/HotelPriceChecker not found")
        return False

    zip_path = base_path / "dist" / "HotelPriceChecker-Windows"

    try:
        shutil.make_archive(str(zip_path), "zip", str(dist_path.parent), "HotelPriceChecker")
        print(f"  [OK] Created: {zip_path}.zip")
        return True
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False


def create_icon():
    """Create Windows .ico file from PNG logo."""
    print("\n=== Creating Application Icon ===")

    base_path = Path(__file__).parent
    png_path = base_path / "ui" / "assets" / "fpr_logo.png"
    ico_path = base_path / "ui" / "assets" / "icon.ico"

    if ico_path.exists():
        print(f"  [OK] Icon already exists: {ico_path}")
        return True

    if not png_path.exists():
        print(f"  [SKIP] Logo not found: {png_path}")
        return False

    try:
        from PIL import Image

        img = Image.open(png_path)
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        sizes = [16, 24, 32, 48, 64, 128, 256]
        icons = [img.resize((s, s), Image.Resampling.LANCZOS) for s in sizes]

        icons[0].save(
            ico_path,
            format="ICO",
            sizes=[(s, s) for s in sizes],
            append_images=icons[1:],
        )
        print(f"  [OK] Created: {ico_path}")
        return True
    except ImportError:
        print("  [SKIP] Pillow not installed, skipping icon creation")
        return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False


def find_inno_setup():
    """Find Inno Setup compiler (iscc.exe)."""
    import os

    # Common installation paths
    possible_paths = [
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 5\ISCC.exe"),
    ]

    # Also check user-specific installation (winget installs here)
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        possible_paths.insert(0, Path(local_app_data) / "Programs" / "Inno Setup 6" / "ISCC.exe")

    for path in possible_paths:
        if path.exists():
            return path

    # Try to find in PATH
    iscc = shutil.which("iscc")
    if iscc:
        return Path(iscc)

    return None


def create_installer():
    """Create Windows installer using Inno Setup."""
    print("\n=== Creating Windows Installer ===")

    base_path = Path(__file__).parent
    iss_file = base_path / "installer.iss"
    dist_path = base_path / "dist" / "HotelPriceChecker"

    if not iss_file.exists():
        print(f"  [ERROR] Inno Setup script not found: {iss_file}")
        return False

    if not dist_path.exists():
        print("  [ERROR] dist/HotelPriceChecker not found. Run build first.")
        return False

    iscc = find_inno_setup()
    if not iscc:
        print("  [ERROR] Inno Setup not found.")
        print("  Download from: https://jrsoftware.org/isdl.php")
        print("  Or install via: winget install JRSoftware.InnoSetup")
        return False

    print(f"  Using: {iscc}")

    try:
        result = subprocess.run(
            [str(iscc), str(iss_file)],
            cwd=str(base_path),
            capture_output=False,
        )

        if result.returncode == 0:
            installer_path = base_path / "dist" / "HotelPriceChecker-Setup.exe"
            if installer_path.exists():
                size_mb = installer_path.stat().st_size / (1024 * 1024)
                print(f"\n  [OK] Created: {installer_path}")
                print(f"  Size: {size_mb:.1f} MB")
                return True

        print("\n  [ERROR] Installer creation failed")
        return False

    except Exception as e:
        print(f"\n  [ERROR] {e}")
        return False


def main():
    """Main entry point."""
    print("=" * 50)
    print("  Hotel Price Checker - Build Script")
    print("=" * 50)

    # Parse arguments
    check_only = "--check" in sys.argv
    install_only = "--install" in sys.argv
    create_installer_flag = "--installer" in sys.argv

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Check/install dependencies
    install_missing = install_only or (not check_only)
    results = check_dependencies(install_missing=install_missing)

    # Verify all required dependencies are installed
    build_ready = all(results["build"].values())
    app_ready = all(results["app"].values())

    if not build_ready or not app_ready:
        missing = []
        for pkg, installed in results["build"].items():
            if not installed:
                missing.append(pkg)
        for pkg, installed in results["app"].items():
            if not installed:
                missing.append(pkg)

        print(f"\n[ERROR] Missing required packages: {', '.join(missing)}")
        print("Run: python build_exe.py --install")
        sys.exit(1)

    if check_only or install_only:
        print("\n[INFO] Dependency check complete")
        sys.exit(0)

    # Check required files
    if not check_required_files():
        print("\n[ERROR] Missing required files")
        sys.exit(1)

    # Create icon if possible
    create_icon()

    # Build
    if not build_exe():
        sys.exit(1)

    # Create ZIP
    create_zip_distribution()

    # Create installer if requested
    if create_installer_flag:
        if not create_installer():
            print("\n[WARNING] Installer creation failed, but ZIP is available")

    print("\n" + "=" * 50)
    print("  Build Complete!")
    print("=" * 50)
    print("\nTo run the application:")
    print("  dist\\HotelPriceChecker\\HotelPriceChecker.exe")
    if create_installer_flag:
        print("\nInstaller:")
        print("  dist\\HotelPriceChecker-Setup.exe")


if __name__ == "__main__":
    main()
