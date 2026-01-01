@echo off
echo ========================================
echo   Hit ^& Run Panda - Installer
echo ========================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\HitAndRunPanda"

echo Installing to: %INSTALL_DIR%
echo.

:: Create directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\assets" mkdir "%INSTALL_DIR%\assets"

:: Copy files
echo Copying files...
copy /Y "%~dp0HitAndRunPanda.exe" "%INSTALL_DIR%\" >nul

:: Copy assets
xcopy /Y /E /I "%~dp0assets" "%INSTALL_DIR%\assets" >nul 2>nul

:: Create Start Menu shortcut
echo Creating shortcuts...
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Hit and Run Panda.lnk"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%INSTALL_DIR%\HitAndRunPanda.exe'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Save()"

:: Create Desktop shortcut
set "DESKTOP_SHORTCUT=%USERPROFILE%\Desktop\Hit and Run Panda.lnk"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP_SHORTCUT%'); $s.TargetPath = '%INSTALL_DIR%\HitAndRunPanda.exe'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Save()"

:: Create uninstaller
echo @echo off > "%INSTALL_DIR%\uninstall.bat"
echo echo Uninstalling Hit ^& Run Panda... >> "%INSTALL_DIR%\uninstall.bat"
echo rmdir /S /Q "%INSTALL_DIR%" >> "%INSTALL_DIR%\uninstall.bat"
echo del "%SHORTCUT%" >> "%INSTALL_DIR%\uninstall.bat"
echo del "%DESKTOP_SHORTCUT%" >> "%INSTALL_DIR%\uninstall.bat"
echo echo Done! >> "%INSTALL_DIR%\uninstall.bat"
echo pause >> "%INSTALL_DIR%\uninstall.bat"

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Installed to: %INSTALL_DIR%
echo.
echo You can find "Hit and Run Panda" in:
echo   - Start Menu
echo   - Desktop
echo   - Windows Search (type "panda")
echo.
echo To uninstall, run: %INSTALL_DIR%\uninstall.bat
echo.

set /p LAUNCH="Launch Hit and Run Panda now? (Y/N): "
if /i "%LAUNCH%"=="Y" start "" "%INSTALL_DIR%\HitAndRunPanda.exe"

pause
