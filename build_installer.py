"""
Build script to create a proper Windows installer.

Steps:
1. Run this script: python build_installer.py
2. Download Inno Setup from https://jrsoftware.org/isdl.php
3. Open installer.iss with Inno Setup and compile it
4. Share the installer_output/HitAndRunPanda_Setup.exe
"""

import subprocess
import sys
import os
import shutil
from PIL import Image

def create_icon():
    """Convert PNG to ICO for Windows."""
    print("Creating icon...")
    try:
        from PIL import Image
        img = Image.open("assets/walking panda 1.png")
        img = img.resize((256, 256), Image.Resampling.LANCZOS)
        img.save("assets/walking panda 1.ico", format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
        print("✓ Icon created")
    except ImportError:
        print("⚠ Pillow not installed. Run: pip install Pillow")
        print("  Skipping icon creation...")
    except Exception as e:
        print(f"⚠ Could not create icon: {e}")

def build_exe():
    """Build the exe with PyInstaller."""
    print("Building executable...")
    
    # Install PyInstaller if needed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Clean previous build
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    
    # Build command - create a folder, not single file
    icon_path = "assets/walking panda 1.ico" if os.path.exists("assets/walking panda 1.ico") else None
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=HitAndRunPanda",
        "--onedir",  # Folder mode for faster startup
        "--windowed",
        "--add-data=assets;assets",
        "launcher.pyw"
    ]
    
    if icon_path:
        cmd.insert(-1, f"--icon={icon_path}")
    
    subprocess.run(cmd)
    
    # Copy assets to dist folder for installer
    if os.path.exists("dist/HitAndRunPanda"):
        print("✓ Executable built in dist/HitAndRunPanda/")
    
def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or ".")
    
    print("=" * 50)
    print("Hit & Run Panda - Installer Builder")
    print("=" * 50)
    
    # Install Pillow for icon creation
    try:
        from PIL import Image
    except ImportError:
        print("Installing Pillow for icon creation...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    
    create_icon()
    build_exe()
    
    print("\n" + "=" * 50)
    print("BUILD COMPLETE!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Download Inno Setup: https://jrsoftware.org/isdl.php")
    print("2. Install Inno Setup")
    print("3. Right-click 'installer.iss' → Compile")
    print("4. Find your installer at: installer_output/HitAndRunPanda_Setup.exe")
    print("\nThe installer will:")
    print("  ✓ Show in Windows Search")
    print("  ✓ Appear in Control Panel")
    print("  ✓ Create Start Menu shortcuts")
    print("  ✓ Optional desktop shortcut")
    print("  ✓ Optional start with Windows")
    print("  ✓ Proper uninstaller")

if __name__ == "__main__":
    main()
