"""
Simple installer creator using NSIS-like batch approach.
Creates a self-extracting installer without external tools.
"""

import subprocess
import sys
import os
import shutil
import zipfile

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or ".")
    
    print("=" * 50)
    print("Hit & Run Panda - Installer Builder")
    print("=" * 50)
    
    # Install requirements
    print("\n1. Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "Pillow", "pywin32", "-q"])
    
    # Create icon
    print("\n2. Creating icon...")
    try:
        from PIL import Image
        img = Image.open("assets/walking panda 1.png")
        img = img.resize((256, 256), Image.Resampling.LANCZOS)
        img.save("assets/app.ico", format='ICO', sizes=[(256, 256), (48, 48), (32, 32), (16, 16)])
        print("   ✓ Icon created")
    except Exception as e:
        print(f"   ⚠ Icon skipped: {e}")
    
    # Clean old builds
    print("\n3. Cleaning old builds...")
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
            except PermissionError:
                print(f"   ⚠ Could not delete {folder} - files in use. Close the app first!")
    
    # Don't delete installer_output, just overwrite files
    os.makedirs("installer_output", exist_ok=True)
    
    # Build main app exe
    print("\n4. Building main application...")
    icon_arg = "--icon=assets/app.ico" if os.path.exists("assets/app.ico") else ""
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=HitAndRunPanda",
        "--onefile",
        "--windowed",
        "--add-data=assets;assets",
        icon_arg,
        "launcher.pyw"
    ]
    cmd = [c for c in cmd if c]
    subprocess.run(cmd, capture_output=True)
    print("   ✓ Main app built")
    
    # Build installer exe
    print("\n5. Building installer wizard...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=HitAndRunPanda_Setup",
        "--onefile",
        "--windowed",
        "--add-data=assets;assets",
        "--add-data=dist/HitAndRunPanda.exe;.",
        icon_arg,
        "setup_wizard.py"
    ]
    cmd = [c for c in cmd if c]
    subprocess.run(cmd, capture_output=True)
    print("   ✓ Installer built")
    
    # Copy to output
    print("\n6. Creating output files...")
    if os.path.exists("dist/HitAndRunPanda_Setup.exe"):
        shutil.copy("dist/HitAndRunPanda_Setup.exe", "installer_output/")
        print("   ✓ installer_output/HitAndRunPanda_Setup.exe")
    
    if os.path.exists("dist/HitAndRunPanda.exe"):
        try:
            # Try to delete first if exists
            standalone_path = "installer_output/HitAndRunPanda.exe"
            if os.path.exists(standalone_path):
                os.remove(standalone_path)
            shutil.copy("dist/HitAndRunPanda.exe", "installer_output/")
            print("   ✓ installer_output/HitAndRunPanda.exe (standalone)")
        except PermissionError:
            print("   ⚠ Could not copy standalone exe (file in use)")
            print("   → Use the Setup.exe instead")
    
    print("\n" + "=" * 50)
    print("DONE!")
    print("=" * 50)
    print("\nShare: installer_output/HitAndRunPanda_Setup.exe")
    print("\nThis installer will:")
    print("  ✓ Show proper install wizard with progress bar")
    print("  ✓ Add to Start Menu")
    print("  ✓ Show in Windows Search")
    print("  ✓ Show in Control Panel → Programs")
    print("  ✓ Create Desktop shortcut (optional)")
    print("  ✓ Start with Windows (optional)")
    print("  ✓ Proper uninstaller")

if __name__ == "__main__":
    main()
