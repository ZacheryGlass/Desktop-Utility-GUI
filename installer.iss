; Inno Setup Script for Desktop Utility GUI
; This creates a Windows installer that installs the application and sets it to run on startup

#define MyAppName "Desktop Utility GUI"
#define MyAppPublisher "Desktop Utilities"
#define MyAppURL "https://github.com/yourusername/Desktop-Utility-GUI"
#define MyAppExeName "DesktopUtilityGUI.exe"

; Version will be set by the build script
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

[Setup]
AppId={{E5D8F3A2-7B9C-4F2D-8A1E-9C3B5D4A6E7F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=DesktopUtilityGUI_Setup_{#MyAppVersion}
SetupIconFile=assets\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}
DisableProgramGroupPage=yes
DisableWelcomePage=no
DisableReadyPage=no
DisableDirPage=no
ShowLanguageDialog=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startup"; Description: "Start Desktop Utility GUI when Windows starts"; GroupDescription: "Startup Options:"; Flags: checked

[Files]
; Main executable and all files from dist folder
Source: "dist\DesktopUtilityGUI.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Include scripts folder if not bundled in exe
Source: "scripts\*"; DestDir: "{app}\scripts"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Add to Windows startup if user selected the option
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "DesktopUtilityGUI"; ValueData: """{app}\{#MyAppExeName}"" --minimized"; Flags: uninsdeletevalue; Tasks: startup

[Run]
; Launch the application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent runascurrentuser

[UninstallRun]
; Kill the application before uninstalling
Filename: "taskkill"; Parameters: "/F /IM {#MyAppExeName}"; Flags: runhidden waituntilterminated

[Code]
// Check if application is running before installation
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  // Try to kill any running instance
  Exec('taskkill', '/F /IM ' + '{#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := True;
end;

// Check if application is running before uninstallation
function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  // Try to kill any running instance
  Exec('taskkill', '/F /IM ' + '{#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := True;
end;

// Custom page to show installation summary
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Any post-installation tasks can be added here
  end;
end;