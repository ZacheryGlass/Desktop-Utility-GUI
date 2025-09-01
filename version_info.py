"""
Version information for PyInstaller executable
This file is used by PyInstaller to embed version info in the Windows executable
"""

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Desktop Utilities'),
        StringStruct(u'FileDescription', u'Desktop Utility GUI - System Tray Script Manager'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'DesktopUtilityGUI'),
        StringStruct(u'LegalCopyright', u'\xa9 2025 Desktop Utilities'),
        StringStruct(u'OriginalFilename', u'DesktopUtilityGUI.exe'),
        StringStruct(u'ProductName', u'Desktop Utility GUI'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)