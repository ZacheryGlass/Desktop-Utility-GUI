@echo off
REM Build script for Desktop Utility GUI
REM Creates both the executable and installer

echo ====================================
echo Desktop Utility GUI Build Script
echo ====================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

REM Clean previous builds
echo.
echo Cleaning previous builds...
if exist "build\" rmdir /s /q build
if exist "dist\" rmdir /s /q dist

REM Build executable with PyInstaller
echo.
echo Building executable with PyInstaller...
pyinstaller desktop_utility_gui.spec --clean

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo Executable built successfully!
echo Location: dist\DesktopUtilityGUI.exe
echo.

REM Check if Inno Setup is installed
set INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if not exist "%INNO_PATH%" (
    echo WARNING: Inno Setup not found at %INNO_PATH%
    echo.
    echo To build the installer, please:
    echo 1. Download Inno Setup from https://jrsoftware.org/isdl.php
    echo 2. Install it to the default location
    echo 3. Run this script again
    echo.
    echo The portable executable is available at: dist\DesktopUtilityGUI.exe
    pause
    exit /b 0
)

REM Get version from version.py
for /f "tokens=2 delims='" %%a in ('findstr "__version__" version.py') do set VERSION=%%a

REM Build installer with Inno Setup
echo Building installer with Inno Setup...
echo Version: %VERSION%
"%INNO_PATH%" /DMyAppVersion=%VERSION% installer.iss

if errorlevel 1 (
    echo.
    echo ERROR: Inno Setup build failed!
    pause
    exit /b 1
)

echo.
echo ====================================
echo Build completed successfully!
echo ====================================
echo.
echo Outputs:
echo - Portable EXE: dist\DesktopUtilityGUI.exe
echo - Installer:    dist\DesktopUtilityGUI_Setup_%VERSION%.exe
echo.
pause