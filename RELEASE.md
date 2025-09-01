# Desktop Utility GUI Release Process

This document describes the build and release process for Desktop Utility GUI, including local builds and automated GitHub releases.

## Overview

Desktop Utility GUI is packaged as a Windows installer that:
- Installs the application to Program Files
- Optionally configures the app to run on Windows startup
- Creates desktop shortcuts
- Handles proper uninstallation

## Prerequisites

### For Local Builds

1. **Python 3.11+** installed
2. **Inno Setup 6** (for creating installer)
   - Download from: https://jrsoftware.org/isdl.php
   - Install to default location: `C:\Program Files (x86)\Inno Setup 6\`

### For GitHub Actions

- Repository with proper secrets configured (GITHUB_TOKEN is automatic)
- Push access to create tags and releases

## Version Management

The application version is managed in two files:
- `version.py` - Python version info
- `version_info.py` - Windows executable version metadata

### Manual Version Bumping

```bash
# Bump patch version (1.0.0 -> 1.0.1)
python bump_version.py patch

# Bump minor version (1.0.0 -> 1.1.0)
python bump_version.py minor

# Bump major version (1.0.0 -> 2.0.0)
python bump_version.py major

# Set specific version
python bump_version.py --set 1.2.3

# Preview changes without modifying files
python bump_version.py patch --dry-run
```

## Local Build Process

### Quick Build

#### Using Batch Script (Windows Command Prompt)
```cmd
build.bat
```

#### Using PowerShell Script
```powershell
.\build.ps1
```

These scripts will:
1. Create/activate virtual environment
2. Install dependencies
3. Build executable with PyInstaller
4. Create installer with Inno Setup (if available)
5. Output files to `dist/` directory

### Manual Build Steps

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **Build executable**
   ```bash
   pyinstaller desktop_utility_gui.spec --clean
   ```
   This creates `dist/DesktopUtilityGUI.exe`

3. **Build installer** (requires Inno Setup)
   ```bash
   # Get current version
   python -c "from version import __version__; print(__version__)"
   
   # Build installer (replace VERSION with actual version)
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DMyAppVersion=VERSION installer.iss
   ```
   This creates `dist/DesktopUtilityGUI_Setup_VERSION.exe`

## GitHub Actions Automated Release

### One-Click Release Process

1. Go to your GitHub repository
2. Click on **Actions** tab
3. Select **Release Desktop Utility GUI** workflow
4. Click **Run workflow**
5. Choose options:
   - **Version bump type**: patch/minor/major
   - **Create GitHub release**: Yes/No
6. Click **Run workflow**

The workflow will automatically:
1. Bump the version in source files
2. Commit the version change
3. Build the executable with PyInstaller
4. Create the installer with Inno Setup
5. Create a git tag
6. Create a GitHub release
7. Upload both portable exe and installer to the release

### Release Artifacts

Each release includes two artifacts:

1. **Installer** (`DesktopUtilityGUI_Setup_X.Y.Z.exe`)
   - Full installation with Program Files integration
   - Start menu shortcuts
   - Optional startup configuration
   - Proper uninstaller

2. **Portable Executable** (`DesktopUtilityGUI_Portable_X.Y.Z.exe`)
   - Single file, no installation required
   - Can be run from any location
   - Settings stored locally
   - Good for USB drives or testing

## File Structure

```
Desktop-Utility-GUI/
├── .github/
│   └── workflows/
│       └── release.yml         # GitHub Actions workflow
├── assets/
│   └── icon.ico               # Application icon
├── dist/                      # Build output (git-ignored)
│   ├── DesktopUtilityGUI.exe
│   └── DesktopUtilityGUI_Setup_X.Y.Z.exe
├── scripts/                   # Utility scripts (included in build)
├── bump_version.py           # Version management script
├── build.bat                 # Windows batch build script
├── build.ps1                 # PowerShell build script
├── desktop_utility_gui.spec  # PyInstaller configuration
├── installer.iss             # Inno Setup script
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
├── version.py                # Version info for Python
└── version_info.py          # Version info for Windows exe
```

## Build Configuration

### PyInstaller Configuration (`desktop_utility_gui.spec`)

- **Entry point**: `main.py`
- **Bundle type**: Single executable
- **Console**: Hidden (windowed application)
- **Included data**: 
  - `style.qss` (UI styling)
  - `scripts/` directory (utility scripts)
- **Hidden imports**: PyQt6, pywin32, APScheduler, easyocr, torch, etc.

### Inno Setup Configuration (`installer.iss`)

- **Install location**: `{autopf}\Desktop Utility GUI` (Program Files)
- **Architecture**: 64-bit Windows only
- **Compression**: LZMA2/max for smallest size
- **Features**:
  - Optional desktop shortcut
  - Optional Windows startup registration
  - Clean uninstallation
  - Kills running instance before install/uninstall

## Troubleshooting

### Common Issues

1. **PyInstaller fails with import errors**
   - Check that all dependencies are in `requirements.txt`
   - Add missing modules to `hiddenimports` in spec file

2. **Inno Setup not found**
   - Install from: https://jrsoftware.org/isdl.php
   - Ensure installed to default location
   - Or update path in build scripts

3. **GitHub Actions workflow fails**
   - Check Python version compatibility
   - Ensure all files are committed
   - Verify workflow has necessary permissions

4. **Executable runs but scripts don't work**
   - Ensure `scripts/` directory is included in build
   - Check that scripts use proper paths
   - Verify all script dependencies are bundled

### Debug Build

To create a debug build with console output:

1. Edit `desktop_utility_gui.spec`
2. Change `console=False` to `console=True`
3. Rebuild with PyInstaller

## Security Considerations

- The installer requires admin privileges for Program Files installation
- Startup registration modifies `HKCU\...\CurrentVersion\Run`
- Global hotkeys use Windows RegisterHotKey API
- Scripts run with user privileges

## Testing Checklist

Before releasing, test:

- [ ] Application starts without errors
- [ ] System tray icon appears
- [ ] Scripts load and execute correctly
- [ ] Hotkeys register and trigger
- [ ] Scheduled scripts execute at correct times
- [ ] Schedule configuration dialog works properly
- [ ] Schedule indicators appear in tray menu
- [ ] Schedules persist between application restarts
- [ ] Settings persist between runs
- [ ] Installer completes successfully
- [ ] Uninstaller removes all files
- [ ] Startup option works correctly

## Release Notes Template

When creating a release, use this template:

```markdown
## Desktop Utility GUI vX.Y.Z

### What's New
- Feature: Description
- Fix: Description
- Enhancement: Description

### Installation
1. Download the installer below
2. Run the installer and follow the prompts
3. Launch from Start Menu or desktop shortcut

### System Requirements
- Windows 10/11 (64-bit)
- No Python installation required

### Known Issues
- Issue description and workaround

### Contributors
- @username - contribution
```

## Support

For issues or questions:
- Create an issue on GitHub
- Check existing issues for solutions
- Include version number and Windows version in reports