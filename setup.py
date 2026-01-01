"""
Hit & Run Panda - Cross-Platform Setup
Works on Windows and macOS.
"""

import sys
import os
import platform
import shutil
import subprocess
from pathlib import Path

IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"

APP_NAME = "Hit and Run Panda"
APP_VERSION = "1.0.0"


def get_install_dir():
    """Get default install directory for current platform."""
    if IS_MAC:
        return Path.home() / "Applications" / "HitAndRunPanda"
    else:
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "HitAndRunPanda"


def get_source_dir():
    """Get source directory."""
    return Path(__file__).parent


def install_app(install_dir=None, create_desktop=True, create_startup=False):
    """Install the application."""
    if install_dir is None:
        install_dir = get_install_dir()
    
    install_dir = Path(install_dir)
    source_dir = get_source_dir()
    
    print(f"Installing {APP_NAME} to {install_dir}...")
    
    # Create directories
    install_dir.mkdir(parents=True, exist_ok=True)
    (install_dir / "assets").mkdir(exist_ok=True)
    
    # Copy files
    files_to_copy = ["main.py", "launcher.pyw", "red_alert.py"]
    for f in files_to_copy:
        src = source_dir / f
        if src.exists():
            shutil.copy2(src, install_dir / f)
            print(f"  Copied {f}")
    
    # Copy assets
    assets_src = source_dir / "assets"
    if assets_src.exists():
        for f in assets_src.iterdir():
            try:
                shutil.copy2(f, install_dir / "assets" / f.name)
            except:
                pass
        print("  Copied assets")
    
    # Platform-specific setup
    if IS_MAC:
        setup_mac(install_dir, create_desktop, create_startup)
    else:
        setup_windows(install_dir, create_desktop, create_startup)
    
    print(f"\n✓ {APP_NAME} installed successfully!")
    print(f"  Location: {install_dir}")
    return install_dir


def setup_mac(install_dir, create_desktop, create_startup):
    """macOS-specific setup."""
    # Create launch script
    launch_script = install_dir / "run_panda.command"
    launch_script.write_text(f'''#!/bin/bash
cd "{install_dir}"
python3 main.py "$@"
''')
    os.chmod(launch_script, 0o755)
    print("  Created launch script")
    
    # Create .app bundle for better integration
    app_bundle = install_dir / f"{APP_NAME}.app"
    contents = app_bundle / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    
    macos.mkdir(parents=True, exist_ok=True)
    resources.mkdir(exist_ok=True)
    
    # Info.plist
    plist = contents / "Info.plist"
    plist.write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.panda.hitandrun</string>
    <key>CFBundleVersion</key>
    <string>{APP_VERSION}</string>
    <key>CFBundleExecutable</key>
    <string>launch</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
''')
    
    # Launcher script inside .app
    launcher = macos / "launch"
    launcher.write_text(f'''#!/bin/bash
cd "{install_dir}"
python3 main.py
''')
    os.chmod(launcher, 0o755)
    print("  Created .app bundle")
    
    # Desktop alias (symlink)
    if create_desktop:
        desktop = Path.home() / "Desktop" / f"{APP_NAME}.app"
        try:
            if desktop.exists():
                desktop.unlink()
            desktop.symlink_to(app_bundle)
            print("  Created Desktop shortcut")
        except Exception as e:
            print(f"  Desktop shortcut failed: {e}")
    
    # Login item (startup)
    if create_startup:
        try:
            # Use osascript to add login item
            subprocess.run([
                "osascript", "-e",
                f'tell application "System Events" to make login item at end with properties {{path:"{app_bundle}", hidden:false}}'
            ], capture_output=True)
            print("  Added to Login Items")
        except Exception as e:
            print(f"  Login item failed: {e}")


def setup_windows(install_dir, create_desktop, create_startup):
    """Windows-specific setup."""
    import winreg
    
    UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\HitAndRunPanda"
    
    # Create batch launcher
    bat_file = install_dir / "HitAndRunPanda.bat"
    bat_file.write_text(f'''@echo off
cd /d "{install_dir}"
pythonw main.py %*
''')
    print("  Created launcher")
    
    # Create shortcuts using PowerShell
    def create_shortcut(target, shortcut_path, working_dir):
        ps_cmd = f'''
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut("{shortcut_path}")
$s.TargetPath = "{target}"
$s.WorkingDirectory = "{working_dir}"
$s.Save()
'''
        subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True
        )
    
    # Start Menu
    start_menu = Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs"
    create_shortcut(bat_file, start_menu / f"{APP_NAME}.lnk", install_dir)
    print("  Created Start Menu shortcut")
    
    # Desktop
    if create_desktop:
        desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
        create_shortcut(bat_file, desktop / f"{APP_NAME}.lnk", install_dir)
        print("  Created Desktop shortcut")
    
    # Startup
    if create_startup:
        startup = Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/Startup"
        create_shortcut(bat_file, startup / f"{APP_NAME}.lnk", install_dir)
        print("  Added to Startup")
    
    # Registry for Add/Remove Programs
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
        winreg.CloseKey(key)
        print("  Registered in Control Panel")
    except Exception as e:
        print(f"  Registry failed: {e}")


def uninstall_app(install_dir=None):
    """Uninstall the application."""
    if install_dir is None:
        install_dir = get_install_dir()
    
    install_dir = Path(install_dir)
    
    print(f"Uninstalling {APP_NAME}...")
    
    if IS_MAC:
        # Remove login item
        try:
            subprocess.run([
                "osascript", "-e",
                f'tell application "System Events" to delete login item "{APP_NAME}"'
            ], capture_output=True)
        except:
            pass
        
        # Remove desktop shortcut
        desktop = Path.home() / "Desktop" / f"{APP_NAME}.app"
        if desktop.exists():
            desktop.unlink()
    else:
        import winreg
        UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\HitAndRunPanda"
        
        # Remove shortcuts
        for path in [
            Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs" / f"{APP_NAME}.lnk",
            Path(os.environ["USERPROFILE"]) / "Desktop" / f"{APP_NAME}.lnk",
            Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/Startup" / f"{APP_NAME}.lnk",
        ]:
            try:
                path.unlink()
            except:
                pass
        
        # Remove registry
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
        except:
            pass
    
    # Remove install directory
    if install_dir.exists():
        shutil.rmtree(install_dir, ignore_errors=True)
    
    print(f"✓ {APP_NAME} uninstalled")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall_app()
    else:
        install_app()
