Releasing Desktop Utility GUI
=============================

This guide explains how to build a signed installer for Windows and publish it to GitHub Releases using a one‑click workflow.

Overview
--------
- Version lives in the root `VERSION` file.
- GitHub Action bumps the version, tags `vX.Y.Z`, builds the EXE (PyInstaller), builds the installer (Inno Setup), and publishes a GitHub Release with the installer attached.
- The installer creates an optional Startup entry (enabled by default) so the app runs on login using `--minimized`.

One‑Click Release (GitHub)
-------------------------
1. Push your changes to `main`.
2. In GitHub, open the `Actions` tab → select `Release` workflow.
3. Click `Run workflow` and choose the bump type: `patch`, `minor`, or `major`.
4. The workflow will:
   - Bump `VERSION`, commit with `chore(release): vX.Y.Z`, and create `vX.Y.Z` tag.
   - Build a standalone EXE via PyInstaller.
   - Build a Windows installer via Inno Setup.
   - Create a GitHub Release and upload `DesktopUtilityGUI-X.Y.Z-Setup.exe`.

Artifacts & Locations
---------------------
- PyInstaller output: `dist/DesktopUtilityGUI/DesktopUtilityGUI.exe`
- Inno Setup output: `installer/output/DesktopUtilityGUI-X.Y.Z-Setup.exe`

Startup Behavior
----------------
- The installer adds a Startup shortcut for the current user so the app launches on login minimized to tray.
- You can opt out during install by unchecking “Start Desktop Utility GUI at login”.
- Uninstall removes the Startup entry.

Local Build (optional)
----------------------
You can build locally if desired (Windows):

1. Create the executable
   - `pip install -r requirements.txt`
   - `pip install pyinstaller`
   - `pyinstaller --noconfirm --clean --name DesktopUtilityGUI --windowed main.py`

2. Create the installer
   - Install Inno Setup (https://jrsoftware.org/isinfo.php)
   - Open `installer/desktop_utility_gui.iss` and click Build (or run `ISCC installer\desktop_utility_gui.iss /DMyAppVersion=0.0.0`)
   - Result: `installer/output/DesktopUtilityGUI-<version>-Setup.exe`

Versioning Notes
----------------
- The release workflow updates only the `VERSION` file and uses it for the tag and installer naming.
- We follow Conventional Commits. The workflow’s bump type is manual to keep things simple. You can later switch to tools like `release-please` or `python-semantic-release` if you want automatic bumping based on commit messages.

Troubleshooting
---------------
- Build failures: Ensure `requirements.txt` is correct. Heavy dependencies (e.g., OCR) can increase build time.
- Missing assets: If your app requires data files, consider adding PyInstaller `--add-data` options or a `.spec` file.
- Startup option not applied: Verify the Startup shortcut exists in `shell:startup`. Reinstall with the task checked if needed.

