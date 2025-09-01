#!/usr/bin/env python3
"""
Version bumping script for Desktop Utility GUI
Supports semantic versioning: major.minor.patch
"""

import argparse
import re
import sys
from pathlib import Path

def parse_version(version_str):
    """Parse version string into tuple of integers"""
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version_str)
    if not match:
        raise ValueError(f"Invalid version format: {version_str}")
    return tuple(map(int, match.groups()))

def format_version(version_tuple):
    """Format version tuple as string"""
    return '.'.join(map(str, version_tuple))

def bump_version(current_version, bump_type):
    """Bump version based on type (major, minor, patch)"""
    major, minor, patch = parse_version(current_version)
    
    if bump_type == 'major':
        return format_version((major + 1, 0, 0))
    elif bump_type == 'minor':
        return format_version((major, minor + 1, 0))
    elif bump_type == 'patch':
        return format_version((major, minor, patch + 1))
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

def update_version_py(file_path, new_version):
    """Update version in version.py"""
    content = file_path.read_text()
    content = re.sub(
        r'__version__\s*=\s*["\'][\d.]+["\']',
        f'__version__ = "{new_version}"',
        content
    )
    file_path.write_text(content)

def update_version_info_py(file_path, new_version):
    """Update version in version_info.py for PyInstaller"""
    major, minor, patch = parse_version(new_version)
    content = file_path.read_text()
    
    # Update filevers
    content = re.sub(
        r'filevers=\(\d+,\s*\d+,\s*\d+,\s*\d+\)',
        f'filevers=({major}, {minor}, {patch}, 0)',
        content
    )
    
    # Update prodvers
    content = re.sub(
        r'prodvers=\(\d+,\s*\d+,\s*\d+,\s*\d+\)',
        f'prodvers=({major}, {minor}, {patch}, 0)',
        content
    )
    
    # Update FileVersion string
    content = re.sub(
        r"StringStruct\(u'FileVersion',\s*u'[\d.]+'\)",
        f"StringStruct(u'FileVersion', u'{major}.{minor}.{patch}.0')",
        content
    )
    
    # Update ProductVersion string
    content = re.sub(
        r"StringStruct\(u'ProductVersion',\s*u'[\d.]+'\)",
        f"StringStruct(u'ProductVersion', u'{major}.{minor}.{patch}.0')",
        content
    )
    
    file_path.write_text(content)

def get_current_version():
    """Get current version from version.py"""
    version_file = Path('version.py')
    if not version_file.exists():
        raise FileNotFoundError("version.py not found")
    
    content = version_file.read_text()
    match = re.search(r'__version__\s*=\s*["\'](.+)["\']', content)
    if not match:
        raise ValueError("Could not find version in version.py")
    
    return match.group(1)

def main():
    parser = argparse.ArgumentParser(description='Bump version for Desktop Utility GUI')
    parser.add_argument(
        'bump_type',
        choices=['major', 'minor', 'patch'],
        nargs='?',
        default='patch',
        help='Type of version bump (default: patch)'
    )
    parser.add_argument(
        '--set',
        metavar='VERSION',
        help='Set version explicitly (e.g., 1.2.3)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    
    args = parser.parse_args()
    
    try:
        # Get current version
        current = get_current_version()
        print(f"Current version: {current}")
        
        # Determine new version
        if args.set:
            new_version = args.set
            # Validate format
            parse_version(new_version)
        else:
            new_version = bump_version(current, args.bump_type)
        
        print(f"New version: {new_version}")
        
        if args.dry_run:
            print("Dry run - no files modified")
            return 0
        
        # Update files
        version_py = Path('version.py')
        version_info_py = Path('version_info.py')
        
        if version_py.exists():
            update_version_py(version_py, new_version)
            print(f"Updated {version_py}")
        
        if version_info_py.exists():
            update_version_info_py(version_info_py, new_version)
            print(f"Updated {version_info_py}")
        
        # Output new version for CI/CD scripts
        print(f"::set-output name=version::{new_version}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())