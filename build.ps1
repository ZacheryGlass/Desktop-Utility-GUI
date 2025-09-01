# PowerShell build script for Desktop Utility GUI
# Creates both the executable and installer

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Desktop Utility GUI Build Script" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install/update dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
pip install pyinstaller

# Clean previous builds
Write-Host ""
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Path "build" -Recurse -Force }
if (Test-Path "dist") { Remove-Item -Path "dist" -Recurse -Force }

# Build executable with PyInstaller
Write-Host ""
Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow
pyinstaller desktop_utility_gui.spec --clean

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: PyInstaller build failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Executable built successfully!" -ForegroundColor Green
Write-Host "Location: dist\DesktopUtilityGUI.exe" -ForegroundColor Green
Write-Host ""

# Check if Inno Setup is installed
$innoPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $innoPath)) {
    Write-Host "WARNING: Inno Setup not found at $innoPath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To build the installer, please:" -ForegroundColor Yellow
    Write-Host "1. Download Inno Setup from https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host "2. Install it to the default location" -ForegroundColor Yellow
    Write-Host "3. Run this script again" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "The portable executable is available at: dist\DesktopUtilityGUI.exe" -ForegroundColor Green
    Read-Host "Press Enter to exit"
    exit 0
}

# Get version from version.py
$versionContent = Get-Content "version.py"
$versionLine = $versionContent | Where-Object { $_ -match '__version__' }
if ($versionLine -match '"([^"]+)"') {
    $version = $matches[1]
} else {
    $version = "1.0.0"
}

# Build installer with Inno Setup
Write-Host "Building installer with Inno Setup..." -ForegroundColor Yellow
Write-Host "Version: $version" -ForegroundColor Cyan
& $innoPath "/DMyAppVersion=$version" "installer.iss"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Inno Setup build failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Green
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Outputs:" -ForegroundColor Cyan
Write-Host "- Portable EXE: dist\DesktopUtilityGUI.exe" -ForegroundColor White
Write-Host "- Installer:    dist\DesktopUtilityGUI_Setup_$version.exe" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"