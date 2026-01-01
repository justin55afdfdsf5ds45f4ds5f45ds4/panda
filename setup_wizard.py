"""
Hit & Run Panda - Windows Installer Wizard
A proper GUI installer with progress bar and registry entries.
"""

import sys
import os
import shutil
import winreg
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QCheckBox, QLineEdit,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon

APP_NAME = "Hit and Run Panda"
APP_VERSION = "1.0.0"
APP_PUBLISHER = "Panda Software"
APP_EXE = "HitAndRunPanda.exe"
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\HitAndRunPanda"


class InstallThread(QThread):
    """Background thread for installation."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, install_dir, create_desktop, create_startup, source_dir):
        super().__init__()
        self.install_dir = install_dir
        self.create_desktop = create_desktop
        self.create_startup = create_startup
        self.source_dir = source_dir
        
    def run(self):
        try:
            install_path = Path(self.install_dir)
            
            # Step 1: Create directories
            self.progress.emit(10, "Creating directories...")
            install_path.mkdir(parents=True, exist_ok=True)
            (install_path / "assets").mkdir(exist_ok=True)
            
            # Step 2: Copy main exe
            self.progress.emit(25, "Copying application...")
            src_exe = Path(self.source_dir) / APP_EXE
            if src_exe.exists():
                shutil.copy2(src_exe, install_path / APP_EXE)
            else:
                # If running from source, copy launcher
                shutil.copy2(Path(self.source_dir) / "launcher.pyw", install_path / "launcher.pyw")
                shutil.copy2(Path(self.source_dir) / "main.py", install_path / "main.py")
            
            # Step 3: Copy assets
            self.progress.emit(40, "Copying assets...")
            src_assets = Path(self.source_dir) / "assets"
            if src_assets.exists():
                for f in src_assets.iterdir():
                    try:
                        shutil.copy2(f, install_path / "assets" / f.name)
                    except:
                        pass
            
            # Step 4: Create Start Menu shortcut
            self.progress.emit(55, "Creating Start Menu shortcut...")
            try:
                start_menu = Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs"
                self.create_shortcut(
                    install_path / APP_EXE,
                    start_menu / f"{APP_NAME}.lnk",
                    install_path
                )
            except Exception as e:
                print(f"Start menu shortcut error: {e}")
            
            # Step 5: Desktop shortcut
            if self.create_desktop:
                self.progress.emit(65, "Creating Desktop shortcut...")
                try:
                    desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
                    self.create_shortcut(
                        install_path / APP_EXE,
                        desktop / f"{APP_NAME}.lnk",
                        install_path
                    )
                except Exception as e:
                    print(f"Desktop shortcut error: {e}")
            
            # Step 6: Startup shortcut
            if self.create_startup:
                self.progress.emit(75, "Adding to startup...")
                try:
                    startup = Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/Startup"
                    self.create_shortcut(
                        install_path / APP_EXE,
                        startup / f"{APP_NAME}.lnk",
                        install_path
                    )
                except Exception as e:
                    print(f"Startup shortcut error: {e}")
            
            # Step 7: Create uninstaller
            self.progress.emit(85, "Creating uninstaller...")
            self.create_uninstaller(install_path)
            
            # Step 8: Add to Windows Registry (Add/Remove Programs)
            self.progress.emit(95, "Registering application...")
            self.register_app(install_path)
            
            self.progress.emit(100, "Installation complete!")
            self.finished.emit(True, str(install_path / APP_EXE))
            
        except Exception as e:
            self.finished.emit(False, str(e))
    
    def create_shortcut(self, target, shortcut_path, working_dir):
        """Create a Windows shortcut using PowerShell."""
        try:
            # Use PowerShell - more reliable than COM
            ps_cmd = f'''
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut("{shortcut_path}")
$s.TargetPath = "{target}"
$s.WorkingDirectory = "{working_dir}"
$s.Save()
'''
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"Shortcut warning: {result.stderr}")
        except Exception as e:
            print(f"Shortcut error: {e}")
    
    def create_uninstaller(self, install_path):
        """Create uninstaller batch file."""
        uninstall_bat = install_path / "uninstall.bat"
        content = f'''@echo off
echo Uninstalling {APP_NAME}...
echo.

:: Remove registry entry
reg delete "HKCU\\{UNINSTALL_KEY}" /f >nul 2>&1

:: Remove shortcuts
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{APP_NAME}.lnk" >nul 2>&1
del "%USERPROFILE%\\Desktop\\{APP_NAME}.lnk" >nul 2>&1
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\{APP_NAME}.lnk" >nul 2>&1

:: Remove install directory (delayed)
echo Removing files...
cd /d "%TEMP%"
rmdir /S /Q "{install_path}" >nul 2>&1

echo.
echo {APP_NAME} has been uninstalled.
echo.
pause
'''
        uninstall_bat.write_text(content)
    
    def register_app(self, install_path):
        """Add entry to Windows Add/Remove Programs."""
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
            
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, APP_PUBLISHER)
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_path))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, str(install_path / "uninstall.bat"))
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(install_path / APP_EXE))
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Registry error: {e}")


class WelcomePage(QWizardPage):
    """Welcome page of the installer."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Logo/Title
        title = QLabel("🐼 Hit & Run Panda")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            f"Welcome to the {APP_NAME} Setup Wizard.\n\n"
            "This will install the productivity pet on your computer.\n\n"
            "The panda will remind you to:\n"
            "  • Drink water\n"
            "  • Take breaks\n"
            "  • Stretch\n"
            "  • And more!\n\n"
            "Click Next to continue."
        )
        desc.setFont(QFont("Segoe UI", 11))
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        layout.addStretch()
        
        # Version
        version = QLabel(f"Version {APP_VERSION}")
        version.setStyleSheet("color: gray;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)


class OptionsPage(QWizardPage):
    """Installation options page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Installation Options")
        self.setSubTitle("Choose where to install and additional options.")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Install location
        loc_label = QLabel("Install location:")
        loc_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(loc_label)
        
        loc_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        default_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "HitAndRunPanda")
        self.path_edit.setText(default_path)
        self.path_edit.setFont(QFont("Segoe UI", 10))
        loc_layout.addWidget(self.path_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse)
        loc_layout.addWidget(browse_btn)
        layout.addLayout(loc_layout)
        
        layout.addSpacing(20)
        
        # Options
        opt_label = QLabel("Additional options:")
        opt_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(opt_label)
        
        self.desktop_check = QCheckBox("Create Desktop shortcut")
        self.desktop_check.setChecked(True)
        self.desktop_check.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.desktop_check)
        
        self.startup_check = QCheckBox("Start with Windows")
        self.startup_check.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.startup_check)
        
        layout.addStretch()
        
        # Register fields
        self.registerField("install_path", self.path_edit)
        self.registerField("create_desktop", self.desktop_check)
        self.registerField("create_startup", self.startup_check)
        
    def browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Installation Folder")
        if folder:
            self.path_edit.setText(os.path.join(folder, "HitAndRunPanda"))


class InstallPage(QWizardPage):
    """Installation progress page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Installing")
        self.setSubTitle("Please wait while the application is being installed...")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        self.status_label = QLabel("Preparing installation...")
        self.status_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        
        self.install_thread = None
        self.install_complete = False
        self.exe_path = ""
        
    def initializePage(self):
        """Start installation when page is shown."""
        wizard = self.wizard()
        install_path = wizard.field("install_path")
        create_desktop = wizard.field("create_desktop")
        create_startup = wizard.field("create_startup")
        
        # Get source directory
        source_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.install_thread = InstallThread(
            install_path, create_desktop, create_startup, source_dir
        )
        self.install_thread.progress.connect(self.update_progress)
        self.install_thread.finished.connect(self.install_finished)
        self.install_thread.start()
        
    def update_progress(self, value, status):
        self.progress_bar.setValue(value)
        self.status_label.setText(status)
        
    def install_finished(self, success, message):
        self.install_complete = success
        if success:
            self.exe_path = message
            self.status_label.setText("✓ Installation complete!")
            self.progress_bar.setValue(100)
        else:
            self.status_label.setText(f"✗ Error: {message}")
        self.completeChanged.emit()
        
    def isComplete(self):
        return self.install_complete


class FinishPage(QWizardPage):
    """Finish page."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Installation Complete")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Success message
        success = QLabel("🎉 Hit & Run Panda has been installed!")
        success.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        success.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(success)
        
        info = QLabel(
            "You can now:\n\n"
            "  • Find it in the Start Menu\n"
            "  • Search 'Panda' in Windows Search\n"
            "  • Find it in Control Panel → Programs\n"
            "  • Use the Desktop shortcut (if created)\n\n"
            "To uninstall, use Control Panel or run uninstall.bat\n"
            "in the installation folder."
        )
        info.setFont(QFont("Segoe UI", 10))
        info.setWordWrap(True)
        layout.addWidget(info)
        
        layout.addStretch()
        
        self.launch_check = QCheckBox("Launch Hit & Run Panda now")
        self.launch_check.setChecked(True)
        self.launch_check.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.launch_check)
        
        self.registerField("launch_app", self.launch_check)


class InstallerWizard(QWizard):
    """Main installer wizard."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} Setup")
        self.setFixedSize(500, 400)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        
        # Add pages
        self.addPage(WelcomePage())
        self.options_page = OptionsPage()
        self.addPage(self.options_page)
        self.install_page = InstallPage()
        self.addPage(self.install_page)
        self.addPage(FinishPage())
        
        self.setButtonText(QWizard.WizardButton.FinishButton, "Finish")
        
    def accept(self):
        """Called when Finish is clicked."""
        if self.field("launch_app"):
            exe_path = self.install_page.exe_path
            if exe_path and os.path.exists(exe_path):
                subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
        super().accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    wizard = InstallerWizard()
    wizard.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
