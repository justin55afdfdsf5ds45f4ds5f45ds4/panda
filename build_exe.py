"""
Build script to create a standalone .exe using PyInstaller.
Run: python build_exe.py
"""

import subprocess
import sys
import os

def build():
    # Install PyInstaller if not present
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=HitAndRunPanda",
        "--onefile",
        "--windowed",  # No console window
        "--icon=assets/walking panda 1.png",  # Use panda as icon
        "--add-data=assets;assets",  # Include assets folder
        "--add-data=settings.json;.",  # Include settings if exists
        "launcher.pyw"
    ]
    
    print("Building executable...")
    print(" ".join(cmd))
    subprocess.run(cmd, cwd=os.path.dirname(__file__) or ".")
    
    print("\n✅ Done! Find your exe in: dist/HitAndRunPanda.exe")
    print("You can share this exe - it includes everything needed!")

if __name__ == "__main__":
    build()
