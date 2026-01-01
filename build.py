"""
Hit & Run Panda - Cross-Platform Build Script
Creates standalone executables for Windows and macOS.
"""

import sys
import os
import platform
import shutil
import subprocess
from pathlib import Path

IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"

APP_NAME = "HitAndRunPanda"
VERSION = "1.0.0"


def main():
    print("=" * 50)
    print(f"Hit & Run Panda - Build Script")
    print(f"Platform: {platform.system()}")
    print("=" * 50)
    
    # Install requirements
    print("\n1. Installing requirements...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pyinstaller", "pyqt6"])
    
    # Clean old builds
    print("\n2. Cleaning old builds...")
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder, ignore_errors=True)
    
    # Build
    print("\n3. Building executable...")
    
    if IS_MAC:
        build_mac()
    else:
        build_windows()
    
    print("\n" + "=" * 50)
    print("BUILD COMPLETE!")
    print("=" * 50)


def build_mac():
    """Build macOS .app bundle."""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--windowed",  # .app bundle
        "--onefile",
        "--add-data", "assets:assets",
        "--hidden-import", "PyQt6.QtNetwork",
        "main.py"
    ]
    
    # Add icon if exists
    icon_path = Path("assets/app.icns")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print(f"\n✓ Built: dist/{APP_NAME}.app")
        
        # Create DMG for distribution
        create_dmg()
    else:
        print("\n✗ Build failed!")
        sys.exit(1)


def build_windows():
    """Build Windows .exe."""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--windowed",
        "--onefile",
        "--add-data", "assets;assets",
        "--hidden-import", "PyQt6.QtNetwork",
        "main.py"
    ]
    
    # Add icon if exists
    icon_path = Path("assets/app.ico")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print(f"\n✓ Built: dist/{APP_NAME}.exe")
        
        # Create portable ZIP
        create_windows_package()
    else:
        print("\n✗ Build failed!")
        sys.exit(1)


def create_dmg():
    """Create macOS DMG for distribution."""
    print("\n4. Creating DMG...")
    
    dmg_name = f"{APP_NAME}_{VERSION}.dmg"
    app_path = f"dist/{APP_NAME}.app"
    
    if not os.path.exists(app_path):
        print("  Skipping DMG (no .app found)")
        return
    
    # Simple DMG creation
    try:
        subprocess.run([
            "hdiutil", "create",
            "-volname", APP_NAME,
            "-srcfolder", app_path,
            "-ov",
            f"dist/{dmg_name}"
        ], check=True)
        print(f"✓ Created: dist/{dmg_name}")
    except Exception as e:
        print(f"  DMG creation failed: {e}")
        print("  You can manually distribute the .app bundle")


def create_windows_package():
    """Create Windows portable package."""
    print("\n4. Creating portable package...")
    
    output_dir = Path("installer_output")
    output_dir.mkdir(exist_ok=True)
    
    exe_path = Path(f"dist/{APP_NAME}.exe")
    if exe_path.exists():
        # Copy exe
        shutil.copy2(exe_path, output_dir / f"{APP_NAME}.exe")
        print(f"✓ Created: installer_output/{APP_NAME}.exe")
        
        # Create ZIP
        zip_name = f"{APP_NAME}_{VERSION}_Windows"
        shutil.make_archive(
            str(output_dir / zip_name),
            "zip",
            "dist"
        )
        print(f"✓ Created: installer_output/{zip_name}.zip")


if __name__ == "__main__":
    main()
